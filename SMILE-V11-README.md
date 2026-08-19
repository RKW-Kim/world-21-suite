# SMILE · V11 — Broadcast Overlay Architecture

> Self-contained HTML overlay for the **SMILE TV** Nairobi finance & trading-education livestream.
> Designed for OBS Studio Browser Source at 1920×1080 / 1280×720. No build step, no frameworks.

**Live URL:** <https://rkw-kim.github.io/world-21-suite/smile-v11.html>

**Ship verdict (GLM 5V Round 4):** `8.6 / 10 — Ship-ready.`

---

## 1. Overview

`smile-v11.html` is the production lower-third + smile-mascot overlay for **SMILE TV**, a Nairobi-based livestream teaching chart-reading, risk management, and Nairobi-Securities-Exchange literacy to retail traders in the East-African time zone. It runs as an **OBS Studio Browser Source** layered on top of the host's webcam + chart capture.

The overlay is intentionally minimalist. The single sacred brand element is the **smile face** — a yellow SVG circle with a curved-arc mouth and two dot eyes. Everything else (ticker, popup island, color theming, animations) is in service of keeping that smile alive on screen without ever modifying it. V11 was the deliberate "revert to simplicity" release after V10 experimented with emoji overlays (teeth, tongue, grin variants) that GLM 5V critique flagged as AI-slop.

### Audience & deployment

- **Audience:** Nairobi retail traders, EAT timezone, demo-account-only education, English + Swahili code-switching in chat.
- **Deploy target:** OBS Studio Browser Source. URL goes in the source's "URL" field. Recommended size 1920×1080, custom CSS `body { background: rgba(0,0,0,0); }` for transparency, framerate 30 fps, shutdown when not visible.
- **Overlay mode:** pass `?overlay` in the URL so the page renders with transparent background and no `market-bg` chart wallpaper (the OBS scene below provides the chart).
- **Live URL:** <https://rkw-kim.github.io/world-21-suite/smile-v11.html> (deployed from `gh-pages` branch; source on `prototype` branch in `RKW-Kim/world-21-suite`).

---

## 2. Live URL

```
https://rkw-kim.github.io/world-21-suite/smile-v11.html
```

| Variant                | URL                                                                             |
| ---------------------- | ------------------------------------------------------------------------------- |
| Default (full-bg)      | `…/smile-v11.html`                                                              |
| OBS overlay (chroma)   | `…/smile-v11.html?overlay`                                                      |
| Bottom-left home       | `…/smile-v11.html?home=bottom-left`                                             |
| Low-perf machine       | `…/smile-v11.html?perf=low`                                                      |

GitHub Pages propagates from `gh-pages` branch within ~60-90s of push. See `scripts/deploy-pages-branch.sh` for the deploy recipe.

---

## 3. Architecture

The page is three layered systems, all driven by a single `<div id="strap">` and a single `<div class="ticker">`:

```
┌─────────────────────────────────────────────────────────────────┐
│  .stage / .bg-grad / .market-bg   ← background gradient + chart │
│                                                                  │
│                                                                  │
│                                                                  │
│                                                                  │
│  ┌─────┐                                                         │
│  │ :-) │  ← #strap (the ISLAND) — single element, morphs idle↔active
│  └─────┘                                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ SMILE·LIVE │ EUR/USD │ GBP/USD │ USD/JPY │ XAU │ BTC │ wire│DESK-TIME│
│  │  cap.left  │  6 ticker cells (5 pinned + 1 rotating wire)  │  pill   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3a. The island morph — one element, two shapes

The single `<div id="strap">` is the entire smile system. It morphs between two shapes:

| State   | Shape                  | Size            | Content                                                              |
| ------- | ---------------------- | --------------- | -------------------------------------------------------------------- |
| **IDLE**| circle (just the face) | 56×56 strap, 48px smile | none — just the gold smile floating over `cap.left` of the ticker   |
| **ACTIVE** | pill (rounded rect)    | 86×86 strap, 64px smile, `width: fit-content` (340–560px) | kicker + headline + sub + badge/num + (ladder or steps) + progress bar |

The morph is achieved with **CSS custom properties registered via `@property`** so the smile size and strap width animate smoothly between idle and active without JS rAF. The smile face stays anchored on the left edge of the strap (or right edge on right-side homes — see §3d).

### 3b. The smile face — sacred, never modified

```svg
<circle class="face face-grad" cx="50" cy="50" r="48"/>
<circle class="eye" cx="31" cy="35" r="5.5"/>
<circle class="eye" cx="69" cy="35" r="5.5"/>
<path class="mouth" d="M 20 48 A 30 30 0 0 0 80 48"/>
```

The face is a `<radialGradient>` filled circle, two dot eyes, and a curved-arc smile path. The HTML carries a comment block at line 35 and line 325 marking it **canonical and never to be modified**. GLM 5V's A6 critique explicitly flagged any per-state recoloring of the face as brand heresy — the smile observes state, never becomes state. State color is carried only by:

1. Island outer glow (`box-shadow` color per `.st-*` class)
2. Badge background (`.badge` per `.st-*` class)
3. Progress bar fill (`#strap.on.st-* .progress i` color)
4. Reactive eye micro-expressions (scaleY transforms — see §5d)

