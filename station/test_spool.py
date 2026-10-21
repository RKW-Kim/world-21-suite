"""Adversarial edge tests for the spool cache. Stdlib only.

Run from repo root:  python3 station/test_spool.py
No real youtube: yt-dlp and ffmpeg are faked. Covers state transitions,
kick re-entrancy + ready filter, _run blast-rate exits (success /
failure / exception / timeout), _cleanup age + cap + live-prefix
protection, _urls_ahead filtering. Touches nothing outside a temp dir.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spool

_ORIG_RUN = subprocess.run  # capture before any monkeypatch rebinds it

tmp = tempfile.mkdtemp()
spool.SPDIR = os.path.join(tmp, "spool")
os.makedirs(spool.SPDIR)
# The station's activity log is the operator's evidence trail: a test
# run must not write its alerts into the live database.
try:
    import daemon
    daemon.DB = os.path.join(tmp, "activity.db")
except Exception:
    pass

_C = {"stream_spool_keep_hours": 0.001,     # 3.6s = instantly aged
      "stream_spool_max_gb": 3.0,
      "stream_spool_ahead": 1.0}
spool._knob = lambda name, default: float(_C.get(name.lower(), default))

# The fixture files are byte-dummies with no audio streams; the real guard
# would purge every one of them as silent. Point the probe at /usr/bin/echo
# whose stdout is non-empty = "has audio", and cover the guard separately
# with a probe that outputs nothing.
spool.FFPROBE = "/usr/bin/echo"

fails = []


def check(name, cond):
    print("%-42s %s" % (name, "ok" if cond else "FAIL"))
    if not cond:
        fails.append(name)


def fpath(k, name):
    return spool.final(k + name)


BIG = b"x" * 2048
URL = "https://youtu.be/spoolTEST00"
K = spool._key(URL)
URL2 = "https://youtu.be/spoolTEST01"
K2 = spool._key(URL2)

# -- 1. state transitions + title mirror ---------------------------------
check("fresh miss", spool.state(URL) == "miss")
open(fpath(K, ".dl.mp4.part"), "w").write("part")
check("part file -> fetching", spool.state(URL) == "fetching")
os.remove(fpath(K, ".dl.mp4.part"))
open(fpath(K, ".mp4"), "wb").write(BIG)
spool._mirror_title(K, "T0")
info = spool.ready(URL)
check("complete -> ready", bool(info))
check("ready reads title mirror", info["title"] == "T0")
check("state -> ready", spool.state(URL) == "ready")
check("unknown url not ready",
      spool.ready("https://youtu.be/zzzNOKEY00") is None)
open(fpath(K, ".mp4"), "w").close()
check("zero-byte not blessed", spool.ready(URL) is None)
os.remove(fpath(K, ".mp4"))

# -- 2. kick: lock, re-entrancy, ready filter -----------------------------
spool._current = None
ran = threading.Event()
gate = threading.Event()


def _fake_run(url, title, alert):
    ran.set()
    gate.wait(10.0)
    spool._current = None


def _restore_run():
    src = open(os.path.join(os.path.dirname(spool.__file__),
                            "spool.py")).read()
    ns = {"__file__": os.path.join(os.path.dirname(spool.__file__),
                                   "spool.py")}
    exec(compile(src, "spool.py", "exec"), ns)
    ns["SPDIR"] = spool.SPDIR    # else the ns .final() hits the REAL cache
    ns["FFPROBE"] = spool.FFPROBE  # exec re-reads the const; keep the echo mock
    spool._run = ns["_run"]


spool._run = _fake_run
picks = spool.kick([{"youtube": URL2, "title": "T2"}], 0)
check("kick picks url", picks == [URL2])
check("kick sets _current", spool._current == URL2)
check("kick empty items noop", spool.kick([], 0) == [])
check("kick while job runs skips",
      spool.kick([{"youtube": URL2}], 0) == [])
check("kick skips dormant ahead",
      spool.kick([{"youtube": URL2, "status": "dormant"}], 1) == [])
check("kick stops at file item",
      spool.kick([{"file": "a.mp4", "title": "A"}, {"youtube": URL2}], 0) == [])
check("kick respects spool False",
      spool.kick([{"youtube": URL2, "spool": False}], 0) == [])
open(fpath(K2, ".mp4"), "wb").write(BIG)
check("kick skips ready item", spool.kick([{"youtube": URL2}], 0) == [])
os.remove(fpath(K2, ".mp4"))
gate.set()
drained = ran.wait(5.0)
for _ in range(50):
    if spool._current is None:
        break
    time.sleep(0.1)
check("job drained, _current cleared", drained and spool._current is None)
_restore_run()

# -- 3. _run blast-rate exits ---------------------------------------------
spool._current = None


def _fake_proc(argv, **kw):
    if argv[0] == spool.FFPROBE:               # audio-guard probe: audible
        return type("R", (), {"returncode": 0,
                              "stderr": "", "stdout": "aac\n"})()
    if "-movflags" in argv:                    # ffmpeg faststart remux
        open(argv[-1], "wb").write(BIG)
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()
    k = spool._key(argv[-1])                   # yt-dlp: writes the .dl
    open(spool.final(k + ".dl.mp4"), "wb").write(BIG)
    return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()


spool.subprocess.run = _fake_proc
LOG = []
spool._run(URL, "T3", lambda m, lvl="INFO": LOG.append((m, lvl)))
check("run-OK _current cleared", spool._current is None)
check("run-OK promotes ready", spool.ready(URL) is not None)
check("run-OK .dl kept for resume", os.path.isfile(fpath(K, ".dl.mp4")))
_mirror_t = spool.ready(URL).get("title")
check("run-OK alert names title",
      any(m.startswith("Spooled: T3") for m, _ in LOG)
      or _mirror_t == "T3")
os.remove(fpath(K, ".mp4"))


def _fail_proc(argv, **kw):
    return type("R", (), {"returncode": 1, "stderr": "", "stdout": ""})


spool.subprocess.run = _fail_proc
LOG = []
spool._run(URL, "T3", lambda m, lvl="INFO": LOG.append((m, lvl)))
check("run-FAIL cleared", spool._current is None)
check("run-FAIL warns", any(m.startswith("Spool failed") for m, _ in LOG))
check("run-FAIL nothing ready", spool.ready(URL) is None)


def _hang_proc(argv, **kw):
    raise subprocess.TimeoutExpired(cmd=argv[0], timeout=1)


spool.subprocess.run = _hang_proc
LOG = []
spool._run(URL, "T3", lambda m, lvl="INFO": LOG.append((m, lvl)))
check("run-TIMEOUT cleared", spool._current is None)
check("run-TIMEOUT warns", any("timed out" in m for m, _ in LOG))


def _boom_proc(argv, **kw):
    raise RuntimeError("disk lamp")


spool.subprocess.run = _boom_proc
LOG = []
spool._run(URL, "T3", lambda m, lvl="INFO": LOG.append((m, lvl)))
check("run-EXC cleared (finally)", spool._current is None)
check("run-EXC warns", any("Spool error" in m for m, _ in LOG))

# -- 4. _cleanup: age, cap, live-prefix protection ------------------------
_C["stream_spool_keep_hours"] = 48.0
aged = fpath("OLDKEY000000000000", ".mp4")
open(aged, "wb").write(b"z" * 512)
os.utime(aged, (time.time() - 100, time.time() - 100))
_C["stream_spool_keep_hours"] = 0.001       # age back on
spool._current = None
spool._cleanup()
check("aged file evicted", not os.path.exists(aged))

# real-scale cap: 3GB knob, 4GB sparse artifacts (no disk cost)
def _sparse(path, size):
    with open(path, "wb") as h:
        h.truncate(size)


spool._current = URL2
fbig = fpath("FBIGKEYkkkkkkkkk", ".mp4")
flive = fpath(K2, ".fs.mp4")
_sparse(fbig, 4 * 2 ** 30)
_sparse(flive, 4 * 2 ** 30)
spool._cleanup()
check("cap: giant non-live evicted", not os.path.exists(fbig))
check("cap: giant live protected", os.path.exists(flive))
spool._current = None
spool._cleanup()
check("cap: giant live evicted once idle",
      not os.path.exists(flive))

# -- 5. urls_ahead shape ----------------------------------------------------
check("urls_ahead returns pairs",
      spool._urls_ahead([{"youtube": "u9", "title": "X"}], 0)
      == [("u9", "X")])
check("urls_ahead link first wins",
      spool._urls_ahead([{"youtube": "u1"}, {"file": "a.mp4"}], 0)
      == [("u1", None)])
check("urls_ahead file first stops scan",
      spool._urls_ahead([{"file": "a.mp4"}, {"youtube": "u1"}], 0) == [])
check("urls_ahead spool False stops",
      spool._urls_ahead([{"youtube": "u1", "spool": False}], 0) == [])
check("urls_ahead dormant skipped",
      spool._urls_ahead([{"youtube": "u1", "status": "dormant"},
                         {"youtube": "u2"}], 0) == [("u2", None)])

# -- 8. audio guard (real subprocess back: real probe binaries run) -------
spool.subprocess.run = _ORIG_RUN
ff = os.path.join(tmp, "fakeffmpeg.sh")
with open(ff, "w") as f:
    # argv: FFMPEG -hide_banner -v error -y -i RAW <codec args…>
    #       -movflags +faststart -f mp4 TMP   => cp "${6}" "$last"
    # (loudnorm added codec args, so TMP is no longer fixed at $13 — the
    # fake copies RAW ($6) to whatever the final argument is)
    f.write('#!/bin/sh\neval "last=\\"\\${$#}\\""\ncp "${6}" "$last"\n')
ff_ok = subprocess.run(["chmod", "+x", ff]).returncode == 0
check("fake ffmpeg executable", ff_ok)
RAW2 = fpath(K2, ".dl.mp4")
open(RAW2, "wb").write(BIG)
spool.FFMPEG = ff
spool.FFPROBE = "/bin/true"  # stdout empty = silent file
spool._faststart(K2)
check("silent faststart purged",
      not os.path.isfile(fpath(K2, ".mp4")) and spool.ready(URL2) is None)
check("silent marker set",
      os.path.isfile(fpath(K2, spool.NOAUDIO)))
check("silent raw freed", not os.path.isfile(RAW2))
# ready() stays a miss with the marker on disk: the live pipe (with sound)
# keeps the item playable and _run refuses a re-download while it stands.
check("silent marker keeps miss", spool.state(URL2) == "miss")
# The marker early-return lives in _run's first lines: invoke it and check
# that it touches nothing in the cache dir.
before = set(os.listdir(spool.SPDIR))
spool._run(URL2, None, lambda m, lvl="INFO": None)
check("marker early-return holds",
      set(os.listdir(spool.SPDIR)) == before)
# Recovery path: marker gone + fresh raw (simulating the fixed selector's
# re-download) -> faststart blesses a file the probe reports as audible.
spool.FFPROBE = "/usr/bin/echo"
open(RAW2, "wb").write(BIG)
os.remove(fpath(K2, spool.NOAUDIO))
spool._faststart(K2)
check("audible file blesses",
      bool(spool.ready(URL2)) and not os.path.isfile(fpath(K2, spool.NOAUDIO)))

print("FAILURES: %s" % (fails or "none"))
sys.exit(1 if fails else 0)
