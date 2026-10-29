#!/usr/bin/env bash
# Downloads the real Team3 photos used by the video into assets/.
# Run on a machine (or session) that can reach www.team3.co.il, then re-render.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets
B=https://www.team3.co.il/wp-content/uploads
get() { curl -fsSL "$1" -o "assets/$2.src" && ffmpeg -y -loglevel error -i "assets/$2.src" -vf "${3:-scale='min(2400,iw)':-2}" -q:v 2 "assets/$2.jpg" && rm "assets/$2.src" && echo "ok  $2"; }
get "$B/2026/09/מצלמות-אבטחה-בבית-פרטי.png"                   cctv     # security camera on a private home
get "$B/2022/05/מוקד2.jpg"                                    moked2   # operators at the control room monitors
# assets/moked.jpg (wide control-room shot) was supplied directly and is committed in assets/
# the motorcycle shot only exists inside an ad banner: crop the riders out of the square version
get "$B/2026/06/WhatsApp-Image-2026-06-09-at-11.16.48-1.jpeg" moto "crop=620:720:980:140"
get "$B/2022/04/GEP_9316-1.jpg"                               patrol   # three patrol officers on motorcycles
get "$B/2022/04/GEP_9120-1-1.jpg"                             patrol2  # two officers patrolling the office plaza
get "$B/2026/10/home-hero-poster.webp"                        hq       # Team3 HQ building with logo
