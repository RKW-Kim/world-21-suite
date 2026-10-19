"""Spool cache for link items: download the NEXT YouTube item while the
current one plays, then cut to the complete local copy instead of a
live HLS pipe.

Contract (user decision 2026-10-20): a finished spool plays from 0:00
with no upstream deps; a partial one (98%-style cases included) is
never half-played — the item streams raw exactly as before and the
partial stays on disk to resume next cycle.

Disk here, not tmpfs: this box runs ~600MB free RAM and /tmp is tmpfs;
a 2h 720p item is 1.4-2.7GB so RAM spooling would starve OBS/ffmpeg.
VPS disk to googlevideo runs 50-100 MB/s: a 2h item lands in <1min.

Files: <SPDIR>/<key>.mp4 = complete; <key>.mp4.part = in-flight or
resumable. key = sha1(url)[:20]; <key>.title = cached title for the
panel/dock so it shows a name without re-resolving.
"""
import hashlib
import json
import os
import subprocess
import threading
import time

import stream as ytstream

ROOT = os.path.dirname(os.path.abspath(__file__))
SPDIR = os.path.join(ROOT, "..", "spool")
JOB_TIMEOUT = 1800
FFMPEG = ytstream.FFMPEG

_state_lock = threading.Lock()
_current = None


def _knob(name, default):
    try:
        with open(os.path.join(ROOT, "..", "knobs.json")) as f:
            return float(json.load(f).get(name) or default)
    except Exception:
        return default


def _key(url):
    return hashlib.sha1(url.encode()).hexdigest()[:20]


def ready(url):
    p = final(_key(url) + ".mp4")
    if not os.path.isfile(p) or os.path.getsize(p) == 0:
        return None
    info = {"path": p, "size": os.path.getsize(p),
            "mtime": os.path.getmtime(p), "title": None}
    try:
        with open(p[:-4] + ".title") as f:
            info["title"] = (json.load(f) or {}).get("title")
    except Exception:
        pass
    return info


def state(url):
    if ready(url):
        return "ready"
    if _current == url or os.path.isfile(final(_key(url) + ".mp4.part")):
        return "fetching"
    return "miss"


def final(name):
    return os.path.join(SPDIR, name)


def _cleanup():
    keep = _knob("STREAM_SPOOL_KEEP_HOURS", 48)
    cap = _knob("STREAM_SPOOL_MAX_GB", 3.0) * (1024 ** 3)
    files = []
    try:
        os.makedirs(SPDIR, exist_ok=True)
        for name in sorted(os.listdir(SPDIR)):
            p = os.path.join(SPDIR, name)
            try:
                files.append([os.path.getmtime(p), os.path.getsize(p), p])
            except OSError:
                pass
    except OSError:
        return
    used = sum(f[1] for f in files)
    now = time.time()
    for f in list(files):
        if f[0] < now - keep * 3600:
            _unlink(f); used -= f[1]; files.remove(f)
    files.sort(key=lambda f: f[0])
    for f in list(files):
        if used <= cap or used - f[1] < cap * 0.8:
            break
        if _current and f[2].endswith(".part") and \
                _key(_current) in os.path.basename(f[2]):
            continue
        _unlink(f); used -= f[1]; files.remove(f)


def _unlink(f):
    try:
        os.unlink(f[2])
    except OSError:
        pass


def _urls_ahead(items, start):
    n = len(items)
    for off in range(n):
        item = items[(start + off) % n]
        if item.get("status") == "dormant":
            continue
        if not item.get("youtube"):
            return []
        if item.get("spool") is False:
            return []
        ahead = _knob("STREAM_SPOOL_AHEAD", 1)
        if ahead < 1:
            return []
        return [item["youtube"]]
    return []


def kick(items, start, alert=lambda m, lvl="INFO": None):
    global _current
    if not items:
        return []
    picks = []
    for url in _urls_ahead(items, start):
        if ready(url) or url == _current:
            continue
        with _state_lock:
            if _current is None:
                _current = url
                threading.Thread(target=_run, args=(url, alert),
                                 daemon=True).start()
                picks.append(url)
            break
    _cleanup()
    return picks


def _run(url, alert):
    global _current
    k = _key(url)
    out = final(k + ".mp4")
    fmt = ytstream.V_FMT + "+ba/" + ytstream.V_FMT
    argv = ytstream._ytdlp_cmd([
        "-f", fmt, "--no-playlist", "--no-warnings",
        "--merge-output-format", "mp4",
        "--max-filesize", "%dM" % (_knob("STREAM_SPOOL_MAX_GB", 3.0) * 1024),
        "--retries", "3", "--newline",
        "-o", final(k + ".%(ext)s"), url])
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=JOB_TIMEOUT)
        err = (p.stderr or "").strip().splitlines()[-1:]
    except subprocess.TimeoutExpired:
        alert("Spool timed out: %s" % (url.rsplit("v=", 1)[-1], ), "WARN")
        _current = None
        return
    except OSError as e:
        alert("Spool failed: %s" % e, "WARN")
        _current = None
        return
    _current = None
    info = ready(url)
    if info:
        _faststart(info["path"])
        info = ready(url)
        alert("Spooled: %s (%.1fMB)" % (info.get("title") or url,
                                        info["size"] / 1e6), "INFO")
    else:
        alert("Spool failed: v%s %s" % (url.rsplit("v=", 1)[-1][:20],
                                        (err[0] if err else "")[-140:]), "WARN")


def _faststart(path):
    """yt-dlp's HLS fixup leaves the MP4 moov at the tail; OBS stalls at
    t=0 on tail-moov files (observed live on a 150MB item 2026-10-20).
    Remux with +faststart; copy-only, so a failure just drops it."""
    tmp = path + ".fs.mp4"
    try:
        p = subprocess.run(
            [FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", path,
             "-c", "copy", "-movflags", "+faststart", "-f", "mp4", tmp],
            capture_output=True, text=True, timeout=600)
        if p.returncode == 0 and os.path.getsize(tmp) > 0:
            os.replace(tmp, path)
    except subprocess.TimeoutExpired:
        pass
    except OSError:
        pass
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
