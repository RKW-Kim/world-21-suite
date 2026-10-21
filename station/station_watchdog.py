#!/usr/bin/env python3
"""Station watchdog: is the station still alive, and can we revive it?

The daemon watches the RENDER PLANE; nothing watched the daemon, the
panel or the overlay server. A daemon that dies silently leaves a station
that looks fine and airs nothing.

This script checks each piece, restarts what is dead, and only raises an
alarm when a restart did not bring it back. It is deliberately boring:
one pass, no daemon of its own, run from a systemd timer.

Usage:
    python3 station/station_watchdog.py            # one pass
    python3 station/station_watchdog.py --check    # report only, change nothing
"""
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BROADCAST = os.environ.get("BROADCAST_ROOT", os.path.join(ROOT, "broadcast"))
HEARTBEAT = os.path.join(BROADCAST, "heartbeat.json")
ACTIVITY = os.path.join(BROADCAST, "activity.db")
SECRETS = os.path.join(BROADCAST, "secrets.env")

# How long each piece may be silent before it counts as dead.
DEAD_AGE = {"daemon": 45.0, "panel": 20.0, "overlay": 20.0, "plane": 90.0}
USER_UNITS = {"daemon": "station-daemon.service",
              "panel": "station-panel.service",
              "overlay": "station-overlay.service",
              "plane": "station-obs.service"}
# A sync.py apply --restart parks the watchdog by dropping this file while
# it stops the daemon, merges the collection and brings units back. A STALE
# park (an apply that died mid-flight) expires: after PARK_TTL the watchdog
# resumes, which is exactly the self-heal an aborted apply needs.
PARK_FILE = os.path.join(BROADCAST, ".watchdog-park")
PARK_TTL = 900.0


def _systemctl(*args, timeout=60):
    """systemctl in the scope the installer used: root installs run SYSTEM
    units, everything else --user. The old hardcoded --user silently
    no-opped on a root install (the command "succeeded" against units that
    were not the station's). Returns (rc, combined output) so callers can
    surface WHY a revive failed instead of pretending it worked."""
    cmd = ["systemctl"]
    if os.geteuid() != 0:
        cmd.append("--user")
    cmd += list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stderr.strip() or p.stdout.strip())
    except Exception as e:
        return 124, str(e)


def parked():
    """True while a sync.py apply owns the station (fresh park file)."""
    try:
        age = time.time() - os.path.getmtime(PARK_FILE)
        # Negative age = mtime in the future. A clock stepped back (NTP
        # correction, VM resume) used to fence the watchdog until wall
        # time crawled past mtime+TTL — hours. A small slack absorbs
        # second-scale jitter between apply's write and this read.
        if -30.0 <= age < PARK_TTL:
            return True
        os.remove(PARK_FILE)   # stale (expired, or from the future)
    except OSError:
        pass
    return False


def load_secrets():
    if not os.path.exists(SECRETS):
        return
    try:
        with open(SECRETS) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip('"').strip("'"))
    except OSError:
        pass


def log(msg, level="INFO"):
    row = (time.strftime("%Y-%m-%d %H:%M:%S"), level, msg)
    try:
        import sqlite3
        con = sqlite3.connect(ACTIVITY, timeout=5)
        try:
            con.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        con.execute("CREATE TABLE IF NOT EXISTS activity_log(ts TEXT, level TEXT, msg TEXT)")
        con.execute("INSERT INTO activity_log VALUES (?,?,?)", row)
        con.commit()
        con.close()
    except Exception:
        pass
    print("[%s] %s" % (level, msg), flush=True)
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        return
    emoji = {"CRIT": "\U0001f534", "WARN": "\U0001f7e1", "INFO": "\U0001f535"}.get(level, "\U0001f535")
    try:
        import urllib.request
        urllib.request.urlopen(urllib.request.Request(
            hook, data=json.dumps({"username": "station",
                                    "content": "%s **[%s]** %s" % (emoji, level, msg)}).encode(),
            headers={"Content-Type": "application/json"}), timeout=10).close()
    except Exception:
        pass


def daemon_age():
    """Seconds since the daemon last ticked, or None if we cannot tell."""
    try:
        with open(HEARTBEAT) as f:
            hb = json.load(f)
        t = hb.get("t")
        if isinstance(t, (int, float)):
            return max(0.0, time.time() - t)
    except Exception:
        pass
    return None


