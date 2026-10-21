#!/usr/bin/env python3
"""Playout daemon: scheduler + prefetch + cache + watchdog + alerts.

Owns the network, the disk, the process tree, and the playlist. The render
plane (OBS today, anything tomorrow) is a dumb renderer that only ever opens
local files handed to it through the Renderer interface below.

Usage (run from repo root, lab defaults to ./broadcast):
  python3 station/daemon.py loop            # run the 24/7 loop (blocks)
  python3 station/daemon.py scene "SMILE | Program"  # one-shot cut (exact OBS name)
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
import contextlib
import fcntl
import hashlib
import json
import os
import random
import shutil
import signal
import socket
import sqlite3
import struct
import subprocess
import sys
import threading
import time
import urllib.request

import faulthandler  # noqa: E402
# Wedge forensics: `kill -USR1 <pid>` dumps every thread's Python stack to
# stderr ("not listening", silent pl_lock holds); earlier restarts lose the
# evidence — the wedge we chased for an hour started exactly at 05:53-05:56.
try:
    faulthandler.register(signal.SIGUSR1, all_threads=True)
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stream as ytstream  # noqa: E402
import spool  # noqa: E402
import shuffler  # noqa: E402


class OBSAppError(RuntimeError):
    """The plane answered but refused the call (bad name, bad args). The
    connection itself is healthy and must STAND — only transport failures
    (OSError, closed handshake, timeouts) justify dropping it."""

ROOT = os.environ.get("BROADCAST_ROOT", os.path.join(os.getcwd(), "broadcast"))
HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
STATE = os.path.join(ROOT, "state.json")
DB = os.path.join(ROOT, "activity.db")
CONTROL = os.path.join(ROOT, "control.json")
CACHE_CAP = int(os.environ.get("CACHE_CAP_BYTES", 50 * 1024**3))
REPEAT_LIMIT = 3  # same fault 3x/hour -> OFF-AIR + escalate


# ---------------------------------------------------------------- Renderer ---
class Renderer:
    """Thin verbs the daemon needs. OBS today, anything tomorrow."""

    def set_scene(self, name): raise NotImplementedError
    def set_media_source(self, source, path): raise NotImplementedError
    def set_source_visible(self, scene, source, visible): raise NotImplementedError
    def set_mute(self, source, muted): raise NotImplementedError
    def restart_media(self, source): raise NotImplementedError
    def get_media_status(self, source): raise NotImplementedError  # {time_ms, duration_ms, state}
    def set_volume(self, source, db): raise NotImplementedError
    def pause_media(self, source): raise NotImplementedError
    def media_action(self, source, action): raise NotImplementedError  # pause|resume|restart
    def set_transition(self, style, duration_ms): raise NotImplementedError
    def get_stream_status(self): raise NotImplementedError  # {active, dropped_frames}
    def on_media_ended(self, callback): raise NotImplementedError


class _WS:
    """Minimal RFC6455 client (handshake + text frames). obs-websocket speaks
    real WebSocket framing, not line-delimited JSON — this is that."""

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, host, port, timeout=5):
        self.s = socket.create_connection((host, port), timeout=timeout)
        try:
            self._upgrade(host, port)
        except Exception:
            # A half-finished handshake must not leave the socket open:
            # obs-websocket's server hands out greetings one client at a
            # time, so a client that upgraded and never read its greeting
            # WEDGES THE PLANE for every later connection (proved live:
            # one stuck client, and no new handshake was greeted -- not
            # even after the stuck client closed).
            try:
                self.s.close()
            except OSError:
                pass
            raise

    def _upgrade(self, host, port):
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
            if len(head) > 65536:
                raise RuntimeError("websocket handshake too large")
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
            if ln > 32 * 1024 * 1024:
                raise RuntimeError("websocket frame too large (%d bytes)" % ln)
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
        # Superseded-call guard: _tls carries the caller's generation (set
        # only by overlay_server.plane_call threads); _sent_gen is the
        # newest generation that has SENT an RPC. A thread carrying an
        # older generation than one that already sent is refused — its
        # sequence outlived its deadline, and letting its tail run is how
        # a late abandoned cut overrides a retry that landed meanwhile.
        # The daemon's own calls set no generation and never see this.
        self._tls = threading.local()
        self._sent_gen = 0

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
        try:
            hello = ws.recv()
        except Exception:
            try:
                ws.close()
            except Exception:
                pass
            raise
        if hello.get("op") != 0:
            ws.close()
            raise RuntimeError("not an obs-websocket v5 server")
        identify = {"op": 1, "d": {"rpcVersion": 1, "eventSubscriptions": 256}}
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
        # hold it. Transport failures drop it; the next call reconnects.
        # Application refusals (bad names, bad args) raise OBSAppError and
        # keep the healthy connection standing.
        with self._lock:
            if self._shared is None:
                self._shared = self._connect()
            ws = self._shared
            try:
                # The guard lives INSIDE the lock: check and send are
                # atomic, so a stale RPC can never slip between its check
                # and its send. OBSAppError keeps the connection standing.
                gen = getattr(self._tls, "gen", None)
                if gen is not None:
                    if gen < self._sent_gen:
                        raise OBSAppError(
                            "superseded: a newer plane call already landed")
                    self._sent_gen = gen
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
                        raise OBSAppError("%s: %s" % (req, d["requestStatus"].get("comment")))
            except OBSAppError:
                raise
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

    def set_mute(self, source, muted):
        self._call("SetInputMute", {"inputName": source, "inputMuted": bool(muted)})

    def set_volume(self, source, db):
        self._call("SetInputVolume",
                   {"inputName": source, "inputVolumeDb": float(db)})

    def pause_media(self, source):
        self._call("TriggerMediaInputAction",
                   {"inputName": source,
                    "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"})

    def media_action(self, source, action):
        assert action in ("pause", "resume", "restart")
        name = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_" + \
            {"pause": "PAUSE", "resume": "PLAY", "restart": "RESTART"}[action]
        self._call("TriggerMediaInputAction",
                   {"inputName": source, "mediaAction": name})

    def restart_media(self, source):
        self._call("TriggerMediaInputAction",
                   {"inputName": source,
                    "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"})

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
                # Finite timeout, not None: a deaf plane must trip the
                # reconnect path, not wedge this thread forever. 90s still
                # rides out ordinary quiet (event gaps are minutes, the
                # timeout only fires on zero bytes at all).
                ws = self._connect(timeout=90)
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
def _post_webhook(hook, payload):
    try:
        urllib.request.urlopen(urllib.request.Request(
            hook, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}), timeout=10)
    except Exception as e:
        print("[WARN] discord failed: %s" % e, flush=True)


ALERT_KEEP_ROWS = 5000     # the log is a trail, not a ledger


def alert(msg, level="WARN"):
    row = (time.strftime("%Y-%m-%d %H:%M:%S"), level, msg)
    try:
        # WAL + busy timeout: the overlay server imports alert() too, so two
        # processes write this DB. Failures print; they never stall playout.
        con = sqlite3.connect(DB, timeout=5)
        try:
            con.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        con.execute("CREATE TABLE IF NOT EXISTS activity_log(ts TEXT, level TEXT, msg TEXT)")
        con.execute("INSERT INTO activity_log VALUES (?,?,?)", row)
        # Keep the log bounded: one row per item rotation, forever, is a
        # slow disk leak on a 24/7 station.
        con.execute("DELETE FROM activity_log WHERE rowid <= "
                    "(SELECT MAX(rowid) - ? FROM activity_log)", (ALERT_KEEP_ROWS,))
        con.commit()
        con.close()
    except Exception as e:
        print("[WARN] activity log write failed: %s" % e, flush=True)
    print("[%s] %s" % (level, msg), flush=True)
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        return
    emoji = {"CRIT": "\U0001f534", "WARN": "\U0001f7e1", "INFO": "\U0001f535"}[level]
    # Fire-and-forget: a dead Discord must never stall the loop for 10s.
    threading.Thread(target=_post_webhook, daemon=True, args=(hook, {
        "username": "station",
        "content": "%s **[%s]** %s" % (emoji, level, msg),
    })).start()


_hold_last = {}  # hold-alert key -> ts


def hold_alert(key, msg, level):
    """A hold state (all items dormant/missing, a cache miss) repeats on
    every pass while it lasts — an all-missing playlist used to write one
    WARN per item per pass, and a night of that erodes the 5,000-row
    evidence trail (and Discord, if hooked). First occurrence alerts;
    repeats at most hourly."""
    now = time.time()
    if now - _hold_last.get(key, 0) >= 3600:
        _hold_last[key] = now
        alert(msg, level)


# ---------------------------------------------------------------- playlist ---
def load_secrets():
    """Source broadcast/secrets.env into the environment (no-op if absent).

    Every entry point (CLI, loop, overlay server) needs OBS_PASS + webhook
    without the operator remembering to export them. An evening was lost to
    4009-auth failures from a server started bare; never again."""
    path = os.path.join(ROOT, "secrets.env")
    try:
        if os.stat(path).st_mode & 0o077:
            print("WARNING: %s is group/world-readable; chmod 600 it." % path,
                  flush=True)
    except OSError:
        pass
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
            st = json.load(f)
    except (OSError, ValueError):
        return {"index": 0, "deck": "A", "faults": {}}
    if not isinstance(st, dict):
        return {"index": 0, "deck": "A", "faults": {}}
    try:
        st["index"] = int(st.get("index", 0))
    except (TypeError, ValueError):
        st["index"] = 0  # hand-edited or torn state must not crash the loop
    return st

def save_state(state):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE)


@contextlib.contextmanager
def pl_lock():
    """Cross-process mutex for playlist+state read-modify-write cycles.

    The loop (daemon) and the operator (overlay /library, /state) share
    these files. Atomic tmp+replace saves are NOT enough: a stale in-memory
    copy saved over a fresh human edit silently eats it. Hold this around
    every load→mutate→save sequence, and re-load fresh inside it.
    Blocking is fine: holders always finish in milliseconds."""
    path = os.path.join(ROOT, ".station.lock")
    os.makedirs(ROOT, exist_ok=True)  # a fresh clone has no broadcast/ yet
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)


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
        # A deck that is idle while the queue HOLDS (a link that will not
        # resolve yet) is not stalled: faulting it escalated a healthy
        # station to OFF-AIR every time YouTube was slow.
        if HOLDING.get("since") and time.time() - HOLDING["since"] < 900:
            return True
        st = self.r.get_media_status(source)
        now = time.time()
        if st["state"] in ("missing", "OBS_MEDIA_STATE_MISSING"):
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
        with pl_lock():
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
        if not publish_expected():
            # No stream key: this is a local station, not a broken one.
            # Logging it as a CRIT every pass drowned the real alerts.
            return False
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
# six — Starting, Program, Q&A, Tech Diffs, Off Air, End Credits).
# Role mapping: STARTING holds the IDENT clip; PROGRAM plays the PLAYOUT_A/B
# deck under ticker+watermark; LIVE carries the SRT feeds under the speaking
# overlay; TECHDIFF frames faults per SCENES.md; OFF-AIR is the harbour.
SCENE_STARTING, SCENE_PROGRAM = "SMILE | Starting", "SMILE | Program"
SCENE_LIVE, SCENE_TECHDIFF = "SMILE | Q&A", "SMILE | Tech Diffs"
SCENE_OFFAIR, SCENE_END = "SMILE | Off Air", "SMILE | End Credits"
PROGRAM, DECK_A, DECK_B, IDENT_SRC = SCENE_PROGRAM, "PLAYOUT_A", "PLAYOUT_B", "IDENT"
AD_SCENE, AD_INPUT = "SMILE | Ad Break", "AD Break"
AD_STREAM_SRC = "STREAM AD"  # ad_links play here (rtmp/slot-ad)
TRANSITION = os.environ.get("TRANSITION", "Fade")
PLAYOUT_C = "PLAYOUT_C"     # third input in PROGRAM: fail-safe, never in normal rotation
FEED_WAIT = 4.0             # seconds AFTER the cut for OBS to reach OPEN/PLAYING
# ponytail: FEED_WAIT hardcoded; env knob only if a weak box ever needs tuning
FALLBACK_DEFAULT = ("loop_a.mp4", "loop_b.mp4")


def ensure_ad_plane(renderer):
    """Repair the ad surfaces the saved collection is missing.

    The Ad-break scene was created by hand in the running plane long ago
    and never captured back into the collection file (station/config debt);
    every OBS restart therefore boots WITHOUT it and every file ad fails
    with "No source `AD Break`". One idempotent repair at loop start beats
    a per-cycle face plant. Sources land default-centered — the operator
    can dress them once, then `sync.py capture` freezes them."""
    try:
        scenes = {s["sceneName"] for s in
                  renderer._call("GetSceneList").get("scenes", [])}
        ins = {i["inputName"] for i in
               renderer._call("GetInputList").get("inputs", [])}
        if AD_SCENE not in scenes:
            renderer._call("CreateScene", {"sceneName": AD_SCENE})
        if AD_INPUT not in ins:
            renderer._call("CreateInput", {
                "sceneName": AD_SCENE, "inputName": AD_INPUT,
                "inputKind": "ffmpeg_source",
                "inputSettings": {"looping": False}})  # the END event is the
                # break's return lever; a looping ad input would air forever
        if AD_STREAM_SRC not in ins:
            renderer._call("CreateInput", {
                "sceneName": AD_SCENE, "inputName": AD_STREAM_SRC,
                "inputKind": "ffmpeg_source",
                "inputSettings": {
                    "input": "rtmp://127.0.0.1:1935/slot-ad",
                    "is_local_file": False, "reconnect_delay_sec": 2}})
        # A repaired scene starts empty of the sources; attach them (idempotent)
        items = {i.get("sourceName") for i in
                 renderer._call("GetSceneItemList",
                                {"sceneName": AD_SCENE}).get("sceneItems", [])}
        for src in (AD_INPUT, AD_STREAM_SRC):
            if src not in items:
                renderer._call("CreateSceneItem", {"sceneName": AD_SCENE, "sourceName": src})
        return True
    except Exception as e:
        alert("ad surface repair failed (%s); file ads may 404." % e, "WARN")
        return False


SCENE_TICKER, SCENE_WATERMARK = "SMILE | Ticker", "SMILE | Watermark"


def ensure_overlays(renderer):
    """Ticker + watermark composited ON TOP of the program, as nested scene
    items. The collection's overlays live as standalone scenes that used to
    be shown through the exeldro downstream-keyer plugin, but its websocket
    vendor channel accepts dsk_select_scene and never persists the scene
    (silent no-op, observed live 2026-10-19) — so the air lost its tickers
    after the last OBS restart. Nested items render identically, need no
    plugin, and survive every restart by re-running here. Idempotent."""
    items = {i.get("sourceName") for i in
             renderer._call("GetSceneItemList",
                            {"sceneName": PROGRAM}).get("sceneItems", [])}
    for ov in (SCENE_TICKER, SCENE_WATERMARK):
        if ov not in items:
            renderer._call("CreateSceneItem", {"sceneName": PROGRAM,
                                               "sourceName": ov})
        renderer.set_source_visible(PROGRAM, ov, True)


def ensure_fallback_plane(renderer):
    """PLAYOUT_C lives in PROGRAM but no normal cut ever shows it: its only
    entry point is failover() inside advance(). Same repair pattern as
    ensure_ad_plane (the collection file never had it). Looping OFF — its
    ENDED event is the lever that tries the queue again."""
    try:
        ins = {i["inputName"] for i in
               renderer._call("GetInputList").get("inputs", [])}
        if PLAYOUT_C not in ins:
            renderer._call("CreateInput", {
                "sceneName": PROGRAM, "inputName": PLAYOUT_C,
                "inputKind": "ffmpeg_source",
                "inputSettings": {"looping": False}})
        items = {i.get("sourceName") for i in
                 renderer._call("GetSceneItemList",
                                {"sceneName": PROGRAM}).get("sceneItems", [])}
        if PLAYOUT_C not in items:
            renderer._call("CreateSceneItem", {"sceneName": PROGRAM,
                                               "sourceName": PLAYOUT_C})
        renderer.set_source_visible(PROGRAM, PLAYOUT_C, False)
        return True
    except Exception as e:
        alert("fallback plane repair failed (%s). Fail-safe disabled." % e, "WARN")
        return False


def evict_cache(cap=None, pinned=frozenset()):
    """Enforce the byte cap: delete LRU .mp4 files, never pinned ones.
    Returns bytes freed. .intake-tmp, playlist.json and intake.db are exempt.
    Cap resolves at CALL time (not def time): tests and small boxes retune
    CACHE_CAP live, and a stale default would silently enforce 50 GB."""
    if cap is None:
        cap = CACHE_CAP
    try:
        # Total counts EVERYTHING (pinned bytes still occupy the cap); only
        # the selection skips pinned. Counting only unpinned here passed all
        # tests with empty pin sets and silently evicted nothing otherwise.
        files = [(os.path.getmtime(os.path.join(MEDIA, f)), f)
                 for f in os.listdir(MEDIA)
                 if f.endswith(".mp4")]
    except OSError:
        return 0
    total = sum(os.path.getsize(os.path.join(MEDIA, f)) for _, f in files)
    freed = 0
    for _, f in sorted(files):
        if total <= cap:
            break
        if f in pinned:
            continue
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


def mute_stream_decks(renderer, muted):
    """Ad breaks hide streams too; failure-tolerant (legacy collections
    predate the STREAM inputs)."""
    for src in (STREAM_DECK["A"], STREAM_DECK["B"]):
        try:
            renderer.set_mute(src, muted)
        except Exception:
            pass


def plan_rolls(duration_s, data, seed=""):
    """Mid-roll schedule for one long item: seconds where an ad should cut
    in WHILE the item keeps playing (muted under cover), then return.

    Rules (ad_plan, all optional):
      threshold_min : shorter items never get mid-rolls (flat 30 min)
      mid_rolls     : how many breaks a long item may take (flat 2)
      min_gap_min   : floor between breaks AND from item start/end (flat 15)
    Placement seeded on the item identity so the /media AUTOMATION view
    shows the exact schedule the daemon will run — one planner, two users.
    """
    dur = None
    try:
        dur = float(duration_s) if duration_s else None
    except (TypeError, ValueError):
        dur = None
    if not dur or dur <= 0:
        return []
    plan = data.get("ad_plan") if isinstance(data.get("ad_plan"), dict) else {}
    if plan.get("enabled") is False:
        return []
    every = 0
    try:
        every = int(data.get("ad_every") or 0)
    except (TypeError, ValueError):
        every = 0
    if every <= 0:
        return []
    thr = _mins(plan.get("threshold_min"), 30)      # long-form threshold
    n = int(_mins(plan.get("mid_rolls"), 2))
    gap = _mins(plan.get("min_gap_min"), 15) * 60.0
    if dur < thr * 60.0 or n <= 0:
        return []
    margin = min(gap, dur / 4.0)  # never schedule past the guard rails
    lo, hi = margin, max(margin, dur - margin)
    if hi - lo < gap:
        return []  # even one break cannot fit the gap: skip weekdays of math
    rng = random.Random(hashlib.sha1(str(seed).encode()).hexdigest())
    marks = []
    for _ in range(n * 12):  # rejection sampling, bounded so no loop hangs
        t = rng.uniform(lo, hi)
        if all(abs(t - m) >= gap for m in marks):
            marks.append(t)
            if len(marks) >= n:
                break
    return sorted(marks)


def _mins(v, flat):
    """Plan-number reader: accepts numbers, falls back to the flat value."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = None
    return x if x is not None and x > 0 else flat


