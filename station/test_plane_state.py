#!/usr/bin/env python3
"""The plane check must not confuse a dead SOCKET with a dead PLANE.

Proved live: the daemon's standing websocket died while the render
plane was up and perfectly well. The poll loop treated the dead
socket as a dead plane, so PLANE_DOWN was set on every pass,
advance() refused to play, and the programme stayed BLACK -- the decks
parked, nothing advancing, the fail-safe never even coming up. The
operator's own workflow (the plane masked on purpose, the daemon
restarted, the operator turns the plane on later) left the station
silent on the bus.

The rules:
  - a dead standing connection is "unknown", not "down": it is dropped
    so the next check makes a FRESH handshake;
  - only a failed fresh handshake can call the plane down;
  - the resume has to clear the flag BEFORE advancing, or advance()
    sees "the plane is down" and refuses to play.

Offline, stdlib only: the renderer and the socket are fakes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import daemon  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


class _Sock:
    """The socket under the websocket (the real code uses ws.s)."""

    def gettimeout(self):
        return None

    def settimeout(self, t):
        pass


class DeadSocket:
    """A standing connection that has died under us."""

    def __init__(self):
        self.closed = False
        self.s = _Sock()

    def _frame(self, op):
        raise OSError("broken pipe")

    def close(self):
        self.closed = True


class LiveSocket:
    def __init__(self):
        self.closed = False
        self.s = _Sock()

    def _frame(self, op):
        pass

    def close(self):
        self.closed = True


class FakeRenderer:
    def __init__(self, shared):
        self._shared = shared
        self._lock = _DummyLock()


class _DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def main():
    orig_ws = daemon._WS

    # 1. a dead standing connection is UNKNOWN, not down
    dead = DeadSocket()
    r = FakeRenderer(dead)
    state, _ = daemon.plane_check(r, gate_pass=2)   # a normal pass
    check(state == "unknown",
          "a dead standing connection is 'unknown', not 'down' (%s)" % state)
    check(dead.closed, "the dead socket is closed")
    check(r._shared is None,
          "the dead socket is dropped, so the next check handshakes fresh")

    # 2. a live standing connection is "up"
    live = LiveSocket()
    r = FakeRenderer(live)
    state, _ = daemon.plane_check(r, gate_pass=2)
    check(state == "up", "a live standing connection is 'up' (%s)" % state)
    check(r._shared is live, "a live connection is kept")

    # 3. a failed FRESH handshake is the only thing that says "down"
    class BadWS:
        def __init__(self, *a, **kw):
            pass

        def recv(self):
            raise OSError("connection refused")

        def close(self):
            pass

    daemon._WS = BadWS
    r = FakeRenderer(None)
    try:
        daemon.plane_check(r, gate_pass=1)
        check(False, "a failed fresh handshake raises")
    except Exception:
        check(True, "a failed fresh handshake raises (the caller says down)")
    finally:
        daemon._WS = orig_ws

    # 4. a fresh handshake that works is "up"
    class GoodWS:
        def __init__(self, *a, **kw):
            pass

        def recv(self):
            return {"op": 0}

        def close(self):
            pass

    daemon._WS = GoodWS
    r = FakeRenderer(None)
    try:
        state, _ = daemon.plane_check(r, gate_pass=1)
        check(state == "up", "a fresh handshake that works is 'up' (%s)" % state)
    finally:
        daemon._WS = orig_ws

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
