# sflat::flat_hash_map in map_benchmark (2026-11)

sflat::flat_hash_map at commit d77af38 (submodule `external/jclin168__sflat_hash_map`)
against boost::unordered_flat_map, ankerl::unordered_dense::map, emhash8::HashMap
and absl::flat_hash_map. `sflat::flat_hash_map 4d705e4` is the sflat version
of the earlier submodule pin, for a before/after comparison. It was built from
a local map directory that is not in git.

## Test environment

| Item | Value |
|---|---|
| CPU | Intel Xeon @ 2.30 GHz, 4 vCPUs, AVX-512, L3 504 MiB (cloud VM, shared) |
| Memory | 15 GiB |
| Compiler | g++ 13.3.0, `-O3 -march=native -DNDEBUG`, C++17 |
| Versions | Boost 1.83 (system), unordered_dense 7c58a8b, emhash 801d02a, Abseil 20260817.0 |

Build and run:

```sh
cd build
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DMAPS="sflat_flat_hash_map|ktprime_hash_table8|ankerl_unordered_dense|abseil_flat_hash_map|boost_unordered_flat_map" \
  -DHASHES="std_hash|ankerl_hash" ..
ninja
for b in $(./bench_sflat_flat_hash_map__std_hash l); do
  for a in bench_*; do ./$a $b; done
done
```

All benchmarks except CtorDtor and ShowHash, one run each, on one core at a
time, with the maps in a different order for each benchmark. Raw output:
[data/sflat_2026-11.txt](data/sflat_2026-11.txt). The VM is shared with other
workloads, so a difference of less than about 10 percent is noise.

## Summary

Geometric mean over the 15 benchmarks of (time / best time) and
(peak memory / lowest peak memory). 1.00 is the best in all benchmarks.
Lower is better.

| Map | std::hash time | std::hash mem | ankerl hash time | ankerl hash mem |
|---|---|---|---|---|
| absl::flat_hash_map | 9.02 | 1.25 | 1.99 | 1.29 |
| ankerl::unordered_dense::map | 1.68 | 1.63 | 1.23 | 1.10 |
| boost::unordered_flat_map 1_83 | 2.30 | 1.80 | 1.69 | 1.22 |
| emhash8::HashMap | 2.38 | 1.14 | 1.49 | 1.19 |
| sflat::flat_hash_map | 2.01 | 1.58 | 1.61 | 1.07 |
| sflat::flat_hash_map 4d705e4 | 2.12 | 1.56 | 1.64 | 1.06 |

- With `ankerl::unordered_dense::hash`, udm is the fastest overall (1.23),
  then emhash8 (1.49), sflat (1.61), boost (1.69) and absl (1.99). sflat
  uses the least memory (1.07).
- With `std::hash` (the identity in libstdc++), sflat is the fastest overall
  of these maps after udm (2.01 against 1.68). absl (9.02) and emhash8 are
  very slow in some benchmarks (for example GameOfLife and RandomDistinct2):
  with an identity hash, their probes get very long for these keys.
- sflat d77af38 against 4d705e4: d77af38 changes only erase and the insert
  slow path. RandomInsertErase is 10 percent faster with std::hash (10.45
  against 11.55 s) and 1 percent with the ankerl hash. Benchmarks without
  erase (InsertHugeInt, RandomFindString_1000000) also differ by up to 16
  percent; this shows the noise level of this VM.
- sflat is the fastest in AccidentallyQuadratic (its per-table seed) and
  InsertHugeInt, and it uses the least memory in InsertHugeInt (1243 MB
  against 1632 to 1779) and RandomDistinct2 (623 MB against 817 to 892).
- sflat is slow in IterateIntegers (4.0 s against 0.43 for udm and
  emhash8, which store the elements in a dense array) and in Copy (5.6 s
  against 1.0 to 1.9 for emhash8 and udm).
- emhash8 with std::hash in RandomFind_2000 (1.36 s) and RandomFind_500000
  (4.60 s) is much faster than all other results. This is probably a
  special case of its layout with identity-hashed keys, not a general
  result.

