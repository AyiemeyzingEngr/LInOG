#!/usr/bin/env python3
"""lp_datum.py -- linog_auto Phase 4c: G16, the datum rebase of the misregistration onto the reference, then G9.

Runs inside lp_env.sh. invertMisreg pins the earliest date, not the reference (linog_reference_datum_bug), so run_06
would resample every secondary misreg(REF) away from the reference. G16 subtracts the reference's constants: azimuth in
full on every date, range scaled by spacing(REF mode) / spacing(date mode) (FBS 1, FBD 2; RGFAC 1 on an FBS-only stack).
It uses the kit's linog_redatum_misreg_v2.py (the 12 frames' and the rehearsal's tool) with the modes from
recon/modes.json passed explicitly (--fbs-dates/--fbd-dates: the tool reads them from raw_fbs_unpacked/, which an
FBS-only frame does not have), as the kit driver's datum phase does it: a dry run, a copy of dates/ into
dates_predatum_bak_<UTC>/, then --apply, which rewrites the shelves in place. The tool is not idempotent, so this
phase applies only to dates/ exactly as invert recorded it, computes the plan itself from invert's values and checks the
tool's plan and its result against it. G9 (the kit's linog_misreg_gate.py) then reads the spreads (FAIL above 5 px).
v0.13 (R9, the ascending record 17.3, with 18.5): on an FBS+FBD frame run_04's pairs mix range units (refineSecondaryTiming.py
107f3632 scales each pair by SLR(a) / SLR(b) and PRF(b) / PRF(a), right only when a has the reference's pixel; 17.2), so
this phase writes dates/ itself from the pair shelves by a consistent inversion, in place of invertMisreg's values rebased
by G16: (1) each pair's azpoly and rgpoly, constants; (2) its SLR and PRF from the two shelve copies run_04 made beside it,
the values its ratios used, every date's equal over its copies and SLC/<d>/ within 1e-9; (3) back to reference units:
o_rg = p_rg x SLR(b) / SLR(a), o_az = p_az x PRF(a) / PRF(b); (4) the least squares of o(a, b) = x(b) - x(a), float64, the
reference's column taken out (x(REF) = 0, so no rebase follows); (5) each date in its own units: rg(d) = x_rg(d) x
SLR(REF) / SLR(d), az(d) = x_az(d) x PRF(d) / PRF(REF); (6) dates/<d>/misreg's constants set to those (as the kit's tool
sets them, the polynomials invertMisreg wrote kept), after the pre-datum copy, under the signal hold. R9 reads only the
pair shelves, so it is idempotent: a repeat applies the same values again. On an FBS-only or FBD-only frame (one SLR on
every date: the range chain is exact) the phase stays v0.12's, the kit's G16 on invertMisreg's output, and R9 runs as a
reading (G4c.10); nothing it writes changes, and the fingerprint is v0.12's (method R9 and the two scripts' md5s enter it
on a mixed frame only), so path 84's frames stay CURRENT.

Gates
  G4c.1  invert PASS on record; recon/reference.json, the fineResamp configs (the kit's need_ref) and refine name
         the same reference                                                                              FAIL
  G4c.2  environment                                                                                  ERROR
  G4c.3  the kit's G16 and G9 at their pins; v0.13: refineSecondaryTiming.py (R9 undoes its ratios) and invertMisreg.py
         at theirs                                                                                    FAIL
  G4c.4  dates/ is invertMisreg's output as invert recorded it (not rebased); or this phase's own earlier
         apply, complete (md5s_after on record) with its pre-datum copy intact: then checked again below,
         never applied twice (v0.13, R9: applied again, the same values; a dates/ that is neither stays a DECISION) DECISION
  G4c.5  the modes of the dates (recon/modes.json)                                                    FAIL
  G4c.8  (v0.13, R9, a mixed frame) the pair shelves are refine's pairs on record, one each (pairs/ holds no other
         folder), readable, constant polynomials, both shelve copies beside each; each date's SLR and PRF equal over
         its copies and SLC/<d>/ within 1e-9; where refine's logs keep run_04's printed "rgratio, azratio", those =
         SLR(a) / SLR(b) and PRF(b) / PRF(a) from the copies within 1e-12                              FAIL
  G4c.9  (v0.13, R9, a mixed frame) the pairs connect every date (rank n - 1)                         FAIL
  G9p    the plan's azimuth and range spreads not above 5 px, before anything is rewritten            FAIL
  G4c.6  the kit's dry run: its plan = this phase's plan within 1e-4 on every date (v0.13: N/A on a mixed frame,
         the kit's G16 not run)                                                                        FAIL
  G4c.10 (v0.13) R9 beside v0.12: on a mixed frame R9's RMSE in range and azimuth (reference units) beside
         invertMisreg's (G4b.8), the values invertMisreg and G16 would have written, and per date the residual they
         would have left after run_06 (R9's truth less what v0.12 applies, reference units), its rms by mode; on an
         FBS-only or FBD-only frame the largest difference between R9 and v0.12's datum                INFO
  G4c.7  the copy: dates_predatum_bak_<UTC>/ with the md5 of every shelve file of dates/              FAIL
  G16    --apply: rc 0, "PASS: N dates rebased"; every date = the plan within 1e-6; the reference 0 and 0 (v0.13, a
         mixed frame: R9's write, every date = R9's plan within 1e-6, the reference 0 and 0)            FAIL
  G9     the kit's misreg gate: azimuth and range spreads below 5 px (and equal to the plan's)       FAIL
v0.13 r2 (the part 6 review's P6R-01): G4c.8 and G16 count a value off unless it is within its line, so a NaN is off (the
form abs(x) > tol read it as on), and G4c.8 names a date whose SLC/<d>/ SLR or PRF is not a finite positive number; on
finite values every verdict is v0.13's, and LOGIC and the fingerprint are v0.13's (datum comes before admit).
The record names the copy before --apply runs; --apply runs in a session of its own while this phase holds SIGINT,
SIGTERM and SIGHUP, and md5s_after is on record before a held signal ends the phase (ERROR); the next run then finds
the complete apply at G4c.4 and checks it again.
--dryrun DIR: a plan only. v0.13, a mixed frame (by the frame's recon/modes.json) whose DIR holds a planned invert: when the
frame itself is past refine, R9's plan from its own pair shelves, printed and recorded in DIR (with its invert, refine and
datum records when its invert is PASS; from refine's record alone, G4c.4 and G4c.10 not read, when invert has not run);
a one-mode frame plans as v0.12. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
Self-test only (under a path table other than the package's own): LINOG_MOCK_DATUM_V12=1 takes v0.12's path on a mixed
frame (M67b: what v0.12 leaves); LINOG_MOCK_R9SLEEP=<s> holds R9's write that long inside the signal hold, writing
LINOG_MOCK_MARK first (M72h: a stop during the write).
"""
import argparse
import collections
import glob
import math
import os
import re
import shutil
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'datum', '4c', 1
KIT = ('linog_redatum_misreg_v2.py', 'linog_misreg_gate.py')
SPACING = {'FBS': 1.0, 'FBD': 2.0}
G9_MAX_SPREAD = 5.0   # linog_misreg_gate.py: FAIL when a spread is above 5.0 px
ROW = re.compile(r'^(\d{8})\s+(FBS|FBD)\s+([\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)')
R9_ISCE = ('refineSecondaryTiming.py', 'invertMisreg.py')   # R9 undoes the first's ratios and replaces the second's values
R9_SAME, R9_RATIO, R9_G16 = 1e-9, 1e-12, 1e-6
RATIO_LINE = re.compile(r'rgratio, azratio:\s+(\S+)\s+(\S+)')


