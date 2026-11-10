#!/usr/bin/env python3
"""Report completed insert RSS separately from incomplete RSS-limited attempts."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
m=json.loads((d/'environment.json').read_text());results=json.loads((d/'results.json').read_text())
assert m['limit_address_space_bytes']==0 and m['inherited_rlimit_as']==[-1,-1]
n=m['entries']; names=dict(zip(['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','google_dense_hash_map','google_sparse_hash_map'],['sflat','Boost flat','Ankerl dense','Abseil flat','Google dense','Google sparse']))
assert len(results)==len(names)
rows=[]
for r in results:
    last=r['last']; complete=r['returncode']==0 and last and last['status']=='completed' and int(last['inserted'])==n
    baseline=int(last['baseline_bytes']) if last else 0
    peak=max(r['observed_hwm_max_bytes'],int(last['peak_bytes']) if last else 0)
    rows.append(dict(map=names[r['map']],target_entries=n,completed=bool(complete),stop_reason=r['stop_reason'],returncode=r['returncode'],last_confirmed_entries=int(last['inserted']) if last else 0,final_rss_delta_gib=(int(last['rss_bytes'])-baseline)/2**30 if complete else '',peak_delta_gib=max(0,peak-baseline)/2**30,peak_is_lower_bound=not complete,observed_cgroup_max_gib=r['observed_cgroup_max_bytes']/2**30,completed_elapsed_s=float(last['elapsed_s']) if complete else ''))
with (d/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
count=sum(x['completed'] for x in rows)
lines=[f'# {n/1e6:g}M 不 reserve insert：實際 RSS 監控測試','',f'目標 {n:,} entries；完成 {count}/6。uint64_t → uint64_t、從空表 native insert、不 reserve、不 find。即時產生唯一 key，不配置輸入陣列；共同排除 Google markers。每個 map 執行一次獨立程序，共用 std::hash、CPU affinity 與先前版本/編譯設定。記憶體讀取/進度輸出每 10M 筆，elapsed 包含 key 生成與監控/進度開銷。','',f'**未限制虛擬位址空間**：RLIMIT_AS inherited soft/hard 均為 unlimited，程式未設定 RLIMIT_AS。監控程序每約 {m["watchdog_poll_seconds"]*1000:g} ms 讀 /proc/PID/status 的 VmRSS/VmHWM；程序 RSS 預算 {m["rss_limit_bytes"]/2**30:g} GiB，整個環境 memory.current 保護線 {m["cgroup_watchdog_bytes"]/2**30:g} GiB。超過任一線即 SIGKILL。環境另有 8 GiB cgroup 硬限制，無 swap。這是取樣監控，並非 Linux RLIMIT_RSS（Linux 不會強制該值）；峰值可能稍超過門檻。','', '| Map | 完成目標 | 最後確認插入數 | 完成後 RSS GiB | 嘗試期間 peak GiB | 停止原因 |','|---|---|---:|---:|---:|---|']
for r in rows:
    rss=f'{r["final_rss_delta_gib"]:.3f}' if r['completed'] else '—'
    peak=('≥' if r['peak_is_lower_bound'] else '')+f'{r["peak_delta_gib"]:.3f}'
    lines.append(f'| {r["map"]} | {"是" if r["completed"] else "否"} | {r["last_confirmed_entries"]:,} | {rss} | {peak} | {r["stop_reason"]} |')
lines+=['', 'RSS/peak 均扣除 map 建立前的程序 baseline。完成者 RSS 在最後一次 insert 完成、map 仍存活時由 smaps_rollup 讀取；完整插入過程 peak 採程序 getrusage 與監控到的 VmHWM 最大值。未完成者沒有目標規模的完成後 RSS；表中 peak 是監控取到的下界，最後確認筆數是最後已輸出的 10M checkpoint，實際停止筆數可能更高。','', 'RSS watchdog 計算整個程序的常駐頁；cgroup watchdog 包含其餘程序、page cache 等，也可能先於 RSS watchdog 觸發。故未完成者只能說在本次保護預算下未完成，不能推論其完整插入所需峰值，也不能當作 8 GiB 硬限制的精確容量上限。','', '```sh',f'python3 tools/run_insert_stream.py --entries {n} --limit-gib 0 --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out {d.name}',f'python3 tools/summarize_insert_rss.py {d.name}','```','', '完整設定、dependency/source/binary SHA、原始 checkpoint、exit status、停止原因、監控最大值與前後 cgroup memory.events 均保留。與前次 500M 的 RLIMIT_AS 診斷不同，本次僅依實際常駐記憶體與整個環境記憶體讀值停止。']
(d/'REPORT.zh-TW.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
