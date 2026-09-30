---
name: smile.co.ke broadcast overlay
description: Mission-control visual language for a Kenyan markets livestream — flat vector, dark, instrument-readout calm, with glow reserved for live state.
colors:
  canvas: "#0A0A0A"
  surface-sunken: "#09090B"
  panel: "#141417"
  hairline: "#27272A"
  hairline-soft: "#2A2A2A"
  structure: "#3A3A41"
  text-primary: "#FAFAFA"
  text-muted: "#A1A1AA"
  text-faint: "#9B9BA4"
  accent-brand: "#FFC107"
  accent-hot: "#F5A623"
  cap-yellow: "#FFCE00"
  cap-yellow-lift: "#FFDE7A"
  logo-yellow: "#FFD100"
  market-up: "#0ECB81"
  market-down: "#F6465D"
  market-alt: "#3FB6FF"
  seat-giggles: "#2BB2F5"
  seat-hype: "#FF5A47"
  seat-banks: "#1FD24F"
  seat-halo: "#7CD9F9"
  seat-prof: "#A78BFA"
typography:
  display:
    fontFamily: "'Space Grotesk', system-ui, sans-serif"
    fontSize: "clamp(64px, 11vh, 112px)"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "'Space Grotesk', system-ui, sans-serif"
    fontSize: "clamp(42px, 9.5vh, 92px)"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "-0.03em"
  title:
    fontFamily: "'Space Grotesk', system-ui, sans-serif"
    fontSize: "clamp(26px, 3.6vh, 34px)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  body:
    fontFamily: "'Space Grotesk', system-ui, sans-serif"
    fontSize: "clamp(14px, 2.4vh, 20px)"
    fontWeight: 500
    lineHeight: 1.5
  label:
    fontFamily: "'IBM Plex Mono', ui-monospace, monospace"
    fontSize: "clamp(10px, 1.7vh, 13px)"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.2em"
  data:
    fontFamily: "'IBM Plex Mono', ui-monospace, monospace"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.06em"
rounded:
  pill: "999px"
  circle: "50%"
  panel: "16px"
  control: "7px"
  micro: "2px"
spacing:
  dock: "76px"
  margin-page: "28px"
  gap-tight: "7px"
  gap-base: "10px"
  gap-loose: "14px"
components:
  chip:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "6px 16px"
  chip-live:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.accent-brand}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "6px 16px"
  chip-solid:
    backgroundColor: "{colors.accent-brand}"
    textColor: "{colors.canvas}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "7px 18px"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.panel}"
    padding: "clamp(7px, 1vh, 11px)"
  ticker-pill:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.pill}"
    height: "54px"
  bubble:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-primary}"
    rounded: "18px"
    padding: "13px 18px 15px"
  desk:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-primary}"
    rounded: "4px"
    height: "clamp(34px, 5vh, 54px)"
---

# Design System: smile.co.ke broadcast overlay

## Overview

**Creative North Star: "Mission control"**

Every surface is an instrument readout. Nothing on screen is decoration; everything
is either a signal, a label attached to a signal, or the structure that holds
them. The room is dark so the instruments read. This is a show about markets
presented as entertainment, so the tension to hold is *calm authority over
apparent chaos* — a lot of data texture and a lot of black, with one warm
signal colour cutting through both.

The whole system is **flat vector**. The one time it was not — when the Smile
face was extruded as stacked copies on `translateZ` planes under a perspective
swing — it was removed, because it read as a muddy stacked blur rather than a
solid object. Depth is communicated by **tonal separation and black shadow**,
never by 3D geometry, perspective, or stacked duplicate layers.

