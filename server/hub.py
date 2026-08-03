import threading
import logging
from obswebsocket import obsws, requests
from server.config import OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD
from automation.layouts import LAYOUTS

log = logging.getLogger(__name__)
LIVE = "03-live"
CAM_SOURCES = [f"CAM-{i}" for i in range(1, 6)]


class Hub:
    def __init__(self):
        self._ws = None
        self._lock = threading.Lock()

    @property
    def connected(self):
        return self._ws is not None

    def connect(self):
        with self._lock:
            if self._ws:
                return True
            try:
                ws = obsws(OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD)
                ws.connect()
                self._ws = ws
                log.info("OBS hub connected @ %s:%s", OBS_WS_HOST, OBS_WS_PORT)
                return True
            except Exception as e:
                log.warning("OBS hub connect failed: %s", e)
                self._ws = None
                return False

    def disconnect(self):
        with self._lock:
            if self._ws:
                try:
                    self._ws.disconnect()
                except Exception:
                    pass
                self._ws = None

    def _call(self, req):
        with self._lock:
            if not self._ws:
                raise RuntimeError("OBS not connected")
            return self._ws.call(req)

    def ping(self):
        with self._lock:
            if not self._ws:
                return False
            try:
                self._ws.call(requests.GetVersion())
                return True
            except Exception:
                self._ws = None
                return False

    def canvas(self):
        vs = self._call(requests.GetVideoSettings())
        return {"w": vs.getBaseWidth(), "h": vs.getBaseHeight()}

    def scenes(self):
        return [s["sceneName"] for s in self._call(requests.GetSceneList()).getScenes()]

    def current_scene(self):
        return self._call(requests.GetSceneList()).getCurrentProgramSceneName()

    def items(self, scene=LIVE):
        out = []
        for it in self._call(requests.GetSceneItemList(sceneName=scene)).getSceneItems():
            tr = it.get("sceneItemTransform", {})
            bw, bh = tr.get("boundsWidth", 0), tr.get("boundsHeight", 0)
            out.append({
                "name": it["sourceName"],
                "id": it["sceneItemId"],
                "x": tr.get("positionX", 0), "y": tr.get("positionY", 0),
                "w": bw or tr.get("sourceWidth", 0), "h": bh or tr.get("sourceHeight", 0),
                "visible": it.get("sceneItemEnabled", True),
            })
        return out

    def audio_level(self, input_name):
        lv = self._call(requests.GetInputAudioLevels(inputName=input_name)).getInputLevels()
        return lv[0][0] if (lv and lv[0]) else -60.0

    def input_muted(self, input_name):
        return self._call(requests.GetInputMuted(inputName=input_name)).getInputMuted()

    def switch_scene(self, name):
        self._call(requests.SetCurrentProgramScene(sceneName=name))

    def _find(self, scene, source):
        for it in self._call(requests.GetSceneItemList(sceneName=scene)).getSceneItems():
            if it["sourceName"] == source:
                return it["sceneItemId"]
        return None

    def set_visible(self, source, visible, scene=LIVE):
        iid = self._find(scene, source)
        if iid is None:
            return False
        self._call(requests.SetSceneItemEnabled(
            sceneName=scene, sceneItemId=iid, sceneItemEnabled=bool(visible)))
        return True

    def set_transform(self, source, x, y, w, h, scene=LIVE):
        iid = self._find(scene, source)
        if iid is None:
            return False
        self._call(requests.SetSceneItemTransform(
            sceneName=scene, sceneItemId=iid,
            sceneItemTransform={
                "positionX": float(x), "positionY": float(y),
                "boundsType": "OBS_BOUNDS_SCALE_INNER", "boundsAlignment": 5,
                "boundsWidth": float(w), "boundsHeight": float(h),
            }))
        return True

    def set_mute(self, input_name, muted):
        self._call(requests.SetInputMute(inputName=input_name, inputMuted=bool(muted)))

    def apply_layout(self, layout):
        slots = LAYOUTS[layout]["slots"]
        for i, src in enumerate(CAM_SOURCES):
            if i < len(slots):
                s = slots[i]
                self.set_transform(src, s["x"], s["y"], s["w"], s["h"])
                self.set_visible(src, True)
            else:
                self.set_visible(src, False)

    def feature_speaker(self, speaker_source):
        slots = LAYOUTS["autotalk"]["slots"]
        main, strip = slots[0], slots[1:]
        self.set_transform(speaker_source, main["x"], main["y"], main["w"], main["h"])
        self.set_visible(speaker_source, True)
        others = [s for s in CAM_SOURCES if s != speaker_source]
        for j, src in enumerate(others):
            if j < len(strip):
                s = strip[j]
                self.set_transform(src, s["x"], s["y"], s["w"], s["h"])
                self.set_visible(src, True)
            else:
                self.set_visible(src, False)
