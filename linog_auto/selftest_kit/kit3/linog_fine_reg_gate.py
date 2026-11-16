#!/usr/bin/env python3
"""G10 v2 after run_06 -- fine registration, measured at windows chosen for
terrain rather than at the image centre.  Run from WORK_DIR.

    linog_fine_reg_gate_v2.py <REF_DATE> [--reselect] [date ...]

v2, 29 Aug 2026.  THREE defects in v1, two of them never recorded:

  1. It had NO fill test at all.  An all-zero patch mean-removes to zeros,
     correlates to a flat surface, and argmax returns index 0 -- decoded as a
     perfect dy=+0 dx=+0.  The emptiest possible scene scored as the best
     registered one.  MIN_FILL reached G7 in v3 and never reached here.
  2. `W, L, PS, PL = 9344, 18432, 2048, 1024` were HARDCODED.  The width was
     never read from the reference, so a frame of any other width would seek to
     wrong offsets and report registration numbers for garbage, silently.  v2
     resolves the width from the reference .slc.xml and says where it got it.
  3. Its tolerance was +/-1 against G7's +/-2 on the same quantity, on a
     2048x1024 patch rather than 512x512, so the two gates were never
     comparable.  Both now use 512x512 and +/-2 on the median-centred residual,
     which is the geometry the 29 Aug calibration measured.

Thresholds come from LINOG_N41_CALIBRATION_20260829.md.  Peak significance is
printed and never used to decide.

An off-frame acquisition is NOT this gate's job.  merged/SLC is resampled, so
run_03 has already applied the granule offset; 20101213 registering at +0/+0
here is correct behaviour.  G21 and per-date coherence own that class.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linog_reg_common as C

if len(sys.argv) < 2:
    sys.exit("usage: linog_fine_reg_gate_v2.py <REF_DATE> [--reselect] [--inject dy,dx,DATE] [date ...]")
argv = sys.argv[1:]
argv, INJ = C.parse_inject(argv)
resel = "--reselect" in argv
argv = [a for a in argv if a != "--reselect"]
REF, want = argv[0], set(argv[1:])

C.run("G10 v2  fine registration, after run_06",
      "merged/SLC",
      ["merged/SLC/%s/%s.slc", "raw_fbs_unpacked/%s/%s.slc"],
      REF, tol=2, want=want or None, reselect=resel, inject=INJ)
