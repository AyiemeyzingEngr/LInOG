#!/usr/bin/env python3
"""Reference-candidate table from a stackStripMap pass-1 run.  Run from WORK_DIR.

v2 fix: stackStripMap prints per-date perpendicular baselines RELATIVE to the
implicit pass-1 reference (date 1), which therefore reads 0.0 and is omitted
from the block entirely.  v1 lost that date and every pair touching it -- on
f0320 that was 20070203 and nine pairs, silently undercounting nine other
dates by one degree each.  Same date-1-is-the-datum idiom as invertMisreg.py
(gate G16).  Any date in phase1_dates.json absent from the block is now seeded
at 0.0 and labelled DATUM.                              LInOG 2026-08-28
"""
import argparse, collections, glob, json, re, sys
from datetime import datetime

ap = argparse.ArgumentParser()
ap.add_argument("--log", default="")
ap.add_argument("--pairs", default="run_files/run_08_igram")
ap.add_argument("--dates", default="phase1_dates.json")
a = ap.parse_args()

logf = a.log or sorted(glob.glob("logs/08_stack_config.log.v*"))[-1]
txt = open(logf, errors="replace").read()
bp = {m.group(1): float(m.group(2))
      for m in re.finditer(r'^\s*(\d{8})\s*:\s*(-?\d+\.\d+)\s*$', txt, re.M)}
if not bp:
    print("*** no per-date baselines found in %s" % logf); sys.exit(1)

meta = {r["date"]: r for r in json.load(open(a.dates))}
missing = [d for d in meta if d not in bp]
if len(missing) > 1:
    print("*** %d dates absent from the baseline block, expected at most 1: %s"
          % (len(missing), missing)); sys.exit(1)
datum = missing[0] if missing else None
if datum: bp[datum] = 0.0

raw = open(a.pairs, errors="replace").read()
pairs = set()
for m in re.finditer(r'(\d{8})[_-](\d{8})', raw):
    x, y = m.group(1), m.group(2)
    if x in bp and y in bp and x != y:
        pairs.add(tuple(sorted((x, y))))
nlines = sum(1 for L in open(a.pairs) if L.strip())

mode = {d: meta.get(d, {}).get("mode", "?") for d in bp}
px   = {d: meta.get(d, {}).get("px", 0)     for d in bp}
mfbs = collections.Counter(px[d] for d in bp if mode[d] == "FBS").most_common(1)
mfbs = mfbs[0][0] if mfbs else 0

deg, maxbp = collections.Counter(), collections.defaultdict(float)
for x, y in pairs:
    deg[x] += 1; deg[y] += 1
    s = abs(bp[x] - bp[y]); maxbp[x] = max(maxbp[x], s); maxbp[y] = max(maxbp[y], s)

mid = (max(bp.values()) + min(bp.values())) / 2.0
ds  = sorted(bp); t = {d: datetime.strptime(d, "%Y%m%d") for d in ds}
tmid = t[ds[0]] + (t[ds[-1]] - t[ds[0]]) / 2

print("pairs parsed=%d   run_08_igram lines=%d   %s"
      % (len(pairs), nlines, "MATCH" if len(pairs) == nlines else "*** MISMATCH"))
print("dates=%d   datum date (bperp 0.0, omitted by stackStripMap)=%s" % (len(bp), datum))
print("bperp %.1f .. %.1f   midpoint %.1f" % (min(bp.values()), max(bp.values()), mid))
print("temporal %s .. %s   midpoint %s\n" % (ds[0], ds[-1], tmid.strftime("%Y%m%d")))
print("DATE       MODE  PX     DEG  BPERP      dMID     dT(d)  MAXBP     NOTE")
for d in sorted(ds, key=lambda d: (-deg[d], abs(bp[d] - mid))):
    n = []
    if d == datum: n.append("DATUM")
    if mode[d] == "FBS" and px[d] != mfbs: n.append("OFF-WIDTH %d" % px[d])
    if deg[d] <= 3: n.append("THIN NODE")
    if maxbp[d] > 1450: n.append("near -b limit")
    print("%-10s %-5s %-6d %-4d %-10.1f %-8.1f %-6d %-9.1f %s" %
          (d, mode[d], px[d], deg[d], bp[d], abs(bp[d] - mid),
           abs((t[d] - tmid).days), maxbp[d], "; ".join(n)))

cand = [d for d in sorted(ds, key=lambda d: (-deg[d], abs((t[d] - tmid).days)))
        if mode[d] == "FBS" and px[d] == mfbs and deg[d] > 3]
print("\n--- eligible FBS references at modal width %d, by degree then temporal centrality" % mfbs)
for d in cand[:6]:
    print("    %-10s deg %-3d  bperp %8.1f  dMID %7.1f  dT %4dd  MAXBP %7.1f"
          % (d, deg[d], bp[d], abs(bp[d] - mid), abs((t[d] - tmid).days), maxbp[d]))
