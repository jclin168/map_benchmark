#!/usr/bin/env python3
"""Summarize the complete std::hash suite, retaining failures and coverage."""
import argparse,csv,json,math,html,hashlib
from pathlib import Path
from run_comprehensive import CASES,DIAGNOSTICS
ROOT=Path(__file__).resolve().parents[1]
GROUPS={'construct':['CtorDtorEmptyMap','CtorDtorSingleEntryMap'],'copy_reinsert':['Copy','AccidentallyQuadratic'],'iteration':['IterateIntegers'],'integer_updates':['InsertHugeInt','RandomDistinct2','RandomInsertErase'],'integer_find':['RandomFind_200','RandomFind_2000','RandomFind_500000'],'string':['RandomFindString','RandomFindString_1000000','RandomInsertEraseStrings'],'applications':['GameOfLife_growing','GameOfLife_stabilizing','knucleotide']}
CORE=[c for c in CASES if c not in DIAGNOSTICS and c not in GROUPS['construct']]
TIMED=[c for c in CASES if c not in DIAGNOSTICS]
def geomean(v):return math.exp(sum(math.log(x) for x in v)/len(v))
def kind(name):
 if name=='greg7mdp_btree_map':return 'ordered tree'
 if 'multiindex' in name:return 'hashed multi-index'
 if 'asteria' in name:return 'copy-on-write hash'
 if 'segmented' in name:return 'segmented dense'
 if 'node' in name.lower() or name.startswith(('std_unordered','boost_unordered_map')):return 'node / allocator variant'
 return 'flat / dense hash'
