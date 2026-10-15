# Worklog — world-21-suite station track

Running record of what was decided, built, broken, and learned. For the
operator and for future agents: the hiccups are the point — each one cost
real debugging time and each fix is load-bearing. Newest first.

## 2026-10-15 — Studio relay forensics + UI-drive harness (overnight)

- Root-caused the flapping, in order: (1) socketserver's buffered rfile
  readahead ate pipelined WS frames (reads now go through rfile/read1);
  (2) handshake timeouts leaked into the splice (both legs blocking now);
  (3) dead legs never released the other side (thread/handler leaks,
  fixed with mutual shutdown); (4) THEIR opcode table was shifted by one
  (requests op5, responses op6...) — real OBS closed every session with
  "Unknown OpCode: 5"; fixed to 6/7/8/9 with proof. Relay now holds
  minutes with megabytes flowing both ways.
- Their mirror busy-gate dropped user actions whenever background event
  traffic held it (e.g. our own deck advances) — removed, echo is harmless
  (all mirrored calls set absolute state). Request path hardened: 12s +
  retry + visible warnings + flap grace.
- Daemon self-healing: reachability gate with full Hello handshake (a
  wedged plane can hold :4455 open saying nothing), restart via stop +
  exact-name kill + start (unit stop alone leaves flatpak zombies),
  10min/30min production thresholds, env-overridable for tests. Also
  caught systemd tracking the dead tree as "running" — the gate, not the
  unit file, is now the source of truth for plane health.
- station/test_studio_ui.py: full CDP-driven harness (own chromium per
  run, fresh profile, OBS-state verification per action, residue cleanup).
  Best honest score, healthy minutes: part1 15/20, part2 13/17.
  Every core TD action proven live repeatedly: connect/sync/cuts/add/
  mixer/studio/preview/transitions/outputs/menus/dialogs.
- Open flaky set (engine takes, OBS intermittently doesn't; deaf minutes
  implicate transport, code paths individually verified): scene rename,
  duration set, eye-via-row, remove confirmations, sources-dock freshness
  after cuts. Plus: record produces no file here (backend quirk, UI flips
  correctly), vcam unavailable (no v4l2loopback), projectors/multiview
  need human eyes, sources dock shows composite rows after churn (their
  render + index-id merge fragility — reported upstream).
- Environment note: this box saturates (agent harness itself ~60% at
  peaks) and deaf minutes correlate with load. Verification runs need
  quiet windows; the harness retries and reports honestly either way.

## 2026-10-14 — Relay timeout kill + machine-independent file standard

- Operator's disconnect, root-caused: the upstream socket kept its 10s
  handshake timeout into the splice, so any 10 quiet seconds killed the
  relay and the replica reported exactly "Disconnected from OBS". One-line
  class of fix (both legs blocking now). Proven: 45s held connection with
  12s quiet gaps, live stats throughout. This was deterministic, not load.
