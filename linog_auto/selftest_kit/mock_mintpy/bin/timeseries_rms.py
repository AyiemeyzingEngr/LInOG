#!/usr/bin/env python3
"""MOCK timeseries_rms.py (linog_auto self-test only, v0.13 r3: the ascending record 96, 97): `timeseries_rms.py RES -m MASK
-r RAMP --cutoff C`, as dfit's DEM-error loop calls it, from the working folder, as MintPy 1.6.2 does it (timeseries_rms.py,
utils1.get_residual_rms, objects/ramp.py deramp, stack.timeseries_rms): RAMP not no: RES_ramp.h5 beside RES, each date less
its plane (linear [y, x, 1] or quadratic [y^2, x^2, yx, y, x, 1]) fitted over the mask's pixels whose value is not zero, the
plane less its value at REF_Y, REF_X when the file names them and zero pixels kept (objects/ramp.py deramp; r3 step 3, 97.5: the
desk check on MintPy found the reference); the
RMS of each date over the mask into rms_<RES_ramp or RES>.txt beside it (1.6.2's header and "date<TAB>rms" lines);
reference_date.txt (the date of least RMS) and exclude_date.txt (the dates over C x median(|rms|) / 0.67449, MintPy's
median_abs_deviation_threshold with center 0) in the working folder, the latter removed when no date is over. Planted:
LINOG_MOCK_P6FAIL=timeseries_rms.py exits 1 before it writes anything."""
import os
import sys

import h5py
import numpy as np

import linog_mock6 as M6

M6.planted_fail('timeseries_rms.py')
pos, opt = M6.args(sys.argv[1:], {'-m': 1, '-r': 1, '--ramp': 1, '--deramp': 1, '--cutoff': 1, '-t': 1})
res = pos[0]
ramp = opt.get('-r') or opt.get('--ramp') or opt.get('--deramp') or 'quadratic'
cut = float(opt.get('--cutoff') or 3)
with h5py.File(res, 'r') as f:
    ts, dates, attrs = f['timeseries'][:].astype(np.float64), f['date'][:], dict(f.attrs)
n, L, W = ts.shape
with h5py.File(opt.get('-m') or 'maskTempCoh.h5', 'r') as f:
    mask = np.asarray(f[list(f.keys())[0]][()]) != 0
ds = [d.decode() for d in dates]
src = res
if ramp != 'no':
    yy, xx = [a.ravel().astype(np.float64) for a in np.mgrid[0:L, 0:W]]
    G = np.column_stack([yy, xx, np.ones(L * W)]) if ramp == 'linear' else \
        np.column_stack([yy ** 2, xx ** 2, yy * xx, yy, xx, np.ones(L * W)])
    out = np.empty_like(ts)
    for i in range(n):
        d = ts[i].ravel()
        use = mask.ravel() & (d != 0) & np.isfinite(d)
        ramp = G @ (np.linalg.pinv(G[use], rcond=1e-15) @ d[use]) if use.sum() >= G.shape[1] else np.zeros(L * W)
        if 'REF_Y' in attrs and 'REF_X' in attrs:   # 1.6.2: ramp -= ramp[ref_idx]
            ry = int(attrs['REF_Y'].decode() if isinstance(attrs['REF_Y'], bytes) else attrs['REF_Y'])
            rx = int(attrs['REF_X'].decode() if isinstance(attrs['REF_X'], bytes) else attrs['REF_X'])
            ramp = ramp - ramp[ry * W + rx]
        ramp[d == 0] = 0
        out[i] = (d - ramp).reshape(L, W)
    src = os.path.splitext(res)[0] + '_ramp.h5'
    with h5py.File(src, 'w') as f:
        f.create_dataset('timeseries', data=out.astype(np.float32))
        f.create_dataset('date', data=dates)
        f.attrs.update(attrs)
    ts = out
rms = np.array([float(np.sqrt(np.mean(np.square(ts[i][mask])))) if mask.any() else float('nan') for i in range(n)])
rf = os.path.join(os.path.dirname(os.path.abspath(src)), 'rms_%s.txt' % os.path.splitext(os.path.basename(src))[0])
with open(rf, 'w') as fh:
    fh.write('# Root Mean Square in space for each acquisition of time-series\n# Timeseries file: %s\n# Mask file: %s\n'
             '# Date\t\tRMS (m)\n' % (src, opt.get('-m')))
    for d, r in zip(ds, rms):
        fh.write('%s\t%s\n' % (d, repr(float(r))))
print('save timeseries RMS to text file: ' + rf)
with open('reference_date.txt', 'w') as fh:
    fh.write(ds[int(np.nanargmin(rms))] + '\n')
thr = cut * float(np.nanmedian(np.abs(rms))) / 0.67449
over = [d for d, r in zip(ds, rms) if r > thr]
print('-' * 50 + '\ndate(s) with RMS > %s * median RMS (%.4f)' % (cut, thr))
if over:
    for d, r in zip(ds, rms):
        if d in over:
            print('%s - %.4f' % (d, r))
    with open('exclude_date.txt', 'w') as fh:
        fh.write(''.join(d + '\n' for d in over))
    print('save date(s) to file: exclude_date.txt')
else:
    print('None.')
    if os.path.isfile('exclude_date.txt'):
        os.remove('exclude_date.txt')
