#!/usr/bin/env python3
"""lp_modestep.py -- linog_auto v0.13 r2: G6a.11, the mode step (DB1), a reading of deliver (6a), not a gate (the ascending
record 15.2, with DB1-a to DB1-d as Ariel approved them, 16.1, and 16.2's size line).

It is RA1's Part B (block RA1, record 1.7: ra1.py lines 356 to 470 and its state()) ported, with 15.2's five changes from RA1:
  1. a frame of one mode in the velocity fit reads N/A, naming the counts (RA1 had no such frame; its floor read NOT JUDGED);
  2. the series' zero dates must be exactly its REF_DATE (RA1 took any all-zero date as a reference, ra1.py 358 to 366);
  3. timeseries_demErr.h5's bperp (one a date, finite, not constant) and dem_error's design (no step date, phase velocity off,
     polyOrder a whole number) are checked, the attributes read as MintPy 1.6.2 writes them, strings, as RA1's empty_attr reads
     them (without regard to case and with '0' among its words), never by a truth test (RA1's B8 read both and did not act);
  4. dem_error's date set is the candidate with the smaller |partial r(c, bperp)| given [1, t, .., t^order], at most
     MODESTEP_PARTIAL_R_MAX (RA1: the first candidate at 1e-3); v0.13 r3 (the ascending record 97): when deliver gives the
     set chain A's dem_error ran over (its log, G6a.6e), that set is taken whenever it is within the bound, and a note names
     any other set the data take instead;
  5. a form is bounded by its share (L95 <= MODESTEP_L95_MAX, RA1's) or by its size (B95 <= MODESTEP_B95_MAX_M_YR across the
     frame; 16.2's 0.0039 m/yr, the single-path floor).
The arithmetic is the desk's (db1_desk.py v2, record Appendix M.2: years, ols, slope, corr, empty_attr, dem_design, line, match,
planes, pixel_checks, zero_check, fitB, bound), which reproduced RA1's twelve frames (15.3 A: the raw form to 1.1e-15, the
dem_error-aware form to 1.9e-5 from the table's rounded bperp) and read the desk's 25 cases and the mock frame's 7 as expected.

What it reads (deliver's own products in radar geometry, and the frame's records; nothing is written):
  mintpy/timeseries_demErr.h5 (chain A: date, bperp, timeseries; REF_DATE, mintpy.topographicResidual.*), mintpy/
  timeseries_demErr_ramp.h5 (chain B), mintpy/velocity_demErr.h5 and velocity_demErr_ramp.h5, mintpy/maskTempCoh.h5 (wmask's,
  G6a.8 holds it), mintpy/exclude_date.txt (the velocity fit's dates out, MintPy's and dfit's R4; linog_phase6.sh holds it aside
  for dem_error and remove_ramp, its lines 13 to 18; v0.13 r3's linog_phase6_r3.sh does not: chain A's dem_error leaves them
  out too), recon/modes.json (verify's: each date's mode).
In this order: the series' dates (its date dataset), recon/modes.json and exclude_date.txt, before any array is loaded: a date
without a mode row, NOT JUDGED; one mode in the fit, N/A; a mixed frame under MODESTEP_MIN_PER_MODE dates of a mode in the fit,
NOT JUDGED (with 2, both forms of Fit B computed and recorded: read, not judged; with 1, the step cannot be read). Then the
arrays: the files match; the series' zero dates; the population (maskTempCoh, finite in all four files, nonzero in the series on
every date but the temporal reference; NOT JUDGED under MODESTEP_MIN_PIXELS); the planes and their planarity (NOT JUDGED above
MODESTEP_PLANARITY_VOID); ROUTE 1; Fit A (NOT JUDGED beyond MODESTEP_ROUTE1_VOID); Fit B raw and as dem_error left it; bperp and
dem_error's design; the state: FLAG when |t| reaches the line on either form; BOUNDED when each form is bounded, by share or by
size; else UNBOUNDED. The line is RA1's, t(1 - MODESTEP_ALPHA / (2 x MODESTEP_TESTS), n - 3), with t(0.975, n - 3) for the bounds,
both from scipy.stats in the pinned env (MintPy 1.6.2 depends on scipy; felix's env holds 1.17.1, 16.5); scipy absent: NOT JUDGED.

The gate line G6a.11 (gate()): INFO for BOUNDED and UNBOUNDED, and "not read" before the frame's first delivery; N/A for one
mode; WARN for FLAG, for NOT JUDGED (with why) and when the reading raises (named, as G6a.9 names its failures); never FAIL or
DECISION, so the delivery stands (lp_common.Status.finish). The reading (read()) is what deliver's record (outputs.mode_step) and
RUN_MANIFEST.json's mode_step hold: the state, how it is bounded, why, the notes; both forms' k, se, t, beta, L, L95, B95, K95;
dem_error's attributes as read, its order and where it came from, its date set, each candidate's partial r, and g; c_x and the
range ramp, the population, the zero pixels, the reference date, the planarity and Fit A; the line, t(0.975), the degrees of
freedom and the settings; recon/modes.json's md5; one row per date (date, mode, t_yr, bperp, c, b, planarity, in the velocity
fit) as JSON floats at full precision, from which bound() gives every number again (M49).

numpy, h5py and scipy are imported inside the functions: deliver's --state runs under the driver's python3, standard library
only, and imports this module. Its md5 goes into deliver's record (st.rec['tools']), not into deliver's fingerprint (15.2).
"""
import datetime
import json
import math
import os
import re

