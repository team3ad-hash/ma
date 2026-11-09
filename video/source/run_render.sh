#!/bin/bash
# usage: run_render.sh WxH outdir
cd "$(dirname "$0")"; RES=$1; OUT=$2; TOT=1800; K=4; CH=$((TOT/K))
for i in $(seq 0 $((K-1))); do node render.js $RES $((i*CH)) $(((i+1)*CH)) $OUT > log_${OUT}_$i.txt 2>&1 & done; wait; echo DONE $OUT
