# SMILE SUITE — MASTER ARCHIVE (context offload)

> Restored from the original build chat. Nothing left out: every turn, every quote
> (including the grilling), every failure, every rule, every discovery.
>
> USAGE: this file + the full `smile-v9.html` code restores 100% context to any new chat.

# SMILE SUITE — MASTER ARCHIVE
> Complete conversion of the original build chat into a single README.
> Nothing left out: every turn, every quote (including the grilling), every failure, every rule, every discovery.
> 
> USAGE: Paste this entire file + the full code of `smile-v9.html` into any new AI chat to restore 100% context.
> The shared-chat link (https://chat.together.ai/s/99949951-c86e-4569-9541-4a7fe12ea0b3) exists for HUMAN reference —
> TESTED: AI web-fetch CANNOT read it ("Unable to fetch this web page"). Do not rely on the link; rely on this file.

---

## 0. HOW TO USE THIS ARCHIVE

1. Paste the whole archive into the new chat first.
2. Paste the complete `smile-v9.html` code second.
3. Ask the continuity test (Section 12) — if the AI fails it, the offload didn't land.
4. Delivery format going forward: COMPLETE FULL FILES in chat. No diffs, no batches for code, no terminal commands.

---

## 1. PROJECT IDENTITY

- **Project**: SMILE TV — a finance/trading education livestream overlay system.
- **Base**: Nairobi, Kenya. Audience: Kenyan / East African retail-trading-curious viewers.
- **Host placeholder**: Mwangi. Site placeholder: smile.co.ke.
- **Format**: Live trading education on a DEMO account — an ethical stance, not a limitation.
  - Framing: "education only, never financial advice; trading involves risk."
  - Some content pre-recorded (clock has a tape mode — never fake-live), some genuinely live.
- **North star reference**: TraderTV Live — their six components mapped to SMILE:
  webcam grid, live P&L widgets, desk commentary, lower-third straps, ticker, breaking-news alerts.
  BUT: our pace is classroom-friendly, not trading-floor frantic. Identity is warm and alive, not corporate.
- **Brand voice** (real phrases used in the overlay copy):
  - "4G smiles"
  - "losses are tuition — we show ours so you pay less of yours"
  - "one question in, one skill out"
  - "the mango test" (teaching metaphor for support/resistance)
  - "Chart School" (4-part lesson series), live lessons Mondays 9PM EAT
- **Deliverable**: ONE self-contained HTML file = OBS browser source. No frameworks, no build step,
  no external assets except Google Fonts. Must run 24/7, survive OBS, never leak memory.

---

## 2. ENVIRONMENT & DELIVERY CONSTRAINTS (hard rules)

1. **Full files only.** User copies the entire file as-is. No patches, no "edit line 40," no scripts.
2. **Batched heredoc delivery failed before** — truncation killed files mid-tag. Never again for code.
   (Batches are acceptable ONLY for this archive document, which the user explicitly allowed.)
3. **No jargon without inline definition.** ("Wire" landed as "wtf is wire" — it's newsroom slang for the Reuters/AP feed.)
4. **No metaphors unflagged.** "Volume up" was once taken literally. Plain language; flag metaphors as metaphors.
5. **User judges by screenshots.** Every delivery must say: what to press, what the eyes should report.
6. **Momentum matters.** Ship first, explain second. Long silence or over-explaining without shipping loses the user.
7. **OBS is the runtime.** Browser source, single display, app-mode windows, future `?present` chromeless mode.

---

## 3. MASTER INDEX OF THE ORIGINAL CHAT (21 turns + finale)

Era 1 — THE v8 BUILD (turns 1–9)          → Archive Section 4
Era 2 — PHILOSOPHY & REFERENCE (10–14)    → Archive Section 5
Era 3 — THE GRILLING ERA (15–20 + finale) → Archive Section 6
Taste profile (grilling distilled)        → Archive Section 7
Landmines catalog                         → Archive Section 8
Design tokens                             → Archive Section 9
V9 file anatomy                           → Archive Section 10
Roadmap                                   → Archive Section 11
Continuity test + working agreement       → Archive Section 12
Machine-readable JSON (everything above)  → Archive Section 13

---

---

## 4. ERA 1 — THE v8 BUILD (turns 1–9)

### Turn 1 — The ask
HUMAN: "Upgrade everything, focus on finance-trading."
AI: Sketched a brand-new SMILE Suite v8 — clean CSS, finance-only controls, Dynamic-Island UI,
OBS-friendly URLs, watch-list, calendar, risk meter, lesson mode, BRB scenes, mascot moods.
LESSON: First reply was a near-complete overnight overhaul. Set the scope of the whole project.

### Turn 2 — The output-limit crisis (process scar #1)
HUMAN: "I hit the output limit — send code in batches."
AI: Pivoted to a diff-based, idempotent batch plan (v8_01_core.py, v8_02_watchlist.py, ...) and
delivered the first patch.
SCAR: Batched delivery was born here out of necessity. It worked for v8 but the same technique
later caused truncation deaths on heredoc-built files. Root cause of the eventual rule:
FULL FILES ONLY for code.

### Turn 3 — Finishing the core script
HUMAN: "Here's the last bits — finish it."
AI: Added the missing JS/HTML for the lesson bar and BRB veil.

### Turn 4 — New file: smilev8.html
HUMAN: "Write a brand-new file smilev8.html."
AI: Outlined a 10-batch plan and shipped batch 1 (skeleton + core CSS).

### Turn 5 — The "Next" cadence begins
HUMAN: "Next."
AI: Delivered dynamic-island CSS, ticker, cards, watchlist, signal tracker, chat/poll CSS,
PiP cam, meet tiles, BRB veil, lesson bar, control-panel CSS, viewer markup, core JS.
NOTE: "Next" became the project's drumbeat. It means: keep shipping, don't stop to ask permission.

### Turn 6 — Island engine & trade tracker
HUMAN: "Next."
AI: Added mascot SVG, island rotation, view timer, alerts, trade state, ticker engine.

### Turn 7 — Backdrop & meet engines
HUMAN: "Next."
AI: Added market-chart, wave, matrix backgrounds, meet tiles, chat/poll pushers,
countdown/lesson/BRB timers.

### Turn 8 — Panel wiring & final boot
HUMAN: "Next."
AI: Wired presets, scenes, layers, inputs, buttons, watchlist, boot logic — finished the
single-file overlay. smilev8.html COMPLETE.

### Turn 9 — Design & workflow philosophy (the nine Q&As)
HUMAN: Asked about island vs ticker, host vs viewer pages, delay & leak protection,
political vs finance channels, demo-account teaching model.
AI explained, in plain language:
  a) EVENT-BUS architecture — one internal message system all modules subscribe to,
     so any widget can react to any event without hard wiring.
  b) RUNDOWN concept — the show as a sequence of named segments.
  c) LIVE-DESK vs LOOP modes — manned broadcasting vs unattended rotation.
  d) Single-display constraints — what one screen can and can't do.
  e) APP-MODE windows — chromeless browser windows for clean capture.
  f) PRESENTER MODE — a future `?present` URL param for a chromeless tab view.
  g) DELAY BUFFERS — OBS delay keeps the broadcast alive through a kill/rejoin
     (stream-kill/rejoin trick confirmed in a later turn: stop the stream, start a
     tech-difficulties scene, re-join — the same broadcast survives).
  h) CHAT MODERATION — delay-buffer awareness for moderation safety.
  i) DEMO-ACCOUNT ETHICS — teaching on demo is honest framing, not a weakness:
     losses shown as tuition, wins shown as process, never as signals to copy.

