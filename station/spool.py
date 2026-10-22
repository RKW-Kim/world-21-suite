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

Files: <SPDIR>/<key>.mp4 = COMPLETE (faststarted, OBS-safe — the only
name ready() will ever bless); <key>.dl.mp4(+.part) = raw yt-dlp
artifact (tail-moov!) and its resumable partial; <key>.fs.mp4 =
faststart remux temp. key = sha1(url)[:20]; <key>.title = cached title
for the panel/dock so it shows a name without re-resolving.

The .dl -> .mp4 split exists because OBS stalls at t=0 on tail-moov
files (150MB bunny, verified live 2026-10-20): ready() must not bless a
download that is complete-but-unfaststarted, or a mid-cut into it can
hang the deck until the watchdog fires. ready() sees .mp4 only AFTER
ffmpeg faststart finished and os.replace() swung it into place.
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
FFPROBE = "/usr/bin/ffprobe"
NOAUDIO = ".noaudio"  # per-key marker: selector produced a silent file; skip
LOUDNORM = os.environ.get("SPOOL_LOUDNORM", "1") != "0" and \
    "I=-16:TP=-1.5:LRA=11"  # string test: env "0" opts down to plain copy

_state_lock = threading.Lock()
_current = None


def _knob(name, default):
    try:
        with open(os.path.join(ROOT, "..", "broadcast", "knobs.json")) as f:
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


_state_cache = {}        # url -> state, invalidated when the entry set moves
_state_key = None        # (sorted spool names, current job) the cache was built on


def state(url):
    """ready / fetching / miss. Cached: the panel asks for 200 of these
    per playlist render, and each one used to be two stat() calls.

    The invalidation key is the spool directory's ENTRY SET plus the
    spooler's current job — every state transition is made of exactly
    those. An earlier draft keyed on the directory's mtime; filesystems
    with coarse mtime granularity never changed it (verified: this box's
    overlayfs), so a finished download served as 'fetching' for a full
    second and test_spool's state->ready caught it."""
    global _state_cache, _state_key
    try:
        names = tuple(sorted(os.listdir(SPDIR)))
    except OSError:
        names = ()
    key = (names, _current)
    if key != _state_key:
        _state_cache = {}
        _state_key = key
    hit = _state_cache.get(url)
    if hit is not None:
        return hit
    res = _state_uncached(url)
    _state_cache[url] = res
    return res


def _state_uncached(url):
    if ready(url):
        return "ready"
    if _current == url:
        return "fetching"
    # yt-dlp writes per-format partials (<key>.dl.f137.mp4.part), so the
    # old "<key>.dl.mp4.part" probe never matched a real download.
    key = _key(url)
    try:
        for f in os.listdir(SPDIR):
            if f.startswith(key + ".dl.") and f.endswith(".part"):
                return "fetching"
    except OSError:
        pass
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
    # Age pass first: an in-flight job's files have fresh mtimes, so no
    # live-key guard is needed here (JOB_TIMEOUT 30min << keep hours).
    for f in list(files):
        if f[0] < now - keep * 3600:
            _unlink(f); used -= f[1]; files.remove(f)
    # Cap pass. The in-flight job owns EVERY file for its key: .dl.mp4,
    # .dl.mp4.part-Frag#, .f<id>.mp4 merge temps, .fs.mp4 remux temp.
    live_pref = final(_key(_current)) if _current else None
    # A raw with a blessed sibling is pure duplication: the blessed file
    # is what plays. Reclaim it now rather than waiting for the age pass
    # (48h) or for the disk to fill up. The in-flight key is exempt --
    # its raw may be the download that is being written right now.
    for f in list(files):
        base = os.path.basename(f[2])
        if ".dl." not in base or not base.endswith(".mp4"):
            continue
        if live_pref and f[2].startswith(live_pref):
            continue
        key = base.split(".dl.")[0]
        if os.path.exists(os.path.join(SPDIR, key + ".mp4")):
            _unlink(f); used -= f[1]; files.remove(f)
    evict = [f for f in files
             if not (live_pref and f[2].startswith(live_pref))]
    def _rank(f):
        """Duplicates first, then largest, then oldest."""
        base = os.path.basename(f[2])
        dup = 0
        if ".dl." in base and base.endswith(".mp4"):
            key = base.split(".dl.")[0]
            if os.path.exists(os.path.join(SPDIR, key + ".mp4")):
                dup = 1   # a raw with a blessed sibling: pure duplication
        return (dup, -f[1], f[0])
    evict.sort(key=_rank)
    for f in list(evict):
        if used <= cap or used - f[1] < cap * 0.8:
            break
        _unlink(f); used -= f[1]; files.remove(f); evict.remove(f)
    if used > cap and evict:
        # Pathological overflow: floor-breaking survivors (e.g. one giant
        # over-cap artifact) would otherwise wedge the disk forever.
        _unlink(evict[0]); used -= evict[0][1]


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
        return [(item["youtube"], item.get("title"))]
    return []


