#!/usr/bin/env python3
"""Both HTTP surfaces must ANSWER a malformed request, never drop it.

Found by fuzzing the operator's two HTTP surfaces:
- POST /api/save with {"playlist": "not-a-dict"} raised AttributeError
  inside the handler, which only caught (ValueError, KeyError): the
  connection died with no answer and the dock showed a network error
  instead of what was wrong with the request.
- POST /obs with {"type": 123} raised AttributeError (int has no
  isalpha) the same way.

A console that drops the connection on bad input is worse than one that
answers: the operator cannot tell a bad request from a dead station.

Offline, stdlib only. It talks to the LIVE panel and overlay (read-only
paths and requests that are refused before any write).
"""
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def call(base, path, method="POST", body=None, headers=None, timeout=15):
    """(status, body). A dropped connection is status None."""
    req = urllib.request.Request(base + path, data=body,
                                 headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:
        return None, str(e).encode()[:120]


def main():
    jsonh = {"Content-Type": "application/json"}

    panel = "http://127.0.0.1:8220"
    overlay = "http://127.0.0.1:7070"

    # The station must be running for this one. On a fresh clone (no
    # station) it skips rather than failing: the suite has to be green
    # everywhere, not only on the live box.
    for base, name in ((panel, "panel"), (overlay, "overlay")):
        try:
            urllib.request.urlopen(base + "/api/ping" if name == "panel"
                                   else base + "/obs/meters", timeout=5).read()
        except Exception as e:
            print("SKIP: the %s is not answering (%s)" % (name, e))
            print("=== FAILURES: 0 ===")
            return 0

    # ---- the panel: a malformed playlist is refused, not fatal --------
    for label, payload in [
            ("a string playlist", {"playlist": "not-a-dict"}),
            ("a number playlist", {"playlist": 42}),
            ("a list playlist", {"playlist": [1, 2]}),
            ("no playlist key", {"knobs": {}}),
            ("items that are not a list", {"playlist": {"items": "nope"}})]:
        st, body = call(panel, "/api/save", body=json.dumps(payload).encode(),
                        headers=jsonh)
        check(st is not None and st == 400,
              "panel: %s -> 400 (got %s)" % (label, st))
        check(st is None or b"ok" in body.lower(),
              "panel: %s -> an answer, not a dropped connection" % label)

    st, _ = call(panel, "/api/state", body=json.dumps({"state": "nope"}).encode(),
                 headers=jsonh)
    check(st == 400, "panel: a string state -> 400 (got %s)" % st)
    st, _ = call(panel, "/api/state", body=json.dumps({"state": [1]}).encode(),
                 headers=jsonh)
    check(st == 400, "panel: a list state -> 400 (got %s)" % st)

    # ---- the panel: the state's VALUES are checked, not just the keys -
    # A non-integer index ("abc") was accepted and written to the live
    # state; the daemon coerced it to 0 and the station would have
    # restarted the show from the top.
    for label, payload in [("a string index", {"index": "abc"}),
                            ("a negative index", {"index": -3}),
                            ("a boolean index", {"index": True}),
                            ("a string flag", {"fallback_air": "yes"})]:
        st, _ = call(panel, "/api/state", body=json.dumps({"state": payload}).encode(),
                     headers=jsonh)
        check(st == 400, "panel: %s -> 400 (got %s)" % (label, st))

    # ---- the overlay: a malformed OBS call is refused, not fatal ------
    for label, payload in [
            ("a number type", {"type": 123}),
            ("a null type", {"type": None}),
            ("a list type", {"type": ["a"]}),
            ("an empty type", {"type": ""}),
            ("data that is not an object", {"type": "GetVersion",
                                            "data": "notadict"})]:
        st, _ = call(overlay, "/obs", body=json.dumps(payload).encode(),
                     headers=jsonh)
        check(st is not None and st in (400, 502, 504),
              "overlay: %s -> an answered 4xx/5xx (got %s)" % (label, st))

    # ---- both: a broken body is refused, not fatal --------------------
    for base, name in ((panel, "panel"), (overlay, "overlay")):
        st, _ = call(base, "/obs" if name == "overlay" else "/api/save",
                     body=b"{not json", headers=jsonh)
        check(st is not None and st == 400,
              "%s: broken JSON -> 400 (got %s)" % (name, st))

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
