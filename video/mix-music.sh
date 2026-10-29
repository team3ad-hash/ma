#!/usr/bin/env bash
# Builds the music version of the soundtrack (music.py score + original effects) and muxes it
# into the three rendered videos as out/team3-demandgen-<format>-music.mp4 (video stream copied).
set -euo pipefail
cd "$(dirname "$0")"
python3 music.py
python3 soundtrack.py --fx
ffmpeg -v error -y -i out/music.wav -i out/soundtrack-fx.wav \
  -filter_complex "[1]volume=-4dB[f];[0][f]amix=inputs=2:normalize=0,alimiter=limit=0.84" -ar 44100 out/mix-pre.wav
M=$(ffmpeg -i out/mix-pre.wav -af loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
F=$(python3 -c "import json,sys;m=json.loads(sys.argv[1]);print(f\"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true\")" "$M")
ffmpeg -v error -y -i out/mix-pre.wav -af "$F" -ar 44100 out/soundtrack-music.wav
rm out/mix-pre.wav
for fmt in portrait landscape square; do
  ffmpeg -v error -y -i "out/team3-demandgen-$fmt.mp4" -i out/soundtrack-music.wav -map 0:v -map 1:a \
    -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "out/team3-demandgen-$fmt-music.mp4"
done
echo "done"
