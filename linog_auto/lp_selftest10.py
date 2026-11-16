#!/usr/bin/env python3
"""lp_selftest10.py -- the v0.10 cases of the linog_auto self-test (T200 to T224), called by lp_selftest.py after the
Phase 5e and 6 cases (record 108.3, the rules approved in 109.0; the path table's entries of 109.3).

  T200 to T200h  admit's R3 and R2 as functions (lp_admit.r3, r2, network_md5) on an F3290-like network (7 dates, 11
                 pairs, 20110121 in one pair) and on small planted networks: the thin date, a dead date past the 25 %
                 limit, the cull refused for a date left with one pair, the 10 % cap at its boundary, the order of dead
                 dates, D1's reference, a network split; and on felix's F3310 and F3320 networks with the pairs RD10 found
                 flagged over land (F3310: 151 of 153, S31's operator file; F3320: 157).
  T201           R1's arithmetic on a synthetic frame (64 x 120 px, its sea 85 % of the grid, flat at 2 m; a block of no
                 height), in the mock env's Python (numpy, scipy): lp_admit's land, pair values and decision beside the
                 kit's own linog_admit.py on the same files. The whole grid's printout is the kit's, line for line (and a
                 changed threshold is caught); a pair random over the sea only is flagged over the whole grid and not over
                 land; a pair random over land, and one unwrapped only off the land, are flagged over land only.
  T202, T203     admit on the Phase 3 frame (p3): the land floor at felix's 50,000 px, at the mock's land count and one
                 pixel above it; a dead date (R3 past its limits under --decide auto, then the operator's file); T202b the
                 water tool off its pin; T224 the install's dry run of admit alone (v0.10's step 5b, v0.12's 5a).
  T204 to T211   a 6-date frame (p6d: 20061010, 690 days before 20080830, in one pair; 11 pairs), recon to igram, then
                 R3's thin date under ask and auto, and dfit (R4): LINOG_MOCK_RAMPDATE screens 20090602 over land,
                 LINOG_MOCK_TS gives the series a rate and that date a ramp, LINOG_MOCK_RMSOUT is MintPy's own outlier;
                 dfit's STALE map and deliver's G6a.1f; dfit run again with no candidate after it took one (its file
                 restored to MintPy's, or moved aside); a stop between dfit's write and its record (T209e); a failed
                 fit; the held file a stopped deliver leaves;
                 RUN_MANIFEST.json's velocity_fit and rules; the delivered velocities fit without the dates; a dry run of
                 the whole chain. v0.13 r3: after T211, the suite 13r3 (lp_selftest13r3.py) on the same frame and its
                 snapshot S6e (run whenever suite 10 runs, unless LINOG_SELFTEST_SUITES names 10 without 13r3); T209 and T210
                 read r3's words, label and LOGIC.
  T212 to T215   the driver's restart (R5) on a stub pipeline (linog_auto.sh and lp_common.py copied, every phase a
                 stub): one restart (LINOG_RESTART no after it), a second request refused (rc 4), an earlier request kept
                 aside, LINOG_RESTART by --only. v0.12: one restart per asking phase (the phase that asked then reads
                 LINOG_RESTART no, the others allowed); T212b drop1's restart and then d9ab's in one run; T213c drop1
                 asking twice (refused, rc 4). v0.13: M28 coarse's (R7), drop1's and d9ab's restarts in one run.
  T216 to T220   the path runner linog_path.sh: a dry run of two frames, the path table's frames by default, a real run
                 to stage, SIGTERM to the group and to the runner alone, Ctrl-C, the wrong host and usage errors.
  T221 to T223   the path table: p083, p086 and p087 against RD4's census, recon's fingerprint unchanged by a new
                 section, and the tag (recon's dry run of their 10 frames through linog_path.sh, mock granules at the
                 census's orbits, dates, widths and folders: rc 2 with G0.12 the only FAIL).
This module needs the standard library only; the HDF5 reads and R1's arithmetic run in the mock env's Python.
"""
import configparser
import datetime
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

FRAME = '3320'
P6D_ORBITS = [3778, 13843, 15185, 16527, 17869, 19211]   # 20061010, the Phase 3 frame's 4 dates, 20090902
THIN, RAMP, RMS = '20061010', '20090602', '20081130'
# RD4's census of felix (archive_range_window.tsv, 27 Sept 2026; record 109.3): (path, frame) -> [(orbit, date, width, folder)]
_P86 = [(13668, '20080818'), (25746, '20101124'), (26417, '20110109'), (27759, '20110411')]
CENSUS = {
    ('087', '3280'): [(7206, '20070602', 9344, '7'), (13916, '20080904', 9376, '17'), (14587, '20081020', 9344, '18')],
    ('087', '3290'): [(7206, '20070602', 9344, '7'), (13916, '20080904', 9344, '17'), (14587, '20081020', 9344, '19')],
    ('087', '3300'): [(7206, '20070602', 9344, '7'), (13916, '20080904', 9344, '17'), (14587, '20081020', 9344, '19')],
    ('086', '3280'): [(13668, '20080818', 9376, '17'), (25746, '20101124', 9344, '35'), (26417, '20110109', 9344, '36')],
    ('086', '3290'): [(13668, '20080818', 9344, '17'), (25746, '20101124', 9376, '35'), (26417, '20110109', 9344, '36'),
                      (27759, '20110411', 9344, '39')],
    ('086', '3300'): [(o, d, 9344, f) for (o, d), f in zip(_P86, ('17', '35', '36', '39'))],
    ('086', '3310'): [(13668, '20080818', 9344, '17'), (25746, '20101124', 9344, '35'), (26417, '20110109', 9376, '36'),
                      (27759, '20110411', 9376, '39')],
    ('083', '3300'): [(26344, '20110104', 9344, '36')],
    ('083', '3310'): [(26344, '20110104', 9376, '36')],
    ('083', '3320'): [(26344, '20110104', 9344, '36')],
}
# G0.12 on those frames as record 109.3 reads them from the census
G012 = {('087', f): '3, 20070602 to 20081020, largest gap 460 d' for f in ('3280', '3290', '3300')}
G012[('086', '3280')] = '3, 20080818 to 20110109, largest gap 828 d'
G012.update({('086', f): '4, 20080818 to 20110411, largest gap 828 d' for f in ('3290', '3300', '3310')})
G012.update({('083', f): '1, 20110104 to 20110104, largest gap - d' for f in ('3300', '3310', '3320')})

# RD10's rd10_pairs.tsv (felix, 5 Oct 2026, md5 f4c81d99; record 97): the networks of P084 F3310 and F3320 (dates; pairs as
# two letters, A the first date) and the pairs the kit's own rule flags over land (F3310: the two of S31's recon/admission.txt)
FELIX = {
    'F3310': ('20061010 20070528 20071013 20080113 20080228 20080414 20080530 20080715 20080830 20081130 20090302 20090602 20090902 '
              '20091018 20091203 20100305 20100420 20100605 20100721 20101021 20101206 20110121 20110308',
              'AC AH AI BC BD BE BF BG BH BI BK CD CE CF CG CH CI CJ CK CL CM DE DF DG DH DI DK DL DM DN DO EF EG EH EI EK EL EM EN EO FG '
              'FH FI FK FL FM FN FO FP GH GK GL GO GP GQ HI HJ HK HL HM HN HO HP HQ HR IJ IK IL IM IN IO IP IQ IR IS JK JL JM JN JO JP JR JS '
              'KL KM KN KO KP KQ KR KS KT KU LM LN LO LP LQ LR LS LT LU LV LW MN MO MP MQ MR MS MT NO NP NQ NR NS NT OP OQ OR OS OT OU OV OW '
              'PQ PR PS PT PU PV PW QR QS QT QU QV QW RS RT RU RV RW ST SU SV SW TU TV TW UV UW VW',
              ['20081130_20100721', '20090302_20101206']),
    'F3320': ('20061010 20061125 20070528 20071013 20080113 20080228 20080414 20080530 20080715 20080830 20081130 20090302 20090602 '
              '20090902 20091018 20091203 20100305 20100420 20100605 20100721 20101021 20101206 20110121 20110308',
              'AB AD AI AJ BJ CD CE CF CG CH CI CJ CL DE DF DG DH DI DJ DK DL DM DN EF EG EH EI EJ EK EL EM EN EO EP FG FH FI FJ FL FM FN '
              'FO FP GH GI GJ GL GM GN GO GP GQ HI HL HM HO HP HQ HR IJ IK IL IM IN IO IP IQ IR IS JK JL JM JN JO JP JQ JR JS JT KL KM KN KO '
              'KP KQ KS KT LM LN LO LP LQ LR LS LT LU LV MN MO MP MQ MR MS MT MU MV MW MX NO NP NQ NR NS NT NU OP OQ OR OS OT OU PQ PR PS PT '
              'PU PV PW PX QR QS QT QU QV QW QX RS RT RU RV RW RX ST SU SV SW SX TU TV TW TX UV UW UX VW VX WX', []),
}

PROBE10 = r'''
import hashlib, json, sys
what, args = sys.argv[1], sys.argv[2:]
import h5py, numpy as np
if what == 'dates':
    with h5py.File(args[0], 'r') as f:
        print(json.dumps([d.decode() if isinstance(d, bytes) else str(d) for d in f['date'][()]]))
elif what == 'drop':
    with h5py.File(args[0], 'r') as f:
        print(json.dumps(['%s_%s' % (x[0].decode(), x[1].decode()) for x, k in zip(f['date'][:], f['dropIfgram'][:]) if not k]))
elif what == 'vmd5':
    out = {}
    for p in args:
        with h5py.File(p, 'r') as f:
            out[p.rsplit('/', 1)[-1]] = hashlib.md5(np.ascontiguousarray(f['velocity'][()]).tobytes()).hexdigest()
    print(json.dumps(out))
'''

# R1 on a synthetic frame: lp_admit's functions beside the kit's own tool (the mock env's Python: numpy, scipy)
R1PROBE = r'''
import json, os, subprocess, sys
here, W, kitdir, pin_admit, pin_water = sys.argv[1:6]
sys.path.insert(0, here)
import numpy as np
import lp_admit as A
gw, gl, nland = 64, 120, 18
xmlt = ('<imageFile>\n  <property name="width">\n    <value>%d</value>\n  </property>\n  <property name="length">\n'
        '    <value>%d</value>\n  </property>\n</imageFile>\n')
os.makedirs(os.path.join(W, 'geom_reference'))
yy, xx = np.mgrid[0:gl, 0:gw].astype(float)
h = np.full((gl, gw), 2.0)                                   # the sea: flat at 2 m
h[:nland] = 30.0 + 0.5 * yy[:nland] + 0.3 * xx[:nland]       # land: lines 0 to 17, a slope (not flat to the water tool)
h[4:8, 20:24] = -1.0e6                                       # no height (|h| > 1e5)
h.astype('<f8').tofile(os.path.join(W, 'geom_reference', 'hgt.rdr'))
open(os.path.join(W, 'geom_reference', 'hgt.rdr.xml'), 'w').write(xmlt % (gw, gl))
dates = ['20080830', '20081130', '20090302', '20090602']
pairs = dict(p01=(0, 1), p02=(0, 2), p12=(1, 2), p13=(1, 3), p23=(2, 3))
names = {}
sea = np.zeros((gl, gw), bool)
sea[nland:] = True
for k, (i, j) in sorted(pairs.items()):
    pr = '%s_%s' % (dates[i], dates[j])
    names[k] = pr
    d = os.path.join(W, 'Igrams', pr)
    os.makedirs(d)
    ph = 2 * np.pi * 3.0 * xx / gw + 0.1 * j
    if k == 'p01':    # random over the sea only
        ph = np.where(sea, np.random.RandomState(11).uniform(-np.pi, np.pi, (gl, gw)), ph)
    if k == 'p23':    # random over land only
        ph = np.where(sea, ph, np.random.RandomState(12).uniform(-np.pi, np.pi, (gl, gw)))
    np.exp(1j * ph).astype('<c8').tofile(os.path.join(d, 'filt_%s.int' % pr))
    np.full((gl, gw), 0.6, '<f4').tofile(os.path.join(d, 'filt_%s.cor' % pr))
    cc = np.ones((gl, gw), np.uint8)
    cc[:2] = 0
    if k == 'p13':    # unwrapped only off the land
        cc[~sea] = 0
    cc.tofile(os.path.join(d, 'filt_%s_snaphu.unw.conncomp' % pr))
env, m, q = dict(KIT=kitdir), dict(KIT_ADMIT_MD5=pin_admit), dict(KIT_WATERMASK_MD5=pin_water)
kf = A.kit_functions(env, m, q)
L = A.land_of(W, gw, gl, kf['flat_masks'])
PV = A.read_pairs(W, L['land'], kf['conc'], gw, gl)
whole = dict((pr, v['whole']) for pr, v in PV.items())
land = dict((pr, v['land']) for pr, v in PV.items())
Kw, Kl = A.decide(whole, kf['defaults']), A.decide(land, kf['defaults'])
p = subprocess.run([sys.executable, os.path.join(kitdir, 'linog_admit.py'), '--dir', 'Igrams', '--width', str(gw), '--length', str(gl)],
                   cwd=W, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = p.stdout.decode('utf-8', 'replace')
kl = A.kit_lines(out)
print(json.dumps(dict(n=L['n'], defaults=kf['defaults'], conc_md5=kf['conc_md5'], flat_md5=kf['flat_masks_md5'], kit_rc=p.returncode,
                      kit_untrust=[u['pair'] for u in A.parse_kit(out)['untrustworthy']], names=names, whole_flagged=Kw['bad'],
                      land_flagged=Kl['bad'], mirror=A.mirror(Kw, kl), rows=len(Kw['rows']),
                      mirror_changed=A.mirror(A.decide(whole, dict(kf['defaults'], min_R=0.10)), kl),
                      R=dict((pr, [round(PV[pr]['whole']['R'], 3), round(PV[pr]['land']['R'], 3)]) for pr in PV),
                      lg=dict((pr, [round(PV[pr]['whole']['lg'], 3), round(PV[pr]['land']['lg'], 3)]) for pr in PV))))
'''

