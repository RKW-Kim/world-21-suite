# SMILE KIT3 — DNA BRIEF (builders' contract)
Source: 475 Dribbble shots downloaded & natively reviewed by the director (main agent).
Catalogs: `research/dribbble/D1-catalog.md` (top-liked), `research/dribbble/D2-catalog.md` (new+niche).
Every file = ONE self-contained 1920×1080 broadcast scene. Inline ALL CSS+JS. Google Fonts <link> allowed. No other external asset.

## 0 · BRAND PACK (verbatim, never redraw)
Palette: `--yellow:#FFCE00 --yellow-hot:#E8A800 --ink:#0A0900 --up:#0ECB81 --down:#F6465D --sky:#3FB6FF`
Grey ramp (dark lanes): page `#0A0900` → panel `#141210` → card `#1C1914` → hairline `#2A251C`; text `#F5F1E6` primary, `#9C9484` muted.
Grey ramp (light lanes): paper `#FFF9E8` → panel `#FFF3C4` → card `#FFFFFF` → hairline `#E4D9B8`; text `#0A0900`.
Face mark (SVG, verbatim — the ONLY allowed smile face rendering):
```html
<svg viewBox="0 0 100 100" aria-label="Smile mark"><circle cx="50" cy="50" r="48" fill="#FFC107"/><circle cx="31" cy="35" r="5.5" fill="#0a0a0a"/><circle cx="69" cy="35" r="5.5" fill="#0a0a0a"/><path d="M 20 48 A 30 30 0 0 0 80 48" fill="none" stroke="#0a0a0a" stroke-width="7.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
```
Wordmark: inline the `<path>` set from `upload/Smile-Logo.svg` when a wordmark row is needed (grey `#E6E6E6` fills may be recolored to ink on light lanes or paper on dark lanes — shapes never edited).
Content vocabulary (use, don't invent): `EPISODE No. <ep>`, `EAT · NAIROBI DESK`, `@smileke`, `smile.co.ke`, `#SmileSquad`, agenda `MAILBAG → HOT TAKES → CHART DIVE`, `Mics hot · coffee brewing · charts loading.`, `PODCAST + SCREEN SHARE`, `SIGNAL 98% NOMINAL`, `ON AIR IN <mm:ss>`, `● WE'RE LIVE`, ticker items `EPISODE ◆ @smileke ◆ smile.co.ke ◆ #SmileSquad` looping.

## 1 · URL CONTRACT (every scene)
`?t=<seconds|ISO datetime>` countdown target (default 10:00; at 00:00 hold and fire the LIVE beat) · `?ep=128` episode · `?title=` `?sub=` text overrides on `[data-title]`/`[data-sub]` · `?obs=1` transparent body background (OBS mode) · `?wm=0` hide corner watermark (default on: 42px face mark, 18% opacity) · Keys: `V` cycles internal variants if any, `H` hides help.
Countdown never negative; with no `?t`, hold `--:--` "STAND BY" for 3s, then animate into default 10:00 count. Implement rolling digits (slide-up roll 420ms cubic-bezier(.2,.9,.25,1), staggered per cell) for at least the seconds field in every scene — kit signature.

## 2 · CRAFT FLOOR (measured from Dribbble's top — violations = reject)
1. **Accent area law**: yellow ≤ ~10% of frame pixels. Yellow is the only hot hue; up/down/sky only as ≤2% data micro-dots. No purple. No rainbow. No gradient washes except ≤6% luminance ramps on glass.
2. **Stacked darks**: dark lanes separate layers by LUMINANCE STEPS (page 8% → panel 14% → card 20%), hairlines 1px `#2A251C` rhythm, never heavy borders. Light lanes: 3 paper steps + ink hairlines.
3. **One hero numeral**: one giant tabular number 3–6× its label size. `font-variant-numeric: tabular-nums` always.
4. **Stage grammar**: wide stage (≥1.3:1 zones): foreground HUD chips (corner-anchored), mid-ground hero (face/dial/headline), background scrim/texture. No centered-box-on-flat-bg layouts.
5. **Glow discipline**: exactly ONE soft glow (12–24px blur, ≤40% alpha) under the one LIVE element. Everything else matte. Brut lanes may use hard-offset solid shadows (4–8px, zero blur) instead.
6. **Spacing**: 8-pt grid. One corner-radius language per scene. Gutters 24/32/48.
7. **Type**: max 2 families + 1 mono. Meta = tracked caps 0.12–0.2em at 11–13px. Headlines −0.02em, weight ≥700. No font below 10px. Fonts (Google): Archivo (+Expanded/Condensed), Manrope, Inter, Space Grotesk, Chakra Petch, IBM Plex Mono, Fraunces, Bricolage Grotesque, Unbounded.
8. **Copy**: real content from the vocabulary only. No lorem, no emoji, no placeholder boxes.
9. **OBS truth**: 1920×1080 fixed stage; scale-to-fit via `transform: scale()` wrapper; `?obs=1` → transparent page bg.

## 3 · MOTION SPEC (production-grade; "sazabi snap in smile language")
- Transform/opacity ONLY. Zero animation of layout props. Every animation declares easing; linear forbidden except ticker marquee.
- **Entry choreography** (0–1.6s): stagger 60–90ms; HUD chips translateY(14px)+fade cubic-bezier(.2,.9,.25,1); panels hard-snap cubic-bezier(.85,0,.15,1) + 2px settle; hero numeral roll-up; face scale .92→1 spring cubic-bezier(.34,1.56,.64,1).
- **Idle loops**: max ONE hero loop (breathing face 3.4s / ticking dial / pulse dot) + micro loops ≤2. Periods 2.4–6s, amplitude 1–3% / 2–4px, asymmetric keyframes (40%/60% splits).
- **Numbers roll**, never fade-swap.
- **LIVE beat at 00:00**: yellow sweep line crosses stage (600ms), "WE'RE LIVE" chip slams (scale 1.15→1 spring), face winks once. No confetti. No flashing >2Hz.
- `prefers-reduced-motion`: final composed state. Zero console errors.

## 4 · QA LOOP (builders cannot see images — measure instead; VLM forbidden)
≥3 iterations; log what changed per round in the worklog:
1. Serve: `cd /home/z/my-project/world-21-suite/overlay/lab/kit3/scenes && python3 -m http.server 8031 &` (reuse if running).
2. `agent-browser set viewport 1920 1080` → `open http://localhost:8031/<file>.html` → `wait --load networkidle`.
3. Geometry via `agent-browser eval`: no element outside stage; every text `scrollWidth<=clientWidth+1`; hero numeral ≥3× label size.
4. `agent-browser screenshot /home/z/my-project/research/kit3/shots/<file>.png` then PIL checks: yellow fraction ≤12%; band luminance matches lane; hue sanity; two shots 1.5s apart differ in ticker band but match in static HUD region.
5. `agent-browser console` / `errors` empty.
6. Reload + screenshot at t≈0.2s to confirm entry animation in flight.

## 5 · BUILD SLOTS — WAVE 1 (one file each, named `{scene}-{code}.html`)
| slot | DNA source (Dribbble) | direction |
|---|---|---|
| start-clay | q9_10 Clay yellow dashboard (D1 #3) | YELLOW FIELD: giant yellow field, one huge organic ink blob cutting the frame; ink bento cards float on yellow carrying countdown, agenda, signal stats; face embossed in the blob; numerals ink-on-yellow |
| start-print | q7_08 d~studio (D2 #24) | PRINT EDITION: cream→yellow paper field, ink serif display headline ("The Evening Desk ~ Episode <ep> > Live"), underline meta rows (EAT time / EP / SIGNAL), giant serif "smile.*" wordmark pinned bottom, ✳ starburst ornaments, hairline rules |
| brb-otto | s17 Otto mascot (D2 #1) | MASCOT DEVICE: face as dot-matrix LED panel device idling in ink void; personality idle loop (blink, tilt, glance ticks); steel-grey tick marks; one caption chip "away from the desk — back in <mm:ss>"; nothing else owns the frame |
| brb-breathe | s14 breathing + s13 amber | AMBER BREATH: ink field; face bobbing on 4s breath cycle with one warm halo expanding/contracting; amber slab chip "BACK IN <mm:ss>"; sand-grey meta row; dial ring shows return progress |
| tech-abyss | q10_01 THE ABYSS watch (D1 #1) | SIGNAL DIAL: ink void; giant instrument dial (thin yellow→grey arc gauge) with huge tabular T-minus inside; micro-caps "SIGNAL RECOVERY IN PROGRESS" hugging the ring; bento status cells (FEED/AUDIO/BITRATE frozen) with one yellow pulse dot on the recovering cell |
| tech-serv | s58 serv Swiss bento (D2 #14) | FREEZE WALL: Swiss bento on stacked ink; one giant "96%"-style stat slab (yellow) = SIGNAL; floating label chips pinned on frozen panels (FEED PAUSED / AUDIO OK / RECONNECT 67%); dot-matrix data art tile; hairline Swiss grid |
| qa-wanna | q7_06 Wannathis greyscale (D1 #2) | MONO QUEUE: near-greyscale question card wall, hairline separators, grey-ramp hierarchy; yellow ONLY on live question chip + face's mouth; up-next rows with rank numerals; "ASK US ANYTHING" tracked caps |
| qa-brut | q4_10 Gumroad + q7_17 BOLT | BRUT ASK: giant ink "smile" wordmark row on paper; hard split fields (yellow/white); sticker-face blobs with thick ink outlines; question chips as brutalist cards; black CTA slab "DROP YOUR QUESTION"; hard-offset shadows only |
| end-reel | s52 Matt Becker (D2 #23) | FILMSTRIP REEL: ink field; credits as filmstrip of episode frame tiles scrubbing slowly sideways; huge two-tone display type ("THAT'S / THE SHOW"); numbered next-episode slab (one filled yellow); sienna→yellow accents |
| end-bento | s13 EduFix brand wall (D2 #7) | BENTO SIGN-OFF: bento brand collage — amber slab with face, watch-face dial tile (next EAT air time), duotone photo tile, ink merch tile, caps statement "SEE YOU THURSDAY."; tiles hand off in sequence |

## 6 · WAVE PROTOCOL
- Wave 1 builders ship v1 of each slot. Director natively reviews screenshots, writes eye-notes.
- Wave 2 improvement agents receive the file + director's eye-notes and MUST push further without regressing.
- Hub + director pages assembled by the director agent afterwards.
