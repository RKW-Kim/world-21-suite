#!/usr/bin/env python3
"""Playout daemon: scheduler + prefetch + cache + watchdog + alerts.

Owns the network, the disk, the process tree, and the playlist. The render
plane (OBS today, anything tomorrow) is a dumb renderer that only ever opens
local files handed to it through the Renderer interface below.

Usage (run from repo root, lab defaults to ./broadcast):
  python3 station/daemon.py loop            # run the 24/7 loop (blocks)
  python3 station/daemon.py scene "SMILE | Meet"  # one-shot cut (exact OBS name)
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
  DISCORD_WEBHOOK   alert channel (a Discord channel webhook URL); unset = log-only
"""

import argparse
import base64
import hashlib
import json
import os
import random
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = os.environ.get("BROADCAST_ROOT", os.path.join(os.getcwd(), "broadcast"))
HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
STATE = os.path.join(ROOT, "state.json")
DB = os.path.join(ROOT, "activity.db")
CACHE_CAP = int(os.environ.get("CACHE_CAP_BYTES", 50 * 1024**3))
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


class _WS:
    """Minimal RFC6455 client (handshake + text frames). obs-websocket speaks
    real WebSocket framing, not line-delimited JSON — this is that."""

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, host, port, timeout=5):
        self.s = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET / HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
                        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
                        "Sec-WebSocket-Version: 13\r\n\r\n" % (host, port, key)).encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.s.recv(4096)
            if not chunk:
                raise RuntimeError("websocket handshake failed (EOF)")
            head += chunk
        accept = base64.b64encode(hashlib.sha1(
            (key + self.GUID).encode()).digest()).decode()
        status = head.split(b"\r\n", 1)[0]
        if b" 101 " not in status or accept.encode() not in head:
            raise RuntimeError("websocket handshake rejected: %s" % status.decode(errors="replace"))
        self.buf = b""

    def _fill(self, n):
        while len(self.buf) < n:
            chunk = self.s.recv(65536)
            if not chunk:
                raise RuntimeError("websocket closed mid-frame")
            self.buf += chunk

    def _frame(self, opcode, payload=b""):
        # Servers MUST drop unmasked client frames (we were killed with 1002
        # for an unmasked close) — so even close/pong go out masked.
        mask = os.urandom(4)
        n = len(payload)
        hdr = bytes([0x80 | opcode])
        if n < 126:
            hdr += bytes([0x80 | n])
        elif n < 65536:
            hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def send(self, obj):
        self._frame(0x1, json.dumps(obj).encode())

    def recv(self):
        frags = []
        while True:
            self._fill(2)
            b1, b2 = self.buf[0], self.buf[1]
            fin, op, ln, off = b1 & 0x80, b1 & 0x0F, b2 & 0x7F, 2
            if ln == 126:
                self._fill(4)
                ln, off = struct.unpack(">H", self.buf[2:4])[0], 4
            elif ln == 127:
                self._fill(10)
                ln, off = struct.unpack(">Q", self.buf[2:10])[0], 10
            masked = b2 & 0x80
            if masked:
                off += 4
            self._fill(off + ln)
            payload = self.buf[off:off + ln]
            if masked:
                m = self.buf[off - 4:off]
                payload = bytes(c ^ m[i % 4] for i, c in enumerate(payload))
            self.buf = self.buf[off + ln:]
            if op == 0x8:
                # Never swallow the code: 4009 means wrong password, 1002 a
                # protocol bug on our side, 1001 server going away. Without
                # this, auth failures masquerade as a dead server (learned
                # the hard way: an entire evening of "deaf server" logs).
                code, reason = None, ""
                if len(payload) >= 2:
                    code = struct.unpack(">H", payload[:2])[0]
                    reason = payload[2:120].decode(errors="replace")
                raise RuntimeError("websocket closed by server (code %s %s)"
                                   % (code, reason))
            if op == 0x9:
                self._frame(0xA)  # ping -> masked pong
                continue
            if op not in (0x0, 0x1):
                continue
            frags.append(payload)
            if fin:
                try:
                    return json.loads(b"".join(frags).decode())
                except ValueError as e:
                    raise RuntimeError("bad frame: %s" % e)

    def close(self):
        try:
            self._frame(0x8)
        except OSError:
            pass
        try:
            self.s.close()
        except OSError:
            pass


