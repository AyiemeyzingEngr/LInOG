#!/usr/bin/env python3
"""MOCK save_gdal.py (linog_auto self-test only, v0.7): `save_gdal.py FILE -d DATASET -m MASK -o OUT` (the kit's step 8):
a mock GeoTIFF of the dataset on the file's geo grid, NaN where the mask is 0 (no NoData set: step 8b sets it), at the
exact path -o names (the kit renames it to .tif)."""
import sys

import numpy as np

import linog_mock6 as M6

M6.planted_fail('save_gdal.py')
pos, opt = M6.args(sys.argv[1:], {'-d': 1, '-m': 1, '-o': 1})
a, attrs = M6.h5_read(pos[0], opt.get('-d'))
a = a.astype(np.float32)
if opt.get('-m'):
    m, _ = M6.h5_read(opt['-m'])
    a[~m.astype(bool)] = np.nan
M6.write_tiff(opt['-o'], dict(geotransform=M6.geotransform(attrs), nodata=None, metadata={}, source=pos[0]), a)
print('MOCK save_gdal.py: %s %s -> %s (%d x %d)' % (pos[0], opt.get('-d'), opt['-o'], a.shape[1], a.shape[0]))