The face fill is **always** `var(--c-accent)` = `#FFB020` (mango gold), in every state, in every home, in every theme.

### 3c. The ticker — `cap.left` + 6 cells + desk-time pill

The ticker is a 68px-tall bar flush against the bottom of the screen (broadcast-safe-area: `left: 48px; right: 48px; bottom: 0;`), with three regions left-to-right:

1. **`cap.left`** — gold gradient bar with `SMILE · LIVE` text. At idle it reserves 64px of left padding for the smile logo to sit on top of (the smile floats over the bar). When a popup fires (`body.strap-active`), the padding collapses to 28px so the text shifts left into the now-empty slot (650ms expo transition). Bevel is **concave/recessed** (highlight on bottom, shadow on top, right-edge inner shadow) — milled-into-strap groove per GLM 5V R2 #1.
2. **`.cells`** — CSS grid `repeat(6, 1fr)` of price cells. Cells 0-4 are pinned pairs (EUR/USD, GBP/USD, USD/JPY, XAU/USD, BTC/USD). Cell 5 is the **wire slot** — rotates through a `UNIVERSE` of 12 instruments (NAS100, SPX500, US30, NVDA, AAPL, TSLA, ETH/USD, SOL/USD, EUR/GBP, USD/KES, NSE 25, US OIL) every 7s, with a 2px progress bar at the bottom showing time-to-swap. Each cell has a flashing background pulse on significant price moves (`.fup`/`.fdn` keyframes) and a colored caret on the change percent.
3. **`.dclock`** — desk-time pill on the right. Cycles through 3 modes via `T` key: **live** (HH:MM:SS + "DEMO"), **tape** (DD MON HH:MM + "REC · DEMO"), **stealth** (black-on-black, invisible — for clean recording).

### 3d. The 5 home positions

The strap (`#strap`) can live in any of 5 corners of the screen, cycled by `M`:

| Class                | Label          | Idle position                    | Active position                  | Island growth direction |
| -------------------- | -------------- | -------------------------------- | -------------------------------- | ----------------------- |
| `home-inside`        | inside-ticker | `left:28; bottom:30` (over `cap.left`) | `left:24; bottom:102` (slides up above ticker) | rightward (smile stays left) |
| `home-bottom-left`   | bottom-left    | `left:24; bottom:102`            | same coords, size grows          | rightward               |
| `home-bottom-right`  | bottom-right   | `right:24; bottom:102`           | same coords, size grows          | **leftward** (island `right:0` anchored) |
| `home-top-left`      | top-left       | `left:24; top:24`                | same coords, size grows          | rightward               |
| `home-top-right`     | top-right      | `right:24; top:24`               | same coords, size grows          | **leftward** (island `right:0` anchored) |

On right-side homes, the smile face is flipped to the RIGHT side of the island (`order: 2`) and content is on the LEFT (`order: 1`, padding mirrored), so the smile stays anchored to the screen edge. This is the GLM 5V A2 fix — the original implementation grew the island off-screen on right-side homes because the strap's 86px width couldn't accommodate the `fit-content` overflow.

---

## 4. State machine — 12 popup states

