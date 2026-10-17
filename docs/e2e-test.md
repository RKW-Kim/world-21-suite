# E2E: compressed-time proof (no 2-hour waits)

The loop is proven practically, not just by reading code: short clips
stand in for long videos, the daemon runs the real automation, and every
claim below was observed live (journal timestamps + RPC state).

## Rig (OBS + daemon + local files only)

No overlay, no MediaMTX, no /studio involved. Two processes, one box:

- OBS render plane, SMILE collection + one RPC-created `SMILE | Ad Break`
  scene (`AD Break` ffmpeg input). Removed after the run.
- Daemon loop with a throwaway playlist (real `broadcast/playlist.json`
  and `state.json` backed up first, restored after).

## Fixtures

`bash station/generate_test_clips.sh` makes them in `broadcast/media/`
(gitignored; ~350KB each): five 10s clips (`e2e_v1..v5`, distinct hue +
tone + burnt-in label) and one 6s ad (`e2e_ad1.mp4`, "AD BREAK").

## Procedure (as run 2026-10-16, ~8 minutes wall time)

1. Backup: `broadcast/media/playlist.json`, `broadcast/state.json`,
   `SMILE-Station.json` to /tmp.
2. Create ad stage: `CreateScene("SMILE | Ad Break")` +
   `CreateInput(ffmpeg "AD Break")` via websocket.
3. Write test playlist: 4x10s items + `"ad_every": 2`,
   `"ad_files": ["e2e_ad1.mp4"]`. Daemon reloads on mtime — no restart.
4. `systemctl restart station-daemon` (clean start of the observation).
5. Watch `journalctl --user -u station-daemon` for the evidence lines.
6. Mid-run: append a 5th item to playlist.json (direct file edit).
7. Restore backups, `RemoveScene` + `RemoveInput` the ad stage, confirm
   the loop resumes the live playlist.

## What was proven (with timestamps)

- Back-to-back advance: `Now playing V1..V5` in rotation, ~30s cadence
  on 10s clips (poll-driven; see gap note below).
- Ad cutaway: `Ad break: e2e_ad1.mp4` — program cuts to the ad scene,
  decks mute, ad rolls from 0 via TriggerMediaInputAction.
- Ad return: `Ad done; back to program` — decks unmute, program back on
  Meet, next item plays where the index points (no skip, no replay).
- Live playlist edit: appended V5 mid-run → `Playlist reloaded` →
  `Now playing: E2E Video 5 (added live)`.
- Fault safety: a decoder stall on one deck produced
  `CRIT PLAYOUT_B: stalled at 33ms` + automatic TECHDIFF hold, stream
  survives, loop self-resumed after.
- End-to-end latency per transition: ~10-30s on 10s clips. This is a
  CONSTANT (two ~10s polls + RPC time), not proportional: on 2-hour
  videos it is <0.5% overhead. Do not "fix" it by shortening polls
  without re-proving the swap-transient guard.

## Findings that changed the code (all landed same night)

- Daemon Identify sent no eventSubscriptions: zero events ever arrived;
  the loop had been advancing via the ~60s re-kick all along. Fixed
  (MediaInputs bit). But verified live: ffmpeg_source natural ends do
  NOT emit MediaInputPlaybackEnded on this build — so advance is now
  poll-driven (two straight ENDED polls enqueue like an event) with
  events as the fast path. Re-kick stays as final backstop.
- /studio listened for events on op 4; real servers send op 5. Every
  event handler (meters, scenes, filters, outputs) was dead code.
  One-line fix; this was the "demo meters" mystery.
- Boot `set_scene(Meet)` undoes an ad break started by boot-advance;
  boot now clears stale in-break flags instead.
- Watchdog watches the AD input (not the muted deck) during breaks.
- `sync.py diff/apply` + playlist schema now carry `ad_every/ad_files`.

## Re-run cost

~10 minutes, two restarts max, zero repo state touched (backups
restored, ad stage removed, collection file diff-clean after).

## Streaming variant (2026-10-17, run #2): links, no disk

Same rig, new playlist family: items keyed by `youtube` (no file), three
public Blender movies with compressed `duration` slots (15/16/12s).

Evidence (journal timestamps):
- 03:22:40 `Now playing: E2E YT One (Big Buck Bunny)` — first-uncached
  resolve (~35s: dump-json + 2 URL fetches) + spawn + MTX publish + cut.
- 03:24:05 `E2E YT Two (Sintel)` — wall-clock EOF (15s + 8 grace, fired
  by the 30s poll). Sintel visually ON AIR (screenshot in evidence dir).
- 03:25:23 `E2E YT Three (Elephants Dream)` + `Playlist exhausted;
  reshuffled` — rotation wrapped.
- 03:26:37 `Now playing: E2E YT Two (Sintel)` — post-shuffle pick.
- Feeds die with their slots: after restore, `slot-stream-*` had zero
  processes; the restored live playlist took over unchanged.

Lessons that shaped stream.py (all hit live, all fixed same night):
1. `yt-dlp -o -` while merging is download-then-emit, NOT a pipe; the
   correct shape is two HLS urls into one ffmpeg (-i -i, both copy).
2. RTSP output rejects YouTube's headerless AAC. FLV mints the missing
   headers — RTSP dead, RTMP the localhost courier (OBS reads it fine).
3. Anonymous resolve gets bot-walled after routine use ("Sign in to
   confirm you're not a bot"). Remedy: cookies. `YTDLP_COOKIES` in
   secrets.env accepts a cookies.txt path or `browser:/name/NAME`.
4. Persistent-retry is load-bearing: the OBS input must keep retrying
   forever (reconnect_delay_sec) and never use restart_on_activate —
   the A variant wedged permanently under restart_on_activate flicker.

## Streaming variant (2026-10-17, run #2): links, no disk

Same rig, new playlist family: items keyed by `youtube` (no file), three
public Blender movies with compressed `duration` slots (15/16/12).

Evidence (journal):
- 03:22:40 `Now playing: E2E YT One (Big Buck Bunny)` — resolve (~35s,
  first uncached) + spawn + MTX publish + cut, all automatic.
- 03:24:05 `E2E YT Two (Sintel)` — wall-clock EOF after 15s+8 grace
 准时'd by the 30s poll. Sintel ON AIR, screenshot captured.
- 03:25:23 `E2E YT Three (Elephants Dream)` + `Playlist exhausted;
  reshuffled` — rotation wrapped.
- 03:26:37 `Now playing: E2E YT Two (Sintel)` — post-shuffle pick.
- Feeds die with their slots; `slot-stream-*` went 0 processes after
  restore; live playlist took over unchanged.

Two lessons that shaped stream.py:
1. `yt-dlp -o -` while merging is download-then-emit, NOT a pipe.
   Correct shape: resolve two HLS urls, one ffmpeg with BOTH inputs.
2. RTSP output rejects YouTube's headerless AAC. FLV muxer mints the
   missing headers; RSTP is dead, RTMP is the localhost courier.
3. YouTube bot-walls anonymous resolve on routine hammering ("Sign in
   to confirm you're not a bot"): fix = cookies (chromium profile or
   cookies.txt), configured via YTDLP_COOKIES.
