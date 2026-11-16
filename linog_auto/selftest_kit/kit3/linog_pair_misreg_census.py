#!/usr/bin/env python3
"""Per-pair run_04 offset census. Run from WORK_DIR.
Usage: linog_pair_misreg_census.py [DATE_TO_ISOLATE]   LInOG 2026-08-27."""
import glob, os, shelve, sys, statistics as st
sel = sys.argv[1] if len(sys.argv) > 1 else None
rows, bad = [], []
for p in sorted(glob.glob("refineSecondaryTiming/pairs/*/misreg.dat")):
    pr = os.path.basename(os.path.dirname(p))
    s = shelve.open(p[:-4], "r")
    try:
        rows.append((pr, float(s["azpoly"]._coeffs[0][0]), float(s["rgpoly"]._coeffs[0][0])))
    except Exception as e:
        bad.append((pr, list(s.keys()), repr(e)[:40]))
    s.close()
print("pairs read: %d   unreadable: %d" % (len(rows), len(bad)))
for pr, k, e in bad[:5]:
    print("  UNREADABLE %s keys=%s %s" % (pr, k, e))
az = [r[1] for r in rows]; rg = [r[2] for r in rows]
print("all-pair az: min %.3f  max %.3f  median %.3f" % (min(az), max(az), st.median(az)))
print("all-pair rg: min %.3f  max %.3f  median %.3f" % (min(rg), max(rg), st.median(rg)))
print("\nDATE       N   AZ_med   AZ_min   AZ_max     RG_med   RG_min   RG_max")
for d in sorted(set(x for pr, _, _ in rows for x in pr.split("_"))):
    v = [a for pr, a, _ in rows if d in pr.split("_")]
    w = [r for pr, _, r in rows if d in pr.split("_")]
    print("%s %3d %8.3f %8.3f %8.3f  %9.3f %8.3f %8.3f"
          % (d, len(v), st.median(v), min(v), max(v), st.median(w), min(w), max(w)))
# N52: range was computed and stored but never reported. A one-gate range shift
# (N53) passed G8 silently because of it.
BIG = 5.0
big = [(pr, a, r) for pr, a, r in rows if abs(r) > BIG]
print("\npairs with |rg| > %.1f samples: %d of %d" % (BIG, len(big), len(rows)))
for pr, a, r in sorted(big, key=lambda x: -abs(x[2]))[:15]:
    print("  %-22s rg %+9.3f  az %+8.3f" % (pr, r, a))
if sel:
    print("\npairs touching %s:" % sel)
    for pr, a, r in rows:
        if sel in pr.split("_"):
            print("  %-22s az %8.3f  rg %8.3f" % (pr, a, r))