# ------------------------------------------------------------------------------------------------ R9 (17.3)
def shelf_slr_prf(sd):
    """(range pixel, PRF) of a shelve folder, as refineSecondaryTiming.py reads them: the instrument's range pixel and the
    frame's PRF (the instrument's when the frame has none); needs ISCE on the path to unpickle."""
    import shelve
    with shelve.open(os.path.join(sd, 'data'), 'r') as db:
        f = db['frame']
    ins = P2.get(f, 'instrument', 'getInstrument')
    slr = P2.get(ins, 'rangePixelSize', 'getRangePixelSize')
    prf = getattr(f, 'PRF', None)
    if prf is None:
        prf = P2.get(ins, 'PRF', 'getPulseRepetitionFrequency')
    return float(slr), float(prf)


def poly_const(poly):
    """(the constant, the orders (azimuth, range), the coefficient array's shape) of a misreg polynomial."""
    c = poly.getCoeffs() if callable(getattr(poly, 'getCoeffs', None)) else getattr(poly, '_coeffs', None)
    ao = poly.getAzimuthOrder() if callable(getattr(poly, 'getAzimuthOrder', None)) else getattr(poly, '_azimuthOrder', None)
    ro = poly.getRangeOrder() if callable(getattr(poly, 'getRangeOrder', None)) else getattr(poly, '_rangeOrder', None)
    shape = (len(c), len(c[0]) if c else 0) if c else (0, 0)
    return (float(c[0][0]) if c and c[0] else None), (ao, ro), shape


def r9_read(W, pairs, dates, refine_logdir):
    """17.3's steps 1 and 2: {pair: dict(a, b, paz, prg, slr_a, prf_a, slr_b, prf_b)}, {date: (slr, prf)} from SLC/<d>/,
    G4c.8's findings, the number of pairs whose run_04 log printed its ratios."""
    import shelve
    vals, bad, copies = {}, [], collections.defaultdict(list)
    for pr in pairs:
        a, b = pr.split('_')
        pd = os.path.join(W, 'refineSecondaryTiming', 'pairs', pr)
        try:
            with shelve.open(os.path.join(pd, 'misreg'), 'r') as db:
                az, rg = db['azpoly'], db['rgpoly']
        except Exception as e:  # noqa: BLE001
            bad.append('%s: its misreg shelve unreadable (%s: %s)' % (pr, type(e).__name__, e))
            continue
        (paz, oaz, saz), (prg, org, srg) = poly_const(az), poly_const(rg)
        if oaz != (0, 0) or org != (0, 0) or saz != (1, 1) or srg != (1, 1):
            bad.append('%s: not constant polynomials (azimuth orders %s, %s coefficients; range orders %s, %s)' % (
                pr, oaz, saz, org, srg))
            continue
        if paz is None or prg is None or not (math.isfinite(paz) and math.isfinite(prg)):
            bad.append('%s: constants %s %s' % (pr, paz, prg))
            continue
        side = {}
        for k, d in (('referenceShelve', a), ('secondaryShelve', b)):
            try:
                side[k] = shelf_slr_prf(os.path.join(pd, k))
                copies[d].append(side[k] + ('%s/%s' % (pr, k),))
            except Exception as e:  # noqa: BLE001
                bad.append('%s: its %s copy unreadable (%s: %s)' % (pr, k, type(e).__name__, e))
        if len(side) < 2:
            continue
        vals[pr] = dict(a=a, b=b, paz=paz, prg=prg, slr_a=side['referenceShelve'][0], prf_a=side['referenceShelve'][1],
                        slr_b=side['secondaryShelve'][0], prf_b=side['secondaryShelve'][1])
    per = {}
    for d in dates:
        try:
            s0, p0 = shelf_slr_prf(os.path.join(W, 'SLC', d))
        except Exception as e:  # noqa: BLE001
            bad.append('SLC/%s: its shelve unreadable (%s: %s)' % (d, type(e).__name__, e))
            continue
        per[d] = (s0, p0)
        if not (math.isfinite(s0) and math.isfinite(p0) and s0 > 0 and p0 > 0):   # v0.13 r2 (P6R-01): a NaN is not a pixel
            bad.append('%s: SLC/%s holds SLR %r m and PRF %r Hz, not finite positive numbers' % (d, d, s0, p0))
            continue
        # v0.13 r2 (the part 6 review's P6R-01): a copy is off unless it is within the line, so a NaN copy is off
        off = ['%s %.12g m %.10g Hz' % (w, sl, pf) for sl, pf, w in copies[d]
               if not (abs(sl / s0 - 1.0) <= R9_SAME and abs(pf / p0 - 1.0) <= R9_SAME)]
        if off:
            bad.append('%s: SLR or PRF differs between its copies: SLC/%s %.12g m %.10g Hz; %s' % (d, d, s0, p0, '; '.join(off[:3])))
    nlog = 0
    for pr, v in sorted(vals.items()):
        lg = sorted(glob.glob(os.path.join(refine_logdir or '/nonexistent', '*', '*_%s.log' % pr)))
        m = None
        for f in lg[-1:]:
            m = RATIO_LINE.search(open(f, errors='replace').read())
        if not m:
            continue
        nlog += 1
        try:
            rgr, azr = float(m.group(1)), float(m.group(2))
        except ValueError:
            bad.append('%s: run_04\'s ratios line unreadable: %s' % (pr, m.group(0)))
            continue
        wr, wa = v['slr_a'] / v['slr_b'], v['prf_b'] / v['prf_a']
        if not (abs(rgr - wr) <= R9_RATIO and abs(azr - wa) <= R9_RATIO):   # v0.13 r2 (P6R-01): a NaN ratio is off
            bad.append('%s: run_04 printed rgratio %r azratio %r, the copies give %r %r' % (pr, rgr, azr, wr, wa))
    return vals, per, bad, nlog