Triggered by keyboard 1-9, 0, Q, E. Each fires `STATES.<name>()` which calls `showStrap(cls, kicker, head, sub, opt)`. The strap gets `on st-<cls> <home-class>` classes; a progress bar starts depleting from 1→0 over the TTL; the strap auto-hides on TTL expiry.

| Key | State class   | Kicker             | Headline                          | Subcontent                                              | TTL    | Extra UI                       |
| --- | ------------- | ------------------ | --------------------------------- | ------------------------------------------------------- | ------ | ------------------------------ |
| `1` | (hide)        | —                  | —                                 | —                                                       | —      | hides any active popup         |
| `2` | `st-lesson`   | LESSON             | Support & Resistance              | Chart School · part 2 of 4 · the mango test             | 8.0s   | `12:00` num + `LEFT` badge     |
| `3` | `st-tp`       | LIVE TRADE · DEMO  | Take Profit Hit                   | EUR/USD · long from 1.0810 · plan followed             | 6.0s   | `+32 PIPS` count-up + ladder 88% |
| `4` | `st-sl`       | LIVE TRADE · DEMO  | Stop Loss Hit                     | GBP/USD · short from 1.2720 · risk respected           | 6.0s   | `-18 PIPS` count-up + ladder 6%  |
| `5` | `st-poll`     | POLL               | You Pick the Next Lesson          | A candles · B risk sizing · C news — type in chat       | 10.0s  | `A·B·C` num + `VOTE` badge      |
| `6` | `st-name`     | HOST               | Mwangi                           | Smile TV · Chart School · Nairobi                       | 6.0s   | `smile.co.ke` link + (no badge) |
| `7` | `st-goal`     | STREAM GOAL        | `<n> / 1000`                      | ring on the smile tracks it live · thanks for the 4G smiles | 6.0s | `<n>%` num + `FUNDED` badge     |
| `8` | (wire card)   | DESK / NOTICE / LESSON | (rotating 4-card deck)        | (rotating)                                             | 6.5s   | auto-fires every 90s; manual `8` |
| `9` | (wire swap)   | —                  | —                                 | —                                                       | —      | advances the wire slot          |
| `0` | `st-lesson`   | CHART SCHOOL       | Part 2 — Support & Resistance     | the mango test · 4 parts · live Mondays 9PM EAT        | 10.0s  | 2-of-4 step dots + `2/4` num    |
| `Q` | `st-poll`     | QUESTION           | "How do you know when a level breaks?" | one question in, one skill out — answering on stream now | 8.0s | `Q&A` num + `FROM CHAT` badge   |
| `E` | `st-note`     | CALENDAR           | US CPI — the inflation report     | Thursday 15:30 EAT · high impact · we trade after the number, never into it | 7.0s | `THU` num + `15:30 EAT` badge   |

Plus an automatic `goalHit` state that fires when the goal counter crosses 1000 (8.0s TTL, `GOAL COMPLETE` headline).

### State-theming model

State CSS class (`st-tp`, `st-sl`, `st-poll`, `st-goal`, `st-note`, `st-lesson`, `st-name`) drives four coordinated color changes — kicker text color, badge background, progress bar fill, island outer glow. The smile face fill **never** changes per state (sacred).

---

## 5. Animations

All easing curves are defined as CSS custom properties at `:root`:

```css
--expo:   cubic-bezier(.16, 1, .3, 1);    /* GLM-standard decel */
--spring: cubic-bezier(.22, 1, .36, 1);    /* critically damped — no overshoot */
```

### 5a. Blink

- Eyes `scaleY(.15)` for **60ms hold**, fired every **6.5s** by `Power.every(blink, 6500)`.
- The transition itself is `.08s ease` (in+out = ~120ms total).
- Was 150ms in V10; GLM 5V A5 flagged as "too slow for true blink" — fix applied.
- Mouth is **never** touched by blink.

### 5b. Look-around

- Picks one of 3 directions (`look-left`, `look-right`, `look-up`) every **5-9s random** (`5000 + Math.random() * 4000` ms).
- Holds for **1.2s**, then returns to center.
- **Gated:** suppressed when `#strap` has class `on` (i.e., popup is active) — GLM 5V A5 rule: don't drift eyes during a TP/SL card.

### 5c. Reactive eye micro-expressions

Per-state eye transforms, applied only when strap is active:

