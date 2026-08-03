# Data sources & the 24/7 budget

## The bridge is the single poller
`core/bridge.py` fetches every provider on one loop and serves `http://localhost:8787/quotes.json`. One poller = no double-counting, which is what makes the budget math true. It also serves the pages over localhost (=> portable JSON) and `/brand.json`.

## Providers
| instrument | provider | key? | limit |
|---|---|---|---|
| BTC/ETH/BNB/XRP/SOL | Binance | no | none |
| XAU/XAG | metals.live | no | none |
| USD/KES, EUR/USD, GBP/USD | fawazahmed0 | no | none (daily) |
| S&P 500, NAS 100 | Twelve Data | your key (secrets.env) | budget-gated |
| CRASH500 / synthetics | Smile feed | dev | none once wired |

## Why your key survives 24/7/365
Plan = 800/day, 8/min. Indices move Mon-Fri 09:30-16:00 NY (~390 min). The bridge polls the 2 index symbols once/min in that window: 390x2 = 780/day (<=800), 2/min (<=8). Overnight/weekends = 0 polls, frozen close shown (correct). Hard fuse at 790/day, resets midnight NY.

## What no public feed gives you
Smile synthetics + the embedded tab's open chart. Two browser sources can't read each other (same-origin). Fix = the site announces. **Verbatim spec for your dev:**

> One WebSocket `wss://api.smile.co.ke/stream/ws`; fan out per trader:
> `{"type":"active","symbol":"CRASH500/CFD","tf":"M1"}` / `{"type":"quote","symbol":"BTC/USDT","price":65019.75,"change":0.47}` / `{"type":"positions","positions":[{"s":"BTC/USDT","side":"LONG","pnl":2.4}]}` / `{"type":"klines","symbol":"BTC/USDT","klines":[[ts,o,h,l,c]]}`.
> Overlay sets `SMILE.api.ws` to that URL; ticker, charts, embedded-tab mirror and progress rail become server-authoritative. REST fallback `.../stream/quotes` + `.../stream/klines?symbol=..&interval=1m` -> `SMILE.api.rest`.

## Dev-free mirror (until the socket exists)
`core/watch-smile.js` (Puppeteer) opens a real smile window you trade in; OBS Window-Captures it; the watcher writes the active symbol to `active.json` (served at `/active`). Needs the CSS selector of the on-screen symbol.

## Key safety
The key is in git-ignored `core/secrets.env`, never committed. If you must hardcode (private repo, accept risk): set `TWELVEDATA_KEY` default in `core/bridge.py`.