def g16_off(after, plan, ref):
    """G16 after the write: the dates whose shelves do not read the plan within R9_G16 (1e-6), and a reference that does not
    read 0 and 0 within 1e-9. v0.13 r2 (the part 6 review's P6R-01): a value is off unless it is within its line, so a NaN
    is off (the form abs(x) > tol read a NaN as on); on finite values the verdicts are the earlier ones."""
    bad = []
    for d, (az, rg) in sorted(after.items()):
        if not (abs(az - plan[d][0]) <= R9_G16 and abs(rg - plan[d][1]) <= R9_G16):
            bad.append('%s reads az %.6f rg %.6f, plan %.6f %.6f' % (d, az, rg, plan[d][0], plan[d][1]))
    if ref in after and not (abs(after[ref][0]) <= 1e-9 and abs(after[ref][1]) <= 1e-9):
        bad.append('the reference reads az %.9f rg %.9f' % after[ref])
    return bad


def r9_solve(vals, per, dates, ref):
    """17.3's steps 3 to 5: dict(x_az, x_rg (reference units), az, rg (each date's own), rmse_az, rmse_rg, rank, n)."""
    import numpy as np
    idx = dict((d, i) for i, d in enumerate(dates))
    prs = sorted(vals)
    A = np.zeros((len(prs), len(dates)))
    oaz, org = np.zeros(len(prs)), np.zeros(len(prs))
    for k, pr in enumerate(prs):
        v = vals[pr]
        A[k, idx[v['b']]], A[k, idx[v['a']]] = 1.0, -1.0
        org[k] = v['prg'] * v['slr_b'] / v['slr_a']
        oaz[k] = v['paz'] * v['prf_a'] / v['prf_b']
    rank = int(np.linalg.matrix_rank(A)) if len(prs) else 0
    keep = [i for i, d in enumerate(dates) if d != ref]
    out = dict(rank=rank, n=len(dates), pairs=len(prs))
    if rank < len(dates) - 1 or ref not in idx:
        return out
    xs = {}
    for name, o in (('az', oaz), ('rg', org)):
        sol = np.linalg.lstsq(A[:, keep], o, rcond=None)[0]
        x = np.zeros(len(dates))
        x[keep] = sol
        xs[name] = x
        res = o - A.dot(x)
        out['rmse_' + name] = float(np.sqrt(np.sum(res ** 2) / len(res)))
    sr, pr_ = per[ref]
    out['x_az'] = dict((d, float(xs['az'][idx[d]])) for d in dates)
    out['x_rg'] = dict((d, float(xs['rg'][idx[d]])) for d in dates)
    out['az'] = dict((d, out['x_az'][d] * per[d][1] / pr_) for d in dates)
    out['rg'] = dict((d, out['x_rg'][d] * sr / per[d][0]) for d in dates)
    return out


def r9_gates(st, W, rr, dates, ref):
    """G4c.8 and G4c.9 on an FBS+FBD frame (17.3): refine's pairs on record read (r9_read), pairs/ holding no folder its record
    lacks (the part 4 review's P4-14), then the rank. Returns (vals, per, sol) with sol holding R9's values, or None after a
    FAIL gate."""
    pairs = sorted((rr.get('outputs') or {}).get('misreg') or {})
    vals, per, bad9, nlog = r9_read(W, pairs, dates, (rr.get('outputs') or {}).get('logdir'))
    pd = os.path.join(W, 'refineSecondaryTiming', 'pairs')
    extra = sorted(set(os.listdir(pd)) - set(pairs)) if os.path.isdir(pd) else []
    bad = bad9 + (['pairs/ holds %d folder(s) refine\'s record does not: %s' % (len(extra), ', '.join(extra[:6]))] if extra else [])
    ok8 = not bad and len(vals) == len(pairs)
    st.gate('G4c.8', 'the pair shelves (R9)', 'PASS' if ok8 else 'FAIL', '%d of %d pairs of refine\'s record read, constant; %d dates\' '
            'SLR and PRF one value over their copies; run_04\'s printed ratios checked on %d pairs' % (len(vals), len(pairs), len(per), nlog),
            'refine\'s pairs, one each, readable, constant, both copies; one SLR and PRF a date (%g); the printed ratios (%g)' % (
                R9_SAME, R9_RATIO), '\n'.join(bad[:10]))
    if not ok8:
        return vals, per, None
    sol = r9_solve(vals, per, dates, ref)
    st.gate('G4c.9', 'the pairs connect the dates (R9)', 'PASS' if sol.get('rank') == len(dates) - 1 else 'FAIL',
            'rank %s of %d dates (%d pairs)' % (sol.get('rank'), len(dates), len(vals)), 'n - 1',
            '' if sol.get('rank') == len(dates) - 1 else 'the pairs split the dates: R9 cannot place them on one reference')
    return vals, per, (sol if 'az' in sol else None)


