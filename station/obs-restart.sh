#!/usr/bin/env bash
# station/obs-restart.sh [COLLECTION] — restart headless OBS without clobbering.
# Order matters and has bitten three times: OBS saves its in-memory collection
# on graceful shutdown, so copy the fresh file only AFTER the old process is
# fully gone (CEF teardown takes 10s+), then launch, then wait for boot.
#   station/obs-restart.sh               # SMILE-Station
#   station/obs-restart.sh SMILE-Lab     # light lab build
set -euo pipefail
cd "$(dirname "$0")/.."
COLLECTION="${1:-SMILE-Station}"
DISP="${DISPLAY_NUM:-99}"
SCENES_DIR="$HOME/.var/app/com.obsproject.Studio/config/obs-studio/basic/scenes"

for pid in $(pgrep -x obs 2>/dev/null); do kill "$pid"; done
for _ in $(seq 1 16); do pgrep -x obs >/dev/null || break; sleep 5; done
if pgrep -x obs >/dev/null; then
  echo "::error::OBS refuses to exit; refusing to race it. kill -9 by hand."
  exit 1
fi
cp "broadcast/scenes/$COLLECTION.json" "$SCENES_DIR/$COLLECTION.json"
echo "collection $COLLECTION installed"
setsid bash -c "DISPLAY=:$DISP flatpak run --socket=x11 --env=DISPLAY=:$DISP com.obsproject.Studio --verbose --minimize-to-tray > /tmp/obs_headless.log 2>&1" < /dev/null > /dev/null 2>&1 & disown
echo "launched; booting (~60s under CEF load)..."
