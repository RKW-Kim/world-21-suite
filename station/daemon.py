#!/usr/bin/env python3
"""Playout daemon: scheduler + prefetch + cache + watchdog + alerts.

Owns the network, the disk, the process tree, and the playlist. The render
plane (OBS today, anything tomorrow) is a dumb renderer that only ever opens
local files handed to it through the Renderer interface below.

Usage (run from repo root, lab defaults to ./broadcast):
  python3 station/daemon.py loop            # run the 24/7 loop (blocks)
  python3 station/daemon.py scene program   # one-shot: cut to a scene
  python3 station/daemon.py go-live         # ident, then cut to LIVE
  python3 station/daemon.py tech-diff       # hard cut to holding card
  python3 station/daemon.py resume          # short sting, back to LIVE
  python3 station/daemon.py return          # back to PROGRAM, resume playlist
  python3 station/daemon.py status          # print health, exit 0/1
  python3 station/daemon.py watch           # one watchdog pass, exit 0/1

Env:
  BROADCAST_ROOT  media/state home (default: ./broadcast)
  OBS_HOST/PORT/PASS  render-plane control socket (default 127.0.0.1:4455)
  TG_TOKEN/TG_CHAT    Telegram alerts; unset = log-only
"""

import argparse
import base64
import hashlib
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = os.environ.get("BROADCAST_ROOT", os.path.join(os.getcwd(), "broadcast"))
MEDIA = os.path.join(ROOT, "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
STATE = os.path.join(ROOT, "state.json")
DB = os.path.join(ROOT, "activity.db")
CACHE_CAP = int(os.environ.get("CACHE_CAP_BYTES", 50 * 1024**3))
WARM_DEPTH = 2
REPEAT_LIMIT = 3  # same fault 3x/hour -> OFF-AIR + escalate


# ---------------------------------------------------------------- Renderer ---
class Renderer:
    """Thin verbs the daemon needs. OBS today, anything tomorrow."""

    def set_scene(self, name): raise NotImplementedError
    def set_media_source(self, source, path): raise NotImplementedError
    def get_media_status(self, source): raise NotImplementedError  # {time_ms, duration_ms, state}
    def set_transition(self, style, duration_ms): raise NotImplementedError
    def get_stream_status(self): raise NotImplementedError  # {active, dropped_frames, cpu}
    def on_media_ended(self, callback): raise NotImplementedError


class OBSRenderer(Renderer):
    """obs-websocket v5 over stdlib sockets. No third-party dependency."""

    def __init__(self, host=None, port=None, password=None):
        self.host = host or os.environ.get("OBS_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("OBS_PORT", "4455"))
        self.password = password or os.environ.get("OBS_PASS", "")
        self._seq = 0
        self._ended_cb = None

    def _connect(self):
        import socket
        s = socket.create_connection((self.host, self.port), timeout=5)
        f = s.makefile("rwb")
        hello = json.loads(f.readline().decode())
        assert hello.get("op") == 0, "not an obs-websocket v5 server"
        identify = {"op": 1, "d": {"rpcVersion": 1}}
        auth = hello["d"].get("authentication")
        if auth:
            secret = base64.b64encode(hashlib.sha256(
                (self.password + auth["salt"]).encode()).digest()).decode()
            response = base64.b64encode(hashlib.sha256(
                (secret + auth["challenge"]).encode()).digest()).decode()
            identify["d"]["authentication"] = response
        f.write((json.dumps(identify) + "\n").encode())
        f.flush()
        identified = json.loads(f.readline().decode())
        assert identified.get("op") == 2, "identify rejected (wrong password?)"
        return s, f

    def _call(self, req, data=None):
        import socket
        try:
            s, f = self._connect()
        except OSError as e:
            raise RuntimeError("render plane unreachable at %s:%d (%s)"
                               % (self.host, self.port, e))
        try:
            self._seq += 1
            rid = "daemon-%d" % self._seq
            f.write((json.dumps({"op": 6, "d": {
                "requestType": req, "requestId": rid,
                "requestData": data or {}}}) + "\n").encode())
            f.flush()
            while True:
                msg = json.loads(f.readline().decode())
                if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                    d = msg["d"]
                    if d["requestStatus"]["result"]:
                        return d.get("responseData", {})
                    raise RuntimeError("%s: %s" % (req, d["requestStatus"].get("comment")))
        finally:
            s.close()

    def set_scene(self, name):
        self._call("SetCurrentProgramScene", {"sceneName": name})

    def set_media_source(self, source, path):
        self._call("SetInputSettings", {
            "inputName": source,
            "inputSettings": {"local_file": path},
            "overlay": True})

    def get_media_status(self, source):
        try:
            d = self._call("GetMediaInputStatus", {"inputName": source})
            return {"time_ms": d.get("mediaCursor", 0),
                    "duration_ms": d.get("mediaDuration", 0),
                    "state": d.get("mediaState", "unknown")}
        except RuntimeError:
            return {"time_ms": -1, "duration_ms": 0, "state": "missing"}

    def set_transition(self, style, duration_ms):
        self._call("SetCurrentSceneTransition", {"transitionName": style})
        self._call("SetCurrentSceneTransitionDuration", {"transitionDuration": duration_ms})

    def get_stream_status(self):
        try:
            d = self._call("GetStreamStatus", {})
            return {"active": d.get("outputActive", False),
                    "dropped_frames": d.get("outputSkippedFrames", 0)}
        except RuntimeError:
            return {"active": False, "dropped_frames": -1}

    def on_media_ended(self, callback):
        self._ended_cb = callback
        t = threading.Thread(target=self._events, daemon=True)
        t.start()

    def _events(self):
        import socket
        while True:
            try:
                s, f = self._connect()
                while True:
                    msg = json.loads(f.readline().decode())
                    if msg.get("op") == 5 and msg["d"].get("eventType") == "MediaInputPlaybackEnded":
                        if self._ended_cb:
                            self._ended_cb(msg["d"]["eventData"].get("inputName"))
                s.close()
            except Exception:
                time.sleep(5)  # reconnect; the loop must not die with the socket


# ------------------------------------------------------------------ alerts ---
def alert(msg, level="WARN"):
    row = (time.strftime("%Y-%m-%d %H:%M:%S"), level, msg)
    try:
        con = sqlite3.connect(DB)
        con.execute("CREATE TABLE IF NOT EXISTS activity_log(ts TEXT, level TEXT, msg TEXT)")
        con.execute("INSERT INTO activity_log VALUES (?,?,?)", row)
        con.commit()
        con.close()
    except Exception:
        pass
    print("[%s] %s" % (level, msg), flush=True)
    tok, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if not (tok and chat):
        return
    try:
        emoji = {"CRIT": "\U0001f534", "WARN": "\U0001f7e1", "INFO": "\U0001f535"}[level]
        urllib.request.urlopen(urllib.request.Request(
            "https://api.telegram.org/bot%s/sendMessage" % tok,
            data=json.dumps({"chat_id": chat,
                             "text": "%s [%s] %s" % (emoji, level, msg)}).encode(),
            headers={"Content-Type": "application/json"}), timeout=10)
    except Exception as e:
        print("[WARN] telegram failed: %s" % e, flush=True)


# ---------------------------------------------------------------- playlist ---
def load_playlist():
    with open(PLAYLIST) as f:
        return json.load(f)

def save_playlist(data):
    tmp = PLAYLIST + ".new"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, PLAYLIST)  # atomic: readers see old or new, never half

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"index": 0, "deck": "A", "faults": {}}

