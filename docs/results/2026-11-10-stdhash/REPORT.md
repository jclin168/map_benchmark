# map_benchmark: std::hash test report

Completed **780/780** configuration/case pairs.
The matrix has 39 configurations, 17 timed cases, and 3 diagnostic cases.
Each pair has one primary result. Input sizes and loop counts are unchanged.
The full matrix is complete.
The environment-boundary check repeated sflat RandomDistinct2 once. The original sample was 5.787578 s. The restored sample was 6.495098 s. The restored sample is primary. Selection uses the execution period only. Both samples are in epoch-recheck/. There are 780 unique pairs and 781 saved results. Attempts without a checkpoint are excluded.


## Scope and method

- The matrix contains all original registered cases. StringHashBench is disabled. The source disables Strings.cpp with #if 0. FlatMap64Reserved and FlatMap64Grow are separate cases.
- All hash-map configurations select std::hash. Each map keeps its internal hash mixing, load factor, allocator, and seed policy. The sflat process seed is 1. The ordered tree does not use a hash function. Parallel maps use one thread.
- The build uses GCC 14.2 and C++17. Release flags are -O3 -DNDEBUG -march=native. Each executable uses a unity build. Test registration uses __COUNTER__. F14 uses three required Folly source files.
- Each native case runs alone on a fixed CPU. The first maps use this order: sflat, std, Boost flat, Ankerl, Abseil flat, Google dense, and Google sparse. The other maps use a fixed random order. The order is not balanced across maps. Timer start and stop points differ by case. Do not interpret these times as find-only costs.
- Each phase checks its expected result. A mismatch causes failure. A stable-reference value of 0 shows unstable references.
- Each process has a 180 s limit. The RSS stop level is 7 GiB. The cgroup stop level is 7.5 GiB. The environment hard limit is 8 GiB. Swap is disabled. RLIMIT_AS is unlimited. The report keeps each failure type. Times from incomplete cases do not enter speed ranks.
- RSS covers the full process. It includes input data, temporary storage, and the allocator. Some endMeasure calls occur after map destruction. Do not use those values as live-map memory. Small tests can reflect memory used before the executable starts. Do not rank small memory differences. CSV and HTML also show virtual-address VmPeak. CSV includes the maximum sampled VmSize. Virtual address space and physical RSS are separate values. Failed-case observations are diagnostic data only.
- Each pair has one sample on a shared VM. No confidence intervals are available. Small differences do not show a stable advantage.

## All configurations

The core set has 15 timed workloads. It excludes constructors. Each workload has equal weight. First, sum all phase times in each workload. Then calculate the geometric mean. Speed/std is the geometric mean of std time divided by candidate time. This value requires all 15 workloads to pass for both maps. A value above 1 means the candidate is faster. Failed cases never disappear from the score. Constructor tests are separate. The compiler can remove empty constructor loops. Core ranks compare only maps that pass all 15 workloads. Time/best divides each complete result by the fastest complete result. A smaller value means less time. These ranks remain available when the std baseline is incomplete.

