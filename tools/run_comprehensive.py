#!/usr/bin/env python3
"""Run every original map_benchmark case with isolated std::hash processes."""
import argparse,csv,hashlib,json,math,os,random,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIAGNOSTICS={'ShowHash','ShowHashString','ShowIsStableReference'}
CASES=['ShowHash','ShowHashString','ShowIsStableReference','CtorDtorEmptyMap','CtorDtorSingleEntryMap','Copy','GameOfLife_growing','GameOfLife_stabilizing','AccidentallyQuadratic','IterateIntegers','RandomDistinct2','InsertHugeInt','RandomInsertErase','RandomInsertEraseStrings','knucleotide','RandomFindString','RandomFindString_1000000','RandomFind_200','RandomFind_2000','RandomFind_500000']
FIELDS=['map_label','hash_label','test','measurement_id','measurement','actual_result','runtime_s','legacy_peak_delta_mib','rss_current_mib','rss_delta_mib','rss_peak_mib','rss_baseline_mib','peak_delta_mib']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(path,value):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)
def gitsha(path):return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,default=ROOT/'build-comprehensive');p.add_argument('--out',type=Path,default=ROOT/'results-comprehensive');p.add_argument('--timeout',type=int,default=180);p.add_argument('--rss-limit-gib',type=float,default=7);p.add_argument('--cgroup-limit-gib',type=float,default=7.5);p.add_argument('--resume',action='store_true');a=p.parse_args()
 if a.timeout<=0 or min(a.rss_limit_gib,a.cgroup_limit_gib)<=0:p.error('positive timeout and memory budgets required')
 a.out.mkdir(exist_ok=True)
 for name in ['runs','stdout','stderr']:(a.out/name).mkdir(exist_ok=True)
 builds=json.loads((a.out/'builds.json').read_text());adapters=(ROOT/'tools/comprehensive_adapters.txt').read_text().split();cpu=min(os.sched_getaffinity(0))
 sources=[ROOT/'CMakeLists.txt',*sorted((ROOT/'src').rglob('*')),*sorted((ROOT/'cmake').glob('*')),Path(__file__)]
 sources={str(x.relative_to(ROOT)):digest(x) for x in sources if x.is_file()}
 binaries={name:digest(a.build/f'bench_{name}__std_hash') for name in adapters if builds.get(name,{}).get('returncode')==0}
 for name in binaries:
  cases=set(subprocess.check_output([str(a.build/f'bench_{name}__std_hash'),'--list'],text=True).splitlines())
  if not set(CASES).issubset(cases):raise RuntimeError(f'Missing native cases in {name}: {set(CASES)-cases}')
 dependencies={x.name:gitsha(x) for x in (ROOT/'external').iterdir() if x.is_dir() and (x/'.git').exists()}
 cache={line.split('=',1)[0].split(':',1)[0]:line.split('=',1)[1] for line in (a.build/'CMakeCache.txt').read_text().splitlines() if '=' in line and not line.startswith(('#','//'))}
 boost_dir=cache.get('MAP_BENCH_BOOST_SOURCE_DIR','')
 if boost_dir and (Path(boost_dir)/'.git').exists():dependencies['modular_boost']=gitsha(Path(boost_dir))
 manifest={'boost_source_dir':boost_dir or None,'boost_package_dir':cache.get('Boost_DIR'),'base_commit':gitsha(ROOT),'source_sha256':sources,'binary_sha256':binaries,'dependencies':dependencies,'cases':CASES,'adapters':adapters,'hash':'std_hash','repeats':1,'timeout_s':a.timeout,'rss_limit_gib':a.rss_limit_gib,'cgroup_limit_gib':a.cgroup_limit_gib,'poll_s':.005,'cpu_affinity':cpu,'cpu':subprocess.check_output(['lscpu'],text=True),'compiler':subprocess.check_output(['c++','--version'],text=True),'thp':Path('/sys/kernel/mm/transparent_hugepage/enabled').read_text().strip(),'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'inherited_rlimit_as':list(resource.getrlimit(resource.RLIMIT_AS)),'unity_build':True,'sflat_process_seed':1,'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 envfile=a.out/'environment.json'
 if a.resume and envfile.exists():
  old=json.loads(envfile.read_text())
  for k in ['source_sha256','binary_sha256','dependencies','cases','adapters','hash','timeout_s','rss_limit_gib','cgroup_limit_gib','cpu_affinity','compiler','unity_build']:
   if old.get(k)!=manifest.get(k):raise RuntimeError('Cannot resume changed configuration: '+k)
 elif (a.out/'runs').glob('*.json') and any((a.out/'runs').glob('*.json')):raise RuntimeError('Existing checkpoints require --resume')
 if not a.resume or not envfile.exists():atomic(envfile,manifest)
 jobs=[]
 for case in CASES:
  order=adapters.copy();random.Random(20261109+CASES.index(case)).shuffle(order)
  priority=[x for x in ['sflat_flat_hash_map','std_unordered_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','google_dense_hash_map','google_sparse_hash_map'] if x in order]
  jobs.extend((x,case) for x in priority+[x for x in order if x not in priority])
 allruns=[]
 for index,(name,case) in enumerate(jobs,1):
  key=name+'__'+case;checkpoint=a.out/'runs'/(key+'.json')
  if a.resume and checkpoint.exists():allruns.append(json.loads(checkpoint.read_text()));continue
  if name not in binaries:
   result={'adapter':name,'case':case,'status':'build_failed','rows':[]};atomic(checkpoint,result);allruns.append(result);continue
  print(f'[{index}/{len(jobs)}] {name} {case}',flush=True)
  start=time.monotonic();reason=None;maxrss=maxhwm=maxvm=maxvmpeak=maxcg=0;stop=None
  before=Path('/sys/fs/cgroup/memory.events').read_text()
  def constraints():
   resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,{cpu})
  env=dict(os.environ,MAP_BENCH_EXTRA_MEMORY='1')
  with (a.out/'stdout'/(key+'.txt')).open('w') as out,(a.out/'stderr'/(key+'.txt')).open('w') as err:
   proc=subprocess.Popen([str(a.build/f'bench_{name}__std_hash'),case],stdout=out,stderr=err,env=env,preexec_fn=constraints)
   heartbeat=0
   while proc.poll() is None:
    try:
     f={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line}
     val=lambda k:int(f.get(k,'0 kB').split()[0])*1024
     rss,hwm,vm,vmp=val('VmRSS'),val('VmHWM'),val('VmSize'),val('VmPeak');cg=int(Path('/sys/fs/cgroup/memory.current').read_text())
     maxrss=max(maxrss,rss);maxhwm=max(maxhwm,hwm);maxvm=max(maxvm,vm);maxvmpeak=max(maxvmpeak,vmp);maxcg=max(maxcg,cg)
     elapsed=time.monotonic()-start
     if rss>a.rss_limit_gib*2**30:reason='rss_watchdog'
     elif cg>a.cgroup_limit_gib*2**30:reason='cgroup_watchdog'
     elif elapsed>a.timeout:reason='timeout'
     if elapsed-heartbeat>5:
      atomic(a.out/'progress.json',{'completed':index-1,'total':len(jobs),'adapter':name,'case':case,'elapsed_s':elapsed,'rss_gib':rss/2**30,'completed_status_counts':{s:sum(r['status']==s for r in allruns) for s in set(r['status'] for r in allruns)}});heartbeat=elapsed
     if reason:
      stop={'rss_bytes':rss,'hwm_bytes':hwm,'vmsize_bytes':vm,'vmpeak_bytes':vmp,'cgroup_bytes':cg,'elapsed_s':elapsed};proc.kill();break
    except (FileNotFoundError,ProcessLookupError):pass
    time.sleep(.005)
   rc=proc.wait()
  stdout=(a.out/'stdout'/(key+'.txt')).read_text(errors='replace');stderr=(a.out/'stderr'/(key+'.txt')).read_text(errors='replace');rows=[];unparsed=[]
  for line in stdout.splitlines():
   fields=next(csv.reader([line],delimiter=';',skipinitialspace=True))
   if len(fields)==13:
    try:
     row=dict(zip(FIELDS,fields));int(row['actual_result'])
     if not all(math.isfinite(float(row[k])) for k in FIELDS[6:]):raise ValueError('nonfinite')
     rows.append(row)
    except ValueError:unparsed.append(line)
   else:unparsed.append(line)
  status=reason or ('ok' if rc==0 else 'process_error')
  if rc and ('benchmark result mismatch' in stderr or 'ERROR: expected' in stdout):status='verification_failed'
  elif rc and ('reserved key' in stderr.lower() or 'reserved marker' in stderr.lower()):status='unsupported_key_domain'
  if status=='ok' and case not in DIAGNOSTICS and (not rows or unparsed):status='invalid_output'
  peak=max(maxhwm,max((int(float(x['rss_peak_mib'])*1048576) for x in rows),default=0))
  result={'adapter':name,'case':case,'kind':'diagnostic' if case in DIAGNOSTICS else 'timed','status':status,'returncode':rc,'wall_s':time.monotonic()-start,'benchmark_s':sum(float(x['runtime_s']) for x in rows),'rss_peak_bytes':peak,'rss_peak_is_lower_bound':status!='ok','observed_rss_bytes':maxrss,'observed_vmsize_bytes':maxvm,'observed_vmpeak_bytes':maxvmpeak,'observed_cgroup_bytes':maxcg,'stop_snapshot':stop,'memory_events_before':before,'memory_events_after':Path('/sys/fs/cgroup/memory.events').read_text(),'rows':rows,'unparsed_lines':unparsed}
  atomic(checkpoint,result);allruns.append(result)
  print(f'  {status} {result["wall_s"]:.2f}s rows={len(rows)} peak={peak/2**30:.3f}GiB',flush=True)
  atomic(a.out/'progress.json',{'completed':index,'total':len(jobs),'last_adapter':name,'last_case':case,'last_status':status,'completed_status_counts':{s:sum(r['status']==s for r in allruns) for s in set(r['status'] for r in allruns)}})
 flat=[]
 for run in allruns:
  flat.extend(dict(adapter=run['adapter'],case_status=run['status'],**row) for row in run['rows'])
 with (a.out/'raw.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['adapter','case_status',*FIELDS]);w.writeheader();w.writerows(flat)
 atomic(a.out/'results.json',allruns)
 print('FINISHED',len(allruns),'processes,',len(flat),'phase rows',flush=True)
if __name__=='__main__':main()
