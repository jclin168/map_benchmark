#!/usr/bin/env python3
"""Build every selected adapter independently and retain build failures."""
import argparse,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--cmake',default='cmake');p.add_argument('--build',type=Path,default=ROOT/'build-comprehensive');p.add_argument('--out',type=Path,default=ROOT/'results-comprehensive');p.add_argument('--retry-failed',action='store_true');a=p.parse_args()
a.out.mkdir(exist_ok=True);(a.out/'build-logs').mkdir(exist_ok=True)
manifest=a.out/'builds.json';results=json.loads(manifest.read_text()) if manifest.exists() else {}
for name in (ROOT/'tools/comprehensive_adapters.txt').read_text().split():
 path=ROOT/'src/maps'/name
 if not (path/'Map.h').exists():continue
 name=path.name
 if name in results and (not a.retry_failed or results[name]['returncode']==0):continue
 target=f'bench_{name}__std_hash';start=time.monotonic();log=a.out/'build-logs'/f'{name}.log'
 print('BUILD',name,flush=True)
 with log.open('w') as f:
  try:r=subprocess.run([a.cmake,'--build',str(a.build),'--target',target,'-j','2'],stdout=f,stderr=subprocess.STDOUT,timeout=600);rc=r.returncode
  except subprocess.TimeoutExpired:rc=124
 results[name]={'returncode':rc,'elapsed_s':time.monotonic()-start,'target':target,'log':str(log.relative_to(a.out))}
 tmp=manifest.with_suffix('.tmp');tmp.write_text(json.dumps(results,indent=2));tmp.replace(manifest)
 print('DONE',name,rc,round(results[name]['elapsed_s'],1),flush=True)
print('Built',sum(v['returncode']==0 for v in results.values()),'/',len(results),flush=True)
