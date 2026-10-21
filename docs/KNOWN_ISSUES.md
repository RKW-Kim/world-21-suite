# Known issues

What is still broken, what is deliberately not done, and what is stale.
Ordered by how much it matters.

---

## Open defects (after the 2026-10-21 regression pass)

The audit list below was worked through in a second pass, and a third
pass then grilled THE FIXES THEMSELVES (five adversarial clusters over
commits 8258642..043dbe9) — which found nine real regressions, all fixed
same-day (9997adf..2641b77, one idea per commit, each with its own
proof; see WORKLOG). What is STILL open, ranked:

- **The OBS unit render is unproven on a REAL GPU-less box.** The
  lab-shaped `station-obs.service` defect is fixed in code (2026-10-21):
  `setup.sh` now renders the installed unit per box — headless → Xvfb
  `:99` + `--env=LIBGL_ALWAYS_SOFTWARE=1`, session-without-GPU → `:0` +
  software GL, lab → untouched — and creates `global.ini` with
  `BrowserHWAccel=false` when it does not exist yet (first boot used to
  skip the guard and die of the CEF GPU-process crash). Verified by a
  render harness against the real unit text for all three box shapes.
  What is NOT yet proven: an actual llvmpipe boot with real air. That is
  step 3 of the `docs/VPS.md` migration order — bring up the plane alone
  and check it renders at the intended size before anything airs.
- **The TD-desk/VNC unit is session-shaped.** `station-vnc.service` runs
  wayvnc, which mirrors a Wayland session — correct on the lab desktop,
  useless on a VPS (none exists; setup.sh now skips installing it
  there). The headless recipe is documented in `docs/VPS.md` §6
  (x11vnc on the Xvfb `:99` over an SSH tunnel) but ships no unit yet.
- **config/collection.json staleness**: `sync.py apply` would create a
  duplicate `SMILE | Meet` scene and restart the on-air deck source
  mid-item; the deck diff only hides `.enabled`, not
  `settings.local_file`, so diff is perpetually noisy and trains the
  operator to ignore drift.
- **station has never published to YouTube end-to-end** (the publish
  leg is deliberately disarmed; see DECISIONS §13). First real cutover
  run is its own checklist.
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
- **duplicate media: the marker lights the first twin** (cosmetic): the
  protection now covers every row with the on-air identity (1f05f41),
  but the green bar itself still picks the first twin when the station
  plays the second. Fixing the marker means teaching onAirIdx the saved
  slot's ordinal — it also feeds insert points, so it wants its own
  change + harness.
- **dock small print**: the staged bar can say "N changes staged" while
  Apply refuses (net-zero edit sequences); the NEXT-marker walk skips
  only dormant rows (the daemon also skips failed-resolve/cache-miss/
  source-only, so the marker can drift or light a source-only twin);
  row rebuild re-derives both markers per row (O(n²) at 200 rows,
  measurable, not fatal).
- **intake workdir sweep: a recycled pid keeps a dead workdir up to
  24 h** (the mtime escape eventually reaps it; bounded, cosmetic).

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
