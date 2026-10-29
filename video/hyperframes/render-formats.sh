#!/usr/bin/env bash
# Renders the 9:16 master (index.html) plus 16:9 and 1:1 variants for Google Demand Gen.
# The variants are built into renders/.formats/<format>/ as copies of this project with only the
# root canvas size changed; the scenes lay themselves out per aspect ratio with container queries.
set -euo pipefail
cd "$(dirname "$0")"
QUALITY="${QUALITY:-delivery}"
HF="npx --yes hyperframes@0.8.214"
mkdir -p renders
render() { # name width height dir
  local name=$1 w=$2 h=$3 dir=$4
  $HF render "$dir" --quality "$QUALITY" --output "$PWD/renders/team3-demandgen-$name.mp4"
}
variant() { # name width height
  local name=$1 w=$2 h=$3 dir="renders/.formats/$1"
  rm -rf "$dir" && mkdir -p "$dir"
  cp -r assets compositions hyperframes.json meta.json package.json "$dir/"
  sed -e "s/width=1080, height=1920/width=$w, height=$h/" \
      -e "s/width: 1080px; height: 1920px/width: ${w}px; height: ${h}px/" \
      -e "s/data-width=\"1080\" data-height=\"1920\"/data-width=\"$w\" data-height=\"$h\"/g" \
      -e "s/Demand Gen 9:16/Demand Gen $name/" index.html > "$dir/index.html"
  echo "$dir"
}
case "${1:-all}" in
  portrait)  render portrait 1080 1920 . ;;
  landscape) render landscape 1920 1080 "$(variant landscape 1920 1080)" ;;
  square)    render square 1080 1080 "$(variant square 1080 1080)" ;;
  variants)  variant landscape 1920 1080 >/dev/null; variant square 1080 1080 >/dev/null ;;
  all)       "$0" portrait; "$0" landscape; "$0" square ;;
esac
