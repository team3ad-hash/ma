#!/usr/bin/env bash
# Pre-scales every photo in assets/ into assets/hd/ with Lanczos + a light unsharp,
# so the browser never has to blow up a small source (its own scaling is softer).
# The short side becomes at least 2100px: enough to cover 1080x1920 with the Ken Burns zoom.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets/hd
for f in assets/*.jpg; do
  n=$(basename "$f")
  ffmpeg -y -loglevel error -i "$f" \
    -vf "scale='if(lt(iw,ih),max(iw,2100),-2)':'if(lt(iw,ih),-2,max(ih,2100))':flags=lanczos,unsharp=5:5:0.45:5:5:0" \
    -q:v 2 "assets/hd/$n"
  echo "hd  $n  $(ffprobe -v error -show_entries stream=width,height -of csv=p=0 "assets/hd/$n")"
done
