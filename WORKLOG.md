# Worklog — world-21-suite station track

Running record of what was decided, built, broken, and learned. For the
operator and for future agents: the hiccups are the point — each one cost
real debugging time and each fix is load-bearing. Newest first.

## 2026-10-14 — Console restyled OBS-dark; menus refused on principle

- console.html rebuilt as OBS-dark docks (Scenes / Sources / Transport /
  Intents / Output) under a slim topbar (conn dot + PGM readout). Our own
  code throughout; OBS-Old contributed arrangement ideas only.
- No File/Edit/View bar, deliberately: menus administer the local app
  (profiles, remux, updates, hotkeys, about), none of which is a show
  operation. Everything a TD does on air is a dock. Nothing hidden, nothing
  to autohide.
- New capability with the restyle: per-source eye toggles for the program
  scene (rebuilds only on scene change so polling never steals taps).
  Hard-reload the page on the MBA to pick this up (browser caches the old).

## 2026-10-14 — MBA sessions reconstructed; bus restarted on clean config

- Bus log forensics closed the "streaming but nothing arrives" case: 01:30
  host_av published fine (7.5 min); 04:48–04:49 MBA retried host_av SIX
  times, all rejected ("path not configured") while OBS showed healthy
  bitrate — a caller-side bitrate display means ENCODING, not DELIVERY.
- Root cause, owned: renamed bus paths host_av→slot-cam WITHOUT restarting
  MediaMTX, while the MBA still held the old URL. Rename + stale client +
  no-restart = silent mismatch. Rule added: config changes ride WITH the
  service restart that loads them, verified via API before announcing.
- 04:49 and 04:56 slot-cam sessions then ran 6 and 21 minutes, clean EOF
  closes. The new URL (MBA screenshot confirms it byte-perfect) works.
- Bus restarted on current file: exactly slot-cam + slot-screen. Daemon restarted on current code.

## 2026-10-14 — Slot model: presenters come and go, scenes never change

- Bus paths renamed person-neutral: `slot-cam` / `slot-screen` (was host_av).
  OBS sources follow: "Slot Cam" / "Slot Screen". Whoever publishes to a slot
  IS that slot: today the operator, tomorrow Ted, zero scene/source edits.
  Audio rides muxed with its camera (lip-sync rule); screen travels alone.
- send.sh now targets the bus only (:9000 + publish: prefixes); the direct
  port-per-feed mode died with the listener weakness it depended on.
  receive.sh kept as raw sender-verifier, with a header warning about the
  :9000 conflict (stop the bus first).
- Remote-access model confirmed: TD needs no OBS anywhere — browser
  console (scenes/intents/transport) + browser guest-send page. Off-LAN reach
  is Tailscale-or-tunnel (VPS runbook); loopback-only binds never change.

## 2026-10-14 — Cache stress battery: 7/7, caught a real bug day one

- `station/stress_cache.py`: proportional edges (rotation, pin survival,
  50-vs-49.9 scaled, pinned-wiring, all-pinned refusal with zero bytes moved,
  failure litter, LRU order). Scaling is honest: policy compares only bytes
  and mtimes. Exit nonzero on any FAIL.
- Battery's first run caught a live accounting bug: evict total EXCLUDED
  pinned files, so any pressure with pins present compared a partial total
  against the full cap and evicted nothing, silently. Total now counts all
  bytes; only selection skips pinned. Fixes like this are why the battery
  exists before the 50 GB deployment, not after.
