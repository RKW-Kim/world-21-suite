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


def obs_req():
    global OBS_REQ
    with OBS_LOCK:
        if OBS_REQ is None:
            OBS_REQ = daemon.OBSRenderer(
                host=os.environ.get("OBS_HOST", "127.0.0.1"),
                port=int(os.environ.get("OBS_PORT", "4455")))
        return OBS_REQ


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
        dead = []
        for q in SUBS:
            try:
                q.put_nowait(payload)
            except queue.Full:
                dead.append(q)
        for q in dead:
            SUBS.remove(q)


def intake_history(limit=20):
    """Past fetches, newest first. Read-only: the intake worker owns writes."""
    import sqlite3
    try:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(daemon.MEDIA, "intake.db"),
                              uri=True, timeout=2)
        rows = con.execute(
            "SELECT title, source, filename, duration, intake_date FROM intake ORDER BY rowid DESC LIMIT ?",
            (limit,)).fetchall()
        con.close()
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
        if f and os.path.isfile(os.path.join(daemon.MEDIA, f)):
            nxt = i
            break
    for i, it in enumerate(items):
        f = it.get("file") or ""
        p = os.path.join(daemon.MEDIA, f) if f else ""
        present = bool(f) and os.path.isfile(p)
        size = os.path.getsize(p) if present else None
        if present:
            media_bytes += size
        out.append({"file": f, "title": it.get("title") or f,
                    "show": it.get("show") or "",
                    "status": it.get("status") or "active",
                    "pinned": bool(it.get("pinned")),
                    "has_source": bool(it.get("source")),
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


MUSIC_DIR = os.path.join(daemon.MEDIA, "music")
os.makedirs(MUSIC_DIR, exist_ok=True)
BED_INPUT = "Music Bed"
BED_SCENES = ("Starting", "Off Air", "End Credits")


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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=OVERLAY_DIR, **kw)

    def do_GET(self):
        if self.headers.get("Upgrade", "").lower() == "websocket":
            return self._ws_relay()
        if self.path == "/console" or self.path.startswith("/console?"):
            self._serve_file(os.path.join(STATION_DIR, "console.html"), "text/html")
        elif self.path == "/media" or self.path.startswith("/media?"):
            self._serve_file(os.path.join(STATION_DIR, "media.html"), "text/html")
        elif self.path == "/studio" or self.path.startswith("/studio/"):
            if self.path == "/studio":
                # Bare path breaks relative assets (css/ resolves to /css/).
                # Redirect so the browser lands on /studio/ instead.
                self.send_response(301)
                self.send_header("Location", "/studio/")
                self.end_headers()
                return
            rel = urlparse(self.path).path[8:] or "index.html"
            return self._serve_tree(os.path.join(STATION_DIR, "studio"), rel)
        elif self.path == "/state":
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
        elif self.path == "/library":
            self._json(200, library_view())
        elif self.path == "/intake":
            self._json(200, {"history": intake_history()})
        elif self.path == "/music":
            return self._music()
        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")  # file:// pages
            self.end_headers()
            q = queue.Queue(maxsize=16)
            with LOCK:
                SUBS.append(q)
            try:
                self.wfile.write(("data: %s\n\n" % json.dumps(load_state())).encode())
                self.wfile.flush()
                while True:
                    self.wfile.write(q.get())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with LOCK:
                    if q in SUBS:
                        SUBS.remove(q)
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/intent/"):
            return self._intent(path[len("/intent/"):])
        if path == "/library":
            return self._library_update()
        if path == "/obs":
            return self._obs_proxy()
        if path == "/music":
            return self._music()
        if path != "/state":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            patch = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_error(400, "bad JSON")
            return
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
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except ValueError:
            body = {}
        try:
            r = daemon.OBSRenderer()
            if name == "scene":
                if not body.get("name"):
                    return self._json(400, {"ok": False, "error": "scene needs {\"name\"}"})
                daemon.do_scene(r, body["name"])
            elif name in INTENTS:
                INTENTS[name](r)
            else:
                return self._json(404, {"ok": False, "error": "unknown intent"})
        except Exception as e:
            return self._json(502, {"ok": False, "error": str(e)[:200]})
        return self._json(200, {"ok": True})

    def _library_update(self):
        # Library manager writes: pin/status toggles, metadata edits,
        # add / remove / reorder. Atomic save; the daemon reloads the
        # playlist on hash change, so edits take effect at the next
        # transition, never mid-air. Same trust model as /state.
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"ok": False, "error": "bad JSON"})
        try:
            data = daemon.load_playlist()
        except (OSError, ValueError):
            return self._json(502, {"ok": False, "error": "playlist unreadable"})
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
            if not title:
                return self._json(400, {"ok": False, "error": "add needs {\"title\"}"})
            if not source and not fname:
                return self._json(400, {"ok": False, "error": "add needs a link (source) or a file already in media/"})
            if fname:
                if "/" in fname or fname.startswith(".") or not os.path.isfile(os.path.join(daemon.MEDIA, fname)):
                    return self._json(400, {"ok": False, "error": "file not in media/"})
            item = {"title": title}
            if fname:
                item["file"] = fname
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

    def _obs_proxy(self):
        # Generic OBS passthrough over the held connection. Same trust as
        # /state (LAN/tunnel-only): the browser never sees :4455 or the
        # password, and never pays a handshake.
        try:
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
            return self._json(200, {"ok": True, "response": obs_req()._call(rtype, data)})
        except Exception as e:
            return self._json(200, {"ok": False, "error": str(e)[:200]})

    def _music(self):
        # Music bed management. GET: tracks on disk + current bed file.
        # POST {op:set, file}: validate, ensure the input, point + restart.
        # POST {op:add, source, title}: intake to media/, then move to music/.
        if self.command == "GET":
            bed = None
            try:
                ins = {i.get("inputName") for i in
                       obs_req()._call("GetInputList").get("inputs", [])}
                if BED_INPUT in ins:
                    bed = (obs_req()._call("GetInputSettings",
                                           {"inputName": BED_INPUT})
                           .get("inputSettings", {}).get("local_file"))
            except Exception:
                pass
            return self._json(200, {"tracks": music_tracks(), "bed": bed})
        try:
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
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title).strip("_") or "music"
            tmp = safe + "_m.mp4"
            try:
                p = subprocess.run(
                    [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake.py"),
                     source, "--as", tmp, "--title", title],
                    capture_output=True, text=True, timeout=1800)
            except Exception as e:
                return self._json(502, {"ok": False, "error": "intake failed to start: %s" % e})
            if p.returncode != 0:
                return self._json(502, {"ok": False, "error": (p.stderr or p.stdout or "intake failed")[-300:]})
            try:
                os.rename(os.path.join(daemon.MEDIA, tmp), os.path.join(MUSIC_DIR, tmp))
            except OSError as e:
                return self._json(502, {"ok": False, "error": "move to music/ failed: %s" % e})
            return self._json(200, {"ok": True, "file": tmp})
        fname = (body.get("file") or "").strip()
        if not fname or "/" in fname or fname.startswith("."):
            return self._json(400, {"ok": False, "error": "set needs a plain filename"})
        if not os.path.isfile(os.path.join(MUSIC_DIR, fname)):
            return self._json(404, {"ok": False, "error": "not in music/"})
        try:
            ensure_bed()
            obs_req()._call("SetInputSettings",
                            {"inputName": BED_INPUT,
                             "inputSettings": {"local_file": os.path.join(MUSIC_DIR, fname),
                                               "looping": True},
                             "overlay": True})
            obs_req()._call("TriggerMediaInputAction",
                            {"inputName": BED_INPUT, "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"})
        except Exception as e:
            return self._json(502, {"ok": False, "error": str(e)[:200]})
        return self._json(200, {"ok": True, "file": fname})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
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
        path = os.path.normpath(os.path.join(daemon.MEDIA, rel))
        if path != daemon.MEDIA and not path.startswith(daemon.MEDIA + os.sep):
            self.send_error(403)
            return
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
                start = int(part[0]) if part[0] else 0
                end = int(part[1]) if part[1] else size - 1
                end = min(end, size - 1)
                if start >= size:
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
        # Confidence monitor: program stills as MJPEG (~2fps). No OBS
        # reconfiguration, no second encode, no new dependency — a plain
        # <img> renders it. Browsers drop the connection on navigate;
        # anything else breaks the loop below.
        import base64 as _b64
        try:
            pgm = obs_req()._call("GetCurrentProgramScene")["currentProgramSceneName"]
        except Exception:
            self.send_error(503, "render plane unreachable")
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=smileframe")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        n = 0
        try:
            while True:
                if n % 10 == 0:
                    try:
                        pgm = obs_req()._call("GetCurrentProgramScene")["currentProgramSceneName"]
                    except Exception:
                        pass
                shot = obs_req()._call("GetSourceScreenshot",
                                       {"sourceName": pgm, "imageFormat": "jpg"})
                img = shot["imageData"]
                if "," in img:  # 5.7.4 returns a data URI, not bare base64
                    img = img.split(",", 1)[1]
                raw = _b64.b64decode(img)
                self.wfile.write(b"--smileframe\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(raw))
                self.wfile.write(raw + b"\r\n")
                n += 1
                time.sleep(0.45)
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
            def rd(n):
                buf = b""
                while len(buf) < n:
                    chunk = sock.recv(n - len(buf))
                    if not chunk:
                        raise RuntimeError("OBS EOF")
                    buf += chunk
                return buf
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
                return ws_read(sock)
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

        try:
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
            if b" 101 " not in uhead.split(b"\r\n", 1)[0]:
                raise RuntimeError("OBS-side handshake rejected")
            hello = ws_read(up)
            if hello.get("op") != 0:
                raise RuntimeError("not v5")
        except (OSError, RuntimeError) as e:
            try:
                up.close()
            except Exception:
                pass
            self.send_error(502, "render plane unreachable: %s" % e)
            return
        try:
            self.request.sendall(
                ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                 "Connection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
        except OSError:
            up.close()
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
            hdr = b""
            while len(hdr) < 2:
                chunk = down.recv(2 - len(hdr))
                if not chunk:
                    raise RuntimeError("browser EOF")
                hdr += chunk
            op, ln = hdr[0] & 0x0F, hdr[1] & 0x7F
            if ln == 126:
                ln = _st.unpack(">H", _read_exact(2))[0]
            elif ln == 127:
                ln = _st.unpack(">Q", _read_exact(8))[0]
            if not hdr[1] & 0x80:
                raise RuntimeError("unmasked browser frame")
            mask = _read_exact(4)
            payload = _read_exact(ln)
            data = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
            if op == 0x8:
                raise RuntimeError("browser closed")
            if op == 0x9:  # ping -> pong, then keep reading for Identify
                down.sendall(bytes([0x8A, 0x00]))
                return cli_read()
            if op != 0x1:
                raise RuntimeError("expected text frame")
            return json.loads(data.decode())

        def _read_exact(n):
            buf = b""
            while len(buf) < n:
                chunk = down.recv(n - len(buf))
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
        except (OSError, RuntimeError, ValueError) as e:
            sys.stderr.write("overlay: relay auth failed (%s)\n" % e)
            self.close_connection = True
            try:
                up.close()
            except Exception:
                pass
            return
        finally:
            # Handshake timeouts must not leak into the splice: either leg
            # going quiet (no events, muted scene) is normal and must hold.
            down.settimeout(None)
            try:
                up.settimeout(None)
            except Exception:
                pass

        def pump(src, dst):
            try:
                while True:
                    chunk = src.recv(65536)
                    if not chunk:
                        break
                    dst.sendall(chunk)
            except OSError:
                pass

        threading.Thread(target=pump, args=(down, up), daemon=True).start()
        pump(up, down)
        try:
            up.close()
        except OSError:
            pass
        try:
            down.shutdown(_sock.SHUT_RDWR)
        except OSError:
            pass

    def _serve_tree(self, base, rel):
        import mimetypes
        path = os.path.normpath(os.path.join(base, rel))
        if path != base and not path.startswith(base + os.sep):
            self.send_error(403)
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if path.endswith(".js"):
            ctype = "text/javascript"  # ES modules refuse octet-stream
        self._serve_file(path, ctype)

    def _serve_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        if self.path not in ("/events",):
            sys.stderr.write("overlay: %s\n" % (fmt % args))


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
