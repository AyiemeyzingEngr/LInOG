#!/usr/bin/env python3
"""MOCK gdal_edit.py (linog_auto self-test only, v0.7): `gdal_edit.py -a_nodata VALUE FILE` (the kit's step 8b, N44)."""
import sys

from osgeo import gdal

import linog_mock6 as M6

M6.planted_fail('gdal_edit.py')
pos, opt = M6.args(sys.argv[1:], {'-a_nodata': 1})
ds = gdal.Open(pos[0], gdal.GA_Update)
ds.GetRasterBand(1).SetNoDataValue(float(opt['-a_nodata']))
ds.FlushCache()
ds = None