---

---

## 5. ERA 2 — PHILOSOPHY & REFERENCE (turns 10–14)

### Turn 10 — Stream-kill/rejoin & full-screen tab capture (two operational discoveries)
HUMAN: "Can I just stop the stream, start a tech-difficulties scene, and re-join…?"
AI confirmed:
  DISCOVERY A — OBS's delay buffer keeps the SAME broadcast alive through a kill/rejoin.
    You can stop the stream, show a tech-difficulties scene, re-join, and viewers never
    leave the original broadcast. Operationally critical for a solo 24/7 station.
  DISCOVERY B — Chrome's "Document Picture-in-Picture" gives a full-screen view of a
    single tab (chromeless). Combined with the future `?present` mode = clean capture
    of any overlay page without OBS scene surgery.

### Turn 11 — Lower-third / ticker layout (the permanent-vs-overlay distinction)
HUMAN: "Is the lower-third permanent or overlay? How to manage it?"
AI clarified the architecture that still governs V9:
  - TICKER = PERMANENT overlay. Always on. Never hides. The station's pulse.
  - LOWER-THIRDS ("straps") = OVERLAY LAYERS. They slide in, do their job, slide out.
  - Gave a full construction blueprint: scrim, kicker, headline, rule, sub-line,
    optional ladder, optional number block, staggered mask-reveal entrance.
  This blueprint became V7's strap — later judged SACRED.

