"""MOCK geo2rdr (linog_auto self-test only): range.off and azimuth.off (float64, the reference grid, sparse), with the
nine rows the kit's G21 reads filled (LINOG_MOCK_OFFFRAME=<date>: 100 x the others). v0.13 (R7's cases): OFFFRAME a comma
list; LINOG_MOCK_AZNAN=<dates>: those dates' rows at -999999.0, under G21's fill line, so G21 prints the date with no ratio."""
import argparse
import os

import numpy as np

import linog_mock3 as M


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--secondary', '--geom', '--outdir'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('geo2rdr')   # v0.9: no WISDOM_FILE in this step's jobs
    W, L = M.frame_dims(a.reference)
    d = M.date_of(a.secondary)
    os.makedirs(a.outdir, exist_ok=True)
    for n in ('range.off', 'azimuth.off'):
        p = os.path.join(a.outdir, n)
        M.sparse(p, 8 * W * L)
        M.write_xml(p, W, L, 'DOUBLE')
    base = 30.0 + (int(d) % 13) * 10.0
    if M.listed('LINOG_MOCK_OFFFRAME', d):
        base *= 100
    if M.listed('LINOG_MOCK_AZNAN', d):
        base = -999999.0
    row = np.full(W, base, dtype='<f8').tobytes()
    with open(os.path.join(a.outdir, 'azimuth.off'), 'r+b') as fh:
        for k in range(1, 10):
            fh.seek(int(L * k / 10) * W * 8)
            fh.write(row)
    print('MOCK geo2rdr %s' % d)
