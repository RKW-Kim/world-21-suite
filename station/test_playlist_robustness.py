#!/usr/bin/env python3
"""A malformed playlist must not stall the playout.

Proved by a battery of malformed rows: a row that is not an object
CRASHED advance() with AttributeError. The loop caught it, but the same
bad row was retried every pass, so the station sat on it forever. A
playlist row that names a PATH (not a media file) is refused too, so a
hand-edited playlist cannot point the renderer outside the media dir.

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


def main():
    tmp = tempfile.mkdtemp()
    media = os.path.join(tmp, "media")
    os.makedirs(media)
    open(os.path.join(media, "a.mp4"), "w").write("x")
    orig = (daemon.MEDIA, daemon.PLAYLIST, daemon.STATE, daemon.DB)
    daemon.MEDIA = media
    daemon.PLAYLIST = os.path.join(media, "playlist.json")
    daemon.STATE = os.path.join(tmp, "state.json")
    daemon.DB = os.path.join(tmp, "a.db")
    decks = {"A": daemon.DECK_A, "B": daemon.DECK_B}
    try:
        # 1. a row that is not an object: skipped, not fatal
        data = {"shuffle_on_complete": False,
                "items": ["not-a-dict", {"file": "a.mp4", "title": "A"}]}
        daemon.save_playlist(data)
        st = {"index": 0, "deck": "A", "faults": {}}
        daemon.advance(daemon.FakeRenderer(), st, data, decks)
        check(st.get("index") == 2,
              "a row that is not an object is skipped and the queue moves on "
              "(index=%r)" % st.get("index"))

        # 2. a file that is a PATH: refused
        data = {"shuffle_on_complete": False,
                "items": [{"file": "../../etc/passwd", "title": "A"},
                          {"file": "a.mp4", "title": "A"}]}
        daemon.save_playlist(data)
        st = {"index": 0, "deck": "A", "faults": {}}
        daemon.advance(daemon.FakeRenderer(), st, data, decks)
        check(st.get("index") == 2,
              "a file row that names a path is skipped (index=%r)" % st.get("index"))

        # 3. the shapes that already worked must keep working
        for name, item in (("a string duration", {"file": "a.mp4", "duration": "12"}),
                           ("a null duration", {"file": "a.mp4", "duration": None}),
                           ("a negative duration", {"file": "a.mp4", "duration": -5}),
                           ("a huge duration", {"file": "a.mp4", "duration": 10 ** 9}),
                           ("a dict title", {"file": "a.mp4", "title": {"x": 1}}),
                           ("an empty file name", {"file": "", "title": "A"}),
                           ("unicode", {"file": "a.mp4", "title": "🎵 Ünïcødé"}),
                           ("a duplicate row", {"file": "a.mp4", "title": "A"})):
            data = {"shuffle_on_complete": False, "items": [item]}
            daemon.save_playlist(data)
            st = {"index": 0, "deck": "A", "faults": {}}
            try:
                daemon.advance(daemon.FakeRenderer(), st, data, decks)
                check(st.get("index") == 1, "%s plays normally" % name)
            except Exception as e:
                check(False, "%s raised %s: %s" % (name, type(e).__name__, e))

        # 4. an absurd cursor must not crash the playout
        for idx in (-1, 0, 999, "x", None, 3.7):
            data = {"shuffle_on_complete": False,
                    "items": [{"file": "a.mp4", "title": "A"}]}
            daemon.save_playlist(data)
            st = {"index": idx, "deck": "A", "faults": {}}
            try:
                daemon.advance(daemon.FakeRenderer(), st, data, decks)
                check(True, "cursor %r plays" % (idx,))
            except Exception as e:
                check(False, "cursor %r raised %s: %s" % (idx, type(e).__name__, e))
    finally:
        daemon.MEDIA, daemon.PLAYLIST, daemon.STATE, daemon.DB = orig
        shutil.rmtree(tmp, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
