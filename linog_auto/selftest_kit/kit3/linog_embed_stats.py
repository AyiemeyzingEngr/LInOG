#!/usr/bin/env python3
"""Embed GDAL statistics INSIDE every GeoTIFF of a delivery folder, so they
travel with the file and cannot outlive the raster they describe.

A .aux.xml sidecar survives a rewrite of its .tif and then reports the previous
product's numbers. Measured on p448 f0320 after the 123-pair rebuild: the stale
sidecar's STATISTICS_MAXIMUM was 0.2255 against the raster's actual 0.1581, an
error of 43%, and VALID_PERCENT read 35.18 against 39.34. QGIS and ArcGIS stretch
the display from those values.

Opening GA_Update and calling ComputeStatistics writes the values into the TIFF
header; GDAL then discards the redundant sidecar. Delivery becomes 16 products
instead of 16 products + 6 caches.
                                                          LInOG 2026-08-28
"""
import argparse, glob, os, sys
from osgeo import gdal
gdal.UseExceptions()

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True, help="delivery folder holding the .tif files")
ap.add_argument("--check", action="store_true", help="report only, write nothing")
a = ap.parse_args()

tifs = sorted(glob.glob(os.path.join(a.dir, "*.tif")))
if not tifs:
    print("*** no .tif in %s" % a.dir); sys.exit(1)

for f in tifs:
    b = os.path.basename(f)
    side = f + ".aux.xml"
    if a.check:
        ds = gdal.Open(f); st = ds.GetRasterBand(1).GetStatistics(False, False)
        ds = None
        print("%-46s embedded=%s  sidecar=%s" % (b, "yes" if st else "NO",
                                                 "present" if os.path.exists(side) else "none"))
        continue
    ds = gdal.Open(f, gdal.GA_Update)
    mn, mx, mean, sd = ds.GetRasterBand(1).ComputeStatistics(False)
    ds.FlushCache(); ds = None
    print("%-46s min %+.6f  max %+.6f  mean %+.6f  sd %.6f  sidecar %s"
          % (b, mn, mx, mean, sd, "gone" if not os.path.exists(side) else "STILL PRESENT"))

if not a.check:
    n = len(glob.glob(os.path.join(a.dir, "*")))
    print("\ndelivery now holds %d files   (expect 16: 6 tif + 6 png + 4 kmz)" % n)
