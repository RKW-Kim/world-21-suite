#!/usr/bin/env python3
"""Localhost overlay server: serves overlay HTML + pushes live data.

OBS browser sources point at http://127.0.0.1:7070/<page>.html.
The dashboard/daemon POSTs to /state; pages listening on /events update
in place — no reload, no OBS restart. Binds loopback only, never public.

The /console page is the deliberate exception: it is a remote control, not
a graphic, so for LAN tests the server takes BIND (default 127.0.0.1). The
console talks to obs-websocket from the VIEWER's browser, so no inbound
hole is needed beyond the OBS socket itself. Password rides in the URL:
fine on a home LAN, SSH-tunnel-only on the VPS, never raw internet.

  python3 station/overlay_server.py [port]   # default 7070
  BIND=0.0.0.0 python3 station/overlay_server.py 7070  # LAN test only
  curl -X POST 127.0.0.1:7070/state -d '{"presenter":"Wanjiru K."}'
"""

import json
import os
import queue
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

OVERLAY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "overlay")
STATION_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(STATION_DIR, "overlay_state.json")
SUBS = []
LOCK = threading.Lock()

sys.path.insert(0, STATION_DIR)
import daemon  # intents below reuse the CLI's exact functions (no second implementation)
daemon.load_secrets()  # OBS_PASS + webhook for intent calls (see daemon.load_secrets)

INTENTS = {
    "go-live": daemon.do_go_live,
    "tech-diff": daemon.do_tech_diff,
    "resume": daemon.do_resume,
    "return": daemon.do_return,
}

OBS_REQ = None  # one held request connection (OBSRenderer._call is locked)
OBS_LOCK = threading.Lock()
METERS = {}  # inputName -> peak 0..1, fed by the event loop below
METERS_LOCK = threading.Lock()
RELAY_SLOTS = threading.Lock()
RELAY_COUNT = [0]  # active _ws_relay splices; capped so N tabs can't
RELAY_MAX = 4  # multiply deaf-plane load without bound (503 past it)
MUSIC_LOCK = threading.Lock()
MUSIC_BUSY = [False]  # one intake at a time (pins thread + yt-dlp + ffmpeg)
TAP_LOCK = threading.Lock()
TAP_CACHE = {"img": None, "n": 0, "at": 0.0, "pgm": None, "fails": 0}
TAP_STARTED = [False]
TAP_REQ = None  # own renderer (own conn+lock): a stuck tap fetch must
                # never serialize control traffic behind OBS_REQ's lock


def ensure_tap_running():
    with TAP_LOCK:
        if TAP_STARTED[0]:
            return
        TAP_STARTED[0] = True
    threading.Thread(target=tap_poller, daemon=True).start()


def tap_poller():
    # Single-flight program snapshots: every /tap.mjpeg viewer shares one
    # ~2fps fetch loop instead of each hammering GetSourceScreenshot.
    # Backs off exponentially on failure (deaf plane) instead of spinning.
    import base64 as _b64
    global TAP_REQ
    backoff = 0.45
    while True:
        try:
            if TAP_REQ is None:
                TAP_REQ = daemon.OBSRenderer(
                    host=os.environ.get("OBS_HOST", "127.0.0.1"),
                    port=int(os.environ.get("OBS_PORT", "4455")))
            if not TAP_CACHE["pgm"] or TAP_CACHE["n"] % 10 == 0:
                try:
                    TAP_CACHE["pgm"] = TAP_REQ._call(
                        "GetCurrentProgramScene")["currentProgramSceneName"]
                except Exception:
                    pass
            if not TAP_CACHE["pgm"]:
                raise RuntimeError("no program scene (plane down?)")
            shot = TAP_REQ._call("GetSourceScreenshot",
                                 {"sourceName": TAP_CACHE["pgm"], "imageFormat": "jpg"})
            img = shot["imageData"]
            if "," in img:  # 5.7.4 returns a data URI, not bare base64
                img = img.split(",", 1)[1]
            raw = _b64.b64decode(img)
            with TAP_LOCK:
                TAP_CACHE["img"] = raw
                TAP_CACHE["n"] += 1
                TAP_CACHE["at"] = time.time()
                TAP_CACHE["fails"] = 0
            backoff = 0.45
        except Exception as e:
            with TAP_LOCK:
                TAP_CACHE["fails"] += 1
                fails = TAP_CACHE["fails"]
            backoff = min(5.0, backoff * 2 if backoff else 0.45)
            if fails <= 2:
                sys.stderr.write("overlay: tap poll failed (%s)\n" % e)
        time.sleep(backoff)


def obs_req():
    global OBS_REQ
    with OBS_LOCK:
        if OBS_REQ is None:
            OBS_REQ = daemon.OBSRenderer(
                host=os.environ.get("OBS_HOST", "127.0.0.1"),
                port=int(os.environ.get("OBS_PORT", "4455")))
        return OBS_REQ


def plane_call(fn, timeout=4.0):
    """Run a plane RPC on a throwaway thread with a hard ceiling.

    A wedged plane is a known failure shape: the shared connection opens,
    says nothing, and an INLINE call pins this handler thread for up to
    OBS_TIMEOUT (60s) -- and a page polling that route piles threads up
    until the server exhausts. The 4s cap exists once (the /music probe);
    every handler-side plane call goes through here now. A wedged call
    leaves one doomed daemon thread behind -- the honest price of
    answering instead of hanging."""
    out = {}

    def _go():
        try:
            out["v"] = fn()
        except Exception as e:
            out["e"] = e

    th = threading.Thread(target=_go, daemon=True)
    th.start()
    th.join(timeout)
    if th.is_alive():
        raise TimeoutError("plane did not answer within %ss" % timeout)
    if "e" in out:
        raise out["e"]
    return out["v"]


def obs_event_loop():
    # Second connection, events only. Meters feed the console cache;
    # scene/studio changes fan out over the existing SSE bus (overlay
    # pages ignore the extra 'obs' key). Reconnects forever: a deaf
    # window must not silently end the event feed.
    import base64
    import hashlib
    host = os.environ.get("OBS_HOST", "127.0.0.1")
    port = int(os.environ.get("OBS_PORT", "4455"))
    while True:
        ws = None
        try:
            ws = daemon._WS(host, port, timeout=60)
            hello = ws.recv()
            if hello.get("op") != 0:
                raise RuntimeError("not v5")
            d = {"rpcVersion": 1, "eventSubscriptions": 2047 | 65536}
            auth = (hello.get("d") or {}).get("authentication")
            if auth:
                secret = base64.b64encode(hashlib.sha256(
                    (os.environ.get("OBS_PASS", "") + auth["salt"]).encode()).digest()).decode()
                d["authentication"] = base64.b64encode(hashlib.sha256(
                    (secret + auth["challenge"]).encode()).digest()).decode()
            ws.send({"op": 1, "d": d})
            if ws.recv().get("op") != 2:
                raise RuntimeError("identify rejected")
            while True:
                m = ws.recv()
                if m.get("op") != 5 or not m.get("d"):
                    continue
                et, ed = m["d"].get("eventType"), m["d"].get("eventData", {}) or {}
                if et == "InputVolumeMeters":
                    with METERS_LOCK:
                        for i in ed.get("inputs", []) or []:
                            lv = i.get("inputLevelsMul") or [[0]]
                            peak = lv[0][1] if len(lv[0]) > 1 else lv[0][0]
                            METERS[i.get("inputName")] = peak
                elif et == "CurrentProgramSceneChanged" and ed.get("sceneName"):
                    broadcast({"obs": {"programScene": ed["sceneName"]}})
                elif et == "CurrentPreviewSceneChanged" and ed.get("sceneName"):
                    broadcast({"obs": {"previewScene": ed["sceneName"]}})
                elif et == "StudioModeStateChanged":
                    broadcast({"obs": {"studioMode": bool(ed.get("studioModeEnabled"))}})
        except Exception as e:
            sys.stderr.write("overlay: obs events down (%s); retry in 5s\n" % e)
            try:
                if ws is not None:
                    ws.close()
            except Exception:
                pass
            time.sleep(5)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    tmp = STATE_FILE + ".new"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def broadcast(state):
    payload = ("data: %s\n\n" % json.dumps(state)).encode()
    with LOCK:
        live = []
        for entry in SUBS:
            q, closer = entry
            try:
                q.put_nowait(payload)
                live.append(entry)
            except queue.Full:
                # slow consumer: kill its connection so the handler thread
                # exits instead of leaking on a wedged queue forever.
                try:
                    closer()
                except Exception:
                    pass
        SUBS[:] = live