# the driver's restart (R5) on a stub pipeline: every phase this file
STUB = r'''#!/usr/bin/env python3
"""linog_auto self-test (lp_selftest10, the driver's restart and the runner): a stub phase. --state prints NONE; a run
appends its name, LINOG_RESTART and LINOG_DECIDE to <frame>/stub_trace.txt; as STUB_SLEEP_PHASE it writes STUB_MARK and
sleeps STUB_SLEEP_S seconds; as one of STUB_RESTART_PHASE (v0.12: a comma list), when LINOG_RESTART is allowed (or
STUB_RESTART_FORCE is set: a phase that asks all the same) and fewer than STUB_RESTART_TIMES restarts were asked by this
phase, it writes <frame>/status/restart.json as d9ab's R5 and drop1 do."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp_common as C
ph = os.path.basename(__file__)[3:-3]
a = sys.argv[1:]
path, frame = C.norm_path(a[a.index('--path') + 1]), C.norm_frame(a[a.index('--frame') + 1])
W = C.frame_dir(C.load_cfg(path), path, frame)
if '--rootcheck' in a:   # v0.13: the driver asks recon's G0.19 before it writes anything
    print('   G0.19   PASS     the root (stub pipeline)')
    sys.exit(0)
if '--state' in a:
    print('NONE')
    sys.exit(0)
with open(os.path.join(W, 'stub_trace.txt'), 'a') as fh:
    fh.write('%s %s %s\n' % (ph, os.environ.get('LINOG_RESTART', '-'), os.environ.get('LINOG_DECIDE', '-')))
if ph == os.environ.get('STUB_SLEEP_PHASE'):   # T219b: a phase that takes a while (its mark written first)
    import time
    open(os.environ['STUB_MARK'], 'w').write('%s %s\n' % (ph, frame))
    time.sleep(float(os.environ.get('STUB_SLEEP_S', '3')))
if ph in os.environ.get('STUB_RESTART_PHASE', '').split(',') and (os.environ.get('LINOG_RESTART') == 'allowed' or os.environ.get('STUB_RESTART_FORCE')):
    cf = os.path.join(W, 'stub_restarts_%s.txt' % ph)
    n = len(open(cf).read().split()) if os.path.isfile(cf) else 0
    if n < int(os.environ.get('STUB_RESTART_TIMES', '0')):
        open(cf, 'a').write('x\n')
        with open(os.path.join(W, 'status', 'restart.json'), 'w') as fh:
            json.dump(dict(reason='stub restart %d' % (n + 1), by=ph), fh)
print('stub %s' % ph)
'''


def listing(d):
    out = []
    for dp, dn, fn in os.walk(d):
        dn.sort()
        for n in sorted(fn):
            q = os.path.join(dp, n)
            st = os.lstat(q)
            out.append((os.path.relpath(q, d), st.st_size, st.st_mtime_ns))
    return out


def gates(r):
    return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))


def val(r, gid):
    return dict((x['id'], x.get('value', '')) for x in (r or {}).get('gates', [])).get(gid, '')


