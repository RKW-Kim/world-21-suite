#!/usr/bin/env python3
"""Generate OBS 30+ Scene Collection. Back-to-front layering, optional test cards."""

import argparse
import json
import sys
import uuid as uuid_mod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from automation.layouts import LAYOUTS, W, H

BRIDGE_DEFAULT = "http://192.168.1.125:8787"
PREV_VER = 520093700
CX = float(W)
CY = float(H)
HUES = [210, 280, 150, 30, 340]

SCENES = [
    ("01-starting-soon", "01-starting-soon.html", False),
    ("02-countdown",     "02-countdown.html",     False),
    ("03-live",          "03-live.html?layout=autotalk", True),
    ("04-brb",           "04-brb.html",           False),
    ("05-ending",        "05-ending.html",        False),
]
DEFAULT_SCENE = "03-live"


def uid():
    return str(uuid_mod.uuid4())


def pos_rel(x, y):
    return {"x": (x - CX) / CY, "y": (y - CY) / CY}


def bounds_rel(bx, by):
    return {"x": bx / CX, "y": by / CY}


def _base(name, sid, vid, settings):
    return {
        "prev_ver": PREV_VER, "name": name, "uuid": uid(),
        "id": sid, "versioned_id": vid, "settings": settings,
        "mixers": 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5,
        "enabled": True, "muted": False,
        "push-to-mute": False, "push-to-mute-delay": 0,
        "push-to-talk": False, "push-to-talk-delay": 0,
        "hotkeys": {}, "deinterlace_mode": 0, "deinterlace_field_order": 0,
        "monitoring_type": 0, "private_settings": {},
    }


def browser(name, url, w, h):
    return _base(name, "browser_source", "browser_source", {
        "url": url, "width": w, "height": h,
        "css": "body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }",
        "shutdown": False, "restart_when_active": False, "refresh_no_cache": False,
    })


def camera(name, platform="windows"):
    kind = "dshow_input" if platform == "windows" else "av_capture_input"
    return _base(name, kind, kind, {})


def item(name, suuid, iid, x, y, bw, bh, btype=0, locked=False):
    return {
        "name": name, "source_uuid": suuid, "visible": True, "locked": locked,
        "rot": 0.0, "scale_ref": {"x": CX, "y": CY}, "align": 5,
        "bounds_type": btype, "bounds_align": 0, "bounds_crop": False,
        "crop_left": 0, "crop_top": 0, "crop_right": 0, "crop_bottom": 0,
        "id": iid, "group_item_backup": False,
        "pos": {"x": float(x), "y": float(y)},
        "pos_rel": pos_rel(float(x), float(y)),
        "scale": {"x": 1.0, "y": 1.0}, "scale_rel": {"x": 1.0, "y": 1.0},
        "bounds": {"x": float(bw), "y": float(bh)},
        "bounds_rel": bounds_rel(float(bw), float(bh)),
        "scale_filter": "disable", "blend_method": "default", "blend_type": "normal",
        "show_transition": {"duration": 0}, "hide_transition": {"duration": 0},
        "private_settings": {},
    }


def build(bridge, participants, test_cards, platform="windows"):
    sources = []

    ambient = browser("ambient", f"{bridge}/core/00-bg.html", W, H)
    ticker = browser("ticker", f"{bridge}/core/market-ticker.html", W, 76)
    alerts = browser("alerts", f"{bridge}/core/08-alerts.html", W, H)
    sources += [ambient, ticker, alerts]

    slots = LAYOUTS["autotalk"]["slots"]
    cams = []
    cam_btype = 0 if test_cards else 2
    for i in range(min(participants, len(slots))):
        s = slots[i]
        name = f"CAM-{i+1}"
        if test_cards:
            c = browser(name, f"{bridge}/core/test-cam.html?cam={i+1}&hue={HUES[i % len(HUES)]}", s["w"], s["h"])
        else:
            c = camera(name, platform)
        cams.append((c, s))
        sources.append(c)

    scene_names = []
    for scene_name, overlay_file, has_cams in SCENES:
        ov = browser(f"{scene_name}-overlay", f"{bridge}/core/{overlay_file}", W, H)
        sources.append(ov)

        items = []
        iid = 1
        # BACK -> FRONT (items[0] = bottom, last = top)
        items.append(item("ambient", ambient["uuid"], iid, 0, 0, 0, 0, 0, True)); iid += 1
        if has_cams:
            for c, s in cams:
                items.append(item(c["name"], c["uuid"], iid, s["x"], s["y"], s["w"], s["h"], cam_btype)); iid += 1
        items.append(item(f"{scene_name}-overlay", ov["uuid"], iid, 0, 0, 0, 0, 0, True)); iid += 1
        items.append(item("ticker", ticker["uuid"], iid, 0, H - 76, 0, 0, 0, True)); iid += 1
        items.append(item("alerts", alerts["uuid"], iid, 0, 0, 0, 0, 0, True)); iid += 1

        hotkeys = {"OBSBasic.SelectScene": []}
        for it in items:
            hotkeys[f"libobs.show_scene_item.{it['id']}"] = []
            hotkeys[f"libobs.hide_scene_item.{it['id']}"] = []

        scene_src = _base(scene_name, "scene", "scene",
                          {"id_counter": iid, "custom_size": False, "items": items})
        scene_src["hotkeys"] = hotkeys
        sources.append(scene_src)
        scene_names.append(scene_name)

    return {
        "current_scene": DEFAULT_SCENE,
        "current_program_scene": DEFAULT_SCENE,
        "scene_order": [{"name": n} for n in scene_names],
        "name": "Smile-Trading-Kit",
        "groups": [],
        "quick_transitions": [
            {"name": "Cut", "duration": 300, "hotkeys": [], "id": 1, "fade_to_black": False},
            {"name": "Fade", "duration": 300, "hotkeys": [], "id": 2, "fade_to_black": False},
            {"name": "Fade", "duration": 300, "hotkeys": [], "id": 3, "fade_to_black": True},
        ],
        "transitions": [],
        "saved_projectors": [],
        "current_transition": "Fade",
        "transition_duration": 300,
        "preview_locked": False,
        "scaling_enabled": False, "scaling_level": 0,
        "scaling_off_x": 0.0, "scaling_off_y": 0.0,
        "virtual-camera": {"type2": 3},
        "modules": {
            "scripts-tool": [],
            "output-timer": {
                "streamTimerHours": 0, "streamTimerMinutes": 0, "streamTimerSeconds": 30,
                "recordTimerHours": 0, "recordTimerMinutes": 0, "recordTimerSeconds": 30,
                "autoStartStreamTimer": False, "autoStartRecordTimer": False,
                "pauseRecordTimer": True,
            },
            "auto-scene-switcher": {
                "interval": 300, "non_matching_scene": "",
                "switch_if_not_matching": False, "active": False, "switches": [],
            },
        },
        "version": 2,
        "sources": sources,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bridge", default=BRIDGE_DEFAULT)
    p.add_argument("--participants", type=int, default=5)
    p.add_argument("--test-cards", action="store_true", help="Use fake camera cards instead of real captures")
    p.add_argument("--platform", choices=["mac", "windows"], default="windows", help="Camera source type")
    p.add_argument("--output", default="obs/Smile-Trading-Kit.json")
    a = p.parse_args()
    col = build(a.bridge, a.participants, a.test_cards, a.platform)
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(col, indent=4), encoding="utf-8")
    mode = "test-cards" if a.test_cards else "real-cameras"
    print(f"OK: {out} | scenes={len(col['scene_order'])} | sources={len(col['sources'])} | {mode}")


if __name__ == "__main__":
    main()
