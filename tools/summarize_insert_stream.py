#!/usr/bin/env python3
"""Summarize completed and failed streaming insert probes without extrapolation."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
manifest=json.loads((d/'environment.json').read_text()); results=json.loads((d/'results.json').read_text())
n=manifest['entries']; cap=manifest['limit_address_space_bytes']/2**30
names=['sflat','Boost flat','Ankerl dense','Abseil flat','Google dense','Google sparse'];rows=[]
for name,r in zip(names,results):
    last=r['last']; complete=r['returncode']==0 and last and last['status']=='completed' and int(last['inserted'])==n
    if last:
        baseline=int(last['baseline_bytes']);rss=(int(last['rss_bytes'])-baseline)/2**30;peak=max(0,int(last['peak_bytes'])-baseline)/2**30
    else:rss=peak=None
    rows.append(dict(map=name,target_entries=n,completed=complete,returncode=r['returncode'],last_status=last['status'] if last else 'no_record',last_confirmed_entries=int(last['inserted']) if last else 0,rss_delta_gib=rss,peak_delta_gib=peak))
with (d/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
lines=['# 500M 不 reserve、單純 insert：受限環境診斷','',f'目標 {n:,} entries，uint64_t → uint64_t。六者均從空表 native insert，不 reserve、不 find；以雙射即時生成唯一 key，排除 Google markers，沒有 O(N) 輸入陣列。每者一個獨立程序、相同 CPU affinity、共用 std::hash 與先前版本/編譯設定。elapsed 包含 key generation 與每 10M checkpoint 開銷。','',f'環境實體記憶體上限 8 GiB、無 swap；本次設 RLIMIT_AS={cap:g} GiB，以免耗盡環境。這是虛擬位址空間上限，並非 RSS 限制。未 touch 的 mmap 與擴容時的新舊配置都計入，因此以下失敗筆數不能當作 8 GiB RAM 的真實容量上限。','',f'完成 {n:,} entries：{sum(r["completed"] for r in rows)}/{len(rows)}。未完成者沒有 500M 實測用量，以下沒有外推或當作同筆數排名。','', '| Map | 狀態 | 最後確認插入數 | 該時 RSS 增量 GiB | 該時累計 peak 增量 GiB |','|---|---|---:|---:|---:|']
for r in rows:
    status='完成' if r['completed'] else ('配置失敗' if r['last_status']=='allocation_failed' else f'程序終止，rc={r["returncode"]}；僅有 checkpoint')
    lines.append(f'| {r["map"]} | {status} | {r["last_confirmed_entries"]:,} | {r["rss_delta_gib"]:.3f} | {r["peak_delta_gib"]:.3f} |')
lines+=['','RSS 與 peak 均扣除建表前程序 baseline；兩者來自不同 kernel accounting，可能略有差異。配置失敗列在 catch 中、map 尚未析構時讀取。訊號終止列只有最後 checkpoint，筆數與峰值都是可確認的下界，並非終止瞬間的峰值。失敗後 RSS 也不是一個保證可正常使用的 map 之用量。','', 'Google sparse 的 stderr 明確回報 failed to reallocate，並以 exit 1 結束；Google dense 以 SIGSEGV 結束。這兩列僅保留最後 checkpoint。系統 cgroup OOM / OOM kill 計數皆為 0。','', '500M 筆 16-byte key/value 的有效資料本身為 7.451 GiB，還需空槽、索引、配置與成長空間。本環境無法提供完整 500M 六者的實測比較。建議在 32 GiB 或更大的機器重跑，保留足夠作業系統餘裕：','', '```sh','python3 tools/run_insert_stream.py --entries 500000000 --limit-gib 0','python3 tools/summarize_insert_stream.py results-flat64-500m','```','', '工具產生獨立 build-flat64-stream executables，沒有覆寫先前 1M/10M/100M 的 benchmark binaries。原始逐 10M checkpoint、stderr、exit status、binary hashes、dependency commits 與環境設定均一併保留。']
(d/'REPORT.zh-TW.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