VERSION_MODESTEP = 'linog_auto v0.13 r3 (2026-10-30)'   # r3: dem_error's date set from deliver's G6a.6e
GATE_ID, GATE_NAME = 'G6a.11', 'the mode step (DB1)'
THRESHOLD = 'a reading, not a gate (DB1; record 15)'
TR = 'mintpy.topographicResidual.'   # MintPy 1.6.2 dem_error.py's key_prefix (its four config_keys)
TF = 'mintpy.timeFunc.'              # timeseries2velocity.py's
FILES = (('ts', 'mintpy/timeseries_demErr.h5'), ('ts_ramp', 'mintpy/timeseries_demErr_ramp.h5'),
         ('vel', 'mintpy/velocity_demErr.h5'), ('vel_ramp', 'mintpy/velocity_demErr_ramp.h5'), ('mask', 'mintpy/maskTempCoh.h5'))
# linog_phase6.cfg's keys (lp_p6.KEYS) and the names the arithmetic takes them under (the desk's SET)
KEYS = (('MODESTEP_MIN_PER_MODE', 'min_per_mode', int), ('MODESTEP_MIN_PIXELS', 'min_pixels', int),
        ('MODESTEP_PLANARITY_VOID', 'planarity_void', float), ('MODESTEP_ROUTE1_VOID', 'route1_void', float),
        ('MODESTEP_PARTIAL_R_MAX', 'partial_r_max', float), ('MODESTEP_L95_MAX', 'l95_max', float),
        ('MODESTEP_B95_MAX_M_YR', 'b95_max_m_yr', float), ('MODESTEP_TESTS', 'tests', int), ('MODESTEP_ALPHA', 'alpha', float))
NOTE_UNBOUNDED = 'for the GNSS plan (DB1u)'
NOTE_FLAG = ('for Ariel\'s review and the GNSS plan, the frames named to Doc JD (DB2) [CONFIRM WITH PL]: mode is season on these '
             'stacks, so the reading cannot tell processing from atmosphere')
NOTE_K95 = ('BOUNDED speaks for the velocity only: chain A\'s per-date series (geo_timeseries_demErr.h5) can carry a step of up to '
            'K95 on each date of the mode its REF_DATE is not; chain B (timeseries_demErr_ramp.h5) takes each date\'s plane out, '
            'and the step with it (record 15.2)')


def settings(q):
    """The reading's settings from linog_phase6.cfg's MODESTEP_* keys (q: lp_p6.load_p6()), under the arithmetic's names."""
    return dict((name, conv(q[key])) for key, name, conv in KEYS)


# ------------------------------------------------------------------------------------- the arithmetic (db1_desk.py v2's)
def years(dates):
    """MintPy's decimal years (ptime.yyyymmdd2years): year + (day of year - 1) / 365.25."""
    import numpy as np
    out = []
    for d in dates:
        x = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
        out.append(x.year + (x.timetuple().tm_yday - 1) / 365.25)
    return np.array(out, dtype=np.float64)


def ols(X, y):
    import numpy as np
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n, q = X.shape
    XtX = X.T @ X
    b = np.linalg.solve(XtX, X.T @ y)
    r = y - X @ b
    dof = n - q
    s2 = float(r @ r) / dof if dof > 0 else float('nan')
    return b, np.sqrt(np.diag(s2 * np.linalg.inv(XtX)))


def slope(t, y):
    import numpy as np
    return float(ols(np.column_stack([np.ones(len(t)), t - t.mean()]), y)[0][1])


def corr(a, b):
    import numpy as np
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float('nan')
    return float(np.corrcoef(a, b)[0, 1])


def astr(v):
    """ra1.py 116-117."""
    return v.decode() if isinstance(v, bytes) else str(v)


def empty_attr(v):
    """ra1.py 157-159: True when a MintPy attribute holds no value ('', [], None, no, False), here without regard to case and
    with '0' among the words. MintPy 1.6.2 writes dem_error's settings as strings: stepDate '[]', phaseVelocity 'False',
    polyOrder '2' (ra1.json, all 12 frames)."""
    return v is None or re.sub(r"[\[\]'\" ]", '', astr(v)).lower() in ('', 'none', 'no', 'false', '0')


def dem_design(attrs):
    """dem_error's design from timeseries_demErr.h5's mintpy.topographicResidual.* attributes (prefix taken off, as RA1's
    dem_error_attrs): (order, where it came from, why it cannot be read, notes). polyOrder is read as a whole number ('2',
    '2.0'); present but not one, it cannot be read. A step date set or phase velocity on changes the design
    [1, t, .., t^order, bperp] the dem_error-aware form assumes (RA1 read both, ra1.py 460-464, and did not act on them).
    An absent attribute takes MintPy's default (order 2, no step date, phase velocity off), with a note."""
    attrs = attrs or {}
    why, notes = [], []
    order, order_from = 2, 'default (no polyOrder attribute)'
    if 'polyOrder' not in attrs or attrs['polyOrder'] is None:
        notes.append('no polyOrder attribute: order 2 taken')
    else:
        po_s = astr(attrs['polyOrder']).strip()
        try:
            po_f = float(po_s)
            ok = po_f == int(po_f) and 0 <= po_f <= 10
        except ValueError:
            ok = False
        if ok:
            order, order_from = int(po_f), 'attributes'
        else:
            why.append('polyOrder %r cannot be read as a whole number: dem_error\'s design is not known' % po_s)
    for key, label in (('stepDate', 'no stepDate attribute: no step date taken'),
                       ('phaseVelocity', 'no phaseVelocity attribute: phase velocity off taken')):
        if key not in attrs:
            notes.append(label)
    if not empty_attr(attrs.get('stepDate')):
        why.append('dem_error ran with step dates %s: its design is not [1, t, .., t^order, bperp]' % astr(attrs['stepDate']))
    if not empty_attr(attrs.get('phaseVelocity')):
        why.append('dem_error ran with phaseVelocity %s: its design is not [1, t, .., t^order, bperp]' % astr(attrs['phaseVelocity']))
    return order, order_from, why, notes


