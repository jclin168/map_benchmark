#!/usr/bin/env python3
"""Report completed insert RSS separately from incomplete RSS-limited attempts."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
m=json.loads((d/'environment.json').read_text());results=json.loads((d/'results.json').read_text())
assert m['limit_address_space_bytes']==0 and m['inherited_rlimit_as']==[-1,-1]
n=m['entries']; names=dict(zip(['sflat_flat_hash_map','boost_unordered_flat_map','ankerl_unordered_dense','abseil_flat_hash_map','google_dense_hash_map','google_sparse_hash_map'],['sflat','Boost flat','Ankerl dense','Abseil flat','Google dense','Google sparse']))
assert len(results)==len(names)
rows=[]
for r in results:
    last=r['last']; complete=r['returncode']==0 and last and last['status']=='completed' and int(last['inserted'])==n
    baseline=int(last['baseline_bytes']) if last else 0
    peak=max(r['observed_hwm_max_bytes'],int(last['peak_bytes']) if last else 0)
    rows.append(dict(map=names[r['map']],target_entries=n,completed=bool(complete),stop_reason=r['stop_reason'],returncode=r['returncode'],last_confirmed_entries=int(last['inserted']) if last else 0,final_rss_delta_gib=(int(last['rss_bytes'])-baseline)/2**30 if complete else '',peak_delta_gib=max(0,peak-baseline)/2**30,peak_is_lower_bound=not complete,observed_cgroup_max_gib=r['observed_cgroup_max_bytes']/2**30,completed_elapsed_s=float(last['elapsed_s']) if complete else ''))
with (d/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
count=sum(x['completed'] for x in rows)
lines=[f'# {n/1e6:g}M insert test without reserve: RSS monitor','',
 f'The target is {n:,} entries. {count}/6 maps completed the target.',
 'The key and value types are uint64_t. Each test starts with an empty map. It uses native insert calls. '
 'It does not call reserve or find. Unique keys are generated during the test. No input array is allocated. '
 'Inputs exclude Google marker keys. Each map runs in one separate process. '
 'All maps use std::hash, the same CPU affinity, and the recorded versions and build settings. '
 'Memory and progress records occur every 10M insertions. Elapsed time includes key generation, monitoring, and progress output.','',
 '## Resource limits','',
 'RLIMIT_AS soft and hard limits are unlimited. The test sets no virtual-address limit.',
 f'The monitor reads VmRSS and VmHWM from /proc/PID/status about every {m["watchdog_poll_seconds"]*1000:g} ms. '
 f'The RSS stop level is {m["rss_limit_bytes"]/2**30:g} GiB. '
 f'The environment memory.current stop level is {m["cgroup_watchdog_bytes"]/2**30:g} GiB. '
 'The monitor sends SIGKILL when either level is exceeded. The cgroup hard limit is 8 GiB. Swap is disabled. '
 'This sampled monitor is separate from RLIMIT_RSS. Linux does not enforce RLIMIT_RSS. A peak can exceed the stop level between samples.','',
 '| Map | Target complete | Last confirmed entries | Final RSS GiB | Observed peak GiB | Stop reason |',
 '|---|---|---:|---:|---:|---|']
for r in rows:
    rss=f'{r["final_rss_delta_gib"]:.3f}' if r['completed'] else '—'
    peak=('≥' if r['peak_is_lower_bound'] else '')+f'{r["peak_delta_gib"]:.3f}'
    lines.append(f'| {r["map"]} | {"Yes" if r["completed"] else "No"} | {r["last_confirmed_entries"]:,} | {rss} | {peak} | {r["stop_reason"]} |')
lines+=['','## Measurement limits','',
 'RSS and peak values subtract the process baseline before map creation. '
 'For a complete test, smaps_rollup gives RSS after the last insertion. The map is still alive. '
 'The peak is the maximum of process getrusage and observed VmHWM. '
 'An incomplete test has no final RSS at the target size. Its peak is an observed lower bound. '
 'The last confirmed count comes from the last 10M checkpoint. The true count at termination can be higher.','',
 'The RSS monitor counts resident pages in the full process. The cgroup monitor also counts other processes and page cache. '
 'The cgroup stop can occur first. A stopped test did not finish within these monitor levels. '
 'Its observations do not establish the full peak required to finish. They do not establish an exact capacity for an 8 GiB machine.','',
 '## Repeat the test','', '```sh',
 f'python3 tools/run_insert_stream.py --entries {n} --limit-gib 0 --rss-limit-gib 7 --cgroup-limit-gib 7.5 --out {d.name}',
 f'python3 tools/summarize_insert_rss.py {d.name}','```','',
 'The files retain settings, source and binary hashes, dependency revisions, checkpoints, exit status, stop reasons, and observed maxima. '
 'They also retain cgroup memory.events before and after the test. '
 'The earlier 500M diagnostic used RLIMIT_AS. This test stops on observed resident memory or total environment memory.']
(d/'REPORT.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
