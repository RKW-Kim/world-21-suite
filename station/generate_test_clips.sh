#!/usr/bin/env bash
# Generate short labeled test clips: 10s "videos" standing in for 2-hour
# items (compressed-time E2E), plus a 6s ad. Distinct hue + tone + burnt-in
# label per clip so screenshots and ears both tell them apart.
#   bash station/generate_test_clips.sh
# Output: broadcast/media/e2e_v{1..5}.mp4 + e2e_ad1.mp4 (gitignored dir).
set -u
OUT="broadcast/media"
FONT="/usr/share/fonts/noto/NotoSans-Regular.ttf"
mk() { # name seconds hue tone label
  ffmpeg -hide_banner -loglevel error -y \
    -f lavfi -i "testsrc=size=640x360:rate=30:duration=$2" \
    -f lavfi -i "sine=frequency=$4:duration=$2" \
    -vf "hue=h=$3,drawtext=fontfile=$FONT:text='$5':fontsize=42:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2,drawtext=fontfile=$FONT:text='E2E $1':fontsize=20:fontcolor=yellow:x=10:y=10" \
    -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest \
    "$OUT/$1" && echo "made $1"
}
mk e2e_v1.mp4 10 0   440 "VIDEO 1 / 10s SIMULATING 2H"
mk e2e_v2.mp4 10 90  494 "VIDEO 2 / 10s SIMULATING 2H"
mk e2e_v3.mp4 10 180 587 "VIDEO 3 / 10s SIMULATING 2H"
mk e2e_v4.mp4 10 270 659 "VIDEO 4 / 10s SIMULATING 2H"
mk e2e_v5.mp4 10 45  523 "VIDEO 5 / ADDED LIVE MID-RUN"
mk e2e_ad1.mp4 6 200 880 "AD BREAK / 6s"
ls -la "$OUT"/e2e_*.mp4 | awk '{print $5, $9}'
