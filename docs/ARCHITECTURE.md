# Architecture

How the station fits together. Read this after `AGENTS.md`.

---

## 1. The shape of it

```
                    ┌──────────────────────────────────────────┐
                    │  render plane: OBS (flatpak) on :0       │
   operator ──────▶ │  PROGRAM ─ deck A/B (files) + C (fail)   │
   (dock :8220)     │           + STREAM_A/B (live) + overlays │
                    │  obs-websocket v5 on :4455              │
                    └───────────────┬──────────────────────────┘
                                    │  (one long-lived ws connection)
                    ┌───────────────▼──────────────────────────┐
                    │  daemon: the brain                       │
                    │  poll loop · advance() · watchdog        │
                    │  spooler · title watcher · fail-safe     │
                    └───┬──────────────┬───────────────┬───────┘
                        │              │               │
              ┌─────────▼───┐  ┌───────▼────────┐  ┌──▼──────────────┐
              │ spool/       │  │ MediaMTX :1935 │  │ broadcast/      │
              │ YouTube      │  │ the ingest bus │  │ playlist,state, │
              │ cache        │  │ slot-stream-a/b│  │ knobs,activity  │
              └──────────────┘  └───────┬────────┘  └────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │ overlay server     │
                              │ pages + SSE :7070  │
                              └────────────────────┘
```

Three processes, three jobs, one shared directory of truth (`broadcast/`).

| Process | Unit | Port | Job |
|---|---|---|---|
| The brain | `station-daemon.service` | — | Decides what plays, cuts OBS, watches for faults, keeps the cache warm, notices renames. |
| The render plane | `station-obs.service` | 4455 | Draws the picture. Knows nothing about playlists. |
| The operator surface | `station-panel.service` | 8220 | Serves the dock and takes the verbs the dock sends. |
| The graphics | `station-overlay.service` | 7070 | Serves the overlay pages OBS renders, pushes state to them over SSE, and hosts the control plane for the other surfaces. |
| The bus | `station-mediamtx.service` | 1935/9997 | Carries live streams between the feed spawner and OBS. Zero disk. |
| The revive | `station-watchdog.timer` | — | Every 5 minutes: is the station alive, and can we restart what is not. |
| The GUI bridge | `station-vnc.service` | 5900 | Mirrors the desktop session (for a headless box). |

## 2. The playout loop

`cmd_loop()` runs one pass every `WATCH_POLL` seconds (the unit sets 2 s):

1. **Apply knobs** — `broadcast/knobs.json` overrides, clamped, every pass.
2. **Reachability gate** — a cheap ping on the standing OBS connection; every
   30th pass a full Hello probe. Sustained silence ⇒ restart the plane
   (after `PLANE_DOWN_SECS`, at most once per `PLANE_RESTART_COOLDOWN`).
3. **Playlist reload** — mtime + content hash. Human edits take effect at
   the next transition, never mid-air.
4. **Drain the end queue** — sources that reported `ENDED` (event or poll
   detection) go through `on_ended()`.
5. **Operator commands** — `broadcast/control.json`: skip, transport, mixer,
   loudness, probe. Consumed and rewritten empty, so one POST fires once.
6. **Stream lifecycle** — wall-clock ends, feed health, respawn (twice), then
   the item ends.
7. **Fault watchdog** — a stalled deck escalates: fail-safe, then Tech
   Diffs, then Off Air, and after `REPEAT_LIMIT` faults in an hour it stops
   and waits for a human.
8. **Ad gate** — mid-rolls and scheduled breaks fire at the planned marks.
9. **Prefetch** — keep the next link item warm in the spool.

### Cutting an item (`advance()`)

```
pick the next item (skipping dormant and pending ones)
  → if it is a link: use the local copy if there is one, else resolve + stream
  → if it is a file:  point the idle deck at it and restart it
  → show it, hide the others, RE-READ the scene and force the truth
  → park the idle deck (muted + paused)
  → apply the operator's mixer value
  → wait for READY; if it never comes up → FAILOVER (PLAYOUT_C)
  → transition, publish the new state, mark the item played
```

`advance()` is a loop, not recursion: a fully missing playlist ends on Tech
Diffs, not in a `RecursionError`.

### The fail-safe

When the new deck does not reach OPEN/PLAYING inside `FEED_WAIT` (4 s), the
station cuts to `PLAYOUT_C`, which holds `loop_a.mp4` and then `loop_b.mp4`.
When that file ends, the same `advance()` runs again: either a deck has
recovered (and the fail-safe is cleared) or the next fallback file plays.
When the fallback files run out, the station holds Tech Diffs. It never
goes black.

## 3. The OBS model

Scenes: `SMILE | Program` (the programme), `SMILE | Starting` (ident),
`SMILE | Q&A` (live segment), `SMILE | Tech Diffs` (fault card),
`SMILE | Off Air` (harbour), `SMILE | End Credits`, `SMILE | Ad Break`, plus
the nested overlay scenes `SMILE | Ticker` and `SMILE | Watermark`.

Inputs the daemon drives:

