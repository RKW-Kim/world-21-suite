#!/usr/bin/env python3
"""Click a point on the headless render plane's Xvfb display (:99).

Used to dismiss modal OBS dialogs that block websocket startup when no human
is looking at the virtual screen — the safe-mode "Run in Normal Mode?" prompt
(500x142 at 700,429; Normal button ~= 1060,532) and the "already running"
singleton prompt (Cancel ~= 1135,532).

Faithful path: warp the virtual pointer, then XTest fake press/release, so Qt
receives the click exactly like a real one. Root-routed send_event does NOT
work (Qt ignores it); verified 2026-10-15.

  python3 station/obs_click.py 1060 532            # click one point
  python3 station/obs_click.py --list               # list top-level windows
  python3 station/obs_click.py --shot /tmp/x.png    # screenshot :99 to file

Requires: python-xlib (pip install python-xlib), ffmpeg for --shot.
"""
import subprocess
import sys
import time

DISPLAY = ":99"


def _display():
    from Xlib.display import Display

    return Display(DISPLAY)


def list_windows():
    d = _display()
    try:
        for c in d.screen().root.query_tree().children:
            try:
                g = c.get_geometry()
                print(f"{c.get_wm_name()!r} {g.width}x{g.height} at {g.x},{g.y}")
            except Exception as e:  # window vanished mid-query
                print(f"<gone> {e}")
    finally:
        d.close()


def click(x, y, settle=0.5):
    from Xlib import X
    from Xlib.ext import xtest

    d = _display()
    try:
        d.screen().root.warp_pointer(x, y)
        d.sync()
        time.sleep(settle)
        xtest.fake_input(d, X.ButtonPress, 1)
        d.sync()
        time.sleep(0.3)
        xtest.fake_input(d, X.ButtonRelease, 1)
        d.sync()
    finally:
        d.close()
    print(f"clicked {x},{y} on {DISPLAY}")


def shot(path, size="1280x800"):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "x11grab", "-video_size", size, "-i", DISPLAY,
         "-frames:v", "1", path],
        check=True,
    )
    print(f"screenshot -> {path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--list"]:
        list_windows()
    elif args[:1] == ["--shot"] and 2 <= len(args) <= 3:
        shot(args[1], args[2] if len(args) > 2 else "1280x800")
    elif len(args) == 2 and all(a.isdigit() for a in args):
        click(int(args[0]), int(args[1]))
    else:
        sys.exit("usage: obs_click.py X Y | --list | --shot PATH [SIZE]")
