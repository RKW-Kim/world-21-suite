# THE SPEC — one brief, many guns

**The M4 rule.** A spec goes out. Many vendors answer it. One builds a futuristic monster with a
grenade launcher, one builds a lean carbine, one builds something nobody expected — and every one
of them is still recognizably an answer to the *same* spec. That is this directory.

The previous wave (`../execs/`) was **one frozen design, five motion hands** — same layout, same
shirt, different stitching. This wave is the opposite: **same spec, radically different layouts.**
Each scene ships 3 structural answers (a/b/c). Nothing here may look like a recolor of anything.

---

## 1 · WHAT STAYS (the constraints — non-negotiable)

Every candidate, no exceptions, keeps:

- **The brand palette.** yellow `#FFC107` / hot `#F5A623` / ink `#0a0a0a` / zinc-dark bg `#09090b`
  / border `#27272a` (+`#3f3f46`) / fg `#fafafa` / muted `#a1a1aa` / faint `#71717a` /
  up `#0ECB81` / down `#F6465D`. This is the shadcn-zinc × smile-yellow system from the Qwen build.
- **The type system.** Space Grotesk (display) · IBM Plex Mono (labels, ticker, terminal, digits) ·
  Inter (body). Google Fonts link:
  `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap`
- **The official mark.** `smile-mark.svg` in this dir is a VERBATIM crop of the brand logo — zero
  redraw. Use it for logo spots. Animated smiles: wrap `<span class="dw">` inside a `.brand`
  element or use `svg.disc` / `.face` and include `smile-mark.js` (sibling) — it upgrades them with
  blink/look/wink/nod/spin/bounce moods and exposes `window.smileMood(mood, ms, target)`.
  - If a candidate needs a **hero smile with custom physics tricks** (eye roles, bowl physics), inline
    a 100×100 disc with EXACTLY the smile-mark.js geometry — never the Qwen approximation:
    ```html
    <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#FFC107"/>
      <ellipse class="eye-l" cx="41" cy="40" rx="6.5" ry="7.6" fill="#0b0b0b"/>
      <ellipse class="eye-r" cx="59" cy="40" rx="6.5" ry="7.6" fill="#0b0b0b"/>
      <path class="mouth" d="M32 55 C 35 77, 65 77, 68 55" fill="none" stroke="#0b0b0b"
            stroke-width="10.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    ```
- **The copy blocks** of its scene (see §5) — wording may be re-set typographically, not rewritten.
- **The market pulse.** Every scene answers the spec with *some* form of live market/ticker
  presence (full bottom ticker, status-bar strip, sidebar feed, price chips…) — executed per layout.
  Binance pattern with graceful fallback (steal verbatim from `_ref/qwen-starting-soon.html`):
  BTC / ETH / PAXG(XAU) + USD/KES walk; 5s interval; flash-on-change; catch → random walk.
- **The URL contract** per scene (§5): strict parse, `99:59:59` cap, zero-state holds a composed
  `00:00` frame (never blank), `?t=90` seconds or `?t=YYYY-MM-DDTHH:MM:SS+03:00` ISO.
- **EAT (Nairobi, UTC+3) clock** wherever a clock fits the layout.

## 2 · WHAT MUST CHANGE (the whole point)

Between candidates of the same scene, at least these must genuinely differ:

1. **Grid & composition** — asymmetric bento vs centered stack vs split rail vs full-bleed stage vs
   material object (ticket/receipt/board). Not the same skeleton with items moved 40px.
2. **Signature structural move** — each candidate owns exactly one big idea (see §5 briefs):
   bento mosaic · terminal chrome · side rail · DVD physics · perforated ticket · rundown table ·
   scoreboard counters · filmstrip · status list · reconnect log · repair bench · TX card cycle ·
   town-hall environment · caller board · bell strike · receipt print · credits crawl.
3. **Type scale & voice** — a 96px keynote hero and a 26px mono terminal do not share a scale.
4. **Where the smile lives and what it does** — hero mascot with the trick engine, titlebar
   tenant, bouncing screensaver, ticket stamp, podium host, engraved bell, receipt seal…
5. **Motion personality** — keynote cascade vs terminal type-out vs physical bounce vs print
   reveal vs broadcast board ticks. Never the same cascade retimed.

## 3 · ANTI-BOILERPLATE LAW

shadcn primitives are the raw material, not the look. The catalog of sites built from the same
components looks nothing alike — that is the bar.

- Forbidden: the default "centered max-w-md card + heading + subtext + button" zinc page. Twice.
- Forbidden: identical section rhythm across candidates (hero → row → footer, thrice).
- A primitive is only on screen if it is **doing its job live** (skeleton rows shimmer while
  "loading", progress bars fill, loaders spin then resolve, badges flip state, meters move).