The brand mark is a character, never a figure. A yellow circle with two eyes and
a smile, no body, no arms, no humanoid framing. It appears at instrument scale
(a radar blip) and at broadcast scale (a host's face at a desk) and it means the
same thing at both.

The system has exactly one easing curve, `cubic-bezier(.2, .9, .3, 1)`, used 73
times across the kit and almost nowhere else. It is a hard exponential ease-out:
fast commit, long settle. Anything that eases in a different shape needs a
reason, and the reason has to fit on one line.

**Key Characteristics:**

- Flat vector. Zero 3D, zero perspective, zero stacked copies.
- Dark by binding commitment, not by theme. There is no light mode.
- Two families of type only: Space Grotesk for language, IBM Plex Mono for
  instrumentation.
- Two families of shadow, strictly separated by meaning — see Elevation.
- Yellow is a state indicator. It is not an accent colour to be sprinkled.
- Motion is compositor-only: transform and opacity. No animated blur, no
  animated filter, no canvas, no `requestAnimationFrame`.

## Colors

Near-black instrument panel, one warm signal colour, and a small set of
functional data colours that only ever mean a market direction or a speaking
seat.

**There are two different yellows, and both are correct.**

| Token | Value | What it is |
|---|---|---|
| `logo-yellow` | `#FFD100` | The fill inside `Smile-Logo.svg`. Verbatim, never touched. |
| `accent-brand` | `#FFC107` | The brand token used for UI — glow, live states, the highlight word in a headline. |
| `cap-yellow` | `#FFCE00` | The ticker cap's flat fill, a legacy value from the stingers era. |

These are not interchangeable. The logo yellow is an asset, not a token. **Never
"correct" one to match the other.** The ticker's gradient runs
`#FFDE5A → #FFC107 → #E8A800` on the cap only.

**Market colours are semantic, never decorative.** `market-up` `#0ECB81` and
`market-down` `#F6465D` appear on numbers and nothing else. `market-alt`
`#3FB6FF` is the fourth data colour for series that are neither direction.

**Seat colours describe a speaking state.** Six seats, each with one colour,
used on that seat's underglow pool, name-tag glow, and mic LED. They are a
status channel, not a palette:

| Seat | Colour |
|---|---|
| SMILE (host) | `#FFC107` — the brand yellow; the host is the brand |
| GIGGLES | `#2BB2F5` |
| HYPE | `#FF5A47` |
| BANKS | `#1FD24F` |
| HALO | `#7CD9F9` |
| PROF | `#A78BFA` |

`brand.json` is **stale and is not the source of truth.** It records
`--muted` as `#8c8c8c` when every page uses `#A1A1AA`; five of its tokens are
used by no page, and seven tokens the pages depend on are missing from it. The
CSS in the pages is authoritative. Fix `brand.json` or delete it — do not
design against it.

## Typography

Two families, and the split is not stylistic — it is **semantic.**

**Space Grotesk** carries anything a person would *say*. Headlines, the tagline,
name tags, ad copy. It is never used for numbers.

**IBM Plex Mono** carries anything a machine would *report*. Clocks, tickers,
episode numbers, seat labels, chip captions, all caps utility text. It appears
70 times across the kit and is the workhorse.

The tracking split is the tell and it must not blur:

- **Display type is tracked negative** — `-.03em` on the display and headline
  roles. Large type in Space Grotesk needs tightening or it reads loose.
- **Labels are tracked wide** — `.14em` to `.46em`, always uppercase, always
  mono. This is the "instrument" signal. There is no un-tracked mono text.

**Weight does the hierarchy work, not size alone.** 600 dominates the kit (63
occurrences) over 500, because 600 survives compression. 400 and 500 are used
sparingly and never for anything that must be read at distance.

**Legibility is a correctness requirement, not a preference.** The viewer may
be on a 5-inch phone or a 100-inch television and we cannot know which. The
observed failures under h.264 at 1080p are, in order:

1. **Anything below ~9px.** Seat role labels were shipped at `6.5px` and had to
   be raised. There is no legitimate reason to go below 9px on a broadcast
   surface, and 11px is the practical floor for anything that carries meaning.
2. **Colour-only distinction at small size.** Green and red at 10px on a
   compressed stream is not a reliable signal. Pair the colour with a `+`/`-`
   sign and a direction word.
3. **Thin weight on dark.** 400-weight mono disappears. 600 minimum on any
   label that must be read.

`font-variant-numeric: tabular-nums` is required on every number that changes
in place — a clock or a ticker that jitters as digits swap is unreadable.

## Layout

**The frame is a fixed instrument panel, not a responsive page.** Every scene
is 1920×1080. The ticker and watermark modules are 1920×76 and 1920×120. There
is no breakpoint work, because there is no second layout — this is not a
website.

**Two reserved zones are structural law:**

- **The bottom 76px** is the ticker's dock, on every scene, without exception.
  It is expressed as `--safe-b: 76px` and is the one number a scene must never
  drift from. Content may not enter it.
- **The top-left corner** belongs to the watermark module. Scenes leave it clear.

Scene margins run 28–36px from the frame edge. Interior gaps cluster tightly at
7–14px, which is what makes the kit read as dense instrumentation rather than
an airy landing page. **Density is the house style.** A scene that feels empty
is usually correct; a scene that feels crowded is usually broken.

Most scenes are **asymmetric and left-weighted**: a headline block on the left
third, the Smile mark or radar mass to the right, data texture along the bottom
edge. Centred compositions are reserved for the two most declarative moments —
`end.html` and `end-credits.html` — because closing a show is a curtain call,
not a dashboard.

## Elevation & Depth

Two shadow families, and **keeping them separate is the single strictest rule in
this system.**

**1. Black ambient shadow — this is depth.** Wide, soft, zero-hue. Its only job
is lifting a surface off the canvas.

```
0 6px 24px rgba(0,0,0,.35)      card / chip
0 10px 30px rgba(0,0,0,.45)     desk
0 34px 90px rgba(0,0,0,.6)      media wall
```

**2. Yellow glow — this is a live state.** It appears **only** when the state it
describes is genuinely active: a seat is speaking, a mic is hot, a chip is live.

```
0 0 14px rgba(255,193,7,.9)     mic LED, active seat
0 8px 28px rgba(255,193,7,.28)  active chip
0 0 10px rgba(246,70,93,.8)     live dot, off-air
```

**The rule: a glow is a sentence with a subject.** If you cannot name the live
state the glow is describing, it is decoration and it comes out. This is the
distinction that keeps the kit from collapsing into the "dark glow" look that
every AI-generated dark theme defaults to.

**Inset shadow is the third tool**, used for a physical edge on a lit surface —
the top highlight line on a desk, the inner shade in a bubble. It is a material
cue, not depth, and it is always 1px-scale.

Flattened surfaces use `1px solid {colors.hairline}` **instead of** shadow, never
as a ghost card on top of one. Pick an edge or pick a soft elevation.

## Shapes

**The system is a capsule world.** `border-radius: 50%` appears 54 times and
`999px` appears 31 times; together they are the overwhelming majority of shape
language. Chips, pills, the ticker, desks, seats, the smile itself.

Beyond the capsule:

| Radius | Use |
|---|---|
| `999px` | any pill, chip, or long surface |
| `50%` | any circle: the face mark, radar blips, live dots, bubbles' tails |
| `16px` | large panels — the media wall, cards |
| `7px` | controls and small containers — name tags |
| `4px` | desk fronts, small insets |
| `2px` | hairlines and the slash separators |

**One diagonal form exists and it is load-bearing:** the ticker's cap is cut with
`clip-path: polygon(0 0, 100% 0, calc(100% - 20px) 100%, 0 100%)`, and its
separators are 16px bars skewed `-24deg`. This is the whole reason the ticker
reads as a market feed rather than a word cloud. **Do not straighten it.**

Asymmetric corner radii do real work too — the Q&A bubbles are
`18px 18px 18px 4px`, or its mirror, so the tail corner points at the speaker.

## Components

**Chip** — the most reused component in the kit. Mono, uppercase, wide-tracked,
pill-shaped. Three states:

- `chip` — quiet panel, primary text. Labels, meta, secondary actions.
- `chip-live` — same shape, yellow text and a live dot. Currently-live state.
- `chip-solid` — yellow fill, dark text. The single most important thing on a
  scene, used once.

A scene has **at most one** `chip-solid`. Two is a hierarchy failure.

**Desk** — a broadcast desk in two parts: a lit top surface (`3d3d48 → 232329 →
141419`, with a white inset highlight) over a dark front face. Carries the seat
name tag and, when active, a radial underglow pool in that seat's colour.

**Ticker cell** — mono, 12.5px, with a `.s` label in 10.5px uppercase at `.14em`
tracking and a tabular-numeral value. Values are green/red with an explicit
`+`/`-`. Cells are separated by a **16px skewed amber slash**, not by spacing
alone and not by a rule.

**Bubble** — Q&A comment. `18px` asymmetric radius, a 13px rotated square tail
in the corner nearest the speaker, `13px 18px 15px` padding.

**Panel** — the media wall and card surfaces. Dark, `16px`, hairline, wide black
shadow.

## Do's and Don'ts

**Do**

- Use Space Grotesk for language, IBM Plex Mono for anything a machine reports.
- Track display type negative (`-.03em`) and mono labels wide (`.14em`+).
- Reach for 600 before you reach for a larger size.
- Put a black ambient shadow under a surface, or a 1px hairline on it. One or
  the other.
- Name the live state a yellow glow is describing. If you can't, delete it.
- Keep the bottom 76px clear on every scene.
- Set `font-variant-numeric: tabular-nums` on anything whose digits change.
- Use `prefers-reduced-motion` as a real poster state, not a paused animation.

**Don't**

- **Don't add 3D.** No `transform-style: preserve-3d`, no `translateZ` stacks,
  no perspective, no duplicated layers for depth. It was tried and removed.
- **Don't build a light mode.** Dark is a binding brand commitment, not a theme.
- **Don't redraw, recolour, "improve" or animate the logo.** Copy the four paths
  from `Smile-Logo.svg` verbatim. The logo yellow `#FFD100` is not the brand
  token `#FFC107` and neither is wrong.
- **Don't add a second easing curve** without a one-line reason. `.2,.9,.3,1`
  is the curve.
- **Don't put more than one `chip-solid` on a scene.**
- **Don't use the seat colours as decoration.** They are a status channel.
- **Don't use `market-up` / `market-down` for anything but market direction.**
- **Don't straighten the ticker's diagonal.** Cap cut and slash separators stay.
- **Don't add a `color-scheme` meta to a transparent page.** It makes Chromium
  paint an opaque root canvas and the module becomes a dark rectangle in OBS.
- **Don't animate blur or filters.** Compositor-only: transform and opacity.
- **Don't design against `brand.json`** — it is stale and contradicts the CSS.

**Confirmed anti-reference**

This system must never look like an **AI-generated dark landing page** — the
big centred hero over a mesh gradient, the purple-to-blue accent, three equal
feature cards, a pill CTA floating in dead space. That is the specific failure
mode named as the thing to avoid, and it is the reason the density rules above
are strict.

The kit is a broadcast instrument panel. Dense, asymmetric, dark, and warm in
exactly one place at a time.
