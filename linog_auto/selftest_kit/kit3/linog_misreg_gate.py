#!/usr/bin/env python3
"""GATE between run_05 and run_06: misreg offsets must be sub-pixel residuals.
Formalises f0280's undocumented *_run05_offsets check. Run from WORK_DIR.
Usage: linog_misreg_gate.py <REFERENCE_DATE>   Exit 1 on FAIL.  LInOG 2026-08-26."""
import glob, os, shelve, sys, statistics as st
REF = sys.argv[1] if len(sys.argv) > 1 else None
rows = []
for p in sorted(glob.glob("refineSecondaryTiming/dates/*/misreg.dat")):
    d = os.path.basename(os.path.dirname(p))
    s = shelve.open(p[:-4], "r")
    try:
        rows.append((d, float(s["azpoly"]._coeffs[0][0]), float(s["rgpoly"]._coeffs[0][0])))
    except Exception as e:
        print("  UNREADABLE %s %s" % (d, repr(e)[:50]))
    s.close()
print("dates with a misreg shelve: %d" % len(rows))
print("DATE          AZ_OFF_px    RG_OFF_px")
for d, a, r in rows:
    print("%s   %10.4f   %10.4f %s" % (d, a, r, "<-- REF (from argv, not measured; after G16 it must read 0.0000 0.0000)" if d == REF else ""))
az = [r[1] for r in rows]; rg = [r[2] for r in rows]
sp_az, sp_rg = max(az) - min(az), max(rg) - min(rg)
print("\nazimuth  min %8.3f  max %8.3f  median %8.3f  SPREAD %8.3f" % (min(az), max(az), st.median(az), sp_az))
print("range    min %8.3f  max %8.3f  median %8.3f  SPREAD %8.3f" % (min(rg), max(rg), st.median(rg), sp_rg))
bad = 0
if sp_az > 5.0:
    print("\n*** FAIL: azimuth spread %.2f px. Coregistration residuals must be sub-pixel"
          " (f0280 healthy = 1.97 px). Something upstream of run_05 is wrong; do NOT run run_06." % sp_az); bad += 1
if sp_rg > 5.0:
    print("*** FAIL: range spread %.2f px. Healthy, measured post-G16: "
          "f0310 1.864, f0320 1.911; pre-G16 2.265 / 2.303." % sp_rg); bad += 1
if REF and abs(dict((d, a) for d, a, _ in rows).get(REF, 0.0)) > 5.0:
    print("*** WARN: reference %s carries az %.3f; invertMisreg pinned a different date as datum."
          % (REF, dict((d, a) for d, a, _ in rows)[REF]))
sys.exit(1 if bad else 0)
