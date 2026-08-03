# Bridge: the ONE server. Serves overlays + dashboard, talks to OBS, holds state.
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse

from server.config import BRIDGE_HOST, BRIDGE_PORT, CORE_DIR, MOCK_MARKET
from server import mock_market
from server.hub import Hub, LIVE
from automation.layouts import LAYOUTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bridge")

hub = Hub()
SPEAK_THRESHOLD = -30.0

state = {
    "layout": "autotalk",
    "slots": LAYOUTS["autotalk"]["slots"],
    "mode": "manual",
    "scene": LIVE,
    "active_speaker": None,
    "strip": [],
    "participants": [
        {"name": "CAM " + str(i), "source": "CAM-" + str(i),
         "mic": "Mic/Aux" if i == 1 else "", "muted": False}
        for i in range(1, 6)
    ],
    "widgets": {"ticker": True, "chart": True, "alerts": True},
    "scenes": [],
    "diag": [],
    "canvas": {"w": 1920, "h": 1080},
    "obs_connected": False,
}

control_clients = set()
overlay_clients = set()


async def refresh_obs_info():
    if not hub.connected:
        return
    try:
        state["scenes"] = await asyncio.to_thread(hub.scenes)
        state["diag"] = await asyncio.to_thread(hub.items)
        state["canvas"] = await asyncio.to_thread(hub.canvas)
        state["scene"] = await asyncio.to_thread(hub.current_scene)
    except Exception as e:
        log.warning("refresh_obs_info: %s", e)


def _state_msg():
    state["obs_connected"] = hub.connected
    return json.dumps({"type": "state", **state})


async def broadcast_state():
    msg = _state_msg()
    for group in (control_clients, overlay_clients):
        for c in list(group):
            try:
                await c.send_text(msg)
            except Exception:
                group.discard(c)


async def autotalk_loop():
    while True:
        await asyncio.sleep(0.25)
        if state["mode"] != "auto" or not hub.connected:
            continue
        levels = {}
        for p in state["participants"]:
            if p["mic"]:
                try:
                    levels[p["source"]] = await asyncio.to_thread(hub.audio_level, p["mic"])
                except Exception:
                    levels[p["source"]] = -60.0
        speaking = [p for p in state["participants"] if levels.get(p["source"], -60.0) > SPEAK_THRESHOLD]
        if not speaking:
            continue
        loudest = max(speaking, key=lambda p: levels[p["source"]])
        if loudest["name"] != state["active_speaker"]:
            state["active_speaker"] = loudest["name"]
            state["strip"] = [p["name"] for p in speaking if p is not loudest][:4]
            await asyncio.to_thread(hub.feature_speaker, loudest["source"])
            await refresh_obs_info()
            await broadcast_state()


async def levels_loop():
    while True:
        await asyncio.sleep(0.4)
        if not hub.connected or not control_clients:
            continue
        levels = {}
        for p in state["participants"]:
            if p["mic"]:
                try:
                    levels[p["name"]] = await asyncio.to_thread(hub.audio_level, p["mic"])
                except Exception:
                    pass
        if levels:
            msg = json.dumps({"type": "levels", "levels": levels})
            for c in list(control_clients):
                try:
                    await c.send_text(msg)
                except Exception:
                    control_clients.discard(c)


async def obs_watchdog():
    while True:
        await asyncio.sleep(5)
        try:
            alive = await asyncio.to_thread(hub.ping) if hasattr(hub, "ping") else hub.connected
            if not alive:
                log.info("OBS connection lost - reconnecting")
                if await asyncio.to_thread(hub.connect):
                    await refresh_obs_info()
                    await broadcast_state()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app):
    if await asyncio.to_thread(hub.connect):
        await refresh_obs_info()
        try:
            await asyncio.to_thread(hub.apply_layout, state["layout"])
        except Exception as e:
            log.warning("initial apply_layout: %s", e)
    else:
        log.warning("OBS not reachable yet - watchdog will keep retrying")
    tasks = [asyncio.create_task(autotalk_loop()),
             asyncio.create_task(levels_loop()),
             asyncio.create_task(obs_watchdog())]
    await broadcast_state()
    yield
    for t in tasks:
        t.cancel()
    try:
        await asyncio.to_thread(hub.disconnect)
    except Exception:
        pass


app = FastAPI(title="smile-live-kit bridge", lifespan=lifespan)
app.mount("/core", StaticFiles(directory=str(CORE_DIR)), name="core")


