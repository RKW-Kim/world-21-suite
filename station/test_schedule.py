#!/usr/bin/env python3
"""Scheduled profile switches.

A switch swaps the running order for a saved profile at a given local
time -- the "different profile for a different occasion" idea, on a
clock. The daemon applies it; the dock shows what is coming.

The guards matter more than the feature: a schedule must never blank
the station, never fire twice, and never apply a profile that is not
there.

Offline, stdlib only: the daemon module is imported against a temp
BROADCAST_ROOT, so nothing touches the live station.
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


def build_root():
    """A throwaway broadcast root: a playlist, a saved profile, a state."""
    root = tempfile.mkdtemp(prefix="w21-sched-")
    os.makedirs(os.path.join(root, "media", "playlists"))
    with open(os.path.join(root, "media", "playlist.json"), "w") as f:
        json.dump({"items": [{"title": "live item", "youtube": "u1"}],
                   "since_ad": 7}, f)
    with open(os.path.join(root, "media", "playlists", "morning.json"), "w") as f:
        json.dump({"items": [{"title": "morning one"}, {"title": "morning two"}]}, f)
    with open(os.path.join(root, "media", "playlists", "empty.json"), "w") as f:
        json.dump({"items": []}, f)
    with open(os.path.join(root, "state.json"), "w") as f:
        json.dump({"index": 3, "deck": "A"}, f)
    return root


def write_schedule(root, switches):
    with open(os.path.join(root, "schedule.json"), "w") as f:
        json.dump({"switches": switches}, f)


def read_playlist(root):
    with open(os.path.join(root, "media", "playlist.json")) as f:
        return json.load(f)


def read_state(root):
    with open(os.path.join(root, "state.json")) as f:
        return json.load(f)


def import_daemon(root):
    """Import the daemon module bound to a temp root."""
    os.environ["BROADCAST_ROOT"] = root
    for mod in ("daemon",):
        sys.modules.pop(mod, None)
    import daemon
    return daemon


def main():
    root = build_root()
    try:
        daemon = import_daemon(root)

        # --- the file is read, and a broken file is not fatal ----------
        write_schedule(root, [{"at": "06:00", "profile": "morning"}])
        sw = daemon.schedule_switches()
        check(len(sw) == 1 and sw[0]["profile"] == "morning",
              "the schedule file is read (%d switches)" % len(sw))

        with open(os.path.join(root, "schedule.json"), "w") as f:
            f.write("{not json")
        check(daemon.schedule_switches() == [],
              "a broken schedule file reads as no switches")
        os.remove(os.path.join(root, "schedule.json"))
        check(daemon.schedule_switches() == [],
              "a missing schedule file reads as no switches")

        # --- the next switch is computed ------------------------------
        write_schedule(root, [{"at": "06:00", "profile": "morning"},
                              {"at": "23:30", "profile": "morning"}])
        nxt = daemon.next_switch()
        check(nxt is not None, "the next switch is known")
        if nxt:
            check(nxt[1] == "morning", "the next switch names its profile")
            check(0 < nxt[2] <= 86400,
                  "the next switch is in the future (%ds)" % nxt[2])

        # --- the switch fires when its time comes ---------------------
        # a time one minute in the past: inside the firing window
        past = time.localtime(time.time() - 60)
        at = time.strftime("%H:%M", past)
        write_schedule(root, [{"at": at, "profile": "morning"}])
        state = daemon.load_state()
        daemon.check_schedule(state)
        pl = read_playlist(root)
        titles = [i.get("title") for i in pl["items"]]
        check(titles == ["morning one", "morning two"],
              "the switch applied the profile (%s)" % titles)
        check(pl.get("since_ad") == 0,
              "the ad cadence restarted with the new order")
        st = read_state(root)
        check(st.get("schedule_last"),
              "the applied switch is remembered in the state (%r)"
              % st.get("schedule_last"))

        # --- the replaced order is recoverable ------------------------
        keep = os.path.join(root, "media", "playlists", "before-switch.json")
        check(os.path.exists(keep),
              "the order the switch replaced is kept as a profile")
        if os.path.exists(keep):
            with open(keep) as f:
                kept = json.load(f)
            check([i.get("title") for i in kept.get("items", [])] ==
                  ["live item"],
                  "the kept profile holds the previous order")

        # --- it cannot fire twice -------------------------------------
        before = read_playlist(root)["items"]
        state = daemon.load_state()
        daemon.check_schedule(state)
        check(read_playlist(root)["items"] == before,
              "the same switch does not fire a second time")

        # --- a missing profile is refused ------------------------------
        write_schedule(root, [{"at": at, "profile": "nosuch"}])
        state = daemon.load_state()
        state.pop("schedule_last", None)
        daemon.check_schedule(state)
        check(read_playlist(root)["items"] == before,
              "a profile that is not there is refused")

        # --- an EMPTY profile is refused (it would blank the station) --
        write_schedule(root, [{"at": at, "profile": "empty"}])
        state = daemon.load_state()
        state.pop("schedule_last", None)
        daemon.check_schedule(state)
        check(read_playlist(root)["items"] == before,
              "an empty profile is refused")

        # --- a switch in the future does not fire ----------------------
        future = time.localtime(time.time() + 3600)
        write_schedule(root, [{"at": time.strftime("%H:%M", future),
                               "profile": "morning"}])
        state = daemon.load_state()
        state.pop("schedule_last", None)
        daemon.check_schedule(state)
        check(read_playlist(root)["items"] == before,
              "a switch that is not due yet does not fire")

        # --- the state survives the save (the marker is a state key) ---
        check("schedule_last" in daemon.STATE_KEYS,
              "schedule_last is a persisted state key")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
