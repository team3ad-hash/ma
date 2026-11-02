#!/bin/bash
# Replace video seconds 22.5–27.0 (frames 675–809) of out/raw_<a>.mp4 with out/tail_<a>.mp4
set -e
cd "$(dirname "$0")"
for a in ${@:-land port sq}; do
  ffmpeg -hide_banner -loglevel error -y -i out/raw_$a.mp4 -i out/tail_$a.mp4 -filter_complex \
   "[0:v]trim=end_frame=675,setpts=PTS-STARTPTS[h];[1:v]trim=end_frame=135,setpts=PTS-STARTPTS[m];[0:v]trim=start_frame=810,setpts=PTS-STARTPTS[t];[h][m][t]concat=n=3:v=1[v]" \
   -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -pix_fmt yuv420p out/raw_${a}_s.mp4
  mv out/raw_${a}_s.mp4 out/raw_$a.mp4
  echo "$a: $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 out/raw_$a.mp4) frames"
done
