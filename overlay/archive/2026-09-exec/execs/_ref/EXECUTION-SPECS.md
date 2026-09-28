# SMILE EXECUTION CATALOG — THE IRON RULES

You are building ONE scene's executions for smile.co.ke (Kenyan trading desk, OBS overlay, 1920×1080).

## THE ONE RULE — SAME GUN, DIFFERENT EXECUTION (1911/2011)

The design is **frozen**. It is the original in `_ref/<scene>-original.html` (+ shared `../smile-core.css`).
You maintain **everything**: same layout skeleton, same positions, same copy, same chips/stats/type
scale, same ticker, same URL contracts, same functionality. You change ONLY the **execution**:
how the motion is engineered, choreographed, and finished. A viewer must recognise the SAME design
in every file — but feel a different hand each time.

FORBIDDEN: moving elements to new positions, resizing type, rewording copy, changing the grid,
adding new sections, removing sections, changing colors of the design system.
ALLOWED: easings, timing, choreography order, motion engines, per-word/per-char treatment of the
SAME text, material/finish effects (sheen/glow/glass) on EXISTING elements, micro-details.

## SHARED ASSETS (relative to each exec file)

- `../smile-core.css` — the original design system (tokens, .bg, .chip, .spark, .ticker, .rise, skyline). Link it exactly like the original links smile.css. You may add per-exec overrides AFTER it in the inline <style>, but the base must win by default.
- `../smile-mark.js` — face upgrade engine (blink/wink/look/nod/bounce). Load it exactly like the original does.
- `../smile-mark.svg` — OFFICIAL smile mark (verbatim crop of Smile-Logo.svg). Wherever the original inlines the hand-drawn disc SVG (circle+eyes+mouth in a .disc), you MAY keep the original inline disc (identical geometry) — layout unchanged.
- `../smile-logo.svg` — full official wordmark+face logo.
- `_ref/<scene>-original.html` — THE design you are executing. Read it first, line by line.

## THE 5 EXECUTION LANES (one file each)

### E1 — "REFINERY" (the original, executed to its absolute ceiling)
Zero structural change, zero engine change. Pure refinement: replace the default easings with the
expo-out family `cubic-bezier(.19,1,.22,1)`, retime the entrance as one orchestrated timeline
(every .rise lands in a deliberate rhythm — no dead air, no crowding), add micro-polish: 1px
hairline glows, perfect stagger on cbars/sparks/cndl sway, sheen timing tuned, tabular-nums locked,
`will-change` only on animating transforms, loop keyframes with symmetric ease-in-out so loops never
"tick". This is the definitive version of the original.

### E2 — "MASS & SPRING" (physical execution)
Same design; every entrance and idle motion is re-driven by a tiny hand-rolled spring engine
(requestAnimationFrame, ~40 lines): stiffness/damping per element (entrance: critically-damped
settle; face/orbit: slightly underdamped with 1-2 visible oscillations; ticker stays CSS linear).
Elements must feel like they have mass — overshoot once, settle, never bounce forever. No spring
libraries. Respect `document.hidden` (pause rAF) so OBS doesn't burn CPU.

### E3 — "MATERIAL STUDY" (finish swap)
Same design; the moving parts get different materials: the load fill becomes liquid (glass sheen +
inner light that travels), rings/borders get specular highlights that rotate, the face gets a bloom
halo + soft top-light, chips get glassy inner strokes, the ticker text gets a slow luminous sweep.
All achieved with gradients/box-shadow/mask/opacity on EXISTING elements — geometry untouched.
Motion curves stay close to the original; the DIFFERENCE is in the surfaces, not the choreography.

### E4 — "TYPE IN MOTION" (kinetic typography)
Same design; text becomes the performer: h1 reveals per-word (or per-char) through clip-path/translate
mask wipes; the kicker chip types itself; stats count up with odometer-style rolls (start value → final,
expo-out); the countdown number rolls like a split-flap/odometer instead of popping; sub text gets a
reading-rhythm reveal. Everything else (positions, sizes) identical.

### E5 — "AMBIENT CINEMA" (the premium idle)
Same design; the scene is always alive but almost imperceptibly: multi-layer parallax drift (bg grid
vs skyline vs sparks at different depths/loops), a 40s light sweep crossing the stage, the face
breathes with a slow 8s scale/glow tide, cbars sway in a wave phase across the column, candle skyline
shimmers, ticker gets a subtle depth shadow. Entrances are slower (1.2–1.6s expo) and longer-staggered.
Everything loops seamlessly — screenshot any two frames 10s apart and both look composed.

