#!/usr/bin/env python3
"""The intake workdir sweep must not be fooled by a RECYCLED pid.

An intake writes its raw downloads into broadcast/media/.intake-tmp-<pid>.
If the process is killed, the workdir is garbage; the sweep reclaims it.
But a pid is REUSED: after weeks of uptime a fresh job can get the pid of
a dead one, and the sweep then saw a live pid and kept the dead
workdir -- for up to a day, because the age rule was the only other
escape. Worse, a fresh job with a recycled pid could ADOPT the stale
raws.

So the workdir names the process's START TIME as well as its pid, and
the sweep only trusts a pid whose start time still matches.

Offline, stdlib only.
"""
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import intake          # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def main():
    tmp = tempfile.mkdtemp()
    orig_media = intake.MEDIA
    intake.MEDIA = tmp
    try:
        pid = os.getpid()
        st = intake._proc_starttime(pid)
        check(st is not None, "the start time of this process is readable")

        # 1. a live pid with a MATCHING start time: our own workdir.
        mine = os.path.join(tmp, ".intake-tmp-%d-%d" % (pid, st))
        os.makedirs(mine)
        # 2. a live pid with a WRONG start time: a RECYCLED pid.
        recycled = os.path.join(tmp, ".intake-tmp-%d-%d" % (pid, (st or 1) + 999))
        os.makedirs(recycled)
        # 3. a dead pid.
        dead = os.path.join(tmp, ".intake-tmp-999999")
        os.makedirs(dead)
        # 4. an old workdir (a day old) whose pid happens to be alive.
        old = os.path.join(tmp, ".intake-tmp-%d-%d" % (pid, st))
        os.makedirs(old, exist_ok=True)
        ancient = os.path.join(tmp, ".intake-tmp-%d-%d" % (pid, st) + "-old")
        os.makedirs(ancient, exist_ok=True)
        t = time.time() - 90000
        os.utime(ancient, (t, t))

        intake._sweep_workdirs()

        check(os.path.isdir(mine),
              "a workdir of a LIVE process is kept")
        check(not os.path.isdir(recycled),
              "a workdir whose pid was RECYCLED is reclaimed")
        check(not os.path.isdir(dead),
              "a workdir of a dead process is reclaimed")
        check(not os.path.isdir(ancient),
              "a workdir older than a day is reclaimed")
    finally:
        intake.MEDIA = orig_media
        shutil.rmtree(tmp, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
