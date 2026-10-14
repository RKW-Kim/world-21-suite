#!/usr/bin/env bash
# station/obs-restart.sh [COLLECTION] — restart headless OBS without clobbering.
# THE only sanctioned way to (re)start OBS here. The systemd unit owns
# execution; this script only prepares state and asks systemd. Never launch
# flatpak OBS by hand: a direct launch alongside the managed instance splits
# the world into two renderers fighting over one lock (seen live: 20 ghost
# restarts, "already running" dialogs, mutually-clobbering collection saves).
# Order matters and has bitten four times: OBS saves its in-memory collection
# on graceful shutdown, so copy the fresh file only AFTER the old process is
# fully gone (CEF teardown takes 10s+), then restart via the unit.
#   station/obs-restart.sh               # SMILE-Station
#   station/obs-restart.sh SMILE-Lab     # light lab build
set -euo pipefail
cd "$(dirname "$0")/.."
COLLECTION="${1:-SMILE-Station}"
SCENES_DIR="$HOME/.var/app/com.obsproject.Studio/config/obs-studio/basic/scenes"

systemctl --user stop station-obs.service 2>/dev/null || true
systemctl --user stop station-obs.service 2>/dev/null || true
for pid in $(pgrep -x obs 2>/dev/null); do kill "$pid"; done
for _ in $(seq 1 16); do pgrep -x obs >/dev/null || break; sleep 5; done
if pgrep -x obs >/dev/null; then
  echo "::error::OBS refuses to exit; refusing to race it. kill -9 by hand."
  exit 1
fi
cp "broadcast/scenes/$COLLECTION.json" "$SCENES_DIR/$COLLECTION.json"
# Install every rendered collection, not just the boot target: a stale file
# in this dir is indistinguishable from a live one until OBS reads it, and
# a runtime collection SWITCH wedges the websocket server for minutes.
# Booting straight into the right file beats switching every time.
for f in broadcast/scenes/*.json; do
  cp "$f" "$SCENES_DIR/" 2>/dev/null || true
done
echo "collections installed: $(ls broadcast/scenes/*.json | xargs -n1 basename | tr '\n' ' ')"
# A held unit (start-limit from an earlier storm) refuses start until reset.
systemctl --user reset-failed station-obs.service 2>/dev/null || true
systemctl --user start station-obs.service
echo "restart requested via unit; booting (~60s under CEF load)..."
sleep 60
# A dying instance can linger in teardown for a while; that is not a second
# renderer, so recount patiently before accusing.
n=0
for _ in $(seq 1 6); do
  n=$(pgrep -x obs 2>/dev/null | wc -l)
  [ "$n" -le 1 ] && break
  sleep 10
done
if [ "$n" -ne 1 ]; then
  echo "::error::expected exactly 1 obs process, found $n. Kill extras by exact PID, never pattern."
  exit 1
fi
echo "singleton OK (1 obs process, unit-managed)"
