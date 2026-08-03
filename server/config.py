import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BRIDGE_HOST = os.getenv("BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8787"))

OBS_WS_HOST = os.getenv("OBS_WS_HOST", "127.0.0.1")
OBS_WS_PORT = int(os.getenv("OBS_WS_PORT", "4455"))
OBS_WS_PASSWORD = os.getenv("OBS_WS_PASSWORD", "")

STREAM_WIDTH = int(os.getenv("STREAM_WIDTH", "1920"))
STREAM_HEIGHT = int(os.getenv("STREAM_HEIGHT", "1080"))

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
BINANCE_WS_URL = os.getenv("BINANCE_WS_URL", "")

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
MOCK_MARKET = not TWELVE_DATA_API_KEY
