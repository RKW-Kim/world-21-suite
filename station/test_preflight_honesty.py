#!/usr/bin/env python3
"""The preflight must not claim it checked something it did not.

The preflight is the operator's first stop when something is wrong. It
used to print "scenes ok" whenever nothing failed -- including when it
ran without a plane, so it never asked OBS about the scenes at all. A
false all-clear sends the operator looking in the wrong place; that is
worse than an honest "not checked".

Offline, stdlib only: a temp BROADCAST_ROOT, no OBS, no network.
"""
import io
import os
import shutil
import sys
import tempfile
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def main():
    root = tempfile.mkdtemp(prefix="w21-preflight-")
    try:
        os.environ["BROADCAST_ROOT"] = root
        for mod in ("daemon", "preflight", "stream"):
            sys.modules.pop(mod, None)
        import daemon
        import preflight

        media = os.path.join(root, "media")
        os.makedirs(media)
        with open(os.path.join(media, "playlist.json"), "w") as f:
            f.write('{"items": [{"file": "a.mp4", "title": "A"}]}')
        with open(os.path.join(media, "a.mp4"), "w") as f:
            f.write("x")
        with open(os.path.join(root, "state.json"), "w") as f:
            f.write('{"index": 1, "deck": "A"}')

        def run(**kw):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                bad = preflight.run(**kw)
            return bad, buf.getvalue()

        # 1. no plane: the scenes were NOT checked, and it must say so
        # (the failure count is not asserted: the disk check depends on
        # the filesystem the temp dir lives on).
        bad, out = run(renderer=None)
        check("scenes ok" not in out,
              "without a plane it does not claim 'scenes ok'")
        check("NOT CHECKED" in out,
              "without a plane it says the scenes were not checked")

        # 2. the plane is off on purpose: skipped, not failed
        bad, out = run(renderer=None, plane_expected=False)
        check("on purpose" in out,
              "a deliberately-off plane says so")
        check("obs" not in out.lower().split("skip obs")[0].split("fail")[-1]
              or "FAIL obs" not in out,
              "a deliberately-off plane is not reported as an obs failure")

        # 3. a broken playlist IS a failure (the preflight's whole point)
        with open(os.path.join(media, "playlist.json"), "w") as f:
            f.write("not json at all")
        bad, out = run(renderer=None)
        check(bad > 0, "an unreadable playlist fails the preflight")
        check("FAIL" in out, "the failure is printed")

        # 4. a missing media file is a failure too
        with open(os.path.join(media, "playlist.json"), "w") as f:
            f.write('{"items": [{"file": "gone.mp4", "title": "G"}]}')
        bad, out = run(renderer=None)
        check(bad > 0, "a missing media file fails the preflight")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