### Turn 12 — TraderTV Live reference (the north star gets mapped)
HUMAN: "I want it to feel like TraderTV Live but with our style."
AI mapped TraderTV's six components to SMILE equivalents:
  1. Webcam grid          → meet tiles (kept)
  2. Live P&L widgets     → trade state / ladder (kept)
  3. Desk commentary      → host + wire cards
  4. Lower-third straps   → the strap system
  5. Ticker               → static 6-cell ticker
  6. Breaking-news alerts → alert lines + strap interrupts
  Adjustments: keep the webcam grid and live-P&L widgets, but pace = classroom-friendly,
  tone = warm teacher, not shouting floor trader.
  Added a new "NAME" bar state (host introduction strap) — later bound to key 6.

### Turn 13 — Tournament-style variant testing (a working method is born)
HUMAN: "Let's build variants and pick the best."
AI proposed three design variants, all sharing ONE LOCKED SPEC so comparison is fair:
  - TERMINAL — dense, data-forward, Bloomberg-flavored
  - STUDIO   — broadcast-warm, type-led, strap-choreographed
  - SIGNAL   — alert-forward, trade-event-centric
  METHOD RULE (permanent): when exploring, present 2–3 NAMED variants sharing a locked
  spec; user picks a winner; winner becomes the new baseline.
  OUTCOME (from later turns): STUDIO won. V7's strap is Studio's legacy.

