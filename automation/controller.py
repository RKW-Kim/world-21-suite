"""OBS scene/source management via obs-websocket-py (v5, keyword-arg API)."""

from __future__ import annotations
import logging
from dataclasses import dataclass, field

from obswebsocket import obsws, requests

from server.config import OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD, STREAM_WIDTH, STREAM_HEIGHT
from automation.layouts import LAYOUTS

log = logging.getLogger(__name__)

CAMERA_KIND = {"windows": "dshow_input", "mac": "av_capture_input"}


@dataclass
class Participant:
    name: str
    cam_source: str
    mic_source: str
    has_video: bool = True
    pinned: bool = False


@dataclass
class SceneConfig:
    name: str
    layout: str
    participants: list[Participant] = field(default_factory=list)
    overlay_url: str = ""
    ticker_url: str = ""
    alerts_url: str = ""
    platform: str = "windows"


class OBSController:
    def __init__(self):
        self._ws: obsws | None = None

    def connect(self) -> None:
        if not OBS_WS_PASSWORD:
            raise RuntimeError("OBS_WS_PASSWORD not set in .env")
        self._ws = obsws(OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD)
        self._ws.connect()
        log.info("Connected to OBS WebSocket at %s:%s", OBS_WS_HOST, OBS_WS_PORT)

    def disconnect(self) -> None:
        if self._ws:
            self._ws.disconnect()
            self._ws = None

    @property
    def ws(self) -> obsws:
        if not self._ws:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._ws

    def create_scene(self, name: str) -> None:
        existing = self.ws.call(requests.GetSceneList()).getScenes()
        if any(s["sceneName"] == name for s in existing):
            log.info("Scene '%s' exists, skipping.", name)
            return
        self.ws.call(requests.CreateScene(sceneName=name))
        log.info("Created scene '%s'", name)

    def add_browser_source(self, scene, source_name, url, w, h, x=0, y=0) -> None:
        try:
            self.ws.call(requests.CreateInput(
                sceneName=scene,
                inputName=source_name,
                inputKind="browser_source",
                inputSettings={
                    "url": url, "width": w, "height": h,
                    "css": "body { background-color: rgba(0,0,0,0); margin: 0; overflow: hidden; }",
                    "shutdown": False, "restart_when_active": False,
                },
            ))
        except Exception:
            log.warning("Source '%s' may already exist.", source_name)
        self._set_transform(scene, source_name, x, y, w, h)

    def add_video_source(self, scene, source_name, x, y, w, h, platform="windows") -> None:
        kind = CAMERA_KIND.get(platform, "dshow_input")
        try:
            self.ws.call(requests.CreateInput(
                sceneName=scene,
                inputName=source_name,
                inputKind=kind,
                inputSettings={},
            ))
        except Exception:
            log.warning("Source '%s' may already exist.", source_name)
        self._set_transform(scene, source_name, x, y, w, h)

    def _set_transform(self, scene, source_name, x, y, w, h) -> None:
        items = self.ws.call(requests.GetSceneItemList(sceneName=scene)).getSceneItems()
        for item in items:
            if item["sourceName"] == source_name:
                self.ws.call(requests.SetSceneItemTransform(
                    sceneName=scene,
                    sceneItemId=item["sceneItemId"],
                    sceneItemTransform={
                        "positionX": float(x),
                        "positionY": float(y),
                        "boundsType": "OBS_BOUNDS_SCALE_INNER",
                        "boundsAlignment": 5,
                        "boundsWidth": float(w),
                        "boundsHeight": float(h),
                    },
                ))
                return
        log.error("Source '%s' not found in scene '%s'", source_name, scene)

    def set_visible(self, scene, source_name, visible) -> None:
        items = self.ws.call(requests.GetSceneItemList(sceneName=scene)).getSceneItems()
        for item in items:
            if item["sourceName"] == source_name:
                self.ws.call(requests.SetSceneItemEnabled(
                    sceneName=scene,
                    sceneItemId=item["sceneItemId"],
                    sceneItemEnabled=bool(visible),
                ))
                return

    def build_scene(self, cfg: SceneConfig) -> None:
        layout = LAYOUTS[cfg.layout]
        slots = layout["slots"]
        self.create_scene(cfg.name)
        for i, participant in enumerate(cfg.participants):
            if i >= len(slots):
                break
            slot = slots[i]
            if participant.has_video:
                self.add_video_source(cfg.name, participant.cam_source,
                                      slot["x"], slot["y"], slot["w"], slot["h"], cfg.platform)
        if cfg.overlay_url:
            self.add_browser_source(cfg.name, "overlay", cfg.overlay_url, STREAM_WIDTH, STREAM_HEIGHT)
        if cfg.ticker_url:
            self.add_browser_source(cfg.name, "ticker", cfg.ticker_url, STREAM_WIDTH, 76, 0, STREAM_HEIGHT - 76)
        if cfg.alerts_url:
            self.add_browser_source(cfg.name, "alerts", cfg.alerts_url, STREAM_WIDTH, STREAM_HEIGHT)
        log.info("Built scene '%s' (%s)", cfg.name, cfg.layout)
