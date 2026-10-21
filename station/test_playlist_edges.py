"""Adversarial edge tests for playlist/library behavior. Stdlib only.

Run from repo root:  python3 station/test_playlist_edges.py
Covers what the daemon selftest cannot: the overlay server's up-next scan
and index preservation, plus cross-layer promotion (remove -> same item
still plays next). Touches nothing outside a temp dir.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daemon
import overlay_server

tmp = tempfile.mkdtemp()
daemon.MEDIA = os.path.join(tmp, "media")
os.makedirs(daemon.MEDIA)
daemon.PLAYLIST = os.path.join(daemon.MEDIA, "playlist.json")
daemon.STATE = os.path.join(tmp, "state.json")
# The station's activity log is the operator's evidence trail: a
# test run must not write its alerts into the live database.
daemon.DB = os.path.join(tmp, "activity.db")
daemon.DB = os.path.join(tmp, "a.db")
daemon.ROOT = tmp

fails = []


def check(name, cond):
    print("%-42s %s" % (name, "ok" if cond else "FAIL"))
    if not cond:
        fails.append(name)


def wfile(name):
    open(os.path.join(daemon.MEDIA, name), "w").write("x")


# -- 1. adjust_index truth table -------------------------------------------
A = overlay_server.adjust_index
check("add before cursor shifts", A("add", 0, 0) == 1)
check("add after cursor steady", A("add", 5, 0) == 0)
check("add at cursor shifts", A("add", 2, 2) == 3)
check("remove before cursor shifts", A("remove", 0, 1) == 0)
check("remove at cursor promotes", A("remove", 1, 1) == 1)
check("remove after cursor steady", A("remove", 5, 1) == 1)
check("remove at zero floors", A("remove", 0, 0) == 0)
check("move across forward", A("move", 0, 1, 2) == 0)
check("move across backward", A("move", 2, 1, 0) == 2)
check("move outside steady", A("move", 0, 2, 1) == 2)
check("move noop steady", A("move", 1, 1, 1) == 1)

# -- 2. true up-next scan ---------------------------------------------------
wfile("a.mp4")
wfile("c.mp4")
daemon.save_playlist({"shuffle_on_complete": False, "items": [
    {"file": "a.mp4", "title": "A", "status": "dormant"},
    {"title": "B", "source": "http://example.invalid/b"},
    {"file": "c.mp4", "title": "C", "duration": 125}]})
daemon.save_state({"index": 0, "deck": "A", "faults": {}})
view = overlay_server.library_view()["items"]
check("dormant never up-next", view[0]["up_next"] is False)
check("pending never up-next", view[1]["up_next"] is False)
check("playable is up-next", view[2]["up_next"] is True)
check("duration exposed", view[2]["duration"] == 125)

# -- 3. remove promotes: same item still plays next -------------------------
wfile("ra.mp4")
wfile("rb.mp4")
wfile("rc.mp4")
daemon.save_playlist({"shuffle_on_complete": False, "items": [
    {"file": "ra.mp4", "title": "RA"},
    {"file": "rb.mp4", "title": "RB"},
    {"file": "rc.mp4", "title": "RC"}]})
daemon.save_state({"index": 1, "deck": "A", "faults": {}})
ni = overlay_server.adjust_index("remove", 0, 1)
check("remove-before shifts file index", ni == 0)
st = daemon.load_state()
st["index"] = ni
daemon.save_state(st)
items = [i for i in daemon.load_playlist()["items"] if i["file"] != "ra.mp4"]
daemon.save_playlist({"shuffle_on_complete": False, "items": items})
r = daemon.FakeRenderer()
daemon.advance(r, daemon.load_state(), daemon.load_playlist(),
               {"A": daemon.DECK_A, "B": daemon.DECK_B})
check("promoted item plays", ("file", daemon.DECK_B, os.path.join(daemon.MEDIA, "rb.mp4")) in r.calls)

# -- 4. pending skipped silently, play continues past -----------------------
daemon.save_playlist({"shuffle_on_complete": False, "items": [
    {"title": "P", "source": "http://example.invalid/p"},
    {"file": "rc.mp4", "title": "RC"}]})
st4 = {"index": 0, "deck": "A", "faults": {}}
r4 = daemon.FakeRenderer()
daemon.advance(r4, st4, daemon.load_playlist(),
               {"A": daemon.DECK_A, "B": daemon.DECK_B})
check("plays past pending", ("file", daemon.DECK_B, os.path.join(daemon.MEDIA, "rc.mp4")) in r4.calls)
check("index advances past pending", st4["index"] == 2)

# -- 5. degenerate views never crash ----------------------------------------
daemon.save_playlist({"shuffle_on_complete": False, "items": []})
check("empty view", overlay_server.library_view()["items"] == [])
daemon.save_playlist({"shuffle_on_complete": False, "items": [
    {"file": "ra.mp4", "title": "RA", "status": "dormant"}]})
check("all-dormant none up-next",
      all(not i["up_next"] for i in overlay_server.library_view()["items"]))

# -- 6. the seam rule must see stream items ---------------------------------
# The just-played item must never lead the next cycle. Stream items carry
# `youtube` (not `url`): a None key there used to drop them from the avoid
# set entirely, so the audience got the same video twice in a row.
import random
import shuffler

yt = {"title": "YT", "youtube": "https://youtu.be/seamTEST00"}
check("stream item has a key", shuffler.item_key(yt) is not None)
check("url item has a key",
      shuffler.item_key({"url": "https://x/v"}) is not None)
check("cycle last keys see youtube",
      shuffler.cycle_last_keys([yt, {"file": "a.mp4"}], count=2) ==
      [shuffler.item_key(yt), "a.mp4"])
pool = [yt] + [{"file": "s%d.mp4" % i, "title": str(i)} for i in range(6)]
for seed in range(200):
    random.seed(seed)
    out = shuffler.reshuffle([dict(i) for i in pool],
                             [shuffler.item_key(yt)])
    if shuffler.item_key(out[0]) == shuffler.item_key(yt):
        check("seam: just-played never leads (seed %d)" % seed, False)
        break
else:
    check("seam: just-played never leads (200 seeds)", True)

print("FAILURES: %s" % (fails or "none"))
sys.exit(1 if fails else 0)
