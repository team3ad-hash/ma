#!/bin/bash
# Mux rendered picture with the audio mix → delivery MP4s (H.264 High, AAC 192k, faststart)
set -e
cd "$(dirname "$0")"
declare -A NAME=( [land]=16x9 [port]=9x16 [sq]=1x1 )
for a in ${@:-land port sq}; do
  [ -f out/raw_$a.mp4 ] || continue
  ffmpeg -hide_banner -loglevel error -y -i out/raw_$a.mp4 -i audio/mix.wav \
    -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart out/team3_guard_${NAME[$a]}.mp4
  ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/team3_guard_${NAME[$a]}.mp4 | sed "s/^/${NAME[$a]}: /"
done
