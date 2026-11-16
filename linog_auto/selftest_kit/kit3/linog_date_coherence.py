#!/usr/bin/env python3
"""Per-date coherence summary over Igrams/. Run from WORK_DIR. LInOG 2026-08-27."""
import glob, os
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
pair = {}
for p in sorted(glob.glob("Igrams/*/filt_*.cor")):
    pr = os.path.basename(os.path.dirname(p))
    ds = gdal.Open(p)
    v = ds.GetRasterBand(ds.RasterCount).ReadAsArray()[::8, ::8]
    ds = None
    v = v[np.isfinite(v) & (v > 0)]
    pair[pr] = float(v.mean()) if v.size else 0.0
print("DATE        N    MEAN     MIN      MAX    >0.30")
for d in sorted({x for pr in pair for x in pr.split("_")}):
    v = np.array([c for pr, c in pair.items() if d in pr.split("_")])
    print("%s  %3d  %.4f  %.4f  %.4f   %3d"
          % (d, v.size, v.mean(), v.min(), v.max(), int((v > 0.30).sum())))
