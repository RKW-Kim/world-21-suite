"""The respawn left the playout pass: feed death is detected on the pass,
but resolve+spawn+ready-wait runs on a background thread. These checks pin
the contract: the pass never blocks on the slow parts, one attempt per deck
at a time, two attempts per item, a give-up routes EOF exactly once, and a
late finishing attempt never touches a deck the world moved on with (proc
identity, not deck key)."""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import daemon

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "media"), exist_ok=True)
# Full isolation: ROOT drives pl_lock's lock file too, not just STATE/DB.
daemon.ROOT = tmp
daemon.MEDIA = os.path.join(tmp, "media")
daemon.PLAYLIST = os.path.join(daemon.MEDIA, "playlist.json")
daemon.STATE = os.path.join(tmp, "state.json")
daemon.DB = os.path.join(tmp, "activity.db")
daemon.CONTROL = os.path.join(tmp, "control.json")

ALERTS = []
daemon.alert = lambda msg, level="WARN": ALERTS.append((level, msg))


class Proc:
    """Stands in for a feed process: poll() is all the respawn reads."""

    def __init__(self, alive=True):
        self._alive = alive

    def poll(self):
        return None if self._alive else 0


class FakeYTS:
    """Stands in for stream.py; every slow part is scriptable."""

    def __init__(self):
        self.resolve_sleep = 0.0
        self.resolve_result = None
        self.spawn_result = "ok"   # Proc, None, or "raise"
        self.ready = True
        self.stopped = []
        self.spawned_paths = []

    def resolve(self, url):
        if self.resolve_sleep:
            time.sleep(self.resolve_sleep)
        return self.resolve_result

    def spawn(self, url, path, meta=None):
        self.spawned_paths.append(path)
        if self.spawn_result == "raise":
            raise OSError("spawn boom")
        if self.spawn_result is None:
            return None
        return Proc()

    def path_ready(self, path):
        return self.ready

    def stop(self, proc):
        self.stopped.append(proc)

    def alive(self, proc):
        return proc is not None and proc.poll() is None


_fake = FakeYTS()
daemon.ytstream = _fake


def reset(url="u1", respawns=0, slot="A"):
    daemon._ENDED[:] = []
    daemon._STREAM_STATE["feeds"].clear()
    daemon._STREAM_STATE["respawning"].clear()
    daemon._RESOLVE_CACHE.clear()
    daemon._fake_stopped = None
    daemon.save_state({"index": 1, "deck": "A",
                       "stream": {"url": url, "slot": slot,
                                  "respawns": respawns,
                                  "start": time.time(), "dur": 600}})
    ALERTS[:] = []


def wait_attempt(deck, timeout=30):
    t = daemon._STREAM_STATE["respawning"].get(deck)
    if t is not None:
        t.join(timeout)
    return t


# 1. a dead network cannot freeze the pass: the resolve stays off it
_fake.resolve_sleep = 1.5
_fake.resolve_result = None          # resolve fails -> cache empty -> give up
reset(url="u1", respawns=0)
_sm = daemon.load_state()["stream"]
t0 = time.time()
daemon.stream_respawn_pass(_sm, "A")
dt = time.time() - t0
check(dt < 0.5, "death pass returned in %.2fs (resolve stayed off the pass)" % dt)
_t = daemon._STREAM_STATE["respawning"].get("A")
check(_t is not None and _t.is_alive(), "respawn thread kicked and running")
check(daemon.load_state()["stream"]["respawns"] == 1, "attempt persisted as 1")
check(any(m == "WARN" and "respawn 1 starting in background" in x
          for m, x in ALERTS), "the kick itself is on the record")
# in-flight guard: a second pass while the attempt lives is a no-op
daemon.stream_respawn_pass(_sm, "A")
check(daemon.load_state()["stream"]["respawns"] == 1, "no double-bump in flight")
check(sum(1 for _, x in ALERTS if "respawn 1 starting" in x) == 1,
      "one kick, one alert")
wait_attempt("A")
check(daemon.STREAM_EOF in daemon._ENDED, "failed attempt routed the give-up EOF")
check(daemon._ENDED.count(daemon.STREAM_EOF) == 1, "EOF exactly once")
check(any(m == "CRIT" for m, _ in ALERTS), "give-up said CRIT")

# 2. attempt 2 after a failed attempt 1; EOF still exactly once; then the
#    exhausted item routes no thread at all
_sm2 = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm2, "A")
wait_attempt("A")
check(daemon._ENDED.count(daemon.STREAM_EOF) == 1, "still exactly one EOF")
_sm3 = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm3, "A")
check(daemon._STREAM_STATE["respawning"].get("A") is None,
      "exhausted item kicks no thread")
check(daemon._ENDED.count(daemon.STREAM_EOF) == 1, "exhaustion adds no EOF")

