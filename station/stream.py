"""YouTube-URL streaming decks: link in, live picture out, zero disk.

Topology per deck (final; every alternative was tried live):
  yt-dlp --dump-json (resolve: metadata + duration + thumbnail)
  yt-dlp -g (two HLS URLs: video <=720p + best audio, fresh per spawn)
  ffmpeg -i <hlsV> -i <hlsA> -c copy -f flv rtmp://127.0.0.1:1935/<path>
  MediaMTX path -> OBS STREAM_A/B input (ffmpeg_source, rtmp read,
  restart_on_activate: a deck connects only once its feed publishes).

Why this shape (documented so nobody "simplifies" it back broken):
- -g https/DASH URLs 403 outside yt-dlp (UA-gated). HLS URLs play.
- yt-dlp -o - merge to stdout is download-then-emit (blocking), not a
  live pipe. Two HLS inputs merged by ffmpeg stream progressively.
- RTSP output rejects YouTube AAC (no global headers, bsf can't fix).
  FLV/RTMP muxer generates the headers; copy still, no transcode.
- Single ffmpeg per deck (~15MB RAM, ~5% CPU remux). No mpv (headless
  has no window), no Studio Player (files only), no ASS (can't fetch).

Wall-clock advance: resolve() returns duration upfront, so the daemon
schedules transitions instead of detecting ends. Livestreams
(duration None) play until the operator advances or the feed dies.
HLS URLs expire in hours: always resolve fresh inside spawn(), and the
watchdog re-resolves on respawn. Prefetch window (30s) covers resolve
(~5-10s) + HLS startup (~5-15s).
"""
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request

log = logging.getLogger("stream")

YTDLP = "/usr/bin/yt-dlp"
FFMPEG = "/usr/bin/ffmpeg"
MTX_RTMP = "rtmp://127.0.0.1:1935"
MTX_API = "http://127.0.0.1:9997"
V_FMT = "bv*[vcodec^=avc1][height<=720][protocol*=m3u8]/bv*[vcodec^=avc1][protocol*=m3u8]"
A_FMT = "ba[acodec^=mp4a][protocol*=m3u8]/ba[protocol*=m3u8]"
RESOLVE_TIMEOUT = 45     # three serial probes: 3x this is the worst case

# Why the last resolve failed, and whether it is PERMANENT. A video that
# is gone will never come back; a timeout or a bot check will. The
# station used to treat both as "unplayable" and SKIP the item -- so a
# slow YouTube (30-60s per metadata call from a datacentre IP) made the
# station eat its own playlist, one item every few seconds.
LAST_ERROR = {"reason": "", "permanent": False, "at": 0.0}

_PERMANENT_MARKERS = (
    "video unavailable", "private video", "has been removed",
    "is not available", "members-only", "account associated with this video",
    "removed by the uploader", "video is no longer available",
    "copyright", "not available in your country",
)


def _classify(err, timed_out=False):
    low = (err or "").lower()
    permanent = any(m in low for m in _PERMANENT_MARKERS)
    LAST_ERROR.update({"reason": (err or ("timeout" if timed_out else ""))[:200],
                       "permanent": permanent, "at": time.time()})
    return permanent


def resolve_failure_is_permanent(since=0.0):
    """True when the last resolve failed for good (the video is gone).
    A timeout, a bot check or a network error is TRANSIENT: the item
    must be held, not consumed."""
    if not LAST_ERROR.get("at"):
        return False
    if since and LAST_ERROR["at"] < since:
        return False      # an older failure says nothing about this one
    return bool(LAST_ERROR.get("permanent"))
READY_TIMEOUT = 45

# YouTube serves some videos to anonymous IPs only after a bot check
# ("Sign in to confirm you're not a bot", seen live on a lab IP after
# routine resolving). The remedy is browser cookies. Accepts:
#   /path/to/cookies.txt      (canonical; works headless everywhere)
#   browser:chromium          (lab convenience; uses the desktop profile)
# Unset = anonymous. Configure via the daemon unit's environment.
_COOKIES = os.environ.get("YTDLP_COOKIES", "")
_COOKIES_WARNED = False


