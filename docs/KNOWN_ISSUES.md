# Known issues

What is still broken, what is deliberately not done, and what is stale.
Ordered by how much it matters.

---

## Open defects (2026-10-21 audit)

Found by a five-agent read of the whole tree (daemon, panel+dock,
overlay/stream/intake, infra, plus the 24-7-Playout-Plugin feature
comparison). The load-bearing ones were fixed and committed the same
day (see WORKLOG); these are the ones still open, ranked:

- **The relay auth bridge hands out authenticated OBS control without
  the OBS password.** `overlay_server.py` /ws + /obs: the bridge
  replaces the browser's Identify auth with the server secret, and the
  guard's no-Origin and `Origin: null` bypasses mean any LAN client —
  or any web page in any browser via a sandboxed iframe — gets the
  render plane. Fine while BIND=127.0.0.1 + tunnels only; before any
  WAN exposure this needs STATION_TOKEN required for /ws + /obs (and
  `hmac.compare_digest` for it). Also: `Origin: null` should refuse
  when STATION_TOKEN is set, not pass.
- **MediaMTX has no publish/read auth and setup.sh opens SRT to the
  world.** `ufw allow 9000:9001/udp` with no source restriction means
  anyone on the internet can publish `slot-cam`/`slot-screen` (on-air
  injection when a seat is free) and read everything. Add
  `authInternalUsers` (publish-only seats) and source-restricted ufw
  rules; WHIP 8889/tcp + the WebRTC UDP mux are also not opened, so the
  documented seats can't reach the box from outside.
- **control.json is a lock-free cross-process RMW.** The panel's
  api_control read-modify-write races the daemon's consume-and-rewrite
  (which spans the whole advance, seconds): a skip posted during a long
  transition can be eaten, or a stale write resurrect a consumed verb
  (double-advance). Needs one side to hold the station lock, and the
  daemon to re-read fresh at write-back and pop only what it consumed.
- **Dock undo/redo is structurally broken.** The history stack stores
  pre-states only: redo never restores the newest state (one edit +
  undo + redo loses the staged edit while the bar claims it is
  staged), and a reload restores the state *before* the last edit.
  DECISIONS §1 promises durable step-by-step history; store post-states
  (or persist `draft` itself).
- **The dock's shuffle-at-end toggle is dead.** `markPending()` only
  diffs item arrays, so toggling shuffle_on_complete alone never
  stages, Apply refuses, and the checkbox is never seeded from the
  station's actual value — the operator can believe it is off while the
  roll reshuffles.
- **Keyboard cursor walks rows hidden inside folded groups.**
  `visibleRows()` returns display:none rows; ↓ off the queue bottom
  strands the roving tab stop in an invisible row (Enter then acts on
  what the operator cannot see). Filter out hidden rows.
- **On-air / NEXT markers are indices into the staged draft.** While
  edits are pending, the green bar lands on whatever now occupies slot
  index-1 in the draft, not on the item actually on air. Mark by item
  identity.
- **Respawn reuses possibly-dead HLS URLs.** stream.py re-resolves only
  when the resolve is >30 min old, so a mid-stream 403 inside the
  window respawns the same dead URLs fifteen times and walks the item
  to the fault limit, when a fresh resolve would heal it. Always
  resolve on respawn.
- **Intake publishes non-atomically.** normalise() writes straight to
  the final media name; a SIGKILLed intake leaves a partial
  broadcast-eligible file plus a full raw in an eviction-exempt
  `.intake-tmp-<pid>` workdir (pid reuse adopts stale workdirs after
  weeks of uptime). Normalise into the workdir, `os.replace` into
  place, sweep stale tmpdirs.
- **The "4s thread cap" exists exactly once (and that once was broken —
  the probe now works, see the fixed list).** `/intent`, `/obs` proxy
  and music-set still call the shared renderer inline, so a wedged
  plane queues handler threads for up to OBS_TIMEOUT each. Wrap plane
  calls in the bounded helper.
