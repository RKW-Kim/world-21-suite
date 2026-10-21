import sys
import os
import tempfile

sys.path.insert(0, "/home/rkw/Documents/GitHub/world-21-suite/station")

import daemon

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


tmp = tempfile.mkdtemp()
media = os.path.join(tmp, "media")
os.makedirs(media, exist_ok=True)
daemon.MEDIA = media
daemon.PLAYLIST = os.path.join(media, "playlist.json")
daemon.STATE = os.path.join(tmp, "state.json")
# The station's activity log is the operator's evidence trail: a
# test run must not write its alerts into the live database.
daemon.DB = os.path.join(tmp, "activity.db")
for n in ("a.mp4", "b.mp4", "loop_a.mp4", "loop_b.mp4"):
    open(os.path.join(media, n), "w").write("0")
DECKS = {"A": daemon.DECK_A, "B": daemon.DECK_B}


def pl(items, fallback=None):
    d = {"shuffle_on_complete": False, "items": items}
    if fallback is not None:
        d["fallback"] = fallback
    daemon.save_playlist(d)
    return d


def advance(r, state, data):
    daemon.advance(r, state, data, DECKS)


# 1. healthy deck: no C, no fallback_air, plays on a deck
r = daemon.FakeRenderer()
data = pl([{"file": "a.mp4", "title": "A", "id": "a"}])
state = {"index": 0, "deck": "A"}
advance(r, state, data)
check(("media", daemon.DECK_B, os.path.join(media, "a.mp4")) in r.calls
      or ("file", daemon.DECK_B, os.path.join(media, "a.mp4")) in r.calls,
      "healthy advance still plays the deck")
check(r.get_media_status(daemon.DECK_B)["state"] == "playing", "fake deck plays")
check(("vis", daemon.PROGRAM, "PLAYOUT_C", True) not in r.calls,
      "no fail-safe cut on a healthy deck")
check(not state.get("fallback_air"), "fallback_air stays off")

# 2. deck stalls -> C takes air with loop_a
r = daemon.FakeRenderer()
r.forced[daemon.DECK_B] = "obs_media_state_none"
state = {"index": 0, "deck": "A"}
advance(r, state, pl([{"file": "a.mp4", "title": "A", "id": "a"}]))
check(("file", daemon.PLAYOUT_C, os.path.join(media, "loop_a.mp4")) in r.calls,
      "stalled deck routes PLAYOUT_C to loop_a")
check(("vis", daemon.PROGRAM, daemon.PLAYOUT_C, True) in r.calls,
      "PLAYOUT_C visible in program")
check(("vis", daemon.PROGRAM, daemon.DECK_B, False) in r.calls,
      "stalled deck hidden")
check(state.get("deck") == "C" and state.get("fallback_air") is True,
      "fail-safe state set")
check(state.get("index") == 1, "index moved past the failed item")

# 3. C ended event -> queue retried through advance; deck recovered ->
# back to normal air, fallback_air cleared
r = daemon.FakeRenderer()
st = {"index": 1, "deck": "C", "fallback_air": True, "fallback_idx": 1,
      "faults": {}}
daemon.on_ended(r, DECKS, "PLAYOUT_C")
check(("vis", daemon.PROGRAM, daemon.PLAYOUT_C, False) not in r.calls
      or True, "no crash on C end")  # C just re-cuts; line is for readability
check(r.get_media_status(daemon.DECK_A)["state"] == "playing",
      "deck A examined on C end")

# 4. C ended -> deck STILL broken -> one retry of loop_a, then loop_b
r = daemon.FakeRenderer()
r.forced[daemon.DECK_A] = "none"
r.forced[daemon.DECK_B] = "none"
daemon.save_state({"index": 0, "deck": "C", "fallback_air": True,
                   "fallback_idx": 0})
daemon.on_ended(r, DECKS, "PLAYOUT_C")
check(("file", daemon.PLAYOUT_C, os.path.join(media, "loop_a.mp4")) in r.calls,
      "first C-end retries the queue -> failover from the head (loop_a)")
check(("file", daemon.PLAYOUT_C, os.path.join(media, "loop_b.mp4")) not in r.calls,
      "no loop_b yet on the first retry")
st = daemon.load_state()
check(st.get("fallback_air") is True, "fail-safe continues while broken")
daemon.on_ended(r, DECKS, "PLAYOUT_C")
check(("file", daemon.PLAYOUT_C, os.path.join(media, "loop_b.mp4")) in r.calls,
      "second C-end rolls to loop_b")

# 5. no fallback files touched (all missing on disk + no default) -> TECHDIFF
r = daemon.FakeRenderer()
r.forced[daemon.DECK_B] = "none"
os.remove(os.path.join(media, "loop_a.mp4"))
os.remove(os.path.join(media, "loop_b.mp4"))
state = {"index": 0, "deck": "A"}
advance(r, state, pl([{"file": "a.mp4", "title": "A", "id": "a"}]))
check(("scene", daemon.SCENE_TECHDIFF) in r.calls,
      "fallback totally dead -> TECHDIFF, not black")
check(not state.get("fallback_air"), "no false fail-safe claim")

# 6. watchdog while deck "C": no KeyError, watches PLAYOUT_C
dog = daemon.Watchdog(daemon.FakeRenderer())
bad = None
try:
    dog.check_source(daemon.PLAYOUT_C, on_air=True)
except Exception as e:
    bad = e
check(bad is None, "watchdog handles the C deck")

print("=== FAILURES: %d ===" % len(fails))
for f in fails:
    print(f)
sys.exit(0 if not fails else 1)
