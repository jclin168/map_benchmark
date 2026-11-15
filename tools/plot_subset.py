#!/usr/bin/env python3
"""Bar charts of the run_subset.sh results: per benchmark, the total time and the peak memory of each map relative to
the best map of that benchmark (log axis, 1x = best). A run killed by the timeout (exit 124 in progress.log) is drawn
as a hatched bar to the edge of the axis and labelled "timeout".

Usage: python3 plot_subset.py RAW_DIR PROGRESS_LOG OUT_DIR
"""
import csv, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

raw, prog, out = sys.argv[1:4]
MAPS = [("sflat_flat_hash_map", "sflat::flat_hash_map", "#2a78d6"),
        ("ankerl_unordered_dense", "ankerl::unordered_dense_map", "#eb6834"),
        ("boost_unordered_flat_map", "boost::unordered_flat_map", "#1baf7a"),
        ("abseil_flat_hash_map", "absl::flat_hash_map", "#eda100"),
        ("std_unordered_map", "std::unordered_map", "#e87ba4")]
MIN_MB = 3.0  # below this the process memory is mostly the runtime, not the map

timeouts = set()
for line in open(prog):
    m = re.search(r"done (\S+) (\S+) exit 124", line)
    if m:
        timeouts.add((m.group(1), m.group(2)))
data = {}  # (hash, bench) -> {map: (seconds, mb) or None for a timeout}
for f in sorted(os.listdir(raw)):
    m = re.match(r"(bench_.+?)\.(.+)\.txt$", f)
    if not m:
        continue
    app, bench = m.groups()
    name, hash_ = app[6:].split("__")
    rows = [r for r in csv.reader(open(os.path.join(raw, f)), delimiter=";", skipinitialspace=True) if len(r) >= 8]
    val = None if (app, bench) in timeouts else (sum(float(r[6]) for r in rows), max(float(r[7]) for r in rows))
    data.setdefault((hash_, bench), {})[name] = val


def plot(hash_, idx, title, xlabel, path, skip_small):
    benches = sorted(b for (h, b) in data if h == hash_)
    if skip_small:
        benches = [b for b in benches if min(v[idx] for v in data[(hash_, b)].values() if v) >= MIN_MB]
    n = len(MAPS)
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(benches) + 2.0), dpi=200)
    ratios = []
    for bi, b in enumerate(benches):
        d = data[(hash_, b)]
        best = min(v[idx] for v in d.values() if v)
        for mi, (key, label, color) in enumerate(MAPS):
            ratios.append(d[key][idx] / best if d.get(key) else None)
    top = max(r for r in ratios if r) * 1.8
    L = 0.9  # the best map (1x) gets a short bar instead of none
    for bi, b in enumerate(benches):
        d = data[(hash_, b)]
        best = min(v[idx] for v in d.values() if v)
        for mi, (key, label, color) in enumerate(MAPS):
            y = bi + (mi - (n - 1) / 2) * 0.15
            v = d.get(key)
            if v is None:
                ax.barh(y, top - L, left=L, height=0.13, color="none", edgecolor=color, hatch="////", linewidth=0.6)
                ax.text(top / 1.05, y, "timeout", ha="right", va="center", fontsize=5.5, color="#52514e")
            else:
                r = v[idx] / best
                ax.barh(y, r - L, left=L, height=0.13, color=color, edgecolor="#fcfcfb", linewidth=0.4)
                if mi == 0 or r == 1:  # label the first map (sflat) and the best one
                    ax.text(r * 1.04, y, "%.2fx (%.4g)" % (r, v[idx]), va="center", fontsize=5.5, color="#52514e")
    ax.set_xscale("log")
    ax.set_xlim(L, top)
    ax.set_yticks(range(len(benches)))
    ax.set_yticklabels(benches, fontsize=7)
    ax.set_xlabel(xlabel, fontsize=8)
    ticks = [t for t in (1, 1.25, 1.5, 2, 3, 5, 10, 20, 50, 100, 200) if L <= t <= top]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: "%gx" % x))
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_ylim(len(benches) - 0.5, -0.5)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(True, axis="x", which="major", linewidth=0.3, color="#d9d8d3")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    handles = [Patch(facecolor=c, label=l) for _, l, c in MAPS] + \
              [Patch(facecolor="none", edgecolor="#52514e", hatch="////", label="timeout (300 s)")]
    # fixed margins in inches: title, then the legend (3 columns x 2 rows), then the plot, so they cannot overlap
    H = fig.get_figheight()
    fig.suptitle(title, fontsize=8, x=0.02, ha="left", y=1 - 0.12 / H)
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.02, 1 - 0.45 / H), ncol=3, fontsize=7, frameon=False)
    fig.subplots_adjust(left=0.2, right=0.98, bottom=0.55 / H, top=1 - 1.25 / H)
    fig.savefig(path, facecolor="#fcfcfb")
    plt.close(fig)


os.makedirs(out, exist_ok=True)
for hash_ in ("std_hash", "ankerl_hash"):
    plot(hash_, 0, "Total time per benchmark, %s. Labels: sflat and the best map, as ratio (seconds)" % hash_,
         "time relative to the fastest map of the benchmark (log scale)", os.path.join(out, "time_%s.png" % hash_), False)
    plot(hash_, 1, "Peak memory per benchmark, %s. Labels: sflat and the smallest, as ratio (MB). Benchmarks under %g MB left out" % (hash_, MIN_MB),
         "peak MB reported by the benchmark, relative to the smallest (log scale)", os.path.join(out, "memory_%s.png" % hash_), True)
print("wrote", sorted(os.listdir(out)))
