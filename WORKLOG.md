# Worklog — world-21-suite station track

Running record of what was decided, built, broken, and learned. For the
operator and for future agents: the hiccups are the point — each one cost
real debugging time and each fix is load-bearing. Newest first.

## 2026-10-12 — Host standard decided: plain OBS GUI, no headless, no scripts

- Hosts run normal OBS (minimized, preview off, VideoToolbox HW encode,
  720p30 ≤1500 kbps, 2 sources). Headless-on-host rejected twice over:
  (1) macOS has no X server, so the weakest machines can't do it at all;
  (2) a browser controller costs more than the Qt GUI it replaces — net
  negative on weak hardware; (3) it deletes the panic-stop/preview UX that
  justified OBS over ffmpeg in the first place.
- Rationale that closed it: hosts learn the GUI in ~5 streams; familiarity
  beats custom tooling. Websocket host page still planned, justified by
  uniformity/direction (same buttons + tally for every host), not efficiency —
  multi-guest phase. ffmpeg stays lab/VPS-side only, never presenter-facing.

- Bug replicated cleanly (no MBA needed): ffmpeg SRT listener takes sender1's
  8s, then sender2's reconnect never arrives (8.4s total). Same disease as the
  MBA's OBS-restream failure and crash. Root cause: whoever owns a listener
  socket can't reliably re-listen while the session is active.
- MediaMTX v1.21.2 in the middle (pinned in setup.sh, binary gitignored):
  PUBLISH-side reconnect is FREE — publisher2 takes over with zero action
  ("closing existing publisher" in log). This alone ends the MBA's crash loop:
  the bus accepts the new publish; nothing else moves.
- READ-side still needs re-arm: a reader connected through a path drop does
  NOT resume; a fresh reader connects fine (proven: 6.0s clean). Station rule:
  daemon polls MTX API and re-arms the OBS SRT source on re-publish (Phase-4
  job, now specified by measurement rather than theory).
- Bus rules learned the hard way: SRT streamids need `publish:`/`read:`
  prefixes (bare names are actively REJECTED); reader arriving before any
  publisher is closed with "no stream available" — publisher MUST be up first,
  readers retry. Daemon will own that ordering.
- MediaMTX is RUNNING on this box now (SRT :9000, API 127.0.0.1:9997, PID in
  /tmp/mtx.pid). MBA can push to it today:
  `srt://<ARCH-IP>:9000?streamid=publish:host_av&latency=800000`.

### Hiccup log, continued
11. `pkill -f <pattern>` matches our own shell when the pattern is a substring
    of our command — murdered two test harnesses. New law: PID files for
    daemons (`/tmp/mtx.pid`), exact PIDs or `pkill -x <name>` for processes.
12. Overlapping background test runs pollute each other (stray publishers showed
    up in the bus log mid-drill). One drill per run: `pkill -x ffmpeg` first,
    fresh log, sequential Python-driven processes, no shell `&` chains.