def jload(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return {}


def tsv(p):
    if not os.path.isfile(p):
        return []
    return [ln.split('\t') for ln in open(p).read().splitlines()[1:] if ln]


def phase10(T, case, S):
    import lp_selftest34 as S34
    import lp_admit as A
    mp = S.real_pins('linog_mintpy.cfg')
    q6 = S.real_pins('linog_phase6.cfg')
    py = S.MOCKPY[0]
    MCFG = os.path.join(T, 'cfg', 'mintpy_mock.cfg')
    host = socket.gethostname()

    def console(head, rc, out):
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## %s  rc %d\n%s' % (head, rc, out))

    def probe(code, *args):
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1',
               'MPLCONFIGDIR': os.path.join(T, 'mplconfig_probe')}
        p = subprocess.run([py, '-B', '-c', code] + [str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        try:
            return json.loads(p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': p.stdout.decode('utf-8', 'replace')[-600:]}

    def mcopy(name, **kv):
        dst = os.path.join(T, 'cfg', name)
        n = 0
        with open(dst, 'w') as fh:
            for ln in open(MCFG):
                k = ln.split('=', 1)[0]
                if k in kv:
                    ln, n = '%s=%s\n' % (k, kv[k]), n + 1
                fh.write(ln)
        assert n == len(kv), (name, kv, n)
        return dst

    # ------------------------------------------------------------------ T200: R3 and R2 as functions
    print('-- v0.10: admit\'s rules (R3, R2 as functions; R1 on a synthetic frame and on p3), a 6-date frame (R3, dfit\'s R4), the '
          'driver\'s restart (R5), the path runner, the path table\'s new entries and the tag')
    dead, exm, cap = float(mp['ADMIT_DEAD_SHARE']), float(mp['ADMIT_EXCL_MAX_FRAC']), float(mp['ADMIT_CULL_MAX_FRAC'])
    L = dict(zip('ABCDEFG', ('20061010', '20070528', '20080113', '20080715', '20080830', '20100420', '20110121')))

    def prs(s):
        return ['%s_%s' % (L[x[0]], L[x[1]]) for x in s.split()]
    net = prs('AD AE BC BD BE CD CE DE DF EF FG')
    dts = sorted(L.values())

    def r3(flags, ref=L['D'], dates=dts, pairs=net):
        return A.r3(dates, pairs, prs(flags), ref, 5, dead, exm)

    def order(r):
        return [x['date'] for x in r['excluded']]
    r = r3('')
    q2 = A.r2(r['pairs'], [], cap)
    case('T200 R3 on an F3290-like network (7 dates, 11 pairs, 20110121 in one pair; min_dates 5, the shipped ADMIT_DEAD_SHARE %g, '
         'ADMIT_EXCL_MAX_FRAC %g, ADMIT_CULL_MAX_FRAC %g), nothing flagged: 20110121 leaves as thin (1 pair), 6 dates and 10 pairs '
         'left, within the limits; R2 culls nothing; network_md5 independent of the pairs\' order' % (dead, exm, cap),
         (dead, exm, cap) == (0.5, 0.25, 0.10) and order(r) == [L['G']] and r['excluded'][0]['why'].startswith('thin: 1 pair ')
         and len(r['pairs']) == 10 and len(r['dates_left']) == 6 and r['ok'] and q2['cull'] == [] and not q2['taken']
         and A.network_md5(net) == A.network_md5(list(reversed(net))) and A.network_md5(net) != A.network_md5(net[1:]),
         'excluded %s; %d pairs, %d dates; ok %s; R2 %s' % (r['excluded'], len(r['pairs']), len(r['dates_left']), r['ok'], q2))
    r = r3('DF EF')
    case('T200b flags on both pairs of 20100420 once 20110121 is gone: 20110121 thin, then 20100420 dead (2 of its 2 pairs); 2 of 7 '
         'dates excluded (28.6 %), past the 25 % limit: not within R3\'s limits (a DECISION in admit)',
         order(r) == [L['G'], L['F']] and r['excluded'][1]['why'] == 'dead: 2 of its 2 pairs flagged over land (more than 0.5)'
         and not r['ok'] and r['problems'] == ['2 of 7 dates excluded (28.6 %), over 25 %'],
         'excluded %s; problems %s' % (order(r), r['problems']))
    r = r3('EF')
    q2 = A.r2(r['pairs'], prs('EF'), cap)
    case('T200c one of 20100420\'s two pairs flagged: not dead (1 of 2 is not more than half); R3 takes 20110121 only; R2\'s cull '
         '(1 of 10 pairs, at the cap) refused: 20100420 would be left with one pair',
         order(r) == [L['G']] and r['ok'] and q2['cull'] == prs('EF') and not q2['taken']
         and q2['why'] == 'dates left with fewer than 2 pairs: 20100420', 'R3 %s ok %s; R2 %s' % (order(r), r['ok'], q2))
    r = r3('DE')
    qa = A.r2(r['pairs'], prs('DE'), cap)
    r = r3('DE BC')
    qb = A.r2(r['pairs'], prs('DE BC'), cap)
    case('T200d R2\'s cap at its boundary: 1 of 10 pairs (10.0 %%) taken; 2 of 10 (20.0 %%) refused by the cap alone (%g)' % cap,
         qa['taken'] and qa['cull'] == prs('DE') and qa['why'] == '1 of 10 pairs (10.0 %), one component, every date in 2 pairs or more'
         and not qb['taken'] and qb['why'] == '2 of 10 pairs (20.0 %), over 10 %', '1 flag: %s | 2 flags: %s' % (qa, qb))
    ra, rb = r3('AD AE BC BD BE'), r3('AD AE DF EF')
    case('T200e the order of dead dates: the highest share first, then the most flagged (20070528, 3 of 3, before 20061010, 2 of 2), '
         'then the earliest (20061010 before 20100420, both 2 of 2); each re-read on the network as it stands',
         order(ra) == [L['G'], L['B'], L['A']] and order(rb) == [L['G'], L['A'], L['F']] and not ra['ok'] and not rb['ok'],
         'share/count: %s | earliest: %s' % (order(ra), order(rb)))
    r = r3('', ref=L['G'])
    case('T200f D1\'s reference date thin (20110121 as the reference): R3 not within its limits, the problem named',
         not r['ok'] and r['problems'] == ['D1\'s reference date 20110121 would be excluded'], 'problems %s' % r['problems'])
    D7 = ['20070101', '20070301', '20070501', '20070701', '20070901', '20071101', '20080101']
    M = dict(zip(('a1', 'a2', 'a3', 'x', 'b1', 'b2', 'b3'), D7))

    def prs2(s):
        return ['%s_%s' % (M[x.split('-')[0]], M[x.split('-')[1]]) for x in s.split()]
    net2 = prs2('a1-a2 a1-a3 a2-a3 a2-x a3-x x-b1 x-b2 b1-b2 b1-b3 b2-b3')
    rs = A.r3(D7, net2, prs2('a2-x a3-x x-b1'), M['a2'], 5, dead, exm)
    rt = A.r3(D7, net2, prs2('a2-x a3-x'), M['a2'], 5, dead, exm)
    qs = A.r2(rt['pairs'], prs2('a2-x a3-x'), 0.25)
    case('T200g two triangles joined by one date: that date dead (3 of its 4 pairs) leaves two components (R3 not within its limits, '
         'the only problem); with 2 of its 4 flagged it is not dead, and R2\'s cull of those 2 (20 %, under a cap of 25 %) is refused: '
         'the network would split', order(rs) == [M['x']] and rs['problems'] == ['the network left is in 2 components']
         and rt['ok'] and order(rt) == [] and not qs['taken'] and qs['why'] == 'the network left would be in 2 components',
         'dead: %s %s | R2: %s' % (order(rs), rs['problems'], qs))

    fx = {}
    for fr, (ds, ps, fl) in sorted(FELIX.items()):
        dd = ds.split()
        pp = ['%s_%s' % (dd[ord(x[0]) - 65], dd[ord(x[1]) - 65]) for x in ps.split()]
        rr = A.r3(dd, pp, fl, None, 5, dead, exm)   # no date leaves, so D1's reference is not in question
        qq = A.r2(rr['pairs'], fl, cap)
        fx[fr] = dict(dates=len(dd), pairs=len(pp), mindeg=min(A.degrees(pp).values()), r3=order(rr), ok=rr['ok'], cull=qq['cull'],
                      taken=qq['taken'], kept=len(A.kept_pairs(pp, rr['dates'], qq['cull'] if qq['taken'] else [])))
    case('T200h R3 and R2 on felix\'s networks with the pairs the kit flags over land (RD10\'s table): F3310 (23 dates, 153 pairs, min '
         'degree 3): no date thin or dead; the cull of its 2 pairs (1.3 %) taken: 151 of 153 kept, the 2 pairs S31\'s recon/admission.txt '
         'names; F3320 (24 dates, 157 pairs, min degree 2): nothing to exclude, 157 kept',
         fx['F3310'] == dict(dates=23, pairs=153, mindeg=3, r3=[], ok=True, cull=['20081130_20100721', '20090302_20101206'], taken=True, kept=151)
         and fx['F3320'] == dict(dates=24, pairs=157, mindeg=2, r3=[], ok=True, cull=[], taken=False, kept=157), '%s' % fx)

    # ------------------------------------------------------------------ T201: R1 on a synthetic frame
    WS = os.path.join(T, 'r1_synthetic')
    os.makedirs(WS)
    z = probe(R1PROBE, S.HERE, WS, os.path.join(T, 'kit'), mp['KIT_ADMIT_MD5'], q6['KIT_WATERMASK_MD5'])
    nm = z.get('names') or {}
    case('T201 R1 on a synthetic frame (64 x 120, the sea flat at 2 m on lines 18 to 119, land a slope on lines 0 to 17, 16 px of no '
         'height; the mock env\'s Python): land 1,136 px, water 6,528 (the sea), no height 16; the kit\'s thresholds from its argparse '
         'defaults (3.0, 0.20, 0.25); over the whole grid the printout is the kit\'s own line for line, and with min-R changed it is '
         'not; flagged over the whole grid: the pair random over the sea (as the kit); over land: the pair random over land and the '
         'one unwrapped only off the land (LARGEST 0)',
         z.get('n') == dict(grid=7680, water=6528, water_low=6528, water_high=0, land=1136, no_height=16)
         and z.get('defaults') == dict(screen_mult=3.0, min_largest=0.2, min_R=0.25) and z.get('kit_rc') == 0 and z.get('mirror') == []
         and z.get('rows') == 4 and len(z.get('mirror_changed') or []) > 0
         and z.get('whole_flagged') == [nm.get('p01')] and z.get('kit_untrust') == [nm.get('p01')]
         and sorted(z.get('land_flagged') or []) == sorted([nm.get('p13'), nm.get('p23')])
         and (z.get('lg') or {}).get(nm.get('p13'), [0, 1])[1] == 0.0,
         'land %s; kit rc %s, untrustworthy %s; whole %s, land %s; mirror %s, changed %d lines; R (whole, land) %s; LARGEST %s%s' % (
             z.get('n'), z.get('kit_rc'), z.get('kit_untrust'), z.get('whole_flagged'), z.get('land_flagged'), z.get('mirror'),
             len(z.get('mirror_changed') or []), z.get('R'), z.get('lg'), ' | ' + z['_error'] if '_error' in z else ''))

    # ------------------------------------------------------------------ T202, T203: admit on the Phase 3 frame
    W3 = S.fdir(T, FRAME, 'p3')

    def restore3(name, tag):
        S.aside(T, W3, 'p10_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', name), W3, symlinks=True, copy_function=S34.link_or_copy)

    def run3(args, extra=None, decide='auto', mcfg=MCFG):
        e = {'LINOG_ROOT': os.path.join(T, 'p3')}
        if mcfg:
            e['LINOG_MINTPY_CFG'] = mcfg
        e.update(extra or {})
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p3.cfg', env_extra=e)

    def r1of(r):
        return ((((r or {}).get('outputs') or {}).get('decisions') or {}).get('r1')) or {}
    if not os.path.isdir(os.path.join(T, 'snap_p3', 'S4e')):
        case('T202-T203 not run: no copy of the Phase 3 frame after bgrid (the Phase 3 and 4 cases stopped early)', False)
    else:
        PAIR = '20080830_20081130'
        restore3('S4e', 'T202')
        rc1, out = run3(['--to', 'admit'], {'LINOG_MOCK_BADPAIR': PAIR}, mcfg=None)
        a1 = S.rec(T, FRAME, '5a', 'admit', 'p3')
        n1 = (r1of(a1).get('land') or {}).get('land')
        rc2, out = run3(['--only', 'admit'], {'LINOG_MOCK_BADPAIR': PAIR}, mcfg=mcopy('mintpy_floor_above.cfg', ADMIT_LAND_MIN_PX=(n1 or 0) + 1))
        a2 = S.rec(T, FRAME, '5a', 'admit', 'p3')
        adm2 = jload(os.path.join(W3, 'recon', 'admission.json'))
        rc3, out = run3(['--only', 'admit'], {'LINOG_MOCK_BADPAIR': PAIR}, mcfg=mcopy('mintpy_floor_at.cfg', ADMIT_LAND_MIN_PX=n1 or 0))
        a3 = S.rec(T, FRAME, '5a', 'admit', 'p3')
        case('T202 R1\'s floor on p3 with a pair of random phase: at felix\'s 50,000 px the mock\'s land (%s px) is over it: G5a.6 INFO, '
             'the pair flagged over land and (v0.12) handed to drop1 (R2 INFO; v0.10 and v0.11: its cull refused by the cap, WARN), D3 '
             'nothing to exclude, 6 kept; '
             'at one pixel above the land: G5a.6 WARN, nothing flagged over land (the whole grid\'s 1 recorded), R2 PASS, '
             'admission.json under_floor true; at the land\'s own count: G5a.6 INFO again; rc 0 each' % n1,
             rc1 == 0 and rc2 == 0 and rc3 == 0 and n1 is not None and n1 >= 50000
             and gates(a1).get('G5a.6') == 'INFO' and r1of(a1).get('flagged') == [PAIR] and gates(a1).get('R2') == 'INFO'
             and gates(a1).get('D3') == 'PASS' and gates(a1).get('G5a.7') == 'PASS'
             and gates(a2).get('G5a.6') == 'WARN' and r1of(a2).get('flagged') == [] and r1of(a2).get('whole_flagged') == [PAIR]
             and gates(a2).get('R2') == 'PASS' and adm2.get('kept') == 6 and ((adm2.get('decisions') or {}).get('r1') or {}).get('under_floor') is True
             and gates(a3).get('G5a.6') == 'INFO' and r1of(a3).get('flagged') == [PAIR],
             'rc %d %d %d; land %s; G5a.6 %s %s %s; flagged over land %s %s %s; R2 %s %s; kept %s' % (
                 rc1, rc2, rc3, n1, gates(a1).get('G5a.6'), gates(a2).get('G5a.6'), gates(a3).get('G5a.6'), r1of(a1).get('flagged'),
                 r1of(a2).get('flagged'), r1of(a3).get('flagged'), gates(a1).get('R2'), gates(a2).get('R2'), adm2.get('kept')))
        restore3('S4e', 'T203')
        DD = '20090602'
        rc, out = run3(['--to', 'admit'], {'LINOG_MOCK_BADDATE': DD})
        ra = S.rec(T, FRAME, '5a', 'admit', 'p3')
        noadm = not os.path.exists(os.path.join(W3, 'recon', 'admission.json'))
        with open(os.path.join(W3, 'recon', 'admission.txt'), 'w') as fh:
            fh.write('# the operator excludes the dead date (self-test T203)\nmintpy.network.excludeDate = %s\n' % DD)
        rc2, out2 = run3(['--to', 'admit'], {'LINOG_MOCK_BADDATE': DD})
        rb = S.rec(T, FRAME, '5a', 'admit', 'p3')
        adm = jload(os.path.join(W3, 'recon', 'admission.json'))
        case('T203 every pair of 20090602 random (LINOG_MOCK_BADDATE): the kit\'s whole grid drops its 3 pairs (G20 PASS); R3: 20090602 '
             'dead (3 of 3), 3 dates left under min_dates 4: D3 DECISION under --decide auto too, rc 4, no admission.json; then '
             'recon/admission.txt names the date: R3 INFO, D3 INFO (the operator\'s, the rules agree), 3 pairs in one component (G5a.5 '
             'PASS), rc 0',
             rc == 4 and gates(ra).get('G20') == 'PASS' and gates(ra).get('R3') == 'DECISION' and gates(ra).get('D3') == 'DECISION'
             and '%s dead: 3 of its 3 pairs flagged over land' % DD in val(ra, 'R3') and 'under min_dates 4' in json.dumps(ra.get('gates'))
             and noadm and rc2 == 0 and gates(rb).get('R3') == 'INFO' and gates(rb).get('D3') == 'INFO' and 'agree' in val(rb, 'D3')
             and gates(rb).get('G5a.5') == 'PASS' and adm.get('kept') == 3 and adm.get('cfg', {}).get('mintpy.network.excludeDate') == DD,
             'rc %d; G20 %s; R3 %s: %s; D3 %s | rc %d; R3 %s, D3 %s (%s); kept %s' % (
                 rc, gates(ra).get('G20'), gates(ra).get('R3'), val(ra, 'R3')[:100], gates(ra).get('D3'), rc2, gates(rb).get('R3'),
                 gates(rb).get('D3'), val(rb, 'D3')[-60:], adm.get('kept')))

        # the water tool off its pin: admit stops before R1
        q6c = os.path.join(T, 'cfg', 'phase6_badwater.cfg')
        txt = open(os.path.join(S.HERE, 'linog_phase6.cfg')).read()
        assert txt.count('KIT_WATERMASK_MD5=%s\n' % q6['KIT_WATERMASK_MD5']) == 1
        open(q6c, 'w').write(txt.replace('KIT_WATERMASK_MD5=%s\n' % q6['KIT_WATERMASK_MD5'], 'KIT_WATERMASK_MD5=%s\n' % ('0' * 32)))
        restore3('S4f', 'T202b')
        rc, out = run3(['--only', 'admit'], {'LINOG_PHASE6_CFG': q6c})
        ra = S.rec(T, FRAME, '5a', 'admit', 'p3')
        case('T202b the water tool (linog_watermask.py, R1\'s land) off its pin in linog_phase6.cfg: admit FAIL at G5a.3w before the kit runs, '
             'rc 2; no admission.json', rc == 2 and gates(ra).get('G5a.3w') == 'FAIL' and 'G20' not in gates(ra)
             and not os.path.exists(os.path.join(W3, 'recon', 'admission.json')), 'rc %d; %s' % (rc, gates(ra)))
        # the install's dry run of admit on this frame (v0.10's step 5b, v0.12's 5a): admit alone
        restore3('S4f', 'T224')
        D5 = os.path.join(T, 'dry_p3_admit')
        l3 = listing(W3)
        rc, out = run3(['--only', 'admit', '--dry-run', D5])
        da = jload(os.path.join(D5, 'status', 'P5a_admit.json'))
        dj = jload(os.path.join(D5, 'recon', 'admission.json'))
        case('T224 the install\'s dry run of admit (v0.10\'s step 5b, v0.12\'s 5a) on the Phase 3 frame (linog_auto.sh 084 3320 --decide auto --only admit --dry-run DIR): rc 0; admit '
             'alone, PASS, with DIR/recon/admission.json (6 of 6 kept, the rules recorded); no other phase\'s record in DIR; the frame unchanged',
             rc == 0 and da.get('verdict') == 'PASS' and dj.get('kept') == 6 and ((dj.get('decisions') or {}).get('d3') or {}).get('rules', {}).get('kept') == 6
             and sorted(os.listdir(os.path.join(D5, 'status'))) == ['P5a_admit.json'] and listing(W3) == l3,
             'rc %d; admit %s; kept %s; records %s; frame unchanged %s' % (rc, da.get('verdict'), dj.get('kept'),
                                                                         sorted(os.listdir(os.path.join(D5, 'status'))) if os.path.isdir(os.path.join(D5, 'status')) else None,
                                                                         listing(W3) == l3))

    # ------------------------------------------------------------------ T204 to T211: the 6-date frame
    a6 = os.path.join(T, 'archive_p6d', 'alos')
    for orb in P6D_ORBITS:
        S.mkzip(os.path.join(a6, '31'), orb, FRAME, width=S.P3_WIDTH, lines=S.P3_LINES)
    arc = os.path.join(T, 'archive', 'alos')
    base_cfg = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    assert base_cfg.count('archive = %s\n' % arc) == 1
    with open(os.path.join(T, 'cfg', 'paths_p6d.cfg'), 'w') as fh:
        fh.write(base_cfg.replace('archive = %s\n' % arc, 'archive = %s\n' % a6))
    W6 = S.fdir(T, FRAME, 'p6d')

    def run6(args, extra=None, decide='auto', keep_default=False):
        e = {'LINOG_ROOT': os.path.join(T, 'p6d'), 'LINOG_MINTPY_CFG': MCFG}
        e.update(extra or {})
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p6d.cfg', env_extra=e, keep_default=keep_default)

    def rec6(idx, ph):
        return S.rec(T, FRAME, idx, ph, 'p6d')

    def snap6(name):
        shutil.copytree(W6, os.path.join(T, 'snap_p6d', name), symlinks=True, copy_function=S34.link_or_copy)

    def restore6(name, tag):
        S.aside(T, W6, 'p6d_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p6d', name), W6, symlinks=True, copy_function=S34.link_or_copy)
    rcs = []
    for to, sn in (('stack2', None), ('bgrid', 'S6e'), ('igram', 'S6f')):
        rc, out = run6(['--to', to])
        rcs.append(rc)
        if rc != 0:
            break
        if sn:
            snap6(sn)
    s1, s2, rf = rec6('2a', 'stack1'), rec6('2c', 'stack2'), jload(os.path.join(W6, 'recon', 'reference.json'))
    nig = len(glob.glob(os.path.join(W6, 'Igrams', '*', 'filt_*.int')))
    built = rcs == [0, 0, 0] and os.path.isdir(os.path.join(T, 'snap_p6d', 'S6f'))
    case('T204 the 6-date frame p6d (20061010 with the Phase 3 frame\'s dates and 20090902), recon to igram under --decide auto: rc 0 '
         'at stack2, bgrid and igram; 11 pairs (20061010 in one, to 20080830: G2a.9 WARN names it, degree 1); D1\'s reference %s; '
         '11 interferograms' % rf.get('reference'),
         built and (s2.get('outputs') or {}).get('pairs') == 11 and gates(s1).get('G2a.9') == 'WARN' and '%s degree 1' % THIN in val(s1, 'G2a.9')
         and rf.get('reference') not in (None, THIN, RAMP) and nig == 11,
         'rc %s; pairs %s; G2a.9 %s %s; reference %s; %d interferograms' % (rcs, (s2.get('outputs') or {}).get('pairs'),
                                                                           gates(s1).get('G2a.9'), val(s1, 'G2a.9'), rf.get('reference'), nig))
    if not built:
        case('T205-T211 not run: the 6-date frame was not built to igram', False)
    else:
        TP = THIN + '_20080830'
        restore6('S6f', 'T205')
        rc, out = run6(['--to', 'admit'], decide='ask')
        ra = rec6('5a', 'admit')
        case('T205 R3\'s thin date under --decide ask: admit DECISION at D3 (the rules\' excludeDate = %s, 10 of 11 pairs kept), R3 INFO '
             'naming it (1 pair), G5a.5 PASS on the rules\' network, rc 4; no admission.json' % THIN,
             rc == 4 and ra.get('verdict') == 'DECISION' and gates(ra).get('D3') == 'DECISION' and gates(ra).get('R3') == 'INFO'
             and '%s thin: 1 pair in the network as it stands' % THIN in val(ra, 'R3') and 'excludeDate = %s' % THIN in val(ra, 'D3')
             and '10 of 11 pairs kept' in val(ra, 'D3') and gates(ra).get('G5a.5') == 'PASS'
             and not os.path.exists(os.path.join(W6, 'recon', 'admission.json')),
             'rc %d; admit %s; R3 %s; D3 %s' % (rc, ra.get('verdict'), val(ra, 'R3')[:90], val(ra, 'D3')[:120]))
        restore6('S6f', 'T206')
        rc, out = run6(['--to', 'sbas'])
        ra, rs = rec6('5a', 'admit'), rec6('5d', 'sbas')
        adm = jload(os.path.join(W6, 'recon', 'admission.json'))
        drop = probe(PROBE10, 'drop', os.path.join(W6, 'mintpy', 'inputs', 'ifgramStack.h5'))
        tsd = probe(PROBE10, 'dates', os.path.join(W6, 'mintpy', 'timeseries.h5'))
        case('T206 the same under --decide auto, to sbas: D3 INFO (the rules, --decide auto) excludeDate = %s, 10 of 11 kept; sbas PASS '
             'with the date\'s pair dropped in the stack and 5 dates in timeseries.h5, rc 0' % THIN,
             rc == 0 and gates(ra).get('D3') == 'INFO' and 'the rules R1 to R3 (--decide auto)' in val(ra, 'D3') and adm.get('kept') == 10
             and adm.get('cfg', {}).get('mintpy.network.excludeDate') == THIN and rs.get('verdict') == 'PASS' and drop == [TP]
             and isinstance(tsd, list) and len(tsd) == 5 and THIN not in tsd,
             'rc %d; D3 %s; kept %s; sbas %s; dropped %s; series %s' % (rc, val(ra, 'D3')[:110], adm.get('kept'), rs.get('verdict'), drop, tsd))

        # R4: 20090602 screened over land, the series' ramp on it
        PL = {'LINOG_MOCK_RAMPDATE': RAMP, 'LINOG_MOCK_TS': '2:%s:20' % RAMP}
        restore6('S6e', 'T207')
        rc, out = run6(['--to', 'dfit'], PL)
        ra, rd = rec6('5a', 'admit'), rec6('5f', 'dfit')
        od = rd.get('outputs') or {}
        tt = (od.get('tests') or [{}])[0]
        fd = os.path.join(W6, od.get('folder') or '-')
        fj = jload(os.path.join(fd, 'fit.json'))
        ex = open(os.path.join(W6, 'mintpy', 'exclude_date.txt')).read() if os.path.isfile(os.path.join(W6, 'mintpy', 'exclude_date.txt')) else None
        ff = (od.get('final_fit') or {})
        case('T207 R4: %s\'s pairs at 12 fringes (LINOG_MOCK_RAMPDATE: 4.0x the frame\'s median peak) and the series with 2 mm/yr and a '
             'ramp of 20 mm on that date (LINOG_MOCK_TS), to dfit: admit screens it over land and keeps it (R4 INFO), excludes %s (thin); '
             'sbas, d9ab and wmask PASS; dfit: A equals mintpy/velocity.h5 (G5f.6 PASS), B without the date has the lower std (R4.1 INFO), '
             'mintpy/exclude_date.txt written with it (G5f.7 INFO), fit.json and the three fits\' logs in dfit/<UTC>/, rc 0' % (RAMP, THIN),
             rc == 0 and RAMP in val(ra, 'R4') and '4.0x' in val(ra, 'R4') and (r1of(ra).get('screened') == [RAMP])
             and all(rec6(i, p).get('verdict') == 'PASS' for i, p in (('5d', 'sbas'), ('5dab', 'd9ab'), ('5e', 'wmask'), ('5f', 'dfit')))
             and gates(rd).get('G5f.5') == 'INFO' and gates(rd).get('G5f.6') == 'PASS' and gates(rd).get('R4.1') == 'INFO'
             and gates(rd).get('G5f.7') == 'INFO' and ex == RAMP + '\n' and od.get('taken') == [RAMP] and od.get('base') == []
             and tt.get('std_b') is not None and tt.get('std_a') is not None and tt['std_b'] < tt['std_a'] and fj.get('taken') == [RAMP] and fj.get('final') == [RAMP]
             and (ff.get('std_final') is not None and ff.get('std_final') < (ff.get('std_a') or 0))
             and all(os.path.isfile(os.path.join(fd, n)) for n in ('fit_A.log', 'fit_B_%s.log' % RAMP, 'fit_final.log')),
             'rc %d; R4 %s; dfit %s; tests %s; exclude_date.txt %r; final fit %s' % (
                 rc, val(ra, 'R4'), [(g, gates(rd).get(g)) for g in ('G5f.5', 'G5f.6', 'R4.1', 'G5f.7')], od.get('tests'), ex, ff))
        m0 = S34.md5q(os.path.join(W6, 'status', 'P5f_dfit.json'))
        rc, out = run6(['--to', 'dfit'])
        ok = rc == 0 and out.count('skip: PASS on record') == 27 and S34.md5q(os.path.join(W6, 'status', 'P5f_dfit.json')) == m0
        with open(os.path.join(W6, 'mintpy', 'exclude_date.txt'), 'a') as fh:
            fh.write(RMS + '\n')
        e5 = S34.md5q(os.path.join(W6, 'mintpy', 'exclude_date.txt'))
        rc2, out2 = run6(['--only', 'deliver'], PL)
        rv = rec6('6a', 'deliver')
        rc3, out3 = run6(['--to', 'dfit'], PL)
        rd = rec6('5f', 'dfit')
        case('T208 the run again to dfit: all 27 phases skipped (v0.13: bandlimit; v0.12: drop1 among them) (dfit CURRENT: exclude_date.txt as it wrote it), the record unchanged; '
             'a date added to mintpy/exclude_date.txt by hand: --only deliver FAILs at G6a.1f before the kit\'s script (rc 2); the run to '
             'dfit finds dfit STALE: the file read as MintPy\'s (%s and %s), no candidate left, A\'s mirror WARN (MintPy\'s velocity.h5 '
             'was fit with every date), the file left as it is, rc 0' % (RMS, RAMP),
             ok and rc2 == 2 and gates(rv).get('G6a.1f') == 'FAIL' and 'NOT as dfit left it' in val(rv, 'G6a.1f')
             and not os.path.exists(os.path.join(W6, 'mintpy', 'timeseries_demErr.h5')) and rc3 == 0 and 'P5f dfit: record STALE' in out3
             and (rd.get('outputs') or {}).get('base') == sorted([RMS, RAMP]) and (rd.get('outputs') or {}).get('candidates') == []
             and gates(rd).get('G5f.6') == 'WARN' and gates(rd).get('G5f.7') == 'PASS' and S34.md5q(os.path.join(W6, 'mintpy', 'exclude_date.txt')) == e5,
             'skip run %s; --only deliver rc %d, G6a.1f %s; to dfit rc %d, base %s, candidates %s, G5f.6 %s, G5f.7 %s' % (
                 ok, rc2, val(rv, 'G6a.1f')[:100], rc3, (rd.get('outputs') or {}).get('base'), (rd.get('outputs') or {}).get('candidates'),
                 gates(rd).get('G5f.6'), gates(rd).get('G5f.7')))
        restore6('S6e', 'T209')
        rc, out = run6(['--to', 'dfit'], {'LINOG_MOCK_RAMPDATE': RAMP})
        rd = rec6('5f', 'dfit')
        od = rd.get('outputs') or {}
        case('T209 the date screened but the series flat (no LINOG_MOCK_TS): B\'s std is not lower (0 and 0), so %s stays in the fit: '
             'R4.1 WARN, no mintpy/exclude_date.txt (G5f.7 PASS), dfit PASS, rc 0' % RAMP,
             rc == 0 and rd.get('verdict') == 'PASS' and gates(rd).get('R4.1') == 'WARN' and 'the date stays in both fits' in val(rd, 'R4.1')   # v0.13 r3's words
             and gates(rd).get('G5f.7') == 'PASS' and od.get('taken') == [] and od.get('candidates') == [RAMP]
             and not os.path.exists(os.path.join(W6, 'mintpy', 'exclude_date.txt')),
             'rc %d; R4.1 %s %s; G5f.7 %s' % (rc, gates(rd).get('R4.1'), val(rd, 'R4.1')[:120], gates(rd).get('G5f.7')))
        # an earlier run of dfit took a date; then admit leaves no candidate (its floor above the land: no screen) and dfit runs again
        FH = mcopy('mintpy_floor_huge.cfg', ADMIT_LAND_MIN_PX=10 ** 9)
        restore6('S6e', 'T209b')
        rc1, out = run6(['--to', 'dfit'], dict(PL, LINOG_MOCK_RMSOUT=RMS))
        ex1 = open(os.path.join(W6, 'mintpy', 'exclude_date.txt')).read().split() if os.path.isfile(os.path.join(W6, 'mintpy', 'exclude_date.txt')) else None
        rc2, out = run6(['--only', 'admit'], {'LINOG_MINTPY_CFG': FH})
        rc3, out3 = run6(['--only', 'dfit'], {'LINOG_MINTPY_CFG': FH})
        rd = rec6('5f', 'dfit')
        od = rd.get('outputs') or {}
        fd = os.path.join(W6, od.get('folder') or '-')
        ex3 = open(os.path.join(W6, 'mintpy', 'exclude_date.txt')).read().split() if os.path.isfile(os.path.join(W6, 'mintpy', 'exclude_date.txt')) else None
        bf = open(os.path.join(fd, 'exclude_date_before.txt')).read().split() if os.path.isfile(os.path.join(fd, 'exclude_date_before.txt')) else None
        case('T209b dfit run again after it took %s (beside MintPy\'s %s), with no candidate left (admit\'s floor above the land): the file '
             'is dfit\'s own by its record, so MintPy\'s %s alone is kept: exclude_date.txt written as %s (G5f.7 INFO, "back in the fit"), '
             'the earlier file kept as exclude_date_before.txt; the record\'s base %s, final %s' % (RAMP, RMS, RMS, RMS, RMS, RMS),
             rc1 == 0 and ex1 == [RMS, RAMP] and rc2 == 0 and rc3 == 0 and 'P5f dfit: record STALE' in out3 and od.get('candidates') == []
             and od.get('base') == [RMS] and od.get('final') == [RMS] and ex3 == [RMS] and bf == [RMS, RAMP]
             and gates(rd).get('G5f.7') == 'INFO' and '%s back in the fit' % RAMP in val(rd, 'G5f.7'),
             'rc %d %d %d; file %s -> %s; before %s; base %s final %s; G5f.7 %s' % (rc1, rc2, rc3, ex1, ex3, bf, od.get('base'), od.get('final'),
                                                                                val(rd, 'G5f.7')[:120]))
        # T209e: from T209b's end (the file dfit's own, MintPy's 20081130 alone), dfit takes 20090602 again; then the record is set
        # as a stop between the write and the record's update leaves it (a SIGTERM there): excl_md5_after still the file as the run
        # found it, excl_pending the write's md5, the verdict not PASS. The next run must find the file as its own by the pending md5
        exf = os.path.join(W6, 'mintpy', 'exclude_date.txt')
        rdl = lambda: open(exf).read().split() if os.path.isfile(exf) else None
        rc1, out = run6(['--only', 'admit'], PL)
        rc2, out = run6(['--only', 'dfit'], PL)
        ex2 = rdl()
        rp = os.path.join(W6, 'status', 'P5f_dfit.json')
        r9 = jload(rp)
        o9 = r9.setdefault('outputs', {})
        o9['excl_md5_after'] = hashlib.md5(('%s\n' % RMS).encode()).hexdigest()
        o9['excl_pending'] = {'md5': S34.md5q(exf)}
        r9['verdict'] = 'ERROR'
        r9['reason'] = 'stopped by a signal between the write of mintpy/exclude_date.txt and the record (self-test T209e)'
        with open(rp, 'w') as fh:
            json.dump(r9, fh, indent=1)
        rc3, out = run6(['--only', 'admit'], {'LINOG_MINTPY_CFG': FH})
        rc4, out4 = run6(['--only', 'dfit'], {'LINOG_MINTPY_CFG': FH})
        rd = rec6('5f', 'dfit')
        od = rd.get('outputs') or {}
        ex4 = rdl()
        case('T209e a stop between dfit\'s write of exclude_date.txt (%s and %s) and its record\'s update (the record set by hand as a '
             'SIGTERM there leaves it: excl_md5_after still the file as the run found it, excl_pending the write\'s md5, ERROR): the next '
             'run, with no candidate, finds the file as its own by the pending md5: MintPy\'s %s alone (A = velocity.h5, G5f.6 PASS), '
             'the file written as %s (G5f.7 INFO, "%s back in the fit"), excl_pending dropped' % (RMS, RAMP, RMS, RMS, RAMP),
             rc1 == 0 and rc2 == 0 and ex2 == [RMS, RAMP] and rc3 == 0 and rc4 == 0 and od.get('base') == [RMS] and od.get('final') == [RMS]
             and ex4 == [RMS] and gates(rd).get('G5f.6') == 'PASS' and gates(rd).get('G5f.7') == 'INFO'
             and '%s back in the fit' % RAMP in val(rd, 'G5f.7') and 'excl_pending' not in od and od.get('excl_md5_after') == S34.md5q(exf),
             'rc %d %d %d %d; file %s -> %s; base %s final %s; G5f.6 %s; G5f.7 %s; pending %s' % (
                 rc1, rc2, rc3, rc4, ex2, ex4, od.get('base'), od.get('final'), gates(rd).get('G5f.6'), val(rd, 'G5f.7')[:100],
                 od.get('excl_pending')))
        restore6('S6e', 'T209c')
        rc1, out = run6(['--to', 'dfit'], PL)
        rc2, out = run6(['--only', 'admit'], {'LINOG_MINTPY_CFG': FH})
        rc3, out3 = run6(['--only', 'dfit'], {'LINOG_MINTPY_CFG': FH})
        rd = rec6('5f', 'dfit')
        od = rd.get('outputs') or {}
        fd = os.path.join(W6, od.get('folder') or '-')
        bf = open(os.path.join(fd, 'exclude_date_before.txt')).read().split() if os.path.isfile(os.path.join(fd, 'exclude_date_before.txt')) else None
        rc4, out4 = run6(['--only', 'deliver'], {'LINOG_MINTPY_CFG': FH})
        rv = rec6('6a', 'deliver')
        vf = jload(os.path.join(W6, 'RUN_MANIFEST.json')).get('velocity_fit') or {}
        vm = probe(PROBE10, 'vmd5', os.path.join(W6, 'mintpy', 'velocity_ramp_demErr.h5'), os.path.join(W6, 'mintpy', 'velocity.h5'))
        case('T209c the same with MintPy writing no file: no date is out of the fit now, so the file dfit wrote is moved into '
             'dfit/<UTC>/exclude_date_before.txt (G5f.7 INFO), none left in mintpy/; deliver PASS (G6a.1f), the kit\'s velocity_ramp_demErr.h5 '
             'fit on every date (= MintPy\'s velocity.h5), RUN_MANIFEST.json\'s dates out of the fit none',
             rc1 == 0 and rc2 == 0 and rc3 == 0 and od.get('final') == [] and bf == [RAMP] and gates(rd).get('G5f.7') == 'INFO'
             and 'moved into' in val(rd, 'G5f.7') and not os.path.exists(os.path.join(W6, 'mintpy', 'exclude_date.txt'))
             and rc4 == 0 and gates(rv).get('G6a.1f') == 'PASS' and vm.get('velocity_ramp_demErr.h5') == vm.get('velocity.h5') is not None
             and vf.get('dates_out_of_fit') == [],
             'rc %d %d %d %d; final %s; before %s; G5f.7 %s; G6a.1f %s; velocities %s; out of the fit %s' % (
                 rc1, rc2, rc3, rc4, od.get('final'), bf, val(rd, 'G5f.7')[:100], gates(rv).get('G6a.1f'), vm, vf.get('dates_out_of_fit')))
        m5x = S34.md5q(os.path.join(W6, 'status', 'P5f_dfit.json'))
        rc5, out5 = run6(['--to', 'dfit', '--force', 'dfit'], {'LINOG_MINTPY_CFG': FH, 'LINOG_MOCK_P6FAIL': 'timeseries2velocity.py'})
        rd5 = rec6('5f', 'dfit')
        case('T209d dfit\'s fit A fails (timeseries2velocity.py exits 1): G5f.6 FAIL, rc 2; nothing written; the record still knows the '
             'file as the run before left it (base, excl_md5_after kept through the stop)',
             rc5 == 2 and gates(rd5).get('G5f.6') == 'FAIL' and m5x != S34.md5q(os.path.join(W6, 'status', 'P5f_dfit.json'))
             and (rd5.get('outputs') or {}).get('base') == [] and 'excl_md5_after' in (rd5.get('outputs') or {})
             and (rd5.get('outputs') or {}).get('excl_md5_after') is None and not os.path.exists(os.path.join(W6, 'mintpy', 'exclude_date.txt')),
             'rc %d; G5f.6 %s; outputs %s' % (rc5, gates(rd5).get('G5f.6'), dict((k, (rd5.get('outputs') or {}).get(k)) for k in ('base', 'excl_md5_after'))))
        restore6('S6e', 'T210')
        rc, out = run6(['--to', 'deliver'], dict(PL, LINOG_MOCK_RMSOUT=RMS))
        rd, rv = rec6('5f', 'dfit'), rec6('6a', 'deliver')
        od = rd.get('outputs') or {}
        fd = os.path.join(W6, od.get('folder') or '-')
        exl = open(os.path.join(W6, 'mintpy', 'exclude_date.txt')).read().split() if os.path.isfile(os.path.join(W6, 'mintpy', 'exclude_date.txt')) else None
        before = open(os.path.join(fd, 'exclude_date_before.txt')).read() if os.path.isfile(os.path.join(fd, 'exclude_date_before.txt')) else None
        man = jload(os.path.join(W6, 'RUN_MANIFEST.json'))
        vf = man.get('velocity_fit') or {}
        ru = ((man.get('decisions') or {}).get('d3') or {}).get('rules') or {}
        vm = probe(PROBE10, 'vmd5', os.path.join(W6, 'mintpy', 'velocity_ramp_demErr.h5'), os.path.join(fd, 'velocity_final.h5'),
                   os.path.join(W6, 'mintpy', 'velocity.h5'))
        case('T210 MintPy\'s own outlier %s too (LINOG_MOCK_RMSOUT: residual_RMS writes exclude_date.txt), to deliver: dfit\'s A excludes '
             'it and equals velocity.h5 (G5f.6 PASS), B excludes %s too and is taken; exclude_date.txt = the union, the earlier file kept as '
             'exclude_date_before.txt; deliver PASS (G6a.1f PASS); v0.13 r3: dfit\'s final fit (on its DEM-error loop\'s series) differs '
             'from the kit\'s velocity_ramp_demErr.h5 (sbas\'s series, every date in its DEM-error fit) and from velocity.h5, as on '
             'MintPy (r2 read them byte for byte equal); RUN_MANIFEST.json: velocity_fit (out of the fit %s and %s; MintPy\'s %s; R4 took '
             '%s), the rules (R3 excluded %s, thin; R4\'s candidate %s); deliver\'s record v0.13 r3, LOGIC 7 (v0.10\'s 4: the KMZs\' fixed '
             'times since, then drop1\'s decision; v0.13 r2: G6a.11\'s reading, LOGIC kept; v0.13 r3: chain A\'s DEM-error fit without the '
             'fit\'s dates)' % (
                 RMS, RAMP, RMS, RAMP, RMS, RAMP, THIN, RAMP),
             rc == 0 and od.get('base') == [RMS] and gates(rd).get('G5f.6') == 'PASS' and od.get('taken') == [RAMP] and exl == [RMS, RAMP]
             and before == RMS + '\n' and rv.get('verdict') == 'PASS' and gates(rv).get('G6a.1f') == 'PASS'
             and vm.get('velocity_final.h5') not in (None, vm.get('velocity.h5'), vm.get('velocity_ramp_demErr.h5'))   # v0.13 r3: below
             and vf.get('dates_out_of_fit') == [RMS, RAMP] and vf.get('mintpy_exclusions') == [RMS] and vf.get('r4_taken') == [RAMP]
             and vf.get('file') == 'mintpy/exclude_date.txt' and [x.get('date') for x in ((ru.get('r3') or {}).get('excluded') or [])] == [THIN]
             and ru.get('r4_candidates') == [RAMP] and rv.get('version') == 'linog_auto v0.13 r3 (2026-10-30)' and rv.get('logic') == 7,
             'rc %d; dfit base %s taken %s, G5f.6 %s; exclude_date.txt %s; before %r; deliver %s G6a.1f %s; velocities %s; velocity_fit %s; '
             'rules %s; deliver %s LOGIC %s' % (rc, od.get('base'), od.get('taken'), gates(rd).get('G5f.6'), exl, before, rv.get('verdict'),
                                                gates(rv).get('G6a.1f'), vm, dict((k, vf.get(k)) for k in ('dates_out_of_fit', 'mintpy_exclusions', 'r4_taken', 'file')),
                                                dict(r3=ru.get('r3'), r4=ru.get('r4_candidates')), rv.get('version'), rv.get('logic')))
        os.rename(os.path.join(W6, 'mintpy', 'exclude_date.txt'), os.path.join(W6, 'mintpy', '_exclude_date.hold'))   # a stopped deliver
        rc, out = run6(['--to', 'deliver'], dict(PL, LINOG_MOCK_RMSOUT=RMS))
        rd = rec6('5f', 'dfit')
        held = os.path.isfile(os.path.join(W6, 'mintpy', '_exclude_date.hold')) and not os.path.exists(os.path.join(W6, 'mintpy', 'exclude_date.txt'))
        os.rename(os.path.join(W6, 'mintpy', '_exclude_date.hold'), os.path.join(W6, 'mintpy', 'exclude_date.txt'))
        rc2, out2 = run6(['--to', 'deliver'], dict(PL, LINOG_MOCK_RMSOUT=RMS))
        rd2 = rec6('5f', 'dfit')
        case('T210b exclude_date.txt held in mintpy/_exclude_date.hold (as linog_phase6.sh leaves it when a deliver stops between its lines '
             '13 and 18): dfit STALE, DECISION at G5f.4h naming the move back, rc 4, nothing written, the record keeping what it knew of the '
             'file; moved back: dfit reads it as its own (MintPy\'s %s, R4\'s %s again), the file as it should be (G5f.7 PASS), deliver '
             'CURRENT, rc 0' % (RMS, RAMP),
             rc == 4 and gates(rd).get('G5f.4h') == 'DECISION' and 'mv -n' in json.dumps(rd.get('gates')) and held
             and (rd.get('outputs') or {}).get('base') == [RMS] and rc2 == 0 and (rd2.get('outputs') or {}).get('base') == [RMS]
             and (rd2.get('outputs') or {}).get('taken') == [RAMP] and gates(rd2).get('G5f.7') == 'PASS' and 'P6a deliver: record CURRENT' in out2,
             'rc %d then %d; G5f.4h %s; base %s then %s; G5f.7 %s' % (rc, rc2, gates(rd).get('G5f.4h'), (rd.get('outputs') or {}).get('base'),
                                                                    (rd2.get('outputs') or {}).get('base'), val(rd2, 'G5f.7')[:90]))
        D = os.path.join(T, 'dry_p6d')
        l0, g0 = listing(W6), S34.md5q(os.path.join(W6, 'logs', 'STATUS.txt'))
        rc, out = run6(['--dry-run', D], dict(PL, LINOG_MOCK_RMSOUT=RMS), keep_default=True)
        drs = sorted(glob.glob(os.path.join(D, 'status', 'P*.json')))
        dv = dict((os.path.basename(p), jload(p).get('verdict')) for p in drs)
        dd = jload(os.path.join(D, 'status', 'P5f_dfit.json'))
        ddo = dd.get('outputs') or {}
        case('T211 a dry run of the whole chain on the delivered frame (no --to, as the install\'s on felix): rc 0, 31 dry records (v0.11: '
             'rerun\'s; v0.12: drop1\'s; v0.13: bandlimit\'s), all '
             'PASS; dfit fits A and B under DIR/dfit/ (MintPy\'s %s as recorded, %s taken again: the file as it should be, G5f.7 PASS), '
             'nothing written in the frame (listing and ledger)' % (RMS, RAMP),
             rc == 0 and len(drs) == 31 and all(v == 'PASS' for v in dv.values()) and ddo.get('taken') == [RAMP] and ddo.get('base') == [RMS]
             and str(ddo.get('folder', '')).startswith('dfit/') and os.path.isfile(os.path.join(D, ddo.get('folder') or '-', 'fit.json'))
             and gates(dd).get('G5f.7') == 'PASS' and val(dd, 'G5f.7').startswith('as it should be, %s, %s' % (RMS, RAMP))
             and listing(W6) == l0 and S34.md5q(os.path.join(W6, 'logs', 'STATUS.txt')) == g0,
             'rc %d; %d records, not PASS: %s; dfit taken %s base %s; G5f.7 %s; frame unchanged %s' % (
                 rc, len(drs), dict((k, v) for k, v in dv.items() if v != 'PASS'), ddo.get('taken'), ddo.get('base'), val(dd, 'G5f.7')[:80],
                 listing(W6) == l0))
        # v0.13 r3: suite 13r3's cases on this frame (lp_selftest13r3.py: they need its snapshot S6e), unless the suites asked
        # for leave it out (LINOG_SELFTEST_SUITES without 13r3 but with 10)
        sw = [x for x in os.environ.get('LINOG_SELFTEST_SUITES', '').replace(' ', '').split(',') if x]
        if not sw or '13r3' in sw:
            import lp_selftest13r3
            try:
                lp_selftest13r3.phase13_r3(T, case, S, dict(run6=run6, rec6=rec6, restore6=restore6, W6=W6, PL=PL, RAMP=RAMP, RMS=RMS,
                                                            probe10=probe, PROBE10=PROBE10, MCFG=MCFG, FRAME=FRAME,
                                                            mcopy=mcopy))
            except Exception as e:  # noqa: BLE001
                import traceback
                case('v0.13 r3 cases (13r3) stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])

    # ------------------------------------------------------------------ T212 to T215: the driver's restart, on a stub pipeline
    SP = os.path.join(T, 'stubpipe')
    os.makedirs(SP)
    for n in ('linog_auto.sh', 'lp_common.py'):
        shutil.copy2(os.path.join(S.HERE, n), os.path.join(SP, n))
    with open(os.path.join(SP, 'lp_env.sh'), 'w') as fh:
        fh.write('#!/usr/bin/env bash\n# linog_auto self-test (lp_selftest10): the env phases of the stub pipeline on this host\'s python3\nexec "$@"\n')
    phases = re.search(r'^PHASES="([^"]*)"', open(os.path.join(S.HERE, 'linog_auto.sh')).read(), re.M).group(1).split()
    for ph in phases:
        with open(os.path.join(SP, 'lp_%s.py' % ph), 'w') as fh:
            fh.write(STUB)
    nd = phases.index('d9ab') + 1

    def srun(root, args, extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_') and not k.startswith('STUB_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths.cfg'), LINOG_AUTO_HOST=host, LINOG_ROOT=os.path.join(T, root))
        env.update(extra)
        p = subprocess.run(['bash', os.path.join(SP, 'linog_auto.sh'), '084', FRAME] + args, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        out = p.stdout.decode('utf-8', 'replace')
        console('stub pipeline: linog_auto.sh 084 %s %s  (LINOG_ROOT=%s, %s)' % (FRAME, ' '.join(args), root, extra), p.returncode, out)
        Wd = S.fdir(T, FRAME, root)
        tr = open(os.path.join(Wd, 'stub_trace.txt')).read().splitlines() if os.path.isfile(os.path.join(Wd, 'stub_trace.txt')) else []
        led = open(os.path.join(Wd, 'logs', 'STATUS.txt')).read() if os.path.isfile(os.path.join(Wd, 'logs', 'STATUS.txt')) else ''
        runs = re.findall(r'auto_run START id=(\S+)', led)
        return p.returncode, out, tr, led, (runs[-1] if runs else '-'), Wd
    rc, out, tr, led, rid, Wd = srun('root_stub1', [], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='1'))
    rk = jload(os.path.join(Wd, 'status', 'restart_%s_1.json' % rid))
    case('T212 the driver\'s restart (R5) on a stub pipeline (%d phases, drop1 after sbas, dfit after wmask; d9ab asks a restart once): '
         'rc 0; the phases to d9ab with LINOG_RESTART=allowed, then all %d from the top, d9ab with LINOG_RESTART=no and the others '
         'allowed (v0.12: one restart per asking phase; %d runs); the ledger has one "auto_run RESTART id=<run> after=d9ab '
         'record=restart_<run>_1.json" and one END rc=0; the request kept as status/restart_<run>_1.json, none left as '
         'status/restart.json (v0.13: bandlimit after rwin, 31 phases)' % (len(phases), len(phases), nd + len(phases)),
         len(phases) == 31 and phases[phases.index('rwin') + 1] == 'bandlimit' and phases[-1] == 'rerun' and phases[phases.index('sbas') + 1] == 'drop1' and phases[phases.index('drop1') + 1] == 'd9ab'
         and phases[phases.index('wmask') + 1] == 'dfit' and phases[phases.index('dfit') + 1] == 'deliver'
         and rc == 0 and len(tr) == nd + len(phases)
         and [x.split()[1] for x in tr] == ['allowed'] * nd + [('no' if p == 'd9ab' else 'allowed') for p in phases]
         and [x.split()[0] for x in tr] == phases[:nd] + phases and led.count('auto_run RESTART id=%s after=d9ab record=restart_%s_1.json' % (rid, rid)) == 1
         and led.count('auto_run RESTART') == 1 and led.count('auto_run END id=%s rc=0' % rid) == 1 and rk.get('reason') == 'stub restart 1'
         and not os.path.exists(os.path.join(Wd, 'status', 'restart.json')) and '== RESTART after P5dab d9ab: stub restart 1' in out,
         'rc %d; %d phases; %d runs; restarts in the ledger %d; record %s' % (rc, len(phases), len(tr), led.count('auto_run RESTART'), rk))
    rc, out, tr, led, rid, Wd = srun('root_stub2', [], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='2', STUB_RESTART_FORCE='1'))
    case('T213 a second restart asked in the same run all the same (a phase that asks with LINOG_RESTART=no): refused, rc 4; the phases '
         'to d9ab twice (%d runs); the ledger "auto_run RESTART REFUSED ... record=restart_<run>_2.json" and END rc=4; both requests kept '
         'in status/' % (2 * nd),
         rc == 4 and len(tr) == 2 * nd and 'auto_run RESTART REFUSED id=%s after=d9ab record=restart_%s_2.json' % (rid, rid) in led
         and led.count('auto_run END id=%s rc=4' % rid) == 1 and os.path.isfile(os.path.join(Wd, 'status', 'restart_%s_1.json' % rid))
         and os.path.isfile(os.path.join(Wd, 'status', 'restart_%s_2.json' % rid))
         and '== STOPPED after P5dab d9ab, rc 4: a second restart asked by d9ab in one run (stub restart 2)' in out,
         'rc %d; %d runs; ledger %s' % (rc, len(tr), [x[22:] for x in led.splitlines() if 'RESTART' in x or 'END id' in x]))
    rc, out, tr, led, rid, Wd = srun('root_stub2b', [], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='2'))
    case('T213b the same phase able to ask twice, as d9ab is: after the first restart LINOG_RESTART is no, so it asks no second one '
         '(d9ab would ask the operator): one RESTART line, the second pass to package, rc 0 (%d runs)' % (nd + len(phases)),
         rc == 0 and len(tr) == nd + len(phases) and led.count('auto_run RESTART') == 1 and 'REFUSED' not in led
         and not os.path.exists(os.path.join(Wd, 'status', 'restart_%s_2.json' % rid)),
         'rc %d; %d runs; ledger restarts %d' % (rc, len(tr), led.count('auto_run RESTART')))
    W0 = S.fdir(T, FRAME, 'root_stub3')
    os.makedirs(os.path.join(W0, 'status'))
    with open(os.path.join(W0, 'status', 'restart.json'), 'w') as fh:
        json.dump(dict(reason='left by a run that ended before its driver read it (self-test T214)'), fh)
    rc, out, tr, led, rid, Wd = srun('root_stub3', [], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='0'))
    ks = jload(os.path.join(Wd, 'status', 'restart_stale_%s.json' % rid))
    case('T214 a restart request left by an earlier run: kept aside as status/restart_stale_<run>.json before the first phase; this run '
         'does not restart (%d runs, no RESTART line), rc 0' % len(phases),
         rc == 0 and 'self-test T214' in ks.get('reason', '') and not os.path.exists(os.path.join(Wd, 'status', 'restart.json'))
         and len(tr) == len(phases) and 'RESTART' not in led and 'restart request kept as status/restart_stale_%s.json' % rid in out,
         'rc %d; kept %s; %d runs' % (rc, ks, len(tr)))
    rc, out, tr, led, rid, Wd = srun('root_stub4', ['--only', 'd9ab'], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='1'))
    rc2, out2, tr2, led2, rid2, Wd = srun('root_stub4', ['--to', 'd9ab'], dict(STUB_RESTART_PHASE='d9ab', STUB_RESTART_TIMES='1'))
    case('T215 --only d9ab: LINOG_RESTART=no for the phase (d9ab asks no restart then), one run, rc 0; then --to d9ab: LINOG_RESTART=allowed, '
         'the restart taken and the second pass ends at d9ab (--to), d9ab then with no and the phases before it with allowed (v0.12), rc 0',
         rc == 0 and [x.split()[:2] for x in tr] == [['d9ab', 'no']] and 'RESTART' not in led and rc2 == 0
         and [x.split()[:2] for x in tr2[1:]] == [[p, 'allowed'] for p in phases[:nd]] + [[p, 'no' if p == 'd9ab' else 'allowed'] for p in phases[:nd]]
         and led2.count('auto_run RESTART id=%s after=d9ab' % rid2) == 1,
         '--only: rc %d, %s | --to: rc %d, %d runs after it' % (rc, tr, rc2, len(tr2) - 1))
    # v0.12: drop1 and d9ab, each one restart a run
    n1 = phases.index('drop1') + 1
    rc, out, tr, led, rid, Wd = srun('root_stub12a', [], dict(STUB_RESTART_PHASE='drop1,d9ab', STUB_RESTART_TIMES='1'))
    k1, k2 = jload(os.path.join(Wd, 'status', 'restart_%s_1.json' % rid)), jload(os.path.join(Wd, 'status', 'restart_%s_2.json' % rid))
    want = [[p, 'allowed'] for p in phases[:n1]] + [[p, 'no' if p == 'drop1' else 'allowed'] for p in phases[:nd]] + \
        [[p, 'no' if p in ('drop1', 'd9ab') else 'allowed'] for p in phases]
    case('T212b v0.12: drop1 asks a restart, then d9ab (each once): rc 0; three passes (%d runs): to drop1 all allowed; to d9ab with drop1 no; '
         'all %d with drop1 and d9ab no; the ledger "auto_run RESTART ... after=drop1 record=restart_<run>_1.json" and "... after=d9ab '
         'record=restart_<run>_2.json", one END rc=0' % (n1 + nd + len(phases), len(phases)),
         rc == 0 and [x.split()[:2] for x in tr] == want and led.count('auto_run RESTART id=%s after=drop1 record=restart_%s_1.json' % (rid, rid)) == 1
         and led.count('auto_run RESTART id=%s after=d9ab record=restart_%s_2.json' % (rid, rid)) == 1 and led.count('auto_run RESTART') == 2
         and k1.get('by') == 'drop1' and k2.get('by') == 'd9ab' and led.count('auto_run END id=%s rc=0' % rid) == 1
         and '== RESTART after P5d1 drop1: stub restart 1' in out and '== RESTART after P5dab d9ab: stub restart 1' in out,
         'rc %d; %d runs; restarts %s; records %s %s' % (rc, len(tr), [x.split('after=')[1].split()[0] for x in led.splitlines() if 'RESTART' in x],
                                                       k1.get('by'), k2.get('by')))
    rc, out, tr, led, rid, Wd = srun('root_stub12b', [], dict(STUB_RESTART_PHASE='drop1', STUB_RESTART_TIMES='2', STUB_RESTART_FORCE='1'))
    case('T213c v0.12: drop1 asks a second restart all the same (with LINOG_RESTART=no): refused, rc 4; the phases to drop1 twice (%d runs); '
         'the ledger "auto_run RESTART REFUSED ... after=drop1 record=restart_<run>_2.json" and END rc=4' % (2 * n1),
         rc == 4 and len(tr) == 2 * n1 and 'auto_run RESTART REFUSED id=%s after=drop1 record=restart_%s_2.json' % (rid, rid) in led
         and led.count('auto_run END id=%s rc=4' % rid) == 1
         and '== STOPPED after P5d1 drop1, rc 4: a second restart asked by drop1 in one run (stub restart 2)' in out,
         'rc %d; %d runs; ledger %s' % (rc, len(tr), [x[22:] for x in led.splitlines() if 'RESTART' in x or 'END id' in x]))
    # v0.13: coarse (R7's take), drop1 and d9ab, each one restart a run
    nc = phases.index('coarse') + 1
    rc, out, tr, led, rid, Wd = srun('root_stub13', [], dict(STUB_RESTART_PHASE='coarse,drop1,d9ab', STUB_RESTART_TIMES='1'))
    ks = [jload(os.path.join(Wd, 'status', 'restart_%s_%d.json' % (rid, i))) for i in (1, 2, 3)]
    want = [[p, 'allowed'] for p in phases[:nc]] + [[p, 'no' if p == 'coarse' else 'allowed'] for p in phases[:n1]] + \
        [[p, 'no' if p in ('coarse', 'drop1') else 'allowed'] for p in phases[:nd]] + \
        [[p, 'no' if p in ('coarse', 'drop1', 'd9ab') else 'allowed'] for p in phases]
    order = [x.split('after=')[1].split()[0] for x in led.splitlines() if 'auto_run RESTART' in x]
    case('M28 v0.13: coarse asks a restart (R7\'s take), then drop1, then d9ab (each once): rc 0; four passes (%d runs): to coarse all '
         'allowed; to drop1 with coarse no; to d9ab with coarse and drop1 no; all %d with the three no; the ledger\'s RESTART lines in the '
         'order after=coarse (restart_<run>_1.json), drop1 (_2), d9ab (_3), one END rc=0' % (nc + n1 + nd + len(phases), len(phases)),
         rc == 0 and [x.split()[:2] for x in tr] == want and order == ['coarse', 'drop1', 'd9ab']
         and all(led.count('auto_run RESTART id=%s after=%s record=restart_%s_%d.json' % (rid, p, rid, i)) == 1
                 for i, p in ((1, 'coarse'), (2, 'drop1'), (3, 'd9ab')))
         and [k.get('by') for k in ks] == ['coarse', 'drop1', 'd9ab'] and led.count('auto_run END id=%s rc=0' % rid) == 1
         and 'REFUSED' not in led and not os.path.exists(os.path.join(Wd, 'status', 'restart.json'))
         and '== RESTART after P3b coarse: stub restart 1' in out,
         'rc %d; %d runs (want %d); restarts %s; records by %s' % (rc, len(tr), len(want), order, [k.get('by') for k in ks]))

    # ------------------------------------------------------------------ T216 to T220: the path runner
    PR = os.path.join(S.HERE, 'linog_path.sh')

    def penv(cfg, extra=None):
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfg), LINOG_AUTO_HOST=host, LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'),
                   LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'),
                   LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'), LINOG_MINTPY_CFG=MCFG)
        env.update(extra or {})
        return env

    def prun(args, cfg='paths.cfg', extra=None):
        p = subprocess.run(['bash', PR] + args, env=penv(cfg, extra), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode('utf-8', 'replace')
        console('linog_path.sh %s  (cfg %s%s)' % (' '.join(args), cfg, ''.join(' %s=%s' % kv for kv in sorted((extra or {}).items()))),
                p.returncode, out)
        return p.returncode, out

    def drec(d, pn, fr):
        return jload(os.path.join(d, 'p%s_f%s' % (pn, fr), 'status', 'P0a_recon.json'))

    # the tag's archive and table (T220, T223): RD4's granules of the three paths, the table's own sections
    real = open(os.path.join(S.HERE, 'linog_paths.cfg')).read()
    at = os.path.join(T, 'archive_tag', 'alos')
    for (pn, fr), v in sorted(CENSUS.items()):
        for o, d, w, fo in v:
            S.mkzip(os.path.join(at, fo), o, fr, width=w, date=d)
    secs = ''.join('\n[p%s]%s' % (pn, real.split('[p%s]' % pn, 1)[1].split('\n[', 1)[0]) for pn in ('083', '086', '087'))
    # v0.13 (M48): the installed table's [p447] now lists frames (expect_<frame>, bbox_<frame>); T220's fifth refusal needs a
    # [p447] that lists none, so the tag table writes its own: the table's four path keys only
    p447 = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    p447.read(os.path.join(S.HERE, 'linog_paths.cfg'))
    secs += '\n[p447]\n# self-test T220: the path keys of the installed [p447], no frame listed\n' + ''.join(
        '%s = %s\n' % (k, p447['p447'][k]) for k in ('direction', 'residue', 'epoch_date', 'epoch_orbit'))
    hdr = base_cfg.split('\n[p084]', 1)[0]
    assert hdr.count('root = %s\n' % os.path.join(T, 'root')) == 1 and hdr.count('archive = %s\n' % arc) == 1
    hdr = hdr.replace('root = %s\n' % os.path.join(T, 'root'), 'root = %s\n' % os.path.join(T, 'root_tag')).replace(
        'archive = %s\n' % arc, 'archive = %s\n' % at)
    with open(os.path.join(T, 'cfg', 'paths_tag.cfg'), 'w') as fh:
        fh.write(hdr.rstrip('\n') + '\n' + secs.rstrip('\n') + '\n')

    D1 = os.path.join(T, 'dry_path1')
    l0 = (listing(S.fdir(T, '3340', 'root')), listing(S.fdir(T, '3320', 'root')))
    rc, out = prun(['084', '3340', '3320', '--dry-run', D1, '--to', 'recon'])
    rows = tsv(os.path.join(D1, 'runner.tsv'))
    x40, x20 = drec(D1, '084', '3340'), drec(D1, '084', '3320')
    case('T216 linog_path.sh 084 3340 3320 --dry-run DIR --to recon: frame 3340 (3 dates) rc 2 at G0.12, frame 3320 rc 0 after it '
         '(a stop does not stop the next frame); exit 5; DIR/runner.tsv one line a frame (frame, start, rc, seconds, the driver\'s last '
         'line), DIR/frame_<F>.log, each frame\'s dry run under DIR/p084_f<F>/; the frames\' folders unchanged',
         rc == 5 and [(x[0], x[2]) for x in rows] == [('3340', '2'), ('3320', '0')] and rows[0][4].startswith('== DRY RUN STOPPED at recon, rc 2')
         and rows[1][4].startswith('== DRY RUN complete') and x40.get('verdict') == 'FAIL' and gates(x40).get('G0.12') == 'FAIL'
         and x20.get('verdict') == 'PASS' and all(os.path.isfile(os.path.join(D1, 'frame_%s.log' % f)) for f in ('3340', '3320'))
         and (listing(S.fdir(T, '3340', 'root')), listing(S.fdir(T, '3320', 'root'))) == l0 and '== linog_path done' in out,
         'rc %d; rows %s; 3340 %s %s; 3320 %s' % (rc, [x[:3] + x[4:] for x in rows], x40.get('verdict'), gates(x40).get('G0.12'), x20.get('verdict')))
    D2 = os.path.join(T, 'dry_path2')
    rc, out = prun(['084', '--dry-run', D2, '--to', 'recon'])
    rows = tsv(os.path.join(D2, 'runner.tsv'))
    cp = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    cp.read(os.path.join(T, 'cfg', 'paths.cfg'))
    want = sorted(k[7:] for k in cp['p084'] if k.startswith('expect_'))
    rcs = [str(drec(D2, '084', f).get('rc')) for f in want]
    case('T217 linog_path.sh 084 with no frame: the path table\'s frames for p084 (its expect_<frame> keys: %s), in order, frames after a '
         'stop run too; each frame\'s rc in runner.tsv is its recon record\'s; exit %s' % (
             ', '.join(want), '5 (a frame not 0)' if any(x != '0' for x in rcs) else '0'),
         [x[0] for x in rows] == want and [x[2] for x in rows] == rcs and rc == (5 if any(x != '0' for x in rcs) else 0) and len(want) == 5
         and '0' in rcs and any(x != '0' for x in rcs),
         'rc %d; rows %s; records %s' % (rc, [(x[0], x[2]) for x in rows], rcs))
    rc, out = prun(['084', '3280', '3320', '--to', 'stage'], extra={'LINOG_ROOT': os.path.join(T, 'root_path')})
    pr = sorted(glob.glob(os.path.join(T, 'root_path', 'p084', '_path_runs', '*')))
    rows = tsv(os.path.join(pr[-1], 'runner.tsv')) if pr else []
    case('T218 a real run, linog_path.sh 084 3280 3320 --to stage: frame 3280 (a granule twice) DECISION at recon (rc 4), frame 3320 '
         'through stage (rc 0) after it; exit 5; the runner\'s records in <root>/p084/_path_runs/<UTC>_<pid>/ (runner.tsv, frame_<F>.log)',
         rc == 5 and len(pr) == 1 and [(x[0], x[2]) for x in rows] == [('3280', '4'), ('3320', '0')]
         and S.rec(T, '3280', '0a', 'recon', 'root_path').get('verdict') == 'DECISION' and S.rec(T, '3320', '0b', 'stage', 'root_path').get('verdict') == 'PASS'
         and all(os.path.isfile(os.path.join(pr[-1] if pr else '-', 'frame_%s.log' % f)) for f in ('3280', '3320')),
         'rc %d; %s; rows %s' % (rc, [os.path.relpath(x, T) for x in pr], [(x[0], x[2], x[4][:60]) for x in rows]))
    d2 = sorted(S.date_of(o) for o in S.ORBITS)[2]
    env = penv('paths.cfg', {'LINOG_ROOT': os.path.join(T, 'root_sig'), 'LINOG_MOCK_SLEEP': d2})
    p = subprocess.Popen(['bash', PR, '084', '3320', '3330', '--to', 'verify'], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    lg = os.path.join(S.fdir(T, '3320', 'root_sig'), 'logs', 'unpack', d2 + '.log.v1')
    t0 = time.time()
    while not os.path.exists(lg) and p.poll() is None and time.time() - t0 < 180:
        time.sleep(0.2)
    time.sleep(1.5)
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
    out = p.communicate(timeout=240)[0].decode('utf-8', 'replace')
    console('linog_path.sh 084 3320 3330 --to verify  (LINOG_ROOT=root_sig, LINOG_MOCK_SLEEP=%s, SIGTERM after %.1f s)' % (d2, time.time() - t0),
            p.returncode, out)
    pr = sorted(glob.glob(os.path.join(T, 'root_sig', 'p084', '_path_runs', '*')))
    rows = tsv(os.path.join(pr[-1], 'runner.tsv')) if pr else []
    ru = S.rec(T, '3320', '1b', 'unpack', 'root_sig')
    led = open(os.path.join(S.fdir(T, '3320', 'root_sig'), 'logs', 'STATUS.txt')).read() if os.path.isfile(
        os.path.join(S.fdir(T, '3320', 'root_sig'), 'logs', 'STATUS.txt')) else ''
    case('T219 SIGTERM to the runner\'s process group while frame 3320 unpacks: the frame\'s run ends rc 143 (unpack ERROR, the ledger\'s '
         'END rc=143 stopped in unpack), runner.tsv has its one line with rc 143 (the console copy outlives the signal, so no SIGPIPE), '
         'the runner exits 143 and starts no further frame (no frame_3330.log)',
         p.returncode == 143 and len(pr) == 1 and [(x[0], x[2]) for x in rows] == [('3320', '143')]
         and rows[0][4].startswith('stopped by a signal (rc 143)') and not os.path.exists(os.path.join(pr[0], 'frame_3330.log'))
         and 'STOPPED by a signal after frame 3320' in out and ru.get('verdict') == 'ERROR' and 'rc=143 stopped in unpack' in led,
         'rc %s; rows %s; unpack %s' % (p.returncode, rows, ru.get('verdict')))
    # a TERM to the runner alone: the frame's run ends first (the stub pipeline: its stage sleeps 4 s)
    shutil.copy2(PR, os.path.join(SP, 'linog_path.sh'))
    mk = os.path.join(T, 'mark_T219b')
    env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_') and not k.startswith('STUB_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths.cfg'), LINOG_AUTO_HOST=host, LINOG_ROOT=os.path.join(T, 'root_stub5'),
               STUB_SLEEP_PHASE='stage', STUB_SLEEP_S='4', STUB_MARK=mk)
    p = subprocess.Popen(['bash', os.path.join(SP, 'linog_path.sh'), '084', '3320', '3330', '--to', 'extract', '--decide', 'auto'], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(mk) and p.poll() is None and time.time() - t0 < 60:
        time.sleep(0.1)
    if p.poll() is None:
        os.kill(p.pid, signal.SIGTERM)
    out = p.communicate(timeout=120)[0].decode('utf-8', 'replace')
    console('stub pipeline: linog_path.sh 084 3320 3330 --to extract  (SIGTERM to the runner alone after %.1f s)' % (time.time() - t0),
            p.returncode, out)
    pr = sorted(glob.glob(os.path.join(T, 'root_stub5', 'p084', '_path_runs', '*')))
    rows = tsv(os.path.join(pr[-1], 'runner.tsv')) if pr else []
    tr = open(os.path.join(S.fdir(T, '3320', 'root_stub5'), 'stub_trace.txt')).read().split() if os.path.isfile(
        os.path.join(S.fdir(T, '3320', 'root_stub5'), 'stub_trace.txt')) else []
    case('T219b SIGTERM to the runner alone while frame 3320 is in a 4 s phase (the stub pipeline; --decide auto passed on to the driver): '
         'the frame\'s run goes on to its end (--to extract, rc 0), then the runner exits 143 and starts no further frame (no '
         'frame_3330.log, frame 3330 never run)',
         p.returncode == 143 and [(x[0], x[2]) for x in rows] == [('3320', '0')] and tr[0::3] == ['recon', 'stage', 'extract']
         and tr[2::3] == ['auto'] * 3 and not os.path.exists(os.path.join(pr[0] if pr else '-', 'frame_3330.log'))
         and not os.path.exists(S.fdir(T, '3330', 'root_stub5')),
         'rc %s; rows %s; frame 3320 ran %s with LINOG_DECIDE %s' % (p.returncode, [(x[0], x[2]) for x in rows], tr[0::3], tr[2::3]))
    # Ctrl-C (SIGINT to the group): the console copy ignores it (tee -i), the driver ends its frame's record, the runner stops
    mk = os.path.join(T, 'mark_T219c')
    env.update(LINOG_ROOT=os.path.join(T, 'root_stub6'), STUB_MARK=mk, STUB_SLEEP_S='30')
    p = subprocess.Popen(['bash', os.path.join(SP, 'linog_path.sh'), '084', '3320', '3330', '--to', 'extract'], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
                         preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
    t0 = time.time()
    while not os.path.exists(mk) and p.poll() is None and time.time() - t0 < 60:
        time.sleep(0.1)
    time.sleep(0.5)
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGINT)
    out = p.communicate(timeout=120)[0].decode('utf-8', 'replace')
    console('stub pipeline: linog_path.sh 084 3320 3330 --to extract  (SIGINT to the group after %.1f s)' % (time.time() - t0), p.returncode, out)
    pr = sorted(glob.glob(os.path.join(T, 'root_stub6', 'p084', '_path_runs', '*')))
    rows = tsv(os.path.join(pr[-1], 'runner.tsv')) if pr else []
    led = open(os.path.join(S.fdir(T, '3320', 'root_stub6'), 'logs', 'STATUS.txt')).read() if os.path.isfile(
        os.path.join(S.fdir(T, '3320', 'root_stub6'), 'logs', 'STATUS.txt')) else ''
    case('T219c Ctrl-C (SIGINT to the runner\'s group) while frame 3320 is in a 30 s phase: the frame\'s run stops, rc 130 (its ledger\'s '
         'END rc=130 stopped in stage), runner.tsv has the one line with rc 130 (the console copy ignores SIGINT), the runner exits 130 '
         'and starts no further frame',
         p.returncode == 130 and [(x[0], x[2]) for x in rows] == [('3320', '130')] and 'rc=130 stopped in stage' in led
         and not os.path.exists(os.path.join(pr[0] if pr else '-', 'frame_3330.log')) and time.time() - t0 < 30,
         'rc %s; rows %s; ledger %s' % (p.returncode, rows, [x[22:] for x in led.splitlines() if 'END id' in x]))
    res = [prun(['084', '3320', '--to', 'recon'], extra={'LINOG_AUTO_HOST': 'not-' + host}), prun(['084', '33x0']),
           prun(['084', '3320', '--decide', 'maybe']), prun(['999']), prun(['447'], cfg='paths_tag.cfg')]
    tests = (('wrong host', 'wrong host'), ('a frame "33x0"', 'a frame must be a number'), ('--decide maybe', '--decide takes ask or auto'),
             ('path 999', 'path 999 is not a path number (1 to 671)'), ('path 447 (no expect_<frame> key)', 'the path table lists no frame for path 447'))
    got = [(t, r[0], w in r[1]) for (t, w), r in zip(tests, res)]
    case('T220 linog_path.sh refuses before any frame starts, rc 3 each, naming the reason: the wrong host, a frame not a number, '
         '--decide maybe, a path that is not a path number (999; v0.13: said so), a path it lists no frame for (p447 in the tag\'s '
         'table, its path keys only: name the frames)',
         all(r == 3 and ok for _, r, ok in got) and not any('== frame ' in r[1] for r in res),
         '; '.join('%s: rc %s%s' % (t, r, '' if ok else ' (reason not printed)') for t, r, ok in got))

    # ------------------------------------------------------------------ T221 to T223: the path table's new entries and the tag
    cp = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    cp.read(os.path.join(S.HERE, 'linog_paths.cfg'))
    bad = []
    for pn in ('083', '086', '087'):
        sec = cp['p' + pn]
        res_, eo, ed = int(sec['residue']), int(sec['epoch_orbit']), datetime.datetime.strptime(sec['epoch_date'], '%Y%m%d')
        if sec.get('direction') != 'D' or eo % 671 != res_ or any(k.startswith('bbox_') for k in sec):
            bad.append('p%s: direction %s, residue %s, anchor orbit %d' % (pn, sec.get('direction'), res_, eo))
        exp = dict((k[7:], int(v)) for k, v in sec.items() if k.startswith('expect_'))
        got = dict((f, len(v)) for (p_, f), v in CENSUS.items() if p_ == pn)
        if exp != got:
            bad.append('p%s: expect %s, the census %s' % (pn, exp, got))
        for (p_, f), v in sorted(CENSUS.items()):
            if p_ != pn:
                continue
            for o, d, w, fo in v:
                k, rem = divmod(o - eo, 671)
                law = (ed + datetime.timedelta(days=46 * k)).strftime('%Y%m%d')
                if rem or law != d:
                    bad.append('p%s f%s orbit %d: residue %d, the law gives %s, the census %s' % (pn, f, o, o % 671, law, d))
    case('T221 the path table\'s p083, p086 and p087 (record 109.3): descending; residue = the anchor orbit mod 671; expect_<frame> = RD4\'s '
         'census (3 frames of 1; 3, 4, 4, 4; 3 of 3); every census granule on the residue and on the date law; no footprint in the table '
         '(v0.13: G0.14 judges the granules\' own corners)',
         not bad, '; '.join(bad) or 'all agree')
    plus = os.path.join(T, 'cfg', 'paths_plus.cfg')
    with open(plus, 'w') as fh:
        fh.write(base_cfg + '\n[p999]\n# self-test T222: a section added to the table\ndirection = D\nresidue = 1\nepoch_date = 20070101\n'
                 'epoch_orbit = 1\nexpect_0001 = 1\n')
    assert base_cfg.count('offnadir_tol = 0.5\n') == 1
    with open(os.path.join(T, 'cfg', 'paths_other.cfg'), 'w') as fh:
        fh.write(base_cfg.replace('offnadir_tol = 0.5\n', 'offnadir_tol = 0.6\n'))

    def rstate(cfg):
        p = subprocess.run(['python3', '-E', '-B', os.path.join(S.HERE, 'lp_recon.py'), '--path', '084', '--frame', '3320', '--state'],
                           env=penv(cfg, {'LINOG_ROOT': os.path.join(T, 'root_path')}), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.stdout.decode('utf-8', 'replace').strip()
    sts = (rstate('paths.cfg'), rstate('paths_plus.cfg'), rstate('paths_other.cfg'))
    case('T222 recon\'s fingerprint reads its own path\'s settings, not the table file: T218\'s frame 3320 CURRENT under its table, '
         'CURRENT under the same table with a section added (as v0.10 adds three), STALE with a [defaults] value changed (the control)',
         sts == ('CURRENT', 'CURRENT', 'STALE'), 'states %s' % (sts,))
    TG = os.path.join(T, 'tag')
    exits, bad, rows_all, n14 = [], [], {}, {}

    def g014_mock(pn, fr):
        """v0.13 (M48, 13.7): G0.14 as the mock's positions give it (lp_selftest.mock_geo's corners against the mock DEM,
        120 to 123 E and 14 to 18 N, with 0.1 deg), registered before the run reads it."""
        cs = S.mock_geo(pn, fr, 'D')['corners']
        la, lo = [c[0] for c in cs], [c[1] for c in cs]
        return 'PASS' if min(min(la) - 14.0, 18.0 - max(la), min(lo) - 120.0, 123.0 - max(lo)) >= 0.1 else 'FAIL'
    for pn, frs in (('087', ('3280', '3290', '3300')), ('086', ('3280', '3290', '3300', '3310')), ('083', ('3300', '3310', '3320'))):
        rc, out = prun([pn] + list(frs) + ['--dry-run', os.path.join(TG, 'p' + pn), '--to', 'recon'], cfg='paths_tag.cfg')
        exits.append(rc)
        rows = tsv(os.path.join(TG, 'p' + pn, 'runner.tsv'))
        rows_all[pn] = [(x[0], x[2]) for x in rows]
        if [x[0] for x in rows] != list(frs) or any(x[2] != '2' for x in rows):
            bad.append('p%s rows %s' % (pn, rows_all[pn]))
        for fr in frs:
            x = drec(os.path.join(TG, 'p' + pn), pn, fr)
            g = gates(x)
            fails = sorted(k for k, v in g.items() if v in ('FAIL', 'ERROR', 'DECISION'))
            w14 = g014_mock(pn, fr)
            if fails != sorted(['G0.12'] + (['G0.14'] if w14 == 'FAIL' else [])) or val(x, 'G0.12') != G012[(pn, fr)] \
                    or g.get('G0.13') != 'PASS' or g.get('G0.14') != w14 or g.get('G0.5') != 'PASS' or g.get('G0.2') != 'PASS' \
                    or g.get('G0.17') != 'PASS' or g.get('G0.16') != 'INFO':
                bad.append('p%s f%s: %s; G0.12 %s; G0.13 %s G0.14 %s (mock position: %s) G0.5 %s G0.2 %s G0.17 %s G0.16 %s' % (
                    pn, fr, fails, val(x, 'G0.12'), g.get('G0.13'), g.get('G0.14'), w14, g.get('G0.5'), g.get('G0.2'), g.get('G0.17'),
                    g.get('G0.16')))
            n14[w14] = n14.get(w14, 0) + 1
    nz = len(glob.glob(os.path.join(at, '*', '*.zip')))
    case('T223 the tag (record 109.3), as the install runs it on felix: linog_path.sh <path> <frames> --dry-run R/tag/p<path> --to recon on '
         'the 10 thin AOI frames (%d mock granules at RD4\'s orbits, dates, widths and folders; the table\'s own sections): every frame '
         'rc 2 with G0.12 FAIL and felix\'s values (P087 3 dates, largest gap 460 d; P086 F3280 3, 828 d; F3290 to F3310 4, 828 d; '
         'P083 1); G0.2, G0.5 (the date law), G0.13 and G0.17 PASS, G0.16 INFO (under min_dates); v0.13 (M48): G0.14 judges the '
         'granules\' corners, its verdict the mock\'s position registers (the mock places these frames by the frame law and step: '
         'those within 0.1 deg of the mock DEM\'s 120 E or west of it FAIL there too); each runner exit 5; no frame folder made' % nz,
         nz == 27 and exits == [5, 5, 5] and not bad and not os.path.exists(os.path.join(T, 'root_tag')),
         'exits %s; %s; G0.14 by position %s; %s' % (exits, rows_all, n14, '; '.join(bad) or 'every frame as felix\'s census'))
