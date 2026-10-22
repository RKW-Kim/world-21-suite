# Worklog — world-21-suite station track

Running record of what was decided, built, broken, and learned. For the
operator and for future agents: the hiccups are the point — each one cost
real debugging time and each fix is load-bearing. Newest first.

## 2026-10-22 (06:00) — the repo's OBS config had fallen years behind the live plane

`station/config/collection.json` is what a fresh box is built from (the
VPS migration). Measured against the live plane: **62 drift lines**.

What the repo was missing, and why it mattered:

- **The loudness chain.** The operator's global compressor + limiter
  (compress -16 dB / 3:1 -> limit -1.5 dBTP) live as OBS filters on the
  live plane. A fresh install from the repo would have had NO loudness
  chain at all.
- **The contribution seats** (Slot Cam / Slot Screen / Slot Audio) — the
  SRT/WHIP seats the operator uses.
- **Three of the nine scenes** (Ad Break, Ticker, Watermark). The apply
  refuses a capture that lacks a scene the daemon drives, so the repo's
  capture could not have been applied at all.

The capture also had a bug of its own: a deck input's file is RUNTIME
state (the daemon points it at the item it is about to play, which is a
spool file with a transient name), and the capture wrote that path
verbatim. It now writes the fail-safe template.

After the re-capture: `sync.py diff` says **"repo matches live (no
drift)"**. The capture went through a temp directory and was checked
for secrets and machine-specific paths before it went near git.

## 2026-10-22 (05:40) — the log told the operator two lies

The activity log is the operator's evidence trail. It was saying two
things that were not true.

