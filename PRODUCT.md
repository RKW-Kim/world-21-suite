# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (overlay kit) + linux VPS (station runtime)

## Users

Three people, rarely in the same room — often just one:

- **The operator / technical director** — runs the entire station, usually
  alone, usually not watching it. Operates from a laptop or a phone through
  the station console and the daemon CLI. Does graphics, engineering,
  presenting, and scheduling, mostly after midnight.
- **The contributors** — a host and one or two guests at a time, each on
  their own device and network. They send camera, microphone, and screen as
  raw feeds. They never see a stream key, never touch OBS, never decide what
  is on air. A guest who has never broadcast can be live in minutes from a
  browser link.
- **The audience** — a general public livestream audience watching on
  YouTube, on anything from a small phone to a 100-inch television. The
  viewing distance and size are unknown and not controllable. This is the
  single most consequential fact about the audience and it governs type and
  contrast across every surface.

An earlier version of this file described a host plus a present producer
running local OBS. That was the kit's origin; it is not the target. The
target is one person running a station that survives without them.

## Product Purpose

Two artifacts, one station:

1. **The overlay kit** (`overlay/`) — full-screen scenes and transparent
   modules for a Smile.co.ke livestream about markets, presented in an
   entertainment register. Success is that a scene can go on air without
   anyone thinking about it, and that it holds up whether the viewer is on
   a phone in a car or on a wall-sized screen across the room.
2. **The station system** (`station/`) — the daemon, intake worker, overlay
   server, contribution bus, and console that run a 24/7 broadcast on a
   headless render plane with nobody watching. Success is a week of airtime
   with zero manual interventions and every incident already in the log with
   its recovery attached.

## Positioning

Markets content as set dressing on an entertainment show. Not financial advice,
not a trading platform, not a dashboard. The brand is a smiley; the register is
a variety show that happens to be about markets.

## Operating Context

- Every overlay page is a standalone **OBS Browser Source**. No build step, no
  framework, no runtime dependencies. The render plane may be a laptop OBS or
  a headless VPS OBS — the pages do not know or care.
- The VPS is the only compositor and the only holder of the stream key. It
  pulls every source; nothing pushes to the audience except it. The
  operator's laptop can die mid-show and the broadcast continues.
- A small daemon drives the render plane over obs-websocket (intents, never
  pixels): playlist loop with shuffle, event-driven ident chaining, watchdog
  with automatic fallback, cache rotation, alerts. Routine control is a CLI
  and a phone-sized console; a web dashboard arrives later, if ever needed.
- Contribution feeds arrive over the local network or the internet into a
  media bus in front of the render plane, which absorbs their chaos and
  exposes their health. Presenters ship raw signals (camera, microphone,
  screen); all composition happens on the VPS.
- Prerecorded material enters through an intake pipeline (link → fetch once →
  normalise → verify → publish to cache → queue). The loop plays local files
  only; links never appear in the air path.
- Scenes and modules follow **opposite** compositing rules and must not be
  confused. This distinction is the core architectural fact of the kit.
- Content that changes per episode is driven two ways: static URL parameters
  (baked at source-add time) and a live localhost data channel the pages
  listen on (updated in place, no reload). There is no remote website in the
  air path.
- The repo is the source of truth. Preview deploys to GitHub Pages by a
  single script; the VPS runs tagged, rehearsed commits pulled from here and
  nothing else. The development laptop is the lab and the staging instance.
- Deployed to GitHub Pages by a single script that mirrors the overlay kit
  to the `gh-pages` branch. The `overlay/` path is load-bearing and the
  published URLs depend on it.
- Streamer.bot switching via URL parameters belongs to the kit's origin era;
  the station path is daemon intents and the console.

## Capabilities and Constraints

**Two source types, opposite rules:**

| Type | Pages | Rule |
|---|---|---|
| Painted scene | 9 — `starting`, `brb`, `intermission`, `intermission-b`, `q&a`, `tech-diff`, `end`, `end-credits`, `coming-up` | paints its own background, always dark |
| Transparent module | 4 — `ticker`, `watermark`, `speaking` (+ `coming-up` in bumper mode) | must composite over gameplay |

- A `color-scheme` meta tag must **not** appear on transparent pages: it makes
  Chromium paint an opaque root canvas and the module becomes a dark rectangle
  in OBS. All three transparent pages carry a comment saying so.
- The bottom 76px of every scene is reserved for the ticker module, which is
  exactly 1920×76. Top-left corner is reserved for the watermark.