def intake_history(limit=20):
    """Past fetches, newest first. Read-only: the intake worker owns writes."""
    import sqlite3
    try:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(daemon.MEDIA, "intake.db"),
                              uri=True, timeout=2)
        try:
            rows = con.execute(
                "SELECT title, source, filename, duration, intake_date FROM intake ORDER BY rowid DESC LIMIT ?",
                (limit,)).fetchall()
        finally:
            con.close()   # a failed query used to leak the connection
    except Exception:
        return []
    return [{"title": r[0], "source": r[1], "file": r[2],
             "duration": r[3], "date": r[4]} for r in rows]


def adjust_index(op, pos, ni, to=None):
    """Keep state.index aimed at the same ITEM across library edits.
    Pure, so the edge tests can pin it. pos: inserted/removed/moved-from
    position; to: move destination; ni: current index. Removing the aimed
    item promotes whatever slides into its place (no jump, no replay)."""
    if op == "add":
        if 0 <= pos <= ni:
            return ni + 1
    elif op == "remove":
        if pos is not None and pos < ni:
            return max(0, ni - 1)
    elif op == "move" and pos is not None and to is not None:
        if pos < ni <= to:
            return ni - 1
        if to <= ni < pos:
            return ni + 1
    return ni


def library_view():
    """Playlist items enriched with on-disk truth. Read-only; the operator
    sees presence, size, pin and status without ever opening a terminal."""
    try:
        data = daemon.load_playlist()
    except (OSError, ValueError):
        data = {"items": []}
    items = data.get("items", [])
    try:
        st = daemon.load_state()
    except (OSError, ValueError):
        st = {}
    out, media_bytes = [], 0
    dex = st.get("index", 0)
    dex = dex if isinstance(dex, int) else 0
    nxt = None  # what advance() would ACTUALLY play next: first playable
    for off in range(len(items)):  # at/after the cursor, wrapping once
        i = (dex + off) % len(items)
        it = items[i]
        if it.get("status") == "dormant":
            continue
        f = it.get("file") or ""
        if (f and os.path.isfile(os.path.join(daemon.MEDIA, f))) or it.get("youtube"):
            nxt = i
            break
    for i, it in enumerate(items):
        f = it.get("file") or ""
        p = os.path.join(daemon.MEDIA, f) if f else ""
        present = bool(f) and os.path.isfile(p)
        size = os.path.getsize(p) if present else None
        if present:
            media_bytes += size
        mode = "youtube" if it.get("youtube") else ("source" if it.get("source") else "file")
        out.append({"file": f, "title": it.get("title") or f,
                    "show": it.get("show") or "",
                    "status": it.get("status") or "active",
                    "pinned": bool(it.get("pinned")),
                    "has_source": bool(it.get("source")),
                    "youtube": it.get("youtube") or "",
                    "mode": mode,
                    "present": present, "size": size,
                    "duration": it.get("duration"),
                    "up_next": nxt is not None and i == nxt})
    try:
        free = shutil.disk_usage(daemon.ROOT).free
    except OSError:
        free = None
    return {"items": out,
            "state": {"index": st.get("index", 0), "deck": st.get("deck", "A")},
            "disk": {"free": free, "media_bytes": media_bytes,
                     "cap": daemon.CACHE_CAP}}


def ads_view():
    """Everything the Ads+AUTOMATION views need in one read: the cycle
    config, the plan, the pool, and the exact roll marks each item will
    run — computed by the SAME planner the daemon executes, so the
    timeline the operator sees is the timeline that happens."""
    try:
        data = daemon.load_playlist()
    except (OSError, ValueError):
        data = {}
    try:
        st = daemon.load_state()
    except (OSError, ValueError):
        st = {}
    plan = data.get("ad_plan") if isinstance(data.get("ad_plan"), dict) else {}
    pool = []
    for f in data.get("ad_files") or []:
        if isinstance(f, str) and os.path.isfile(os.path.join(daemon.MEDIA, f)):
            pool.append({"kind": "file", "name": f})
    for u in data.get("ad_links") or []:
        if isinstance(u, str) and u:
            pool.append({"kind": "link", "name": u})
    nxt, items = [], data.get("items", [])
    dex = st.get("index", 0)
    dex = dex if isinstance(dex, int) else 0
    for window in range(min(len(items), 10)):  # next 10 items get a timeline
        it = items[(dex + window) % len(items)] if items else None
        if it is None:
            break
        dur = None
        if it.get("youtube"):
            # Duration from the item's own field (the daemon's resolve
            # cache lives in the daemon process — from here it is always
            # empty; recent plans learned durations and wrote them into
            # playlist entries, so this is the honest durable record).
            dur = it.get("duration")
        elif it.get("file"):
            dur = it.get("duration")  # files learn marks from their clock
        marks = daemon.plan_rolls(dur, data,
                                  daemon.roll_marks_onair(it, data))
        nxt.append({"title": it.get("title") or it.get("file") or
                    it.get("youtube", "?"),
                    "duration": dur, "marks": marks,
                    "status": it.get("status") or "active"})
    return {"ad_every": data.get("ad_every") or 0,
            "ad_plan": {"threshold_min": plan.get("threshold_min") if
                        plan.get("threshold_min") else 30,
                        "mid_rolls": plan.get("mid_rolls") if
                        plan.get("mid_rolls") is not None else 2,
                        "min_gap_min": plan.get("min_gap_min") if
                        plan.get("min_gap_min") else 15,
                        "enabled": plan.get("enabled", True) is not False},
            "ad_files": data.get("ad_files") or [],
            "ad_links": data.get("ad_links") or [],
            "pool": pool, "since_ad": st.get("since_ad", 0),
            "queue": nxt, "index": dex,
            "on_air": bool(st.get("in_ad_break"))}


THUMB_DIR = os.path.join(daemon.MEDIA, ".thumbs")
THUMB_SEM = threading.Semaphore(2)   # at most 2 concurrent thumbnail decodes
THUMB_LOCKS = {}
THUMB_LOCKS_GUARD = threading.Lock()
THUMB_LOCKS_CAP = 512


