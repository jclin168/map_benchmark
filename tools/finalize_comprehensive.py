#!/usr/bin/env python3
"""Validate, check the restored-environment boundary, and package the full suite."""
import argparse,csv,hashlib,json,os,shutil,subprocess,tempfile,time,zipfile
from pathlib import Path
from run_comprehensive import ROOT,CASES

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2));t.replace(p)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'results-comprehensive');p.add_argument('--build',type=Path,default=ROOT/'build-comprehensive');p.add_argument('--bundle',type=Path,default=ROOT/'map-benchmark-comprehensive.zip');p.add_argument('--patch',type=Path,default=ROOT/'map-benchmark-comprehensive.patch');p.add_argument('--wait',action='store_true');a=p.parse_args();out=a.out.resolve()
 env=json.loads((out/'environment.json').read_text());expected={(n,c) for n in env['adapters'] for c in CASES};assert len(expected)==780
 while True:
  done=out/'results.json'
  if done.exists():
   rows=json.loads(done.read_text())
   if {(r['adapter'],r['case']) for r in rows}==expected:break
  if not a.wait:raise RuntimeError('Main suite not complete')
  time.sleep(10)
 time.sleep(2)
 print('MAIN SUITE COMPLETE; verifying restore boundary',flush=True)
 boundary=out/'epoch-recheck';marker=boundary/'record.json'
 if (out/'resumptions.json').exists() and not marker.exists():
  boundary.mkdir(exist_ok=True);name='sflat_flat_hash_map__RandomDistinct2';old=out/'runs'/(name+'.json')
  with tempfile.TemporaryDirectory(prefix='map-suite-boundary-',dir='/tmp') as td:
   mirror=Path(td)/'results';mirror.mkdir()
   for f in ['environment.json','builds.json']:shutil.copy2(out/f,mirror/f)
   for folder in ['runs','stdout','stderr']:
    shutil.copytree(out/folder,mirror/folder)
   (mirror/'runs'/(name+'.json')).unlink()
   with (boundary/'recheck.log').open('w') as log:
    subprocess.run(['python3',str(ROOT/'tools/run_comprehensive.py'),'--build',str(a.build.resolve()),'--out',str(mirror),'--resume'],stdout=log,stderr=subprocess.STDOUT,check=True)
   for label,base in [('original',out),('restored',mirror)]:
    d=boundary/label;d.mkdir(exist_ok=True)
    shutil.copy2(base/'runs'/(name+'.json'),d/'result.json')
    for stream in ['stdout','stderr']:shutil.copy2(base/stream/(name+'.txt'),d/(stream+'.txt'))
   original=json.loads((boundary/'original/result.json').read_text());replacement=json.loads((boundary/'restored/result.json').read_text())
   for folder,suffix in [('runs','.json'),('stdout','.txt'),('stderr','.txt')]:
    dest=out/folder/(name+suffix);tmp=dest.with_suffix('.replacement');shutil.copy2(mirror/folder/(name+suffix),tmp);tmp.replace(dest)
   for f in ['raw.csv','results.json']:shutil.copy2(mirror/f,out/f)
   write_json(marker,{'reason':'The original sflat RandomDistinct2 checkpoint preceded the environment loss; the other38 maps for that case were measured in the restored environment. Exactly one recheck uses the same executable and original inputs in the restored environment. The restored sample is selected by epoch, irrespective of whether it is faster; both samples are preserved.','original_benchmark_s':original['benchmark_s'],'restored_benchmark_s':replacement['benchmark_s'],'original_status':original['status'],'restored_status':replacement['status'],'primary_sample':'restored','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
 rows=json.loads((out/'results.json').read_text());assert len(rows)==780 and {(r['adapter'],r['case']) for r in rows}==expected
 for name,v in env['binary_sha256'].items():assert sha(a.build/f'bench_{name}__std_hash')==v,name
 for name,v in env['source_sha256'].items():assert sha(ROOT/name)==v,name
 builds=json.loads((out/'builds.json').read_text());assert len(builds)==39 and all(x['returncode']==0 for x in builds.values())
 for r in rows:
  disk=json.loads((out/'runs'/(r['adapter']+'__'+r['case']+'.json')).read_text());assert r==disk
 hashes={r['hash_label'] for job in rows for r in job.get('rows',[])};assert hashes=={'std::hash'},hashes
 subprocess.run(['python3',str(ROOT/'tools/summarize_comprehensive.py'),str(out)],check=True)
 record={'unique_pairs':len(rows),'adapters':39,'native_cases':20,'retained_process_results':780+int(marker.exists()),'uncheckpointed_interrupted_attempts_not_counted':True,'builds_passed':39,'source_and_binary_sha256_verified':True,'hash_labels':sorted(hashes),'status_counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},'oom_kill_event_cases':sum(dict(line.split() for line in r.get('memory_events_after','').splitlines()).get('oom_kill')!=dict(line.split() for line in r.get('memory_events_before','').splitlines()).get('oom_kill') for r in rows)}
 write_json(out/'publication-validation.json',record)
 paths=set(subprocess.check_output(['git','diff','HEAD','--name-only','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
 paths.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
 allowed=['src/','cmake/','docs/','tests/','tools/','external/'];names=['.gitignore','.gitmodules','CMakeLists.txt','README.md']
 paths=sorted(x for x in paths if x and (x in names or any(x.startswith(prefix) for prefix in allowed)))
 with tempfile.TemporaryDirectory(prefix='map-suite-patch-',dir='/tmp') as td:
  git_env=dict(os.environ,GIT_INDEX_FILE=str(Path(td)/'index'))
  for args in [['read-tree','HEAD'],['add','--',*paths]]:subprocess.run(['git',*args],cwd=ROOT,env=git_env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  patch=subprocess.check_output(['git','diff','--cached','--binary','--full-index','HEAD'],cwd=ROOT,env=git_env)
  patchpath=a.patch.resolve();patchpath.write_bytes(patch)
  if patch:
   subprocess.run(['git','apply','--reverse','--check',str(patchpath)],cwd=ROOT,check=True)
   checkout=Path(td)/'baseline';subprocess.run(['git','clone','--quiet','--no-hardlinks',str(ROOT),str(checkout)],check=True)
   subprocess.run(['git','apply','--check',str(patchpath)],cwd=checkout,check=True)
 with zipfile.ZipFile(str(a.bundle.resolve()),'w',zipfile.ZIP_DEFLATED) as z:
  z.write(patchpath,'integration.patch');z.write(ROOT/'LICENSE','LICENSE')
  for f in out.rglob('*'):
   if f.is_file() and f.resolve()!=a.bundle.resolve():z.write(f,str(Path('results-comprehensive')/f.relative_to(out)))
  for f in paths:
   if (ROOT/f).is_file():z.write(ROOT/f,'source/'+f)
  for f in ['comprehensive-progress.log','comprehensive-resume.log','comprehensive-adapter-tests.log','build-comprehensive.log']:
   if (ROOT/f).exists():z.write(ROOT/f,'validation/'+f)
 with zipfile.ZipFile(str(a.bundle.resolve())) as z:assert z.testzip() is None
 write_json(out/'completion.json',{'complete':True,'validation':record,'patch':str(patchpath),'zip':str(a.bundle.resolve())})
 print('FINALIZED',json.dumps(record),flush=True)
if __name__=='__main__':main()