| Container | Type | Timed pass | Core pass | Core rank | Time/best | Speed/std | Highest observed RSS GiB | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| ankerl::unordered_dense::map | flat / dense hash | 17/17 | 15/15 | 1 | 1.00x | — | 1.689 | ok:20 |
| sflat::flat_hash_map | flat / dense hash | 17/17 | 15/15 | 2 | 1.22x | — | 1.215 | ok:20 |
| ankerl::unordered_dense::segmented_map | segmented dense | 17/17 | 15/15 | 3 | 1.27x | — | 1.435 | ok:20 |
| boost::unordered_flat_map 1_93 | flat / dense hash | 17/17 | 15/15 | 4 | 1.38x | — | 1.596 | ok:20 |
| folly::F14ValueMap | flat / dense hash | 17/17 | 15/15 | 5 | 1.62x | — | 1.510 | ok:20 |
| boost::unordered_flat_map no SSE 1_93 | flat / dense hash | 17/17 | 15/15 | 6 | 1.70x | — | 1.596 | ok:20 |
| gtl::parallel_flat_hash_map | flat / dense hash | 17/17 | 15/15 | 7 | 1.79x | — | 1.162 | ok:20 |
| robin_hood::unordered_flat_map | flat / dense hash | 17/17 | 15/15 | 8 | 1.80x | — | 1.689 | ok:20 |
| ska::flat_hash_map | flat / dense hash | 17/17 | 15/15 | 9 | 1.83x | — | 4.502 | ok:20 |
| robin_hood::unordered_node_map | node / allocator variant | 17/17 | 15/15 | 10 | 1.96x | — | 2.252 | ok:20 |
| ska::bytell_hash_map | flat / dense hash | 17/17 | 15/15 | 11 | 2.07x | — | 1.689 | ok:20 |
| boost::unordered_node_map 1_93 | node / allocator variant | 17/17 | 15/15 | 12 | 2.08x | — | 4.010 | ok:20 |
| folly::F14NodeMap | node / allocator variant | 17/17 | 15/15 | 13 | 2.30x | — | 4.379 | ok:20 |
| gtl::node_hash_map | node / allocator variant | 17/17 | 15/15 | 14 | 2.61x | — | 4.587 | ok:20 |
| gtl::parallel_node_hash_map | node / allocator variant | 17/17 | 15/15 | 15 | 2.82x | — | 4.143 | ok:20 |
| std::unordered_map PoolAllocator | node / allocator variant | 17/17 | 15/15 | 16 | 3.23x | — | 2.231 | ok:20 |
| boost::multi_index::hashed_unique | hashed multi-index | 17/17 | 15/15 | 17 | 4.64x | — | 3.698 | ok:20 |
| absl::flat_hash_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 1.689 | ok:14, timeout:6 |
| absl::node_hash_map | node / allocator variant | 11/17 | 9/15 | — | — | — | 4.590 | ok:14, timeout:6 |
| asteria::cow_hashmap | copy-on-write hash | 9/17 | 7/15 | — | — | — | ≥5.499 | ok:12, timeout:6, verification_failed:2 |
| boost::unordered_map 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 3.744 | ok:19, timeout:1 |
| boost::unordered_map PoolAllocator 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 2.273 | ok:19, timeout:1 |
| boost::unordered_map unsynchronized_pool_resource 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 2.364 | ok:19, timeout:1 |
| fph::DynamicFphMap | flat / dense hash | 14/17 | 13/15 | — | — | — | ≥1.861 | ok:17, timeout:3 |
| fph::MetaFphMap | flat / dense hash | 15/17 | 13/15 | — | — | — | ≥1.136 | ok:18, timeout:2 |
| google::dense_hash_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| google::sparse_hash_map | flat / dense hash | 10/17 | 8/15 | — | — | — | 0.870 | ok:13, timeout:7 |
| gtl::btree_map | ordered tree | 11/17 | 9/15 | — | — | — | ≥1.024 | ok:14, timeout:6 |
| gtl::flat_hash_map | flat / dense hash | 16/17 | 14/15 | — | — | — | 1.689 | ok:19, timeout:1 |
| spp::sparse_hash_map | flat / dense hash | 12/17 | 10/15 | — | — | — | 1.215 | ok:15, timeout:5 |
| jg::dense_hash_map | flat / dense hash | 13/17 | 11/15 | — | — | — | 3.002 | ok:16, timeout:4 |
| emhash7::HashMap | flat / dense hash | 13/17 | 11/15 | — | — | — | 2.275 | ok:16, timeout:4 |
| emhash8::HashMap | flat / dense hash | 13/17 | 11/15 | — | — | — | 1.738 | ok:16, timeout:4 |
| rigtorp::HashMap | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| std::unordered_map | node / allocator variant | 16/17 | 14/15 | — | — | — | 3.704 | ok:19, timeout:1 |
| std::unordered_map unsynchronized_pool_resource | node / allocator variant | 16/17 | 14/15 | — | — | — | ≥2.243 | ok:19, timeout:1 |
| tsl::hopscotch_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| tsl::robin_map | flat / dense hash | 11/17 | 9/15 | — | — | — | ≥7.000 | ok:14, rss_watchdog:1, timeout:5 |
| tsl::sparse_map | flat / dense hash | 13/17 | 11/15 | — | — | — | 1.104 | ok:16, timeout:4 |

## Diagnostic results

| Diagnostic | Processes passed | Description |
|---|---:|---|
| ShowHash | 39/39 | 1 distinct output values. These values check the selected hash adapter. |
| ShowHashString | 39/39 | 1 distinct output values. These values check the selected hash adapter. |
| ShowIsStableReference | 39/39 | 15 configurations with stable references; 24 with unstable references |

The reference test observes 10,000 insertions. It does not establish an API guarantee for other operations. A value of 0 is valid diagnostic output. See stable_reference_diagnostic in overview.csv.