def roll_marks_onair(item, data):
    """Seed source for plan_rolls: stable per item, long enough to make
    identical items differ (title + url + file name)."""
    return ("%s|%s|%s" % (item.get("title"), item.get("youtube"),
                          item.get("file"),))


def play_ad(renderer, data, decks, mid=False):
    """Cut away to the ad scene and roll one ad. The pool is ad_files on
    disk AND ad_links (YouTube URLs streamed live through the same deck
    machinery — zero disk). Returns True when a break actually started
    (caller returns without advancing the index); False when ads are
    off/missing (caller plays content normally). Deck inputs are muted
    (not paused) so their clocks keep running and no watchdog fault fires
    mid-break; deck-ended events during the break are ignored by on_ended,
    and the watchdog watches the ad input instead (feed pairs use the
    stream poller, like content streams).

    mid=True marks a MID-ROLL: the break was scheduled from ad_plan at a
    percentage of the current item, not the every-N-items cycle. The
    return then resumes the SAME item instead of advancing (ad_mid flag).
    Either way the content stream record (if any) survives: it parks in
    stream_pre and comes back when the break ends — mid-break file ads
    used to wipe it, silently unlatching the feed watchdog."""
    try:
        every = int(data.get("ad_every") or 0)
    except (TypeError, ValueError):
        every = 0
    files = [f for f in (data.get("ad_files") or []) if isinstance(f, str)]
    links = [u for u in (data.get("ad_links") or [])
             if isinstance(u, str) and u]
    if (every <= 0) or (not files and not links):
        return False
    ready = [f for f in files if os.path.exists(os.path.join(MEDIA, f))]
    pool = [("file", f) for f in ready] + [("link", u) for u in links]
    if not pool:
        alert("Ad break due but no ad file on disk or link configured; "
              "playing on.", "WARN")
        with pl_lock():
            # Fresh copy here: load_state() returns a throwaway dict built
            # from the file; mutating it in place and re-loading would be a
            # no-op and leave since_ad stuck (endless re-alert).
            save_state(dict(load_state(), since_ad=0))
        return False
    kind, choice = random.choice(pool)
    with pl_lock():
        pre = load_state().get("stream")  # content record, parked for return
    if kind == "link":
        # Spawn FIRST: program keeps playing untouched until the feed is
        # live, then the break cuts in one motion (no black air).
        started = start_stream_feed(choice, "AD")
        if not started:
            alert("Ad stream failed to publish; playing on.", "WARN")
            with pl_lock():
                save_state(dict(load_state(), since_ad=0))
            return False
        feed, meta = started
        try:
            renderer.set_mute(decks["A"], True)
            renderer.set_mute(decks["B"], True)
            mute_stream_decks(renderer, True)
            renderer.set_source_visible(AD_SCENE, AD_INPUT, False)
            renderer.set_source_visible(AD_SCENE, AD_STREAM_SRC, True)
            renderer.set_scene(AD_SCENE)
        except Exception as e:
            alert("Ad break failed to start (%s); playing on." % e, "WARN")
            ytstream.stop(feed)
            _STREAM_STATE["feeds"].pop("AD", None)
            try:
                renderer.set_mute(decks["A"], False)
                renderer.set_mute(decks["B"], False)
            except Exception:
                pass
            mute_stream_decks(renderer, False)
            # We already cut to the ad scene: come back to the program, or
            # the station sits on a silent ad card until a human fixes it.
            try:
                renderer.set_scene(SCENE_PROGRAM)
            except Exception:
                pass
            return False
        with pl_lock():
            state = load_state()
            state["in_ad_break"] = True
            state["stream_pre"] = pre
            if not mid:
                state["since_ad"] = 0
            state["ad_mid"] = bool(mid)
            state["stream"] = {"start": time.time(),
                               "dur": meta.get("duration"),
                               "url": choice, "respawns": 0, "slot": "AD"}
            save_state(state)
        choice = "ad link %s" % choice
    else:
        try:
            renderer.set_media_source(AD_INPUT, os.path.join(MEDIA, choice))
            renderer.set_mute(decks["A"], True)
            renderer.set_mute(decks["B"], True)
            mute_stream_decks(renderer, True)
            renderer.set_source_visible(AD_SCENE, AD_STREAM_SRC, False)
            renderer.set_source_visible(AD_SCENE, AD_INPUT, True)
            renderer.set_scene(AD_SCENE)
            renderer.restart_media(AD_INPUT)
        except Exception as e:
            alert("Ad break failed to start (%s); playing on." % e, "WARN")
            try:
                renderer.set_mute(decks["A"], False)
                renderer.set_mute(decks["B"], False)
            except Exception:
                pass
            mute_stream_decks(renderer, False)
            # We already cut to the ad scene: come back to the program, or
            # the station sits on a silent ad card until a human fixes it.
            try:
                renderer.set_scene(SCENE_PROGRAM)
            except Exception:
                pass
            return False
        with pl_lock():
            state = load_state()
            state["in_ad_break"] = True
            state["stream_pre"] = pre
            if not mid:
                state["since_ad"] = 0
            state["stream"] = None
            if mid:
                state["ad_mid"] = True
            save_state(state)
    alert("Ad break: %s.%s" % (choice, " (mid-roll)" if mid else ""), "INFO")
    return True


# ------------- YouTube-link stream decks (zero-disk playout) ---------------
# A playlist item with a "youtube" key plays a LIVE pipe: yt-dlp resolves HLS,
# ffmpeg copy-remuxes into MediaMTX, OBS STREAM_A/B read persistent-retry.
# Advance is wall-clock (resolve() knows the duration); the poll loop also
# enqueues a sentinel when the feed dies, so both paths land in on_ended.
STREAM_DECK = {"A": "STREAM_A", "B": "STREAM_B"}
WATCH_POLL = float(os.environ.get("WATCH_POLL", "4"))
PLANE_DOWN_SECS = float(os.environ.get("PLANE_DOWN_SECS", "600"))
# The render plane can be switched OFF on purpose (the operator does not
# want the OBS window on their desktop). With this set to 0 the daemon
# stops resurrecting it: the plane stays down until it is switched back
# on by hand.
PLANE_AUTORESTART = os.environ.get("PLANE_AUTORESTART", "1") != "0"
PLANE_RESTART_COOLDOWN = float(os.environ.get("PLANE_RESTART_COOLDOWN", "1800"))
STREAM_GRACE = 8.0      # seconds past duration before wall-clock advance
last_advance = 0.0      # poll-loop thread only; refractory anchor for on_ended
last_advance_src = None  # ...for WHICH source (the one we just cut to)
STREAM_SPAWN_TRIES = 15  # 15 x 3s of path_ready polling
STREAM_EOF = "__stream__"  # sentinel routed like a deck-ended event

# ROOT already IS the broadcast dir (broadcast/), so this must not say
# "broadcast" twice: the old path was broadcast/broadcast/knobs.json,
# which never existed, and the panel's knob UI was dead.
KNOBS_PATH = os.path.join(ROOT, "knobs.json")
KNOB_KEYS = ("FEED_WAIT", "STREAM_GRACE", "STREAM_SPAWN_TRIES",
             "STREAM_PRIME_LEAD", "REPEAT_LIMIT", "WATCH_POLL",
             "PLANE_DOWN_SECS", "PLANE_RESTART_COOLDOWN")


def apply_knobs():
    """Panel-authored live overrides (broadcast/knobs.json), applied each
    loop pass. Unknown keys and junk values are ignored, never fatal."""
    try:
        with open(KNOBS_PATH) as f:
            knobs = json.load(f)
    except (OSError, ValueError):
        return
    if not isinstance(knobs, dict):
        return
    g = globals()
    for k, v in knobs.items():
        if k not in KNOB_KEYS or not isinstance(v, (int, float)) or v < 0:
            continue
        if k == "REPEAT_LIMIT":
            g[k] = max(int(v), 1)
        else:
            g[k] = max(min(float(v), 3600), 0.5)
_STREAM_STATE = {"feeds": {}, "resolving": {}, "respawning": {},
                 "primed": None}   # {"deck","url","meta","feed"} ready-to-cut
# "respawning": deck -> the one background respawn attempt in flight for
# it. The playout pass only detects a dead feed, counts the attempt and
# kicks the thread; the resolve+spawn+ready-wait happens OFF the pass
# (stream_respawn_pass below).
STREAM_PRIME_LEAD = float(os.environ.get("STREAM_PRIME_LEAD", "30"))
_RESOLVE_CACHE = {}  # url -> (epoch, meta)
_RESOLVE_TTL = 1800  # HLS URLs expire in hours; refresh sooner


def cached_resolve(url, force=False):
    """resolve() with a half-hour TTL cache, so cuts never wait on a resolve.
    force=True skips the cache READ (a respawn prefers FRESH urls: a mid-stream
    403 inside the TTL window would otherwise respawn the same dead urls every
    poll until the item hit the fault limit). On resolve FAILURE the cached
    meta is still returned -- honest for HLS (urls expire in hours, the cache
    is 30 minutes, so a blip resolve is worth one retry with the old urls);
    repeated death still walks to the attempt cap and ends the item."""
    if not force:
        deadline, meta = _RESOLVE_CACHE.get(url, (0, None))
        # A live stream's HLS urls EXPIRE (hours). The old "live means keep
        # it forever" short-circuit handed every respawn the same dead urls,
        # so a feed could never come back. Age it like everything else.
        if meta and (deadline + _RESOLVE_TTL > time.time()
                     or (meta.get("live") and meta.get("hls_at", 0)
                         > time.time() - 1800)):
            return meta
    meta = ytstream.resolve(url)
    if meta and meta.get("hls_v") and meta.get("hls_a"):
        _RESOLVE_CACHE[url] = (time.time(), meta)
        return meta
    return _RESOLVE_CACHE.get(url, (0, None))[1]


def stop_feed(deck):
    feed = _STREAM_STATE["feeds"].pop(deck, None)
    ytstream.stop(feed)


# Media-ended events queue here; main()'s poll loop drains it. Module-level
# (was a main() local): the background respawn thread routes its give-up
# STREAM_EOF from outside main(), which is impossible with a closure list
# and is exactly why the whole respawn used to sit inline on the playout
# pass.
_ENDED = []


def _respawn_give_up(url, deck, n):
    """Route the give-up EOF from a failed respawn attempt -- but only if
    the item this attempt was for is STILL the one on air. The world moves
    on during a 60s resolve (operator skip, wall-clock advance, ad return):
    a late EOF for a dead item would advance past whatever is on air now."""
    try:
        _st = load_state()
    except (OSError, ValueError):
        _st = {}
    _sm = _st.get("stream") or {}
    if not (_sm.get("url") == url
            and (_sm.get("slot") or _st.get("deck")) == deck):
        return
    alert("Stream feed died and respawn failed.", "CRIT")
    with END_LOCK:
        if STREAM_EOF not in _ENDED:
            alert("Stream feed exhausted (%s); ending item." % deck, "WARN")
            _ENDED.append(STREAM_EOF)


def _respawn_work(url, deck, n):
    """One background respawn attempt: fresh resolve, spawn, wait for
    MediaMTX to publish. Runs OFF the playout pass -- the inline version
    did all of this between two poll iterations, and a dead network froze
    the deck (and every other loop duty: control, advance, fail-safe)
    for up to ~3x20s resolve + 15x3s ready per attempt.

    Cleanup is by PROC IDENTITY, never by deck key: while this attempt is
    still in its ready-wait the world can hand the deck to a new item
    (operator skip, ad return), and a deck-keyed stop would kill the
    successor's feed."""
    path = ("slot-ad" if deck == "AD"
            else "slot-stream-%s" % deck.lower())
    feed = None   # kept outside the try: the crash path stops it by identity
    try:
        meta = cached_resolve(url, force=True)
        if meta and meta.get("hls_v") and meta.get("hls_a"):
            feed = ytstream.spawn(url, path, meta=meta)
        ok = False
        if feed is not None:
            # Adopt early: while the ready-wait runs, the main loop's death
            # check must see a live proc, not re-detect the corpse.
            _STREAM_STATE["feeds"][deck] = feed
            for _ in range(STREAM_SPAWN_TRIES):
                if ytstream.path_ready(path):
                    ok = True
                    break
                if feed.poll() is not None:
                    break
                time.sleep(3)
        if not ok:
            if feed is not None:
                ytstream.stop(feed)
                if _STREAM_STATE["feeds"].get(deck) is feed:
                    _STREAM_STATE["feeds"].pop(deck, None)
            _respawn_give_up(url, deck, n)
            return
        try:
            _st = load_state()
        except (OSError, ValueError):
            _st = {}
        _sm = _st.get("stream") or {}
        if _sm.get("url") == url and (_sm.get("slot") or _st.get("deck")) == deck:
            alert("Stream feed died; respawned (%d)." % n, "WARN")
        else:
            # Finished late: the item moved on while this attempt was
            # waiting. Stop MY proc by identity; the deck's current entry
            # belongs to whatever is on air now and is not touched.
            if _STREAM_STATE["feeds"].get(deck) is feed:
                _STREAM_STATE["feeds"].pop(deck, None)
            ytstream.stop(feed)
            alert("Respawn %d finished late (%s); item moved on, feed dropped."
                  % (n, deck), "INFO")
    except Exception as e:
        # A crashed respawn thread would leave the deck with neither a
        # recovery nor an EOF: route the give-up exactly like a failure,
        # and stop anything this attempt already spawned (by identity --
        # the deck's current entry may belong to a successor by now).
        alert("respawn %d crashed: %s" % (n, e), "WARN")
        if feed is not None:
            ytstream.stop(feed)
            if _STREAM_STATE["feeds"].get(deck) is feed:
                _STREAM_STATE["feeds"].pop(deck, None)
        try:
            _respawn_give_up(url, deck, n)
        except Exception:
            pass
    finally:
        _STREAM_STATE["respawning"].pop(deck, None)


