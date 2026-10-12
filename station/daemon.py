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
  python3 station/daemon.py selftest        # offline logic check, exit 0/1

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
    def set_source_visible(self, scene, source, visible): raise NotImplementedError
    def get_media_status(self, source): raise NotImplementedError  # {time_ms, duration_ms, state}
    def set_transition(self, style, duration_ms): raise NotImplementedError
    def get_stream_status(self): raise NotImplementedError  # {active, dropped_frames}
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

    def set_source_visible(self, scene, source, visible):
        items = self._call("GetSceneItemList", {"sceneName": scene}).get("sceneItems", [])
        for it in items:
            if it.get("sourceName") == source:
                self._call("SetSceneItemEnabled",
                           {"sceneName": scene, "sceneItemId": it["sceneItemId"],
                            "sceneItemEnabled": bool(visible)})
                return
        raise RuntimeError("source %s not in scene %s" % (source, scene))

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
        while True:
            try:
                s, f = self._connect()
                while True:
                    msg = json.loads(f.readline().decode())
                    if msg.get("op") == 5 and msg["d"].get("eventType") == "MediaInputPlaybackEnded":
                        if self._ended_cb:
                            try:
                                self._ended_cb(msg["d"]["eventData"].get("inputName"))
                            except Exception as e:
                                # A dying callback must never kill the event thread:
                                # that would silently stop all playlist advance.
                                print("event callback failed: %s" % e, file=sys.stderr, flush=True)
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
# Scene model (OBS side): scene PROGRAM holds PLAYOUT_A + PLAYOUT_B (one
# visible at a time) plus overlay sources; scene STARTING holds source IDENT;
# TECHDIFF / OFF-AIR / LIVE / END are static scenes. Names are fixed here so
# the state machine can reason about them; rename in OBS and here together.
PROGRAM, DECK_A, DECK_B, IDENT_SRC = "PROGRAM", "PLAYOUT_A", "PLAYOUT_B", "IDENT"
TRANSITION = os.environ.get("TRANSITION", "Fade")


def evict_cache(cap=CACHE_CAP, pinned=frozenset()):
    """Enforce the byte cap: delete LRU .mp4 files, never pinned ones.
    Returns bytes freed. .intake-tmp, playlist.json and intake.db are exempt."""
    try:
        files = [(os.path.getmtime(os.path.join(MEDIA, f)), f)
                 for f in os.listdir(MEDIA)
                 if f.endswith(".mp4") and f not in pinned]
    except OSError:
        return 0
    total = sum(os.path.getsize(os.path.join(MEDIA, f)) for _, f in files)
    freed = 0
    for _, f in sorted(files):
        if total <= cap:
            break
        p = os.path.join(MEDIA, f)
        try:
            size = os.path.getsize(p)
            os.remove(p)
            total -= size
            freed += size
            alert("Evicted %s (cache cap)." % f, "INFO")
        except OSError:
            pass
    return freed


def advance(renderer, state, data, deck_sources):
    """Play next item on the idle deck, cut under a transition.

    Loop, not recursion: a fully-missing playlist must end on TECHDIFF,
    not in RecursionError."""
    items = data.get("items", [])
    if not items:
        renderer.set_scene("TECHDIFF")
        alert("Playlist empty; holding.", "WARN")
        return
    skipped = 0
    while skipped < len(items):
        idx = state.get("index", 0) % len(items)
        item = items[idx]
        path = os.path.join(MEDIA, item["file"])
        if os.path.exists(path):
            break
        alert("Cache miss: %s. Skipping to next." % item["file"], "WARN")
        state["index"] = idx + 1
        skipped += 1
    else:
        renderer.set_scene("TECHDIFF")
        alert("Every playlist item missing; holding.", "CRIT")
        return
    deck = "B" if state.get("deck", "A") == "A" else "A"
    src, other = deck_sources[deck], deck_sources["B" if deck == "A" else "A"]
    renderer.set_media_source(src, path)
    renderer.set_source_visible(PROGRAM, src, True)
    renderer.set_source_visible(PROGRAM, other, False)
    renderer.set_transition(TRANSITION, 750)
    state.update({"index": idx + 1, "deck": deck})
    if state["index"] >= len(items) and data.get("shuffle_on_complete"):
        random.shuffle(data["items"])
        save_playlist(data)
        state["index"] = 0
        alert("Playlist exhausted; reshuffled.", "INFO")
    save_state(state)


def on_ended(renderer, decks, source):
    """Route a media-ended event by source name. Unknown sources are ignored."""
    if source == IDENT_SRC:
        renderer.set_scene("LIVE")  # ident played to completion; cut to live
        alert("Ident done; LIVE on air.", "INFO")
    elif source in decks.values():
        advance(renderer, load_state(), load_playlist(), decks)
    # anything else (sting, bed loop, preview) is not the daemon's business


