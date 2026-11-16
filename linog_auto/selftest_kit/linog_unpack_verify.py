#!/usr/bin/env python3
"""Post-unpack verify across BOTH SLC/ (FBD) and raw_fbs_unpacked/ (FBS):
xml width vs shelve ns, r0 on the ALOS gate grid, synthetic PRF, date match,
and the image path each shelve bakes in.  Run from WORK_DIR.  Exit 1 on any
flag.  Needs PYTHONPATH=<env>/site-packages/isce/components.  LInOG 2026-08-26."""
import glob, os, re, shelve, sys, collections
GRID, R0REF = 149.89632, 845217.5596
rows, tops, bad = [], [], 0
for pat in ("SLC/*/data.dat", "raw_fbs_unpacked/*/data.dat"):
    for p in sorted(glob.glob(pat)):
        d = os.path.dirname(p); date = os.path.basename(d)
        sh = shelve.open(p[:-4], "r"); f = sh["frame"]; sh.close()
        ns, r0, prf = int(f.numberOfSamples), float(f.startingRange), float(f.instrument.PRF)
        try: tops.append(f.image.filename.split("/")[0])
        except Exception: tops.append("?")
        xs, xw = os.path.join(d, date + ".slc.xml"), 0
        if os.path.exists(xs):
            m = re.search(r'name="width".*?<value>(\d+)', open(xs).read(), re.S)
            xw = int(m.group(1)) if m else 0
        fl = []
        if xw and xw != ns: fl.append("XML_NE_NS")
        k = (r0 - R0REF) / GRID
        if abs(round(k) - k) * GRID > 1.0: fl.append("R0_OFFGRID")
        q = 100000.0 / prf
        if abs(q - round(q)) < 1e-6: fl.append("PRF_SYNTH")
        if f.sensingStart.strftime("%Y%m%d") != date: fl.append("DATE_MISMATCH")
        if fl: bad += 1
        rows.append((date, pat.split("/")[0], ns, xw, int(round(k)) + 1, r0, prf, ",".join(fl)))
print("DATE       SOURCE             NS     XMLW   POS  R0            PRF        FLAGS")
for r in sorted(rows): print("%-10s %-18s %-6d %-6d %-4d %-13.4f %-10.4f %s" % r)
print("\nscenes=%d  flagged=%d  gate positions=%s" % (len(rows), bad,
      sorted(set(r[4] for r in rows))))
print("distinct PRFs:", sorted(set(round(r[6], 4) for r in rows)))
print("shelve image roots:", dict(collections.Counter(tops)))
sys.exit(1 if bad else 0)
