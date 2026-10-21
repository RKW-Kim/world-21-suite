#!/usr/bin/env python3
"""Station control panel (localhost only) — pick and tweak everything the
daemon reads without SSH or vim.

127.0.0.1:8220. GET / is the page; /api/state is the merged truth (playlist +
knobs + on-air state); POST /api/save writes playlist.json + knobs.json (the
daemon live-reloads the playlist at the next transition and re-applies knobs
each pass); POST /api/state patches state.json allowed keys; POST /api/restart
restarts a unit. Every exposed field carries a description of what it does.
"""
import json
import os
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEREDOC_DIR = os.path.dirname(os.path.abspath(__file__))
# BROADCAST_ROOT (as the daemon defines it) is the broadcast dir itself.
# Only the daemon unit used to be told the root: with BROADCAST_ROOT set
# (the documented VPS layout), the daemon played /var/broadcast while the
# panel read the repo tree - dock saves invisible, heartbeat never found.
ROOT = os.environ.get("BROADCAST_ROOT") or \
    os.path.join(os.path.dirname(HEREDOC_DIR), "broadcast")
REPO = os.path.dirname(HEREDOC_DIR)  # the spool cache is repo-relative
MEDIA = os.path.join(ROOT, "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
STATE = os.path.join(ROOT, "state.json")
KNOBS = os.path.join(ROOT, "knobs.json")
CONTROL = os.path.join(ROOT, "control.json")
PLAYLISTS = os.path.join(MEDIA, "playlists")
PORT = int(os.environ.get("PANEL_PORT", "8220"))

KNOB_HELP = {
    "FEED_WAIT": ("Deck readiness window (s)",
                  "After a cut, how long the daemon waits for OBS to show the new deck OPEN/PLAYING before declaring it stalled and running the fail-safe. Higher = more patience."),
    "STREAM_GRACE": ("Stream end tolerance (s)",
                     "YouTube items end by wall clock (no End signal from OBS). This adds slack past the video's true duration so the last seconds are not chopped."),
    "STREAM_SPAWN_TRIES": ("Feed spawn retries (x3s)",
                           "After a stream feed spawns, MediaMTX is polled this many times (every 3s) for a live publisher before the spawn counts as failed."),
    "STREAM_PRIME_LEAD": ("Pre-buffer lead (s)",
                          "Seconds before the current stream ends at which the NEXT stream is spawned on the idle deck, so the transition is a flip between two live feeds (no black gap). The viewer joins this many seconds into the next video."),
    "REPEAT_LIMIT": ("Fault escalation limit",
                     "Same fault hit this many times in 1h = output goes OFF-AIR and waits for a human. Higher = more retries."),
    "WATCH_POLL": ("Watchdog cadence (s)",
                   "How often the daemon polls faults, feed health and the plane restart. Lower = faster reactions, more CPU."),
    "PLANE_DOWN_SECS": ("OBS restart after (s)",
                        "Seconds of OBS websocket silence tolerated before the daemon auto-restarts the render plane."),
    "PLANE_RESTART_COOLDOWN": ("OBS restart cooldown (s)",
                               "Minimum spacing between two automatic render-plane restarts (one wedged boot cannot loop into a restart storm)."),
    "STREAM_SPOOL_AHEAD": ("Spool lookahead (items)",
                           "How many upcoming link items the daemon pre-downloads while the current one plays. 0 disables spooling (everything streams raw as before)."),
    "STREAM_SPOOL_MAX_GB": ("Spool cache cap (GB)",
                            "Max size of broadcast/spool before the oldest cached copies are evicted. Single items larger than this are skipped (they stream raw)."),
    "STREAM_SPOOL_KEEP_HOURS": ("Spool cache age (h)",
                                "Cached copies older than this are deleted. Low = cache always hot but re-downloads links more often."),
}

STATE_FLAGS = (
    ("index", "Position in the playlist. Deck plays item[index-1]; set 0 to restart from the top at the next transition."),
    ("just_played", "Last played item key; the shuffler avoids repeating it across a seam. Clear ('') if a tiny playlist deadlocks."),
    ("fallback_air", "True = the fail-safe is holding the air with the fallback loop. Only clears the flag; the fail loop is replaced at the next successful cut."),
    ("in_ad_break", "True while an ad break is on screen. Set false to drop the next transition back to the program."),
    ("ad_mid", "Mid-roll planner bookkeeping for the current item. Clear ({} or '') to re-arm the planner."),
)


def _read(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _dock_version():
    """Fingerprint of station/dock.html (mtime + size): the dock reloads
    itself when this changes."""
    try:
        st = os.stat(os.path.join(HEREDOC_DIR, "dock.html"))
        return "%d-%d" % (int(st.st_mtime), st.st_size)
    except OSError:
        return "0"


_title_cache = {}          # url -> title (avoids re-reading 200 .title files a poll)
_title_cache_at = 0.0


def _titles_for(items):
    """Titles for the YouTube rows, cached: a poll used to open and parse
    200 title files every 2s, which the dock pays for in latency. The
    cache is dropped when the playlist changes or once a minute, so a
    freshly spooled title still shows up."""
    import spool
    global _title_cache, _title_cache_at
    now = time.time()
    if now - _title_cache_at > 60:
        _title_cache = {}
        _title_cache_at = now
    out = {}
    missing = False
    for it in items:
        url = it.get("youtube")
        if url is None:
            continue
        if url in _title_cache:
            out[url] = _title_cache[url]
            continue
        r = spool.ready(url)
        if r and r.get("title"):
            _title_cache[url] = r["title"]
            out[url] = r["title"]
        else:
            missing = True
    if missing:
        _title_cache_at = 0.0     # look again next poll
    return out


def _normalize_on(default=True):
    """Station-wide loudness switch (daemon-owned file)."""
    v = _read(os.path.join(ROOT, "normalize.json"), None)
    if isinstance(v, dict) and "on" in v:
        return bool(v.get("on"))
    return default


def api_ping():
    """A tiny "did anything move?" answer. The dock polled the full
    58KB state every 2s; this lets it skip that fetch entirely when the
    playlist, the state and the spool are all unchanged."""
    ver = []
    for path in (PLAYLIST, STATE):
        try:
            st = os.stat(path)
            ver.append("%d-%d" % (int(st.st_mtime_ns), st.st_size))
        except OSError:
            ver.append("0-0")
    try:
        ver.append(str(int(os.stat(os.path.join(REPO, "spool")).st_mtime_ns)))
    except OSError:
        ver.append("0")
    hb = _read(os.path.join(ROOT, "heartbeat.json"), {})
    age, pass_ms, busy = None, 0, ""
    if isinstance(hb, dict):
        if isinstance(hb.get("t"), (int, float)):
            age = round(max(0.0, time.time() - hb["t"]), 1)
        pass_ms = int(hb.get("pass_ms") or 0)
        busy = hb.get("busy") or ""
    return {"v": "|".join(ver), "daemon": {"stale": age, "pass_ms": pass_ms,
                                          "busy": busy},
            "onair": (hb.get("onair") or {}) if isinstance(hb, dict) else {},
            "normalize": {"on": _normalize_on()},
            "dock_version": _dock_version()}


def api_state():
    import spool
    items = (_read(PLAYLIST, {}) or {}).get("items") or []
    titles = _titles_for(items)
    hb = _read(os.path.join(ROOT, "heartbeat.json"), {})
    daemon_age = None
    pass_ms = 0
    busy = ""
    if isinstance(hb, dict) and isinstance(hb.get("t"), (int, float)):
        daemon_age = round(max(0.0, time.time() - hb["t"]), 1)
        pass_ms = int(hb.get("pass_ms") or 0)
        busy = hb.get("busy") or ""
    _st = _read(STATE, {})
    _hb = _read(os.path.join(ROOT, "broadcast", "heartbeat.json"), {})
    if isinstance(_hb, dict) and _hb.get("onair"):
        _st["onair"] = _hb["onair"]
    return {
        "playlist": _read(PLAYLIST, {"items": []}),
        "state": _st,
        "knobs": _read(KNOBS, {}),
        "knob_help": KNOB_HELP,
        "state_flags": STATE_FLAGS,
        "media_files": sorted(f for f in os.listdir(MEDIA) if f.endswith(".mp4")),
        "spool": [spool.state(i["youtube"]) if i.get("youtube") is not None else "file"
                  for i in items],
        "yt_titles": titles,
        "daemon": {"stale": daemon_age, "pass_ms": pass_ms, "busy": busy},
        "normalize": {"on": _normalize_on()},
        # The dock compares this with the version it loaded and reloads
        # itself when the file changed — an OBS browser dock caches the
        # page, so without this the operator keeps looking at stale UI.
        "dock_version": _dock_version(),
    }


def api_restart(unit):
    if unit not in ("station-daemon.service", "station-obs.service"):
        return {"ok": False, "err": "unknown unit"}
    p = subprocess.run(["systemctl", "--user", "restart", unit],
                       capture_output=True, text=True, timeout=60)
    return {"ok": p.returncode == 0, "err": p.stderr.strip()}


def api_playlists_post(data):
    """Profile library: broadcast/media/playlists/<name>.json.
    save stores the playlist it is given (the dock's working copy, so a
    profile can be saved before it is applied); load RETURNS the profile
    instead of overwriting the live playlist — the dock stages it and the
    operator presses Apply."""
    name = str(data.get("name") or "").strip()
    if not name or "/" in name or name.startswith("."):
        return {"ok": False, "err": "bad name"}
    path = os.path.join(PLAYLISTS, name + ".json")
    action = data.get("action")
    if action == "save":
        os.makedirs(PLAYLISTS, exist_ok=True)
        pl = data.get("playlist")
        if not isinstance(pl, dict) or not isinstance(pl.get("items"), list):
            pl = _read(PLAYLIST, {})
        validate_playlist(pl)
        _write(path, pl)
        return {"ok": True}
    if action == "load":
        p = _read(path, None)
        if p is None:
            return {"ok": False, "err": "no such profile"}
        validate_playlist(p)
        return {"ok": True, "playlist": p}
    if action == "delete":
        try:
            os.unlink(path)
        except OSError:
            return {"ok": False, "err": "no such profile"}
        return {"ok": True}
    return {"ok": False, "err": "unknown action"}


def api_playlists_get():
    if not os.path.isdir(PLAYLISTS):
        return {"playlists": []}
    return {"playlists": sorted(
        f[:-5] for f in os.listdir(PLAYLISTS) if f.endswith(".json"))}


def api_control(data):
    """Dock transport: control.json is read each daemon pass. skip ends the
    current item exactly like a natural media end; {"media": {...}} carries
    the transport/mixer verbs the daemon consumes (pause/resume/restart/mix);
    {"normalize": {"global": true|false}} is the station-wide loudness
    switch (compress+limit on every playback input).

    The whole RMW sits under the station lock: the daemon reads this file,
    acts for seconds, then re-reads fresh and pops only what it consumed.
    An unlocked write here could land between its read and write-back --
    a skip posted during a long transition got eaten, and a stale copy
    could resurrect a verb the daemon had just consumed (double-advance).
    """
    import daemon   # the station lock lives with the daemon
    with daemon.pl_lock():
        ctl = _read(CONTROL, {})
        if data.get("skip"):
            ctl["skip"] = True
        if isinstance(data.get("media"), dict):
            ctl["media"] = dict(data["media"])
        norm = data.get("normalize")
        if isinstance(norm, dict):
            if norm.get("file"):
                ctl["normalize"] = {"file": str(norm["file"])}
            elif norm.get("url"):
                ctl["normalize"] = {"url": str(norm["url"])}
            elif "global" in norm:
                ctl["normalize"] = {"global": bool(norm.get("global"))}
        _write(CONTROL, ctl)
    return {"ok": True}


def api_ytpl(data):
    """YouTube playlist import (dock): paste a /playlist?list=... link, get
    the videos back as a flat ordered list. yt-dlp --flat-playlist resolves
    titles WITHOUT touching the videos (seconds, no downloads)."""
    url = str(data.get("url") or "").strip()
    if "list=" not in url or not ("youtube.com" in url or "youtu.be" in url):
        return {"ok": False, "err": "paste a YouTube playlist link (with list=) here"}
    exe = shutil.which("yt-dlp") or "/usr/bin/yt-dlp"
    if not os.path.exists(exe):
        return {"ok": False, "err": "yt-dlp not found on this host"}
    try:
        p = subprocess.run(
            [exe, "--flat-playlist", "--no-warnings", "-J", url],
            capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            return {"ok": False, "err": (p.stderr or "yt-dlp failed")[-180:]}
        j = json.loads(p.stdout or "{}")
        vids = [{"url": "https://www.youtube.com/watch?v=" + e["id"],
                 "title": e.get("title") or ""}
                for e in (j.get("entries") or []) if e.get("id")]
        if not vids:
            return {"ok": False, "err": "playlist came back empty (private or empty list?)"}
        return {"ok": True, "title": j.get("title") or "playlist", "videos": vids}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "playlist fetch timed out"}
    except (OSError, ValueError) as e:
        return {"ok": False, "err": str(e)[-180:]}


_PANEL_KEYS = {"items", "shuffle_on_complete", "ad_every", "ad_files", "fallback"}


def save_playlist(p):
    """The panel edits the playlist; unknown keys already on disk for OTHER
    flows (ad_plan, idents, per-item fetch metadata) are preserved, not
    silently dropped: the panel is one editor among several."""
    import daemon
    # The WHOLE read-modify-write inside the station lock. The read used to
    # sit outside it: the daemon's shuffle-save/played-marks landing in that
    # window were published over by this stale copy (AGENTS.md rule 2 —
    # /api/state POST already did this right).
    with daemon.pl_lock():
        cur = _read(PLAYLIST, {})
        out = dict(cur)
        for k in cur:
            if k not in _PANEL_KEYS:
                out[k] = cur[k]  # pass through untouched
        for k, v in p.items():
            out[k] = v  # panel owns the editable keys
        if isinstance(cur.get("items"), list) and \
                isinstance(out.get("items"), list) and \
                len(cur["items"]) == len(out["items"]):
            for old, new in zip(cur["items"], out["items"]):
                if isinstance(old, dict) and isinstance(new, dict):
                    for k in old:
                        # the dock owns these too — if its copy dropped the key
                        # (cleared meta_trip, unparked gorder), it meant it
                        if k not in ("youtube", "file", "title", "status",
                                     "duration", "meta_trip", "group",
                                     "gorder", "tab"):
                            new.setdefault(k, old[k])
        validate_playlist(out)
        _write(PLAYLIST, out)


def validate_playlist(p):
    if not isinstance(p, dict):
        raise ValueError("playlist must be an object")
    items = p.get("items", [])
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    for it in items:
        if not isinstance(it, dict):
            raise ValueError("item is not an object")
        if not (it.get("youtube") or it.get("file")):
            raise ValueError("item needs youtube or file")
        if it.get("youtube") and it.get("file"):
            raise ValueError("item cannot be both a link and a file")
    p.setdefault("shuffle_on_complete", False)
    p.setdefault("ad_every", 0)
    return p


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>World-21 Station Panel</title>
<style>
 body{font:14px/1.45 system-ui,sans-serif;margin:2em auto;max-width:960px;color:#222}
 h1{font-size:1.35em} h2{border-bottom:1px solid #aaa;padding-bottom:2px;font-size:1.1em;margin-top:1.6em}
 table{border-collapse:collapse;width:100%;margin-top:.4em}
 td,th{border:1px solid #ddd;padding:4px 6px;vertical-align:top;text-align:left}
 th{background:#f4f4f4}
 input,select,textarea{width:100%;box-sizing:border-box}
 .desc{color:#666;font-size:.85em}
 .btn{padding:4px 10px;border:1px solid #888;background:#f4f4f4;cursor:pointer;margin:2px}
 .btn.warn{border-color:#a33;color:#a33}
 input[data-b],select[data-b]{padding:3px}
 #out{font-family:monospace;white-space:pre-wrap;background:#111;color:#9f9;padding:8px;min-height:3em}
</style></head><body>
<h1>World-21 station control</h1>
<div class="desc">This panel writes exactly the files the daemon reads every pass.
playlist.json reloads live (applies at the next transition); knobs.json applies on
the next watchdog pass — no restart needed. State patches take effect on their own.</div>
<div>
<button class="btn" onclick="location.reload()">Reload from disk</button>
<button class="btn warn" onclick="restart('station-daemon.service');return false;" href="#">Restart daemon</button>
<button class="btn warn" onclick="restart('station-obs.service');return false;" href="#">Restart OBS</button>
</div>

<h2>Playing now</h2>
<table id="now"><tr><th>Deck</th><th>Item index</th><th>Title</th><th>Flags</th></tr></table>

<h2>Playlist (order is live; the deck plays items top to bottom)</h2>
<table id="items">
<tr><th>#</th><th>Kind</th><th>Value</th><th>Title</th><th>Status</th><th>Duration (s)</th><th>Cache</th><th></th></tr>
</table>
<button class="btn" onclick="addItem('clean')">+ add</button>
<div class="desc">Kind stream = YouTube URL, played live through rtlnk/std-rtmp (no disk).
Kind file = local file from broadcast/media. Status active = plays; dormant = kept but never
selected. Duration overrides the probed/expected length (recover end-of-stream schedule).</div>

<h2>Ad configuration</h2>
<table>
<tr><th>ad_every <span class="desc">(items between breaks; 0 = off)</span></th>
<td><input data-b="ad_every"></td></tr>
<tr><th>Ad pool <span class="desc">(one local media file per line; engine picks at random)</span></th>
<td><textarea data-b="ad_files" rows="3"></textarea></td></tr>
</table>

<h2>Fail-safe pool</h2>
<div class="desc">Files used to hold the air if a deck stalls. Usually a short loop.</div>
<textarea data-b="fallback" rows="3"></textarea>

<h2>Knobs (the daemon re-reads these values every watchdog pass)</h2>
<table id="knobs"><tr><th>Knob</th><th>Current</th><th>What it does and how it links</th></tr></table>
<button class="btn warn" onclick="saveAll()">Save playlist + knobs</button>

<h2>state.json patches</h2>
<table id="flags"><tr><th>Key</th><th>Current</th><th>Set to (JSON value)</th><th>Meaning</th></tr></table>
<button class="btn warn" onclick="saveState()">Apply patches</button>

<h2>Log</h2><pre id="out">panel ready — load from disk happened on page load</pre>

<script>
let S = {};

async function post(url, body) {
  try {
    const r = await fetch(url, {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    return await r.json();
  } catch (e) { return {ok: false, err: String(e)}; }
}

async function restart(u) {
  const out = await post('/api/restart', {unit: u});
  document.getElementById('out').textContent = 'restart ' + u + ': ' + JSON.stringify(out);
}

function items() { return S.playlist.items || []; }

function gather() {
  const pl = {items: items(), shuffle_on_complete: !!document.querySelector('[data-b=shuffle]').checked};
  const ae = parseInt(document.querySelector('[data-b=ad_every]').value, 10);
  if (!isNaN(ae)) pl.ad_every = ae;
  pl.ad_files = (document.querySelector('[data-b=ad_files]').value || '')
    .split('\\n').map(x => x.trim()).filter(x => x);
  pl.fallback = (document.querySelector('[data-b=fallback]').value || '')
    .split('\\n').map(x => x.trim()).filter(x => x);
  const knobs = {};
  document.querySelectorAll('#knobs input[data-k]').forEach(inp => {
    const v = parseFloat(inp.value);
    if (!isNaN(v)) knobs[inp.dataset.k] = v;
  });
  const st = {};
  document.querySelectorAll('#flags input[data-f]').forEach(inp => {
    if (inp.value.trim() === '') return;
    try { st[inp.dataset.f] = JSON.parse(inp.value); }
    catch (e) { st[inp.dataset.f] = inp.value; }
  });
  return {playlist: pl, knobs: knobs, state: st};
}

function upd(idx, key, value) {
  S.playlist.items[idx][key] = value;
  if (key === 'kind') {
    const it = S.playlist.items[idx];
    if (value === 'stream') { it.youtube = it.file || ''; delete it.file; }
    else { it.file = it.youtube || ''; delete it.youtube; }
  }
  renderItems();
}

async function saveAll() {
  const g = gather();
  const out = await post('/api/save', g);
  document.getElementById('out').textContent = JSON.stringify(out, null, 1);
}

async function saveState() {
  const out = await post('/api/state', {state: gather().state});
  document.getElementById('out').textContent = JSON.stringify(out, null, 1);
}

function mv(idx, d) {
  const rows = document.querySelectorAll('#items tr[data-idx]');
  const to = idx + d;
  if (to < 0 || to >= rows.length) return;
  const src = S.playlist.items[idx];
  S.playlist.items.splice(idx, 1);
  S.playlist.items.splice(to, 0, src);
  renderItems();
}

function del(idx) {
  S.playlist.items.splice(idx, 1);
  renderItems();
}

function addItem(kind) {
  S.playlist.items = S.playlist.items || [];
  S.playlist.items.push(kind === 'stream'
    ? {youtube: '', title: ''}
    : {file: '', title: ''});
  renderItems();
}

function renderNow() {
  const rows = [];
  const st = S.state || {};
  const items = S.playlist.items || [];
  const cur = items[(Math.max(0, parseInt(st.index || 0, 10)) - 1) % Math.max(1, items.length)];
  const flags = ['fallback_air', 'in_ad_break'].map(f => st[f] ? f : null).filter(Boolean).join(',') || '-';
  rows.push('<tr><td>' + esc(st.deck || (st.in_ad_break ? 'AD' : '?')) + '</td><td>' +
    esc(st.index || 0) + ' / ' + items.length + '</td><td>' +
    esc((cur && (cur.title || cur.youtube || cur.file)) || '—') + '</td><td>' + esc(flags) + '</td></tr>');
  document.querySelector('#now tbody').innerHTML = rows.join('');
}

function renderItems() {
  const tb = document.querySelector('#items');
  tb.querySelectorAll('tr[data-idx]').forEach(r => r.remove());
  const its = items();
  its.forEach((it, idx) => {
    const tr = document.createElement('tr');
    tr.dataset.idx = idx;
    const kind = it.youtube ? 'stream' : 'file';
    const val = kind === 'stream' ? (it.youtube || '') : (it.file || '');
    const dur = (it.duration === undefined || it.duration === null) ? '' : it.duration;
    const sp = ((S.spool || [])[idx]) || '';
    tr.innerHTML =
      '<td>' + idx + '</td>' +
      '<td><select data-c="kind"></select></td>' +
      '<td><input data-c="value" value="' + esc(val) + '"></td>' +
      '<td><input data-c="title" value="' + esc(it.title || '') + '"></td>' +
      '<td><input data-c="status" size="8" value="' + esc(it.status || 'active') + '"></td>' +
      '<td><input data-c="dur" size="7" value="' + esc(dur) + '"></td>' +
      '<td class="spool" title="cache: ready = buffered copy will play whole; fetching = downloading now; miss = will stream raw">' + esc(sp) + '</td>' +
      '<td><button class="btn" data-a="del" title="remove row">x</button>' +
      '<button class="btn" data-a="up" title="move up">&#8593;</button>' +
      '<button class="btn" data-a="down" title="move down">&#8595;</button></td>';
    tb.appendChild(tr);
    const kindSel = tr.querySelector('[data-c=kind]');
    kindSel.innerHTML = kind === 'stream'
      ? '<option value="stream" selected>stream</option><option value="file">file</option>'
      : '<option value="stream">stream</option><option value="file" selected>file</option>';
    kindSel.onchange = () => upd(idx, 'kind', kindSel.value);
    tr.querySelector('[data-c=value]').onchange = e =>
      upd(idx, kind === 'stream' ? 'youtube' : 'file', e.target.value);
    tr.querySelector('[data-c=title]').onchange = e => upd(idx, 'title', e.target.value);
    tr.querySelector('[data-c=status]').onchange = e => upd(idx, 'status', e.target.value);
    tr.querySelector('[data-c=dur]').onchange = e =>
      upd(idx, 'duration', e.target.value === '' ? null : parseFloat(e.target.value));
    tr.querySelector('[data-a=del]').onclick = () => del(idx);
    tr.querySelector('[data-a=up]').onclick = () => mv(idx, -1);
    tr.querySelector('[data-a=down]').onclick = () => mv(idx, 1);
  });
}

function esc(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
}

function render() {
  const pl = S.playlist || {};
  document.querySelector('[data-b=shuffle]').checked = !!pl.shuffle_on_complete;
  document.querySelector('[data-b=ad_every]').value = pl.ad_every ?? 0;
  document.querySelector('[data-b=ad_files]').value = (pl.ad_files || []).join('\\n');
  document.querySelector('[data-b=fallback]').value = (pl.fallback || []).join('\\n');
  renderItems();
  renderNow();
  // knobs
  const kb = document.querySelector('#knobs');
  kb.innerHTML = '<tr><th>Knob</th><th>Current</th><th>What it does and how it links</th></tr>';
  Object.entries(S.knob_help || {}).forEach(([k, [label, desc]]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${k} <span class="desc">(${label})</span></td>` +
      `<td><input data-k="${k}" size="7" value="${esc((S.knobs || {})[k] ?? '')}"></td>` +
      `<td class="desc">${desc}</td>`;
    kb.appendChild(tr);
  });
  // state patches
  const fb = document.querySelector('#flags');
  fb.innerHTML = '<tr><th>Key</th><th>Current</th><th>Set to (JSON value)</th><th>Meaning</th></tr>';
  (S.state_flags || []).forEach(([k, desc]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${k}</td><td>${esc(JSON.stringify((S.state || {})[k] ?? ''))}</td>` +
      `<td><input data-f="${k}" placeholder="e.g. 0"></td><td class="desc">${desc}</td>`;
    fb.appendChild(tr);
  });
}

async function load() {
  S = await (await fetch('/api/state')).json();
  S.playlist.items = S.playlist.items || [];
  render();
}

load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 with keep-alive: the dock polls every 2s, and under
    # HTTP/1.0 every poll opened a fresh TCP connection (the handler
    # itself takes 0.4ms; the connection setup was the other ~60ms).
    # Every response here sets Content-Length, so keep-alive is safe.
    protocol_version = "HTTP/1.1"
    timeout = 30
    def _send(self, code, body, ctype="text/html"):
        if isinstance(body, bytes):
            raw = body
        elif isinstance(body, str):
            raw = body.encode()
        else:
            raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/api/state"):
            self._send(200, api_state(), "application/json")
        elif self.path.startswith("/api/ping"):
            self._send(200, api_ping(), "application/json")
        elif self.path.startswith("/api/thumb"):
            # The dock shows a poster frame for the row it is inspecting.
            # The overlay server owns the thumbnail cache; the panel
            # proxies it so the dock stays same-origin.
            name = ""
            if "?" in self.path:
                name = self.path.split("?", 1)[1]
                for k, v in (p.split("=", 1) for p in name.split("&") if "=" in p):
                    if k == "file":
                        name = v
            # The dock percent-encodes the filename; decode before the
            # basename guard, or "intro video.mp4" arrived as a literal
            # "%20" string and the proxy 404'd every spaced/unicode name.
            name = urllib.parse.unquote(name)
            name = os.path.basename(name)
            if not name or "/" in name or name.startswith("."):
                return self._send(404, {"ok": False, "err": "no file"}, "application/json")
            try:
                with urllib.request.urlopen(
                        "http://127.0.0.1:7070/thumbs/" + urllib.parse.quote(name),
                        timeout=20) as r:
                    body = r.read()
                self._send(200, body, "image/jpeg")
            except Exception as e:
                self._send(404, {"ok": False, "err": str(e)[:80]},
                           "application/json")
        elif self.path.startswith("/api/playlists"):
            self._send(200, api_playlists_get(), "application/json")
        elif self.path.startswith("/dock"):
            try:
                # Stamp the served bytes with their own fingerprint, so the
                # dock can tell "this is what I loaded" from "the file on
                # disk is newer" and reload itself.
                ver = _dock_version()
                with open(os.path.join(HEREDOC_DIR, "dock.html")) as f:
                    html = f.read()
                html = html.replace(
                    "<body>", '<body>\n<script>window.__DOCK_VERSION__=%s;</script>'
                    % json.dumps(ver), 1)
                self._send(200, html, "text/html")
            except OSError:
                self._send(404, "dock.html missing", "text/plain")
        else:
            self._send(200, PAGE)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n)
        try:
            data = json.loads(body) if body else {}
        except ValueError:
            return self._send(400, {"ok": False, "err": "bad JSON"}, "application/json")
        try:
            if self.path.startswith("/api/save"):
                save_playlist(data["playlist"])
                knobs = {k: v for k, v in (data.get("knobs") or {}).items()
                         if k in KNOB_HELP and isinstance(v, (int, float))}
                if knobs:
                    _write(KNOBS, knobs)
                _send_ok(self)
            elif self.path.startswith("/api/state"):
                import daemon   # the station lock lives with the daemon
                allowed = {"index", "just_played", "fallback_air",
                           "in_ad_break", "ad_mid", "ad_reports"}
                # The station lock: the daemon reads and writes the same
                # file, and an unlocked read-modify-write here silently
                # ate its index update (and vice versa).
                with daemon.pl_lock():
                    st = _read(STATE, {})
                    for k, v in (data.get("state") or {}).items():
                        if k in allowed:
                            st[k] = v
                    _write(STATE, st)
                _send_ok(self)
            elif self.path.startswith("/api/restart"):
                self._send(200, api_restart(data.get("unit")), "application/json")
            elif self.path.startswith("/api/playlists"):
                self._send(200, api_playlists_post(data), "application/json")
            elif self.path.startswith("/api/control"):
                self._send(200, api_control(data), "application/json")
            elif self.path.startswith("/api/ytpl"):
                self._send(200, api_ytpl(data), "application/json")
            else:
                self._send(404, {"ok": False, "err": "unknown endpoint"},
                           "application/json")
        except (ValueError, KeyError) as ex:
            self._send(400, {"ok": False, "err": str(ex)}, "application/json")

    def log_message(self, *a):
        pass


def _send_ok(self):
    self._send(200, {"ok": True}, "application/json")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("panel serving http://127.0.0.1:%d" % PORT, flush=True)
    srv.serve_forever()
