#!/usr/bin/env python3
"""Render scenes.json.template into an OBS scene collection.

Fills {{MEDIA}} {{OVERLAY}} {{FILES}}, stamps unique UUIDs, numbers scene items, and
validates internal consistency (unique names, every item resolves, no
placeholder survives, ticker docked at y=1004). This checks OUR work, not
OBS's acceptance — first load inside real OBS is still an explicit step.

  python3 station/render_scenes.py --check              # validate only
  python3 station/render_scenes.py [--root DIR]         # write broadcast/scenes/SMILE-Station.json
  python3 station/render_scenes.py --selftest           # offline proof
Env: BROADCAST_ROOT (default ./broadcast), OVERLAY_URL (default 127.0.0.1:7070).
"""

import argparse
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "scenes.json.template")
CANVAS_W, CANVAS_H, TICKER_H = 1920, 1080, 76


def render(media, overlay_url, assets=None, light=False, files_url=None):
    with open(TEMPLATE) as f:
        text = f.read().replace("{{MEDIA}}", media).replace("{{OVERLAY}}", overlay_url)
    if files_url is None:
        # Machine-independent media standard: collections reference clips as
        # http://<host>:7070/files/<name> (served by the overlay server with
        # ranges), never /home/... paths, so the same JSON airs anywhere the
        # bytes exist. Daemon-driven decks still take absolute local paths.
        files_url = overlay_url.rstrip("/") + "/files"
    text = text.replace("{{FILES}}", files_url)
    if assets is None:
        assets = os.path.join(os.path.dirname(media), "assets")
    text = text.replace("{{ASSETS}}", assets)
    assert "{{" not in text, "unfilled placeholder survives"
    col = json.loads(text)
    if light:
        # LAB ONLY (LAB_LIGHT=1): strip browser sources. The 2-core lab box
        # cannot feed 12 resident CEF mouths; mechanics (advance, routing,
        # watchdog) don't need them. VPS runs the full file. Never bake this
        # difference into the template — it is a render-time flag.
        dead = {s["name"] for s in col["sources"] if s["id"] == "browser_source"}
        col["sources"] = [s for s in col["sources"] if s["id"] != "browser_source"]
        for s in col["sources"]:
            items = s.get("settings", {}).get("items", [])
            s["settings"]["items"] = [i for i in items if i["name"] not in dead]
    resolve_media(col, media, assets)
    names = [s["name"] for s in col["sources"]]
    assert len(names) == len(set(names)), "duplicate source names"
    by_name = {s["name"]: s for s in col["sources"]}
    for s in col["sources"]:
        s.setdefault("uuid", str(uuid.uuid4()))
        for i, it in enumerate(s.get("settings", {}).get("items", [])):
            it.setdefault("id", i + 1)
            assert it["name"] in by_name, "%s references missing %s" % (s["name"], it["name"])
    for s in col["sources"]:
        items = s.get("settings", {}).get("items", [])
        if items:
            s["settings"]["id_counter"] = len(items)
    order = [e["name"] for e in col["scene_order"]]
    assert all(n in by_name for n in order), "scene_order names unknown source"
    assert col["current_program_scene"] in order, "program scene not in order"
    return col


def resolve_media(col, media, assets):
    """Point decks + ident at REAL files when they exist.

    Decks take the first two playlist items present on disk (broadcast
    playlist preferred, template fallback); IDENT takes the first ident
    present. Anything missing keeps its placeholder path on purpose: OBS
    shows its missing-file dialog, and the daemon skips missing items to
    TECHDIFF instead of dying. A placeholder in the rendered file therefore
    means 'intake has not delivered this yet', never 'config is broken'."""
    have = {f for f in os.listdir(media) if f.endswith(".mp4")} if os.path.isdir(media) else set()
    items = []
    for pl in (os.path.join(media, "playlist.json"), os.path.join(HERE, "playlist.json")):
        try:
            items = json.load(open(pl)).get("items", [])
            break
        except (OSError, ValueError):
            continue
    lined = [i["file"] for i in items if i.get("file") in have]
    idents = sorted(f for f in os.listdir(os.path.join(assets, "idents"))
                    if f.endswith(".mp4")) if os.path.isdir(os.path.join(assets, "idents")) else []
    by_name = {s["name"]: s for s in col["sources"]}
    for src, default in (("PLAYOUT_A", lined[:1]), ("PLAYOUT_B", lined[1:2])):
        if default:
            by_name[src]["settings"]["local_file"] = os.path.join(media, default[0])
    if idents:
        by_name["IDENT"]["settings"]["local_file"] = os.path.join(assets, "idents", idents[0])
    return col