- Zero canvas, zero `requestAnimationFrame`, at most one gated `setInterval`
  per page (the clock). All other motion is compositor CSS: transform and
  opacity only, no animated blur or filter.
- `prefers-reduced-motion` must produce a real poster state, not a
  half-finished animation.
- Output survives h.264 compression at 1080p on an unknown display. Small text
  is the first thing that fails.
- Static graphics get baked to video where it matters (no browser cost, no
  renderer-stutter class, frame-accurate); genuinely live data (ticker,
  dynamic names, chat) stays in HTML fed by the local overlay server.
- The station control surface (console + intents) sends commands and data,
  never pixels. The operator's connection quality never affects the broadcast.
- The console talks only to the overlay server over plain HTTPS-fetchable
  endpoints; the server holds the single OBS connection and the password.
  No OBS port or secret ever touches the operator's machine.
- Everything is driven by URL parameters and the local data channel today.
  There is **no** remote live-data bridge and no external site dependency.

## Brand Commitments

- Name: **Smile** / `smile.co.ke`. Handles: `@smileke`, `#SmileSquad`.
- The logo is **verbatim**. The four paths of `Smile-Logo.svg` are copied
  exactly and never redrawn. `Smile-Logo™.svg` is a materially different
  drawing and is not interchangeable with it.
- The brand is deliberately **dark**, and this is binding. Any change that
  lightens a surface, or introduces a light-mode variant, is a rebrand and not
  a refinement.
- The face mark is a circle with two eyes and a smile — a character, never a
  humanoid figure. It is never given a body.
- Yellow is the single accent. A palette is set of seat colours that describe
  which seat is currently speaking, and is not a decorative palette.

## Evidence on Hand

- `overlay/` — 14 live pages, the working kit.
- `station/` — daemon, intake, overlay server, console, scene templates,
  contribution test kit, systemd units, cache stress battery.
- `archive/core/` — old source-of-truth originals, the approved logo files,
  and the original Qwen design reference the kit grew out of (archived;
  nothing loads it).
- `archive/obs-web-edition/` — a saved visual mockup of an OBS-like web UI,
  kept as a control-surface reference only (no protocol code, no license to
  take).
- `audit/frames/` — one curated best-moment reference frame per scene, captured
  across each scene's animation cycle rather than at a fixed moment.
- `brand.json` — generated from the overlay CSS by
  `scripts/sync-brand-tokens.py` (do not hand-edit; CI fails on drift).
- `docs/VPS.md` — the runbook: fresh box to verified air.
- `.archify/` — the validated station architecture diagram with repo-pinned
  evidence.
- `WORKLOG.md` — every decision, failure, and fix in chronological order.
- `SCENES.md` — the presenter's script: what each screen is for.

**Future work must not fabricate:** viewer numbers, engagement, sponsorship
rates, audience demographics, or any testimonial. None exist.

## Product Principles

1. **The viewer may be on a phone or a 100-inch screen, and we cannot know
   which.** Design to the worst case of both. Legibility outranks density,
   always.
2. **Scenes and modules are different things.** Never ship a change that
   breaks the boundary between them, and never let a module paint a background.
3. **The logo is copied, not drawn.** No approximation, no restyling, no
   "improvement" to the face.
4. **Content that changes per episode must be changeable in one place**, not
   by editing markup. This is a correctness problem, not a convenience one.
5. **Motion must mean something.** An animation that cannot be justified in one
   sentence does not ship. A ticker may loop; a live indicator may pulse.
6. **The station survives without a human.** Every automation decision is
   judged by the 3 a.m. test: asleep operator, no intervention, no
   embarrassment. Boring beats clever.
7. **Intents, never pixels.** Control surfaces command and inform; they never
   carry the broadcast. The operator's laptop, network, and power are all
   allowed to die mid-show.

## Accessibility & Inclusion

- Legibility under video compression, at unknown viewing distance and size, is
  an accessibility requirement here, not a preference. WCAG contrast does not
  directly model a compressed stream watched from across a room.
- Views small and large must both work. No information may exist only in a
  size that suits one of them.
- `prefers-reduced-motion` is honoured as a real state on every page.
- The operator console must be fully usable from a phone, one-handed, on a
  bad connection: big targets, no hover-dependent controls, no pixel
  previews where a state readout suffices.
- Entertainment-led, not regulated financial advice, so no disclaimer or
  compliance framing is a design requirement.
