# C++ hash map benchmark: std::hash snapshot (2026-11-10 UTC)

This snapshot compares **39 container/configuration adapters × std::hash × 20 original registered cases**: 17 timed workloads and three diagnostics, 780 unique pairs, using the original corpus sizes and loop counts. It includes sflat::flat_hash_map, Ankerl unordered_dense, Boost unordered_flat_map, Abseil flat_hash_map, Google dense/sparse hash maps, emhash7/8, Folly F14 and the other upstream adapters.

**691 passed, 86 timed out, one exceeded the RSS watchdog and two failed expected-result verification.** All 39 builds succeeded. No kernel OOM kill occurred. sflat passed all 20 cases. Among the 17 configurations passing the same 15 non-constructor timed workloads, Ankerl dense ranked first and sflat second. Failed/missing cases never improve a score by disappearing.

| Full-core rank | Container | Geometric-mean time relative to Ankerl |
|---:|---|---:|
| 1 | Ankerl unordered_dense | 1.00x |
| 2 | sflat flat_hash_map | 1.22x |
| 3 | Ankerl segmented_map | 1.27x |
| 4 | Boost unordered_flat_map | 1.38x |
| 5 | Folly F14ValueMap | 1.62x |

Each workload has equal weight; original phase times are summed within each workload. The std::unordered_map baseline timed out on RandomFind_500000, so an aggregate speed ratio versus std is not reported.

## Example: original InsertHugeInt workload

These seconds include the original **100M integer insertion attempts and clear**, not isolated insertion ns/op. RSS is the whole-process workload peak, including temporaries and allocator retention, not live-map allocation bytes or exactly 100M distinct entries.

| Container | Timed seconds | Peak RSS GiB |
|---|---:|---:|
| sflat | 15.77 | 1.215 |
| Boost flat | 15.61 | 1.596 |
| Ankerl dense | 26.50 | 1.689 |
| Abseil flat | 38.38 | 1.689 |
| Google dense | 24.35 | 3.002 |
| Google sparse | 129.33 | 0.870 |
| emhash8 | 27.40 | 1.738 |
| std::unordered_map | 137.32 | 3.704 |

## Reports and raw data

- [Full report in English](REPORT.md): every adapter, coverage, category ranks, workload times and profiling targets.
- [Interactive table](comparison.html): download and open locally; select a workload/class and sort time, RSS or virtual-address VmPeak.
- [All-container overview CSV](overview.csv), [all 780 case cells](case_results.csv), [original phase CSV](raw.csv).
- [Complete run ZIP](complete-run.zip): all checkpoints, stdout/stderr, build logs, source patch, diagnostics and reproduction instructions. Paths such as runs/ and stdout/ in the report refer to this archive.
- [Environment, dependency pins and source/binary SHA-256](environment.json), [actual compilation flags](compile-flags.json), [build records](builds.json), [publication validation](publication-validation.json).
- [Environment restoration record](resumptions.json), [boundary sample recheck](epoch-recheck/record.json). There are 781 retained case results including one predeclared boundary recheck; the restored sample is primary irrespective of speed, and both samples are preserved.
- [Reproduction/build profile](../../COMPREHENSIVE.md). SHA256SUMS covers the published files.

## Scope and interpretation

Linux x86-64, Xeon Platinum 8573C, GCC 14.2, C++17, -O3 -DNDEBUG -march=native, one native case at a time pinned to CPU 0. The environment had an 8 GiB cgroup limit and no swap; each case had a 180 s timeout, 7 GiB RSS and 7.5 GiB cgroup watchdogs. RLIMIT_AS was unlimited. Virtual address space is reported separately from RSS.

One sample on a shared VM does not establish stable small differences or confidence intervals. Constructors can be optimized away and are excluded from the aggregate. Timer boundaries differ across original workloads. std::hash is the common configured hasher; containers retain internal mixing, load factors, allocators and seed policies. Masked integer patterns can stress weak hash distributions. The ordered B-tree ignores hash selection, and parallel containers were exercised through single-threaded APIs.

The measured source baseline was upstream **7acf847**, with sflat **f163c3d**, Abseil **d38452e1 (20250814.1)**, Ankerl **7c58a8b7**, and emhash **12b336f**; exact revisions for all dependencies are in the manifest. This fork also contains a lazy-seed sflat adapter and newer Abseil/emhash pins from its earlier PR. Those newer configurations were not part of this recorded snapshot. Use the original source patch and dependency revisions in the archive to reproduce the historical measurements.

The two verification failures are in the pinned asteria cow_hashmap revision; a native-API clear() reproduction is included. Tessil robin_map exceeded 7 GiB RSS during RandomFind_500000; this incomplete run is not a completed 500K-entry map footprint. Failed-process resource observations are diagnostic data and are excluded from efficiency rankings.

The report text and labels use English. Numerical records, process output, and measured source hashes are unchanged.
