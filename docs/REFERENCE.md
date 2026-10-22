# Reference

Lookup tables. Regenerate the file:line references when the code moves
substantially.

---

## 1. Environment variables

### Daemon (`station/daemon.py`)

| Variable | Default | Controls |
|---|---|---|
| `BROADCAST_ROOT` | `<cwd>/broadcast` | The live-state root: media, playlist, state, knobs, control, heartbeat, activity DB. |
| `OBS_HOST` / `OBS_PORT` | `127.0.0.1` / `4455` | The render plane's obs-websocket. |
| `OBS_PASS` | — | obs-websocket auth secret (SHA-256 challenge). |
| `OBS_TIMEOUT` | `60` | Seconds for a websocket connect/read. |
| `OBS_READY_TRIES` | `12` (unit: `60`) | Boot attempts before giving up on the plane. |
| `WATCH_POLL` | `4` (unit: `2`) | Seconds between poll passes. |
| `PLANE_DOWN_SECS` | `600` | Silence tolerated before the plane is restarted. |
| `PLANE_RESTART_COOLDOWN` | `1800` | Minimum spacing between plane restarts. |
| `STREAM_PRIME_LEAD` | `30` | Seconds before a stream ends to spawn the next one. |
| `TITLE_WATCH_SECS` | `300` | Interval of the YouTube rename watcher. |
| `TRANSITION` | `Fade` | The OBS transition used for cuts. |
| `CACHE_CAP_BYTES` | 50 GiB | Cap for `broadcast/media/*.mp4`. |
| `DISCORD_WEBHOOK` | — | Alert channel. Unset = log only. |
| `YOUTUBE_STREAM_KEY` | — | Real key ⇒ the station creates its RTMP output and expects to publish. |

### Other modules

| Variable | Where | Controls |
|---|---|---|
| `PANEL_PORT` | `panel.py` | The panel's port (default 8220). |
| `BIND` | `overlay_server.py` | Overlay bind address. `0.0.0.0` exposes the control plane — do not. |
| `STATION_TOKEN` | `overlay_server.py` | Bearer token for the control plane. Set it on any WAN-reachable box. |
| `YTDLP_COOKIES` | `stream.py`, `intake.py` | `cookies.txt` path or `browser:<profile>` for yt-dlp. |
| `FFERR_PATH` | `stream.py` | Where a feed's ffmpeg stderr goes. |
| `SPOOL_LOUDNORM` | `spool.py` | `0` = no loudness pass at intake. |
| `INTAKE_MIN_FREE_BYTES` | `intake.py` | Free disk required before intake starts. |
| `PLANE_DISPLAY` | `obs_click.py` | The X display the render plane lives on (`:0`). |
| `OVERLAY_URL`, `STATION_PROFILE`, `STATION_COLLECTION`, `LAB_LIGHT` | `sync.py`, `render_scenes.py` | Configuration sync and rendering. |
| `OBS_RELAY_SNIFF` / `_FULLSNIFF` / `_RPCLOG` | `overlay_server.py` | Debug logging for the websocket relay. |

`broadcast/secrets.env` holds `YOUTUBE_STREAM_KEY`, `OBS_PASS`,
`DISCORD_WEBHOOK`, `TG_TOKEN`, `TG_CHAT`, `YTDLP_COOKIES`. It is sourced
into the environment with `setdefault`, so an exported variable wins.

## 2. HTTP endpoints

### Panel — `127.0.0.1:8220`

| Method | Path | Body | Effect |
|---|---|---|---|
| GET | `/api/state` | — | The merged truth: playlist, state, knobs, spool, titles, daemon health, loudness switch, dock version. ~58 KB. |
| GET | `/api/ping` | — | ~200 bytes: a version stamp + daemon health + loudness + dock version. **The dock polls this.** |
| GET | `/api/playlists` | — | Saved profile names. |
| GET | `/api/schedule` | — | The configured profile switches, the next one (`{at, profile, in_s}`) and the saved profile names. |
| GET | `/dock` | — | The dock UI, with `window.__DOCK_VERSION__` stamped in. |
| POST | `/api/save` | `{playlist, knobs}` | Write the playlist (under the station lock) and the knobs. |
| POST | `/api/state` | `{state:{index,...}}` | Patch the cursor (under the station lock). |
| POST | `/api/restart` | `{unit}` | Restart `station-daemon.service` or `station-obs.service`. |
| POST | `/api/playlists` | `{action:save\|load\|delete, name, playlist?}` | Profiles. `load` **returns** the profile; it does not apply it. |
| POST | `/api/control` | `{skip}`, `{media:{action,db}}`, `{normalize:{file\|url\|global}}` | Control verbs, merged into `broadcast/control.json`. |
| POST | `/api/ytpl` | `{url}` | Import a YouTube playlist (titles only, no downloads). |

