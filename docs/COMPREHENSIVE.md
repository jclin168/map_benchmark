# All-container original suite with std::hash

This recorded profile selects the 39 adapters listed in tools/comprehensive_adapters.txt, including sflat, all three standard-library allocator variants, Boost variants, Ankerl normal/segmented, Abseil flat/node, both Folly F14 maps, Google dense/sparse, FPH, emhash, GTL/parallel-hashmap/sparsepp, Tessil, ska, robin_hood, rigtorp, jg and asteria. GTL btree_map is an ordered tree and does not use the selected hash; the report identifies it separately. Parallel-container APIs are called by one thread.

There are 39 adapters, 20 original registered cases: 17 timed and 3 diagnostic. All 780 pairs are attempted once. The fork also retains its pre-existing sflat lazy-seed adapter; it was absent from the measured upstream baseline and is not included in this recorded 39-adapter profile. The corpus sizes and loop counts are unchanged. StringHashBench is commented out upstream, Strings.cpp is #if 0, and the additional FlatMap64 cases are outside this original-suite matrix. They are not counted as skipped registered tests.

## Build

Use Linux, GCC/Clang C++17, Python 3, GNU make and CMake >=3.16. Initialize the submodules named in .gitmodules that provide the selected maps. The original checkout also has an orphan gitlink for an unused hash dependency; a blanket submodule update can fail on that path. The std::hash profile does not need that unused hash. A source tree of modular Boost is supported; it needs the header libraries for all Boost containers, not only unordered_flat_map. Recent Boost.Container is header-only; older installed Boost may also require its compiled library.

```sh
MAP_BENCH_BOOST_SOURCE_DIR=/path/to/boost ./tools/build_comprehensive.sh
ctest --test-dir build-comprehensive --output-on-failure
```

MAP_BENCH_CMAKE selects a non-default CMake executable. MAP_BENCH_ANKERL_DIR and MAP_BENCH_ABSEIL_DIR optionally override their pinned submodule paths. The build helper records per-adapter stdout/stderr, return code and elapsed time under results-comprehensive/build-logs and builds.json. It continues after a build failure. --retry-failed retries only unsuccessful targets. Use a fresh build/result directory for a different configuration.

The profile enables two opt-in CMake options:

- MAP_BENCH_UNITY_BUILD: one translation unit per executable reduces repeated parsing across the original source files. The benchmark registration identifier uses __COUNTER__ rather than __LINE__ so registrations from different included files do not collide. All 39 selected adapters use the same strategy.
- MAP_BENCH_FOLLY_MINIMAL: only F14Table.cpp, SafeAssert.cpp and ToAscii.cpp plus the platform configuration needed for F14 are built. This avoids unrelated Folly runtime dependencies; the path here is validated on Linux x86-64. The full upstream Folly build remains available when this option is off.

## Run and resume

```sh
python3 tools/run_comprehensive.py
python3 tools/summarize_comprehensive.py results-comprehensive
# After an interruption, with identical source/build/configuration:
python3 tools/run_comprehensive.py --resume
```

Each process is pinned to one allowed CPU and runs alone. Within a case, selected reference maps are first and the remaining adapters use a reproducible shuffled order. This is a single sweep, not repeated randomized timing samples. The runner saves an atomic JSON checkpoint after every pair. Resume verifies sources, binary SHA-256 values, dependencies and configuration before reusing checkpoints.

Default per-case timeout is 180 seconds. A monitor polls approximately every 5 ms and stops a process above 7 GiB RSS or 7.5 GiB total cgroup memory.current. The original environment has an independent 8 GiB cgroup hard limit and no swap. The runner does not set RLIMIT_AS or use Linux's unenforced RLIMIT_RSS. Kernel accounting and polling can overshoot a threshold. These resource limits are part of the experiment: a timeout or memory stop is not a completed measurement or a precise estimate of resources needed to finish.

The original embedded expected-result checks remain active in Release and return failure on a mismatch. Build errors, timeout, watchdog stops, invalid output, verification failure, crashes and Google reserved-sentinel exceptions are retained. Google marker exceptions can be normalized from process_error to unsupported_key_domain by the report, using preserved stderr. Some original cases can use sentinel keys; do not alter the common input for one container to hide incompatibility.

## Results and interpretation