13. MBA brew ffmpeg has NO libsrt (`Protocol not found` on any srt:// URL).
    No script survives a missing protocol: `send.sh` now preflights
    `ffmpeg -protocols | grep -qw srt` and dies with the actual reason.
    MBA falls back to OBS-push (its bundled SRT is proven working).

## 2026-10-12 — Archify architecture diagram (all gates pass, visually inspected)

- `.archify/architecture-smile-station-20261013-032357/smile-station.html`:
  13 nodes, 4 planes as boundaries, 14 labeled edges, repo-pinned evidence
  (HEAD `8dd2d6e`). finalize: validate+deliver+check+browser-check green.
  First layout failed 3 crossings; reflowed (daemon right of OBS, Discord/
  YouTube stacked) and passed clean. Screenshot inspected: legible, no
  overlapping labels; two routes bend more than ideal, meaning intact.
- Alerts moved Telegram → Discord webhook (zero infra: no bot, no token
  rotation). WhatsApp deliberately NOT built: no free official API; paths are
  Twilio (paid), CallMeBot (free, phone opt-in, rate-limited), or fragile
  bridges. If ever required, it's one function swap in `alert()`.

## 2026-10-12 — Headless OBS rig live (Flatpak 32.2.2 + Xvfb :99)

- Daemon speaks real RFC6455 now (obs-websocket is framed WebSocket, not line
  JSON — first version never could have connected). Masked close/pong (server
  kills unmasked client frames with 1002), 60s call timeout (OBS stalls 10s+
  on SetInputSettings under load; short timeouts lie "unreachable").
- Fresh installs ship websocket OFF with a random password:
  `plugin_config/obs-websocket/config.json` → enable, keep auth.
- Template collection loads perfectly (all 6 scenes, 18 sources, harbour first).
- PROVEN: media decode+progress (PLAYING 10033/12000ms, ENDED on finish),
  deck file swap + visibility toggle, scene cuts, 19s program RECORD to disk
  (h264+aac), red color-source renders (compositor alive headless).
- CEF verdict: NOT broken, brutally SLOW. First paint 4–6 min on 2 shared cores
  with 12 browsers; then pixel-perfect (starting.html verified visually).
  Consequence: browser `shutdown` flipped FALSE everywhere (unload-on-hide =
  blank-on-every-cut). Bake-static is now load-shedding, not just hygiene.
- Gotchas: Flatpak /tmp is namespaced (SaveSourceScreenshot invisible from
  host — use GetSourceScreenshot base64); background OBS dies with tool-call
  timeout (relaunch via setsid); 12s clips exhaust during slow round-trips
  (use 60s+ media for headless tests); D-Bus abort killed one run (unresolved,
  watching); collection switch needs OBS restart to appear in list.

## 2026-10-12 — Scene collection + SMILE|X naming (template, unverified in OBS)

- Deck's six are now OBS scenes `SMILE | Starting/Meet/Q&A/Tech Diffs/Off Air/
  End Credits`, authored in `station/scenes.json.template`, rendered by
  `station/render_scenes.py` (env paths, fresh UUIDs, structural checks).
- Role mapping: PROGRAM→Meet (deck+chrome, meet.html NOT on air), LIVE→Q&A
  (SRT + speaking overlay), TECHDIFF→Tech Diffs (fault framing per SCENES.md),
  STARTING holds IDENT, OFF-AIR harbour, END credits. Daemon rewired to match.
- `overlay_server` sends ACAO:* so file:// pages can consume /events + /state.
- setup.sh renders the collection + prints the OBS profile checklist (output
  settings stay manual — profiles can't be safely templated blind).
- BLOCKED on real OBS: no Xvfb on lab box (`sudo pacman -S xorg-server-xvfb`
  needs the operator; agent has no sudo). Template validity is internal-only
  until first OBS load. Offscreen QPA refused ("Unable to open X display").

## 2026-10-12 — Stress test #1: brownout murder drill (PASS)

- Sender SIGKILLed at wall-t=10.0s. Receiver file: 10.36s, h264+aac present,
  decodes 100% clean. The take survives the contributor's death exactly as
  the local-record rule promises.
- Datum: listener-side dead-peer detection took ~7s (receiver exited at 17s).
  SRT doesn't signal a dead caller instantly; watchdog trip time must assume
  seconds, not milliseconds. Follow-up: tune peer-idle timeouts so the
  TECHDIFF cut lands faster than the audience notices.

### Hiccup log, continued
8. `pkill -9 -f "srt://IP:port"` matched our own shell (pattern is substring
   of our command line) and murdered the test harness, not the sender.
   Kill exact PIDs (Python subprocess handle), never patterns — or use the
   `[s]rt://` bracket trick. Lost 20 minutes to this.
9. Kill-drills are INVALID without realtime pacing: lavfi sources encode
   faster than wallclock (~3x here), so a 30s receiver finished before the
   10s murder landed — three "clean" runs proved nothing. Rule: senders in
   any timing test get `-re` on every lavfi input, or wall-time means nothing.
10. SRT listener does not exit promptly on caller death (see datum above).
    Design watchdog thresholds around measured detection latency, not zero.

## 2026-10-12 — SRT laptop-to-laptop proof (PASS with tuning debt)

- MBA (OBS 31.0.4, SRT caller) → Arch box (ffmpeg listener) held ~4 min.
  Firewall was the blocker; lossy WiFi is the tuning item. Nothing disconnected.
- Worst burst survived: 956 dropped packets at once. Stream degraded, never died.
  This is the SRT thesis demonstrating itself (RTMP would have collapsed).
- Tuning prescribed: MBA 720p30 ≤1500 kbps ultrafast, latency 1500 ms BOTH ends
  (effective window = max of both; `receive.sh --latency` added for this),
  wired Air for load-bearing nights. Re-run `--sample` and compare drop counts.

### Hiccup log (each found by testing, not reasoning)
1. `tee` + any output failed: ffmpeg 9's tee needs explicit `-map`
   (auto-map doesn't propagate). Fix in `send.sh`; verified with plain files.
2. `tee` single output failed: tee can't infer format without extension —
   always prefix `[f=mpegts]`. Error was "Unable to choose an output format".
3. Receiver double-bound :9000 in `--sample` (ffplay + ffmpeg). Sample mode now
   records only. One listener per port, always.
4. `daemon.py status` traceback with no OBS: `_call` now converts `OSError` to
   `RuntimeError("render plane unreachable")`; commands degrade to JSON + exit 1.
5. ufw default-DROP on Arch silently killed MBA→Arch SRT while loopback passed.
   ICMP was allowed, so ping lied. Fix: `ufw allow 9000:9001/udp`; `setup.sh`
   now opens SRT ports. Lesson: loopback proves the stack, only two-machine
   runs prove the path. VPS provisioning must include the firewall step.
6. `q&a.html` shipped with triple `</script>` closers (harmless, parsers forgive).
  Listener edit collapsed them to one — validated balanced by html.parser.
7. `/tmp` on this box is cleaned between sessions (samples vanished). Never rely
   on `/tmp` persistence; tapes go to `--record DIR`, never /tmp.

## 2026-10-12 — Station scaffold (`station/`, commit `1d1f608` + grill `979bbd4`)

- `daemon.py` (stdlib-only): `Renderer` ABC + obs-websocket v5 adapter,
  playlist loop w/ shuffle + A/B deck, progress-based watchdog (3×/hr → OFF-AIR),
  Telegram + SQLite log, CLI intents. `overlay_server.py` (127.0.0.1:7070,
  SSE push; verified POST→push→no-reload). `intake.py` (fetch-once → broadcast
  profile → verify → atomic queue). `setup.sh` (broadcast root, 0600 secrets,
  Flatpak OBS pin in `station/manifest/`).
- Grill fixes (all root-caused, all verified): deck visibility never toggled
  (loop would advance on a frozen frame); every media-ended routed to advance
  (ident end now cuts LIVE, unknown sources ignored); callback exception could
  kill the event thread silently (wrapped); total cache miss recursed
  (now loops to TECHDIFF); corrupt playlist edit crashed loop (keeps old order);
  50 GB cap was a comment (`evict_cache()` runs in loop + pre-intake; intake
  refuses when disk critical). `selftest` covers deck/route/evict/stall offline.
- Overlays: EventSource listeners on `ticker`/`speaking`/`q&a` (no-op without
  `/events`; params stay defaults; chat text via textContent only; q&a clones
  same-platform bubbles, caps 6 live). `meet.html` header marks `?yt=` embed
  preview-only, never air path (debrief §19).
- Proven on this box: SRT A+V loopback, intake file→queue, overlay push,
  daemon-no-OBS degradation, `selftest` green.

## 2026-10-12 — Repo surgery (commits `45116d5`, `c37f7ad`, `027f0dc`)

- `prototype` (209 commits of overlay work) is now `main`; old Python-server
  `main` preserved at tag `archive/main-legacy-20261012`; `origin/prototype`
  deleted; `gh-pages` kept + redeployed. Deploy script + README repointed.
- `core/`, `font-test/`, `bubble-lab.html` → `archive/` via `git mv` (zero
  functional references; deploy/serve touch `overlay/` only). README/PRODUCT/
  sync-docstring/CI triggers updated.
- Caught pre-commit: dirty `ticker.html` flipped Nairobi EAT +3→−1 against its
  own comment. Reverted. `end-credits.html` scroll-snap rework kept.
- Open, not fixed: `tech-diff.html` holds `--muted #8c8c8c` vs 16 pages on
  `#a1a1aa` (`sync-brand-tokens.py --check` FAILs; pre-existing).

## 2026-10-12 — Design audit (two independent passes)

- Full chat (5,834 lines) + both debrief fragments + repo docs extracted to 55
  items, then re-audited against two newer full exports (markdown + 3.1 MB JSON).
- Result: zero contradictions. JSON holds the complete §§1–27 debrief
  (node `d40a2592`) — nothing is reconstructed anymore.
- Real tensions recorded: PRODUCT.md assumes host+producer present running OBS
  locally (current-kit truth, wrong target — VPS-sole-compositor wins);
  scene mapping PROGRAM→meet etc. is proposal, ungrounded; `meet.html ?yt=`
  preview-only label was missing (added); token drift above.
- Standing decisions: Ubuntu LTS VPS + Arch lab, Flatpak pin, small-daemon-first
  (Node-RED only if something hurts), same-repo `station/` subfolder,
  local-proof-before-VPS-migration. Empirical list unchanged (soak, steal,
  RTT→SRT budget, overlay soak, captions, Flatpak parity, CPU flags).
