# Design system

## Brand truth (smile.co.ke)
Near-black UI (`--ink #0a0a0a`), dark hairline cards (`--panel #141414`, `--line #2a2a2a`), yellow accent `#FFC107`, green `#0ECB81`, red `#F6465D`, muted `#8c8c8c`. Section titles carry a yellow vertical tick. Type: Manrope / Inter.

## The mark - 1:1, traced, never prettified
viewBox 0 0 100 100 (in `core/smile-mark.js` + `core/smile-mark.svg`):
- disc `<circle cx=50 cy=50 r=50 fill=#FFC107>`
- eyes `<ellipse cx=41 cy=40 rx=6.5 ry=7.6>` and `cx=59` (close together, not wide)
- mouth `<path d="M32 55 C 35 77, 65 77, 68 55" stroke=#0b0b0b stroke-width=10.5 stroke-linecap=round>`
The thick stroke (10.5) is what makes the smile read as one stroke; thinner splits into two ball-ends (parody look). Do not adjust to taste - re-trace from the asset.

## Motion / moods
Idle blinks/glances automatic. Event moods via `smileMood('wink'|'smirk'|'spin'|'bounce'|'nod'|'look'|'celebrate'|'shake')`, or lock with `data-mood="..."`. The live HUD fires celebrate on green spikes, shake on red.

## Layouts (`core/03-live.html?layout=`)
| layout | use | boxes |
|---|---|---|
| solo | caster + chart + chat | cam1, chart, struct, chat, lower-third |
| chart | deep analysis | chart (wide), struct (tall) |
| duo | two talking heads | cam1, cam2 |
| panel | 3-4 guests | cam1-4, struct |
| video | replay + progress | media, chart strip, progress rail |
| nocam | voice-only | chart, struct, chat |
| nochat | cam + chart + movers | cam1, chart, struct, board |
| fullface | one big cam | cam1 (large), lower-third |
