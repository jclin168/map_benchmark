#!/usr/bin/env python3
"""Summarize completed and failed streaming insert probes without extrapolation."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
manifest=json.loads((d/'environment.json').read_text()); results=json.loads((d/'results.json').read_text())
n=manifest['entries']; cap=manifest['limit_address_space_bytes']/2**30
names=['sflat','Boost flat','Ankerl dense','Abseil flat','Google dense','Google sparse'];rows=[]
for name,r in zip(names,results):
    last=r['last']; complete=r['returncode']==0 and last and last['status']=='completed' and int(last['inserted'])==n
    if last:
        baseline=int(last['baseline_bytes']);rss=(int(last['rss_bytes'])-baseline)/2**30;peak=max(0,int(last['peak_bytes'])-baseline)/2**30
    else:rss=peak=None
    rows.append(dict(map=name,target_entries=n,completed=complete,returncode=r['returncode'],last_status=last['status'] if last else 'no_record',last_confirmed_entries=int(last['inserted']) if last else 0,rss_delta_gib=rss,peak_delta_gib=peak))
with (d/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
lines=['# 500M insert-only test without reserve: limited-environment diagnostic','',
 f'The target is {n:,} entries. The key and value types are uint64_t. '
 'Each map starts empty and uses native insert calls. The test does not call reserve or find. '
 'A bijection generates unique keys during the test. Inputs exclude Google marker keys. '
 'There is no input array proportional to N. Each map uses a separate process. '
 'All maps use std::hash, the same CPU affinity, and recorded versions and build settings. '
 'Elapsed time includes key generation and each 10M checkpoint.','',
 f'The environment has an 8 GiB memory limit and no swap. RLIMIT_AS is {cap:g} GiB. '
 'This limit measures virtual address space. It does not limit RSS directly. '
 'Untouched mmap mappings and old/new growth allocations count toward this limit. '
 'A failure count does not establish the physical capacity of 8 GiB RAM.','',
 f'{sum(r["completed"] for r in rows)}/{len(rows)} maps completed {n:,} entries. '
 'Incomplete rows have no completed-target measurement. No extrapolation or equal-entry rank is used.','',
 '| Map | Status | Last confirmed entries | RSS increase at record GiB | Peak increase at record GiB |',
 '|---|---|---:|---:|---:|']
for r in rows:
    status='Complete' if r['completed'] else ('Allocation failed' if r['last_status']=='allocation_failed' else f'Process stopped, rc={r["returncode"]}; checkpoint only')
    lines.append(f'| {r["map"]} | {status} | {r["last_confirmed_entries"]:,} | {r["rss_delta_gib"]:.3f} | {r["peak_delta_gib"]:.3f} |')
lines+=['','## Interpretation','',
 'RSS and peak values subtract the process baseline before map creation. '
 'Different kernel accounting methods can give small differences. '
 'Allocation-failure rows are read in the catch block before map destruction. '
 'Signal-stop rows contain only the last checkpoint. Entry counts and peaks are confirmed lower bounds. '
 'They are not peaks at the time of termination. RSS after failure does not establish usable map memory.','',
 'In the recorded 500M test, Google sparse reported failed reallocation and exit 1. '
 'Google dense ended with SIGSEGV. Both rows retain only the last checkpoint. '
 'The recorded cgroup OOM and OOM-kill counts were 0.','',
 'The key/value payload for 500M entries of 16 bytes is 7.451 GiB. '
 'Empty slots, indexes, allocation overhead, and growth need more memory. '
 'This environment cannot provide six complete 500M measurements. '
 'Use a machine with at least 32 GiB for that test. Keep sufficient memory for the operating system.','',
 '## Repeat the test','', '```sh',
 'python3 tools/run_insert_stream.py --entries 500000000 --limit-gib 0',
 'python3 tools/summarize_insert_stream.py results-flat64-500m','```','',
 'The tool builds separate build-flat64-stream executables. Existing 1M, 10M, and 100M benchmark binaries are unchanged. '
 'The files retain 10M checkpoints, stderr, exit status, binary hashes, dependency commits, and environment settings.']
(d/'REPORT.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