## Results by test group

Each group ranks maps that pass the same group workloads. Ranks use geometric-mean time. Ranks appear after all configurations have attempted that group. Speed/std stays empty when the std baseline does not pass the group.

| Group | Cases | Complete maps | Fastest map | Speed/std | sflat rank |
|---|---:|---:|---|---:|---:|
| construct | 2 | — | Constructor cases are separate. No aggregate ratio. | — | — |
| copy_reinsert | 2 | 38 | ankerl::unordered_dense::map | 10.18x | 7/38 |
| iteration | 1 | 39 | emhash8::HashMap | 27.56x | 9/39 |
| integer_updates | 3 | 18 | sflat::flat_hash_map | 8.53x | 1/18 |
| integer_find | 3 | 24 | boost::unordered_node_map 1_93 | — | 11/24 |
| string | 3 | 37 | ankerl::unordered_dense::map | 2.64x | 4/37 |
| applications | 3 | 31 | ankerl::unordered_dense::map | 3.09x | 4/31 |

## sflat time difference by workload

Each workload compares maps that pass the full case. Ranks appear after all 39 configurations have attempted that case. The time ratio is sflat time divided by the fastest time. A value above 1 means sflat takes more time. Use these differences to select profiling tests. They do not identify a cause.

| Workload | Maps passed | sflat rank | sflat time s | Fastest map | sflat time / fastest time |
|---|---:|---:|---:|---|---:|
| Copy | 39/39 | 14/39 | 6.4598 | tsl::sparse_map | 6.28x |
| GameOfLife_growing | 32/39 | 4/32 | 3.0875 | ankerl::unordered_dense::map | 1.15x |
| GameOfLife_stabilizing | 31/39 | 4/31 | 8.5018 | ankerl::unordered_dense::map | 1.44x |
| AccidentallyQuadratic | 38/39 | 1/38 | 0.8591 | sflat::flat_hash_map | 1.00x |
| IterateIntegers | 39/39 | 9/39 | 5.7492 | emhash8::HashMap | 8.60x |
| RandomDistinct2 | 34/39 | 1/34 | 6.4951 | sflat::flat_hash_map | 1.00x |
| InsertHugeInt | 34/39 | 3/34 | 15.7713 | rigtorp::HashMap | 1.02x |
| RandomInsertErase | 22/39 | 2/22 | 13.1131 | boost::unordered_flat_map 1_93 | 1.19x |
| RandomInsertEraseStrings | 37/39 | 1/37 | 24.6775 | sflat::flat_hash_map | 1.00x |
| knucleotide | 39/39 | 9/39 | 4.4552 | gtl::flat_hash_map | 1.37x |
| RandomFindString | 38/39 | 17/38 | 30.8114 | boost::unordered_node_map 1_93 | 1.42x |
| RandomFindString_1000000 | 37/39 | 3/37 | 37.8273 | ankerl::unordered_dense::map | 1.12x |
| RandomFind_200 | 28/39 | 21/28 | 46.2458 | fph::MetaFphMap | 1.77x |
| RandomFind_2000 | 25/39 | 17/25 | 37.9264 | ska::flat_hash_map | 1.48x |
| RandomFind_500000 | 24/39 | 3/24 | 52.4890 | boost::unordered_node_map 1_93 | 1.04x |

## Workload times for selected maps

Times appear only for complete cases with correct results. Failed cases show their status. CSV and HTML contain all 39 configurations and phase data.

