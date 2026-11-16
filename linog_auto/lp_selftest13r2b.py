#!/usr/bin/env python3
"""lp_selftest13r2b.py -- linog_auto v0.13 r2's deliver cases: G6a.11, the mode step (DB1, lp_modestep.py), RUN_MANIFEST.json's
new fields and the mock MintPy that carries a known answer (the ascending record 15.2 to 15.4, 16.2 and 16.4; 11.7 and 18.5 for
the manifest's dropped dates, branch and looks); called by lp_selftest.py as the suite 13r2b.

The frames, on 13p4's mock ground (LINOG_MOCK_V13=1), in a root of their own (r2b), under --decide auto:
  the mixed full-height frame 3354 (13p4's and 13p6's archive v13mx: frame 3350's 12 dates, 20061010 to 20090302, FBD on
     20070528, 20080228, 20080530 and 20080715 as 15.4 asks, 1000 samples x 18432 lines, so the Phase 5 and 6 grid is 658 x 83:
     15.4's frame 3350 at a full height, as 13p4 and 13p6 run it), recon to deliver with the table not planted, then delivered
     again (its outputs moved into _archive/ by G6a.5's own instruction, then removed; --only deliver --force deliver) once for each of the
     table's seven cases (LINOG_MOCK_DB1, the kit's db1/mock3350_table.json: the desk's 15.3 D at 16.2's line 0.0039) and once
     with an HDF5 damaged (LINOG_MOCK_H5BREAK);
  an FBS-only full-height frame 3344 (the same 12 orbits, every granule FBS; with a P1.1 product and an off-beam granule more,
     which recon drops by G0.9 and G1), recon to dfit, a dry run of deliver, then on to rerun.
Each frame's folder is removed once all its cases PASS (the mixed frame's before the FBS-only frame runs; kept when one fails,
for the reader of the console), so that the suite holds one full-height frame on disk at a time.
The function-level cases run lp_modestep.read() on synthetic frames on the mock's 658 x 83 grid built from the table's M49 case
(each date's plane exact, float32 noise beside it), changed one thing at a time, in the mock env's Python (PROBE); M50 runs
lp_modestep.bound() on RA1's own per-date table (db1/ra1_dates.tsv, ra1_frames.tsv and ra1_frames.json, copied into the kit).
Cases (record 15.4):
  M49  the mixed frame through deliver, the table's M49 planted: G6a.11 INFO BOUNDED by share (|t| and L95 on both forms as the
       desk's); RUN_MANIFEST.json's mode_step one row per date at full precision, the rows' c equal to the table's within 1e-6
       (relative to the largest), lp_modestep.bound() on those rows giving the record's numbers exactly; deliver PASS; first the
       grid's width (83) and all 12 dates in the series, none dropped by admit, drop1 or G0.16;
  M49b (22.2's deliver row) RUN_MANIFEST.json's branch (FBS+FBD by recon and verify) and looks (12 x 28, the grid 83 x 658);
  M49c (11.7) dates.dropped: none on the mixed frame; on the FBS-only frame its two drops with date, mode, reason and the gate
       (G0.9, G1); on a synthetic RECON.json every kind (G0.4, G0.9, G1, G0.16, recon/exclude.txt, R7 with its loop) and the
       decision files' md5s as recon read them;
  M50  bound() on RA1's table: RA1's twelve states, the raw form within 1e-12 and the dem_error-aware form within 1e-4
       (relative), partial r within 1e-6 and Fit A's miss within 1e-9 (absolute); the zero dates RA1's REF_DATE on 12 of 12;
       RA1's attributes judged with no note;
  M51  the FBS-only frame through deliver: G6a.11 N/A naming the counts, no array loaded; deliver PASS; the same on a folder
       holding only the series' dates (no array, no other product): N/A;
  M51b (18.5) an FBD-only frame (the synthetic frame, every date FBD): N/A, one mode; the manifest's branch and looks on an
       FBD-only frame's records: FBD-only, 6 x 28 looks with the reference's R6-d note;
  M52  two FBD dates in the fit: NOT JUDGED, WARN, both forms recorded; one: NOT JUDGED, WARN (the step cannot be read);
  M53  the table's 43 cm step through the mock dem_error: FLAG, WARN, the note for Ariel's review, deliver PASS; the 1 cm step:
       BOUNDED by share;
  M54  dem_error over the dates less exclude_date.txt: that set found, judged, with the note; a bperp term after dem_error:
       NOT JUDGED, WARN;
  M55  the velocity over all dates while exclude_date.txt names two: NOT JUDGED (Fit A), WARN;
  M56  on the synthetic frame: no bperp dataset, bperp one date short, bperp constant (0 on every date), a date without a row
       in recon/modes.json, stepDate "['20090101']", phaseVelocity 'True', polyOrder 'auto': NOT JUDGED, WARN, each with its
       one reason (M49's '[]' and 'False' read as none and off); no polyOrder: order 2 with a note, judged (INFO);
  M56c bperp constant through deliver, the mock's zeros with the table not planted (the mixed frame's first delivery): NOT
       JUDGED, WARN, deliver PASS;
  M57  a-d: the population under 1,000 px; one date curved; 25 % of the pixels at zero on a date (judged); a second all-zero
       date: NOT JUDGED but the third;
  M58  an unreadable HDF5 (the series damaged after geocode, LINOG_MOCK_H5BREAK): G6a.11 WARN naming it; deliver PASS;
       RUN_MANIFEST.json written, with mode_step's error;
  M59  a: the dry run of the delivered mixed frame: G6a.11 read from the frame's own products, the preview's mode_step marked as
       a dry run's, the frame unchanged; b: the dry run of the FBS-only frame before its delivery: INFO "not read";
  M60  scipy absent (a stub that raises on import, first on the path): NOT JUDGED, WARN;
  M61  deliver's record and RUN_MANIFEST.json's label name v0.13 r2, LOGIC 6 (and v0.12's T167, T210 and T300 read them so);
  M62  the table's 0.5 cm/yr trend: BOUNDED by size, INFO, both B95s in the note; ten times its scatter: UNBOUNDED, INFO, "for
       the GNSS plan (DB1u)"; with the 43 cm step: FLAG, WARN;
  M63  the ramp series one date short; one date other: NOT JUDGED, WARN (the files do not match);
  M64  nothing goes STALE: the FBS-only frame's deliver fingerprint is v0.12 r2's formula on its inputs; with its record made
       v0.12's (v0.12's label, no mode_step, no lp_modestep.py among its tools) --state reads deliver CURRENT and a run to deliver
       skips it (PASS on record); then the frame's DEM changed (its dem_3344 key, the table's DEM for it, 14.4): --state reads
       recon and stage STALE, and once recon and stage have run again and stage has linked the new DEM, stack1, stack2 and topo
       read STALE;
  M65  the table's tenth of M49's scatter with a 4 cm step: FLAG, WARN, where without the line it would read BOUNDED by share;
       deliver PASS.
v0.12's cases changed (M61), each because deliver's label changes with G6a.11 (15.2's build note), LOGIC unchanged:
  T167 (lp_selftest6.py): the manifest's label RUN_MANIFEST.json (linog_auto v0.13 r2 ..., deliver's record v0.13 r2, LOGIC 6;
  T210 (lp_selftest10.py) and T300 (lp_selftest11.py): deliver's record v0.13 r2, LOGIC 6 (T300: and the manifest's label).
Departures, recorded: 15.4's frame 3350 runs Phases 2 to 6 at a full height as frame 3354 (13p4's split, its granules 1000 x 18432,
which multilook to 83 x 658); M64's DEM is the frame's own key (the mock frames at 13 N carry dem_<frame> keys, 14.4), not the
path table's default, which only path 84's real frames read; M64 checks deliver CURRENT, as 22.2's item 6 has it (accept's LOGIC 2
since v0.13 makes accept STALE on a v0.12 frame, 18.6).
"""
import json
import os
import re
import shutil
import subprocess
import sys

import lp_common as C
import lp_selftest13p1 as P13

FR_MX, FR_FBS, ROOT = '3354', '3344', 'r2b'
LF = 18432
TABLE = ('M49', 'M53_flag', 'M53_small', 'M62', 'M62_x10', 'M62_flag', 'M65')

