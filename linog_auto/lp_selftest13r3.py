#!/usr/bin/env python3
"""lp_selftest13r3.py -- linog_auto v0.13 r3's cases (the ascending record 96.3, 96.4 and 97): dfit's DEM-error loop and R4 out
of both fits, deliver's linog_phase6_r3.sh (G6a.3r, G6a.6e), RUN_MANIFEST.json's dem_error_excluded and demfit, G6a.11 given
G6a.6e's dates, and a frame made under r2 read under r3. Called from lp_selftest10.py's phase10 after T211 (it needs suite 10's
6-date frame p6d and its snapshot S6e, after bgrid), when the suite 13r3 is wanted (suite 10 runs it whenever both are).

The mock (selftest_kit/mock_mintpy): dem_error.py reads the template's mintpy.topographicResidual.excludeDate (auto:
exclude_date.txt in the working folder), prints MintPy 1.6.2's line naming the dates out of its fit, passes
mintpy/timeseries_ramp.h5 through (as the mock sbas's correct_topography does) and, planted, gives each date a residual
(LINOG_MOCK_DEMFIT: 1 mm, or 10 mm on a named date, or on a date named "D@A+B" once A and B are out of the fit);
LINOG_MOCK_DEM_NOEXCL=1 makes it read no exclusion (r2's chain A). timeseries_rms.py is MintPy 1.6.2's arithmetic (the
quadratic deramp, the RMS over the mask, the cutoff x median / 0.67449 rule, exclude_date.txt written or removed).

Function-level cases (lp_dfit in the mock env's Python, on a synthetic 12-date folder; the mock commands on the PATH):
  R3F1  the chain d2@d1, d3@d2, d4@d3, d5@d4 from d1: four passes each naming one new date, then G5f.10 DECISION (not
        stopped in 4), the loop's E d1 to d5, each pass's input exclude_date.txt as E then was;
  R3F2  d2@d1 from d1: pass 1 names d2, pass 2 none: G5f.10 PASS after 2 passes;
  R3F3  timeseries_rms.py fails (LINOG_MOCK_P6FAIL): G5f.9 FAIL on pass 1, the loop stops; dem_error.py fails: the same;
        dem_error reads no exclusion (LINOG_MOCK_DEM_NOEXCL): G5f.9 FAIL, its log naming no date;
  R3F4  template_rms(): auto keys (3, quadratic, sbas's mask); cutoff 2.5 and deramp linear read; a maskFile other than
        maskTempCoh.h5, a deramp other, and topographicResidual.excludeDate no: one problem each;
  R3F5  dem_excluded(): MintPy's line read (sorted); no line: []; a count that disagrees with the list: None.
Frame-level cases (the p6d frame from S6e, under --decide auto):
  R301  MintPy's outlier 20081130 (LINOG_MOCK_RMSOUT) and, once it is out of the DEM-error fit, a third date (LINOG_MOCK_DEMFIT
        "20081130;X@20081130", X the series' last date), to deliver: L1 two passes (pass 1 names X, pass 2 none: G5f.9 PASS
        twice, G5f.10 PASS), A1 (G5f.11 PASS), exclude_date.txt 20081130 and X, demfit.added X; deliver PASS: G6a.3r PASS,
        G6a.6e PASS naming both, mintpy/exclude_date.txt in place after (no _exclude_date.hold), RUN_MANIFEST.json's
        velocity_fit.dem_error_excluded both and its demfit with L1, mode_step's dem_error_excluded both, the log's line;
  R302  R4 out of both fits (LINOG_MOCK_RAMPDATE and LINOG_MOCK_TS, no MintPy outlier): no L1 (G5f.9 INFO), R4.1 INFO "leaves
        both fits" with dem_error's own run in r4/<date>/ (its input and its log naming the date), L2 in demfit2/ (G5f.9 PASS,
        G5f.10 PASS), the final fit on L2's series (G5f.8 PASS); deliver's G6a.6e naming the date;
  R303  deliver with chain A's exclusions not read (LINOG_MOCK_DEM_NOEXCL): G6a.6 PASS, G6a.6e FAIL ("no date" against the
        fit's), rc 2;
  R304  linog_phase6_r3.sh one line off its pin, in a copy of the pipeline (the package's own script never edited): G6a.3r
        FAIL before the script runs, rc 2;
  R305  a frame made under r2 (R302's delivered frame, dfit's and deliver's records given r2's fingerprints: dfit LOGIC 1,
        deliver LOGIC 6 without the r3 script; r3's formulas first checked against the records as written): --state reads every
        phase before dfit CURRENT, dfit and deliver STALE; the run to deliver runs dfit again (G5f.7 PASS, the file left) and
        stops at deliver's G6a.5 DECISION, rc 4; its outputs moved into the frame's _archive/ as the gate says: the run again
        delivers (PASS, G6a.6e naming the date), rc 0.
  R306  --only deliver on a frame whose dfit record is r2's (no DEM-error loop, LOGIC 1): G6a.1f FAIL, rc 2 (the review's item 1);
  R307  R4's own dem_error run fails: R4.1 FAIL, rc 2, exclude_date.txt not written;
  R308  R4's candidate taken first by the loop: G5f.11c INFO, no R4.N;
  R309  (97.6) the loop's limit 1 (a mock cfg's DFIT_DEMFIT_MAX_PASSES) and a third date: G5f.10 DECISION naming recon/demfit.txt,
        rc 4, mintpy/exclude_date.txt as sbas left it; --only deliver then G6a.1f FAIL;
  R310  A1's fit fails (LINOG_MOCK_T2V_FAIL_OUT=velocity_A1.h5): G5f.11 FAIL, rc 2, the file as sbas left it;
  R311  (97.6) the operator's recon/demfit.txt on R309's frame: dfit PASS, G5f.5o INFO, one pass, G5f.10 INFO, the file's dates out
        of both fits; deliver PASS naming them; dfit CURRENT, then STALE once the file changes;
  R312  recon/demfit.txt leaving out MintPy's date: G5f.5o FAIL, rc 2.
R301 also reads A1 against the mock's fit of sbas's series without E1: the mock's dem_error adds 0.1 mm/yr per date out on
timeseries_ramp.h5, so A1 read from L1's series differs by exactly 0.2 mm/yr (a fit read from the wrong series is caught).
"""
import json
import os
import shutil
import subprocess
import sys