- Companion fixes: cap resolves at call time (stale def-time default would
  have enforced 50 GB in tests); intake `--as` hardlink path; INTAKE_MIN_FREE
  override for tmpfs-bound tests; pin set wired from playlist+state into
  both loop and intake (playing/prev/next + operator pins can never be
  evicted, including by intake's own pre-burst sweep).

## 2026-10-14 — Q&A carries its page; scenes/sources split settled

- Operator correction taken: scenes are SMILE|X shells, SOURCES are the html
  files (starting/speaking/tech-diff/offair/end-credits/ticker/watermark.html
  + functional IDENT/PLAYOUT_A/B/SRT Cam/Screen). q&a.html added as a hidden
  source in the Q&A scene (audience mode on toggle; live-talk by default).
  Verified live via GetSceneItemList: 6 items, correct visibility.
- Shared-source question resolved by inspection: ticker/watermark were ALREADY
  single definitions referenced from two scenes (Add-Existing pattern) —
  no plugin needed, nothing to change. That is also why they cost one CEF
  instance, not two.
- Meet scene recommendation (operator asked): video deck + ticker + watermark
  as separate native layers; meet.html stays OUT of the air path (its ?yt=
  embed is intake-preview only). Confirmed as the standing composition.

## 2026-10-14 — Restart storm root-caused: two launch lineages

- 20 ghost restarts + "already running" dialogs = MY setsid launches racing
  the systemd unit over one lock (plus crash-loop churn on a weak box).
  obs-restart.sh now ONLY prepares state and calls `systemctl start`; direct
  flatpak launches are banned by comment and by design. One owner per process.
- Companion fixes in the same pass: unit rate caps hold-and-shout instead of
  spinning; obs-restart resets stale holds before start; daemon re-baselines
  its playlist hash after natural advances (own shuffle no longer announces).
- Standing rule (third time written, first time enforced by construction):
  nobody starts an OBS that isn't the unit. The script is the only path.

## 2026-10-14 — Scenes renamed to overlay filenames + OBS-Old verdict

- Operator overruled SMILE|X: OBS scenes are now exactly the overlay filenames
  (`starting.html`, `tech-diff.html`, `q&a.html`, `offair.html`, `meet.html`,
  `end-credits.html`; note the two spellings that differ from guesses:
  tech-diff not tech-diffs, offair not off-air). Self-documenting: scene name
  IS the file. Daemon constants + renderer checks follow.
- OBS-Old.md (476 KB "OBS Studio Web Edition" from another device): archived
  to `archive/obs-web-edition/`. Verdict after inspection: static GUI-chrome
  mockup — 64 menu labels, zero protocol code (2 "websocket" hits are menu
  TEXT), external script.js/style.css companions missing, CDN deps, no
  license. Nothing to wire, nothing licensed to take. Its one honest use is
  the control inventory (which native buttons exist) for growing our console.
  Same ruling as Codepen: visible is not licensed.
- Restart/collection discipline x3: obs-restart installs ALL rendered
  collections (a stale sibling is indistinguishable until read); boot lands
  on last-used so runtime switches are never needed (they wedge the server
  for minutes); verify scene names live via GetSceneList, never disk alone.

## 2026-10-14 — OBS exited 0 spontaneously; Restart=always + idle re-kick

- Render plane exited clean (status 0, no crash, no log) after 5.5h; cause
  unknown. Units were Restart=on-failure, so it stayed dead. Now always.
- Same incident exposed the resume gap: after any OBS restart nothing plays,
  so no ENDED event ever arrives and the loop idles forever. Poll loop now
  re-kicks the deck after 6 idle polls (~3 min). Verified live within minutes.
- Codepen "OBS WebApp Clone": page chrome only via fetch (JS app, no code
  visible) — and visibility isn't license anyway. Codepen pens default to
  all-rights-reserved unless the author states otherwise: look, don't yoink.
- MBA record-via-console confirmed landing in broadcast/ by the operator —
  remote-control loop closed end-to-end (click on phone → file on disk).

## 2026-10-13 — Cutover: station runs on systemd, survives reboot

- `linger` on, all five units enabled+active (xvfb → obs → daemon chain,
  mediamtx, overlay). Loop advancing + reshuffling under unit supervision;
  throttle behavior nominal in journal. Reboot no longer kills the station.
- Real bug from the cutover: transition check used a nonexistent
  `GetTransitionList` (fail-open hid it). Correct request is
  `GetSceneTransitionList` (verified live against 5.7.4); fail-fast stands.
- Overlay unit exposes BIND=0.0.0.0 (home LAN for the Mac console; tunnel on
  VPS). ufw still needs 7070/tcp for the MBA (told, unconfirmed).
- Unplanned drill that got us here: the box rebooted overnight with nothing
  supervised — total outage, zero self-recovery. That outage is now the
  regression test for this entry.

## 2026-10-13 — Prefetch worker (look-ahead resolve, three misdiagnoses)

- `prefetch_pass()` in the poll loop: next-2 items with `source` but no file
  get resolved via intake SUBPROCESS (crash-isolated, max 2 concurrent).
  Deterministic `--as` names so the daemon knows what to expect; intake
  hardlinks already-cached bytes under a new name instead of re-fetching.
  Doomed sources back off 15 min (a fork+alert churn every 30s is how a quiet
  box spends a night achieving nothing). Proven live in selftest.
- Misdiagnosis chain, honestly recorded: (1) "hung subprocess" was a respawn
  loop — tmpfs /tmp can never satisfy the 5 GB intake guard, so every pass
  spawned a fetch that died instantly; fixed with backoff + test env
  `INTAKE_MIN_FREE_BYTES`. (2) Then the 3s test file tripped the 5s verify
  floor — correct rejection, wrong test asset (now 6s). (3) `pkill -f`
  murdered my own shell a THIRD time (pattern contained the plain form).
  New absolute law: no pkill-with-pattern, ever — PID files and exact PIDs.
- Also fixed en route: intake failure litter, intake env override, playlist
  `source` field documented, in-flight dict persistence across polls (a fresh
  dict per pass blinds the spawn guard — caught by reading, not by failure).

## 2026-10-13 — obs-web studied (reference only, never vendor)

- Niek/obs-web (1.5k stars, GPL-3.0, Svelte, updated yesterday): static page,
  direct browser→OBS, scenes, Studio Mode, 1fps screenshot previews, meters,
  recording/streaming, phone-friendly. Read obs.js + ProgramPreview directly.
- LEGAL: our repo is MIT; obs-web is GPL-3.0. Vendoring any of it would
  infect our license. Reference the patterns, write our own lines. Decided.
- Patterns worth stealing (ideas, not code): `obsws://host:port/password`
  deeplink format (nicer than our ?obs=&pass=); InputVolumeMeters needs
  explicit subscription (meters ARE available — earlier "no meters" note
  corrected); named event handlers removed on destroy (reconnect listener
  stacking is real — audit ours: console.html adds `route` once per connect()
  but never removes on close → same stacking bug on every reconnect!).
- Our console keeps its lane: station intents + deck transport, not a clone.
  Full-feel test path for the operator: open obs-web against the Arch box.
- Caught by the comparison and fixed same hour: our status poller WAS stacking
  (new setInterval per reconnect → N pollers hammering). One global poller now.
  (Message listeners were safe — they die with their socket; only the interval
  leaked across reconnects.)

## 2026-10-13 — Director intents over HTTP (console grows up)

- Console gained GO LIVE / TECH DIFF / RESUME / RETURN buttons POSTing to
  `/intent/*` on the overlay server, which runs the CLI's exact functions
  (extracted to `do_*`, single implementation). Phone and terminal agree.
- Found live: intent server started bare fails 4009 (OBS_PASS only in chat
  history). `load_secrets()` now sources broadcast/secrets.env in daemon CLI
  AND overlay server at startup. Verified: tech-diff + return both ok:true,
  program confirmed on Meet.
- Ident→LIVE chain fired again in the wild (loop log + program on Q&A) —
  consistent with the MBA operator experimenting via console scene buttons
  while the loop's event thread routes. System absorbs concurrent drivers.
- Research verdict (web search, 2026-08): OBS ships NO official web UI;
  Niek/obs-web is the closest existing thing (static page, scenes, Studio
  Mode, 1fps previews, mobile-friendly). Decision: do NOT clone 1:1. Try
  obs-web for the full-feel test; grow ours only toward station intents it
  lacks. Full GUI parity is the wrong target (preview video + meters over
  ws is a slideshow, not a switcher).

## 2026-10-12 — Audit pass: full daemon read-through + small sharp fixes

- Read all 754 lines as-shipped. Real finds, all fixed: `WARM_DEPTH` dead
  constant (deleted); disk-full CRIT spammed per-poll (hourly throttle now);
  fault keys grew unbounded (pruned); IDENT-end hijacked program after a
  mid-ident RETURN (guarded on program-still-Starting); missing transition
  wedged advance into infinite deferred-retry (fail-fast check at loop start,
  degrades to warning if the check itself can't run); poll tracebacks now
  once-per-distinct-error; intake failure littered partials in cache
  (removed on failure — verified live: rejected 3s file, zero litter);
  overlay server hung on Ctrl+C with open SSE connections (daemon_threads);
  setup.sh required curl without checking it + mapped all Darwins to arm64
  (Intel MBA would have fetched the wrong MediaMTX — uname -m now).
- Deliberately NOT changed: evict INFO-per-file (fine at real volumes);
  intake corrupt-playlist crash (cron surfaces it); console enum strings
  (server errors surface in-page by design); POST/state without auth
  (documented trust: home LAN / tunnel-only users).
- Failure-path verification: intake rejection leaves no litter; overlay
  server exits with open SSE connections; all syntax + both selftests green.

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

## 2026-10-12 — Missing-file dialog killed at the root

- OBS "Missing Files" dialog (IDENT + PLAYOUT_A/B placeholders) is the template
  working as designed, not breakage — but placeholders must never reach a
  human. `render_scenes.py` now resolves decks to the first playlist items on
  disk and IDENT to the first ident present (new `{{ASSETS}}` placeholder);
  missing entries keep placeholder paths so the dialog names exactly what
  intake hasn't delivered yet.
- Real fixes underneath: media paths are ABSOLUTE (OBS resolves relative
  against its own cwd, not the collection dir — relative paths silently miss);
  generated a 6s `ident_evening.mp4` slate so IDENT exists; setup.sh pin is
  idempotent now (was re-stamping the timestamp every run, dirtying git).
- Restart discipline (learned the hard way): OBS saves its in-memory
  collection on graceful shutdown, and 12-CEF teardown takes 10s+. A
  kill → sleep-4 → relaunch cycle lets the shutdown-save clobber a fresh copy
  or races the old instance. Rule: poll `pgrep -x obs` to ZERO before
  relaunch, reinstall the file, then verify via GetInputSettings (MEMORY),
  never disk alone — disk can say absolute while memory holds stale relative.
- Bonus from the hydrated file OBS writes back: the true on-disk schema
  (source_uuid links, full item keys, `shutdown` normalization) — template
  stays minimal, OBS hydrates; do not hand-author hydrated fields.

## 2026-10-12 — systemd units written, not yet switched on

- `station/systemd/`: xvfb → obs → daemon chain plus mediamtx + overlay,
  all `systemd-analyze verify` clean. Secrets via EnvironmentFile, restart
  policy on-failure throughout. Installed to `~/.config/systemd/user/` but
  NOT enabled/started: manual processes currently prove the soak, and two
  drivers already burned us once.
- `linger` NOT enabled (sudo window closed before we got there). Without it,
  user units die at logout and autostart can't work. One command, needs sudo:
  `sudo loginctl enable-linger rkw`. Do it with the VPS setup, or next window.
- Cutover procedure when ready: stop manual loop/OBS/MTX/overlay,
  `systemctl --user enable --now` all five, confirm via activity.db + program
  scene, then walk away for the first unattended night.

## 2026-10-12 — Loop night COMPLETE on live headless OBS

- Full cycle observed: advance → deck progress → ENDED → advance → shuffle ×2,
  stall induced at 57.8s → detected with exact cursor → TECHDIFF verified on
  program → resumed → Meet, PLAYING 8s/65s. No crashes, no alert spam, one
  driver throughout (PID file + flock held).
- Media actions (PLAY/PAUSE) EXECUTE but their ACKs stall for minutes here —
  the pause landed (cursor froze) while the caller timed out. Fire them
  patiently; never treat their timeout as failure. Resume that works:
  visibility-cycle (restart_on_activate); re-setting the identical file path
  is a no-op, not a restart.
- Program starts on Meet at loop start (deck previously played dark into the
  Off Air harbour — caught live). Cuts fire only from on-air scenes.
- Self reload notices debounced by content hash (own shuffle-save no longer
  announces). Post-escalation repeats hourly, stream-down reminds hourly.
- Lab box verdict: simultaneous SRT-fail log spam + 12-browser... (light
  collection in use) — box survives the loop but every websocket call needs
  patience. VPS doubles the headroom; numbers travel, conclusions don't.

## 2026-10-12 — False-cascade night: idle ≠ missing, one driver, quiet server

- Tonight's TECHDIFF→OFF-AIR cascade was a FALSE positive: a never-played deck
  reports cursor null, which the watchdog read as "missing". Lifecycle is now
  modeled honestly — missing (query failed) vs idle (exists, unmeasured) vs
  playing vs stalled — and only regressions fault. Pre-first-reading sources
  are measured, never faulted.
- Cuts only fire from on-air scenes (PROGRAM/LIVE roles); a fault during
  harbour/starting/credits alerts without yanking. Unreadable program state
  fails safe toward cutting. Post-escalation repeats throttled to hourly.
- Two self-inflicted wounds, both now structural: (1) TWO loop instances drove
  one OBS (a timed-out launcher survived) → flock lock + PID file; verify via
  /proc, never pgrep patterns near lingered shells. (2) Every loop failure was
  4009-auth-close, not deafness — OBS_PASS lived only in chat history, never
  in secrets.env. Close frames now carry code+reason so auth can never again
  masquerade as a dead server.
- Deaf-window pattern stands but narrowed: genuine stalls (TimeoutError with
  correct auth) cluster post-boot and post-switch; quiet recovers. Persistent
  connection + queued advance-retries + wait budget are the standing answer;
  root cause (memory pressure vs CEF churn) still open, VPS re-proves it.

## 2026-10-12 — Loop night, part 1: deaf-server pattern + light collection

- Websocket server goes DEAF in bursts (accepts TCP, then close-frames new
  handshakes) and recovers after minutes of quiet — seen 4 times. Ruled OUT:
  connection pileup (zero ESTABLISHED during deafness), death (process alive,
  log clean), CEF-only load. Best model: thread starvation under memory
  pressure (165 MB free) + 13 CEF mouths. Lab discipline until disproven:
  batch diagnostics into single scripts, ≥60s spacing, never rapid-fire
  one-liners — earlier "wedges" were partly self-inflicted probes.
- Consequences shipped: `wait_ready` (no blind starts), `OBS_READY_TRIES`
  (default 12, lab uses 60), `WATCH_POLL` (default 10, lab 30), per-item
  "Now playing" air log, `station/obs-restart.sh` (kill→wait-zero→cp→launch;
  never cp-then-kill: shutdown-save clobbers fresh copies).
- `SMILE-Lab` light collection (no browser sources) for mechanics proof;
  OBS enumerates by INTERNAL name, not filename (a same-named shadow file is
  silently ignored — lost an hour). VPS runs full SMILE-Station.
- Daemon/OBS contract note: collection switches wedge the server for minutes;
  choose the boot collection by restart, never switch at runtime.
- STILL OPEN at write time: loop waiting out the storm (60-try budget); first
  real advance → deck progress → ENDED → second advance unobserved. CEF/slow
  concerns from the full collection stand until the VPS re-proves them.

## 2026-10-12 — Remote console for Mac-driven tests (console.html + BIND)

- `station/console.html`: raw scene switching + media transport + status over
  obs-websocket, served at `/console`. No server side: the VIEWER's browser
  speaks ws:// directly, so no inbound hole beyond the OBS socket. Daemon
  intents stay CLI-only until the dashboard phase (documented in-page).
- `overlay_server.py` takes BIND (default loopback); LAN mode prints a
  tunnel warning. MBA needs `sudo ufw allow 4455/tcp` on this box (agent has
  no sudo) + `BIND=0.0.0.0` server + URL with `?obs=<ip>&pass=`.
- Bugs caught before the Mac ever loaded the page: MBA-OBS filter excluded
  the very ffmpeg inputs transport targets (inverted); `crypto.subtle` does
  NOT exist on plain-http LAN origins, so auth uses an embedded SHA-256 —
  verified against NIST vectors AND byte-identical to the daemon against a
  real server challenge. GetInputList keys confirmed live.
- Second unexplained OBS death (no FATAL, no OOM trace; first was D-Bus
  abort). Two deaths in ~3h on 2 cores/3.8 GB with 12 CEF browsers. Stability
  on lab hardware is NOT proven; systemd-restart covers exactly this class,
  and the VPS spec doubles the headroom. Watching.

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
