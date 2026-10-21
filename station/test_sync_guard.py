#!/usr/bin/env python3
"""sync.py apply must not create a duplicate scene from a stale capture.

The capture in git is a snapshot. If the live plane renamed a scene
("SMILE | Meet" -> "SMILE | Program"), applying the old capture CREATES
the old name as a second scene, orphans the live one, and leaves the
daemon -- which drives the LIVE name -- cutting to a scene with no deck
in it. The apply must refuse, loudly, before it touches OBS at all.

Offline, stdlib only: the guard runs before the first RPC, so this can
be proven without a plane.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import daemon          # noqa: E402
import sync            # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


REQUIRED = {daemon.SCENE_STARTING, daemon.SCENE_PROGRAM, daemon.SCENE_LIVE,
            daemon.SCENE_TECHDIFF, daemon.SCENE_OFFAIR, daemon.SCENE_END}


def write_config(root, scene_names):
    """A minimal config tree the apply can load."""
    os.makedirs(os.path.join(root, "config"), exist_ok=True)
    scenes = []
    for n in scene_names:
        scenes.append({"name": n, "items": []})
    col = {"inputs": [], "name": "test", "preview": "x", "program": "x",
           "scenes": scenes}
    for fn, obj in (("collection.json", col),
                    ("video.json", {"baseWidth": 1920, "baseHeight": 1080,
                                    "outputWidth": 960, "outputHeight": 540,
                                    "fpsNumerator": 30, "fpsDenominator": 1}),
                    ("service.json", {"type": "rtmp_custom",
                                      "settings": {"server": "rtmp://x/y",
                                                   "use_auth": False}}),
                    ("transition.json", {"name": "Fade", "duration": 300}),
                    ("encoder.json", {"streamEncoder.json": {}})):
        with open(os.path.join(root, "config", fn), "w") as f:
            json.dump(obj, f)


def main():
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "station")
    os.makedirs(root)

    # 1. a CURRENT capture passes the guard (it gets as far as the RPC,
    #    which we stub to fail loudly if reached).
    write_config(root, sorted(REQUIRED))
    reached = {"rpc": False}

    def boom(*a, **kw):
        reached["rpc"] = True
        raise AssertionError("the apply reached OBS before the guard")

    orig_rpc = sync.rpc
    sync.rpc = boom
    try:
        rc = sync.apply_all(os.path.join(root, "config"), False)
    except SystemExit:
        rc = 0
    except Exception as e:
        rc = "exception: %s" % e
    finally:
        sync.rpc = orig_rpc
    check(rc != 1,
          "a current capture is not refused by the skew guard (rc=%r)" % (rc,))

    # 2. a STALE capture (the plane renamed the programme scene) is
    #    REFUSED, and refused BEFORE any OBS call.
    stale = [n for n in sorted(REQUIRED) if n != daemon.SCENE_PROGRAM]
    stale.append("SMILE | Meet")
    write_config(root, stale)
    reached["rpc"] = False
    sync.rpc = boom
    try:
        rc = sync.apply_all(os.path.join(root, "config"), False)
    except SystemExit:
        rc = 0
    except Exception as e:
        rc = "exception: %s" % e
    finally:
        sync.rpc = orig_rpc
    check(rc == 1, "a stale capture is refused (rc=%r, expected 1)" % (rc,))
    check(not reached["rpc"],
          "the refusal happens BEFORE any OBS call (no scene was created)")

    # 3. the guard's message names the missing scene and the fix.
    out = []
    orig_print = print

    def cap(*a, **kw):
        out.append(" ".join(str(x) for x in a))

    import builtins
    builtins.print = cap
    try:
        sync.apply_all(os.path.join(root, "config"), False)
    except Exception:
        pass
    finally:
        builtins.print = orig_print
    text = "\n".join(out)
    check("stale" in text.lower(), "the refusal says the capture is stale")
    check("capture" in text.lower(), "the refusal says what to do about it")

    # 4. the diff ignores local_file (runtime state, like the eye state)
    #    but still reports a REAL difference.
    repo = {"collection.json": {
        "inputs": [{"name": "PLAYOUT_A", "kind": "ffmpeg_source",
                    "settings": {"local_file": "/media/a.mp4", "volume_db": 0.0},
                    "muted": False}],
        "scenes": [{"name": daemon.SCENE_PROGRAM,
                    "items": [{"source": "PLAYOUT_A", "visible": True}]}]}}
    live = {"collection.json": {
        "inputs": [{"name": "PLAYOUT_A", "kind": "ffmpeg_source",
                    "settings": {"local_file": "/media/b.mp4", "volume_db": 0.0},
                    "muted": False}],
        "scenes": [{"name": daemon.SCENE_PROGRAM,
                    "items": [{"source": "PLAYOUT_A", "visible": True}]}]}}
    orig_cap = sync.capture_to_memory
    sync.capture_to_memory = lambda: live
    try:
        problems = sync.diff_live(repo)
    finally:
        sync.capture_to_memory = orig_cap
    check(not any("local_file" in p for p in problems),
          "the diff does not report a media source's local_file")
    # a real difference must still be reported
    live["collection.json"]["scenes"][0]["items"][0]["source"] = "PLAYOUT_B"
    sync.capture_to_memory = lambda: live
    try:
        problems = sync.diff_live(repo)
    finally:
        sync.capture_to_memory = orig_cap
    check(any("PLAYOUT_B" in p for p in problems),
          "the diff still reports a real difference")

    shutil.rmtree(tmp, ignore_errors=True)
    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