import lp_common as C

PHASES = ('recon stage extract unpack rwin bandlimit verify stack1 reference stack2 topo coarse refine invert datum fine bgrid igram report '
          'admit prep mcfg sbas drop1 d9ab wmask dfit deliver accept package rerun').split()
BEFORE = PHASES[:PHASES.index('dfit')]

# the mock env's Python: argv[1] the case, argv[2] the pipeline folder, argv[3] a work folder; JSON last line
PROBE = r'''
import json, os, sys
what, HERE, D = sys.argv[1], sys.argv[2], sys.argv[3]
ARGS = sys.argv[4:]
sys.path.insert(0, HERE)
import numpy as np
import h5py
import lp_dfit as DF
os.environ['MPLCONFIGDIR'] = os.environ.get('LINOG_MPLCONFIG_PROBE', D)

DATES = ['2007%02d01' % m for m in range(1, 13)]


class St(object):
    def __init__(self):
        self.g = []

    def gate(self, gid, name, verdict, value, threshold='', note=''):
        self.g.append(dict(id=gid, name=name, verdict=verdict, value=value, note=note))


def frame(W, cfg=''):
    os.makedirs(os.path.join(W, 'mintpy', 'inputs'))
    os.makedirs(os.path.join(W, 'mintpy', 'watermask'))
    L, Wd = 20, 30
    with h5py.File(os.path.join(W, 'mintpy', 'timeseries_ramp.h5'), 'w') as f:
        f.create_dataset('timeseries', data=np.zeros((len(DATES), L, Wd), np.float32))
        f.create_dataset('date', data=np.array([d.encode() for d in DATES]))
        f.attrs.update(dict(FILE_TYPE='timeseries', REF_DATE=DATES[0], LENGTH=str(L), WIDTH=str(Wd)))
    with h5py.File(os.path.join(W, 'mintpy', 'inputs', 'geometryRadar.h5'), 'w') as f:
        f.create_dataset('height', data=np.zeros((L, Wd), np.float32))
    with h5py.File(os.path.join(W, 'mintpy', 'watermask', 'maskTempCoh.orig.h5'), 'w') as f:
        f.create_dataset('mask', data=np.ones((L, Wd), bool))
    with open(os.path.join(W, 'mintpy', 'smallbaselineApp.cfg'), 'w') as fh:
        fh.write(cfg or 'mintpy.residualRMS.cutoff = auto  #[0.0-inf], auto for 3\nmintpy.residualRMS.deramp = auto\n'
                        'mintpy.residualRMS.maskFile = auto\nmintpy.topographicResidual.excludeDate = auto\n')


def loop(tag, E0, env):
    W = os.path.join(D, tag)
    frame(W)
    for k in ('LINOG_MOCK_DEMFIT', 'LINOG_MOCK_P6FAIL', 'LINOG_MOCK_DEM_NOEXCL'):
        os.environ.pop(k, None)
    os.environ.update(env)
    tpl, bad = DF.template_rms(W)
    st = St()
    folder = os.path.join(W, 'dfit', 'x')
    os.makedirs(folder)
    E, passes, ok, ser = DF.demfit_loop(st, W, folder, E0, tpl, 120, {}, 'demfit')
    ins = [open(os.path.join(folder, p['folder'], 'exclude_date_input.txt')).read().split() for p in passes]
    return dict(E=E, ok=ok, n=len(passes), new=[p['new'] for p in passes], over=[p['over'] for p in passes],
                named=[p['dem_error_named'] for p in passes], ins=ins, tplbad=bad,
                gates=[(g['id'], g['verdict'], g['value'][:160]) for g in st.g])


d = DATES
out = {}
if what == 'loops':
    chain = '%s;%s@%s;%s@%s;%s@%s;%s@%s' % (d[1], d[2], d[1], d[3], d[2], d[4], d[3], d[5], d[4])
    out['f1'] = loop('f1', [d[1]], {'LINOG_MOCK_DEMFIT': chain})
    out['f2'] = loop('f2', [d[1]], {'LINOG_MOCK_DEMFIT': '%s;%s@%s' % (d[1], d[2], d[1])})
    out['f3a'] = loop('f3a', [d[1]], {'LINOG_MOCK_DEMFIT': d[1], 'LINOG_MOCK_P6FAIL': 'timeseries_rms.py'})
    out['f3b'] = loop('f3b', [d[1]], {'LINOG_MOCK_DEMFIT': d[1], 'LINOG_MOCK_P6FAIL': 'dem_error.py'})
    out['f3c'] = loop('f3c', [d[1]], {'LINOG_MOCK_DEMFIT': d[1], 'LINOG_MOCK_DEM_NOEXCL': '1'})
elif what == 'tpl':
    for tag, cfg in (('auto', ''),
                     ('set', 'mintpy.residualRMS.cutoff = 2.5\nmintpy.residualRMS.deramp = linear\n'),
                     ('mask', 'mintpy.residualRMS.maskFile = waterMask.h5\n'),
                     ('ramp', 'mintpy.residualRMS.deramp = cubic\n'),
                     ('topo', 'mintpy.topographicResidual.excludeDate = no\n')):
        W = os.path.join(D, 'tpl_' + tag)
        frame(W, cfg)
        t, bad = DF.template_rms(W)
        out[tag] = dict(cutoff=t['cutoff'], deramp=t['deramp'], mask=os.path.relpath(t['mask'], W) if t['mask'] else None, bad=bad)
    for tag, txt in (('two', "x\nexclude the following dates for DEM error estimation: (2)\n['20110214', '20100929']\ny\n"),
                     ('none', 'MOCK dem_error.py: nothing excluded\n'),
                     ('count', "exclude the following dates for DEM error estimation: (3)\n['20110214', '20100929']\n")):
        p = os.path.join(D, 'log_' + tag)
        open(p, 'w').write(txt)
        out['log_' + tag] = DF.dem_excluded(p)
elif what == 'a1':   # ARGS: velocity_A1.h5, mintpy/timeseries_ramp.h5, then E1: A1 less the mock's fit of sbas's series without E1
    import linog_mock6 as M6
    v1 = h5py.File(ARGS[0], 'r')['velocity'][()].astype(np.float64)
    v0 = M6.fit_velocity(ARGS[1], ARGS[2:])[0]['velocity'].astype(np.float64)
    d_ = (v1 - v0)[np.isfinite(v1 - v0)]
    out = dict(n=int(d_.size), mean=float(d_.mean()) if d_.size else None, ptp=float(np.ptp(d_)) if d_.size else None)
print(json.dumps(out))
'''


