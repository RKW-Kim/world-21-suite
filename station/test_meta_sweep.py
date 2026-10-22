#!/usr/bin/env python3
"""The metadata sweep must actually SWEEP.

Proved live: after days of running, 8 of 201 items had a description --
and they were the first eight. Two reasons, both fixed here:

1. cached_resolve() only cached a resolve that had BOTH HLS renditions,
   which is a LIVE STREAM. A VOD's metadata was therefore never cached,
   so every pass re-resolved the same rows from scratch.
2. The pass always started at the top of the playlist. With a half-hour
   cache TTL and a five-minute cycle, the frontier never moved: the pass
   re-resolved the first rows and never reached the rest.

Offline, stdlib only: yt-dlp is faked, the playlist lives in a temp dir.
"""
import json
import os
import shutil
import sys
import tempfile
import time

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
    root = tempfile.mkdtemp(prefix="w21-sweep-")
    try:
        os.environ["BROADCAST_ROOT"] = root
        for mod in ("daemon", "stream"):
            sys.modules.pop(mod, None)
        import daemon
        ytstream = daemon.ytstream          # the daemon imports stream as ytstream

        media = os.path.join(root, "media")
        os.makedirs(media)

        # A playlist of 10 VODs, none of them described yet.
        items = [{"youtube": "https://youtu.be/v%d" % i,
                  "title": "Video %d" % i} for i in range(10)]
        with open(os.path.join(media, "playlist.json"), "w") as f:
            json.dump({"items": items}, f)
        # No item is on air: the sweep skips the on-air row by design.
        with open(os.path.join(root, "state.json"), "w") as f:
            json.dump({"index": 99, "deck": "A"}, f)

        # A fake resolver: a VOD meta has NO hls urls at all.
        resolved = []

        def fake_resolve(url):
            resolved.append(url)
            return {"title": "Video %s" % url.rsplit("v", 1)[-1],
                    "duration": 100, "description": "desc " + url,
                    "channel": "chan", "live": False}

        ytstream.resolve = fake_resolve

        # 1. a VOD resolve must be CACHED (it has no hls_v/hls_a)
        daemon._RESOLVE_CACHE.clear()
        m = daemon.cached_resolve("https://youtu.be/v0")
        check(bool(m), "a VOD resolves")
        check("https://youtu.be/v0" in daemon._RESOLVE_CACHE,
              "a VOD's metadata is cached (it has no HLS renditions)")
        n_before = len(resolved)
        daemon.cached_resolve("https://youtu.be/v0")
        check(len(resolved) == n_before,
              "the second call is served from the cache (no re-resolve)")

        # 2. the sweep must ADVANCE, not restart at the top
        # The first pass of a day is the FULL sweep (limit 20), so it
        # covers the whole list and the cursor wraps to the top again.
        daemon._SWEEP_DAY = None
        daemon._RESOLVE_CACHE.clear()
        resolved.clear()
        daemon._title_watch_pass()
        check(bool(resolved), "the first pass resolves something")
        check(len(resolved) >= 10,
              "the daily pass sweeps the whole list (%d resolves)"
              % len(resolved))

        # The ordinary pass (limit 3) must continue where it stopped.
        daemon._SWEEP_DAY = time.strftime("%Y-%m-%d")   # already swept today
        daemon._RESOLVE_CACHE.clear()
        resolved.clear()
        daemon._title_watch_pass()
        first = list(resolved)
        check(len(first) == 3, "an ordinary pass resolves at most 3 (%d)"
              % len(first))
        pos1 = daemon._sweep_pos_get()
        check(pos1 == 3,
              "the pass leaves a cursor at the next unresolved row (pos=%s)"
              % pos1)

        resolved.clear()
        daemon._RESOLVE_CACHE.clear()
        daemon._title_watch_pass()
        second = list(resolved)
        check(bool(second), "the next pass resolves something")
        check(first[0] != second[0],
              "the next pass starts where the cursor is (%s -> %s)"
              % (first[0], second[0]))
        check(daemon._sweep_pos_get() == 6,
              "the cursor advances again (pos=%s)" % daemon._sweep_pos_get())

        # 3. the descriptions land in the playlist
        with open(os.path.join(media, "playlist.json")) as f:
            data = json.load(f)
        described = sum(1 for i in data["items"] if i.get("desc"))
        check(described > 0,
              "the pass captures the descriptions (%d of 10)" % described)
        checked = sum(1 for i in data["items"] if i.get("meta_checked"))
        check(checked > 0, "the pass stamps meta_checked (%d of 10)" % checked)

        # 4. the cursor survives a restart (a new process reads the file)
        pos_file = os.path.join(root, "sweep_pos.json")
        check(os.path.isfile(pos_file), "the cursor is written to disk")
        with open(pos_file) as f:
            check(isinstance(json.load(f).get("pos"), int),
                  "the cursor file holds a position")

        # 5. with a LIMIT of 3 fresh resolves, the whole list is reachable
        daemon._RESOLVE_CACHE.clear()
        resolved.clear()
        for _ in range(6):          # 6 passes x 3 = 18 > 10 items
            daemon._title_watch_pass()
        with open(os.path.join(media, "playlist.json")) as f:
            data = json.load(f)
        described = sum(1 for i in data["items"] if i.get("desc"))
        check(described == 10,
              "after enough passes EVERY item is described (%d of 10)"
              % described)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
