#!/usr/bin/env python3
"""The unit-render contract: what setup.sh writes into ~/.config/systemd/user.

setup.sh renders the installed units for THIS box (paths, secrets file,
media root, and the render-plane shape). The rendering is a pile of seds,
which is exactly the kind of thing that silently stops matching when a
unit is edited -- and a unit that loses its BROADCAST_ROOT looks fine
until it starts: ${BROADCAST_ROOT}/mediamtx.yml expands to
/mediamtx.yml, which does not exist, and the ingest bus never comes up.

This harness runs the REAL renderer (station/render_units.sh) for three
box shapes and asserts the result is a unit systemd can actually run.

Offline, stdlib only, no systemd calls.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
UNIT_SRC = os.path.join(HERE, "systemd")
RENDER = os.path.join(HERE, "render_units.sh")

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def render(dst, root, repo_path, shape):
    p = subprocess.run(["bash", RENDER, UNIT_SRC, dst, root, repo_path, shape],
                       capture_output=True, text=True, timeout=60)
    return p


def units_in(dst):
    return sorted(u for u in os.listdir(dst) if u.endswith(".service"))


def main():
    tmp = tempfile.mkdtemp()
    root = "/var/broadcast"          # a VPS-shaped install
    repo_path = "/srv/station"

    # ---- the three box shapes -----------------------------------------
    for shape, expect_99, expect_sw, expect_vnc in (
            ("lab", False, False, True),
            ("session-nogpu", False, True, True),
            ("headless", True, True, False)):
        dst = os.path.join(tmp, shape)
        os.makedirs(dst)
        p = render(dst, root, repo_path, shape)
        check(p.returncode == 0,
              "%s: the render succeeds (%s)" % (shape, p.stderr.strip()[:80]))
        if p.returncode != 0:
            continue

        us = units_in(dst)
        check(len(us) >= 6, "%s: the unit set is present (%d units)" % (shape, len(us)))

        # The render plane's stop must REAP the flatpak tree. OBS
        # ignores SIGTERM when it has no window manager, so a unit that
        # only sends SIGTERM leaves the plane holding :4455 -- the
        # daemon keeps talking to a plane the operator believes is off.
        with open(os.path.join(dst, "station-obs.service")) as f:
            obs_unit = f.read()
        check("pkill -9" in obs_unit and "obs-browser-page" in obs_unit,
              "%s: the plane's stop escalates to SIGKILL and reaps the "
              "browser pages" % shape)

        for name in us:
            with open(os.path.join(dst, name)) as f:
                text = f.read()

            # 1. every unit that EXPANDS a variable must define it.
            for var in set(re.findall(r"\$\{([A-Z_]+)\}", text)):
                check("Environment=%s=" % var in text,
                      "%s/%s defines %s (it expands ${%s})"
                      % (shape, name, var, var))

            # 2. the paths must point at THIS install.
            check("%s/Documents/GitHub/world-21-suite" % repo_path not in text,
                  "%s/%s has no hardcoded repo path" % (shape, name))
            check("/home/rkw/Documents/GitHub/world-21-suite" not in text,
                  "%s/%s has no machine-specific path" % (shape, name))

            # 3. the media root must be the same for every unit, AND it
            #    must be inside [Service] -- a line appended to the end of
            #    the file lands in [Install], where systemd ignores it.
            m = re.search(r"^Environment=BROADCAST_ROOT=(.*)$", text, re.M)
            check(m is not None and m.group(1).strip() == root,
                  "%s/%s uses BROADCAST_ROOT=%s" % (shape, name, root))
            service = text.split("[Service]", 1)[-1].split("[Install]", 1)[0] \
                if "[Service]" in text else ""
            check("Environment=BROADCAST_ROOT=" in service,
                  "%s/%s defines BROADCAST_ROOT inside [Service]" % (shape, name))

            # 4. the secrets file must be the one this install wrote.
            m = re.search(r"^EnvironmentFile=.*$", text, re.M)
            if m:
                check(m.group(0).endswith("/secrets.env"),
                      "%s/%s points at a secrets.env" % (shape, name))

        # 5. the render plane shape.
        obs = os.path.join(dst, "station-obs.service")
        if os.path.isfile(obs):
            with open(obs) as f:
                text = f.read()
            check(("--env=DISPLAY=:99" in text) == expect_99,
                  "%s: the plane display is %s" % (shape, ":99" if expect_99 else ":0"))
            check(("--env=LIBGL_ALWAYS_SOFTWARE=1" in text) == expect_sw,
                  "%s: software GL is %s" % (shape, "on" if expect_sw else "off"))

        # 6. the VNC unit only exists where there is a session to mirror.
        check(os.path.isfile(os.path.join(dst, "station-vnc.service")) == expect_vnc,
              "%s: the vnc unit is %s" % (shape, "installed" if expect_vnc else "skipped"))

        # 7. the unit that RUNS mediamtx must not point at the repo template.
        mtx = os.path.join(dst, "station-mediamtx.service")
        if os.path.isfile(mtx):
            with open(mtx) as f:
                text = f.read()
            check("station/mediamtx.yml" not in text,
                  "%s: the mediamtx unit does not run the repo TEMPLATE" % shape)
            check("mediamtx.yml" in text,
                  "%s: the mediamtx unit runs a rendered config" % shape)

    # 8. the committed render plane unit keeps the lab shape: the VPS
    #    shape is rendered at install time, never committed.
    with open(os.path.join(UNIT_SRC, "station-obs.service")) as f:
        text = f.read()
    check("Environment=DISPLAY=:0" in text,
          "the committed obs unit keeps the lab display (:0)")
    check("LIBGL_ALWAYS_SOFTWARE=1 com.obsproject.Studio" not in text,
          "the committed obs unit does not force software GL (the lab has a GPU)")

    # 9. the renderer must FAIL LOUD when its patterns stop matching.
    #    (A unit edit that renames the flags the render greps for would
    #    otherwise boot the wrong plane in silence.)
    broken = os.path.join(tmp, "broken")
    os.makedirs(broken)
    src = os.path.join(UNIT_SRC, "station-obs.service")
    with open(src) as f:
        text = f.read()
    text = text.replace("com.obsproject.Studio --verbose",
                        "com.obsproject.Studio --quiet")
    with open(os.path.join(broken, "station-obs.service"), "w") as f:
        f.write(text)
    p = subprocess.run(["bash", RENDER, broken, os.path.join(tmp, "broken-out"),
                        root, repo_path, "headless"],
                       capture_output=True, text=True, timeout=60)
    check(p.returncode != 0 and "render failed" in p.stderr,
          "the render fails loud when the unit text no longer matches")

    shutil.rmtree(tmp, ignore_errors=True)
    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
