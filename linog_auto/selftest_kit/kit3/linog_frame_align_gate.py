#!/usr/bin/env python3
"""G21 -- along-track frame alignment.  Run from WORK_DIR, straight after run_03.

A granule can carry the right frame number AND the right off-nadir angle and
still be centred half a frame away along track.  G1 tests off-nadir, G4
polarisation, G5 spectrum, G6 does not exist -- none tests where the scene
actually sits.  Measured on p447 f0310, 29 August 2026:

    20101213   median |azimuth.off|  9684.7   frame median 94.3   = 103x
    every other date                    1.4 .. 230.7   (worst healthy 2.45x)

That granule sat ~9,200 lines off (4.24 s, ~30 km, 43% of an ALOS frame), so a
geo2rdr solution existed only for reference lines below 18432-9200.
resampleSlc produced a scene 83.6% zeros; all 13 of its pairs landed at the
0.285 estimator floor; and G7/G10 both PASSED it because their patch was empty
(N35).  run_04, run_06 and run_08 each spent time on a date that could never
work.  The data this reads is already on disk from geo2rdr, so it costs nothing.

    linog_frame_align_gate.py [--mult 5.0] [--rows 9] [--offsets offsets]

Exit 1 if any date's median |azimuth.off| exceeds --mult x the frame median.
LInOG 2026-08-29
"""
import argparse, glob, os, re, sys
import numpy as np
import xml.etree.ElementTree as ET

FILL = -999998.0
ap = argparse.ArgumentParser()
ap.add_argument("--offsets", default="offsets")
ap.add_argument("--mult", type=float, default=5.0)
ap.add_argument("--rows", type=int, default=9, help="rows sampled through the file")
a = ap.parse_args()

def width_of(xml_path):
    try:
        for prop in ET.parse(xml_path).getroot().iter('property'):
            if prop.get('name', '').lower() in ('width', 'number_of_samples'):
                return int(prop.find('value').text)
    except Exception:
        pass
    return None

dates = sorted(d for d in (os.path.basename(p.rstrip('/'))
                           for p in glob.glob(os.path.join(a.offsets, '*/')))
               if re.match(r'^\d{8}$', d))
if not dates:
    sys.exit("*** no 8-digit dates under %s/ -- has run_03 run?" % a.offsets)

rows = []
for d in dates:
    az = os.path.join(a.offsets, d, 'azimuth.off')
    if not os.path.exists(az):
        rows.append((d, float('nan'), 0.0, 'MISSING azimuth.off')); continue
    W = width_of(az + '.xml')
    if not W:
        rows.append((d, float('nan'), 0.0, 'cannot read width from azimuth.off.xml')); continue
    L = os.path.getsize(az) // 8 // W
    vals, tot = [], 0
    for k in range(1, a.rows + 1):
        v = np.fromfile(az, dtype=np.float64, count=W, offset=int(L * k / (a.rows + 1)) * W * 8)
        tot += v.size; vals.append(v[v > FILL])
    v = np.concatenate(vals) if vals else np.array([])
    rows.append((d, float(np.median(np.abs(v))) if v.size else float('nan'),
                 (v.size / tot) if tot else 0.0, ''))

good = [m for _, m, _, _ in rows if m == m]
if not good:
    sys.exit("*** no readable azimuth.off anywhere")
fmed = float(np.median(good))

print("G21 along-track frame alignment: %d date(s), frame median |az| %.1f lines, threshold %.1fx"
      % (len(rows), fmed, a.mult))
print("%-10s %12s %8s %8s  %s" % ("DATE", "MED|AZ|", "RATIO", "VALID", "NOTE"))
bad = 0
for d, m, f, note in rows:
    if m != m:
        print("%-10s %12s %8s %8.3f  *** %s" % (d, "-", "-", f, note)); bad += 1; continue
    r = m / fmed if fmed else float("inf")
    flag = "   *** OFF-FRAME, this granule images different ground" if r > a.mult else ""
    print("%-10s %12.1f %7.1fx %8.3f  %s%s" % (d, m, r, f, note, flag))
    if r > a.mult: bad += 1
print("%s  %d of %d beyond %.1fx" % ("FAIL" if bad else "PASS", bad, len(rows), a.mult))
print("reference: p447 f0310 read 103x on 20101213; its worst healthy ratio was 2.45x")
sys.exit(1 if bad else 0)
