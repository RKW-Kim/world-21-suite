# Decisions

Why the station is the way it is. Each entry: the decision, the reasoning,
and what was rejected. If you want to change one of these, read the entry
first — most of them were decided the hard way.

---

## 1. The dock stages edits; Apply is the only thing that changes the station

**Decision.** Every edit in the dock (reorder, retag, park, add, import,
shuffle) lands in a local working copy. Nothing is sent to the station
until the operator presses **Apply** (the tick button).

**Why.** The dock used to save on every click. That produced a write
storm: a burst of actions became a burst of `POST /api/save` calls, and the
panel's read-modify-write raced the daemon's own writes. The operator's
complaint — "I act too fast and it hangs" — was this, not a slow daemon.
Staging also makes every edit undoable without a round trip, and it gives
the operator a place to think.

**Rejected.** Auto-apply (a write per click — the storm came back).
Per-edit "apply?" prompts (a modal per click is worse than one button).

**Consequences.** The dock shows a persistent *staged* bar (amber) whenever
the working copy differs from the station, with Apply / Undo / Redo /
Revert. The history is durable (localStorage): it survives a reload, and
revert walks back step by step to the last applied state. A `beforeunload`
guard covers a closed tab. The station keeps running the old order until
Apply, and the bar says so.

## 2. Profiles are saved running orders, and loading one stages it

**Decision.** The dock's save button stores the *working copy* under a name
("Save version" became "Save profile"). Load brings a profile back into the
working copy — it does not touch the station. Apply does.

**Why.** The operator wanted distinct running orders for different
occasions ("different profiles for different occasions"). Loading a profile
straight onto the air would cut the programme mid-show; staging it means the
operator decides when the show changes.

**Rejected.** Load = apply (too sharp an edge for a live show).

## 3. One loudness switch for the whole station

**Decision.** The wave icon next to Shuffle toggles compress (−16 dB, 3:1)
+ limit (−1.5 dBTP) on **every** playback input. Off removes the chain. The
choice is remembered in `broadcast/normalize.json`. There is no per-item
"normalize this one video" in the row menu any more.

**Why.** The operator's words: *"why would I only want to apply to one video
in particular, it's either fully on on everything or not."* A per-row
loudness pass also did nothing useful for a link that was already spooled
and normalised at intake.

**Rejected.** Per-item loudness (kept the file-level EBU pass in
`spool.py`, which runs at intake; the per-row verb is gone).

**Note.** The chain is a *dynamics* pass, not a loudness lift: it does not
change the perceived level, it keeps the peaks and the jumps consistent.

## 4. The dot answers one question: is this link still what it was?

**Decision.** One dot per row:
**green** = the link is there and its metadata is unchanged;
**amber** = YouTube renamed it (or replaced it) and it needs review;
**hollow** = a local file, nothing to check. The cache state moved into the
row's label (`YT cached` / `YT live`).

**Why.** The old dot meant "cached", which is a *storage* fact, and it was
ambiguous ("grey/green dot?"). The operator asked for a dot that means
something about the *content*: green = fine, amber = needs review.

**Rule.** State is never carried by colour alone: the amber row also
carries a `meta?` badge, the shapes differ (filled / hollow), and every dot
has an accessible label.

## 5. A renamed video keeps playing — unless the duration changed

**Decision.** The title watcher flags a rename. If the duration is
unchanged, the item **keeps playing** and is only flagged. If the duration
also changed, it is a different upload wearing the old name, and it is
**held back** (parked) until approved.

**Why.** The operator: *"letting the video just continue, but only hold it
if the video duration is different."* A title change is cosmetic; a
duration change means the content is not what was approved.

**Consequence.** The flag carries `same_video`; the dock's Approve only
unparks an item the *watcher* parked, never one the operator parked.

## 6. Icons, not labels — and right-click, not a per-row button

**Decision.** The transport and library controls are inline SVG icons
(stroke, `currentColor`) with tooltips and accessible names. A row's
actions open on **right-click** (the browser's own menu is suppressed app
-wide, except inside text fields, where paste still has to work). The
per-row `⋯` button is gone.

**Why.** The operator: *"having icons is better and simplifies the UI/UX …
when I right click on something it should bring me its context menu not the
chrome/browser one, i'm annoyed i have to click the three dotted thing on
each video."* Removing 200+ buttons also made the list cheaper to render.

**Rule.** Icon-only controls need `aria-label` **and** a tooltip. A bare
glyph is not a name.

## 7. The music bed is a waiting-room bed, and it is kept out of Programme

**Decision.** The bed lives in Starting, Off Air, End Credits and Tech
Diffs — the scenes with no media of their own. The daemon checks at boot
(`ensure_bed_isolation()`) and removes it from Program, Ad Break and Q&A.

**Why.** The operator's intent: the bed is for static scenes; under the
programme or an ad break it fights the audio that is already there.

## 8. Playlists are groups, and shuffle only moves what has not played

