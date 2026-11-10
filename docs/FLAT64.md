# Six-map flat hash profile

The profile adds `sflat::flat_hash_map`, `google::dense_hash_map` and `google::sparse_hash_map` adapters to the existing map/hash matrix. It compares them with Boost unordered_flat_map, Ankerl unordered_dense and Abseil flat_hash_map. Original benchmark sources remain available and compile into each selected executable.

The controlled `FlatMap64Reserved` and `FlatMap64Grow` cases run through the original `BenchRegistry`, `Bench` timer and RSS functions. They extend the suite with common uint64_t keys/values and a memory baseline that excludes the input vector. These are additional cases, not a claim that every original suite workload was executed.

## Dependencies and build

Initialize the required submodules without recursing into unrelated test dependencies:

```sh
git submodule update --init \
  external/jclin168__sflat_hash_map external/google__sparsehash \
  external/martinus__unordered_dense external/abseil__abseil-cpp
```

Use installed Boost >= 1.81, or provide a modular Boost source tree (including its needed header submodules) with `MAP_BENCH_BOOST_SOURCE_DIR`. Google sparsehash's configure script and GNU make generate only its small platform config header; no library installation is needed. On Windows the supplied sparsehash Windows config is used. Build tooling and measured results in this change are validated on Linux.

```sh
MAP_BENCH_BOOST_SOURCE_DIR=/path/to/boost ./tools/build_flat64.sh
ctest --test-dir build-flat64 --output-on-failure
python3 tools/run_flat64.py
python3 tools/summarize_flat64.py results-flat64
```

Override the CMake executable using `MAP_BENCH_CMAKE` if necessary. In the cloud workspace it is `/workspace/build-tools/cmake/data/bin/cmake`; the Boost source tree is `/workspace/deps/boost`. Build jobs default to two and can be set with `MAP_BENCH_BUILD_JOBS`.

CMake options:

- `MAP_BENCH_MAPS`: semicolon-separated adapter directory names; empty retains the full map matrix.
- `MAP_BENCH_HASHES`: semicolon-separated hash directory names; empty retains all hashes.
- `MAP_BENCH_ANKERL_DIR`, `MAP_BENCH_ABSEIL_DIR`: optional source overrides, defaulting to their pinned submodules.
- `MAP_BENCH_BOOST_SOURCE_DIR`: optional Boost source tree for headers. The initial six-map profile does not need compiled Boost libraries. Other allocator adapters may require Boost.Container as before.
- `MAP_BENCH_SFLAT_SEED`: optional deterministic process seed. The provided profile uses 1; general builds leave the library default unchanged.
- `MAP_BENCH_USE_GOLD`: opt-in use of gold; the default system linker works without gold installed.

## Running

```sh
# Smaller validation run; all six maps, each in a fresh process.
python3 tools/run_flat64.py --sizes 1000 --repeats 1 --out results-flat64-smoke

# Main profile: default 1M, 10M, 100M; three independent processes per case.
python3 tools/run_flat64.py --sizes 1000000 10000000 100000000 --repeats 3

# Two original upstream cases, one process each, as compatibility checks.
python3 tools/run_flat64.py --native-only --out results-flat64-native

# Original cases remain selectable.
build-flat64/bench_sflat_flat_hash_map__std_hash --list
build-flat64/bench_sflat_flat_hash_map__std_hash Copy
```

The runner pins each process to one allowed CPU, randomizes map/case order within each size/repetition, runs one process at a time, records dependency SHAs and environment metadata, and saves raw semicolon output plus parsed per-process checkpoints. It aborts on nonzero status, malformed rows or benchmark verification failure. `--resume` can reuse completed checkpoints from an identical build. Default per-process timeout is 1800 seconds.

`FlatMap64Reserved` measures reserve+insert, random-order successful find, and unsuccessful find. `FlatMap64Grow` measures insertion without reserve. Each find phase queries N keys. Key generation/shuffling and RSS reads are outside timers. Insert uses the value_type insert API across all six libraries. The native Google API is accessed only after the common corpus has excluded its reserved keys. Hit count, size, value checksum and zero false hits are checked. This profile does not enable the experimental sflat batch patch or modify default load factors/THP behavior.

## Memory output

Without `MAP_BENCH_EXTRA_MEMORY`, the first eight original output fields remain unchanged. With `MAP_BENCH_EXTRA_MEMORY=1`, append:

1. Current RSS in MiB.
2. Current RSS minus the selected baseline in MiB.
3. Cumulative process peak RSS in MiB.
4. Baseline current RSS in MiB.
5. Cumulative peak RSS minus that baseline, clamped at zero, in MiB.

For the controlled cases, the baseline is captured after filling the 8N-byte input vector and before map construction. The primary steady-memory comparison is field 2 at the insert measurement, while the map is alive. The growth comparison uses field 5 as a peak-memory estimate. For original workloads, the default baseline is benchmark entry; their allocations and object lifetimes differ, so the delta is not necessarily memory for one map.

The original eighth field remains the cumulative peak increase relative to benchmark entry, including input buffers in the controlled cases. It must not be labeled steady map memory. Current RSS uses Linux smaps_rollup when available, falling back to statm; peak uses getrusage. These kernel accounting methods can differ slightly. Peak-minus-baseline is an estimate, includes runtime/allocator overhead, and is not an isolated per-allocation profiler. At tiny sizes, process startup peaks can dominate. There is no memory prediction for 1B from this run.

## Google adapter restrictions

Dense hash reserves two keys, sparse hash reserves one deleted marker. Integral markers use max()/max()-1; string markers use explicit unlikely non-ASCII marker strings. The controlled uint64_t corpus excludes both integral markers for every map and generates disjoint missing keys via a bijection. This avoids bias from duplicate keys and makes the input domain identical.

