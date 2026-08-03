#!/usr/bin/env python3
"""
Visual test for autotalk. Cycles fake speakers so you can watch the layout
reshuffle with only one physical mic/camera (or none).

Usage:
  python3 scripts/test_autotalk.py --simulate
"""

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.controller import OBSController, Participant
from automation.autotalk import AutoTalkController
from server.config import OBS_WS_PASSWORD, BRIDGE_PORT

logging.basicConfig(level=logging.INFO, format="%(message)s")

SCENE = "03-live"
BRIDGE_URL = f"http://127.0.0.1:{BRIDGE_PORT}"

# Demo script: each step = (description, [speaker CAM numbers])
SCRIPT = [
    ("Single speaker: CAM 1 takes the main slot",            [1]),
    ("Speaker switch: CAM 2 promoted to main",               [2]),
    ("Two up: CAM 3 main, CAM 4 in the strip",               [3, 4]),
    ("Three up: CAM 1 main, CAM 2 + CAM 5 in strip",         [1, 2, 5]),
    ("Full grid: CAM 2 main, 1/3/4/5 fill the strip",        [2, 1, 3, 4, 5]),
    ("Back to solo: CAM 4 alone",                            [4]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--interval", type=float, default=3.5, help="seconds per step")
    a = ap.parse_args()

    if not a.simulate:
        print("Run with --simulate")
        return

    obs = OBSController()
    obs.connect()

    parts = [Participant(f"CAM {i}", f"CAM-{i}", f"Mic-{i}") for i in range(1, 6)]
    by_num = {i: parts[i - 1] for i in range(1, 6)}

    ctl = AutoTalkController(obs, SCENE, parts, bridge_url=BRIDGE_URL)

    print(f"Testing scene '{SCENE}' — watch OBS. Ctrl+C to stop.\n")
    try:
        while True:
            for desc, nums in SCRIPT:
                main = by_num[nums[0]]
                strip = [by_num[n] for n in nums[1:]]
                print(f"  > {desc}")
                ctl.apply_state(main, strip)
                time.sleep(a.interval)
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        obs.disconnect()


if __name__ == "__main__":
    main()
