#!/usr/bin/env python3
"""lp_selftest13p6.py -- linog_auto v0.13's part 6 cases that the first install (22-d) carries with parts 1 to 5: accept under
R9 and the FBD-only factor (the ascending record 18.5, 18.6), and the review package's prefix by the path's direction (11.13,
22-b); called by lp_selftest.py as the suite 13p6.

The frames, on 13p4's mock ground (LINOG_MOCK_V13=1):
  the mixed full-height frame 3354 from 13p4's archive v13mx (12 dates, 8 FBS and 4 FBD), recon to accept under --decide auto;
  an FBD-only full-height frame of 12 dates, 3364 from an archive of its own, v13fbd12 (the mixed frame's orbits, every
     granule FBD, 1048 samples but one at 1000): 18.5's M81 has 12 dates; 13p4's 6-date frame 3364 cannot pass admit (two of
     its dates in one pair: R3 thins them, which leaves 4, under min_dates 5; with the operator's file G5a.5 FAILs them).
Cases:
  M99 (11.13, 22-b) the package's prefix from linog_phase6.cfg: LINOG_DESC on a descending path, LINOG_ASC on an ascending
      one, the package's name and glob with it, a direction neither A nor D refused (lp_p6, in this Python);
  M84 (18.6) the mixed frame to accept (v0.13 r2: accept's LOGIC 3, part C's review items; it read 2 under r1): datum's method
      R9; the verifier copy's N22 and G16 PASS "by R9's plan", G6b.5 (8 FBS
      of 12) and G6b.6 PASS; one secondary's dates/ misreg moved 0.01 in range by hand after datum (the mock env's Python):
      accept forced again: N22 FAIL naming the date, G6b.6 FAIL, rc 2;
  M85 (18.5) the FBD-only frame to accept: datum as v0.12 (method G16); N22 PASS by G16's relation with factor 1 on its 11
      FBD secondaries, each date's range change the reference's shift, which the frame's own shelves give as not 0 (the kit's
      0.5 for every FBD date would want half of it), G6b.6 PASS.
"""
import json
import os
import re
import subprocess
import sys

import lp_selftest13p1 as P13

FR_MX, FR_FBD = '3354', '3364'
LF = 18432

# M99: the package's prefix (lp_p6), argv[1] the pipeline folder
CODE99 = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import lp_p6 as P6
q = P6.load_p6()
out = dict(d=P6.package_prefix(q, 'D'), a=P6.package_prefix(q, 'A'), a_low=P6.package_prefix(q, ' a '),
           name_a=P6.package_name('447', '0310', q, '20261018', 'A'), name_d=P6.package_name('084', '3320', q, '20261018', 'D'),
           glob_a=P6.package_glob('447', '0310', q, 'A'), glob_d=P6.package_glob('084', '3320', q, 'D'), version=q['PACKAGE_VERSION'],
           xfer=q['XFER'])
for x in ('X', '', None):
    try:
        P6.package_prefix(q, x)
        out['refused_%r' % (x,)] = 'no error'
    except ValueError as e:
        out['refused_%r' % (x,)] = str(e)
print(json.dumps(out))
'''

# The frame's misreg shelves in the mock env (Poly2D unpickles there): argv[1] the frame, argv[2] read | shift, argv[3] the
# date to shift, argv[4] the samples
SHELVES = r'''
import glob, json, os, shelve, sys
W = sys.argv[1]
R = os.path.join(W, 'refineSecondaryTiming')
def val(base):
    with shelve.open(base, 'r') as db:
        return [float(db['azpoly'].getCoeffs()[0][0]), float(db['rgpoly'].getCoeffs()[0][0])]
if sys.argv[2] == 'shift':
    base = os.path.join(R, 'dates', sys.argv[3], 'misreg')
    with shelve.open(base, 'w') as db:
        p = db['rgpoly']
        c = p.getCoeffs()[0][0]
        p.initPoly(rangeOrder=0, azimuthOrder=0, coeffs=[[c + float(sys.argv[4])]])
        db['rgpoly'] = p
    print(json.dumps(dict(shifted=sys.argv[3], by=float(sys.argv[4]))))
else:
    baks = sorted(glob.glob(os.path.join(R, 'dates_predatum_bak_*')))
    out = dict(post=dict((os.path.basename(os.path.dirname(p)), val(p[:-4])) for p in glob.glob(os.path.join(R, 'dates', '*', 'misreg.dat'))),
               pre=dict((os.path.basename(os.path.dirname(p)), val(p[:-4])) for p in glob.glob(os.path.join(baks[-1], '*', 'misreg.dat')))
               if baks else {})
    print(json.dumps(out))
