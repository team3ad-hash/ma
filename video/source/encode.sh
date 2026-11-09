#!/bin/bash
# usage: encode.sh framesdir out.mp4
cd "$(dirname "$0")"
ffmpeg -hide_banner -loglevel error -y -framerate 60 -i $1/f%05d.jpg -i mix.wav \
  -vf "tmix=frames=2:weights='1 1',fps=30,format=yuv420p" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -tune film -movflags +faststart \
  -c:a aac -b:a 256k -ar 48000 -shortest -t 30 $2 && ls -la $2 && ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of compact $2
