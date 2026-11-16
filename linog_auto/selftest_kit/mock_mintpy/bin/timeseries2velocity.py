#!/usr/bin/env python3
"""MOCK timeseries2velocity.py (linog_auto self-test only, v0.7): `timeseries2velocity.py TS [-t TEMPLATE] -o OUT
[--ex DATE ... | --ex FILE.txt]` (the kit's step 4; v0.10: dfit's fits): the least-squares rate (m/yr) of each pixel over
the dates, as MintPy's linear model, with velocityStd, intercept, interceptStd and residue (linog_mock6.fit_velocity).
v0.10, as MintPy 1.6.2: the dates --ex names are left out, and with -t those of mintpy.timeFunc.excludeDate (auto:
exclude_date.txt in the working folder, when there). v0.13 r3 (97.6): LINOG_MOCK_T2V_FAIL_OUT=<name> exits 1, writing nothing,
when -o names a file of that name (one fit of dfit's fails, the others run)."""
import os
import sys

import h5py

import linog_mock6 as M6

M6.planted_fail('timeseries2velocity.py')
argv = sys.argv[1:]
ex = []
if '--ex' in argv or '--ex-date' in argv:
    i = argv.index('--ex') if '--ex' in argv else argv.index('--ex-date')
    j = i + 1
    while j < len(argv) and not argv[j].startswith('-'):
        ex += M6.read_date_txt(argv[j]) if argv[j].endswith('.txt') else [argv[j]]
        j += 1
    argv = argv[:i] + argv[j:]
pos, opt = M6.args(argv, {'-t': 1, '-o': 1})
if os.environ.get('LINOG_MOCK_T2V_FAIL_OUT') and os.path.basename(opt.get('-o') or '') == os.environ['LINOG_MOCK_T2V_FAIL_OUT']:
    print('MOCK timeseries2velocity.py: failed (planted for %s)' % opt.get('-o'))
    sys.exit(1)
if opt.get('-t'):
    ex += M6.template_exclude(opt['-t'])
v, attrs, used = M6.fit_velocity(pos[0], sorted(set(ex)))
with h5py.File(opt['-o'], 'w') as f:
    for k in ('velocity', 'intercept', 'velocityStd', 'interceptStd', 'residue'):
        f.create_dataset(k, data=v[k])
    f.attrs.update(dict(attrs, FILE_TYPE='velocity', DATA_TYPE='float32', UNIT='m/year'))
print('exclude date: %s' % sorted(set(ex)))
print('MOCK timeseries2velocity.py: %s -> %s (%d dates used of the file\'s)' % (pos[0], opt['-o'], len(used)))
