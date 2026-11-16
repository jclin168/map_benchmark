#!/bin/bash
cd "$(dirname "$0")/../../../../build-run"
O=../docs/results/2026-11-14-i5-3230M-subset/aq-rerun
for r in 1 2 3; do
  for a in $(ls bench_* | grep -v '\.' | sort); do
    echo "$(date -Is) start $a run $r clock $(taskset -c 2 ../docs/results/2026-11-14-i5-3230M-subset/clk)"
    timeout 300 taskset -c 2 ./$a AccidentallyQuadratic > $O/$a.$r.txt 2> $O/$a.$r.err
    echo "$(date -Is) done $a run $r exit $?"
  done
done
echo "$(date -Is) ALL DONE"
