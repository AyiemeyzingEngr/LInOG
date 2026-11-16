#!/usr/bin/env python3
"""GATE: every ISCE shelve must carry doppler+fmrate+frame. Run from WORK_DIR.
['frame'] alone = the stock unpacker ran; geo2rdr native:True will produce
garbage azimuth. See linog-unpacker-path-shadow.  LInOG 2026-08-26."""
import glob, os, shelve, sys
paths = sorted(glob.glob("SLC/*/data.dat") + glob.glob("raw_fbs_unpacked/*/data.dat"))
bad = 0
for p in paths:
    s = shelve.open(p[:-4], "r"); k = sorted(s.keys()); s.close()
    if k != ["doppler", "fmrate", "frame"]:
        print("  BAD %-34s %s" % (os.path.dirname(p), k)); bad += 1
print("shelves=%d  bad=%d" % (len(paths), bad))
sys.exit(1 if bad or not paths else 0)