def line(dof, s):
    """(t975, the line): t(0.975) for L95, and RA1's family-wise line, two-sided alpha / tests per test (mk_expect.py line 79).
    scipy.stats in the pinned env; an ImportError goes to the caller (read(): NOT JUDGED, 15.2)."""
    from scipy import stats
    return float(stats.t.ppf(0.975, dof)), float(stats.t.ppf(1 - s['alpha'] / (2 * s['tests']), dof))


def match(d1, d2, shapes):
    """ra1.py 351-355: the two series hold the same dates, and the series, the velocities and the mask one grid."""
    s1, s2, v1, v2, mk = shapes
    why = []
    if d1 != d2:
        why.append('the files do not match: the two series\' dates differ (%d and %d dates)' % (len(d1), len(d2)))
    if s1 != s2 or tuple(s1[1:]) != tuple(v1) or tuple(v1) != tuple(v2) or tuple(mk) != tuple(v1):
        why.append('the files do not match (shapes %s %s %s %s %s)' % (s1, s2, v1, v2, mk))
    return why


def planes(ts1, ts2, vv1, vv2, mask):
    """RA1's population and planes (ra1.py 356-390): the population is the mask, finite in all four arrays, and nonzero in
    ts1 on every date but the temporal reference (a date with no nonzero pixel in the mask); per date the plane
    [1, y, x] of ts1 - ts2 over it (c the range term, b the azimuth term); ROUTE 1 the plane of vv1 - vv2."""
    import numpy as np
    n, L, Wd = ts1.shape
    good = np.isfinite(ts1).all(axis=0) & np.isfinite(ts2).all(axis=0) & np.isfinite(vv1) & np.isfinite(vv2)
    zero_dates = [i for i in range(n) if not np.any(ts1[i][mask & good])]
    nz = np.ones((L, Wd), dtype=bool)
    for i in range(n):
        if i not in zero_dates:
            nz &= ts1[i] != 0
    pop = mask & good & nz
    nP = int(pop.sum())
    out = dict(mask_px=int(mask.sum()), pop_px=nP, zero_px_in_mask=int((mask & good & ~nz).sum()), zero_dates=zero_dates,
               width=int(Wd), length=int(L))
    if nP < 3:
        return out
    yy, xx = np.nonzero(pop)
    G = np.column_stack([np.ones(nP), yy - float(yy.mean()), xx - float(xx.mean())])
    Dd = (ts1[:, pop].astype(np.float64) - ts2[:, pop].astype(np.float64)).T
    coef = np.linalg.lstsq(G, Dd, rcond=None)[0]
    fit_ = G @ coef
    rms = np.sqrt(np.mean((Dd - fit_) ** 2, axis=0))
    pp = fit_.max(axis=0) - fit_.min(axis=0)
    dv = vv1[pop] - vv2[pop]
    cv = np.linalg.lstsq(G, dv, rcond=None)[0]
    nzpp = pp[pp > 1e-12]
    out.update(c=coef[2].astype(np.float64), b=coef[1].astype(np.float64), rms=rms, pp=pp,
               planarity=float(rms.max() / np.median(nzpp)) if len(nzpp) else float('inf'),
               cV=float(cv[2]), bV=float(cv[1]),
               route1=dict(c=float(cv[2]), b=float(cv[1]), rms=float(np.sqrt(np.mean((dv - G @ cv) ** 2))),
                           pp=float((G @ cv).max() - (G @ cv).min())))
    return out


def pixel_checks(P, s):
    """The reasons the pixel part voids a frame (ra1.py 367-407)."""
    why = []
    if P['pop_px'] < s['min_pixels']:
        why.append('%d pixels in the population (< %d)' % (P['pop_px'], s['min_pixels']))
    elif P['planarity'] > s['planarity_void']:
        why.append('a per-date difference is not a plane (max rms / median pp %.2e)' % P['planarity'])
    return why


def zero_check(dates, zero_idx, ref_date):
    """The series' zero dates must be exactly its REF_DATE (RA1: one on each of the 12 frames, its REF_DATE)."""
    zd = [dates[i] for i in zero_idx]
    return [] if zd == [ref_date] else ['the series\' zero dates %s are not its REF_DATE %s' % (zd or 'none', ref_date)]