## All results

Total seconds of each benchmark (lower is better) and peak memory in MB in
parentheses. **Bold** is the fastest in the column.

**AccidentallyQuadratic** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | **0.92** (304) | **0.98** (305) |
| sflat::flat_hash_map 4d705e4 | 1.04 (305) | 1.04 (305) |
| absl::flat_hash_map | 19.62 (327) | 4.11 (327) |
| ankerl::unordered_dense::map | 1.25 (381) | 1.60 (381) |
| boost::unordered_flat_map 1_83 | 13.88 (296) | 14.15 (296) |
| emhash8::HashMap | 2.57 (409) | 2.44 (409) |

**Copy** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 5.63 (100) | 5.56 (100) |
| sflat::flat_hash_map 4d705e4 | 6.17 (99) | 6.30 (99) |
| absl::flat_hash_map | 9.13 (137) | 9.03 (137) |
| ankerl::unordered_dense::map | 1.89 (99) | 1.83 (99) |
| boost::unordered_flat_map 1_83 | 4.22 (97) | 4.16 (97) |
| emhash8::HashMap | **1.17** (105) | **1.04** (105) |

**GameOfLife_growing** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 2.07 (3) | 2.62 (3) |
| sflat::flat_hash_map 4d705e4 | 2.20 (2) | 2.53 (2) |
| absl::flat_hash_map | 171.67 (1) | 2.71 (3) |
| ankerl::unordered_dense::map | **1.93** (2) | **1.81** (2) |
| boost::unordered_flat_map 1_83 | 2.09 (2) | 2.14 (2) |
| emhash8::HashMap | 35.05 (2) | 3.38 (2) |

**GameOfLife_stabilizing** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 6.27 (1) | 7.22 (1) |
| sflat::flat_hash_map 4d705e4 | 6.54 (1) | 7.16 (1) |
| absl::flat_hash_map | 77.84 (1) | 8.35 (1) |
| ankerl::unordered_dense::map | **3.91** (1) | **3.96** (1) |
| boost::unordered_flat_map 1_83 | 5.64 (1) | 5.59 (1) |
| emhash8::HashMap | 46.24 (1) | 8.12 (1) |

**InsertHugeInt** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | **15.70** (1243) | **17.23** (1242) |
| sflat::flat_hash_map 4d705e4 | 18.24 (1242) | 18.78 (1242) |
| absl::flat_hash_map | 38.49 (1729) | 22.26 (1729) |
| ankerl::unordered_dense::map | 25.77 (1728) | 26.31 (1728) |
| boost::unordered_flat_map 1_83 | 17.77 (1632) | 18.36 (1632) |
| emhash8::HashMap | 26.87 (1779) | 31.42 (1779) |

**IterateIntegers** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 4.03 (2) | 3.97 (2) |
| sflat::flat_hash_map 4d705e4 | 3.95 (2) | 4.00 (2) |
| absl::flat_hash_map | 11.84 (2) | 11.70 (2) |
| ankerl::unordered_dense::map | **0.43** (2) | **0.43** (2) |
| boost::unordered_flat_map 1_83 | 4.24 (2) | 5.49 (2) |
| emhash8::HashMap | 0.45 (2) | 0.49 (2) |

**RandomDistinct2** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | **8.30** (623) | 9.35 (623) |
| sflat::flat_hash_map 4d705e4 | 8.95 (623) | 10.22 (623) |
| absl::flat_hash_map | 209.62 (865) | 9.34 (865) |
| ankerl::unordered_dense::map | 15.01 (865) | 14.20 (865) |
| boost::unordered_flat_map 1_83 | 9.36 (817) | **9.28** (817) |
| emhash8::HashMap | 15.55 (892) | 20.14 (892) |

