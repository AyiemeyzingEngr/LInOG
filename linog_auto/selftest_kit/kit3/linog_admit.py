#!/usr/bin/env python3
"""G20 -- Phase 4.5 -> 5 admission gate.  Decides include/exclude numerically.
Run from WORK_DIR.  No images in the loop.

Per pair, from Igrams/<pair>/ :
  filt_*.cor                  mean coherence
  filt_*snaphu.unw.conncomp   largest component fraction, MAX over labels >= 1.
                              snaphu caps NCOMP at 20 and numbers arbitrarily, so
                              label 1 is NOT always the largest.  f0320
                              20070921_20081108: label 0 65.9%, label 2 14.4%,
                              label 1 0.9%.  v1 used (g == 1) and agreed with G18
                              only on healthy pairs.
  filt_*.int                  phase-gradient concentration R = |mean(exp(i*dphi))|
                              and the 2-D spectral peak of exp(i*phase), in cycles

DATE exclusion -> mintpy.network.excludeDate
  A date carrying a frame-spanning phase ramp: per-date MEDIAN spectral-peak
  magnitude >= --screen-mult x the frame median.  Measured on p448 f0320:
  20110214 = 5.0x, next worst 20100929 = 1.8x -- 3.0 separates them cleanly.

PAIR exclusion -> mintpy.network.excludeDate12
  A pair whose unwrapping cannot be trusted: largest component < --min-largest
  OR R < --min-R.  On f0320 these agree with G18: all five of its UNUSABLE
  pairs sit in the bottom eleven by R.

LOW COHERENCE EXCLUDES NOTHING.  That is what
mintpy.networkInversion.maskThreshold is for; dropping a date on coherence
discards its good pairs as well.                          LInOG 2026-08-28
"""
import argparse, glob, os, sys, math
from collections import defaultdict
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default="Igrams")
ap.add_argument("--width", type=int, default=778)
ap.add_argument("--length", type=int, default=658)
ap.add_argument("--screen-mult", type=float, default=3.0)
ap.add_argument("--min-largest", type=float, default=0.20)
ap.add_argument("--min-R", type=float, default=0.25)
ap.add_argument("--show", type=int, default=12)
a = ap.parse_args()
W, L = a.width, a.length

def conc(z, ax):
    d = z * np.conj(np.roll(z, 1, axis=ax))
    d = d[1:, :] if ax == 0 else d[:, 1:]
    m = np.isfinite(d) & (np.abs(d) > 0)
    return float(np.abs(np.mean(d[m] / np.abs(d[m])))) if m.sum() else 0.0

P = {}
for ip in sorted(glob.glob(os.path.join(a.dir, "*", "filt_*.int"))):
    pr = os.path.basename(os.path.dirname(ip))
    if len(pr) != 17 or "_" not in pr: continue
    z = np.fromfile(ip, dtype=np.complex64, count=W * L)
    if z.size < W * L: continue
    z = z.reshape(L, W); ok = np.isfinite(z) & (np.abs(z) > 0)
    u = np.zeros_like(z); u[ok] = z[ok] / np.abs(z[ok])
    R = max(conc(u, 0), conc(u, 1))
    S = np.abs(np.fft.fft2(u)) ** 2; S[0, 0] = 0.0
    k = int(np.argmax(S)); fy, fx = k // W, k % W
    if fy > L // 2: fy -= L
    if fx > W // 2: fx -= W
    pk = math.hypot(fy, fx)
    coh = float("nan")
    cf = glob.glob(os.path.join(os.path.dirname(ip), "filt_*.cor"))
    if cf:
        c = np.fromfile(cf[0], dtype=np.float32, count=W * L)
        c = c[np.isfinite(c) & (c > 0)]
        if c.size: coh = float(c.mean())
    lg = float("nan")
    gf = glob.glob(os.path.join(os.path.dirname(ip), "filt_*snaphu.unw.conncomp"))
    if gf:
        g = np.fromfile(gf[0], dtype=np.uint8, count=W * L)
        if g.size == W * L and (g > 0).sum():
            bc = np.bincount(g.astype(np.int64))
            bc[0] = 0                     # label 0 = unwrapped nowhere
            lg = float(bc.max()) / float(g.size)
    P[pr] = dict(coh=coh, R=R, pk=pk, fy=fy, fx=fx, lg=lg)

if not P:
    print("*** no pairs read"); sys.exit(1)
frame_pk = float(np.median([v["pk"] for v in P.values()]))

bydate = defaultdict(list)
for pr, v in P.items():
    for d in pr.split("_"): bydate[d].append(v)

print("G20 ADMISSION GATE   pairs=%d  dates=%d  frame median peak=%.2f cycles\n"
      % (len(P), len(bydate), frame_pk))
print("DATE       N   MED_PK  xFRAME   MED_R   MED_COH   VERDICT")
screen = []
for d in sorted(bydate):
    v = bydate[d]
    mp = float(np.median([x["pk"] for x in v]))
    mr = float(np.median([x["R"] for x in v]))
    mc = float(np.nanmedian([x["coh"] for x in v]))
    rat = mp / frame_pk if frame_pk else 0
    tag = "*** PHASE SCREEN -> excludeDate" if rat >= a.screen_mult else ""
    if tag: screen.append(d)
    print("%s %3d  %6.2f  %5.1fx  %6.3f  %7.4f   %s" % (d, len(v), mp, rat, mr, mc, tag))

bad = sorted([pr for pr, v in P.items()
              if (v["lg"] == v["lg"] and v["lg"] < a.min_largest) or v["R"] < a.min_R],
             key=lambda p: P[p]["R"])
drop_by_date = set(pr for pr in P if any(d in screen for d in pr.split("_")))
bad_extra = [pr for pr in bad if pr not in drop_by_date]

print("\nUNTRUSTWORTHY PAIRS  (largest < %.2f or R < %.2f)" % (a.min_largest, a.min_R))
print("PAIR                    COH     R     LARGEST%   also dropped by date?")
for pr in bad:
    v = P[pr]
    print("%-22s %6.4f %6.3f   %6.1f     %s" % (pr, v["coh"], v["R"],
          100 * v["lg"] if v["lg"] == v["lg"] else -1,
          "yes" if pr in drop_by_date else "no"))

keep = [pr for pr in P if pr not in drop_by_date and pr not in set(bad_extra)]
deg = defaultdict(int)
for pr in keep:
    for d in pr.split("_"): deg[d] += 1
adj = defaultdict(set)
for pr in keep:
    x, y = pr.split("_"); adj[x].add(y); adj[y].add(x)
seen, comp = set(), 0
for d in adj:
    if d in seen: continue
    comp += 1; st = [d]
    while st:
        n = st.pop()
        if n in seen: continue
        seen.add(n); st.extend(adj[n] - seen)

print("\nRESULT")
print("  pairs in  %d   dropped by date %d   dropped by pair %d   kept %d"
      % (len(P), len(drop_by_date), len(bad_extra), len(keep)))
print("  dates kept %d   network components %s   min degree %d (%s)"
      % (len(deg), comp, min(deg.values()),
         sorted(deg, key=lambda d: deg[d])[0]))
print("\n--- paste into mintpy/smallbaselineApp.cfg ---")
print("mintpy.network.excludeDate     = %s" % (",".join(sorted(screen)) if screen else "no"))
print("mintpy.network.excludeDate12   = %s" % (",".join(sorted(bad_extra)) if bad_extra else "auto"))
sys.exit(0 if comp == 1 else 1)
