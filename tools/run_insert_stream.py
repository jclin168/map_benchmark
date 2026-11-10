#!/usr/bin/env python3
"""Build separate streaming insert probes using existing CMake target flags/libraries."""
import argparse,csv,hashlib,json,os,resource,shlex,subprocess,time
from pathlib import Path
from run_flat64 import ADAPTERS,ROOT,metadata
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--entries',type=int,default=500000000)
p.add_argument('--limit-gib',type=float,default=7)
p.add_argument('--rss-limit-gib',type=float,default=0,help='Sampled process RSS watchdog; 0 disables. Not a virtual-address limit.')
p.add_argument('--cgroup-limit-gib',type=float,default=0,help='Sampled total cgroup memory watchdog; 0 disables.')
p.add_argument('--timeout',type=int,default=3600)
p.add_argument('--out',type=Path,default=ROOT/'results-flat64-500m')
a=p.parse_args()
if a.entries <= 0 or min(a.limit_gib,a.rss_limit_gib,a.cgroup_limit_gib) < 0 or a.timeout <= 0: p.error('entries/timeout must be positive; limit-gib must be nonnegative')
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
build=ROOT/'build-flat64'; dest=ROOT/'build-flat64-stream';dest.mkdir(exist_ok=True)
cpu=min(os.sched_getaffinity(0));limit=int(a.limit_gib*2**30)
manifest=metadata(build,cpu)
manifest.update(inherited_rlimit_as=resource.getrlimit(resource.RLIMIT_AS),entries=a.entries,limit_address_space_bytes=limit,rss_limit_bytes=int(a.rss_limit_gib*2**30),cgroup_watchdog_bytes=int(a.cgroup_limit_gib*2**30),watchdog_poll_seconds=0.005,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input='streaming bijective uint64; no input vector; no reserve; includes key generation and checkpoint overhead',source_sha256_stream=hashlib.sha256((ROOT/'tools/insert_stream.cpp').read_bytes()).hexdigest())
(out/'environment.json').write_text(json.dumps(manifest,indent=2))
(out/'insert_stream.measured.cpp').write_bytes((ROOT/'tools/insert_stream.cpp').read_bytes())
(out/'memory.events.before').write_text(Path('/sys/fs/cgroup/memory.events').read_text())
results=[]
for adapter in ADAPTERS:
    target=f'bench_{adapter}__std_hash'; td=build/'CMakeFiles'/f'{target}.dir'
    flags={line.split(' = ',1)[0]:line.split(' = ',1)[1] for line in (td/'flags.make').read_text().splitlines() if ' = ' in line}
    obj=dest/f'{adapter}.o'; binary=dest/adapter
    subprocess.run(['/usr/bin/c++',*shlex.split(' '.join(flags[k] for k in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'])),'-c',str(ROOT/'tools/insert_stream.cpp'),'-o',str(obj)],check=True)
    original=shlex.split((td/'link.txt').read_text()); tail=original[original.index('-o')+2:]
    subprocess.run([original[0],'-O3','-march=native',str(obj),str(td/'src/app/getRSS.cpp.o'),'-o',str(binary),*tail],cwd=build,check=True)
    print('START',adapter,'N',a.entries,flush=True)
    def constraints():
        if limit: resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        os.sched_setaffinity(0,{cpu})
    begin=time.monotonic(); reason=None; observed_rss=0; observed_hwm=0; observed_cgroup=0; observed_vms=0; observed_vmpeak=0; stop_snapshot=None
    with (out/f'{adapter}.csv').open('w') as stdout, (out/f'{adapter}.stderr').open('w') as stderr:
        process=subprocess.Popen([str(binary),str(a.entries)],stdout=stdout,stderr=stderr,preexec_fn=constraints)
        while process.poll() is None:
            try:
                fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{process.pid}/status').read_text().splitlines() if ':' in line}
                rss=int(fields.get('VmRSS','0 kB').split()[0])*1024
                hwm=int(fields.get('VmHWM','0 kB').split()[0])*1024
                vms=int(fields.get('VmSize','0 kB').split()[0])*1024
                vmpeak=int(fields.get('VmPeak','0 kB').split()[0])*1024
                observed_vms=max(observed_vms,vms);observed_vmpeak=max(observed_vmpeak,vmpeak)
                cg=int(Path('/sys/fs/cgroup/memory.current').read_text())
                observed_rss=max(observed_rss,rss);observed_hwm=max(observed_hwm,hwm);observed_cgroup=max(observed_cgroup,cg)
                if a.rss_limit_gib and rss > a.rss_limit_gib*2**30: reason='rss_watchdog'
                elif a.cgroup_limit_gib and cg > a.cgroup_limit_gib*2**30: reason='cgroup_watchdog'
                elif time.monotonic()-begin > a.timeout: reason='timeout'
                if reason:
                    stop_snapshot={'rss_bytes':rss,'rss_hwm_bytes':hwm,'vmsize_bytes':vms,'vmpeak_bytes':vmpeak,'cgroup_bytes':cg,'elapsed_s':time.monotonic()-begin}
                    process.kill();break
            except (FileNotFoundError, ProcessLookupError): pass
            time.sleep(.005)
        rc=process.wait()
    rows=list(csv.DictReader((out/f'{adapter}.csv').open()))
    result={'map':adapter,'returncode':rc,'stop_reason':reason or ('completed' if rc==0 else 'process_error'),'observed_rss_max_bytes':observed_rss,'observed_hwm_max_bytes':observed_hwm,'observed_cgroup_max_bytes':observed_cgroup,'observed_vmsize_max_bytes':observed_vms,'observed_vmpeak_max_bytes':observed_vmpeak,'stop_snapshot':stop_snapshot,'wall_s':time.monotonic()-begin,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'last':rows[-1] if rows else None}
    results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(result),flush=True)

(out/'memory.events.after').write_text(Path('/sys/fs/cgroup/memory.events').read_text())
