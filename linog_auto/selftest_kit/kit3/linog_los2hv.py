#!/usr/bin/env python3
"""Project a geocoded LOS velocity file to vertical or ground-range.
NOT a decomposition - one ascending track cannot separate E/N/U.
  Vertical   = LOS/cos(inc)  assumes NO horizontal motion
  Horizontal = LOS/sin(inc)  assumes NO vertical motion; ground-range component,
                             look azimuth ~78 deg from N (within 2.3% of E-W)
Usage: linog_los2hv.py <geo_velocity.h5> <geo_geometryRadar.h5> <Vertical|Horizontal> <out.h5>
LInOG 2026-08-27."""
import shutil, sys
import numpy as np
import h5py
src, geom, comp, dst = sys.argv[1:5]
with h5py.File(geom, 'r') as g:
    inc = np.radians(g['incidenceAngle'][:].astype('f8'))
inc = np.where(np.isfinite(inc) & (inc > 0), inc, np.nan)
fac = 1.0/np.cos(inc) if comp == 'Vertical' else 1.0/np.sin(inc)
shutil.copyfile(src, dst)
with h5py.File(dst, 'r+') as f:
    for d in ['velocity', 'velocityStd', 'intercept', 'interceptStd', 'residue']:
        if d in f:
            f[d][:] = (f[d][:] * fac).astype(f[d].dtype)
    f.attrs['PROJECTION_COMPONENT']  = comp
    f.attrs['PROJECTION_FORMULA']    = 'LOS/cos(inc)' if comp == 'Vertical' else 'LOS/sin(inc)'
    f.attrs['PROJECTION_ASSUMPTION'] = ('pure vertical motion, no horizontal' if comp == 'Vertical'
        else 'pure ground-range motion, no vertical; look azimuth ~78 deg from N')
    f.attrs['PROJECTION_SOURCE']     = src
    f.attrs['PROJECTION_NOTE']       = 'Single ascending track: projection, NOT a decomposition.'
print('%-10s -> %-34s factor med=%.6f  min=%.6f  max=%.6f'
      % (comp, dst, np.nanmedian(fac), np.nanmin(fac), np.nanmax(fac)))
