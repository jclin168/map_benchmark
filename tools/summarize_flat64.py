#!/usr/bin/env python3
"""Aggregate independent map_benchmark flat64 processes and preserve min/max."""
import csv,json,statistics,collections,sys,os
from pathlib import Path
from run_flat64 import ADAPTERS
LABELS={'sflat_flat_hash_map':'sflat','boost_unordered_flat_map':'Boost flat','ankerl_unordered_dense':'Ankerl','abseil_flat_hash_map':'Abseil flat','google_dense_hash_map':'Google dense','google_sparse_hash_map':'Google sparse'}
def median(rows,key):return statistics.median(float(r[key]) for r in rows)
def summarize(out):
    manifest=json.loads((out/'environment.json').read_text())
    rows=list(csv.DictReader((out/'raw.csv').open()))
    if manifest.get('native_only'):raise ValueError('Use the controlled profile output directory')
    sizes=manifest['sizes'];repeats=manifest['repeats']
    assert len(rows)==len(ADAPTERS)*len(sizes)*repeats*4
    groups=collections.defaultdict(list)
    for r in rows:groups[r['adapter'],int(r['entries']),r['test'],r['measurement_id']].append(r)
    for v in groups.values():assert len(v)==repeats
    for n in sizes:
        hits=[r for r in rows if int(r['entries'])==n and r['measurement_id']=='02']
        assert len({r['actual_result'] for r in hits})==1
    summaries=[]
    for a in ADAPTERS:
        for n in sizes:
            rs=groups[a,n,'FlatMap64Reserved','01'];hit=groups[a,n,'FlatMap64Reserved','02'];miss=groups[a,n,'FlatMap64Reserved','03'];grow=groups[a,n,'FlatMap64Grow','01']
            item={'adapter':a,'map':LABELS[a],'entries':n,'processes_per_case':repeats}
            for name,data,key in [('insert_s',rs,'runtime_s'),('hit_s',hit,'runtime_s'),('miss_s',miss,'runtime_s'),('steady_rss_mib',rs,'rss_minus_input_baseline_mib'),('reserved_peak_mib',rs,'rss_peak_minus_input_baseline_mib'),('grow_s',grow,'runtime_s'),('grow_steady_mib',grow,'rss_minus_input_baseline_mib'),('grow_peak_mib',grow,'rss_peak_minus_input_baseline_mib')]:
                values=[float(r[key]) for r in data];item[name]=statistics.median(values);item[name+'_min']=min(values);item[name+'_max']=max(values)
            item['steady_bytes_per_entry']=item['steady_rss_mib']*1048576/n
            summaries.append(item)
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=summaries[0]);w.writeheader();w.writerows(summaries)
    lookup={(r['adapter'],r['entries']):r for r in summaries}
    commits=manifest['commits']
    cpu_name=next((line.split(':',1)[1].strip() for line in manifest['cpu'].splitlines() if line.startswith('Model name:')),'See environment.json')
    compiler_name=manifest['compiler'].splitlines()[0]
    seed_list=', '.join(str(42+i) for i in range(repeats))
    report=f'''# map_benchmark: six flat hash maps

The source base is martinus/map_benchmark commit {commits['map_benchmark'][:12]}.
This build adds sflat, Google dense, and Google sparse adapters.
The controlled 64-bit cases use the existing BenchRegistry and timer.
Each target builds all original benchmark source files.
This run tests the controlled profile and two original cases for compatibility.
It does not claim to execute every original workload.

## Test conditions

- CPU: {cpu_name}. Compiler: {compiler_name}. Flags: C++17, -O3 -DNDEBUG -march=native.
- Each map selects std::hash. Internal hash mixing, default load factor, allocator, and THP behavior remain unchanged.
- The sflat process seed is SFLAT_PROCESS_SEED=1. The earlier experimental patch is not applied.
- Keys and values are uint64_t. Unique keys have a random distribution. All maps use the same inputs and queries.
- Inputs exclude two Google marker keys. Disjoint parts of one bijection produce inserted keys and missing keys.
- Each map/size/case has {repeats} independent process samples. One benchmark process runs at a time on a fixed CPU.
- Map and case order are randomized. Query shuffle seeds are {seed_list}.
- Reserved tests call reserve(N), perform N native value_type inserts, then perform N hits and N misses in shuffled order.
- Grow tests insert N entries into an empty map without reserve.
- Input generation, shuffle, RSS reads, and destruction are outside these timers. Build time includes construction, reserve, and page faults.
- The Google native API has no emplace or reserve. General adapters provide these interfaces.
- The controlled profile uses validated keys with native Google insert/find calls. This excludes adapter marker-check costs from those timed calls.
- The memory limit is 8 GiB. THP is madvise. environment.json records CPU, compiler, revisions, and build flags.

## Revisions

'''
    for name,sha in commits.items():report+=f'- {name}: `{sha}`\n'
    report+='''
The recorded versions are Ankerl 5.3.3, Abseil LTS 20250814.1, Google sparsehash 2.0.4, and Boost 1.93 development headers.
The sflat revision is shown above. Load factors and allocators are unchanged.

## Reserved time and resident memory

Times are medians from independent processes. The unit is seconds.
RSS uses MiB, where one MiB is 2^20 bytes.
RSS is read after insertion while the map is alive.
The input key vector and process baseline are subtracted.
RSS includes the allocator, page rounding, and some initial page use.
It is not an exact count of logical allocation bytes.

'''
    for n in sizes:
        report+=f'### {n:,} entries\n\n| Map | reserve+insert s | find hit s | find miss s | Resident RSS MiB |\n|---|---:|---:|---:|---:|\n'
        for a in ADAPTERS:
            r=lookup[a,n];report+=f"| {LABELS[a]} | {r['insert_s']:.4f} | {r['hit_s']:.4f} | {r['miss_s']:.4f} | {r['steady_rss_mib']:.1f} |\n"
        report+='\n'
    report+='''## Build without reserve and observed peak

The peak is process ru_maxrss minus current RSS after input preparation.
This is an estimate of the build peak. It is not an allocation profile.
Original fields also retain absolute current RSS and peak RSS.

| Entries | Map | Insert without reserve s | Final RSS MiB | Estimated peak MiB |
|---|---|---:|---:|---:|
'''
    for n in sizes:
        for a in ADAPTERS:
            r=lookup[a,n];report+=f"| {n:,} | {LABELS[a]} | {r['grow_s']:.4f} | {r['grow_steady_mib']:.1f} | {r['grow_peak_mib']:.1f} |\n"
    report+='''
## Memory interpretation

The original Bench column eight gives the cumulative peak increase from the start of the benchmark.
In the new cases, that value also includes the input array.
Do not use it as resident memory for one map.
The new fields retain current RSS, input baseline, RSS minus baseline, absolute peak, and peak minus baseline.

The primary memory comparison uses RSS after insertion minus the baseline.
Growth peaks include old/new tables and memory retained by the allocator.
Each lookup phase also records memory.
smaps_rollup and getrusage use different kernel accounting methods. Small differences can occur.
Process startup can affect small-test peaks. Do not extrapolate those peaks.

## Original-case compatibility checks

All six maps passed the adapter CTests.
These tests cover integer and string keys, duplicate insertions, find, copy, erase, iteration, clear, and Google marker rejection.
The 1000-entry check completed 12 processes and 24 measurements.
It also checked that output without extra-memory mode keeps the original eight columns.

Each map also executed CtorDtorSingleEntryMap and AccidentallyQuadratic once.
Those results are single samples. They are separate from the three-repeat medians and the controlled 64-bit workloads.
They keep the original inputs and expected-result checks.
The remaining original workloads were not all executed in this profile.

'''
    native=out.parent/'results-flat64-native'/'raw.csv'
    if native.exists():
        nr=list(csv.DictReader(native.open()));assert len(nr)==24
        ng=collections.defaultdict(list)
        for r in nr:ng[r['adapter'],r['test'],r['measurement_id']].append(r)
        report+='| Map | 5M single-entry ctor/dtor s | 10M int insert s | iterate s | iterate-and-copy s |\n|---|---:|---:|---:|---:|\n'
        for a in ADAPTERS:
            get=lambda case,phase:float(ng[a,case,phase][0]['runtime_s'])
            report+=f"| {LABELS[a]} | {get('CtorDtorSingleEntryMap','01'):.4f} | {get('AccidentallyQuadratic','01'):.4f} | {get('AccidentallyQuadratic','02'):.4f} | {get('AccidentallyQuadratic','03'):.4f} |\n"
    report+='''
## Limits and reproduction

- The VM is shared. Timing can vary. summary.csv retains minimum and maximum values.
- Plot error bars show minimum and maximum values. They are not confidence intervals. Do not infer stable small advantages.
- This profile uses std::hash and uniformly distributed integer keys. Strings, other hash functions, and mixed updates need separate tests.
- Other original cases can give different ranks.
- Google dense and sparse maps reserve marker keys. Controlled inputs exclude them. The general wrapper rejects marker insertions.
- Other original workloads can include marker keys.
- A successful 100M test does not establish a 1B result. This run does not extrapolate 1B time.
- See docs/FLAT64.md for settings and field definitions.
- Use tools/build_flat64.sh, ctest, tools/run_flat64.py, and tools/summarize_flat64.py to repeat the profile.
- The files retain source and dependency hashes and raw checkpoints.
'''
    (out/'REPORT.md').write_text(report)
    # A standalone figure covering both runtime and resident memory at each N.
    os.environ.setdefault('MPLCONFIGDIR','/tmp/map-benchmark-flat64-mpl')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,len(sizes),figsize=(6*len(sizes),9),layout='constrained',squeeze=False)
    labels=[LABELS[a] for a in ADAPTERS]
    for j,n in enumerate(sizes):
        ax=axes[0,j]
        for k,(field,label) in enumerate([('insert_s','Insert (reserved)'),('hit_s','Find hit'),('miss_s','Find miss')]):
            vals=[lookup[a,n][field]*1e9/n for a in ADAPTERS]
            lows=[(lookup[a,n][field]-lookup[a,n][field+'_min'])*1e9/n for a in ADAPTERS]
            highs=[(lookup[a,n][field+'_max']-lookup[a,n][field])*1e9/n for a in ADAPTERS]
            ax.bar([i+(k-1)*.25 for i in range(len(ADAPTERS))],vals,width=.25,yerr=[lows,highs],capsize=2,label=label)
        ax.set_xticks(range(len(labels)),labels,rotation=25,ha='right');ax.set(title=f'{n:,} entries',ylabel='ns / operation (log scale)',yscale='log');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        if j==0:ax.legend(fontsize=8)
        ax=axes[1,j]
        ax.bar(range(len(labels)),[lookup[a,n]['steady_rss_mib'] for a in ADAPTERS],color=['#277da8','#7cb59c','#efbe68','#9984b4','#e08373','#8b9da5'])
        ax.set_xticks(range(len(labels)),labels,rotation=25,ha='right');ax.set(ylabel='Steady RSS minus input baseline (MiB)');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('map_benchmark | uint64_t -> uint64_t | shared std::hash adapter\nXeon Platinum 8573C, GCC 14.2 -O3 -march=native | median of independent processes; error bars min-max')
    fig.savefig(out/'comparison.png',dpi=180);fig.savefig(out/'comparison.pdf')
    print((out/'REPORT.md').read_text())
if __name__=='__main__':summarize(Path(sys.argv[1] if len(sys.argv)>1 else 'results-flat64').resolve())
