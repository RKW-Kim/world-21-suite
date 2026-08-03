"""
Mock market data. Random-walk prices, no external calls.
Swap this module out when real API keys are configured.
"""

import random
import time

_SYMBOLS = [
    {"symbol": "BTC/USD", "price": 114_250.00, "vol": 0.0008},
    {"symbol": "ETH/USD", "price": 3_680.00, "vol": 0.0012},
    {"symbol": "SOL/USD", "price": 172.40, "vol": 0.0025},
    {"symbol": "SPX", "price": 5_920.00, "vol": 0.0004},
    {"symbol": "EUR/USD", "price": 1.0842, "vol": 0.0002},
]

_state: list[dict] = []


def _init() -> None:
    global _state
    _state = [
        {
            "symbol": s["symbol"],
            "price": s["price"],
            "prev_close": s["price"],
            "vol": s["vol"],
        }
        for s in _SYMBOLS
    ]


def tick() -> list[dict]:
    """Advance one step. Returns list of ticker dicts."""
    if not _state:
        _init()

    out = []
    for s in _state:
        drift = random.gauss(0, s["vol"])
        s["price"] *= 1 + drift
        change_pct = ((s["price"] - s["prev_close"]) / s["prev_close"]) * 100
        out.append(
            {
                "symbol": s["symbol"],
                "price": round(s["price"], 2),
                "change_pct": round(change_pct, 3),
                "direction": "up" if change_pct >= 0 else "down",
                "ts": int(time.time()),
            }
        )
    return out
