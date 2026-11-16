#!/usr/bin/env python3
"""Coherence census over Igrams/.  Run from WORK_DIR.
Usage: linog_coherence_census.py [WATCH_DATE]

v2, 2026-08-29 -- N36 and N12.
v1 carried a HARDCODED p448 FBS date set:

    FBS = {"20070203","20071222","20080206","20080323","20081108","20090208",
           "20091111","20091227","20100211","20101230","20110214"}

None of p447's 26 dates are in it, so every pair fell through to "FBD" and the
mode split collapsed to a single row, FBD n=180.  The MIXED fingerprint that
identifies N22 -- a per-mode constant error cancels within a mode and shows in
full across modes -- was therefore unreadable on that frame.  Same defect class
as G7 v1's hardcoded date list.  FBS is now derived from raw_fbs_unpacked/, the
rule linog_redatum_misreg_v2.py and autofix_widths_v2.py already use.

v1 also printed a hardcoded "(f0280: 0.5095, 121/149)" beside every row,
including rows it did not describe (N12).  Baselines are now opt-in via
--baseline, and unset by default: a number is comparable only to one measured
from the same artifact over the same sample.
"""
import argparse, glob, os, sys
import numpy as np
from osgeo import gdal
gdal.UseExceptions()

ap = argparse.ArgumentParser()
ap.add_argument("watch", nargs="?", default=None, help="date to report separately")
ap.add_argument("--fbs-dir", default="raw_fbs_unpacked")
ap.add_argument("--stride", type=int, default=4)
ap.add_argument("--baseline", default="", help="free text printed once, e.g. 'f0280 0.5095 121/149'")
a = ap.parse_args()

FBS = set(os.path.basename(x.rstrip("/")) for x in glob.glob(a.fbs_dir + "/*/"))
if not FBS:
    print("*** no dates under %s/ -- every pair would be classed FBD (N36)" % a.fbs_dir)
    sys.exit(1)

rows = []
for p in sorted(glob.glob("Igrams/*/filt_*.cor")):
    pr = os.path.basename(os.path.dirname(p))
    if pr.count("_") != 1:
        continue
    x, y = pr.split("_")
    cls = "FBS  " if (x in FBS and y in FBS) else ("FBD  " if (x not in FBS and y not in FBS) else "MIXED")
    try:
        ds = gdal.Open(p)
        v = ds.GetRasterBand(ds.RasterCount).ReadAsArray()[::a.stride, ::a.stride]
        v = v[np.isfinite(v) & (v > 0)]
        rows.append((pr, cls, float(v.mean()) if v.size else 0.0))
    except Exception:
        rows.append((pr, cls, -1.0))

print("igrams found: %d   FBS dates %d, from %s/" % (len(rows), len(FBS), a.fbs_dir))
try:
    n8 = sum(1 for L in open("run_files/run_08_igram") if L.strip())
    print("run_08_igram lines: %d   %s" % (n8, "MATCH" if n8 == len(rows) else "*** MISMATCH"))
except Exception:
    print("run_08_igram: unreadable (not run from WORK_DIR?)")

ok = [r for r in rows if r[2] >= 0]
if not ok:
    sys.exit("*** no readable .cor files")
m = np.array([r[2] for r in ok])
print("MEAN COHERENCE %.4f   pairs > 0.30: %d/%d" % (m.mean(), int((m > 0.30).sum()), len(m)))
if a.baseline:
    print("  baseline given: %s" % a.baseline)

print("%-6s %6s %9s %9s" % ("CLASS", "n", "mean", ">0.30"))
split = {}
for c in ("FBS  ", "FBD  ", "MIXED"):
    s = np.array([r[2] for r in ok if r[1] == c])
    if not s.size:
        print("%-6s %6d %9s %9s" % (c, 0, "-", "-")); continue
    split[c.strip()] = s.mean()
    print("%-6s %6d %9.4f %9d" % (c, s.size, s.mean(), int((s > 0.30).sum())))
if len(split) == 3 and split["MIXED"] == min(split.values()):
    print("*** MIXED is the WORST class -- that is the N22 fingerprint. A per-mode")
    print("    constant range-datum error cancels within a mode and shows in full")
    print("    across modes. Check RGFAC: 1.000 FBS, 0.500 FBD.")

rows_ok = sorted(ok, key=lambda r: r[2])
print("worst 5: " + ", ".join("%s %.3f" % (r[0], r[2]) for r in rows_ok[:5]))
print("best  5: " + ", ".join("%s %.3f" % (r[0], r[2]) for r in rows_ok[-5:]))

if a.watch:
    w = [r for r in ok if a.watch in r[0].split("_")]
    if not w:
        print("WATCH %s: no pairs" % a.watch)
    else:
        s = np.array([r[2] for r in w])
        print("WATCH %s: n=%d mean %.4f min %.4f max %.4f  >0.30: %d"
              % (a.watch, s.size, s.mean(), s.min(), s.max(), int((s > 0.30).sum())))
        if s.max() < 0.30:
            print("    every pair below 0.30 with a spread of %.4f -- that is the"
                  % (s.max() - s.min()))
            print("    estimator floor, i.e. no correlation at all, not weak correlation.")
