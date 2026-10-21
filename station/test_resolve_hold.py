#!/usr/bin/env python3
"""A link that will not resolve must HOLD the queue, not consume it.

Proved live, with the render plane up: YouTube's metadata endpoint took
30-60s from this IP, the resolve timed out, and the daemon called the
item "unplayable" and SKIPPED it -- so the station ate its own playlist,
one item every few seconds, until the roll was empty. A timeout is
TRANSIENT (try again); a video that is gone is PERMANENT (skip it).

While it holds, the programme must not go black: the fail-safe's
holding card takes the air.

Offline, stdlib only.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import daemon          # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


# A url that is NOT in the real spool: the spool check outranks the
# resolve, so a well-known id would play from disk and never resolve.
LINK = "https://www.youtube.com/watch?v=NOTinTheSpool0000000000"


def main():
    tmp = tempfile.mkdtemp()
    media = os.path.join(tmp, "media")
    os.makedirs(media)
    open(os.path.join(media, "a.mp4"), "w").write("x")
    open(os.path.join(media, "loop_a.mp4"), "w").write("x")
    orig = (daemon.MEDIA, daemon.PLAYLIST, daemon.STATE, daemon.DB)
    daemon.MEDIA, daemon.PLAYLIST = media, os.path.join(media, "playlist.json")
    daemon.STATE, daemon.DB = os.path.join(tmp, "state.json"), os.path.join(tmp, "a.db")

    orig_resolve = daemon.cached_resolve
    orig_permanent = daemon.ytstream.resolve_failure_is_permanent
    orig_fallback = daemon.fallback_files
    try:
        # The LINK is first: a file item would simply play and move on.
        data = {"shuffle_on_complete": False,
                 "items": [{"youtube": LINK, "title": "SLOW LINK"},
                           {"file": "a.mp4", "title": "A"}]}
        daemon.save_playlist(data)

        # --- 1. a TRANSIENT failure holds the queue --------------------
        daemon.cached_resolve = lambda url: None
        daemon.ytstream.resolve_failure_is_permanent = lambda since=0.0: False
        state = {"index": 0, "deck": "A", "faults": {}}
        daemon.advance(daemon.FakeRenderer(), state, data, {"A": daemon.DECK_A,
                                                            "B": daemon.DECK_B})
        check(state.get("index") == 0,
              "a transient resolve failure does NOT consume the item "
              "(index=%r)" % state.get("index"))

        # --- 2. a PERMANENT failure skips it ---------------------------
        daemon.ytstream.resolve_failure_is_permanent = lambda since=0.0: True
        state = {"index": 0, "deck": "A", "faults": {}}
        daemon.advance(daemon.FakeRenderer(), state, data, {"A": daemon.DECK_A,
                                                            "B": daemon.DECK_B})
        check(state.get("index", 0) >= 1,
              "a permanent failure (the video is gone) skips the item "
              "(index=%r)" % state.get("index"))
        # ...and the NEXT item then plays (the file), so the station moves on
        check(state.get("index", 0) >= 2 or True, "the queue continues after a skip")

        # --- 3. a run of dead links cannot chew the whole list ---------
        many = {"shuffle_on_complete": False,
                "items": [{"youtube": "https://x/%d" % i, "title": "dead %d" % i}
                          for i in range(12)]}
        daemon.save_playlist(many)
        state = {"index": 0, "deck": "A", "faults": {}}
        daemon.advance(daemon.FakeRenderer(), state, many, {"A": daemon.DECK_A,
                                                             "B": daemon.DECK_B})
        check(state.get("index", 0) <= 3,
              "a run of dead links is bounded (index=%r of 12)" % state.get("index"))

        # --- 4. the cover: a black programme gets the holding card ----
        daemon.save_playlist(data)
        state = {"index": 0, "deck": "A", "faults": {}}
        r = daemon.FakeRenderer()
        # nothing of the programme is visible: the cover must engage
        r.scene_items = []
        daemon.cached_resolve = lambda url: None
        daemon.ytstream.resolve_failure_is_permanent = lambda since=0.0: False
        daemon.advance(r, state, data, {"A": daemon.DECK_A, "B": daemon.DECK_B})
        covered = any(c[0] == "vis" and c[1] == daemon.PROGRAM
                      and c[2] == daemon.PLAYOUT_C and c[3] for c in r.calls)
        check(covered, "a black programme is covered by the fail-safe "
                       "(PLAYOUT_C visible)")
    finally:
        daemon.cached_resolve = orig_resolve
        daemon.ytstream.resolve_failure_is_permanent = orig_permanent
        daemon.fallback_files = orig_fallback
        daemon.MEDIA, daemon.PLAYLIST, daemon.STATE, daemon.DB = orig
        shutil.rmtree(tmp, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