def stream_respawn_pass(_sm, _deck):
    """Feed-death handling for the on-air stream item. Runs on the playout
    pass; every slow part happens on the respawn thread, so the pass never
    blocks (the inline version spent up to ~4 min inside one iteration on
    a dead network). One attempt per deck at a time; two per item before
    the item is ended -- the inline contract, kept."""
    _rt = _STREAM_STATE["respawning"].get(_deck)
    if _rt is not None:
        if _rt.is_alive():
            return  # a background attempt owns this deck's recovery
        _STREAM_STATE["respawning"].pop(_deck, None)  # finished; reap
    _urls = _sm.get("url")
    if int(_sm.get("respawns") or 0) < 2:
        with pl_lock():
            # Persist the bump on a FRESH load: this used to mutate the
            # throwaway load_state() dict only, so every pass saw
            # respawns=0 and a dead feed was respawned on every poll.
            _sv = load_state()
            _svsm = _sv.get("stream") or {}
            _svsm["respawns"] = int(_svsm.get("respawns") or 0) + 1
            _sv["stream"] = _svsm
            save_state(_sv)
        _n = _svsm["respawns"]
        _sm["respawns"] = _n
        alert("Stream feed died; respawn %d starting in background." % _n,
              "WARN")
        _t = threading.Thread(target=_respawn_work, args=(_urls, _deck, _n),
                              daemon=True)
        _STREAM_STATE["respawning"][_deck] = _t
        _t.start()
    else:
        alert("Stream feed exhausted (%s); ending item." % _deck, "WARN")
        with END_LOCK:
            if STREAM_EOF not in _ENDED:
                _ENDED.append(STREAM_EOF)


def start_stream_feed(url, deck, meta=None, fresh=False):
    """Spawn on the deck's MTX path and wait until MediaMTX publishes.
    Returns (feed, meta) or None on spawn/ready failure. deck "AD" is the
    ad-break slot (same pipeline, landed in the ad scene). fresh=True
    forces a re-resolve instead of trusting the caller's meta.

    Used by the CUT paths (advance, prime, ad break) -- all of which may
    block the pass for the ready-wait, an accepted cost at a transition.
    The RESPAWN path must not: it runs through _respawn_work, off the
    playout pass, with proc-identity cleanup (a deck-keyed stop here would
    kill a successor feed if the world moved on mid-wait)."""
    meta = meta or cached_resolve(url, force=fresh)
    if not meta:
        return None
    path = ("slot-ad" if deck == "AD"
            else "slot-stream-%s" % deck.lower())
    feed = ytstream.spawn(url, path, meta=meta)
    if not feed:
        return None
    _STREAM_STATE["feeds"][deck] = feed
    for _ in range(STREAM_SPAWN_TRIES):
        if ytstream.path_ready(path):
            return feed, meta
        if feed.poll() is not None:
            ytstream.stop(feed)
            _STREAM_STATE["feeds"].pop(deck, None)
            return None
        time.sleep(3)
    stop_feed(deck)  # spawned but never published: no black frames on air
    return None


def prefetch_stream_pass(data, state):
    """Resolve upcoming youtube items in the background so advance never
    blocks on a resolve. One dict of in-flight threads, best-effort: a
    missed resolve is simply re-attempted inline at advance time."""
    # Prune the cache while here: entries past their TTL that a cached_resolve
    # would no longer serve are dead weight (months of URLs accumulate to
    # tens of MB and every lookup walks a map that never shrinks).
    now = time.time()
    for u in list(_RESOLVE_CACHE):
        deadline, meta = _RESOLVE_CACHE[u]
        fresh_live = (meta.get("live") and meta.get("hls_at", 0)
                      > now - 1800)
        if not (deadline + _RESOLVE_TTL > now or fresh_live):
            del _RESOLVE_CACHE[u]
    items = data.get("items", [])
    n = len(items)
    if not n:
        return
    sidx = state.get("index", 0)
    for o in (0, 1):  # next up and the one after
        item = items[(sidx + o) % n]
        url = item.get("youtube")
        if not url or url in _RESOLVE_CACHE:
            continue
        if _STREAM_STATE["resolving"].get(url):
            continue

        def _go(u=url):
            try:
                cached_resolve(u)
            except Exception:
                pass
            _STREAM_STATE["resolving"].pop(u, None)

        t = threading.Thread(target=_go, daemon=True)
        _STREAM_STATE["resolving"][url] = t
        t.start()


def prime_next_stream(payload, cur, deck):
    """Feed the idle deck with the NEXT stream item so the transition is a
    deck flip, not a resolve+spawn+reconnect gap (observed as black bars
    when a single stream item looped on itself 2026-10-19).
    Best-effort: a failed prime just leaves advance() to spawn live."""
    items = payload.get("items", [])
    if not items:
        return
    n = len(items)
    st = load_state()
    idx = int(st.get("index") or 0)
    nxt = items[idx % n]
    url = nxt.get("youtube")
    if not url:
        return
    other = "A" if deck == "B" else "B"
    stop_feed(other)
    try:
        started = start_stream_feed(url, other, meta=None)
    except Exception as e:
        alert("Prime failed (deck %s): %s" % (other, e), "WARN")
        return
    if started:
        _STREAM_STATE["primed"] = {"deck": other, "url": url,
                                   "meta": started[1], "feed": started[0]}
        alert("Primed deck %s for next stream: %s."
              % (other, nxt.get("title") or url), "INFO")
    else:
        alert("Prime failed (deck %s); advance will spawn live." % other, "WARN")


def stream_item_on_air(items, state):
    """True when the item playing (index-1) streams live. A YouTube item
    with a complete spool plays as a FILE (advance() swaps to the local
    copy), so the naive youtube check would call a cached item a stream —
    blocking deck transport and dropping the poll backstop for it (seen:
    pause refused on-air an spooled item at 05:44)."""
    n = len(items)
    if not n:
        return False
    idx = ((state.get("index", 0) or 0) - 1) % n
    item = items[idx]
    url = item.get("youtube")
    if url is None:
        return False
    if item.get("spool") is False:
        return True
    return spool.ready(url) is None


def media_ready(renderer, source, wait=None, poll=0.5):
    """True once `source`'s media state shows the file actually loaded.
    The only state a broken/absent/unbufferable file never reaches is
    open/playing — measured, not assumed. The poll exists because the
    alternative was cutting blind and letting the watchdog burn 8 REPEAT
    faults per stall on air (observed live 2026-10-18)."""
    if wait is None:
        wait = float(globals().get("FEED_WAIT", 4))
    deadline = time.time() + wait
    while True:
        try:
            st = str(renderer.get_media_status(source).get("state", ""))
            st = st.lower().replace("obs_media_state_", "")
            if st in ("open", "playing"):
                return True
        except Exception:
            pass
        if time.time() >= deadline:
            return False
        time.sleep(poll)


def studio_mode_off(renderer):
    """OBS Studio Mode splits preview/program; deck cuts then look like
    'preview has content, program black' to the operator. Guard at boot."""
    try:
        if renderer._call("GetStudioModeEnabled").get("studioModeEnabled"):
            renderer._call("SetStudioModeEnabled", {"studioModeEnabled": False})
            alert("Studio mode was ON; turned it off — deck cuts don't do "
                  "preview/program pairs.", "WARN")
    except Exception:
        pass


def _ensure_filters(renderer, source, chain):
    """chain: ((filterName, filterKind, settings), ...). Idempotent — create
    what is missing, re-tune what is already there. Filter kinds are OBS's
    real ids ('compressor_filter', 'limiter_filter', ...): anything else is
    refused with "filter kind is not supported by OBS". Returns the number
    of filters created here."""
    try:
        have = {f.get("filterName") for f in renderer._call(
            "GetSourceFilterList", {"sourceName": source}).get("filters", [])}
    except Exception as e:
        alert("filters unreadable on %s: %s." % (source, e), "WARN")
        return 0
    made = 0
    for fname, fkind, settings in chain:
        if fname not in have:
            try:
                renderer._call("CreateSourceFilter", {
                    "sourceName": source, "filterName": fname,
                    "filterKind": fkind, "filterSettings": settings})
                have.add(fname)
                made += 1
            except Exception as e:
                alert("filter %s on %s failed: %s." % (fname, source, e), "WARN")
                continue
        try:
            renderer._call("SetSourceFilterSettings", {
                "sourceName": source, "filterName": fname,
                "filterSettings": settings, "overlay": False})
        except Exception as e:
            alert("filter %s on %s could not be tuned: %s."
                  % (fname, source, e), "WARN")
    return made


def clear_fault_history(why=""):
    """Drop the fault history. Used when the faults were caused by a
    render plane that was switched off on purpose: they are not station
    faults, and leaving them would trip the REPEAT_LIMIT off-air
    escalation on the first real fault after the plane returns."""
    try:
        with pl_lock():
            st = load_state()
            if st.get("faults"):
                st["faults"] = {}
                save_state(st)
                alert("Fault history cleared (%s)." % (why or "stale faults"),
                      "INFO")
    except Exception:
        pass


def apply_mic_normalizer(renderer):
    """Host microphones vary wildly and nobody is at the mixer: every local
    audio-input source gets suppress + compressor + limiter, idempotently
    (filters persist with the collection; existing ones are re-tuned).
    A plane with no mic input says so instead of staying silent."""
    chain = (
        ("AStation NoiseSuppress", "noise_suppress_filter", {}),
        ("AStation Mic Compressor", "compressor_filter",
         {"threshold": -20.0, "ratio": 4.0, "attack": 10.0,
          "release": 120.0, "output_gain": 0.0}),
        ("AStation Mic Limiter", "limiter_filter",
         {"threshold": -1.5, "release": 60.0}),
    )
    try:
        inputs = renderer._call("GetInputList").get("inputs", [])
    except Exception as e:
        alert("mic normalizer skipped: %s." % e, "WARN")
        return
    mics = [i.get("inputName") for i in inputs
            if (i.get("inputKind") or "").startswith(
                ("wasapi_input", "alsa_input", "pulse_input"))]
    if not mics:
        alert("No microphone input on this plane; mic normalizer skipped.", "INFO")
        return
    for name in mics:
        _ensure_filters(renderer, name, chain)
    alert("Microphone normalizer armed on %s." % ", ".join(mics), "INFO")


HEARTBEAT = os.path.join(ROOT, "heartbeat.json")


def apply_deck_normalizer(renderer):
    """Link items and uploaded files arrive at wildly different loudness:
    spooled ones are lifted at intake, but raw YouTube streams can't be
    loudnorm'd live. Attach compress + limit (Spotify-style dynamics, no
    intensity lift) to every playback input, idempotently, so nobody has
    to ride the fader. Compressor tames the jumps, limiter keeps peaks at
    -1.5 dBTP. Runs on the same boot pass as the mic normalizer."""
    chain = (
        ("AStation Compressor", "compressor_filter",
         {"threshold": -16.0, "ratio": 3.0, "attack": 25.0,
          "release": 250.0, "output_gain": 0.0}),
        ("AStation Limiter", "limiter_filter",
         {"threshold": -1.5, "release": 60.0}),
    )
    targets = [DECK_A, DECK_B, PLAYOUT_C,
               STREAM_DECK["A"], STREAM_DECK["B"]]
    try:
        names = {inp.get("inputName") for inp
                 in renderer._call("GetInputList").get("inputs", [])}
    except Exception as e:
        alert("deck normalizer skipped: %s." % e, "WARN")
        return
    here = [t for t in targets if t in names]
    missing = [t for t in targets if t not in names]
    made = 0
    for src in here:
        made += _ensure_filters(renderer, src, chain)
    if here:
        alert("Deck normalizer armed on %s (compress -16dB/3:1 -> limit -1.5dB)."
              % ", ".join(here), "INFO")
    if missing:
        alert("deck normalizer: %s not on this plane." % ", ".join(missing), "WARN")


def remove_deck_normalizer(renderer):
    """Take the station-wide loudness chain back off: the dock's switch is
    a real off, not a "stop doing it from now on"."""
    targets = [DECK_A, DECK_B, PLAYOUT_C,
               STREAM_DECK["A"], STREAM_DECK["B"]]
    names = ("AStation Compressor", "AStation Limiter")
    try:
        present = {inp.get("inputName") for inp
                   in renderer._call("GetInputList").get("inputs", [])}
    except Exception as e:
        alert("deck normalizer off failed: %s." % e, "WARN")
        return
    gone = []
    for src in targets:
        if src not in present:
            continue
        for fname in names:
            try:
                renderer._call("RemoveSourceFilter",
                               {"sourceName": src, "filterName": fname})
                gone.append(src)
            except Exception:
                pass
    if gone:
        alert("Deck normalizer off (removed from %s)." % ", ".join(sorted(set(gone))))


NORM_FILE = os.path.join(ROOT, "normalize.json")


def normalize_on(default=True):
    """The station-wide loudness switch, kept in its own file: state.json
    merges delete keys they don't carry, so a switch stored there would
    be wiped by the next unrelated save."""
    try:
        with open(NORM_FILE) as f:
            v = json.load(f)
        return bool(v.get("on"))
    except Exception:
        return default


def write_normalize(on):
    try:
        with open(NORM_FILE + ".tmp", "w") as f:
            json.dump({"on": bool(on), "t": time.time()}, f)
        os.replace(NORM_FILE + ".tmp", NORM_FILE)
    except OSError:
        pass


def set_deck_normalizer(renderer, on):
    """The station-wide loudness switch. On: compress+limit on every
    playback input (Spotify-style dynamics, no intensity lift). Off: the
    chain is removed again. The choice is remembered across restarts."""
    if on:
        apply_deck_normalizer(renderer)
    else:
        remove_deck_normalizer(renderer)
    write_normalize(bool(on))


def publish_expected():
    """Is this station supposed to be publishing at all? Without a real
    YouTube stream key it is a LOCAL station, and "the output is not
    active" is not a fault worth alerting on."""
    key = os.environ.get("YOUTUBE_STREAM_KEY", "") or ""
    return bool(key) and not key.startswith("paste-once") and key != "change-me"


def ensure_stream_output(renderer):
    """Give the station its YouTube output when it has a real key.

    The render plane ships with no RTMP output: the station was never
    publishing, it was only LOOKING like a broadcaster (and logging
    "Stream output not active!" every pass). With a key in secrets.env
    the output is created once at boot; without one the station stays
    local and quiet."""
    if not publish_expected():
        return
    try:
        outs = renderer._call("GetOutputList").get("outputs", [])
    except Exception:
        return
    for o in outs:
        if o.get("outputKind") in ("rtmp_output", "rtmp_custom"):
            return                      # already there
    try:
        renderer._call("CreateOutput", {
            "outputName": "YouTube",
            "outputKind": "rtmp_output",
            "outputSettings": {
                "server": "rtmp://a.rtmp.youtube.com/live2",
                "key": os.environ.get("YOUTUBE_STREAM_KEY", "")}})
        alert("YouTube output created — the station is publishing.", "INFO")
    except Exception as e:
        alert("Could not create the YouTube output: %s" % e, "WARN")


def refresh_item_metadata(url, alert_fn=None):
    """Re-resolve one item's metadata and store it on the playlist item
    (title, description, channel, duration, checked-at). This is the
    operator's manual "refresh this video's details" button; the same
    fields are filled in by the title watcher as it goes."""
    meta = ytstream.resolve(url)
    if not meta:
        if alert_fn:
            alert_fn("Could not refresh the metadata for that link.", "WARN")
        return None
    with pl_lock():
        data = load_playlist()
        for it in data.get("items") or []:
            if it.get("youtube") == url:
                it["title"] = meta.get("title") or it.get("title")
                it["desc"] = meta.get("description") or it.get("desc") or ""
                it["channel"] = meta.get("channel") or it.get("channel") or ""
                if meta.get("duration"):
                    it["duration"] = meta["duration"]
                it["meta_checked"] = int(time.time())
                save_playlist(data)
                if alert_fn:
                    alert_fn("Metadata refreshed for “%s”." % it.get("title"), "INFO")
                return it
    if alert_fn:
        alert_fn("That link is not in the playlist any more.", "WARN")
    return None