| State    | Eye transform       | Effect                                  |
| -------- | ------------------- | --------------------------------------- |
| `st-tp`  | `scaleY(1.12)`      | Eyes widen — "we made pips!"            |
| `st-sl`  | `scaleY(0.88)`      | Eyes narrow — "we took the loss"        |
| `st-goal`| `scaleY(1.18)`      | Eyes wide — "goal hit!"                 |
| `st-poll`| `translateY(-1px)`  | Eyes lift — "your turn to vote"         |
| (others) | (none)              | Eyes rest in default position           |

Transition: `.25s var(--expo)`. Mouth is **never** touched.

### 5d. Island morph

- **Width:** `width .32s cubic-bezier(.22,1,.36,1)` — critically damped, settles in **320ms** with zero overshoot. (Was `cubic-bezier(.34, 1.56, .64, 1)` ease-back in R2; GLM 5V R3 #5 flagged the 7% overshoot as "consumer-bouncy not enterprise-snappy" — replaced with critically damped spring.)
- **Height/background/box-shadow:** parallel transitions on `.4s ease` / `.5s var(--expo)`.
- **Strap position:** `left / bottom / top / right` all transition on `.55s var(--expo)` for smooth glides between homes.
- **CSS custom properties** (`--smile-size`, `--island-w`, `--island-h`) registered via `@property` so they animate smoothly without JS rAF.

### 5e. `cap.left` padding collapse

- Idle: `padding-left: 64px` (reserves space for the smile logo to sit on top).
- Active (`body.strap-active`): collapses to `padding-left: 28px` over **650ms** `var(--expo)`.
- The "SMILE · LIVE" text shifts left into the now-empty slot, creating space for the popup card above the ticker.
- Bevel is **concave/recessed** — `inset 0 -1px 0 rgba(255,255,255,.15)` (bottom highlight) + `inset 0 1px 0 rgba(0,0,0,.4)` (top shadow) + `inset -1px 0 0 rgba(0,0,0,.3)` (right-edge groove). Was convex in R1 (highlight top); GLM 5V R2 #1 flagged as "sitting on top of the strap rather than milled into it" — inverted.

### 5f. Other animations

- **Ticker entrance:** `tickin .9s var(--expo)` with 150ms delay (slides up 90px + fades in).
- **Cell entrance:** cascade `.50s / .60s / .74s / .92s / 1.14s / 1.40s` delays on `cellin .7s var(--expo)`.
- **Cell flash on price move:** `.fup`/`.fdn` 700ms keyframes — green/red inner glow + value color pulse. Locked to 3s minimum interval per cell via `flashLock[]`.
- **Wire slot progress:** 2px bottom bar `wprog` animates `scaleX 0→1` over `--wire-dur` (7s) linear.
- **Idle breathe:** ticker opacity `.92→.97` over 5.2s (above just-noticeable-difference threshold).
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` clamps all animations to 0.01s.

---

## 6. Color palette

```css
--c-bg:      #100d0a;   /* near-black warm — broadcast dark, not pure black */
--c-surface: #1a1612;   /* ticker surface */
--c-elevated:#221d18;   /* elevated panel */
--c-fg:      #FBF7EE;   /* warm white text (not pure #FFF — avoids chroma burn) */
--c-muted:   #a1a1aa;   /* secondary text */
--c-faint:   #8a8a93;   /* tertiary text */
--c-border:  #2a2620;   /* hairline border */
--c-on-accent:#0a0a0a; /* text on gold (smile eyes/mouth) */

/* State colors */
--c-accent:  #FFB020;   /* mango gold — the SMILE brand color. ALWAYS on the face. */
--c-up:      #2EA876;   /* sage green — TP, profit, market-up */
--c-down:    #D9534F;   /* terracotta red — SL, loss, market-down */
--c-sky:     #0ea5e9;   /* sky blue — poll, question, lesson */
--c-violet:  #A855F7;   /* violet — stream goal */
--c-amber:   #D97706;   /* amber (darker gold) — note, calendar */
```

### Sacred rule

The smile face fill is **always** `--c-accent` (`#FFB020`), in every state. State color is carried only by island glow, badge, progress bar, and kicker text. This rule was established by GLM 5V swarm agent A6 — the original V10 implementation recolored the face per state (emerald for TP, red for SL), which A6 flagged as brand heresy.

### Theme variants

- **Dark (default):** bg `#100d0a`, fg `#FBF7EE`.
- **Light** (`body.light`, toggle `L`): bg `#f4f4f2`, fg `#111113`. Smile face still gold.
- **Scenes** (`body[data-scene="1..4"]`, cycle `V`): 4 background gradient variations for different broadcast segments (lesson scene, breakout scene, news scene, etc.). Scene 4 is also light.

---

## 7. Keyboard shortcuts

| Key | Action                                                            |
| --- | ---------------------------------------------------------------- |
| `1` | Hide any active popup (return to idle smile)                     |
| `2` | LESSON popup (`st-lesson`)                                       |
| `3` | Take Profit popup (`st-tp`) — triggers ticker up-line alert      |
| `4` | Stop Loss popup (`st-sl`) — triggers ticker down-line alert     |
| `5` | Poll popup (`st-poll`)                                           |
| `6` | Host / name popup (`st-name`)                                    |
| `7` | Stream goal popup (`st-goal`)                                    |
| `8` | Wire card (manual fire of rotating 4-card deck)                 |
| `9` | Swap wire slot now (advance to next instrument)                 |
| `0` | Chart School popup (`st-lesson`, with 2-of-4 step dots)         |
| `Q` | Question from chat popup (`st-poll`-styled)                      |
| `E` | Economic calendar popup (`st-note`)                              |
| `M` | Cycle home position (5 positions — see §3d)                     |
| `D` | Toggle demo auto-cycle (fires all 9 states every 4.5s)           |
| `V` | Cycle background scene (5 scenes; scene 4 = light theme)        |
| `T` | Cycle desk-time pill mode (live / tape / stealth)               |
| `L` | Toggle light theme                                               |
| `B` | Toggle market-bg chart wallpaper on/off                          |
| `O` | Toggle overlay-mode (transparent bg, hides market-bg)           |
| `H` | Toggle this help panel                                           |

**OBS integration tip:** Bind OBS hotkeys to send these keystrokes to the Browser Source via the "Browser Source → Interaction" feature, or use a Stream Deck with the OBS WebSocket plugin to fire keystrokes through OBS's "Hotkeys" → "Send hotkey to focused source" action.

---

## 8. URL parameters

| Param         | Values                                         | Effect                                                                                       |
| ------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `?home=`      | `inside` \| `bottom-left` \| `bottom-right` \| `top-left` \| `top-right` | Sets initial home position (default: `inside`). M still cycles after. |
| `?overlay`    | (presence-only)                                | Adds `body.overlay-mode` — transparent background, hides market-bg chart wallpaper. Use this for OBS. |
| `?perf=low`   | (presence-only)                                | Adds `body.perf-low` — strips `backdrop-filter: blur(40px) saturate(180%)` from the island (saves GPU on low-end streaming PCs). |

Example OBS URL:

```
https://rkw-kim.github.io/world-21-suite/smile-v11.html?overlay&home=bottom-left&perf=low
```

---

## 9. Design history — 4 rounds of GLM 5V critique

The overlay was iteratively refined through 4 rounds of critique by GLM 5V (vision-capable LLM via z-ai-web-dev-sdk). Each round sent a screenshot montage + structured prompt asking for "remaining top-N issues" with Bloomberg / Apple Keynote / Binance Pro / MSNBC references.

| Round | Issues raised | Issues applied | Issues deferred             | Composite score |
| ----- | ------------- | -------------- | --------------------------- | ---------------- |
| R1 (8-agent swarm) | 8             | 5              | 3 (mouth-arc raise blocked by sacred-logo rule) | (no score — open critique) |
| R2    | 5             | 5              | 0                           | (post-R2: 7.1)   |
| R3    | 5             | 3              | 2 (gold + backdrop-filter)  | (post-R3: 7.5)   |
| R4    | (verdict only)| 0              | 0                           | **8.6 — Ship**   |

### 13 applied fixes

**Round 1 (swarm consolidated, 5 GLM-A1..A8-sourced applied):**

1. **(A1) `cap.left` padding collapse** — reserve 64px at idle for the smile logo to sit over the bar; collapse to 28px when `body.strap-active` fires. 650ms expo transition. "Disney-12 follow-through."
2. **(A2) Right-side strap home flip** — island anchored `right:0` so it grows LEFTWARD (was growing off-screen rightward on `home-bottom-right`/`home-top-right`). Per-state glow color (was always amber — bug).
3. **(A3+A4) Progress bar + ticker bevel** — progress bar was GROWING (`scaleX 0→1`) instead of DEPLETING (`1→0`); fixed. Bumped 2px→3px height, track `.05→.10` opacity, added missing state colors (lesson=sky, note=amber, name=emerald). `cap.left` bevel = milled-aluminum channel (inset top highlight + bottom shadow + right edge).
4. **(A5+A6) Reactive eyes + sacred smile** — face fill stays GOLD in every state (was changing per state — brand heresy). TP widens eyes `scaleY(1.12)`, SL narrows `0.88`, Goal `1.18`, Poll `translateY(-1px)`. Blink hold `150ms → 60ms` (true ~120ms total). Look-around suppressed during popup. Mouth NEVER touched.
5. **(A7+A8) Typography + idle breathe** — "SMILE · LIVE" letter-spacing `.22em → .28em` (broadcast-prestige tracking). `.meta` `11px italic rgba(.4) → 13px var(--c-muted)` (WCAG AA 5.8:1 contrast, was 2.6:1). Idle breathe delta `.92 → .97` (above just-noticeable-difference threshold).

**Round 2 (5 applied):**

6. **Inverted `cap.left` bevel** (P0) — was convex (highlight top, shadow bottom = protruding look); inverted to concave (highlight bottom, shadow top = recessed/milled-into-strap). Deeper right-edge groove. Bloomberg Terminal chassis aesthetic.
7. **Ticker glassmorphic separation** (P0) — added `1px solid rgba(255,255,255,.06)` top border + `inset 0 -1px 0 rgba(0,0,0,.3)` bottom inner shadow. Creates under-glass Binance Pro / TradingView Terminal aesthetic instead of flat-against-bg.
8. **Progress bar track opacity** (P1) — `.10 → .18`. Now meets WCAG 2.1 non-text contrast 3:1 against `#0a0a0a` (was 2.8% luminance, now ~5%).
9. **Card typography 6/12 rhythm** (P1) — `margin-bottom: 6px` on kicker+headline row, `margin-bottom: 12px` on sub+badge row. Headline `font-weight: 700`, subtitle `font-weight: 400`. MSNBC/Sky News asymmetric broadcast scannability.
10. **Island spring** (P2) — replaced `--expo .55s` on `.island` width/height with `--spring` (`cubic-bezier(.34, 1.56, .64, 1)`) `.4s`. Anticipation + ease-back. Sacred `.smile-face` transition left on `--expo .55s` (smile never bounces).

**Round 3 (3 applied):**

11. **Ticker broadcast safe area** (P0) — `bottom: 24px → 0`, `left/right: 24px → 48px`. Removed `border` and `border-radius: 14px` (now flush to screen edges). Replaced 5-layer inset/outset shadow with 3-layer drop shadow (`0 -12px 40px rgba(0,0,0,.6)` ambient occlusion + `0 -4px 12px rgba(0,0,0,.4)` contact + `inset 0 1px 0 rgba(255,255,255,.06)` top edge).
12. **Tabular nums on `.cchg`** (P1) — the lone holdout (`.cval` and `.num` already had it). Added `font-variant-numeric: tabular-nums; font-feature-settings: 'tnum' 1, 'zero' 1`. Bloomberg 4px baseline grid compliance.
13. **Critically damped spring** (P2) — replaced `--spring: cubic-bezier(.34, 1.56, .64, 1)` (7% overshoot) with `--spring: cubic-bezier(.22, 1, .36, 1)` (zero overshoot, 320ms settling). Was R2 fix #5's spring; GLM 5V R3 #5 flagged as "consumer-bouncy not enterprise-snappy" — now critically damped.

### Round 4 — Ship verdict

GLM 5V's final composite score:

| Axis                  | Score | Assessment                                                            |
| --------------------- | ----- | --------------------------------------------------------------------- |
| (a) Visual polish     | 8.5   | Glass + bevel + shadow at Apple Keynote quality; minor gold saturation |
| (b) Information hierarchy | 9.0 | 6/12 rhythm + 700/400 weight + tabular nums = scannable data-dense     |
| (c) Animation quality | 9.0  | Critically damped spring — authoritative, no overshoot, 320ms settling |
| (d) Brand consistency | 8.0   | Strong SMILE identity, centered smile, locked palette                  |
| (e) Broadcast readiness | 8.5 | 48px safe-area margins for 1080p overscan, no rounded ticker corners, layered drop shadows with ambient occlusion |
| **COMPOSITE**         | **8.6** | **Ship-ready.**                                                       |

Verbatim: *"This is a broadcast-grade asset now. Ship now. Unambiguously."*

---

## 10. Deferred items

Two GLM 5V recommendations were intentionally not applied, both contingent on viewer feedback post-launch:

### (a) Gold `#FFB020` → `#E6B84F` desaturation — NICE-TO-HAVE

GLM 5V framed this as the **single highest-impact change still on the table** — the difference between "YouTube overlay" and "Bloomberg Terminal." The current `#FFB020` reads as "warning yellow" / "hazard orange" on consumer TN panels after OBS encoding compresses the color space. `#E6B84F` is the "money color" — desaturated warm brass that signals value without screaming.

**Why deferred:** Brand-sensitive. The smile face fill is the most recognizable brand asset; changing it requires explicit user sign-off per the swarm A6 sacred-logo rule. GLM 5V's verdict: *"for SMILE's likely demographic, the current warmth is acceptable brand expression. Defer to v11.1 post-launch if viewers report eye-strain during long sessions."*

**Open question:** A/B test `#FFB020` vs `#E6B84F` vs `#F5A623` (Apple Keynote standard) in a 30-min stream segment, measure viewer-retention delta.

### (b) `backdrop-filter: blur/saturate` on progress bar track — SKIPPABLE

GLM 5V R3 #4 recommended unifying glassmorphism by inheriting `backdrop-filter` from the ticker to the progress track, for visual consistency (Apple HIG requires consistent glass within a component).

**Why deferred:** At 30fps OBS browser-source, `backdrop-filter` is a GPU tax that provides diminishing returns. The progress bar is already visually separated by `.18` opacity + position. 99% of viewers won't consciously register the blur; 100% of low-end streaming PCs will feel it as frame-time variance. GLM 5V verdict: *"Leave it."*

**Open question:** If OBS drift (see §11.2) is reported in production monitoring, add `will-change: transform` sparingly OR reduce `box-shadow` complexity on the ticker before considering backdrop-filter inheritance.

Both items are tracked for **v11.1** (gold) and **v11.2** (backdrop-filter) post-launch iterations.

---

## 11. Production monitoring

Three failure modes GLM 5V R4 flagged for live OBS use, to watch in the first 2 weeks of broadcast:

### 11.1 Chroma subsampling artifacts (4:2:0 color bleed)

YouTube/Twitch transcode streams use 4:2:0 chroma subsampling. Watch the thin tabular `.cchg` values (`+0.12%`, `+0.31%` — the green/red change percentages) against the dark background after transcoding. If rainbow "fringing" or color-halo edges appear around small numerals, the hotfix is one of:

- Add `text-shadow: 0 0 0.5px rgba(255,255,255,.4)` to `.cchg`.
- Nudge the white color from `#FFFFFF` to `#F0F0F0` (anti-aliased white — pure `#FFFFFF` on `#000000` is the #1 cause of ugly text in compressed video).

### 11.2 OBS browser-source memory leak ("OBS drift")

The `backdrop-filter: blur(40px) saturate(180%)` on the island + the CSS keyframe animations (`blink`, `lookAround`, `idleBreathe`, `wprog`) can cause the embedded Chromium instance in OBS to slowly bloat memory over a 2+ hour stream.

**Monitoring:** Open OBS's `Help → Task List` or `Tools → Activity Monitor` (macOS) / Task Manager (Windows) before going live. Note the OBS process's working-set memory at stream-start. Check again at 60min, 90min, 120min. If working-set grows by >200MB and frame-time begins to drop, apply hotfix:

- Add `will-change: transform` to `#strap .island` (already done — verify still present).
- Reduce ticker `box-shadow` from 6 layers to 3 (drop the inset highlights).
- If still drifting, set `?perf=low` in the OBS browser-source URL (strips `backdrop-filter` from island entirely).

### 11.3 Font fallback flash (FOUT)

The custom font stack (`Space Grotesk` display + `IBM Plex Mono` for tabular numbers + `Inter` body) is loaded via Google Fonts CDN `@import`. If the network hiccups or the CDN URL fails to resolve inside OBS's embedded Chromium, the fallback chain is `system-ui, sans-serif` (Arial / Helvetica) — which has **different metric widths**. Tabular-numeric alignment will break (the `+0.12%` numbers will visibly jump as the wire slot rotates).

**Mitigation:** In OBS, set the Browser Source URL to `file:///path/to/local/smile-v11.html` instead of the GitHub Pages URL, and bundle the fonts locally. To test: temporarily rename the `@import` URL line while OBS is running — if the numbers jump, the alignment is metric-dependent and you must ship local fonts.

**Test procedure:** Comment out line 7 of `smile-v11.html` (the `@import` for fonts) while OBS is open. If the wire-slot numbers visibly shift width when the next swap fires, the test is positive — bundle fonts locally in v11.1.

---

## 12. File structure

```
overlay/
├── smile-v11.html              ← the entire overlay (632 lines, single file)
└── SMILE-V11-README.md         ← this file
```

`smile-v11.html` is **self-contained** — no build step, no `node_modules`, no framework, no external CSS/JS. Everything is inline:

- **CSS** in a single `<style>` block (~290 lines) at the top of `<head>`.
- **HTML body** (~40 lines) — `.stage` (background gradient + market-bg chart wallpaper) + `#help` panel + `#strap` (the island + smile face + popup content + progress bar) + `.ticker` (cap.left + 6 cells + desk-time pill).
- **JS** in a single `<script>` block (~265 lines) at the end of `<body>` — `Power` interval manager, data model (`PINNED` array + `UNIVERSE` array + `SESSIONS` session-weighting), `paint()`/`tick()` price simulation, `STATES` popup state machine, keydown handler, scene/demo/keyboard wiring.
- **SVG** inline (`<svg class="smile">` for the smile face, `<svg viewBox="0 0 1920 460">` for the market-bg chart wallpaper).

### Dependencies

- **Google Fonts** (`@import` at line 7) — Space Grotesk, IBM Plex Mono, Inter. Falls back to system fonts if blocked (see §11.3).
- **No JS frameworks.** No React, Vue, jQuery. Vanilla DOM + `setInterval` + `addEventListener('keydown')`.
- **No build step.** Edit the HTML, save, refresh OBS Browser Source (`Right-click → Reload` or `Ctrl+R` while focused).

### Branching & deployment

- **Source branch:** `prototype` on `RKW-Kim/world-21-suite`.
- **Deploy branch:** `gh-pages` (GitHub Pages reads from this branch in "Deploy from a branch" mode).
- **Deploy script:** `scripts/deploy-pages-branch.sh` — stashes working tree, snapshots `overlay/`, wipes `gh-pages` tree, restores snapshot, commits `chore(pages): regenerate gh-pages from prototype/overlay/`, force-pushes `gh-pages`, switches back to `prototype`, pops stash.
- **Live propagation:** ~60-90s after `gh-pages` force-push. Verify via `curl -sI https://rkw-kim.github.io/world-21-suite/smile-v11.html | head -1` expecting `HTTP/2 200`.

---

## License & ownership

© SMILE TV, Nairobi. Source code in this repository is the property of the SMILE TV project. See `LICENSE` in repo root.

## Related artifacts

- **GLM 5V critique responses:** `/home/z/my-project/glm-frames/{r1-swarm-a1..a8,r2,r3,r4}-response.txt`
- **Screenshot montages:** `/home/z/my-project/glm-frames/{r2,r3,r4}-montage.png`
- **Worklog:** `/home/z/my-project/worklog.md` — full session history across all 4 rounds
- **Deploy script:** `scripts/deploy-pages-branch.sh`
- **OBS setup guide:** `docs/OBS_SETUP.md`

---

*Last updated: 2026-08-19 — Task ID: DOC-SMILE-V11*