def thumb_path(fname):
    """Serve (generating once, cached) a poster frame for a media/ file.
    ffmpeg takes 25% in — front-loaded intros are covers, not content."""
    fname = os.path.basename(fname)  # no traversal
    src = os.path.join(daemon.MEDIA, fname)
    if not os.path.isfile(src):
        return None
    os.makedirs(THUMB_DIR, exist_ok=True)
    out = os.path.join(THUMB_DIR, fname + ".jpg")
    # One lock object per filename EVER requested grew without bound; when
    # the map passes its cap, entries whose media is gone are dropped. A
    # lock dropped while held is harmless: the holder still releases it.
    if len(THUMB_LOCKS) > THUMB_LOCKS_CAP:
        with THUMB_LOCKS_GUARD:
            for k in [k for k in THUMB_LOCKS
                      if not os.path.isfile(os.path.join(daemon.MEDIA, k))]:
                THUMB_LOCKS.pop(k, None)
    lock = THUMB_LOCKS.get(fname)
    if lock is None:
        with THUMB_LOCKS_GUARD:
            lock = THUMB_LOCKS.setdefault(fname, threading.Lock())
    if lock.acquire(timeout=25):
        try:
            if not os.path.exists(out):
                # At most 2 decoders at a time: the daemon and OBS need
                # this box's CPU more than a page of thumbnails does.
                # Write to a tmp name and rename: a timeout-killed ffmpeg
                # used to leave a HALF JPEG at the final name, and it was
                # then served forever (the cache never re-checks). The tmp
                # keeps a .jpg suffix so ffmpeg's muxer guess still works.
                tmp = out[:-4] + ".part.jpg"
                with THUMB_SEM:
                    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                                    "-y", "-ss", "0.25", "-i", src, "-frames:v", "1",
                                    "-vf", "scale=320:-1", "-q:v", "5", tmp],
                                   timeout=20, check=True)
                    os.replace(tmp, out)
        except Exception:
            try:
                if os.path.exists(out + ".part"):
                    os.remove(out + ".part")
            except OSError:
                pass
        finally:
            lock.release()
    if not os.path.exists(out):
        return None
    return out


MUSIC_DIR = os.path.join(daemon.MEDIA, "music")
os.makedirs(MUSIC_DIR, exist_ok=True)
BED_INPUT = "Music Bed"
# The bed is a WAITING-ROOM bed: the scenes that carry no media of their
# own. Program and Ad Break carry audio and must never share with it.
BED_SCENES = ("Starting", "Off Air", "End Credits", "TechDiffs")
MONITOR_PATH = "monitor"  # MediaMTX path the lab profile streams to
MONITOR_AV_PATH = "monitor-av"  # same return, Opus audio (ffmpeg repack)
MONITOR_WHEP = "http://127.0.0.1:8889/%s/whep"
WHEP_PATHS = {"monitor", "monitor-av"}


def monitor_path_status(name):
    """Is a monitor path actually publishing? Read-only; short fuse."""
    import urllib.request as _url
    try:
        with _url.urlopen("http://127.0.0.1:9997/v3/paths/get/%s" % name,
                           timeout=3) as r:
            d = json.loads(r.read().decode())
        src = d.get("source") or {}
        return {"live": bool(d.get("ready") and d.get("source")),
                "ready": bool(d.get("ready")),
                "source": src.get("type"),
                "tracks": [t.get("codec") for t in d.get("tracks2", [])]}
    except Exception as e:
        return {"live": False, "error": str(e)[:120]}


def monitor_status():
    out = monitor_path_status(MONITOR_PATH)
    out["av"] = monitor_path_status(MONITOR_AV_PATH)
    return out


def music_tracks():
    try:
        files = [f for f in sorted(os.listdir(MUSIC_DIR))
                 if f.lower().endswith((".mp3", ".mp4", ".m4a", ".ogg", ".wav", ".flac"))
                 and os.path.isfile(os.path.join(MUSIC_DIR, f))]
    except OSError:
        files = []
    return files


def ensure_bed():
    """Music Bed ffmpeg loop input, present in the waiting-room scenes
    (Starting / Off Air / End Credits). Audio beds cannot be global inputs, so one input lives in
    each waiting scene; cuts between them restart the bed (documented,
    accepted for v1). Returns the input name."""
    ins = {i.get("inputName") for i in
           obs_req()._call("GetInputList").get("inputs", [])}
    if BED_INPUT not in ins:
        scenes = [s.get("sceneName", "") for s in
                  obs_req()._call("GetSceneList").get("scenes", [])]
        targets = [s for s in scenes if any(k in s for k in BED_SCENES)]
        first = targets[0] if targets else scenes[0]
        obs_req()._call("CreateInput", {"sceneName": first, "inputName": BED_INPUT,
                                        "inputKind": "ffmpeg_source",
                                        "inputSettings": {"looping": True}})
        for s in targets[1:]:
            try:
                obs_req()._call("CreateSceneItem", {"sceneName": s, "sourceName": BED_INPUT})
            except Exception:
                pass
    return BED_INPUT


def _bed_probe():
    # Module level, not a Handler method: as a class-body name it was never
    # in method scope, so every GET /music raised NameError inside the probe
    # thread and answered plane:"?" bed:null. Its OWN connection: the shared
    # renderer serialises on one lock, so a probe that used it blocked /obs
    # and /music behind it.
    try:
        r = daemon.OBSRenderer()
        ins = {i.get("inputName") for i in
               r._call("GetInputList").get("inputs", [])}
        if BED_INPUT in ins:
            return {"bed": (r._call("GetInputSettings",
                                    {"inputName": BED_INPUT})
                            .get("inputSettings", {}).get("local_file")),
                    "plane": "up"}
        return {"bed": None, "plane": "up"}
    except Exception:
        return {"bed": None, "plane": "down"}