# the mock env's Python (numpy, h5py, scipy): argv[1] the reading, argv[2] the pipeline folder, then its arguments; JSON last line
PROBE = r'''
import csv, json, os, shutil, sys
what, HERE = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
if what == 'stub':   # M60: a scipy that raises on import, first on the path
    sys.path.insert(0, args[0])
    what, args = args[1], args[2:]
sys.path.insert(0, HERE)
import numpy as np
import h5py
import lp_modestep as MS
import lp_p6
S6 = MS.settings(lp_p6.load_p6())
L, W = 658, 83


def synth(F, v, tab):
    """A frame folder F with deliver's five products, exclude_date.txt and recon/modes.json: the table's case c per date as
    each date's exact plane across the columns (the reference date, the first, zero), float32 noise in the ramp series and
    the ramp velocity, ROUTE 1 the fit of c over the velocity's dates; v changes one thing (the cases)."""
    dates = list(tab['dates'])
    n = len(dates)
    case = tab['cases'][v.get('case', 'M49')]
    bp = np.array(tab['bperp_m'], dtype=np.float64)
    t = MS.years(dates)
    excl = list(v.get('excl') or [])
    fit = np.array([d not in excl for d in dates])
    c = np.array(case['c_m_per_px'], dtype=np.float64)
    if v.get('dem_over_less'):   # dem_error's projection over the dates less exclude_date.txt (the desk's C8)
        cp = np.array(case['c_into_dem_error_m_per_px'], dtype=np.float64)
        tc = t - t[fit].mean()
        X = np.column_stack([np.ones(n), tc, tc ** 2, bp])
        c = cp - np.linalg.lstsq(X[fit], cp[fit], rcond=None)[0][-1] * (bp - bp[0])
    if v.get('bperp_term'):      # a bperp term added after dem_error (the desk's C7), relative to the reference date
        c = c + float(v['bperp_term']) * (bp - bp[0])
    cV = MS.slope(t, c) if v.get('velocity_all') else MS.slope(t[fit], c[fit])
    rng = np.random.default_rng(20261019)
    yy, xx = np.mgrid[0:L, 0:W]
    x0 = (W - 1) / 2.0
    mask = np.ones((L, W), bool)
    mask[:30, :] = False
    mask[400:470, 20:60] = False
    if v.get('small_mask'):
        mask[:] = False
        mask[200:210, :] = True
    ts2 = rng.normal(0, 0.002, (n, L, W)).astype(np.float32)
    ts1 = (ts2.astype(np.float64) + 0.001 * np.arange(n)[:, None, None] + c[:, None, None] * (xx - x0)[None]).astype(np.float32)
    ts1[0] = 0.0
    ts2[0] = 0.0
    zero_px = 0
    if v.get('curve_date') is not None:
        i = v['curve_date']
        ts1[i] = (ts1[i].astype(np.float64) + 0.02 * ((xx - x0) / W) ** 2).astype(np.float32)
    if v.get('zero_share'):
        i, f_ = v['zero_share']
        sel = rng.random((L, W)) < f_
        ts1[i][sel] = 0.0
        ts2[i][sel] = 0.0
        zero_px = int((sel & mask).sum())
    if v.get('zero_date') is not None:
        ts1[v['zero_date']] = 0.0
        ts2[v['zero_date']] = 0.0
    vv2 = rng.normal(0, 0.001, (L, W))
    vv1 = vv2 + cV * (xx - x0)
    M = os.path.join(F, 'mintpy')
    os.makedirs(M)
    os.makedirs(os.path.join(F, 'recon'))
    at = {'REF_DATE': dates[0], 'FILE_TYPE': 'timeseries', MS.TR + 'polyOrder': '2', MS.TR + 'stepDate': '[]',
          MS.TR + 'phaseVelocity': 'False', MS.TR + 'excludeDate': "['exclude_date.txt']"}
    for k, x in (v.get('attrs') or {}).items():
        if x is None:
            at.pop(MS.TR + k, None)
        else:
            at[MS.TR + k] = x
    d1 = [d.encode() for d in dates]
    with h5py.File(os.path.join(M, 'timeseries_demErr.h5'), 'w') as f:
        f.create_dataset('timeseries', data=ts1)
        f.create_dataset('date', data=np.array(d1))
        b_ = v.get('bperp', 'table')
        if b_ != 'none':
            f.create_dataset('bperp', data=(bp[:-1] if b_ == 'short' else np.zeros(n) if b_ == 'zeros' else bp).astype(np.float32))
        f.attrs.update(at)
    d2, t2 = list(d1), ts2
    if v.get('ramp_short'):
        d2, t2 = d2[:-1], ts2[:-1]
    if v.get('ramp_other'):
        d2[5] = b'20990101'
    with h5py.File(os.path.join(M, 'timeseries_demErr_ramp.h5'), 'w') as f:
        f.create_dataset('timeseries', data=t2)
        f.create_dataset('date', data=np.array(d2))
        f.attrs.update(at)
    for name, a in (('velocity_demErr.h5', vv1), ('velocity_demErr_ramp.h5', vv2)):
        with h5py.File(os.path.join(M, name), 'w') as f:
            f.create_dataset('velocity', data=a.astype(np.float32))
            f.attrs.update(dict(FILE_TYPE='velocity'))
    with h5py.File(os.path.join(M, 'maskTempCoh.h5'), 'w') as f:
        f.create_dataset('mask', data=mask)
    if excl:
        open(os.path.join(M, 'exclude_date.txt'), 'w').write(''.join(d + '\n' for d in excl))
    md = dict(zip(dates, tab['modes']))
    md.update(v.get('modes') or {})
    rows = [dict(date=d, mode=md[d]) for d in dates if d != v.get('no_mode_row')]
    json.dump(dict(dates=rows), open(os.path.join(F, 'recon', 'modes.json'), 'w'))
    return zero_px


def brief(r):
    g = MS.gate(r)
    return dict(state=r.get('state'), bounded_by=r.get('bounded_by'), why=r.get('why'), notes=r.get('notes'), error=r.get('error'),
                verdict=g[0], value=g[1], note=g[2], raw=r.get('raw'), dem=r.get('dem_error_aware'), fitA=r.get('fitA'),
                n_fit_fbs=r.get('n_fit_fbs'), n_fit_fbd=r.get('n_fit_fbd'), arrays=r.get('arrays_loaded'), pop=r.get('population_px'),
                zero_px=r.get('zero_px_in_mask'), mask_px=r.get('mask_px'), planarity=r.get('planarity'), dof=r.get('dof'),
                line=r.get('line'), rows=len(r.get('rows') or []))


out = {}
if what == 'synth':   # args: the table, a scratch folder; stdin: [[name, variant], ...]
    tab = json.load(open(args[0]))
    for name, v in json.load(sys.stdin):
        F = os.path.join(args[1], name)
        if os.path.exists(F):
            shutil.rmtree(F)
        zp = synth(F, v, tab)
        out[name] = dict(brief(MS.read(F, s=S6)), zero_px_planted=zp)
        shutil.rmtree(F)   # the folder's 5 files, about 6 MB: only the reading is kept
elif what == 'm50':   # args: the kit's db1 folder
    D = args[0]
    J = json.load(open(os.path.join(D, 'ra1_frames.json')))
    rows = list(csv.DictReader(open(os.path.join(D, 'ra1_dates.tsv'), newline=''), delimiter='\t'))
    frows = dict((r['frame'], r) for r in csv.DictReader(open(os.path.join(D, 'ra1_frames.tsv'), newline=''), delimiter='\t'))
    RAW = (('fitB.k', 'fitB', 'k'), ('fitB.se', 'fitB', 'se'), ('fitB.z', 'fitB', 'z'), ('fitB.beta', 'fitB', 'beta'), ('fitB.L', 'fitB', 'L'),
           ('fitB.L95', 'fitB', 'L95'))
    DEM = (('dem_error_aware.g', 'dem_error_aware', 'g'), ('dem_error_aware.beta_t', 'dem_error_aware', 'beta_t'),
           ('dem_error_aware.k_t', 'dem_error_aware', 'k_t'), ('dem_error_aware.se_t', 'dem_error_aware', 'se_t'),
           ('dem_error_aware.z_t', 'dem_error_aware', 'z_t'), ('dem_error_aware.L95_t', 'dem_error_aware', 'L95_t'))
    wr, wd, wpr, wfa, st_ok, zero_ok, clean_ok = 0.0, 0.0, 0.0, 0.0, 0, 0, 0
    states = {}
    for key in J['order']:
        fj = J['frames'][key]
        rr = [r for r in rows if r['frame'] == key]
        dates = [r['date'] for r in rr]
        R = MS.bound(dates, [r['mode'] for r in rr], [float(r['c_m_per_px']) for r in rr], [float(r['bperp_m']) for r in rr],
                     fj['exclude_date_txt'], float(frows[key]['route1.c']), fj['dem_error_attrs'], S6, t975=fj['t975'], zline=fj['zfw'],
                     width=int(fj['grid'][1]))
        for name, a, k in RAW:
            wr = max(wr, abs(R[a][k] - float(frows[key][name])) / max(abs(float(frows[key][name])), 1e-300))
        for name, a, k in DEM:
            wd = max(wd, abs(R[a][k] - float(frows[key][name])) / max(abs(float(frows[key][name])), 1e-300))
        wpr = max(wpr, abs(R['dem_error_aware']['partial_r_c_bperp'] - float(frows[key]['dem_error_aware.partial_r_c_bperp'])))
        wfa = max(wfa, abs(R['fitA']['rel'] - float(frows[key]['fitA.rel'])))
        st_ok += R['state'] == fj['state']
        zero_ok += not MS.zero_check(dates, [dates.index(x) for x in fj['ref_dates']], fj['REF_DATE'])
        clean_ok += not R['why'] and not R['notes']
        states[key] = R['state']
    out = dict(states=states, states_ok=st_ok, zero_ok=zero_ok, clean_ok=clean_ok, worst_raw=wr, worst_dem=wd, worst_pr=wpr, worst_fitA=wfa)
elif what == 'manifest':   # args: RUN_MANIFEST.json, the table, the case: the rows against the table, bound() on the rows
    man = json.load(open(args[0]))
    tab = json.load(open(args[1]))
    ms = man.get('mode_step') or {}
    rows = ms.get('rows') or []
    out = dict(rows=len(rows), state=ms.get('state'))
    if rows:
        ct = np.array(tab['cases'][args[2]]['c_m_per_px']) if args[2] in tab['cases'] else None
        cr = np.array([r['c'] for r in rows])
        out['c_rel'] = float(np.max(np.abs(cr - ct)) / np.max(np.abs(ct))) if ct is not None and len(ct) == len(cr) else None
        out['floats'] = all(isinstance(r[k], float) for r in rows for k in ('t_yr', 'bperp', 'c', 'b', 'planarity'))
        dates = [r['date'] for r in rows]
        excl = [r['date'] for r in rows if not r['in_velocity_fit']]
        # v0.13 r3: the dates chain A's dem_error left out, as the reading was given them (G6a.6e), given again
        kw = dict(b=[r['b'] for r in rows], bV=ms['route1']['b'], width=ms['width'], dem_excl=ms.get('dem_error_excluded'))
        R = MS.bound(dates, [r['mode'] for r in rows], [r['c'] for r in rows], [r['bperp'] for r in rows], excl, ms['route1']['c'],
                     ms['dem_error_attrs'], ms['settings'], **kw)
        raw, dem = MS.forms(R)
        same = dict(raw=MS.clean(raw) == ms.get('raw'), dem=MS.clean(dem) == ms.get('dem_error_aware'),
                    fitA=MS.clean(R.get('fitA')) == ms.get('fitA'), state=R.get('state') == ms.get('state'),
                    by=R.get('bounded_by') == ms.get('bounded_by'),
                    nums=all(MS.clean(R.get(k)) == ms.get(k2) for k, k2 in (('dof', 'dof'), ('t975', 't975'), ('line', 'line'),
                                                                              ('ramp_m_yr', 'range_ramp_m_yr'))))
        out.update(same=same, exact=all(same.values()))
        Rx = MS.bound(dates, [r['mode'] for r in rows], [r['c'] for r in rows], [r['bperp'] for r in rows], excl, ms['route1']['c'],
                      ms['dem_error_attrs'], ms['settings'], zline=float('inf'), t975=ms['t975'], **kw)
        out.update(without_line=Rx.get('state'), without_line_by=Rx.get('bounded_by'))
elif what == 'series_only':   # args: a frame folder, a scratch folder: only the series' dates and attributes, recon/modes.json
    W0, F = args
    if os.path.exists(F):
        shutil.rmtree(F)
    os.makedirs(os.path.join(F, 'mintpy'))
    os.makedirs(os.path.join(F, 'recon'))
    with h5py.File(os.path.join(W0, 'mintpy', 'timeseries_demErr.h5'), 'r') as f, h5py.File(os.path.join(F, 'mintpy', 'timeseries_demErr.h5'), 'w') as g:
        g.create_dataset('date', data=f['date'][:])
        g.attrs.update(dict(f.attrs))
    shutil.copy2(os.path.join(W0, 'recon', 'modes.json'), os.path.join(F, 'recon', 'modes.json'))
    if os.path.isfile(os.path.join(W0, 'mintpy', 'exclude_date.txt')):
        shutil.copy2(os.path.join(W0, 'mintpy', 'exclude_date.txt'), os.path.join(F, 'mintpy', 'exclude_date.txt'))
    out = dict(brief(MS.read(F, s=S6)), files=sorted(os.listdir(os.path.join(F, 'mintpy'))))
    shutil.rmtree(F)
elif what == 'series':   # args: a frame folder: the series' dates and grid
    W0 = args[0]
    with h5py.File(os.path.join(W0, 'mintpy', 'timeseries.h5'), 'r') as f:
        out = dict(dates=[d.decode() for d in f['date'][:]], shape=list(f['timeseries'].shape))
print(json.dumps(MS.clean(out)))
'''