- REPORT.zh-TW.md: coverage, methods, overview, category results and selected per-case timings.
- comparison.html: standalone interactive table, no network dependencies; select a case/container class and click column headers to sort.
- overview.csv / overview.json: every adapter's coverage, observed resource peak and optional full-coverage score.
- case_results.csv: every adapter/case cell, including pending or unsuccessful cells, peak RSS, maximum sampled VmSize and kernel VmPeak observed during polling.
- raw.csv: per-measurement parsed fields, emitted when the runner finishes.
- runs/, stdout/, stderr/: atomic per-process records and full original logs.
- environment.json: source/dependency/binary SHA values, CPU/compiler, affinity and policy.

The 15 non-constructor timed workloads are equally weighted in the throughput aggregate. For each workload all original phase seconds are summed, then speed versus std::unordered_map is combined by geometric mean. A total score requires all the same 15 workloads to pass for both the adapter and baseline. Missing/failed workloads never improve a score by silently disappearing. Full-core ranks additionally order only adapters that pass all 15 core workloads by geometric-mean workload time, with time normalized to the fastest complete adapter. This ordering remains available when the std baseline lacks a valid complete result; it uses the same 15 workloads and never drops failed cases. Category ranks similarly compare the same complete category workloads independently of baseline availability, and are shown after every adapter has attempted that category. Constructor costs and the three diagnostics are separate. Full per-workload rows remain available regardless of aggregate eligibility.

Original timer boundaries differ: random-find workloads include surrounding updates/destruction, for example. Scores describe these workloads, not isolated find nanoseconds. Default load factors, internal hash mixing and seed behavior remain part of each implementation; std::hash input can expose weaknesses for deliberately masked integer patterns. Do not reinterpret this as all hash functions or all latest library releases: exact measured revisions are in the manifest, and upstream-pinned versions vary.

Memory is whole-process workload peak RSS, including input buffers, temporaries and allocator retention. Some endMeasure calls occur after destruction; RSS at that instant is not live-map memory. Tiny cases can be dominated by startup/exec accounting. Failed-process peaks are observed lower bounds. Use per-case large-workload comparisons, not an average bytes-per-map allocation claim.

The environment is a shared VM and there is one sample per pair. Do not infer stable small advantages or confidence intervals. Resource failures and compatibility limitations are part of the coverage result, and the ordered tree / allocator / copy-on-write variants are labeled so comparisons remain interpretable.

## Validate and package this recorded run

```sh
python3 tools/finalize_comprehensive.py --wait
```

The finalizer waits for all 780 checkpoints, verifies the measured source and binary SHA-256 values and all 39 build records, then regenerates the reports. It checks the generated integration patch against both the current tree (reverse application) and a clean checkout of the base commit, and CRC-checks the result ZIP. The finalizer writes `map-benchmark-comprehensive.patch` and `map-benchmark-comprehensive.zip` in the checkout by default; `--patch` and `--bundle` select other paths. A clean checkout needs no integration patch; its source commit is recorded in the environment manifest.

This recorded sweep resumed after 391 checkpoints following environment restoration. CPU model/topology and resource limits matched, and source/binary/dependency fingerprints passed before resuming. To avoid comparing the pre-restoration sflat RandomDistinct2 sample with the other 38 post-restoration samples for that case, the finalizer performs exactly one sequential recheck of that boundary sample after the main sweep. It selects the restored sample by environment epoch, irrespective of speed. Both samples and the reason are retained in `epoch-recheck/`. There are 780 unique pairs and 781 retained process results with this recheck (excluding interrupted attempts without checkpoints); this is not a repeated timing study.

While the recorded run and finalizer are active and progress.json exists, an optional separate terminal can run `python3 tools/watch_comprehensive.py`. It prints progress every 45 seconds and refreshes snapshots after five additional checkpoints or a case change. It stops refreshing when the native matrix completes, leaving the final report to the finalizer, and exits after completion.json appears.

## Published snapshot and current fork

[Published results](results/2026-11-10-stdhash/README.md) contain the measured versions, per-case and per-phase CSV, an offline interactive table, and the complete original source/results ZIP. The measured source baseline was upstream commit 7acf847, not the fork's later PR #1. The archive includes an integration patch for that exact baseline and all dependency SHAs.

This PR preserves the fork's newer Abseil 20260817 LTS and emhash pins, its MAPS/HASHES regex options, and its lazy-seed adapter. The measured snapshot used Abseil 20250814.1 and emhash 12b336f; results do not claim to measure the newer pins. To reproduce the historical run, use the archived source patch on 7acf847 and its recorded dependency revisions. New runs against this checkout record the current source and dependency revisions in their own manifest. emhash adapters support both old and new header locations.
