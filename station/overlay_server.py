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
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

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
                    "up_next": bool(items) and i == st.get("index", 0) % len(items)})
    try:
        free = shutil.disk_usage(daemon.ROOT).free
    except OSError:
        free = None
    return {"items": out,
            "state": {"index": st.get("index", 0), "deck": st.get("deck", "A")},
            "disk": {"free": free, "media_bytes": media_bytes,
                     "cap": daemon.CACHE_CAP}}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=OVERLAY_DIR, **kw)

    def do_GET(self):
        if self.path == "/console" or self.path.startswith("/console?"):
            self._serve_file(os.path.join(STATION_DIR, "console.html"), "text/html")
        elif self.path == "/state":
            body = json.dumps(load_state()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")  # file:// pages
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/library":
            self._json(200, library_view())
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
        # Pin / dormant toggles from the console. Atomic save; the daemon
        # reloads the playlist on hash change, so edits take effect at the
        # next transition, never mid-air. Same trust model as /state.
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"ok": False, "error": "bad JSON"})
        f = (body.get("file") or "")
        if not f:
            return self._json(400, {"ok": False, "error": "item needs {\"file\"}"})
        try:
            data = daemon.load_playlist()
        except (OSError, ValueError) as e:
            return self._json(502, {"ok": False, "error": "playlist unreadable"})
        for it in data.get("items", []):
            if it.get("file") == f:
                break
        else:
            return self._json(404, {"ok": False, "error": "no such item"})
        if "pinned" in body:
            it["pinned"] = bool(body["pinned"])
        if "status" in body:
            if body["status"] not in ("active", "dormant"):
                return self._json(400, {"ok": False, "error": "status is active|dormant"})
            it["status"] = body["status"]
        daemon.save_playlist(data)
        return self._json(200, {"ok": True, "file": f})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
    srv.serve_forever()