def http_alive(port, path, timeout=4):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout) as s:
            s.sendall(("GET %s HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n" % path).encode())
            s.settimeout(timeout)
            head = s.recv(64)
            return head.startswith(b"HTTP/")
    except OSError:
        return False


def plane_alive():
    """The obs-websocket answers an HTTP upgrade with 426: that is the
    cheapest proof that the render plane is up (a websocket handshake
    from outside hangs, as we learned the hard way)."""
    try:
        with socket.create_connection(("127.0.0.1", 4455), 4) as s:
            s.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1:4455\r\nUpgrade: websocket\r\n"
                      b"Connection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                      b"Sec-WebSocket-Version: 13\r\n\r\n")
            s.settimeout(4)
            head = s.recv(128)
            return b"426" in head or b"101" in head
    except OSError:
        return False


def unit_active(unit):
    """active, or on its way up (systemd's Restart=always spends a moment
    in "activating" — that is NOT a dead unit)."""
    rc, out = _systemctl("is-active", unit, timeout=10)
    return rc == 0 and out in ("active", "activating", "reloading")


def unit_disabled(unit):
    """The operator switched this unit off on purpose. A disabled unit is
    not a fault: the watchdog must not start it (that is how you keep the
    OBS window off your desktop)."""
    rc, out = _systemctl("is-enabled", unit, timeout=10)
    return out in ("disabled", "masked", "static")


def daemon_alive():
    """The daemon is alive only if the UNIT is running AND it is still
    ticking. A stopped daemon leaves a fresh heartbeat behind for a
    while, so the unit state is the stronger signal."""
    if not unit_active(USER_UNITS["daemon"]):
        return False
    age = daemon_age()
    return age is not None and age < DEAD_AGE["daemon"]


def restart(unit):
    rc, out = _systemctl("restart", unit)
    return rc == 0, out


def check_piece(name, alive):
    unit = USER_UNITS[name]
    if unit_disabled(unit):
        log("Watchdog: %s is switched off on purpose — leaving it off." % unit, "INFO")
        return True
    if alive:
        return True
    if not unit_active(unit):
        # Not running: start it (a stopped unit needs start, not restart).
        rc, out = _systemctl("start", unit)
        if rc != 0:
            log("Watchdog: start %s failed (rc=%d): %s" % (unit, rc, out[:200]), "CRIT")
    else:
        rc, out = restart(unit)
        if not rc:
            log("Watchdog: restart %s failed (rc=%d): %s" % (unit, rc, out[:200]), "CRIT")
    time.sleep(6)
    ok = check_again(name)
    if ok:
        log("Watchdog: %s was dead, %s restarted and is back." % (name, unit), "WARN")
    else:
        log("Watchdog: %s is dead and the restart of %s did NOT bring it "
            "back. The station needs a human." % (name, unit), "CRIT")
    return ok


def check_again(name):
    if name == "daemon":
        return daemon_alive()
    if name == "panel":
        return http_alive(8220, "/api/ping")
    if name == "overlay":
        return http_alive(7070, "/state")
    if name == "plane":
        return plane_alive()
    return False


def main():
    check_only = "--check" in sys.argv
    load_secrets()
    age = daemon_age()
    states = {
        "daemon": daemon_alive(),
        "panel": http_alive(8220, "/api/ping"),
        "overlay": http_alive(7070, "/state"),
        "plane": plane_alive(),
    }
    if check_only:
        off = [k for k, u in USER_UNITS.items() if unit_disabled(u)]
        print(json.dumps({"daemon_age": age, "parked": parked(),
                          "intentionally_off": off, **states}, indent=2))
        return 0 if all(states.values()) else 1
    if parked():
        # A sync.py apply --restart is mid-flight: units are stopped BY
        # DESIGN and reviving them would start the daemon under the merge.
        log("Watchdog: parked (sync apply in progress) — not reviving.", "INFO")
        return 0
    # A unit that is switched off on purpose is not "not answering" -- it
    # is off. Alerting on it every cycle filled the operator's log with
    # rows that meant nothing.
    off = [k for k, u in USER_UNITS.items() if unit_disabled(u)]
    bad = [k for k, v in states.items() if not v and k not in off]
    if not bad:
        return 0
    log("Watchdog: %s not answering. Reviving." % ", ".join(bad), "WARN")
    failed = [k for k in bad if not check_piece(k, False)]
    if failed:
        log("Watchdog: could not revive %s. The station is degraded." % ", ".join(failed), "CRIT")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