def phase13_r3(T, case, S, X):
    """X: suite 10's frame helpers (run6, rec6, restore6, W6, PL, RAMP, RMS, probe10, PROBE10)."""
    run6, rec6, restore6, W6, PL, RAMP, RMS = (X[k] for k in ('run6', 'rec6', 'restore6', 'W6', 'PL', 'RAMP', 'RMS'))

    def gates(r):
        return dict((g['id'], g['verdict']) for g in (r or {}).get('gates', []))

    def glist(r, gid):
        return [(g['verdict'], g.get('value') or '') for g in (r or {}).get('gates', []) if g['id'] == gid]

    def val(r, gid):
        x = glist(r, gid)
        return x[-1][1] if x else ''

    def jload(p):
        try:
            return json.load(open(p))
        except (OSError, ValueError):
            return {}

    def words(p):
        return open(p).read().split() if os.path.isfile(p) else None

    def probe(what, *args):
        D = os.path.join(T, 'r3probe_' + what)
        shutil.rmtree(D, ignore_errors=True)
        os.makedirs(D)
        # in the mock env as the phases run (lp_env.sh: conda activate, the mock MintPy's commands first on the PATH)
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1',
               'LINOG_ENV_CFG': os.path.join(T, 'cfg', 'env_mock.cfg'), 'LINOG_MPLCONFIG_PROBE': os.path.join(T, 'mplconfig_probe')}
        p = subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh'), 'python3', '-B', '-c', PROBE, what, S.HERE, D] + [str(a) for a in args],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        txt = p.stdout.decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## suite 13r3 probe %s  rc %d\n%s' % (what, p.returncode, txt))
        try:
            return json.loads(txt.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': txt[-800:]}

    # ---------------------------------------------------------------- function-level
    L = probe('loops')
    d = ['2007%02d01' % m for m in range(1, 13)]
    f1 = L.get('f1') or {}
    case('R3F1 (97) the DEM-error loop on a chain (d2@d1, d3@d2, d4@d3, d5@d4) from d1: four passes, each naming one new date, '
         'then G5f.10 DECISION (not stopped in 4); E d1 to d5; each pass\'s input the E of its time; dem_error\'s log naming it',
         f1.get('ok') is False and f1.get('n') == 4 and f1.get('new') == [[d[2]], [d[3]], [d[4]], [d[5]]] and f1.get('E') == d[1:6]
         and f1.get('ins') == [d[1:2], d[1:3], d[1:4], d[1:5]] and f1.get('named') == f1.get('ins')
         and [g[:2] for g in f1.get('gates') or []] == [['G5f.9', 'PASS']] * 4 + [['G5f.10', 'DECISION']],
         json.dumps(f1)[:900] if f1 else json.dumps(L)[:900])
    f2 = L.get('f2') or {}
    case('R3F2 the loop that stops: d2@d1 from d1: pass 1 names d2, pass 2 none; G5f.10 PASS after 2 passes; E d1, d2',
         f2.get('ok') is True and f2.get('n') == 2 and f2.get('new') == [[d[2]], []] and f2.get('E') == d[1:3]
         and [g[:2] for g in f2.get('gates') or []] == [['G5f.9', 'PASS'], ['G5f.9', 'PASS'], ['G5f.10', 'PASS']],
         json.dumps(f2)[:600])
    f3 = [L.get(k) or {} for k in ('f3a', 'f3b', 'f3c')]
    case('R3F3 a pass that fails stops the loop at G5f.9 FAIL: timeseries_rms.py exits 1; dem_error.py exits 1; dem_error reads no '
         'exclusion (its log names no date against E)',
         all(x.get('ok') is False and x.get('n') == 1 and [g[:2] for g in x.get('gates') or []] == [['G5f.9', 'FAIL']] for x in f3)
         and f3[2].get('named') == [[]] and 'its log names no date' in (f3[2].get('gates') or [[None, None, '']])[0][2],
         json.dumps(f3)[:900])
    P = probe('tpl')
    case('R3F4 template_rms(): auto keys read as MintPy 1.6.2\'s defaults (3, quadratic, sbas\'s mask, wmask\'s copy of it); cutoff 2.5 '
         'and deramp linear read; a maskFile other than maskTempCoh.h5, a deramp other, topographicResidual.excludeDate no: one '
         'problem each',
         (P.get('auto') or {}).get('cutoff') == 3.0 and (P.get('auto') or {}).get('deramp') == 'quadratic'
         and (P.get('auto') or {}).get('mask') == 'mintpy/watermask/maskTempCoh.orig.h5' and (P.get('auto') or {}).get('bad') == []
         and (P.get('set') or {}).get('cutoff') == 2.5 and (P.get('set') or {}).get('deramp') == 'linear' and (P.get('set') or {}).get('bad') == []
         and all(len((P.get(k) or {}).get('bad') or []) == 1 for k in ('mask', 'ramp', 'topo')),
         json.dumps(dict((k, P.get(k)) for k in ('auto', 'set', 'mask', 'ramp', 'topo', '_error')))[:900])
    case('R3F5 dem_excluded(): MintPy\'s line read, sorted (20100929, 20110214); no line: []; a count that disagrees with the list: '
         'None (not read)',
         P.get('log_two') == ['20100929', '20110214'] and P.get('log_none') == [] and P.get('log_count') is None,
         'two %s; none %s; count %s' % (P.get('log_two'), P.get('log_none'), P.get('log_count')))

    # ---------------------------------------------------------------- R301: L1 with a third date, to deliver
    restore6('S6e', 'R301')
    rc0, out0 = run6(['--to', 'sbas'], {'LINOG_MOCK_RMSOUT': RMS})
    tsd = X['probe10'](X['PROBE10'], 'dates', os.path.join(W6, 'mintpy', 'timeseries.h5'))
    third = [x for x in (tsd if isinstance(tsd, list) else []) if x not in (RMS, RAMP)][-1:]
    TD = third[0] if third else None
    E = sorted([RMS, TD]) if TD else None
    rc, out = run6(['--to', 'deliver'], {'LINOG_MOCK_RMSOUT': RMS, 'LINOG_MOCK_DEMFIT': '%s;%s@%s' % (RMS, TD, RMS)})
    rd, rv = rec6('5f', 'dfit'), rec6('6a', 'deliver')
    od, ov = rd.get('outputs') or {}, rv.get('outputs') or {}
    fd = os.path.join(W6, od.get('folder') or '-')
    g9 = glist(rd, 'G5f.9')
    man = jload(os.path.join(W6, 'RUN_MANIFEST.json'))
    vf = man.get('velocity_fit') or {}
    a1 = probe('a1', os.path.join(fd, 'velocity_A1.h5'), os.path.join(W6, 'mintpy', 'timeseries_ramp.h5'), *(E or []))
    lp6 = ov.get('log') or '-'   # the log deliver's record names (P1.new_log keeps earlier ones as .v<n>)
    lp6t = open(lp6).read() if os.path.isfile(lp6) else ''
    case('R301 (96.3, 97) MintPy\'s outlier %s and a third date %s once it is out of the DEM-error fit, to deliver: L1 two passes '
         '(pass 1 names %s, pass 2 none), G5f.10 PASS, A1 (G5f.11) PASS; exclude_date.txt both, demfit.added %s; deliver PASS: G6a.3r '
         'PASS, G6a.6e PASS naming both, exclude_date.txt in place after (no _exclude_date.hold); RUN_MANIFEST.json\'s velocity_fit '
         'dem_error_excluded both and its demfit (one loop, 2 passes); mode_step\'s dem_error_excluded both; the log\'s line' % (
             RMS, TD, TD, TD),
         TD is not None and rc0 == 0 and rc == 0 and rd.get('verdict') == 'PASS' and rd.get('logic') == 2
         and [v for v, _ in g9] == ['PASS', 'PASS'] and 'new %s' % TD in g9[0][1] and 'new none' in g9[1][1]
         and gates(rd).get('G5f.10') == 'PASS' and gates(rd).get('G5f.11') == 'PASS' and od.get('final') == E
         and (od.get('demfit') or {}).get('added') == [TD] and words(os.path.join(W6, 'mintpy', 'exclude_date.txt')) == E
         and words(os.path.join(fd, 'demfit', 'pass1', 'exclude_date_input.txt')) == [RMS]
         and words(os.path.join(fd, 'demfit', 'pass2', 'exclude_date_input.txt')) == E
         and rv.get('verdict') == 'PASS' and rv.get('logic') == 7 and gates(rv).get('G6a.3r') == 'PASS' and gates(rv).get('G6a.6e') == 'PASS'
         and ov.get('dem_error_excluded') == E and not os.path.lexists(os.path.join(W6, 'mintpy', '_exclude_date.hold'))
         and vf.get('dem_error_excluded') == E and len(((vf.get('demfit') or {}).get('loops') or [{}])[0].get('passes') or []) == 2
         and (man.get('mode_step') or {}).get('dem_error_excluded') == E
         and 'exclude the following dates for DEM error estimation: (2)' in lp6t
         and a1.get('n', 0) > 0 and abs(a1.get('mean', 0) - 2e-4) < 1e-6 and a1.get('ptp', 1) < 1e-6,
         'rc %d %d; A1 less the fit of sbas\'s series without E1 %s (the mock\'s 2 x 0.1 mm/yr: A1 read L1\'s series); series %s; dfit %s, G5f.9 %s, G5f.10 %s, G5f.11 %s; final %s added %s; file %s; deliver %s LOGIC %s, G6a.3r %s, G6a.6e %s %s; '
         'manifest %s; mode_step %s' % (
             rc0, rc, a1, tsd, rd.get('verdict'), [(v, x[:90]) for v, x in g9], gates(rd).get('G5f.10'), gates(rd).get('G5f.11'), od.get('final'),
             (od.get('demfit') or {}).get('added'), words(os.path.join(W6, 'mintpy', 'exclude_date.txt')), rv.get('verdict'), rv.get('logic'),
             gates(rv).get('G6a.3r'), gates(rv).get('G6a.6e'), val(rv, 'G6a.6e')[:120], vf.get('dem_error_excluded'),
             (man.get('mode_step') or {}).get('dem_error_excluded')))

    # ---------------------------------------------------------------- R302: R4 out of both fits, L2
    restore6('S6e', 'R302')
    rc, out = run6(['--to', 'deliver'], PL)
    rd, rv = rec6('5f', 'dfit'), rec6('6a', 'deliver')
    od = rd.get('outputs') or {}
    fd = os.path.join(W6, od.get('folder') or '-')
    g9 = glist(rd, 'G5f.9')
    r4d = os.path.join(fd, 'r4', RAMP)
    r4log = open(os.path.join(r4d, 'dem_error.log')).read() if os.path.isfile(os.path.join(r4d, 'dem_error.log')) else ''
    case('R302 (97) R4 out of both fits: no MintPy outlier, so no L1 (G5f.9 INFO); R4.1 INFO "leaves both fits", B\'s dem_error run '
         'in r4/%s/ (its input and its log naming the date); L2 in demfit2/ (G5f.9 PASS, G5f.10 PASS); the final fit on L2\'s series '
         '(G5f.8 PASS); exclude_date.txt %s; deliver PASS, G6a.6e naming it' % (RAMP, RAMP),
         rc == 0 and rd.get('verdict') == 'PASS' and [v for v, _ in g9] == ['INFO', 'PASS'] and 'no loop' in g9[0][1]
         and gates(rd).get('R4.1') == 'INFO' and 'leaves both fits' in val(rd, 'R4.1') and 'G5f.11' not in gates(rd)
         and words(os.path.join(r4d, 'exclude_date_input.txt')) == [RAMP] and "['%s']" % RAMP in r4log
         and gates(rd).get('G5f.10') == 'PASS' and any(g['id'] == 'G5f.10' and 'demfit2' in g.get('name', '') for g in rd.get('gates') or [])
         and gates(rd).get('G5f.8') == 'PASS'
         and 'demfit2/pass1' in val(rd, 'G5f.8') and od.get('final') == [RAMP] and od.get('taken') == [RAMP]
         and rv.get('verdict') == 'PASS' and gates(rv).get('G6a.6e') == 'PASS' and (rv.get('outputs') or {}).get('dem_error_excluded') == [RAMP],
         'rc %d; dfit %s; G5f.9 %s; R4.1 %s %s; r4 input %s, log line %s; G5f.10 %s; G5f.8 %s; final %s; deliver %s G6a.6e %s' % (
             rc, rd.get('verdict'), [(v, x[:70]) for v, x in g9], gates(rd).get('R4.1'), val(rd, 'R4.1')[:80],
             words(os.path.join(r4d, 'exclude_date_input.txt')), "['%s']" % RAMP in r4log, val(rd, 'G5f.10')[:80], val(rd, 'G5f.8')[:100],
             od.get('final'), rv.get('verdict'), val(rv, 'G6a.6e')[:100]))

    # ---------------------------------------------------------------- R305 first: R302's delivered frame read as an r2 frame
    W = W6
    m5 = {}
    for ln in open(X['MCFG']):
        if '=' in ln and not ln.lstrip().startswith('#'):
            k, v = ln.split('=', 1)
            m5[k.strip()] = v.strip()
    rw, rs, ra, rr = rec6('5e', 'wmask'), rec6('5d', 'sbas'), rec6('5a', 'admit'), rec6('4g', 'report')
    r9, r1 = rec6('5dab', 'd9ab'), rec6('5d1', 'drop1')
    rd, rv = rec6('5f', 'dfit'), rec6('6a', 'deliver')
    od = rd.get('outputs') or {}

    def fp_dfit(logic):
        d_ = dict(logic=logic, wmask=(rw.get('outputs') or {}).get('digest'), sbas=(rs.get('outputs') or {}).get('digest'),
                  r4=(ra.get('outputs') or {}).get('r4_md5'), mintpy=m5.get('MINTPY_VERSION'), defaults=m5.get('MINTPY_DEFAULTS_MD5'))
        if logic >= 2:   # r3 (97.6): the loop's limit as the cfg names it and the operator file's md5 (none here)
            d_.update(demfit_max_passes=m5.get('DFIT_DEMFIT_MAX_PASSES') or '4', demfit_file=None)
        return C.md5_obj(d_)
    rj = jload(os.path.join(W, 'recon', 'reference.json'))
    kit = dict((n, S.md5(os.path.join(T, 'kit', n))) for n in ('linog_phase6.sh', 'linog_los2hv.py', 'linog_embed_stats.py',
                                                              'linog_gen_interactive_kmz.py'))
    dec2 = C.md5_obj(dict(base=od.get('base'), taken=od.get('taken'), final=od.get('final')))   # r2's dfit decision_md5

    def fp_deliver(logic, dfit_dec, r3):
        d_ = dict(logic=logic, wmask=(rw.get('outputs') or {}).get('digest'), report=(rr.get('outputs') or {}).get('digest'), kit=kit,
                  reference=rj.get('reference'), mintpy=m5.get('MINTPY_VERSION'), d9ab=(r9.get('outputs') or {}).get('decision_md5'),
                  dfit=dfit_dec, drop1=(r1.get('outputs') or {}).get('decision_md5'))
        if r3:
            d_['phase6_r3'] = S.md5(os.path.join(S.HERE, 'linog_phase6_r3.sh'))
        return C.md5_obj(d_)
    same3 = fp_dfit(2) == rd.get('fingerprint') and fp_deliver(7, od.get('decision_md5'), True) == rv.get('fingerprint')
    for idx, ph, fp, lg, dec in (('5f', 'dfit', fp_dfit(1), 1, dec2), ('6a', 'deliver', fp_deliver(6, dec2, False), 6, None)):
        f = os.path.join(W, 'status', 'P%s_%s.json' % (idx, ph))
        r = jload(f)
        r.update(fingerprint=fp, logic=lg, version='linog_auto v0.13 r2 (2026-10-19)')
        if dec:
            r['outputs']['decision_md5'] = dec
            r['outputs'].pop('demfit', None)
        with open(f, 'w') as fh:
            json.dump(r, fh, indent=1)
            fh.write('\n')
    fpenv = {k: v_ for k, v_ in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
             and not k.startswith('LINOG_MOCK_')}

    def state(ph, mcfg=None):
        e = dict(fpenv, LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p6d.cfg'), LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'),
                 LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'),
                 LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'), LINOG_ROOT=os.path.join(T, 'p6d'), LINOG_MINTPY_CFG=mcfg or X['MCFG'],
                 LINOG_AUTO_HOST=__import__('socket').gethostname())
        p = subprocess.run([sys.executable, '-E', '-B', os.path.join(S.HERE, 'lp_%s.py' % ph), '--path', '084', '--frame', X['FRAME'],
                            '--state'], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t = p.stdout.decode('utf-8', 'replace').strip().splitlines()
        return t[-1].strip() if t else 'rc %d' % p.returncode
    st = dict((ph, state(ph)) for ph in PHASES)
    before_ok = all(st[ph] == 'CURRENT' for ph in BEFORE if ph != 'bandlimit')   # bandlimit: NONE on an FBS-only frame
    rc1, out1 = run6(['--to', 'deliver'], PL)
    rd1, rv1 = rec6('5f', 'dfit'), rec6('6a', 'deliver')
    import lp_p6 as P6
    way = [x for x in P6.deliver_way('084', X['FRAME']) if os.path.lexists(os.path.join(W, x))]
    arch = os.path.join(W, '_archive', 'r2_deliver_selftest')
    for x in way:
        os.makedirs(os.path.dirname(os.path.join(arch, x)), exist_ok=True)
        os.rename(os.path.join(W, x), os.path.join(arch, x))
    rc2, out2 = run6(['--to', 'deliver'], PL)
    rv2 = rec6('6a', 'deliver')
    case('R305 (96.4, step 6\'s rehearsal) a frame made under r2 (R302\'s, dfit\'s and deliver\'s records given r2\'s fingerprints: dfit LOGIC '
         '1, deliver LOGIC 6 without the r3 script; r3\'s formulas first reproduce the records as written): --state reads the %d phases '
         'before dfit CURRENT (bandlimit CURRENT or NONE), dfit and deliver STALE; the run to deliver runs dfit again (PASS, G5f.7 PASS: the file '
         'left) and stops at deliver\'s G6a.5 DECISION, rc 4; its outputs moved into the frame\'s _archive/ as the gate says, the run '
         'again delivers (PASS, LOGIC 7, G6a.6e naming %s), rc 0' % (len(BEFORE) - 1, RAMP),
         same3 and before_ok and st['bandlimit'] in ('NONE', 'CURRENT') and st['dfit'] == 'STALE' and st['deliver'] == 'STALE'
         and rc1 == 4 and rd1.get('verdict') == 'PASS' and rd1.get('logic') == 2 and gates(rd1).get('G5f.7') == 'PASS'
         and rv1.get('verdict') == 'DECISION' and gates(rv1).get('G6a.5') == 'DECISION' and '_archive/' in json.dumps(rv1.get('gates'))
         and len(way) > 10 and rc2 == 0 and rv2.get('verdict') == 'PASS' and rv2.get('logic') == 7
         and (rv2.get('outputs') or {}).get('dem_error_excluded') == [RAMP],
         'r3 formulas reproduce the records %s; states %s; to deliver rc %d (dfit %s G5f.7 %s; deliver %s G6a.5 %s); %d paths moved; '
         'again rc %d deliver %s LOGIC %s %s' % (
             same3, dict((ph, st[ph]) for ph in PHASES if st[ph] != 'CURRENT'), rc1, rd1.get('verdict'), gates(rd1).get('G5f.7'),
             rv1.get('verdict'), gates(rv1).get('G6a.5'), len(way), rc2, rv2.get('verdict'), rv2.get('logic'),
             (rv2.get('outputs') or {}).get('dem_error_excluded')))

    # ---------------------------------------------------------------- R303: chain A's exclusions not read
    restore6('S6e', 'R303')
    rc0, out0 = run6(['--to', 'dfit'], PL)
    rc, out = run6(['--only', 'deliver'], dict(PL, LINOG_MOCK_DEM_NOEXCL='1'))
    rv = rec6('6a', 'deliver')
    case('R303 (96.3) deliver with chain A\'s exclusions not read (LINOG_MOCK_DEM_NOEXCL, as r2\'s script ran it): G6a.6 PASS, G6a.6e '
         'FAIL ("no date" against the fit\'s %s), rc 2' % RAMP,
         rc0 == 0 and rc == 2 and gates(rv).get('G6a.6') == 'PASS' and gates(rv).get('G6a.6e') == 'FAIL'
         and 'names no date' in val(rv, 'G6a.6e') and RAMP in val(rv, 'G6a.6e'),
         'rc %d %d; G6a.6 %s; G6a.6e %s %s' % (rc0, rc, gates(rv).get('G6a.6'), gates(rv).get('G6a.6e'), val(rv, 'G6a.6e')[:140]))

    # ---------------------------------------------------------------- R304: the r3 script off its pin, in a copy of the pipeline
    PC = os.path.join(T, 'pipe_r304')
    shutil.rmtree(PC, ignore_errors=True)
    shutil.copytree(S.HERE, PC, symlinks=True, ignore=shutil.ignore_patterns('__pycache__', '.git'))
    sp, spc = os.path.join(S.HERE, 'linog_phase6_r3.sh'), os.path.join(PC, 'linog_phase6_r3.sh')
    m_pkg = S.md5(sp)
    with open(spc, 'ab') as fh:
        fh.write(b'# off its pin (the self-test\'s R304)\n')
    e = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
         and not k.startswith('LINOG_MOCK_')}
    e.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p6d.cfg'), LINOG_AUTO_HOST=__import__('socket').gethostname(),
             LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
             LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
             LINOG_ROOT=os.path.join(T, 'p6d'), LINOG_MINTPY_CFG=X['MCFG'])
    e.update(PL)
    p = subprocess.run(['bash', os.path.join(PC, 'linog_auto.sh'), '084', X['FRAME'], '--decide', 'auto', '--only', 'deliver'], env=e,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rc = p.returncode
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## R304: %s/linog_auto.sh --only deliver  rc %d\n%s' % (PC, rc, p.stdout.decode('utf-8', 'replace')))
    rv = rec6('6a', 'deliver')
    case('R304 (96.3; the review\'s item: in a copy of the pipeline, the package\'s own script never edited) linog_phase6_r3.sh one '
         'line off its pin: G6a.3r FAIL before the script runs (no G6a.6), rc 2; the package\'s script as it was',
         rc == 2 and gates(rv).get('G6a.3r') == 'FAIL' and 'G6a.6' not in gates(rv) and S.md5(sp) == m_pkg and PC in val(rv, 'G6a.3r'),
         'rc %d; G6a.3r %s %s; G6a.6 %s; the package\'s script %s' % (rc, gates(rv).get('G6a.3r'), val(rv, 'G6a.3r')[:140], gates(rv).get('G6a.6'),
                                                                    'as it was' if S.md5(sp) == m_pkg else 'CHANGED'))
    shutil.rmtree(PC, ignore_errors=True)

    # ---------------------------------------------------------------- R306: an r3 deliver on an r2 dfit record (the review's item 1)
    restore6('S6e', 'R306')
    rc0, out0 = run6(['--to', 'dfit'], PL)
    f5 = os.path.join(W6, 'status', 'P5f_dfit.json')
    r5 = jload(f5)
    (r5.get('outputs') or {}).pop('demfit', None)
    r5.update(logic=1, version='linog_auto v0.13 r2 (2026-10-19)')
    with open(f5, 'w') as fh:
        json.dump(r5, fh, indent=1)
        fh.write('\n')
    rc, out = run6(['--only', 'deliver'], PL)
    rv = rec6('6a', 'deliver')
    case('R306 (the review\'s item 1) --only deliver on a frame whose dfit record is r2\'s (no DEM-error loop on record, LOGIC 1): G6a.1f '
         'FAIL naming it, before the script; rc 2; no delivery written',
         rc0 == 0 and rc == 2 and gates(rv).get('G6a.1f') == 'FAIL' and 'not r3' in val(rv, 'G6a.1f') and 'G6a.6' not in gates(rv)
         and not os.path.exists(os.path.join(W6, 'mintpy', 'timeseries_demErr.h5')),
         'rc %d %d; G6a.1f %s %s; G6a.6 %s' % (rc0, rc, gates(rv).get('G6a.1f'), val(rv, 'G6a.1f')[:160], gates(rv).get('G6a.6')))

    # ---------------------------------------------------------------- R307: R4's own dem_error fails
    restore6('S6e', 'R307')
    rc, out = run6(['--to', 'dfit'], dict(PL, LINOG_MOCK_P6FAIL='dem_error.py'))
    rd = rec6('5f', 'dfit')
    case('R307 (the review\'s coverage item) R4\'s dem_error run fails (LINOG_MOCK_P6FAIL; no MintPy outlier, so no L1 before it): R4.1 '
         'FAIL naming dem_error\'s rc, rc 2, mintpy/exclude_date.txt not written',
         rc == 2 and rd.get('verdict') == 'FAIL' and gates(rd).get('R4.1') == 'FAIL' and 'dem_error.py without %s: rc 1' % RAMP in val(rd, 'R4.1')
         and not os.path.exists(os.path.join(W6, 'mintpy', 'exclude_date.txt')),
         'rc %d; dfit %s; R4.1 %s %s' % (rc, rd.get('verdict'), gates(rd).get('R4.1'), val(rd, 'R4.1')[:160]))

    # ---------------------------------------------------------------- R308: a candidate the loop takes first
    restore6('S6e', 'R308')
    rc, out = run6(['--to', 'dfit'], dict(PL, LINOG_MOCK_RMSOUT=RMS, LINOG_MOCK_DEMFIT='%s;%s@%s' % (RMS, RAMP, RMS)))
    rd = rec6('5f', 'dfit')
    od = rd.get('outputs') or {}
    case('R308 (the review\'s coverage item) R4\'s candidate %s taken first by the DEM-error loop (once %s is out, MintPy\'s rule names it): '
         'G5f.11c INFO naming it, no R4.N, taken none; the fit\'s dates %s and %s; dfit PASS' % (RAMP, RMS, RMS, RAMP),
         rc == 0 and rd.get('verdict') == 'PASS' and gates(rd).get('G5f.11c') == 'INFO' and RAMP in val(rd, 'G5f.11c')
         and not any(g['id'].startswith('R4.') for g in rd.get('gates') or []) and od.get('taken') == [] and od.get('final') == sorted([RMS, RAMP]),
         'rc %d; dfit %s; G5f.11c %s %s; R4 gates %s; taken %s final %s' % (
             rc, rd.get('verdict'), gates(rd).get('G5f.11c'), val(rd, 'G5f.11c')[:100],
             [g['id'] for g in rd.get('gates') or [] if g['id'].startswith('R4.')], od.get('taken'), od.get('final')))

    # ---------------------------------------------------------------- R309 to R312: the limit, A1's failure, the operator's file
    M1 = X['mcopy']('mintpy_demfit1.cfg', DFIT_DEMFIT_MAX_PASSES=1)
    P9 = {'LINOG_MOCK_RMSOUT': RMS, 'LINOG_MOCK_DEMFIT': '%s;%s@%s' % (RMS, TD, RMS), 'LINOG_MINTPY_CFG': M1}
    restore6('S6e', 'R309')
    rc, out = run6(['--to', 'dfit'], P9)
    rd = rec6('5f', 'dfit')
    rc2, out2 = run6(['--only', 'deliver'], P9)
    rv = rec6('6a', 'deliver')
    case('R309 (97.6) the loop\'s limit 1 (DFIT_DEMFIT_MAX_PASSES in a mock cfg) and the third date %s once %s is out: G5f.10 DECISION '
         'naming recon/demfit.txt, rc 4, mintpy/exclude_date.txt as sbas left it (%s); --only deliver then G6a.1f FAIL, rc 2' % (TD, RMS, RMS),
         TD is not None and rc == 4 and rd.get('verdict') == 'DECISION' and gates(rd).get('G5f.10') == 'DECISION'
         and 'recon/demfit.txt' in json.dumps(rd.get('gates')) and words(os.path.join(W6, 'mintpy', 'exclude_date.txt')) == [RMS]
         and rc2 == 2 and gates(rv).get('G6a.1f') == 'FAIL',
         'rc %d; dfit %s, G5f.10 %s %s; file %s; deliver rc %d G6a.1f %s' % (rc, rd.get('verdict'), gates(rd).get('G5f.10'),
                                                                          val(rd, 'G5f.10')[:100], words(os.path.join(W6, 'mintpy', 'exclude_date.txt')),
                                                                          rc2, gates(rv).get('G6a.1f')))
    with open(os.path.join(W6, 'recon', 'demfit.txt'), 'w') as fh:
        fh.write('# the dates out of both fits (the self-test\'s R311)\n%s\n%s\n' % (RMS, TD))
    rc, out = run6(['--to', 'deliver'], P9)
    rd, rv = rec6('5f', 'dfit'), rec6('6a', 'deliver')
    od = rd.get('outputs') or {}
    g9 = glist(rd, 'G5f.9')
    s1 = state('dfit', M1)
    with open(os.path.join(W6, 'recon', 'demfit.txt'), 'a') as fh:
        fh.write('# changed\n')
    s2 = state('dfit', M1)
    case('R311 (97.6) the operator\'s recon/demfit.txt (%s, %s) on R309\'s frame, to deliver: dfit PASS, G5f.5o INFO, one pass (G5f.9 '
         'PASS), G5f.10 INFO naming the file, the fit\'s dates the file\'s, exclude_date.txt both; deliver PASS, G6a.6e naming both; '
         'dfit CURRENT, then STALE once the file changes' % (RMS, TD),
         rc == 0 and rd.get('verdict') == 'PASS' and gates(rd).get('G5f.5o') == 'INFO' and [v for v, _ in g9] == ['PASS']
         and gates(rd).get('G5f.10') == 'INFO' and 'recon/demfit.txt' in val(rd, 'G5f.10') and od.get('final') == sorted([RMS, TD])
         and words(os.path.join(W6, 'mintpy', 'exclude_date.txt')) == sorted([RMS, TD]) and rv.get('verdict') == 'PASS'
         and (rv.get('outputs') or {}).get('dem_error_excluded') == sorted([RMS, TD]) and s1 == 'CURRENT' and s2 == 'STALE',
         'rc %d; dfit %s, G5f.5o %s, G5f.9 %s, G5f.10 %s %s; final %s; deliver %s %s; state %s then %s' % (
             rc, rd.get('verdict'), gates(rd).get('G5f.5o'), [v for v, _ in g9], gates(rd).get('G5f.10'), val(rd, 'G5f.10')[:90],
             od.get('final'), rv.get('verdict'), (rv.get('outputs') or {}).get('dem_error_excluded'), s1, s2))
    with open(os.path.join(W6, 'recon', 'demfit.txt'), 'w') as fh:
        fh.write('%s\n' % TD)
    rc, out = run6(['--only', 'dfit'], P9)
    rd = rec6('5f', 'dfit')
    case('R312 (97.6) recon/demfit.txt leaving out MintPy\'s %s: G5f.5o FAIL naming it, rc 2' % RMS,
         rc == 2 and gates(rd).get('G5f.5o') == 'FAIL' and RMS in val(rd, 'G5f.5o'),
         'rc %d; G5f.5o %s %s' % (rc, gates(rd).get('G5f.5o'), val(rd, 'G5f.5o')[:120]))
    restore6('S6e', 'R310')
    rc, out = run6(['--to', 'dfit'], {'LINOG_MOCK_RMSOUT': RMS, 'LINOG_MOCK_T2V_FAIL_OUT': 'velocity_A1.h5'})
    rd = rec6('5f', 'dfit')
    case('R310 (the review\'s coverage item) A1\'s fit fails (LINOG_MOCK_T2V_FAIL_OUT=velocity_A1.h5; A\'s own fit runs): G5f.11 FAIL, rc '
         '2, mintpy/exclude_date.txt as sbas left it (%s)' % RMS,
         rc == 2 and gates(rd).get('G5f.6') == 'PASS' and gates(rd).get('G5f.11') == 'FAIL'
         and words(os.path.join(W6, 'mintpy', 'exclude_date.txt')) == [RMS],
         'rc %d; G5f.6 %s; G5f.11 %s %s; file %s' % (rc, gates(rd).get('G5f.6'), gates(rd).get('G5f.11'), val(rd, 'G5f.11')[:100],
                                                   words(os.path.join(W6, 'mintpy', 'exclude_date.txt'))))
