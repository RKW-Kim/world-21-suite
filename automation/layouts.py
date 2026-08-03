"""
Transform maps for 1920x1080 canvas.
Each layout defines named slots with (x, y, w, h).
The overlay HTML and OBS source transforms both read from this.
"""

W = 1920
H = 1080

LAYOUTS: dict[str, dict] = {
    "single": {
        "slots": [
            {"name": "main", "x": 0, "y": 0, "w": W, "h": H},
        ],
    },
    "duo": {
        "slots": [
            {"name": "left", "x": 0, "y": 0, "w": W // 2, "h": H},
            {"name": "right", "x": W // 2, "y": 0, "w": W // 2, "h": H},
        ],
    },
    "grid4": {
        "slots": [
            {"name": "tl", "x": 0, "y": 0, "w": W // 2, "h": H // 2},
            {"name": "tr", "x": W // 2, "y": 0, "w": W // 2, "h": H // 2},
            {"name": "bl", "x": 0, "y": H // 2, "w": W // 2, "h": H // 2},
            {"name": "br", "x": W // 2, "y": H // 2, "w": W // 2, "h": H // 2},
        ],
    },
    "autotalk": {
        "slots": [
            {"name": "main", "x": 0, "y": 0, "w": 1440, "h": H},
            {"name": "strip_0", "x": 1440, "y": 0, "w": 480, "h": 270},
            {"name": "strip_1", "x": 1440, "y": 270, "w": 480, "h": 270},
            {"name": "strip_2", "x": 1440, "y": 540, "w": 480, "h": 270},
            {"name": "strip_3", "x": 1440, "y": 810, "w": 480, "h": 270},
        ],
        "max_strip": 4,
        "peak_threshold_db": -30.0,
        "poll_ms": 200,
    },
}


def get_slot(layout: str, slot_name: str) -> dict:
    for s in LAYOUTS[layout]["slots"]:
        if s["name"] == slot_name:
            return s
    raise KeyError(f"No slot '{slot_name}' in layout '{layout}'")
