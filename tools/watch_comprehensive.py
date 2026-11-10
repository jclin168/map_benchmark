#!/usr/bin/env python3
"""Print progress and refresh snapshots; the finalizer owns completed reports."""
import argparse,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--out',type=Path,default=ROOT/'results-comprehensive')
 a=p.parse_args();out=a.out.resolve();last_count=-5;last_case=None
 while True:
  current=json.loads((out/'progress.json').read_text())
  print(json.dumps(current),flush=True)
  count=current['completed'];case=current.get('case',current.get('last_case'))
  if count<current['total'] and (count-last_count>=5 or case!=last_case):
   subprocess.run(['python3',str(ROOT/'tools/summarize_comprehensive.py'),str(out)],check=True)
   last_count=count;last_case=case
  if (out/'completion.json').exists():
   print('COMPLETE',flush=True);break
  time.sleep(45)
if __name__=='__main__':main()