| Input | Role |
|---|---|
| `PLAYOUT_A` / `PLAYOUT_B` | The two file decks. One is on air, the other is loading. |
| `PLAYOUT_C` | The fail-safe. Never in normal rotation. |
| `STREAM_A` / `STREAM_B` | Live YouTube feeds, published by ffmpeg into MediaMTX and read back with `restart_on_activate`. |
| `AD Break` / `STREAM AD` | The ad slot: a local file or a streamed link. |
| `IDENT` | The ident clip in the Starting scene; its END cuts to Q&A. |
| `Music Bed` | The waiting-room bed (overlay server's, kept out of Programme by the daemon). |

The daemon talks to OBS over obs-websocket v5 with a hand-rolled client
(`daemon.py`, no third-party dependency). It keeps **one** long-lived
connection: fresh handshakes are slow and the server does not always greet
new clients, so a new connection per call is how the station used to wedge
itself.

## 4. The data files

Everything live lives under `broadcast/` and is gitignored.

| File | Written by | Read by |
|---|---|---|
| `media/playlist.json` | the dock (Apply), the daemon (its own shuffle) | the daemon, the dock |
| `state.json` | the daemon, the panel (index pin) | the daemon, the panel, the dock |
| `knobs.json` | the panel | the daemon (every pass), the spooler |
| `control.json` | the panel | the daemon (one pass, then cleared) |
| `heartbeat.json` | the daemon (its own thread) | the panel → the dock |
| `activity.db` | everyone (SQLite, WAL) | the panel, the dock, you |
| `normalize.json` | the daemon | the panel → the dock (the loudness switch) |
| `obs_probe.json` | the daemon (`{"probe": true}`) | you |
| `media/playlists/<name>.json` | the dock (Save profile) | the dock (Load) |
| `spool/` | the spooler | the daemon (local copies) |

Two locks matter:

- **`daemon.pl_lock()`** — a cross-process `flock` on
  `broadcast/.station.lock`. Every read-modify-write of `playlist.json` or
  `state.json` takes it. Without it, the daemon and the panel race.
- **`daemon.lock`** — held by the running loop; refuses a second driver.

## 5. The dock

One file (`station/dock.html`), no build step, no dependencies. It polls
`/api/ping` every 2 s and only fetches the full state when the version
stamp moves. It **stages** edits locally and sends them to the station only
when the operator presses Apply — see `docs/DECISIONS.md` §1.

The list is only rebuilt when its content changes: a full rebuild of 200+
rows cost 40 ms every 2 s inside the OBS process, and it destroyed focus,
drags and the operator's cursor.

## 6. The media path

Two kinds of item:

- **A local file** in `broadcast/media/` — played straight by OBS.
- **A YouTube link** — two paths:
  - *spooled*: downloaded in the background (yt-dlp), loudness-normalised
    (two-pass EBU R128, −16 LUFS, −1.5 dBTP) and faststarted, then played
    from disk. This is the default, and it is what makes cuts reliable.
  - *streamed*: resolved live and published into MediaMTX, then read by the
    `STREAM_A/B` inputs. Zero disk, but a network hiccup can freeze a frame
    (mitigated by an ffmpeg I/O timeout and a respawn).

The spooler keeps one item ahead of the playhead
(`STREAM_SPOOL_AHEAD`), caps the cache (`STREAM_SPOOL_MAX_GB`) and ages it
out (`STREAM_SPOOL_KEEP_HOURS`). Duplicates of a URL share one key
(`sha1(url)[:20]`).

## 7. The audio path

Three layers, and they are deliberately separate:

1. **Intake** — a spooled item is loudness-normalised to −16 LUFS on the
   way in (`spool.py`, two-pass linear mode).
2. **The station chain** — compress (−16 dB, 3:1) + limit (−1.5 dBTP) on
   every playback input, so raw links and studio cards sit together. It is
   one switch for the whole station (`broadcast/normalize.json`), not a
   per-item setting.
3. **The mixer** — the operator's dB value per deck, remembered across
   cuts (`state.deck_volume_db`).

## 8. Failure model

| Failure | Who catches it | What happens |
|---|---|---|
| The render plane dies | The daemon's gate, then the watchdog | The plane restarts; the daemon keeps its state; the programme resumes. |
| The daemon dies | `station-watchdog.timer` | The daemon restarts within 5 minutes and re-reads the state. |
| A deck stalls | `advance()` | The fail-safe takes the air, then the next fallback file, then Tech Diffs. |
| A file is missing | `advance()` | The item is skipped with a warning; the next one plays. |
| A link is dead | `spool` / `stream` | The item is skipped, or the feed respawns (twice), then the item ends. |
| A video is renamed on YouTube | The title watcher | The row is flagged (amber). If the duration changed, it is held back; if only the title changed, it keeps playing. |
| The disk fills | The spool eviction, the intake guard | The oldest unpinned copies go; intake refuses to start. |
| The panel dies | The watchdog | The panel restarts; the dock reconnects by itself. |
| The operator closes the browser | — | The dock is a view, not a controller: the station keeps playing. |