class Handler(SimpleHTTPRequestHandler):
    # 30s socket timeout. The base class default is None, and
    # StreamRequestHandler only calls settimeout() when it is set: a
    # client that connects and says nothing pinned a thread + fd forever.
    timeout = 30
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=OVERLAY_DIR, **kw)

    def _token_ok(self):
        # Bearer via header (POST/fetch) or ?token= (WebSocket handshakes
        # cannot carry custom headers). compare_digest: a wrong guess must
        # not be faster than a right one.
        import hmac
        tok = os.environ.get("STATION_TOKEN", "")
        if not tok:
            return False, None
        supplied = ""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            supplied = auth[len("Bearer "):]
        if not supplied:
            q = parse_qs(urlparse(self.path).query).get("token", [""])[0]
            supplied = q
        return bool(supplied) and \
            hmac.compare_digest(supplied.encode(), tok.encode()), tok

    def _guard(self):
        # Control-plane guard. The threat: ANY web page open in ANY browser
        # on this network can fire POSTs at this server (no preflight if the
        # body is text/plain; the old Access-Control-* did not stop that).
        # Allowed:
        #   - non-browser clients (no Origin header): ssh, curl, systemd.
        #   - same-origin pages we serve (console/media/studio/whip).
        #   - file:// operator panes ("null" origin) — only while no token
        #     is set; once STATION_TOKEN exists they must present it.
        #   - every origin, if the request carries the bearer token.
        # Set STATION_TOKEN (secrets.env or systemd) once this box speaks to
        # the WAN; Origins outside our Host are refused without it.
        ok, tok = self._token_ok()
        if ok:
            return True
        origin = self.headers.get("Origin", "")
        if not origin:
            return True
        if origin == "null" and not tok:
            return True
        host = self.headers.get("Host", "")
        return origin.rstrip("/") in ("http://" + host, "https://" + host)

    def _guard_control(self):
        # The surfaces that hand out AUTHENTICATED render-plane control
        # (/ws relay, /obs proxy) are a stricter tier: the relay completes
        # OBS authentication with the server-side secret, so a client here
        # never needs — but effectively gets — the OBS password. When a
        # STATION_TOKEN exists, those surfaces REQUIRE it: any Origin,
        # same-origin or not, tunnel or LAN. Without a token the ordinary
        # _guard trust model applies (loopback + tunnels only).
        ok, tok = self._token_ok()
        if tok:
            return ok
        return self._guard()

    def _refused(self):
        self.send_error(403, "origin/referrer refused (set STATION_TOKEN to pin your client)")

    def do_GET(self):
        if self.headers.get("Upgrade", "").lower() == "websocket":
            if not self._guard_control():
                return self._refused()
            return self._ws_relay()
        # /console /media /studio: archived on branch archive/console-studio
        # (2026-10-18). Control now lives on the OBS window over VNC; a single
        # successor page will replace them later.
        elif self.path == "/whip" or self.path.startswith("/whip?"):
            # Contribution seats: publishes browser media into MediaMTX over
            # WHIP (the OBS side needs nothing — seats fill themselves).
            self._serve_file(os.path.join(STATION_DIR, "whip.html"), "text/html", nocache=True)
        elif self.path == "/state":
            if not self._guard():
                # The file:// pages are allowed by _guard; a random site
                # in the operator's browser is not.
                return self._refused()
            body = json.dumps(load_state()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")  # file:// pages
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/obs/meters":
            with METERS_LOCK:
                snap = dict(METERS)
            self._json(200, snap)
        elif self.path == "/tap.mjpeg":
            return self._tap()
        elif self.path.startswith("/files/"):
            return self._serve_media(urlparse(self.path).path[7:])
        elif self.path.startswith("/thumbs/"):
            from urllib.parse import unquote
            tp = thumb_path(unquote(urlparse(self.path).path[len("/thumbs/"):]))
            if not tp:
                self.send_error(404)
                return
            with open(tp, "rb") as fh:
                img = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(img)))
            self.end_headers()
            self.wfile.write(img)
        elif self.path == "/library":
            self._json(200, library_view())
        elif self.path == "/ads":
            self._json(200, ads_view())
        elif self.path == "/intake":
            self._json(200, {"history": intake_history()})
        elif self.path == "/music":
            return self._music()
        elif self.path == "/monitor":
            return self._json(200, monitor_status())
        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")  # file:// pages
            self.end_headers()
            # Reap the dead: a client that vanishes without a FIN leaves
            # the socket ESTABLISHED and the heartbeat writes keep
            # succeeding, so the thread and the SUBS entry live forever.
            try:
                self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            except OSError:
                pass
            q = queue.Queue(maxsize=16)

            def _close_sse():
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
            entry = (q, _close_sse)
            with LOCK:
                SUBS.append(entry)
            try:
                self.wfile.write(("data: %s\n\n" % json.dumps(load_state())).encode())
                self.wfile.flush()
                while True:
                    try:
                        self.wfile.write(q.get(timeout=25))
                    except queue.Empty:
                        # heartbeat comment: keeps intermediaries from
                        # timing out idle SSE, and bounds the thread's
                        # blocking window so eviction actually kills it.
                        self.wfile.write(b":hb\n\n")
                    self.wfile.flush()
            except OSError:
                pass
            finally:
                with LOCK:
                    try:
                        SUBS.remove(entry)
                    except ValueError:
                        pass
        else:
            super().do_GET()

    def do_POST(self):
        if not self._guard():
            return self._refused()
        path = urlparse(self.path).path
        if path.startswith("/intent/"):
            return self._intent(path[len("/intent/"):])
        if path == "/library":
            return self._library_update()
        if path == "/ads":
            return self._ads_update()
        if path == "/obs":
            # _guard_control: /obs is authenticated render-plane control
            # (the server holds the OBS secret for the caller).
            if not self._guard_control():
                return self._refused()
            return self._obs_proxy()
        if path == "/music":
            return self._music()
        if path == "/whep":
            return self._whep()
        if path != "/state":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 262144:
                # A negative length reads until EOF (hangs); a huge one
                # allocates it, and the state push multiplies it by every
                # SSE subscriber. This is a memory bomb, not a nitpick.
                return self.send_error(413, "body too large")
            patch = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_error(400, "bad JSON")
            return
        with daemon.pl_lock():
            # load inside the lock: the daemon's fault()/advance saves
            # must not land between our read and write.
            state = load_state()
            state.update(patch if isinstance(patch, dict) else {})
            save_state(state)
        broadcast(state)
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _intent(self, name):
        # Director intents over HTTP: same functions the CLI runs, so the
        # phone and the terminal can never disagree about what GO LIVE does.
        # Trust model = same as /state (LAN/tunnel-only users, no auth token).
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 262144:
                # A negative length reads until EOF (hangs); a huge one
                # allocates it, and the state push multiplies it by every
                # SSE subscriber. This is a memory bomb, not a nitpick.
                return self.send_error(413, "body too large")
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except ValueError:
            body = {}
        try:
            r = obs_req()          # the shared connection, not a new one
            if name == "scene":
                if not body.get("name"):
                    return self._json(400, {"ok": False, "error": "scene needs {\"name\"}"})
                plane_call(lambda: daemon.do_scene(r, body["name"]))
            elif name in INTENTS:
                # GO LIVE and friends run a whole cut sequence: 8s ceiling.
                plane_call(lambda: INTENTS[name](r), timeout=8.0)
            else:
                return self._json(404, {"ok": False, "error": "unknown intent"})
        except TimeoutError as e:
            # A wedged plane answers 504 honestly instead of pinning the
            # handler thread for OBS_TIMEOUT while the polls pile up.
            return self._json(504, {"ok": False, "error": str(e)})
        except Exception as e:
            return self._json(502, {"ok": False, "error": str(e)[:200]})
        return self._json(200, {"ok": True})

    def _ads_update(self):
        """Write the ad config: cycle count, plan keys, pool links. Takes
        effect at the next transition (the daemon reloads on hash change)."""
        body = self._read_body()
        if body is None:
            return
        return self._playlist_write(lambda: self._ads_write(body))

    def _read_body(self):
        """Parse the request body BEFORE any lock work. Reading inside
        pl_lock let a slow/drip-feeding client hold the cross-process
        flock for the whole body read (the socket timeout resets per
        recv) — the playout loop blocks on that lock ~20x per pass."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 262144:
                # A negative length reads until EOF (hangs); a huge one
                # allocates it, and the state push multiplies it by every
                # SSE subscriber. This is a memory bomb, not a nitpick.
                self.send_error(413, "body too large")
                return None
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_error(400, "bad JSON")
            return None

    def _playlist_write(self, fn):
        # pl_lock is a flock-based CROSS-PROCESS mutex (see daemon): the
        # daemon's shuffle/advance and intake's append can't slide between
        # our load and save. Whole RMW inside the lock, every time - and
        # only the RMW: the body is read before we get here.
        with daemon.pl_lock():
            return fn()

    def _ads_write(self, body):
        try:
            data = daemon.load_playlist()
        except (OSError, ValueError):
            return self._json(502, {"ok": False, "error": "playlist unreadable"})
        if "ad_every" in body:
            try:
                data["ad_every"] = max(0, int(body["ad_every"]))
            except (TypeError, ValueError):
                return self._json(400, {"ok": False, "error": "ad_every must be a number"})
        if "ad_links" in body:
            if not isinstance(body["ad_links"], list):
                return self._json(400, {"ok": False, "error": "ad_links must be a list"})
            data["ad_links"] = [u for u in body["ad_links"]
                                if isinstance(u, str) and u.strip()]
        if "ad_files" in body:
            if not isinstance(body["ad_files"], list):
                return self._json(400, {"ok": False, "error": "ad_files must be a list"})
            data["ad_files"] = [f for f in body["ad_files"]
                                if isinstance(f, str) and f]
        if "ad_plan" in body:
            pl = body["ad_plan"]
            if not isinstance(pl, dict):
                return self._json(400, {"ok": False, "error": "ad_plan must be an object"})
            cur = data.get("ad_plan") if isinstance(data.get("ad_plan"), dict) else {}
            cur = dict(cur)
            for k in ("threshold_min", "mid_rolls", "min_gap_min"):
                if k in pl:
                    try:
                        cur[k] = float(pl[k])
                    except (TypeError, ValueError):
                        return self._json(400, {"ok": False, "error": "%s must be a number" % k})
            if "enabled" in pl:
                cur["enabled"] = bool(pl["enabled"])
            data["ad_plan"] = cur
        daemon.save_playlist(data)
        return self._json(200, {"ok": True})

    def _library_update(self):
        # Library manager writes: pin/status toggles, metadata edits,
        # add / remove / reorder. Same trust model as /state; serialization
        # lives in _playlist_write (cross-process flock).
        body = self._read_body()
        if body is None:
            return
        return self._playlist_write(lambda: self._library_write(body))

    def _library_write(self, body):
        try:
            data = daemon.load_playlist()
        except (OSError, ValueError):
            return self._json(502, {"ok": False, "error": "playlist unreadable"})
        # NOTE: this read-modify-write runs inside _playlist_write's
        # pl_lock. That is safe now that the daemon side always
        # re-loads fresh under pl_lock before saving: neither side can any
        # longer clobber the other with a minutes-stale copy. Worst case is
        # a lost shuffle ORDER (self-heals at loop end), never lost items.
        items = data.setdefault("items", [])
        op = body.get("op", "set")
        # Pending items (source, no file yet) share file:"" — address them
        # by position. Cached items match by file name as before.
        idx = None
        if isinstance(body.get("index"), int) and 0 <= body["index"] < len(items):
            idx = body["index"]
        elif body.get("file"):
            idx = next((i for i, it in enumerate(items) if it.get("file") == body["file"]), None)
        at = moved = None
        if op == "add":
            title = (body.get("title") or "").strip()
            source = (body.get("source") or "").strip()
            fname = (body.get("file") or "").strip()
            ylink = (body.get("youtube") or "").strip()
            if not title:
                return self._json(400, {"ok": False, "error": "add needs {\"title\"}"})
            if not ylink and not source and not fname:
                return self._json(400, {"ok": False, "error": "add needs a link (source/youtube) or a file already in media/"})
            if fname:
                if "/" in fname or fname.startswith(".") or not os.path.isfile(os.path.join(daemon.MEDIA, fname)):
                    return self._json(400, {"ok": False, "error": "file not in media/"})
            item = {"title": title}
            if fname:
                item["file"] = fname
            elif ylink:
                item["youtube"] = ylink
                if isinstance(body.get("duration"), (int, float)) and body["duration"] > 0:
                    item["duration"] = int(body["duration"])
            else:
                item["file"] = ""
                item["source"] = source  # prefetch resolves it, daemon links it
            if body.get("show"):
                item["show"] = body["show"]
            if body.get("status") in ("active", "dormant"):
                item["status"] = body["status"]
            pos = body.get("position", "end")
            if isinstance(pos, int) and 0 <= pos <= len(items):
                items.insert(pos, item)
                at = pos
            else:
                items.append(item)
                at = len(items) - 1
        elif op == "remove":
            if idx is None:
                return self._json(404, {"ok": False, "error": "no such item (pending items need {\"index\"})"})
            item = items.pop(idx)
            f = item.get("file") or ""
            if body.get("delete_file") and f and "/" not in f and not f.startswith("."):
                if not any(i.get("file") == f for i in items):
                    try:
                        os.remove(os.path.join(daemon.MEDIA, f))
                    except OSError:
                        pass
        elif op == "move":
            if idx is None:
                return self._json(404, {"ok": False, "error": "no such item (pending items need {\"index\"})"})
            try:
                to = int(body.get("to", 0))
            except (TypeError, ValueError):
                return self._json(400, {"ok": False, "error": "move needs {\"to\": index}"})
            item = items.pop(idx)
            newp = max(0, min(to, len(items)))
            items.insert(newp, item)
            moved = (idx, newp)
        else:  # set: pin / status / title / show / source on one item
            if idx is None:
                return self._json(404, {"ok": False, "error": "no such item (pending items need {\"index\"})"})
            it = items[idx]
            if "pinned" in body:
                it["pinned"] = bool(body["pinned"])
            if "status" in body:
                if body["status"] not in ("active", "dormant"):
                    return self._json(400, {"ok": False, "error": "status is active|dormant"})
                it["status"] = body["status"]
            for k in ("title", "show", "source"):
                if body.get(k) is not None:
                    it[k] = body[k]
        if op in ("add", "remove", "move"):
            # Aim state.index at the same ITEM across the edit; the loop
            # reloads state fresh at every transition, so this sticks.
            try:
                st8 = daemon.load_state()
            except (OSError, ValueError):
                st8 = None
            if st8 is not None and isinstance(st8.get("index"), int):
                ni = st8["index"]
                if op == "add" and at is not None:
                    ni = adjust_index("add", at, ni)
                elif op == "remove" and idx is not None:
                    ni = adjust_index("remove", idx, ni)
                elif op == "move" and moved is not None:
                    ni = adjust_index("move", moved[0], ni, moved[1])
                if ni != st8["index"]:
                    st8["index"] = ni
                    daemon.save_state(st8)
        daemon.save_playlist(data)
        return self._json(200, {"ok": True, "items": len(items)})

    def _whep(self):
        # Same-origin WHEP signaling proxy: the MBA posts its SDP offer
        # here, so only :7070 needs to be reachable from the operator side.
        # ICE media itself still flows direct MBA<->lab (same LAN).
        # ?path= selects the monitor path (whitelisted): monitor-av first
        # (video+Opus), plain monitor as video-only fallback.
        import urllib.request as _url
        import urllib.error as _ue
        from urllib.parse import parse_qs as _pq, urlparse as _up
        name = _pq(_up(self.path).query).get("path", ["monitor"])[0]
        if name not in WHEP_PATHS:
            self.send_error(400, "unknown monitor path")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        if length <= 0 or length > 65536:
            self.send_error(400, "SDP offer required")
            return
        try:
            offer = self.rfile.read(length)
        except Exception:
            self.send_error(400, "offer unreadable")
            return
        try:
            req = _url.Request(MONITOR_WHEP % name, data=offer,
                               headers={"Content-Type": "application/sdp"},
                               method="POST")
            with _url.urlopen(req, timeout=10) as r:
                answer = r.read()
                code = r.status
        except _ue.HTTPError as e:
            try:
                detail = e.read()[:200]
            except Exception:
                detail = b""
            self.send_error(502, "whep refused: %s %s" % (e.code, detail.decode(errors="replace")))
            return
        except Exception as e:
            self.send_error(502, "whep unreachable: %s" % str(e)[:120])
            return
        self.send_response(code)
        self.send_header("Content-Type", "application/sdp")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(answer)))
        self.end_headers()
        self.wfile.write(answer)

    def _obs_proxy(self):
        # Generic OBS passthrough over the held connection. Same trust as
        # /state (LAN/tunnel-only): the browser never sees :4455 or the
        # password, and never pays a handshake.
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 262144:
                # A negative length reads until EOF (hangs); a huge one
                # allocates it, and the state push multiplies it by every
                # SSE subscriber. This is a memory bomb, not a nitpick.
                return self.send_error(413, "body too large")
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"ok": False, "error": "bad JSON"})
        rtype = body.get("type", "")
        if not rtype or not rtype.isalpha():
            return self._json(400, {"ok": False, "error": "call needs {\"type\"}"})
        data = body.get("data") or {}
        if not isinstance(data, dict):
            return self._json(400, {"ok": False, "error": "data must be an object"})
        try:
            return self._json(200, {"ok": True, "response": plane_call(
                lambda: obs_req()._call(rtype, data), timeout=8.0)})
        except TimeoutError as e:
            return self._json(504, {"ok": False, "error": str(e)})
        except Exception as e:
            # Honest status: transport failures (plane down/deaf) are 502;
            # application refusals (bad names) stay 200 ok:False.
            msg = str(e)
            transport = isinstance(e, OSError) or any(
                k in msg for k in ("closed", "handshake", "unreachable",
                                   "timed out", "reset", "refused", "EOF",
                                   "not connected", "connection reset"))
            if transport:
                return self._json(502, {"ok": False, "error": msg[:200]})
            return self._json(200, {"ok": False, "error": msg[:200]})

    def _music(self):
        # Music bed management. GET: tracks on disk + current bed file.
        # POST {op:set, file}: validate, ensure the input, point + restart.
        # POST {op:add, source, title}: intake to media/, then move to music/.
        if self.command == "GET":
            # Bound the plane read: a wedged RPC (plane wedge is a known
            # failure shape) must not hang the library page's Promise.all.
            out = {"bed": None, "plane": "?"}
            th = threading.Thread(target=lambda: out.update(_bed_probe()),
                                  daemon=True)
            th.start()
            th.join(4)
            if th.is_alive():
                out["plane"] = "slow"
            return self._json(200, dict(tracks=music_tracks(),
                                        bed=out.get("bed"), plane=out.get("plane")))
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 262144:
                # A negative length reads until EOF (hangs); a huge one
                # allocates it, and the state push multiplies it by every
                # SSE subscriber. This is a memory bomb, not a nitpick.
                return self.send_error(413, "body too large")
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"ok": False, "error": "bad JSON"})
        op = body.get("op", "set")
        if op == "add":
            source = (body.get("source") or "").strip()
            title = (body.get("title") or "music").strip()[:40]
            if not source:
                return self._json(400, {"ok": False, "error": "add needs {\"source\"}"})
            # One intake at a time: each pins a handler thread + yt-dlp +
            # ffmpeg for up to 30 min on a loaded box. Second caller gets
            # 429, not a pileup.
            with MUSIC_LOCK:
                if MUSIC_BUSY[0]:
                    return self._json(429, {"ok": False, "error": "an intake is already running; try when it lands"})
                MUSIC_BUSY[0] = True
            try:
                import uuid as _uuid
                safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title).strip("_") or "music"
                tmp = "%s_%s_m.mp4" % (safe, _uuid.uuid4().hex[:8])
                proc = None
                try:
                    proc = subprocess.Popen(
                        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake.py"),
                         source, "--as", tmp, "--title", title],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, start_new_session=True)
                    out, err = proc.communicate(timeout=1800)
                    rc = proc.returncode
                except subprocess.TimeoutExpired:
                    # Whole process group: intake's ffmpeg grandchild dies
                    # with it (plain kill on intake.py left orphans + a
                    # partial file eating the quota).
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass
                    proc.communicate()
                    return self._json(502, {"ok": False, "error": "intake timed out"})
                except Exception as e:
                    if proc is not None:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        except Exception:
                            pass
                    return self._json(502, {"ok": False, "error": "intake failed to start: %s" % e})
                if rc != 0:
                    return self._json(502, {"ok": False, "error": (err or out or "intake failed")[-300:]})
                try:
                    os.rename(os.path.join(daemon.MEDIA, tmp), os.path.join(MUSIC_DIR, tmp))
                except OSError as e:
                    return self._json(502, {"ok": False, "error": "move to music/ failed: %s" % e})
                return self._json(200, {"ok": True, "file": tmp})
            finally:
                with MUSIC_LOCK:
                    MUSIC_BUSY[0] = False
        fname = (body.get("file") or "").strip()
        if not fname or "/" in fname or fname.startswith("."):
            return self._json(400, {"ok": False, "error": "set needs a plain filename"})
        if not os.path.isfile(os.path.join(MUSIC_DIR, fname)):
            return self._json(404, {"ok": False, "error": "not in music/"})
        try:
            ensure_bed()
            plane_call(lambda: obs_req()._call(
                "SetInputSettings",
                {"inputName": BED_INPUT,
                 "inputSettings": {"local_file": os.path.join(MUSIC_DIR, fname),
                                   "looping": True},
                 "overlay": True}))
            plane_call(lambda: obs_req()._call(
                "TriggerMediaInputAction",
                {"inputName": BED_INPUT,
                 "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"}))
        except TimeoutError as e:
            return self._json(504, {"ok": False, "error": str(e)})
        except Exception as e:
            return self._json(502, {"ok": False, "error": str(e)[:200]})
        return self._json(200, {"ok": True, "file": fname})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        # No wildcard CORS here: every page that reads these routes is
        # same-origin (served by us) — an open mirror on other tabs would
        # only widen the read surface (library/ads state leak) for nothing.
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_media(self, rel):
        # Machine-independent file standard: every collection references
        # media as http://<host>:7070/files/<name>, never /home/... paths,
        # so the same JSON airs on any machine that holds the bytes (via
        # intake links or explicit sync). Rooted at media/ ONLY: secrets.env
        # lives one level up and must never be reachable. Range-capable so
        # ffmpeg inputs and <video> can seek.
        import mimetypes
        import urllib.parse as _up
        rel = _up.unquote(rel)
        if "\x00" in rel:
            # A %00 in the path raises ValueError from os.path.join --
            # outside the OSError catch, that killed the connection with
            # no response at all. A bad request gets a bad-request answer.
            self.send_error(400, "bad path")
            return
        path = os.path.normpath(os.path.join(daemon.MEDIA, rel))
        # realpath: a symlink inside media/ must not escape to secrets.env
        # (one level up) or anywhere else. Dotfiles never served either.
        try:
            real = os.path.realpath(path)
        except OSError:
            self.send_error(404)
            return
        if real != daemon.MEDIA and not real.startswith(daemon.MEDIA + os.sep):
            self.send_error(403)
            return
        if os.path.basename(real).startswith(".") or os.path.islink(path):
            self.send_error(403)
            return
        path = real
        if not os.path.isfile(path):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        size = os.path.getsize(path)
        start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes="):
            try:
                part = rng[6:].split("-", 1)
                if not part[0] and part[1]:
                    # "bytes=-500" means the LAST 500 bytes, not the first.
                    start = max(0, size - int(part[1]))
                    end = size - 1
                else:
                    start = int(part[0]) if part[0] else 0
                    end = int(part[1]) if part[1] else size - 1
                end = min(end, size - 1)
                if start > end or start >= size:
                    raise ValueError
                code = 206
            except ValueError:
                self.send_error(416)
                return
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if code == 206:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)

    def _tap(self):
        # Confidence monitor: program stills as MJPEG (~2fps). One shared
        # background poller feeds every viewer from a single frame cache —
        # N viewers used to mean N screenshot RPCs each, hammering the deaf
        # plane linearly. Viewers that arrive to a stale cache (>15s, plane
        # down) get 503 instead of a frozen lie. No OBS reconfiguration, no
        # second encode, no new dependency — a plain <img> renders it.
        ensure_tap_running()
        t0 = time.time()
        while time.time() - t0 < 12:
            with TAP_LOCK:
                n, img, at = TAP_CACHE["n"], TAP_CACHE["img"], TAP_CACHE["at"]
            if img is not None:
                break
            time.sleep(0.25)
        else:
            self.send_error(503, "render plane unreachable (no frame yet)")
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=smileframe")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        last = -1
        try:
            while True:
                with TAP_LOCK:
                    n, img, at = TAP_CACHE["n"], TAP_CACHE["img"], TAP_CACHE["at"]
                if img is None or time.time() - at > 15:
                    break  # stale cache: end the stream, don't serve a lie
                if n != last:
                    self.wfile.write(b"--smileframe\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(img))
                    self.wfile.write(img + b"\r\n")
                    last = n
                time.sleep(0.2)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            sys.stderr.write("overlay: tap ended (%s)\n" % e)

    def _ws_relay(self):
        # Raw obs-websocket relay for full clients (the /studio replica):
        # finish the browser handshake here, then splice TCP bytes to the
        # render plane untouched. Auth stays end-to-end (their own connect
        # dialog asks for the password); this endpoint only decides who may
        # reach the socket at all (LAN/tunnel-only, same trust as /obs).
        # Target pinned to the OBS port: a render-plane relay, not a proxy.
        import base64
        import hashlib
        import socket as _sock
        import struct as _st
        try:
            port = int(parse_qs(urlparse(self.path).query).get("XTransformPort", [""])[0])
        except (TypeError, ValueError):
            port = 0
        if port != int(os.environ.get("OBS_PORT", "4455")):
            self.send_error(400, "relay target is the OBS port only")
            return
        key = self.headers.get("Sec-WebSocket-Key", "")
        if not key:
            self.send_error(400, "websocket upgrade required")
            return
        accept = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        def ws_read(sock):
            # One unmasked server-role text frame -> parsed JSON. Pings get
            # a masked pong (client role toward OBS) and we keep reading.
            # Iterative, not recursive: a ping flood must not grow the stack.
            def rd(n):
                buf = b""
                while len(buf) < n:
                    chunk = sock.recv(n - len(buf))
                    if not chunk:
                        raise RuntimeError("OBS EOF")
                    buf += chunk
                return buf
            while True:
                hdr = rd(2)
                op, ln = hdr[0] & 0x0F, hdr[1] & 0x7F
                if ln == 126:
                    ln = _st.unpack(">H", rd(2))[0]
                elif ln == 127:
                    ln = _st.unpack(">Q", rd(8))[0]
                if hdr[1] & 0x80:
                    raise RuntimeError("masked OBS frame")
                payload = rd(ln)
                if op == 0x8:
                    raise RuntimeError("OBS closed")
                if op == 0x9:
                    mask = os.urandom(4)
                    sock.sendall(bytes([0x8A, 0x80 | 0]) + mask)
                    continue
                if op != 0x1:
                    raise RuntimeError("expected text frame")
                return json.loads(payload.decode())

        def ws_send_masked(obj):
            payload = json.dumps(obj).encode()
            n = len(payload)
            mask = os.urandom(4)
            if n < 126:
                hdr = bytes([0x81, 0x80 | n])
            elif n < 65536:
                hdr = bytes([0x81, 0x80 | 126]) + _st.pack(">H", n)
            else:
                hdr = bytes([0x81, 0x80 | 127]) + _st.pack(">Q", n)
            up.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

        up = None
        claimed = [False]

        def done_relay():
            # idempotent relay-slot release; every exit path must call it
            # or the cap wedges at zero real sessions.
            if claimed[0]:
                claimed[0] = False
                with RELAY_SLOTS:
                    RELAY_COUNT[0] = max(0, RELAY_COUNT[0] - 1)

        try:
            with RELAY_SLOTS:
                if RELAY_COUNT[0] >= RELAY_MAX:
                    raise RuntimeError("relay busy (%d sessions max) — close another obs-relay tab" % RELAY_MAX)
                RELAY_COUNT[0] += 1
                claimed[0] = True
            up = _sock.create_connection(
                (os.environ.get("OBS_HOST", "127.0.0.1"), port), timeout=10)
            ukey = base64.b64encode(os.urandom(16)).decode()
            up.sendall(("GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nUpgrade: websocket\r\n"
                        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
                        "Sec-WebSocket-Version: 13\r\n\r\n" % (port, ukey)).encode())
            uhead = b""
            while b"\r\n\r\n" not in uhead:
                chunk = up.recv(4096)
                if not chunk:
                    raise RuntimeError("OBS-side handshake EOF")
                uhead += chunk
                if len(uhead) > 65536:
                    raise RuntimeError("OBS-side handshake too large")
            if b" 101 " not in uhead.split(b"\r\n", 1)[0]:
                raise RuntimeError("OBS-side handshake rejected")
            # validate the upstream accept (wrong key = proxy/shadow, not OBS)
            expect = base64.b64encode(hashlib.sha1(
                (ukey + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            if expect.encode() not in uhead:
                raise RuntimeError("OBS-side accept mismatch")
            hello = ws_read(up)
            if hello.get("op") != 0:
                raise RuntimeError("not v5")
        except (OSError, RuntimeError) as e:
            done_relay()
            try:
                if up is not None:
                    up.close()
            except Exception:
                pass
            sys.stderr.write("overlay: ws relay upstream failed (%s)\n" % e)
            self.send_error(502, "render plane unreachable: %s" % e)
            return
        try:
            self.request.sendall(
                ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                 "Connection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
        except OSError:
            done_relay()
            try:
                if up is not None:
                    up.close()
            except Exception:
                pass
            return
        sys.stderr.write("overlay: ws relay open (browser -> OBS :%d)\n" % port)
        self.close_connection = True
        down = self.connection

        def srv_send(obj):
            # server-role frame: unmasked, as browsers require.
            payload = json.dumps(obj).encode()
            n = len(payload)
            hdr = bytes([0x81])
            if n < 126:
                hdr += bytes([n])
            elif n < 65536:
                hdr += bytes([126]) + _st.pack(">H", n)
            else:
                hdr += bytes([127]) + _st.pack(">Q", n)
            down.sendall(hdr + payload)

        def cli_read():
            # browser-role frame: masked, as servers require. Answers ping,
            # then keeps reading for the Identify.
            # Iterative, not recursive: a ping flood must not grow the stack.
            while True:
                hdr = b""
                while len(hdr) < 2:
                    chunk = self.rfile.read(2 - len(hdr))
                    if not chunk:
                        raise RuntimeError("browser EOF")
                    hdr += chunk
                op, ln = hdr[0] & 0x0F, hdr[1] & 0x7F
                if ln == 126:
                    ln = _st.unpack(">H", _read_exact(2))[0]
                elif ln == 127:
                    ln = _st.unpack(">Q", _read_exact(8))[0]
                if ln > 32 * 1024 * 1024:
                    # Same cap daemon._WS applies: the declared length is
                    # client-controlled and _read_exact would otherwise
                    # accumulate it (a 2^63 header = a memory bomb).
                    raise RuntimeError("frame too large (%d)" % ln)
                if not hdr[1] & 0x80:
                    raise RuntimeError("unmasked browser frame")
                mask = _read_exact(4)
                payload = _read_exact(ln)
                data = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
                if op == 0x8:
                    raise RuntimeError("browser closed")
                if op == 0x9:  # ping -> pong, then keep reading for Identify
                    down.sendall(bytes([0x8A, 0x00]))
                    continue
                if op != 0x1:
                    raise RuntimeError("expected text frame")
                return json.loads(data.decode())

        def _read_exact(n):
            # Reads via rfile, not the raw socket: the handler's buffered
            # reader may already hold frame bytes (readahead past the HTTP
            # headers). Raw recv would miss them and hang.
            buf = b""
            while len(buf) < n:
                chunk = self.rfile.read(n - len(buf))
                if not chunk:
                    raise RuntimeError("browser EOF")
                buf += chunk
            return buf

        # Auth bridge: the browser identifies however it likes (empty
        # password included); the relay completes authentication with the
        # server-side secret and forwards an authenticated Identify.
        down.settimeout(15)
        try:
            srv_send(hello)  # clients start from Hello, not from the 101.
            ident = cli_read()
            if ident.get("op") != 1:
                raise RuntimeError("expected Identify")
            auth = (hello.get("d") or {}).get("authentication")
            if auth:
                secret = base64.b64encode(hashlib.sha256(
                    (os.environ.get("OBS_PASS", "") + auth["salt"]).encode()).digest()).decode()
                ident["d"]["authentication"] = base64.b64encode(hashlib.sha256(
                    (secret + auth["challenge"]).encode()).digest()).decode()
            ws_send_masked(ident)
            identified = ws_read(up)
            if identified.get("op") != 2:
                raise RuntimeError("identify rejected")
            srv_send(identified)
            sys.stderr.write("overlay: relay bridged (authenticated)\n")
        except Exception as e:
            # Broad on purpose: a malformed Identify (missing/null "d")
            # raised KeyError/TypeError past the old tuple and skipped
            # done_relay forever - two of those wedged the relay at its
            # session cap until a service restart.
            sys.stderr.write("overlay: relay auth failed (%s)\n" % e)
            self.close_connection = True
            try:
                # the 101 already went out: speak a close frame so the
                # browser lands in onclose instead of hanging open.
                body = _st.pack(">H", 4400) + b"obs auth failed"
                down.sendall(bytes([0x88, len(body)]) + body)
            except Exception:
                pass
            try:
                up.close()
            except Exception:
                pass
            done_relay()
            return
        finally:
            # Splice phase: quiet is normal (muted scene, no events), so no
            # read timeouts — but dead legs must still be reaped. Kernel
            # keepalives catch vanished peers; an idle watchdog catches the
            # deaf-but-open plane (accepts, never speaks, never FINs). A
            # relay silent for 120s is abandoned by design: the client's
            # dead-man redials at 20s of silence, and a healthy plane moves
            # stats bytes ~1/s. Only dead legs go quiet.
            for s in (down, up):
                try:
                    s.setsockopt(_sock.SOL_SOCKET, _sock.SO_KEEPALIVE, 1)
                    s.setsockopt(_sock.IPPROTO_TCP, _sock.TCP_KEEPIDLE, 60)
                    s.setsockopt(_sock.IPPROTO_TCP, _sock.TCP_KEEPINTVL, 15)
                    s.setsockopt(_sock.IPPROTO_TCP, _sock.TCP_KEEPCNT, 4)
                except Exception:
                    pass
            down.settimeout(None)
            try:
                up.settimeout(None)
            except Exception:
                pass
            last = [time.time()]

            def watchdog():
                while True:
                    time.sleep(30)
                    if time.time() - last[0] > 120:
                        sys.stderr.write("overlay: relay idle 120s — tearing down\n")
                        try:
                            down.shutdown(_sock.SHUT_RDWR)
                        except Exception:
                            pass
                        try:
                            up.shutdown(_sock.SHUT_RDWR)
                        except Exception:
                            pass
                        return

            threading.Thread(target=watchdog, daemon=True).start()

        SNIFF = os.environ.get("OBS_RELAY_SNIFF", "")
        FULLSNIFF = os.environ.get("OBS_RELAY_FULLSNIFF", "")
        sniffs = {"n": 0}

        def sniff(tag, chunk):
            # Env-gated frame peek for post-mortems: direction, opcode, len.
            # FULLSNIFF removes the cap for single-session captures.
            # RPCLOG decodes small JSON frames to bare request/event names.
            # NOTE: post-bridge chunks are raw stream slices, not frame
            # aligned — op/len here are best-effort, not gospel.
            if not SNIFF or (not FULLSNIFF and sniffs["n"] >= 40):
                return
            sniffs["n"] += 1
            try:
                b1, b2 = chunk[0], chunk[1]
                ln = b2 & 0x7F
                sys.stderr.write("overlay: relay frame %s op=%d len~%d masked=%s\n"
                                 % (tag, b1 & 0x0F, ln, bool(b2 & 0x80)))
                if (b1 & 0x0F) == 0x8:
                    sys.stderr.write("overlay: relay close payload: %r\n" % chunk[2:80])
            except Exception:
                pass

        def rpc_log(tag, payload):
            if not os.environ.get("OBS_RELAY_RPCLOG", ""):
                return
            try:
                d = json.loads(payload.decode())
                inner = d.get("d", {})
                sys.stderr.write("overlay: relay rpc %s op=%s %s\n"
                                 % (tag, d.get("op"),
                                    inner.get("requestType") or inner.get("eventType") or "?"))
            except Exception:
                pass

        def pump_down():
            # Browser leg reads via rfile.read1: pipelined frames may sit in
            # the buffered reader, and read() would block for a full chunk.
            # Ending here must release the main pump too, or the handler
            # thread leaks with the OBS socket held open.
            nbytes = 0
            try:
                while True:
                    chunk = self.rfile.read1(65536)
                    if not chunk:
                        break
                    up.sendall(chunk)
                    nbytes += len(chunk)
                    last[0] = time.time()
                    if SNIFF and nbytes == len(chunk):
                        sys.stderr.write("overlay: relay first browser bytes: %r\n" % chunk[:160])
                    sniff("browser->obs", chunk)
            except (OSError, ValueError) as e:
                sys.stderr.write("overlay: relay browser->obs down (%s after %d bytes)\n" % (e, nbytes))
            else:
                sys.stderr.write("overlay: relay browser->obs EOF (%d bytes)\n" % nbytes)
            try:
                up.shutdown(_sock.SHUT_RDWR)
            except OSError:
                pass

        def pump(src, dst, tag):
            # Raw-socket leg (OBS side is never buffered): block for data.
            nbytes = 0
            try:
                while True:
                    chunk = src.recv(65536)
                    if not chunk:
                        break
                    sniff(tag, chunk)
                    dst.sendall(chunk)
                    nbytes += len(chunk)
                    last[0] = time.time()
            except OSError as e:
                sys.stderr.write("overlay: relay %s down (%s after %d bytes)\n" % (tag, e, nbytes))
                return
            sys.stderr.write("overlay: relay %s EOF (%d bytes)\n" % (tag, nbytes))

        threading.Thread(target=pump_down, daemon=True).start()
        pump(up, down, "obs->browser")
        try:
            up.close()
        except OSError:
            pass
        try:
            down.shutdown(_sock.SHUT_RDWR)
        except OSError:
            pass
        done_relay()

    def _serve_file(self, path, ctype, nocache=False):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        if nocache:
            self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Strip the query: console URLs carry ?pass=<OBS_PASS> and the
        # request line otherwise lands verbatim in the systemd journal.
        if self.path.split("?")[0] not in ("/events",):
            clean = self.path.split("?")[0]
            sys.stderr.write("overlay: %s %s\n" % (self.command, clean))


if __name__ == "__main__":
    bind = os.environ.get("BIND", "127.0.0.1")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7070

    class Server(ThreadingHTTPServer):
        # SSE handlers block in queue.get() forever; without daemon threads
        # Ctrl+C hangs on shutdown instead of exiting. Learned, not theorized.
        daemon_threads = True

    srv = Server((bind, port), Handler)
    print("overlay server on http://%s:%d/ (%s)" %
          (bind, port, "LOOPBACK ONLY" if bind in ("127.0.0.1", "localhost") else "LAN-EXPOSED: tunnel on VPS"),
          flush=True)
    threading.Thread(target=obs_event_loop, daemon=True).start()
    srv.serve_forever()
