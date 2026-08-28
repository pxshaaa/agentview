#!/bin/sh
# Rebuild the README demo end to end. Needs vhs, ffmpeg and gifsicle, plus
# agents running against a sandbox registry (see "Regenerating the demo").
set -e
cd "$(dirname "$0")/.."
for t in 1-overview 2-detail 3-ask; do vhs "demo/seg/$t.tape"; done
python3 demo/compose.py
ffmpeg -loglevel error -y -i demo/agentview.gif \
  -vf "scale=1200:-2:flags=lanczos,palettegen=max_colors=128" /tmp/av-pal.png
ffmpeg -loglevel error -y -i demo/agentview.gif -i /tmp/av-pal.png \
  -lavfi "scale=1200:-2:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4" \
  /tmp/av-scaled.gif
gifsicle -O3 --lossy=60 /tmp/av-scaled.gif -o demo/agentview.gif
rm -rf demo/.build /tmp/av-pal.png /tmp/av-scaled.gif
ls -lh demo/agentview.gif