The compatibility wrapper sets native sentinels, translates reserve to resize and emplace to native value_type insert, and rejects insertion of reserved keys. It is intended for the benchmark's integral/string key types, not as a general drop-in unordered_map replacement. Original workloads that produce a reserved key cannot be run unchanged through Google's native sentinel-based table. The two executed original cases passed verification for all six adapters; that is not a claim that all original workloads avoid the markers.

## Reproducibility and interpretation

The initial run uses sflat f163c3d353e7, Ankerl 5.3.3 (7c58a8b7a48e), Abseil LTS 20250814.1 (d38452e1ee03), sparsehash 2.0.4 (f93c0c69e959), and Boost 1.93 development headers. Exact actual source SHAs, build flags, CPU, seed and memory policy are recorded in the result manifest. The Ankerl/Abseil submodule revisions are updated to match this comparison.

Report medians of independent processes and their min/max ranges. Internal phases from one process are not independent repetitions. Results apply to this uniform integer corpus and platform; strings, adversarial hashes, mixed updates and the remaining original suite cases can rank differently. A shared VM can produce large timing outliers; do not infer a stable advantage from small differences. All first-pass measurements are performed, not extrapolated from previous tables.

## Streaming 500M no-reserve probe

`tools/insert_stream.cpp` is an additional insert-only executable using the same adapters, hash, compiler flags and dependency libraries from `build-flat64`. It generates unique keys on demand, excludes Google's markers, inserts native value_type pairs without reserve, and records RSS/peak every 10M inserts plus completion/allocation failure. It does not allocate an input vector or run find. Its elapsed time includes key generation/checkpoint overhead and is not directly comparable to FlatMap64Grow timings.

```sh
# Large-memory machine: no artificial address-space cap. Keep adequate RAM available.
python3 tools/run_insert_stream.py --entries 500000000 --limit-gib 0
python3 tools/summarize_insert_stream.py results-flat64-500m

# Reproduce the diagnostic performed on this 8 GiB environment:
python3 tools/run_insert_stream.py --entries 500000000 --limit-gib 7
```

The script builds separate executables under `build-flat64-stream`, preserving the earlier benchmark binaries. `--limit-gib` sets RLIMIT_AS (virtual address space), not resident RAM. Default 7 GiB is a protective diagnostic budget for this environment. mmap reservations and simultaneous old/new arrays count even when their pages are not resident. Partial insertion counts and peaks under this limit must not be labeled 500M memory or interpreted as maximum capacity under an equivalent physical-RAM budget. Google native allocation failures can terminate with a signal; in that case only the last completed checkpoint is available and is a lower bound. A complete 500M comparison requires adequate RAM; results in results-flat64-500m document whether each map actually completed. A run without the cap should be performed on a larger machine, not this 8 GiB environment.

## 300M with resident-memory monitoring and unlimited virtual address space

```sh
python3 tools/run_insert_stream.py --entries 300000000 --limit-gib 0 \
  --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out results-flat64-300m-rss
python3 tools/summarize_insert_rss.py results-flat64-300m-rss
```

`--limit-gib 0` leaves RLIMIT_AS unlimited. This mode monitors actual `/proc/PID/status` VmRSS and VmHWM every approximately 5 ms and kills the child when process RSS exceeds 7 GiB, or total cgroup memory.current exceeds 7.5 GiB. The cgroup itself retains its 8 GiB hard cap. The latter watchdog leaves space for other processes and page cache, and can fire slightly before the process RSS threshold. This is a sampled watchdog, not a kernel hard RSS cap; Linux RLIMIT_RSS does not enforce resident memory limits. Sampled peaks may slightly exceed thresholds and are lower bounds for killed processes.

For completed runs, the report shows live-map RSS after all 300M insertions, excluding process baseline, plus cumulative peak. For incomplete runs the final 300M RSS is unavailable; the last confirmed 10M checkpoint is a lower bound on progress, and the monitor's peak is a lower bound on memory reached. Do not substitute either for the memory required to complete 300M. These are single-process memory measurements, one run per adapter, not a repeat-based timing comparison. The runner records inherited RLIMIT_AS, stop reasons, observed process/cgroup peaks, hashes, raw checkpoints and before/after cgroup OOM event counters. The original benchmark executables remain unchanged.

## 250M virtual address space and RSS

```sh
python3 tools/run_insert_stream.py --entries 250000000 --limit-gib 0 \
  --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out results-flat64-250m-vm-rss
python3 tools/summarize_insert_vm_rss.py results-flat64-250m-vm-rss
```

The streaming executable appends `vmsize_bytes`, `vmpeak_bytes`, and `baseline_vmsize_bytes` to its original six CSV fields. These are Linux /proc/self/status values, sampled while the map remains alive. The watchdog also records virtual high-water marks and a paired VmSize/RSS snapshot immediately before killing an over-budget process. Completed maps are reported after exactly 250M inserts; incomplete maps are reported separately at their stop snapshot and do not have a completed 250M measurement.

This report uses absolute whole-process VmSize/RSS, preserving their baselines in raw CSV. This differs from the baseline-subtracted map RSS column in earlier reports by the small process startup footprint. VmSize measures currently mapped virtual address space; VmPeak is its historical maximum. Neither is committed physical memory. The virtual and resident peaks may occur at different times. RLIMIT_AS remains unlimited; physical-memory watchdog settings are the same as the 300M run. Source and binary hashes for the new measurement executable are stored alongside the results, and older result directories retain their own measured source snapshots.
