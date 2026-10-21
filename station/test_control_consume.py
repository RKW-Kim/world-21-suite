#!/usr/bin/env python3
"""control.json consume/produce, live-fired with a FakeRenderer.

control.json is the dock's command channel into the running station: the
panel writes verbs, the daemon consumes them once. The race being tested:
the daemon's consume can take SECONDS (skip runs a whole advance), and a
verb posted by the panel during that window used to be destroyed by the
stale write-back, while a stale panel write could resurrect an already
consumed verb (double-advance). The contract now:

  1. a verb posted while the consume is running SURVIVES the write-back;
  2. every verb this pass consumed is gone from the file;
  3. skip acts exactly once, with force=True (beats the refractory);
  4. a corrupt or non-dict file is swallowed, not crashed on;
  5. the panel's api_control RMW is atomic under the same station lock.

Run: python3 station/test_control_consume.py
"""

import json
import os
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


tmp = tempfile.mkdtemp()
os.environ["BROADCAST_ROOT"] = tmp
import daemon

daemon.DB = os.path.join(tmp, "activity.db")   # a test must not write the live trail
CONTROL = daemon.CONTROL


def seed(d):
    with open(CONTROL, "w") as f:
        json.dump(d, f)


def read_ctl():
    with open(CONTROL) as f:
        return json.load(f)


class FakeRenderer:
    def __init__(self):
        self.vols = []
        self.actions = []

    def set_volume(self, src, db):
        self.vols.append((src, db))

    def media_action(self, src, act):
        self.actions.append((src, act))


DECKS = {"A": daemon.DECK_A, "B": daemon.DECK_B}
DATA = {"items": [{"file": "a.mp4", "title": "A", "id": "a"}]}

# ---- 1+2+3: the mid-consume verb survives; consumed keys are gone ------
ended_calls = []
_real_on_ended = daemon.on_ended


def fake_on_ended(renderer, decks, src, force=False):
    ended_calls.append((src, force))
    # The panel posts a skip WHILE the daemon is mid-consume (this is the
    # window the old write-back destroyed): an honest panel RMW under the
    # station lock, exactly what api_control does.
    with daemon.pl_lock():
        ctl = read_ctl()
        ctl["skip"] = True
        ctl["media"] = {"action": "pause"}
        with open(CONTROL, "w") as f:
            json.dump(ctl, f)


daemon.on_ended = fake_on_ended
seed({"skip": True, "probe": True})
r = FakeRenderer()
daemon.consume_control(r, DECKS, DATA)
check(ended_calls == [(daemon.DECK_A, True)],
      "skip acted once, direct route (force=True)")
after = read_ctl()
# The mid-consume SKIP is deliberately eaten: skip is a bare boolean with
# no instance identity, the pass already acted on one, and the 6s post-cut
# refractory exists to absorb slam-skips. What must survive is any verb
# whose key the pass never saw -- here, the media verb.
check("skip" not in after,
      "a skip posted mid-consume is swallowed (acted once this pass, same key)")
check(after.get("media") == {"action": "pause"},
      "a media verb posted mid-consume SURVIVES the write-back (was eaten before)")
check("probe" not in after, "the consumed probe key is gone from the file")

# The surviving verbs are consumed by the NEXT pass, exactly once more.
# skip was swallowed (see above), so this pass acts on media only.
daemon.on_ended = _real_on_ended
daemon.probe_plane = lambda renderer: None
r2 = FakeRenderer()
daemon.consume_control(r2, DECKS, DATA)
after2 = read_ctl()
check("skip" not in after2 and "media" not in after2,
      "second pass consumes the surviving verbs cleanly")
check(r2.actions and r2.actions[-1][1] == "pause",
      "surviving media verb reaches the renderer on the second pass")

# ---- 4: hostile file shapes are swallowed ------------------------------
with open(CONTROL, "w") as f:
    f.write("{not json at all")
daemon.consume_control(FakeRenderer(), DECKS, DATA)   # must not raise
check(True, "corrupt control.json does not crash the consume")
with open(CONTROL, "w") as f:
    json.dump(["a", "list"], f)
daemon.consume_control(FakeRenderer(), DECKS, DATA)   # must not raise
check(True, "non-dict control.json does not crash the consume")
with open(CONTROL, "w") as f:
    json.dump({"skip": True}, f)
daemon.on_ended = _real_on_ended
daemon.consume_control(FakeRenderer(), DECKS, DATA)
check(read_ctl() == {}, "healthy skip round-trip leaves the file empty")

# ---- 5: the panel's RMW is one atomic step under the station lock ------
import panel

panel.CONTROL = CONTROL
panel.ROOT = tmp
# api_control under contention: a reader running between the panel's read
# and write must see either the old or the new dict, never a torn one.
stop = threading.Event()
torn = []


def hammer():
    while not stop.is_set():
        try:
            d = read_ctl()
            if not isinstance(d, dict):
                torn.append(d)
        except Exception as e:
            torn.append(str(e))


th = threading.Thread(target=hammer, daemon=True)
th.start()
for i in range(200):
    panel.api_control({"skip": bool(i % 2), "normalize": {"global": True}})
stop.set()
th.join(timeout=2)
check(not torn, "no torn reads across %d panel writes" % 200)
final = read_ctl()
check(final.get("normalize") == {"global": True},
      "panel normalize verb lands and persists")

print()
if fails:
    print("FAILED: %d" % len(fails))
    sys.exit(1)
print("ALL PASS")