class OBSRenderer(Renderer):
    """obs-websocket v5 over stdlib sockets. No third-party dependency."""

    def __init__(self, host=None, port=None, password=None):
        self.host = host or os.environ.get("OBS_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("OBS_PORT", "4455"))
        self.password = password or os.environ.get("OBS_PASS", "")
        self._seq = 0
        self._ended_cb = None
        self._shared = None
        self._lock = threading.Lock()

    def _connect(self, timeout="default"):
        # Calls default to 60s: on weak boxes a SetInputSettings can stall the
        # server thread for many seconds (ffmpeg probe + CEF contention), and a
        # short timeout turns that into a false "unreachable". Overridable via
        # OBS_TIMEOUT. The event thread passes None and blocks forever instead.
        if timeout == "default":
            timeout = int(os.environ.get("OBS_TIMEOUT", "60"))
        try:
            ws = _WS(self.host, self.port, timeout=timeout)
        except OSError as e:
            raise RuntimeError("render plane unreachable at %s:%d (%s)"
                               % (self.host, self.port, e))
        hello = ws.recv()
        if hello.get("op") != 0:
            ws.close()
            raise RuntimeError("not an obs-websocket v5 server")
        identify = {"op": 1, "d": {"rpcVersion": 1}}
        auth = hello["d"].get("authentication")
        if auth:
            secret = base64.b64encode(hashlib.sha256(
                (self.password + auth["salt"]).encode()).digest()).decode()
            response = base64.b64encode(hashlib.sha256(
                (secret + auth["challenge"]).encode()).digest()).decode()
            identify["d"]["authentication"] = response
        ws.send(identify)
        identified = ws.recv()
        if identified.get("op") != 2:
            ws.close()
            raise RuntimeError("identify rejected (wrong password?)")
        return ws

    def _call(self, req, data=None):
        # One shared connection, reused across polls: every handshake is a
        # chance to catch the server in a deaf window, so we pay it once and
        # hold it. Any failure drops it; the next call reconnects.
        with self._lock:
            if self._shared is None:
                self._shared = self._connect()
            ws = self._shared
            try:
                self._seq += 1
                rid = "daemon-%d" % self._seq
                ws.send({"op": 6, "d": {"requestType": req, "requestId": rid,
                                        "requestData": data or {}}})
                while True:
                    msg = ws.recv()
                    if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                        d = msg["d"]
                        if d["requestStatus"]["result"]:
                            return d.get("responseData", {})
                        raise RuntimeError("%s: %s" % (req, d["requestStatus"].get("comment")))
            except Exception:
                try:
                    ws.close()
                except Exception:
                    pass
                self._shared = None
                raise

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
            # OBS returns explicit nulls when idle (key present, value None) —
            # .get(key, default) does NOT cover that. Normalize or every idle
            # source reads as a crash downstream.
            cur = d.get("mediaCursor")
            dur = d.get("mediaDuration")
            return {"time_ms": cur if isinstance(cur, (int, float)) else -1,
                    "duration_ms": dur if isinstance(dur, (int, float)) else 0,
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
                ws = self._connect(timeout=None)
                try:
                    while True:
                        msg = ws.recv()
                        if msg.get("op") == 5 and msg["d"].get("eventType") == "MediaInputPlaybackEnded":
                            if self._ended_cb:
                                try:
                                    self._ended_cb(msg["d"]["eventData"].get("inputName"))
                                except Exception as e:
                                    # A dying callback must never kill the event thread:
                                    # that would silently stop all playlist advance.
                                    print("event callback failed: %s" % e, file=sys.stderr, flush=True)
                finally:
                    ws.close()
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
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        return
    try:
        emoji = {"CRIT": "\U0001f534", "WARN": "\U0001f7e1", "INFO": "\U0001f535"}[level]
        urllib.request.urlopen(urllib.request.Request(
            hook,
            data=json.dumps({"username": "station",
                             "content": "%s **[%s]** %s" % (emoji, level, msg)}).encode(),
            headers={"Content-Type": "application/json"}), timeout=10)
    except Exception as e:
        print("[WARN] discord failed: %s" % e, flush=True)


# ---------------------------------------------------------------- playlist ---
def load_secrets():
    """Source broadcast/secrets.env into the environment (no-op if absent).

    Every entry point (CLI, loop, overlay server) needs OBS_PASS + webhook
    without the operator remembering to export them. An evening was lost to
    4009-auth failures from a server started bare; never again."""
    path = os.path.join(ROOT, "secrets.env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except OSError:
        pass


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
        self._was_active = None
        self._last_note = {}  # key -> ts of last repeatable notice

    def _note(self, key, interval, level, msg):
        """Repeatable notices, throttled: first occurrence alerts, repeats
        at most once per interval. Alert fatigue is how a real incident gets
        slept through."""
        now = time.time()
        if now - self._last_note.get(key, 0) >= interval:
            self._last_note[key] = now
            alert(msg, level)

    def check_source(self, source, on_air):
        st = self.r.get_media_status(source)
        now = time.time()
        if st["state"] == "missing":
            return self.fault(source, "source missing", on_air)
        if st["time_ms"] < 0:
            return True  # exists but idle/loading: nothing to measure yet.
            # Faulting here caused a full false TECHDIFF→OFF-AIR cascade on a
            # source that simply hadn't started playing. Only regressions fault.
        if st["time_ms"] == self.last_ms.get(source):
            if now - self.last_progress.get(source, now) > 5:
                return self.fault(source, "stalled at %sms" % st["time_ms"], on_air)
        else:
            self.last_ms[source] = st["time_ms"]
            self.last_progress[source] = now
        return True

    def _program_is_live(self):
        try:
            pgm = self.r._call("GetCurrentProgramScene")["currentProgramSceneName"]
            return pgm in (SCENE_PROGRAM, SCENE_LIVE)
        except Exception:
            return True  # unknown: fail safe toward cutting, not toward silence

    def fault(self, source, reason, on_air):
        state = load_state()
        faults = state.setdefault("faults", {})
        key = "%s:%s" % (source, reason.split(" at ")[0])
        hist = [t for t in faults.get(key, []) if time.time() - t < 3600] + [time.time()]
        faults[key] = hist
        faults = {k: v for k, v in faults.items() if v}  # don't grow dead keys
        state["faults"] = faults
        save_state(state)
        if len(hist) >= REPEAT_LIMIT:
            if len(hist) == REPEAT_LIMIT:
                alert("REPEATED FAILURE %s (%s) x%d in 1h. OFF-AIR, waiting for human."
                      % (source, reason, len(hist)), "CRIT")
                self.r.set_scene(SCENE_OFFAIR)
            else:
                self._note(key + ":escalated", 3600, "CRIT",
                           "Still failing: %s (%s). OFF-AIR held." % (source, reason))
            return False
        alert("%s: %s." % (source, reason), "CRIT")
        if on_air and self._program_is_live():
            alert("Cutting to TECHDIFF; stream survives.", "INFO")
            self.r.set_scene(SCENE_TECHDIFF)
        return False

    def check_stream(self):
        st = self.r.get_stream_status()
        if st["active"]:
            self._was_active = True
            return True
        if self._was_active is not False:
            # Transition into inactive: loud once. While it stays down (lab
            # has no stream key at all), hourly reminder, not per-poll spam.
            alert("Stream output not active!", "CRIT")
            self._was_active = False
        else:
            self._note("stream-down", 3600, "WARN",
                       "Stream output still not active.")
        return False

    def check_disk(self):
        free = shutil.disk_usage(ROOT).free
        if free < 5 * 1024**3:
            # Throttled: a full disk stays full for hours; per-poll CRIT is
            # how an operator learns to mute the channel.
            self._note("disk", 3600, "CRIT",
                       "Disk critical: %.1f GB free." % (free / 1024**3))
            return False
        return True


# ------------------------------------------------------------------- loop ---
# Scene model (OBS side; collection built by render_scenes.py from the deck's
# six — Starting, Meet, Q&A, Tech Diffs, Off Air, End Credits).
# Role mapping: STARTING holds the IDENT clip; PROGRAM plays the PLAYOUT_A/B
# deck under ticker+watermark; LIVE carries the SRT feeds under the speaking
# overlay; TECHDIFF frames faults per SCENES.md; OFF-AIR is the harbour.
SCENE_STARTING, SCENE_PROGRAM = "SMILE | Starting", "SMILE | Meet"
SCENE_LIVE, SCENE_TECHDIFF = "SMILE | Q&A", "SMILE | Tech Diffs"
SCENE_OFFAIR, SCENE_END = "SMILE | Off Air", "SMILE | End Credits"
PROGRAM, DECK_A, DECK_B, IDENT_SRC = SCENE_PROGRAM, "PLAYOUT_A", "PLAYOUT_B", "IDENT"
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
        renderer.set_scene(SCENE_TECHDIFF)
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
        renderer.set_scene(SCENE_TECHDIFF)
        alert("Every playlist item missing; holding.", "CRIT")
        return
    deck = "B" if state.get("deck", "A") == "A" else "A"
    src, other = deck_sources[deck], deck_sources["B" if deck == "A" else "A"]
    renderer.set_media_source(src, path)
    renderer.set_source_visible(PROGRAM, src, True)
    renderer.set_source_visible(PROGRAM, other, False)
    renderer.set_transition(TRANSITION, 750)
    alert("Now playing: %s." % item.get("title", item["file"]), "INFO")
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
        # ...unless the operator already moved on (RETURN mid-ident): cutting
        # LIVE over their program would hijack the show from under them.
        try:
            pgm = renderer._call("GetCurrentProgramScene")["currentProgramSceneName"]
        except Exception:
            pgm = SCENE_STARTING  # unknown: honor the intent, cut anyway
        if pgm != SCENE_STARTING:
            alert("Ident ended but program is %s; leaving it." % pgm, "INFO")
            return
        renderer.set_scene(SCENE_LIVE)  # ident played to completion; cut to live
        alert("Ident done; LIVE on air.", "INFO")
    elif source in decks.values():
        advance(renderer, load_state(), load_playlist(), decks)
    # anything else (sting, bed loop, preview) is not the daemon's business


def wait_ready(renderer, tries=None, pause=15):
    """Block until the render plane answers. A fresh boot under CEF load can
    take minutes before the first Hello; crashing on it would make every
    autostart a coin flip (systemd would restart-loop us)."""
    import time as _t
    if tries is None:
        tries = int(os.environ.get("OBS_READY_TRIES", "12"))
    for n in range(1, tries + 1):
        try:
            renderer._call("GetVersion")
            return True
        except Exception as e:
            print("render plane not ready (%d/%d): %s" % (n, tries, e), flush=True)
            _t.sleep(pause)
    return False


def prefetch_name(item):
    base = (item.get("title") or "item")[:40]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base).strip("_") or "item"
    digest = hashlib.sha1(item["source"].encode()).hexdigest()[:8]
    return "%s_%s.mp4" % (safe, digest)


def prefetch_pass(data, state, in_flight, failed=None):
    """Warm the next items: reap finished fetches, spawn at most one new one.

    Runs inside the poll loop (no extra thread). Items carry an optional
    "source" (URL or file path); the resolver runs as a SUBPROCESS, never
    in-process — a hung yt-dlp dies with its process, not with the daemon.
    Max 2 concurrent: weak boxes choke on parallel transcodes.
    Persistently failing sources back off (15 min) instead of respawning
    every pass — a doomed fetch churning fork+alert every 30s is how a
    quiet box spends a night achieving nothing.
    """
    if failed is None:
        failed = {}
    now = time.time()
    for source, proc in list(in_flight.items()):
        if proc.poll() is None:
            continue
        del in_flight[source]
        if proc.returncode == 0:
            failed.pop(source, None)
            for item in data.get("items", []):
                if item.get("source") == source:
                    name = prefetch_name(item)
                    if os.path.exists(os.path.join(MEDIA, name)):
                        item["file"] = name
            save_playlist(data)
            alert("Prefetched %s." % source[-60:], "INFO")
        else:
            failed[source] = now
            alert("Prefetch failed for %s; retrying in 15 min." % source[-60:], "WARN")
    items = data.get("items", [])
    if not items or len(in_flight) >= 2:
        return
    idx = state.get("index", 0) % len(items)
    for off in (0, 1):
        item = items[(idx + off) % len(items)]
        source = item.get("source")
        if not source or source in in_flight:
            continue
        if now - failed.get(source, 0) < 900:
            continue  # backing off a doomed fetch; see reap branch
        if item.get("file") and os.path.exists(os.path.join(MEDIA, item["file"])):
            continue  # already cached under its file name (empty = not cached:
                      # exists() on the bare directory would lie True)
        name = prefetch_name(item)
        if os.path.exists(os.path.join(MEDIA, name)):
            item["file"] = name  # fetched earlier, never linked into playlist
            save_playlist(data)
            continue
        try:
            env = dict(os.environ, BROADCAST_ROOT=os.path.dirname(MEDIA))
            in_flight[source] = subprocess.Popen(
                [sys.executable, os.path.join(HERE, "intake.py"),
                 source, "--as", name, "--title", item.get("title", "")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            alert("Prefetching %s ..." % source[-60:], "INFO")
        except OSError as e:
            alert("Prefetch spawn failed: %s." % e, "WARN")
        return  # one new fetch per pass; the next pass takes the next item


def cmd_loop(renderer):
    import fcntl
    try:
        lock = open(os.path.join(ROOT, "daemon.lock"), "w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError):
        print("another loop already holds %s/daemon.lock; refusing a second driver." % ROOT)
        return 2
    with open(os.path.join(ROOT, "daemon.pid"), "w") as f:
        # PID file: pgrep counting lies when launcher shells linger in the
        # same command line (their cmdline contains our own pattern). Read
        # this file and check /proc/<pid> for the truth.
        f.write(str(os.getpid()))
    try:
        data = load_playlist()
    except (OSError, ValueError) as e:
        print("cannot start: playlist unreadable (%s). Fix %s." % (e, PLAYLIST))
        return 2
    state = load_state()
    decks = {"A": DECK_A, "B": DECK_B}
    dog = Watchdog(renderer)
    last_loop_err = None
    mtime = os.path.getmtime(PLAYLIST)
    last_hash = json.dumps(data, sort_keys=True)
    ended = []  # media-ended events queue here; the poll loop drains them.
    end_lock = threading.Lock()  # ...so a deaf window delays advance, never drops it.

    def note_ended(source):
        with end_lock:
            ended.append(source)

    renderer.on_media_ended(note_ended)
    if not wait_ready(renderer):
        print("render plane never answered; refusing to start blind.")
        return 2
    try:
        names = [t["name"] for t in
                 renderer._call("GetTransitionList").get("transitions", [])]
        assert TRANSITION in names, "transition %r missing (have %s)" % (TRANSITION, names)
    except AssertionError as e:
        print("cannot start loop: %s." % e)
        return 2
    except RuntimeError as e:
        print("cannot verify transitions (%s); starting anyway." % e)
    try:
        advance(renderer, state, data, decks)
    except RuntimeError as e:
        print("cannot start loop: %s. Is the render plane running?" % e)
        return 2
    try:
        # The deck plays wherever the files point, but nobody SEES it until
        # program is the Meet scene. Caught live: a full advance cycle ran
        # into the Off Air harbour because nothing cut program.
        renderer.set_scene(SCENE_PROGRAM)
    except RuntimeError as e:
        alert("Program is not on Meet (%s); cut manually." % e, "WARN")
    alert("Loop running: %d items." % len(data.get("items", [])), "INFO")
    # In-flight fetches live across polls: a fresh dict per pass would make
    # the spawn guard blind and duplicate every fetch.
    in_flight, failed = {}, {}
    while True:
        try:
            if os.path.getmtime(PLAYLIST) != mtime:  # reload at next cut, never mid-air
                mtime = os.path.getmtime(PLAYLIST)
                try:
                    new_data = load_playlist()
                    # Our own shuffle-save also bumps mtime; only announce
                    # human edits, or the operator learns to ignore the log.
                    if json.dumps(new_data, sort_keys=True) != last_hash:
                        data = new_data
                        last_hash = json.dumps(data, sort_keys=True)
                        alert("Playlist reloaded; takes effect at next transition.", "INFO")
                except ValueError:
                    alert("Playlist edit is not valid JSON; keeping old order.", "WARN")
            with end_lock:
                pending, ended[:] = ended[:], []
            for source in pending:  # failures stay queued for the next pass
                try:
                    on_ended(renderer, decks, source)
                except Exception as e:
                    alert("advance deferred (%s); retrying next pass." % e, "WARN")
                    with end_lock:
                        ended.append(source)
            evict_cache()  # cheap stat scan; pinning handled at intake time
            prefetch_pass(data, state, in_flight, failed)
            dog.check_stream()
            dog.check_disk()
            dog.check_source(decks[load_state().get("deck", "A")], on_air=True)
        except Exception:
            import traceback
            # Full trace once per distinct error; deaf windows repeat the same
            # failure every poll and would drown the log otherwise.
            sig = traceback.format_exc(limit=3)
            if sig != last_loop_err:
                last_loop_err = sig
                traceback.print_exc()
                alert("loop error (see log for traceback).", "WARN")
        time.sleep(int(os.environ.get("WATCH_POLL", "10")))


# --------------------------------------------------------------- selftest ---
class FakeRenderer(Renderer):
    """Offline stand-in: records calls, serves scripted media positions."""

    def __init__(self):
        self.calls = []
        self.pos = {}
        self.program_scene = SCENE_STARTING

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

    def _call(self, req, data=None):
        # fail-safe probe: faults must still cut. Doubles as the program
        # reader for the ident-hijack guard (returns self.program_scene).
        if req == "GetCurrentProgramScene":
            return {"currentProgramSceneName": self.program_scene}
        raise RuntimeError("nope")


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
    assert ("scene", SCENE_LIVE) in r.calls, r.calls
    r.program_scene = "SMILE | Meet"  # operator moved on mid-ident: no hijack
    live_calls = len(r.calls)
    on_ended(r, decks, IDENT_SRC)
    assert len(r.calls) == live_calls, r.calls
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
    assert ("scene", SCENE_TECHDIFF) not in [c for c in r.calls if c[0] == "scene"], r.calls
    r.pos["IDLE"] = -1  # exists but never played: measured, never faulted
    n = len(r.calls)
    assert dog.check_source("IDLE", on_air=True) is True
    assert len(r.calls) == n, r.calls
    r.pos["STUCK"] = 5  # unseen program state: faults still cut (fail safe)
    assert dog.check_source("STUCK", on_air=True) is True
    dog.last_progress["STUCK"] -= 10
    assert dog.check_source("STUCK", on_air=True) is False
    assert ("scene", SCENE_TECHDIFF) in r.calls, r.calls
    r2 = FakeRenderer()
    del r2.program_scene  # unreadable program: cut anyway, never silence
    assert Watchdog(r2)._program_is_live() is True
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=5",
                    "-t", "6", "-c:v", "libx264", "-preset", "ultrafast",
                    os.path.join(tmp, "rawsrc.mp4")], check=True)
    save_playlist({"shuffle_on_complete": False, "items": [
        {"title": "P", "source": os.path.join(tmp, "rawsrc.mp4")}]})
    st, flying, failed = {"index": 0, "deck": "A", "faults": {}}, {}, {}
    os.environ["INTAKE_MIN_FREE_BYTES"] = "1024"  # selftest runs on tmpfs
    for _ in range(45):  # prefetch resolves in background; wait it out
        prefetch_pass(load_playlist(), st, flying, failed)
        got = load_playlist()["items"][0].get("file", "")
        if got and os.path.exists(os.path.join(MEDIA, got)):
            break
        time.sleep(2)
    else:
        raise AssertionError("prefetch never delivered: %s" % flying)
    print("selftest: all checks passed.")
    return 0


def do_scene(renderer, name):
    renderer.set_scene(name)
    alert("Cut to %s." % name, "INFO")


def do_go_live(renderer):
    renderer.set_scene(SCENE_STARTING)  # ident plays; MediaInputPlaybackEnded -> LIVE
    alert("GO LIVE: ident running, LIVE armed.", "INFO")


def do_tech_diff(renderer):
    renderer.set_scene(SCENE_TECHDIFF)
    alert("TECH DIFF on air.", "WARN")


def do_resume(renderer):
    renderer.set_scene(SCENE_LIVE)  # short sting lives in the scene; no full re-intro
    alert("Resumed LIVE.", "INFO")


def do_return(renderer):
    renderer.set_scene(SCENE_PROGRAM)
    alert("Returned to PROGRAM.", "INFO")


def main():
    ap = argparse.ArgumentParser(description="Station playout daemon (lab-safe: no-ops without OBS).")
    ap.add_argument("cmd", choices=["loop", "scene", "go-live", "tech-diff",
                                    "resume", "return", "status", "watch",
                                    "selftest"],
                    help="intent to execute")
    ap.add_argument("arg", nargs="?", help="scene name for 'scene'")
    args = ap.parse_args()
    load_secrets()
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
        do_scene(r, args.arg)
    elif args.cmd == "go-live":
        do_go_live(r)
    elif args.cmd == "tech-diff":
        do_tech_diff(r)
    elif args.cmd == "resume":
        do_resume(r)
    elif args.cmd == "return":
        do_return(r)
    elif args.cmd == "loop":
        return cmd_loop(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
