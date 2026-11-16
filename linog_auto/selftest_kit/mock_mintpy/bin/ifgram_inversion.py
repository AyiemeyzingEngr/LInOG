#!/usr/bin/env python3
"""MOCK ifgram_inversion.py (linog_auto self-test only, v0.11): `ifgram_inversion.py STACK -t CFG`, as lp_compare.py's split
runs it on its copy. In the folder it runs in: timeseries.h5 and temporalCoherence.h5 from the stack's kept pairs
(dropIfgram True): each date's value the sum, over the kept pairs that end on it, of their unwrapPhase x 0.001 m per radian
and their coherence x 0.0001 m (so dropping a pair moves the dates it ends on, and the mock's zero phases still give a
rate), REF_DATE the first date; the temporal coherence the kept pairs' mean
coherence + 0.2, as the mock smallbaselineApp's invert_network, with the scene's decorrelated sea at 0.3.
v0.12 (drop1's tests): numInvIfgram.h5 too (the kept pairs' count, as invert_network writes it); linog_mock3.d1_plant
(LINOG_MOCK_D1BAD); LINOG_MOCK_D1FAIL=<pair>: exit 1, nothing written, when that pair is not kept; LINOG_MOCK_D1SLEEP=<pair>:<s>:
sleep first when that pair is not kept, after writing 'pid <its pid>' into LINOG_MOCK_MARK when that is set. It prints which of
the files MintPy 1.6.2's inversion reads around a stack are there (../avgSpatialCoh.h5 from the stack's folder; waterMask.h5
in the working folder, the template's waterMaskFile auto), and of two it does not read (../maskConnComp.h5, geometryRadar.h5
beside the stack; v0.12 r2 no longer copies them), as drop1 places them; it uses none of them."""
import os
import sys
import time

import h5py
import numpy as np

import linog_mock3 as M3


def _yn(p):
    return 'yes' if os.path.isfile(p) else 'no'


stack = sys.argv[1]
sd = os.path.dirname(os.path.abspath(stack))
print('MOCK ifgram_inversion.py: around the stack: ../avgSpatialCoh.h5 %s, waterMask.h5 (the working folder) %s; not read by MintPy 1.6.2\'s '
      'inversion: ../maskConnComp.h5 %s, geometryRadar.h5 %s' % (_yn(os.path.join(sd, '..', 'avgSpatialCoh.h5')), _yn('waterMask.h5'),
                                                                _yn(os.path.join(sd, '..', 'maskConnComp.h5')), _yn(os.path.join(sd, 'geometryRadar.h5'))))
with h5py.File(stack, 'r') as f:
    keep = f['dropIfgram'][()].astype(bool)
    d12 = [(x[0].decode(), x[1].decode()) for x in f['date'][()]]
    unw = f['unwrapPhase'][()].astype(np.float64)
    coh = f['coherence'][()].astype(np.float64)
    attrs = dict(f.attrs)
dates = sorted(set(d for (a, b), k in zip(d12, keep) if k for d in (a, b)))
names = ['%s_%s' % ab for ab in d12]
out_ = [n for n, k in zip(names, keep) if not k]
sl = os.environ.get('LINOG_MOCK_D1SLEEP', '')
if sl and sl.split(':')[0] in out_:
    if os.environ.get('LINOG_MOCK_MARK'):
        with open(os.environ['LINOG_MOCK_MARK'], 'w') as fh:
            fh.write('pid %d sleeping in %s\n' % (os.getpid(), os.getcwd()))
    time.sleep(float(sl.split(':')[1]))
if os.environ.get('LINOG_MOCK_D1FAIL') and os.environ['LINOG_MOCK_D1FAIL'] in out_:
    print('MOCK ifgram_inversion.py: failed (LINOG_MOCK_D1FAIL, %s not kept)' % os.environ['LINOG_MOCK_D1FAIL'])
    sys.exit(1)
n, l, w = unw.shape
ts = np.zeros((len(dates), l, w), np.float32)
for i, ((a, b), k) in enumerate(zip(d12, keep)):
    if k and b in dates:
        ts[dates.index(b)] += (0.001 * unw[i] + 0.0001 * coh[i]).astype(np.float32)
with h5py.File('timeseries.h5', 'w') as f:
    f.create_dataset('timeseries', data=ts)
    f.create_dataset('date', data=np.array([d.encode() for d in dates]))
    f.attrs.update(dict(attrs, FILE_TYPE='timeseries', REF_DATE=dates[0]))
tc = np.clip(coh[keep].mean(axis=0) + 0.2, 0, 1)
tc[M3.scene(l, w)['decor']] = 0.3
tc = M3.d1_plant(tc, d12, keep)
with h5py.File('temporalCoherence.h5', 'w') as f:
    f.create_dataset('temporalCoherence', data=tc.astype(np.float32))
    f.attrs.update(dict(attrs, FILE_TYPE='temporalCoherence'))
with h5py.File('numInvIfgram.h5', 'w') as f:
    f.create_dataset('mask', data=np.full((l, w), int(keep.sum()), np.int16))
    f.attrs.update(dict(attrs, FILE_TYPE='mask'))
print('MOCK ifgram_inversion.py: %d of %d pairs kept, %d dates -> timeseries.h5, temporalCoherence.h5, numInvIfgram.h5' % (keep.sum(), n, len(dates)))