def ensure_bed_isolation(renderer):
    """The music bed belongs to the waiting-room scenes (Starting / Off
    Air / End Credits / Tech Diffs) and nowhere else: program, ad break
    and the live scene all carry their own audio, and a bed under them
    fights it. If a bed input ever ended up there, take it out."""
    bed = "Music Bed"
    for scene in (SCENE_PROGRAM, AD_SCENE, SCENE_LIVE):
        try:
            items = renderer._call(
                "GetSceneItemList", {"sceneName": scene}).get("sceneItems", [])
        except Exception:
            continue
        for it in items:
            if it.get("sourceName") == bed and it.get("sceneItemEnabled"):
                try:
                    renderer._call("SetSceneItemEnabled", {
                        "sceneName": scene, "sceneItemId": it["sceneItemId"],
                        "sceneItemEnabled": False})
                    alert("Music bed disabled in %s: it must not fight the "
                          "program audio." % scene, "WARN")
                except Exception:
                    pass


def cover_idle_deck(renderer, state, decks):
    """The programme must never be black.

    The question is NOT "is the deck idle" -- a deck can be busy
    playing a FROZEN file (the watchdog's "stalled at 41ms"), and that is
    just as black. The question is: is ANY of the programme visible? If
    not, the fail-safe takes the air with its holding card until the
    item is ready. The index is NOT moved: the item is pending, not
    skipped."""
    try:
        items = renderer._call(
            "GetSceneItemList", {"sceneName": SCENE_PROGRAM}).get("sceneItems", [])
        visible = {i.get("sourceName") for i in items if i.get("sceneItemEnabled")}
    except Exception:
        return
    programme = {DECK_A, DECK_B, PLAYOUT_C,
                 STREAM_DECK["A"], STREAM_DECK["B"]}
    # A visible source only counts as "on air" if it is actually MOVING.
    # A deck that is visible but frozen (the watchdog's "stalled at 41ms")
    # is just as black as an idle one -- and after a plane restart the
    # collection restores the deck VISIBLE, so the cover would never
    # engage and the station would sit on a frozen frame.
    for src in sorted(visible & programme):
        try:
            m = renderer.get_media_status(src)
        except Exception:
            continue
        pos = int(m.get("time_ms") or 0)
        prev = _LAST_POS.get(src)
        _LAST_POS[src] = pos
        if m.get("state") == "OBS_MEDIA_STATE_PLAYING" and (prev is None or pos != prev):
            return          # it is playing AND moving: no black to cover
    # NOTE: the state's fallback_air flag is NOT consulted here. After a
    # plane restart the flag still says "the fail-safe is holding" while
    # the scene says it is not -- and the cover would never engage, so
    # the station sat black with the flag claiming otherwise.
    try:
        # move_index=False: the cover is not a failure, so the cursor
        # must stay on the item that is still pending.
        failover(renderer, state, decks, max(0, int(state.get("index") or 0) - 1),
                 move_index=False)
    except Exception:
        pass


def probe_plane(renderer):
    """Dump what the plane actually looks like: input names, the filters
    riding on them, and the filter kinds this OBS build offers. The ws
    server greets new clients unreliably (it usually answers the one
    long-lived connection and leaves the rest hanging), so the daemon —
    which owns that connection — is the only one able to ask. Writes
    broadcast/obs_probe.json; also answers the {"probe": true} control
    verb so the dock/ops can re-read it on demand."""
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    inputs = []
    try:
        inputs = renderer._call("GetInputList").get("inputs", [])
    except Exception as e:
        rep["input_list_error"] = str(e)
    rep["inputs"] = [{"name": i.get("inputName"), "kind": i.get("inputKind"),
                      "type": i.get("inputType")} for i in inputs]
    filt = {}
    for i in inputs:
        name = i.get("inputName")
        try:
            fl = renderer._call(
                "GetSourceFilterList", {"sourceName": name}).get("filters", [])
            filt[name] = [{"name": f.get("filterName"), "kind": f.get("filterKind"),
                           "settings": f.get("filterSettings")} for f in fl]
        except Exception as e:
            filt[name] = "err: %s" % str(e)[:120]
    rep["filters"] = filt
    if inputs:
        try:
            rep["filter_kinds"] = renderer._call(
                "GetSourceFilterKindList",
                {"sourceName": inputs[0].get("inputName")}).get("sourceFilterKinds", [])
        except Exception as e:
            rep["filter_kinds_error"] = str(e)
    path = os.path.join(ROOT, "obs_probe.json")
    try:
        with open(path + ".tmp", "w") as f:
            json.dump(rep, f, indent=1, default=str)
        os.replace(path + ".tmp", path)
    except Exception as e:
        alert("probe write failed: %s." % e, "WARN")
    return rep


PASS_STATE = {"ms": 0, "what": "", "since": 0.0}
ON_AIR = {"src": None, "pos_ms": 0, "dur_ms": 0, "state": ""}
# Set while the queue HOLDS for a link that will not resolve yet. A deck
# that is idle because we are waiting is not stalled, and faulting it
# would escalate a healthy station to OFF-AIR for a slow YouTube.
HOLDING = {"since": 0.0, "why": ""}
# Last seen media position per source, to tell "playing" from "frozen".
_LAST_POS = {}


def touch_heartbeat():
    """Liveness marker the panel/dock read to tell 'daemon wedged' apart
    from 'panel unreachable'. Carries the last poll pass: a pass that is
    merely SLOW (a busy plane, a long OBS call) must not be reported as a
    dead daemon — the dock shows that as BUSY, not STALLED."""
    try:
        with open(HEARTBEAT + ".tmp", "w") as f:
            json.dump({"t": time.time(),
                       "pass_ms": PASS_STATE.get("ms", 0),
                       "busy": PASS_STATE.get("what", ""),
                       "onair": dict(ON_AIR)}, f)
        os.replace(HEARTBEAT + ".tmp", HEARTBEAT)
    except OSError:
        pass


def heartbeat_thread():
    """The heartbeat is written by its own thread, not by the poll loop:
    a pass blocked on a wedged plane then still proves the process is
    alive, and the dock can say 'busy' instead of 'not responding'."""
    while True:
        touch_heartbeat()
        time.sleep(1.0)