def dry_from_refine(st, W, rr, ref, dates, modes, env, s, tools):
    """v0.13 (17.9's M74; the part 4 review's P4-07): the dry run of an FBS+FBD frame past refine whose invert has not run:
    R9's plan from the frame's own pair shelves and refine's record, printed and recorded (G4c.4, the kit's plan and
    G4c.10's v0.12 values need invert's output, and are not read); writes only DIR."""
    ro = rr.get('outputs') or {}
    why = [] if ro.get('reference') == ref else ['refine ran with reference %s, recon/reference.json names %s' % (ro.get('reference'), ref)]
    st.gate('G4c.1', 'invert PASS on record', 'FAIL' if why else 'N/A', '; '.join(why) or 'dry run: the frame past refine (PASS on record, '
            '%d dates, reference %s), its invert not run: R9 plans from refine\'s pair shelves' % (len(dates), ref),
            'the reference the rebase uses = the one run_06 resamples onto')
    if why:
        return st.finish()
    if not P2.env_gate(st, 'G4c.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4c.3', tools, 'the kit\'s G16 and G9, refineSecondaryTiming.py and invertMisreg.py (R9)'):
        return st.finish()
    bad = ['%s: mode %s' % (d, m) for d, m in modes.items() if m not in SPACING] + \
        ([] if ref in modes else ['the reference %s is not among the dates' % ref])
    st.gate('G4c.5', 'the modes', 'FAIL' if bad else 'PASS', '%d FBS, %d FBD (recon/modes.json); the reference %s %s' % (
        sum(1 for m in modes.values() if m == 'FBS'), sum(1 for m in modes.values() if m == 'FBD'), ref, modes.get(ref)),
        'FBS or FBD for every date', '\n'.join(bad))
    if bad:
        return st.finish()
    _, per, sol = r9_gates(st, W, rr, dates, ref)
    if not sol:
        return st.finish()
    plan = dict((d, (sol['az'][d], sol['rg'][d])) for d in dates)
    paz = max(v[0] for v in plan.values()) - min(v[0] for v in plan.values())
    prg = max(v[1] for v in plan.values()) - min(v[1] for v in plan.values())
    over = [x for x, v in (('azimuth', paz), ('range', prg)) if v > G9_MAX_SPREAD]
    st.gate('G9p', 'misregistration spread (the plan)', 'FAIL' if over else 'PASS', 'azimuth %.3f, range %.3f px after the R9 '
            'inversion' % (paz, prg), 'not above %.1f px (linog_misreg_gate.py), checked before the write' % G9_MAX_SPREAD)
    if over:
        return st.finish()
    st.gate('G4c.6', 'the kit\'s dry run', 'N/A', 'an FBS+FBD frame: R9 writes dates/, the kit\'s G16 is not run (17.3)')
    print('   R9 would write %d dates (reference %s at 0 and 0) once invert has run; the largest |rg| %.4f px, |az| %.4f lines' % (
        len(plan), ref, max(abs(v[1]) for v in plan.values()), max(abs(v[0]) for v in plan.values())))
    st.rec['outputs'] = dict(planned=True, dryrun=True, note='datum, from refine\'s record (invert not run)', method='R9',
                             plan={d: list(v) for d, v in sorted(plan.items())},
                             r9=dict(x_az=sol['x_az'], x_rg=sol['x_rg'], az=sol['az'], rg=sol['rg'], rmse_az=sol['rmse_az'],
                                     rmse_rg=sol['rmse_rg'], rank=sol['rank'], pairs=sol['pairs'],
                                     slr_prf=dict((d, list(v)) for d, v in sorted(per.items()))))
    return st.finish('plan only (dry run, from refine\'s record)')


def r9_beside(r9, v12, per, ref, modes):
    """G4c.10's reading: per date the residual v0.12's values leave after run_06 in reference units (R9's x less what v0.12
    applies, converted), the largest differences, the rms by mode."""
    sr, prr = per[ref]
    resid = {}
    for d in sorted(r9['x_az']):
        if d not in v12:
            continue
        az, rg = v12[d]
        resid[d] = (r9['x_az'][d] - az * prr / per[d][1], r9['x_rg'][d] - rg * per[d][0] / sr)
    rms = {}
    for m in ('FBS', 'FBD'):
        xs = [v for d, v in resid.items() if modes.get(d) == m and d != ref]
        if xs:
            rms[m] = (math.sqrt(sum(a * a for a, _ in xs) / len(xs)), math.sqrt(sum(b * b for _, b in xs) / len(xs)))
    dmax = (max((abs(r9['az'][d] - v12[d][0]) for d in v12 if d in r9['az']), default=None),
            max((abs(r9['rg'][d] - v12[d][1]) for d in v12 if d in r9['rg']), default=None))
    return resid, rms, dmax