async def handle_command(msg):
    cmd = msg.get("cmd")
    try:
        if cmd == "set_layout":
            layout = msg.get("layout")
            if layout in LAYOUTS:
                state["layout"] = layout
                state["slots"] = LAYOUTS[layout]["slots"]
                if hub.connected:
                    await asyncio.to_thread(hub.apply_layout, layout)
        elif cmd == "set_scene":
            if hub.connected:
                await asyncio.to_thread(hub.switch_scene, msg["scene"])
                state["scene"] = msg["scene"]
        elif cmd == "set_mode":
            state["mode"] = msg.get("mode")
        elif cmd == "set_speaker":
            part = next((p for p in state["participants"] if p["name"] == msg.get("name")), None)
            if part:
                state["mode"] = "manual"
                state["active_speaker"] = part["name"]
                state["strip"] = [p["name"] for p in state["participants"] if p["name"] != part["name"]][:4]
                if hub.connected:
                    await asyncio.to_thread(hub.feature_speaker, part["source"])
        elif cmd == "toggle_mute":
            part = next((p for p in state["participants"] if p["name"] == msg.get("name")), None)
            if part and part["mic"] and hub.connected:
                part["muted"] = not part["muted"]
                await asyncio.to_thread(hub.set_mute, part["mic"], part["muted"])
        elif cmd == "toggle_widget":
            key = msg.get("widget")
            if key in state["widgets"]:
                state["widgets"][key] = not state["widgets"][key]
                if hub.connected:
                    await asyncio.to_thread(hub.set_visible, key, state["widgets"][key])
        elif cmd == "fire_alert":
            await broadcast_alert(msg.get("kind", "alert"), msg.get("text", ""))
        elif cmd == "reconnect_obs":
            await asyncio.to_thread(hub.disconnect)
            if await asyncio.to_thread(hub.connect):
                await refresh_obs_info()
                try:
                    await asyncio.to_thread(hub.apply_layout, state["layout"])
                except Exception:
                    pass
    except Exception as e:
        log.error("command %s failed: %s", cmd, e)
    await refresh_obs_info()
    await broadcast_state()


async def broadcast_alert(kind, text):
    msg = json.dumps({"type": "alert", "kind": kind, "text": text})
    for c in list(overlay_clients):
        try:
            await c.send_text(msg)
        except Exception:
            overlay_clients.discard(c)


@app.websocket("/api/control")
async def control_ws(ws: WebSocket):
    await ws.accept()
    control_clients.add(ws)
    await refresh_obs_info()
    await ws.send_text(_state_msg())
    try:
        while True:
            await handle_command(json.loads(await ws.receive_text()))
    except WebSocketDisconnect:
        control_clients.discard(ws)


@app.websocket("/api/autotalk/state")
async def overlay_ws(ws: WebSocket):
    await ws.accept()
    overlay_clients.add(ws)
    await ws.send_text(_state_msg())
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        overlay_clients.discard(ws)


@app.get("/", response_class=HTMLResponse)
async def root():
    badge = '<span class="on">CONNECTED</span>' if hub.connected else '<span class="off">DISCONNECTED</span>'
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>smile-live-kit</title>
<style>
 body{background:#0a0f0d;color:#e8f1ec;font-family:'Segoe UI',monospace;margin:0;padding:40px}
 h1{font-size:22px;letter-spacing:.08em}
 .card{border:1px solid #1e2b25;border-radius:6px;padding:20px;max-width:560px;background:#101714;margin-top:16px}
 .row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141d18}
 .on{color:#3ddc84;font-weight:700}.off{color:#ff5c5c;font-weight:700}
 a{color:#5ad1e6;text-decoration:none;display:block;padding:8px 0}
 a:hover{color:#3ddc84}
 small{color:#7d918a}
</style></head><body>
<h1>SMILE LIVE KIT &mdash; bridge</h1>
<div class="card">
 <div class="row"><span>OBS</span>__OBS__</div>
 <div class="row"><span>Canvas</span><span>__CANVAS__</span></div>
 <div class="row"><span>Scene</span><span>__SCENE__</span></div>
 <div class="row"><span>Layout</span><span>__LAYOUT__</span></div>
</div>
<div class="card">
 <a href="/core/control.html">Command Centre (dashboard)</a>
 <a href="/core/03-live.html?layout=autotalk">Live overlay</a>
 <a href="/core/market-ticker.html">Market ticker</a>
 <a href="/health">Health (JSON)</a>
</div>
<small>Auto-refreshes every 3s</small>
<script>setTimeout(function(){location.reload()},3000)</script>
</body></html>"""
    html = html.replace("__OBS__", badge)
    html = html.replace("__CANVAS__", str(state["canvas"].get("w", 1920)) + "x" + str(state["canvas"].get("h", 1080)))
    html = html.replace("__SCENE__", state.get("scene", ""))
    html = html.replace("__LAYOUT__", state.get("layout", ""))
    return html


@app.get("/api/market/ticker")
async def market_ticker():
    if MOCK_MARKET:
        return JSONResponse(mock_market.tick())
    return JSONResponse({"error": "provider not configured"}, status_code=501)


@app.websocket("/api/market/ws")
async def market_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(mock_market.tick() if MOCK_MARKET else [])
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


@app.post("/api/autotalk/push")
async def autotalk_push(payload: dict):
    state["active_speaker"] = payload.get("main")
    state["strip"] = payload.get("strip", [])
    await broadcast_state()
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok", "obs_connected": hub.connected,
            "control_clients": len(control_clients), "overlay_clients": len(overlay_clients)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BRIDGE_HOST, port=BRIDGE_PORT)