def fitB(cf, tf, mf, cV, t975, width=None):
    """c on [1, t, m] over the fit dates (ra1.py 309-316): k, se, t, beta (m on t), L, L95; and, when the grid's width is
    given, B95, the most a step could carry across the frame's velocity at 95 % (m/yr), (|k| + t975 se) |beta| (W - 1), and
    K95, the most it could put on one date of the series across the frame at 95 % (m), (|k| + t975 se) (W - 1): on each
    date of the mode its reference date is not (the series is relative to REF_DATE)."""
    import numpy as np
    b, se = ols(np.column_stack([np.ones(len(tf)), tf - tf.mean(), mf]), cf)
    k, sk = float(b[2]), float(se[2])
    beta = slope(tf, mf)
    return dict(k=k, se=sk, z=k / sk if sk > 0 else float('nan'), beta=beta,
                L=abs(k) * abs(beta) / abs(cV) if cV else float('inf'),
                L95=(abs(k) + t975 * sk) * abs(beta) / abs(cV) if cV else float('inf'), share=k * beta / cV if cV else float('nan'),
                B95=(abs(k) + t975 * sk) * abs(beta) * (width - 1) if width else None,
                K95=(abs(k) + t975 * sk) * (width - 1) if width else None)


def bound(dates, mode, c, bperp, excl, cV, dem_attrs, s, t975=None, zline=None, b=None, bV=None, width=None, dem_excl=None):
    """RA1's Part B on the per-date terms (ra1.py 391-470 and its state()), with section 15.2's changes (db1_desk.py v2's
    bound(), unchanged). dates, mode ('FBS' or 'FBD' per date), c (the range term per date), bperp (per date, or None), excl
    (the dates exclude_date.txt names), cV (ROUTE 1's range term), dem_attrs (timeseries_demErr.h5's
    mintpy.topographicResidual.* attributes as MintPy writes them, strings: polyOrder, stepDate, phaseVelocity; dem_design()),
    s (settings()), width (the radar grid's columns, for the ramp |cV| (W - 1), B95 and K95). t975 and zline given: those
    quantiles (RA1's own, M50); else the line's, at n_fit - 3 degrees of freedom. dem_excl (v0.13 r3): the dates chain A's
    dem_error left out, as deliver's G6a.6e read them from its log; None (r2's script, or not known): r2's choice, unchanged.
    Returns the reading with its state: N/A, NOT JUDGED, FLAG, UNBOUNDED, BOUNDED (by share or by size)."""
    import numpy as np
    r = dict(why=[], notes=[])
    order, order_from, dwhy, dnotes = dem_design(dem_attrs)
    nomode = [d for d, x in zip(dates, mode) if x not in ('FBS', 'FBD')]
    if nomode:
        r['why'].append('no mode for %s' % ', '.join(nomode))
        r['state'] = 'NOT JUDGED'
        return r
    t = years(dates)
    c = np.asarray(c, dtype=np.float64)
    m = np.array([1.0 if x == 'FBD' else 0.0 for x in mode])
    fit = np.array([d not in (excl or []) for d in dates])
    r.update(n=len(dates), n_fit=int(fit.sum()), n_fit_fbs=int((fit & (m == 0)).sum()), n_fit_fbd=int((fit & (m == 1)).sum()))
    dof = r['n_fit'] - 3
    if t975 is None:
        t975, zline = line(dof, s) if dof > 0 else (float('nan'), float('nan'))
    r.update(dof=dof, t975=t975, line=zline, ramp_m_yr=abs(cV) * (width - 1) if width else None)
    lo = min(r['n_fit_fbs'], r['n_fit_fbd'])
    if lo == 0:
        r['state'] = 'N/A'
        r['notes'].append('one mode in the velocity fit: FBS %d, FBD %d' % (r['n_fit_fbs'], r['n_fit_fbd']))
        return r
    if lo < s['min_per_mode']:   # RA1's floor (ra1.py 403-405): a mixed frame, too few dates of a mode to judge
        r['why'].append('a mixed frame with fewer than %d dates of a mode in the velocity fit (FBS %d, FBD %d): %s' % (
            s['min_per_mode'], r['n_fit_fbs'], r['n_fit_fbd'], 'read, not judged' if lo >= 2 else 'the step cannot be read'))
        if lo < 2:
            r['state'] = 'NOT JUDGED'
            return r
    r['why'] += dwhy
    tf, cf, mf = t[fit], c[fit], m[fit]
    vA, vAall = slope(tf, cf), slope(t, c)
    r['fitA'] = dict(v=vA, rel=abs(vA - cV) / abs(cV) if cV else float('inf'), v_all=vAall,
                     rel_all=abs(vAall - cV) / abs(cV) if cV else float('inf'))
    if b is not None and bV:
        r['fitA']['rel_b'] = abs(slope(tf, np.asarray(b, float)[fit]) - bV) / abs(bV)
    if r['fitA']['rel'] > s['route1_void']:
        r['why'].append('ROUTE 1 is not the fit over the dates exclude_date.txt leaves (%.2e; over all dates %.2e)'
                        % (r['fitA']['rel'], r['fitA']['rel_all']))
    r['fitB'] = fitB(cf, tf, mf, cV, t975, width)
    cfb, cfd = cf[mf == 0], cf[mf == 1]
    r['delta'] = dict(delta=float(np.median(cfd) - np.median(cfb)))
    bp = None if bperp is None else np.asarray(bperp, dtype=np.float64)
    if bp is not None and bp.shape != (len(dates),):
        r['why'].append('bperp is not one value a date (shape %s, %d dates)' % (bp.shape, len(dates)))
        bp = None
    elif bp is None:
        r['why'].append('no bperp in timeseries_demErr.h5: the dem_error-aware form cannot be read')
    elif not np.all(np.isfinite(bp)) or float(np.ptp(bp)) == 0.0:
        r['why'].append('bperp is constant or not finite (%s m): the dem_error-aware form cannot be read'
                        % ('%g' % bp[0] if np.isfinite(bp[0]) else 'nan'))
        bp = None
    r['corr'] = dict(m_t=corr(mf, tf), m_bperp=corr(mf, bp[fit]) if bp is not None else None,
                     bperp_t=corr(bp[fit], tf) if bp is not None else None, c_t=corr(cf, tf))
    r['notes'] += dnotes
    dem = None
    if bp is not None:
        try:
            n = len(dates)
            sets = [('all dates', np.ones(n, dtype=bool))] + ([('the dates less exclude_date.txt', fit.copy())] if not fit.all() else [])
            # v0.13 r3: the set dem_error ran over, as deliver read it from its log (G6a.6e); a third candidate only when it is
            # neither of the two (G6a.6e holds it to exclude_date.txt's, so not in a delivery that passed)
            want = None
            if dem_excl is not None:
                du = np.array([d not in dem_excl for d in dates])
                want = next((lab0 for lab0, u0 in sets if np.array_equal(u0, du)), None)
                if want is None:
                    want = 'the dates less dem_error\'s (G6a.6e)'
                    sets.append((want, du))
            pr = []
            for lab_, use in sets:
                tc = t - t[use].mean()
                Xp = np.column_stack([tc ** j for j in range(order + 1)])[use]
                rc = c[use] - Xp @ np.linalg.lstsq(Xp, c[use], rcond=None)[0]
                rb = bp[use] - Xp @ np.linalg.lstsq(Xp, bp[use], rcond=None)[0]
                pr.append((lab_, use, corr(rc, rb)))
            hit = sorted([x for x in pr if math.isfinite(x[2]) and abs(x[2]) <= s['partial_r_max']], key=lambda x: abs(x[2]))
            if want is not None and any(x[0] == want for x in hit):   # v0.13 r3: the set dem_error ran over, when the data agree
                hit = [x for x in hit if x[0] == want] + [x for x in hit if x[0] != want]
            lab_, use, prv = hit[0] if hit else (next(x for x in pr if x[0] == want) if want is not None else pr[0])
            tc = t - t[use].mean()
            X = np.column_stack([tc ** j for j in range(order + 1)] + [bp])
            gco = float(ols(X[use], m[use])[0][-1])
            mt = m - gco * bp
            dem = dict(order=order, order_from=order_from, dates=lab_, partial_r=dict((x[0], x[2]) for x in pr),
                       partial_r_c_bperp=prv, g=gco)
            dem.update({k_ + '_t': v_ for k_, v_ in fitB(cf, tf, mt[fit], cV, t975, width).items()})
        except np.linalg.LinAlgError as e:
            r['why'].append('the dem_error-aware form cannot be read: %s' % e)
            dem, hit, lab_ = None, True, 'all dates'
            want = None
        if dem is not None and not hit:
            r['why'].append('c carries a bperp term over either date set (partial r %s): dem_error did not run as the record knows it'
                            % ', '.join('%s %+.4f' % (x[0], x[2]) for x in pr))
        if dem is not None and lab_ != (want or 'all dates'):
            r['notes'].append('dem_error ran over %s, not as phase 6 runs it%s' % (lab_, ' (its log: %s)' % want if want else ''))
        if dem is not None:
            dem['dates_expected'] = want or 'all dates'
            dem['dates_expected_from'] = 'chain A\'s dem_error log (deliver G6a.6e, v0.13 r3)' if want else 'r2\'s script (every date)'
    r['dem_error_aware'] = dem
    if r['why']:
        r['state'] = 'NOT JUDGED'
        return r
    forms = [(r['fitB']['z'], r['fitB']['L95'], r['fitB']['B95']), (dem['z_t'], dem['L95_t'], dem['B95_t'])]
    if not all(math.isfinite(z) and abs(z) < zline for z, _, _ in forms):
        r['state'] = 'FLAG'
        return r
    by = []
    for _, l9, b9 in forms:
        if math.isfinite(l9) and l9 <= s['l95_max']:
            by.append('share')
        elif b9 is not None and math.isfinite(b9) and b9 <= s['b95_max_m_yr']:
            by.append('size')
        else:
            by.append(None)
    if all(by):
        r['state'] = 'BOUNDED'
        r['bounded_by'] = 'share' if by == ['share', 'share'] else 'size'
        if 'size' in by:
            big = max(forms[0][2], forms[1][2]) >= (r['ramp_m_yr'] or 0)
            r['notes'].append('bounded by size: a step could carry at most %.2f and %.2f cm/yr across the frame (raw, dem_error-aware), '
                              'against a range ramp of %.2f cm/yr%s' % (100 * forms[0][2], 100 * forms[1][2], 100 * (r['ramp_m_yr'] or 0),
                                                                       ': as much as the ramp itself, so all of the ramp could be '
                                                                       'step' if big else ''))
    else:
        r['state'] = 'UNBOUNDED'
    return r