def check(col):
    """Structural invariants of the station contract."""
    by_name = {s["name"]: s for s in col["sources"]}
    scenes = [s for s in col["sources"] if s["id"] == "scene"]
    assert len(scenes) == 6, "want exactly the 6 deck scenes, got %d" % len(scenes)
    decks = {s["name"] for s in scenes}
    assert decks == {"SMILE | Starting", "SMILE | Program", "SMILE | Q&A",
                     "SMILE | Tech Diffs", "SMILE | Off Air", "SMILE | End Credits"}, decks
    program_items = {i["name"] for i in by_name["SMILE | Program"]["settings"]["items"]}
    assert {"PLAYOUT_A", "PLAYOUT_B"} <= program_items
    if "ticker.html" in by_name:  # absent in LAB_LIGHT builds
        assert "ticker.html" in program_items
        for item in by_name["SMILE | Program"]["settings"]["items"]:
            if item["name"] == "ticker.html":
                assert item["pos"]["y"] == CANVAS_H - TICKER_H, "ticker off the dock"
                assert by_name["ticker.html"]["settings"]["height"] == TICKER_H
    live_items = {i["name"] for i in by_name["SMILE | Q&A"]["settings"]["items"]}
    assert {"Slot Cam", "Slot Screen"} <= live_items
    if "speaking.html" in by_name:
        assert "speaking.html" in live_items
    for url_src in ["OB Starting Page", "OB Speaking", "MOD Ticker"]:
        if url_src not in by_name:
            continue
        url = by_name[url_src]["settings"]["url"]
        assert url.startswith("http://127.0.0.1:"), "overlay URL must be localhost: %s" % url
    for fsrc in ["PLAYOUT_A", "PLAYOUT_B", "IDENT"]:
        assert by_name[fsrc]["settings"].get("is_local_file") is True, fsrc
    for srt in ["Slot Cam", "Slot Screen"]:
        assert by_name[srt]["settings"].get("is_local_file") is False, srt
        assert "streamid=read:" in by_name[srt]["settings"]["input"], srt + " must pull from the bus, never listen (bus owns :9000)"
    return True


def selftest():
    col = render("/tmp/media", "http://127.0.0.1:7070")
    assert check(col)
    light = render("/tmp/media", "http://127.0.0.1:7070", light=True)
    assert all(s["id"] != "browser_source" for s in light["sources"])
    assert check(light)
    print("render selftest: 6 scenes, deck wired, dock exact, localhost-only. OK.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--light", action="store_true",
                    help="lab-only: strip browser sources (see render())")
    ap.add_argument("--name", default="SMILE-Station",
                    help="collection name (SMILE-Lab for light builds)")
    ap.add_argument("--root", default=os.environ.get("BROADCAST_ROOT",
                                                     os.path.join(os.getcwd(), "broadcast")))
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    media = os.path.abspath(os.path.join(args.root, "media"))
    overlay = os.environ.get("OVERLAY_URL", "http://127.0.0.1:7070")
    col = render(media, overlay, light=args.light or bool(os.environ.get("LAB_LIGHT")))
    col["name"] = args.name  # OBS enumerates collections by internal name, not filename
    check(col)
    if args.check:
        print("template consistent.")
        return 0
    outdir = os.path.join(args.root, "scenes")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, args.name + ".json")
    tmp = out + ".new"
    with open(tmp, "w") as f:
        json.dump(col, f, indent=2)
    os.replace(tmp, out)
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
