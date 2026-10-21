#!/usr/bin/env python3
"""Intake worker: link -> fetch once -> normalise -> verify -> publish -> queue.

Each item is downloaded exactly once and cached until evicted; the loop plays
from cache, never from the link. Accepts a URL (needs yt-dlp) or a local file.

  python3 station/intake.py <url-or-file> [--title T] [--playlist]

Broadcast profile: H.264 CFR 30fps 1920x1080 padded, AAC 128k 48kHz,
loudnorm I=-16, +faststart. Env: BROADCAST_ROOT (default ./broadcast).
"""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from daemon import evict_cache, CACHE_CAP
except ImportError:  # running from anywhere odd; cap still enforced by daemon loop
    CACHE_CAP = 50 * 1024**3
    evict_cache = lambda cap=None, pinned=frozenset(): 0

ROOT = os.environ.get("BROADCAST_ROOT", os.path.join(os.getcwd(), "broadcast"))
MEDIA = os.path.join(ROOT, "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
DB = os.path.join(MEDIA, "intake.db")

PROFILE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30",
           "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                  "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
           "-movflags", "+faststart"]


def run(*cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("%s\n%s" % (" ".join(cmd[:3]), p.stderr[-2000:]))
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def already_done(source):
    if not os.path.exists(DB):
        return None
    con = sqlite3.connect(DB)
    row = con.execute("SELECT filename FROM intake WHERE source=?", (source,)).fetchone()
    con.close()
    return row[0] if row else None


# Warned-once flag for a configured-but-missing YTDLP_COOKIES file (the
# fetch would otherwise silently run anonymous; see fetch_source).
_warned_cookies = {"warned": False}


def fetch_source(source, workdir):
    """Return a local raw file. URLs via yt-dlp; anything else must be a file."""
    if os.path.isfile(source):
        return source
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        raise RuntimeError("yt-dlp not installed and '%s' is not a local file." % source)
    out = os.path.join(workdir, "raw.%(ext)s")
    cmd = [ytdlp, "-f",
           "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
           "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
           "-o", out, "--no-playlist"]
    # Match stream.py: YTDLP_COOKIES may be a cookies.txt path OR
    # "browser:<profile>" for the live desktop profile (cookies.txt goes
    # stale the moment Chrome rotates its v11 keys; the profile read
    # doesn't). YTDLP_BROWSER wins over YTDLP_COOKIES if set.
    cookies = os.environ.get("YTDLP_COOKIES", "")
    browser = os.environ.get("YTDLP_BROWSER",
                             cookies[8:] if cookies.startswith("browser:") else "")
    if browser:
        cmd += ["--cookies-from-browser", browser]
    elif os.path.isfile(cookies):
        cmd += ["--cookies", cookies]
    elif cookies and not _warned_cookies.get("warned"):
        # Same silent-fallback lesson as stream.py: a configured cookies
        # path that is missing downgrades to anonymous and the operator
        # cannot tell why the bot-wall returned. Say it once.
        _warned_cookies["warned"] = True
        sys.stderr.write("intake: YTDLP_COOKIES=%r does not exist -- "
                         "fetching anonymously (bot-wall risk)\n" % cookies)
    cmd.append(source)
    run(*cmd)
    cands = [os.path.join(workdir, f) for f in os.listdir(workdir)
             if f.startswith("raw.")]
    if not cands:
        raise RuntimeError("yt-dlp produced no file for %s" % source)
    return cands[0]


def normalise(raw, dest):
    run("ffmpeg", "-y", "-i", raw, *PROFILE, dest)


def _sweep_workdirs():
    """Remove .intake-tmp-<pid> dirs whose intake is gone.

    A SIGKILLed intake used to leave its raw downloads behind FOREVER (the
    workdir is eviction-exempt by name), and after weeks of uptime a pid
    could be REUSED: a fresh job's workdir then adopted the stale raws of
    a dead one. A workdir dies with its pid -- or once it is old enough
    that no intake can still be running, because the pid may belong to
    someone else by now. (os.kill(pid,0) on a live foreign pid raises
    PermissionError, an OSError: treated as dead, which is correct -- this
    MEDIA tree belongs to one user.)"""
    now = time.time()
    try:
        names = os.listdir(MEDIA)
    except OSError:
        return
    for n in names:
        if not n.startswith(".intake-tmp-"):
            continue
        d = os.path.join(MEDIA, n)
        pid = n[len(".intake-tmp-"):]
        alive = False
        if pid.isdigit():
            try:
                os.kill(int(pid), 0)
                alive = True
            except OSError:
                alive = False
        if not alive or now - os.path.getmtime(d) > 86400:
            shutil.rmtree(d, ignore_errors=True)


def verify(path, expect_min_s=5):
    p = run("ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", path)
    dur = float(p.stdout.strip())
    assert dur >= expect_min_s, "suspicious duration %ss" % dur
    return dur


def _pinned_files():
    """What the loop is playing, about to play, or the operator pinned.
    Intake must never evict these — evicting the on-air file mid-play is
    the one unrecoverable cache failure (everything else retries)."""
    try:
        items = json.load(open(PLAYLIST)).get("items", [])
    except (OSError, ValueError):
        return frozenset()
    try:
        idx = json.load(open(os.path.join(ROOT, "state.json"))).get("index", 0)
    except (OSError, ValueError):
        idx = 0
    pinned, n = set(), len(items)
    if n:
        for o in (-1, 0, 1):
            f = items[(idx + o) % n].get("file")
            if f:
                pinned.add(f)
    pinned |= {i.get("file") for i in items if i.get("pinned") and i.get("file")}
    return frozenset(pinned)


def _estimate_size(source):
    """Incoming bytes if knowable without downloading: local size, else HTTP
    Content-Length. Anything else (yt-dlp URLs, streams) is None = proceed
    on faith, verify after."""
    if os.path.isfile(source):
        return os.path.getsize(source)
    if not source.startswith(("http://", "https://")):
        return None
    try:
        req = urllib.request.Request(source, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            n = r.headers.get("Content-Length")
            return int(n) if n else None
    except Exception:
        return None


def intake(source, title=None, queue=False, target=None):
    done = already_done(source)
    if done and os.path.exists(os.path.join(MEDIA, done)):
        if target:
            # --as is a contract: the exact name materializes, even if the
            # bytes already lived here under another name. Hardlink: instant,
            # no extra bytes, same filesystem guaranteed (MEDIA dir).
            want = os.path.join(MEDIA, "".join(
                c if c.isalnum() or c in "-_." else "_" for c in target).strip("_.") or "item.mp4")
            have = os.path.join(MEDIA, done)
            if want != have and not os.path.exists(want):
                try:
                    os.link(have, want)
                except OSError:
                    shutil.copyfile(have, want)
            print("already cached as %s." % os.path.basename(want))
            return os.path.basename(want)
        print("already cached as %s; skipping (quota-safe)." % done)
        return done
    if shutil.disk_usage(MEDIA if os.path.exists(MEDIA) else "/tmp").free < int(
            os.environ.get("INTAKE_MIN_FREE_BYTES", 5 * 1024**3)):
        raise RuntimeError("disk too full to intake; free space or raise the cap first.")
    pinned = _pinned_files()
    est = _estimate_size(source)
    if est is not None:
        try:
            sizes = {f: os.path.getsize(os.path.join(MEDIA, f)) for f in os.listdir(MEDIA)
                     if f.endswith(".mp4")}
        except OSError:
            sizes = {}
        room = CACHE_CAP - sum(sizes.get(f, 0) for f in pinned)
        if est > room:
            raise RuntimeError(
                "cache cannot fit ~%d bytes: %d cap, %d pinned (playing/next/operator). "
                "Unpin, raise the cap, or pick a smaller file. Nothing downloaded."
                % (est, CACHE_CAP, sum(sizes.get(f, 0) for f in pinned)))
    evict_cache(pinned=pinned)  # make room before the burst, not after
    _sweep_workdirs()
    # Unique workdir per invocation: daemon prefetch + overlay /music add
    # + CLI intakes can run CONCURRENTLY; a shared .intake-tmp collided
    # raw.* files across jobs (one job adopted the other's half-download).
    workdir = os.path.join(MEDIA, ".intake-tmp-%s" % os.getpid())
    os.makedirs(workdir, exist_ok=True)
    raw = fetch_source(source, workdir)
    name = (title or os.path.splitext(os.path.basename(source))[0])[:80]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "item"
    if target:
        # Prefetch names its target deterministically (see daemon) so the
        # caller knows exactly which file to expect. Same source = same bytes;
        # already_done() short-circuits repeats before we ever get here.
        dest = os.path.join(MEDIA, "".join(
            c if c.isalnum() or c in "-_." else "_" for c in target).strip("_.") or "item.mp4")
    else:
        dest = os.path.join(MEDIA, "%s_%d.mp4" % (safe, int(time.time())))
    try:
        # Normalise INTO the workdir, then publish with os.replace. The old
        # form ran ffmpeg straight at the final name: a SIGKILLed intake
        # left a partial, broadcast-ELIGIBLE file in MEDIA (right name, no
        # playlist row, invisible to eviction) while its raw stayed in an
        # eviction-exempt workdir. verify+hash the tmp, then one atomic
        # rename: MEDIA only ever holds complete files.
        out = os.path.join(workdir, "out.mp4")
        normalise(raw, out)
        dur = verify(out)
        digest = sha256(out)
        con = sqlite3.connect(DB)
        con.execute("CREATE TABLE IF NOT EXISTS intake("
                    "source TEXT PRIMARY KEY, filename TEXT, duration REAL, "
                    "sha256 TEXT, intake_date TEXT, title TEXT)")
        con.execute("INSERT OR REPLACE INTO intake VALUES (?,?,?,?,?,?)",
                    (source, os.path.basename(dest), dur, digest,
                     time.strftime("%Y-%m-%d"), title or safe))
        con.commit()
        con.close()
        os.replace(out, dest)   # atomic: the cache never sees a partial
        # Estimates undershoot (normalised output can outgrow its input);
        # settle the cap now that the real bytes are known.
        evict_cache(pinned=pinned)
        if queue:
            # Same flock the daemon/overlay use for playlist writes
            # (daemon.pl_lock semantics): append must not clobber a
            # concurrent shuffle or edit.
            fd = os.open(os.path.join(ROOT, ".station.lock"),
                         os.O_CREAT | os.O_RDWR, 0o600)
            try:
                import fcntl as _fcntl
                _fcntl.flock(fd, _fcntl.LOCK_EX)
                try:
                    with open(PLAYLIST) as f:
                        pl = json.load(f)
                except (OSError, ValueError):
                    pl = {"shuffle_on_complete": True, "items": []}
                pl["items"].append({"file": os.path.basename(dest),
                                    "title": title or safe, "duration": int(dur)})
                tmp = PLAYLIST + ".new"
                with open(tmp, "w") as f:
                    json.dump(pl, f, indent=2)
                os.replace(tmp, PLAYLIST)  # atomic; loop picks it up at next cut
            finally:
                _fcntl.flock(fd, _fcntl.LOCK_UN)
                os.close(fd)
        print("OK %s (%.0fs, sha256 %.12s)" % (os.path.basename(dest), dur, digest))
        return os.path.basename(dest)
    except Exception:
        # A failed verify must not litter the cache: an unnamed partial would
        # sit below the eviction radar (no playlist entry) yet eat the cap.
        if os.path.exists(dest):
            os.remove(dest)
        raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch once, normalise, publish to cache.")
    ap.add_argument("source", help="URL (needs yt-dlp) or local file path")
    ap.add_argument("--title", default=None)
    ap.add_argument("--playlist", action="store_true", help="append to playlist.json")
    ap.add_argument("--as", dest="target", default=None,
                    help="exact target basename (prefetch names its own output)")
    args = ap.parse_args()
    os.makedirs(MEDIA, exist_ok=True)
    try:
        intake(args.source, args.title, args.playlist, args.target)
    except Exception as e:
        print("INTAKE FAILED: %s" % e)
        sys.exit(1)