- File standard (operator's instinct, formalized): collections reference
  playable files as http://<host>:7070/files/<name>, never /home/... or
  /Users/... paths. New ranged /files route rooted at media/ ONLY
  (secrets.env lives one level up; traversal 403s raw and encoded,
  missing 404s, ranges 206 with correct MIME). render_scenes.py supports
  {{FILES}} (derived from OVERLAY_URL); template converts nothing yet —
  cutover needs an OBS collection reload, scheduled with the operator.
- Bytes travel two approved ways (URLs identical everywhere): intake
  re-fetch per machine (catalog keeps every link), or explicit file sync.
- Personal lint note, now enforced by habit not willpower: ast.parse +
  `//` grep after every Python edit, after three same-night slips.

## 2026-10-14 — Zero-config studio connect + scene portability doc

- Relay now BRIDGES authentication: the browser identifies however it
  likes (empty password included); the relay completes auth with the
  server-side secret and splices transparently after. No secret ever
  touches the operator side. Proven: empty-password Identify -> op2 ->
  scene list, all through the relay.
- Replica auto-connects 800ms after paint (LOCAL-PATCH, gateway defaults
  already target this server). DOM-dump proof: `WebSocket: Connected`.
  Earlier screenshots crying offline were racing the handshake, not
  showing steady state — lesson: capture timing matters, trust logs.
- Grill bites on the way: (1) relay v1 spliced TCP without the OBS-side
  upgrade — 101 out, Hello never (OBS waits for Upgrade); fixed with a
  real client handshake. (2) Forgot to forward Hello to the browser —
  both sides waited forever; fixed. (3) _WS object into a byte pump
  (AttributeError) — went all-socket with role-correct framers instead.
  (4) My own `//` comments in Python, three times — ast.parse every time,
  no exceptions, and noted as a personal lint rule.
- docs/scene-portability.md: the MBA-design-then-push workflow is real.
  Contract (six scene names, PLAYOUT_A/B + IDENT, Fade), transfers vs
  rebinds, canvas discipline, export->commit->render->verify steps, and
  profiles-travel-separately with the stream-key-never-committed rule.

## 2026-10-14 — Studio fixes: bare-URL redirect, one-password connect, live-not-mock audit

- `/studio` (bare) broke all relative assets. Now 301 -> `/studio/`.
  Connect is already near password-only: gateway mode (default ON) ignores
  the host field and uses the page origin, port defaults 4455 — type the
  password, Connect, done. Three taps: Tools -> Connect to OBS -> password.
- Live-vs-mock audit of the replica, three real gaps found and patched
  (marked LOCAL-PATCH, listed in VENDORED.md for re-application):
  1. Transitions dock was DEAD live: wrong field name
     (`sceneTransitionName` vs real `transitionName`), failing silently.
  2. Scene reorder called a nonexistent `ReorderScenes`: now a spoken
     warning, local order only (no such protocol call exists, verified).
  3. Mixer dB was sim-only: no Meters subscription bit, no event consumer.
     Added both + live-level sink with disconnect clearing. Proven:
     InputVolumeMeters events flow through the relay with the exact patched
     subscription (PLAYOUT_B at live level), consumer reviewed defensive
     against empty level arrays (seen live on idle inputs).
- Verified still-live (not mock): preview screenshots, scene/source CRUD,
  mixer mute/volume, outputs, studio mode, transitions (post-fix), meters
  (post-fix) — all real RPC or events. Sim-only by design when offline.

## 2026-10-14 — Third-party replica vended at /studio + raw WS relay

- Rights confirmed by operator (commissioned work): tree vendored to
  station/studio/ (index/css/js/README, 296K), pristine-tree policy in
  VENDORED.md. Excluded: server.mjs, demo mock (port-4455 shadow hazard),
  launchers, docs/. Deploy script only mirrors overlay/, so the control
  surface is never published. Their tree untouched by our edits.
- Pre-vendor audit: zero CDN/deps, hand-drawn icons, request names clean
  (scary ones live only in its README). Known upstream notes recorded in
  VENDORED.md (Linux-absent kinds, README row).
- New relay: browser WS handshake on /?XTransformPort=<obs-port> (target
  pinned to OBS port), OBS-side upgrade performed server-side, then raw
  TCP splice both ways. Auth stays end-to-end via their connect dialog.
- Grill bite, fixed: first version spliced TCP without the OBS-side
  upgrade — handshake 101 succeeded but no Hello ever came (OBS waits for
  Upgrade). Caught by the e2e test, fixed, re-proven: 101 -> Hello ->
  Identify+auth -> Identified -> GetVersion 32.2.2, all through the relay.
  Wrong-port probe correctly 400s.
- Served with MIME-correct subtree routing (ES modules need real JS
  MIME); headless screenshot shows the full replica booted offline-clean.
  Console links it under Tools. Their client needs no changes at all.

## 2026-10-14 — Preview tap + music bed spike: both proven live

- Tap: GET /tap.mjpeg serves program screenshots as MJPEG (~2fps measured:
  40 frames in 20s). Zero OBS reconfiguration, zero new deps (plain <img>
  renders it), zero extra encode on the weak box. Console PROGRAM cap has
  a watch/stills toggle that pauses the stills poller while watching.
- Grill bites found live and fixed: (1) 5.7.4 returns imageData as a DATA
  URI, not bare base64 — tap decoder strips to the comma, and the console
  was double-prefixing (worked by browser leniency; now correct).
  (2) No vlc_source in this build — bed is ffmpeg_source, decided by
  evidence not docs. (3) Full deaf windows recur under load (even
  GetCurrentProgramScene stalls); held connections ride through, fresh
  ones pay. Tap breaks cleanly on deafness; operator re-taps.
- Music: GET/POST /music (list, set with auto-ensure, add via intake then
  move to music/). Bed input auto-created in Starting/Off Air/End Credits
  (verified in all three). Full chain proven with a synthesized tone:
  fetch -> set -> PLAYING (cursor moving, 8s duration) -> STOP. Bed file
  stays set but stopped. Bed restarts on scene cuts (v1 limitation, stated
  in UI). Volume via mixer like any input.
- Residue hunt: aborted first conform run left a collection + OBS-made
  .bak files behind (API residue checks were clean — files are invisible
  to the protocol). All deleted off disk; verified zero. CONFORM_Y still
  listed via API after dir deletion = in-memory cache until OBS restart;
  ghost only, no action (no restart mid-loop).
- SRT-record tap REJECTED after spiking: needs ini archaeology, a second
  x264 encode on a saturated box, and hijacks the recording output. MJPEG
  wins on every axis except smoothness; documented, moving on.

## 2026-10-14 — Edge-case grill: parked/catalog model + promotion semantics

- Operator killed "archive a new link": model renamed in the UI to
  Parked (held out, link kept, one click back) and Catalog (every fetch
  on record, each row queueable = the revert trail, re-fetching if the
  file was evicted). Code enum stays `dormant` (internal); UI never says
  archive again. Template comment rewritten in the same language.
- Grill results, all fixed + tested (23/23 in station/test_playlist_edges.py,
  selftest + stress_cache still green):
  1. Dormant COULD display up-next while never airing (marker lied,
     playout was right). up_next is now a forward playable scan.
  2. Remove/move/add shifted state.index blindly (replay/skip). Edits now
     preserve aim via adjust_index (pure, table-tested); removing the aimed
     item promotes whatever slides in — proven end to end (RB plays).
  3. Pending items spammed WARN every pass. Silent while a source exists;
     all-pending holds on TECHDIFF with WARN (fetch may land), not CRIT.
  4. Prefetch only warmed index/index+1: a parked-then-returned link missed
     at airtime. Now scans the whole rotation (spawn caps unchanged).
  5. Corrupt state.json (non-int index, non-dict) crashed advance +% ops.
     load_state coerces; advance/prefetch/view belt-and-suspenders.
  6. Nameless entries (no file, no source) faulted silently-ish: now loud.
  7. Selftest's shared call-log assertions went order-dependent with the
     new TECHDIFF cuts: snapshotted per-assertion (strictly stronger).
- Left as documented behavior, not bugs: concurrent editors last-writer-wins
  (single-operator station); removing the PLAYING file degrades to a
  cache-miss skip; dormant prefetch burns some bandwidth to keep the bench
  warm; index grows unboundedly across all-skip passes (modulo contains it).

## 2026-10-14 — Media manager split out to /media (parity-10 stands)

- Library dock removed from the console (replaced by Tools -> Media
  manager, new tab); all lib JS moved out with it, zero remnants.
- station/media.html: add form (link/file/show/status), rotation table
  with up-next + per-row move/pin/archive/edit/remove, pending table
  (link registered, file unresolved), dormant archive, music-bed plan
  note, intake history from intake.db. Pending items addressed by index
  server-side (they share file:"").
- One render bug caught by screenshot (appendChild of a string on empty
  tables), fixed, re-verified clean. Endpoints proven: /media 200,
  /intake real rows, add/remove round-trip byte-clean.

## 2026-10-14 — Library manager: add/replace/remove/move + music plan (parity-10)

- POST /library grew ops (same atomic save, daemon reloads on hash change
  — verified in code): add (link for intake-prefetch or file already in
  media/, title/show/status/position), remove (+optional file delete with
  traversal guard + still-referenced guard), move (index), set (pin/status/
  title/show/source). Proven live: add dormant music-tagged probe -> 3
  items with correct pending flags -> remove -> back to 2.
- Console Library dock: + add dialog (link/file/show + cap note), per-row
  up/down/pin/dormant/remove, double-click title/show edit. Cap honesty:
  intake preflight refuses, loop evicts LRU over 50 GB, pinned never moves.
- Music: NOT a playlist rotation (daemon would air it fullscreen). Plan:
  a VLC "Music Bed" input in the collection, UI manages its playlist via
  inputSettings, volume via mixer. Build with the preview-tap spike.
- Preview tap (how the operator WATCHES the loop): record-to-SRT on the
  render plane -> MediaMTX `preview` path -> HLS <video> in the console.
  Uses existing Controls record buttons; archive stays YouTube-unlisted.
- Jellyfin verdict: wrong tool (on-demand server, no linear playout, no
  obs-websocket control, no cap-managed loop). MediaMTX stays as the pipe;
  the manager is necessarily custom — nothing off-shelf does yt-dlp in,
  normalize, cap-eviction, dormant/pin semantics, daemon playout.

## 2026-10-14 — Console parity-9: native select/toggle split in Sources

- Operator was right: click-to-hide was a leftover conflation, not native
  behavior. Rows are now [eye toggle] + [name selects + highlights];
  rename on double-click; Lucide eye/eye-off vendored (12 icons, ISC).
- Screenshot-verified live through the proxy (bare URL, zero params):
  green dot, PGM label, blue on-air scene row, source row with eye+name,
  transitions, media, Library, footer stats. An empty first capture was
  poll timing under load, not a bug — confirmed by a longer capture.
- Program sat on Tech Diffs after conformance churn (watchdog cut, correct
  supervision); loop itself never stopped.

## 2026-10-14 — Intent-routing migration shipped (parity-8): console holds no socket

- Measured justification first: fresh OBS handshakes stall 10s+ under load
  while the daemon's held connection rides through. Every new client paid
  the lottery — including the TD's browser on every page load.
- Overlay server now holds ONE request connection (locked _call) plus an
  event-only connection (meters cache + scene/studio changes onto the
  existing SSE bus). New: POST /obs passthrough (type allow-listed to
  request names, data must be an object) and GET /obs/meters.
- Console deleted ~130 lines: SHA-256 auth, handshake, reconnect, route
  demux, ?obs/?pass params. call() is now a fetch with the same signature
  (zero call-site changes); meters poll 1s; scene changes arrive over SSE
  with the 5s poll as backstop. No OBS port or password on the TD side.
- Proven: /obs GetVersion -> 32.2.2, /obs/meters live, headless screenshot
  of bare /console (no params) shows scenes/transitions/media/library all
  populated through the proxy. PRODUCT.md updated to the new trust shape.
- Tooling lesson: headless screenshots hang on open SSE streams; use
  --timeout, not --virtual-time-budget, for evented pages.

## 2026-10-14 — Console parity-7: interaction parity, all proven live

- Live fader drags (was change-on-release), arrow-key nudge (Shift=1px,
  read-modify-write transform), F2 rename, studio Cut/Fade buttons (shown
  only in studio mode), right-click context menus on scenes and sources,
  scene duplicate via item-by-item clone (no such protocol call),
  preview-scaling submenu, stats modal refreshing while open.
- Proven live, scratch-only except one self-inflicted program cut (preview
  never set -> trigger cut stale preview; restored via RETURN, lab only,
  no audience): transition select/duration/trigger ok, CreateSceneItem
  clone ok, preview-set ok IN studio (refuses outside it, correctly —
  console already gates on studioOn), program untouched throughout.
- In passing: one TAKE back — SetCurrentPreviewScene outside studio mode
  is refused by design, not a bug; test was wrong, console was right.

## 2026-10-14 — Console parity-6: native OBS icon set, licensed and local

- Native set identified WITHOUT copying it: OBS binary resource names
  (plus/minus/up/down/filter/refresh/media_*/recording-*/network-*) map 1:1
  onto Lucide, which OBS itself derives them from. GPL assets untouched.
- Lucide v1.57.0 (ISC) fetched once, 10 icons vendored INLINE into the
  single console.html with attribution comment; zero runtime requests,
  then and now. Hand-drawn set fully retired, zero remnants.
- Toolbars now native: scenes + − grid, sources + − gear sliders ↑ ↓,
  mixer gear, external-link undocks, refresh/pin glyphs. Rename buttons
  removed (native has none); rename lives on double-click for scenes and
  sources, exactly like the desktop, with title hints. Screenshot-verified.

## 2026-10-14 — Console parity-5: zip reference mined, theme converged

- Operator supplied obs-ywa-app.zip (21 entries). Unpacked to /tmp ONLY
  (stays out of the repo; nothing vendored). Mined for measurements, not
  code: token ramp (#1d1f26/#272a33/#2b2e38/#3c404d/#dfdfdf/#1e50a0/#4daafc),
  Segoe 13px, 100vh flex column, 250px dock row, header-bar docks, 24px
  icon buttons, 4px-radius #3c404d buttons, dark inputs, scrollbar.
- Their script.js inventoried (84 fns): purely local compositing
  (renderLoop, audio nodes, canvas) — zero remote protocol, as established.
  No further wiring lessons; behavior spec unchanged.
- Applied as OUR css: tokens, font, fixed 250px single-row docks with
  internal scroll, filled header bars, 24px toolbars, dark inputs,
  header-bar dialogs, sticky footer. Screenshot-verified against their
  layout at the same viewport: structurally adjacent.
- Boundary restated in repo history: reference informs, never ships.

## 2026-10-14 — Console parity-4: icon redraw, density pass, screenshot-verified

- Verbatim paste refused once more, plainly: their code is proprietary with
  no license, and their engine cannot drive our render plane. No paid icon
  set fetched (no license to use it); standing offer: hand over a set you
  own and it gets wired in same-day.
- Icons redrawn sharper (plus/trash/pencil/chevrons/gear/sliders/grid +
  pop-out undock), still self-drawn inline SVG, still zero dependencies.
- Density toward reference, verified by headless screenshots of BOTH pages:
  scene/source buttons are now full-width list rows with blue on-air row,
  Controls stacked full-width, menu bar tightened, dock/stage padding
  tightened, mixer rows compacted. Current shot is structurally adjacent
  to the reference at the same viewport.
- Pass discipline: bounded edit → screenshot → fix → confirm, then stop.
  Next pass only after operator eyes on parity-4 (private window,
  corrected URL without :4455).

## 2026-10-14 — Protocol conformance: server's own request list as ground truth

- Asked the render plane for GetVersion.availableRequests (5.7.4) and
  diffed all 62 request names the console uses: 58 exist, 4 did not.
  Fixed: AddSourceFilter -> CreateSourceFilter (v5 rename), ReorderSceneItems
  -> get-index/set-index relative moves (no such request), WebSocket
  settings get/set -> do not exist in 5.7.4 (row now disabled-with-reason).
- Live write lifecycle on scratch scenes (program untouched throughout):
  scene/input/settings/rename/duplicate/index/enable/transform all ok;
  filter create/enable-off/settings-roundtrip (brightness 0.5 MATCH via
  GetSourceFilter)/remove ok; profile create ok; collection create ok
  (lands on it, switch back ok, RETURN restores Meet).
- Two silent no-ops found (ok returned, nothing happens): gain_filter on a
  sourceless text input (no audio pin; video filters attach fine), and
  RemoveProfile (persists across calls — server bug/quirk). Console offers
  neither lie: filter kinds are the operator's pick, Profile Remove is now
  disabled-with-reason. Scratch residue deleted off disk (profiles +
  collection file), lists verified clean.
- Deaf windows are real and recurring: new handshakes and mid-connection
  calls stall 10s+ under load (CEF contention), then recover. Daemon's
  persistent conn rides through; every fresh client pays the lottery. This
  is measured justification for the intent-routing migration (console via
  the server's held connection instead of direct :4455): tracked, not built.
- Impeccable skill loaded (context run); console is Operate mode. Visual
  pass against reference screenshots done structurally (parity-3); remaining
  delta is taste-level spacing/type, queued behind function.

## 2026-10-14 — Console parity-3: full OBS menu tree, dock chrome, text bar

- Reference (saved YWA DOM, studied as functional spec only — no code, no
  CSS, no assets taken) vs ours compared via headless screenshots of both.
  Gaps found: no File/Edit/Docks menus, double header, stage hogging the
  viewport, no dock toolbars, no per-kind bars, no footer timecodes.
- Shipped: single slim menu bar (meta: conn dot, build chip, PGM) with the
  FULL tree File/Edit/View/Docks/Profile/Scene Collection/Tools/Help, real
  names, submenu support, live checkmarks, shortcuts, disabled-with-reason
  rows (hover says why: no remote protocol / render-plane-local / would
  kill the broadcast). Settings moved to File where it belongs.
- Working entries, all real protocol: scenes/sources CRUD + reorder,
  props + filters, transforms (reset/flip via read-modify-write),
  duplicate, advanced audio (volume dB + monitor type per input),
  websocket server settings (get + set, with own-foot warning), output
  timer (read-only timecodes), profiles/collections create + switch +
  remove, custom browser docks (self-maintaining in Docks menu), lock/
  reset docks, dock toolbars toggle, source icons toggle, scene-list
  compact, preview lock (holds last frame), statusbar toggle, text
  quick-edit bar (appears for text kinds only), stream/record timecodes
  in the footer.
- Icons: self-drawn inline SVG (plus/trash/pencil/chevrons/gear/sliders/
  grid), zero CDN, zero downloads, zero external requests anywhere in the
  console (audited: no http refs except code comments). Favicon inlined as
  data: to silence the 404. Nothing phones home; no outbound links at all.
- Deviations from the reference, deliberate: Director-intents + Library +
  Media docks (station value-adds, same chrome), NLE editor + hotkeys +
  appearance/accessibility pages (local-app concerns, no remote surface),
  display/audio-capture source kinds (capture the VIEWER's hardware — wrong
  machine for a remote console).
- Verified: node --check clean, every new handler present in served bytes.

## 2026-10-14 — Console full-parity build, phase 1 (clean-room, our code)

- obs.ywa.app inspected: proprietary (no license/source link), zero
  obs-websocket (standalone in-browser compositor). Verbatim clone refused
  (copyright) and useless (cannot drive our render plane). Operator chose
  full functional parity instead: same coverage, our implementation, real
  protocols. Their menus/docks/dialogs studied as functional spec only.
- Shipped in console.html (same URL, hard-reload): scenes add/rename/remove
  (no v5 scene-reorder exists; creation order rules), sources add (kind
  picker from GetInputKindList) / remove / rename / reorder (ReorderSceneItems)
  / props (friendly fields + raw inputSettings JSON, all kinds) / filters
  (list, toggle, add from kind list, remove), Settings modal (stream incl.
  key, video base/output/fps, record dir), click-to-cut Multiview (stills on
  open only, on-air pane marked), full Stats modal. Selection follows clicks;
  toolbar acts on it. Tools menu wires all three modals.
- Verified: node --check clean, served page contains every new handler.
  Live testing against OBS left to the operator (MBA hard-reload first).

## 2026-10-14 — Library UI (playlist schema now visible + operable)

- advance() never honored `status: dormant` (comment promised "never airs",
  code aired everything on disk). Fixed: dormant skips silently (operator
  intent, not a fault), all-dormant holds on TECHDIFF with its own CRIT,
  file-less prefetch items hardened (.get, no KeyError). Selftest covers
  both; verified against real daemon code in an isolated BROADCAST_ROOT.
- Overlay server: GET /library (presence, size, pin, status, show, up_next,
  disk vs cap) + POST /library (pin/status toggles, atomic save, daemon
  picks up next transition). Proven live via curl both directions; test
  toggles reverted, playlist left as found.
- Console: Library dock (↻, disk line, per-item pin + active/dormant
  buttons, UP NEXT marker, missing files red). Same URL, hard-reload on MBA.
- Caution: two edit-tool misfires glued lines in overlay_server.py
  (IndentationError, caught by ast.parse before restart, fixed). Lesson:
  never send oldString==newString; verify with ast.parse/node --check
  after every edit, not just at the end.
- Correction to earlier message: console v2 talks direct browser→OBS:4455
  for OBS ops (same as v1) + same-origin fetch for daemon intents. The
  ?obs=&pass= params are still required. Intent-routing migration (no 4455
  on the TD side) is still open work, not shipped.

## 2026-10-14 — MBA→bus→OBS proven end to end, operator-confirmed

- MBA OBS (composed screen + cam PiP) → bus slot-cam → OBS Slot Cam
  PLAYING → composited Q&A screenshot shows the Rick wallpaper + mirrored
  text + operator PiP. Operator confirmed the pixels are theirs. The last
  unproven link is proven; contribution path closed.
- Console v2 shipped: menu bar (working entries only), preview/program stills,
  Studio Mode, transitions + duration, mixer (mute/volume/meters via explicit
  subscription), stream/record/virtualcam, stats bar. MBA hard-reload needed
  (browser caches v1).

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

## 2026-10-15 — Render-plane outage 05:52–09:20 EAT (OBS boot wedge + CEF GPU crash)

- Symptom: after host restart, OBS never brought up `:4455`; daemon
  `wait_ready` exhausted, loop dead ~3.5h. Two stacked causes, both
  headless-only (never seen with a human at the screen).
- Cause A — wrong display: unit set only `DISPLAY=:99`, but Qt prefers
  Wayland when `WAYLAND_DISPLAY` leaks in from the user session, so every
  boot opened on the real Hyprland desktop (safe-mode dialog sat VISIBLE on
  tty2, `hyprctl clients` proved it) while Xvfb screenshots stayed black.
  Fix: `QT_QPA_PLATFORM=xcb` + `UnsetEnvironment=WAYLAND_DISPLAY` +
  `--nosocket=wayland --nosocket=fallback-x11` in `station-obs.service`.
  Nothing of OBS's may ever touch the user's screen again.
- Cause B — CEF GPU suicide: with `BrowserHWAccel=true`, Chromium's GPU
  process dies under Xvfb/software-GL and logs
  `FATAL: gpu_data_manager_impl_private.cc(454) GPU process isn't usable.
  Goodbye.` — killing the whole main OBS ~30s after Normal-mode dismissal,
  every boot (coredump SIGTRAP + `obs-browser-page` SIGTRAP/SIGSEGV cluster).
  Bisect: Untitled stable 200s+, SMILE-Station dead ~30s, no-browser copy
  also dead (plugin init alone is enough). Fix: `BrowserHWAccel=false` in
  `global.ini [General]` (known upstream issue obsproject/obs-studio#12679);
  all 7 overlay pages render in software. `setup.sh` now enforces it.
- Bonus fix — safe-mode trigger identified: leftover
  `obs-studio/.sentinel/run_*` files ARE the "did not properly shut down"
  signal. `ExecStartPre` now clears them (+ CEF Singleton*) so every
  (re)boot is dialog-free; verified: 2 stale files → dialog, cleared → straight
  to main window. Self-heal (`restart_plane` → unit start) works unsupervised.
- Tools: `station/obs_click.py` (warp-pointer + XTest click on :99;
  root-routed send_event is ignored by Qt — learned the hard way),
  Normal button ~= 1060,532, singleton-cancel ~= 1135,532.
- Collateral learned: daemon `restart_plane` correctly drives the unit
  (`stop`/`start station-obs`); a second manual obs instance parks at "OBS is
  already running" — converge on the unit, never hand-run beside it.
- Log hygiene: OBS keeps last 10 logs; restart churn rotated out the healthy
  03:11 boot log before it was copied. Copy logs out BEFORE churning.
- State at close: all 5 units active, SMILE-Station stable, daemon looping
  (`Now playing: Loop A`), `Stream output not active` CRIT is lab-normal.

## 2026-10-15 (night) — MBA "not connecting" + full studio/relay review blitz

- MBA diagnosis from the lab side: the 502s the MBA hit (~21:34) were the
  post-reboot window when OBS was genuinely still booting — the relay
  correctly reported "render plane unreachable", not a relay bug. After
  that: zero MBA requests in 15 min (page closed or network), while a local
  handshake completed in 0.0s. Verdict: plane + relay healthy; ask the MBA
  to reload and read the badge/banner. Also note 244% OBS CPU (software
  rendering) — new handshakes still starve when saturated; that, not the
  UI, is what "demos" usually means (never Identified => sim meters).
- Four parallel review agents (connection lifecycle, sync/mirror, UI,
  server) returned ~55 findings; triaged and implemented same night:
  - ws.js: generation-scoped connections, dead-man switch (20s silence),
    shared teardownConnection, wantConnect (manual Disconnect sticks),
    auth-hint on double pre-Identify close, reads-retry/writes-fire-once,
    queued-mirror coalescing, mirrorOnly pre-capture (remove/rename were
    silently never reaching the server), volume/mute debounce.
  - sync: upsertScene/Source, forgetItem, syncSceneItems (reindex),
    snapshot/restore, real Input*/filter/media/audio events, SceneRemoved
    sweep, filter merge-by-name, persistSoon, undo remote-tags + attached
    warning + per-sync clear.
  - UI: retina drawImage overdraw (remote + transition ghost), marquee off
    + pointer cursor while attached, Space/Enter double-fire, menu z,
    bottom-strip/gutter drops, width clamps, filter dialog fixes.
  - server: relay cap (4) + keepalive + 120s idle watchdog + auth close
    frame + accept check + iterative ws_read + slot release on all paths;
    SSE evict-kill + heartbeats; tap single-flight poller (own renderer
    conn); honest 502 vs 200; music busy/uuid; files realpath/range;
    daemon OBSAppError (no conn drop on app errors), 90s event timeout,
    threaded alerts + WAL, pl_lock + fresh-reload shuffle/prefetch,
    restart port-wait, frame/header caps.
- Deferred (judgment, not oversight): full OBS gateway/circuit-breaker,
  fixed HTTP pool, inverse-RPC undo table, dock registry — proposed by
  reviewers, too invasive to land blind on a live station. Queued.
- Verified: py+js syntax, daemon selftest, playlist edges, engine node
  asserts, headless-Chromium CDP suite incl. online live-toggle both
  directions with button/backend agreement. Loop + all 5 units healthy.
