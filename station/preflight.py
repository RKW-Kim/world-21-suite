"""Boot preflight, adopted from obs-relay's playlist.validate_playlist().

Checks the benign-looking failures that only surface hours into a run:
missing media files, OBS scenes renamed under us (the SCENE_PROGRAM
Meet->Program drift), and disk pressure where the cache lives.

python3 station/preflight.py [--strict]   # WARN-only by default
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import daemon

DISK_MIN_GB = 5.0


def _err(tag, detail):
    print("FAIL %-10s %s" % (tag, detail))
    return 1


def run(renderer=None, plane_expected=True):
    """Check the station before it goes on air. Returns the number of
    failures. plane_expected=False means the render plane is switched off
    ON PURPOSE: the OBS checks are then SKIPPED, not failed -- crying
    CRIT at every boot for the operator's own choice teaches them to
    ignore the log."""
    bad = 0
    # A corrupt or missing playlist is the exact broken boot this tool
    # exists to diagnose -- the old bare load_playlist() crashed HERE,
    # on that boot, with a traceback instead of a finding.
    try:
        data = daemon.load_playlist()
        if not isinstance(data, dict) or not isinstance(
                data.get("items", []), list):
            # Valid JSON, wrong shape (a bare list, a string, items not a
            # list): the walk below would raise AttributeError -- the
            # same "traceback instead of a finding" the guard above
            # exists to prevent, one step later.
            raise ValueError("playlist is not the expected shape "
                             "(need {\"items\": [...]})")
    except (OSError, ValueError) as e:
        data = {}
        bad = _err("playlist", "unreadable (%s) -- the seed to restore is %s"
                   % (e, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "playlist.json")))
    try:
        state = daemon.load_state()
    except (OSError, ValueError) as e:
        state = {}
        bad = _err("state", "unreadable (%s) -- the daemon will rebuild it" % e)
    for it in data.get("items", []):
        f = it.get("file")
        if f and not os.path.exists(os.path.join(daemon.MEDIA, f)):
            bad = _err("media", "missing file %r (%s)" % (f, it.get("title", "")))
    # Scenes must exist in OBS by exact name (the Meet->Program rename cost
    # us a day of ghost re-kicks).
    scene_names = []
    if not plane_expected:
        # Said every time, not only on the PASS line: the disk check can
        # fail on a small filesystem, and the operator still needs to know
        # that the scenes were skipped ON PURPOSE.
        print("SKIP obs        the render plane is switched off on purpose")
    else:
        if renderer:
            try:
                scene_names = [s["sceneName"] for s in
                               renderer._call("GetSceneList")["scenes"]]
            except Exception:
                print("WARN obs        scene list unreadable (renderer down)")
                # Not a PASS: with no scene list the check below was
                # skipped entirely and the boot reported "scenes ok".
                bad = _err("obs", "scene list unreadable (renderer down)")
        if not renderer:
            # No plane to ask. Said here, not only on the PASS line: the
            # disk check can fail on a small filesystem, and the operator
            # still needs to know the scenes were not looked at.
            print("NOTE obs        the scenes were NOT CHECKED "
                  "(no plane; use --strict)")
        wanted = [getattr(daemon, a) for a in
                  ("SCENE_STARTING", "SCENE_PROGRAM", "SCENE_OFFAIR",
                   "SCENE_TECHDIFF", "SCENE_END", "SCENE_LIVE", "AD_SCENE")]
        for name in wanted:
            if scene_names and name not in scene_names:
                bad = _err("scenes", "OBS has no scene %r" % name)
    # Disk headroom under the cache root.
    try:
        free_gb = os.statvfs(daemon.ROOT).f_bavail * \
            os.statvfs(daemon.ROOT).f_frsize / 2**30
        if free_gb < DISK_MIN_GB:
            bad = _err("disk", "free %.1f GB < %s on %s"
                       % (free_gb, DISK_MIN_GB, daemon.ROOT))
    except OSError:
        print("WARN disk        statvfs failed on %s" % daemon.ROOT)
    if not bad:
        items = len(data.get("items", []))
        # Honest about what was checked. The preflight run without
        # --strict never talks to OBS, so it must not say "scenes ok":
        # the operator runs this when something is wrong, and a false
        # all-clear sends them looking in the wrong place.
        if scene_names:
            scene_note = "scenes ok"
        elif plane_expected:
            scene_note = "scenes NOT CHECKED (no plane; use --strict)"
        else:
            scene_note = "scenes not checked (the plane is off on purpose)"
        print("PASS preflight %d playlist item(s), %s, disk ok"
              % (items, scene_note))
    return bad


if __name__ == "__main__":
    renderer = None
    if "--strict" in sys.argv or "-s" in sys.argv:
        try:
            renderer = daemon.OBSRenderer()
        except Exception as e:
            print("renderer unreachable: %s" % e)
    # The default run honours the deliberate-off state: the operator
    # switched the plane off on purpose, so "the renderer is down" is
    # their choice, not a fault. --strict still checks it (they asked).
    sys.exit(run(renderer, plane_expected=bool(daemon.PLANE_AUTORESTART)))