'''


def phase13_6(T, case, S):
    print('-- v0.13 part 6 (the first install\'s subset): accept under R9 and the FBD-only factor, the package\'s prefix by the '
          'path\'s direction; the mixed frame 3354 and a 12-date FBD-only frame 3364 to accept (LINOG_MOCK_V13)')
    p = subprocess.run([sys.executable, '-B', '-c', CODE99, S.HERE], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'), 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        j = json.loads(p.stdout.decode())
    except ValueError:
        j = {}
    case('M99 (11.13, 22-b) the review package\'s prefix by the path\'s direction (linog_phase6.cfg\'s PACKAGE_PREFIX and '
         'PACKAGE_PREFIX_ASC): LINOG_DESC for D, LINOG_ASC for A (and " a "), the name _xfer/LINOG_ASC_P447F0310_v0.1_<day>_review '
         'and its glob for an ascending path, LINOG_DESC_P084F3320 for path 84 as v0.12; X, "" and None refused',
         j.get('d') == 'LINOG_DESC' and j.get('a') == 'LINOG_ASC' and j.get('a_low') == 'LINOG_ASC'
         and j.get('name_a') == 'LINOG_ASC_P447F0310_%s_20261018_review' % j.get('version')
         and j.get('name_d') == 'LINOG_DESC_P084F3320_%s_20261018_review' % j.get('version')
         and j.get('glob_a') == '%s/LINOG_ASC_P447F0310_%s_*_review' % (j.get('xfer'), j.get('version'))
         and j.get('glob_d') == '%s/LINOG_DESC_P084F3320_%s_*_review' % (j.get('xfer'), j.get('version'))
         and all('neither A nor D' in str(j.get(k)) for k in ("refused_'X'", "refused_''", 'refused_None')),
         '%s %s' % (j, p.stderr.decode('utf-8', 'replace')[-300:]))

    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M84-M85 not run: the mock ground needs numpy, and neither Python tried has it', False)
        return
    ORB = S.ORBITS[:12]
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    dem12 = re.search(r'^dem_3350 = (.+)$', base, re.M).group(1)
    with open(os.path.join(T, 'cfg', 'paths_p6v13.cfg'), 'w') as fh:
        fh.write(base.rstrip('\n') + '\n# v0.13 part 6: the full-height mock frames, on the same mock DEM\ndem_%s = %s\ndem_%s = %s\n' % (
            FR_MX, dem12, FR_FBD, dem12))
    full = dict(lines=LF, rows13=True)
    am = P13.make_variant(T, S, 'v13mx', dict((i, full) for i in range(12)), frame=FR_MX, orbs=ORB, fbd=S.FBD_3350)
    af = P13.make_variant(T, S, 'v13fbd12', dict((i, full) for i in range(12)), frame=FR_FBD, orbs=ORB, fbd=range(12),
                          width=lambda i: S.W_MX if i == 5 else S.W_MX + 48)
    if not am or not af:
        case('M84-M85 not run: the full-height mock archives could not be made (numpy)', False)
        return

    def run(root, frame, args, extra=None):
        e = {'LINOG_ROOT': os.path.join(T, root), 'LINOG_MOCK_V13': '1', 'LINOG_ARCHIVE': am if frame == FR_MX else af}
        e.update(extra or {})
        return S.run(T, ['084', frame, '--decide', 'auto'] + args, cfg='paths_p6v13.cfg', env_extra=e)

    def rec(root, frame, idx, ph):
        return S.rec(T, frame, idx, ph, root)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gval(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def vlines(r, tag):
        return [(v, t, x) for v, t, x in ((r or {}).get('outputs') or {}).get('lines') or [] if t == tag]

    def in_env(W, args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        env['LINOG_ENV_CFG'] = os.path.join(T, 'cfg', 'env_mock.cfg')
        q = subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh')] + args, cwd=W, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        out = q.stdout.decode('utf-8', 'replace')
        try:
            return q.returncode, json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return q.returncode, out[-600:]

    def modes_of(W):
        f = os.path.join(W, 'recon', 'modes.json')
        return dict((x['date'], x.get('mode')) for x in json.load(open(f)).get('dates', [])) if os.path.isfile(f) else {}

    # =============================================================================== M84: the mixed frame under R9
    W = S.fdir(T, FR_MX, 'r6')
    rc, _ = run('r6', FR_MX, ['--to', 'accept'])
    ra = rec('r6', FR_MX, '6b', 'accept')
    rdm = rec('r6', FR_MX, '4c', 'datum')
    n22, g16 = vlines(ra, 'N22'), vlines(ra, 'G16')
    MODES = modes_of(W)
    REF = (json.load(open(os.path.join(W, 'recon', 'reference.json'))) if os.path.isfile(os.path.join(W, 'recon', 'reference.json'))
           else {}).get('reference')
    ok1 = rc == 0 and ra.get('verdict') == 'PASS' and (rdm.get('outputs') or {}).get('method') == 'R9' and len(n22) == 1 \
        and n22[0][0] == 'PASS' and 'by R9\'s plan' in n22[0][2] and '7 FBS + 4 FBD secondaries, 0 off' in n22[0][2] \
        and any(v == 'PASS' and 'by R9\'s plan' in x for v, t, x in g16) and gates(ra).get('G6b.5') == 'PASS' \
        and '8 FBS of 12 dates' in gval(ra, 'G6b.5') and gates(ra).get('G6b.6') == 'PASS' and ra.get('logic') == 3   # r2: 3 (part C)
    d84 = [d for d in sorted(MODES) if d != REF and MODES[d] == 'FBD'][0] if MODES and REF else None
    rcs, js = in_env(W, ['python3', '-B', '-c', SHELVES, W, 'shift', d84 or '-', '0.01'])
    rc2, _ = run('r6', FR_MX, ['--only', 'accept', '--force', 'accept'])
    rb = rec('r6', FR_MX, '6b', 'accept')
    n22b = vlines(rb, 'N22')
    ok2 = rcs == 0 and isinstance(js, dict) and js.get('shifted') == d84 and rc2 == 2 and rb.get('verdict') == 'FAIL' \
        and len(n22b) == 1 and n22b[0][0] == 'FAIL' and '1 off by more than 1e-6' in n22b[0][2] and d84 in n22b[0][2] \
        and gates(rb).get('G6b.6') == 'FAIL' and d84 in gval(rb, 'G6b.6')
    case('M84 (18.6) the mixed full-height frame 3354 (8 FBS, 4 FBD) recon to accept under --decide auto: rc 0, datum\'s method R9, '
         'accept (LOGIC 3 since v0.13 r2) PASS with the verifier copy\'s N22 "by R9\'s plan" (7 FBS + 4 FBD secondaries, 0 off by more than 1e-6) '
         'and G16\'s azimuth by the plan, G6b.5 8 FBS of 12, G6b.6 PASS; %s\'s dates/ misreg moved 0.01 sample in range by hand: '
         'accept forced again: N22 FAIL naming it, G6b.6 FAIL, rc 2' % d84,
         ok1 and ok2,
         'rc %d accept %s logic %s; datum %s; N22 %s; G16 %s | edit rc %s %s; rc %d; N22 %s; G6b.6 %s' % (
             rc, ra.get('verdict'), ra.get('logic'), (rdm.get('outputs') or {}).get('method'), n22[:1], g16[-1:], rcs, js, rc2, n22b[:1],
             gval(rb, 'G6b.6')[:100]))

    # =============================================================================== M85: the FBD-only frame, G16 with factor 1
    WF = S.fdir(T, FR_FBD, 'f6')
    rc, _ = run('f6', FR_FBD, ['--to', 'accept'])
    rf = rec('f6', FR_FBD, '6b', 'accept')
    rdf = rec('f6', FR_FBD, '4c', 'datum')
    MF = modes_of(WF)
    REFF = (json.load(open(os.path.join(WF, 'recon', 'reference.json'))) if os.path.isfile(os.path.join(WF, 'recon', 'reference.json'))
            else {}).get('reference')
    rcr, sh = in_env(WF, ['python3', '-B', '-c', SHELVES, WF, 'read'])
    shift = None
    gotw = []
    if isinstance(sh, dict) and REFF in (sh.get('pre') or {}):
        shift = -sh['pre'][REFF][1]
        gotw = [abs((sh['post'][d][1] - sh['pre'][d][1]) - shift) for d in sh['post'] if d != REFF and d in sh['pre']]
    n22f = vlines(rf, 'N22')
    case('M85 (18.5) the 12-date FBD-only full-height frame 3364 recon to accept under --decide auto: rc 0, datum as v0.12 (method '
         'G16); accept PASS with N22 by G16\'s relation at factor 1 (11 FBD secondaries, 0 wrong), G6b.5 0 FBS of 12, G6b.6 PASS; '
         'from the frame\'s own shelves every secondary\'s range change is the reference\'s shift within 1e-4 and the shift is not 0 '
         '(the kit\'s 0.5 for every FBD date would FAIL each)',
         rc == 0 and rf.get('verdict') == 'PASS' and (rdf.get('outputs') or {}).get('method') == 'G16' and set(MF.values()) == {'FBD'}
         and len(MF) == 12 and len(n22f) == 1 and n22f[0][0] == 'PASS' and '0 FBS + 11 FBD secondaries, 0 wrong' in n22f[0][2]
         and gates(rf).get('G6b.5') == 'PASS' and '0 FBS of 12 dates' in gval(rf, 'G6b.5') and gates(rf).get('G6b.6') == 'PASS'
         and rcr == 0 and shift is not None and abs(shift) > 1e-3 and len(gotw) == 11 and max(gotw) <= 1e-4,
         'rc %d accept %s; datum %s; %d dates %s; N22 %s; shift %s, largest |change - shift| %s' % (
             rc, rf.get('verdict'), (rdf.get('outputs') or {}).get('method'), len(MF), sorted(set(MF.values())), n22f[:1], shift,
             max(gotw) if gotw else None))