def _ytdlp_cmd(extra):
    global _COOKIES_WARNED
    base = [YTDLP, "--no-playlist"]
    c = _COOKIES
    if c:
        if c.startswith("browser:"):
            base += ["--cookies-from-browser", c.split(":", 1)[1]]
        elif os.path.isfile(c):
            base += ["--cookies", c]
            # Healthy again: re-arm the warn. The flag used to latch for
            # the process lifetime, so after one fix a SECOND cookies
            # disappearance (days later) resolved anonymously in silence.
            if _COOKIES_WARNED:
                _COOKIES_WARNED = False
        elif not _COOKIES_WARNED:
            # A configured-but-missing cookies file silently downgraded to
            # anonymous -- and the operator could not tell why the bot-wall
            # came back. Say it once, loudly, then keep going.
            _COOKIES_WARNED = True
            sys.stderr.write("stream: YTDLP_COOKIES=%r does not exist -- "
                             "resolving anonymously (bot-wall risk)\n" % c)
    return base + extra


def _g(url, fmt):
    try:
        p = subprocess.run(
            _ytdlp_cmd(["-f", fmt, "-g", "--no-warnings", url]),
            capture_output=True, text=True, timeout=RESOLVE_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if p.returncode != 0:
        return None
    for line in (p.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("http"):
            return line
    return None


def resolve(url):
    """Metadata + playable HLS URLs. Dict or None (unplayable)."""
    try:
        p = subprocess.run(
            _ytdlp_cmd(["--dump-json", "--no-warnings", url]),
            capture_output=True, text=True, timeout=RESOLVE_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        _classify("timeout after %ss" % RESOLVE_TIMEOUT, timed_out=True)
        log.warning("resolve %s: timed out after %ss (TRANSIENT)",
                    url, RESOLVE_TIMEOUT)
        return None
    except OSError as e:
        _classify(str(e))
        log.warning("resolve %s: %s", url, e)
        return None
    if p.returncode != 0:
        _classify((p.stderr or "")[-400:])
        log.warning("resolve %s failed: %s", url, (p.stderr or "")[-200:])
        return None
    try:
        j = json.loads(p.stdout)
    except ValueError:
        return None
    live = bool(j.get("is_live"))
    desc = j.get("description") or ""
    return {"id": j.get("id"), "title": j.get("title") or url,
            "duration": None if live else j.get("duration"),
            "thumbnail": j.get("thumbnail"), "live": live,
            # The description is what the dock's preview panel shows: the
            # operator confirms a video by reading it, not by its title.
            "description": desc[:4000],
            "upload_date": j.get("upload_date") or j.get("release_date") or "",
            "channel": j.get("channel") or j.get("uploader") or "",
            "hls_at": time.time(),
            "hls_v": _g(url, V_FMT), "hls_a": _g(url, A_FMT)}


def spawn(url, path, meta=None):
    """Start the feed ffmpeg publishing to a MediaMTX path. Returns proc.

    HLS urls expire (hours). A meta older than 30 minutes is re-resolved
    here, so a respawn does not hand ffmpeg the same dead urls."""
    if meta and meta.get("hls_at", 0) < time.time() - 1800:
        fresh = resolve(url)
        if fresh:
            meta = fresh
    meta = meta or resolve(url)
    if not meta or not meta.get("hls_v") or not meta.get("hls_a"):
        log.warning("spawn %s: unresolvable", url)
        return None
    try:
        # Truncate per spawn: /tmp is a tmpfs (RAM) and the log grew
        # forever, one stats line per 0.5s of stream.
        err = open(os.environ.get("FFERR_PATH", "/tmp/feed-%s.err" % path), "wb")
        ff = subprocess.Popen(
            [FFMPEG, "-hide_banner", "-loglevel", "warning",
             # 15s socket timeout: without it a dead upstream keeps the
             # process alive (and the frame frozen) forever.
             "-rw_timeout", "15000000", "-reconnect", "1", "-reconnect_streamed", "1",
             "-re", "-i", meta["hls_v"], "-re", "-i", meta["hls_a"],
             "-c", "copy", "-f", "flv", "%s/%s" % (MTX_RTMP, path)],
            stdout=subprocess.DEVNULL, stderr=err)
    except OSError as e:
        log.warning("spawn %s: %s", path, e)
        return None
    return ff


def alive(proc):
    """Feed process still running."""
    return proc is not None and proc.poll() is None


def stop(proc):
    """Kill a feed, SIGTERM then SIGKILL."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=5)   # reap: a killed child is a zombie until waited on
        except (OSError, subprocess.TimeoutExpired):
            pass
    except OSError:
        pass


def path_ready(path):
    """MediaMTX has a live publisher on this path."""
    try:
        req = urllib.request.Request("%s/v3/paths/get/%s" % (MTX_API, path))
        with urllib.request.urlopen(req, timeout=5) as r:
            j = json.load(r)
    except Exception:
        return False
    return bool(j.get("source"))