STUB = 'raise ImportError("MOCK scipy: a stub that raises on import (the self-test\'s M60), not scipy")\n'


def phase13_r2b(T, case, S):
    import lp_deliver as D6
    import lp_p6 as P6
    print('-- v0.13 r2 deliver: G6a.11, the mode step (DB1), RUN_MANIFEST.json\'s mode_step, dates.dropped, branch and looks; the '
          'mixed frame 3354 and the FBS-only frame 3344 (LINOG_MOCK_V13), the table planted in the mock dem_error')
    py = S.MOCKPY[0]
    site = os.path.join(T, 'mockconda', 'envs', 'linog_isce2', 'lib', 'site-packages')
    kit = os.path.join(S.KITSRC, 'db1')
    table = os.path.join(kit, 'mock3350_table.json')
    tab = json.load(open(table))
    scratch = os.path.join(T, 'r2b_scratch')
    os.makedirs(scratch, exist_ok=True)

    def probe(what, *args, stdin=None, stub=None):
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': site}
        argv = [py, '-B', '-c', PROBE] + (['stub', S.HERE, stub, what] if stub else [what, S.HERE]) + [str(a) for a in args]
        p = subprocess.run(argv, input=(stdin or '').encode(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        txt = p.stdout.decode('utf-8', 'replace')
        try:
            return json.loads(txt.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': txt[-600:]}

    if not py:
        case('M49-M65 not run: the mock MintPy and lp_modestep need numpy, h5py and scipy, and neither Python tried has them', False)
        return

    # =============================================================================== M50: the port on RA1's own table
    j = probe('m50', kit)
    case('M50 (15.3 A, 15.4) lp_modestep.bound() on RA1\'s per-date table (db1/ra1_dates.tsv, ra1_frames.tsv): RA1\'s twelve states '
         '(BOUNDED on 12 of 12), the raw form within 1e-12 and the dem_error-aware form within 1e-4 (relative), partial r within 1e-6 '
         'and Fit A\'s miss within 1e-9 (absolute), RA1\'s quantiles; the zero dates RA1\'s REF_DATE on 12 of 12; RA1\'s dem_error '
         'attributes as MintPy wrote them (\'2\', \'[]\', \'False\') judged with no note on 12 of 12',
         j.get('states_ok') == 12 and set((j.get('states') or {}).values()) == {'BOUNDED'} and j.get('worst_raw', 1) <= 1e-12
         and j.get('worst_dem', 1) <= 1e-4 and j.get('worst_pr', 1) <= 1e-6 and j.get('worst_fitA', 1) <= 1e-9 and j.get('zero_ok') == 12
         and j.get('clean_ok') == 12,
         dict((k, j.get(k)) for k in ('states_ok', 'zero_ok', 'clean_ok', 'worst_raw', 'worst_dem', 'worst_pr', 'worst_fitA', '_error')))

    # =============================================================================== M52 to M63: the reading on synthetic frames
    D = tab['dates']
    FBD = [d for d, m in zip(D, tab['modes']) if m == 'FBD']
    FBS2 = [D[3], D[9]]   # two FBS dates, neither the reference
    V = [('base', {}),
         ('m52a', dict(modes=dict((d, 'FBS') for d in FBD[2:]))), ('m52b', dict(modes=dict((d, 'FBS') for d in FBD[1:]))),
         ('m54a', dict(excl=FBS2, dem_over_less=True)), ('m54b', dict(bperp_term=2e-8)),
         ('m55', dict(excl=FBS2, velocity_all=True)),
         ('m56a', dict(bperp='none')), ('m56b', dict(bperp='short')), ('m56c', dict(bperp='zeros')), ('m56d', dict(no_mode_row=D[6])),
         ('m56e', dict(attrs=dict(stepDate="['20090101']"))), ('m56f', dict(attrs=dict(phaseVelocity='True'))),
         ('m56g', dict(attrs=dict(polyOrder=None))), ('m56h', dict(attrs=dict(polyOrder='auto'))),
         ('m57a', dict(small_mask=True)), ('m57b', dict(curve_date=3)), ('m57c', dict(zero_share=(5, 0.25))), ('m57d', dict(zero_date=6)),
         ('m63a', dict(ramp_short=True)), ('m63b', dict(ramp_other=True)),
         ('m51b', dict(modes=dict((d, 'FBD') for d in D)))]
    R = probe('synth', table, scratch, stdin=json.dumps(V))
    b0 = R.get('base') or {}

    def one(name, want, why=None, verdict='WARN'):
        """(ok, detail): the variant's state is want, its verdict verdict, and for NOT JUDGED its one reason holds why."""
        r = R.get(name) or {}
        ok = r.get('state') == want and r.get('verdict') == verdict and (why is None or (len(r.get('why') or []) == 1 and why in r['why'][0]))
        return ok, '%s: %s %s %s' % (name, r.get('verdict'), r.get('state'), '; '.join(r.get('why') or [])[:220] or R.get('_error', ''))

    ok0 = b0.get('state') == 'BOUNDED' and b0.get('bounded_by') == 'share' and b0.get('verdict') == 'INFO' and not b0.get('why') \
        and not b0.get('notes') and abs(abs((b0.get('raw') or {}).get('t', 0)) - abs(tab['cases']['M49']['z'])) < 1e-4 * abs(tab['cases']['M49']['z'])
    a, da = one('m52a', 'NOT JUDGED', 'read, not judged')
    r52 = R.get('m52a') or {}
    b, db = one('m52b', 'NOT JUDGED', 'the step cannot be read')
    case('M52 (15.2, 15.4) too few dates of a mode in the fit: two FBD dates: NOT JUDGED, WARN, "read, not judged", both forms of Fit '
         'B recorded; one: NOT JUDGED, WARN, "the step cannot be read" (the synthetic frame\'s own reading, the table\'s M49: BOUNDED by '
         'share, INFO, as the desk\'s)', ok0 and a and r52.get('n_fit_fbd') == 2 and bool(r52.get('raw')) and bool(r52.get('dem'))
         and b and (R.get('m52b') or {}).get('n_fit_fbd') == 1,
         'base %s %s by %s; %s (FBD %s, forms %s %s); %s' % (b0.get('verdict'), b0.get('state'), b0.get('bounded_by'), da, r52.get('n_fit_fbd'),
                                                            bool(r52.get('raw')), bool(r52.get('dem')), db))
    r54 = R.get('m54a') or {}
    b, db = one('m54b', 'NOT JUDGED', 'c carries a bperp term')
    case('M54 (15.2, 15.4) dem_error\'s dates: over the dates less exclude_date.txt (two FBS dates named): that set found by the smaller '
         '|partial r| (under 1e-5), judged, with the note "not as phase 6 runs it"; a bperp term after dem_error: NOT JUDGED, WARN, '
         'c carries a bperp term over either date set',
         r54.get('state') in ('BOUNDED', 'UNBOUNDED', 'FLAG') and not r54.get('why') and (r54.get('dem') or {}).get('dates') == 'the dates less exclude_date.txt'
         and abs((r54.get('dem') or {}).get('partial_r_c_bperp', 1)) <= 1e-5 and any('not as phase 6 runs it' in x for x in r54.get('notes') or [])
         and b, 'm54a: %s %s, set %s, partial r %s, notes %s; %s' % (r54.get('verdict'), r54.get('state'), (r54.get('dem') or {}).get('dates'),
                                                                   (r54.get('dem') or {}).get('partial_r'), r54.get('notes'), db))
    a, da = one('m55', 'NOT JUDGED', 'ROUTE 1 is not the fit over the dates exclude_date.txt leaves')
    case('M55 (15.2, 15.4) the velocity over all dates while exclude_date.txt names two: NOT JUDGED (Fit A), WARN', a, da)
    res = [one('m56a', 'NOT JUDGED', 'no bperp in timeseries_demErr.h5'), one('m56b', 'NOT JUDGED', 'not one value a date'),
           one('m56c', 'NOT JUDGED', 'bperp is constant'), one('m56d', 'NOT JUDGED', 'without an FBS or FBD row in recon/modes.json'),
           one('m56e', 'NOT JUDGED', 'step dates'), one('m56f', 'NOT JUDGED', 'phaseVelocity True'),
           one('m56h', 'NOT JUDGED', 'cannot be read as a whole number')]
    r56g = R.get('m56g') or {}
    ok56g = r56g.get('state') == 'BOUNDED' and r56g.get('verdict') == 'INFO' and (r56g.get('dem') or {}).get('order') == 2 \
        and (r56g.get('dem') or {}).get('order_from', '').startswith('default') and 'no polyOrder attribute: order 2 taken' in (r56g.get('notes') or [])
    case('M56 (15.2, 15.4) missing or other inputs, on the synthetic frame: no bperp dataset, bperp one date short, bperp constant (0 on '
         'every date), a date without a row in recon/modes.json, stepDate "[\'20090101\']", phaseVelocity \'True\', polyOrder \'auto\': '
         'NOT JUDGED, WARN, each with its one reason; no polyOrder attribute: order 2 with the note, judged (BOUNDED, INFO); M49\'s \'[]\' '
         'and \'False\' read as none and off (the base reading judged, no note)',
         all(x[0] for x in res) and ok56g and ok0, ' | '.join(x[1] for x in res if not x[0]) or 'm56g %s %s order %s from %s, notes %s' % (
             r56g.get('verdict'), r56g.get('state'), (r56g.get('dem') or {}).get('order'), (r56g.get('dem') or {}).get('order_from'), r56g.get('notes')))
    a, da = one('m57a', 'NOT JUDGED', 'pixels in the population (< 1000)')
    b, db = one('m57b', 'NOT JUDGED', 'not a plane')
    r57c, r57d = R.get('m57c') or {}, R.get('m57d') or {}
    c57 = r57c.get('state') == 'BOUNDED' and r57c.get('verdict') == 'INFO' and r57c.get('zero_px') == r57c.get('zero_px_planted') \
        and r57c.get('pop') == r57c.get('mask_px') - r57c.get('zero_px') and 0.2 < (r57c.get('zero_px') or 0) / float(r57c.get('mask_px') or 1) < 0.3
    d57 = r57d.get('state') == 'NOT JUDGED' and r57d.get('verdict') == 'WARN' and 'are not its REF_DATE' in ((r57d.get('why') or [''])[0])
    case('M57 (15.2, 15.4) the population: 830 px (under 1,000): NOT JUDGED; one date curved by 2 cm across the frame: NOT JUDGED (not a '
         'plane); 25 % of the pixels at zero on one date: judged (BOUNDED), the zero pixels counted and left out of the population; a '
         'second all-zero date: NOT JUDGED, the zero-date rule first', a and b and c57 and d57,
         '%s; %s; m57c %s %s pop %s of %s, zero %s (planted %s); m57d %s %s' % (da, db, r57c.get('verdict'), r57c.get('state'), r57c.get('pop'),
                                                                             r57c.get('mask_px'), r57c.get('zero_px'), r57c.get('zero_px_planted'),
                                                                             r57d.get('state'), (r57d.get('why') or [''])[0][:120]))
    r63a, r63b = R.get('m63a') or {}, R.get('m63b') or {}
    # the one reason: the files do not match (a series one date short reads it twice, by its dates and by its shape)
    a, b = [r_.get('state') == 'NOT JUDGED' and r_.get('verdict') == 'WARN' and all('the files do not match' in x for x in r_.get('why') or ['-'])
            for r_ in (r63a, r63b)]
    case('M63 (15.2, 15.4) the files do not match: the ramp series one date short (its dates and its shape); the same length with one '
         'date other: NOT JUDGED, WARN, every reason "the files do not match"', a and b,
         'm63a %s %s %s; m63b %s %s %s' % (r63a.get('verdict'), r63a.get('state'), r63a.get('why'), r63b.get('verdict'), r63b.get('state'),
                                           r63b.get('why')))
    # M51b (18.5): an FBD-only frame reads N/A, one mode; and RUN_MANIFEST.json's branch and looks name R6-d's 6 range looks
    r51b = R.get('m51b') or {}
    fo = os.path.join(scratch, 'fbd_only')
    os.makedirs(os.path.join(fo, 'recon'), exist_ok=True)
    os.makedirs(os.path.join(fo, 'status'), exist_ok=True)
    rnote = 'FBD-only frame: range looks 6 (linog_mixed.cfg STACK_RLKS_FBD) in place of STACK_RLKS 12 (R6-d)'
    for rel, obj in (('recon/RECON.json', dict(branch='FBD-only', granules=[])), ('recon/modes.json', dict(branch='FBD-only', dates=[])),
                     ('recon/reference.json', dict(reference='20080113', geometry=dict(width=773, length=658, rlks=6, alks=28))),
                     ('status/P2b_reference.json', dict(phase='reference', verdict='PASS', outputs=dict(looks=rnote)))):
        with open(os.path.join(fo, rel), 'w') as fh:
            json.dump(obj, fh)
    bf, lf = D6.branch_entry(fo), D6.looks_entry(fo)
    case('M51b (18.5) an FBD-only frame: G6a.11 N/A, "one mode in the velocity fit: FBS 0, FBD 12", no array loaded (the synthetic '
         'frame, every date FBD); RUN_MANIFEST.json\'s branch FBD-only and looks 6 x 28 with the reference\'s R6-d note (deliver\'s '
         'branch_entry and looks_entry on an FBD-only frame\'s records)',
         r51b.get('state') == 'N/A' and r51b.get('verdict') == 'N/A' and 'one mode in the velocity fit: FBS 0, FBD 12' in r51b.get('value', '')
         and r51b.get('arrays') is False and bf.get('value') == 'FBD-only' and lf.get('range') == 6 and lf.get('azimuth') == 28
         and lf.get('grid_columns') == 773 and lf.get('note') == rnote,
         'm51b %s %s %s; branch %s; looks %s' % (r51b.get('verdict'), r51b.get('state'), r51b.get('value', '')[:120], bf, lf))
    # M60: scipy absent, a stub first on the path
    sd = os.path.join(scratch, 'stub_scipy')
    os.makedirs(os.path.join(sd, 'scipy'), exist_ok=True)
    with open(os.path.join(sd, 'scipy', '__init__.py'), 'w') as fh:
        fh.write(STUB)
    R60 = probe('synth', table, scratch, stdin=json.dumps([['m60', {}]]), stub=sd).get('m60') or {}
    case('M60 (15.2, 15.4) scipy absent (a scipy package whose __init__ raises ImportError, first on the path): NOT JUDGED, WARN, '
         'naming the import; the reading does not raise', R60.get('state') == 'NOT JUDGED' and R60.get('verdict') == 'WARN'
         and 'scipy' in str(R60.get('error')) and any('will not import' in x for x in R60.get('why') or []),
         '%s %s; %s' % (R60.get('verdict'), R60.get('state'), R60.get('why')))

    if not S.DATA_OK[0]:
        case('M49, M51, M53, M58, M59, M61, M62, M64, M65 not run: the mock ground needs numpy, and neither Python tried has it', False)
        return

    # =============================================================================== the frames
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    dem12 = re.search(r'^dem_3350 = (.+)$', base, re.M).group(1)
    with open(os.path.join(T, 'cfg', 'paths_r2b.cfg'), 'w') as fh:
        fh.write(base.rstrip('\n') + '\n# v0.13 r2: the full-height mock frames, on the same mock DEM\ndem_%s = %s\ndem_%s = %s\n' % (
            FR_MX, dem12, FR_FBS, dem12))
    ORB = S.ORBITS[:12]
    full = dict(lines=LF, rows13=True)
    am = P13.make_variant(T, S, 'v13mx', dict((i, full) for i in range(12)), frame=FR_MX, orbs=ORB, fbd=S.FBD_3350)
    af = P13.make_variant(T, S, 'r2bfbs', dict((i, full) for i in range(12)), frame=FR_FBS, orbs=ORB, fbd=(),
                          extra=[[S.ORBITS[12], dict(product='P1.1')], [S.ORBITS[13], dict(offnadir=41.5)]])
    if not am or not af:
        case('M49, M51, M53, M58, M59, M61, M62, M64, M65 not run: the full-height mock archives could not be made (numpy)', False)
        return

    def run(frame, args, extra=None, cfg='paths_r2b.cfg'):
        e = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MOCK_V13': '1', 'LINOG_ARCHIVE': am if frame == FR_MX else af}
        e.update(extra or {})
        return S.run(T, ['084', frame, '--decide', 'auto'] + args, cfg=cfg, env_extra=e, keep_default=True)

    def rec(frame, idx, ph):
        return S.rec(T, frame, idx, ph, ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gl(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return (x[-1]['verdict'], x[-1]['value'], x[-1].get('note') or '') if x else (None, '', '')

    def manifest(W):
        p = os.path.join(W, 'RUN_MANIFEST.json')
        return json.load(open(p)) if os.path.isfile(p) else {}

    def aside(W, frame, tag):
        """deliver's outputs (lp_p6.deliver_way, G6a.5's list) into <frame>/_archive/<tag>/, G6a.5's own instruction; then that
        folder removed (about 140 MB a delivery on the mixed frame; no case reads a delivery once the next is made)."""
        for rel in P6.deliver_way('084', frame):
            src = os.path.join(W, rel)
            if os.path.lexists(src):
                dst = os.path.join(W, '_archive', tag, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                os.rename(src, dst)
        shutil.rmtree(os.path.join(W, '_archive', tag), ignore_errors=True)

    def listing(W):
        out = []
        for dp, dn, fn in os.walk(W):
            dn.sort()
            for n in sorted(fn):
                q = os.path.join(dp, n)
                st = os.lstat(q)
                out.append((os.path.relpath(q, W), st.st_size, st.st_mtime_ns))
        return out

    def plant(name):
        return {'LINOG_MOCK_DB1': name, 'LINOG_MOCK_DB1_TABLE': table}

    W = S.fdir(T, FR_MX, ROOT)
    WF = S.fdir(T, FR_FBS, ROOT)
    passed = {}   # each frame's cases, PASS or not: its folder is removed after them only when every one PASSed

    def fcase(frame, name, cond, detail=''):
        passed.setdefault(frame, []).append(bool(cond))
        case(name, cond, detail)

    # ---- the mixed frame, recon to deliver, the table not planted (M56c through deliver)
    rc, out = run(FR_MX, ['--to', 'deliver'])
    rd = rec(FR_MX, '6a', 'deliver')
    v, val, note = gl(rd, 'G6a.11')
    ms0 = (rd.get('outputs') or {}).get('mode_step') or {}
    man0 = manifest(W)
    ser = probe('series', W)
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    r1 = rec(FR_MX, '5d1', 'drop1')
    fcase(FR_MX, 'M56c (15.4) the mixed frame 3354 recon to deliver with the table not planted: deliver PASS, rc 0; G6a.11 WARN NOT JUDGED, '
         '"bperp is constant" (the mock dem_error\'s bperp, 0 on every date as the mock\'s ifgramStack.h5 holds it); the record\'s '
         'mode_step and RUN_MANIFEST.json\'s the same reading',
         rc == 0 and rd.get('verdict') == 'PASS' and v == 'WARN' and 'bperp is constant' in val and ms0.get('state') == 'NOT JUDGED'
         and man0.get('mode_step') == ms0, 'rc %d deliver %s; G6a.11 %s %s' % (rc, rd.get('verdict'), v, val[:240]))
    ok_pre = ser.get('dates') == D and ser.get('shape', [0, 0, 0])[2] == 83 and ser.get('shape', [0, 0, 0])[1] == 658 \
        and (adm.get('cfg') or {}).get('mintpy.network.excludeDate') in ('no', '', None) \
        and str((r1.get('outputs') or {}).get('state')) in ('none flagged', 'no cull') and not (r1.get('outputs') or {}).get('taken') \
        and ((man0.get('dates') or {}).get('dropped') or {}).get('count') == 0 \
        and not os.path.isfile(os.path.join(W, 'mintpy', 'exclude_date.txt'))
    # ---- M49: the table's M49 planted
    aside(W, FR_MX, 'M49')
    rc, out = run(FR_MX, ['--only', 'deliver', '--force', 'deliver'], plant('M49'))
    rd = rec(FR_MX, '6a', 'deliver')
    v, val, note = gl(rd, 'G6a.11')
    man = manifest(W)
    ms = man.get('mode_step') or {}
    pm = probe('manifest', os.path.join(W, 'RUN_MANIFEST.json'), table, 'M49')
    w49 = tab['cases']['M49']
    fcase(FR_MX, 'M49 (15.4) the mixed frame 3354 through deliver, the table\'s M49 planted (a 4 cm/yr trend, no step): first the grid 658 x 83 '
         'and all 12 dates in the series (timeseries.h5), none dropped by recon, admit, drop1 or exclude_date.txt; G6a.11 INFO BOUNDED '
         'by share, |t| 1.52 and 1.50 against the line 4.27 and L95 0.087 and 0.010 as the desk\'s (within 1e-4); RUN_MANIFEST.json\'s '
         'mode_step one row per date as JSON floats, their c the table\'s within 1e-6 of the largest; lp_modestep.bound() on those rows '
         'gives the record\'s numbers exactly; deliver PASS',
         ok_pre and rc == 0 and rd.get('verdict') == 'PASS' and v == 'INFO' and val.startswith('BOUNDED by share') and ms.get('state') == 'BOUNDED'
         and ms.get('bounded_by') == 'share' and abs(abs(ms['raw']['t']) - abs(w49['z'])) <= 1e-4 * abs(w49['z'])
         and abs(abs(ms['dem_error_aware']['t']) - abs(w49['z_t'])) <= 1e-4 * abs(w49['z_t'])
         and abs(ms['raw']['L95'] - w49['L95']) <= 1e-4 * w49['L95'] and abs(ms['dem_error_aware']['L95'] - w49['L95_t']) <= 1e-4 * w49['L95_t']
         and abs(ms.get('line', 0) - w49['line']) <= 1e-6 * w49['line'] and pm.get('rows') == 12 and pm.get('floats') is True
         and pm.get('c_rel') is not None and pm['c_rel'] <= 1e-6 and pm.get('exact') is True and (rd.get('outputs') or {}).get('mode_step') == ms,
         'series %s %s; adm excluded %s, drop1 %s; rc %d deliver %s; G6a.11 %s %s; probe %s' % (
             ser.get('shape'), ser.get('dates') == D, (adm.get('cfg') or {}).get('mintpy.network.excludeDate'), (r1.get('outputs') or {}).get('state'),
             rc, rd.get('verdict'), v, val[:200],
             dict((k, pm.get(k)) for k in ('rows', 'floats', 'c_rel', 'exact', 'same', '_error'))))
    br, lk = man.get('branch') or {}, man.get('looks') or {}
    fcase(FR_MX, 'M49b (22.2, 18.5) RUN_MANIFEST.json names the branch and the looks: branch FBS+FBD (recon\'s G0.10 and verify\'s), range 12 and '
         'azimuth 28 looks, the grid 83 x 658 (recon/reference.json\'s geometry)',
         br.get('value') == 'FBS+FBD' and br.get('recon') == 'FBS+FBD' and br.get('verify') == 'FBS+FBD' and lk.get('range') == 12
         and lk.get('azimuth') == 28 and lk.get('grid_columns') == 83 and lk.get('grid_lines') == 658, 'branch %s; looks %s' % (br, lk))
    rd49 = rd
    # ---- M59a: the dry run of the delivered frame
    l0 = listing(W)
    DRY = os.path.join(T, 'r2b_dry_mx')
    rc, out = run(FR_MX, ['--dry-run', DRY, '--only', 'deliver'])
    rdd = json.load(open(os.path.join(DRY, 'status', 'P6a_deliver.json'))) if os.path.isfile(os.path.join(DRY, 'status', 'P6a_deliver.json')) else {}
    v, val, note = gl(rdd, 'G6a.11')
    pmd = json.load(open(os.path.join(DRY, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(DRY, 'RUN_MANIFEST.json')) else {}
    msd = pmd.get('mode_step') or {}
    fcase(FR_MX, 'M59a (15.2, 15.4) the dry run of the delivered mixed frame (--dry-run --only deliver): G6a.11 INFO, read from the frame\'s own '
         'products ("dry run, from the frame\'s own products: BOUNDED by share"), the preview\'s mode_step marked as a dry run\'s with '
         'the delivery\'s numbers; the frame unchanged (its listing)',
         rc == 0 and rdd.get('verdict') == 'PASS' and v == 'INFO' and val.startswith('dry run, from the frame\'s own products: BOUNDED by share')
         and msd.get('dry_run') is True and 'a dry run' in str(msd.get('source')) and msd.get('raw') == ms.get('raw')
         and msd.get('rows') == ms.get('rows') and listing(W) == l0, 'rc %d; deliver %s; G6a.11 %s %s; dry %s %s; unchanged %s' % (
             rc, rdd.get('verdict'), v, val[:160], msd.get('dry_run'), msd.get('source'), listing(W) == l0))
    # ---- the other six of the table, and the damaged series
    got = {}
    for name in TABLE[1:]:
        aside(W, FR_MX, name)
        rc, out = run(FR_MX, ['--only', 'deliver', '--force', 'deliver'], plant(name))
        r_ = rec(FR_MX, '6a', 'deliver')
        got[name] = dict(rc=rc, verdict=r_.get('verdict'), gate=gl(r_, 'G6a.11'), ms=(manifest(W).get('mode_step') or {}),
                         pm=probe('manifest', os.path.join(W, 'RUN_MANIFEST.json'), table, name))

    def near(ms_, name):
        w = tab['cases'][name]
        ok = ms_.get('raw') and ms_.get('dem_error_aware') and abs(abs(ms_['raw']['t']) - abs(w['z'])) <= 1e-4 * abs(w['z']) \
            and abs(abs(ms_['dem_error_aware']['t']) - abs(w['z_t'])) <= 1e-4 * abs(w['z_t']) \
            and abs(ms_['raw']['B95'] - w['B95']) <= 1e-4 * w['B95'] and abs(ms_['dem_error_aware']['B95'] - w['B95_t']) <= 1e-4 * w['B95_t']
        return bool(ok)

    def det(name):
        g = got[name]
        return '%s: rc %s deliver %s; G6a.11 %s %s | %s; c %s exact %s' % (name, g['rc'], g['verdict'], g['gate'][0], g['gate'][1][:150],
                                                                         g['gate'][2][:120], g['pm'].get('c_rel'), g['pm'].get('exact'))

    def fine(name, state, verdict, by=None):
        g = got[name]
        return g['rc'] == 0 and g['verdict'] == 'PASS' and g['ms'].get('state') == state and g['gate'][0] == verdict \
            and (by is None or g['ms'].get('bounded_by') == by) and near(g['ms'], name) and g['pm'].get('exact') is True \
            and (g['pm'].get('c_rel') or 1) <= 1e-6
    fcase(FR_MX, 'M53 (15.3 D, 15.4) a step through the mock dem_error on the FBD dates across the frame: 43 cm: FLAG, WARN, the note for '
         'Ariel\'s review ("for Ariel\'s review and the GNSS plan ... [CONFIRM WITH PL]"), |t| 13.63 and 14.33 as the desk\'s, deliver '
         'PASS; 1 cm: BOUNDED by share, INFO; both with the rows\' c the table\'s within 1e-6 and bound() exact on them',
         fine('M53_flag', 'FLAG', 'WARN') and 'for Ariel\'s review and the GNSS plan' in got['M53_flag']['gate'][2]
         and '[CONFIRM WITH PL]' in got['M53_flag']['gate'][2] and fine('M53_small', 'BOUNDED', 'INFO', 'share'),
         det('M53_flag') + ' || ' + det('M53_small'))
    fcase(FR_MX, 'M62 (15.3 D at 16.2\'s line, 15.4) a small ramp, the table\'s 0.5 cm/yr trend with the scatter x 0.67: BOUNDED by size, INFO, '
         'both B95s (0.23 and 0.03 cm/yr) and the ramp in the note; x 6.7: UNBOUNDED, INFO, "for the GNSS plan (DB1u)"; with the 43 cm '
         'step: FLAG, WARN; deliver PASS in each',
         fine('M62', 'BOUNDED', 'INFO', 'size') and 'bounded by size: a step could carry at most 0.23 and 0.03 cm/yr' in got['M62']['gate'][2]
         and 'range ramp of 0.50 cm/yr' in got['M62']['gate'][2] and fine('M62_x10', 'UNBOUNDED', 'INFO')
         and 'for the GNSS plan (DB1u)' in got['M62_x10']['gate'][2] and fine('M62_flag', 'FLAG', 'WARN'),
         det('M62') + ' || ' + det('M62_x10') + ' || ' + det('M62_flag'))
    fcase(FR_MX, 'M65 (15.3 D, 15.4) FLAG first: a tenth of M49\'s scatter, a 4 cm step: FLAG, WARN, |t| 12.89 and 13.43 against 4.27, where '
         'without the line it would read BOUNDED by share (bound() on the rows with the line at infinity); deliver PASS',
         fine('M65', 'FLAG', 'WARN') and got['M65']['pm'].get('without_line') == 'BOUNDED' and got['M65']['pm'].get('without_line_by') == 'share',
         det('M65') + '; without the line %s by %s' % (got['M65']['pm'].get('without_line'), got['M65']['pm'].get('without_line_by')))
    # M58: the series damaged after geocode (the mock view.py, step 9)
    aside(W, FR_MX, 'M58')
    rc, out = run(FR_MX, ['--only', 'deliver', '--force', 'deliver'],
                  dict(plant('M49'), LINOG_MOCK_H5BREAK=os.path.join(W, 'mintpy', 'timeseries_demErr.h5')))
    rd = rec(FR_MX, '6a', 'deliver')
    v, val, note = gl(rd, 'G6a.11')
    m58 = manifest(W).get('mode_step') or {}
    fcase(FR_MX, 'M58 (15.2, 15.4) an exception inside the reading (mintpy/timeseries_demErr.h5 written over after geocode, LINOG_MOCK_H5BREAK): '
         'G6a.11 WARN naming it ("the reading raised OSError ..."); deliver PASS, rc 0; RUN_MANIFEST.json written (G6a.7 PASS), its '
         'mode_step holding the error',
         rc == 0 and rd.get('verdict') == 'PASS' and v == 'WARN' and 'the reading raised OSError' in val and gates(rd).get('G6a.7') == 'PASS'
         and str(m58.get('error', '')).startswith('OSError') and m58.get('state') == 'NOT JUDGED',
         'rc %d deliver %s; G6a.11 %s %s; G6a.7 %s; mode_step error %s' % (rc, rd.get('verdict'), v, val[:200], gates(rd).get('G6a.7'), m58.get('error')))
    fcase(FR_MX, 'M61 (15.2, 15.4; v0.13 r3: the ascending record 96.3) deliver\'s record names v0.13 r3 (%s), LOGIC 7, and '
         'RUN_MANIFEST.json\'s label "RUN_MANIFEST.json (%s deliver)"; lp_modestep.py\'s md5 in the record\'s tools (not the '
         'fingerprint\'s kit); v0.12\'s T167, T210 and T300 read them so' % (D6.VERSION_DELIVER, D6.VERSION_DELIVER),
         rd49.get('version') == D6.VERSION_DELIVER == 'linog_auto v0.13 r3 (2026-10-30)' and rd49.get('logic') == 7
         and man.get('manifest') == 'RUN_MANIFEST.json (linog_auto v0.13 r3 (2026-10-30) deliver)'
         and (rd49.get('tools') or {}).get('lp_modestep.py') == S.md5(os.path.join(S.HERE, 'lp_modestep.py'))
         and 'lp_modestep.py' not in ((rd49.get('inputs') or {}).get('tools') or {}),
         'version %s logic %s; label %s; tools %s' % (rd49.get('version'), rd49.get('logic'), man.get('manifest'),
                                                     (rd49.get('tools') or {}).get('lp_modestep.py')))
    # the mixed frame's folder is read no more (M49c holds its manifest, man0, and M61 its record): removed when its cases PASSed
    if passed.get(FR_MX) and all(passed[FR_MX]):
        shutil.rmtree(W, ignore_errors=True)

    # =============================================================================== the FBS-only frame 3344
    rc, out = run(FR_FBS, ['--to', 'dfit'])
    rdf = rec(FR_FBS, '5f', 'dfit')
    DRY2 = os.path.join(T, 'r2b_dry_fbs')
    l0 = listing(WF)
    rc2, out2 = run(FR_FBS, ['--dry-run', DRY2, '--only', 'deliver'])
    rdd = json.load(open(os.path.join(DRY2, 'status', 'P6a_deliver.json'))) if os.path.isfile(os.path.join(DRY2, 'status', 'P6a_deliver.json')) else {}
    v, val, note = gl(rdd, 'G6a.11')
    pmd = json.load(open(os.path.join(DRY2, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(DRY2, 'RUN_MANIFEST.json')) else {}
    fcase(FR_FBS, 'M59b (15.2, 15.4) the dry run of the FBS-only frame 3344 after dfit, not yet delivered: G6a.11 INFO "dry run, from the frame\'s '
         'own products: not read: no products yet"; the preview\'s mode_step "not read"; the frame unchanged',
         rc == 0 and rdf.get('verdict') == 'PASS' and rc2 == 0 and v == 'INFO' and 'not read: no products yet' in val
         and (pmd.get('mode_step') or {}).get('state') == 'not read' and listing(WF) == l0,
         'rc %d dfit %s; dry rc %d; G6a.11 %s %s; preview %s; unchanged %s' % (rc, rdf.get('verdict'), rc2, v, val[:160],
                                                                             (pmd.get('mode_step') or {}).get('state'), listing(WF) == l0))
    rc, out = run(FR_FBS, [])
    rd = rec(FR_FBS, '6a', 'deliver')
    v, val, note = gl(rd, 'G6a.11')
    msf = (rd.get('outputs') or {}).get('mode_step') or {}
    so = probe('series_only', WF, os.path.join(scratch, 'series_only'))
    pv = [rec(FR_FBS, i, p).get('verdict') for i, p in (('6a', 'deliver'), ('6b', 'accept'), ('6c', 'package'), ('6d', 'rerun'))]
    fcase(FR_FBS, 'M51 (15.2, 15.4) the FBS-only path-84 mock 3344 recon to rerun: deliver PASS (and accept, package, rerun PASS), rc 0; G6a.11 N/A '
         '"one mode in the velocity fit: FBS 12, FBD 0 ... no array loaded", the reading\'s arrays_loaded false; the same reading on a '
         'folder holding only the series\' dates and attributes (no timeseries dataset, no other product): N/A',
         rc == 0 and pv == ['PASS'] * 4 and v == 'N/A' and re.search(r'one mode in the velocity fit: FBS \d+, FBD 0 \(', val) is not None
         and 'no array loaded' in val
         and msf.get('state') == 'N/A' and msf.get('arrays_loaded') is False and so.get('state') == 'N/A' and so.get('verdict') == 'N/A'
         and so.get('arrays') is False and so.get('files') == ['timeseries_demErr.h5'],
         'rc %d; %s; G6a.11 %s %s; arrays %s; series only %s %s %s' % (rc, pv, v, val[:160], msf.get('arrays_loaded'), so.get('verdict'),
                                                                       so.get('state'), so.get('files') or so.get('_error')))
    # M49c: the manifest's dropped dates, on both frames and on a synthetic RECON.json
    dr = (manifest(WF).get('dates') or {}).get('dropped') or {}
    gs = dr.get('granules') or []
    want_by = sorted(['G0.9', 'G1'])
    syn = os.path.join(scratch, 'recon_syn')
    os.makedirs(os.path.join(syn, 'recon'), exist_ok=True)
    os.makedirs(os.path.join(syn, 'status'), exist_ok=True)
    kinds = [('excluded in recon/exclude.txt: a person\'s reason', 'recon/exclude.txt', None),
             ('R7 (D2), loop 2: G21 flagged it', 'R7', 2), ('unreadable: no LED member', 'G0.4', None),
             ('product P1.1 (polarimetric), not an FBS/FBD L1.1 granule', 'G0.9', None),
             ('off-beam: off-nadir 41.5, modal 34.3, tolerance 0.5', 'G1', None),
             ('G0.16 framing (R6-b): dev_c -30.360 km, dev_b -30.1 km along track, beyond 11.27 km', 'G0.16', None)]
    with open(os.path.join(syn, 'recon', 'RECON.json'), 'w') as fh:
        json.dump(dict(exclusions_md5='e' * 32, granules=[dict(scene='ALPSRP%05d3399' % i, zip='z%d.zip' % i, date_summary='2008%04d' % (101 + i),
                                                               mode='FBS' if i % 2 else 'FBD', status='DROPPED', reason=k[0])
                                                          for i, k in enumerate(kinds)] + [dict(scene='KEPT', status='KEPT', reason='')]), fh)
    with open(os.path.join(syn, 'status', 'P0a_recon.json'), 'w') as fh:
        json.dump(dict(inputs=dict(exclusions_md5='e' * 32, d2_decision_md5='d' * 32)), fh)
    ds = D6.dropped_entry(syn)
    sg = ds.get('granules') or []
    fcase(FR_FBS, 'M49c (11.7) RUN_MANIFEST.json\'s dates.dropped: none on the mixed frame (count 0); the FBS-only frame\'s two (its P1.1 product, '
         'G0.9, and its off-beam granule, G1), each with its date, mode and reason; a RECON.json holding every kind of drop: the gate or '
         'file of each (recon/exclude.txt, R7 with its loop 2, G0.4, G0.9, G1, G0.16), in date order, and the decision files\' md5s as '
         'recon\'s record read them',
         ((man0.get('dates') or {}).get('dropped') or {}).get('count') == 0 and dr.get('count') == 2 and sorted(x.get('by') for x in gs) == want_by
         and all(x.get('date') and x.get('mode') == 'FBS' and x.get('reason') for x in gs)
         and [(x.get('by'), x.get('loop')) for x in sg] == [(k[1], k[2]) for k in kinds] and ds.get('count') == 6
         and ds.get('decision_files') == {'recon/exclude.txt': 'e' * 32, 'recon/d2_decision.json': 'd' * 32},
         'mixed %s; FBS-only %s; synthetic %s, files %s' % (((man0.get('dates') or {}).get('dropped') or {}).get('count'),
                                                           [(x.get('date'), x.get('mode'), x.get('by')) for x in gs],
                                                           [(x.get('by'), x.get('loop')) for x in sg], ds.get('decision_files')))

    # =============================================================================== M64: nothing goes STALE
    fpenv = {k: v_ for k, v_ in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
             and not k.startswith('LINOG_MOCK_')}

    def state(phase, cfg='paths_r2b.cfg'):
        e = dict(fpenv, LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfg), LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'),
                 LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'),
                 LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'), LINOG_ROOT=os.path.join(T, ROOT), LINOG_ARCHIVE=af)
        p = subprocess.run([sys.executable, '-E', '-B', os.path.join(S.HERE, 'lp_%s.py' % phase), '--path', '084', '--frame', FR_FBS,
                            '--state'], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1] if p.stdout else 'rc %d' % p.returncode

    rp = dict((p, rec(FR_FBS, i, p)) for i, p in (('5e', 'wmask'), ('4g', 'report'), ('5dab', 'd9ab'), ('5f', 'dfit'), ('5d1', 'drop1'),
                                                   ('6a', 'deliver')))
    q6, m5 = S.real_pins('linog_phase6.cfg'), S.real_pins('linog_mintpy.cfg')
    rj = os.path.join(WF, 'recon', 'reference.json')
    # deliver's fingerprint by v0.12 r2's formula (its lp_deliver.py, lines 584 to 587; LOGIC 6), on this frame's records and kit
    fp12 = C.md5_obj(dict(logic=6, wmask=(rp['wmask'].get('outputs') or {}).get('digest'), report=(rp['report'].get('outputs') or {}).get('digest'),
                          kit=dict((n, S.md5(os.path.join(T, 'kit', n))) for n in ('linog_phase6.sh', 'linog_los2hv.py', 'linog_embed_stats.py',
                                                                                    'linog_gen_interactive_kmz.py')),
                          reference=json.load(open(rj)).get('reference') if os.path.isfile(rj) else None, mintpy=m5.get('MINTPY_VERSION'),
                          d9ab=(rp['d9ab'].get('outputs') or {}).get('decision_md5'), dfit=(rp['dfit'].get('outputs') or {}).get('decision_md5'),
                          drop1=(rp['drop1'].get('outputs') or {}).get('decision_md5'))) if q6 else None
    f6 = os.path.join(WF, 'status', 'P6a_deliver.json')
    r6 = json.load(open(f6)) if os.path.isfile(f6) else {}
    same_fp = r6.get('fingerprint') == fp12
    r6.update(version='linog_auto v0.12 (2026-10-09)', fingerprint=fp12)   # the record as v0.12 r2 wrote it, as far as --state reads it
    (r6.get('outputs') or {}).pop('mode_step', None)
    (r6.get('tools') or {}).pop('lp_modestep.py', None)
    with open(f6, 'w') as fh:
        json.dump(r6, fh, indent=1)
        fh.write('\n')
    s_del = state('deliver')   # v0.13 r3: STALE (LOGIC 7; the ascending record 96.3), where r2 read it CURRENT
    # the frame's DEM changed: a copy of the mock DEM under another name, named by the frame's dem_ key
    d0 = dem12
    d1 = os.path.join(os.path.dirname(d0), 'mock12b.dem.wgs84')
    for e in ('', '.vrt', '.xml'):
        if not os.path.exists(d1 + e):
            shutil.copy2(d0 + e, d1 + e)
    with open(d1 + '.vrt') as fh:
        vrt = fh.read()
    with open(d1 + '.vrt', 'w') as fh:
        fh.write(vrt.replace(os.path.basename(d0), os.path.basename(d1)))
    txt = open(os.path.join(T, 'cfg', 'paths_r2b.cfg')).read()
    with open(os.path.join(T, 'cfg', 'paths_r2b_dem.cfg'), 'w') as fh:
        fh.write(txt.replace('dem_%s = %s\n' % (FR_FBS, d0), 'dem_%s = %s\n' % (FR_FBS, d1)))
    s1 = dict((p, state(p, 'paths_r2b_dem.cfg')) for p in ('recon', 'stage', 'stack1', 'stack2', 'topo', 'deliver'))
    s0 = dict((p, state(p)) for p in ('accept', 'package', 'rerun'))   # read, not judged: this fixture's accept is v0.13's (LOGIC 2)
    rc2, out2 = run(FR_FBS, ['--to', 'stage'], cfg='paths_r2b_dem.cfg')
    s2 = dict((p, state(p, 'paths_r2b_dem.cfg')) for p in ('recon', 'stage', 'stack1', 'stack2', 'topo'))
    fcase(FR_FBS, 'M64 (15.2, 15.4; 22.2\'s item 6; v0.13 r3: the ascending record 96.3) on the delivered FBS-only frame deliver\'s '
         'fingerprint is r3\'s formula, not v0.12 r2\'s (LOGIC 7 and linog_phase6_r3.sh\'s md5); its record made v0.12\'s (v0.12\'s '
         'label and fingerprint, no mode_step, no lp_modestep.py among its tools): --state reads deliver STALE under r3 (r2 read it '
         'CURRENT: M64 before r3); then the frame\'s DEM changed (dem_3344 naming a copy of the mock DEM): --state reads recon and '
         'stage STALE (deliver STALE); recon and stage run again (rc 0) and, stage having linked the new DEM, stack1, stack2 and topo '
         'read STALE',
         not same_fp and s_del == 'STALE' and s1.get('recon') == 'STALE' and s1.get('stage') == 'STALE'
         and s1.get('deliver') == 'STALE' and rc2 == 0 and s2.get('recon') == 'CURRENT' and s2.get('stage') == 'CURRENT'
         and s2.get('stack1') == 'STALE' and s2.get('stack2') == 'STALE' and s2.get('topo') == 'STALE',
         'fingerprint as v0.12 r2\'s %s; --state deliver %s (accept, package, rerun %s, read); DEM changed %s; --to stage rc %d; then %s' % (
             same_fp, s_del, s0, s1, rc2, s2))
    shutil.rmtree(scratch, ignore_errors=True)
    if passed.get(FR_FBS) and all(passed[FR_FBS]):
        shutil.rmtree(WF, ignore_errors=True)
