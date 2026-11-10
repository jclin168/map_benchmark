#!/usr/bin/env python3
"""Summarize live-map virtual space and RSS, separating completed and stopped runs."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
m=json.loads((d/'environment.json').read_text());rs=json.loads((d/'results.json').read_text())
assert m['limit_address_space_bytes']==0 and m['inherited_rlimit_as']==[-1,-1]
n=m['entries'];names=dict(zip(['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','google_dense_hash_map','google_sparse_hash_map'],['sflat','Boost flat','Ankerl dense','Abseil flat','Google dense','Google sparse']))
assert len(rs)==6
rows=[]
for r in rs:
 last=r['last'];done=bool(r['returncode']==0 and last and last['status']=='completed' and int(last['inserted'])==n)
 snap=last if done else r['stop_snapshot']
 assert snap is not None
 rss_peak=max(int(last['peak_bytes']) if last else 0,r['observed_hwm_max_bytes'])
 vm_peak=max(int(snap['vmpeak_bytes']),r['observed_vmpeak_max_bytes'])
 rows.append(dict(map=names[r['map']],completed=done,target_entries=n,last_confirmed_entries=int(last['inserted']) if last else 0,measurement='after_target_insert' if done else 'at_watchdog_stop',vmsize_gib=int(snap['vmsize_bytes'])/2**30,rss_gib=int(snap['rss_bytes'])/2**30,vmpeak_gib=vm_peak/2**30,rss_peak_gib=rss_peak/2**30,peak_is_lower_bound=not done,stop_reason=r['stop_reason'],returncode=r['returncode']))
with (d/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
lines=[f'# {n/1e6:g}M 不 reserve insert：VmSize 與 RSS','',f'uint64_t → uint64_t；唯一 key 即時生成，不配置輸入陣列；不 reserve、不 find。六種 map 共用 std::hash、相同輸入順序、CPU affinity、原有版本與編譯設定；每種一個獨立程序。目標 {n:,} entries，完成 {sum(x["completed"] for x in rows)}/6。','', '**本表為整個程序用量，沒有扣除 baseline**（baseline 仍保存於原始 CSV）。VmSize 是當下整個虛擬位址空間，包含預留、尚未 resident 的映射；RSS 是當下常駐頁。VmPeak 是程序歷來最大 VmSize，RSS peak 是 getrusage 與已監控 VmHWM 的最大值，兩個峰值不一定發生於同一時刻。單位 GiB = 2^30 bytes。','', '## 完成目標：最後一筆 insert 後、map 仍存活','', '| Map | Entries | VmSize GiB | RSS GiB | VmPeak GiB | RSS peak GiB |','|---|---:|---:|---:|---:|---:|']
for x in rows:
 if x['completed']:lines.append(f'| {x["map"]} | {n:,} | {x["vmsize_gib"]:.3f} | {x["rss_gib"]:.3f} | {x["vmpeak_gib"]:.3f} | {x["rss_peak_gib"]:.3f} |')
lines+=['','## 未完成目標：監控發出 SIGKILL 前的同一個取樣','', '| Map | 最後確認筆數下界 | 停止時 VmSize GiB | 停止時 RSS GiB | 已觀測 VmPeak GiB | 已觀測 RSS peak GiB |','|---|---:|---:|---:|---:|---:|']
for x in rows:
 if not x['completed']:lines.append(f'| {x["map"]} | ≥{x["last_confirmed_entries"]:,} | {x["vmsize_gib"]:.3f} | {x["rss_gib"]:.3f} | ≥{x["vmpeak_gib"]:.3f} | ≥{x["rss_peak_gib"]:.3f} |')
lines+=['', f'未完成者以上用量是停止取樣，不能當成 {n/1e6:g}M 的用量，也不能當成完成 {n/1e6:g}M 所需峰值；最後確認筆數來自每 10M checkpoint，停止當時實際筆數可能更高。取樣與 SIGKILL 之間仍可能有少量配置，因此未完成者 peak 是下界。','',f'RLIMIT_AS soft/hard 均為 unlimited，沒有設定虛擬位址限制。每約 {m["watchdog_poll_seconds"]*1000:g} ms 監控實際 RSS；程序 RSS 預算 {m["rss_limit_bytes"]/2**30:g} GiB、整個環境 memory.current 保護線 {m["cgroup_watchdog_bytes"]/2**30:g} GiB，環境硬上限 8 GiB，無 swap。總用量包含其他程序與 page cache，可能先觸發總用量保護。這是取樣監控，並非 Linux RLIMIT_RSS 硬限制。','', '完成者的 VmSize/VmPeak 從程序內 /proc/self/status 讀取，RSS 從 smaps_rollup 讀取；未完成者的 VmSize/RSS 同取自外部監控的 /proc/PID/status。兩種 RSS kernel accounting 可能有少量差異。','', '```sh',f'python3 tools/run_insert_stream.py --entries {n} --limit-gib 0 --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out {d.name}',f'python3 tools/summarize_insert_vm_rss.py {d.name}','```','', '原始 CSV、停止時快照、觀測峰值、metadata、source/dependency/binary SHA、測量用 C++ source snapshot、前後 OOM event counters 均保留。這是單次記憶體測試；elapsed 包含即時 key 產生、checkpoint 與監控成本，不應直接與先前純 insert timing 排名混用。']
(d/'REPORT.zh-TW.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