def _normalize_media(name, title=None):
    """Dock row-menu loudness pass. file items take the in-place ffmpeg
    pass; link items force a re-spool (fetches fresh from YouTube through
    the loudnorm'd faststart). Refuses whatever is on air. Runs on a
    thread so the poll loop never stalls."""
    url = None
    base = None
    import spool as _sp
    if isinstance(name, str) and name.startswith("http"):
        url = name
        info = _sp.ready(url)
        if not info:
            alert("Normalize skipped: that link has no local copy yet — "
                  "cut to it once so the spool builds, or it streams live.",
                  "WARN")
            return
        base = os.path.basename(info["path"])
    else:
        base = os.path.basename(str(name))
        if not base.endswith(".mp4") or "/" in base:
            alert("Normalize refused: %s is not a media file." % name, "WARN")
            return
    src = os.path.join(MEDIA, base)
    tmp = src + ".norm.mp4"
    try:
        _st = load_state()
        with pl_lock():
            _items = load_playlist().get("items") or []
        _onitem = (_items[max(0, (int(_st.get("index") or 1)) - 1)] or {})
        _onfile = _onitem.get("file")
        onair = ((_onfile == base) or (url and _onitem.get("youtube") == url))
    except Exception:
        onair = False
    if onair:
        alert("Normalize skipped: %s is on air right now." % base, "WARN")
        return

    def work():
        try:
            if url is not None:
                import spool as _sp2
                _sp2.renormalize(url, title, alert)
                return
            if not _sp._has_audio(src):
                alert("Normalize skipped: %s has no audio stream." % base, "WARN")
                return
            alert("Normalizing loudness: %s (runs ~30s)." % base)
            p = subprocess.run(
                [_sp.FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", src,
                 "-map", "0:v", "-c:v", "copy", "-map", "0:a",
                 "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                 "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-f", "mp4", tmp],
                capture_output=True, text=True, timeout=900)
            if p.returncode == 0 and os.path.getsize(tmp) > 0:
                os.replace(tmp, src)
                alert("Normalized: %s — plays at the new target on its "
                      "next cut." % base)
            else:
                alert("Normalize failed: %s: %s" % (
                    base, (p.stderr or "")[-120:]), "WARN")
        except subprocess.TimeoutExpired:
            alert("Normalize timed out: %s." % base, "WARN")
        except Exception as e:
            alert("Normalize error on %s: %s" % (base, e), "WARN")
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    threading.Thread(target=work, daemon=True).start()


_SWEEP_DAY = None   # the day of the last full metadata sweep


def _title_watch_pass():
    global _SWEEP_DAY
    """One metadata watch cycle: re-resolve YouTube items that carry a
    stored title and flag the ones whose title changed (dragged to
    Available + meta_trip marker; the dock renders Approve/Discard).
    Bound: at most 3 fresh resolves and 2 trips per cycle, and never trip
    the on-air item."""
    with pl_lock():
        items = list((load_playlist().get("items") or []))
    st = load_state()
    onidx = max(0, (int(st.get("index") or 1)) - 1)
    # Once a day, walk the whole list: the operator wants to know that a
    # video's metadata is still current, not only when it happens to
    # change. The daily pass resolves more items per cycle; the rest of
    # the day stays cheap.
    today = time.strftime("%Y-%m-%d")
    sweep = _SWEEP_DAY != today
    if sweep:
        _SWEEP_DAY = today
    limit = 20 if sweep else 3
    fresh = 0
    tripped = []
    for pos, it in enumerate(items):
        url = it.get("youtube")
        old = it.get("title")
        if not url or not old or it.get("meta_trip") or url in tripped:
            continue
        meta = _RESOLVE_CACHE.get(url, (0, None))[1]
        if meta is None:
            if fresh >= limit:
                continue
            fresh += 1
        try:
            meta = cached_resolve(url)
        except Exception:
            continue
        if pos == onidx:
            continue
        new = (meta or {}).get("title")
        if new and new == old:
            # Nothing changed, but the description may never have been
            # captured: the dock's preview panel shows it.
            with pl_lock():
                data = load_playlist()
                touched = False
                for cand in data.get("items") or []:
                    if (cand.get("youtube") == url and
                            cand.get("title") == old and
                            not cand.get("desc") and
                            (meta or {}).get("description")):
                        cand["desc"] = (meta or {}).get("description") or ""
                        cand["channel"] = (meta or {}).get("channel") or ""
                        cand["meta_checked"] = int(time.time())
                        touched = True
                        break
                if touched:
                    save_playlist(data)
        if new and new != old:
            # A renamed video is usually the SAME video: let it keep
            # playing and just flag it. But if the DURATION also changed,
            # this is a different upload wearing the old name — that one
            # is held back (parked) until the operator approves it.
            old_dur = it.get("duration")
            new_dur = (meta or {}).get("duration")
            same_video = not (old_dur and new_dur and
                              abs(float(old_dur) - float(new_dur)) > 1.0)
            with pl_lock():
                data = load_playlist()
                for cand in data.get("items") or []:
                    if (cand.get("youtube") == url and
                            cand.get("title") == old and
                            not cand.get("meta_trip")):
                        cand["meta_trip"] = {"old": old, "new": new,
                                             "same_video": bool(same_video)}
                        if not same_video:
                            # A different video under the old name: hold it
                            # until it is approved, and keep it out of the
                            # groups so it cannot air from a playlist.
                            cand["status"] = "dormant"
                            cand.pop("group", None)
                            cand.pop("gorder", None)
                        save_playlist(data)
                        if same_video:
                            alert("Title changed on YouTube: “%s” is now "
                                  "“%s”. Same video, same length — it keeps "
                                  "playing, flagged for review." % (old, new), "INFO")
                        else:
                            alert("Title changed on YouTube: “%s” is now "
                                  "“%s” AND the duration changed (%s -> %s): "
                                  "that is a different video, so it is held "
                                  "back until you approve it." % (
                                      old, new, old_dur, new_dur), "WARN")
                        break
            tripped.append(url)
            if len(tripped) >= 2:
                break


def _title_watch():
    while True:
        time.sleep(float(os.environ.get("TITLE_WATCH_SECS", "300")))
        try:
            _title_watch_pass()
        except Exception as e:
            alert("title watch failed: %s." % e, "WARN")


def park_decks(renderer, deck, src, deck_sources):
    """Parked slots stay PARKED: the hidden decks are muted (clocks keep
    running) so exactly one thing on air is audible. Deliberately NOT
    paused — the watchdog reads a frozen cursor as "stalled" and escalates
    to OFF-AIR on a deck that is merely parked (the lab invariant:
    "muted (not paused) so their clocks keep running and no watchdog fault
    fires"). Runs at every cut in advance() — and once at boot."""
    other = "B" if deck == "A" else "A"
    parked = [deck_sources[other], STREAM_DECK[other]]
    parked.append(STREAM_DECK[deck] if src is deck_sources[deck]
                  else deck_sources[deck])
    for s in {id(s): s for s in parked}.values():  # dedupe, keep order
        try:
            if renderer.get_media_status(s).get(
                    "state") == "OBS_MEDIA_STATE_PAUSED":
                # A paused parked deck heals into this exact freeze the
                # mute invariant was written against: cursor parked, clock
                # stopped, watchdog says "stalled", OFF-AIR escalates on a
                # deck nobody is watching. RESTART is the proven unpause.
                renderer.restart_media(s)
        except Exception:
            pass
        try:
            renderer.set_mute(s, True)
        except Exception:
            pass
    try:
        renderer.set_mute(src, False)
    except Exception:
        pass


def fallback_files():
    """PLAYOUT_C pool: playlist.json `"fallback": [...]` overrides; default
    is the evergreen loop cards. A missing or corrupt playlist means the
    DEFAULTS, not a raise: this query backs the fail-safe, and the one
    boot it exists to survive is exactly the one where the playlist is
    unreadable (intake's pin set rides this too, and a missing playlist
    must not break an intake)."""
    files = None
    with pl_lock():
        try:
            files = load_playlist().get("fallback")
        except (OSError, ValueError):
            files = None
    files = files or FALLBACK_DEFAULT
    return [f for f in files if os.path.exists(os.path.join(MEDIA, f))]


def failover(renderer, state, decks, skip_idx, move_index=True):
    """PLAYOUT_C on air: the next deck didn't come up inside FEED_WAIT.

    Recovery reuses advance() itself — when PLAYOUT_C's file ends,
    on_ended calls advance() again, which either cuts a recovered deck
    (and clears fallback_air mid-success) or drops straight into this
    function again for the next fallback file. One loop, one code path."""
    files = fallback_files()
    # The deck that was on air keeps its feed publishing to MediaMTX after
    # a failover: nothing stops it until the next successful cut.
    try:
        stop_feed(state.get("deck") or "A")
    except Exception:
        pass
    start = int(state.get("fallback_idx") or 0)
    for fi in range(len(files)):
        name = files[(start + fi) % len(files)]
        renderer.set_media_source(PLAYOUT_C, os.path.join(MEDIA, name))
        for slot in ("A", "B"):
            renderer.set_source_visible(PROGRAM, decks[slot], False)
            renderer.set_source_visible(PROGRAM, STREAM_DECK[slot], False)
        renderer.set_source_visible(PROGRAM, PLAYOUT_C, True)
        # Activation opens the file; a broken one stays NONE forever.
        if not media_ready(renderer, PLAYOUT_C):
            continue
        renderer.set_transition(TRANSITION, 750)
        globals()["last_advance_src"] = PLAYOUT_C
        state.update({"index": (skip_idx + 1) if move_index
                      else int(state.get("index") or 0),
                      "deck": "C", "fallback_air": True,
                      "stream": None, "fallback_idx": start + fi + 1})
        merge_save_state(state)
        alert("Fail-safe on air: %s (deck stalled on load)." % name, "CRIT")
        return True
    renderer.set_scene(SCENE_TECHDIFF)
    alert("No fail-safe file plays either; holding TECHDIFF.", "CRIT")
    return False


def advance(renderer, state, data, deck_sources):
    """Play next item on the idle deck, cut under a transition.

    Loop, not recursion: a fully-missing playlist must end on TECHDIFF,
    not in RecursionError."""
    global last_advance
    last_advance = time.time()  # refractory anchor for the on_ended guard
    items = data.get("items", [])
    if not items:
        renderer.set_scene(SCENE_TECHDIFF)
        alert("Playlist empty; holding.", "WARN")
        return
    if globals().get("PLANE_DOWN"):
        # The renderer is not answering: HOLD. Advancing now would consume
        # the playlist item by item (each one "unplayable" because nothing
        # can play it) and the queue would be empty by morning.
        alert("Render plane is down: holding the queue, nothing advanced.",
              "WARN")
        return
    skipped = dormant = pending = 0
    try:
        # The DISK cursor as of entry: if it moves while we work, the
        # operator moved it and their value wins.
        sidx0 = load_state().get("index", 0)
    except Exception:
        sidx0 = state.get("index", 0)
    try:
        every = int(data.get("ad_every") or 0)
    except (TypeError, ValueError):
        every = 0
    if every > 0 and int(state.get("since_ad") or 0) >= every \
            and not state.get("in_ad_break"):
        # Ad slot due: cut away instead of advancing content. The index is
        # untouched, so the return path resumes exactly where it left off.
        # A declined break (no file) falls through to content normally.
        if play_ad(renderer, data, deck_sources):
            return
    while skipped + dormant + pending < len(items):
        sidx = state.get("index", 0)
        idx = (sidx if isinstance(sidx, int) else 0) % len(items)
        item = items[idx]
        if item.get("status") == "dormant":
            dormant += 1  # operator intent, not a fault: silent, no alert
            state["index"] = idx + 1
            continue
        url = item.get("youtube")
        if url:
            # Link item. A complete spool outranks the pipe: play the
            # whole local copy instead (falls through to the file lane
            # below); otherwise resolve and stream raw as before.
            _sp = spool.ready(url)
            if _sp and item.get("spool") is not False:
                path = _sp["path"]
                url = None
                break
            # Link item: needs no disk (link outranks a stale file copy).
            # Resolve is cached by prefetch; a miss resolves inline here,
            # costing a few seconds on this transition only.
            # Cover FIRST: the resolve can take 45s on a slow YouTube, and
            # if the deck is idle the audience would stare at black for
            # all of it. The fail-safe's holding card takes the air.
            cover_idle_deck(renderer, state, deck_sources)
            meta = cached_resolve(url)
            if meta:
                break
            # A resolve that failed for a TRANSIENT reason (a timeout, a
            # bot check, a network hiccup) must NOT consume the item: on a
            # slow YouTube (30-60s per metadata call from a datacentre IP)
            # the old behaviour made the station eat its own playlist, one
            # item every few seconds. HOLD instead: the current item keeps
            # playing and the prefetch warms this one.
            if not ytstream.resolve_failure_is_permanent():
                alert("Link not resolving yet (%s): holding the queue."
                      % (item.get("title") or url), "WARN")
                HOLDING["since"] = time.time()
                HOLDING["why"] = str(item.get("title") or url)
                cover_idle_deck(renderer, state, deck_sources)
                return
            # Permanent: the video is gone. Skip it -- but not more than
            # a few per pass, so a run of dead videos cannot chew through
            # the whole playlist in one go.
            if skipped >= 3:
                alert("Several dead links in a row: holding the queue.", "WARN")
                return
            alert("Unplayable link: %s. Skipping." % (item.get("title") or url), "WARN")
            state["index"] = idx + 1
            skipped += 1
            continue
        if not item.get("file"):
            if item.get("source"):
                pending += 1  # link registered, file not here yet: silent
                state["index"] = idx + 1
                continue
            skipped += 1  # entry names nothing at all: fault, loud below
            alert("Playlist entry names no file: %s. Skipping." % item.get("title", "?"), "WARN")
            state["index"] = idx + 1
            continue
        path = os.path.join(MEDIA, item["file"])
        if os.path.exists(path):
            break
        hold_alert("miss:" + item["file"],
                   "Cache miss: %s. Skipping to next." % item["file"], "WARN")
        state["index"] = idx + 1
        skipped += 1
    else:
        renderer.set_scene(SCENE_TECHDIFF)
        if pending and not skipped and not dormant:
            hold_alert("hold:fetching",
                       "Every playlist item still fetching; holding.", "WARN")
        elif dormant and not skipped and not pending:
            hold_alert("hold:dormant",
                       "Every playlist item dormant; holding.", "CRIT")
        else:
            hold_alert("hold:missing",
                       "Every playlist item missing; holding.", "CRIT")
        return
    primed = _STREAM_STATE.pop("primed", None)
    deck = "B" if state.get("deck", "A") == "A" else "A"
    other = "B" if deck == "A" else "A"
    started = None
    if primed and (not url or primed["url"] != url):
        # Stale prime (playlist edited or a file item now): drop its feed.
        ytstream.stop(primed["feed"])
        primed = None
    if url and primed:
        slot = "slot-stream-%s" % primed["deck"].lower()
        for _ in range(6):  # ~18s grace for a knockout-ready prime
            if ytstream.path_ready(slot):
                started = (primed["feed"], primed["meta"])
                break
            time.sleep(3)
        if started:
            # Cut to the deck that was feeding while the previous item ran:
            # publishing already live at native rate.
            deck = primed["deck"]
            other = "B" if deck == "A" else "A"
        else:
            alert("Primed deck never published; spawning live.", "WARN")
            ytstream.stop(primed["feed"])
            primed = None
    if url:
        if not started:
            # No usable prime: spawn synchronously on the idle deck.
            started = start_stream_feed(url, deck, meta=meta)
        if not started:
            alert("Stream deck %s failed to publish %s. Skipping." % (deck, item.get("title") or url), "CRIT")
            state["index"] = idx + 1
            merge_save_state(state)   # persist the skip, or the same link
            return                    # blocks the queue for good
        feed, meta = started
        src = STREAM_DECK[deck]
        onair = {"start": time.time(),
                 "dur": item.get("duration") or meta.get("duration"),
                 "url": url, "respawns": 0, "slot": deck}
    else:
        src = deck_sources[deck]
        onair = None
        stop_feed(deck)
        renderer.set_media_source(src, path)
        # A paused input may exist from the transient pause experiment or a
        # stray operator pause: the next file cut RESTARTs it, which is why
        # the parked decks keep playing silently. This comment documents the
        # deal. Remove together with park_decks — an input left PAUSED at
        # boot would hand back "stalled at 0ms" to the watchdog.
        try:
            renderer.restart_media(src)
        except Exception as e:
            alert("restart after load failed (%s); hoping for implicit." % e, "WARN")
    # Every cut shows exactly one deck input. Hide BOTH other decks of BOTH
    # kinds — a stream can follow a file and vice versa in one transition.
    renderer.set_source_visible(PROGRAM, src, True)
    renderer.set_source_visible(PROGRAM, deck_sources[other], False)
    renderer.set_source_visible(PROGRAM, STREAM_DECK[other], False)
    # The fail-safe deck is the topmost scene item: if a failover left it
    # visible, it covers everything that plays after it.
    renderer.set_source_visible(PROGRAM, PLAYOUT_C, False)
    # Reconcile — the trio above trusts OBS ordering; races (item edits
    # landing mid-advance, a stream source that never got hidden on its own
    # last cut) can put the wrong deck back. Re-read and force: the
    # operator saw program showing one item while another was still live.
    try:
        have = {i.get("sourceName"): i.get("sceneItemEnabled") for i in renderer._call(
            "GetSceneItemList", {"sceneName": PROGRAM}).get("sceneItems", [])}
        for s, want in ((deck_sources[other], False), (STREAM_DECK[other], False),
                        (STREAM_DECK[deck], False), (PLAYOUT_C, False),
                        (src, True)):
            if have.get(s) != want:
                renderer.set_source_visible(PROGRAM, s, want)
    except Exception as e:
        alert("visibility reconcile skipped: %s." % e, "WARN")
    park_decks(renderer, deck, src, deck_sources)
    _vdb = state.get("deck_volume_db")
    if _vdb is not None:
        try:
            renderer.set_volume(src, _vdb)  # operator mix rides every cut
        except Exception:
            pass
    if not onair:
        # Measured readiness, POST-activation: OBS media sources sit at
        # MEDIA_STATE_NONE until they become active (restart_on_activate),
        # so a pre-cut check could never pass — the fail-safe would fire on
        # a perfectly healthy lane (observed live after restart 2026-10-19).
        # ACTIVATION starts the decode; ~1s to OPEN/PLAYING for locals.
        # A second failure is usually the post-restart plugin soft-lock:
        # input sits at NONE forever no matter the file; one explicit
        # restart action unlocks it (proven live on PLAYOUT_A 2026-10-19).
        if not media_ready(renderer, src):
            try:
                renderer.restart_media(src)
            except Exception:
                pass
            if not media_ready(renderer, src, wait=2.0):
                failover(renderer, state, deck_sources, idx)
                return
    renderer.set_transition(TRANSITION, 750)
    # A fault cut us to TECHDIFF: come back to the program when the next
    # item starts, or the audience stares at the fault card.
    try:
        if renderer._call("GetCurrentProgramScene").get(
                "currentProgramSceneName") == SCENE_TECHDIFF:
            renderer.set_scene(SCENE_PROGRAM)
    except Exception:
        pass
    globals()["last_advance_src"] = src   # the flicker guard watches THIS input
    stop_feed(other)  # the just-cut deck's feed (if any) ends with its slot
    HOLDING["since"] = 0.0
    HOLDING["why"] = ""
    alert("Now playing: %s." % (item.get("title") or item.get("youtube", "?")), "INFO")
    state.update({"index": idx + 1, "deck": deck, "deck_paused": False,
                  "just_played": shuffler.item_key(item)})
    # Mark the item that just finished as PLAYED. The dock needs this for
    # the Spotify-style group shuffle: turning shuffle off must not
    # replay what was already sent past, and turning it on again must be
    # able to re-shuffle everything that has NOT played yet.
    try:
        with pl_lock():
            _pl = load_playlist()
            for _c in _pl.get("items") or []:
                if shuffler.item_key(_c) == shuffler.item_key(item):
                    _c["played"] = 1
                    break
            save_playlist(_pl)
    except Exception:
        pass
    if state.pop("fallback_air", None):
        alert("Fail-safe cleared: deck %s plays again." % deck, "INFO")
    state["stream"] = onair
    # Mid-roll schedule for this item, if the plan asks for one. Streams
    # know their duration here and plan now. File items must NOT seed
    # marks_for here: the poll's lazy-fill gate opens on
    # marks_for != this item's seed, and pre-seeding it with exactly that
    # seed closed the gate forever — file items never got their mid-rolls.
    # Instead, when the new item is not immediately plannable and its seed
    # differs from what is stored, clear the previous item's plan and leave
    # marks_for stale so the gate opens the first time the media clock
    # reports a length.
    if onair and onair.get("dur"):
        state["marks_for"] = roll_marks_onair(item, data)
        state["next_roll"] = 0
        marks = plan_rolls(onair["dur"], data, state["marks_for"])
        state["roll_marks"] = marks
        if marks:
            alert("Mid-rolls planned: %s" % ", ".join(
                "%02d:%02d" % (int(m / 60), int(m % 60)) for m in marks))
    elif state.get("marks_for") != roll_marks_onair(item, data):
        state["roll_marks"] = []
        state["next_roll"] = 0
    try:
        if int(data.get("ad_every") or 0) > 0:
            state["since_ad"] = int(state.get("since_ad") or 0) + 1
    except (TypeError, ValueError):
        pass
    if state["index"] >= len(items) and data.get("shuffle_on_complete"):
        # Shuffle the FRESH list under lock, not our possibly-stale copy:
        # a same-window /library edit rides along instead of being eaten.
        # Seam rule from VLC's randomizer (via media-playlist-source):
        # the first item of the new cycle must not repeat the last item
        # of the one that just ended.
        with pl_lock():
            try:
                fresh = load_playlist()
            except ValueError:
                fresh = data
            shuffler.reshuffle(fresh.get("items", []),
                               [state["just_played"]] if state.get("just_played") else [])
            save_playlist(fresh)
            globals()["_SELF_WROTE_PLAYLIST"] = True
            data["items"] = fresh["items"]
        state["index"] = 0
        alert("Playlist exhausted; reshuffled.", "INFO")
    # The operator may have re-pinned the cursor while we were busy: the
    # dock knows which item is on air, we only know what we saw at entry.
    try:
        with pl_lock():
            _disk = load_state()
            if _disk.get("index") != sidx0:
                state["index"] = _disk["index"]
    except Exception:
        pass
    merge_save_state(state)
    try:
        if spool.kick(data.get("items") or [], state["index"], alert=alert):
            alert("Spooling next in background.", "INFO")
    except Exception as e:
        alert("Spool error: %s" % e, "WARN")


STATE_KEYS = ("index", "deck", "stream", "roll_marks",
              "next_roll", "marks_for", "since_ad",
              "fallback_air", "fallback_idx", "just_played",
              "deck_volume_db", "deck_paused")


def merge_save_state(state):
    """Persist our touch keys over a FRESH disk read: advance can run for
    ~45s (stream spawn) while watchdog faults or a /library edit may
    rewrite state.json in that window — saving our stale copy would eat
    those writes. Populated keys overwrite, ABSENT keys delete: advance
    pop()s fallback_air to clear it, and a merge that only carried present
    keys would resurrect the on-disk flag every save (observed live
    2026-10-19: "Fail-safe cleared" on every rotation)."""
    with pl_lock():
        fresh = load_state()
        for k in STATE_KEYS:
            if k in state:
                fresh[k] = state[k]
            else:
                fresh.pop(k, None)
        save_state(fresh)


def ad_return(renderer, decks, mid=False):
    """Shared return from any ad (file or stream): unmute, clear flags,
    cut back to program, advance. Diverges only in that stream ads stop
    their own feed. Program-scene guard keeps an operator who moved away
    mid-break in charge.
    Mid-rolls (mid=True, or the ad_mid flag the poller set) resume the SAME
    item: advance only if that item finished playing under the break's
    cover — otherwise the schedule promise ("break here, then continue")
    would eat 80% of a 2-hour stream."""
    try:
        pgm = renderer._call("GetCurrentProgramScene")["currentProgramSceneName"]
    except Exception:
        pgm = AD_SCENE
    try:
        renderer.set_mute(decks["A"], False)
        renderer.set_mute(decks["B"], False)
    except Exception:
        pass
    mute_stream_decks(renderer, False)
    stop_feed("AD")  # no-op for file ads
    ended_this_item = False
    try:
        st = load_state()
    except (OSError, ValueError):
        st = {}
    mid = bool(mid) or bool(st.get("ad_mid"))
    if mid and pgm == AD_SCENE:
        # Did the current item end while the break covered it? Streams: wall
        # clock past duration (grace folded in) or a dead feed; files: the
        # media input reports ENDED (muted decks never pause their clocks).
        item = None
        try:
            items = load_playlist().get("items", [])
            i = st.get("index", 0)
            i = i if isinstance(i, int) else 0
            item = items[(i - 1) % len(items)] if items else None
        except (OSError, ValueError):
            item = None
        if item is not None and (item.get("youtube") or item.get("file")):
            if item.get("youtube"):
                dur = st.get("stream_pre", {}).get("dur")
                try:
                    elapsed = time.time() - st.get("stream_pre", {}).get(
                        "start", 0)
                except TypeError:
                    elapsed = 0
                ended_this_item = not ytstream.alive(
                    _STREAM_STATE["feeds"].get(st.get("deck", "A"))) or (
                    dur and elapsed >= float(dur) + STREAM_GRACE)
            else:
                src = decks.get(st.get("deck", "A"), decks["A"])
                try:
                    ms = renderer.get_media_status(src)
                    ended_this_item = \
                        ms.get("state") == "OBS_MEDIA_STATE_ENDED"
                except Exception:
                    ended_this_item = False
    with pl_lock():
        try:
            state = load_state()
        except (OSError, ValueError):
            state = {}
        state["in_ad_break"] = False
        state["ad_mid"] = False
        state["stream"] = state.get("stream_pre")  # content record restored
        state["stream_pre"] = None
        save_state(state)
    if pgm != AD_SCENE:
        alert("Ad ended but program is %s; leaving it." % pgm, "INFO")
        return
    renderer.set_scene(SCENE_PROGRAM)
    alert("Ad done; back to program%s." % (" to finish the item" if mid and not ended_this_item else "."), "INFO")
    if mid and not ended_this_item:
        return
    advance(renderer, load_state(), load_playlist(), decks)


def on_ended(renderer, decks, source, force=False):
    """Route a media-ended event by source name. Unknown sources are ignored."""
    # Post-cut refractory (~2 polls): a fresh RESTART/swap on the
    # just-loaded input can flicker OBS_MEDIA_STATE_ENDED for a moment,
    # and the poll detector (streak >= 1) reading that window enqueues a
    # bogus immediate re-advance — the 3s cut cascade. A skip that must
    # beat the window calls with force=True.
    if not force and source == last_advance_src \
            and time.time() - last_advance < 6.0:
        return
    # Routed triggers name themselves: when cuts cascade the operator (and
    # we) must see WHICH source drove it, not just playlist churn. Slot
    # Cam/Screen/Audio and idle AD end-event floods never route at all —
    # the OBS event bus spews ENDED for them at ~2/s, so they are dropped
    # here silently instead of burning a log line (and a route) each pass.
    if source not in (DECK_A, DECK_B, PLAYOUT_C, AD_INPUT, STREAM_EOF,
                      IDENT_SRC):
        return
    alert("advance trigger: %s." % source, "INFO")
    if source == STREAM_EOF:
        # Wall-clock end of a youtube item (or feed death after respawn
        # gave up): same routing semantics as a local deck ending. If the
        # stream that ended was the AD slot, it's the break ending:
        # route back to program exactly like a file ad ending.
        try:
            st = load_state()
        except (OSError, ValueError):
            st = {}
        if st.get("in_ad_break") and (st.get("stream") or {}).get("slot") == "AD":
            ad_return(renderer, decks)
            return
        if st.get("in_ad_break"):
            return  # content feed ended under cover of the break
        if not st.get("stream"):
            # Stale EOF: the stream item it was routed for is already gone
            # (an operator skip or an ad return landed between the append
            # and this drain). Advancing here would skip whatever the
            # operator is watching now.
            alert("stale stream EOF; no stream on air to end.", "INFO")
            return
        advance(renderer, st, load_playlist(), decks)
        return
    if source == AD_INPUT:
        ad_return(renderer, decks)
        return
    if source == PLAYOUT_C:
        # Fail-safe file ended: same drive loop, one hop up.
        try:
            st = load_state()
        except (OSError, ValueError):
            st = {}
        if st.get("fallback_air") and not st.get("in_ad_break"):
            advance(renderer, st, load_playlist(), decks)
        return  # stray end while off-air (boot cleanup) is not our business
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
        try:
            st = load_state()
        except (OSError, ValueError):
            st = {}
        if st.get("in_ad_break"):
            # Deck ended under cover of the ad break: ignore it. The
            # return path advances; reacting here would skip an item.
            return
        lane = "B" if source == DECK_B else "A"
        if (st.get("stream") or {}).get("slot"):
            # A stream item is on air: its deck files end harmlessly while
            # parked (the mute contract burns the copy); stream items
            # advance by wall clock (STREAM_EOF), never by deck events.
            alert("parked %s ended behind a stream; ignored." % source, "INFO")
            return
        if not force and st.get("deck", "A") != lane:
            alert("parked %s ended behind %s; ignored."
                  % (source, st.get("deck")), "INFO")
            return
        # Final gate: a real end HOLDS the input at OBS_MEDIA_STATE_ENDED,
        # while a straggler event for a file the deck already swapped lands
        # while the deck reports PLAYING/OPENING for the NEW media. The
        # observed cascade (cuts every ~3s, 2026-10-20) was exactly this:
        # each cut fired the OLD file's end up to ~10s late. Swallow those
        # — but NOT for force (operator skip: the live item is playing,
        # and that is precisely the point). A plane error here falls back
        # to trusting the event.
        try:
            _mst = renderer.get_media_status(source).get("state")
        except Exception:
            _mst = None
        if not force and _mst and _mst != "OBS_MEDIA_STATE_ENDED":
            alert("stale end event for %s (media swapped); ignored." % source, "INFO")
            return
        advance(renderer, st, load_playlist(), decks)
    # anything else (sting, bed loop, preview) is not the daemon's business


def wait_ready(renderer, tries=None, pause=15):
    """Block until the render plane answers. A fresh boot under CEF load can
    take minutes before the first Hello; crashing on it would make every
    autostart a coin flip (systemd would restart-loop us)."""
    import time as _t
    if tries is None:
        tries = int(os.environ.get("OBS_READY_TRIES", "12"))
    long_to = int(os.environ.get("OBS_TIMEOUT", "60"))
    stuck = 0
    for n in range(1, tries + 1):
        try:
            with renderer._lock:
                if renderer._shared is None:
                    # 20s, not the 60s default: a hung TCP handshake must
                    # not burn a minute per try. 20s (not 8s) because a
                    # SOFTWARE-GL plane can be slow to answer -- and the
                    # difference matters: a too-short timeout turns a slow
                    # plane into a crash loop.
                    ws = renderer._connect(timeout=20)
                    try:
                        ws.s.settimeout(long_to)
                    except OSError:
                        pass
                    renderer._shared = ws
            renderer._call("GetVersion")
            return True
        except Exception as e:
            print("render plane not ready (%d/%d): %s" % (n, tries, e), flush=True)
            with renderer._lock:
                try:
                    if renderer._shared is not None:
                        renderer._shared.close()
                except Exception:
                    pass
                renderer._shared = None
            # Three greetings in a row that never came: the plane's
            # control plane is WEDGED (a client that upgraded and never
            # read its greeting blocks every later handshake -- proved
            # live). Waiting 15 minutes for it to un-wedge is not
            # booting, it is dying slowly: restart the plane instead.
            stuck += 1
            if stuck >= 3:
                stuck = 0
                try:
                    restart_plane()
                    print("render plane restarted (greeting wedged)", flush=True)
                except Exception as re:
                    print("plane restart failed: %s" % re, flush=True)
                _t.sleep(pause)
                continue
            _t.sleep(pause)
    return False


def prefetch_name(item):
    base = (item.get("title") or "item")[:40]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base).strip("_") or "item"
    digest = hashlib.sha1(item["source"].encode()).hexdigest()[:8]
    return "%s_%s.mp4" % (safe, digest)


