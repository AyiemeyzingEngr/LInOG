#!/usr/bin/env python3
"""G7 v4 after run_03 -- coarse registration, measured at windows chosen for
terrain rather than at one hardcoded row and column.  Run from WORK_DIR.

    linog_coarse_reg_gate_v4.py <REF_DATE> [--reselect] [date ...]

v4, 29 Aug 2026.  v3 read ONE window baked into patch()'s default arguments,
r0=9000 c0=4200, and took argmax with no peak test.  On p447 f0300 that window
sat on void-fill DEM at 41.0 m with backscatter 4x lower than land, and the
gate failed all 25 correctly-registered dates.  MIN_FILL could not catch it:
the patch was 100 % non-zero, it was simply water.

Everything that decides is now in linog_reg_common.py, shared with G10, because
N41 happened by the two gates drifting apart.  Thresholds were read off
LINOG_N41_CALIBRATION_20260829.md, not chosen.  Peak significance is printed
and never used -- it overlaps, 5.14 good against 5.20 bad.

Self-test: --inject dy,dx,DATE shifts one date in memory only, so the gate
can be shown to FAIL. Interface otherwise unchanged: argv[1] is the reference date, no argparse, matching the
other bare-argv gates.  Optional trailing dates restrict the check.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linog_reg_common as C

if len(sys.argv) < 2:
    sys.exit("usage: linog_coarse_reg_gate_v4.py <REF_DATE> [--reselect] [--inject dy,dx,DATE] [date ...]")
argv = sys.argv[1:]
argv, INJ = C.parse_inject(argv)
resel = "--reselect" in argv
argv = [a for a in argv if a != "--reselect"]
REF, want = argv[0], set(argv[1:])

C.run("G7 v4  coarse registration, after run_03",
      "coregSLC/Coarse",
      ["raw_fbs_unpacked/%s/%s.slc", "SLC/%s/%s.slc"],
      REF, tol=2, want=want or None, reselect=resel, inject=INJ)