def cmd_loop(renderer):
    try:
        data = load_playlist()
    except (OSError, ValueError) as e:
        print("cannot start: playlist unreadable (%s). Fix %s." % (e, PLAYLIST))
        return 2
    state = load_state()
    decks = {"A": DECK_A, "B": DECK_B}
    dog = Watchdog(renderer)
    mtime = os.path.getmtime(PLAYLIST)

    renderer.on_media_ended(lambda src: on_ended(renderer, decks, src))
    advance(renderer, state, data, decks)
    alert("Loop running: %d items." % len(data.get("items", [])), "INFO")
    while True:
        try:
            if os.path.getmtime(PLAYLIST) != mtime:  # reload at next cut, never mid-air
                mtime = os.path.getmtime(PLAYLIST)
                try:
                    data = load_playlist()
                    alert("Playlist reloaded; takes effect at next transition.", "INFO")
                except ValueError:
                    alert("Playlist edit is not valid JSON; keeping old order.", "WARN")
            evict_cache()  # cheap stat scan; pinning handled at intake time
            dog.check_stream()
            dog.check_disk()
            dog.check_source(decks[load_state().get("deck", "A")], on_air=True)
        except Exception as e:
            alert("loop error: %s" % e, "WARN")
        time.sleep(10)


# --------------------------------------------------------------- selftest ---
class FakeRenderer(Renderer):
    """Offline stand-in: records calls, serves scripted media positions."""

    def __init__(self):
        self.calls = []
        self.pos = {}

    def set_scene(self, name):
        self.calls.append(("scene", name))

    def set_media_source(self, source, path):
        self.calls.append(("file", source, path))

    def set_source_visible(self, scene, source, visible):
        self.calls.append(("vis", scene, source, visible))

    def get_media_status(self, source):
        return {"time_ms": self.pos.get(source, 0), "duration_ms": 1000, "state": "playing"}

    def set_transition(self, style, duration_ms):
        self.calls.append(("trans", style))

    def get_stream_status(self):
        return {"active": True, "dropped_frames": 0}

    def on_media_ended(self, callback):
        self._cb = callback


def selftest():
    """One runnable check for the non-trivial logic. No OBS, no network."""
    import tempfile
    global MEDIA, PLAYLIST, STATE, DB
    tmp = tempfile.mkdtemp()
    MEDIA, PLAYLIST = os.path.join(tmp, "media"), os.path.join(tmp, "media", "playlist.json")
    STATE, DB = os.path.join(tmp, "state.json"), os.path.join(tmp, "a.db")
    os.makedirs(MEDIA)
    open(os.path.join(MEDIA, "a.mp4"), "w").write("x")
    save_playlist({"shuffle_on_complete": True,
                   "items": [{"file": "a.mp4", "title": "A", "duration": 1},
                             {"file": "gone.mp4", "title": "G", "duration": 1}]})
    r, decks = FakeRenderer(), {"A": DECK_A, "B": DECK_B}
    advance(r, load_state(), load_playlist(), decks)  # plays a.mp4 on B, visible
    assert ("file", DECK_B, os.path.join(MEDIA, "a.mp4")) in r.calls, r.calls
    assert ("vis", PROGRAM, DECK_B, True) in r.calls, r.calls
    assert ("vis", PROGRAM, DECK_A, False) in r.calls, r.calls
    on_ended(r, decks, IDENT_SRC)  # ident end cuts LIVE, never advances playlist
    assert ("scene", "LIVE") in r.calls, r.calls
    live_calls = len(r.calls)
    on_ended(r, decks, "SOME_PREVIEW")  # unknown sources are ignored
    assert len(r.calls) == live_calls, r.calls
    evict_cache(cap=0, pinned=frozenset({"a.mp4"}))  # pinned survives any cap...
    assert os.path.exists(os.path.join(MEDIA, "a.mp4")), "pinned file evicted!"
    evict_cache(cap=0)  # ...unpinned, it goes
    assert not os.path.exists(os.path.join(MEDIA, "a.mp4")), "eviction skipped!"
    dog = Watchdog(r)  # stall detector: frozen position faults once stale
    assert dog.check_source(DECK_A, on_air=False) is True
    dog.last_progress[DECK_A] -= 10  # simulate 10s of no movement
    assert dog.check_source(DECK_A, on_air=False) is False
    assert ("scene", "TECHDIFF") not in [c for c in r.calls if c[0] == "scene"], r.calls
    print("selftest: all checks passed.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Station playout daemon (lab-safe: no-ops without OBS).")
    ap.add_argument("cmd", choices=["loop", "scene", "go-live", "tech-diff",
                                    "resume", "return", "status", "watch",
                                    "selftest"],
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
    if args.cmd == "selftest":
        return selftest()
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