def renormalize(url, title=None, alert=lambda m, lvl="INFO": None):
    """One-off forced re-spool for the dock loudness verb on link items.
    Refetches and refaststarts the url so it passes through `_faststart`
    (which applies the loudnorm lift). Serialized with the background
    spooler through `_current`; the caller checks on-air first."""
    global _current
    with _state_lock:
        if _current is not None:
            alert("Spooler busy — retry the loudness pass in a minute.",
                  "WARN")
            return False
        _current = url
    threading.Thread(target=_run, args=(url, title, alert),
                     daemon=True).start()
    return True


def kick(items, start, alert=lambda m, lvl="INFO": None):
    global _current
    if not items:
        return []
    picks = []
    for url, title in _urls_ahead(items, start):
        if ready(url) or url == _current:
            continue
        with _state_lock:
            if _current is None:
                _current = url
                threading.Thread(target=_run, args=(url, title, alert),
                                 daemon=True).start()
                picks.append(url)
            break
    _cleanup()
    return picks


def _run(url, title, alert):
    """Blast-rate safety: _current must clear in EVERY exit path, or the
    spooler wedges forever (kick would keep skipping; nothing retries)."""
    global _current
    k = _key(url)
    if os.path.isfile(final(k + NOAUDIO)):
        # Previously produced a silent file; don't redownload forever.
        # _current MUST still be cleared here: the early return used to
        # skip the finally, and one silent item wedged the spooler for
        # the whole station uptime.
        _current = None
        return
    fmt = "bv*[vcodec^=avc1][height<=720]+ba/b[height<=720]/b"
    argv = ytstream._ytdlp_cmd([
        "-f", fmt, "--no-playlist", "--no-warnings",
        "--merge-output-format", "mp4",
        "--max-filesize", "%dM" % (_knob("STREAM_SPOOL_MAX_GB", 3.0) * 1024),
        "--retries", "3", "--newline",
        # .dl. name: ready() must not see the raw (tail-moov) artifact
        # Process-unique: two spoolers must never share a temp file.
        "-o", final(k + ".dl.%d.%%(ext)s" % os.getpid()), url])
    try:
        try:
            p = subprocess.run(argv, capture_output=True, text=True,
                               timeout=JOB_TIMEOUT)
            err = (p.stderr or "").strip().splitlines()[-1:]
        except subprocess.TimeoutExpired:
            alert("Spool timed out: v%s" % url.rsplit("v=", 1)[-1][:20], "WARN")
            return
        except OSError as e:
            alert("Spool failed: %s" % e, "WARN")
            return
        raw = _find_raw(k)
        if raw or ready(url) is not None:
            _mirror_title(k, title)
            _faststart(k, raw=raw)
            info = ready(url)
            if os.path.isfile(final(k + NOAUDIO)):
                # The guard purged the silent bless below; report as a miss.
                info = None
                alert("Spool has no audio: v%s. Purged; live stream keeps "
                      "the sound." % url.rsplit("v=", 1)[-1][:20], "WARN")
            if info:
                alert("Spooled: %s (%.1fMB)" % (info.get("title") or url,
                                                info["size"] / 1e6), "INFO")
            else:
                alert("Spool failed: v%s faststart produced no playable "
                      "mp4" % url.rsplit("v=", 1)[-1][:20], "WARN")
        else:
            alert("Spool failed: v%s %s" % (url.rsplit("v=", 1)[-1][:20],
                                            (err[0] if err else "")[-140:]), "WARN")
    except Exception as e:
        alert("Spool error: %s" % e, "WARN")
    finally:
        _current = None


def _mirror_title(k, title):
    if not title:
        return
    try:
        tmp = final(k + ".title.tmp")
        with open(tmp, "w") as f:
            json.dump({"title": str(title)}, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final(k + ".title"))
    except OSError:
        pass


