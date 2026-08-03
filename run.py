import threading
import webbrowser

import uvicorn

from server.config import BRIDGE_HOST, BRIDGE_PORT


def main():
    base = "http://127.0.0.1:" + str(BRIDGE_PORT)
    print()
    print("=" * 64)
    print("   SMILE LIVE KIT - bridge")
    print("=" * 64)
    print("   Status page : " + base + "/")
    print("   Dashboard   : " + base + "/core/control.html")
    print()
    print("   The dashboard opens in your browser automatically.")
    print("   Leave this window open. Press Ctrl+C to stop.")
    print("=" * 64)
    print()
    threading.Timer(2.5, lambda: webbrowser.open(base + "/core/control.html")).start()
    uvicorn.run("server.app:app", host=BRIDGE_HOST, port=BRIDGE_PORT, log_level="warning")


if __name__ == "__main__":
    main()