**Decision.** An imported playlist is a **group**: a folded parent row with
its own header actions (play, shuffle, reset, a `YT PLAYLIST`/`FILES`
badge) that expands into its rows. Items carry a `played` flag, set by the
daemon when they air.

**Why.** The operator's model, borrowed from Spotify: with shuffle on, the
order is random; turning shuffle off does not drag what was already sent
past back into the running order (those items stay unplayed, in the shadow
zone); turning shuffle on again re-shuffles everything that has not played.

**Consequences.** `orderGroup()` reorders **only** the unplayed items, in
place — the played ones keep their slots. "Send this group back to
Available" returns the group to the parked section while the item on air
finishes first.

## 9. The heartbeat comes from its own thread, and "busy" is not "dead"

**Decision.** `broadcast/heartbeat.json` is written every second by a
dedicated thread and carries `pass_ms` and `busy`. The dock shows
*"daemon busy (media status) — last pass took 11.4s"* when a pass is slow,
and only raises the alarm overlay when the heartbeat itself goes stale.

**Why.** The heartbeat used to be written by the poll loop, so any slow
pass (a busy plane, a long OBS call) made the dock scream "DAEMON NOT
RESPONDING" — which is what the operator experienced as the station
"struggling". It was not struggling; it was working and being misreported.

## 10. The poll is cheap, and the list only rebuilds when it changes

**Decision.** The dock polls `/api/ping` (≈200 bytes: mtimes of the
playlist, the state and the spool directory) and only fetches the 58 KB
state when that stamp moves. The list is rebuilt only when its content
signature changes.

**Why.** The dock is an **OBS browser dock**: it shares the OBS process
with the video render. A 40 ms full rebuild of 200 rows every 2 s, inside
the renderer, was the single biggest cost in the system — and it kept
destroying focus, drags and the operator's cursor.

**Measured.** 58 KB → 205 B per poll; 40 ms → ~5 ms per no-change pass.

## 11. The render plane runs on the real desktop, on hardware GL

**Decision.** OBS runs on XWayland `:0` (the real session), with
`LIBGL_ALWAYS_SOFTWARE` removed.

**Why.** The station's OBS was on an Xvfb display, where GLX is software
only: llvmpipe burned 200 % of a core at the real window size, which
starved the websocket and made everything feel wedged. On `:0` the Intel
HD 520 does the rendering and OBS dropped to ~80 %.

**Consequence.** The GUI bridge is `wayvnc`, not `x11vnc` (x11vnc cannot
scrape XWayland at all — `BadMatch / X_GetImage`).

## 12. The station watchdog revives the station; it does not replace the operator

**Decision.** A systemd timer runs `station/station_watchdog.py` every five
minutes. It checks the daemon (unit state **and** heartbeat), the panel,
the overlay server and the render plane; it restarts what is dead, and
alarms only when a restart did not bring it back.

**Why.** The daemon watched the plane; nothing watched the daemon. A
silently dead daemon leaves a station that looks fine and airs nothing.

**Rejected.** Alerting on the first failure (noise). A watchdog that
"fixes" a sick configuration (it must restart, not reconfigure).

## 13. The publish leg is off by default

**Decision.** `station-publish.service` and `publish_youtube.sh` exist, but
are **not enabled**. The script refuses to run with a placeholder key. The
daemon creates the OBS RTMP output only when a real key is present.

**Why.** Publishing is outward-facing and irreversible. It must be a
deliberate act by the operator, not a side effect of a boot.

## 14. Python stays

**Decision.** The daemon stays Python.

**Why (measured).** A poll pass takes 20–190 ms and the daemon is idle
~99 % of the time. The perceived stalls were: a heartbeat written by the
poll loop (fixed), a boot handshake with no timeout (fixed), and a dock
that rebuilt 200 rows every 2 s inside OBS (fixed). None of those is a
language problem, and a Go rewrite would change none of them while
replacing 2,900 lines of OBS/ffmpeg/yt-dlp integration.

**When Go (or Rust) would be right:** a hard-realtime control loop, or
hundreds of concurrent streams. Neither is this station.

## 15. The music bed, the recording and the scheduled playlists

**Decision.** Recording is out of scope for now (the operator records
Google Meet segments manually, choosing the source by hand). Scheduled
playlists are still open (see `docs/KNOWN_ISSUES.md`).

**Why.** The operator: *"I don't want to record the media/playlist, but in
future I will be coming in and having a meeting … those are the ones I want
to record, but I will just do that manually."* Recording the programme
would double the disk and the CPU for a feature nobody asked for.

## 16. The destination is a headless VPS — with software rendering

**Decision.** The station moves to a VPS after it is perfect locally. The
VPS has **no GPU**, so OBS renders in software.

**What that means.** A GPU-less box is a different engineering problem:
more cores, a lower output resolution/fps, and a different GL profile. The
spec sheet, the platform shortlist, the security posture and the code
changes are in `docs/VPS.md`.

**Why it still makes sense.** The station's failure modes are all
server-side (the daemon, the spooler, the watchdog). They run better
headless than on a desktop that also runs a browser, a compositor and a
video editor.