def main():
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();out=a.directory
 env=json.loads((out/'environment.json').read_text());runs=[json.loads(f.read_text()) for f in sorted((out/'runs').glob('*.json'))];lookup={(r['adapter'],r['case']):r for r in runs};adapters=env['adapters'];baseline='std_unordered_map'
 for r in runs:
  if r['status']=='process_error':
   err=(out/'stderr'/(r['adapter']+'__'+r['case']+'.txt')).read_text(errors='replace')
   if 'reserved sentinel key' in err:r['analysis_status']='unsupported_key_domain'
   events=lambda text:{line.split()[0]:int(line.split()[1]) for line in text.splitlines()}
   if events(r.get('memory_events_after','')).get('oom_kill',0)>events(r.get('memory_events_before','')).get('oom_kill',0):r['analysis_status']='kernel_oom'
  r.setdefault('analysis_status',r['status'])
 good=lambda n,c:(n,c) in lookup and lookup[n,c]['status']=='ok' and lookup[n,c].get('benchmark_s',0)>0
 ratio=lambda n,c:lookup[baseline,c]['benchmark_s']/lookup[n,c]['benchmark_s']
 over=[];case_rows=[];labels={}
 for n in adapters:
  rr=[r for r in runs if r['adapter']==n];labels[n]=next((r['rows'][0]['map_label'] for r in rr if r.get('rows')),n)
  core=sum(good(n,c) for c in CORE);score=geomean([ratio(n,c) for c in CORE]) if core==len(CORE) and all(good(baseline,c) for c in CORE) else None
  stable=lookup.get((n,'ShowIsStableReference'))
  prop=(out/'stderr'/(n+'__ShowIsStableReference.txt')).read_text().split()[0] if stable and stable['status']=='ok' else ''
  peak_run=max(rr,key=lambda r:r.get('rss_peak_bytes',0),default={})
  counts={s:sum(r['analysis_status']==s for r in rr) for s in sorted(set(r['analysis_status'] for r in rr))}
  over.append({'adapter':n,'label':labels[n],'container_kind':kind(n),'completed_processes':len(rr),'total_cases':len(CASES),'timed_passed':sum(lookup.get((n,c),{}).get('status')=='ok' for c in TIMED),'timed_total':len(TIMED),'core_passed':core,'core_total':len(CORE),'speed_vs_std':score,'max_observed_rss_gib':peak_run.get('rss_peak_bytes',0)/2**30,'peak_is_lower_bound':peak_run.get('rss_peak_is_lower_bound',True),'stable_reference_diagnostic':prop,'status_counts':counts})
  for c in CASES:
   r=lookup.get((n,c));status=r['analysis_status'] if r else 'pending'
   case_rows.append({'adapter':n,'label':labels[n],'case':c,'kind':'diagnostic' if c in DIAGNOSTICS else 'timed','status':status,'runtime_s':r.get('benchmark_s') if r and status=='ok' and c not in DIAGNOSTICS else None,'wall_s':r.get('wall_s') if r else None,'rss_peak_gib':r.get('rss_peak_bytes',0)/2**30 if r else None,'observed_vmsize_max_gib':r.get('observed_vmsize_bytes',0)/2**30 if r else None,'vmpeak_gib':r.get('observed_vmpeak_bytes',0)/2**30 if r else None,'phase_count':len(r.get('rows',[])) if r else 0})
 complete=sorted((x for x in over if x['core_passed']==len(CORE)),key=lambda x:sum(math.log(lookup[x['adapter'],c]['benchmark_s']) for c in CORE)) if len(lookup)==len(adapters)*len(CASES) else []
 core_times={x['adapter']:geomean([lookup[x['adapter'],c]['benchmark_s'] for c in CORE]) for x in complete}
 for x in over:
  n=x['adapter'];x['full_core_rank']=next((i+1 for i,v in enumerate(complete) if v['adapter']==n),None)
  x['relative_core_time_to_best']=core_times[n]/core_times[complete[0]['adapter']] if n in core_times else None
 for name,data in [('overview.csv',over),('case_results.csv',case_rows)]:
  with (out/name).open('w') as f:
   w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows({k:json.dumps(v,sort_keys=True) if isinstance(v,dict) else v for k,v in row.items()} for row in data)
 (out/'overview.json').write_text(json.dumps(over,indent=2))
 lines=['# map_benchmark 全容器綜合評比（std::hash）','',f'已完成 **{len(runs)}/{len(adapters)*len(CASES)}** 組容器／測項；{len(adapters)} 種容器／配置、{len(TIMED)} 個計時測項、{len(DIAGNOSTICS)} 個診斷測項。主矩陣每組一次，原始參數，沒有縮減循環。{"本報告為完整主矩陣結果。" if len(runs)==len(adapters)*len(CASES) else "本報告為進度快照。"}','', '## 範圍與方法','', '- 全部原有「已註冊」測項；StringHashBench 在原始程式中被註解、Strings.cpp 內容被 #if 0 排除，不是可執行測項。新增 FlatMap64Reserved/Grow 不混入本輪原始 suite。','- 共用 std::hash adapter，保留容器內部 hash mixing、load factor、allocator 與種子政策；sflat 的 process seed 固定為 1。樹型容器不使用 hash，另標示類別。平行容器在此以單執行緒 API 測試，不代表多執行緒效能。','- GCC 14.2、C++17、Release -O3 -DNDEBUG -march=native；每個 executable 以 unity build 編譯，註冊名稱使用 __COUNTER__ 避免跨原始檔行號碰撞。F14 使用所需的三個 Folly source files，不建置其餘 Folly 元件。','- 每個程序單獨執行、固定 CPU affinity；每個測項先依固定順序測 sflat、std、Boost flat、Ankerl、Abseil flat、Google dense、Google sparse，其餘容器以固定亂數順序執行；沒有把執行順序平衡化。不同測項有插入、查詢、析構等不同計時邊界，數字代表原始 workload，不是純 find ns/op。','- 逐階段使用原程式的 expected-result 檢查；不相符會回傳失敗。診斷的 stable-reference=0 是正常屬性結果，不是驗證失敗。','- 每程序 '+str(env['timeout_s'])+' 秒上限；RSS '+str(env['rss_limit_gib'])+' GiB、整體 cgroup '+str(env['cgroup_limit_gib'])+' GiB 取樣保護線；環境硬上限 8 GiB、無 swap，RLIMIT_AS 保持原本 unlimited。逾時、記憶體停止、crash、sentinel domain 不相容與驗證失敗各自保留，失敗程序的部分階段不納入計時排名。','- RSS 是整個原始 workload 的程序峰值，含輸入、暫存與配置器，不能稱為單一 map 常駐記憶體。endMeasure 有些在 map 析構後，該點 RSS 也不能當作 live-map 用量。極小測項的 peak 可能受程序啟動／exec accounting 底線主導；不要比較其微小記憶體差距。CSV/HTML 另列虛擬位址空間 VmPeak（及 CSV 的最大取樣 VmSize）；虛擬位址預留不等同於實體 RSS，失敗程序僅有已觀測用量，僅供診斷，不與正確完成者做記憶體效率排名。','- 單次測量、共享 VM，沒有信賴區間；小幅差距不可據此視為穩定優勢。','', '## 全容器總覽','', '速度倍率為 std::unordered_map / 該容器的幾何平均：15 個非建構計時 workload 各占相同權重，每個 workload 先加總其所有階段秒數。**只有容器與 std baseline 均完成同一組 15 個 workload 才列倍率**；建構另列，失敗缺項不以較少測項補算總分。空表建構迴圈可能被編譯器消除，該微測項不合成吞吐量倍率。相對 std 的速度倍率大於 1 表示較快。完整核心名次另以同一組 15 項的幾何平均耗時排序，相對最快完整者的耗時倍率越小越好；因此即使 std baseline 未完整通過，其他完整容器之間仍可比較。','', '| Container | 類別 | 計時通過 | 核心覆蓋 | 完整核心名次 | 相對最快完整者耗時 | 相對 std 速度 | 已觀測最高 RSS GiB | 狀態 |','|---|---|---:|---:|---:|---:|---:|---:|---|']
 ranked=sorted(over,key=lambda x:(x['full_core_rank'] is None,x['full_core_rank'] or 0,x['adapter']))
 boundary=out/'epoch-recheck/record.json'
 if boundary.exists():
  b=json.loads(boundary.read_text())
  lines.insert(4, f"恢復環境交界另重測 sflat RandomDistinct2 一次（原始 {b['original_benchmark_s']:.6f} 秒、恢復後 {b['restored_benchmark_s']:.6f} 秒）；以恢復後樣本作主結果，與其餘 38 個容器保持同一執行時段。選樣依環境時段，與快慢無關；兩份原始結果均保留於 epoch-recheck/。合計 780 組、781 份已保存程序結果，不含環境中斷未留下 checkpoint 的嘗試。\n")
 for x in ranked:
  score=f'{x["speed_vs_std"]:.2f}x' if x['speed_vs_std'] else '—'
  core_rank=x['full_core_rank'] or '—';core_slow=f"{x['relative_core_time_to_best']:.2f}x" if x['relative_core_time_to_best'] is not None else '—'
  mem=('≥' if x['peak_is_lower_bound'] else '')+f'{x["max_observed_rss_gib"]:.3f}'
  status=', '.join(f'{k}:{v}' for k,v in x['status_counts'].items()) or 'pending'
  lines.append(f'| {x["label"]} | {x["container_kind"]} | {x["timed_passed"]}/{x["timed_total"]} | {x["core_passed"]}/{x["core_total"]} | {core_rank} | {core_slow} | {score} | {mem} | {status} |')
 lines+=['','## 診斷結果','', '| 診斷 | 通過程序 | 說明 |','|---|---:|---|']
 for diag in ['ShowHash','ShowHashString']:
  valid=[n for n in adapters if lookup.get((n,diag),{}).get('status')=='ok']
  hashes={hashlib.sha256((out/'stderr'/(n+'__'+diag+'.txt')).read_bytes()).hexdigest() for n in valid}
  lines.append(f'| {diag} | {len(valid)}/{len(adapters)} | {len(hashes)} 種不同輸出；用來確認共同 hash adapter |')
 stable_yes=[x['label'] for x in over if x['stable_reference_diagnostic']=='1']
 stable_no=[x['label'] for x in over if x['stable_reference_diagnostic']=='0']
 lines.append(f'| ShowIsStableReference | {len(stable_yes)+len(stable_no)}/{len(adapters)} | {len(stable_yes)} 種觀測穩定、{len(stable_no)} 種觀測不穩定 |')
 lines+=['', '穩定引用診斷只觀察原測項的 10,000 次插入，不等同於所有操作的 API 保證；0 並非失敗。各容器觀測值在 overview.csv 的 stable_reference_diagnostic 欄位。']
 lines+=['','## 分類結果','', '各分類以完整通過同一組分類測項者的幾何平均耗時排序；所有容器均已嘗試該分類後才列名次。std baseline 未完整通過分類時，相對 std 欄留空。','', '| 分類 | 測項數 | 可完整比較容器數 | 最快容器 | 相對 std 速度 | sflat 名次 |','|---|---:|---:|---|---:|---:|']
 for group,cases in GROUPS.items():
  if group=='construct':
   lines.append('| construct | 2 | — | 建構微測項逐項列出，不合成倍率 | — | — |');continue
  eligible=sorted((geomean([lookup[n,c]['benchmark_s'] for c in cases]),n) for n in adapters if all(good(n,c) for c in cases))
  if not all((n,c) in lookup for n in adapters for c in cases):
   lines.append(f'| {group} | {len(cases)} | {len(eligible)} | 尚未完成該分類全部容器 | — | — |');continue
  if eligible:
   best=eligible[0];rank=next((str(i+1)+'/'+str(len(eligible)) for i,x in enumerate(eligible) if x[1]=='sflat_flat_hash_map'),'—')
   speed=f'{geomean([ratio(best[1],c) for c in cases]):.2f}x' if all(good(baseline,c) for c in cases) else '—'
   lines.append(f'| {group} | {len(cases)} | {len(eligible)} | {labels[best[1]]} | {speed} | {rank} |')
  else:lines.append(f'| {group} | {len(cases)} | 0 | 沒有完整通過該分類的容器 | — | — |')
 lines+=['','## sflat 逐 workload 的效能差距','', '每個 workload 只比較完整通過者；全部 39 種配置均已嘗試才列出名次。耗時倍率為 sflat / 該項最快者，大於 1 表示 sflat 花更多時間。這些差距可作為後續 profiling 的優先順序，不代表已確定根因。','', '| Workload | 通過數 | sflat 名次 | sflat 秒數 | 最快容器 | sflat 耗時／最快耗時 |','|---|---:|---:|---:|---|---:|']
 for c in CORE:
  passed=sorted((n for n in adapters if good(n,c)),key=lambda n:lookup[n,c]['benchmark_s'])
  if all((n,c) in lookup for n in adapters) and good('sflat_flat_hash_map',c):
   n='sflat_flat_hash_map';fast=passed[0];rank=passed.index(n)+1
   lines.append(f'| {c} | {len(passed)}/39 | {rank}/{len(passed)} | {lookup[n,c]["benchmark_s"]:.4f} | {labels[fast]} | {lookup[n,c]["benchmark_s"]/lookup[fast,c]["benchmark_s"]:.2f}x |')
  else:lines.append(f'| {c} | {len(passed)}/39 | — | — | 無有效完整結果，或尚未全部完成 | — |')
 lines+=['','## 主要容器逐 workload 秒數','', '只列整個 case 完成且驗證成功的秒數；其他狀態不以部分階段秒數替代。完整 39 種與逐階段數據見 CSV/HTML。','']
 selected=['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','ktprime_hash_table8','std_unordered_map']
 lines+=['| Workload | '+' | '.join(selected)+' |','|---|'+'---:|'*len(selected)]
 for c in TIMED:
  values=[f'{lookup[n,c]["benchmark_s"]:.4f}' if good(n,c) else lookup.get((n,c),{}).get('analysis_status','pending') for n in selected]
  lines.append('| '+c+' | '+' | '.join(values)+' |')
 guarded=[r for r in runs if r['status'] in {'rss_watchdog','cgroup_watchdog'}]
 if guarded:
  lines+=['','## 記憶體保護觸發紀錄','', '以下為未完成 workload 中止前的已觀測程序用量，不能解讀為完成指定 entry 數後的 map 大小；不納入速度或記憶體效率排名。VmPeak 是虛擬位址空間，不是 RSS。','', '| 容器 | Workload | 停止原因 | 程序秒數（未完成） | 已觀測 RSS GiB | 已觀測 VmPeak GiB | 已完成階段 |','|---|---|---|---:|---:|---:|---:|']
  for r in guarded:
   lines.append(f'| {labels[r["adapter"]]} | {r["case"]} | {r["status"]} | {r["wall_s"]:.2f} | {r["rss_peak_bytes"]/2**30:.4f} | {r["observed_vmpeak_bytes"]/2**30:.4f} | {len(r["rows"])} |')
 lines+=['','## 整數查找逾時所在階段','', '原程式每種命中率依序測低 32 位、高 32 位。依已完成的原始階段數，推定逾時時下一個未完成階段；這不是該階段完成所需秒數。結果限定本輪 std::hash 與原始 masked 輸入，不同 hash 設定需另行測量。','', '| Workload | 逾時程序 | 下一階段為高 32 位 | 下一階段為低 32 位 |','|---|---:|---:|---:|']
 for c in GROUPS['integer_find']:
  failed=[r for r in runs if r['case']==c and r['status']=='timeout']
  high=sum(len(r.get('rows',[]))%2==1 for r in failed)
  lines.append(f'| {c} | {len(failed)} | {high} | {len(failed)-high} |')
 if (out/'diagnostics/sflat_find200_phases.md').exists():
  lines+=['','## 後續 profiling 目標','', '[200 次插入整數查找的命中率階段比較](diagnostics/sflat_find200_phases.md)：依已通過的 sflat 與 Boost flat checkpoint 比較，25% 命中率的差距較大；高命中率接近。這是單次測量的觀察，尚未判定根因。']
 if (out/'diagnostics/asteria_clear.txt').exists():
  lines+=['','## 已確認的 pinned dependency 問題','', 'asteria-cow_hashmap 在 GameOfLife_stabilizing 的 R-pentomino 輸出 167249，原預期 116。InsertHugeInt 的 clear 100M int 階段也留下 59,122,781 個元素（預期 0）。另以原生 rocket::cow_hashmap API（不經 benchmark adapter）重現：reserve(64)、插入 key=1 後 clear()，size 仍為 1，find(1) 仍命中。當前 revision 的 clear() 對 bucket range 使用 size()，而非整個 bucket range，會殘留元素。','', '這會影響多次清空的應用測項，不能將異常工作狀態的耗時當作正確 workload 的速度，其記憶體數字也僅描述錯誤執行狀態。原始 timeout／verification_failed 狀態仍完整保留。結論只針對 manifest 記錄的 revision，不代表目前上游版本。','', '- [最小原生 API 重現程式](diagnostics/asteria_clear.cpp)、[輸出](diagnostics/asteria_clear.txt)、[版本與重現資訊](diagnostics/asteria_clear.json)。']
 lines+=['','## 詳細檔案','', '- [互動表格](comparison.html)：選測項與容器類型，可排序所有容器的時間及峰值記憶體。','- [全容器總覽 CSV](overview.csv)、[全部 case 結果 CSV](case_results.csv)、[environment.json](environment.json)、[compile-flags.json](compile-flags.json)、[builds.json](builds.json)。','- runs/：每個程序的 JSON checkpoint；stdout/、stderr/：原始輸出；build-logs/：每個 adapter 的編譯紀錄。','- [續跑環境紀錄](resumptions.json)：環境中斷後保留391個 checkpoint；在相同CPU型號／拓樸與資源上限的恢復環境接續，屬跨執行環境時段的單次 sweep，不是獨立重複樣本。','- 原始階段 CSV raw.csv 在全部程序完成時由 runner 輸出；未完成與失敗 case 的記錄保留供診斷，排名只採整個 case 通過者。','- docs/COMPREHENSIVE.md 說明建置、續跑與重現方式。']
 (out/'REPORT.zh-TW.md').write_text('\n'.join(lines)+'\n')
 payload=json.dumps({'overview':over,'cases':case_rows,'case_names':CASES,'completed':len(runs),'total':len(adapters)*len(CASES)},ensure_ascii=False).replace('</','<\\/')
 page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>map_benchmark 全容器評比</title><style>body{font:15px system-ui;margin:24px;color:#17232a;background:#f5f7fa}h1{font-size:24px}select,button{font:inherit;padding:8px;margin:4px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}th{cursor:pointer;background:#e5edf3}td.num{text-align:right;font-variant-numeric:tabular-nums}.bad{color:#a32020}.ok{color:#12643d}.note{max-width:1100px;line-height:1.6}</style><h1>map_benchmark：全部容器 × std::hash</h1><p id="progress"></p><p class="note">單次、原始 workload 參數；未通過／逾時／記憶體停止不納入速度。總分只比較完整的 15 個非建構 workload；建構與診斷另列。RSS 為程序 workload 峰值，含輸入與暫存，不是 live-map 配置量。單次共享 VM 測量不宜判讀微小差距。</p><label>測項 <select id="case"><option value="overview">總覽</option></select></label><label>容器類型 <select id="kind"><option value="all">全部</option></select></label><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table><script>const DATA=PAYLOAD;const sel=document.getElementById('case'),kind=document.getElementById('kind');for(const c of DATA.case_names){let o=document.createElement('option');o.value=c;o.textContent=c;sel.append(o)}for(const c of [...new Set(DATA.overview.map(x=>x.container_kind))]){let o=document.createElement('option');o.value=c;o.textContent=c;kind.append(o)}document.getElementById('progress').textContent=`已完成 ${DATA.completed} / ${DATA.total} 組容器／測項`;let sortKey='label',desc=false;function render(){const overview=sel.value==='overview';let rows=DATA.overview.filter(x=>kind.value==='all'||x.container_kind===kind.value).map(x=>overview?x:{...x,...DATA.cases.find(r=>r.adapter===x.adapter&&r.case===sel.value)});let cols=overview?[['label','容器'],['container_kind','類別'],['timed_passed','通過計時測項 /17'],['core_passed','核心覆蓋 /15'],['full_core_rank','完整核心名次'],['relative_core_time_to_best','相對最快完整者耗時'],['speed_vs_std','相對 std 倍率'],['max_observed_rss_gib','最高 RSS GiB'],['status_counts','狀態']]:[['label','容器'],['status','狀態'],['runtime_s','已通過 case 秒數'],['rss_peak_gib','已觀測程序 RSS peak GiB'],['vmpeak_gib','已觀測 VmPeak GiB'],['phase_count','完成階段數']];rows.sort((a,b)=>{let x=a[sortKey],y=b[sortKey];if(x==null)return 1;if(y==null)return -1;let cmp=typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y));return desc?-cmp:cmp});let h=document.getElementById('head');h.replaceChildren();for(let [k,title] of cols){let e=document.createElement('th');e.textContent=title;e.onclick=()=>{desc=sortKey===k?!desc:false;sortKey=k;render()};h.append(e)}let body=document.getElementById('body');body.replaceChildren();for(let r of rows){let tr=document.createElement('tr');for(let [k] of cols){let td=document.createElement('td'),v=r[k];td.textContent=v==null?'—':typeof v==='number'?Number.isInteger(v)?v:v.toFixed(4):typeof v==='object'?Object.entries(v).map(([a,b])=>`${a}:${b}`).join(', '):v;if(typeof v==='number'){td.className='num';if((['rss_peak_gib','vmpeak_gib'].includes(k)&&r.status!=='ok')||(k==='max_observed_rss_gib'&&r.peak_is_lower_bound))td.textContent='≥'+td.textContent;}if(k==='status')td.className=v==='ok'?'ok':'bad';tr.append(td)}body.append(tr)}}sel.onchange=()=>{sortKey=sel.value==='overview'?'label':'runtime_s';desc=false;render()};kind.onchange=render;render();</script></html>'''.replace('PAYLOAD',payload)
 (out/'comparison.html').write_text(page)
 print(f'Report: {len(runs)}/{len(adapters)*len(CASES)} processes; {sum(r["status"]=="ok" for r in runs)} OK')
if __name__=='__main__':main()
