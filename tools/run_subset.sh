#!/bin/bash
# One iteration of the benchmarks for the maps in build-run, pinned to core 2 (CPUs 0,2 online), one at a time.
# Both cores on the performance governor and turbo off; the effective clock (results/.../clk, ~1.35 is normal)
# is logged before and after each benchmark. A run that takes longer than TIMEOUT seconds is killed and logged.
cd "$(dirname "$0")/.."
R=docs/results/2026-11-14-i5-3230M-subset
TIMEOUT=${TIMEOUT:-300}
BENCHS="AccidentallyQuadratic Copy GameOfLife_growing GameOfLife_stabilizing InsertHugeInt IterateIntegers RandomDistinct2 RandomFindString RandomFindString_1000000 RandomFind_200 RandomFind_2000 RandomFind_500000 RandomInsertErase RandomInsertEraseStrings knucleotide"
APPS=$(cd build-run && ls bench_* | grep -v '\.' | sort)
log() { echo "$(date -Is) $*"; }
for b in $BENCHS; do
  for a in $APPS; do
    log "start $a $b clock $(taskset -c 2 $R/clk)"
    ( cd build-run && timeout $TIMEOUT taskset -c 2 ./$a $b ) > $R/raw/$a.$b.txt 2> $R/raw/$a.$b.err
    log "done $a $b exit $?"
  done
done
log "clock end $(taskset -c 2 $R/clk)"
log "ALL DONE"
