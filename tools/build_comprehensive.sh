#!/usr/bin/env bash
set -euo pipefail
root_dir=$(cd "$(dirname "$0")/.." && pwd)
cmake_bin=${MAP_BENCH_CMAKE:-cmake}
build_dir=${MAP_BENCH_SUITE_BUILD_DIR:-"$root_dir/build-comprehensive"}
result_dir=${MAP_BENCH_SUITE_RESULT_DIR:-"$root_dir/results-comprehensive"}
suite_maps=$(paste -sd';' "$root_dir/tools/comprehensive_adapters.txt")
args=(-DMAP_BENCH_MAPS="$suite_maps" -S "$root_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release
  -DMAP_BENCH_HASHES=std_hash -DMAP_BENCH_SFLAT_SEED=1
  -DENABLE_FOLLY=ON -DMAP_BENCH_FOLLY_MINIMAL=ON -DMAP_BENCH_UNITY_BUILD=ON)
if [[ -n ${MAP_BENCH_BOOST_SOURCE_DIR:-} ]]; then args+=(-DMAP_BENCH_BOOST_SOURCE_DIR="$MAP_BENCH_BOOST_SOURCE_DIR"); fi
if [[ -n ${MAP_BENCH_ANKERL_DIR:-} ]]; then args+=(-DMAP_BENCH_ANKERL_DIR="$MAP_BENCH_ANKERL_DIR"); fi
if [[ -n ${MAP_BENCH_ABSEIL_DIR:-} ]]; then args+=(-DMAP_BENCH_ABSEIL_DIR="$MAP_BENCH_ABSEIL_DIR"); fi
"$cmake_bin" "${args[@]}"
python3 "$root_dir/tools/build_comprehensive.py" --cmake "$cmake_bin" --build "$build_dir" --out "$result_dir" "$@"
