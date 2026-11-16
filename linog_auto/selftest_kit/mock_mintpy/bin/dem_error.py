#!/usr/bin/env python3
"""MOCK dem_error.py (linog_auto self-test only, v0.7; v0.13 r2: the ascending record 15.4 and 16.4): `dem_error.py TS -t
TEMPLATE -g GEOMETRY -o OUT`, as the kit's linog_phase6.sh (step 2) calls it: OUT, and demErr.h5 and timeseriesResidual.h5
beside it, as MintPy 1.6.2 writes them. v0.13 r2: OUT carries a 1-D bperp (one a date) and MintPy 1.6.2's four
mintpy.topographicResidual attributes as strings (dem_error.py's config_keys, str() of each: polyOrder '2', phaseVelocity
'False', stepDate '[]', excludeDate "['exclude_date.txt']"), which G6a.11 reads.
Unplanted: the time series with the mock's deformation added, a subsidence bowl (at most 3 cm/yr, centred on the grid), on
MintPy's decimal years from the first date (v0.7 to v0.13 r1: days / 365.25); bperp 0 on every date, as the mock's
ifgramStack.h5 holds it (smallbaselineApp.py's load_data), so G6a.11 reads it constant (NOT JUDGED).
Planted (15.4): LINOG_MOCK_DB1=<case> with LINOG_MOCK_DB1_TABLE=<the kit's db1/mock3350_table.json> (the desk's table, 15.3 D at
16.2's line): the series must hold the table's 12 dates (else this exits 1, writing nothing). Each date's range plane from the
case's c into dem_error (m/px across the columns, relative to the reference date, the first), with an offset of 1 mm x the
date's index so that no pixel is zero but on the reference date, and no bowl (its linear part over the mock's land is a ramp of
its own); then, per pixel, the part of the series on bperp, taken relative to the reference date, given [1, t, t^2] over all
dates in decimal years, out, so the reference date stays zero (MintPy's own bperp is not zero on the reference date, and the
reading does not depend on bperp's offset); the table's bperp written. A step through dem_error is in the case's c already (on
the FBD dates, across the frame), so it reaches the series as MintPy's dem_error leaves it: k (m - g bperp).
v0.13 r3 (the ascending record 96, 97): `[--dem-err-file F]` (demErr there, else beside OUT); the dates out of the fit as MintPy
1.6.2 reads them, the template's mintpy.topographicResidual.excludeDate (auto: exclude_date.txt in the working folder, when
there), printed as 1.6.2 prints them ("exclude the following dates for DEM error estimation: (N)" and the sorted list) when
there are any, and left out of the table's fit of g (date_flag); on mintpy/timeseries_ramp.h5 (dfit's loop and R4's B) the
series is passed through, as the mock smallbaselineApp's correct_topography writes timeseries_ramp_demErr.h5 (a copy of
timeseries_ramp.h5), so a fit with no date out gives sbas's series again (as S78's ctrl read MintPy do it, 95.2), and with N
dates out the series plus a uniform rate of N x 0.1 mm/yr (so the series differ with the date set); the residual
is zero unless planted: LINOG_MOCK_DEMFIT=<spec> gives each date a residual field of std 1 mm (seeded by the date), 10 mm on a
date the spec names: "D" always, "D@A+B" only when A and B are both out of the fit (a date MintPy's rule then names), entries
separated by ";". LINOG_MOCK_DEM_NOEXCL=1: the exclusions not read (every date in the fit, no line printed)."""
import json
import os
import sys

import h5py
import numpy as np

import linog_mock6 as M6

M6.planted_fail('dem_error.py')
pos, opt = M6.args(sys.argv[1:], {'-t': 1, '-g': 1, '-o': 1, '--dem-err-file': 1, '--dem-error-file': 1})
src, out = pos[0], opt['-o']
ex = M6.template_exclude(opt.get('-t'), 'mintpy.topographicResidual.excludeDate')   # v0.13 r3: 1.6.2's read_exclude_date
with h5py.File(src, 'r') as f:
    ts, dates, attrs = f['timeseries'][:], f['date'][:], dict(f.attrs)
n, L, W = ts.shape
ds = [d.decode() for d in dates]
t = np.array([M6.yyyymmdd2years(d) - M6.yyyymmdd2years(ds[0]) for d in ds])
ex = sorted(d for d in ex if d in ds)   # 1.6.2: a date not in the series is dropped
if os.environ.get('LINOG_MOCK_DEM_NOEXCL'):   # v0.13 r3 plant (suite 13r3, R303): the exclusions not read, as r2's chain A ran
    ex = []
