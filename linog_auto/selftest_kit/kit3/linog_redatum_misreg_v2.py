#!/usr/bin/env python3
# linog_redatum_misreg_v2.py -- LInOG, 2026-08-27
#
# G16, mode-aware.
#
# v1 rebased every date's misreg onto the coregistration reference by
# subtracting the reference's constant from all of them.  That is correct for
# AZIMUTH on every date -- both modes carry 18432 lines, so the units are
# common.  It is WRONG for RANGE on FBD dates.
#
# resampleSlc evaluates the range-offset polynomial in the INPUT scene's
# samples.  FBD scenes are 4640 wide at 9.36852 m; FBS scenes are 9344 wide at
# 4.68426 m -- exactly 2x.  Subtracting an FBS-referenced range constant from an
# FBD date applies twice the intended physical shift.
#
# Measured on P448 F0300 after the uniform v1 rebase:
#     FBS-FBS   0.6251 -> 0.7130,  28/36 -> 36/36     (both scenes correct)
#     FBD-FBD   0.6784 -> 0.6691,  31/31 -> 31/31     (both identically wrong, cancels)
#     MIXED     0.6518 -> 0.6087,  67/77 -> 72/77     (partners inconsistent)
# which is the signature of a range-only, FBD-only error.
#
# Mode is read from the filesystem: a date with raw_fbs_unpacked/<date>/ is FBS,
# otherwise FBD.  Override with --fbs-dates / --fbd-dates.
#
#   python linog_redatum_misreg_v2.py <REF_DATE> [--dates-dir DIR]
#          [--fbs-root raw_fbs_unpacked] [--only DATE[,DATE...]]
#          [--no-rg-mode-scale] [--apply]
#
# Dry run by default.  Back up the dates directory before --apply.
# Input values must be the ORIGINAL invertMisreg output -- this is not
# idempotent against an already-rebased solution.  Restore from backup first.

import argparse
import os
import shelve
import sys

# range sample spacing in units of one FBS sample
SPACING = {'FBS': 1.0, 'FBD': 2.0}


def get_const(poly):
    c = None
    f = getattr(poly, 'getCoeffs', None)
    if callable(f):
        try:
            c = f()
        except Exception:
            c = None
    if c is None:
        c = getattr(poly, '_coeffs', None)
    if not c:
        return None
    try:
        return float(c[0][0])
    except Exception:
        return None


def set_const(poly, val):
    c = None
    f = getattr(poly, 'getCoeffs', None)
    if callable(f):
        try:
            c = f()
        except Exception:
            c = None
    if c is None:
        c = getattr(poly, '_coeffs', None)
    if not c:
        raise RuntimeError('no coefficient array on %r' % type(poly))
    c[0][0] = float(val)
    s = getattr(poly, 'setCoeffs', None)
    if callable(s):
        s(c)
    else:
        poly._coeffs = c
    return poly


