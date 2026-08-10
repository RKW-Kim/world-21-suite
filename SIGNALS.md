# SMILE · Live Signals Integration (for the smile dev)

The overlay (`overly/test-7.html`) already polls `overly/state.json` every 3s.
When `trades` exists, the Dynamic Island switches from simulator to LIVE feed automatically.

## state.json schema
{
  "goal":  { "current": 640, "target": 1000 },
  "event": { "id": "e-101", "type": "superthanks|superchat|follow|sub|schedule|trade|close",
             "user": "Kip", "amount": "KES 500", "msg": "thanks!" },
  "trades": [
    { "id": 3, "market": "XAU/USD", "side": "LONG",
      "entry": 2384.20, "tp": 2398.00, "sl": 2377.00,
      "status": "open", "now": 2391.40, "pips": 72.0 },
    { "id": 2, "market": "EUR/USD", "side": "SHORT",
      "entry": 1.0850, "tp": 1.0800, "sl": 1.0890,
      "status": "closed", "closeReason": "tp|sl|manual|time", "pips": 50 }
  ]
}

Rules the writer (bot) should follow:
1. Keep only the ACTIVE trade with status "open"; closed ones may stay for history.
2. Update "now" (or "pips") as often as you like — the island dot springs, it never jumps.
3. Flip status to "closed" + set closeReason → the island fires a result alert
   (✅ +pips / ❌ −pips) and goes flat until the next "open" appears.
4. "event" needs a unique "id" per notification (dedupe key).

## Who decides to close?
NOT the overlay. The overlay is display-only on purpose (OBS browser source,
no secrets, no trade risk). Auto-close lives where the money lives:
- Bot/EA closes on TP/SL/time/price and writes the closed status → overlay animates it.
- Host closes manually on smile → bot detects (websocket/position diff) → same write.

## Integration paths (pick one)
A. FILE (works today): bot/EA → tiny script writes overly/state.json. Done.
B. BRIDGE (after modularize): bridge.py exposes POST /state; bot hits HTTP;
   overlay swaps polling for push. One-line change (watchState → EventSource).
C. SMILE NATIVE (ask the dev): smile backend emits a webhook on position
   open/update/close → webhook writer → state.json (or bridge). Zero scraping.
D. DOM SCRAPE (last resort): hidden browser source logged into smile.co.ke +
   MutationObserver on the positions table → postMessage to the overlay.
   Fragile (login sessions, CSP, cross-origin) — only if A–C are impossible.

## Test hooks (no bot needed)
Command Center → Dynamic Island buttons: Signal Open / Close / Hit TP / Hit SL.
They post BroadcastChannel commands the viewer engine handles exactly like a
live feed, so you can rehearse alerts on stream.