if ex:
    print('exclude the following dates for DEM error estimation: (%d)\n%s' % (len(ex), ex))
flag = np.array([d not in ex for d in ds])
case = os.environ.get('LINOG_MOCK_DB1')
if os.path.basename(src) == 'timeseries_ramp.h5':   # v0.13 r3: as the mock sbas's correct_topography (a copy)
    # with dates out of the fit, a uniform rate of 0.1 mm/yr per date out added (the review's item: the series must differ
    # with the date set, as MintPy's do, so a fit read from the wrong series is caught; uniform, so no std changes)
    ts2 = (ts.astype(np.float64) + 1e-4 * len(ex) * t[:, None, None]).astype(np.float32) if ex else ts.astype(np.float32)
    bp = np.zeros(n, np.float64)
    note = 'timeseries_ramp.h5 passed through (the mock sbas\'s correct_topography); bperp 0'
elif case:
    tab = json.load(open(os.environ['LINOG_MOCK_DB1_TABLE']))
    if ds != tab['dates'] or case not in tab['cases']:
        print('MOCK dem_error.py: LINOG_MOCK_DB1=%s planted, but the series\' dates %s are not the table\'s %s (or no such case)'
              % (case, ds, tab['dates']))
        sys.exit(1)
    cpre = np.array(tab['cases'][case]['c_into_dem_error_m_per_px'], dtype=np.float64)
    bp = np.array(tab['bperp_m'], dtype=np.float64)
    xx = np.arange(W, dtype=np.float64) - (W - 1) / 2.0
    y = ts.astype(np.float64) + cpre[:, None, None] * xx[None, None, :] + 0.001 * np.arange(n)[:, None, None]
    tc = t - t.mean()
    X = np.column_stack([np.ones(n), tc, tc ** 2, bp])
    g = np.linalg.lstsq(X[flag], y.reshape(n, -1)[flag], rcond=None)[0][3]   # v0.13 r3: over the dates in the fit (date_flag)
    ts2 = (y - ((bp - bp[0])[:, None] * g[None, :]).reshape(n, L, W)).astype(np.float32)
    note = 'the table planted (LINOG_MOCK_DB1=%s): each date\'s plane and offset, its bperp part given [1, t, t^2] out' % case
else:
    yy, xx = np.mgrid[0:L, 0:W]
    v = -0.03 * np.exp(-(((yy - L / 2.0) / (L / 4.0)) ** 2 + ((xx - W / 2.0) / (W / 3.0)) ** 2))
    ts2 = (ts + t[:, None, None] * v[None]).astype(np.float32)
    bp = np.zeros(n, np.float64)
    note = 'the bowl added; bperp 0 on every date (the mock stack\'s)'
meta = dict(attrs)
for k, val in (('polyOrder', '2'), ('phaseVelocity', 'False'), ('stepDate', '[]'), ('excludeDate', "['exclude_date.txt']")):
    meta['mintpy.topographicResidual.' + k] = val   # MintPy 1.6.2: meta[key_prefix + key] = str(vars(inps)[key])
d = os.path.dirname(os.path.abspath(out))
res = np.zeros_like(ts2)
spec = os.environ.get('LINOG_MOCK_DEMFIT')
if spec:   # v0.13 r3 plant: each date's residual field, 1 mm, or 10 mm on a date the spec names
    big = set()
    for e in [x for x in spec.split(';') if x]:
        dd, _, cond = e.partition('@')
        if not cond or all(c in ex for c in cond.split('+')):
            big.add(dd)
    for i, dd in enumerate(ds):
        res[i] = (np.random.RandomState(int(dd)).normal(0, 1, (L, W)) * (0.010 if dd in big else 0.001)).astype(np.float32)
    note += '; residual planted (LINOG_MOCK_DEMFIT): 10 mm on %s' % (', '.join(sorted(big & set(ds))) or 'no date')
for name, data in ((out, ts2), (os.path.join(d, 'timeseriesResidual.h5'), res)):
    with h5py.File(name, 'w') as f:
        f.create_dataset('timeseries', data=data)
        f.create_dataset('date', data=dates)
        f.create_dataset('bperp', data=bp.astype(np.float32))
        f.attrs.update(meta)
with h5py.File(opt.get('--dem-err-file') or opt.get('--dem-error-file') or os.path.join(d, 'demErr.h5'), 'w') as f:
    f.create_dataset('dem', data=np.zeros((L, W), np.float32))
    f.attrs.update(dict(meta, FILE_TYPE='dem'))
print('MOCK dem_error.py: %s -> %s, demErr.h5, timeseriesResidual.h5 (%d dates, %d x %d; %s)' % (src, out, n, L, W, note))