def prefetch_order(data, index):
    """Candidate order, pure so the edge tests can pin it: the next two
    items first (just-in-time), then every other item in rotation order.
    A parked-then-returned link must already be warm when it rejoins, so
    the scan is not limited to the head — the spawn caps (max 2 in flight,
    one new per pass) are what protect weak boxes, not a short scan."""
    items = data.get("items", [])
    n = len(items)
    if not n:
        return []
    idx = index if isinstance(index, int) else 0
    return [(idx + off) % n for off in range(n)]


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
        started = getattr(proc, "started_at", 0)
        if started and now - started > 2700:
            # Backstop: a hung yt-dlp would otherwise live forever (the
            # in-flight slot pin, never reaped, starves every later fetch).
            proc.kill()
            try:
                proc.wait(10)
            except Exception:
                pass
        if proc.poll() is None:
            continue
        del in_flight[source]
        if proc.returncode == 0:
            failed.pop(source, None)
            renames = {}
            for item in data.get("items", []):
                if item.get("source") == source:
                    name = prefetch_name(item)
                    if os.path.exists(os.path.join(MEDIA, name)):
                        item["file"] = name
                        renames[source] = name
            # Apply to the FRESH list under lock (a same-window /library
            # edit survives), then mirror into our in-memory copy.
            with pl_lock():
                try:
                    fresh = load_playlist()
                except ValueError:
                    fresh = data
                for item in fresh.get("items", []):
                    if item.get("source") in renames:
                        item["file"] = renames[item["source"]]
                save_playlist(fresh)
            alert("Prefetched %s." % source[-60:], "INFO")
        else:
            failed[source] = now
            alert("Prefetch failed for %s; retrying in 15 min." % source[-60:], "WARN")
    items = data.get("items", [])
    if not items or len(in_flight) >= 2:
        return
    for i in prefetch_order(data, state.get("index", 0)):
        item = items[i]
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
            with pl_lock():
                try:
                    fresh = load_playlist()
                except ValueError:
                    fresh = None
                if fresh is not None:
                    for it in fresh.get("items", []):
                        if it.get("source") == source:
                            it["file"] = name
                    save_playlist(fresh)
            continue
        try:
            env = dict(os.environ, BROADCAST_ROOT=os.path.dirname(MEDIA))
            in_flight[source] = subprocess.Popen(
                [sys.executable, os.path.join(HERE, "intake.py"),
                 source, "--as", name, "--title", item.get("title", "")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            in_flight[source].started_at = time.time()
            alert("Prefetching %s ..." % source[-60:], "INFO")
        except OSError as e:
            alert("Prefetch spawn failed: %s." % e, "WARN")
        return  # one new fetch per pass; the next pass takes the next item


def restart_plane():
    """Restart the render plane when the reachability gate declares it dead.

    systemctl stop does not reliably reap the flatpak/bwrap tree (seen
    live: unit inactive, obs still holding :4455), so belt and suspenders:
    stop, kill exact-name leftovers, start. Exact comm names only — never
    pattern-match, or the killer eats its own launcher.
    """
    def run(*args):
        try:
            subprocess.run(list(args), timeout=100,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            alert("Plane restart step %s failed: %s." % (args[-1], e), "WARN")
            return False
    run("systemctl", "--user", "stop", "station-obs")
    time.sleep(3)
    for comm in ("obs", "bwrap"):
        try:
            subprocess.run(["pkill", "-x", comm], timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    # Wait for the port to actually free: starting OBS while the old tree
    # still holds :4455 fails the bind and burns the restart on nothing.
    # (Single-purpose box: exact comm names only, never patterns.)
    import socket as _s
    for _ in range(15):
        try:
            probe = _s.create_connection(("127.0.0.1", 4455), timeout=1)
            probe.close()
        except OSError:
            break
        time.sleep(1)
    time.sleep(2)
    if run("systemctl", "--user", "start", "station-obs"):
        alert("Render plane restart issued; waiting for first Hello.", "INFO")


_CONTROL_KEYS = ("skip", "media", "normalize", "refresh", "probe")
# Guards the ended-events queue shared by the media watch and the poll
# loop; the dock's skip path (consume_control) reads state under it too.
END_LOCK = threading.Lock()


def consume_control(renderer, decks, data):
    """Operator commands from the dock/panel: broadcast/control.json.

    {"skip": true} ends the current item exactly like a natural media end;
    {"media": {...}} carries transport/mixer verbs; {"normalize": ...} the
    loudness switch; {"refresh": {"url": ...}} one row's metadata;
    {"probe": true} plane introspection. The file is rewritten without the
    consumed keys so one POST fires exactly once.

    The panel's api_control holds pl_lock across its whole read-modify-
    write. This side reads under the lock, runs the (slow) consume
    unlocked, then takes the lock again to RE-READ the file fresh and pop
    only what is still exactly the verb this pass consumed. A verb whose
    key this pass never saw survives verbatim; a DIFFERENT verb of a seen
    kind (a new mix value, a fresh skip after a false) is a new instance
    and survives to the next pass; an identical repeat of a verb already
    acted on is indistinguishable from it and is consumed (bare booleans
    carry no instance identity -- the 6s post-cut refractory exists to
    absorb slam-skips). A stale panel write cannot resurrect a verb this
    pass already acted on, because the panel writes under the same lock.
    The old form -- read unlocked, act, rewrite the stale copy -- ate
    verbs posted mid-consume (a skip posted during a long transition
    vanished) and could resurrect a consumed one (double-advance).
    """
    if not os.path.isfile(CONTROL):
        return
    try:
        with pl_lock():
            with open(CONTROL) as _f:
                _ctl = json.load(_f)
    except Exception:
        return
    if not isinstance(_ctl, dict):
        return
    _ctl = dict(_ctl)
    # What this pass actually SAW, with the values seen: at write-back a
    # key is popped only when the file still holds exactly the verb this
    # pass consumed. A same-kind verb with a DIFFERENT value posted while
    # the consume was running is a new instance and survives to the next
    # pass, where it acts on whatever is on air then. A throwing consume
    # still pops what it saw (the identical verb is still in the file),
    # so a failing advance cannot leave {"skip": true} behind and loop
    # forever.
    _seen = {k: _ctl[k] for k in _CONTROL_KEYS if k in _ctl}
    if _ctl.pop("skip", False):
        with END_LOCK:
            _sk_st = load_state()
            if (_sk_st.get("stream") or {}).get("slot"):
                # Stream item on air: skipping ends the stream (wall
                # clock), the deck file is just parked underneath it.
                _src = STREAM_EOF
            else:
                _src = decks.get(_sk_st.get("deck", "A"), DECK_A)
        # Direct, not queued: an operator slam-skipping within the 6s
        # post-cut refractory must still beat it, which force=True on a
        # direct route does. Swallow-but-consume: the consumed keys are
        # popped at write-back regardless, so a throwing advance can't
        # leave {"skip": true} behind and loop forever.
        try:
            on_ended(renderer, decks, _src, force=True)
        except Exception as _se:
            alert("skip failed: %s." % _se, "WARN")
    # Dock transport/mixer: {"media": {"action": ...}}. pause/resume/
    # restart touch only FILE decks -- a live stream paused is just a
    # half-swallowed feed; mix sets input volume db (not system volume)
    # and persists so every future cut rides the same mix.
    _med = _ctl.pop("media", None)
    if isinstance(_med, dict):
        try:
            _mst = load_state()
            _mdeck = decks.get(_mst.get("deck", "A"), DECK_A)
            _live = stream_item_on_air(data.get("items", []), _mst)
            _mact = _med.get("action")
            _mdb = _med.get("db")
            if _mact == "mix" and isinstance(_mdb, (int, float)):
                _msrc = STREAM_DECK.get(_mst.get("deck", "A"),
                                        STREAM_DECK["A"]) if _live else _mdeck
                renderer.set_volume(_msrc, max(-70.0, min(0.0, _mdb)))
                # The state snapshot rides AFTER the plane call:
                # set_volume can block for seconds on a slow plane, and
                # merge_save_state overwrites every STATE_KEY it is
                # handed -- carrying the pre-call snapshot back would
                # silently revert anything written meanwhile (the
                # panel's /api/state, the overlay's /state). Only the
                # mix keys ride forward on a fresh read.
                _mst2 = load_state()
                merge_save_state(dict(
                    _mst2, deck_volume_db=_mdb,
                    deck_paused=_mst2.get("deck_paused")))
            elif _mact in ("pause", "resume", "restart"):
                if _live:
                    alert("Transport ignored: a live stream "
                          "is on air, not a file deck.", "WARN")
                else:
                    renderer.media_action(_mdeck, _mact)
                    # Same shape as mix: pause/resume carries no db, and
                    # the saved mix must come from the state AS IT IS
                    # when the plane call returns, not as it was before
                    # the call could block (one pause used to wipe it;
                    # every later cut went out raw).
                    _mst2 = load_state()
                    merge_save_state(dict(
                        _mst2, deck_paused=(_mact == "pause"),
                        deck_volume_db=(_mdb if _mdb is not None
                                        else _mst2.get("deck_volume_db"))))
        except Exception as _me:
            alert("transport failed: %s." % _me, "WARN")
    # Dock loudness verb: {"normalize": {"file": name}} or
    # {"normalize": {"url": link}} (forced re-spool through the loudnorm'd
    # faststart), or the station-wide switch {"global": true}.
    _norm = _ctl.pop("normalize", None)
    if isinstance(_norm, dict) and _norm.get("file"):
        _normalize_media(str(_norm["file"]))
    elif isinstance(_norm, dict) and _norm.get("url"):
        _normalize_media(str(_norm["url"]))
    elif isinstance(_norm, dict) and "global" in _norm:
        set_deck_normalizer(renderer, bool(_norm["global"]))
    # Dock: "Refresh metadata" on one row.
    _ref = _ctl.pop("refresh", None)
    if isinstance(_ref, dict) and _ref.get("url"):
        threading.Thread(
            target=refresh_item_metadata,
            args=(str(_ref["url"]), alert),
            daemon=True).start()
    # Read-only plane introspection: {"probe": true} refreshes
    # broadcast/obs_probe.json (inputs, filters, available filter kinds).
    if _ctl.pop("probe", False):
        try:
            probe_plane(renderer)
        except Exception as _pe:
            alert("probe failed: %s." % _pe, "WARN")
    # Write-back under the lock, from a FRESH read: pop only what is
    # still exactly the verb this pass consumed. Anything else the dock
    # posted while we were consuming survives for the next pass.
    try:
        with pl_lock():
            try:
                with open(CONTROL) as _f2:
                    _fresh = json.load(_f2)
            except Exception:
                _fresh = {}
            if not isinstance(_fresh, dict):
                _fresh = {}
            for _k, _consumed in _seen.items():
                if _k not in _fresh or _fresh[_k] == _consumed:
                    _fresh.pop(_k, None)
            with open(CONTROL + ".tmp", "w") as _f:
                json.dump(_fresh, _f)
            os.replace(CONTROL + ".tmp", CONTROL)
    except Exception:
        pass


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
    ended = _ENDED  # media-ended events queue; the poll loop drains it.
    # Module-level object (see _ENDED above): the background respawn thread
    # routes its give-up EOF from outside main(), which a main-local list
    # made impossible.
    # end_lock is module-level now: consume_control (the dock's skip path)
    # takes it too, and it used to live only here.
    end_lock = END_LOCK

    def note_ended(source):
        # Stream decks report MediaInputPlaybackEnded on every RTMP reader
        # hiccup (not just real live-signals); they advance by wall clock
        # and feed health instead (loop line ~1760). Observed live 2026-10-19:
        # the event killed a healthy -re feed at 4:55 of a 10:34 VOD.
        if source in (STREAM_DECK.get("A"), STREAM_DECK.get("B")):
            return
        with end_lock:
            ended.append(source)

    renderer.on_media_ended(note_ended)
    if not PLANE_AUTORESTART:
        # The plane is switched off ON PURPOSE (the operator does not want
        # the OBS window). Do not sit in wait_ready for 15 minutes: start
        # the loop, which HOLDS the queue until the plane comes back.
        # The hold flag must be set HERE, before the opening advance():
        # the poll loop's gate has not run yet, and without it the boot
        # cut would consume the queue one unplayable link at a time.
        globals()["PLANE_DOWN"] = time.time()
        clear_fault_history("the plane was switched off on purpose")
        alert("Render plane is switched off on purpose: starting without "
              "it. The queue holds until it returns.", "INFO")
    elif not wait_ready(renderer):
        print("render plane never answered; refusing to start blind.")
        return 2
    # The preflight needs the plane, so it runs AFTER wait_ready: before
    # that it could only ever see "renderer down" and cried CRIT on every
    # cold boot.
    try:
        import preflight
        if preflight.run(renderer):
            alert("Preflight FAILURES at boot (see daemon journal for list).",
                  "CRIT")
    except Exception as e:
        alert("preflight could not run (%s)." % e, "WARN")
    try:
        # Code/collection version skew breaks advance() with cryptic
        # GetSceneItemList errors and crash-loops the daemon (seen live:
        # new-code daemon vs old-name collection). Fail fast naming names.
        have_scenes = {s["sceneName"] for s in
                       renderer._call("GetSceneList").get("scenes", [])}
        want_scenes = {SCENE_STARTING, SCENE_PROGRAM, SCENE_LIVE,
                       SCENE_TECHDIFF, SCENE_OFFAIR, SCENE_END}
        missing = want_scenes - have_scenes
        assert not missing, "scenes missing in OBS: %s (collection skew?)" % sorted(missing)
        ensure_ad_plane(renderer)
        ensure_fallback_plane(renderer)
        have_items = {i.get("sourceName") for i in
                      renderer._call("GetSceneItemList",
                                     {"sceneName": SCENE_PROGRAM}).get("sceneItems", [])}
        for src in (DECK_A, DECK_B, STREAM_DECK["A"], STREAM_DECK["B"], PLAYOUT_C):
            assert src in have_items, "%s not in %s (collection skew?)" % (src, SCENE_PROGRAM)
    except AssertionError as e:
        print("cannot start loop: %s." % e)
        return 2
    except RuntimeError as e:
        print("cannot verify scenes (%s); starting anyway." % e)
    try:
        names = [t["transitionName"] for t in
                 renderer._call("GetSceneTransitionList").get("transitions", [])]
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
        # A reboot mid-ad-break leaves a stale in_ad_break flag pointing at
        # a dead ad input: clear it, unmute the decks, start clean. Loses at
        # most one ad slot; a stuck flag suppressing advances would be worse.
        with pl_lock():
            _boot_state = load_state()
            _broke_ad = bool(_boot_state.get("in_ad_break"))
            if _broke_ad:
                _boot_state["in_ad_break"] = False
                _boot_state["ad_mid"] = False
                _boot_state["stream"] = _boot_state.get("stream_pre")
                _boot_state["stream_pre"] = None
                _boot_state["roll_marks"] = None
                _boot_state["marks_for"] = None
                _boot_state["next_roll"] = 0
                save_state(_boot_state)
    except (OSError, ValueError):
        _broke_ad = False
    if _broke_ad:
        try:
            renderer.set_mute(decks["A"], False)
            renderer.set_mute(decks["B"], False)
        except Exception:
            pass
        mute_stream_decks(renderer, False)
        stop_feed("AD")  # a stream ad may have been mid-publish
        alert("Reboot interrupted an ad break; decks unmuted, starting clean.", "WARN")
    try:
        # The deck plays wherever the files point, but nobody SEES it until
        # program is the Meet scene. Caught live: a full advance cycle ran
        # into the Off Air harbour because nothing cut program.
        renderer.set_scene(SCENE_PROGRAM)
    except RuntimeError as e:
        alert("Program is not on Meet (%s); cut manually." % e, "WARN")
    alert("Loop running: %d items." % len(data.get("items", [])), "INFO")
    # Post-restart plugin soft-lock: any file input that survived an OBS
    # restart can sit at MEDIA_STATE_NONE forever, refusing to decode no
    # matter the file or scene activation (observed live on PLAYOUT_A
    # 2026-10-19, while boot-created PLAYOUT_C opened instantly). One
    # restart action per input per boot; harmless on healthy inputs.
    for src in [PLAYOUT_C, DECK_A, DECK_B]:
        try:
            renderer.restart_media(src)
        except Exception as e:
            alert("unlock %s failed: %s." % (src, e), "WARN")
    # Ticker + watermark on air. The exeldro downstream-keyer vendor channel
    # accepts dsk_select_scene but never persists it (silent no-op, seen
    # live 2026-10-19), so the overlays are composited as nested scene items
    # instead — same look, every scene regardless of keyer state. Idempotent.
    try:
        ensure_overlays(renderer)
    except Exception as e:
        alert("overlays failed: %s." % e, "WARN")
    try:
        studio_mode_off(renderer)
    except Exception:
        pass
    try:
        apply_mic_normalizer(renderer)
    except Exception:
        pass
    try:
        # The loudness switch is remembered: only a station that was
        # explicitly switched OFF boots without the chain.
        if normalize_on(True):
            apply_deck_normalizer(renderer)
    except Exception:
        pass
    try:
        ensure_bed_isolation(renderer)
    except Exception:
        pass
    try:
        ensure_stream_output(renderer)
    except Exception:
        pass
    try:
        probe_plane(renderer)
    except Exception:
        pass
    # Park whatever is NOT on air, mirroring the last cut: a daemon restart
    # mid-item left a hidden file deck playing silently on request otherwise.
    try:
        _boot_st = load_state()
        _boot_idx = int(_boot_st.get("index") or 0)
        _boot_deck = _boot_st.get("deck", "A")
        _boot_item = None
        if 1 <= _boot_idx <= len(data.get("items", [])):
            _boot_item = data["items"][_boot_idx - 1]
        if _boot_deck in ("A", "B") and _boot_item and not _boot_st.get("fallback_air"):
            # Classify with the same helper the transport uses: a link with
            # a complete spool plays as a FILE on the playout deck. The
            # bare youtube-key check used here before parked (muted) the
            # very deck that was on air, and a restarted item aired silent
            # until the next cut.
            _bsrc = (STREAM_DECK[_boot_deck]
                     if stream_item_on_air(data.get("items", []), _boot_st)
                     else decks[_boot_deck])
            park_decks(renderer, _boot_deck, _bsrc, decks)
            alert("boot parked idle decks (%s on air)." % _bsrc, "INFO")
    except Exception as e:
        alert("boot park skipped: %s." % e, "WARN")
    # In-flight fetches live across polls: a fresh dict per pass would make
    # the spawn guard blind and duplicate every fetch.
    in_flight, failed = {}, {}
    idle_streak = 0  # polls in a row the on-air deck reported idle (see below)
    ended_streaks = {}  # input -> consecutive ENDED polls (poll-driven advance)
    plane_down_since = None  # first poll the render plane failed to answer
    plane_restarted_at = 0.0  # last self-healing restart, epoch
    gate_pass = 0  # liveness-gate cadence: full probe every ~30 passes
    threading.Thread(target=_title_watch, daemon=True).start()
    while True:
        pass_started = time.time()
        PASS_STATE["since"] = pass_started
        PASS_STATE["what"] = "starting"
        try:
            apply_knobs()
            # Reachability gate: a dead plane must not spin the loop, and a
            # plane that stays dead gets restarted (cooldown-capped).
            # Full Hello handshake, not just TCP: a wedged plane can hold
            # the listener open while answering nothing (seen live).
            # 8s bounded, never stalls the poll.
            # Thresholds are env-overridable so the self-healing path stays
            # testable without waiting out production values.
            DOWN_SECS = globals().get("PLANE_DOWN_SECS", 600.0)
            COOLDOWN_SECS = globals().get("PLANE_RESTART_COOLDOWN", 1800.0)
            # Liveness check, two speeds. Between checks a masked ping on
            # the standing connection is the canary (cheap, no handshake);
            # every GATE_EVERY passes — and whenever the standing one is
            # gone — the full Hello probe runs. The old all-passes probe
            # opened ~30 fresh handshakes a minute, and with the plane busy
            # those connects stretched into the very seconds the poll was
            # supposed to save, dragging every skip ~8s late.
            gate_pass = (gate_pass + 1) % 30
            PASS_STATE["what"] = "plane check"
            # Operator commands FIRST: a skip must not wait behind a
            # 45s metadata resolve or a slow OBS call. The verbs are
            # cheap; the playout work is not.
            consume_control(renderer, decks, data)
            try:
                if renderer._shared is not None and gate_pass != 1:
                    with renderer._lock:
                        ws = renderer._shared
                        # Bound the send: a half-dead socket inherits the
                        # call timeout; the ping must not stall the poll.
                        old_to = ws.s.gettimeout()
                        try:
                            ws.s.settimeout(3.0)
                            ws._frame(0x9)  # ping -> pong (skipped by recv)
                        finally:
                            try:
                                ws.s.settimeout(old_to)
                            except OSError:
                                pass
                else:
                    probe = _WS(os.environ.get("OBS_HOST", "127.0.0.1"),
                                int(os.environ.get("OBS_PORT", "4455")), timeout=8)
                    hello = probe.recv()
                    probe.close()
                    if hello.get("op") != 0:
                        raise RuntimeError("not v5")
                if globals().get("PLANE_DOWN"):
                    # The plane is back. Whatever it recorded while it was
                    # away was its absence, not a station fault.
                    clear_fault_history("the render plane was away")
                plane_down_since = None
                globals()["PLANE_DOWN"] = 0
            except Exception:
                now = time.time()
                globals()["PLANE_DOWN"] = now
                if plane_down_since is None:
                    plane_down_since = now
                elif (PLANE_AUTORESTART and
                      now - plane_down_since > DOWN_SECS and
                      now - plane_restarted_at > COOLDOWN_SECS):
                    plane_restarted_at = now
                    alert("Render plane unreachable; restarting it.", "CRIT")
                    restart_plane()
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
                    # The failed advance must not hold the refractory: the
                    # retry would be swallowed and the deck stay half-cut.
                    globals()["last_advance"] = 0.0
                    globals()["last_advance_src"] = None
                    with end_lock:
                        ended.append(source)
            # Poll-driven end detection backs up media-ended events, which
            # do not reliably arrive. Two straight ENDED polls enqueue the
            # source exactly like an event would.
            try:
                _est = load_state()
                _watch = []
                if _est.get("in_ad_break"):
                    _watch.append(AD_INPUT)
                else:
                    _deck_now = decks.get(_est.get("deck", "A"), DECK_A)
                    if not stream_item_on_air(data.get("items", []), _est):
                        # Stream items advance by wall-clock, not media
                        # status: their PLAYOUT ledger input is idle/stale
                        # and would fire spurious advances.
                        _watch.append(_deck_now)
                PASS_STATE["what"] = "media status"
                for _src in _watch:
                    try:
                        _ms = renderer.get_media_status(_src)
                    except Exception:
                        continue
                    # Publish the on-air position so the dock can say how
                    # long is left, not only what is playing. It goes in
                    # the HEARTBEAT, not state.json: rewriting the state
                    # file every pass churned the disk and -- worse -- its
                    # mtime changed every 2s, which defeated the dock's
                    # version check and made it re-fetch 58KB every poll.
                    ON_AIR.update({
                        "src": _src,
                        "pos_ms": int(_ms.get("time_ms") or 0),
                        "dur_ms": int(_ms.get("duration_ms") or 0),
                        "state": _ms.get("state") or ""})
                    if _ms.get("state") == "OBS_MEDIA_STATE_ENDED":
                        ended_streaks[_src] = ended_streaks.get(_src, 0) + 1
                    else:
                        ended_streaks[_src] = 0
                    # One ENDED read is enough: advance only picks the deck
                    # after media_ready() saw it PLAYING, so anything the
                    # watch reads as ENDED already survived the cut gate.
                    # The old 2-streak rule held a finished item on air up
                    # to two extra watchdog cycles of trailing black.
                    if ended_streaks.get(_src, 0) >= 1:
                        ended_streaks[_src] = 0
                        with end_lock:
                            if _src not in ended:
                                ended.append(_src)
            except Exception:
                pass
            # Stream-item lifecycle: wall-clock duration + feed health. The
            # feed lives in this process, so its death is observable locally
            # after all: two respawns then route to the next item. Runs for
            # ad-break streams too (state.stream.slot == "AD"); their EOF
            # routes back to program instead of advancing content.
            try:
                _sst = load_state()
                _sm = _sst.get("stream")
                if _sm:
                    _deck = _sm.get("slot") or _sst.get("deck", "A")
                    _feed = _STREAM_STATE["feeds"].get(_deck)
                    if not ytstream.alive(_feed):
                        # Feed health moved OFF the playout pass
                        # (2026-10-21): the pass only detects, counts and
                        # kicks; the resolve+spawn+ready-wait runs on the
                        # respawn thread, so a dead network can no longer
                        # freeze the deck for minutes. stream_respawn_pass.
                        stream_respawn_pass(_sm, _deck)
                    _dur = _sm.get("dur")
                    if _dur:
                        _elapsed = time.time() - _sm.get("start", 0)
                        if _elapsed >= _dur + STREAM_GRACE:
                            with end_lock:
                                if STREAM_EOF not in ended:
                                    ended.append(STREAM_EOF)
                        elif (_STREAM_STATE["primed"] is None
                              and _elapsed >= _dur - STREAM_PRIME_LEAD
                              and not load_state().get("in_ad_break")):
                            # Prime the idle deck while the stream plays:
                            # the viewer fades to a feed that is ALREADY
                            # publishing, not to a resolve+spawn gap.
                            # Skipped when the next item's spool is at
                            # work or done: a local copy outranks a live
                            # deck and the prime would be thrown away.
                            _pidx = int((load_state().get("index") or 1)) - 1
                            nxt = spool._urls_ahead(data.get("items") or [],
                                                    _pidx)
                            if not (nxt and (spool.ready(nxt[0][0])
                                             or spool.state(nxt[0][0]) == "fetching")):
                                prime_next_stream(data, _sm,
                                                  deck=_sm.get("slot") or "A")
            except Exception:
                pass
            # Mid-roll scheduler (ad_plan): on this same cadence, fire a
            # scheduled break once the playing item reaches its mark —
            # streams by wall clock, files by their media clock (which
            # never paused: muted, not paused). ±10s on the hit is fine;
            # the promise the plan makes is "around here", not at the
            # second. Skips any scene the operator drifted to: a mid-cut
            # into their manual frame is theft, not automation.
            try:
                # Mid-roll scheduler: SIX layers of "no theft" — program
                # scene check, break flag, then the plan itself. Unified:
                # both stream and file items go through the same gate.
                _mst = load_state()
                _items = data.get("items", [])
                _i = _mst.get("index", 0)
                _cur = _items[(int(_i) - 1) % len(_items)] if _items and isinstance(_i, int) and _i > 0 else None
                if _cur and not _mst.get("in_ad_break"):
                    _pgm = renderer._call("GetCurrentProgramScene") \
                        .get("currentProgramSceneName", SCENE_PROGRAM)
                    if _pgm == SCENE_PROGRAM:
                        # File items learn their clock lazily (media clock);
                        # streams already planned at advance(). Recompute once
                        # per item (marks_for = the planner seed).
                        _seed = roll_marks_onair(_cur, data)
                        if _mst.get("marks_for") != _seed:
                            _dur_s = 0.0
                            if _cur.get("youtube"):
                                _sm2 = _mst.get("stream") or {}
                                if _sm2.get("slot") in ("A", "B"):
                                    _dur_s = _sm2.get("dur") or 0
                            else:
                                try:
                                    _dur_s = (renderer.get_media_status(
                                        decks[_mst.get("deck", "A")]
                                    ).get("duration_ms") or 0) / 1000.0
                                except Exception:
                                    _dur_s = 0.0
                            if _dur_s > 0:
                                _pm = plan_rolls(_dur_s, data, _seed)
                                with pl_lock():
                                    _sv = load_state()
                                    _sv["roll_marks"] = _pm
                                    _sv["marks_for"] = _seed
                                    _sv["next_roll"] = 0
                                    save_state(_sv)
                                if _pm:
                                    alert("Mid-rolls planned: %s" % ", ".join(
                                        "%02d:%02d" % (int(m / 60), int(m % 60))
                                        for m in _pm))
                                _mst = load_state()
                        _marks = _mst.get("roll_marks") or []
                        _next = int(_mst.get("next_roll") or 0)
                        if _marks and _next < len(_marks):
                            _elapsed = 0.0
                            if _cur.get("youtube"):
                                _sm2 = _mst.get("stream") or {}
                                if _sm2.get("slot") in ("A", "B"):
                                    _elapsed = time.time() - _sm2.get("start", 0)
                            else:
                                try:
                                    _msm = renderer.get_media_status(
                                        decks[_mst.get("deck", "A")])
                                    _elapsed = (_msm.get("time_ms") or 0) / 1000.0
                                except Exception:
                                    _elapsed = 0.0
                            if _elapsed >= _marks[_next]:
                                if play_ad(renderer, data, decks, mid=True):
                                    with pl_lock():
                                        _sv = load_state()
                                        _sv["next_roll"] = _next + 1
                                        save_state(_sv)
            except Exception:
                pass
            # Natural advances (shuffle especially) rewrite the file behind
            # our back; re-baseline the hash so the next poll doesn't announce
            # our own shuffle as a human edit. A same-window human edit rides
            # along silently — rare, harmless, content still loads.
            # Re-baseline ONLY for our own shuffle write: re-baselining
            # every pass folded a human edit into the hash, and the next
            # pass then saw "no change" and kept the stale order.
            if globals().get("_SELF_WROTE_PLAYLIST"):
                globals()["_SELF_WROTE_PLAYLIST"] = False
                try:
                    last_hash = json.dumps(load_playlist(), sort_keys=True)
                except ValueError:
                    pass
            try:
                items = data.get("items", [])
                st8 = load_state()
                pinned, n = set(), len(items)
                if n:
                    # Playing, previous and next stay resident; operator-pinned
                    # items are never eviction candidates, whatever their age.
                    for o in (-1, 0, 1):
                        f = items[(st8.get("index", 0) + o) % n].get("file")
                        if f:
                            pinned.add(f)
                    pinned |= {i.get("file") for i in items
                               if i.get("pinned") and i.get("file")}
                # The safety assets live in MEDIA too: near the cap,
                # eviction used to eat the fail-safe loops and the ad
                # pool - the exact files the station leans on when a deck
                # stalls (failover() finds an empty pool and holds
                # Tech Diffs immediately) or a break fires.
                pinned |= set(fallback_files())
                pinned |= {f for f in (data.get("ad_files") or [])
                           if isinstance(f, str) and f}
                evict_cache(pinned=pinned)
            except Exception as e:
                alert("evict failed: %s." % e, "WARN")
            prefetch_pass(data, load_state(), in_flight, failed)
            prefetch_stream_pass(data, load_state())
            try:
                # Re-kick: after an OBS restart nothing is playing, so no
                # ENDED event will ever arrive to advance us. Six idle polls
                # (≈3 min) means stuck, not loading — replay current item.
                # "missing" is excluded: that's fault()'s job (plane down).
                # Stream items are exempt: media status lies for them (the
                # PLAYOUT ledger is idle), and feed health above answers.
                if HOLDING.get("since") and time.time() - HOLDING["since"] > 30:
                    # We are holding for a link: retry the advance so the
                    # station goes back to content as soon as the link
                    # resolves. Every ~30s, not every pass (a resolve can
                    # take 45s and YouTube rate-limits).
                    HOLDING["since"] = time.time()
                    try:
                        advance(renderer, load_state(), data, decks)
                    except Exception as e:
                        alert("hold retry failed (%s)." % e, "WARN")
                if not stream_item_on_air(data.get("items", []), load_state()):
                    # The fail-safe holds the air on deck "C", which is NOT
                    # in the deck map: looking it up by name raised
                    # KeyError('C') and the re-kick never ran.
                    _dk = load_state().get("deck", "A")
                    _src = PLAYOUT_C if _dk == "C" else decks.get(_dk, DECK_A)
                    mst = renderer.get_media_status(_src)
                    if mst.get("state") in ("OBS_MEDIA_STATE_NONE", "unknown", None):
                        idle_streak += 1
                    else:
                        idle_streak = 0
                    if idle_streak >= 6:
                        idle_streak = 0
                        alert("Deck idle with nothing advancing; re-kicking.", "WARN")
                        advance(renderer, load_state(), data, decks)
            except Exception as e:
                # The alert stays one line (the log is a trail, not a dump);
                # the trace goes to the journal, where it can be read.
                import traceback
                print("re-kick failed: %s\n%s" % (e, traceback.format_exc(limit=8)),
                      flush=True)
                alert("re-kick failed (%s)." % e, "WARN")
            dog.check_stream()
            dog.check_disk()
            # While an ad break owns the program, the deck is muted/hidden
            # and supposed to be still: watch the AD input instead, or the
            # idle deck reads as a stall and faults mid-ad. Stream items
            # replace the media watchdog with feed health (already polled
            # above): a live RTMP pipe reports no useful media state.
            _wst = load_state()
            _ad_stream_break = bool(_wst.get("in_ad_break")) and \
                (_wst.get("stream") or {}).get("slot") == "AD"
            if not stream_item_on_air(data.get("items", []), _wst) \
                    and not _ad_stream_break:
                # Stream-ad breaks: the ad slot feed is watched by the poll
                # block above (rtmp state is useless to watch the way files
                # are). File-ad breaks watch the AD input as before.
                if _wst.get("in_ad_break"):
                    watched = AD_INPUT
                elif _wst.get("deck") == "C":
                    watched = PLAYOUT_C  # fail-safe owns the air
                else:
                    watched = decks[_wst.get("deck", "A")]
                # Only watch a deck if there IS a plane to watch it on.
                # With the plane switched off on purpose, "source missing"
                # is the operator's decision, not a fault: without this the
                # watchdog counted its own absence, escalated to OFF-AIR and
                # then failed to cut (no plane) every pass.
                if PLANE_AUTORESTART:
                    dog.check_source(watched, on_air=True)
        except Exception:
            import traceback
            # Full trace once per distinct error; deaf windows repeat the same
            # failure every poll and would drown the log otherwise.
            sig = traceback.format_exc(limit=3)
            if sig != last_loop_err:
                last_loop_err = sig
                traceback.print_exc()
                alert("loop error (see log for traceback).", "WARN")
        PASS_STATE["ms"] = int((time.time() - pass_started) * 1000)
        PASS_STATE["what"] = ""
        time.sleep(max(1, int(globals().get("WATCH_POLL", 10))))


# --------------------------------------------------------------- selftest ---
class FakeRenderer(Renderer):
    """Offline stand-in: records calls, serves scripted media positions."""

    def __init__(self):
        self.calls = []
        self.pos = {}
        self.forced = {}  # source -> media state, for stall tests
        self.program_scene = SCENE_STARTING
        self.scene_items = [{"sourceName": DECK_A, "sceneItemEnabled": True},
                            {"sourceName": DECK_B, "sceneItemEnabled": False}]

    def set_scene(self, name):
        self.calls.append(("scene", name))

    def set_media_source(self, source, path):
        self.calls.append(("file", source, path))

    def set_source_visible(self, scene, source, visible):
        self.calls.append(("vis", scene, source, visible))

    def set_mute(self, source, muted):
        self.calls.append(("mute", source, bool(muted)))

    def restart_media(self, source):
        self.calls.append(("restart", source))

    def set_volume(self, source, db):
        self.calls.append(("volume", source, db))

    def pause_media(self, source):
        self.calls.append(("pause_out", source))

    def media_action(self, source, action):
        self.calls.append(("act", source, action))

    def get_media_status(self, source):
        return {"time_ms": self.pos.get(source, 0), "duration_ms": 1000,
                "state": self.forced.get(source, "playing")}

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
        if req == "GetSceneItemList":
            return {"sceneItems": self.scene_items}
        if req == "CreateSceneItem":
            self.calls.append(("create_item", data["sceneName"],
                               data["sourceName"]))
            self.scene_items.append({"sourceName": data["sourceName"],
                                     "sceneItemEnabled": False})
            return {}
        if req == "SetSceneItemEnabled":
            self.calls.append(("enable", data["sceneName"],
                               data["sceneItemId"], data["sceneItemEnabled"]))
            return {}
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
    ensure_overlays(r)  # boot repair: ticker+watermark nested into PROGRAM
    assert ("create_item", PROGRAM, SCENE_TICKER) in r.calls, r.calls
    assert ("create_item", PROGRAM, SCENE_WATERMARK) in r.calls, r.calls
    assert r._call("GetSceneItemList")["sceneItems"] == [
        {"sourceName": DECK_A, "sceneItemEnabled": True},
        {"sourceName": DECK_B, "sceneItemEnabled": False},
        {"sourceName": SCENE_TICKER, "sceneItemEnabled": False},
        {"sourceName": SCENE_WATERMARK, "sceneItemEnabled": False}]
    ensure_overlays(r)  # idempotent: neither created again
    assert len(r.calls) >= 4  # both creates recorded exactly once
    assert r.calls.count(("create_item", PROGRAM, SCENE_TICKER)) == 1, r.calls
    advance(r, load_state(), load_playlist(), decks)  # plays a.mp4 on B, visible
    assert ("file", DECK_B, os.path.join(MEDIA, "a.mp4")) in r.calls, r.calls
    assert ("vis", PROGRAM, DECK_B, True) in r.calls, r.calls
    assert ("vis", PROGRAM, DECK_A, False) in r.calls, r.calls
    on_ended(r, decks, IDENT_SRC)  # ident end cuts LIVE, never advances playlist
    assert ("scene", SCENE_LIVE) in r.calls, r.calls
    r.program_scene = "SMILE | Program"  # operator moved on mid-ident: no hijack
    live_calls = len(r.calls)
    on_ended(r, decks, IDENT_SRC)
    assert len(r.calls) == live_calls, r.calls
    on_ended(r, decks, "SOME_PREVIEW")  # unknown sources are ignored
    assert len(r.calls) == live_calls, r.calls
    open(os.path.join(MEDIA, "d.mp4"), "w").write("d")  # dormant never airs...
    open(os.path.join(MEDIA, "e.mp4"), "w").write("e")
    save_playlist({"shuffle_on_complete": False, "items": [
        {"file": "d.mp4", "title": "D", "status": "dormant"},
        {"file": "e.mp4", "title": "E"}]})
    st2 = {"index": 0, "deck": "A", "faults": {}}
    advance(r, st2, load_playlist(), decks)
    assert ("file", DECK_B, os.path.join(MEDIA, "e.mp4")) in r.calls, r.calls
    save_playlist({"shuffle_on_complete": False, "items": [  # ...all dormant holds
        {"file": "d.mp4", "title": "D", "status": "dormant"}]})
    n = len(r.calls)
    advance(r, {"index": 0, "deck": "A", "faults": {}}, load_playlist(), decks)
    assert ("scene", SCENE_TECHDIFF) in r.calls[n:], r.calls
    save_playlist({"shuffle_on_complete": False, "items": [  # pending: silent
        {"title": "P", "source": "http://example.invalid/x"}]})
    n = len(r.calls)
    st3 = {"index": 0, "deck": "A", "faults": {}}
    advance(r, st3, load_playlist(), decks)
    assert ("scene", SCENE_TECHDIFF) in r.calls[n:], r.calls
    assert st3["index"] == 1, st3
    save_playlist({"shuffle_on_complete": False, "items": [  # nameless: loud
        {"file": "gone.mp4", "title": "G"}]})
    n = len(r.calls)
    advance(r, {"index": 0, "deck": "A", "faults": {}}, load_playlist(), decks)
    assert ("scene", SCENE_TECHDIFF) in r.calls[n:], r.calls
    open(STATE, "w").write('{"index": "oops", "deck": "A"}')  # corrupt: coerce
    assert load_state()["index"] == 0
    assert prefetch_order({"items": [{}, {}, {}]}, 5) == [2, 0, 1]
    assert prefetch_order({"items": []}, 0) == []
    evict_cache(cap=0, pinned=frozenset({"a.mp4"}))  # pinned survives any cap...
    assert os.path.exists(os.path.join(MEDIA, "a.mp4")), "pinned file evicted!"
    evict_cache(cap=0)  # ...unpinned, it goes
    assert not os.path.exists(os.path.join(MEDIA, "a.mp4")), "eviction skipped!"
    dog = Watchdog(r)  # stall detector: frozen position faults once stale
    assert dog.check_source(DECK_A, on_air=False) is True
    dog.last_progress[DECK_A] -= 10  # simulate 10s of no movement
    n = len(r.calls)
    assert dog.check_source(DECK_A, on_air=False) is False
    assert ("scene", SCENE_TECHDIFF) not in r.calls[n:], r.calls
    r.pos["IDLE"] = -1  # exists but never played: measured, never faulted
    n = len(r.calls)
    assert dog.check_source("IDLE", on_air=True) is True
    assert len(r.calls) == n, r.calls
    r.pos["STUCK"] = 5  # unseen program state: faults still cut (fail safe)
    assert dog.check_source("STUCK", on_air=True) is True
    dog.last_progress["STUCK"] -= 10
    n = len(r.calls)
    assert dog.check_source("STUCK", on_air=True) is False
    assert ("scene", SCENE_TECHDIFF) in r.calls[n:], r.calls
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
    # ad_plan math: threshold, gap floor, determinism, off-switch.
    long_data = {"ad_every": 4,
                 "ad_plan": {"mid_rolls": 2, "min_gap_min": 15}}
    a = plan_rolls(7200, long_data, "Sintel | http://x/1 | ")
    b = plan_rolls(7200, long_data, "Sintel | http://x/1 | ")
    assert a == b and len(a) == 2, (a, b)  # seeded: UI preview == runtime
    assert a[0] > 15 * 60 and a[1] < 7200 - 15 * 60, a  # gaps from both ends
    assert a[1] - a[0] >= 15 * 60, a
    assert plan_rolls(20 * 60, long_data, "short") == []  # below threshold
    assert plan_rolls(7200, {"ad_every": 0}, "x") == []  # ads globally off
    assert plan_rolls(7200, {"ad_every": 4, "ad_plan": {"enabled": False}}, "x") == []
    assert plan_rolls(None, long_data, "x") == []  # unknown duration: no math
    gaps = [900.0]  # one-mark case: any single mark lands in the window
    m1 = plan_rolls(3600, {"ad_every": 4, "ad_plan": {"mid_rolls": 1}}, "y")
    assert len(m1) == 1 and 900 <= m1[0] <= 2700, m1
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
    # Liveness first, before anything that can block: the plane handshake
    # can hang for a long time, and the dock must still be able to tell
    # "booting" from "dead" instead of showing a false STALLED.
    PASS_STATE["what"] = "booting"
    threading.Thread(target=heartbeat_thread, daemon=True).start()

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
