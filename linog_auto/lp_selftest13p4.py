#!/usr/bin/env python3
"""lp_selftest13p4.py -- linog_auto v0.13's Phase 3 and 4 cases for FBS+FBD and FBD-only frames (called by lp_selftest.py as
the suite 13p4; the ascending automation record's case numbers).

phase13_4: two full-height mock frames on one mock ground (LINOG_MOCK_V13=1, 17.9's four mocks: the SLC writer, refine,
resample and topo; selftest_kit/mock_isce/linog_mock3.py's V13 model), recon to igram:
  the mixed frame 3354, 1000 samples x 18432 lines, frame 3350's 12 dates with the same four FBD (15.4); the kit's G7 and
     G10 read windows of a full-height ALOS frame, which frame 3350's 512 lines cannot give (a departure from 15.4's single
     frame, recorded at the build);
  the FBD-only frame 3364, 6 FBD dates 1048 samples wide but one at 1000 (18.5's M81 at the mock's scale).
Cases:
  M1e the mixed frame to igram, every Phase 3 and 4 record PASS (M1's later lines);
  M73c (17.7, 17.9) G3a.14 PASS on the ground's relief (simamp by ISCE's formula from the heights that shade every date);
  M68 (17.4) G3b.12 reads each date's coarse misregistration (the mock's truth) within 0.03 samples and lines;
  M66 (17.3) R9 writes each date's truth in its own units within 1e-9 (G4c.3 4 of 4, G4c.8, G4c.9, G9p, G16, G9 PASS; G4c.6
     N/A); M66c G4c.10's v0.12 values and residuals equal an independent chain (invertMisreg's pinv in float32, G16's
     rebase) within 1e-6; M66b with N(0, 0.005) on each pair: R9's range RMSE 0.003 to 0.007, every date within 0.02;
  M67 G10 v3 after R9: every date within 0.02 of 0, G10v3 and G10m INFO, v2 PASS; M67b without R9 (the hook
     LINOG_MOCK_DATUM_V12): G10 v3 reads G4c.10's predicted residual within 0.03, G10m WARN, G10v3 WARN naming the dates
     the residual puts over 0.125;
  M69 water over 7 of the 9 cells (LINOG_MOCK_WATER): G10v3 NOT MEASURED (WARN), v2 PASS, fine PASS;
  M70 one date moved 3 samples after run_06 (LINOG_MOCK_FINESHIFT): v2 FAIL, G10v3 WARN naming it, fine FAIL rc 2, the note
     giving 17.8's way on;
  M67c the late band's products decorrelated and one date cut short of the far columns: those windows do not vote, that
     date is read at fill 0.90 only; M67d v2's vote rule on a table (the part 4 review's P4-01 and P4-02);
  M72 R9's limits: a pair shelve missing, a pair at range order 1, a date's SLR differing between two copies, pairs/ holding
     a folder refine's record lacks, run_04's printed ratio off: G4c.8 FAIL, nothing written; a pair list that splits the
     dates: G4c.9 FAIL; refineSecondaryTiming.py off its pin: G4c.3 FAIL; datum forced again after PASS: G4c.4 PASS, the
     same values, no byte of dates/ changed; a SIGTERM while R9 writes, and the resume;
  M74 the dry run: topo, coarse and fine plan only (no reading); datum's plan is R9's from the frame's own pair shelves;
     nothing in the frame changes; M74b the same on a frame past refine whose invert has not run;
  M14 (4.8) G11m on the mixed frame: the census reads recon/modes.json's FBS dates, its classes the network's; M14b the
     census given SLC as --fbs-dir (v0.12's call, the hook LINOG_MOCK_G11_SLC): G11m FAIL; Igrams 83 wide;
  M98 (21.4) G17: the reference .xml's FILE_NAME naming another file of the same size: G17 FAIL, nothing run;
  M81e to M81h (18.5) the FBD-only frame's later lines: G3a.14 PASS (a gate 16 samples); datum as v0.12 with G4c.10 equal in
     range within 1e-6 and apart in azimuth by the PRF ratios as the chain predicts; G10v3 INFO with a 0.03-sample truth and
     WARN at 0.1 (rho 16 / 14), G10m N/A; Igrams 174 wide
     (6 x 28 looks); G11 with every pair FBD-FBD and G11m on "FBS dates 1" (the _none/ placeholder).
The numeric references (the truth, the shelves' SLR and PRF by the mock's laws, the v0.12 chain) are computed by
CHAIN in the mock env's Python (numpy), from linog_mock3's own truth; the self-test's Python needs no numpy for them.
Each date carries the ground's common speckle and one of its own (linog_mock3.GAMMA13: a pair keeps a coherence of about 0.6).
Frames are kept after stack2, coarse, refine, invert, datum and fine (files over 1 MB hard-linked: the phases write new files,
after their way gates, and datum rewrites only shelves under 1 MB); a planted case puts the frame back at the same path.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import time

import lp_selftest13p1 as P13

FR, FR_FBD = '3354', '3364'
LF = 18432   # a full-height ALOS frame (the kit's G7 and G10 windows)
P34 = (('3a', 'topo'), ('3b', 'coarse'), ('4a', 'refine'), ('4b', 'invert'), ('4c', 'datum'), ('4d', 'fine'), ('4e', 'bgrid'),
       ('4f', 'igram'))

# The references, in the mock env's Python (numpy): input JSON {mock_isce, dates, modes, ref, pairs, v13}; output JSON
# {slr, prf (the mock sensor's laws), truth (linog_mock3), x (reference units, x(REF) = 0), own (each date's own units, R9's
# truth), v12 (invertMisreg's float32 pinv with the earliest date pinned, then G16's rebase), resid (what v12 leaves
# after run_06, reference units)}. The pairs' values as the mock refine writes them (isce2's ratios).
CHAIN = r'''
import json, sys
import numpy as np
inp = json.load(sys.stdin)
sys.path.insert(0, inp['mock_isce'])
import linog_mock3 as M
C = 299792458.0
dates = sorted(inp['dates'])
modes, ref = inp['modes'], inp['ref']
slr = dict((d, C / (2.0 * (32e6 if modes[d] == 'FBS' else 16e6))) for d in dates)
if inp['v13']:
    prf = dict((d, 100000.0 / (46.1 + 0.1 * (int(d) % 6))) for d in dates)
    t = dict((d, M.truth13(d, modes[d] == 'FBD')) for d in dates)
else:
    prf = dict((d, 100000.0 / 46.3) for d in dates)
    t = dict((d, M.truth(d)) for d in dates)
x = dict((d, (t[d][0] - t[ref][0], t[d][1] - t[ref][1])) for d in dates)
own = dict((d, (x[d][0] * prf[d] / prf[ref], x[d][1] * slr[ref] / slr[d])) for d in dates)
idx = dict((d, i) for i, d in enumerate(dates))
prs = sorted(inp['pairs'])
A = np.zeros((len(prs), len(dates)))
paz, prg = np.zeros(len(prs)), np.zeros(len(prs))
for k, pr in enumerate(prs):
    a, b = pr.split('_')
    A[k, idx[b]], A[k, idx[a]] = 1.0, -1.0
    paz[k] = (t[b][0] - t[a][0]) * (prf[b] / prf[a])
    prg[k] = (t[b][1] - t[a][1]) * (slr[a] / slr[b])
A1 = np.array(np.linalg.pinv(A[:, 1:]), np.float32)
Saz = np.concatenate([[0.0], np.dot(A1, paz)])
Srg = np.concatenate([[0.0], np.dot(A1, prg)])
sp = {'FBS': 1.0, 'FBD': 2.0}
v12 = dict((d, (float(Saz[idx[d]] - Saz[idx[ref]]), float(Srg[idx[d]] - Srg[idx[ref]] * sp[modes[ref]] / sp[modes[d]])))
           for d in dates)
res = dict((d, (x[d][0] - v12[d][0] * prf[ref] / prf[d], x[d][1] - v12[d][1] * slr[d] / slr[ref])) for d in dates)
json.dump(dict(slr=slr, prf=prf, truth=t, x=x, own=own, v12=v12, resid=res), sys.stdout)
'''

# Shelve edits in the mock env (the frames and polynomials unpickle there): argv[1] the action, then its arguments
EDIT = r'''
import shelve, sys
act = sys.argv[1]
if act == 'order1':   # a pair's rgpoly at range order 1, its constant kept
    with shelve.open(sys.argv[2], 'w') as db:
        p = db['rgpoly']
        c = p.getCoeffs()[0][0]
        p.initPoly(rangeOrder=1, azimuthOrder=0, coeffs=[[c, 1e-6]])
        db['rgpoly'] = p
elif act == 'slr':    # a shelve copy's range pixel times (1 + rel)
    with shelve.open(sys.argv[2], 'w') as db:
        f = db['frame']
        f.instrument.rangePixelSize = f.instrument.rangePixelSize * (1.0 + float(sys.argv[3]))
        db['frame'] = f
print('edited', act, sys.argv[2])
'''


def link_or_copy(src, dst):
    if os.path.getsize(src) > (1 << 20):
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None


def median(v):
    v = sorted(v)
    return None if not v else (v[len(v) // 2] if len(v) % 2 else 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2]))


def phase13_4(T, case, S):
    print('-- v0.13 Phases 3 and 4 (R9, G10 v3, G10m, G3b.12, igram\'s G11 classes and G17): the full-height mock frames 3354 '
          '(8 FBS, 4 FBD) and 3364 (6 FBD) on one mock ground (LINOG_MOCK_V13)')
    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M1e-M98 not run: the mock ground needs numpy, and neither Python tried has it', False)
        return
    ORB = S.ORBITS[:12]
    MI = os.path.join(S.KITSRC, 'mock_isce')
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    dem12 = re.search(r'^dem_3350 = (.+)$', base, re.M).group(1)
    with open(os.path.join(T, 'cfg', 'paths_p4.cfg'), 'w') as fh:
        fh.write(base.rstrip('\n') + '\n# v0.13 part 4: the full-height mock frames, on the same mock DEM\ndem_%s = %s\ndem_%s = %s\n' % (
            FR, dem12, FR_FBD, dem12))
    full = dict(lines=LF, rows13=True)
    am = P13.make_variant(T, S, 'v13mx', dict((i, full) for i in range(12)), frame=FR, orbs=ORB, fbd=S.FBD_3350)
    af = P13.make_variant(T, S, 'v13fbd', dict((i, full) for i in range(6)), frame=FR_FBD, orbs=S.ORBITS[:6], fbd=range(6),
                          width=lambda i: S.W_MX if i == 5 else S.W_MX + 48)
    if not am or not af:
        case('M1e-M98 not run: the full-height mock archives could not be made (numpy)', False)
        return

    def fd(root, frame=FR):
        return S.fdir(T, frame, root)

    def run(root, args, extra=None, frame=FR, decide=True):
        e = dict({'LINOG_ROOT': os.path.join(T, root), 'LINOG_MOCK_V13': '1', 'LINOG_ARCHIVE': am if frame == FR else af},
                 **(extra or {}))
        return S.run(T, ['084', frame] + (['--decide', 'auto'] if decide else []) + args, cfg='paths_p4.cfg', env_extra=e)

    def rec(root, idx, ph, frame=FR):
        return S.rec(T, frame, idx, ph, root)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gval(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def snap(root, frame, name):
        dst = os.path.join(T, 'snap_13p4', name)
        shutil.copytree(fd(root, frame), dst, symlinks=True, copy_function=link_or_copy)

    def restore(root, frame, name, tag):
        S.aside(T, fd(root, frame), '13p4_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_13p4', name), fd(root, frame), symlinks=True, copy_function=link_or_copy)

    def in_env(W, args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        env['LINOG_ENV_CFG'] = os.path.join(T, 'cfg', 'env_mock.cfg')
        p = subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh')] + args, cwd=W, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        return p.returncode, p.stdout.decode('utf-8', 'replace')

    def popen_env(root, frame, extra):
        """The environment S.run gives a run, for a run started with Popen (M72h's stop)."""
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p4.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_ROOT=os.path.join(T, root), LINOG_MOCK_V13='1', LINOG_ARCHIVE=am if frame == FR else af)
        env.update(extra)
        return env

    def mockpy(code, args=()):
        p = subprocess.run([S.MOCKPY[0], '-B', '-c', code] + list(args), cwd=T, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'), 'PYTHONDONTWRITEBYTECODE': '1'})
        if p.returncode:
            return None, p.stderr.decode('utf-8', 'replace')[-600:]
        return json.loads(p.stdout.decode()), ''

    def chain(inp):
        p = subprocess.run([S.MOCKPY[0], '-B', '-c', CHAIN], input=json.dumps(dict(inp, mock_isce=MI)).encode(), cwd=T,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'), 'PYTHONDONTWRITEBYTECODE': '1'})
        if p.returncode:
            return None, p.stderr.decode('utf-8', 'replace')[-600:]
        return json.loads(p.stdout.decode()), ''

    def dates_md5(W):
        return dict((os.path.relpath(f, W), md5(f)) for f in sorted(glob.glob(os.path.join(W, 'refineSecondaryTiming', 'dates', '*', 'misreg*'))))

    def baks(W):
        d = os.path.join(W, 'refineSecondaryTiming')
        return sorted(x for x in os.listdir(d) if x.startswith('dates_predatum_bak_')) if os.path.isdir(d) else []

    def listing(W):
        out = {}
        for dp, dn, fn in os.walk(W):
            for n in fn + [x for x in dn if os.path.islink(os.path.join(dp, x))]:
                p = os.path.join(dp, n)
                s_ = os.lstat(p)
                out[os.path.relpath(p, W)] = (s_.st_size, s_.st_mtime_ns)
        return out

    def modes_of(W):
        p = os.path.join(W, 'recon', 'modes.json')
        return dict((r['date'], r) for r in json.load(open(p)).get('dates', [])) if os.path.isfile(p) else {}

    def refjson(W):
        p = os.path.join(W, 'recon', 'reference.json')
        return json.load(open(p)) if os.path.isfile(p) else {}

    def iwidth(W, pairs):
        ws = set()
        for pr in pairs:
            x = os.path.join(W, 'Igrams', pr, '%s.int.xml' % pr)
            m = re.search(r'name="width">\s*<value>(\d+)', open(x).read()) if os.path.isfile(x) else None
            ws.add(int(m.group(1)) if m else None)
        return sorted(ws, key=lambda v: (v is None, v))

    def classes(pairs, modes):
        out = dict(FBS=0, FBD=0, MIXED=0)
        for pr in pairs:
            a, b = pr.split('_')
            out['FBS' if modes[a] == modes[b] == 'FBS' else 'FBD' if modes[a] == modes[b] == 'FBD' else 'MIXED'] += 1
        return out

    # =============================================================================== the mixed frame 3354, clean
    W = fd('m4')
    rcs = []
    for to, sn in (('stack2', 'mS2'), ('coarse', 'mS3b'), ('refine', 'mS4a'), ('invert', 'mS4b'), ('datum', 'mS4c'), ('fine', 'mS4d'),
                   ('igram', None)):
        rc, _ = run('m4', ['--to', to])
        rcs.append(rc)
        if rc != 0:
            break
        if sn:
            snap('m4', FR, sn)
    R = dict((ph, rec('m4', i, ph)) for i, ph in P34)
    rj = refjson(W)
    REF = rj.get('reference')
    MR = modes_of(W)
    MODES = dict((d, r.get('mode')) for d, r in MR.items())
    DATES = sorted(MODES)
    FBS = [d for d in DATES if MODES[d] == 'FBS']
    FBDD = [d for d in DATES if MODES[d] == 'FBD']
    SECS = [d for d in DATES if d != REF]
    PAIRS = sorted((R['refine'].get('outputs') or {}).get('misreg') or {})
    case('M1e (17.9) the mixed full-height frame 3354 on one mock ground, recon to igram under --decide auto: rc 0 at each of 7 stops, '
         'the 8 Phase 3 and 4 records PASS; 12 dates (8 FBS, 4 FBD), an FBS reference (D1f), %d pairs' % len(PAIRS),
         rcs == [0] * 7 and all(R[ph].get('verdict') == 'PASS' for _, ph in P34) and len(DATES) == 12 and len(FBDD) == 4
         and MODES.get(REF) == 'FBS' and len(PAIRS) >= 11,
         'rc %s; %s; reference %s; %d FBS, %d FBD' % (rcs, [(ph, R[ph].get('verdict')) for _, ph in P34], REF, len(FBS), len(FBDD)))
    if rcs != [0] * 7 or not REF or not PAIRS:
        case('M66-M98 not run: the mixed frame did not reach igram', False)
        return
    ch, err = chain(dict(dates=DATES, modes=MODES, ref=REF, pairs=PAIRS, v13=True))
    if not ch:
        case('M66-M98 not run: the reference chain failed in the mock env\'s Python', False, err)
        return

    # M73c: G3a.14 on the one ground's relief
    t14 = (R['topo'].get('outputs') or {}).get('g3a14') or {}
    c14 = [x['dx'] for x in t14.get('readings', []) if x.get('ratio') is not None and x['ratio'] >= 1.25 and x.get('dx') is not None]
    m14 = median(c14)
    case('M73c (17.7, 17.9) G3a.14 on the full-height mixed frame: simamp by ISCE\'s formula from the heights that shade every date\'s '
         'amplitude, against the band-limited FBS reference: PASS on 3 or more counted windows, the median within 1.5 samples of 0',
         gates(R['topo']).get('G3a.14') == 'PASS' and t14.get('counted', 0) >= 3 and m14 is not None and abs(m14) <= 1.5
         and abs(t14.get('gate_samples', 0) - 32.0) < 1e-6,
         '%s; %d counted, median %s' % (gval(R['topo'], 'G3a.14')[:140], t14.get('counted', 0), m14))

    # M68: G3b.12 on the coarse products
    g12 = (R['coarse'].get('outputs') or {}).get('g3b12') or {}
    dd12 = g12.get('dates') or {}
    e12 = dict((d, (abs(dd12[d]['dy'] - ch['x'][d][0]), abs(dd12[d]['dx'] - ch['x'][d][1]))) for d in SECS
               if d in dd12 and dd12[d].get('dx') is not None and dd12[d].get('dy') is not None)
    w12 = max((max(v) for v in e12.values()), default=None)
    case('M68 (17.4) G3b.12 on the coarse products (INFO): every date\'s dx and dy the mock\'s coarse misregistration (the date\'s truth '
         'less the reference\'s, the FBD dates 0.80 px more in range) within 0.03 samples and lines; the FBD less FBS offset read',
         gates(R['coarse']).get('G3b.12') == 'INFO' and len(e12) == len(SECS) and w12 is not None and w12 <= 0.03
         and (g12.get('mode') or {}).get('dx') is not None and abs(g12['mode']['dx'] - 0.80) < 0.15,
         'largest error %s on %d of %d dates; mode %s' % (None if w12 is None else round(w12, 4), len(e12), len(SECS),
                                                          dict((k, round(v, 4)) for k, v in (g12.get('mode') or {}).items()
                                                               if k in ('dx', 'dy'))))

    # M66: R9's write
    od = R['datum'].get('outputs') or {}
    r9 = od.get('r9') or {}
    after = od.get('after') or {}
    eo = max((max(abs(after[d][0] - ch['own'][d][0]), abs(after[d][1] - ch['own'][d][1])) for d in DATES if d in after), default=None)
    sp = r9.get('slr_prf') or {}
    elaw = max((max(abs(sp[d][0] / ch['slr'][d] - 1.0), abs(sp[d][1] / ch['prf'][d] - 1.0)) for d in DATES if d in sp), default=None)
    gd = gates(R['datum'])
    case('M66 (17.3) R9 on the mixed frame: datum writes each date\'s truth in its own units (rg x SLR(REF) / SLR(d), az x PRF(d) / '
         'PRF(REF)) within 1e-9; method R9; G4c.3 4 of 4, G4c.8 (run_04\'s printed ratios checked on every pair), G4c.9, G9p, G16, G9 '
         'PASS, G4c.6 N/A; the reference 0 and 0; each date\'s SLR and PRF the mock sensor\'s laws (relative 1e-12)',
         od.get('method') == 'R9' and eo is not None and eo <= 1e-9 and len(after) == 12 and after.get(REF) == [0.0, 0.0]
         and '4 of 4' in gval(R['datum'], 'G4c.3') and all(gd.get(k) == 'PASS' for k in ('G4c.8', 'G4c.9', 'G9p', 'G16', 'G9'))
         and gd.get('G4c.6') == 'N/A' and elaw is not None and elaw <= 1e-12 and r9.get('rank') == 11
         and 'checked on %d pairs' % len(PAIRS) in gval(R['datum'], 'G4c.8'),
         'method %s; largest error %s; SLR/PRF %s; gates %s' % (od.get('method'), eo, elaw, dict((k, gd.get(k)) for k in (
             'G4c.3', 'G4c.4', 'G4c.6', 'G4c.8', 'G4c.9', 'G9p', 'G4c.10', 'G16', 'G9'))))
    v12, rv = r9.get('v12') or {}, r9.get('residual_v12') or {}
    ev = max((max(abs(v12[d][0] - ch['v12'][d][0]), abs(v12[d][1] - ch['v12'][d][1])) for d in DATES if d in v12), default=None)
    er = max((max(abs(rv[d][0] - ch['resid'][d][0]), abs(rv[d][1] - ch['resid'][d][1])) for d in DATES if d in rv), default=None)
    rms = r9.get('rms_v12') or {}
    case('M66c (17.3) G4c.10 (INFO) on the mixed frame: v0.12\'s values (invertMisreg\'s pinv in float32, the earliest date pinned, '
         'G16\'s rebase) and the residual they would leave after run_06 equal an independent chain on the mock\'s network within '
         '1e-6 (the desk\'s chain() of g10_units.py in range, extended to azimuth by the PRF ratios, invertMisreg\'s float32 '
         'reproduced: CHAIN); the FBD dates\' rms in range above the FBS dates\'',
         gd.get('G4c.10') == 'INFO' and ev is not None and ev <= 1e-6 and er is not None and er <= 1e-6 and len(v12) == 12
         and rms.get('FBD') and rms.get('FBS') and rms['FBD'][1] > rms['FBS'][1],
         'largest differences %s, %s; rms by mode %s' % (ev, er, rms))

    # M67: G10 v3 after R9
    gv = (R['fine'].get('outputs') or {}).get('g10v3') or {}
    dv = gv.get('dates') or {}
    w67 = max((max(abs(v['dx']), abs(v['dy'])) for v in dv.values() if v.get('dx') is not None and v.get('dy') is not None),
              default=None)
    gf = gates(R['fine'])
    case('M67 (17.9) G10 v3 after R9: every date within 0.02 samples and lines of 0 on 3 or more voting windows; G10v3 INFO, G10m '
         'INFO, v2 (G10) PASS; rho 32 / 14 (a mixed frame)',
         gf.get('G10') == 'PASS' and gf.get('G10v3') == 'INFO' and gf.get('G10m') == 'INFO' and len(dv) == 11
         and all(v.get('n', 0) >= 3 for v in dv.values()) and w67 is not None and w67 <= 0.02 and gv.get('voting', 0) >= 3
         and abs(gv.get('rho', 0) - 32.0 / 14.0) < 1e-9 and abs((gv.get('mode') or {}).get('dx', 1.0)) <= 0.02,
         'largest |dx|, |dy| %s on %s voting windows; G10m %s' % (w67, gv.get('voting'), gval(R['fine'], 'G10m')[:120]))

    # M14: the census's classes on the mixed frame; Igrams' width
    gi = gates(R['igram'])
    g11 = (R['igram'].get('outputs') or {}).get('g11') or {}
    cw = classes(PAIRS, MODES)
    iw = iwidth(W, PAIRS)
    case('M14 (4.8) G11m on the mixed frame: the census read recon/modes.json\'s 8 FBS dates (one folder each under '
         'logs/igram/fbs_dates_<UTC>/) and its classes are the network\'s (FBS-FBS %d, MIXED %d, FBD-FBD %d); G11, G11d, G17 PASS; '
         'Igrams 83 wide (1000 at 12 x 28 looks)' % (cw['FBS'], cw['MIXED'], cw['FBD']),
         gi.get('G11m') == 'PASS' and gi.get('G11') == 'PASS' and gi.get('G17') == 'PASS' and gi.get('G11d') == 'PASS'
         and g11.get('fbs_census') == 8
         and g11.get('fbs_modes') == 8 and g11.get('classes') == cw and iw == [83]
         and sorted(os.listdir(g11.get('fbs_dir') or '/nonexistent')) == FBS,
         'G11m %s; classes %s; widths %s' % (gval(R['igram'], 'G11m')[:120], g11.get('classes'), iw))

    # M74: the dry run on the frame past igram: plans only, R9's plan from the frame's own records; the frame unchanged
    dr = os.path.join(T, 'dry_13p4')
    l0, d0 = listing(W), dates_md5(W)
    rc, _ = run('m4', ['--dry-run', dr, '--to', 'fine'])
    l1, d1 = listing(W), dates_md5(W)

    def drec(idx, ph):
        p = os.path.join(dr, 'status', 'P%s_%s.json' % (idx, ph))
        return json.load(open(p)) if os.path.isfile(p) else {}
    dt, dc, dda, dfn = drec('3a', 'topo'), drec('3b', 'coarse'), drec('4c', 'datum'), drec('4d', 'fine')
    pl, plw = (dda.get('outputs') or {}).get('plan') or {}, od.get('plan') or {}
    epl = max((max(abs(pl[d][0] - plw[d][0]), abs(pl[d][1] - plw[d][1])) for d in plw if d in pl), default=None)
    changed = sorted(k for k in set(l0) | set(l1) if l0.get(k) != l1.get(k))
    case('M74 (17.9) the dry run to fine on the frame past igram: rc 0; topo, coarse and fine plans only (no G3a.14, G3b.12 or G10v3, '
         'no reading in their records); datum\'s plan R9\'s from the frame\'s own pair shelves (its records the frame\'s: DIR\'s invert '
         'a plan), = the datum on record within 1e-12; nothing in the frame changed (%d files compared)' % len(l0),
         rc == 0 and all((r.get('outputs') or {}).get('planned') for r in (dt, dc, dfn)) and 'G3a.14' not in gates(dt)
         and 'g3a14' not in (dt.get('outputs') or {}) and 'G3b.12' not in gates(dc) and 'G10v3' not in gates(dfn)
         and 'g10v3' not in (dfn.get('outputs') or {}) and dda.get('verdict') == 'PASS' and (dda.get('outputs') or {}).get('method') == 'R9'
         and len(pl) == 12 and epl is not None and epl <= 1e-12 and 'the frame\'s own' in str((dda.get('inputs') or {}).get('records'))
         and not changed and d0 == d1,
         'rc %d; datum %s %s, plan within %s; changed %s' % (rc, dda.get('verdict'), (dda.get('outputs') or {}).get('method'), epl,
                                                             changed[:5]))

    # M74b (the part 4 review's P4-07): the dry run of the frame past refine, its invert not run: R9's plan from refine's record
    restore('m4', FR, 'mS4a', 'M74b')
    dr2 = os.path.join(T, 'dry_13p4b')
    l0b = listing(W)
    rc, _ = run('m4', ['--dry-run', dr2, '--to', 'datum'])
    l1b = listing(W)
    p2 = os.path.join(dr2, 'status', 'P4c_datum.json')
    db_ = json.load(open(p2)) if os.path.isfile(p2) else {}
    plb = (db_.get('outputs') or {}).get('plan') or {}
    eplb = max((max(abs(plb[d][0] - plw[d][0]), abs(plb[d][1] - plw[d][1])) for d in plw if d in plb), default=None)
    chb = sorted(k for k in set(l0b) | set(l1b) if l0b.get(k) != l1b.get(k))
    case('M74b (17.9; the part 4 review\'s P4-07) the dry run to datum on the frame past refine, its invert not run: rc 0; datum\'s '
         'plan R9\'s from refine\'s record and the frame\'s pair shelves (G4c.1 N/A, G4c.8 and G4c.9 PASS), = the datum the clean run '
         'wrote within 1e-12; nothing in the frame changed (%d files compared)' % len(l0b),
         rc == 0 and db_.get('verdict') == 'PASS' and (db_.get('outputs') or {}).get('planned') and (db_.get('outputs') or {}).get('method') == 'R9'
         and gates(db_).get('G4c.1') == 'N/A' and gates(db_).get('G4c.8') == 'PASS' and gates(db_).get('G4c.9') == 'PASS'
         and len(plb) == 12 and eplb is not None and eplb <= 1e-12 and 'refine record' in str((db_.get('inputs') or {}).get('records'))
         and not chb and not os.path.isdir(os.path.join(W, 'refineSecondaryTiming', 'dates')),
         'rc %d; datum %s; G4c.1 %s; plan within %s; changed %s' % (rc, db_.get('verdict'), gates(db_).get('G4c.1'), eplb, chb[:5]))

    # M66b: noise on each pair
    restore('m4', FR, 'mS3b', 'M66b')
    rc, _ = run('m4', ['--to', 'datum'], {'LINOG_MOCK_PAIRNOISE': '0.005'})
    ob = rec('m4', '4c', 'datum').get('outputs') or {}
    rb = ob.get('r9') or {}
    ab = ob.get('after') or {}
    eb = max((max(abs(ab[d][0] - ch['own'][d][0]), abs(ab[d][1] - ch['own'][d][1])) for d in DATES if d in ab), default=None)
    case('M66b (17.9) N(0, 0.005) on each pair\'s offset (LINOG_MOCK_PAIRNOISE): R9\'s range RMSE 0.003 to 0.007 (reference units) and '
         'every date within 0.02 of its truth, rc 0',
         rc == 0 and rb.get('rmse_rg') is not None and 0.003 <= rb['rmse_rg'] <= 0.007 and eb is not None and eb <= 0.02 and len(ab) == 12,
         'rc %d; RMSE rg %s az %s; largest error %s' % (rc, rb.get('rmse_rg'), rb.get('rmse_az'), eb))

    # M67b: v0.12's datum on the mixed frame (the hook), then fine
    restore('m4', FR, 'mS4b', 'M67b')
    rc, out67 = run('m4', ['--to', 'fine'], {'LINOG_MOCK_DATUM_V12': '1'})
    rd, rf = rec('m4', '4c', 'datum'), rec('m4', '4d', 'fine')
    o7 = rd.get('outputs') or {}
    res7 = (o7.get('r9') or {}).get('residual_v12') or {}
    g7 = (rf.get('outputs') or {}).get('g10v3') or {}
    dv7 = g7.get('dates') or {}
    e7 = dict((d, max(abs(dv7[d]['dx'] - res7[d][1]), abs(dv7[d]['dy'] - res7[d][0]))) for d in SECS
              if d in dv7 and d in res7 and dv7[d].get('dx') is not None and dv7[d].get('dy') is not None)
    note7 = gval(rf, 'G10v3')
    must = sorted(d for d in SECS if d in res7 and (abs(res7[d][1]) > 0.155 or abs(res7[d][0]) > 0.28))
    never = sorted(d for d in SECS if d in res7 and abs(res7[d][1]) < 0.095 and abs(res7[d][0]) < 0.22)
    named = sorted(d for d in SECS if re.search(r'(^|\n|\| )%s ' % d, note7))
    case('M67b (17.9) v0.12\'s datum on the mixed frame (the hook LINOG_MOCK_DATUM_V12: the kit\'s G16, G4c.6 PASS): G10 v3 reads each '
         'date within 0.03 of G4c.10\'s predicted residual; G10m WARN; G10v3 WARN naming every date the residual puts beyond 0.155 '
         'and none under 0.095; v2 as its own rule gives (%s)' % gates(rf).get('G10'),
         rc in (0, 2) and o7.get('method') == 'G16' and gates(rd).get('G4c.6') == 'PASS' and gates(rd).get('G16') == 'PASS'
         and 'SELF-TEST HOOK LINOG_MOCK_DATUM_V12' in out67 and len(e7) == len(SECS) and max(e7.values()) <= 0.03
         and gates(rf).get('G10m') == 'WARN' and gates(rf).get('G10v3') == 'WARN' and must and set(must) <= set(named)
         and not set(never) & set(named),
         'rc %d; largest |measured - predicted| %s; must %s, named %s, never %s; G10m %s' % (
             rc, round(max(e7.values()), 4) if e7 else None, must, named, never, gval(rf, 'G10m')[:100]))

    # M67c (the part 4 review's P4-02): the late band decorrelated (its windows do not vote) and one date's product zero from
    # column 744 (its patches there under the fill line)
    dcut = [d for d in FBS if d != REF][1]
    restore('m4', FR, 'mS4c', 'M67c')
    rc, _ = run('m4', ['--to', 'fine'], {'LINOG_MOCK_DECOR': '4', 'LINOG_MOCK_FILLCUT': '%s:744' % dcut})
    rfc = rec('m4', '4d', 'fine')
    gc = (rfc.get('outputs') or {}).get('g10v3') or {}
    wins = gc.get('windows') or []
    late = [w for w in wins if (w.get('cell') or [None])[0] == 2]
    early_mid = [w for w in wins if (w.get('cell') or [None])[0] != 2]
    vk = set(w['window'] for w in wins if w.get('votes'))
    lowfill = set(x['window'] for x in (gc.get('readings') or {}).get(dcut, []) if x['window'] in vk and x['fill'] < 0.90)
    nd = dict((d, v.get('n')) for d, v in (gc.get('dates') or {}).items())
    case('M67c (17.4; the part 4 review\'s P4-02) the late band\'s fine products a field of each date\'s own (LINOG_MOCK_DECOR) and %s\'s '
         'product zero from column 744 (LINOG_MOCK_FILLCUT): the 3 late windows do not vote (median ratio under 1.25), the 6 others '
         'do; %s read on the voting windows at fill 0.90 only, every other date on all 6; G10v3 INFO, v2 PASS, fine PASS' % (dcut, dcut),
         rc == 0 and rfc.get('verdict') == 'PASS' and gates(rfc).get('G10') == 'PASS' and gates(rfc).get('G10v3') == 'INFO'
         and len(late) == 3 and all(not w.get('votes') and (w.get('median_ratio') or 0) < 1.25 for w in late)
         and len(early_mid) == 6 and all(w.get('votes') for w in early_mid) and gc.get('voting') == 6
         and len(lowfill) >= 2 and nd.get(dcut) == 6 - len(lowfill) and all(n == 6 for d, n in nd.items() if d != dcut),
         'rc %d; G10v3 %s; late ratios %s; voting %s; %s under the fill line on %d windows, n %s; others\' n %s' % (
             rc, gates(rfc).get('G10v3'), [round(w.get('median_ratio') or 0, 2) for w in late], gc.get('voting'), dcut, len(lowfill),
             nd.get(dcut), sorted(set(n for d, n in nd.items() if d != dcut))))
    code67 = ("import json, sys\nsys.path.insert(0, sys.argv[1])\nimport lp_reg3 as R3\n"
              "wins = [dict(r0=0, c0=0, cell=[0, 0], demstd=5.0, fill=1.0, amp=1.0)]\n"
              "rd = dict(('2008%04d' % (101 + i), [dict(window=0, dx=0.01, dy=0.0, ratio=1.0 if i < 6 else 2.0, sigma=5.0, "
              "fill=0.5 if i < 6 else 1.0)]) for i in range(11))\n"
              "s = R3.g10v3_summary(256, wins, rd, dict((d, 'FBS') for d in rd), '20080001', 1000)\n"
              "print(json.dumps(dict(votes=s['windows'][0]['votes'], median=s['windows'][0]['median_ratio'], "
              "n=sorted(v['n'] for v in s['dates'].values()))))\n")
    j67, e67 = mockpy(code67, [S.HERE])
    case('M67d (17.4; the part 4 review\'s P4-01) G10 v3\'s vote is v2\'s: a window read on 11 dates, 6 at fill 0.5 and ratio 1.0, 5 at '
         'full fill and ratio 2.0: the median ratio over the 5 at fill 0.90 is 2.0 and the window votes; the 6 are not read there',
         bool(j67) and j67.get('votes') is True and j67.get('median') == 2.0 and j67.get('n') == [0] * 6 + [1] * 5,
         '%s %s' % (j67, e67))

    # M69: water over 7 of the 9 cells
    restore('m4', FR, 'mS2', 'M69')
    rc, _ = run('m4', ['--to', 'fine'], {'LINOG_MOCK_WATER': '1'})
    rf9, rt9 = rec('m4', '4d', 'fine'), rec('m4', '3a', 'topo')
    g9 = (rf9.get('outputs') or {}).get('g10v3') or {}
    case('M69 (17.9) water over 7 of the 9 cells (LINOG_MOCK_WATER: relief only in the first 256 samples of the early and mid bands): '
         'G10v3 NOT MEASURED (WARN), G10m NOT MEASURED (WARN), the 7 cells named; v2 PASS on the kit\'s 4 windows; fine PASS, rc 0',
         rc == 0 and rf9.get('verdict') == 'PASS' and gates(rf9).get('G10') == 'PASS' and gates(rf9).get('G10v3') == 'WARN'
         and 'NOT MEASURED' in gval(rf9, 'G10v3') and gates(rf9).get('G10m') == 'WARN' and len(g9.get('named') or []) == 7,
         'rc %d; fine %s; G10 %s; G10v3 %s; named %s; topo\'s G3a.14 %s' % (rc, rf9.get('verdict'), gates(rf9).get('G10'),
                                                                         gval(rf9, 'G10v3')[:90], g9.get('named'),
                                                                         gval(rt9, 'G3a.14')[:80]))

    # M70: one date moved 3 samples after run_06
    d70 = [d for d in FBS if d != REF][0]
    restore('m4', FR, 'mS4c', 'M70')
    rc, _ = run('m4', ['--to', 'fine'], {'LINOG_MOCK_FINESHIFT': '%s:3' % d70})
    r70 = rec('m4', '4d', 'fine')
    v70 = (((r70.get('outputs') or {}).get('g10v3') or {}).get('dates') or {}).get(d70) or {}
    case('M70 (17.8, 17.9) %s moved 3 samples after run_06 (LINOG_MOCK_FINESHIFT): v2 (G10) FAIL naming it, G10v3 WARN naming it at '
         'about +3, fine FAIL, rc 2; G10\'s note gives 17.8\'s way on' % d70,
         rc == 2 and r70.get('verdict') == 'FAIL' and gates(r70).get('G10') == 'FAIL' and d70 in gval(r70, 'G10')
         and 'the way on (17.8)' in gval(r70, 'G10') and gates(r70).get('G10v3') == 'WARN' and d70 in gval(r70, 'G10v3')
         and v70.get('dx') is not None and abs(v70['dx'] - 3.0) <= 0.1,
         'rc %d; G10 %s; %s dx %s' % (rc, gval(r70, 'G10')[:80], d70, v70.get('dx')))

    # M72: R9's limits, each on the frame after invert (datum alone: --only datum)
    p72 = PAIRS[len(PAIRS) // 2]
    restore('m4', FR, 'mS4b', 'M72a')
    m0 = dates_md5(W)
    for f in glob.glob(os.path.join(W, 'refineSecondaryTiming', 'pairs', p72, 'misreg*')):
        S.aside(T, f, 'M72a')
    rca, _ = run('m4', ['--only', 'datum'])
    ra = rec('m4', '4c', 'datum')
    oka = rca == 2 and gates(ra).get('G4c.8') == 'FAIL' and p72 in gval(ra, 'G4c.8') and 'G16' not in gates(ra) \
        and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4b', 'M72b')
    krb, ob_ = in_env(W, ['python3', '-B', '-c', EDIT, 'order1', os.path.join(W, 'refineSecondaryTiming', 'pairs', p72, 'misreg')])
    rcb, _ = run('m4', ['--only', 'datum'])
    rb_ = rec('m4', '4c', 'datum')
    okb = krb == 0 and rcb == 2 and gates(rb_).get('G4c.8') == 'FAIL' and 'not constant polynomials' in gval(rb_, 'G4c.8') \
        and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4b', 'M72c')
    b72 = p72.split('_')[1]
    krc, oc_ = in_env(W, ['python3', '-B', '-c', EDIT, 'slr', os.path.join(W, 'refineSecondaryTiming', 'pairs', p72, 'secondaryShelve',
                                                                           'data'), '1e-7'])
    rcc, _ = run('m4', ['--only', 'datum'])
    rc_ = rec('m4', '4c', 'datum')
    okc = krc == 0 and rcc == 2 and gates(rc_).get('G4c.8') == 'FAIL' and 'differs between its copies' in gval(rc_, 'G4c.8') \
        and b72 in gval(rc_, 'G4c.8') and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4b', 'M72d')
    grp = set(DATES[:2])
    rfp = os.path.join(W, 'status', 'P4a_refine.json')
    rr0 = json.load(open(rfp))
    cut = sorted(pr for pr in rr0['outputs']['misreg'] if len(set(pr.split('_')) & grp) == 1)
    for pr in cut:
        del rr0['outputs']['misreg'][pr]
    with open(rfp, 'w') as fh:
        json.dump(rr0, fh, indent=1)
    rcd0, _ = run('m4', ['--only', 'datum'])
    rd0 = rec('m4', '4c', 'datum')
    okd0 = cut and rcd0 == 2 and gates(rd0).get('G4c.8') == 'FAIL' and 'pairs/ holds %d folder(s)' % len(cut) in gval(rd0, 'G4c.8')
    for pr in cut:
        S.aside(T, os.path.join(W, 'refineSecondaryTiming', 'pairs', pr), 'M72d')
    rcd, _ = run('m4', ['--only', 'datum'])
    rd_ = rec('m4', '4c', 'datum')
    okd = okd0 and rcd == 2 and gates(rd_).get('G4c.8') == 'PASS' and gates(rd_).get('G4c.9') == 'FAIL' \
        and 'split' in gval(rd_, 'G4c.9') and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4c', 'M72e')
    a0, m1, k0 = (rec('m4', '4c', 'datum').get('outputs') or {}).get('after'), dates_md5(W), baks(W)
    rce, _ = run('m4', ['--only', 'datum', '--force', 'datum'])
    re_ = rec('m4', '4c', 'datum')
    oe = re_.get('outputs') or {}
    oke = rce == 0 and gates(re_).get('G4c.4') == 'PASS' and 'applied again' in gval(re_, 'G4c.4') and gates(re_).get('G16') == 'PASS' \
        and oe.get('after') == a0 and dates_md5(W) == m1 and baks(W) == k0 and len(k0) == 1 and oe.get('written') == 0 \
        and oe.get('already') == 12
    restore('m4', FR, 'mS4b', 'M72f')
    lgd = (rec('m4', '4a', 'refine').get('outputs') or {}).get('logdir')
    lgs = sorted(glob.glob(os.path.join(lgd or '/nonexistent', '*', '*_%s.log' % p72)))
    t0_ = open(lgs[-1]).read() if lgs else ''
    t1_ = re.sub(r'(rgratio, azratio:\s+)(\S+)', lambda mm: mm.group(1) + repr(float(mm.group(2)) * (1.0 + 1e-9)), t0_, count=1)
    if lgs:
        with open(lgs[-1], 'w') as fh:
            fh.write(t1_)
    rcf, _ = run('m4', ['--only', 'datum'])
    rf_ = rec('m4', '4c', 'datum')
    okf = bool(lgs) and t1_ != t0_ and rcf == 2 and gates(rf_).get('G4c.8') == 'FAIL' and 'run_04 printed' in gval(rf_, 'G4c.8') \
        and p72 in gval(rf_, 'G4c.8') and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4b', 'M72g')
    bad_cfg = os.path.join(T, 'cfg', 'run_badrefine.cfg')
    with open(bad_cfg, 'w') as fh:
        fh.write(re.sub(r'^REFINE_MD5=.*$', 'REFINE_MD5=' + '0' * 32, open(os.path.join(T, 'cfg', 'run_mock.cfg')).read(), flags=re.M))
    rcg, _ = run('m4', ['--only', 'datum'], {'LINOG_RUN_CFG': bad_cfg})
    rg9 = rec('m4', '4c', 'datum')
    okg = rcg == 2 and gates(rg9).get('G4c.3') == 'FAIL' and 'refineSecondaryTiming.py' in gval(rg9, 'G4c.3') \
        and 'G4c.8' not in gates(rg9) and dates_md5(W) == m0 and not baks(W)
    restore('m4', FR, 'mS4b', 'M72h')
    inv72 = (rec('m4', '4b', 'invert').get('outputs') or {}).get('md5s')
    mark = os.path.join(T, 'r9_72h.mark')
    ph = subprocess.Popen(['bash', S.ENTRY, '084', FR, '--decide', 'auto', '--to', 'datum'], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, start_new_session=True,
                          env=popen_env('m4', FR, {'LINOG_MOCK_R9SLEEP': '3', 'LINOG_MOCK_MARK': mark}))
    t0 = time.time()
    while not os.path.exists(mark) and ph.poll() is None and time.time() - t0 < 300:
        time.sleep(0.2)
    time.sleep(0.5)
    if ph.poll() is None:
        os.killpg(ph.pid, signal.SIGTERM)
    outh = ph.communicate(timeout=300)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 %s --to datum (m4, LINOG_MOCK_R9SLEEP, SIGTERM during R9\'s write) rc %d\n%s' % (
            FR, ph.returncode, outh))
    rh = rec('m4', '4c', 'datum')
    oh = rh.get('outputs') or {}
    nowh, kh = dates_md5(W), baks(W)
    rch, _ = run('m4', ['--to', 'datum'])
    rh2 = rec('m4', '4c', 'datum')
    ah2 = (rh2.get('outputs') or {}).get('after') or {}
    eh2 = max((max(abs(ah2[d][0] - ch['own'][d][0]), abs(ah2[d][1] - ch['own'][d][1])) for d in DATES if d in ah2), default=None)
    hist = sorted(os.listdir(os.path.join(W, 'status', 'history'))) if os.path.isdir(os.path.join(W, 'status', 'history')) else []
    okh = os.path.exists(mark) and ph.returncode == 143 and rh.get('verdict') == 'ERROR' and oh.get('md5s_after') == nowh \
        and oh.get('md5s_before') == inv72 and oh.get('written') == 12 and len(kh) == 1 and rch == 0 and rh2.get('verdict') == 'PASS' \
        and 'the run of' in gval(rh2, 'G4c.4') and 'applied again' in gval(rh2, 'G4c.4') and baks(W) == kh \
        and dates_md5(W) == nowh and eh2 is not None and eh2 <= 1e-9 and any(x.startswith('P4c_datum.') for x in hist)
    case('M72 (17.9) R9\'s limits, datum alone on the frame after invert: (a) pair %s\'s shelve missing: G4c.8 FAIL naming it; (b) its '
         'rgpoly at range order 1: G4c.8 FAIL; (c) its secondaryShelve copy\'s SLR 1e-7 off: G4c.8 FAIL naming %s; each rc 2 with '
         'dates/ unchanged and no copy made; (d) refine\'s pair list cut between two dates and the rest: G4c.8 FAIL while pairs/ holds '
         'the cut folders (P4-14), then G4c.9 FAIL; (e) datum forced again after PASS: G4c.4 PASS (applied again), G16 PASS, the same '
         'values, no byte of dates/ changed, the one copy; (f) run_04\'s printed rgratio of %s off by 1e-9 (relative): G4c.8 FAIL '
         '(P4-06); (g) refineSecondaryTiming.py\'s pin changed: G4c.3 FAIL before any reading (P4-05: the build\'s G4c.3, not 17.3\'s '
         'G4c.2); (h) SIGTERM while R9 writes (the hook LINOG_MOCK_R9SLEEP): rc 143, datum ERROR with md5s_after = dates/ and its '
         'one copy; the next run: G4c.4 finds the complete apply, R9 applied again, PASS, the truth within 1e-9, the ERROR record '
         'kept in status/history/ (P4-10)' % (p72, b72, p72),
         oka and okb and okc and okd and oke and okf and okg and okh,
         '(a) %s rc %d %s; (b) %s rc %d %s; (c) %s rc %d %s; (d) %s rc %d, %d then %s; (e) %s rc %d, written %s already %s; (f) %s rc %d %s; '
         '(g) %s rc %d %s; (h) %s rc %s %s then %d %s' % (
             oka, rca, gates(ra).get('G4c.8'), okb, rcb, gval(rb_, 'G4c.8')[:60], okc, rcc, gval(rc_, 'G4c.8')[:60], okd, rcd,
             len(cut), gval(rd_, 'G4c.9')[:50], oke, rce, oe.get('written'), oe.get('already'), okf, rcf, gval(rf_, 'G4c.8')[-90:],
             okg, rcg, gval(rg9, 'G4c.3')[:70], okh, ph.returncode, rh.get('verdict'), rch, gval(rh2, 'G4c.4')[:70]))

    # M98 and M14b: igram on the frame after fine, with bgrid run first
    restore('m4', FR, 'mS4d', 'M98')
    rc0, _ = run('m4', ['--to', 'bgrid'])
    xf = os.path.join(W, 'SLC', REF, '%s.slc.xml' % REF)
    xs = open(xf).read()
    other = os.path.join(T, 'm98', '%s.slc' % REF)
    os.makedirs(os.path.dirname(other), exist_ok=True)
    os.link(os.path.join(W, 'SLC', REF, '%s.slc' % REF), other)
    shutil.copy2(xf, os.path.join(T, 'm98', '%s.slc.xml.orig' % REF))
    with open(xf, 'w') as fh:
        fh.write(re.sub(r'(name="file_name">\s*<value>)[^<]*(</value>)', lambda mm: mm.group(1) + other + mm.group(2), xs))
    rc1, _ = run('m4', ['--only', 'igram'])
    r98 = rec('m4', '4f', 'igram')
    shutil.copy2(os.path.join(T, 'm98', '%s.slc.xml.orig' % REF), xf)
    case('M98 (21.4) the reference\'s .slc.xml FILE_NAME naming another file of the same size (a hard link outside the frame): igram '
         'FAIL at G17 (crossmul would open that file\'s .vrt), rc 2, run_08 not run',
         rc0 == 0 and rc1 == 2 and gates(r98).get('G17') == 'FAIL' and 'names %s' % other in gval(r98, 'G17')
         and not os.path.isdir(os.path.join(W, 'Igrams')),
         'bgrid rc %d; igram rc %d; G17 %s' % (rc0, rc1, gval(r98, 'G17')[:160]))
    rc2, _ = run('m4', ['--only', 'igram'], {'LINOG_MOCK_G11_SLC': '1'})
    r14 = rec('m4', '4f', 'igram')
    case('M14b (4.8) the census given SLC as --fbs-dir (v0.12\'s call; the hook LINOG_MOCK_G11_SLC): it counts all 12 dates FBS, G11m '
         'FAIL against recon/modes.json\'s 8, rc 2',
         rc2 == 2 and gates(r14).get('G11') == 'PASS' and gates(r14).get('G11m') == 'FAIL'
         and ((r14.get('outputs') or {}).get('g11') or {}).get('fbs_census') == 12,
         'rc %d; G11m %s' % (rc2, gval(r14, 'G11m')[:140]))

    # =============================================================================== the FBD-only frame 3364
    WF = fd('f4', FR_FBD)
    rcs = []
    for to in ('stack2', 'datum'):
        rc, _ = run('f4', ['--to', to], frame=FR_FBD)
        rcs.append(rc)
        if rc != 0:
            break
    snap('f4', FR_FBD, 'fS4c')
    rjf = refjson(WF)
    REFF = rjf.get('reference')
    MF = dict((d, r.get('mode')) for d, r in modes_of(WF).items())
    d81 = [d for d in sorted(MF) if d != REFF][1] if len(MF) > 2 else None
    for to in ('fine', 'igram'):
        if rcs[-1] != 0:
            break
        rc, _ = run('f4', ['--to', to], {'LINOG_MOCK_FINESHIFT': '%s:0.03' % d81}, frame=FR_FBD)
        rcs.append(rc)
    RF = dict((ph, rec('f4', i, ph, FR_FBD)) for i, ph in P34)
    PF = sorted((RF['refine'].get('outputs') or {}).get('misreg') or {})
    tf = (RF['topo'].get('outputs') or {}).get('g3a14') or {}
    odf = RF['datum'].get('outputs') or {}
    r9f = odf.get('r9') or {}
    chf, _ = chain(dict(dates=sorted(MF), modes=MF, ref=REFF, pairs=PF, v13=True)) if REFF and PF else (None, '')
    paz = max(abs(chf['own'][d][0] - chf['v12'][d][0]) for d in MF) if chf else None
    mdf = r9f.get('max_diff') or [None, None]
    case('M81e (18.5) the FBD-only full-height frame 3364 (6 dates, one at 1000 samples) to datum: rc 0; G3a.14 PASS (a gate 16 samples); '
         'datum as v0.12 (method G16, G4c.6 PASS, G16 PASS) with R9 as a reading: G4c.10 INFO, R9 equal in range within 1e-6 (one '
         'SLR); in azimuth R9 and v0.12 apart by the PRF ratios, the chain\'s prediction within 1e-9 (the part 4 review\'s P4-04)',
         rcs[:2] == [0, 0] and gates(RF['topo']).get('G3a.14') == 'PASS' and abs(tf.get('gate_samples', 0) - 16.0) < 1e-6
         and odf.get('method') == 'G16' and gates(RF['datum']).get('G4c.6') == 'PASS' and gates(RF['datum']).get('G16') == 'PASS'
         and gates(RF['datum']).get('G4c.10') == 'INFO' and None not in mdf and mdf[1] <= 1e-6 and paz is not None
         and paz > 1e-6 and abs(mdf[0] - paz) <= 1e-9 and len(MF) == 6 and set(MF.values()) == {'FBD'},
         'rc %s; G3a.14 %s; datum %s; max_diff %s, the chain\'s azimuth %s' % (rcs, gval(RF['topo'], 'G3a.14')[:80], odf.get('method'),
                                                                              mdf, paz))
    gvf = (RF['fine'].get('outputs') or {}).get('g10v3') or {}
    v81 = (gvf.get('dates') or {}).get(d81) or {}
    case('M81f (18.5) G10 v3 on the FBD-only frame with %s moved 0.03 samples after run_06: G10v3 INFO (every date within 0.0625: rho '
         '16 / 14), the date read at 0.03 within 0.01; G10m N/A (one mode); v2 PASS' % d81,
         len(rcs) == 4 and rcs[2] == 0 and gates(RF['fine']).get('G10v3') == 'INFO' and gates(RF['fine']).get('G10m') == 'N/A'
         and gates(RF['fine']).get('G10') == 'PASS' and v81.get('dx') is not None and abs(v81['dx'] - 0.03) <= 0.01
         and abs(gvf.get('rho', 0) - 16.0 / 14.0) < 1e-9,
         'rc %s; G10v3 %s; %s dx %s' % (rcs, gval(RF['fine'], 'G10v3')[:100], d81, v81.get('dx')))
    gif = gates(RF['igram'])
    g11f = (RF['igram'].get('outputs') or {}).get('g11') or {}
    case('M81h (18.5) igram on the FBD-only frame: Igrams 174 wide (1048 at 6 x 28 looks); G11 PASS with every pair FBD-FBD (%d); G11m '
         'PASS on "FBS dates 1" (the _none/ placeholder); G17 PASS' % len(PF),
         len(rcs) == 4 and rcs[3] == 0 and iwidth(WF, PF) == [174] and gif.get('G11') == 'PASS' and gif.get('G11m') == 'PASS'
         and gif.get('G17') == 'PASS' and g11f.get('fbs_census') == 1 and g11f.get('fbs_modes') == 0
         and g11f.get('classes') == dict(FBS=0, FBD=len(PF), MIXED=0)
         and sorted(os.listdir(g11f.get('fbs_dir') or '/nonexistent')) == ['_none'],
         'rc %s; widths %s; G11m %s' % (rcs, iwidth(WF, PF), gval(RF['igram'], 'G11m')[:120]))
    restore('f4', FR_FBD, 'fS4c', 'M81g')
    rc, _ = run('f4', ['--to', 'fine'], {'LINOG_MOCK_FINESHIFT': '%s:0.1' % d81}, frame=FR_FBD)
    rg_ = rec('f4', '4d', 'fine', FR_FBD)
    vg = (((rg_.get('outputs') or {}).get('g10v3') or {}).get('dates') or {}).get(d81) or {}
    case('M81g (18.5) %s moved 0.1 samples instead: G10v3 WARN naming it (over 0.0625), fine PASS (a reading), rc 0' % d81,
         rc == 0 and gates(rg_).get('G10v3') == 'WARN' and d81 in gval(rg_, 'G10v3') and vg.get('dx') is not None
         and abs(vg['dx'] - 0.1) <= 0.01 and rg_.get('verdict') == 'PASS',
         'rc %d; G10v3 %s; dx %s' % (rc, gval(rg_, 'G10v3')[:100], vg.get('dx')))
