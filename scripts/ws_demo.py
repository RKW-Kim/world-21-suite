#!/usr/bin/env python3
"""
WebSocket system demo + alignment diagnostic.
Proves bridge <-> OBS <-> overlays communicate, shows what OBS WS can do,
and reports the real canvas size + every source's transform so we can fix alignment.

Run: py scripts/ws_demo.py
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from obswebsocket import obsws, requests
from server.config import OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD, BRIDGE_PORT
from automation.layouts import LAYOUTS, W, H

BRIDGE = f"http://127.0.0.1:{BRIDGE_PORT}"
LIVE = "03-live"
SCENES = ["01-starting-soon", "02-countdown", "03-live", "04-brb", "05-ending"]


def line(t=""):
    print(t)


def step(n, t):
    line()
    line(f"--- [{n}] {t} ---")


def main():
    line("============================================================")
    line("   smile-live-kit  -  WebSocket system demo + diagnostics")
    line("============================================================")

    if not OBS_WS_PASSWORD:
        line("ERROR: OBS_WS_PASSWORD not set in .env")
        return

    ws = obsws(OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD)
    ws.connect()
    line(f"Connected to OBS WebSocket @ {OBS_WS_HOST}:{OBS_WS_PORT}")

    # 1. READ: version
    step(1, "READ  GetVersion")
    v = ws.call(requests.GetVersion())
    line(f"  OBS Studio : {v.getObsVersion()}")
    line(f"  WS protocol: {v.getWebsocketVersion()}  (RPC {v.getRpcVersion()})")
    line("  -> we can query OBS metadata over WS")

    # 2. READ: canvas / video settings  (ALIGNMENT KEY)
    step(2, "READ  GetVideoSettings  (alignment baseline)")
    vs = ws.call(requests.GetVideoSettings())
    bw, bh = vs.getBaseWidth(), vs.getBaseHeight()
    ow, oh = vs.getOutputWidth(), vs.getOutputHeight()
    line(f"  Base canvas : {bw} x {bh}")
    line(f"  Output      : {ow} x {oh}")
    if (bw, bh) != (W, H):
        line(f"  !! MISMATCH: overlays are designed for {W}x{H}.")
        line(f"     OBS -> Settings -> Video -> Base Resolution -> {W}x{H}.")
    else:
        line(f"  OK canvas matches the {W}x{H} overlay design.")

    # 3. READ: scenes
    step(3, "READ  GetSceneList")
    sl = ws.call(requests.GetSceneList())
    line(f"  Current program scene: {sl.getCurrentProgramSceneName()}")
    existing = []
    for s in sl.getScenes():
        existing.append(s["sceneName"])
        line(f"   - {s['sceneName']}")

    def find_item(name):
        for it in ws.call(requests.GetSceneItemList(sceneName=LIVE)).getSceneItems():
            if it["sourceName"] == name:
                return it["sceneItemId"]
        return None

    have_live = LIVE in existing

    # 4. READ: live scene transforms  (ALIGNMENT KEY)
    if have_live:
        step(4, f"READ  GetSceneItemList('{LIVE}')  (per-source position/size)")
        items = ws.call(requests.GetSceneItemList(sceneName=LIVE)).getSceneItems()
        line(f"  {'source':<22}{'x':>7}{'y':>7}{'w':>7}{'h':>7}  vis")
        for it in items:
            tr = it.get("sceneItemTransform", {})
            px = tr.get("positionX", 0); pyy = tr.get("positionY", 0)
            sw = tr.get("sourceWidth", 0); sh = tr.get("sourceHeight", 0)
            bww = tr.get("boundsWidth", 0); bhh = tr.get("boundsHeight", 0)
            wshow = bww or sw; hshow = bhh or sh
            line(f"  {it['sourceName']:<22}{px:>7.0f}{pyy:>7.0f}{wshow:>7.0f}{hshow:>7.0f}  {it.get('sceneItemEnabled')}")
        line("  -> ground truth of where OBS has each layer")
    else:
        step(4, "SKIP  live scene not found - import the collection first")

    # 5. CONTROL: scene switching
    step(5, "CONTROL  SetCurrentProgramScene  (cycle scenes)")
    cycle = [s for s in SCENES if s in existing] or existing
    for sc in cycle:
        ws.call(requests.SetCurrentProgramScene(sceneName=sc))
        line(f"  switched -> {sc}")
        time.sleep(1.5)
    if have_live:
        ws.call(requests.SetCurrentProgramScene(sceneName=LIVE))
    line("  -> scene switching is fully scriptable over WS")

    if have_live:
        # 6. CONTROL: visibility
        step(6, "CONTROL  SetSceneItemEnabled  (blink alerts layer)")
        aid = find_item("alerts")
        if aid is not None:
            ws.call(requests.SetSceneItemEnabled(sceneName=LIVE, sceneItemId=aid, sceneItemEnabled=False))
            line("  alerts hidden"); time.sleep(1.0)
            ws.call(requests.SetSceneItemEnabled(sceneName=LIVE, sceneItemId=aid, sceneItemEnabled=True))
            line("  alerts shown")
        line("  -> any layer can be shown/hidden over WS")

        # 7. CONTROL: transforms (autotalk movement)
        step(7, "CONTROL  SetSceneItemTransform  (move CAM-1 across slots)")
        slots = LAYOUTS["autotalk"]["slots"]
        cid = find_item("CAM-1")
        if cid is not None:
            for s in slots:
                ws.call(requests.SetSceneItemTransform(
                    sceneName=LIVE, sceneItemId=cid,
                    sceneItemTransform={
                        "positionX": float(s["x"]), "positionY": float(s["y"]),
                        "boundsType": "OBS_BOUNDS_SCALE_INNER", "boundsAlignment": 5,
                        "boundsWidth": float(s["w"]), "boundsHeight": float(s["h"]),
                    }))
                line(f"  CAM-1 -> {s['name']} ({s['x']},{s['y']} {s['w']}x{s['h']})")
                time.sleep(1.2)
            m = slots[0]
            ws.call(requests.SetSceneItemTransform(
                sceneName=LIVE, sceneItemId=cid,
                sceneItemTransform={
                    "positionX": float(m["x"]), "positionY": float(m["y"]),
                    "boundsType": "OBS_BOUNDS_SCALE_INNER", "boundsAlignment": 5,
                    "boundsWidth": float(m["w"]), "boundsHeight": float(m["h"]),
                }))
            line("  CAM-1 restored -> main")
        line("  -> sources reposition/resize live over WS (this IS autotalk)")

    # 8. READ: audio telemetry
    step(8, "READ  GetInputAudioLevels  (live mic telemetry)")
    try:
        inputs = ws.call(requests.GetInputList()).getInputs()
        audio = [i for i in inputs if i.get("inputKind", "") in
                 ("wasapi_input_capture", "coreaudio_input_capture", "wasapi_output_capture")]
        if audio:
            nm = audio[0]["inputName"]
            lv = ws.call(requests.GetInputAudioLevels(inputName=nm)).getInputLevels()
            peak = lv[0][0] if (lv and lv[0]) else None
            line(f"  input '{nm}' peak={peak}")
            line("  -> live audio levels readable over WS (drives speaker detection)")
        else:
            line("  no audio input found (add a mic in OBS to see levels)")
    except Exception as e:
        line(f"  audio read failed: {e}")

    # 9. BRIDGE <-> OVERLAY
    step(9, "BRIDGE  POST /api/autotalk/push  (overlay highlight)")
    try:
        h = httpx.get(f"{BRIDGE}/health", timeout=2).json()
        line(f"  bridge health: {h}")
        for who in ["CAM 2", "CAM 3"]:
            httpx.post(f"{BRIDGE}/api/autotalk/push",
                       json={"main": who, "main_slot": "main", "strip": []}, timeout=2)
            line(f"  pushed active speaker = {who}  -> overlay frame glows")
            time.sleep(1.5)
        line("  -> bridge fans state out to overlay browser sources over WS")
    except Exception as e:
        line(f"  bridge not reachable ({e})")
        line(f"  start it: py -m uvicorn server.app:app --host 0.0.0.0 --port {BRIDGE_PORT}")

    step("OK", "Capabilities demonstrated")
    line("  READ   : version, canvas/video settings, scenes, scene items, audio levels")
    line("  CONTROL: switch scenes, show/hide sources, move/resize sources")
    line("  BRIDGE : push autotalk state -> overlay reacts (browser WS)")
    line()
    line("  Paste this output back. Section 2 (canvas) + Section 4 (source table)")
    line("  tell me exactly what to realign.")

    ws.disconnect()


if __name__ == "__main__":
    main()
