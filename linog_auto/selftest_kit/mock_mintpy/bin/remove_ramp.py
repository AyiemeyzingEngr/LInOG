#!/usr/bin/env python3
"""MOCK remove_ramp.py (linog_auto self-test only, v0.7; v0.13 r2: the ascending record 15.4): `remove_ramp.py TS -s linear -m
MASK -o OUT` (the kit's step 3). v0.13 r2: OUT = TS less, per date, the linear plane MintPy 1.6.2's deramp fits (utils1.run_deramp,
one date at a time; objects/ramp.py deramp): over the mask's pixels whose value on that date is finite and not zero, the
design [y, x, 1] by least squares (here in float64 on the float32 file), the plane referenced to the file's REF_Y, REF_X when
it names them, and kept 0 where the date's value is 0 (so the series' zero date stays zero); its dates and attributes kept.
v0.7 to v0.13 r1 took out a fixed ramp, 0.001 x a range ramp x the date's index, which no per-date plane of the series gave."""
import sys

import h5py
import numpy as np

import linog_mock6 as M6

M6.planted_fail('remove_ramp.py')
pos, opt = M6.args(sys.argv[1:], {'-s': 1, '-m': 1, '-o': 1})
with h5py.File(pos[0], 'r') as f:
    ts, dates, attrs = f['timeseries'][:], f['date'][:], dict(f.attrs)
    extra = dict((k, f[k][()]) for k in f.keys() if k not in ('timeseries', 'date'))
n, L, W = ts.shape
with h5py.File(opt['-m'], 'r') as f:
    mask = np.asarray(f['mask'][()]) != 0
yy, xx = np.mgrid[0:L, 0:W]
G = np.column_stack([yy.ravel(), xx.ravel(), np.ones(L * W)]).astype(np.float64)
ref = None
if 'REF_Y' in attrs and 'REF_X' in attrs:
    ref = int(str(attrs['REF_Y'].decode() if isinstance(attrs['REF_Y'], bytes) else attrs['REF_Y'])) * W + \
        int(str(attrs['REF_X'].decode() if isinstance(attrs['REF_X'], bytes) else attrs['REF_X']))
out = np.empty_like(ts)
for i in range(n):
    d = ts[i].astype(np.float64).ravel()
    use = mask.ravel() & np.isfinite(d) & (d != 0)
    ramp = G @ (np.linalg.pinv(G[use]) @ d[use]) if use.sum() >= 3 else np.zeros(L * W)
    if ref is not None:
        ramp = ramp - ramp[ref]
    ramp[d == 0] = 0
    out[i] = (d - ramp).reshape(L, W).astype(ts.dtype)
with h5py.File(opt['-o'], 'w') as f:
    f.create_dataset('timeseries', data=out)
    f.create_dataset('date', data=dates)
    for k, v in extra.items():   # bperp (v0.13 r2), as MintPy's layout_hdf5 copies the reference file's datasets
        f.create_dataset(k, data=v)
    f.attrs.update(attrs)
print('MOCK remove_ramp.py: %s -> %s (linear, one plane a date over the mask %s, as MintPy 1.6.2\'s deramp)' % (pos[0], opt['-o'], opt.get('-m')))
