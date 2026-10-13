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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from daemon import evict_cache
except ImportError:  # running from anywhere odd; cap still enforced by daemon loop
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


def fetch_source(source, workdir):
    """Return a local raw file. URLs via yt-dlp; anything else must be a file."""
    if os.path.isfile(source):
        return source
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        raise RuntimeError("yt-dlp not installed and '%s' is not a local file." % source)
    out = os.path.join(workdir, "raw.%(ext)s")
    run(ytdlp, "-f",
        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "-o", out, "--no-playlist", source)
    cands = [os.path.join(workdir, f) for f in os.listdir(workdir)
             if f.startswith("raw.")]
    if not cands:
        raise RuntimeError("yt-dlp produced no file for %s" % source)
    return cands[0]


def normalise(raw, dest):
    run("ffmpeg", "-y", "-i", raw, *PROFILE, dest)


def verify(path, expect_min_s=5):
    p = run("ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", path)
    dur = float(p.stdout.strip())
    assert dur >= expect_min_s, "suspicious duration %ss" % dur
    return dur


def intake(source, title=None, queue=False):
    done = already_done(source)
    if done and os.path.exists(os.path.join(MEDIA, done)):
        print("already cached as %s; skipping (quota-safe)." % done)
        return done
    if shutil.disk_usage(MEDIA if os.path.exists(MEDIA) else "/tmp").free < 5 * 1024**3:
        raise RuntimeError("disk too full to intake; free space or raise the cap first.")
    evict_cache()  # make room before the burst, not after
    workdir = os.path.join(MEDIA, ".intake-tmp")
    os.makedirs(workdir, exist_ok=True)
    raw = fetch_source(source, workdir)
    name = (title or os.path.splitext(os.path.basename(source))[0])[:80]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "item"
    dest = os.path.join(MEDIA, "%s_%d.mp4" % (safe, int(time.time())))
    try:
        normalise(raw, dest)
        dur = verify(dest)
        digest = sha256(dest)
        con = sqlite3.connect(DB)
        con.execute("CREATE TABLE IF NOT EXISTS intake("
                    "source TEXT PRIMARY KEY, filename TEXT, duration REAL, "
                    "sha256 TEXT, intake_date TEXT, title TEXT)")
        con.execute("INSERT OR REPLACE INTO intake VALUES (?,?,?,?,?,?)",
                    (source, os.path.basename(dest), dur, digest,
                     time.strftime("%Y-%m-%d"), title or safe))
        con.commit()
        con.close()
        if queue:
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
    args = ap.parse_args()
    os.makedirs(MEDIA, exist_ok=True)
    try:
        intake(args.source, args.title, args.playlist)
    except Exception as e:
        print("INTAKE FAILED: %s" % e)
        sys.exit(1)
