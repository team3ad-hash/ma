#!/bin/bash
# Mix: VO (delayed 50ms to match video), music bed ducked under VO, procedural SFX. Output -14 LUFS / -1.5 dBTP.
set -e
cd "$(dirname "$0")"
ffmpeg -hide_banner -loglevel error -y -i music30.wav -i vo.wav -i sfx.wav -filter_complex "\
[1:a]adelay=50|50,highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,equalizer=f=3000:t=q:w=1:g=2,volume=1.9,apad=whole_dur=30,asplit=2[vo][vosc];\
[0:a]volume=0.36[mus];[mus][vosc]sidechaincompress=threshold=0.02:ratio=5:attack=25:release=400[musd];\
[2:a]volume=0.62[fx];\
[musd][vo][fx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=9[out]" -map "[out]" -ar 48000 -t 30 mix.wav
