# Known issues

What is still broken, what is deliberately not done, and what is stale.
Ordered by how much it matters.

---

## Open defects (after the 2026-10-21 regression pass AND the web
## agent's round, verified 2026-10-22)

> **Verified 2026-10-22 (the z.ai agent's 55-commit round, reviewed
> on the box).** The round's four fixes are sound and its suite runner
> works. Three defects were found in ITS work and fixed here: the unit
> render never reached four units (the ingest bus would not have
> started on a fresh install), the render was untestable, and
> plane-off mode was incoherent. Details: WORKLOG, 2026-10-21 (late, 5).

The audit list below was worked through in a second pass, and a third
pass then grilled THE FIXES THEMSELVES (five adversarial clusters over
commits 8258642..043dbe9) — which found nine real regressions, all fixed
same-day (9997adf..2641b77, one idea per commit, each with its own
proof; see WORKLOG). What is STILL open, ranked:

- ~~**The OBS unit render is unproven on a REAL GPU-less box.**~~ The
  lab-shaped `station-obs.service` defect is fixed in code (2026-10-21):
  `setup.sh` now renders the installed unit per box — headless → Xvfb
  `:99` + `--env=LIBGL_ALWAYS_SOFTWARE=1`, session-without-GPU → `:0` +
  software GL, lab → untouched — and creates `global.ini` with
  `BrowserHWAccel=false` when it does not exist yet (first boot used to
  skip the guard and die of the CEF GPU-process crash). Verified by a
  render harness against the real unit text for all three box shapes.
  **PROVEN 2026-10-22:** the headless unit IS the GPU-less shape
  (Xvfb :99 + `LIBGL_ALWAYS_SOFTWARE=1`). The plane booted under it, the
  programme output came up, and a frame pulled off the bus carried the
  real picture -- the fail-safe's test pattern, the watermark and the
  ticker -- not black. The output is 960x540 (the canvas is 1920x1080 and
  the output scales it), which is the light build's resolution. (What is
  still unproven is a REAL VPS: the box itself, with its own X server
  and a real network path -- `docs/VPS.md` §6.)
- **The station used to stay black when the plane came back** — FIXED
  2026-10-22. Four causes, all in the poll loop and the boot: the
  programme output was only created at boot; the plane-down hold was
  not a HOLD (no marker), so nothing re-attempted the advance; a dead
  STANDING websocket was treated as a dead PLANE (PLANE_DOWN on every
  pass, advance() refusing to play, with the plane up and well); and
  the resume cleared the flag AFTER calling advance(). Proven live:
  daemon booted with the plane off, the plane came back, the station
  resumed by itself and the frame on the bus carried a real picture.
- **Stopping the plane did not stop the plane** — FIXED 2026-10-22: OBS
  ignores SIGTERM with no window manager, so the unit went inactive
  while the old process kept holding :4455 and 14 CEF browser pages
  stayed resident. The unit's stop now escalates to SIGKILL and reaps
  them; proven live (the port closes, no process remains).
- **The TD-desk/VNC unit is session-shaped.** `station-vnc.service` runs
  wayvnc, which mirrors a Wayland session — correct on the lab desktop,
  useless on a VPS (none exists; setup.sh now skips installing it
  there). The headless recipe is documented in `docs/VPS.md` §6
  (x11vnc on the Xvfb `:99` over an SSH tunnel) but ships no unit yet.