- Texture is earned, not sprinkled: one ambient system per candidate (dot grid OR beam sweep OR
  candle market OR film grain OR marquee columns), tuned to the layout.

## 4 · IRON RULES (OBS reality)

- Canvas is 1920×1080, must scale to any window (`body` flex/center, scale via clamp/vh units —
  the Qwen file's approach is the reference).
- `file://` safe: no local fetches; only Google Fonts + `api.binance.com` (both with fallbacks).
- Smoothness law: everything eases **home** — no snap-ends, ever. Compose frame one (negative
  delays / pre-populated fields). Only `transform`/`opacity`/`stroke-dashoffset` animate; no
  layout reads in rAF; `will-change` released after settle.
- `document.hidden` pauses rAF loops (OBS-friendly CPU), `prefers-reduced-motion` → composed
  static frame. `tabular-nums` on every digit. No `<marquee>`, no GIF, no video, no canvas-heavy
  (≤1 canvas if truly needed — prefer SVG/DOM). Max ~6 `backdrop-filter` elements per page (CEF).
- Self-contained files: inline `<style>`, sibling `<script src="smile-mark.js">`, `smile-mark.svg`
  as favicon. Zero build step. Zero console errors.

## 5 · SCENE ROSTER (frozen copy + contract + the three answers)

### STARTING SOON — `soon-a.html` `soon-b.html` `soon-c.html`
Copy essence: eyebrow `● PRE-MARKET · STREAM LOADING` · h1 `markets open soon.` ·
sub `Charts loading, coffee brewing. Grab your seat before the bell — spot, futures, MT5 & good
vibes under one Smile desk.` · stats `1,416 TRADERS TRUST US` `198 ACTIVE MARKETS` ·
loading tiles CHARTS/CANDLES/COFFEE/VIBES → `✓ ready` · chips `@smileke` `smile.co.ke` `#SmileSquad`.
Contract: `?t=90|ISO` drives the countdown (big or small per layout), `?ep=` episode tag.
- **a · BENTO DESK** — asymmetric 12-col bento of live zinc cards around one hero card (smile +
  gradient h1 + rotating tagline). Cards: countdown (odometer digits, ?t=), market preview (live
  candle SVG), skeleton-loading card (shimmer rows → ✓), socials card, EAT clock. Bottom ticker.
- **b · TERMINAL BOOT** — full-bleed macOS-chrome terminal (titlebar smile disc, traffic lights),
  mono boot log typing itself (`$ smile --open --ep=128 …`), giant odometer countdown as output,
  blinking cursor, progress 0→100, tiles resolve to ✓ lines, status-bar ticker. ENTER = step.
- **c · SIDE RAIL STAGE** — 320px shadcn sidebar rail (lockup, status list FEED/CHARTS/COFFEE/
  VIBES with live ✓ cascade, session meta, EAT clock) + full spotlight hero right (eyebrow chip,
  huge gradient h1, trick-engine smile above it) + bottom marquee.

### BRB — `brb-a.html` `brb-b.html` `brb-c.html`
Copy essence: h1 `be right back.` · sub `Trader stepped away — charts secured, smile intact.` ·
chips `✦ BE RIGHT BACK` `positions secured` `don't close the tab` · ticker continues.
Contract: `?elapsed=90` (seconds away → paused mm:ss), optional `?t=` ETA.
- **a · STANDBY SAVER** — screensaver physics: the smile disc bounces DVD-logo style across the
  dark stage (real velocity, corner snaps glow), every Nth wall-hit fires a trick (spin/wink);
  corner-locked `be right back.` lockup + paused timer; ticker bottom.
- **b · AWAY CONSOLE** — centered shadcn dialog card `positions paused`, progress ring of away
  time, checklist staggering to ✓ (positions secured / charts locked / mic muted), what's-next
  queue, status ticker strip.
- **c · TICKET BOOTH** — the scene as a physical ticket: perforated notches, dashed tear line,
  big `BE RIGHT BACK` stamp thunking in (scale 3→1 + ink bleed), animated barcode, smile as the
  face stamp, ETA chip, stub with session meta. Tilted ~2°, desk-shadow.

### INTERMISSION — `inter-a.html` `inter-b.html` `inter-c.html`
Copy essence: h1 `intermission.` · sub `Stretch. Hydrate. Back at HH:MM EAT.` · rundown +
`#SmileSquad` chips. Contract: `?t=90|ISO` = back-at countdown (mandatory big presence), `?ep=`.
- **a · PROGRAMME RUNDOWN** — editorial split: giant stacked vertical `INTERMISSION` type left
  (outline + yellow fill mixed), right a rundown table (segments with states: done ✓ / ON DECK /
  queued, animated state markers, live progress hairline). Countdown chip pinned. Ticker.
- **b · HALFTIME BOARD** — scoreboard panel: stat counters count up (uptime, EP, trades called,
  peak vibes 100%), smile perched/bobbing on the board's top edge (Qwen-calendar DNA), rotating
  "while you were away" note cards, back-at countdown in the board header. Ticker.
- **c · FILMSTRIP GALLERY** — horizontal auto-drifting filmstrip of upcoming-segment cards
  (sprocket holes, gradient/typographic covers), center `back at HH:MM` + countdown, smile hops
  along the strip's top edge card-to-card. Ticker.

### TECHNICAL DIFFICULTIES — `tech-a.html` `tech-b.html` `tech-c.html`
Copy essence: h1 `we're on it.` · chips `● FEED RECONNECTING` / `SYSTEMS NOMINAL` ·
`markets paused — our desk is on it.` Contract: `?elapsed=` downtime clock.
- **a · STATUS PAGE** — incident layout: yellow incident banner, component status list (FEED /
  SOCKETS / CHARTS / ALERTS) each with spinner→✓ recovery cycle on loop, heartbeat pulses, ETA
  chip, smile avatar nodding in the header, downtime clock. Status-bar ticker.
- **b · RECONNECT LAB** — the buffer ring reimagined as one big shadcn progress ring with a mono
  reconnect log beneath (timestamped attempt lines typing, retry #9 → #10 …), loader-eyes smile
  seated in the ring center, recovery sweep on the ring. Ticker.
- **c · WORKSHOP BENCH** — narrative split bench: left a flatlined broken chart (dead candles,
  error badge), right the smile with a wrench prop "repairing" it — 3-step checklist ticks over,
  candles reignite alive left-to-right, `FEED RESTORED` flash, then a soft loop resets. Ticker.

### Q&A / OPEN FLOOR — `qa-a.html` `qa-b.html` `qa-c.html`
Copy essence: h1 `open comms.` or `ask me anything.` · channel strip `OPEN COMMS · CHANNEL 01` ·
TX cards `TX·01 @handle "question…" SIG 96%` · `MIC HOT` `ROOM LISTENING`. Contract: `?ep=128`.
- **a · TRANSMISSION FEED** — split: left giant `ASK ME ANYTHING` keynote type + submission chips
  (drop it in chat / @smileke), right a cycling stack of TX question cards (slide in, hold, file
  away) from a demo pool, signal bars animating per card. Ticker.
- **b · TOWN HALL** — built environment: podium desk with nameplate + smile host behind it
  (peek/bob/lean), a parallax wall of giant dim `?` glyphs behind, two vertical question
  marquees flowing up the sides, ON AIR lamp glowing red. Ticker.
- **c · CALLER BOARD** — broadcast call-in board: rows ON AIR / NEXT / QUEUED with animated VU
  meters, hold-music equalizer bars, dial chip `@smileke`, EP badge, big board title. Ticker.

### END — `end-a.html` `end-b.html` `end-c.html`
Copy essence: eyebrow `✓ MARKET CLOSED` · h1 `session closed.` · sub `Asante for trading with us
today — books balanced, smile intact. Same desk next time.` · socials `▶ YouTube · /smileke`
`◉ Twitch · /smileke` `♪ TikTok · @smileke` · `NEXT SESSION · FRIDAY 8PM EAT`.
- **a · CLOSING BELL** — the strike: giant bell disc with the smile engraved swings in and rings
  once at t≈1s (swing arc, radial shockwave rings, confetti burst, subtle camera shake), then the
  results panel + socials + NEXT SESSION settle. Confetti palette locked:
  `#FFC107 #0ECB81 #F6465D #FFFFFF #3FB6FF`.
- **b · RECEIPT PRINT** — thermal receipt prints down from a printer slot (clip-path reveal, mono
  type, jagged torn bottom): session lines (EP, uptime, moves called, vibes 100%), dashed
  separators, barcode, `PAID IN FULL — SMILE CO.`, stamp `✓ MARKET CLOSED`, tear-off wobble at
  the end. Desk shadow, faint paper grain.
- **c · CREDITS CRAWL** — keynote black stage: giant smile center doing tricks, `thank you.`
  gradient h1, an auto-scrolling credits column (desk roles → handles → smile.co.ke), confetti
  drift on depth planes, `NEXT SESSION · FRIDAY 8PM EAT` marquee band.

---

## 6 · QA PROTOCOL (every builder, every file)

1. Screenshot 1920×1080 with agent-browser at t≈0, t≈2s, t≈8s (isolated `--session`; verify the
   page URL before every shot). Save to `../../audit/spec/`.
2. **Read the PNGs yourself with the Read tool — native eyes only. VLM skills are banned.**
   Judge: composition matches the brief, brand tokens correct, digits legible, nothing clipped/
   overflowing/boilerplate, frame one already composed.
3. Console must be clean; fix and re-shoot until pass. Log every fix.
4. Leave a per-file verdict in the worklog.