def forms(R):
    """Both forms of Fit B as deliver's record and RUN_MANIFEST.json carry them, from bound()'s reading: raw and dem_error-aware,
    each k, se, t, beta, L, L95, B95, K95 and the share; the dem_error-aware form with dem_error's order and where it came from,
    its date set, the partial r of each candidate and g. None for a form not computed."""
    f, d = R.get('fitB'), R.get('dem_error_aware')
    raw = None if not f else dict(k=f['k'], se=f['se'], t=f['z'], beta=f['beta'], L=f['L'], L95=f['L95'], B95=f['B95'], K95=f['K95'],
                                  share=f['share'])
    dem = None if not d else dict(k=d['k_t'], se=d['se_t'], t=d['z_t'], beta=d['beta_t'], L=d['L_t'], L95=d['L95_t'], B95=d['B95_t'],
                                  K95=d['K95_t'], share=d['share_t'], order=d['order'], order_from=d['order_from'], dates=d['dates'],
                                  partial_r=d['partial_r'], partial_r_c_bperp=d['partial_r_c_bperp'], g=d['g'],
                                  dates_expected=d.get('dates_expected'), dates_expected_from=d.get('dates_expected_from'))   # v0.13 r3
    return raw, dem


def clean(o):
    """JSON-able, every number a Python one at full precision; a non-finite float becomes None (RUN_MANIFEST.json stays JSON)."""
    if isinstance(o, dict):
        return dict((str(k), clean(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [clean(x) for x in o]
    if isinstance(o, bool) or o is None or isinstance(o, str):
        return o
    if isinstance(o, int):
        return int(o)
    if isinstance(o, float):
        return float(o) if math.isfinite(o) else None
    tn = type(o).__module__
    if tn == 'numpy':   # numpy scalars and arrays
        if hasattr(o, 'tolist'):
            return clean(o.tolist())
    return str(o)


# ------------------------------------------------------------------------------------- the reading of a frame's products
def read_modes(W):
    """({date: mode}, md5) from <frame>/recon/modes.json's dates rows (verify's), or ({}, None) when there is none."""
    p = os.path.join(W, 'recon', 'modes.json')
    if not os.path.isfile(p):
        return {}, None
    import hashlib
    with open(p, 'rb') as fh:
        raw = fh.read()
    j = json.loads(raw.decode())
    return dict((str(x.get('date')), x.get('mode')) for x in j.get('dates') or []), hashlib.md5(raw).hexdigest()


def read_excl(p):
    """The dates exclude_date.txt names (as ra1.py reads it: every 8-digit word), or None when there is no file."""
    if not os.path.isfile(p):
        return None
    return sorted(set(re.findall(r'\b(\d{8})\b', open(p, errors='replace').read())))


def read(W, q=None, s=None, dry=False, dem_excl=None):
    """G6a.11's reading of the frame folder W's products (deliver's, in radar geometry) and records. q: lp_p6.load_p6() (its
    MODESTEP_* keys), or s, the settings themselves. dry: a dry run's reading of the frame's own products, so marked. Never
    raises: a failure is the reading's error, NOT JUDGED, and the gate's WARN names it. dem_excl (v0.13 r3): the dates chain A's
    dem_error left out (deliver's G6a.6e), or None (r2's choice of dem_error's date set, unchanged)."""
    out = dict(reader='lp_modestep.py (G6a.11, the ascending record 15.2)', version=VERSION_MODESTEP, state=None, bounded_by=None,
               why=[], notes=[], arrays_loaded=False, dry_run=bool(dry), dem_error_excluded=dem_excl)
    try:
        out['settings'] = s if s is not None else settings(q)
        _read(W, out['settings'], out, dem_excl)
    except ImportError as e:   # numpy, h5py or scipy (15.2: scipy absent, NOT JUDGED and the delivery stands)
        out.update(state='NOT JUDGED', error='%s: %s' % (type(e).__name__, str(e)[:200]), bounded_by=None)
        out['why'].append('a module will not import (%s: %s): %s' % (type(e).__name__, str(e)[:160], 'scipy\'s quantiles of the line '
                          'cannot be computed' if 'scipy' in str(e) else 'the reading cannot be made'))
    except Exception as e:  # noqa: BLE001  a reading, not a gate: a failure is named, the delivery stands (as G6a.9's)
        out.update(state='NOT JUDGED', error='%s: %s' % (type(e).__name__, str(e)[:200]), bounded_by=None)
        out['why'].append('the reading raised %s: %s' % (type(e).__name__, str(e)[:200]))
    if out.get('state') == 'FLAG':
        out['notes'].append(NOTE_FLAG)
    elif out.get('state') == 'UNBOUNDED':
        out['notes'].append(NOTE_UNBOUNDED)
    if out.get('state') in ('BOUNDED', 'UNBOUNDED', 'FLAG'):
        out['k95_note'] = NOTE_K95
    return clean(out)


def _read(W, s, out, dem_excl=None):
    paths = dict((k, os.path.join(W, rel)) for k, rel in FILES)
    out['files'] = dict((k, rel) for k, rel in FILES)
    if not os.path.isfile(paths['ts']):   # before the frame's first delivery (a dry run): nothing to read
        out['state'] = 'not read'
        out['why'].append('no products yet (%s absent)' % dict(FILES)['ts'])
        return
    import h5py
    # the series' dates, recon/modes.json and exclude_date.txt, before any array is loaded
    with h5py.File(paths['ts'], 'r') as h:
        dates = [astr(x) for x in h['date'][:]]
        attrs = dict((k, astr(v)) for k, v in h.attrs.items())
    modes, mmd5 = read_modes(W)
    excl = read_excl(os.path.join(W, 'mintpy', 'exclude_date.txt'))
    dem_attrs = dict((k[len(TR):], v) for k, v in attrs.items() if k.startswith(TR))
    mode = [modes.get(d) for d in dates]
    fit = [d not in (excl or []) for d in dates]
    out.update(dates=dates, n=len(dates), ref_date=attrs.get('REF_DATE'), modes_json='recon/modes.json', modes_json_md5=mmd5,
               exclude_date_txt=excl, dem_error_attrs=dem_attrs,
               n_fit=sum(fit), n_fit_fbs=sum(1 for m_, f_ in zip(mode, fit) if f_ and m_ == 'FBS'),
               n_fit_fbd=sum(1 for m_, f_ in zip(mode, fit) if f_ and m_ == 'FBD'))
    nomode = [d for d, m_ in zip(dates, mode) if m_ not in ('FBS', 'FBD')]
    if nomode:
        out['state'] = 'NOT JUDGED'
        out['why'].append('a date of the series without an FBS or FBD row in recon/modes.json: %s%s' % (
            ', '.join(nomode), '' if mmd5 else ' (no recon/modes.json)'))
        return
    lo = min(out['n_fit_fbs'], out['n_fit_fbd'])
    if lo == 0:
        out['state'] = 'N/A'
        out['notes'].append('one mode in the velocity fit: FBS %d, FBD %d (%d dates in the series, %d out of the fit); read from the '
                            'series\' dates, recon/modes.json and exclude_date.txt, no array loaded' % (
                                out['n_fit_fbs'], out['n_fit_fbd'], len(dates), len(dates) - sum(fit)))
        return
    if lo < 2:   # RA1's floor: with one date of a mode the step cannot be read (bound() says so, with no array)
        out['state'] = 'NOT JUDGED'
        out['why'].append('a mixed frame with fewer than %d dates of a mode in the velocity fit (FBS %d, FBD %d): the step cannot '
                          'be read' % (s['min_per_mode'], out['n_fit_fbs'], out['n_fit_fbd']))
        return
    import numpy as np
    missing = [rel for k, rel in FILES if not os.path.isfile(paths[k])]
    if missing:
        out['state'] = 'NOT JUDGED'
        out['why'].append('the files do not match: %s absent' % ', '.join(missing))
        return
    with h5py.File(paths['ts'], 'r') as h1, h5py.File(paths['ts_ramp'], 'r') as h2:
        d2 = [astr(x) for x in h2['date'][:]]
        bp = np.asarray(h1['bperp'][:], dtype=np.float64) if 'bperp' in h1 else None
        ts1 = np.asarray(h1['timeseries'][:], dtype=np.float32)
        ts2 = np.asarray(h2['timeseries'][:], dtype=np.float32)
    with h5py.File(paths['vel'], 'r') as v1, h5py.File(paths['vel_ramp'], 'r') as v2:
        vv1 = np.asarray(v1['velocity'][:], dtype=np.float64)
        vv2 = np.asarray(v2['velocity'][:], dtype=np.float64)
        va = dict((k, astr(v)) for k, v in v1.attrs.items())
    with h5py.File(paths['mask'], 'r') as fm:
        mask = np.asarray(fm['mask'][:]) != 0
    out['arrays_loaded'] = True
    out['bperp'] = None if bp is None else [float(x) for x in bp.ravel()]
    why = match(dates, d2, (ts1.shape, ts2.shape, vv1.shape, vv2.shape, mask.shape))
    if why:
        out['state'] = 'NOT JUDGED'
        out['why'] += why
        return
    P = planes(ts1, ts2, vv1, vv2, mask)
    del ts1, ts2
    out.update(grid=[P['length'], P['width']], width=P['width'], mask_px=P['mask_px'], population_px=P['pop_px'],
               zero_px_in_mask=P['zero_px_in_mask'], zero_dates=[dates[i] for i in P['zero_dates']])
    pre = zero_check(dates, P['zero_dates'], out['ref_date'])
    if 'c' not in P:
        out['state'] = 'NOT JUDGED'
        out['why'] += pre + pixel_checks(dict(P, planarity=float('inf')), s)
        return
    pre += pixel_checks(P, s)
    out.update(planarity=P['planarity'], route1=dict(P['route1'], range_ramp_m_yr=abs(P['cV']) * (P['width'] - 1),
                                                    azimuth_ramp_m_yr=abs(P['bV']) * (P['length'] - 1)))
    # RA1's B3, read, not judged: velocity_demErr.h5 names a linear model from the first to the last of the velocity's dates
    fd = [d for d, f_ in zip(dates, fit) if f_]
    vpoly = va.get(TF + 'polynomial')
    others = all(empty_attr(va.get(TF + x)) for x in ('periodic', 'stepDate', 'exp', 'log'))
    out['velocity_model'] = dict(
        polynomial=vpoly, others_empty=others, start_end=[va.get('START_DATE'), va.get('END_DATE')],
        fit_start_end=[fd[0], fd[-1]] if fd else None,
        as_phase6=((vpoly is None or re.sub(r'\D', '', vpoly) == '1') and others and
                   (va.get('START_DATE') is None or [va.get('START_DATE'), va.get('END_DATE')] == ([fd[0], fd[-1]] if fd else None))),
        note='read, not judged (RA1\'s B3)')
    R = bound(dates, mode, P['c'], bp, excl, P['cV'], dem_attrs, s, b=P['b'], bV=P['bV'], width=P['width'], dem_excl=dem_excl)
    t = years(dates)
    out['rows'] = [dict(date=d, mode=mode[i], t_yr=float(t[i]),
                        bperp=float(bp[i]) if bp is not None and bp.shape == (len(dates),) else None,
                        c=float(P['c'][i]), b=float(P['b'][i]),
                        planarity=float(P['rms'][i] / P['pp'][i]) if P['pp'][i] > 1e-12 else 0.0, pp_m=float(P['pp'][i]),
                        in_velocity_fit=bool(fit[i])) for i, d in enumerate(dates)]
    raw, dem = forms(R)
    out.update(dof=R.get('dof'), t975=R.get('t975'), line=R.get('line'), range_ramp_m_yr=R.get('ramp_m_yr'), raw=raw,
               dem_error_aware=dem, fitA=R.get('fitA'), delta=R.get('delta'), corr=R.get('corr'))
    if R.get('fitB'):
        cf = np.array([r_['c'] for r_ in out['rows'] if r_['in_velocity_fit']])
        cm = [r_['mode'] for r_ in out['rows'] if r_['in_velocity_fit']]
        out['delta'] = dict(R.get('delta') or {}, fbs_median=float(np.median(cf[[x == 'FBS' for x in cm]])),
                            fbd_median=float(np.median(cf[[x == 'FBD' for x in cm]])),
                            note='the per-date c by mode over the velocity fit\'s dates (the medians\' difference): read, not judged')
    out['why'] = pre + R.get('why', [])
    out['notes'] += R.get('notes', [])
    if pre and R.get('state') not in ('NOT JUDGED', 'N/A'):   # the pixel part voids what the forms would read
        out['state_of_the_forms'] = R.get('state')
        out['state'] = 'NOT JUDGED'
        out['notes'] = [x for x in out['notes'] if not x.startswith('bounded by size')]
    else:
        out['state'] = 'NOT JUDGED' if pre else R.get('state')
        out['bounded_by'] = R.get('bounded_by') if not pre else None


# ------------------------------------------------------------------------------------- the gate line
def _f(x, fmt='%.3f'):
    return fmt % x if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else 'none'


def gate(ms):
    """(verdict, value, note) of the gate line G6a.11 from a reading (read()'s): INFO for BOUNDED, UNBOUNDED and "not read",
    N/A for one mode, WARN for FLAG, NOT JUDGED and a reading that raised. Never FAIL or DECISION."""
    st = ms.get('state')
    pre = 'dry run, from the frame\'s own products: ' if ms.get('dry_run') else ''
    raw, dem = ms.get('raw') or {}, ms.get('dem_error_aware') or {}
    nums = ''
    if raw:
        nums = ('k %s and %s, |t| %s and %s against the line %s (%s dof); L95 %s and %s; B95 %s and %s cm/yr; the range ramp %s cm/yr '
                'across %s columns; %d dates (FBS %d, FBD %d in the fit of %d)' % (
                    _f(raw.get('k'), '%+.3e'), _f(dem.get('k'), '%+.3e'), _f(abs(raw['t']) if raw.get('t') is not None else None, '%.2f'),
                    _f(abs(dem['t']) if dem.get('t') is not None else None, '%.2f'), _f(ms.get('line'), '%.2f'), ms.get('dof'),
                    _f(raw.get('L95')), _f(dem.get('L95')), _f(100 * raw['B95'] if raw.get('B95') is not None else None, '%.3f'),
                    _f(100 * dem['B95'] if dem.get('B95') is not None else None, '%.3f'),
                    _f(100 * ms['range_ramp_m_yr'] if ms.get('range_ramp_m_yr') is not None else None, '%.2f'), ms.get('width'),
                    ms.get('n') or 0, ms.get('n_fit_fbs') or 0, ms.get('n_fit_fbd') or 0, ms.get('n_fit') or 0))
        if dem:
            nums += '; dem_error over %s (order %s, partial r %s)' % (dem.get('dates'), dem.get('order'), _f(dem.get('partial_r_c_bperp'), '%+.1e'))
    notes = '\n'.join(ms.get('notes') or [])
    if st == 'not read':
        return 'INFO', pre + 'not read: ' + '; '.join(ms.get('why') or ['no products yet']), ''
    if st == 'N/A':
        return 'N/A', pre + '; '.join(ms.get('notes') or ['one mode in the velocity fit']), ''
    if st == 'BOUNDED':
        return 'INFO', pre + 'BOUNDED by %s: %s' % (ms.get('bounded_by'), nums), notes
    if st == 'UNBOUNDED':
        return 'INFO', pre + 'UNBOUNDED (neither its share, L95 <= %s, nor its size, B95 <= %s cm/yr, bounds a form): %s' % (
            _f((ms.get('settings') or {}).get('l95_max'), '%.2f'), _f(100 * (ms.get('settings') or {}).get('b95_max_m_yr', float('nan')), '%.2f'),
            nums), notes
    if st == 'FLAG':
        return 'WARN', pre + 'FLAG (|t| reaches the line on a form): %s' % nums, notes
    if ms.get('error'):
        return 'WARN', pre + 'NOT JUDGED: %s' % '; '.join(ms.get('why') or [ms['error']]), notes
    return 'WARN', pre + 'NOT JUDGED: %s%s' % ('; '.join(ms.get('why') or ['no reason recorded']), ('; read: ' + nums) if nums else ''), notes