### Overlay server — `127.0.0.1:7070`

| Method | Path | Purpose |
|---|---|---|
| GET | `/state` | The overlay's own state file. |
| GET | `/events` | SSE stream of state pushes (25 s heartbeat). |
| GET | `/files/<name>` | Range-capable media from `broadcast/media/`. |
| GET | `/thumbs/<name>` | A generated poster frame. |
| GET | `/library`, `/ads`, `/intake`, `/music`, `/monitor`, `/obs/meters`, `/tap.mjpeg` | The other surfaces' data. |
| GET | `/whip` | The contribution-seat publisher page. |
| POST | `/intent/<name>` | `scene`, `go-live`, `tech-diff`, `resume`, `return`. |
| POST | `/library`, `/ads`, `/obs`, `/music`, `/state`, `/whep` | The control plane. |

Guard: no `Origin` header ⇒ allowed (ssh, curl, systemd); `Origin: null`
⇒ allowed unless `STATION_TOKEN` is set; otherwise the origin must match
the host; a bearer token always passes. Otherwise: **403**.

## 3. Knobs

Written by the panel to `broadcast/knobs.json`; applied by the daemon every
pass (`KNOB_KEYS`) and read directly by the spooler (`STREAM_SPOOL_*`).

| Knob | Default | What it changes |
|---|---|---|
| `FEED_WAIT` | 4 s | How long a deck has to reach OPEN/PLAYING before the fail-safe takes over. |
| `STREAM_GRACE` | 8 s | Slack past a stream's true duration. |
| `STREAM_SPAWN_TRIES` | 15 | 3-second polls for a live publisher before the spawn fails. |
| `STREAM_PRIME_LEAD` | 30 s | How early the next stream is spawned. |
| `REPEAT_LIMIT` | 3 | Faults in an hour before the station goes off-air. |
| `WATCH_POLL` | 4 s (unit 2) | Poll cadence. |
| `PLANE_DOWN_SECS` | 600 s | Silence before the plane is restarted. |
| `PLANE_RESTART_COOLDOWN` | 1800 s | Minimum spacing between plane restarts. |
| `STREAM_SPOOL_AHEAD` | 1 | Items pre-downloaded ahead of the playhead. |
| `STREAM_SPOOL_MAX_GB` | 3 | Spool cache cap (also yt-dlp's `--max-filesize`). |
| `STREAM_SPOOL_KEEP_HOURS` | 48 | How long a cached copy survives. |

Clamps: values must be numeric and ≥ 0; everything else is clamped to
0.5…3600 (integers ≥ 1 for `REPEAT_LIMIT`). Unknown keys are ignored.

## 4. Units

| Unit | Does | Restart | Notes |
|---|---|---|---|
| `station-daemon.service` | The brain. | always / 15 s | `Wants=` the plane (never `Requires=`). |
| `station-obs.service` | The render plane (OBS flatpak on `:0`). | always / 20 s | `LIBGL_ALWAYS_SOFTWARE` must NOT be set. |
| `station-panel.service` | The operator surface. | always / 5 s | Loopback only. |
| `station-overlay.service` | Graphics + control plane. | always / 5 s | |
| `station-mediamtx.service` | The ingest bus. | always / 5 s | |
| `station-xvfb.service` | A spare display on `:99`. | always / 5 s | Vestigial. |
| `station-vnc.service` | `wayvnc` mirror of the session. | always / 10 s | Needs the user-session Wayland env. |
| `station-watchdog.service` + `.timer` | Revives the station every 5 min. | oneshot | |
| `station-publish.service` | The YouTube publish leg. | always | **Not enabled by default.** |

## 5. Ports

| Port | Owner | Purpose |
|---|---|---|
| 8220 | panel | The operator surface (loopback). |
| 7070 | overlay server | Graphics, SSE, control plane (loopback unless `BIND` is changed). |
| 4455 | OBS | obs-websocket v5. |
| 1935 | MediaMTX | RTMP ingest (`monitor`, `slot-stream-a/b`, `slot-ad`, the seats). |
| 9997 | MediaMTX | Control API (loopback). |
| 8888/8889/8892/8893 | MediaMTX | HLS, WHIP/WHEP, WebRTC UDP. |
| 9000 | MediaMTX | SRT ingest (the seats push here). |
| 5900 | wayvnc | The desktop mirror. |

## 6. On-disk formats

### `broadcast/media/playlist.json`

Top level: `items` (the order), `shuffle_on_complete`, `idents`,
`ad_every`, `ad_plan{threshold_min,mid_rolls,min_gap_min,enabled}`,
`ad_files`, `ad_links`, optional `fallback` (the fail-safe pool).

Per item: `youtube` | `file`, `title`, `duration`, `status`
(`active`/`dormant`), `source`, `show`, `pinned`, `spool`, `id`,
`meta_trip{old,new,same_video}`, `group`, `gorder`, `tab`
(`video`/`music`), `played`.

### `broadcast/schedule.json`

The profile switches, on a clock:

```json
{"switches": [{"at": "06:00", "profile": "morning"}]}
```

`at` is a local `HH:MM`, `profile` the name of a saved profile in
`broadcast/media/playlists/<profile>.json`. The daemon applies the
profile when the clock passes `at` (within a five-minute window, at the
next cut). Guards: the profile must exist and must not be empty (an
empty profile would blank the station); the same switch cannot fire
twice in a day; the order the switch replaced is kept as the
`before-switch` profile so it can be loaded back from the dock.

The file may be absent or broken — the station then simply has no
switches.

### `broadcast/state.json`

`index` (1-based, the **next** item), `deck` (`A`/`B`/`C`), `stream`,
`stream_pre`, `roll_marks`, `next_roll`, `marks_for`, `since_ad`,
`fallback_air`, `fallback_idx`, `just_played`, `deck_volume_db`,
`deck_paused`, `schedule_last` (the switch that already fired today),
`faults`, `in_ad_break`, `ad_mid`, `ad_start`,
`onair{src,pos_ms,dur_ms,state}`.

### `broadcast/knobs.json`, `normalize.json`, `heartbeat.json`, `control.json`

Flat maps, except `heartbeat.json` = `{t, pass_ms, busy}` and
`control.json` = `{skip?, media?, normalize?, probe?}` (rewritten empty
after each daemon pass).

### `broadcast/activity.db`

SQLite: `activity_log(ts TEXT, level TEXT, msg TEXT)`, WAL, capped at
5,000 rows. Levels `INFO`/`WARN`/`CRIT`.

### `spool/` naming

`key = sha1(url)[:20]`.

| File | Meaning |
|---|---|
| `<key>.mp4` | Complete and OBS-safe. The only name `ready()` blesses. |
| `<key>.dl.<pid>.<ext>` | The raw download (not blessed; process-unique). |
| `<key>.dl.<pid>.f<id>.<ext>.part` | A resumable per-format partial. |
| `<key>.fs.<pid>.mp4` | The faststart/loudnorm temp. |
| `<key>.title` | `{"title": "..."}` sidecar. |
| `<key>.noaudio` | This selector produced silence; never retry it. |

## 7. Scenes and inputs

Scenes: `SMILE | Program`, `SMILE | Starting`, `SMILE | Q&A`,
`SMILE | Tech Diffs`, `SMILE | Off Air`, `SMILE | End Credits`,
`SMILE | Ad Break`, plus the nested `SMILE | Ticker` and
`SMILE | Watermark`.

Inputs: `PLAYOUT_A`, `PLAYOUT_B` (file decks), `PLAYOUT_C` (fail-safe),
`STREAM_A`, `STREAM_B` (live feeds), `AD Break`, `STREAM AD`, `IDENT`,
`Music Bed` (waiting-room scenes only).

## 8. Tests

| Command | Covers |
|---|---|
| `bash station/selftest.sh` | **Everything below, one command.** The list in the script is the canonical suite. |
| `python3 station/test_spool.py` | Spool states, the blast-rate exits, eviction, the audio guard. |
| `python3 station/test_fallback.py` | The fail-safe: healthy decks, a stalled deck, the loop_a→loop_b roll, TECHDIFF when the pool runs out. |
| `python3 station/test_playlist_edges.py` | The index truth table, the up-next scan, degenerate playlists, the shuffle seam (stream items included). |
| `python3 station/test_stream_respawn.py` | The background respawn: the pass never blocks, one attempt per deck, EOF exactly once, proc-identity cleanup. |
| `python3 station/test_control_consume.py` | The control write-back: verbs pop by value, no resurrection, no double execution. |
| `python3 station/test_overlay_auth.py` | The control-plane guard: STATION_TOKEN tiers, Origin rules, compare_digest. |
| `python3 station/test_plane_guard.py` | plane_call generations: the stale tail of a timed-out sequence dies superseded. |
| `python3 station/daemon.py selftest` | Offline: overlay repair, advance, ident routing, dormants, corrupt state, cache eviction, the watchdog. |
| `python3 station/stress_cache.py` | The cache-eviction battery on a tmpfs. |

There is no pytest. They are stdlib scripts and they exit non-zero on
failure. **Point `daemon.DB` at a temp file in any new test** — the live
activity log is the operator's evidence trail.

## 9. Git

Branch `main`; remote `origin` (GitHub). The work is committed on `main`
and pushed in batches; work-in-progress goes on a branch with a PR. The
live state is gitignored, so a clone has no `broadcast/` and no `spool/` —
that is correct: those belong to the machine, not the repository.
