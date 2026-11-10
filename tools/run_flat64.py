#!/usr/bin/env python3
"""Run selected map_benchmark binaries in fresh, sequential, pinned processes."""
import argparse,csv,hashlib,json,math,os,random,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADAPTERS=['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','google_dense_hash_map','google_sparse_hash_map']
FIELDS=['map','hash','test','measurement_id','measurement','actual_result','runtime_s','legacy_peak_delta_mib','rss_current_mib','rss_minus_input_baseline_mib','rss_peak_mib','rss_input_baseline_mib','rss_peak_minus_input_baseline_mib']

def git_sha(path):
    return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
def metadata(build,cpu):
    repos={'map_benchmark':ROOT,'sflat':ROOT/'external/jclin168__sflat_hash_map','google_sparsehash':ROOT/'external/google__sparsehash','ankerl':ROOT/'external/martinus__unordered_dense','abseil':ROOT/'external/abseil__abseil-cpp'}
    cache=(build/'CMakeCache.txt').read_text()
    cache_values={line.split(':',1)[0]:line.split('=',1)[1] for line in cache.splitlines() if not line.startswith(('#','//')) and ':' in line and '=' in line}
    compiler=cache_values.get('CMAKE_CXX_COMPILER','g++')
    target_flags={}
    for a in ADAPTERS:
        flagfile=build/'CMakeFiles'/f'bench_{a}__std_hash.dir'/'flags.make'
        if flagfile.exists():
            target_flags[a]='\n'.join(line for line in flagfile.read_text().splitlines() if line.startswith(('CXX_DEFINES','CXX_FLAGS')))
        else:
            target_flags[a]='CMake cache fallback: '+json.dumps({k:cache_values.get(k,'') for k in ['CMAKE_CXX_FLAGS','CMAKE_CXX_FLAGS_RELEASE','MAP_BENCH_SFLAT_SEED']},sort_keys=True)
    for line in cache.splitlines():
        for key,label in [('MAP_BENCH_ANKERL_DIR:PATH=','ankerl'),('MAP_BENCH_ABSEIL_DIR:PATH=','abseil'),('MAP_BENCH_BOOST_SOURCE_DIR:PATH=','boost')]:
            if line.startswith(key) and line[len(key):]:repos[label]=Path(line[len(key):])
    files=[ROOT/'CMakeLists.txt',ROOT/'src/app/bench.h',ROOT/'src/app/getRSS.cpp',ROOT/'src/benchmarks/FlatMap64.cpp',ROOT/'src/app/google_hash_map_adapter.h']
    binaries={a:hashlib.sha256((build/f'bench_{a}__std_hash').read_bytes()).hexdigest() for a in ADAPTERS}
    return {'binary_sha256':binaries,'commits':{k:git_sha(v) for k,v in repos.items()},'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'cpu_affinity':cpu,'cpu':subprocess.check_output(['lscpu'],text=True),'compiler':subprocess.check_output([compiler,'--version'],text=True),'target_compile_flags':target_flags,'thp':Path('/sys/kernel/mm/transparent_hugepage/enabled').read_text().strip(),'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'build_directory':str(build),'flags':'C++17; std::hash; actual flags in target_compile_flags','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def parse_output(stdout):
    rows=[]
    for line in stdout.splitlines():
        fields=next(csv.reader([line],delimiter=';',skipinitialspace=True))
        if len(fields)!=len(FIELDS):raise RuntimeError('Unexpected benchmark row: '+line)
        row=dict(zip(FIELDS,fields))
        int(row['actual_result'])
        for k in FIELDS[6:]:
            if not math.isfinite(float(row[k])):raise RuntimeError('Non-finite measurement: '+line)
        rows.append(row)
    return rows

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build-dir',type=Path,default=ROOT/'build-flat64')
    ap.add_argument('--out',type=Path,default=ROOT/'results-flat64')
    ap.add_argument('--sizes',type=int,nargs='+',default=[1000000,10000000,100000000])
    ap.add_argument('--repeats',type=int,default=3)
    ap.add_argument('--cpu',type=int,default=None)
    ap.add_argument('--timeout',type=int,default=1800)
    ap.add_argument('--resume',action='store_true')
    ap.add_argument('--native-only',action='store_true',help='Run two original upstream cases once per adapter')
    args=ap.parse_args()
    if any(n<=0 for n in args.sizes) or args.repeats<=0:ap.error('sizes and repeats must be positive')
    build=args.build_dir.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True);(out/'raw').mkdir(exist_ok=True)
    cpu=args.cpu if args.cpu is not None else min(os.sched_getaffinity(0))
    for a in ADAPTERS:
        if not (build/f'bench_{a}__std_hash').is_file():ap.error('Missing executable for '+a)
    manifest=metadata(build,cpu)
    manifest['native_only']=args.native_only;manifest['sizes']=args.sizes;manifest['repeats']=1 if args.native_only else args.repeats
    previous=out/'environment.json'
    if args.resume and previous.exists():
        old=json.loads(previous.read_text())
        for key in ['binary_sha256','commits','source_sha256','flags','compiler','target_compile_flags','cpu','cpu_affinity','native_only','sizes','repeats']:
            if old.get(key)!=manifest.get(key):
                raise RuntimeError('Cannot resume with changed build/configuration: '+key)
        for key in ['measurement_source_sha256','integration_validation']:
            if key in old:manifest[key]=old[key]
    (out/'environment.json').write_text(json.dumps(manifest,indent=2))
    jobs=[]
    if args.native_only:
        jobs=[(a,0,case,0) for a in ADAPTERS for case in ['CtorDtorSingleEntryMap','AccidentallyQuadratic']]
    else:
        for n in args.sizes:
            for repeat in range(args.repeats):
                batch=[(a,n,case,repeat) for a in ADAPTERS for case in ['FlatMap64Reserved','FlatMap64Grow']]
                random.Random(20261109+n+repeat).shuffle(batch);jobs+=batch
    for index,(adapter,n,case,repeat) in enumerate(jobs,1):
        key=f'{adapter}__{case}__{n}__{repeat}'
        checkpoint=out/'raw'/f'{key}.json'
        if args.resume and checkpoint.exists():
            print(f'[{index}/{len(jobs)}] cached {key}',flush=True);continue
        seed=42+repeat
        env=dict(os.environ,MAP_BENCH_N=str(n),MAP_BENCH_SEED=str(seed),MAP_BENCH_EXTRA_MEMORY='1')
        command=['taskset','-c',str(cpu),str(build/f'bench_{adapter}__std_hash'),case]
        print(f'[{index}/{len(jobs)}] {adapter} {case} N={n} repeat={repeat+1}',flush=True)
        start=time.monotonic()
        result=subprocess.run(command,env=env,text=True,capture_output=True,timeout=args.timeout)
        (out/'raw'/f'{key}.txt').write_text(result.stdout)
        (out/'raw'/f'{key}.stderr').write_text(result.stderr)
        if result.returncode:raise RuntimeError(f'{key}: exit {result.returncode}: {result.stderr}')
        rows=parse_output(result.stdout)
        expected=3 if case in ['FlatMap64Reserved','AccidentallyQuadratic'] else 1
        if len(rows)!=expected:raise RuntimeError(f'{key}: expected {expected} measurements')
        for row in rows:row.update(adapter=adapter,entries=n,repeat=repeat+1,seed=seed,process_wall_s=time.monotonic()-start)
        temporary=checkpoint.with_suffix('.tmp')
        temporary.write_text(json.dumps(rows,indent=2))
        temporary.replace(checkpoint)
        print('  '+', '.join(f"{r['measurement']}: {r['runtime_s']}s, RSS-baseline {r['rss_minus_input_baseline_mib']} MiB" for r in rows),flush=True)
    allrows=[]
    for adapter,n,case,repeat in jobs:
        allrows+=json.loads((out/'raw'/f'{adapter}__{case}__{n}__{repeat}.json').read_text())
    with (out/'raw.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    print(f'Completed {len(jobs)} processes, {len(allrows)} measurements. {out}',flush=True)
if __name__=='__main__':main()
