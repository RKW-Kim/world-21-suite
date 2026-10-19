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
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEREDOC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HEREDOC_DIR)
MEDIA = os.path.join(ROOT, "broadcast", "media")
PLAYLIST = os.path.join(MEDIA, "playlist.json")
STATE = os.path.join(ROOT, "broadcast", "state.json")
KNOBS = os.path.join(ROOT, "broadcast", "knobs.json")
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


def api_state():
    import spool
    items = (_read(PLAYLIST, {}) or {}).get("items") or []
    return {
        "playlist": _read(PLAYLIST, {"items": []}),
        "state": _read(STATE, {}),
        "knobs": _read(KNOBS, {}),
        "knob_help": KNOB_HELP,
        "state_flags": STATE_FLAGS,
        "media_files": sorted(f for f in os.listdir(MEDIA) if f.endswith(".mp4")),
        "spool": [spool.state(i["youtube"]) if i.get("youtube") is not None else "file"
                  for i in items],
    }


def api_restart(unit):
    if unit not in ("station-daemon.service", "station-obs.service"):
        return {"ok": False, "err": "unknown unit"}
    p = subprocess.run(["systemctl", "--user", "restart", unit],
                       capture_output=True, text=True, timeout=60)
    return {"ok": p.returncode == 0, "err": p.stderr.strip()}


_PANEL_KEYS = {"items", "shuffle_on_complete", "ad_every", "ad_files", "fallback"}


def save_playlist(p):
    """The panel edits the playlist; unknown keys already on disk for OTHER
    flows (ad_plan, idents, per-item fetch metadata) are preserved, not
    silently dropped: the panel is one editor among several."""
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
                    if k not in ("youtube", "file", "title", "status", "duration"):
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
  rows.push('<tr><td>' + (st.deck || (st.in_ad_break ? 'AD' : '?')) + '</td><td>' +
    (st.index || 0) + ' / ' + items.length + '</td><td>' +
    ((cur && (cur.title || cur.youtube || cur.file)) || '—') + '</td><td>' + flags + '</td></tr>');
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
      `<td><input data-k="${k}" size="7" value="${(S.knobs || {})[k] ?? ''}"></td>` +
      `<td class="desc">${desc}</td>`;
    kb.appendChild(tr);
  });
  // state patches
  const fb = document.querySelector('#flags');
  fb.innerHTML = '<tr><th>Key</th><th>Current</th><th>Set to (JSON value)</th><th>Meaning</th></tr>';
  (S.state_flags || []).forEach(([k, desc]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${k}</td><td>${JSON.stringify((S.state || {})[k] ?? '')}</td>` +
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
    def _send(self, code, body, ctype="text/html"):
        raw = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/api/state"):
            self._send(200, api_state(), "application/json")
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
                allowed = {"index", "just_played", "fallback_air",
                           "in_ad_break", "ad_mid", "ad_reports"}
                st = _read(STATE, {})
                for k, v in (data.get("state") or {}).items():
                    if k in allowed:
                        st[k] = v
                _write(STATE, st)
                _send_ok(self)
            elif self.path.startswith("/api/restart"):
                self._send(200, api_restart(data.get("unit")), "application/json")
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
