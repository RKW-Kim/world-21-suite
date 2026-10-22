#!/usr/bin/env python3
"""The station watchdog must watch every piece, and its check must be
honest.

Two gaps, both found by reading the watchdog against the units it is
supposed to protect:

- NOTHING watched the bus. The programme output (OBS ->
  rtmp://.../monitor), the live-stream lane and the publish leg all run
  through MediaMTX; if it died the station looked alive and went dark
  downstream. It is now watched, and the revival is proven live.
- `--check` answered exit code 1 for a perfectly healthy station whose
  plane is masked on purpose. A check that always fails teaches the
  reader that the exit code means nothing.

Offline, stdlib only: systemctl and the sockets are faked.
"""
import io
import os
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import station_watchdog as wd  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def main():
    # 1. every unit the watchdog knows has a liveness check
    wd.daemon_alive = lambda: True
    wd.http_alive = lambda port, path, timeout=4: True
    wd.plane_alive = lambda: True
    wd.bus_alive = lambda: True
    for name in wd.USER_UNITS:
        check(wd.check_again(name),
              "the watchdog can tell whether %s is alive" % name)

    # 2. the bus is one of the pieces
    check("bus" in wd.USER_UNITS,
          "the bus is watched (units: %s)" % ", ".join(wd.USER_UNITS))

    # 3. a piece the watchdog does not know about is NOT reported alive
    #    (a missing branch would otherwise look like health)
    check(not wd.check_again("something-else"),
          "an unknown piece is not reported alive")

    # 4. --check: the exit code ignores a unit that is off on purpose
    wd.unit_disabled = lambda unit: unit == wd.USER_UNITS["plane"]
    wd.plane_alive = lambda: False
    # main() reads sys.argv for --check
    old_argv = sys.argv
    sys.argv = ["station_watchdog.py", "--check"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = wd.main()
    sys.argv = old_argv
    check(rc == 0,
          "--check answers 0 when the only dead piece is off on purpose (%s)"
          % rc)
    check("intentionally_off" in buf.getvalue(),
          "--check says which pieces are off on purpose")

    # 5. --check answers 1 when a piece that SHOULD be alive is dead
    wd.http_alive = lambda port, path, timeout=4: False
    sys.argv = ["station_watchdog.py", "--check"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = wd.main()
    sys.argv = old_argv
    check(rc == 1, "--check answers 1 when a real piece is dead (%s)" % rc)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
