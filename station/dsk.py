#!/usr/bin/env python3
"""Toggle the station's downstream keyers (watermark / ticker) on|off.

The control is the keyer's *scene selection* (exeldro downstream-keyer
plugin): selecting its scene shows the overlay on program, selecting ""
hides it. "tie" only defers changes until the next scene transition, so
the CLI never touches it.

  python3 station/dsk.py status
  python3 station/dsk.py watermark on|off
  python3 station/dsk.py ticker on|off
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

VENDOR = "downstream-keyer"


def _renderer():
    from daemon import OBSRenderer

    return OBSRenderer()


def _retry(fn):
    last = None
    for _ in range(5):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(15)
    raise last


def _vendor(request_type, **data):
    r = _renderer()
    return r._call("CallVendorRequest", {
        "vendorName": VENDOR, "requestType": request_type,
        "requestData": data})["responseData"]


def _keyers():
    return {k["name"]: k for k in
            _retry(lambda: _vendor("get_downstream_keyers")
                   .get("downstream_keyers", []))}


def _scene_of(k):
    p = k.get("scene")
    return p if p else ((k.get("scenes") or [{}])[0].get("name") or "")


def status():
    out = {name: {"on": bool(k.get("scene")),
                   "scene": k.get("scene") or None,
                   "tie": bool(k.get("tie"))}
           for name, k in _keyers().items()}
    # Say what actually governs the overlays, so nobody reads this as
    # the state of the watermark on air.
    out["_note"] = ("the daemon composites the watermark and the ticker "
                    "as nested scene items in PROGRAM; these keyers are "
                    "not in the loop")
    return out


def set_state(name, on):
    ks = _keyers()
    if name not in ks:
        sys.exit(f"unknown keyer {name!r} (have: {list(ks)})")
    target = _scene_of(ks[name]) if on else ""
    res = _retry(lambda: _vendor("dsk_select_scene",
                                 dsk_name=name, scene=target))
    if not res.get("success", True):
        sys.exit(f"select failed: {res}")
    # READ IT BACK. The plugin accepts dsk_select_scene and never
    # persists it (silent no-op, seen live 2026-10-19) -- so the old
    # version reported {"on": true} for a change that had not happened.
    # An operator who sees "on: true" expects the watermark on air.
    after = _retry(lambda: _keyers().get(name, {}))
    if bool(after.get("scene")) != bool(on):
        sys.exit(
            "the keyer accepted the request but did NOT persist it.\n"
            "That plugin's scene selection is a known no-op on this box, "
            "and the overlays on air are composited by the daemon as "
            "nested scene items -- so the watermark and the ticker are "
            "governed by the daemon, not by this keyer. Nothing changed.")
    return {"name": name, "on": bool(on), "scene": target or None}


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["status"]:
        print(json.dumps(status(), indent=2))
    elif len(args) == 2 and args[0] in ("watermark", "ticker"):
        print(json.dumps(set_state(args[0].capitalize(), args[1] == "on")))
    else:
        sys.exit(__doc__)
