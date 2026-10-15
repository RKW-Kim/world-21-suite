# Vendored: OBS Studio Web Replica (`station/studio/`)

- **Origin:** user-supplied `OBS-Studio-Web-Replica.zip` (received 2026-10-14),
  commissioned work owned by the operator. Vendored with permission.
- **Kept:** `index.html`, `css/`, `js/`, `README.md` — unmodified.
- **Excluded:** `server.mjs` (our overlay server serves the tree),
  `demo-obs-server.mjs` (mock OBS on :4455 — NEVER run on the render-plane
  host, it would shadow the real socket), `start-*` launchers, `docs/`
  (kept in Downloads, not shipped).
- **Pristine-tree policy:** twenty-four marked `LOCAL-PATCH` lines exist (see below);
  everything else byte-identical to the drop. Updates: re-copy the tree,
  re-apply the listed patches, commit.
- **LOCAL-PATCH list (all verified live against OBS 32.2.2 / ws 5.7.4):**
  1. `js/ws.js` Identify: `+ Meters bit (0x10000)` — without it no live
     levels ever arrive; mixer dB was sim-only.
  2. `js/ws.js` event switch: `InputVolumeMeters` case feeding
     `obs.setLiveLevel()` — the consumer never existed.
  3. `js/engine.js`: `_liveLevels` map + `setLiveLevel/clearLiveLevels` +
     `getLevel()` prefers live peaks when attached (sim otherwise).
  4. `js/ws.js` disconnect: clears live levels (no frozen meters).
  5. `js/ws.js` mirror `setTransition`: real field is `transitionName`
     (was `sceneTransitionName` — failed silently on every transitions
     change).
  6. `js/ws.js` mirror `reorderScene`: no such protocol call exists —
     replaced with a spoken warning, local order only.
  7. `js/ws.js` opcode table: Request is op 6 (was 5), responses op 7
     (was 6), batch op 8 (was 7), batch-responses op 9 (was 8). The whole
     client spoke a shifted dialect that only its own mock understood;
     real OBS closed every session with "Unknown OpCode: 5".
  8. `js/ws.js` request(): 12s window + one retry + visible warnings
     (was 5s-then-silent), plus 15s flap grace before first send.
  9. `js/ws.js` mirror wrap: no `busy` gate (it is held by unrelated async
     event handling, e.g. the daemon's own deck advances, and silently
     dropped user actions fired mid-flight; every mirrored call sets
     absolute state so echo is harmless).
  10. `js/main.js` boot: auto-connect after paint + 5s watchdog with
     stuck-handshake redial (never stamps on a handshake younger than 15s).
  7. `js/main.js` boot: auto-connect after first paint (gateway defaults
     already target this server; the relay bridges authentication, so no
     password is needed anywhere on the operator side).
  11. `js/ws.js` drops: singleton non-modal reconnect banner instead of one
     msgBox per drop (the 5s watchdog redial stacked 100+ OKs on flaky
     links); "Reconnected" toast only after a real drop, silent otherwise.
  12. `js/ws.js` reconcile-don't-append: `initialSync` rebuilds scene.items
     and S.items from zero (every reconnect duplicated each source row),
     `addRemoteItem` is idempotent per sceneItemId and swaps the local
     echo-ghost for the server row instead of doubling it.
  13. Preview left / Program right (was reversed), per-pane Refresh +
     Live toggle. Live truth is single-sourced in ws (`view` + `setLive`
     at module scope, `wsApi.isLive/toggleLive`); panes own no boolean
     and only mirror acks — closing a real desync class where a
     per-reconnect closure re-subscribed and button state drifted.
  14. Screenshot engine: JPEG ladder (640px q60) with PNG fallback, one
     request in flight max, NOTHING polls by default (Refresh / connect
     snap / Live only), Live ~150ms concurrent program+preview, pause
     when the tab hides, deaf-guard forces Live off after 5 straight
     failures, disconnect always stands live down. No 60fps mode exists
     on purpose — see README "live view budget".
  15. Mixer LIVE/SIM badge (`engine.metersLive()`: attached + meter event
     within 3s). Green LIVE = real plane peaks; grey SIM = simulation.
  16. Audio-filter mirror for mic tuning: engine CRUD
     (`add/removeSourceFilter`, `setFilterProp`), OBS kind/key maps,
     server chain sync in `initialSync`, re-sync on filter events,
     debounced settings pushes, dialog add/remove/audio-sliders wired
     through it. Effect filters stay local-only sim.
  17. Layout lock while attached: canvas move/scale cursors and gestures
     gated on `wsMode` (selection + right-click still work), Transform
     dialog refuses with directions; offline sim keeps full editing.
  18. Dock layout system: resizable side columns (drag splitters,
     persisted), All-Docks-Bottom preset (Docks menu), free drag-reorder
     of any dock header across left/right/bottom with drop indicators,
     order + widths persisted, Reset UI restores factory.
  19. Connection generations + dead-man + shared teardown + manual
     Disconnect that sticks (wantConnect): stale sockets/events/syncs
     abort instead of killing the new connection; connected-but-deaf
     forces a fresh generation after 20s of total silence; drops and
     manual disconnects share one teardown (timers, pending, debounce
     maps, queued mirrors); double pre-Identify close toasts the
     password hint instead of redialing mute.
  20. RPC discipline: reads retry once, writes fire once (a resent
     Create* duplicated server state); queued absolute-state mirrors
     coalesce latest-wins per target across flap windows; remove/rename
     mirrors pre-capture identifiers before orig() deletes them (the old
     microtask lookup always missed); volume/mute are trailing-debounced
     and resolve names at fire time.
  21. Reconcile layer: upsertScene/upsertSource (one stable
     `scene-<name>` id scheme), forgetItem (rows + both id maps + sizes),
     syncSceneItems (reindex repair), snapshot/restore around initialSync,
     real InputCreated/Removed/NameChanged, SceneRemoved sweep with
     program/preview repair, filter merge-by-name (pending rows kept),
     new cases (reindex, filter enable/order, media playback, audio
     monitor/offset/balance/tracks, collection/profile switches),
     debounced persistSoon on remote branches, undo skips remote-applied
     ops + warns while attached + stacks cleared per sync.
  22. Meter peak across channels; `!!x ?? y` precedence fix; remote
     selection applies to preview only; mirrorTransform bails loudly on
     unknown ids; live-view names reseeded from engine truth on failure.
  23. Attached-canvas honesty: remote frames drawn at CSS size (retina
     overdraw), transition ghosts likewise; marquee off + pointer cursor
     while attached; Space/Enter no longer double-fires from focused
     buttons/dialogs; menus join the dialog z-ladder; bottom strip hides
     with its docks; empty columns stay as drop gutters; splitter widths
     clamped; scene-filter orphan fixed; effect adds persist + say
     preview-only; Transform sync unsubscribed on close; eye/lock clicks
     don't reselect; source row-drag locked while attached; narrow-
     window media query; dead CSS rules removed.
- **Integration:** served at `/studio` (MIME-correct, no-cache exempt —
  browsers may cache; hard-reload after updates). OBS traffic goes through
  the overlay server's raw relay: the replica's gateway mode
  (`?XTransformPort=<obs-port>`) is spliced TCP-to-TCP to the render plane,
  auth end-to-end via its own connect dialog. See `_ws_relay`.
- **Known notes (theirs to fix upstream, not forked here):**
  - Add-source offers platform-specific captures absent on Linux
    (game/dshow/vlc/AVFoundation); those creates fail at runtime.
  - README's `Enable/DisableStudioMode` row is docs-only; the code
    correctly uses `SetStudioModeEnabled`.
  - Deploy script only mirrors `overlay/` to gh-pages, so this tree is
    never published publicly. Keep it that way: it is a control surface.
