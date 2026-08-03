"""Auto-talk controller. Polls audio (or simulates), promotes active speaker."""

from __future__ import annotations
import time
import logging

import httpx
from obswebsocket import requests

from automation.controller import OBSController, Participant
from automation.layouts import LAYOUTS

log = logging.getLogger(__name__)


class AutoTalkController:
    def __init__(self, obs, scene_name, participants, bridge_url=None):
        self.obs = obs
        self.scene = scene_name
        self.participants = participants
        self.bridge_url = bridge_url
        self._cfg = LAYOUTS["autotalk"]
        self._threshold = self._cfg["peak_threshold_db"]
        self._poll_s = self._cfg["poll_ms"] / 1000.0
        self._max_strip = self._cfg["max_strip"]
        self._last_main = None
        self._debounce_count = 0
        self._debounce_required = 3

    def get_audio_levels(self):
        levels = {}
        for p in self.participants:
            try:
                resp = self.obs.ws.call(requests.GetInputAudioLevels(inputName=p.mic_source))
                raw = resp.getInputLevels()
                levels[p.mic_source] = raw[0][0] if (raw and raw[0]) else -60.0
            except Exception:
                levels[p.mic_source] = -60.0
        return levels

    def apply_state(self, main, strip):
        """Place `main` in the big slot, `strip` in the side slots, hide the rest."""
        main_slot = self._cfg["slots"][0]
        if main:
            self.obs._set_transform(self.scene, main.cam_source,
                                    main_slot["x"], main_slot["y"], main_slot["w"], main_slot["h"])
            self.obs.set_visible(self.scene, main.cam_source, True)
        for i, p in enumerate(strip):
            slot = self._cfg["slots"][i + 1]
            self.obs._set_transform(self.scene, p.cam_source,
                                    slot["x"], slot["y"], slot["w"], slot["h"])
            self.obs.set_visible(self.scene, p.cam_source, True)
        shown = {main.cam_source if main else None} | {p.cam_source for p in strip}
        for p in self.participants:
            if p.cam_source not in shown:
                self.obs.set_visible(self.scene, p.cam_source, False)
        self._push(main, strip)

    def _push(self, main, strip):
        if not self.bridge_url:
            return
        payload = {
            "main": main.name if main else None,
            "main_slot": "main",
            "strip": [p.name for p in strip],
        }
        try:
            httpx.post(f"{self.bridge_url}/api/autotalk/push", json=payload, timeout=1.0)
        except Exception:
            pass

    def tick(self):
        levels = self.get_audio_levels()
        speaking = [p for p in self.participants
                    if levels.get(p.mic_source, -60.0) > self._threshold]
        if not speaking:
            return
        pinned = next((p for p in self.participants if p.pinned), None)
        if pinned and pinned in speaking:
            main = pinned
        else:
            loudest = max(speaking, key=lambda p: levels.get(p.mic_source, -60.0))
            if loudest.name == self._last_main:
                self._debounce_count += 1
            else:
                self._debounce_count = 0
                self._last_main = loudest.name
            if self._debounce_count < self._debounce_required and self._last_main:
                main = next((p for p in self.participants if p.name == self._last_main), loudest)
            else:
                main = loudest
        strip = [p for p in speaking if p is not main and p.has_video][:self._max_strip]
        self.apply_state(main, strip)

    def run(self):
        log.info("Auto-talk live on '%s' | %d participants", self.scene, len(self.participants))
        try:
            while True:
                self.tick()
                time.sleep(self._poll_s)
        except KeyboardInterrupt:
            log.info("Auto-talk stopped.")

    def pin(self, name):
        for p in self.participants:
            p.pinned = (p.name == name)

    def unpin_all(self):
        for p in self.participants:
            p.pinned = False