def r9_write(W, plan):
    """17.3's step 6: dates/<d>/misreg's constants set to R9's (as the kit's linog_redatum_misreg_v2.py sets them: the
    polynomials invertMisreg wrote, their constant replaced). A shelve that already holds both values exactly is not opened
    for writing (a repeat changes no byte of dates/: ISCE's shelves are dbm.dumb, which appends on every write).
    Returns (written, already)."""
    import shelve
    n = same = 0
    for d, (az, rg) in sorted(plan.items()):
        p = os.path.join(W, 'refineSecondaryTiming', 'dates', d, 'misreg')
        if P3.shelf_consts(p) == (float(az), float(rg)):
            same += 1
            continue
        with shelve.open(p, 'w', writeback=False) as db:
            for key, val in (('azpoly', az), ('rgpoly', rg)):
                poly = db[key]
                c = poly.getCoeffs() if callable(getattr(poly, 'getCoeffs', None)) else poly._coeffs
                c[0][0] = float(val)
                if callable(getattr(poly, 'setCoeffs', None)):
                    poly.setCoeffs(c)
                else:
                    poly._coeffs = c
                db[key] = poly
        n += 1
    return n, same


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4c: G16 datum rebase (v0.13: R9 on a mixed frame), G9')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, r = P1.load_env(), P2.load_stack(), P3.load_run()
    tm = P3.tools(s, env, r, kit=KIT)
    tm9 = P3.tools(s, env, r, isce=R9_ISCE)
    # v0.13 (17.9's M74): the dry run of an FBS+FBD frame (by the frame's recon/modes.json) whose own invert is a plan reads the
    # frame's own records when the frame is past refine: its invert, refine and datum records when its invert is PASS, else
    # refine's alone (dry_from_refine), so the plan is R9's from the frame's pair shelves; one-mode frames plan as v0.12 (the
    # part 4 review's P4-15); only DIR is written
    rows, _, _ = P2.modes_rows(W)
    src, from_refine = recdir, False
    if a.dryrun and len(set(v.get('mode') for v in rows.values() if v.get('mode'))) > 1:
        dri, fri, frr = (P1.record(recdir, '4b', 'invert') or {}, P1.record(W, '4b', 'invert') or {},
                         P1.record(W, '4a', 'refine') or {})
        own = lambda x: x.get('verdict') == 'PASS' and not (x.get('outputs') or {}).get('planned')  # noqa: E731
        if (not dri or (dri.get('outputs') or {}).get('planned')) and own(frr):
            src, from_refine = W, not own(fri)
    geo, _ = P3.geometry(src)
    ref = (geo or {}).get('ref')
    ri = P1.record(src, '4b', 'invert') or {}
    oi = ri.get('outputs', {})
    dates = oi.get('dates') or []
    if from_refine:
        dates = (P1.record(W, '4a', 'refine') or {}).get('outputs', {}).get('dates') or []
    modes = {d: (rows.get(d) or {}).get('mode') for d in dates}
    mixed = len(set(m for m in modes.values() if m)) > 1
    hook_v12 = mixed and os.environ.get('LINOG_MOCK_DATUM_V12') and C.selftest_hook('LINOG_MOCK_DATUM_V12')
    r9 = mixed and not hook_v12
    fpd = dict(logic=LOGIC, reference=ref, invert=oi.get('md5s'), modes=modes, tools={k: v[1] for k, v in tm.items()})
    if r9:   # 17.3: method R9 and the two scripts' md5s enter the fingerprint on a mixed frame only
        fpd.update(method='R9', r9_tools={k: v[1] for k, v in tm9.items()})
    fp = C.md5_obj(fpd)
    if a.state:
        def missing(rec):
            o = (rec or {}).get('outputs', {})
            out = []
            if P3.shelf_md5s(W, 'refineSecondaryTiming/dates') != o.get('md5s_after'):
                out.append('dates/ is not the datum on record')
            b = o.get('backup')
            if not b or P3.shelf_md5s(W, b) != {n.replace('refineSecondaryTiming/dates/', b + '/', 1): m
                                                 for n, m in (o.get('md5s_before') or {}).items()}:
                out.append('the pre-datum copy %s is not as recorded' % b)
            return out
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    own0 = P1.record(src, IDX, PHASE) or {}   # read before begin() replaces it (a copy goes to status/history/)
    inputs = dict(modes=modes, method='R9' if r9 else 'G16', tools={k: dict(path=v[0], md5=v[1]) for k, v in list(tm.items()) +
                                                                    list(tm9.items())})
    if src != recdir:
        inputs['records'] = ('the frame\'s own refine record (its invert not run; DIR\'s invert a plan)' if from_refine else
                             'the frame\'s own invert, refine and datum records (DIR\'s invert a plan)')
    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, inputs, a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun, '   method %s%s' % ('R9 (an FBS+FBD frame, 17.3)' if r9 else
                                                                    'G16 (v0.12%s)' % (', the self-test\'s hook' if hook_v12 else ''),
                                                                    ('; %s' % inputs['records']) if src != recdir else ''))
    if from_refine:
        return dry_from_refine(st, W, P1.record(W, '4a', 'refine') or {}, ref, dates, modes, env, s,
                               dict(list(tm.items()) + list(tm9.items())))
    ri = P3.prior3(st, 'G4c.1', src, '4b', 'invert')
    if not ri:
        return st.finish()
    planned = ri.get('outputs', {}).get('planned')
    rr = P1.record(src, '4a', 'refine') or {}
    if planned:
        st.gate('G4c.1', 'invert PASS on record', 'PASS', 'dry-run invert was a plan only')
    else:
        cref = sorted(P3.fine_cfg_refs(W))
        why = []
        if cref != [ref]:
            why.append('configs/config_fineResamp_* name %s as their reference, recon/reference.json %s' % (
                ', '.join(cref) or 'none', ref))
        if (rr.get('outputs') or {}).get('reference') != ref:
            why.append('refine ran with reference %s, recon/reference.json names %s' % ((rr.get('outputs') or {}).get('reference'), ref))
        st.gate('G4c.1', 'invert PASS on record', 'FAIL' if why else 'PASS', '; '.join(why) or '%d dates; the earliest %s pinned '
                'at 0; reference %s (reference.json, the fineResamp configs and refine agree)' % (len(dates), oi.get('first'), ref),
                'the reference the rebase uses = the one run_06 resamples onto')
        if why:
            return st.finish()
    if not P2.env_gate(st, 'G4c.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4c.3', dict(list(tm.items()) + list(tm9.items())), 'the kit\'s G16 and G9, refineSecondaryTiming.py '
                        'and invertMisreg.py (R9)'):
        return st.finish()
    if planned:
        return P3.plan_only(st, {}, 'after a planned invert')

    # G4c.4: dates/ is invert's output; or this phase's own earlier apply, complete, with its copy intact (a stop after
    # --apply, or a re-run after a PASS): then it is checked again (v0.12) or applied again (R9: the same values)
    cur = P3.shelf_md5s(W, 'refineSecondaryTiming/dates')
    o0 = own0.get('outputs') or {}
    bk0 = o0.get('backup')

    def copy_intact(bk, before):
        return bool(bk) and P3.shelf_md5s(W, bk) == {n.replace('refineSecondaryTiming/dates/', bk + '/', 1): m
                                                     for n, m in (before or {}).items()}
    resume = False
    if cur != oi.get('md5s'):
        applied = bool(o0.get('md5s_after')) and cur == o0.get('md5s_after')
        same_method = (o0.get('method') or 'G16') == ('R9' if r9 else 'G16')
        if applied and same_method and o0.get('md5s_before') == oi.get('md5s') and o0.get('reference') == ref and \
                copy_intact(bk0, o0.get('md5s_before')):
            resume = True
            if r9:
                how = 'R9 %s (it reads only the pair shelves: the same values)' % ('would be applied again' if a.dryrun else
                                                                                   'applied again below')
            else:
                how = 'would be checked again, not applied twice' if a.dryrun else 'checked again below, not applied twice'
            st.gate('G4c.4', 'dates/ as invert wrote it', 'PASS', 'dates/ is the datum the run of %s applied (its record: %s); the '
                    'pre-datum copy %s intact: %s' % (own0.get('start'), own0.get('verdict'), bk0, how),
                    'invert\'s md5s, or this phase\'s own complete apply with its copy')
        else:
            what = ('the datum the run of %s applied, but its pre-datum copy %s is not as recorded' % (own0.get('start'), bk0)
                    if applied and same_method else 'neither invertMisreg\'s output on record nor a complete datum on record')
            back = ('move dates/ into %s/_archive/ and copy %s back as dates/, or run invert again' % (
                W, ('refineSecondaryTiming/%s/' % os.path.basename(bk0)) if bk0 else 'the newest refineSecondaryTiming/'
                'dates_predatum_bak_*/'))
            st.gate('G4c.4', 'dates/ as invert wrote it', 'DECISION', 'dates/ is %s' % what,
                    'the md5 of every shelve file = invert\'s record',
                    ('R9 writes its values over invert\'s output, so a dates/ that is neither is a person\'s to look at before the '
                     'copy is taken (17.3): to apply R9, %s' % back) if r9 else 'G16 is not idempotent: to apply it again, %s' % back)
            return st.finish()
    else:
        st.gate('G4c.4', 'dates/ as invert wrote it', 'PASS', '%d shelve files, md5 as invert recorded them' % len(cur), 'not rebased')
    bad = ['%s: mode %s' % (d, m) for d, m in modes.items() if m not in SPACING]
    if ref not in modes:
        bad.append('the reference %s is not among the dates' % ref)
    fbs = sorted(d for d, m in modes.items() if m == 'FBS')
    fbd = sorted(d for d, m in modes.items() if m == 'FBD')
    st.gate('G4c.5', 'the modes', 'FAIL' if bad else 'PASS', '%d FBS, %d FBD (recon/modes.json); the reference %s %s' % (
        len(fbs), len(fbd), ref, modes.get(ref)), 'FBS or FBD for every date', '\n'.join(bad))
    if bad:
        return st.finish()
    before = {d: tuple(v) for d, v in oi['misreg'].items()}
    raz, rrg = before[ref]
    plan12 = {d: (az - raz, rg - rrg * SPACING[modes[ref]] / SPACING[modes[d]]) for d, (az, rg) in before.items()}

    # R9: on a mixed frame the plan (G4c.8, G4c.9); on every other frame a reading beside v0.12's plan (G4c.10)
    if r9:
        vals, per, sol = r9_gates(st, W, rr, dates, ref)
        if not sol:
            return st.finish()
        plan = dict((d, (sol['az'][d], sol['rg'][d])) for d in dates)
    else:
        pairs = sorted((rr.get('outputs') or {}).get('misreg') or {})
        vals, per, bad9, nlog = r9_read(W, pairs, dates, (rr.get('outputs') or {}).get('logdir'))
        sol = r9_solve(vals, per, dates, ref) if not bad9 and len(vals) == len(pairs) else {}
        plan = plan12
    # G9 from the plan, before anything is rewritten (the kit's G9 reads the same spreads after the write)
    paz = max(v[0] for v in plan.values()) - min(v[0] for v in plan.values())
    prg = max(v[1] for v in plan.values()) - min(v[1] for v in plan.values())
    over = [x for x, v in (('azimuth', paz), ('range', prg)) if v > G9_MAX_SPREAD]
    st.gate('G9p', 'misregistration spread (the plan)', 'FAIL' if over else 'PASS', 'azimuth %.3f, range %.3f px after the %s' % (
        paz, prg, 'R9 inversion' if r9 else 'rebase'), 'not above %.1f px (linog_misreg_gate.py), checked before the write' % G9_MAX_SPREAD,
        '' if not over else 'dates/ not rewritten: something upstream of run_05 is wrong (the kit: do NOT run run_06)')
    if over:
        return st.finish()
    # G4c.10: R9 beside v0.12
    r9rec = None
    if 'az' in sol:
        resid, rms, dmax = r9_beside(sol, plan12, per, ref, modes)
        r9rec = dict(x_az=sol['x_az'], x_rg=sol['x_rg'], az=sol['az'], rg=sol['rg'], rmse_az=sol['rmse_az'], rmse_rg=sol['rmse_rg'],
                     rank=sol['rank'], pairs=sol['pairs'], slr_prf=dict((d, list(v)) for d, v in sorted(per.items())),
                     v12=dict((d, list(v)) for d, v in sorted(plan12.items())),
                     residual_v12=dict((d, list(v)) for d, v in sorted(resid.items())), rms_v12=rms, max_diff=list(dmax),
                     invert_rmse=oi.get('rmse'))
        big = sorted(((d, v) for d, v in resid.items() if abs(v[1]) > 0.125), key=lambda kv: -abs(kv[1][1]))
        if mixed:
            val = ('R9\'s RMSE az %.4f rg %.4f (reference units), invertMisreg\'s az %s rg %s; v0.12\'s chain would leave %s' % (
                sol['rmse_az'], sol['rmse_rg'], (oi.get('rmse') or {}).get('azimuth'), (oi.get('rmse') or {}).get('range'),
                ', '.join('%s dates at rms az %.3f rg %.3f' % (m, v[0], v[1]) for m, v in sorted(rms.items()))))
        else:
            val = 'R9 beside v0.12\'s datum: largest difference az %.3g lines, rg %.3g px (one SLR: range exact but for ' \
                  'invertMisreg\'s float32; azimuth by the PRF ratios)' % dmax
        st.gate('G4c.10', 'R9 beside v0.12', 'INFO', val, 'a reading (17.3)', ('dates v0.12 would leave beyond 0.125 px in range: ' +
                ', '.join('%s %+.3f' % (d, v[1]) for d, v in big[:8])) if (mixed and big) else '')
    elif not r9:
        st.gate('G4c.10', 'R9 beside v0.12', 'INFO', 'R9 not read: %s' % ('; '.join(bad9[:2]) or 'rank %s of %d' % (sol.get('rank'),
                len(dates))), 'a reading (17.3)')
    if a.dryrun:
        if r9:
            st.gate('G4c.6', 'the kit\'s dry run', 'N/A', 'an FBS+FBD frame: R9 writes dates/, the kit\'s G16 is not run (17.3)')
            print('   R9 would write %d dates (reference %s at 0 and 0); the largest |rg| %.4f px, |az| %.4f lines' % (
                len(plan), ref, max(abs(v[1]) for v in plan.values()), max(abs(v[0]) for v in plan.values())))
        else:
            print('   G16 would rebase %d dates onto %s: az %+.4f and rg %+.4f subtracted (RGFAC 1 for FBS, 0.5 for FBD)' % (
                len(plan), ref, raz, rrg))
        st.rec['outputs'] = dict(planned=True, dryrun=True, note='datum', method='R9' if r9 else 'G16',
                                 plan={d: list(v) for d, v in sorted(plan.items())}, r9=r9rec)
        return st.finish('plan only (dry run)')
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    lg = os.path.join(logroot, 'G16_apply.log')
    out_common = dict(logdir=logroot, reference=ref, method='R9' if r9 else 'G16', before={d: list(v) for d, v in sorted(before.items())},
                      plan={d: list(v) for d, v in sorted(plan.items())}, r9=r9rec)
    m = None
    krc = 0
    if resume and not r9:
        bk_rel = bk0
        st.rec['outputs'] = dict(out_common, backup=bk0, md5s_before=o0.get('md5s_before'),
                                 resumed_from=dict(start=own0.get('start'), verdict=own0.get('verdict'), pid=own0.get('pid')))
    elif r9:
        st.gate('G4c.6', 'the kit\'s dry run', 'N/A', 'an FBS+FBD frame: R9 writes dates/, the kit\'s G16 is not run (17.3)')
        if resume:   # a repeat: the copy of invert's output kept, R9's values written again
            bk_rel = bk0
            st.rec['outputs'] = dict(out_common, backup=bk0, md5s_before=o0.get('md5s_before'),
                                     resumed_from=dict(start=own0.get('start'), verdict=own0.get('verdict'), pid=own0.get('pid')))
        else:
            bk_rel = 'refineSecondaryTiming/dates_predatum_bak_%s' % C.utc().replace('-', '').replace(':', '')
            shutil.copytree(os.path.join(W, 'refineSecondaryTiming', 'dates'), os.path.join(W, bk_rel), copy_function=shutil.copy2)
            ok = copy_intact(bk_rel, cur)
            st.gate('G4c.7', 'the pre-datum copy', 'PASS' if ok else 'FAIL', '%s: %d files, md5 = dates/' % (
                bk_rel, len(P3.shelf_md5s(W, bk_rel))), 'every shelve file copied', '' if ok else 'the copy differs from dates/')
            st.rec['outputs'] = dict(out_common, backup=bk_rel, md5s_before=cur)
            if not ok:
                return st.finish()
        st.rec['outputs']['applying'] = True
        st.write()
        with P3.Deferred():
            slp = os.environ.get('LINOG_MOCK_R9SLEEP') and C.selftest_hook('LINOG_MOCK_R9SLEEP')
            if slp:   # self-test only (M72h): a stop arriving while R9 writes is held until the write and its record are done
                if os.environ.get('LINOG_MOCK_MARK'):
                    with open(os.environ['LINOG_MOCK_MARK'], 'w') as fh:
                        fh.write('R9 write held %s s\n' % slp)
                time.sleep(float(slp))
            n9, same9 = r9_write(W, plan)
            st.rec['outputs'].update(applying=False, written=n9, already=same9, md5s_after=P3.shelf_md5s(W, 'refineSecondaryTiming/dates'))
            st.write()
        with open(lg, 'w') as fh:
            fh.write('R9 (lp_datum.py, 17.3): %d dates written onto %s, %d already held R9\'s values\n' % (n9, ref, same9))
            for d, (az, rg) in sorted(plan.items()):
                fh.write('%s %s az %+.9f rg %+.9f\n' % (d, modes[d], az, rg))
    else:
        args = [ref, '--dates-dir', 'refineSecondaryTiming/dates', '--fbs-dates', ','.join(fbs)] + \
            (['--fbd-dates', ','.join(fbd)] if fbd else [])
        lgd = os.path.join(logroot, 'G16_dryrun.log')
        krc, out = P3.kit_run(env, KIT[0], args, W, lgd)
        got = {mm.group(1): (mm.group(2), float(mm.group(3)), float(mm.group(6)), float(mm.group(7))) for mm in
               (ROW.match(x) for x in out.splitlines()) if mm}
        bad = []
        if krc != 0 or '[DRY RUN]' not in out:
            bad.append('rc %d, %s' % (krc, 'a [DRY RUN] line' if '[DRY RUN]' in out else 'no [DRY RUN] line'))
        for d, (qaz, qrg) in sorted(plan.items()):
            g = got.get(d)
            fac = SPACING[modes[ref]] / SPACING[modes[d]]
            if not g or g[0] != modes[d] or abs(g[1] - fac) > 1e-3 or abs(g[2] - qaz) > 1e-4 or abs(g[3] - qrg) > 1e-4:
                bad.append('%s: kit %s, plan %s %.3f %.4f %.4f' % (d, g, modes[d], fac, qaz, qrg))
        extra = sorted(set(got) - set(plan))
        if extra:
            bad.append('the kit plans dates this phase does not: %s' % ', '.join(extra))
        st.gate('G4c.6', 'the kit\'s dry run', 'FAIL' if bad else 'PASS', '%d dates planned, as this phase plans them: reference %s '
                'az %+.4f rg %+.4f subtracted' % (len(got), ref, raz, rrg), 'within 1e-4 on every date', '\n'.join(bad[:10] +
                (['log %s' % lgd] if bad else [])))
        if bad:
            return st.finish()
        bk_rel = 'refineSecondaryTiming/dates_predatum_bak_%s' % C.utc().replace('-', '').replace(':', '')
        bk = os.path.join(W, bk_rel)
        shutil.copytree(os.path.join(W, 'refineSecondaryTiming', 'dates'), bk, copy_function=shutil.copy2)
        ok = copy_intact(bk_rel, cur)
        st.gate('G4c.7', 'the pre-datum copy', 'PASS' if ok else 'FAIL', '%s: %d files, md5 = dates/' % (bk_rel, len(P3.shelf_md5s(W, bk_rel))),
                'every shelve file copied', '' if ok else 'the copy differs from dates/')
        st.rec['outputs'] = dict(out_common, backup=bk_rel, md5s_before=cur)
        if not ok:
            return st.finish()
        # --apply rewrites dates/ in place: the record names the copy first; the tool runs in a session of its own with
        # SIGINT, SIGTERM and SIGHUP held here, so a stop lands after the rewrite and after md5s_after is on record
        st.rec['outputs']['applying'] = True
        st.write()
        with P3.Deferred():
            krc, out = P3.kit_run(env, KIT[0], args + ['--apply'], W, lg, session=True)
            st.rec['outputs'].update(applying=False, md5s_after=P3.shelf_md5s(W, 'refineSecondaryTiming/dates'))
            st.write()
        m = re.search(r'^PASS: (\d+) dates rebased onto (\d{8})', out, re.M)
    after, bad = {}, []
    for d in plan:
        try:
            after[d] = P3.shelf_consts(os.path.join(W, 'refineSecondaryTiming', 'dates', d, 'misreg'))
        except Exception as e:  # noqa: BLE001
            bad.append('%s: %s: %s' % (d, type(e).__name__, e))
    bad += g16_off(after, plan, ref)   # v0.13 r2 (P6R-01): a NaN is off
    if not r9 and not resume and (krc != 0 or not m or int(m.group(1)) != len(plan) or m.group(2) != ref):
        bad.insert(0, 'the kit\'s --apply: rc %d, %s' % (krc, m.group(0) if m else 'no "PASS: N dates rebased" line'))
    if r9:
        how = 'R9 written%s; every date R9\'s plan within 1e-6' % (' again (the run of %s applied it first)' % own0.get('start')
                                                                 if resume else '')
    else:
        how = (('checked again: applied by the run of %s' % own0.get('start')) if resume else 'the reference reads 0 and 0') + \
            '; every date the plan within 1e-6'
    st.gate('G16', 'datum rebase', 'FAIL' if bad else 'PASS', '%d dates onto %s: %s' % (len(after), ref, how) if not bad else
            '%d problems' % len(bad), 'R9\'s plan; REF 0 and 0' if r9 else 'rc 0; the plan; REF 0 and 0',
            '\n'.join(bad[:10] + (['log %s; the pre-datum copy %s' % (lg, bk_rel)] if bad else [])))
    st.rec['outputs'].update(after={d: list(v) for d, v in sorted(after.items())},
                             md5s_after=P3.shelf_md5s(W, 'refineSecondaryTiming/dates'))
    if bad:
        return st.finish()
    lg9 = os.path.join(logroot, 'G9_misreg_gate.log')
    krc, out = P3.kit_run(env, KIT[1], [ref], W, lg9)
    sp = dict(re.findall(r'^(azimuth|range)\s+min.*SPREAD\s+(-?[\d.]+)', out, re.M))
    own_az = max(v[0] for v in after.values()) - min(v[0] for v in after.values())
    own_rg = max(v[1] for v in after.values()) - min(v[1] for v in after.values())
    agree = sp and abs(float(sp.get('azimuth', 'nan')) - own_az) < 1e-3 and abs(float(sp.get('range', 'nan')) - own_rg) < 1e-3
    verdict = 'PASS' if krc == 0 and agree else 'FAIL'
    st.gate('G9', 'misregistration spread (kit)', verdict, 'azimuth %s, range %s px (this phase: %.3f, %.3f); kit rc %d' % (
        sp.get('azimuth'), sp.get('range'), own_az, own_rg, krc), 'below 5 px (linog_misreg_gate.py)',
        '' if verdict == 'PASS' else 'log %s\n%s' % (lg9, P3.tail(lg9, 6)))
    st.rec['outputs'].update(g9=dict(rc=krc, spread_az=own_az, spread_rg=own_rg, log=lg9))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_datum', main)
