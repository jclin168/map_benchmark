#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
profile_build_dir=${MAP_BENCH_BUILD_DIR:-"${repo_dir}/build-flat64"}
profile_cmake=${MAP_BENCH_CMAKE:-cmake}
profile_args=(-S "$repo_dir" -B "$profile_build_dir" -DCMAKE_BUILD_TYPE=Release
  '-DMAP_BENCH_MAPS=sflat_flat_hash_map;boost_unordered_flat_map;ankerl_unordered_dense;abseil_flat_hash_map;google_dense_hash_map;google_sparse_hash_map'
  -DMAP_BENCH_HASHES=std_hash -DMAP_BENCH_SFLAT_SEED=1)
if [[ -n ${MAP_BENCH_BOOST_SOURCE_DIR:-} ]]; then
  profile_args+=("-DMAP_BENCH_BOOST_SOURCE_DIR=${MAP_BENCH_BOOST_SOURCE_DIR}")
fi
"$profile_cmake" "${profile_args[@]}"
"$profile_cmake" --build "$profile_build_dir" --target std_hash_all -j "${MAP_BENCH_BUILD_JOBS:-2}"