### Turn 14 — The Test-7 pivot (THE TURNING POINT)
HUMAN: "I want to edit that look… use variants of that one." (referring to Test-7.html)
AI fetched the file, analyzed it: a rich, "warm, alive" design.
PIVOT: stopped trying to rewrite from scratch. New strategy = EVOLVE WHAT ALREADY WORKS.
  Plan: V1 baseline → V2 wired → V3 faithful (with the user's exact smile SVG).
  This turn ended the "clean rebuild" instinct and started the "preserve the good stuff,
  add choreography" instinct that produced every version the user actually liked.

---

---

## 6. ERA 3 — THE GRILLING ERA (turns 15–20 + finale)
> This is the most important era. Every quote is verbatim. Every verdict produced a rule.

### Turn 15 — "I hate it" (the taste line gets drawn)
HUMAN, VERBATIM: "I'm not a fan of it, genuinely I hate it."
  (About the minimal/stripped baseline V1–V2 direction.)
AI response: acknowledged the pattern on the spot —
  MINIMAL = DISLIKED. RICH + CHOREOGRAPHED = LIKED.
  Asked for two things: the exact smile SVG, and a one-sentence "good stuff" list from Test-7.
RULE FORGED: Never offer minimalism as a virtue. Density with intent is the house style.

### Turn 16 — The smile SVG arrives
HUMAN: provided the exact smile markup (canonical 100-viewBox: face circle r=48 at 50,50;
  eyes r=5.5 at 31,35 and 69,35; smile-path mouth).
AI: delivered V3 (faithful to Test-7 + exact SVG) and V4 (amplified: entrance springs,
  sheen, wire, lower-third choreography).
HUMAN VERDICT: still not good enough.
RULE FORGED: The canonical smile SVG is FIXED. Any mouth path must be authored in the
  100-viewBox coordinate space, chord-centered at x=50. (This rule exists because of
  the later off-center grin bug — wrong-viewBox paths.)

### Turn 17 — "V4 wins… but not wowing me"
HUMAN, VERBATIM: "Better but of course V4 wins here, but still not wowing me honestly."
AI explained: "volume up" had been a METAPHOR (user had taken it literally — jargon/metaphor
  scar). Clarified what V4 actually added: polish (entrance springs, sheen, wire,
  lower-third choreography), not loudness.
RULE FORGED: Plain language always. If a metaphor is used, flag it as a metaphor.

### Turn 18 — V5: "different stuff… and more"
HUMAN: "Do V5 with different stuff as you have said and more."
AI delivered the "living ticker":
  - six live symbol cells
  - full-ticker alert floods (top line draws across in up/down color)
  - smile mouth morphs (grin/frown via d:path transitions)
  - pips counter with cubic-eased counting
  - particle burst on take-profit
  - trade ladder (SL—dot—TP position bar)
  - REMOVED the marquee (scrolling ticker text) — static cells instead

### Turn 19 — V6: the static-ticker rationale
HUMAN: "Talk me through the concept of just the ticker thing not scrolling."
AI explained: a static ticker reads at a glance from across the room; scrolling demands
  attention a teacher can't spare; the station's pulse comes from flashes and swaps,
  not motion for motion's sake.
V6 changes:
  - removed the right-cap pill
  - goal tube → GOAL RING on the smile (progress arc around the mascot)
  - wire messages → lower-third cards (the "wire cards")
  - fixed smile moods
  - removed sparklines from ticker cells

### Turn 20 — V7: THE APPROVED ONE
HUMAN: "Talk me more into it. Lower-third pop out card thingie design not to big on them
  honestly." (i.e., explain it more; and keep the cards small)
AI delivered the "Studio" style:
  - STRAP-TYPE lower third with TYPE-ONLY MASK REVEALS (no box sliding, just type
    rising out of overflow-hidden masks, staggered: kicker .08s, headline .16s,
    rule .30s, sub .34s, expo ease cubic-bezier(.16,1,.3,1))
  - refined ticker
  - new visual hierarchy
VERDICT: APPROVED. V7's strap choreography is henceforth SACRED — do not regress it.

### FINALE — The V8 precision rebuild disaster ("Broski, we're going backwards")
AI attempted a "precision rebuild" (V8) with four changes:
  1. clip-path wipe for the strap number block
  2. absolute-positioned number block
  3. JS-injected ticker cells
  4. JS-calculated strap position
ALL FOUR FAILED. The user's eyes reported:
  - number block DETACHED and OVERLAPPED the ticker
  - strap LAY ON TOP of ticker cells
  - cells FLASHED LIKE STROBES (entrance animation replaying on every flash)
  - grin rendered OFF-CENTER (mouth paths authored for the wrong viewBox)
  - wire slot's counter badge COLLIDED with its change pill
  - progress bar read as a RANDOM UNDERLINE under the price
  - goal ring track read as an UGLY OUTLINE around the smile
HUMAN, VERBATIM: "Broski, we're going backwards."
AI response: converted the grilling into a numbered fix list and shipped V9 —
  V7's EXACT motion system restored, with ONLY surgical fixes:
  - flashes: soft 1.4s fades, significance-gated, max 1 per 3s per cell,
    entrance animation plays EXACTLY ONCE (.done class on animationend)
  - wire cell: counter badge DELETED; progress bar moved to cell's BOTTOM EDGE;
    masked slide swap for symbol changes
  - strap: FIXED bottom:104px (never JS-calculated); number block back IN THE FLEX ROW
  - smile: canonical 100-box mouths; layered CONTACT SHADOW (no glow)
  - goal ring track alpha .12 (invisible until progress fills)
  - desk-time pill: live / tape / stealth modes
  - V key: 5 test backgrounds; T: clock modes; H: hide help
VERDICT ON V9: accepted as the CURRENT GOOD BASELINE. This is the file to build from.

### WHAT THE GRILLING TAUGHT (the meta-lessons)
1. When the user says "we're going backwards," they are ALWAYS right. Diff mentally
   against the last approved version; restore what was lost BEFORE adding anything new.
2. Don't defend during a grilling. Convert to a numbered fix list and ship the fix.
3. The user grills because they care about quality. Momentum + honesty defuses it.
4. "Not wowing me" = the choreography is correct but the richness is insufficient.
   Answer with MORE life (more states, more motion layers), never with simplification.

---

---

## 7. TASTE PROFILE — THE GRILLING DISTILLED (most important section)

1. MINIMAL = HATED. RICH + CHOREOGRAPHED = LOVED. Verbatim proof: "I'm not a fan of it,
   genuinely I hate it" (minimal) vs. approval of V7 (rich). NEVER offer minimalism as a virtue.
2. "EXPENSIVE" IS THE BAR. Choreography = Bloomberg terminal meets warm classroom.
   Staggered mask reveals, expo easing, everything enters with intent.
   Nothing linear, nothing snappy-cheap, nothing that just "appears."
3. ALIVE BUT CALM. Density is good; noise is not. Every element earns its place,
   but the place should be FULL.
4. METAPHORS CONFUSE. "Volume up" was taken literally. Plain language; flag metaphors.
5. NO JARGON. "Wire" landed as "wtf is wire." Define terms inline, every time.
6. JUDGED BY SCREENSHOTS. Describe what the eyes should report. Give exact keys to press
   and exactly what should be seen.
7. "WE'RE GOING BACKWARDS" = ALWAYS RIGHT. Compare against the last approved version
   before shipping anything.
8. TOURNAMENT METHOD WORKS. 2–3 named variants, one locked spec, user picks a winner.
9. COMMUNICATION STYLE: "Next" = keep shipping. "Great stuff" = pleased. Hard grilling
   = quality dropped; convert to fix list immediately, don't defend, don't take personally.
10. MOMENTUM MATTERS. Ship, then explain. Silence and over-explanation lose the room.

---

## 8. LANDMINES CATALOG (each cost a version — never repeat)

1. ENTRANCE REPLAY BUG — flash animations that re-run the entrance = strobe.
   Entrance plays ONCE (.done class via animationend); flashes are separate animations
   that only run on .done cells.
2. ABSOLUTE-POSITIONED STRAP NUMBER BLOCK — detaches, overlaps ticker.
   Keep it in the flex row (margin-left:26px).
3. JS-CALCULATED STRAP POSITION — strap lies on ticker cells. FIXED bottom:104px. Never compute.
4. WRONG-VIEWBOX MOUTH PATHS — off-center grin. Canonical 100-box coordinates only,
   chord-centered at x=50:
   neutral: M 20 48 A 30 30 0 0 0 80 48
   grin:    M 15 44 A 35 35 0 0 0 85 44
   frown:   M 30 64 A 22 22 0 0 1 70 64
5. GOAL RING TRACK TOO VISIBLE — reads as an outline. Track alpha .12 max.
6. WIRE CELL COUNTER BADGE — collides with the change pill. Deleted entirely. Don't re-add.
7. PROGRESS BAR UNDER PRICE — reads as an underline. Belongs on the cell's BOTTOM EDGE.
8. GLOW SHADOWS — cheap. Layered contact shadows only:
   drop-shadow(0 1px 1px rgba(0,0,0,.35)) drop-shadow(0 3px 6px rgba(0,0,0,.4))
9. JARGON WITHOUT DEFINITIONS — confusion. Define inline.
10. BATCHED HEREDOC CODE DELIVERY — truncation risk. FULL FILES ONLY, pasted in chat.
11. SHARED-CHAT LINKS — AI cannot fetch them (tested). Archives must be pasted, not linked.
12. INLINE ELEMENTS IGNORE TRANSFORM — `<span>` elements default to `display: inline`.
    CSS `transform` DOES NOT APPLY to inline elements per the spec — it silently no-ops.
    This broke `#strap .head` (translateY(115%)) and `#strap .sub` (translateY(140%))
    since V7 — they were always at translateY(0), fully visible, the moment `.on` was added.
    The "staggered mask reveal" was actually just: kicker slides up, then head/sub
    appear INSTANTLY, then rule scales in. Fixed on 2026-08-15 by adding `display: block`
    to both rules. RULE: any `<span>` with `transform:` MUST also have `display: block`
    (or `flex` / `inline-block`) set explicitly. (Note: `<span>`s inside flex containers
    or with `position: absolute` are auto-blockified, so they're safe.)

---

## 9. DESIGN LANGUAGE TOKENS

FONTS:
  Space Grotesk — display / headlines / prices (weight 700)
  IBM Plex Mono — kickers / labels / symbols / clock (weight 500–600)
  Inter         — body / sub-lines (weight 400–600)

PALETTE (dark):
  accent      #FFC107  (rgb 255,193,7)
  bg          #0a0a0b
  fg          #fafafa
  muted       #a1a1aa
  faint       #6b6b74
  border      #232326
  on-accent   #0a0a0a
  up          #0ECB81
  down        #F6465D
PALETTE (light theme):
  bg #f4f4f2, fg #111113, muted #52525b, faint #8a8a93, border #dcdcd6

MOTION:
  --expo: cubic-bezier(.16,1,.3,1)
  Strap staggers: kicker .08s, headline .16s, rule .30s, sub .34s, number .30s, ladder .42s
  Flashes: 1.4s soft background fades, heat-scaled alpha (--heat .05–.18)
  Blink: every 6.5s, scaleY(.08), 150ms
  Wire rotation: 7000ms cycle, 460ms masked swap
  Nothing linear. Ever.

GEOMETRY:
  Ticker: 74px tall, 16px radius, 10px screen margins, #101013, hairline border
  Strap: bottom:104px, padding-left:32px, scrim 760×220 with mask + backdrop-blur
  Headline 31px Space Grotesk; sub 13px Inter; kicker 10px mono .24em letterspacing
  Pill chips for change badges and clock; 8px colored square tick in kickers

---

## 10. V9 FILE ANATOMY (smile-v9.html — the current good baseline)

TICKER (permanent, bottom):
  - Amber cap: canonical smile inside GOAL RING (pathLength=100 arc, GOAL_MAX=1000,
    track alpha .12) + "SMILE · LIVE" wordmark.
  - 5 PINNED CELLS: EUR/USD 1.0842, GBP/USD 1.2691, USD/JPY 151.44, XAU/USD 2384.5,
    BTC/USD 67240 (seed values; random-walk ticks every 1.6s).
    Cell = mono symbol (9.5px, faint), % change pill (green/red, caret triangle),
    20px tabular-nums price.
  - 6TH CELL = THE WIRE (define when using: "the rotating news/instrument slot"):
    12-instrument universe (NAS100, SPX500, US30, NVDA, AAPL, TSLA, ETH/USD, SOL/USD,
    EUR/GBP, USD/KES, NSE 25, US OIL), rotates every 7s, amber symbol, 2px progress bar
    on cell bottom edge, masked slide swap. SESSION-SCORED rotation: instruments in
    currently-open trading sessions rank higher (Sydney/Tokyo/London/NY + Nairobi 10–15h).
    Off-screen instrument spiking >3× its threshold force-jumps in with "· MOVING" tag,
    locks 2 cycles.
  - DESK-TIME PILL (right end): rounded chip, pulsing dot, tabular clock.
    T cycles: LIVE (green dot, seconds) → TAPE (amber dot, date, "REC · DEMO" — for
    pre-recorded segments, never fake-live) → STEALTH (black-on-black: invisible on
    stream, visible on host monitor).

STRAP (lower-third, bottom:104px FIXED):
  - Scrim: gradient + backdrop-blur, masked, fades in.
  - Kicker (mono, colored square tick) → headline (31px) → amber rule (scaleX draw) →
    sub-line (13px) → optional SL/TP ladder (gradient bar, sliding white dot) →
    optional number block (in flex row, counts with cubic easing).
  - STATES: lesson, tp (green, grin+celebrate, ladder 88%, +32.0 pips), sl (red,
    frown+shake, ladder 6%, -18.0), poll, name/host, goal, goalHit.
  - Auto WIRE CARDS (DESK/NOTICE/LESSON notices) rotate every 90s when idle.
  - Note style: smaller muted headline (for compliance lines).

MASCOT: canonical 100-viewBox smile; d:path mouth transitions; blink 6.5s;
  nod/celebrate/shake keyframes; layered contact shadow.

BACKGROUNDS: dark radial-gradient stage + faint amber market-line SVG (masked, .28).
  V cycles 5 test scenes: 0 dark, 1 bright chart, 2 talking-head warmth, 3 city-night,
  4 light (auto-toggles light theme). L = light toggle. B = market bg toggle.

ENGINES:
  Power engine — intervals pause when tab hidden; prefers-reduced-motion respected;
  ?perf=low kills backdrop-blur.
  Significance-gated flashes — soft 1.4s fades, heat-scaled, max 1 per 3s per cell,
  entrance once (.done class).
  Goal ring auto-increments; goalHit state at max.

KEYS: 1 hide · 2 lesson · 3 TP · 4 SL · 5 poll · 6 host · 7 goal · 8 wire card ·
  9 force wire swap · V scenes · T clock mode · L light · B market bg · H hide help

---

---

## 11. ROADMAP (creative room — build on V9, keep V7/V9 choreography sacred)

- MORE STRAP/CARD TYPES: economic calendar events, chat question-of-the-day,
  lesson progress tracker (part 2 of 4 with a progress tick), multi-guest name straps.
- RUNDOWN SYSTEM: segment state machine (pre-show → open → lesson block → live desk →
  Q&A → close) with auto-choreographed transitions between segments.
- CHAT INTEGRATION: poll tallies, question queue, moderation-safe display,
  delay-buffer awareness (chat shown on stream is delayed to match OBS buffer).
- BRB / BREAK SCENES in the same design language (warm, alive, not a static card).
- OBS POLISH: hotkey mapping, URL-param scene presets (?scene=lesson),
  presenter mode (?present) for chromeless Document-PiP capture.
- 24/7 LOOP MODE: unattended rotation of wire cards, goal updates, lesson promos
  when no host is live — with the clock in tape mode, never fake-live.
- Anything that makes it MORE alive without getting noisy.

---

## 12. CONTINUITY TEST + WORKING AGREEMENT

CONTINUITY TEST (ask the new chat these; if it fails, the offload didn't land):
  Q1: "What are the three clock modes and why does tape mode exist?"
      A: live / tape / stealth. Tape exists because some content is pre-recorded —
         honesty rule: never fake-live; tape shows date + "REC · DEMO" in amber.
  Q2: "What is the wire, and what two things were wrong with it in V8?"
      A: The rotating 6th ticker cell (newsroom slang for the feed). V8 wrongs:
         counter badge collided with the change pill; progress bar read as an
         underline under the price instead of sitting on the cell's bottom edge.
  Q3: "What happens when I say 'we're going backwards'?"
      A: I'm always right. Diff against the last approved version, restore what was
         lost FIRST, then add new things.
  Q4: "Why is the strap at bottom:104px and who decided that?"
      A: JS-calculated positioning made the strap lie on top of ticker cells in V8.
         Fixed 104px (30px above the 74px ticker + 10px margin) is the rule.

WORKING AGREEMENT:
  1. Ship full files, then explain. Verify with exact keys + expected visuals.
  2. Grilling → numbered fix list → ship the fix. No defending.
  3. Variants when exploring: named, locked spec, user picks winner.
  4. Push richness. Challenge assumptions with better ideas, explained plainly.
  5. V7's strap choreography and V9's fixes are SACRED. Extend, never regress.
  6. Define jargon inline. Flag metaphors. Screenshots are the judge.

---

## 13. MACHINE-READABLE JSON (the entire archive, structured)

{
  "project": {
    "name": "SMILE TV",
    "type": "finance/trading education livestream overlay",
    "location": "Nairobi, Kenya",
    "audience": "Kenyan / East African",
    "host_placeholder": "Mwangi",
    "site_placeholder": "smile.co.ke",
    "content_model": "demo account trading education; never financial advice; some pre-recorded (tape mode), some live",
    "north_star": "TraderTV Live, but classroom-paced, warm and alive",
    "brand_phrases": ["4G smiles", "losses are tuition — we show ours so you pay less of yours", "one question in, one skill out", "the mango test", "Chart School", "live lessons Mondays 9PM EAT"],
    "deliverable": "one self-contained HTML file as OBS browser source; no frameworks; Google Fonts only external asset; must run 24/7"
  },
  "delivery_rules": {
    "code_format": "COMPLETE FULL FILES pasted in chat; no diffs, no batches, no terminal commands",
    "jargon": "define inline always",
    "metaphors": "flag as metaphors",
    "verification": "state exact keys to press and exactly what should be seen",
    "links": "shared-chat links cannot be fetched by AI; archives must be pasted"
  },
  "taste_profile": {
    "loves": ["richness", "choreography", "staggered mask reveals", "expo easing", "density with intent", "warm + alive", "expensive feel"],
    "hates": ["minimalism", "linear easing", "things that just appear", "glow shadows", "noise without purpose", "regressions"],
    "verbatim_verdicts": {
      "minimal_v1_v2": "I'm not a fan of it, genuinely I hate it",
      "v4": "Better but of course V4 wins here, but still not wowing me honestly",
      "v8_rebuild": "Broski, we're going backwards"
    },
    "communication": {"next": "keep shipping", "great stuff": "pleased", "grilling": "quality dropped; convert to numbered fix list and ship"}
  },
  "history": {
    "era1_v8_build": "turns 1-9: full suite sketched; output-limit crisis birthed batch delivery; smilev8.html completed in 10 batches; nine philosophy Q&As (event-bus, rundown, live-desk vs loop, presenter mode, delay buffers, chat moderation, demo ethics)",
    "era2_philosophy": "turns 10-14: OBS delay-buffer kill/rejoin confirmed; Document PiP discovered; ticker=permanent vs strap=overlay distinction; TraderTV six-component mapping; tournament method born (Terminal/Studio/Signal, locked spec); Test-7 pivot — evolve what works, stop rewriting",
    "era3_grilling": "turns 15-20+finale: 'I hate it' (minimal) → taste line drawn; exact smile SVG provided; V4 'not wowing' → more life not less; V5 living ticker; V6 static ticker + goal ring + wire cards; V7 Studio strap APPROVED (sacred); V8 precision rebuild failed all four changes; V9 = V7 motion + surgical fixes = CURRENT BASELINE"
  },
  "landmines": [
    "entrance animation replaying on flashes = strobe; entrance once via .done class",
    "absolute-positioned strap number block detaches and overlaps ticker; keep in flex row",
    "JS-calculated strap position lays on ticker; fixed bottom:104px",
    "wrong-viewBox mouth paths = off-center grin; canonical 100-box, chord-centered x=50",
    "goal ring track alpha > .12 reads as outline",
    "wire counter badge collides with change pill; deleted",
    "progress bar under price reads as underline; belongs on cell bottom edge",
    "glow shadows cheap; layered contact shadows only",
    "jargon undefined = confusion",
    "batched heredoc code = truncation deaths",
    "shared links unfetchable by AI"
  ],
  "tokens": {
    "fonts": {"display": "Space Grotesk 700", "mono": "IBM Plex Mono 500-600", "body": "Inter 400-600"},
    "colors": {"accent": "#FFC107", "bg": "#0a0a0b", "fg": "#fafafa", "muted": "#a1a1aa", "faint": "#6b6b74", "border": "#232326", "on_accent": "#0a0a0a", "up": "#0ECB81", "down": "#F6465D", "light_bg": "#f4f4f2", "light_fg": "#111113"},
    "motion": {"expo": "cubic-bezier(.16,1,.3,1)", "strap_staggers_s": [0.08, 0.16, 0.30, 0.34], "flash_s": 1.4, "blink_every_s": 6.5, "wire_cycle_ms": 7000, "wire_swap_ms": 460},
    "geometry": {"ticker_h": 74, "ticker_radius": 16, "screen_margin": 10, "strap_bottom": 104, "headline_px": 31, "sub_px": 13, "kicker_px": 10}
  },
  "v9_anatomy": {
    "ticker": {"cap": "smile in goal ring (GOAL_MAX 1000, track alpha .12) + SMILE · LIVE", "pinned": ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD", "BTC/USD"], "wire": "6th cell, 12-instrument universe, session-scored rotation, spike force-jump with MOVING tag, 2-cycle lock", "clock": "live/tape/stealth pill"},
    "strap": {"states": ["lesson", "tp", "sl", "poll", "name", "goal", "goalHit"], "auto_wire_cards_every_s": 90, "structure": "scrim, kicker, headline, rule, sub, optional ladder, optional counting number"},
    "mascot": {"mouths": {"neutral": "M 20 48 A 30 30 0 0 0 80 48", "grin": "M 15 44 A 35 35 0 0 0 85 44", "frown": "M 30 64 A 22 22 0 0 1 70 64"}, "shadow": "drop-shadow(0 1px 1px rgba(0,0,0,.35)) drop-shadow(0 3px 6px rgba(0,0,0,.4))"},
    "scenes": ["0 dark", "1 bright chart", "2 talking-head warmth", "3 city-night", "4 light"],
    "keys": {"1": "hide", "2": "lesson", "3": "TP", "4": "SL", "5": "poll", "6": "host", "7": "goal", "8": "wire card", "9": "force wire swap", "v": "scenes", "t": "clock mode", "l": "light", "b": "market bg", "h": "hide help"}
  },
  "roadmap": ["more strap/card types", "rundown segment state machine", "chat integration with delay awareness", "BRB scenes", "OBS hotkeys + URL presets + ?present mode", "24/7 loop mode with honest tape clock"],
  "sacred": ["V7 strap choreography", "V9 surgical fixes", "canonical smile SVG", "static ticker", "goal ring on smile", "tape-mode honesty"]
}

---

## END OF ARCHIVE
> Paste order for new chat: (1) this whole archive, (2) full smile-v9.html code,
> (3) ask the continuity test questions from Section 12.
> Then continue building. Momentum matters. Ship, then explain.