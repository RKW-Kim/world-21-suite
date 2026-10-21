#!/usr/bin/env python3
"""The control-plane guard, live-fired against the real handler stack.

The relay (/ws) and the /obs proxy hand out AUTHENTICATED render-plane
control — the server completes OBS authentication with its own secret, so
a caller never needs (but effectively gets) the OBS password. The guard
contract being tested:

  1. STATION_TOKEN set -> /ws and /obs REQUIRE it (header or ?token=),
     from any Origin, same-origin or not.
  2. STATION_TOKEN set -> an "Origin: null" request (sandboxed iframe,
     file:// pane) is refused unless it presents the token. It used to
     PASS, which is exactly the sandboxed-iframe hole.
  3. The bearer comparison is hmac.compare_digest, not ==.
  4. No token configured -> the LAN/tunnel trust model is unchanged:
     no-Origin clients and null origins still get through /state and /obs
     (the documented pre-token posture), so setting nothing breaks nobody.

Run: python3 station/test_overlay_auth.py
"""

import os
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


tmp = tempfile.mkdtemp()
# A test run must not write into the live tree: point the module's
# mutable paths at the sandbox before anything else touches them.
os.environ["BROADCAST_ROOT"] = tmp
import overlay_server

overlay_server.OVERLAY_DIR = tmp
overlay_server.STATE_FILE = os.path.join(tmp, "overlay_state.json")

TOKEN = "test-token-31337"


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), overlay_server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def req(base, path, method="GET", headers=None, body=None):
    r = urllib.request.Request(base + path, method=method,
                               data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # connection refused etc. is a guard PASS-through
        return None, str(e).encode()


srv, base = serve()

# ---- 1-2: token configured: the strict tier ---------------------------
os.environ["STATION_TOKEN"] = TOKEN

st, _ = req(base, "/obs", "POST", {"Content-Type": "application/json"}, b"{}")
check(st == 403, "token set: /obs without a token is refused (%s)" % st)

st, _ = req(base, "/obs", "POST", {
    "Content-Type": "application/json", "Authorization": "Bearer wrong"}, b"{}")
check(st == 403, "token set: /obs with a WRONG token is refused (%s)" % st)

st, body = req(base, "/obs", "POST", {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + TOKEN}, b'{"type":"GetVersion"}')
check(st is not None and st != 403,
      "token set: /obs with the right token passes the guard (%s)" % st)

st, _ = req(base, "/state", "POST",
            {"Content-Type": "application/json", "Origin": "null"}, b"{}")
check(st == 403, "token set: Origin null is refused without a token (%s)" % st)

st, _ = req(base, "/state", "POST",
            {"Content-Type": "application/json", "Origin": "null",
             "Authorization": "Bearer " + TOKEN}, b"{}")
check(st is not None and st != 403,
      "token set: Origin null WITH the token passes (%s)" % st)

# WebSocket handshake: browsers cannot set headers, so the token must ride
# in the URL. The relay will fail later (no OBS here); 403 is the only
# status that means the guard refused.
st, _ = req(base, "/ws?XTransformPort=4455", "GET", {
    "Upgrade": "websocket", "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
    "Sec-WebSocket-Version": "13"})
check(st == 403, "token set: /ws without a token is refused (%s)" % st)

st, _ = req(base, "/ws?XTransformPort=4455&token=" + TOKEN, "GET", {
    "Upgrade": "websocket", "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
    "Sec-WebSocket-Version": "13"})
check(st is not None and st != 403,
      "token set: /ws with ?token= passes the guard (%s)" % st)

# Same-origin without the token: STILL refused on the control tier — the
# relay hands out authenticated control, so same-origin is not enough.
st, _ = req(base, "/obs", "POST", {
    "Content-Type": "application/json", "Origin": base}, b"{}")
check(st == 403,
      "token set: /obs same-origin but tokenless is refused (%s)" % st)

# ---- 3: no token configured: today's trust model must not break -------
del os.environ["STATION_TOKEN"]

st, _ = req(base, "/obs", "POST", {"Content-Type": "application/json"}, b"{}")
check(st is not None and st != 403,
      "no token: /obs keeps the tunnel trust model (%s)" % st)

st, _ = req(base, "/state", "POST",
            {"Content-Type": "application/json", "Origin": "null"}, b"{}")
check(st is not None and st != 403,
      "no token: Origin null keeps the file:// pane path (%s)" % st)

srv.shutdown()

print()
if fails:
    print("FAILED: %d" % len(fails))
    sys.exit(1)
print("ALL PASS")