- ~~**config/collection.json: the scene NAMES are fixed, the CONTENT
  still wants a re-capture.**~~ — DONE 2026-10-22: the content was
  re-captured from the live plane and `sync.py diff` now says "repo
  matches live (no drift)". The capture had fallen behind in ways that
  mattered for a fresh install (the VPS): it had NO loudness chain (the
  operator's global compressor + limiter), no contribution seats
  (Slot Cam/Screen/Audio), and three of the nine scenes (Ad Break,
  Ticker, Watermark) were missing -- an apply would have been REFUSED,
  and a fresh box would have had no loudness at all. The capture also
  needed a fix of its own: a deck input's file is RUNTIME state (the
  daemon points it at the item it is about to play), so the capture now
  writes the fail-safe template instead of a transient spool path. The capture in git had `SMILE | Meet` while the
  live plane has `SMILE | Program` (renamed on the plane after the
  capture). Fixed 2026-10-22: the capture, the collection TEMPLATE
  (`station/scenes.json.template` — the thing the rendered collection is
  built from) and `render_scenes.py`'s structural check all say
  `SMILE | Program` now, so the capture covers exactly the six scenes
  the daemon drives and `sync.py apply` no longer refuses. The apply
  still REFUSES a capture that lacks any scene the daemon drives —
  before touching OBS, with the fix spelled out — because that is what
  would have created a duplicate scene and orphaned the live one; and
  the diff no longer reports a media source's `settings.local_file`
  (runtime state, like the deck's eye state). What remains needs the
  plane: re-capture the CONTENT (`python3 station/sync.py capture`),
  because the item settings in the capture may have drifted since
  October. (The plane is currently switched off at the operator's
  request, so this cannot be done yet.)
- **The OBS -> bus leg is FIXED and PROVEN (2026-10-22).** The live
  render plane had NO output at all (only a file output), so the finished
  programme never left OBS: MediaMTX's monitor path was never fed and
  the programme was black to everyone downstream -- the original
  "preview has content, program is black" report. The daemon now brings
  the output up at boot with StartStream (this ws build has no
  CreateOutput request) pointing at the LOCAL bus, and it restarts the
  output when a plane restart leaves it stopped. Proven live: 143 video
  frames and 262 audio frames read back from
  `rtmp://127.0.0.1:1935/monitor` at 960x540.
  **Still open:** the bus -> YouTube leg has never run against YouTube's
  own endpoint -- that is the operator's cutover (see DECISIONS §13).
  The leg's PLUMBING is now proven (2026-10-22): with the destination
  overridable (`PUBLISH_DEST`), the leg pulled the programme off the
  bus and pushed it, `-c copy`, into a local RTMP sink -- video
  (h264) and audio (aac) crossed unchanged. The only untested step is
  YouTube's handshake with a real key.
- **plane_call is a deadline, not a bound** — FIXED 2026-10-21 to the
  extent Python can: every plane_call takes a generation and the
  renderer refuses an RPC older than one that already sent (the guard
  lives inside the plane lock, so a stale RPC cannot slip between its
  check and its send). A timed-out MULTI-RPC sequence (an intent,
  ensure_bed) now dies "superseded" instead of landing its tail over a
  newer intent — the "late cut overrides a retry" shape is gone
  (test_plane_guard.py pins it). What remains, inherent: a single RPC
  already in flight server-side when its deadline hits will still
  complete — nothing of that call follows it, and the daemon's
  reconcile pass re-forces visibility/mutes at the next cut, so the
  residue is one request that landed late, not a sequence that
  overrode newer intent. Real cancellation would need cooperative
  checkpoints inside every call; not worth it at this blast radius.
- **stream respawn residual races (fixed 2026-10-21, narrowed not
  erased)**: the old defect — resolve+spawn+ready-wait inline INSIDE the
  playout pass, a dead network freezing the deck ~4 min per attempt — is
  fixed: `stream_respawn_pass` detects, counts and kicks; the slow work
  runs on one background thread per deck (`_respawn_work`) with
  proc-identity cleanup. What remains, bounded: (1) a give-up EOF is
  relevance-checked in the thread right before it is queued, so an
  operator skip landing inside the following ~1-poll window can still
  let a stale EOF advance one extra item (the consumer now refuses EOFs
  with no stream on air, which kills the common case; the
  stream->stream case would need the url carried in the sentinel);
  (2) a stale EOF for an AD slot arriving just after `ad_return` could
  advance once — pre-existing (the bare sentinel cannot name its item),
  and the thread-side relevance check means the NEW code creates none.
- ~~**duplicate media: the marker lights the first twin**~~ — FIXED
  2026-10-22: identity alone cannot say WHICH copy of a duplicated
  item is on air, so the lookups carry the ORDINAL (how many rows with
  that identity come before the saved slot). The marker now lands on the
  copy the station is actually playing, and the NEXT cue does the same.
- **dock small print**: CLOSED (2026-10-22). The staged bar now keys on
  the PENDING state, not the history depth, so it can no longer say "N
  changes staged" while Apply would refuse (net-zero edit sequences);
  the NEXT-marker walk now skips the same classes the daemon skips
  (parked, pending, nameless, a file that is not on disk) instead of
  only parked rows, so the marker cannot light a row the daemon will
  walk past; and the row rebuild is linear again (the on-air identity
  scan and the next-item walk are computed once per rebuild, not once
  per row: 41,209 key comparisons -> 22).
- ~~**intake workdir sweep: a recycled pid keeps a dead workdir up to
  24 h**~~ — FIXED 2026-10-22: the workdir now names its process's
  START TIME as well as its pid (`/proc/<pid>/stat` field 22), and the
  sweep only trusts a pid whose start time still matches. A recycled pid
  can no longer keep a dead workdir (or hand a fresh job the stale raws
  of a dead one). `station/test_intake_sweep.py` pins all four cases.

## Fixed same-day (2026-10-21) — kept here until the next doc pass

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

## Earlier findings (kept for the record)

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

### The Xvfb display `:99` is vestigial on the lab box (load-bearing on a VPS)

OBS moved to the real session (`:0`) for hardware GL, so on the lab
desktop `station-xvfb.service` renders nothing and costs a little RAM.
It stays: `station-obs.service` still `Requires=` it, and on a headless
VPS the plane IS `:99` (setup.sh renders the unit onto it — see the top
of this file). Do not delete it.

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

## Closed since the last round (kept here so nobody re-investigates them)

- **The unit render never reached four units** (panel, overlay,
  watchdog, mediamtx had no `Environment=` line, so the BROADCAST_ROOT
  injection was a no-op and mediamtx's `${BROADCAST_ROOT}/mediamtx.yml`
  expanded to `/mediamtx.yml` — the ingest bus never started on a fresh
  install). Fixed: the render inserts the line into `[Service]` and
  fails loud when a unit expands a variable it never defines. The
  render moved to `station/render_units.sh` so
  `station/test_unit_render.py` can run the real thing.
- **The daemon's opening cut consumed the queue while the plane was
  off**: the "hold" flag was only set by the poll loop's gate, which has
  not run at boot. Fixed: the hold is armed before the opening cut, and
  the fault watchdog does not count a deliberately-absent plane as a
  fault (it used to escalate to OFF-AIR and fail to cut every pass).

## Closed 2026-10-22 (battle test with the plane up)

- **The station ate its own playlist** when YouTube was slow: every
  resolve timed out, every link was called "unplayable" and SKIPPED.
  Now a resolve failure is classified: permanent (the video is gone) ->
  skip; transient (timeout, bot check, network) -> HOLD the queue. A run
  of dead links is capped at 3 per pass.
- **The programme went black while the station waited.** The fail-safe's
  holding card now takes the air whenever nothing of the programme is
  visible.
- **The watchdog faulted the station for waiting** (OFF-AIR while
  holding for a link). A deliberate hold is not a stall.
- **The operator's commands waited behind a 45s resolve.** The control
  channel now runs first in the pass.
- **The "plane is wedged" mystery**: a client that upgrades the
  websocket and never reads its greeting blocks EVERY later handshake
  (proved by experiment) -- and the daemon's own failed boots were
  creating the stuck clients. The client now closes deterministically on
  any handshake failure, the boot timeout went 8s -> 20s, and three
  greetings in a row that never came now restart the plane.

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

- ~~**Per-item preview panel** (operator's Q5)~~ — DONE 2026-10-21:
  clicking a row opens a card with the poster frame (new
  `/api/thumb` proxy on the panel), the real title, the description, the
  source and how fresh the metadata is, with a manual "refresh
  metadata" button (`{"refresh": {"url": ...}}` verb) and a daily full
  metadata sweep in the title watcher. The sweep is FIXED too
  (2026-10-22): it now reaches every row instead of re-resolving the
  same ones for ever, so a fresh import's description arrives with the
  sweep rather than waiting for a manual press.
- ~~**Scheduled profiles** (day/night running orders switching on a clock).~~
  DONE 2026-10-22: `broadcast/schedule.json` holds the switches, the
  daemon applies them (a missing or EMPTY profile is refused, the same
  switch cannot fire twice in a day, the replaced order is kept as
  `before-switch`), and the dock shows the next one. Proven live.
- ~~**A queue timeline / playhead**~~ — DONE 2026-10-22 (the Studio
  Player pattern): the dock now draws a RUNNING ORDER strip under the
  header — one tile per queued item, the playhead on the item that is on
  air, the next one in amber, the played ones struck through, and a
  click on a tile selects that row and opens its preview. It is bounded
  to a window of 24 tiles around the playhead.
- ~~**Bulk review of amber rows**~~ — DONE 2026-10-22: the dock shows a
  review bar when rows are flagged ("N videos renamed on YouTube") with
  approve-all / discard-all, staged like every other edit.
- ~~**The daily metadata sweep**~~ — DONE (it was already running; it
  captures the description, the channel and a checked-at stamp for the
  items it visits). FIXED 2026-10-22: the sweep never actually swept
  (8 of 201 rows after days — it re-resolved the same rows for ever),
  because a VOD's resolve was never cached and the pass always started
  at the top. It now caches every resolve and keeps a cursor, so it
  reaches every row and survives a restart.

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