| Workload | sflat_flat_hash_map | boost_unordered_flat_map | ankerl_unordered_dense | abseil_flat_hash_map | ktprime_hash_table8 | std_unordered_map |
|---|---:|---:|---:|---:|---:|---:|
| CtorDtorEmptyMap | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0022 | 0.0000 |
| CtorDtorSingleEntryMap | 0.4614 | 0.1793 | 0.1773 | 0.0000 | 0.0851 | 0.1998 |
| Copy | 6.4598 | 3.3132 | 1.5451 | 9.2028 | 1.1013 | 15.5716 |
| GameOfLife_growing | 3.0875 | 2.8444 | 2.6797 | timeout | 49.8443 | 10.2252 |
| GameOfLife_stabilizing | 8.5018 | 7.5898 | 5.9141 | timeout | 69.2910 | 18.3568 |
| AccidentallyQuadratic | 0.8591 | 15.2172 | 1.1761 | 28.9009 | 1.9810 | 12.1042 |
| IterateIntegers | 5.7492 | 6.0711 | 0.6710 | 15.1371 | 0.6682 | 18.4195 |
| RandomDistinct2 | 6.4951 | 10.2870 | 14.0084 | timeout | 15.1970 | 131.4227 |
| InsertHugeInt | 15.7713 | 15.6074 | 26.4980 | 38.3811 | 27.3963 | 137.3160 |
| RandomInsertErase | 13.1131 | 11.0273 | 14.3737 | timeout | timeout | 46.1516 |
| RandomInsertEraseStrings | 24.6775 | 28.1853 | 27.8784 | 28.9254 | 35.4769 | 60.9822 |
| knucleotide | 4.4552 | 4.1899 | 3.4345 | 20.9308 | 4.9209 | 8.5848 |
| RandomFindString | 30.8114 | 25.1017 | 24.3299 | 27.3209 | 25.8035 | 55.2534 |
| RandomFindString_1000000 | 37.8273 | 38.3049 | 33.7284 | 39.5975 | 42.3416 | 125.0060 |
| RandomFind_200 | 46.2458 | 28.8344 | 43.2009 | 111.2294 | timeout | 57.4233 |
| RandomFind_2000 | 37.9264 | 28.6647 | 32.8283 | timeout | timeout | 58.5418 |
| RandomFind_500000 | 52.4890 | 72.7596 | 57.3560 | timeout | timeout | timeout |

## Memory watchdog stops

These observations come from stopped workloads. They do not show map size after the target entry count. They do not enter speed or memory-efficiency ranks. VmPeak measures virtual address space. RSS measures resident memory.

| Map | Workload | Stop reason | Process time s, incomplete | Observed RSS GiB | Observed VmPeak GiB | Completed phases |
|---|---|---|---:|---:|---:|---:|
| tsl::robin_map | RandomFind_500000 | rss_watchdog | 47.83 | 7.0001 | 9.0061 | 1 |

## Integer-find phases at timeout

For each hit rate, the source tests low 32 bits first and high 32 bits second. The completed phase count identifies the next incomplete phase. It does not give the time required to finish that phase. These results apply to std::hash and the original masked inputs. Other hash settings need separate tests.

| Workload | Timeouts | Next phase: high 32 bits | Next phase: low 32 bits |
|---|---:|---:|---:|
| RandomFind_200 | 11 | 11 | 0 |
| RandomFind_2000 | 14 | 14 | 0 |
| RandomFind_500000 | 14 | 12 | 2 |

## Tests for further profiling

See the [200-insertion phase comparison](diagnostics/sflat_find200_phases.md). Both sflat and Boost flat passed this case. The difference is larger at a 25% hit rate. Times are close at high hit rates. This single sample does not identify a cause.

## Confirmed fault in a recorded dependency

asteria-cow_hashmap returns 167249 for the R-pentomino in GameOfLife_stabilizing. The expected value is 116. InsertHugeInt leaves 59,122,781 entries after clear. The expected count is 0. A separate test uses the native rocket::cow_hashmap API. It calls reserve(64), inserts key=1, and calls clear(). The size stays at 1. find(1) still finds the key. In this revision, clear() uses size() for the bucket range. It leaves entries outside that range.

This fault affects cases that clear and reuse a map. Times and memory values describe incorrect execution. Do not use them as valid workload costs. Original timeout and verification_failed states remain in the data. This finding applies only to the revision in the manifest.

- Native API test: [source](diagnostics/asteria_clear.cpp), [output](diagnostics/asteria_clear.txt), and [revision data](diagnostics/asteria_clear.json).

## Files

- [Interactive table](comparison.html): download and open it locally. Select a case and map type. Select a column to sort the data.
- Data files: [overview.csv](overview.csv), [case_results.csv](case_results.csv), [environment.json](environment.json), [compile-flags.json](compile-flags.json), and [builds.json](builds.json).
- runs/ contains JSON checkpoints. stdout/ and stderr/ contain original process output. build-logs/ contains adapter build logs. These folders are in the complete-run archive.
- [Resume record](resumptions.json): 391 checkpoints survived the environment interruption. The restored environment had the same CPU model, topology, and resource limits. This is one matrix across execution periods. It is not an independent repeat.
- The runner writes raw.csv when all processes finish. It retains failed and incomplete records for diagnosis. Ranks use complete cases with correct results.
- docs/COMPREHENSIVE.md gives build, resume, and reproduction instructions.