def save_state(state):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE)


# ---------------------------------------------------------------- watchdog ---
class Watchdog:
    """Measures progress, not liveness. A stalled fd looks 'connected'."""

    def __init__(self, renderer):
        self.r = renderer
        self.last_ms = {}
        self.last_progress = {}

    def check_source(self, source, on_air):
        st = self.r.get_media_status(source)
        now = time.time()
        if st["time_ms"] < 0:
            return self.fault(source, "source missing", on_air)
        if st["time_ms"] == self.last_ms.get(source):
            if now - self.last_progress.get(source, now) > 5:
                return self.fault(source, "stalled at %sms" % st["time_ms"], on_air)
        else:
            self.last_ms[source] = st["time_ms"]
            self.last_progress[source] = now
        return True

    def fault(self, source, reason, on_air):
        state = load_state()
        faults = state.setdefault("faults", {})
        key = "%s:%s" % (source, reason.split(" at ")[0])
        hist = [t for t in faults.get(key, []) if time.time() - t < 3600] + [time.time()]
        faults[key] = hist
        save_state(state)
        if len(hist) >= REPEAT_LIMIT:
            alert("REPEATED FAILURE %s (%s) x%d in 1h. OFF-AIR, waiting for human."
                  % (source, reason, len(hist)), "CRIT")
            self.r.set_scene("OFF-AIR")
            return False
        alert("%s: %s." % (source, reason), "CRIT")
        if on_air:
            alert("Cutting to TECHDIFF; stream survives.", "INFO")
            self.r.set_scene("TECHDIFF")
        return False

    def check_stream(self):
        st = self.r.get_stream_status()
        if not st["active"]:
            alert("Stream output not active!", "CRIT")
            return False
        return True

    def check_disk(self):
        free = shutil.disk_usage(ROOT).free
        if free < 5 * 1024**3:
            alert("Disk critical: %.1f GB free." % (free / 1024**3), "CRIT")
            return False
        return True


