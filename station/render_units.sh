#!/usr/bin/env bash
# render_units.sh -- render the installed systemd units for THIS box.
#
#   render_units.sh <unit_src_dir> <unit_dst_dir> <broadcast_root> <repo_path> <shape>
#
# shape: lab | session-nogpu | headless
#
# The install used to live inside setup.sh, where nothing could test it.
# It is a pile of seds whose patterns stop matching the moment a unit is
# edited -- and a unit that silently loses its BROADCAST_ROOT looks fine
# until it starts: ${BROADCAST_ROOT}/mediamtx.yml expands to
# /mediamtx.yml, which does not exist, and the ingest bus never comes up.
#
# So the render lives here, it is standalone, and station/test_unit_render.py
# runs it for real.
set -euo pipefail

UNIT_SRC="${1:?unit src dir}"
UNIT_DST="${2:?unit dst dir}"
ROOT="${3:?broadcast root}"
REPO_PATH="${4:?repo path}"
SHAPE="${5:-lab}"

mkdir -p "$UNIT_DST"

render_one() {
  u="$1"
  _uf="$UNIT_DST/$(basename "$u")"
  case "$u" in
    *monitor-av*) return 0 ;;   # dead path (mediamtx dropped it 2026-10-18)
    *station-vnc*)
      [ "$SHAPE" = headless ] && return 0   # no Wayland session to mirror
      ;;
  esac
  # The unit has to point at THIS install: the repo path, the secrets
  # file and the media root all move together (a VPS install lives in
  # /var/broadcast, not in the repo).
  sed -e "s|%h/Documents/GitHub/world-21-suite|$REPO_PATH|g" \
      -e "s|/home/rkw/Documents/GitHub/world-21-suite|$REPO_PATH|g" \
      -e "s|EnvironmentFile=.*|EnvironmentFile=$ROOT/secrets.env|" \
      "$u" > "$_uf"
  # Every unit gets the media root, not just the daemon: panel, overlay
  # and watchdog honor BROADCAST_ROOT too. One unit left on the repo tree
  # meant a /var/broadcast daemon playing state the others could not see.
  if ! grep -q "^Environment=BROADCAST_ROOT=" "$_uf"; then
    if grep -q "^Environment=" "$_uf"; then
      sed -i "s|^Environment=|Environment=BROADCAST_ROOT=$ROOT\nEnvironment=|" "$_uf"
    else
      # A unit with NO Environment= line at all (panel, overlay,
      # watchdog, mediamtx) needs the line INSERTED -- and it must land
      # inside [Service]: appending to the end of the file puts it in
      # [Install], where systemd ignores it ("Referenced but unset
      # environment variable evaluates to an empty string").
      sed -i "/^\[Service\]/a Environment=BROADCAST_ROOT=$ROOT" "$_uf"
    fi
  fi
}

for u in "$UNIT_SRC"/station-*.service; do
  render_one "$u"
done

# The render plane: the unit in git is the lab shape (a real session on
# :0 with hardware GL). A GPU-less headless box boots a different plane:
# Xvfb :99 + llvmpipe. Rendered at provision time so a re-run self-heals
# a drifted or hand-edited unit.
OBS_UNIT="$UNIT_DST/station-obs.service"
if [ -f "$OBS_UNIT" ]; then
  if [ "$SHAPE" = lab ]; then
    echo "render plane: real session :0, hardware GL (as shipped)"
  else
    # LIBGL_ALWAYS_SOFTWARE: on the lab iGPU it chained the plane to
    # llvmpipe and burned 2x realtime CPU. On a box with no GPU driver
    # that trade does not exist -- without the flag OBS may fail to
    # create a GLX context at all. Xvfb cannot host hardware GLX anyway,
    # so headless means software GL, full stop.
    if ! grep -q -- '--env=LIBGL_ALWAYS_SOFTWARE=1' "$OBS_UNIT"; then
      sed -i 's| com.obsproject.Studio --verbose| --env=LIBGL_ALWAYS_SOFTWARE=1 com.obsproject.Studio --verbose|' "$OBS_UNIT"
    fi
    if [ "$SHAPE" = session-nogpu ]; then
      echo "render plane: session :0 but NO GPU driver -> LIBGL_ALWAYS_SOFTWARE=1"
    else
      sed -i -e 's|--env=DISPLAY=:0|--env=DISPLAY=:99|' \
             -e 's|--env=PLANE_DISPLAY=:0|--env=PLANE_DISPLAY=:99|' \
             -e 's|^Environment=DISPLAY=:0|Environment=DISPLAY=:99|' \
             -e 's|^Environment=PLANE_DISPLAY=:0|Environment=PLANE_DISPLAY=:99|' \
             "$OBS_UNIT"
      echo "render plane: headless -> Xvfb :99 + LIBGL_ALWAYS_SOFTWARE=1"
    fi
    # The render edits exact strings from the unit file. A future unit
    # edit that renames one of them must fail LOUD here -- not silently
    # boot a :0 plane on a box with no :0.
    grep -q -- '--env=LIBGL_ALWAYS_SOFTWARE=1' "$OBS_UNIT" || {
      echo "::error::station-obs.service render failed: LIBGL flag not planted -- the unit text no longer matches the sed." >&2
      exit 1
    }
    if [ "$SHAPE" = headless ] && ! grep -q -- '--env=DISPLAY=:99' "$OBS_UNIT"; then
      echo "::error::station-obs.service render failed: display not moved to :99 -- the unit text no longer matches the sed." >&2
      exit 1
    fi
  fi
fi

# Fail loud: a unit that references ${BROADCAST_ROOT} without defining it
# expands to an empty path at start, and the failure is a missing file,
# not a message anyone reads.
for _f in "$UNIT_DST"/station-*.service; do
  if grep -q '\${BROADCAST_ROOT}' "$_f" && ! grep -q "^Environment=BROADCAST_ROOT=" "$_f"; then
    echo "::error::$(basename "$_f") uses \${BROADCAST_ROOT} but never defines it." >&2
    exit 1
  fi
done