**RandomFindString** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 23.88 (17) | 33.15 (17) |
| sflat::flat_hash_map 4d705e4 | 22.69 (17) | 30.08 (17) |
| absl::flat_hash_map | 20.15 (17) | 27.91 (19) |
| ankerl::unordered_dense::map | **17.29** (16) | **20.50** (16) |
| boost::unordered_flat_map 1_83 | 18.98 (16) | 22.93 (16) |
| emhash8::HashMap | 20.30 (16) | 21.65 (16) |

**RandomFindString_1000000** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 38.08 (87) | 94.28 (87) |
| sflat::flat_hash_map 4d705e4 | 45.17 (87) | 92.83 (87) |
| absl::flat_hash_map | 44.19 (124) | 107.68 (124) |
| ankerl::unordered_dense::map | **32.25** (79) | **86.98** (79) |
| boost::unordered_flat_map 1_83 | 41.52 (116) | 103.60 (116) |
| emhash8::HashMap | 36.39 (97) | 100.16 (97) |

**RandomFind_200** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 22.59 (1) | 25.59 (1) |
| sflat::flat_hash_map 4d705e4 | 22.83 (1) | 25.62 (1) |
| absl::flat_hash_map | 75.26 (1) | 24.64 (1) |
| ankerl::unordered_dense::map | 23.02 (1) | 22.39 (1) |
| boost::unordered_flat_map 1_83 | **19.89** (1) | 19.96 (1) |
| emhash8::HashMap | 213.57 (1) | **17.12** (1) |

**RandomFind_2000** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 22.66 (1) | 26.45 (1) |
| sflat::flat_hash_map 4d705e4 | 23.62 (1) | 26.90 (1) |
| absl::flat_hash_map | 169.89 (1) | 25.06 (1) |
| ankerl::unordered_dense::map | 22.68 (1) | 22.79 (1) |
| boost::unordered_flat_map 1_83 | 19.76 (1) | 19.66 (1) |
| emhash8::HashMap | **1.36** (0) | **17.63** (1) |

**RandomFind_500000** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 43.55 (21) | 46.24 (21) |
| sflat::flat_hash_map 4d705e4 | 43.18 (21) | 49.74 (21) |
| absl::flat_hash_map | 19.64 (26) | 48.73 (35) |
| ankerl::unordered_dense::map | 48.13 (18) | 48.39 (18) |
| boost::unordered_flat_map 1_83 | 37.01 (33) | **39.57** (33) |
| emhash8::HashMap | **4.60** (17) | 63.13 (30) |

**RandomInsertErase** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 10.45 (287) | 11.90 (287) |
| sflat::flat_hash_map 4d705e4 | 11.55 (287) | 12.04 (287) |
| absl::flat_hash_map | 169.20 (2) | 14.05 (409) |
| ankerl::unordered_dense::map | 13.69 (235) | 13.87 (235) |
| boost::unordered_flat_map 1_83 | **10.25** (385) | **9.75** (385) |
| emhash8::HashMap | 55.55 (1) | 16.04 (270) |

**RandomInsertEraseStrings** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 22.79 (73) | **31.85** (73) |
| sflat::flat_hash_map 4d705e4 | **22.26** (73) | 33.05 (73) |
| absl::flat_hash_map | 25.83 (98) | 39.90 (98) |
| ankerl::unordered_dense::map | 31.15 (97) | 35.32 (97) |
| boost::unordered_flat_map 1_83 | 23.46 (153) | 33.46 (153) |
| emhash8::HashMap | 36.71 (84) | 46.34 (84) |

**knucleotide** (seconds, peak MB)

| Map | std::hash | ankerl::unordered_dense::hash |
|---|---|---|
| sflat::flat_hash_map | 2.95 (128) | 4.15 (128) |
| sflat::flat_hash_map 4d705e4 | 3.12 (128) | 3.89 (128) |
| absl::flat_hash_map | 13.44 (128) | 2.46 (128) |
| ankerl::unordered_dense::map | **1.96** (128) | **2.43** (128) |
| boost::unordered_flat_map 1_83 | 2.75 (128) | 2.70 (128) |
| emhash8::HashMap | 3.50 (126) | 4.62 (126) |
