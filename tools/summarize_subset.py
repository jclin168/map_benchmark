"""Summarize the raw output of run_subset.sh: per benchmark and map, total seconds (sum of the sub-benchmarks) and
peak MB. A run killed by the timeout (exit 124 in progress.log) is shown as 'timeout'."""
import re, sys, os, csv, collections
raw, prog = sys.argv[1], sys.argv[2]
to = set()
for l in (l for f in prog.split(",") for l in open(f)):
    m = re.search(r"done (\S+) (\S+) exit 124", l)
    if m: to.add((m.group(1), m.group(2)))
data = collections.defaultdict(dict)
for f in sorted(os.listdir(raw)):
    if not f.endswith(".txt"): continue
    app, bench = re.match(r"(bench_.+?)\.(.+)\.txt", f).groups()
    rows = [r for r in csv.reader(open(os.path.join(raw, f)), delimiter=";", skipinitialspace=True, quotechar='"') if len(r) >= 8]
    t = sum(float(r[6]) for r in rows); mem = max([float(r[7]) for r in rows] or [0])
    data[(bench, app.split("__")[1])][app.split("__")[0][6:]] = "timeout" if (app, bench) in to else (t, mem)
names = ["sflat_flat_hash_map", "bflat_unordered_flat_map", "ankerl_unordered_dense", "boost_unordered_flat_map", "abseil_flat_hash_map", "std_unordered_map"]
for hash_ in ("std_hash", "ankerl_hash"):
    for what, idx in (("total seconds", 0), ("peak MB", 1)):
        print("\n### %s, %s\n" % (hash_, what))
        print("| benchmark | " + " | ".join(n.replace("_", "::", 1) if False else n for n in names) + " |")
        print("|---|" + "---|" * len(names))
        for (bench, h), d in sorted(data.items()):
            if h != hash_: continue
            vals = [v[idx] if isinstance(v, tuple) else None for v in (d.get(n) for n in names)]
            ok = [v for v in vals if v is not None]; best = min(ok) if ok else None
            cells = []
            for n, v in zip(names, vals):
                if d.get(n) == "timeout": cells.append("timeout")
                elif v is None: cells.append("-")
                else: cells.append(("**%.1f**" if v == best else "%.1f") % v)
            print("| %s | %s |" % (bench, " | ".join(cells)))