def read_all(dates_dir):
    out = {}
    for d in sorted(os.listdir(dates_dir)):
        p = os.path.join(dates_dir, d, 'misreg')
        if not any(os.path.exists(p + e) for e in ('.dat', '.dir', '.db', '')):
            continue
        try:
            db = shelve.open(p, 'r')
        except Exception as e:
            out[d] = (None, None, str(e))
            continue
        try:
            az = get_const(db['azpoly']) if 'azpoly' in db else None
            rg = get_const(db['rgpoly']) if 'rgpoly' in db else None
            out[d] = (az, rg, None)
        finally:
            db.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ref')
    ap.add_argument('--dates-dir', default='refineSecondaryTiming/dates')
    ap.add_argument('--fbs-root', default='raw_fbs_unpacked')
    ap.add_argument('--fbs-dates', default='')
    ap.add_argument('--fbd-dates', default='')
    ap.add_argument('--only', default='')
    ap.add_argument('--no-rg-mode-scale', action='store_true')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()

    if not os.path.isdir(a.dates_dir):
        sys.exit('FAIL: no such directory %s' % a.dates_dir)

    forced_fbs = set(x for x in a.fbs_dates.split(',') if x)
    forced_fbd = set(x for x in a.fbd_dates.split(',') if x)
    only = set(x for x in a.only.split(',') if x)

    def mode(d):
        if d in forced_fbs:
            return 'FBS'
        if d in forced_fbd:
            return 'FBD'
        return 'FBS' if os.path.isdir(os.path.join(a.fbs_root, d)) else 'FBD'

    before = read_all(a.dates_dir)
    if a.ref not in before:
        sys.exit('FAIL: reference %s has no misreg shelve under %s' % (a.ref, a.dates_dir))
    raz, rrg, err = before[a.ref]
    if raz is None or rrg is None:
        sys.exit('FAIL: cannot read reference constants for %s (%s)' % (a.ref, err))

    rmode = mode(a.ref)
    if not os.path.isdir(a.fbs_root):
        print('WARNING: %s not found - mode detection will call every date FBD'
              % a.fbs_root)

    counts = {}
    for d in before:
        counts[mode(d)] = counts.get(mode(d), 0) + 1
    print('reference %s  mode %s  az %+.4f  rg %+.4f' % (a.ref, rmode, raz, rrg))
    print('modes detected from %s/: %s' % (a.fbs_root, counts))
    if a.no_rg_mode_scale:
        print('range scaling DISABLED (--no-rg-mode-scale): v1 behaviour')
    else:
        print('range constant scaled by  spacing(%s) / spacing(mode)' % rmode)
    if only:
        print('restricted to: %s' % ', '.join(sorted(only)))
    print('')
    print('%-10s %-4s %6s %10s %10s   %10s %10s'
          % ('DATE', 'MODE', 'RGFAC', 'AZ_BEFORE', 'RG_BEFORE', 'AZ_AFTER', 'RG_AFTER'))

    plan = {}
    for d in sorted(before):
        az, rg, e = before[d]
        if az is None or rg is None:
            print('%-10s %-4s %6s %10s %10s   ERROR %s' % (d, mode(d), '-', 'ERR', 'ERR', e))
            continue
        m = mode(d)
        fac = 1.0 if a.no_rg_mode_scale else SPACING[rmode] / SPACING[m]
        if only and d not in only:
            print('%-10s %-4s %6.3f %10.4f %10.4f   %10s %10s'
                  % (d, m, fac, az, rg, 'skip', 'skip'))
            continue
        naz, nrg = az - raz, rg - rrg * fac
        mark = '  <-- REF' if d == a.ref else ''
        print('%-10s %-4s %6.3f %10.4f %10.4f   %10.4f %10.4f%s'
              % (d, m, fac, az, rg, naz, nrg, mark))
        plan[d] = (naz, nrg)

    print('\n%d dates in plan' % len(plan))

    if not a.apply:
        print('\n[DRY RUN]  nothing written.  Back up %s, then re-run with --apply'
              % a.dates_dir)
        return

    written = 0
    for d, (naz, nrg) in sorted(plan.items()):
        p = os.path.join(a.dates_dir, d, 'misreg')
        db = shelve.open(p, 'w', writeback=False)
        try:
            db['azpoly'] = set_const(db['azpoly'], naz)
            db['rgpoly'] = set_const(db['rgpoly'], nrg)
        finally:
            db.close()
        written += 1
    print('\nwrote %d shelves' % written)

    after = read_all(a.dates_dir)
    bad = []
    for d, (naz, nrg) in plan.items():
        az, rg, _e = after.get(d, (None, None, 'missing'))
        if az is None or rg is None or abs(az - naz) > 1e-6 or abs(rg - nrg) > 1e-6:
            bad.append(d)
    if a.ref in plan:
        aaz, arg, _ = after[a.ref]
        print('verify: reference %s now az %.6f rg %.6f' % (a.ref, aaz, arg))
        if abs(aaz) > 1e-9 or abs(arg) > 1e-9:
            bad.append(a.ref + '(nonzero)')
    if bad:
        print('FAIL: verification mismatch on %s' % bad)
        sys.exit(1)
    print('PASS: %d dates rebased onto %s' % (written, a.ref))


if __name__ == '__main__':
    main()
