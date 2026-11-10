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
lines=[f'# {n/1e6:g}M insert test without reserve: VmSize and RSS','',
 'The key and value types are uint64_t. Unique keys are generated during the test. No input array is allocated. '
 'The test does not call reserve or find. Each map runs in a separate process. '
 'All six maps use std::hash, the same input order, CPU affinity, and recorded versions and build settings.',
 f'The target is {n:,} entries. {sum(x["completed"] for x in rows)}/6 maps completed the target.','',
 '## Memory terms','',
 'All values cover the full process. No baseline is subtracted. Original CSV files retain the baseline. '
 'VmSize is the current virtual address space. It includes reserved mappings that are not resident. '
 'RSS is the current resident memory. VmPeak is the highest process VmSize. '
 'RSS peak is the maximum of getrusage and observed VmHWM. The two peaks can occur at different times. '
 'One GiB is 2^30 bytes.','',
 '## Complete tests: after the last insertion','',
 'The map is still alive at this measurement.','',
 '| Map | Entries | VmSize GiB | RSS GiB | VmPeak GiB | RSS peak GiB |',
 '|---|---:|---:|---:|---:|---:|']
for x in rows:
 if x['completed']:lines.append(f'| {x["map"]} | {n:,} | {x["vmsize_gib"]:.3f} | {x["rss_gib"]:.3f} | {x["vmpeak_gib"]:.3f} | {x["rss_peak_gib"]:.3f} |')
lines+=['','## Incomplete tests: sample before SIGKILL','',
 '| Map | Last confirmed entries, lower bound | VmSize at stop GiB | RSS at stop GiB | Observed VmPeak GiB | Observed RSS peak GiB |',
 '|---|---:|---:|---:|---:|---:|']
for x in rows:
 if not x['completed']:lines.append(f'| {x["map"]} | ≥{x["last_confirmed_entries"]:,} | {x["vmsize_gib"]:.3f} | {x["rss_gib"]:.3f} | ≥{x["vmpeak_gib"]:.3f} | ≥{x["rss_peak_gib"]:.3f} |')
lines+=['',
 f'An incomplete row is a stop sample. It is not memory use after {n/1e6:g}M entries. '
 f'It does not establish the full peak required to finish {n/1e6:g}M entries. '
 'The last confirmed count comes from a 10M checkpoint. The true count at termination can be higher. '
 'Allocations can occur between the sample and SIGKILL. Incomplete peaks are lower bounds.','',
 '## Resource limits and data sources','',
 'RLIMIT_AS soft and hard limits are unlimited. The test sets no virtual-address limit.',
 f'The monitor samples RSS about every {m["watchdog_poll_seconds"]*1000:g} ms. '
 f'The process RSS stop level is {m["rss_limit_bytes"]/2**30:g} GiB. '
 f'The environment memory.current stop level is {m["cgroup_watchdog_bytes"]/2**30:g} GiB. '
 'The cgroup hard limit is 8 GiB. Swap is disabled. '
 'Total memory includes other processes and page cache. The total-memory stop can occur first. '
 'This sampled monitor is separate from the unenforced Linux RLIMIT_RSS.','',
 'Complete tests read VmSize and VmPeak from /proc/self/status. They read RSS from smaps_rollup. '
 'Incomplete tests use VmSize and RSS from one external /proc/PID/status sample. '
 'The two kernel RSS accounting methods can give small differences.','',
 '## Repeat the test','', '```sh',
 f'python3 tools/run_insert_stream.py --entries {n} --limit-gib 0 --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out {d.name}',
 f'python3 tools/summarize_insert_vm_rss.py {d.name}','```','',
 'The files retain original CSV, stop samples, observed peaks, metadata, source and binary hashes, dependency revisions, and measured C++ source. '
 'They also retain OOM event counts before and after the test. '
 'This is one memory test. Elapsed time includes key generation, checkpoints, and monitoring. '
 'Do not combine these elapsed times with the earlier insert-only timing ranks.']
(d/'REPORT.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