- **`_RESOLVE_CACHE` never prunes** (unbounded over months of URLs;
  tens of MB). Drop expired entries during prefetch_stream_pass.
- **Silent cookie fallback**: stream.py/intake.py pass `--cookies` only
  when the file exists; a stale file silently downgrades to anonymous
  and the operator cannot tell why the bot-wall returned. Log once.
- **preflight.py crashes on a corrupt/missing playlist** — the exact
  broken boot it exists to diagnose. Guard the load.
- **Watchdog ignores systemctl exit codes and is scope-blind on root
  installs** (hardcoded `--user`); a failed start counts as revived.
  Also no park fence vs `sync.py apply --restart` (a timer firing
  mid-apply can start the daemon under the merge) and no plane-restart
  cooldown of its own.
- **sync.py apply mixes systemd scopes on root installs**: stops
  system units, "restarts" user units (swallowed failures, station
  dark). Use the resolved scope for both directions.
- **station-obs.service is lab-shaped for the VPS**: DISPLAY=:0 with no
  headless session recipe shipped, no `LIBGL_ALWAYS_SOFTWARE=1` path
  for a GPU-less boot, BrowserHWAccel=false only written when
  global.ini already exists, and the setup checklist says 1080p/6000k
  while config/ + VPS.md say 540p/2500k.
- **config/collection.json staleness** (listed below) is now sharper:
  `sync.py apply` would create a duplicate `SMILE | Meet` scene and
  restart the on-air deck source mid-item; the deck diff also only
  hides `.enabled`, not `settings.local_file`, so diff is perpetually
  noisy and trains the operator to ignore drift.
- **Thumbnail cache bookkeeping**: one lock object per filename ever
  requested, unbounded waiter queue, and a timeout-killed ffmpeg can
  leave a partial .jpg that is served forever (generate to tmp +
  os.replace, cap the map).
- **`/files` NUL byte** escapes the OSError catch (ValueError → dead
  connection, no response). Cosmetic; catch it.

### Fixed same-day (2026-10-21) — kept here until the next doc pass

