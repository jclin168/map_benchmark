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
    report=f'''# map_benchmark 六種 flat hash table 實測

已在 martinus/map_benchmark（基底 commit {commits['map_benchmark'][:12]}）加入 sflat、Google dense、Google sparse adapters，並加入既有 BenchRegistry/計時器中的 64-bit 比較測項。六個目標均編譯全部原有 benchmark source；本輪執行受控 64-bit profile 與兩個原有測項作相容性檢查，沒有宣稱已跑完所有原有 workloads。

## 測試條件

- {cpu_name}；{compiler_name}；C++17、-O3 -DNDEBUG -march=native。
- 六者共用 std::hash adapter；保留各容器內部的 hash mixing、預設 load factor、allocator 與 THP 行為。sflat 使用可重現的 SFLAT_PROCESS_SEED=1，沒有套用前次實驗 patch。
- uint64_t → uint64_t，唯一隨機分布 key。所有容器使用相同輸入與查詢，排除 Google 的兩個保留 marker；未命中 key 與插入 key 由同一雙射的不重疊區段生成。
- 每個 map/size/case {repeats} 次獨立程序；每次只有一個 benchmark 程序，固定 CPU affinity，隨機化 map/case 順序。查詢 shuffle seeds 為 {seed_list}。
- Reserved：reserve(N)+N 次 native value_type insert、N 次打亂順序的 hit、N 次 miss。Grow：從空表插入 N 次，不 reserve。資料生成、shuffle、RSS 讀取及析構不計入這些測項時間；建表包含 constructor、reserve 及 page faults。
- Google 原生 API 沒有 emplace/reserve；一般 adapter 提供相容包裝。本受控測項以已驗證的共同 key domain 直接使用 Google native insert/find，避免把 adapter sentinel 檢查開銷計入比較。
- 記憶體上限 8 GiB，THP=madvise。實際 CPU/編譯器/commit/build flags 等完整資料保存在 environment.json。

## 版本

'''
    for name,sha in commits.items():report+=f'- {name}: `{sha}`\n'
    report+='''
Ankerl 為 5.3.3，Abseil 為 LTS 20250814.1，Google sparsehash 為 2.0.4；Boost 使用本機 1.93 開發版 modular headers。sflat 為取得時最新版。這些實作沒有改負載因子或使用特殊 allocator。

## Reserved runtime 與常駐記憶體

數字為獨立程序的中位數，時間單位秒。RSS 單位 MiB（2^20 bytes），是在 insert 完成、map 仍存活時量測，扣除 input key vector 與程序基準。RSS 包含 allocator、頁面 rounding 和少量 runtime first-touch，不是精確 logical allocation bytes。

'''
    for n in sizes:
        report+=f'### {n:,} entries\n\n| Map | reserve+insert s | find hit s | find miss s | steady RSS MiB |\n|---|---:|---:|---:|---:|\n'
        for a in ADAPTERS:
            r=lookup[a,n];report+=f"| {LABELS[a]} | {r['insert_s']:.4f} | {r['hit_s']:.4f} | {r['miss_s']:.4f} | {r['steady_rss_mib']:.1f} |\n"
        report+='\n'
    report+='''## 自動擴容建表與峰值

Peak 是程序累積 ru_maxrss 減掉輸入準備後的 baseline current RSS，為建表峰值估計，不是逐 allocation profiler；原始欄位也保留絕對 current/peak RSS。

| Entries | Map | insert without reserve s | end RSS MiB | estimated peak MiB |
|---|---|---:|---:|---:|
'''
    for n in sizes:
        for a in ADAPTERS:
            r=lookup[a,n];report+=f"| {n:,} | {LABELS[a]} | {r['grow_s']:.4f} | {r['grow_steady_mib']:.1f} | {r['grow_peak_mib']:.1f} |\n"
    report+='''
## 如何解讀記憶體

原 Bench 的第八欄是從 benchmark 開始計算的累積 peak 增量；在新測項中它還包含輸入陣列，不能當成單一 map 的 steady memory。本次保留該欄位，額外記錄 current RSS、input baseline、扣基準的 current RSS、絕對 peak 和扣基準的 peak。

主要比較以 insert 後的 current RSS 減 baseline 為準。成長時 old/new table、allocator 留存會反映在 peak；lookup 階段通常不增長，但逐階段數字均有記錄。smaps_rollup 的 current RSS 與 getrusage 的 peak 使用不同 kernel accounting，可能有小差距。小規模測試的 peak 可能受程序啟動高水位影響，不能外推。

## 原有測項相容性檢查

六者皆通過 adapter CTest（整數/字串、重複插入、find、copy、erase、迭代、clear、Google sentinel 拒絕）。小規模 1000-entry profile 完成 12 個程序、24 個測量，並確認未開 extra-memory 時仍輸出原本八欄。

另對六者各執行一次原有 CtorDtorSingleEntryMap 與 AccidentallyQuadratic。這些不是三輪中位數，也不是與上述 64-bit 測項相同的工作負載；它們保留原始資料與 expected-result 驗證。原有所有 workload 未全部執行。

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
## 限制與重跑

- 共享 VM 有計時波動。summary.csv 保留 min/max；圖的誤差棒也是 min/max，不是信賴區間。不要把小差距當成穩定優勢。
- 這是 std::hash、均勻整數輸入的第一輪比較；字串、其他 hash、mixed update 與其餘原有 benchmarks 可能改變排序。
- Google dense/sparse 有原生 sentinel key 限制。共同輸入排除了 marker；一般相容 wrapper 會拒絕 marker 插入。不能假設所有原有 workload 都避開它們。
- 100M 實測成功不代表已測過 1B。本輪沒有外推 1B runtime。
- 詳細設定與欄位定義見 docs/FLAT64.md。執行 tools/build_flat64.sh、ctest、tools/run_flat64.py 與 tools/summarize_flat64.py 可重跑；source/dependency SHAs 與 raw checkpoints 都有保留。
'''
    (out/'REPORT.zh-TW.md').write_text(report)
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
    print((out/'REPORT.zh-TW.md').read_text())
if __name__=='__main__':summarize(Path(sys.argv[1] if len(sys.argv)>1 else 'results-flat64').resolve())