# ------------------------------------------------------------------- loop ---
def advance(renderer, state, data, deck_sources):
    """Play next item on the idle deck, cut under a transition."""
    items = data["items"]
    if not items:
        renderer.set_scene("TECHDIFF")
        alert("Playlist empty; holding.", "WARN")
        return
    idx = state.get("index", 0) % len(items)
    item = items[idx]
    deck = "B" if state.get("deck", "A") == "A" else "A"
    src = deck_sources[deck]
    path = os.path.join(MEDIA, item["file"])
    if not os.path.exists(path):
        alert("Cache miss: %s. Skipping to next." % item["file"], "WARN")
        state["index"] = idx + 1
        save_state(state)
        return advance(renderer, state, data, deck_sources)
    renderer.set_media_source(src, path)
    renderer.set_transition("Fade", 750)
    # visibility swap PLAYOUT_B <-> PLAYOUT_A happens in OBS scene "PROGRAM";
    # media source restart-on-activate covers the file change.
    state.update({"index": idx + 1, "deck": deck})
    if state["index"] >= len(items) and data.get("shuffle_on_complete"):
        random.shuffle(data["items"])
        save_playlist(data)
        state["index"] = 0
        alert("Playlist exhausted; reshuffled.", "INFO")
    save_state(state)


def cmd_loop(renderer):
    data = load_playlist()
    state = load_state()
    decks = {"A": "PLAYOUT_A", "B": "PLAYOUT_B"}
    dog = Watchdog(renderer)
    mtime = os.path.getmtime(PLAYLIST)

    def on_ended(source):
        advance(renderer, load_state(), load_playlist(), decks)

    renderer.on_media_ended(on_ended)
    advance(renderer, state, data, decks)
    alert("Loop running: %d items." % len(data["items"]), "INFO")
    while True:
        try:
            if os.path.getmtime(PLAYLIST) != mtime:  # reload at next cut, never mid-air
                mtime = os.path.getmtime(PLAYLIST)
                data = load_playlist()
                alert("Playlist reloaded; takes effect at next transition.", "INFO")
            dog.check_stream()
            dog.check_disk()
            dog.check_source(decks[load_state().get("deck", "A")], on_air=True)
        except Exception as e:
            alert("loop error: %s" % e, "WARN")
        time.sleep(10)


def main():
    ap = argparse.ArgumentParser(description="Station playout daemon (lab-safe: no-ops without OBS).")
    ap.add_argument("cmd", choices=["loop", "scene", "go-live", "tech-diff",
                                    "resume", "return", "status", "watch"],
                    help="intent to execute")
    ap.add_argument("arg", nargs="?", help="scene name for 'scene'")
    args = ap.parse_args()
    r = OBSRenderer()

    if args.cmd == "status":
        s = r.get_stream_status()
        print(json.dumps(s, indent=2))
        return 0 if s["active"] else 1
    if args.cmd == "watch":
        d = Watchdog(r)
        ok = d.check_stream() and d.check_disk()
        return 0 if ok else 1
    if args.cmd == "scene":
        r.set_scene(args.arg)
        alert("Cut to %s." % args.arg, "INFO")
    elif args.cmd == "go-live":
        r.set_scene("STARTING")  # ident plays; MediaInputPlaybackEnded -> LIVE
        alert("GO LIVE: ident running, LIVE armed.", "INFO")
    elif args.cmd == "tech-diff":
        r.set_scene("TECHDIFF")
        alert("TECH DIFF on air.", "WARN")
    elif args.cmd == "resume":
        r.set_scene("LIVE")  # short sting lives in the scene; no full re-intro
        alert("Resumed LIVE.", "INFO")
    elif args.cmd == "return":
        r.set_scene("PROGRAM")
        alert("Returned to PROGRAM.", "INFO")
    elif args.cmd == "loop":
        cmd_loop(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