# 3. success: fresh urls, spawn on the deck's MTX path, feed adopted
_fake.resolve_sleep = 0.0
_fake.resolve_result = {"url": "u1", "hls_v": "v", "hls_a": "a"}
_fake.spawn_result = "ok"
_fake.ready = True
reset(url="u1", respawns=0)
_sm = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm, "A")
wait_attempt("A")
check("slot-stream-a" in _fake.spawned_paths, "spawn targeted the deck's path")
check(daemon._STREAM_STATE["feeds"].get("A") is not None
      and daemon._STREAM_STATE["feeds"]["A"].poll() is None,
      "fresh feed adopted on the deck")
check(daemon.STREAM_EOF not in daemon._ENDED, "no EOF on success")
check(any(m == "WARN" and "respawned (1)" in x for m, x in ALERTS),
      "success alerted")
check(daemon._STREAM_STATE["respawning"].get("A") is None,
      "attempt marker reaped")

# 4. AD slot respawns on the ad path
reset(url="ad1", respawns=0, slot="AD")
daemon.save_state({"index": 1, "deck": "A", "in_ad_break": True,
                   "stream": {"url": "ad1", "slot": "AD", "respawns": 0,
                              "start": time.time(), "dur": 60}})
_sm = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm, "AD")
wait_attempt("AD")
check("slot-ad" in _fake.spawned_paths, "AD respawn targeted slot-ad")
check(daemon.load_state()["stream"]["respawns"] == 1, "AD attempt counted")

# 5. late finish: the item moved on during the ready-wait -> the feed is
#    stopped BY IDENTITY, no EOF, the deck entry not left behind
reset(url="u1", respawns=0)
_calls = {"n": 0}


def ready_world_moves(path):
    _calls["n"] += 1
    if _calls["n"] >= 2:
        # the operator skipped while the attempt was waiting
        daemon.save_state({"index": 2, "deck": "A", "stream": None})
        return True
    return False


_fake.path_ready = ready_world_moves
_sm = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm, "A")
wait_attempt("A")
del _fake.path_ready   # unshadow the class method
check(len(_fake.stopped) == 1, "late feed stopped (by identity)")
check(daemon._STREAM_STATE["feeds"].get("A") is None,
      "late feed left no deck entry")
check(daemon.STREAM_EOF not in daemon._ENDED, "late finish routes no EOF")
check(any(m == "INFO" and "finished late" in x for m, x in ALERTS),
      "late finish said so, quietly")

# 6. a crashed attempt still cleans up and still routes the give-up
reset(url="u1", respawns=0)


def ready_boom(path):
    raise RuntimeError("ready boom")


_fake.path_ready = ready_boom
_sm = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm, "A")
wait_attempt("A")
del _fake.path_ready
check(daemon.STREAM_EOF in daemon._ENDED, "crashed attempt routes the give-up")
check(daemon._STREAM_STATE["respawning"].get("A") is None,
      "crash reaps the marker (deck recovery cannot wedge)")

# 7. spawn refuses (no urls): give-up without a feed to clean
_fake.spawn_result = None
reset(url="u1", respawns=0)
_sm = daemon.load_state()["stream"]
daemon.stream_respawn_pass(_sm, "A")
wait_attempt("A")
check(daemon.STREAM_EOF in daemon._ENDED, "unspawnable meta routes the give-up")
check(daemon._STREAM_STATE["respawning"].get("A") is None, "marker reaped")

# 8. the stale-EOF hardening: an EOF drained with no stream on air is
#    ignored, not advanced (it would skip what the operator just cut to)
_fake.spawn_result = "ok"
r = daemon.FakeRenderer()
daemon.save_state({"index": 1, "deck": "A", "stream": None})
daemon._ENDED[:] = []
before = len(r.calls)
daemon.on_ended(r, {"A": daemon.DECK_A, "B": daemon.DECK_B},
                daemon.STREAM_EOF)
check(len(r.calls) == before, "stale EOF cut nothing")

# 9. a current EOF with a stream on air still advances (unchanged path):
#    the next item is a file, so the cut is a real media load and the
#    stream block clears
open(os.path.join(daemon.MEDIA, "b.mp4"), "w").write("0")
r = daemon.FakeRenderer()
daemon.save_playlist({"shuffle_on_complete": False, "items": [
    {"youtube": "https://youtu.be/x", "title": "X", "id": "x"},
    {"file": "b.mp4", "title": "B", "id": "b"}]})
daemon._RESOLVE_CACHE["https://youtu.be/x"] = (
    time.time(), {"url": "https://youtu.be/x", "hls_v": "v", "hls_a": "a",
                  "duration": 30})
daemon._STREAM_STATE["feeds"].clear()
daemon.save_state({"index": 1, "deck": "A",
                   "stream": {"url": "https://youtu.be/x", "slot": "A",
                              "respawns": 0, "start": time.time(),
                              "dur": 30}})
daemon.on_ended(r, {"A": daemon.DECK_A, "B": daemon.DECK_B},
                daemon.STREAM_EOF)
check(any(c[0] == "file" for c in r.calls), "a current EOF still advances")
check(daemon.load_state().get("stream") is None,
      "the file item that took air cleared the stream block")

print()
if fails:
    print("FAILURES: %d" % len(fails))
    for f in fails:
        print(" - %s" % f)
    sys.exit(1)
print("FAILURES: none")
