"""MOCK FilterAndCoherence (linog_auto self-test only): filt_<pair>.int (three range fringes; magnitude 10 in the grid's
first corner, 1 elsewhere; LINOG_MOCK_BADPAIR=<pair>[,<pair>...]: random phase (v0.10: a list); LINOG_MOCK_RANDMAG=<pair>[,<pair>...]: magnitudes
spread as a real frame's, lognormal, and random phase, RandomState(3), on which numpy 1.26's stretch tops one float32
step above 1 at 83 x 658 (F49); LINOG_MOCK_NANPAIR=<pair>[,<pair>...]: a 10 x 10 block of NaN at line gl/3, column
gw/2 - 5) and filt_<pair>.cor (float32, a coherence per pair; LINOG_MOCK_DEADDATE=<date>: 0.2 on that date's pairs).
v0.9: icu's wisdom lines (linog_mock3.fft_wisdom) between the filter and the coherence.
v0.10 (admit's rules): LINOG_MOCK_BADDATE=<date>[,<date>...]: every pair of those dates random phase (R3's dead date);
LINOG_MOCK_RAMPDATE=<date>: that date's pairs at 12 fringes across the width, not 3 (the kit's date screen: its median peak
4x the others' where its pairs are under half the network).
v0.12 (drop1's peers): LINOG_MOCK_COHPAIR=<pair>:<coherence>[,...]: that pair's coherence (its .cor) at that value."""
import argparse
import os
import re

import numpy as np

import linog_mock3 as M


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--input', '--filt', '--coh', '--strength'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    x = open(a.input + '.xml').read()
    gw, gl = (int(re.search(r'name="%s">\s*<value>(\d+)' % n, x).group(1)) for n in ('width', 'length'))
    d1, d2 = os.path.basename(os.path.dirname(os.path.abspath(a.coh))).split('_')
    pr = '%s_%s' % (d1, d2)
    yy, xx = np.mgrid[0:gl, 0:gw]
    bad_dates = [x for x in M.env('LINOG_MOCK_BADDATE').split(',') if x]
    if pr in M.env('LINOG_MOCK_BADPAIR').split(',') or d1 in bad_dates or d2 in bad_dates:
        ph = np.random.RandomState(int(d1[-4:]) + int(d2[-4:])).uniform(-np.pi, np.pi, (gl, gw))
    elif M.env('LINOG_MOCK_RAMPDATE') in (d1, d2):
        ph = 2 * np.pi * 12.0 * xx / gw + 0.1 * int(d2[-2:])   # v0.10: 12 fringes across the width
    else:
        ph = 2 * np.pi * 3.0 * xx / gw + 0.1 * int(d2[-2:])   # 3 fringes across the width
    mag = np.ones((gl, gw))
    mag[:gl // 4, :gw // 4] = 10.0   # line 0 and column 0's corner: a descending frame's report shows it top right
    if pr in M.env('LINOG_MOCK_RANDMAG').split(','):
        rs = np.random.RandomState(3)
        mag, ph = rs.lognormal(0.0, 1.0, (gl, gw)), rs.uniform(-np.pi, np.pi, (gl, gw))
    z = (mag * np.exp(1j * ph)).astype('<c8')
    if pr in M.env('LINOG_MOCK_NANPAIR').split(','):
        z[gl // 3:gl // 3 + 10, gw // 2 - 5:gw // 2 + 5] = complex(np.nan, np.nan)
    z.tofile(a.filt)
    M.write_xml(a.filt, gw, gl, 'CFLOAT')
    M.env_line('FilterAndCoherence')
    M.fft_wisdom('icu', pr)   # v0.9: the filter (psfilt) plans nothing; icu's coherence plans through cfft1d_jpl
    v = 0.2 if M.env('LINOG_MOCK_DEADDATE') in (d1, d2) else 0.55 + 0.02 * (int(d2[-2:]) % 5)
    for x in (y for y in M.env('LINOG_MOCK_COHPAIR').split(',') if y):   # v0.12
        if x.split(':')[0] == pr:
            v = float(x.split(':')[1])
    np.full((gl, gw), v, dtype='<f4').tofile(a.coh)
    M.write_xml(a.coh, gw, gl, 'FLOAT')