- **"Preflight FAILURES at boot" (CRIT) at every boot.** The preflight
  checked OBS and, with the plane switched off on purpose, could only
  fail. The same boot said "Render plane is switched off on purpose"
  one line earlier. The operator's own choice was reported as a
  failure, which teaches them to ignore the CRIT. The preflight now
  SKIPS the OBS checks when the plane is deliberately off ("SKIP obs —
  the render plane is switched off on purpose") and the boot says
  "PASS preflight".
- **Eight warnings per pass, forever.** With the plane down, every
  pass wrote eight rows ("plane unreachable" from the normalizers, the
  overlays, the three deck unlocks, the scene check and the hold). At
  one pass every few minutes that is ~2,300 rows a day: the 5,000-row
  trail fills in two days and the useful rows are trimmed away. These
  now go through the same hourly rate-limit the hold states use.

## 2026-10-22 (05:20) — the daily metadata sweep never swept

The operator asked for a daily check of the videos' metadata (Q5) and
the dock shows the description in the preview panel. After days of
running, **8 of 201 items had a description** — and they were the first
eight.

Two causes, both in the watcher:

- `cached_resolve()` only cached a resolve that had BOTH HLS renditions
  — which is a LIVE STREAM. A VOD's metadata was never cached, so every
  pass re-resolved the same rows from scratch.
- The pass always started at the top of the playlist. With a half-hour
  cache TTL and a five-minute cycle, the frontier never moved: it
  re-resolved the first rows and never reached the rest.

The fix: cache every successful resolve, and give the pass a cursor
(`broadcast/sweep_pos.json`) so it continues where it stopped. The
first pass of the day is still the full sweep (20 resolves); the
ordinary passes now advance 3 rows each instead of re-resolving the
same 3 forever.

This is the same shape as the schedule bug earlier today: the OFFLINE
test passed (the code did what it said) while the RUNNING station did
not (the code was not what the station actually did). The proof is in
the data the operator sees — 8 descriptions — not in the code.

## 2026-10-22 (05:00) — the spool held every download twice, and the test suite touched live state

Two defects, found by looking at the disk rather than the code.

- **The spool kept the raw download next to the blessed copy.** The raw
  IS the download; the blessed file is its remux. Nothing deleted the
  raw, so the cache held 2x the data and the 3 GB cap only ever bought
  1.5 GB of content. The remux now frees the raw, and the sweep
  reclaims a raw whose blessed sibling is there (the case left behind by
  older runs). Measured: 782 MB -> 376 MB in the live spool.
- **THE TEST SUITE EVICTED FROM THE OPERATOR'S LIVE CACHE.** advance()
  ends with spool.kick(), which runs the cache cleanup, and the
  daemon's selftest calls advance() -- with the LIVE spool directory.
  Proved with a canary: the suite deleted a file from broadcast's
  spool/. The selftest now points the spool at its temp dir (like it
  already did for the playlist, the state and the activity log), and
  asserts it.

The second one only became visible because the first fix made the
cleanup delete a duplicate raw: the suite was already evicting from the
live cache (it just had nothing to evict before). A green suite is not
proof that the live station was untouched -- that has to be measured.

## 2026-10-22 (04:30) — scheduled profile switches

The "different order for a different occasion" idea, on a clock.

- `broadcast/schedule.json` holds the switches; the daemon applies them
  and the dock shows the next one (`next switch 06:00 · morning`).
- The guards are the point: a missing profile is refused, an EMPTY
  profile is refused (it would blank the station), the same switch
  cannot fire twice in a day, and the order a switch replaces is kept
  as the `before-switch` profile so it can be loaded back with one
  click.
- PROVEN LIVE: a switch fired once (04:24:01), the order became the
  profile, the ad cadence restarted, and `before-switch` held the
  operator's 203 rows. The station's playlist was restored afterwards.
- **A live catch the offline test could not make:** the switch fired
  THREE times on the first live run. The reason was that the running
  daemon predated the `schedule_last` state key, so the "already
  applied" marker was never persisted and every pass re-applied the
  switch. The offline test passed because it imported the new module.
  This is the rule in AGENTS.md §4 in its plainest form: the unit test
  and the running station are two different things, and only one of
  them was current.
- New: `station/test_schedule.py` (the file, the next switch, the
  guards, the marker, the recoverable order).

## 2026-10-22 (04:00) — the stream lane, and a content class the station could not play

The stream lane had never been run against a real live stream. It
needed one, so yt-dlp was asked for live music radio and a 24/7
channel was picked.

- **THE STATION COULD NOT PLAY A COMBINED LIVE STREAM.** The feed needs
  a video rendition AND an audio rendition; the 24/7 music channels
  publish ONE HLS rendition carrying both and no separate audio one.
  The resolve therefore returned "unplayable" and the item was
  SKIPPED -- i.e. the most obvious content for a music station could
  never play. The resolve now also looks for a combined rendition and
  the spawn feeds ffmpeg ONE input for it.
- PROVEN LIVE: the combined stream resolved, ffmpeg spawned, and
  MediaMTX's slot-stream-a path was READY 5 seconds later. The
  programme output was read back from the bus at the same time (143
  video frames, 262 audio frames), so the OBS side of the same path is
  proven too.
- The test item was removed again afterwards: the playlist is back to
  203 rows with no test debris.

Two harness expectations were wrong and are fixed (a websocket
handshake that PASSES the guard takes the connection over, so the client
never sees an HTTP status; and the harness timed out before the /obs
proxy's 8s plane deadline, so the client gave up first and broke the
pipe on the server side).

## 2026-10-21 (night) — the fixes got grilled: five adversarial clusters, nine regressions found and fixed

- The operator's directive: "grill/audit even the fixes you made so that
  they didn't fix one but cause others." Five parallel auditors, one per
  fix cluster (concurrency, overlay server, intake+spool, watchdog+sync
  +preflight+stream, dock), each told to assume the fix broke something.
  It had. Nine commits, one idea each, every one with a probe or a
  harness run:
- **apply --restart was dead on arrival (9997adf).** b545cbd's park
  write called `time.strftime` with only `_time` imported and caught
  only OSError — NameError killed the documented daily merge flow
  before anything was stopped, which also means that half of b545cbd
  was never live-fired despite "each with its own proof". Behind it:
  the park was never removed (the comment claimed a finally that did
  not exist — every apply fenced the watchdog for the full TTL), the
  daemon start hardcoded `systemctl --user` (root install: stopped by
  scope, never started, "daemon restarted" printed, station dark), and
  `_run` discarded exit codes. Also in that commit: `parked()` now
  treats a future mtime as stale (a clock step-back fenced revival for
  as long as the skew) with 30s slack for write/read jitter.
- **The control write-back popped by key, not by value (03d7c61).**
  b2acb62's fix ate more than the documented skip swallow: ANY
  same-kind verb posted mid-consume was destroyed unheard. Real cadence:
  fader to −10, SKIP, fader to −30 while the advance runs → the −30
  popped, the stale −10 acted on the deck the skip had just cut to. UI
  said −30, air played −10. `_seen` now carries the consumed VALUES and
  write-back pops only the identical verb; a different dict survives to
  the next pass; a skip over a seen false survives too. The media path
  also snapshotted state BEFORE the renderer call and merge_save_state
  overwrites all 12 STATE_KEYS — a slow-but-alive plane carried the
  pre-call snapshot back over concurrent writes; the snapshot is
  post-call now. And the docstring claimed the opposite of the code,
  which is how the next editor would have reintroduced the
  double-advance.
- **The cap contract was false, the thumb cleanup cleaned the wrong
  name (bab1c0d).** adf4f2f said "every handler-side plane call rides
  the bounded cap", but POST /music ran ensure_bed() INLINE first — 1-5
  raw RPCs, the one pin the commit promised was gone (live-fired 502 at
  10.5s). ensure_bed rides plane_call(8s) now. The thumbnail guard
  removed `out + ".part"` while the tmp is `<name>.part.jpg` — a failed
  ffmpeg left the real part-file forever; and the lock-map sweep could
  drop a HELD lock (media churn mid-generate) → two ffmpegs on one
  .part.jpg, the half-jpeg class the tmp scheme exists to kill — the
  sweep skips held names. The %00 fix guarded /files only; every other
  route fell through to the static handler and died on the NUL with no
  response — one guard now covers do_GET + do_HEAD. Honest note: my
  first cut of the NUL guard hit an UnboundLocalError on EVERY request
  (the /thumbs branch's function-local `from urllib.parse import
  unquote` made the name local to all of do_GET) — test_overlay_auth
  caught it before the commit; the local import is gone.
- **Intake's eviction pin missed the safety assets (6140583).** The
  daemon's pass pins fallback_files() + ad_files; intake's post-publish
  evict ran the SAME evict_cache with only on-air ±1 + operator pins —
  the loops are the oldest files in MEDIA, first in LRU order, so a
  near-cap intake could evict the fail-safe pool. Pins unified. The
  test suite then caught the enabling bug: fallback_files() caught only
  ValueError, so a MISSING playlist crashed intake (stress_cache died)
  and would have crashed the daemon's own failover on the one boot the
  fail-safe exists to survive — missing/corrupt now means the DEFAULT
  evergreen loops.
- **Small sharp fixes:** preflight walked a wrong-shape playlist
  unguarded (valid-JSON top-level list → AttributeError — the same
  traceback-instead-of-finding one step later) and its restore hint
  named the corrupt file itself + a backups dir nothing writes
  (1a025e5); the cookies warn-once flag latched forever so a SECOND
  cookies disappearance stayed silent — the healthy path re-arms it
  (eba5604).
- **The dock, three defects (8cedbfe, 1f05f41, 2641b77).** p-load
  staged the profile's rows but the spread kept the WORKING COPY's
  shuffle flag — a profile saved switch-ON loaded OFF and Apply wrote
  the drop silently (Playwright harness: checkbox False→True, disk
  False→True). Duplicate media: the marker picks the FIRST twin while
  the station plays the OTHER one, and the row menu protected only the
  marked row — the playing twin carried an ENABLED Remove; protection
  now matches by identity key (the marker's first-twin pick stays,
  documented: onAirIdx also feeds insert points). Biggest: while edits
  are staged, adoption is blocked, so the daemon's seam reshuffle left
  the undo stack's base at the OLD order — undo-to-base and Revert
  armed an Apply that silently un-reshuffled the station and could
  replay aired items (the overnight case, exactly when a 24/7 station
  reshuffles). The poll re-seeds the base when the live key sequence
  drifts under a pending session: Ctrl+Z home now finds draft == live
  and DISARMS the bar instead of arming an attack on the station's
  order (harness: draft lands on the reshuffled order, bar hidden,
  apply-armed false).
- **What the grill found SOUND** (so nobody re-audits it tomorrow): no
  lock cycle pl_lock↔END_LOCK (all 26 + 7 acquisition sites mapped);
  no verb resurrection; no double execution; flock does mutually
  exclude threads; intake publish is same-FS by construction (workdir
  under BROADCAST_ROOT — no EXDEV anywhere); the spool state cache is
  strictly cheaper than the old 2-stats-per-url; the resolve-cache
  prune turned the title watcher from unbounded re-resolves into a
  ≤3/5min budget (an improvement, not a storm); the watchdog cannot
  false-kill a daemon stuck in a resolve (heartbeat is its own thread);
  SSE never holds a lock on a slow client; the cap blast radius is
  per-call — the dock cannot be hammered into 504s; /files traversal
  is solid; the loudness pass cannot publish a half-written file.
- Deferred, with reasons, in KNOWN_ISSUES: the stream respawn blocks
  the playout pass on a dead network (architectural — resolve belongs
  off the playout thread), plane_call is a deadline not a bound
  (cancellation/sequencing is the real fix), the duplicate-marker
  tiebreak (touches insert points), and the dock small print.
- Verification this round: full stdlib suite green after every commit
  (spool, fallback, playlist_edges, selftest, control_consume — grown
  from 12 to 20 checks — overlay_auth, stress_cache), plus Playwright
  dock harness 28 PASS with only the three checks that documented the
  now-fixed bugs failing INVERTED.

## 2026-10-21 (evening) — the audit list worked through: 2 WAN blockers, the control race, 4 dock defects, and the long tail (13 commits)

- The PAT landed, so this pass ran as the operator: pull, rebase (the
  render-plane mask commits came in from the live machine mid-flight —
  PLANE_AUTORESTART + the hold-queue guard read clean, kept as-is), work,
  push. One idea per commit, each with its own proof.
- **The relay auth bridge (top blocker).** /ws + /obs hand out
  AUTHENTICATED render-plane control — the server completes OBS auth with
  its own secret. A token now makes those surfaces REQUIRE it
  (Authorization header or ?token= — browser WS handshakes cannot carry
  headers), compare_digest, and Origin:null REFUSES under a token instead
  of passing (that was the sandboxed-iframe hole). No token configured =
  the tunnel trust model unchanged, so nothing existing broke.
  test_overlay_auth.py live-fires the handler stack: 5 failures on the old
  code, 0 on the new.
- **MediaMTX auth (blocker two).** The shipped default is user:any/pass:any
  from any IP — i.e. anyone who could reach :9000 could inject on air.
  Three tiers now: loopback anonymous-everything (OBS monitor publish, ffmpeg
  decks, OBS SRT reads, WHEP proxy, API keep working with ZERO credential
  churn), seat users publish-only on ONE path each, everything else refused.
  Proved live against the real binary on this box: loopback RTMP publish
  accepted, remote anonymous SRT refused, seat-cam credential allowed on
  slot-cam but refused on monitor.
  - Lesson: **mediamtx does NOT expand ${VARS} in the YAML** — the literal
    string became the password (the live test caught it: correct pass
    refused, literal pass accepted). The config is a TEMPLATE now;
    setup.sh renders the real passes into $BROADCAST_ROOT/mediamtx.yml
    (600) and the unit runs that file. Adopted from the 24-7-Playout
    plugin's one genuinely good lifecycle habit: regenerate the config at
    provision time.
  - Lesson two: **v1.21's WebRTC ICE mux is 8189/udp, not 8892** — MoQ took
    8892 (and is ON by default with wildcard listeners; disabled here).
    Every firewall rule and doc that said 8892 now says 8189.
  - setup.sh: `--seat CIDR` (repeatable) opens SRT/WHIP/ICE per SOURCE
    NETWORK — nothing seat-shaped is world-open anymore; the old
    `ufw allow 9000:9001/udp` is gone. whip.html sends Basic (mediamtx
    internal auth), srt_test/send.sh embeds seat credentials.
  - Bonus catch: the release asset is `mediamtx_v1.21.2_...` — the URL
    stripped the v and 404'd, so setup.sh's mediamtx fetch was broken.
- **control.json race.** The panel's api_control RMW and the daemon's
  consume (which spans a whole advance — seconds) shared no lock: a skip
  posted mid-transition was EATEN by the stale write-back; a stale panel
  write could resurrect a consumed verb (double-advance). Panel holds
  pl_lock across its RMW; the daemon (consume_control, extracted from the
  loop) reads under the lock, acts unlocked, then re-reads FRESH and pops
  exactly the keys the original read contained. Verbs posted mid-consume
  survive; consumed ones cannot be resurrected. The one deliberate
  swallow: a skip posted during a skip consume (bare booleans have no
  instance identity; the refractory exists for slam-skips).
  END_LOCK moved to module level for the skip path.
- **The dock's four defects**, browser-verified red→green per defect
  (Playwright harness against a real panel on :8221): undo/redo stores
  POST-states (redo reaches the newest step; reload restores what the
  operator saw); the shuffle-at-end toggle stages, applies and seeds;
  the keyboard cursor never lands on a folded (display:none) row; the
  on-air/NEXT green bar follows ITEM IDENTITY (youtube-url-or-file), not
  draft slot index.
- **The long tail**, one commit each: respawns resolve FRESH (a mid-TTL
  403 used to respawn the same dead urls to the fault limit) +
  _RESOLVE_CACHE finally prunes; preflight diagnoses a corrupt/missing
  playlist instead of crashing on the exact boot it exists to diagnose;
  watchdog/sync share one systemd scope (sync STOPped system units but
  STARTed user ones — a root install stayed dark), watchdog surfaces
  systemctl exit codes, and apply --restart drops a .watchdog-park the
  watchdog honors (15-min stale expiry = the self-heal for an apply that
  died mid-flight); intake publishes ATOMICALLY (normalise into the
  workdir, verify, os.replace — no more partial broadcast-eligible files)
  and sweeps dead-pid workdirs (pid reuse can't adopt stale raws); the
  silent cookie fallback says itself once; /files answers a %00 path with
  400 instead of a dead connection; thumbnails generate to a .part.jpg
  and rename (a killed ffmpeg served a HALF jpeg forever — first attempt
  used .part alone and ffmpeg refused to guess the muxer: the live test
  caught it) with a 512-cap on the lock map; every handler-side plane
  call rides the bounded cap now (a wedged plane answers 504 instead of
  pinning threads for OBS_TIMEOUT each).
- **VPS answer for the 1080p60 target (budget $5-30)**: the honest
  anchors are that the laptop datapoint was OBS IDLE (no encode measured)
  and deck pipelines are -c copy (free) — so the whole story is llvmpipe
  render + x264. Three tiers priced in docs/VPS.md: CPX41-class 8
  dedicated vCPU (~$26-30) for 1080p60, CPX31 (~$15-18) for
  1080p30/720p60, CPX21 (~$9-11) for the shipped 540p30 profile. Shared
  burst vCPU will drop frames; 8 GB is the floor at 1080p60. setup.sh's
  OBS checklist now READS video.json/encoder.json instead of restating
  numbers (the "1080p/6000k vs 540p/2500k" two-truths bug).
- From the plugin deep-dive (its v0.8.41 release ships SOURCE — 12k lines
  of C++ mined; the git repo itself is binaries-only): their mediamtx
  config is WORSE than ours (no auth, wildcard binds) — but the adopt
  list is real: per-seat signal status in the dock (3s paths/list poll
  + OBS media state per row), planned start/end times per rundown with a
  60s drift warning, Now/Next viewer overlay on the SSE bus with their
  push-on-change cadence, config backup/auto-recovery (atomic save +
  parse-validated .bak restore), Discord rundown notifications,
  next-up event ~20s before item end. REJECT confirmed: their mediamtx
  config, alwaysAvailable slates (masks the dead-input state the
  watchdog uses), recording, the OBS-plugin architecture (12k-line Qt
  dock inside the OBS process is the cautionary example), Twitch
  automation, their live-feed failure posture (display-only; our
  failover→fallback→Tech Diffs is ahead).
- Sandbox notes: mediamtx runs here, so the auth matrix was proven
  against the real binary (P1-P7). This sandbox's ffmpeg SRT client
  EOFs instantly against mediamtx v1.21 WITH and WITHOUT auth — a
  client incompatibility, not the config; the real lab SRT flow
  (laptop-to-laptop, OBS) was proven earlier and seat streamids now
  carry credentials.

## 2026-10-21 — full-tree audit (5 agents) + 13 same-day fixes; fresh-clone baseline established

- Context: the station now has a second machine — a sandbox VM standing in
  for the migration target. First act there was a clean baseline, and the
  baseline itself caught the first bug: `test_spool.py` FAILS on a fresh
  clone (`state -> ready`) because `spool.state()`'s cache invalidated on
  the spool dir's MTIME, and this box's filesystem never moves it. A
  finished download reported "fetching" for a full second. The cache key is
  now the directory's entry set + the spooler's current job — the exact
  inputs every state transition is made of. Lesson: the mtime was a proxy
  for the truth; proxies lie on filesystems you haven't met yet.
- Same fresh-clone baseline killed a second bug: `pl_lock()` opened
  `broadcast/.station.lock` without ensuring `broadcast/` exists, so
  `daemon.py selftest` — the documented first step — crashed. makedirs, one
  line, selftest green on a true fresh clone.
- Five parallel audit agents then read the whole tree (daemon / panel+dock /
  overlay+stream+intake / infra+units+setup / the KPLiveDE 24-7-Playout
  plugin for feature gaps) and returned ~50 findings. Fixed same day, one
  idea per commit, each verified red→green where a seam existed:
  1. **File ad breaks self-destructed** — `play_ad()`'s file branch wrote
     `state["ad_start"]` before `state` existed on that path; every file
     break raised UnboundLocalError into the unwind path (flash to Ad
     Break, flash back, latch nothing, re-fire mid-rolls every poll).
     Reproduced with FakeRenderer + temp root before and after. The write
     was dead: nothing reads `ad_start` anywhere.
  2. **The shuffle seam rule never saw stream items** — `item_key()` missed
     the `youtube` field, so just-played link items had key None and the
     avoid-set was empty: 43/200 shuffles led the next cycle with the video
     that had just ended. Regression checks in test_playlist_edges §6 (any
     seed that leads with the just-played item fails).
  3. **Boot park muted the on-air deck** after a daemon restart onto a
     spooled YouTube item (naive youtube-key check vs advance()'s
     spool-aware one — silent air for the rest of the item). Both now use
     `stream_item_on_air()`.
  4. **One pause wiped the saved mix** (deck_volume_db=None through
     merge_save_state); **the stream respawn budget never persisted**
     (bumped a throwaway dict; respawn-every-poll storm, each costing a
     resolve + up to 45s of ready-waits inside one pass).
  5. **File items never got their planned mid-rolls** — advance()
     pre-seeded `marks_for` with the new item's seed, which is exactly what
     the poll's lazy-fill gate compares against. Streams plan at cut; files
     now leave the previous seed so the gate opens when the media clock
     reports a duration.
  6. **Eviction could eat the fail-safe loops and the ad pool** near the
     cap (the pin set only knew playlist files) — failover() would have
     found an empty pool and held Tech Diffs immediately.
  7. **`/library` + `/ads` read request bodies inside pl_lock** — a
     drip-feeding client held the cross-process flock and froze playout
     (the loop takes that lock ~20× per pass). Bodies are read before the
     lock now; live-fired against the real handler stack.
  8. **The relay wedged at its session cap on a malformed Identify**
     (KeyError/TypeError escaped the except tuple, done_relay skipped) and
     accepted client-declared frame lengths up to 2^63 (memory bomb). Both
     fixed; 32MB cap matches daemon._WS.
  9. **GET /music's bed probe raised NameError on every call** (class-body
     function called bare from a method — class scope is not in method
     lookup), so the page answered plane:"?" forever. Module function now.
  10. **Panel**: the playlist RMW was torn (read outside pl_lock — the
      exact race AGENTS.md rule 2 exists for); the legacy page
      interpolated YouTube titles unescaped (XSS in a surface that can
      restart units); /api/thumb double-encoded filenames (every spaced
      name 404'd). All fixed + smoke-tested.
  11. **setup.sh armed the publish leg** (enable list took every
      station-*.service — with a real key, provisioning = going live),
      never enabled station-watchdog.timer (the 5-minute self-heal layer
      did not exist on provisioned boxes), and a double-sed turned every
      EnvironmentFile line into a bare path systemd silently drops.
  12. **BROADCAST_ROOT split-brain**: only the daemon unit got the env; on
      the documented /var/broadcast VPS layout the panel read the repo
      tree while the daemon played /var/broadcast. panel.py honors the env
      now (spool probe stays repo-relative), setup.sh injects it into
      every unit.
  13. **Hold states alerted every pass** (all-missing = one WARN per item
      per re-kick; a night of that rotates the 5,000-row trail over).
      hold_alert(): first occurrence, repeats hourly.
- Not fixed (ranked, in docs/KNOWN_ISSUES.md "2026-10-21 audit"): the relay
  auth bridge + Origin:null guard bypass (WAN-blocking, needs
  STATION_TOKEN-first), MediaMTX with no publish auth + SRT open to the
  world, control.json's lock-free cross-process RMW, the dock's broken
  undo/redo + dead shuffle toggle + hidden-row keyboard cursor +
  index-into-draft markers, stale-URL respawns, non-atomic intake publish,
  the thread caps applied once, watchdog scope/exit-code blind spots,
  sync.py scope mixing, the VPS-shaped OBS unit, `_RESOLVE_CACHE` growth,
  silent cookie fallback, preflight crashing on the boot it diagnoses.
- From the 24-7-Playout plugin comparison, the borrow list (value/effort):
  a live Now/Next viewer overlay fed by the SSE bus (the one viewer-facing
  gap), planned start/end times per rundown, Discord rundown notifications,
  config backup/auto-recovery, calendar view. Rejected as already-parity or
  against station decisions: recording, per-item loudness UI, auto-apply,
  OBS-plugin architecture, Twitch-centric automation.
- Sandbox lessons for the record: the OOM-killer here SIGKILLs test runs
  under memory pressure and the wreckage stalls subsequent runs (stress_cache
  "hung" twice on wreckage, passed 7/7 clean — the worklog's "verification
  runs need quiet windows" applies to this box too); faulthandler +
  file-redirect is the way to autopsy them.

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

## 2026-10-16 — Program video return (LIVE finally means live) + unit hygiene

- LIVE-as-screenshots was the wrong species: each frame is a main-thread
  render+encode, so "10 refreshes/sec" would deafen the plane, not inform
  the director. Built the real pipeline instead: lab profile streams
  program A/V (rtmp_custom) to a new MediaMTX `monitor` path; /studio
  program pane plays it over WHEP with vanilla RTCPeerConnection
  (sub-second, independent of obs-websocket AND screenshots).
- Two findings en route, both load-bearing: (1) this MediaMTX build
  rejects undefined paths (`path 'monitor' is not configured` — added to
  mediamtx.yml); (2) WebRTC H264 has no B-frames — MediaMTX closes the
  session mid-handshake, x264 veryfast emits them, simple-mode OBS has no
  custom-x264 knob, so the lab profile runs ultrafast (verified: 60s+
  real-time playback, rs=4, clock advancing). Monitor output 960x540.
- WHEP audio deliberately video-only (AAC not WebRTC-playable in Chrome;
  meters cover audio visually). Signaling proxied same-origin (/whep),
  ICE direct. Preview pane keeps snapshot-live; Refresh stops video first.
- Lab profile was EMPTY (no service/output/video settings — the "host
  standard" was aspirational). Now: service.json + basic.ini [Video] +
  [SimpleOutput] ultrafast, all machine-local under ~/.var, re-apply list
  in docs/VPS.md. Lab ws server is passwordless (loopback-only, harmless;
  VPS must set OBS_PASS).
- Unit hygiene: `systemctl stop station-obs` never reaped flatpak/bwrap
  (old obs held :4455 while the new instance parked at "already running")
  — ExecStop now pkill -x obs/bwrap; mirrored to station/systemd. Also:
  station-daemon tracks obs restarts (a plain `stop station-obs` takes the
  loop down too — document, don't fight).
- Daemon/loop untouched by the monitor (check_stream stays silent while
  active; stopping later fires the one lab-normal CRIT). CPU: box already
  saturated by llvmpipe; the 540p ultrafast encode adds little on top.

## 2026-10-16 (early) — Program video return goes live (WHEP, sub-second)

- LIVE-as-screenshots retired for program: OBS lab profile now streams
  program A/V (rtmp_custom) to new MediaMTX `monitor` path; program pane
  plays it via vanilla WHEP (return.js). Verified: 90s+ playback,
  readyState 4, clock real-time; new joins get video in ~4s.
- Path demanded two fixes: (1) this MediaMTX needs paths listed
  (`path 'monitor' is not configured`); (2) WebRTC H264 forbids B-frames
  — session closed mid-handshake every time until x264 ran B-frame-free.
- Encoder archaeology (for the record): simple mode ignores keyint_sec
  AND the x264-custom string (absent from the plugin binary — the old
  `x264Settings=bf=0` was a no-op); ultrafast implies bf=0 (proven: the
  session held). Short GOP needs ADVANCED mode + streamEncoder.json
  (`keyint_sec:2` → `keyint: 60` in the encoder log). Simple+ultrafast
  was the working fallback throughout.
- Gotcha drilled twice tonight: `systemctl stop station-obs` does not
  reap flatpak/bwrap (ExecStop pkill added), and unit stop/restart takes
  station-daemon with it (restart it after). Daemon loop otherwise rides
  plane restarts via wait_ready.
- Monitor stream is MANUAL (Start Streaming; lab routes locally). Nothing
  auto-starts it — deliberate (VPS semantics differ). /studio says so on
  the button when the path is dark. Stopping later fires the one
  lab-normal CRIT; check_stream stays silent while active.
- WHEP audio deliberately video-only (AAC unplayable in Chrome WebRTC);
  meters cover audio. Preview pane keeps snapshot-live.

## 2026-10-16 (early) — Config-as-code: capture/diff/apply + A/V return sound

- station/sync.py: OBS<->repo 1:1 machine sync. capture (scenes/items/
  inputs/volumes/filters/video/service/transition/encoder.json, secrets
  redacted to $secret + leak-scanned, paths tokenized media:/overlay:/),
  diff (volatile runtime excluded: program/preview cuts, A/B deck eyes),
  apply (live RPCs + profile files + optional restart that parks/ resumes
  the daemon and merges geometry while obs is dead). Round-trip PROVEN in
  lab: planted +10px -> diff caught it (1 line) -> apply --restart ->
  live 10.0 -> revert -> 0.0 -> diff clean.
- Three traps found by doing it, not theorizing: (1) SetSceneItemTransform
  rejects correct payloads server-side (matches upstream #1299) — geometry
  goes by file, never RPC; (2) a running OBS autosaves over the collection
  file and eats merges — merge only while dead (kill-verified); (3) OBS
  trusts stale *_rel caches over fresh absolute pos (file said 10.0,
  plane rendered 0.0) — merge deletes pos_rel/scale_rel/bounds_rel
  (template ships without them; OBS regenerates).
- A/V return: monitor-av path (ffmpeg AAC->Opus repack, own unit) +
  return.js tries av-then-video + speaker toggle. Verified: live Opus
  track, unmute works. /monitor reports both paths; /whep?path= proxied.
- Docs: docs/machine-sync.md (new-device + daily flows, what syncs and
  what deliberately doesn't, known edges). VPS.md re-apply list corrected
  (advanced + streamEncoder.json verbatim).
- Niek/obs-web studied for the preview question: same 1fps screenshot
  technique + meter events; nothing simpler to integrate (already beyond
  it), and GPL-3.0 forbids copying into this MIT tree anyway. Ideas only.

## 2026-10-16 — Studio Player evaluation (source read, no install)

- Read Substazz/studio-player source (70KB StudioPlayerDock.cpp): playback
  is a localhost HTTP page (127.0.0.1:<port>/player.html) inside a plain
  browser_source, driven by JS-event proc calls; queue advance on "ended"
  is INTERNAL (playNextQueuedVideo). No yt-dlp/mpv/ffmpeg backend, no
  media-state broadcast for ASS to watch, no remote API — remote surface
  is frontend hotkeys only (blind, no queue readback). License GPL.
- Verdict: nothing to merge; render-plane install refused (headless dock
  UI unusable, v1.0.0 in-process crash risk to the air chain, queue
  invisible to config-as-code/alerts/prefetch). MBA-side evaluation is
  the safe path (caveat: upstream issue #1 is macOS load failure).
- ASS necessity rejected for our architecture: single program scene +
  deck-swapped inputs means no scene-hopping for playout; daemon already
  owns ended-events, watchdog, alerts. Only genuine gap is wall-clock
  scheduling (belongs in cron/daemon, not a GUI plugin).

## 2026-10-16 (evening) — E2E compressed-time proof + ad automation + event drought

- User asked for practical proof, not code review: built it. 10s labeled
  clips stand in for 2h videos, 6s ad, OBS+daemon+local files only
  (station/generate_test_clips.sh; procedure + evidence in docs/e2e-test.md).
- PROVEN live: back-to-back advance, ad cutaway (mute+cut+roll), ad return
  (unmute+Meet+resume, no skip/replay), mid-run playlist append playing,
  fault safety (stall -> CRIT + TECHDIFF hold + self-resume).
- New product: daemon ad breaks (playlist ad_every/ad_files; AD scene;
  deck mute; return routing with operator-moved-on guard; watchdog
  watches AD input mid-break; boot clears stale break flags).
- Three load-bearing discoveries, all fixed same night:
  1. Daemon Identify sent NO eventSubscriptions: zero events ever; the
     loop had been advancing via the ~60s re-kick all along. Fixed.
  2. ffmpeg_source natural ends do NOT emit MediaInputPlaybackEnded here
     (proven: restarted clip + 40s silence on the wire). Advance is now
     poll-driven (2 straight ENDED polls enqueue like an event).
  3. /studio listened for events on op 4; real servers send op 5. Every
     event handler was dead code — the "demo meters" mystery, one line.
- Inter-transition latency ~10-30s CONSTANT (poll cadence), negligible at
  real durations. Live state fully restored after (playlist/state/
  collection backups back, ad stage removed, loop on live items).

## 2026-10-17 (night) — zero-disk streaming decks: YouTube-link playout shipped

User pinned the real-world constraint: approved content arrives as YouTube
links; no storage budget. Decision: kill download-to-disk playout entirely;
stream the links live (intake/cache/eviction archived). Studio Player and
ASS evaluated AGAINST the constraint and refused: Player cannot fetch, ASS
cannot fetch nor set inputs; mpv needs a window headless lacks. Built:

- stream.py: resolve (dump-json + two fresh HLS urls, cookie-aware) ->
  one ffmpeg (-i hlsV -i hlsA -c copy -f flv rtmp://127.0.0.1:8554/..RTMP)
  -> MediaMTX slot-stream-a/b -> OBS STREAM_A/B persistent-retry inputs.
  (~15MB RAM + ~5% CPU per deck; feed dies with its slot.)
- Quality ceiling: 720p (YouTube serves automation clients split HLS only,
  that is the honest top). Pairing with copy remux keeps CPU at zero.
- daemon: playlist items may carry `youtube` (+ optional compressed
  `duration`), advance() spawns+waits the feed on the idle deck, cuts under
  the transition (hides BOTH other decks of BOTH kinds), keeps wall-clock
  state (stream.start/dur), stops old feed after cut, polls: EOF at dur+8,
  feed-death respawn (<=2) else advance, ad breaks mute STREAM decks, boot
  unwind, prefetch resolves next links in background threads with 30min
  TTL cache.
- Landed from live firefights: RTSP unsuitable for YT audio (headerless
  AAC; FLV works), restart_on_activate WEDGES an rtmp ffmpeg_source
  permanently (A died; replaced with persistent-retry), bot-wall on
  anonymous resolve — cookies via YTDLP_COOKIES (secrets.env),
  sync capture needs wide OBS_TIMEOUT under load storms.
- E2E (compressed via duration slots, public videos, cookies on): three
  cuts on the journal (03:22:40, 03:24:05, 03:25:23 + shuffle wrap
  03:26:37), Sintel and Big Buck Bunny visually on program, rotation
  wrapped cleanly, live state restored to Loop A after, feed procs 0.

## 2026-10-17 (late night) — ad links + WHIP seats restored; ad links shape

- play_ad pool is now ad_files OR ad_links (YouTube URLs streamed zero-disk
  through slot-ad -> STREAM AD input in the ad scene). Stream ads spawn
  BEFORE the cut (no black air), ride the same wall-clock EOF, and the
  return path is unified (ad_return: unmute, stop AD feed, back to program,
  advance). Watchdog: stream-ad breaks skip check_source (feed health owns
  the slot, rtmp state is not worth watching).
- Media manager learns a YouTube field: paste a link on /media and it airs
  without ever touching disk; optional seconds compress the slot. The
  rotation/pending split now knows the family.
- Whip.html (/whip): browser publisher for the contribution seats —
  screen -> slot-screen, camera(+mic, lip-sync rule) -> slot-cam. WHIP POST
  + non-trickle answer; per-seat state line; Stop returns the seat to
  black. Designed for MBA over the tunnel; token field for when MTX
  publishes need auth.
- Seats rebuilt live (they had quietly vanished from the running plane):
  created via RPC with template URIs, PLUS the restart_on_activate=False
  lesson baked into both the live plane and scenes.json.template.
- proof: ffmpeg SRT publisher -> slot-screen: MTX reports readers=1 (the
  OBS seat pulled it up by itself) and the seat screenshot shows the
  testcard. ffmpeg 9's WHIP muxer is half-baked here (no video frames out);
  browsers are the WHIP client that matters, endpoint OPTIONS=204.
- Plane wedge bookkeeping: obs-websocket 5.7.4 accepted connections but
  answered nothing for long stretches (correlates with CEF spin at 240%);
  GetSceneList specifically wedged; a zombie OBS instance survived one
  restart (killed from /proc; unit said active while its listener was
  dead). Seat capture deferred until a calm window; on-disk template is
  the source of truth meanwhile.

## 2026-10-17 (dawn) — deck + seats get a face; mic seat; cookies courier

- media.html rebuilt from OBS-bare to "SMILE Deck": paste-a-link hero
  (stream family is the default), advanced drawer for intake/filters,
  hover-reveal row actions, up-next highlight, live/fetch/pin/missing
  pills, music bed card, collapsed waiting/parked/fetched sections, toast
  errors. Same endpoints, no new server work.
- whip.html rebuilt to match and FACT-CHECKED against reality: three seat
  cards (slot-screen, slot-cam, slot-audio), per-seat toggle + Share all
  three; host/token fields for the future Vercel front. slot-audio is NEW
  (microphone seat): mediamtx path + OBS "Slot Audio" ffmpeg_source in
  Q&A (rtmp read, persistent-retry flags).
- cookies_push.sh: MBA-side courier — scp cookies.txt up, resolve-probe
  THROUGH the uploader (yt-dlp rejects the bad session before it lands),
  atomic swap with a one-deep .bak. Daemon reads the file per spawn, so
  NO restart: refresh can run daily, takes seconds.
- riding fix: overlay route additions only exist after restarting
  station-overlay (it serves python handlers from its binary启动 memory).
  /whip 404'd for the operator until the restart — lesson logged.

## 2026-10-17 (morning) — the Library: segmented media manager + mid-roll engine

- /music GET used to hang the whole page when the render plane wedged
  (RPC with no bound). It now probes through a 4s thread cap and answers
  "plane: slow/down" instead. THE page hangs are why the deck looked dead.
- daemon: mid-roll ad engine — ad_plan (threshold_min / mid_rolls /
  min_gap_min) with a seeded planner (plan_rolls) shared by /media and
  the runtime: what the UI previews is what fires, ±10s. Streams plan at
  cut, files learn their clock lazily. Break start parks the content
  stream record in stream_pre (file ads used to WIPE it), break end
  restores it. Mid-rolls resume the SAME item: return advances only when
  the item finished under cover.
- overlay_server: GET/POST /ads (config + per-item planned marks via the
  same daemon planner), FALL-GENERATIC /thumbs/<file> poster frames
  (ffmpeg 25% in, cached in media/.thumbs).
- media.html REBUILT as the SMILE Library: right-hand segment rail
  (Rotation / Available / Ads / Music bed / Automations), grid+rows
  toggle, ffmpeg/ytimg thumbnails, hover actions, edit dialog, fetch
  queue + intake history inside Available. Automations view = rule cards
  (cycle cadence, long-form mid-rolls) + per-item TIMELINES with exact
  break markers, Brightcove-style.
- whip.html: Share→Connect everywhere + insecure-context banner (the
  operator's 404-equivalent: http://LANTORD-blocked mediaDevices → dead
  page). SSH-forward recipe printed in-place.
- browser-proven: seats page publishes a real camera (slot-cam READY,
  webrtc source); library page renders thumbs/segments; plan pipeline
  (POST /ads → planner → UI markers) shown end to end.

! mid-rolls have NOT yet fired against a live plane (engine + planner
! selftested only). Real proof: long item on air, watch break/return.

## 2026-10-18 (03:xx) — audit round: leaks closed, mid-roll engine fixed, ad breaks proven live

- SECURITY: any web page in any LAN/browser tab could POST to /state//obs/
  /library anonymously (text/plain = no CORS preflight) and even read the
  OBS stream key via GetStreamServiceSettings. Now: Origin/bearer guard on
  every POST + the WS relay. Same-origin pages, curl, OBS panes (file://)
  pass; other origins need the STATION_TOKEN env (set it for VPS era).
- BUGS FIXED: file items were permanently ineligible for mid-rolls
  (None-mark gate); advance saved stale state over watchdog faults; broken
  since_ad reset alerted forever; intake temp-dir collisions between
  parallel prefetch/music adds; playlist writes now flock cross-process;
  OBS_PASS was journalled via ?pass= URLs (log strips query now).
- BOOT REPAIR: the saved collection was missing "SMILE | Ad Break" (+AD
  Break/STREAM AD inputs) — every OBS restart failed ALL file ads at
  runtime ("No source `AD Break`"). ensure_ad_plane() now rebuilds them
  at loop start; non-looping so the END event is the return lever.
- LIVE PROOF: file-ad break -> return -> advance on air; YouTube link
  stream-ad break -> MTX slot-ad publish -> 61s -> return -> advance.
  Console + Library verified against the new guard.
- mediamtx: RTSP/RTMP/HLS/API loopback-only; SRT + WHIP/WHEP stay public.

! capture still wedges on a filter-list RPC (plane can go deaf mid-walk)
! mid-rolls never live-fired (engine+planner selftested; same return path)

## 2026-10-18 05:00 — real-content demo + plane/daemon bootstrap fix

- intake.py now honours YTDLP_COOKIES=browser:<profile> (and YTDLP_BROWSER)
  like stream.py already did: cookies.txt goes stale the moment Chrome
  rotates v11 keys; reading the desktop profile live side-steps the 429
  login-wall (cookies_push.sh file-flow stays the VPS route).
- Fed the station five real clips (HDF Presidential/Wash/Collins, Menta
  motivation, Almond) as 12s slices (yt-dlp --download-sections) plus two
  full items; nothing more than needed was downloaded.
- unit fix (root-caused): station-daemon REQUIRED station-obs, so the
  watchdog's own "plane unreachable → stop station-obs" stopped the
  daemon too and nothing came back (04:41 wedge). Now Wants=, daemon
  survives a plane restart.
- live demo cycle proven on air with real clips: playlist rolls all five,
  ad break fires at every transition (ad_every=1, pool [Menta, Almond]),
  returns, advances, reshuffles at the end. Console/Library healthy.

## 2026-10-18 16:15 — TD desk over VNC (MBA) proven

- Installed x11vnc + enabled sshd (user-ran sudo); station-vnc unit added:
  x11vnc on :99, localhost-only, --rfbauth password, UnsetEnvironment=
  WAYLAND_DISPLAY (else x11vnc exits "Wayland sessions unsupported").
  MBA flow: ssh -L 5900:127.0.0.1:5900 -> Screen Sharing vnc://127.0.0.1:5900.
  macOS Screen Sharing CANNOT cope with a passwordless VNC server (hangs),
  hence the -rfbauth. UFW had to allow 22/tcp on the box.
- obs_click.py gained --key <keysym> (XTest KeyPress/KeyRelease): used to
  dismiss the "OBS is already running" singleton dialog (Return key) since
  its Launch Anyway button ignored two pointer clicks.
- OBS main window resizes via python-xlib XMoveResizeWindow (live, no WM);
  geometry re-written into user.ini while running so the next boot stays
  fullscreen 1920x1080.
- Removed --minimize-to-tray from station-obs ExecStart: on tray-less
  Xvfb some boots hid the main window entirely (WebSocketServer ran, black
  screen). Lesson lives in AGENTS.md too.

## 2026-10-18 17:00 — 720p VNC desk + deterministic boot fullscreen

- Xvfb :99 screen shrunk 1920x1080 -> 1280x720. Program output stays 1080p;
  only the OBS control UI changes, so VNC/MBA traffic drops a lot. Window
  fills the whole virtual screen (resized live; screenshot verified).
- station-obs unit gained an ExecStartPost that polls for the main OBS
  window and forces it to the full 1280x720 frame: OBS ignores its saved
  geometry on some boots (opened 896x482 default this boot) and geometry
  ini pinning alone is not deterministic.
- station-obs ExecStartPre now also reaps stale obs/bwrap processes before
  every boot (systemctl stop already didn't reap the flatpak tree), kill
  source for the "OBS is already running" modal at boot.
- obs_click.py: --resize X Y W H helper (idempotent XMoveResize on the
  main window; exit 1 when no window matched so ExecStartPost can poll).
- After the xvfb/obs bounce the daemon sat on a dead socket (recv timed
  out, deduped WARN loop) and the watchdog was holding OFF-AIR over the
  earlier PLAYOUT_B stall; /intent/resume cleared the hold and cycling
  resumed (ad break + return verified on air again).

## 2026-10-18 17:50 — console/studio archived; port debris trimmed

- Git branch `archive/console-studio` snapshots the old control surfaces.
  On main: station/studio/, console.html, media.html, test_studio_ui.py
  removed; overlay_server dropped the /console /media /studio routes
  (+ now-unused _serve_tree; /whip, /files, overlays, /events, /state,
  /intent, /thumbs, /music, /obs stay).
- station-overlay now binds 127.0.0.1:7070 (was 0.0.0.0); the MBA reaches
  every control surface through the SSH tunnel only. The future single
  page (media + TD mgmt) will be served by this same server.
- monitor chain deleted: station-monitor-av.service disabled + removed
  (it sat restart-retrying 11,571 times toward a `monitor` path OBS never
  publishes on the real station) and mediamtx paths monitor/monitor-av
  dropped from the config.
- mediamtx webrtc note: v1.21 has a hard-coded second wildcard UDP
  listener on the ICE mux port; specific-LAN-IP binds cannot coexist with
  it (bind: address already in use loops). Exposure of 8889/tcp+8892/udp
  is handled at the firewall instead; 7070/8554/8888/1935/9997 all
  loopback, VNC 5900 loopback, ssh 22 only socket.
- test_playlist_edges.py: FAILURES none empty view.

## 2026-10-18 21:55 — VNC outage root-caused (not the firewall)

- x11vnc crash-looped (restart counter 1387) since the 17:00 speed pass:
  this build does not accept -compresslevel 0 ("unrecognized option",
  exit 1). Remove it; -wait 5 -defer 10 stay. 5900 listening again.
- Lesson for MBA debugging: when Screen Sharing "hangs" first ask
  `systemctl --user is-active station-vnc` + `ss -tlnp | grep 5900`
  BEFORE blaming UFW.

## 2026-10-21 (late) — the render plane is now VPS-shaped: the unit is rendered per box

- Top open defect from the regression pass: station-obs.service assumed a
  real X session on :0 with hardware GL — none of which exists on the
  $5-30/mo box this project is aimed at. Three holes: no display for a
  headless boot, no LIBGL_ALWAYS_SOFTWARE path for a GPU-less one (it was
  stripped 2026-10-20 because it hurt the iGPU lab box; on a VPS the same
  flag is the difference between llvmpipe and "OBS cannot create a GLX
  context"), and BrowserHWAccel=false only written when global.ini ALREADY
  existed — a fresh box's first boot skipped the guard and died of the CEF
  GPU-process crash ~30s in, every boot (the 2026-10-15 class of outage).
- setup.sh now detects the box shape (any X socket in /tmp/.X11-unix, any
  /dev/dri/renderD*) and RENDERS the installed unit, the same
  provision-time-render pattern the mediamtx config uses: headless ->
  DISPLAY/PLANE_DISPLAY :99 + --env=LIBGL_ALWAYS_SOFTWARE=1 (flatpak form,
  the one proven before it was removed); session-without-GPU -> :0 kept,
  software GL forced; lab -> untouched. Every run reinstalls the unit from
  the pristine git copy first, so renders never compound; the render's
  seds are verified by grep and FAIL LOUD on a mismatch (a silent miss
  would boot a :0 plane on a box with no :0 — the exact wedge this
  prevents). The guarded LIBGL insert survives a future flow that renders
  without reinstalling.
- global.ini missing -> setup.sh creates it ([General] BrowserHWAccel=
  false); existing files keep the old enforce/append paths. Idempotent
  across re-runs (harness-checked).
- station-xvfb.service: 1920x1080x24 -> 1280x720x24, matching the live
  desk (shrunk 2026-10-18, never committed) and the forced window frame;
  on a VPS every extra pixel is llvmpipe CPU.
- station-vnc (wayvnc) needs a Wayland session to mirror; on a headless
  box it would crash-loop forever — the monitor-av class of debt (11k
  restarts doing nothing). setup.sh now skips installing AND enabling it
  when no session exists; the headless TD-desk recipe (x11vnc on :99 over
  an SSH tunnel — the lab's own proven 2026-10-18 flow) is documented in
  VPS.md §6.
- Regression grill ON THIS FIX (the operator's standing order), pre-commit:
  (1) first cut had a broken empty if-branch (left by an edit) that would
  have re-planted the LIBGL flag inside the headless sed — caught by
  re-reading the diff before commit; (2) the LIBGL sed insert was NOT
  idempotent standalone — now guarded, and moot anyway since the install
  loop resets from git first; (3) set -e survival of the `ls &&` detection
  lines proven under `set -euo pipefail`; (4) the render harness replays
  BROADCAST_ROOT injection THEN the render, for all three box shapes,
  against the real unit text — headless asserts :99 everywhere + exactly
  one --env=LIBGL flag (the earlier "3 occurrences" scare was the unit's
  own COMMENTS mentioning the string; the guard matches the --env= prefix,
  which comments don't carry); (5) 1920x1080 stragglers: only the
  intentional history comment.
- Verified: bash -n clean; harness green for lab/session-nogpu/headless;
  full stdlib suite green (spool, fallback, playlist_edges, selftest,
  control_consume, overlay_auth). NOT yet proven: a real llvmpipe boot
  with air — that is VPS.md migration step 3, on the box itself, and it
  stays on the record in KNOWN_ISSUES.

## 2026-10-21 (late, 2) — the respawn left the playout pass: the deck can no longer be frozen by a dead network

- The last architectural defect from the regression pass: a stream feed
  death was handled INLINE in the daemon's single playout thread — fresh
  resolve (3x20s subprocess timeouts), spawn re-resolve, then 15x3s of
  ready-wait, up to twice per item. A dead network froze the deck AND
  every other loop duty (operator control, advance, the fail-safe watch)
  for up to ~4 minutes per attempt, and on resolve failure the stale
  cache fallback burned the whole ready-wait window before the give-up.
- New shape, same contract: the pass DETECTS (cheap poll()), COUNTS and
  KICKS; the slow work runs on one background thread per deck
  (_respawn_work), whose result is adopted only if the item it was
  spawned for is still the one on air. One attempt per deck at a time
  (_STREAM_STATE["respawning"]), two per item before the give-up routes
  STREAM_EOF — the inline contract, kept, plus new observability: the
  kick itself is now a WARN ("respawn N starting in background").
- Three structural enablers: (1) the media-ended queue moved from a
  main() local to module-level _ENDED — a thread cannot route a give-up
  EOF into a closure list, which is exactly why the respawn was inline
  in the first place; (2) cleanup inside the thread is by PROC IDENTITY,
  never deck key — while an attempt sits in its ready-wait the world can
  hand the deck to a successor (operator skip, ad return), and the old
  deck-keyed stop_feed would have killed the successor's feed; (3) the
  EOF consumer hardening: on_ended refuses a STREAM_EOF when no stream
  item is on air (a queued EOF outliving its item used to advance past
  whatever the operator just cut to).
- cached_resolve's docstring now tells the truth: force=True PREFERS
  fresh urls; on resolve failure the cached meta gets one more try
  (HLS urls expire in hours, the cache is 30 minutes — a blip resolve is
  worth a retry), and the attempt cap still ends a dead item.
- Regression grill ON THIS FIX (standing order), findings applied
  pre-commit: (a) the crash path originally leaked the adopted feed (an
  orphan ffmpeg publishing a hidden input) — feed handle moved outside
  the try, crash path stops by identity; (b) my first test assertions
  were wrong twice (index semantics: it points at NEXT, so a cut to item
  2 keeps index=1... the invariant holds, the test lied; FakeRenderer
  records a file load as "file", not "media") — the code was right both
  times, the harness now asserts the real contract; (c) TOCTOU on the
  give-up EOF: relevance is checked under END_LOCK immediately before
  the append, leaving a ~1-poll window for a stream->stream skip to slip
  a stale advance — bounded, on the record in KNOWN_ISSUES (closing it
  fully means carrying the url in the sentinel; not this pass); (d) the
  pre-existing stale-EOF-after-ad_return case: pre-dates this change,
  the new code creates none.
- Verified: new station/test_stream_respawn.py (29 checks: pass returns
  in 0.00s with a 1.5s resolve scripted; no double-bump in flight; EOF
  exactly once across attempts; exhaustion kicks no thread; AD path;
  late finish stopped by identity with no EOF; crashed attempt cleans up
  AND still routes the give-up; stale EOF cut nothing; current EOF
  still advances). Full stdlib suite green after the change (spool,
  fallback, playlist_edges, control_consume, overlay_auth, selftest).
  NOT live-fired against a real dead YouTube link yet — the next real
  feed death on the station is the live proof (watch for "respawn 1
  starting in background" then "respawned (1)" with the pass never
  going BUSY).

## 2026-10-21 (late, 3) — plane_call is now a bound: the stale tail of a timed-out sequence dies "superseded"

- The regression pass deferred this as architectural: plane_call's 504
  answered "we stopped waiting", not "it did not happen" — the abandoned
  call kept the plane lock and a timed-out MULTI-RPC sequence (an INTENT,
  ensure_bed) could keep landing its remaining RPCs up to OBS_TIMEOUT
  later, on top of a newer intent that fired meanwhile. That is the "late
  cut overrides a retry" shape: the plane ends on the older intent.
- Fix: a generation guard, at the only point that can be atomic. Every
  plane_call takes the next generation (overlay_server._PLANE_GEN); its
  worker thread stamps it into the renderer's thread-local
  (OBSRenderer._tls.gen); _call — holding the plane lock — refuses an RPC
  whose generation is OLDER than the newest one that already SENT
  (OBSAppError, connection stands), and updates _sent_gen under the same
  lock. Check+send atomic means a stale RPC can never slip between its
  check and its send. The daemon's own calls carry no generation and are
  never refused — the guard exists only where the deadline exists.
- Semantics, stated: within ONE call its whole sequence lands (same
  generation); once a NEWER call has sent, every older in-flight
  sequence's remaining RPCs are refused — the newest operator action
  wins, which is the correct contract for a console. Single RPCs already
  in flight server-side still complete (Python cannot kill a thread;
  nothing of that call follows it, and the daemon's reconcile pass
  re-forces visibility/mutes at the next cut).
- Regression grill ON THIS FIX, pre-commit: (1) plane_call routes are
  all operator-initiated POSTs (intents, /obs passthrough, /music, ad
  refresh) — no background poll carries generations, so there is no
  "poll starves intent" trap; the tap poll and the event loop ride their
  own ungenerated renderers; (2) ensure_bed superseded mid-ensure is
  self-healing (idempotent, re-run on the next probe) and the daemon's
  reconcile covers half-intents; (3) thread-local gens die with their
  doomed threads — no leak, no cross-thread contamination; (4) the
  first test run caught MY OWN harness bug (the wait loop exited while
  the abandoned thread was still sleeping) — the code was right, the
  probe was not; (5) the guard raise is OBSAppError, which _call already
  re-raises without dropping the connection — no transport churn.
- Verified: new station/test_plane_guard.py (12 checks: stale refused
  BEFORE the send with the connection standing; same-gen sequences
  continue; ungenerated daemon-shape calls unaffected; the timed-out
  sequence's tail dies superseded while the newer call lands; one call's
  own two-RPC sequence never refused). Full stdlib suite green
  (spool, fallback, playlist_edges, control_consume, overlay_auth,
  stream_respawn, selftest). Live proof arrives with the next real
  deaf-plane window: the journal should show "superseded" where it used
  to show a late intent landing.

## 2026-10-21 (late, 4) — the suite got a canonical runner

- Process debt found by looking at my own work: the verify lists named a
  SUBSET of the suite — docs/AUDIT-LOOP.md, OPERATIONS.md and AGENTS.md
  each listed 3-4 files while test_control_consume, test_overlay_auth,
  stress_cache (and the two harnesses added today) existed outside every
  list. A test the docs do not name is a test the next agent never runs.
- station/selftest.sh: the whole stdlib suite in one command, each file
  PASS/FAIL with a tail of its log, non-zero exit on any failure. The
  rule is now written where it will be read: a new test file joins the
  runner's list in the same commit that adds the file. The three verify
  lists now point at the runner instead of maintaining their own
  subsets, and REFERENCE.md's command table names every file with what
  it covers.
- Verified: bash station/selftest.sh — all green (spool, fallback,
  playlist_edges, stream_respawn, control_consume, overlay_auth,
  plane_guard, daemon selftest).

## 2026-10-21 (late, 5) — the web agent's round, verified; three defects fixed

The z.ai agent worked a full round on its own VM and pushed 55 commits
(`b39358e..90a1154`). This entry records the VERIFICATION, not the
narrative: what was checked, what was wrong, what was fixed.

### What the round did (and what survived verification)

- **The render plane boots on a GPU-less box** (`f3b92c7`): setup.sh now
  renders the installed unit per box shape — headless -> Xvfb :99 +
  `LIBGL_ALWAYS_SOFTWARE=1`, session-without-GPU -> :0 + software GL,
  lab -> untouched. It also creates `global.ini` with
  `BrowserHWAccel=false` when missing (a fresh box's first boot used to
  skip the guard and CEF-crash ~30s in) and skips the VNC unit on a
  headless box. VERIFIED: the lab shape is preserved in git (a real
  session on :0 with hardware GL — the llvmpipe burn of 2026-10-20 does
  NOT come back), the render fails loud when its sed patterns stop
  matching, and the VPS shape is correct in the text.
- **The stream respawn left the playout pass** (`fbe378f`): a dead
  network used to freeze the deck AND every other loop duty for ~4
  minutes. Now the pass only detects/counts/kicks; resolve+spawn+ready
  runs on one background thread per deck, with PROC-IDENTITY cleanup (a
  deck-keyed stop would kill a successor's feed) and a relevance-checked
  give-up EOF. VERIFIED: the code is sound (identity checks in every
  exit path, `END_LOCK` around every `_ENDED` append, the drain under
  the lock) and `test_stream_respawn.py` (29 checks) pins it.
- **plane_call is a deadline, not a bound** (`773848d`): every plane_call
  takes a generation and the renderer refuses an RPC older than one that
  already sent, under the plane lock. `test_plane_guard.py` (12 checks)
  pins it. VERIFIED: sound; the residual (a single in-flight RPC still
  completes server-side) is inherent to Python and is recorded.
- **One canonical suite runner** (`90a1154`): `station/selftest.sh`.
  VERIFIED: runs green here, 8/8, including the four new harnesses.
- Also landed and spot-checked as sound: the station lock around the
  panel's playlist/control RMW, the control.json write-back that pops
  by VALUE under the lock (a verb the dock posted meanwhile survives),
  the overlay's seat/plane-call guards, the mediamtx auth tiers, the
  sync.py scope fix, the eviction pins, the preflight shape check, the
  shuffler's stream-aware seam rule, the "hold states alert once an
  hour" change, the intake workdir cleanup, the cookies-not-failing-
  silently change, and the dock's identity-based on-air marker (VERIFIED
  in a browser: the marker follows the ITEM, not the slot, across a
  staged reorder).

### What was WRONG, and is now fixed (d49fe2f)

1. **The unit render never reached four units.** setup.sh injected
   BROADCAST_ROOT by rewriting an existing `Environment=` line. panel,
   overlay, watchdog and mediamtx have none, so they silently kept the
   repo root — and mediamtx's `${BROADCAST_ROOT}/mediamtx.yml` expanded
   to `/mediamtx.yml`, which does not exist: **the ingest bus never
   started on a fresh install.** The render now INSERTS the line into
   `[Service]` (appending to the file put it in `[Install]`, where
   systemd ignores it: "Referenced but unset environment variable"),
   and fails loud if a unit expands a variable it never defines.
2. **The render was untestable.** It lived inside setup.sh, so a
   harness could only reimplement it — and would have passed while
   setup.sh regressed. It now lives in `station/render_units.sh`, which
   setup.sh calls and `station/test_unit_render.py` runs FOR REAL over
   three box shapes, including a check that the variable lands in
   `[Service]` (not just in the text) and a check that the render fails
   loud when the unit text stops matching. The harness has teeth: with
   the old injection reverted it fails (3 failures).
3. **Plane-off mode was incoherent.** The daemon sat 15 minutes in
   `wait_ready`, then its opening cut consumed the queue (the hold flag
   was only set by the poll loop's gate, which had not run yet), and the
   fault watchdog counted the deliberately-absent plane as a fault,
   escalated to OFF-AIR and failed to cut every pass. Now: no boot
   wait, the hold is armed BEFORE the opening cut, the fault watchdog
   is off while the plane is off, and the watchdog timer does not alert
   about a unit that is switched off on purpose.

### The live box, brought in line with the new design

The mediamtx config is now RENDERED (real seat credentials generated into
`broadcast/secrets.env`, 600, rendered to `broadcast/mediamtx.yml`), the
installed units carry BROADCAST_ROOT, and the render plane stays MASKED
(the operator asked for OBS to be closed; the queue holds, the heartbeat
is fresh, the ingest bus is up).

### Where the loop stands for the next agent

Ranked, from `docs/KNOWN-ISSUES.md`:

1. `config/collection.json` staleness — `sync.py apply` can create a
   duplicate scene and restart the on-air deck mid-item. Operator-tool
   fix, medium size.
2. The dock small print (needs a browser harness on the box).
3. The duplicate-marker tiebreak (cosmetic).
4. The VPS render is unproven on a REAL GPU-less box (needs the box).

The two rules the loop taught this round, both now enforced by code
rather than by memory: **a test file joins `station/selftest.sh` in the
same commit that adds it**, and **a sed-based render must have a harness
that runs the real script**.

## 2026-10-22 (early) — the loop continues: `sync.py apply` cannot
## duplicate a scene any more

Took the top-ranked open item from KNOWN_ISSUES (the web agent's
round left it first) and closed the dangerous half of it.

- **THE SKEW GUARD.** The capture in git is a snapshot; the live plane
  renamed a scene ("SMILE | Meet" -> "SMILE | Program"). `sync.py apply`
  CREATES every capture scene the live plane does not have — so applying
  the stale capture created a duplicate `SMILE | Meet`, orphaned the
  live scene, and left the daemon (which drives the LIVE name) cutting
  to a scene with no deck in it. Apply now REFUSES a capture that lacks
  any scene the daemon drives, BEFORE it touches OBS, and says what to
  do (re-capture). Proof: `station/test_sync_guard.py` stubs the RPC to
  raise if reached, and shows the refusal happens before it.
- **The diff noise.** A media source's `settings.local_file` is runtime
  state (the deck points at whatever is playing) — the same class as the
  deck's eye state, which was already filtered. It is filtered now, so
  the diff is quiet enough to be read instead of training the operator
  to ignore drift. The harness proves a REAL difference is still
  reported.
- What still needs the plane (it is switched off at the operator's
  request): re-capture `station/config/collection.json` so the repo file
  carries the live scene names. Until then apply refuses, which is the
  safe failure.
- The new test joins `station/selftest.sh` in the same commit that adds
  it — the rule from the last round. Suite: all green (10 files).

## 2026-10-22 (early, 2) — the dock's small print, closed

Took the dock items the web agent's round left ranked and closed them.

- **The rebuild was O(n^2).** `rowEl()` called `onAirIdx()` (an O(n)
  identity scan) and `effectiveNextIdx()` (O(n) for every row: 41,209
  key comparisons per rebuild, inside the OBS process, next to the video
  render). Both are computed once per rebuild now: 41,209 -> 22
  comparisons, measured by instrumenting the scan.
- **The progress bar froze.** It is painted inside the row, and the list
  is only rebuilt when its content changes, so the bar sat at the last
  rebuild's width while the item played on. It updates in place now,
  like the strip countdown.
- **The staged bar could lie.** It said "N changes staged" while Apply
  would refuse (a net-zero edit sequence: edit, then undo back to the
  applied state). It keys on the PENDING state now; the history depth
  and the pending difference are two different truths and the bar says
  which one it is showing.
- **The NEXT marker could lie.** It skipped parked rows only, while the
  daemon also walks past pending rows (registered, not fetched), nameless
  rows and a file that is not on disk. The marker now skips the same
  classes, so it cannot light a row the daemon will walk past.

## 2026-10-22 (early, 3) — a trap in the "turn the plane back on" moment

The plane-off period left 30 `PLAYOUT_A: source missing` hits in the
fault history (the watchdog counted the deliberately-absent plane before
the fix). The fault history is a 1-hour sliding window and the
escalation fires at REPEAT_LIMIT (3) hits of the SAME fault — so the
first genuine fault after the operator switches the plane back on would
have tripped the off-air escalation immediately, on a station that was
actually fine.

- The fault history is now cleared when the plane is switched off on
  purpose (at boot) and again when it comes back (the down->up
  transition): those faults were the plane's ABSENCE, not the station's
  fault.
- Worth stating plainly: this class of bug is invisible until the
  moment it fires. The station was in a "safe" state (off-air) that
  nobody was watching, because the plane was off on purpose.

## 2026-10-22 (early, 4) — the poll got cheap, and the disk stopped churning

Found by asking why the dock's traffic was still 58KB every 2s, after
the version check was supposed to have fixed it.

- **The on-air progress was rewriting `state.json` every 2 seconds.**
  That churned the disk AND -- worse -- changed the state's mtime, which
  is part of the version stamp the dock polls: so the dock re-fetched the
  whole 58KB state every poll, forever. The progress now rides the
  HEARTBEAT (which its own thread already wrote every second), the state
  file changes only when the state really changes, and the panel's ping
  carries the live position so the dock's countdown and progress bar keep
  moving without the big fetch.
- **The panel spoke HTTP/1.0**: every poll opened a fresh TCP
  connection. It is now HTTP/1.1 with keep-alive (every response sets
  Content-Length, so it is safe) plus a 30s socket timeout. The ping
  went from 2-40ms to 1-5ms.
- **The pending check was two JSON.stringify calls over every item** --
  37ms a poll, twice a second, in the browser that shares the OBS
  process. It is a hash now, like the render signature.
- Measured after: 10 poll cycles = 0 full state fetches, 272 bytes a
  cycle, render 3.7ms, and a state file whose mtime no longer moves.

## 2026-10-22 (late) — BATTLE TEST: the plane up, the station broken, and
## the two root causes behind every "the station is struggling"

The advantage of this box over a sandbox: the render plane can be brought
UP and the playout can be attacked. The operator's OBS is off, so the
test ran in the HEADLESS shape (Xvfb :99 + software GL — the VPS shape),
which is invisible on their desktop and was restored to masked
afterwards.

### What the battle test found

1. **THE STATION WAS EATING ITS OWN PLAYLIST.** YouTube's metadata
   endpoint takes 30-60s from this IP (the resolve SUCCEEDS given 45s;
   the daemon's timeout was 20s). So every link timed out, the daemon
   called it "unplayable" and SKIPPED it — one item every 10-20s, the
   roll draining itself. This is the "daemon is struggling" feeling, and
   it would be catastrophic on a VPS (a datacentre IP is exactly where
   YouTube rate-limits hardest).
   FIXED: a resolve failure is now classified. PERMANENT (the video is
   gone) → skip it. TRANSIENT (a timeout, a bot check, a network
   hiccup) → HOLD the queue and try again. A run of dead links is capped
   at 3 per pass, so a list of dead videos cannot be chewed through in
   one go. `station/test_resolve_hold.py` pins all four behaviours.
2. **THE PROGRAMME WENT BLACK WHILE WAITING.** Holding is right, but a
   hold with an idle (or frozen) deck leaves the audience looking at
   black. The fail-safe's holding card now takes the air whenever
   NOTHING of the programme is visible. Verified live: PLAYOUT_C playing
   loop_a, the position advancing (5.8s -> 11.8s).
3. **THE WATCHDOG FAULTED THE STATION FOR WAITING.** "PLAYOUT_A: stalled
   at 41ms" x3 → OFF-AIR, while the station was merely waiting for a
   link. A deliberate hold is not a stall: the watchdog now stands down
   while we hold.
4. **THE OPERATOR'S COMMANDS WAITED BEHIND THE RESOLVE.** The control
   channel ran AFTER the advance work in the pass, so a skip sat behind
   a 45s metadata call. It now runs FIRST in the pass.
5. **THE "PLANE IS WEDGED" MYSTERY, SOLVED.** Proved with a deliberate
   experiment: a client that completes the websocket upgrade and NEVER
   READS its greeting blocks EVERY later handshake — not even after the
   stuck client closes. One timed-out client therefore wedges the
   plane's control plane for the daemon, the overlay server and the
   dock. That is the chronic "the plane is wedged, a restart heals it"
   symptom, and it is self-inflicted: the daemon's own failed boot
   attempts were creating the stuck clients.
   FIXED: the websocket client now closes its socket deterministically
   on ANY handshake failure; the boot's greeting timeout went 8s -> 20s
   (a software-GL plane is slow; 8s turned "slow" into a crash loop);
   and three greetings in a row that never came now RESTART the plane
   instead of waiting 15 minutes for it to un-wedge.
6. **THE VPS SHAPE, MEASURED (not guessed).** With the full scene under
   llvmpipe, OBS burns **238% CPU** and its websocket greetings
   intermittently hang for tens of seconds. The agent's cost table
   (0.5-1 core for 540p30) is far too optimistic with 7 resident CEF
   browser sources. The headless build must be the LIGHT one
   (LAB_LIGHT=1 strips the browser sources) or the box needs more cores
   than anyone budgeted. `docs/VPS.md` now carries the measured numbers.

### The state afterwards

OBS is masked again (the operator's request), the daemon is back in
plane-off mode (the queue holds, the heartbeat is fresh, the ingest bus
is up), and the suite is green with the new harness in it.

## 2026-10-22 (late, 2) — battle test, round 2: the paths the first round missed

The plane came up again (headless, invisible on the operator's desktop)
and the remaining playout paths were attacked. Five more defects, all
fixed:

- **KeyError('C') in the re-kick.** The fail-safe holds the air on deck
  "C", which is NOT in the deck map -- so the re-kick's
  `decks[state["deck"]]` raised, and the re-kick NEVER ran while the
  fail-safe was holding (i.e. exactly when the station needed it most).
- **The hold never retried.** With the fail-safe playing, no ENDED event
  arrives, so nothing re-attempted the advance: the station sat on the
  holding card even after the link came back. The hold now retries every
  ~30s.
- **The cover trusted a stale flag.** `state["fallback_air"]` says "the
  fail-safe is holding" -- but after a plane restart the flag survives
  while the scene says the fail-safe is not on air, so the cover never
  engaged and the station sat black. The SCENE is the truth now.
- **A visible but FROZEN deck counted as "on air".** After a plane
  restart the collection restores the deck VISIBLE, and the watchdog
  calls it "stalled at 41ms" -- the audience sees a frozen frame. The
  cover now requires a visible source that is actually MOVING.
- **The cover consumed the item.** `failover()` moves the cursor past
  the item that FAILED; a cover is not a failure. `move_index=False` now.
- **The preflight cried CRIT on every cold boot.** It ran BEFORE
  wait_ready, so all it could ever see was "renderer down". It runs
  after the plane is up now, and passes.

### What the battery proved working, live

- Apply (dock) -> the daemon reloads the playlist -> the next transition
  takes the new order.
- A link that will not resolve -> the queue HOLDS, the fail-safe's card
  takes the air, and the fail-safe ROLLS (loop_a -> loop_b) on its own.
- The link resolves -> "Fail-safe cleared: deck A plays again" and the
  deck plays and MOVES.
- The dock and the plane AGREE: the same title, a countdown that ticks
  (3:17 -> 3:12), a progress bar that moves (30% -> 32%), and the same
  NEXT row.

## 2026-10-22 (late, 3) — the two operator features that were still open

- **BULK RENAME REVIEW.** One renamed video is a row-menu job; a
  channel-wide relabel can flag dozens of rows, and clicking through
  each one is a trap. The dock now shows a review bar whenever rows are
  flagged ("N videos renamed on YouTube", with the count of the ones
  held back because the video is a different one) and offers
  approve-all / discard-all. Like every other edit, they STAGE: the
  operator still presses Apply.
- **THE METADATA SWEEP IS WORKING** (it was already running; nobody had
  checked): 7 of 203 rows now carry a captured description, the channel
  and a checked-at stamp. The preview card shows them, and the manual
  "refresh metadata" button re-resolves one row on demand.

The live rename that surfaced while testing is a good example of WHY
the amber dot exists: the "Big Buck Bunny (prime test)" row's YouTube
id now serves a completely different upload (Lady Gaga - Gimme More).
The duration check catches that case and holds it; a title-only change
would have kept playing.

## 2026-10-22 (late, 4) — "the preview has content and the programme is
## black", solved

The oldest item on the backlog, and the reason the station was never
actually broadcasting: **the live render plane had NO output at all** —
only a file output. The finished programme never left OBS, MediaMTX's
`monitor` path was never fed, and everything downstream saw black while
the operator's preview looked perfect.

- The daemon now brings the programme output up at boot, pointing at
  the LOCAL bus (`rtmp://127.0.0.1:1935/monitor`), and restarts it when
  a plane restart leaves it stopped.
- The request matters: this obs-websocket build has NO `CreateOutput`
  ("Your request type is not valid") — `StartStream` on the custom
  service is the way.
- It points at the BUS, not at YouTube. The bus is what the publish leg
  reads, what the confidence monitor reads, and where the failover can
  be observed. Publishing straight from OBS would bypass all three.
- Proven live: 143 video frames and 262 audio frames read back from the
  monitor path at 960x540, with the output active and 12MB written.

The bus -> YouTube leg still needs a real stream key (the operator's
cutover); the OBS -> bus leg is now proven.

## 2026-10-22 (late, 5) — the ad break, the edge cases, and a 1200-row playlist

More live work with the plane up, then a battery of malformed input.

- **THE AD BREAK, ROUND TRIP, VERIFIED.** The ad configuration is off
  (`ad_every: 0`, no ad files), so the test drove the FUNCTION with a
  temp plan and left the operator's configuration untouched: the ad
  scene cuts, the ad plays, the decks mute, the ad ends, and the daemon
  hands back to the programme ("Ad done; back to program") with the decks
  unmuted and `in_ad_break` cleared.
- **A MALFORMED PLAYLIST ROW CRASHED THE PLAYOUT.** A row that is not
  an object raised AttributeError in advance(). The loop caught it, but
  the SAME bad row was retried every pass, so the station sat on it
  forever. Malformed rows are now skipped with a warning. A row that
  names a PATH instead of a media file is refused too, so a hand-edited
  playlist cannot point the renderer outside the media dir.
  `station/test_playlist_robustness.py` pins it, along with the shapes
  that already worked (string/null/negative/huge durations, a dict
  title, an empty file name, unicode, duplicates) and an absurd cursor
  (negative, out of range, a string, a float).
- **A 1200-ROW PLAYLIST COST A 300ms REBUILD** inside the OBS
  process. The dock now draws at most 200 rows per section and offers
  a "show all" row for the rest (the rows are all still there, and
  searchable -- the DOM just does not hold a thousand of them for
  nothing). Rebuild 300ms -> 200ms, and a no-change pass is 11-20ms.

## 2026-10-22 (late, 6) — the running order (the Studio Player queue)

The last of the operator's "steal its ideas" asks: a queue you can
SEE, not a list you have to read. The dock now draws a strip of tiles
under the header — one per queued item, the playhead on the item that is
on air (green), the next one in amber, the played ones struck through
and dimmed, parked rows excluded. Clicking a tile selects that row and
opens its preview, so the operator can look at an item without hunting
for it in the list.

It is bounded: a window of 24 tiles around the playhead, not the whole
playlist, so a 200-item roll does not become a wall of DOM (the list
itself is capped at 200 rows per section, with a "show all" row).


## 2026-10-22 (06:40) — the panel accepted a corrupt cursor

Found by fuzzing the panel's own endpoints: `POST /api/state` with
`{"state": {"index": "abc"}}` answered 200 and wrote the value to the
live state. The daemon then coerced it to 0 — so the station would have
restarted the show from the top — and the operator's position was gone.

The panel now checks the state's VALUES, not only the key names: the
index must be a whole number (and not a bool, which is an int in
Python), the flags must be booleans, and the cursor must not be
negative. A malformed value is a 400 with the reason.

Two other things cleaned up in the same pass:

- A leftover OBS process from an earlier session was still running
  (1h39m, ignoring SIGTERM — it needed SIGKILL). The unit was masked,
  so nothing was served by it; it was just RAM and CPU.
- The live cursor was repaired to where it was (row 10 — the row after
  the last item that played).

## 2026-10-22 (06:20) — the operator's first-stop diagnostic lied, and a countdown went negative

Two small lies found by running the tools the operator actually runs.

- **The preflight said "scenes ok" without ever asking OBS.** Run
  without `--strict` (the normal way), it has no renderer, so the
  scene checks are skipped -- and the PASS line still claimed the
  scenes were fine. The preflight is the first stop when something is
  wrong, and a false all-clear sends the operator looking in the wrong
  place. It now says "scenes NOT CHECKED (no plane; use --strict)", and
  says so even when another check (the disk) fails. With the plane
  switched off on purpose it says "SKIP obs -- the render plane is
  switched off on purpose" instead of crying FAIL.
- **A switch that was DUE showed a negative countdown** ("in -2 min").
  The firing window (five minutes) and the display used different
  rules. They now share one constant: a due switch reads zero ("due
  now" in the dock), and one long past reads tomorrow.

New: station/test_preflight_honesty.py.

## 2026-10-22 (06:50) — nothing watched the bus

The station watchdog revives the daemon, the panel, the overlay server
and the render plane. It did **not** watch MediaMTX — the bus that
carries the finished programme out of OBS, the live feeds in, and the
publish leg out. If the bus died, the station looked alive and went
dark downstream, and nothing brought it back.

The bus is now one of the watched pieces (MediaMTX's API on 9997 is the
liveness probe). PROVEN LIVE: the bus was stopped, the watchdog found
it ("bus not answering. Reviving."), restarted it, and the API came
back.

The same pass fixed the check's exit code: `--check` answered 1 for a
perfectly healthy station whose plane is masked on purpose. A check
that always fails teaches the reader that the exit code means nothing.
It now answers 0 when the only dead piece is one the operator switched
off, and 1 when a piece that should be alive is dead.

## 2026-10-22 (07:00) — the contribution seats, proven end to end

The seats (a guest joining with a screen or a camera) had never been
run against a real publisher. They are the operator's "a guest is in
the show" feature, and the bus is the only thing they touch.

Proven live, from the LAN address (the real guest's vantage point):

- **SRT publish**: a seat publishes with its own credential
  (`streamid=publish:slot-cam:seat-cam:<pass>`) and the path comes up
  ready/available/online with two tracks (H264 + AAC), bytes climbing
  for the whole 35 s.
- **SRT read**: a reader on `streamid=read:slot-cam` — exactly what
  the OBS "Slot Cam" input does — receives the video and the audio.
- **WHIP publish**: the right credential gets 201 with a session URL.
- **The auth holds**: a wrong password from the LAN is refused
  ("failed to authenticate"), an unknown user is refused, and the right
  credential against the WRONG path (slot-screen) is refused — the
  path scoping works.
- Loopback is tier 1 ("the box itself, anonymous, every action"), so
  a local publisher needs no credential. That is the design, not a
  hole: the seats are remote, and the remote path is checked.

One thing the test did find: a publisher that is torn down mid-flight
takes the path down with it ("no stream is available"), which is why
the read side failed on the first attempt — a test artefact, not a
station fault, but worth knowing when a guest's tab closes.

## 2026-10-22 (07:20) — the browser seat's secure-context trap, documented

While proving the seats, the one thing a guest would actually hit was
clear: `getUserMedia` is blocked on a plain `http://` page that is not
localhost, so a guest who opens `station/whip.html` on the box's LAN
address gets "denied" and no explanation. The page says so; the
operations doc did not.

Both ways round it are supported today and are now written down: the
guest opens the page through an SSH tunnel (localhost is a secure
context), or the guest publishes over SRT from OBS/ffmpeg and needs no
browser at all.