File ad breaks self-destructed (dead `ad_start` write crashed every
one — the break flash-cut and back, latched nothing); the shuffle seam
rule never saw stream items (`item_key` missed `youtube` — 43/200
shuffles led with the just-played video); boot park muted the on-air
deck after a restart onto a spooled item; pause wiped the saved mix;
the stream respawn budget never persisted (respawn-every-poll storm);
file items never got their planned mid-rolls (advance pre-seeded the
poll's own gate); eviction could eat the fail-safe loops and the ad
pool; `/library` + `/ads` read bodies inside the station lock (a slow
client froze playout); the relay wedged at its session cap on a
malformed Identify and had no frame-size cap; GET /music's probe
raised NameError on every call; the panel's playlist RMW was torn
(read outside the lock), the legacy page interpolated titles
unescaped, and /api/thumb double-encoded filenames; the spool state
cache served stale states on coarse-mtime filesystems (caught by the
fresh-clone test baseline on the migration target); hold states
alerted every pass instead of hourly; pl_lock crashed selftest on a
fresh clone; setup.sh armed the publish leg, never enabled the
watchdog timer, double-sed'd EnvironmentFile into a bare path, and
told only the daemon the BROADCAST_ROOT (panel split-brain).

---

## Open defects

### The "monitor" path was missing from MediaMTX (fixed 2026-10-21, but read this)

OBS's stream service targets `rtmp://127.0.0.1:1935/monitor`. The path
was removed from `station/mediamtx.yml` on 2026-10-18 as a "lab-era
leftover", so OBS's output went inactive and the daemon logged
`Stream output not active!` on every pass. The path is restored and the
alert is now gated on a real stream key being present. **The publish leg
itself is still off by default** — see `docs/DECISIONS.md` §13.

### The station has never published to YouTube

There was no publish leg at all: the stream key in `secrets.env` is a
convention placeholder and nothing consumed it. `station/publish_youtube.sh`
+ `station-publish.service` now exist, disabled, and refuse to run with
the placeholder. To go live: put a real key in `broadcast/secrets.env`,
`systemctl --user enable --now station-publish.service`.

### The OBS stream service in `station/config/` is not what the live plane has

`station/config/collection.json` is a **capture** and it is stale: it names
the scene `SMILE | Meet`, while the live plane has `SMILE | Program` (a
rename that cost a day of ghost re-kicks). `sync.py apply` pushes the
config; it also stops the daemon and the plane first. Do not run it
casually on a live station: it overwrites the live collection.

### `station-monitor-av.service` is a dead path

It republishes `rtsp://127.0.0.1:1935/monitor` as `monitor-av`; neither
path exists any more, and the unit crash-looped 11k+ times doing nothing.
`setup.sh` no longer installs it, but the file is still in
`station/systemd/`. Delete it when nobody is looking at the history.

### The Xvfb display `:99` is vestigial

OBS moved to the real session (`:0`) for hardware GL. `station-xvfb.service`
still runs `Xvfb :99` and `station-obs.service` still `Requires=` it. It
costs a little RAM and nothing else. Removing it means also fixing
`obs_click.py`'s default display.

### The title watcher only checks a few items per cycle

`_title_watch_pass()` resolves at most 3 fresh URLs and flags at most 2
renames per cycle (every `TITLE_WATCH_SECS`, default 300 s). A 200-item
playlist therefore takes many cycles to be fully checked. The operator
asked for a **daily** full metadata sweep; that is not implemented yet
(see "Not done" below).

### The Music Bed input has no bed file by default

`broadcast/media/music/` is empty, so the waiting-room scenes have a bed
input pointing at nothing. It is harmless (no audio) but it is not the
finished thing.

---

## Deliberately not done

| Item | Why |
|---|---|
| **Recording the programme** | The operator will record live segments manually (Google Meet, choosing the source by hand). Recording the whole programme would double the disk and the CPU for a feature nobody asked for. |
| **A Go rewrite of the daemon** | Measured: a pass is 20–190 ms, the daemon is idle ~99 % of the time, and the felt stalls were a misreported heartbeat, an unbounded handshake and a 40 ms DOM rebuild inside OBS. A rewrite would change none of them. |
| **Per-item loudness in the row menu** | Replaced by the station-wide switch (operator's decision). The file-level EBU pass still runs at intake. |
| **Re-loudnorming all 200 spooled links** | It would re-download every YouTube item for hours and hammer the disk. The station-wide dynamics chain covers the "fully on" intent. |
| **The browser context menu inside text fields** | Suppressed everywhere except inputs, where paste has to work. |
| **Auto-apply of low-risk edits** | The operator chose staged-only, with a loud prompt instead. |

---

## Not done yet (asked for, not built)

- **Per-item preview panel** (operator's Q5): clicking a row should show
  its thumbnail, description and other metadata, with a manual refresh and
  a daily metadata check. The pieces exist — `/thumbs/<file>` on the
  overlay server, and the title watcher as a metadata prober — but the
  panel in the dock does not exist.
- **Scheduled profiles** (day/night running orders switching on a clock).
- **A queue timeline / playhead** (the Studio Player pattern): a visual
  running order with a draggable playhead.
- **Bulk review of amber rows** (approve all / discard all) — the operator
  asked for the bulk action alongside the per-row one.
- **The daily metadata sweep** described above.

---

## Deliberate sharp edges

Things that look like bugs but are the design:

- **Parked decks are muted, not paused.** They keep decoding silently so a
  cut is instant. The daemon's comment says so; do not "fix" it.
- **The 6-second post-cut refractory** looks like a stuck advance. It
  guards against `ENDED` flicker right after a cut. It is anchored to the
  input that was just cut to, so the fail-safe can still roll.
- **`merge_save_state()` deletes absent keys.** By design: the daemon
  clears `fallback_air` by omitting it. Callers must pass the whole state.
- **The station is quiet when it is fine.** The activity log is trimmed to
  5,000 rows and INFO rows are only interesting when you go looking.
