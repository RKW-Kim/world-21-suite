"""The plane_call deadline is a BOUND, not a lie: every plane_call takes a
generation, and the renderer refuses an RPC older than one that already
sent. A timed-out multi-RPC sequence (an intent, ensure_bed) therefore
cannot keep landing its tail over a newer intent that fired meanwhile —
the "late cut overrides a retry" shape the regression pass deferred.

The daemon's own calls carry no generation and must never be refused."""
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

tmp = tempfile.mkdtemp()
os.environ["BROADCAST_ROOT"] = tmp   # before anything imports the modules

import daemon
import overlay_server

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


class FakeWS:
    """Answers every request with an immediate OK carrying its requestId."""

    def __init__(self):
        self.sent = []

    def send(self, o):
        self.sent.append(o)

    def recv(self):
        rid = self.sent[-1]["d"]["requestId"]
        return {"op": 7, "d": {"requestId": rid,
                               "requestStatus": {"result": True}},
                "responseData": {}}

    def close(self):
        pass


r = daemon.OBSRenderer(host="127.0.0.1", port=1)
r._shared = FakeWS()
REQS = ["One", "Two", "New", "Three", "Fresh", "Tail"]


def sent_types():
    return [s["d"]["requestType"] for s in r._shared.sent]


# 1. generations rise: gen 1 sends, then gen 2 sends
def with_gen(gen, req, out):
    def _go():
        r._tls.gen = gen
        try:
            r._call(req)
            out.append(("ok", req))
        except Exception as e:
            out.append((type(e).__name__, req))
    t = threading.Thread(target=_go)
    t.start()
    t.join(5)
    return out


out = []
with_gen(1, "One", out)
check(out == [("ok", "One")], "gen 1 sends")
out = []
with_gen(2, "Two", out)
check(out == [("ok", "Two")], "gen 2 sends after gen 1")

# 2. the stale tail is refused: gen 1 again cannot land after gen 2 sent
out = []
with_gen(1, "New", out)
check(out == [("OBSAppError", "New")], "stale generation refused")
check("New" not in sent_types(), "the refusal happened before the send")
check(r._shared is not None, "the connection stands (OBSAppError, not transport)")

# 3. the newer generation keeps working; same-gen sequences continue
out = []
with_gen(2, "Three", out)
check(out == [("ok", "Three")], "same generation continues its sequence")

# 4. no generation at all (the daemon's own shape) is never refused
def bare(req, out):
    def _go():
        try:
            r._call(req)
            out.append(("ok", req))
        except Exception as e:
            out.append((type(e).__name__, req))
    t = threading.Thread(target=_go)
    t.start()
    t.join(5)


out = []
bare("Fresh", out)
check(out == [("ok", "Fresh")], "ungenerated call (daemon shape) unaffected")

# 5. plane_call integration: a timed-out multi-RPC fn dies superseded
r2 = overlay_server.obs_req()
r2._shared = FakeWS()

landed = []


def slow_seq():
    try:
        r2._call("One")
        landed.append("one")
    except Exception as e:
        landed.append("one-failed:%r" % e)
        return
    time.sleep(1.0)   # outlives the 0.3s deadline
    try:
        r2._call("Tail")
        landed.append("tail-landed")
    except daemon.OBSAppError:
        landed.append("superseded")
    except Exception as e:
        landed.append("tail-other:%r" % e)


t0 = time.time()
try:
    overlay_server.plane_call(slow_seq, timeout=0.3)
    check(False, "slow sequence should have raised TimeoutError")
except TimeoutError:
    check(time.time() - t0 < 0.9, "handler freed at the deadline (%.2fs)"
          % (time.time() - t0))

# the newer call fires while the abandoned thread is still sleeping
overlay_server.plane_call(lambda: r2._call("New"), timeout=2.0)
deadline = time.time() + 3
while time.time() < deadline and len(landed) < 2:
    time.sleep(0.05)
check("one" in landed, "the first RPC of the sequence had already landed")
check("superseded" in landed, "the abandoned tail died superseded")
check("tail-landed" not in landed, "no stale RPC landed after the newer call")

# 6. a clean same-call sequence: both RPCs of ONE plane_call land
landed2 = []


def two_rpcs():
    r2._call("Three")
    landed2.append("a")
    r2._call("Tail")
    landed2.append("b")


overlay_server.plane_call(two_rpcs, timeout=4.0)
check(landed2 == ["a", "b"], "one call's own sequence is never refused")

print()
if fails:
    print("FAILURES: %d" % len(fails))
    for f in fails:
        print(" - %s" % f)
    sys.exit(1)
print("FAILURES: none")