def _find_raw(k):
    """The raw download this process produced: <key>.dl.<pid>.mp4."""
    try:
        cands = [f for f in os.listdir(SPDIR)
                 if f.startswith(k + ".dl.") and f.endswith(".mp4")]
    except OSError:
        return None
    cands.sort(key=lambda f: os.path.getmtime(os.path.join(SPDIR, f)),
               reverse=True)
    for f in cands:
        p = os.path.join(SPDIR, f)
        if os.path.getsize(p) > 0:
            return p
    return None


def _measured_loudnorm(out):
    """The measured_* block from loudnorm's JSON report, as filter args."""
    try:
        i = out.rfind("{")
        j = out.find("}", i)
        blob = json.loads(out[i:j + 1])
        return (":measured_I=%s:measured_TP=%s:measured_LRA=%s"
                ":measured_thresh=%s:offset=%s:linear=true"
                % (blob["input_i"], blob["input_tp"], blob["input_lra"],
                   blob["input_thresh"], blob["target_offset"]))
    except Exception:
        return ""


def _faststart(k, raw=None):
    raw = raw or final(k + ".dl.mp4")
    tmp = final(k + ".fs.%d.mp4" % os.getpid())
    try:
        # Loudness fix at intake: a music video spooled from YouTube plays
        # on air at a different perceived loudness than the studio cards
        # otherwise; the faststart pass already rewraps, so lift audio to a
        # broadcast target (EBU R128-ish, YouTube loud). Video streams are
        # only copied; a silent raw falls back to plain copy (loudnorm has
        # no audio stream to bind to).
        if LOUDNORM and _has_audio(raw):
            # Two-pass loudnorm. A single pass runs in DYNAMIC mode, which
            # cannot hold the target on wide-LRA music (it clamps to
            # LRA/TP and pumps); measuring first and applying with
            # linear=true hits the target exactly. The second pass also
            # pins the sample rate: loudnorm resamples to 192k internally
            # and the encoder then wrote 96kHz files.
            measured = ""
            try:
                mp = subprocess.run(
                    [FFMPEG, "-hide_banner", "-v", "info", "-i", raw,
                     "-map", "0:a",
                     "-af", "loudnorm=" + LOUDNORM + ":print_format=json",
                     "-f", "null", "-"],
                    capture_output=True, text=True, timeout=300)
                # loudnorm prints its JSON report on STDERR.
                measured = _measured_loudnorm(mp.stderr or "")
            except Exception:
                measured = ""
            cmd = [FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", raw,
                   "-map", "0:v", "-c:v", "copy", "-map", "0:a",
                   "-af", "loudnorm=" + LOUDNORM + measured,
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                   "-movflags", "+faststart", "-f", "mp4", tmp]
        else:
            cmd = [FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", raw,
                   "-c", "copy", "-movflags", "+faststart", "-f", "mp4", tmp]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if p.returncode == 0 and os.path.getsize(tmp) > 0:
            os.replace(tmp, final(k + ".mp4"))
            # The raw IS the download; the blessed file is the remux of it.
            # Keeping both doubles the spool's disk use, so the 3 GB cap
            # only ever bought 1.5 GB of cache. The raw is only needed
            # while there is no blessed copy.
            if raw and os.path.exists(raw):
                try:
                    os.unlink(raw)
                except OSError:
                    pass
            if not _has_audio(final(k + ".mp4")):
                # Silent file: purge the bless so ready() stays a miss (the
                # live pipe keeps sound), drop the raw frees 150MB+, and the
                # marker makes _run refuse the url forever.
                for junk in (".mp4", ".dl.mp4"):
                    try:
                        os.unlink(final(k + junk))
                    except OSError:
                        pass
                try:
                    with open(final(k + NOAUDIO), "w") as f:
                        f.write("1\n")
                except OSError:
                    pass
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


def _has_audio(path):
    """True when the faststarted file carries an audio stream. A silent
    spool airs silent — the playlist falls back to the live pipe instead."""
    try:
        p = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a",
                            "-show_entries", "stream=codec_type", "-of",
                            "csv=p=0", path],
                           capture_output=True, text=True, timeout=60)
        return bool((p.stdout or "").strip())
    except Exception:
        return True  # probe failure must not purge a good file
