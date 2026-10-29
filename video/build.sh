#!/usr/bin/env bash
# Builds both Demand Gen formats: 16:9 (YouTube in-stream / feed) and 9:16 (Shorts).
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules ] || npm ci
python3 music.py build/music.wav
node render.js 1920 1080 build/team3_demandgen_16x9.mp4
node render.js 1080 1920 build/team3_demandgen_9x16.mp4
