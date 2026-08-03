import json
import os

def build_obs_scene_collection(name="Stream Setup"):
    """
    Generates a valid OBS Studio Scene Collection JSON object
    with structured layering (Top-to-Bottom).
    """
    obs_config = {
        "current_scene": "Main Scene",
        "current_program_scene": "Main Scene",
        "current_transition": "Fade",
        "name": name,
        "scene_order": [
            {"name": "Main Scene"},
            {"name": "Be Right Back"}
        ],
        "sources": [
            # -------------------------------------------------------------
            # SCENE 1: Main Scene
            # -------------------------------------------------------------
            {
                "id": "scene",
                "name": "Main Scene",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "custom_size": False,
                    "id_counter": 3,
                    # Layering order: Index 0 is TOP, Index N is BOTTOM
                    "items": [
                        {
                            "id": 3,
                            "name": "Webcam Overlay",
                            "visible": True,
                            "locked": False,
                            "pos": {"x": 1420.0, "y": 740.0},
                            "scale": {"x": 0.25, "y": 0.25},
                            "align": 5,
                            "rot": 0.0
                        },
                        {
                            "id": 2,
                            "name": "Browser Alerts",
                            "visible": True,
                            "locked": False,
                            "pos": {"x": 0.0, "y": 0.0},
                            "scale": {"x": 1.0, "y": 1.0},
                            "align": 5,
                            "rot": 0.0
                        },
                        {
                            "id": 1,
                            "name": "Display Capture",
                            "visible": True,
                            "locked": False,
                            "pos": {"x": 0.0, "y": 0.0},
                            "scale": {"x": 1.0, "y": 1.0},
                            "align": 5,
                            "rot": 0.0
                        }
                    ]
                }
            },
            # -------------------------------------------------------------
            # SCENE 2: Be Right Back
            # -------------------------------------------------------------
            {
                "id": "scene",
                "name": "Be Right Back",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "custom_size": False,
                    "id_counter": 1,
                    "items": [
                        {
                            "id": 1,
                            "name": "BRB Screen Text",
                            "visible": True,
                            "locked": True,
                            "pos": {"x": 640.0, "y": 480.0},
                            "scale": {"x": 1.0, "y": 1.0},
                            "align": 5,
                            "rot": 0.0
                        }
                    ]
                }
            },
            # -------------------------------------------------------------
            # INDIVIDUAL SOURCES (Referenced inside Scenes)
            # -------------------------------------------------------------
            {
                "id": "dshow_input",
                "name": "Webcam Overlay",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "video_device_id": ""  # OBS auto-detects or rebinds on import
                }
            },
            {
                "id": "browser_source",
                "name": "Browser Alerts",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "url": "http://localhost:8000",
                    "width": 1920,
                    "height": 1080,
                    "fps": 60,
                    "restart_when_active": True
                }
            },
            {
                "id": "monitor_capture",
                "name": "Display Capture",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "capture_cursor": True
                }
            },
            {
                "id": "text_gdiplus_v2",
                "name": "BRB Screen Text",
                "enabled": True,
                "muted": False,
                "volume": 1.0,
                "settings": {
                    "text": "BE RIGHT BACK",
                    "font": {"face": "Arial", "size": 72, "style": "Bold"}
                }
            }
        ]
    }
    return obs_config

def export_json(filename="obs_scene_collection.json"):
    data = build_obs_scene_collection()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[SUCCESS] Created OBS Scene Collection file: {os.path.abspath(filename)}")

if __name__ == "__main__":
    export_json()
