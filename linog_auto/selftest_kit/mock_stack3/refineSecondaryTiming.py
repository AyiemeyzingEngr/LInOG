"""MOCK refineSecondaryTiming (linog_auto self-test only): the pair's misreg shelve (constant azpoly and rgpoly) and both
shelve copies; ISCE's off.log in the working folder. As isce2 v2.6.4's refineSecondaryTiming.py (107f3632, lines 199 to
235), the pair's offset, measured in the reference's pixels (the truth of the second date less the first's), is scaled by
rgratio = SLR(mm) / SLR(ss) in range and azratio = PRF(ss) / PRF(mm) in azimuth, read from the two shelve copies (the
instrument's range pixel, the frame's PRF), and the line 'rgratio, azratio:  <r> <a>' printed: so an FBD-to-FBS pair is
doubled in range, as on felix (the ascending record 17.2). On the FBS-only P3 frame every ratio is 1 and the pair is the
truth's difference, as before v0.13.
LINOG_MOCK_JOBFAIL=<pair> raises; LINOG_MOCK_P3SLEEP=<pair> writes LINOG_MOCK_MARK and sleeps 60 s;
LINOG_MOCK_BIGAZ=<pair>:<px> adds px to that pair's azimuth offset. v0.9: ampcor's wisdom lines (linog_mock3.fft_wisdom).
v0.13 (17.9): LINOG_MOCK_V13=1 takes linog_mock3.truth13 (FBD_RG13 more in range on an FBD date, by its shelve's pixel);
LINOG_MOCK_PAIRNOISE=<sigma> adds N(0, sigma) (seeded by the pair) to the pair's offset in both axes before the scaling."""
import argparse
import os
import shelve
import time

import linog_mock3 as M


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--secondary', '--mm', '--ss', '--outfile'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    out = os.path.dirname(a.outfile)
    pair = M.pairs_of(out)
    if M.env('LINOG_MOCK_JOBFAIL') == pair:
        raise RuntimeError('MOCK: refineSecondaryTiming failed for %s (planted)' % pair)
    M.env_line('refineSecondaryTiming')
    M.fft_wisdom('ampcor', pair)   # v0.9: ampcor plans its FFTs through cfft1d_jpl
    if M.env('LINOG_MOCK_P3SLEEP') == pair:
        open(M.env('LINOG_MOCK_MARK'), 'w').write('sleeping in %s\n' % pair)
        time.sleep(60)
    from isceobj.Util.Poly2D import Poly2D
    d1, d2 = M.date_of(a.mm), M.date_of(a.ss)
    os.makedirs(out, exist_ok=True)
    rs, ss = os.path.join(out, 'referenceShelve'), os.path.join(out, 'secondaryShelve')
    M.copy_shelve(a.mm, rs)
    M.copy_shelve(a.ss, ss)
    (slr1, prf1), (slr2, prf2) = M.slr_prf(rs), M.slr_prf(ss)
    rgratio, azratio = slr1 / slr2, prf2 / prf1
    print('*************************************')
    print('rgratio, azratio: ', rgratio, azratio)
    print('*************************************')
    if M.v13():
        t1, t2 = M.truth13(d1, slr1 > 6.0), M.truth13(d2, slr2 > 6.0)
    else:
        t1, t2 = M.truth(d1), M.truth(d2)
    big = M.env('LINOG_MOCK_BIGAZ').split(':')
    extra = float(big[1]) if len(big) == 2 and big[0] == pair else 0.0
    oaz, org = t2[0] - t1[0] + extra, t2[1] - t1[1]
    sig = float(M.env('LINOG_MOCK_PAIRNOISE') or 0.0)
    if sig:
        import numpy as np
        rng = np.random.RandomState((int(d1) * 31 + int(d2)) % (2 ** 31))
        oaz, org = oaz + sig * rng.normal(), org + sig * rng.normal()
    az, rg = Poly2D(), Poly2D()
    az.initPoly(rangeOrder=0, azimuthOrder=0, coeffs=[[oaz * azratio]])
    rg.initPoly(rangeOrder=0, azimuthOrder=0, coeffs=[[org * rgratio]])
    db = shelve.open(a.outfile)
    db['azpoly'], db['rgpoly'] = az, rg
    db.close()
    open('off.log', 'a').write('MOCK off %s\n' % pair)
    print('Estimated az shift:  %s' % (oaz * azratio))
    print('Estimated rg shift:  %s' % (org * rgratio))
