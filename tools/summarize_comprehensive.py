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
 lines=[
 '# map_benchmark: std::hash test report','',
 f'Completed **{len(runs)}/{len(adapters)*len(CASES)}** configuration/case pairs.',
 f'The matrix has {len(adapters)} configurations, {len(TIMED)} timed cases, and {len(DIAGNOSTICS)} diagnostic cases.',
 'Each pair has one primary result. Input sizes and loop counts are unchanged.',
 'The full matrix is complete.' if len(runs)==len(adapters)*len(CASES) else 'This is a progress report.','',
 '## Scope and method','',
 '- The matrix contains all original registered cases. StringHashBench is disabled. The source disables Strings.cpp with #if 0. '
 'FlatMap64Reserved and FlatMap64Grow are separate cases.',
 '- All hash-map configurations select std::hash. Each map keeps its internal hash mixing, load factor, allocator, and seed policy. '
 'The sflat process seed is 1. The ordered tree does not use a hash function. Parallel maps use one thread.',
 '- The build uses GCC 14.2 and C++17. Release flags are -O3 -DNDEBUG -march=native. '
 'Each executable uses a unity build. Test registration uses __COUNTER__. F14 uses three required Folly source files.',
 '- Each native case runs alone on a fixed CPU. The first maps use this order: '
 'sflat, std, Boost flat, Ankerl, Abseil flat, Google dense, and Google sparse. '
 'The other maps use a fixed random order. The order is not balanced across maps. '
 'Timer start and stop points differ by case. Do not interpret these times as find-only costs.',
 '- Each phase checks its expected result. A mismatch causes failure. A stable-reference value of 0 shows unstable references.',
 f'- Each process has a {env["timeout_s"]} s limit. The RSS stop level is {env["rss_limit_gib"]} GiB. '
 f'The cgroup stop level is {env["cgroup_limit_gib"]} GiB. '
 'The environment hard limit is 8 GiB. Swap is disabled. RLIMIT_AS is unlimited. '
 'The report keeps each failure type. Times from incomplete cases do not enter speed ranks.',
 '- RSS covers the full process. It includes input data, temporary storage, and the allocator. '
 'Some endMeasure calls occur after map destruction. Do not use those values as live-map memory. '
 'Small tests can reflect memory used before the executable starts. Do not rank small memory differences. '
 'CSV and HTML also show virtual-address VmPeak. CSV includes the maximum sampled VmSize. '
 'Virtual address space and physical RSS are separate values. Failed-case observations are diagnostic data only.',
 '- Each pair has one sample on a shared VM. No confidence intervals are available. '
 'Small differences do not show a stable advantage.','',
 '## All configurations','',
 'The core set has 15 timed workloads. It excludes constructors. Each workload has equal weight. '
 'First, sum all phase times in each workload. Then calculate the geometric mean. '
 'Speed/std is the geometric mean of std time divided by candidate time. '
 'This value requires all 15 workloads to pass for both maps. A value above 1 means the candidate is faster. '
 'Failed cases never disappear from the score. Constructor tests are separate. '
 'The compiler can remove empty constructor loops. '
 'Core ranks compare only maps that pass all 15 workloads. Time/best divides each complete result by the fastest complete result. '
 'A smaller value means less time. These ranks remain available when the std baseline is incomplete.','',
 '| Container | Type | Timed pass | Core pass | Core rank | Time/best | Speed/std | Highest observed RSS GiB | Status |',
 '|---|---|---:|---:|---:|---:|---:|---:|---|']
 ranked=sorted(over,key=lambda x:(x['full_core_rank'] is None,x['full_core_rank'] or 0,x['adapter']))
 boundary=out/'epoch-recheck/record.json'
 if boundary.exists():
  b=json.loads(boundary.read_text())
  lines.insert(6, f"The environment-boundary check repeated sflat RandomDistinct2 once. "
   f"The original sample was {b['original_benchmark_s']:.6f} s. The restored sample was {b['restored_benchmark_s']:.6f} s. "
   "The restored sample is primary. Selection uses the execution period only. "
   "Both samples are in epoch-recheck/. There are 780 unique pairs and 781 saved results. "
   "Attempts without a checkpoint are excluded.\n")

 for x in ranked:
  score=f'{x["speed_vs_std"]:.2f}x' if x['speed_vs_std'] else '—'
  core_rank=x['full_core_rank'] or '—';core_slow=f"{x['relative_core_time_to_best']:.2f}x" if x['relative_core_time_to_best'] is not None else '—'
  mem=('≥' if x['peak_is_lower_bound'] else '')+f'{x["max_observed_rss_gib"]:.3f}'
  status=', '.join(f'{k}:{v}' for k,v in x['status_counts'].items()) or 'pending'
  lines.append(f'| {x["label"]} | {x["container_kind"]} | {x["timed_passed"]}/{x["timed_total"]} | {x["core_passed"]}/{x["core_total"]} | {core_rank} | {core_slow} | {score} | {mem} | {status} |')
 lines+=['','## Diagnostic results','', '| Diagnostic | Processes passed | Description |','|---|---:|---|']
 for diag in ['ShowHash','ShowHashString']:
  valid=[n for n in adapters if lookup.get((n,diag),{}).get('status')=='ok']
  hashes={hashlib.sha256((out/'stderr'/(n+'__'+diag+'.txt')).read_bytes()).hexdigest() for n in valid}
  lines.append(f'| {diag} | {len(valid)}/{len(adapters)} | {len(hashes)} distinct output values. These values check the selected hash adapter. |')
 stable_yes=[x['label'] for x in over if x['stable_reference_diagnostic']=='1']
 stable_no=[x['label'] for x in over if x['stable_reference_diagnostic']=='0']
 lines.append(f'| ShowIsStableReference | {len(stable_yes)+len(stable_no)}/{len(adapters)} | {len(stable_yes)} configurations with stable references; {len(stable_no)} with unstable references |')
 lines+=['', 'The reference test observes 10,000 insertions. It does not establish an API guarantee for other operations. A value of 0 is valid diagnostic output. See stable_reference_diagnostic in overview.csv.']
 lines+=['','## Results by test group','', 'Each group ranks maps that pass the same group workloads. Ranks use geometric-mean time. Ranks appear after all configurations have attempted that group. Speed/std stays empty when the std baseline does not pass the group.','', '| Group | Cases | Complete maps | Fastest map | Speed/std | sflat rank |','|---|---:|---:|---|---:|---:|']
 for group,cases in GROUPS.items():
  if group=='construct':
   lines.append('| construct | 2 | — | Constructor cases are separate. No aggregate ratio. | — | — |');continue
  eligible=sorted((geomean([lookup[n,c]['benchmark_s'] for c in cases]),n) for n in adapters if all(good(n,c) for c in cases))
  if not all((n,c) in lookup for n in adapters for c in cases):
   lines.append(f'| {group} | {len(cases)} | {len(eligible)} | Some configurations remain incomplete | — | — |');continue
  if eligible:
   best=eligible[0];rank=next((str(i+1)+'/'+str(len(eligible)) for i,x in enumerate(eligible) if x[1]=='sflat_flat_hash_map'),'—')
   speed=f'{geomean([ratio(best[1],c) for c in cases]):.2f}x' if all(good(baseline,c) for c in cases) else '—'
   lines.append(f'| {group} | {len(cases)} | {len(eligible)} | {labels[best[1]]} | {speed} | {rank} |')
  else:lines.append(f'| {group} | {len(cases)} | 0 | No map passed every case in this group | — | — |')
 lines+=['','## sflat time difference by workload','', 'Each workload compares maps that pass the full case. Ranks appear after all 39 configurations have attempted that case. The time ratio is sflat time divided by the fastest time. A value above 1 means sflat takes more time. Use these differences to select profiling tests. They do not identify a cause.','', '| Workload | Maps passed | sflat rank | sflat time s | Fastest map | sflat time / fastest time |','|---|---:|---:|---:|---|---:|']
 for c in CORE:
  passed=sorted((n for n in adapters if good(n,c)),key=lambda n:lookup[n,c]['benchmark_s'])
  if all((n,c) in lookup for n in adapters) and good('sflat_flat_hash_map',c):
   n='sflat_flat_hash_map';fast=passed[0];rank=passed.index(n)+1
   lines.append(f'| {c} | {len(passed)}/39 | {rank}/{len(passed)} | {lookup[n,c]["benchmark_s"]:.4f} | {labels[fast]} | {lookup[n,c]["benchmark_s"]/lookup[fast,c]["benchmark_s"]:.2f}x |')
  else:lines.append(f'| {c} | {len(passed)}/39 | — | — | No valid full result, or some cases remain incomplete | — |')
 lines+=['','## Workload times for selected maps','', 'Times appear only for complete cases with correct results. Failed cases show their status. CSV and HTML contain all 39 configurations and phase data.','']
 selected=['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','ktprime_hash_table8','std_unordered_map']
 lines+=['| Workload | '+' | '.join(selected)+' |','|---|'+'---:|'*len(selected)]
 for c in TIMED:
  values=[f'{lookup[n,c]["benchmark_s"]:.4f}' if good(n,c) else lookup.get((n,c),{}).get('analysis_status','pending') for n in selected]
  lines.append('| '+c+' | '+' | '.join(values)+' |')
 guarded=[r for r in runs if r['status'] in {'rss_watchdog','cgroup_watchdog'}]
 if guarded:
  lines+=['','## Memory watchdog stops','', 'These observations come from stopped workloads. They do not show map size after the target entry count. They do not enter speed or memory-efficiency ranks. VmPeak measures virtual address space. RSS measures resident memory.','', '| Map | Workload | Stop reason | Process time s, incomplete | Observed RSS GiB | Observed VmPeak GiB | Completed phases |','|---|---|---|---:|---:|---:|---:|']
  for r in guarded:
   lines.append(f'| {labels[r["adapter"]]} | {r["case"]} | {r["status"]} | {r["wall_s"]:.2f} | {r["rss_peak_bytes"]/2**30:.4f} | {r["observed_vmpeak_bytes"]/2**30:.4f} | {len(r["rows"])} |')
 lines+=['','## Integer-find phases at timeout','', 'For each hit rate, the source tests low 32 bits first and high 32 bits second. The completed phase count identifies the next incomplete phase. It does not give the time required to finish that phase. These results apply to std::hash and the original masked inputs. Other hash settings need separate tests.','', '| Workload | Timeouts | Next phase: high 32 bits | Next phase: low 32 bits |','|---|---:|---:|---:|']
 for c in GROUPS['integer_find']:
  failed=[r for r in runs if r['case']==c and r['status']=='timeout']
  high=sum(len(r.get('rows',[]))%2==1 for r in failed)
  lines.append(f'| {c} | {len(failed)} | {high} | {len(failed)-high} |')
 if (out/'diagnostics/sflat_find200_phases.md').exists():
  lines+=['','## Tests for further profiling','', 'See the [200-insertion phase comparison](diagnostics/sflat_find200_phases.md). Both sflat and Boost flat passed this case. The difference is larger at a 25% hit rate. Times are close at high hit rates. This single sample does not identify a cause.']
 if (out/'diagnostics/asteria_clear.txt').exists():
  lines+=['','## Confirmed fault in a recorded dependency','', 'asteria-cow_hashmap returns 167249 for the R-pentomino in GameOfLife_stabilizing. The expected value is 116. InsertHugeInt leaves 59,122,781 entries after clear. The expected count is 0. A separate test uses the native rocket::cow_hashmap API. It calls reserve(64), inserts key=1, and calls clear(). The size stays at 1. find(1) still finds the key. In this revision, clear() uses size() for the bucket range. It leaves entries outside that range.','', 'This fault affects cases that clear and reuse a map. Times and memory values describe incorrect execution. Do not use them as valid workload costs. Original timeout and verification_failed states remain in the data. This finding applies only to the revision in the manifest.','', '- Native API test: [source](diagnostics/asteria_clear.cpp), [output](diagnostics/asteria_clear.txt), and [revision data](diagnostics/asteria_clear.json).']
 lines+=['','## Files','', '- [Interactive table](comparison.html): download and open it locally. Select a case and map type. Select a column to sort the data.','- Data files: [overview.csv](overview.csv), [case_results.csv](case_results.csv), [environment.json](environment.json), [compile-flags.json](compile-flags.json), and [builds.json](builds.json).','- runs/ contains JSON checkpoints. stdout/ and stderr/ contain original process output. build-logs/ contains adapter build logs. These folders are in the complete-run archive.','- [Resume record](resumptions.json): 391 checkpoints survived the environment interruption. The restored environment had the same CPU model, topology, and resource limits. This is one matrix across execution periods. It is not an independent repeat.','- The runner writes raw.csv when all processes finish. It retains failed and incomplete records for diagnosis. Ranks use complete cases with correct results.','- docs/COMPREHENSIVE.md gives build, resume, and reproduction instructions.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
 payload=json.dumps({'overview':over,'cases':case_rows,'case_names':CASES,'completed':len(runs),'total':len(adapters)*len(CASES)},ensure_ascii=False).replace('</','<\\/')
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>map_benchmark: std::hash results</title><style>body{font:15px system-ui;margin:24px;color:#17232a;background:#f5f7fa}h1{font-size:24px}select,button{font:inherit;padding:8px;margin:4px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}th{cursor:pointer;background:#e5edf3}td.num{text-align:right;font-variant-numeric:tabular-nums}.bad{color:#a32020}.ok{color:#12643d}.note{max-width:1100px;line-height:1.6}</style><h1>map_benchmark: all configurations with std::hash</h1><p id="progress"></p><p class="note">Each pair has one sample. Inputs and loop counts are unchanged. Failed cases do not enter speed ranks. The core rank uses 15 complete workloads. Constructor and diagnostic cases are separate. RSS includes process input and temporary storage. VmPeak measures virtual address space. Small differences on this shared VM do not establish a stable advantage.</p><label>Case <select id="case"><option value="overview">Overview</option></select></label><label>Map type <select id="kind"><option value="all">All</option></select></label><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table><script>const DATA=PAYLOAD;const sel=document.getElementById('case'),kind=document.getElementById('kind');for(const c of DATA.case_names){let o=document.createElement('option');o.value=c;o.textContent=c;sel.append(o)}for(const c of [...new Set(DATA.overview.map(x=>x.container_kind))]){let o=document.createElement('option');o.value=c;o.textContent=c;kind.append(o)}document.getElementById('progress').textContent=`Completed ${DATA.completed} / ${DATA.total} configuration/case pairs`;let sortKey='label',desc=false;function render(){const overview=sel.value==='overview';let rows=DATA.overview.filter(x=>kind.value==='all'||x.container_kind===kind.value).map(x=>overview?x:{...x,...DATA.cases.find(r=>r.adapter===x.adapter&&r.case===sel.value)});let cols=overview?[['label','Map'],['container_kind','Type'],['timed_passed','Timed pass /17'],['core_passed','Core pass /15'],['full_core_rank','Core rank'],['relative_core_time_to_best','Time / best complete map'],['speed_vs_std','Speed / std'],['max_observed_rss_gib','Highest RSS GiB'],['status_counts','Status']]:[['label','Map'],['status','Status'],['runtime_s','Passed case time s'],['rss_peak_gib','Observed process peak RSS GiB'],['vmpeak_gib','Observed VmPeak GiB'],['phase_count','Completed phases']];rows.sort((a,b)=>{let x=a[sortKey],y=b[sortKey];if(x==null)return 1;if(y==null)return -1;let cmp=typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y));return desc?-cmp:cmp});let h=document.getElementById('head');h.replaceChildren();for(let [k,title] of cols){let e=document.createElement('th');e.textContent=title;e.onclick=()=>{desc=sortKey===k?!desc:false;sortKey=k;render()};h.append(e)}let body=document.getElementById('body');body.replaceChildren();for(let r of rows){let tr=document.createElement('tr');for(let [k] of cols){let td=document.createElement('td'),v=r[k];td.textContent=v==null?'—':typeof v==='number'?Number.isInteger(v)?v:v.toFixed(4):typeof v==='object'?Object.entries(v).map(([a,b])=>`${a}:${b}`).join(', '):v;if(typeof v==='number'){td.className='num';if((['rss_peak_gib','vmpeak_gib'].includes(k)&&r.status!=='ok')||(k==='max_observed_rss_gib'&&r.peak_is_lower_bound))td.textContent='≥'+td.textContent;}if(k==='status')td.className=v==='ok'?'ok':'bad';tr.append(td)}body.append(tr)}}sel.onchange=()=>{sortKey=sel.value==='overview'?'label':'runtime_s';desc=false;render()};kind.onchange=render;render();</script></html>'''.replace('PAYLOAD',payload)
 (out/'comparison.html').write_text(page)
 print(f'Report: {len(runs)}/{len(adapters)*len(CASES)} processes; {sum(r["status"]=="ok" for r in runs)} OK')
if __name__=='__main__':main()
