# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two people, both present during a stream:

- **The host** — on camera, going live. Not operating OBS. They are thinking
  about what they are saying, not about the overlay.
- **The producer/editor** — runs OBS: builds browser sources, switches scenes,
  pastes chat, triggers stingers.

The audience is a general public livestream audience watching on YouTube and
Twitch, **on anything from a small phone to a 100-inch television.** The
viewing distance and size are unknown and not controllable. This is the single
most consequential fact about the audience and it governs type and contrast
across every surface.

## Product Purpose

A set of full-screen scenes and transparent modules for a Smile.co.ke livestream
about markets, presented in an entertainment register. Success is that a scene
can go on air without anyone thinking about it, and that it holds up whether
the viewer is on a phone in a car or on a wall-sized screen across the room.

## Positioning

Markets content as set dressing on an entertainment show. Not financial advice,
not a trading platform, not a dashboard. The brand is a smiley; the register is
a variety show that happens to be about markets.

## Operating Context

- Every page is a standalone **OBS Browser Source**. No build step, no
  framework, no runtime dependencies. Reload in OBS and the edit is live.
- The producer adds a scene as a full-screen source, then layers the
  transparent modules (ticker, watermark) above it.
- Scenes and modules follow **opposite** compositing rules and must not be
  confused. This distinction is the core architectural fact of the kit.
- Content that changes per episode — host names, dates, episode numbers,
  schedules — currently means editing the HTML by hand. This is the most
  frequent source of friction.
- Deployed to GitHub Pages by a single script that mirrors `prototype/overlay/`
  to the `gh-pages` branch. The `overlay/` path is load-bearing and the
  published URLs depend on it.
- Streamer.bot switches scenes and triggers stingers via URL parameters.

## Capabilities and Constraints

**Two source types, opposite rules:**

| Type | Pages | Rule |
|---|---|---|
| Painted scene | 9 — `starting-soon`, `brb`, `intermission`, `intermission-b`, `qa`, `tech-diff`, `end`, `end-credits`, `coming-up` | paints its own background, always dark |
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
- Everything is driven by URL parameters today. There is **no** live data
  bridge — `state.json` was once documented but never implemented, and no
  scene reads it.

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
- `core/` — source-of-truth originals, the approved logo files, and the
  original Qwen design reference the kit grew out of.
- `audit/frames/` — one curated best-moment reference frame per scene, captured
  across each scene's animation cycle rather than at a fixed moment.
- `brand.json` — **stale and must not be trusted.** `--muted` is recorded as
  `#8c8c8c` while every page uses `#a1a1aa`; five of its tokens are used by no
  page; seven tokens the pages depend on are absent from it.

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

## Accessibility & Inclusion

- Legibility under video compression, at unknown viewing distance and size, is
  an accessibility requirement here, not a preference. WCAG contrast does not
  directly model a compressed stream watched from across a room.
- Views small and large must both work. No information may exist only in a
  size that suits one of them.
- `prefers-reduced-motion` is honoured as a real state on every page.
- Entertainment-led, not regulated financial advice, so no disclaimer or
  compliance framing is a design requirement.