## SMOOTHNESS LAW (all lanes — non-negotiable)

1. Animate ONLY `transform` and `opacity` (+ clip-path/mask where the lane demands). Never animate
   top/left/width/height/margin. The load-bar fill may animate width via transform:scaleX only.
2. Every keyframe loop uses ease-in-out symmetric curves — no linear except the ticker march.
3. Staggers: 60–120ms steps for columns, 500ms+ between logical groups. Never random-looking.
4. `will-change: transform` only on elements with continuous animation; remove nowhere needed.
5. Zero jank: no layout reads in rAF loops, batch style writes, use `transform: translateZ(0)` sparingly.
6. Fonts: keep the exact Google Fonts links from the original (Manrope display / Inter body).
7. Page must work over file:// (OBS) — relative asset paths only, no fetch(), no modules.
8. 1920×1080 design surface; `body{background:transparent}` + `.bg` painting EXACTLY like original
   (originals paint the dark radial backdrop; keep it — OBS users see the same frame).
9. Keep every original ID/class hook and behavior (countdown ?from= param, beeps, flash+endlogo,
   starting-soon load %, clock). "Maintain everything" includes FUNCTION.

## TECH & QA SCENES (no original exists — derive, don't invent)

Both must look like they were born in the same core kit: reuse the core skeleton elements verbatim
(.bg, chips, h1 with .y accent + ".":, .sub, .socials chips, .ticker, sparks, orbit face from start,
buffer ring from brb, .rise entrances). Copy tone: Kenyan trading desk, warm + confident.

- TECH base (closest sibling: brb): centered stage. Buffer ring (like brb's) but with a reconnect
  progress fill; h1 "we're on <span class=y>it</span>."; sub about the feed hiccup + desk fixing it;
  status chips (● FEED RECONNECTING / SYSTEMS NOMINAL); bounce dots; ticker: "✦ TECHNICAL HICCUP /
  markets paused / our desk is on it / @smileke / smile.co.ke / #SmileSquad".
- QA base (closest sibling: start): topbar (brand + clock chip NAIROBI DESK), left column: kicker
  chip "● LIVE Q&A · ASK US ANYTHING", h1 "ask us<br><span class=y>anything</span>.", sub inviting
  questions in chat, stats (Q&A format: "12 QUESTIONS IN QUEUE" / "LIVE · 1,416 WATCHING"), a
  "drop yours in chat" ghost chip row; right column: orbit face + a rotating mic-like bar column
  (reuse cbars geometry); ticker: "✦ Q&A SESSION / drop questions in chat / @smileke / smile.co.ke".

## SELF-REVIEW LOOP (mandatory, run it twice minimum)

Round 1: build all 5 files.
Round 2: for EACH file:
  - `agent-browser set viewport 1920 1080`
  - `agent-browser open file:///home/z/my-project/world-21-suite/overlay/execs/<file>.html`
  - `agent-browser screenshot /home/z/my-project/world-21-suite/audit/exs/<file>-t0.png` (immediately, catches entrance state)
  - `sleep 2 && agent-browser screenshot ...-t2.png` and `sleep 6 && ...-t8.png` (idle state)
  - READ the screenshots (you have native vision). Hunt: overlaps, clipped text, dead first frame,
    elements stuck mid-animation, kerning crimes, contrast fails, ticker seam pops.
  - FIX and re-shoot until you'd stake your reputation on it. Doubt yourself, then verify.
Also verify the first frame is never an empty flash (entrances must start from composed opacity 0 →
no FOUC) and the ticker seam is invisible.

## WORKLOG (mandatory)

Before working: `tail -c 8000 /home/z/my-project/worklog.md` for context.
When done: append with `cat >> /home/z/my-project/worklog.md <<'EOF'` a section starting with a line
containing exactly `---`, then `Task ID: <yours>`, `Agent: <name>`, `Task:`, `Work Log:`, `Stage Summary:`.

## DELIVERABLES

Exactly 5 files: `<scene>-e1.html` … `<scene>-e5.html` in `/home/z/my-project/world-21-suite/overlay/execs/`.
Each: `<!doctype html>`, title `SMILE · <scene> · <lane name>`, self-contained inline <style> AFTER the
smile-core.css link, `<script src="../smile-mark.js"></script>` like the original.
