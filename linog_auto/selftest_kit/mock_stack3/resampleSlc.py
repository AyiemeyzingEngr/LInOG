"""MOCK resampleSlc (linog_auto self-test only): <coreg>/<date>.slc on the reference grid (the mock ground, the date's
noise; LINOG_MOCK_N53=<date>: shifted 32 samples in range, coarse only), .xml and .vrt, and both shelve copies.
v0.13 (the ascending record 17.9), LINOG_MOCK_V13=1: the date's product is linog_mock3's one ground band-limited to the
reference's band (0.21875 cycles a sample on an FBS reference, 0.4375 on an FBD one) and shifted, by its spectrum, by its
residual misregistration in the reference's pixels, as resamp_slc.f90 leaves it: the coarse product (no --poly) by the
date's truth less the reference's (linog_mock3.truth13); the fine product by that less the misregistration polynomial
--poly applies, converted from the date's own pixels and lines (x SLR(d) / SLR(REF), x PRF(REF) / PRF(d)).
LINOG_MOCK_FINESHIFT=<date>:<dx>[:<dy>] moves that date's fine product by dx samples (and dy lines) more (M70, M81).
LINOG_MOCK_DECOR=<k> makes every fine product's band k of linog_mock3.BANDS13 a field of the date's own, flat in brightness
(nothing of the ground: G10 v3's windows there do not vote); LINOG_MOCK_FILLCUT=<date>:<col> zeroes that date's fine
product from column col on (its patches there under G10 v3's fill line); M67c, the part 4 review's P4-02.
v0.13 (R7's cases, part 5), coarse products only (no --poly): LINOG_MOCK_N53 a comma list of dates; LINOG_MOCK_COARSEEMPTY=
<dates> writes those dates' products all zeros (sparse); LINOG_MOCK_GATEOFF=<date>:<m>[,...] moves that date's product by
(the secondary shelve's startingRange - (the leader's r0 + m)) / SLR(REF) samples in range (linog_mock3.gateoff): 0 where
rwin set startingRange to the records' column 0, +32 on an FBS reference for a one-gate window rwin did not correct."""
import argparse
import os
import shelve

import linog_mock3 as M


def misreg_consts(poly):
    db = shelve.open(poly, 'r')
    try:
        return float(db['azpoly'].getCoeffs()[0][0]), float(db['rgpoly'].getCoeffs()[0][0])
    finally:
        db.close()


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--secondary', '--coreg', '--offsets', '--poly'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('resampleSlc')   # v0.9: no WISDOM_FILE in this step's jobs
    W, L = M.frame_dims(a.reference)
    d = M.date_of(a.secondary)
    os.makedirs(a.coreg, exist_ok=True)
    M.copy_shelve(a.secondary, os.path.join(a.coreg, 'secondaryShelve'))
    M.copy_shelve(a.reference, os.path.join(a.coreg, 'referenceShelve'))
    print('Polynomial doppler provided')
    out = os.path.join(a.coreg, os.path.basename(os.path.normpath(a.coreg)) + '.slc')
    if not a.poly and M.listed('LINOG_MOCK_COARSEEMPTY', d):   # v0.13: a coarse product of zeros (G7 reads EMPTY)
        M.sparse(out, L * W * 8)
        print('MOCK resampleSlc: %s coarse product all zeros (LINOG_MOCK_COARSEEMPTY)' % d)
    elif M.v13() and L >= M.LINES_FULL:
        ref = M.date_of(a.reference)
        (sd, pd), (sr, pr) = M.slr_prf(a.secondary), M.slr_prf(a.reference)
        td, tr = M.truth13(d, sd > 6.0), M.truth13(ref, sr > 6.0)
        dy, dx = td[0] - tr[0], td[1] - tr[1]
        if a.poly:
            paz, prg = misreg_consts(a.poly)
            dy, dx = dy - paz * pr / pd, dx - prg * sd / sr
            fs = M.env('LINOG_MOCK_FINESHIFT').split(':')
            if fs[0] == d and len(fs) >= 2:
                dx += float(fs[1])
                dy += float(fs[2]) if len(fs) > 2 else 0.0
        else:
            if M.listed('LINOG_MOCK_N53', d):
                dx += 32.0
            go = M.gateoff(d)
            if go is not None:
                r0s, r0l = M.shelf_r0(a.secondary)
                dx += (r0s - (r0l + go)) / sr
        half = 0.21875 if sr < 6.0 else 0.4375
        decor = M.env('LINOG_MOCK_DECOR') if a.poly else ''
        cut = M.env('LINOG_MOCK_FILLCUT').split(':')
        cut = int(cut[1]) if a.poly and len(cut) == 2 and cut[0] == d else None
        with open(out, 'wb') as fh:
            fh.truncate(L * W * 8)
        with open(out, 'r+b') as fh:
            for k, (b0, b1) in enumerate(M.BANDS13):
                z = M.decor13(b0, b1, W, d, half) if decor == str(k) else M.product13(b0, b1, W, d, dy, dx, half)
                if cut is not None:
                    z[:, cut:] = 0
                fh.seek(b0 * W * 8)
                fh.write(z.tobytes())
        print('MOCK resampleSlc v0.13: %s residual az %+.6f rg %+.6f (reference units)' % (d, dy, dx))
    else:
        M.write_slc(out, W, L, d, shift_cols=32 if (M.listed('LINOG_MOCK_N53', d) and not a.poly) else 0)
    M.write_xml(out, W, L, 'CFLOAT')
