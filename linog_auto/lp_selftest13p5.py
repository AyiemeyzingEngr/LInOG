#!/usr/bin/env python3
"""lp_selftest13p5.py -- linog_auto v0.13's R7 cases, coarse's D2 loop (the ascending record 11.2 to 11.10 and 18.4), called by
lp_selftest.py as the suite 13p5 (the record's case numbers).

The frames, on 13p4's mock ground (LINOG_MOCK_V13=1, selftest_kit/mock_isce/linog_mock3.py's V13 model):
  the mixed full-height frame 3354 (12 dates, 8 FBS and 4 FBD, 1000 samples x 18432 lines) from an archive of its own,
     v13mx5: 13p4's granules but 20080715's (FBD), whose image records put column 0 one gate nearer than the leader's r0
     (rwin's k = -1). Every run of the frame carries LINOG_MOCK_GATEOFF for that date: the mock world's truth that its first
     sample lies one gate nearer, which rwin's correction of the shelve cancels (M79);
  the FBD-only full-height frame 3364 (13p4's archive v13fbd, 6 dates) under a path table with min_dates 6 (M20's L3, M32).
The mixed frame runs to topo once (S3a), then to coarse under --decide ask with 20090302 (FBS) off-frame at G21
(LINOG_MOCK_OFFFRAME): coarse's D2 DECISION with R7's proposal, nothing moved (D). Most cases start from D, whose coarse
products the reuse rule (11.5) reads again without run_03; M19 and M80 start from S3a, since their plants act in run_03.
Cases:
  M18b the ask run's DECISION; recon/d2.txt naming another date (D2t WARN, the DECISION stays, run_03 not run); "keep"
       (coarse PASS, the date kept); "take" under ask (the operator's take, the restart, coarse PASS on the rest by reuse);
  M79 (18.4) 20080715 one gate off by its records: rwin's k -1 and its correction cancel the mock's truth, G7 reads it ok;
  M23, M23b --only coarse under auto, and the operator's take under --only: DECISION (L0) before anything moves;
  M29 a target name taken (L6); a rename made to fail (LINOG_MOCK_D2FAILAT: G3b.11 FAIL, rc 2, MOVES.txt naming the moves
       made, nothing deleted); SIGTERM during the take (LINOG_MOCK_D2SLEEP: held, the take whole, then the stop); the next
       run keeps the request aside and coarse reuses;
  M20 L2 (4 of 12 under auto: DECISION; the operator's take: D2w WARN and the loop); L4 (the take would make the reference
       the earliest date); L3 on the FBD-only frame (5 dates left, min_dates 6; the operator's take too);
  M31 L8 (every FBD date flagged: the branch would turn FBS-only);
  M21 the loops: a second flag in the same run (L0 and L1), in a new run (L1), the operator's loop 2, a third refused (L1);
  M18 auto from D to igram: R7 takes 20090302, the frame runs again from the top: recon drops it (G0.4d), stage to rwin
       write nothing, recon/modes.json without it, the reference kept, topo CURRENT, coarse reuses (G3b.6), G21 and G7 PASS,
       refine to igram PASS; M26 its .slc and .slc.prefilter archived, bandlimit's G1bl.11, G11m's 7 FBS dates, D1f;
  M27 the same run again: every phase CURRENT, no restart, nothing written;
  M22 an operator's take (loop 2) on the frame past igram: DECISION (L5);
  M19, M80 a fresh run_03 under auto with N53 planted on 20081130 (FBS, 32 samples) and an uncorrected one-gate window on
       20080530 (FBD, LINOG_MOCK_GATEOFF, rwin's k 0): G7 calls both out, R7 takes both (loop 1), the record giving each
       date's G7 calls and rwin record;
  M24 the reuse guards on that frame after the loop (each: G3b.6 DECISION, run_03 not run, the products unchanged), and
       the positive control (G3b.6 PASS);
  M32 on the FBD-only frame: a G21 row with no ratio (LINOG_MOCK_AZNAN) and a G7 call-out on EMPTY windows
       (LINOG_MOCK_COARSEEMPTY), a measured flag beside them (the hook): v0.12's D2 DECISION, R7 taking nothing;
  M25 admit's R3 counting R7's dates (lp_admit.r3) and M30 R7's limits L1, L2, L4 and L7 (lp_coarse.r7_limits), at the
       function level in this Python.
Self-test hooks (lp_common.selftest_hook: a path table other than the package's): LINOG_MOCK_D2FLAG, LINOG_MOCK_D2TAG,
LINOG_MOCK_D2FAILAT, LINOG_MOCK_D2SLEEP. Frames are kept as copies (files over 1 MB hard-linked, never written in place:
a case that changes such a file writes a new one first, unlink_copy) and a case puts a copy back at the same path.
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
import sys
import time

import lp_selftest13p1 as P13

FR, FR_FBD = '3354', '3364'
LF = 18432
PHASES18 = (('0a', 'recon'), ('0b', 'stage'), ('1a', 'extract'), ('1b', 'unpack'), ('1br', 'rwin'), ('1bs', 'bandlimit'),
            ('1c', 'verify'), ('2a', 'stack1'), ('2b', 'reference'), ('2c', 'stack2'), ('3a', 'topo'), ('3b', 'coarse'),
            ('4a', 'refine'), ('4b', 'invert'), ('4c', 'datum'), ('4d', 'fine'), ('4e', 'bgrid'), ('4f', 'igram'))

# M25: admit's R3 with R7's dates (lp_admit.r3), argv[1] the pipeline folder
CODE25 = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import lp_admit as A
dates = ['2007%02d%02d' % (1 + i // 28, 1 + i % 28) for i in range(20)]
pairs = sorted(set('%s_%s' % (dates[i], dates[j]) for i in range(20) for j in range(i + 1, min(i + 4, 20))))
def flagged(dead):
    return [p for p in pairs if set(p.split('_')) & set(dead)]
out = {}
for name, dead, r7 in (('three_r7', [dates[4], dates[10], dates[16]], 4), ('two_r7', [dates[4], dates[10]], 4),
                       ('three_v12', [dates[4], dates[10], dates[16]], 0)):
    r = A.r3(dates, pairs, flagged(dead), dates[8], 5, 0.5, 0.25, r7=r7)
    out[name] = dict(ok=r['ok'], dates=r['dates'], problems=r['problems'])
# admit's own count (the part 5 review's P5-01, P5-09): lp_admit.r7_count on frame folders under argv[2]
import os
def frame(name, body):
    W = os.path.join(sys.argv[2], name)
    os.makedirs(os.path.join(W, 'recon'), exist_ok=True)
    if body is not None:
        with open(os.path.join(W, 'recon', 'd2_decision.json'), 'w') as fh:
            fh.write(body if isinstance(body, str) else json.dumps(body))
    return W
two_loops = dict(N0=12, reference='20070108', loops=[dict(loop=1, dates={'20070105': dict(granule='g1'), '20070111': dict(granule='g2')}),
                                                     dict(loop=2, dates={'20070117': dict(granule='g3')})])
for name, body in (('count_two_loops', two_loops), ('count_none', None), ('count_not_json', '{"loops": [1, '),
                   ('count_dates_list', dict(loops=[dict(loop=1, dates=['20070105'])])),
                   ('count_date_string', dict(loops=[dict(loop=1, dates={'20070105': 'x'})])),
                   ('count_loop_string', dict(loops=['loop1']))):
    n, m5, err = A.r7_count(frame(name, body))
    out[name] = [n, m5, err]
print(json.dumps(out))
'''

# M24i: lp_coarse.reuse_check's refusals on a synthetic frame (the part 5 review's P5-06, after its chk_reuse.py); argv[1] the
# pipeline folder, argv[2] a scratch folder
CODE24 = r'''
import copy, json, os, sys
sys.path.insert(0, sys.argv[1])
import lp_coarse as K
import lp_p3 as P3
W = os.path.join(sys.argv[2], 'f')
ref, secs = '20070301', ['20070501', '20070601']
def wr(rel, body='x' * 64):
    p = os.path.join(W, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as fh:
        fh.write(body)
for d in secs + [ref]:
    for n in ('%s.slc' % d, '%s.slc.xml' % d, '%s.slc.vrt' % d, 'data.dat', 'data.dir'):
        wr('SLC/%s/%s' % (d, n))
for d in secs:
    for n in ('range.off', 'range.off.xml', 'azimuth.off', 'azimuth.off.xml'):
        wr('offsets/%s/%s' % (d, n))
    for n in ('%s.slc' % d, '%s.slc.xml' % d, 'referenceShelve/data.dat', 'secondaryShelve/data.dat'):
        wr('coregSLC/Coarse/%s/%s' % (d, n))
    wr('configs/config_focus_split_%s' % d, '[Common]\n')
    wr('configs/config_geo2rdr_coarseResamp_%s' % d, '[Function-1]\nreference : %s/SLC/%s\n' % (W, ref))
L2 = ['stripmapWrapper.py -c %s/configs/config_focus_split_%s' % (W, d) for d in secs]
L3 = ['stripmapWrapper.py -c %s/configs/config_geo2rdr_coarseResamp_%s' % (W, d) for d in secs]
tm = dict((n, ('/env/%s' % n, 'md5_%s' % n, 'pin')) for n in K.REUSE_TOOLS)
topo = 'topo_digest_A'
own = dict(verdict='PASS', start='2026-10-18T00:00:00Z', gates=[dict(id=g, verdict='PASS') for g in ('G3b.8', 'G3b.9', 'G3b.10')],
           outputs=dict(files=P3.listing(W, P3.OUTS['coarse']), reuse=K.reuse_data(W, secs, ref, topo, tm, L2, L3)))
out = {}
def check(name, own0=own, s3=secs, r=ref, td=topo, t=tm, plant=None, undo=None):
    if plant:
        plant()
    out[name] = list(K.reuse_check(W, own0, s3, r, td, t, L2, L3))
    if undo:
        undo()
check('control')
check('refused_record', own0=dict(verdict='DECISION', start='x', outputs={}, gates=[dict(id='G3b.6', verdict='DECISION')]))
check('reference', r='20070601', s3=['20070501'])
check('topo', td='topo_digest_B')
t2 = copy.deepcopy(tm)
t2['resampleSlc.py'] = ('/env/resampleSlc.py', 'md5_other', 'pin')
check('tool', t=t2)
check('running', own0=dict(own, verdict='RUNNING'))
check('stray_coarse', plant=lambda: os.makedirs(os.path.join(W, 'coregSLC', 'Coarse', '20990101')),
      undo=lambda: os.rmdir(os.path.join(W, 'coregSLC', 'Coarse', '20990101')))
check('unlisted', s3=secs + ['20070701'])
st = os.stat(os.path.join(W, 'SLC', ref, '%s.slc' % ref))
check('reference_slc', plant=lambda: os.utime(os.path.join(W, 'SLC', ref, '%s.slc' % ref), ns=(st.st_atime_ns, st.st_mtime_ns + 10 ** 9)))
print(json.dumps(out))
'''

# M30: R7's limits (lp_coarse.r7_limits), argv[1] the pipeline folder, argv[2] an empty frame folder (L5 reads it)
CODE30 = r'''
import json, os, sys
sys.path.insert(0, sys.argv[1])
os.environ['LINOG_RESTART'] = 'allowed'
import lp_coarse as K
W = sys.argv[2]
dates = ['20070101', '20070201', '20070301', '20070401', '20070501', '20070601', '20070701', '20070801']
modes = dict((d, 'FBS') for d in dates)
modes['20070401'] = modes['20070701'] = 'FBD'
ref = '20070301'
ring = [[dates[i], dates[(i + 1) % 8]] for i in range(8)] + [[dates[i], dates[(i + 2) % 8]] for i in range(8)]
two = [[dates[i], dates[i + 1]] for i in range(3)] + [[dates[0], dates[2]], [dates[1], dates[3]]] + \
      [[dates[i], dates[i + 1]] for i in range(4, 7)] + [[dates[4], dates[6]], [dates[5], dates[7]]] + \
      [[dates[3], '20070901'], ['20070901', dates[4]]]
def lims(F, pairs, dec0=None, operator=False, ds=dates, md=modes):
    return dict((x['id'], [x['ok'], x['warn'], x['text']]) for x in K.r7_limits(W, F, ref, dec0, ds, md, pairs, 5, 0.25, operator))
d9 = dates + ['20070901']
m9 = dict(modes, **{'20070901': 'FBS'})
dec1 = dict(N0=8, reference=ref, loops=[dict(loop=1, dates={'20070801': dict(granule='g')})])
out = dict(
    control=lims(['20070501'], ring),
    split=lims(['20070901'], two, ds=d9, md=m9),
    thin=lims(['20070601'], [p for p in ring if p != [dates[6], dates[7]] and p != [dates[7], dates[1]]]),
    ref_in=lims([ref], ring),
    l2_two=lims(['20070501', '20070601'], ring),
    l2_three=lims(['20070501', '20070601', '20070201'], ring),
    loop2_auto=lims(['20070501'], ring, dec0=dec1),
    loop2_op=lims(['20070501'], ring, dec0=dec1, operator=True),
    loop2_l2=lims(['20070501', '20070601'], ring, dec0=dec1, operator=True),
    nomode=lims(['20070501'], ring, md=dict(modes, **{'20070201': None})))
# L6 and the take before its first move (the part 5 review's P5-03): _archive a file, then a dangling link
R = dict(kept=[dict(date='20070501', scene='S1', zip='/a/S1.zip')])
for name, mk in (('archive_file', lambda p: open(p, 'w').close()), ('archive_link', lambda p: os.symlink(p + '_nowhere', p))):
    W6 = os.path.join(W, name)
    os.makedirs(W6)
    mk(os.path.join(W6, '_archive'))
    adir, moves, bad = K.r7_paths(W6, ['20070501'], R, 'T1')
    try:
        K.r7_take(W6, adir, [], None, dict(loop=1, utc='u', reference=ref, n_before=8, dates={}))
        took = 'no error'
    except K.TakeError as e:
        took = [e.n, str(e)]
    except Exception as e:
        took = 'not a TakeError: %s' % type(e).__name__
    out[name] = dict(bad=bad, take=took)
# the DECISION's way on (P5-02)
F = ['20070501']
out['way'] = dict(l0=K.way_on({'L0'}, 0, False, F, W), l1=K.way_on({'L1'}, 1, False, F, W), l0l1=K.way_on({'L0', 'L1'}, 1, False, F, W),
                  l2=K.way_on({'L2'}, 0, False, F, W), third=K.way_on({'L1'}, 2, True, F, W), l4=K.way_on({'L4'}, 0, False, F, W),
                  l0op=K.way_on({'L0'}, 1, True, F, W))
print(json.dumps(out))
'''


def link_or_copy(src, dst):
    if os.path.getsize(src) > (1 << 20):
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None


def unlink_copy(p):
    """p as a file of its own (a copy with its mtime, put in place): a frame copy's big files are hard links of the kept
    copy's, which a change in place would reach."""
    shutil.copy2(p, p + '.selftest_copy')
    os.replace(p + '.selftest_copy', p)


def l7_expect(pairs, F, dates):
    """L7 as 11.3 states it: stack1's pairs less F's in one component, every date left in 2 pairs or more."""
    left = [d for d in dates if d not in F]
    adj = dict((d, set()) for d in left)
    deg = dict((d, 0) for d in left)
    for a, b in pairs:
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
            deg[a] += 1
            deg[b] += 1
    seen, comps = set(), 0
    for d in left:
        if d in seen:
            continue
        comps += 1
        todo = [d]
        seen.add(d)
        while todo:
            x = todo.pop()
            for y in adj[x] - seen:
                seen.add(y)
                todo.append(y)
    return comps == 1 and all(v >= 2 for v in deg.values())


def phase13_5(T, case, S):
    print('-- v0.13 R7, coarse\'s D2 loop (part 5): the mixed full-height frame 3354 (archive v13mx5: 20080715 one gate off by '
          'its records) and the FBD-only frame 3364 under min_dates 6, on the one mock ground (LINOG_MOCK_V13)')
    # the function-level cases first: they need no frame
    w25 = os.path.join(T, 'm25_frames')
    os.makedirs(w25, exist_ok=True)
    j25, e25 = fcall(S, CODE25, [S.HERE, w25])
    J = j25 or {}
    t3, t2, tv = [J.get(k) or {} for k in ('three_r7', 'two_r7', 'three_v12')]
    c2, cn, cj, cl, cs, cp = [J.get(k) or [None, None, None] for k in ('count_two_loops', 'count_none', 'count_not_json',
                                                                       'count_dates_list', 'count_date_string', 'count_loop_string')]
    case('M25 (11.7, R7-e) admit\'s R3 counts R7\'s dates (lp_admit.r3): a 20-date network after R7 took 4 of N0 24, R3 finding 3 '
         'dead dates: 7 of 24 is past 25 %, a problem naming both counts; 2 dead: 6 of 24, taken; the 3 without R7\'s (v0.12\'s '
         'count, 3 of 20): taken; admit\'s own count (lp_admit.r7_count, the part 5 review\'s P5-01 and P5-09): 3 dates over 2 '
         'loops with the file\'s md5, 0 and no md5 without the file, and "unreadable" with its reason for a file that is not JSON, a '
         'loop whose dates are a list, a date that is not a mapping and a loop that is not one (each a FAIL at G5a.8)',
         bool(j25) and not t3.get('ok') and len(t3.get('dates') or []) == 3
         and any('7 of 24 dates excluded: R3\'s 3 and R7\'s 4' in p for p in t3.get('problems') or [])
         and t2.get('ok') is True and len(t2.get('dates') or []) == 2 and tv.get('ok') is True and len(tv.get('dates') or []) == 3
         and c2[0] == 3 and c2[1] and len(c2[1]) == 32 and c2[2] is None and cn == [0, None, None]
         and cj[:2] == [0, 'unreadable'] and 'is not JSON' in str(cj[2]) and cl[:2] == [0, 'unreadable'] and 'not R7\'s' in str(cl[2])
         and cs[:2] == [0, 'unreadable'] and 'not a date with its granule' in str(cs[2])
         and cp[:2] == [0, 'unreadable'] and 'not R7\'s' in str(cp[2]),
         '%s %s' % (j25, e25[-300:]))
    w24 = os.path.join(T, 'm24i_frame')
    os.makedirs(w24, exist_ok=True)
    j24, e24 = fcall(S, CODE24, [S.HERE, w24])
    R24 = j24 or {}

    def rz(name, text):
        v = R24.get(name) or [None, []]
        return v[0] is False and any(text in w for w in v[1])
    case('M24i (11.5; the part 5 review\'s P5-06) the reuse rule\'s other refusals, on a synthetic frame (lp_coarse.reuse_check): the '
         'control reuses; refused, each with its reason: the record of a refused run (no config md5s), the reference changed, topo\'s '
         'digest changed, resampleSlc.py\'s md5 changed, the earlier record RUNNING, a stray coregSLC/Coarse/20990101/, a secondary '
         'the earlier listing lacks, the reference\'s own SLC touched',
         bool(j24) and (R24.get('control') or [None])[0] is True and rz('refused_record', 'holds no config md5s')
         and rz('reference', 'the reference 20070601, recorded 20070301') and rz('topo', 'topo\'s digest changed')
         and rz('tool', 'resampleSlc.py changed') and rz('running', 'is RUNNING') and rz('stray_coarse', 'hold other entries: 20990101')
         and rz('unlisted', '20070701: not in the earlier record\'s listing') and rz('reference_slc', '20070301: its SLC identity changed'),
         '%s %s' % (dict((k, v[0]) for k, v in R24.items()), e24[-300:]))
    w30 = os.path.join(T, 'm30_frame')
    os.makedirs(w30, exist_ok=True)
    j30, e30 = fcall(S, CODE30, [S.HERE, w30])
    L = j30 or {}

    def lk(name, lid, i=0):
        return ((L.get(name) or {}).get(lid) or [None, None, ''])[i]
    case('M30 (11.3) R7\'s limits at the function level (lp_coarse.r7_limits): L7 holds on a ring of 16 pairs less one date, FAILs '
         'when the date taken joins two parts (2 components) and when it leaves a date in one pair; L4 FAILs the reference among '
         'the flags; L2 holds at 2 of 8 (25 %) and FAILs at 3 of 8, passed with a WARN by the operator\'s take; L1 under auto '
         'refuses a second loop, the operator\'s take makes it, L2 then counting the earlier loop\'s date',
         bool(j30) and all(lk('control', 'L%d' % i) for i in range(9))
         and lk('split', 'L7') is False and '2 component(s)' in lk('split', 'L7', 2)
         and lk('thin', 'L7') is False and '20070801' in lk('thin', 'L7', 2)
         and lk('ref_in', 'L4') is False and 'among the flagged dates' in lk('ref_in', 'L4', 2)
         and lk('l2_two', 'L2') is True and lk('l2_three', 'L2') is False
         and lk('loop2_auto', 'L1') is False and lk('loop2_op', 'L1') is True and lk('loop2_l2', 'L2') is True
         and lk('loop2_l2', 'L2', 1) is True and '3 of N0 8' in lk('loop2_l2', 'L2', 2)
         and lk('nomode', 'L8') is False and 'no mode in recon/modes.json for 20070201' in lk('nomode', 'L8', 2),
         '%s %s' % (dict((k, dict((i, v[0]) for i, v in x.items() if isinstance(v, list) and not v[0])) for k, x in L.items()
                         if k not in ('way', 'archive_file', 'archive_link')), e30[-300:]))
    af_, al_, wy = L.get('archive_file') or {}, L.get('archive_link') or {}, L.get('way') or {}
    case('M30b (11.3; the part 5 review\'s P5-02, P5-03, P5-10) L8 FAILs a date with no mode; L6 FAILs an _archive that is a file '
         'or a link, and the take there stops before its first move with a TakeError of 0 moves; the DECISION\'s way on: a new run '
         'where L0 alone fails, the operator\'s take where L1 (a second loop) or L2 fails, keep or by hand for a third loop or L4',
         any('_archive is not a folder of the frame (a file)' in x for x in af_.get('bad') or [])
         and any('_archive is not a folder of the frame (a link)' in x for x in al_.get('bad') or [])
         and isinstance(af_.get('take'), list) and af_['take'][0] == 0 and '(after 0 move(s) of the take)' in af_['take'][1]
         and isinstance(al_.get('take'), list) and al_['take'][0] == 0
         and 'run the frame again without --only' in wy.get('l0', '') and 'run the frame again without --only' in wy.get('l0op', '')
         and 'the operator\'s take (11.6) makes the second loop (L1):' in wy.get('l1', '')
         and 'the operator\'s take (11.6) makes the second loop (L1) and in a new run (L0):' in wy.get('l0l1', '')
         and 'the operator\'s take (11.6) passes L2 with a WARN:' in wy.get('l2', '') and 'by hand (11.1)' in wy.get('third', '')
         and 'by hand (11.1)' in wy.get('l4', ''),
         '%s %s %s' % (af_, al_, dict((k, v[:40]) for k, v in wy.items())))

    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M18-M80 not run: the mock ground needs numpy, and neither Python tried has it', False)
        return
    ORB = S.ORBITS[:12]
    D = [S.date_of(o) for o in ORB]
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    dem12 = re.search(r'^dem_3350 = (.+)$', base, re.M).group(1)
    p5 = base.rstrip('\n') + '\n# v0.13 part 5: the full-height mock frames, on the same mock DEM\ndem_%s = %s\ndem_%s = %s\n' % (
        FR, dem12, FR_FBD, dem12)
    with open(os.path.join(T, 'cfg', 'paths_p5.cfg'), 'w') as fh:
        fh.write(p5)
    with open(os.path.join(T, 'cfg', 'paths_p5m6.cfg'), 'w') as fh:
        fh.write(p5.replace('min_dates = 5\n', 'min_dates = 6\n'))
    full = dict(lines=LF, rows13=True)
    plants = dict((i, full) for i in range(12))
    plants[8] = dict(full, r1_off_m=-S.GATE)
    plants[11] = dict(full, g016=dict(along_km=3.0))   # 20090302, M18's date: 3 km off along track, inside G0.16's line (P5-08)
    am = P13.make_variant(T, S, 'v13mx5', plants, frame=FR, orbs=ORB, fbd=S.FBD_3350)
    af = P13.make_variant(T, S, 'v13fbd', dict((i, full) for i in range(6)), frame=FR_FBD, orbs=S.ORBITS[:6], fbd=range(6),
                          width=lambda i: S.W_MX if i == 5 else S.W_MX + 48)
    if not am or not af or p5.count('min_dates = 5\n') != 1:
        case('M18-M80 not run: the full-height mock archives could not be made (numpy), or the path table has no min_dates 5 line',
             False)
        return
    G8 = '%s:%r' % (D[8], -S.GATE)   # the mock world's truth for 20080715: its first sample one gate nearer

    def fd(root, frame=FR):
        return S.fdir(T, frame, root)

    def run(root, args, extra=None, frame=FR, decide=True):
        e = {'LINOG_ROOT': os.path.join(T, root), 'LINOG_MOCK_V13': '1', 'LINOG_ARCHIVE': am if frame == FR else af}
        if frame == FR:
            e['LINOG_MOCK_GATEOFF'] = G8
        e.update(extra or {})
        return S.run(T, ['084', frame] + (['--decide', 'auto'] if decide else []) + args,
                     cfg='paths_p5.cfg' if frame == FR else 'paths_p5m6.cfg', env_extra=e)

    def popen_env(root, extra):
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p5.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_ROOT=os.path.join(T, root), LINOG_MOCK_V13='1', LINOG_ARCHIVE=am, LINOG_MOCK_GATEOFF=G8)
        env.update(extra)
        return env

    def rec(root, idx, ph, frame=FR):
        return S.rec(T, frame, idx, ph, root)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gval(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def r7of(r):
        return ((r or {}).get('outputs') or {}).get('r7') or {}

    def failing(r):
        return sorted(x['id'] for x in r7of(r).get('limits') or [] if not x['ok'])

    def snap(root, frame, name):
        shutil.copytree(fd(root, frame), os.path.join(T, 'snap_13p5', name), symlinks=True, copy_function=link_or_copy)

    def restore(root, frame, name, tag):
        S.aside(T, fd(root, frame), '13p5_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_13p5', name), fd(root, frame), symlinks=True, copy_function=link_or_copy)

    def listing(W):
        out = {}
        for dp, dn, fn in os.walk(W):
            for n in fn + [x for x in dn if os.path.islink(os.path.join(dp, x))]:
                p = os.path.join(dp, n)
                if os.path.islink(p):   # a copy makes its links anew: a link is its target
                    out[os.path.relpath(p, W)] = ('link', os.readlink(p))
                    continue
                s_ = os.lstat(p)
                out[os.path.relpath(p, W)] = (s_.st_size, s_.st_mtime_ns)
        return out

    def under(lst, tops, skip=()):
        def inn(k, ts):
            return any(k == t or k.startswith(t + '/') for t in ts)
        return dict((k, v) for k, v in lst.items() if inn(k, tops) and not inn(k, skip))

    def ledger_run(W):
        """(this run's id, its ledger lines) from logs/STATUS.txt."""
        p = os.path.join(W, 'logs', 'STATUS.txt')
        ls = open(p).read().splitlines() if os.path.isfile(p) else []
        st = [k for k, x in enumerate(ls) if 'auto_run START id=' in x]
        if not st:
            return '-', []
        return re.search(r'auto_run START id=(\S+)', ls[st[-1]]).group(1), ls[st[-1]:]

    def hist(W, idx, ph, gate=None):
        out = []
        for f in sorted(glob.glob(os.path.join(W, 'status', 'history', 'P%s_%s.*.json' % (idx, ph)))):
            try:
                r = json.load(open(f))
            except ValueError:
                continue
            if gate is None or gate in gates(r):
                out.append(r)
        return out

    def d2dec(W):
        p = os.path.join(W, 'recon', 'd2_decision.json')
        return json.load(open(p)) if os.path.isfile(p) else {}

    def write_d2(W, line):
        with open(os.path.join(W, 'recon', 'd2.txt'), 'w') as fh:
            fh.write('# the self-test\'s operator\n%s\n' % line)

    def archives(W):
        return sorted(os.path.basename(x) for x in glob.glob(os.path.join(W, '_archive', 'd2_*')))

    def modes_of(W):
        p = os.path.join(W, 'recon', 'modes.json')
        return dict((r['date'], r.get('mode')) for r in json.load(open(p)).get('dates', [])) if os.path.isfile(p) else {}

    def refjson(W):
        p = os.path.join(W, 'recon', 'reference.json')
        return json.load(open(p)) if os.path.isfile(p) else {}

    def nothing_moved(W, l0, dates, ref=None, tops=('offsets', 'coregSLC', 'SLC')):
        """No take: no _archive/d2_*, no decision, no restart request; every date's SLC/ and every secondary's offsets/ in
        place, and the trees tops as in the listing l0."""
        return not archives(W) and not os.path.exists(os.path.join(W, 'recon', 'd2_decision.json')) \
            and not os.path.exists(os.path.join(W, 'status', 'restart.json')) \
            and all(os.path.isdir(os.path.join(W, 'SLC', d)) for d in dates) \
            and all(os.path.isdir(os.path.join(W, 'offsets', d)) for d in dates if d != ref) \
            and under(listing(W), tops) == under(l0, tops)

    def group(name, fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            import traceback
            case('%s stopped early by %s: %s' % (name, type(e).__name__, e), False, traceback.format_exc()[-900:])

    # =============================================================================== the mixed frame 3354: S3a and D
    W = fd('r5')
    rc0, _ = run('r5', ['--to', 'topo'])
    MODES = modes_of(W)
    DATES = sorted(MODES)
    REF = refjson(W).get('reference')
    RW = dict((x.get('date'), x) for x in ((rec('r5', '1br', 'rwin').get('outputs') or {}).get('dates') or []))
    PAIRS1 = (rec('r5', '2a', 'stack1').get('outputs') or {}).get('pair_list') or []
    if rc0 != 0 or len(DATES) != 12 or MODES.get(REF) != 'FBS' or REF != D[4]:
        case('M18-M80 not run: the mixed frame 3354 did not reach topo with 12 dates and the FBS reference %s' % D[4], False,
             'rc %d; %d dates; reference %s' % (rc0, len(DATES), REF))
        return
    snap('r5', FR, 'S3a')
    FBDD = [d for d in DATES if MODES[d] == 'FBD']
    DOFF = D[11]   # 20090302, FBS, the latest: off-frame at G21 under ask (D); stack1's network keeps L7 without it (20080830's
    # removal would leave 20061125 in one pair: L7, as M30 tests)
    l_s3a = listing(W)
    rcA, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_OFFFRAME': DOFF}, decide=False)
    rA = rec('r5', '3b', 'coarse')
    gA = gates(rA)
    limA = dict((x['id'], x) for x in r7of(rA).get('limits') or [])
    g7A = (rA.get('outputs') or {}).get('g7') or {}
    l_D = listing(W)
    sc_off = 'ALPSRP%05d%s' % (ORB[11], FR)
    rjA = json.load(open(os.path.join(W, 'recon', 'RECON.json')))
    fgA = ((rjA.get('framing') or {}).get('granules') or {}).get(sc_off) or {}
    case('M18b (11.10) under --decide ask, %s framed 3 km off along track (mkzip\'s g016, inside G0.16\'s 11.27 km line: G0.16 PASS '
         'keeps it, its dev_c about 3 km) and off-frame at G21 (LINOG_MOCK_OFFFRAME, 100 x: the mock geo2rdr does not derive its '
         'offsets from the framing): run_02 and run_03 run (G3b.8, G3b.9 PASS), G21 DECISION naming it, G21e INFO, G7 PASS, D2 '
         'DECISION with R7\'s proposal (F, its reading, L0 to L8 each holding) and the line that takes it; rc 4; nothing moved (no '
         '_archive/d2_*, recon/d2_decision.json or status/restart.json)' % DOFF,
         gates(rec('r5', '0a', 'recon')).get('G0.16') == 'PASS' and fgA.get('dev_c_km') is not None and 2.0 <= abs(fgA['dev_c_km']) <= 4.0
         and any(x.get('scene') == sc_off for x in rjA.get('kept') or [])
         and rcA == 4 and rA.get('verdict') == 'DECISION' and gA.get('G3b.8') == 'PASS' and gA.get('G3b.9') == 'PASS'
         and 'not run' not in gval(rA, 'G3b.9') and gA.get('G21') == 'DECISION' and DOFF in gval(rA, 'G21')
         and gA.get('G21e') == 'INFO' and gA.get('G7') == 'PASS' and gA.get('D2') == 'DECISION'
         and 'R7\'s proposal (11.2): take %s' % DOFF in gval(rA, 'D2') and 'write the one line "take %s"' % DOFF in gval(rA, 'D2')
         and 'OFF-FRAME' in gval(rA, 'D2') and r7of(rA).get('F') == [DOFF] and sorted(limA) == ['L%d' % i for i in range(9)]
         and all(x['ok'] for x in limA.values()) and nothing_moved(W, l_s3a, DATES, REF, ('SLC',)),
         'G0.16 %s, dev_c %s km; rc %d; %s; F %s; failing %s; D2 %s' % (
             gates(rec('r5', '0a', 'recon')).get('G0.16'), fgA.get('dev_c_km'), rcA, dict((k, gA.get(k)) for k in (
                 'G3b.8', 'G3b.9', 'G21', 'G7', 'D2')), r7of(rA).get('F'), failing(rA), gval(rA, 'D2')[:200]))
    rk8 = RW.get(D[8]) or {}
    case('M79 (18.4) %s (FBD), its image records\' column 0 one gate nearer than the leader\'s r0: rwin\'s k -1 and r0 set to r0 '
         '- 149.896229 m (G1br.8 PASS), every other date k 0; the mock\'s truth one gate off (LINOG_MOCK_GATEOFF) cancelled by '
         'that: G7 reads it ok and PASSes, R7 has no flag of it (only %s, G21\'s)' % (D[8], DOFF),
         rk8.get('k') == -1 and rk8.get('r0_after') is not None and rk8.get('r0_leader') is not None
         and abs(rk8['r0_after'] - (rk8['r0_leader'] - S.GATE)) < 1e-6
         and gates(rec('r5', '1br', 'rwin')).get('G1br.8') == 'PASS' and all((RW.get(d) or {}).get('k') == 0 for d in DATES if d != D[8])
         and ((g7A.get('dates') or {}).get(D[8]) or [None, None])[1] == 'ok' and gA.get('G7') == 'PASS' and r7of(rA).get('F') == [DOFF],
         'k %s, r0 %s -> %s; G7 %s %s' % (rk8.get('k'), rk8.get('r0_leader'), rk8.get('r0_after'), gA.get('G7'),
                                         (g7A.get('dates') or {}).get(D[8])))
    if rcA != 4 or r7of(rA).get('F') != [DOFF]:
        case('M18-M80 not run: the ask run did not stop at D2 on %s alone' % DOFF, False)
        return
    snap('r5', FR, 'D')

    def m18b():
        write_d2(W, 'take %s' % D[6])
        rcB, _ = run('r5', ['--to', 'coarse'], decide=False)
        rB = rec('r5', '3b', 'coarse')
        gB = gates(rB)
        case('M18b recon/d2.txt "take %s" (another date than the flag): not applied, D2t WARN, the DECISION stays, rc 4; coarse '
             'reuses the DECISION record\'s products (G3b.6 PASS by 11.5, G3b.8 and G3b.9 "not run"), G21 reads them again; '
             'nothing moved, the products unchanged' % D[6],
             rcB == 4 and gB.get('D2t') == 'WARN' and gB.get('D2') == 'DECISION' and gB.get('G3b.6') == 'PASS'
             and '(11.5)' in gval(rB, 'G3b.6') and 'not run' in gval(rB, 'G3b.8') and 'not run' in gval(rB, 'G3b.9')
             and gB.get('G21') == 'DECISION' and nothing_moved(W, l_D, DATES, REF)
             and ((rB.get('outputs') or {}).get('reused_from') or {}).get('start') == rA.get('start'),
             'rc %d; %s; reused from %s' % (rcB, dict((k, gB.get(k)) for k in ('G3b.6', 'G3b.9', 'G21', 'D2t', 'D2')),
                                           ((rB.get('outputs') or {}).get('reused_from') or {}).get('start')))
        write_d2(W, 'keep %s' % DOFF)
        rcC, _ = run('r5', ['--to', 'coarse'], decide=False)
        rC = rec('r5', '3b', 'coarse')
        gC = gates(rC)
        case('M18b recon/d2.txt "keep %s": G21 INFO (kept by the operator), D2 INFO with the file\'s md5, coarse PASS, rc 0; the '
             'date stays (recon/modes.json\'s 12 dates); nothing moved' % DOFF,
             rcC == 0 and rC.get('verdict') == 'PASS' and gC.get('G21') == 'INFO' and 'kept by the operator' in gval(rC, 'G21')
             and gC.get('D2') == 'INFO' and md5(os.path.join(W, 'recon', 'd2.txt')) in gval(rC, 'D2')
             and r7of(rC).get('kept_by_operator') is True and len(modes_of(W)) == 12 and nothing_moved(W, l_D, DATES, REF),
             'rc %d; %s' % (rcC, dict((k, gC.get(k)) for k in ('G3b.6', 'G21', 'G7', 'D2'))))
        write_d2(W, 'take %s' % DOFF)   # the part 5 review's P5-07: keep changed to take makes the PASS record STALE (11.6)
        rcK, outK = run('r5', ['--to', 'coarse'], decide=False)
        ridK, lrK = ledger_run(W)
        hK = (hist(W, '3b', 'coarse', 'G3b.11') or [{}])[-1]
        rK = rec('r5', '3b', 'coarse')
        case('M18b recon/d2.txt\'s "keep %s" changed to "take %s" after the keep\'s PASS (11.6): coarse STALE by the file\'s md5 in '
             'its fingerprint, the operator\'s take under ask on the keep record\'s products (reused, run_03 not run), G3b.11 PASS, '
             'one restart, the second pass\'s coarse PASS on the 10 left; rc 0' % (DOFF, DOFF),
             rcK == 0 and '-- P3b coarse: record STALE' in outK and gates(hK).get('G3b.11') == 'PASS'
             and ((hK.get('outputs') or {}).get('reused_from') or {}).get('start') == rC.get('start')
             and sum('auto_run RESTART id=%s after=coarse' % ridK in x for x in lrK) == 1 and rK.get('verdict') == 'PASS'
             and len((rK.get('outputs') or {}).get('secondaries') or []) == 10 and DOFF not in modes_of(W),
             'rc %d; STALE %s; take %s from %s; final %s' % (rcK, '-- P3b coarse: record STALE' in outK, gates(hK).get('G3b.11'),
                                                            ((hK.get('outputs') or {}).get('reused_from') or {}).get('start'),
                                                            rK.get('verdict')))
        restore('r5', FR, 'D', 'M18bt')
        write_d2(W, 'take %s' % DOFF)
        rcE, _ = run('r5', ['--to', 'coarse'], decide=False)
        rid, lr = ledger_run(W)
        hE = (hist(W, '3b', 'coarse', 'G3b.11') or [{}])[-1]
        dE = d2dec(W)
        rE = rec('r5', '3b', 'coarse')
        lp1 = (dE.get('loops') or [{}])[0]
        case('M18b recon/d2.txt "take %s" under ask: the operator\'s take on the DECISION record\'s products (G3b.6 PASS by 11.5, '
             'run_03 not run), G3b.11 PASS, G21 and D2 INFO; one restart after coarse; recon/d2_decision.json\'s loop 1 by the '
             'operator with the file\'s md5; the second pass\'s coarse PASS on the 10 secondaries left, by reuse; rc 0' % DOFF,
             rcE == 0 and sum('auto_run RESTART id=%s after=coarse' % rid in x for x in lr) == 1
             and sum('auto_run RESTART' in x for x in lr) == 1 and gates(hE).get('G3b.11') == 'PASS'
             and gates(hE).get('G3b.6') == 'PASS' and 'not run' in gval(hE, 'G3b.9') and gates(hE).get('D2') == 'INFO'
             and gates(hE).get('G21') == 'INFO' and 'the operator\'s take' in gval(hE, 'G21')
             and len(dE.get('loops') or []) == 1 and str(lp1.get('by')).startswith('the operator (recon/d2.txt "take %s"' % DOFF)
             and sorted(lp1.get('dates') or {}) == [DOFF] and rE.get('verdict') == 'PASS'
             and len((rE.get('outputs') or {}).get('secondaries') or []) == 10 and gates(rE).get('G3b.6') == 'PASS'
             and DOFF not in modes_of(W),
             'rc %d; restarts %s; take record %s; loops %d by %s; final %s %s' % (
                 rcE, [x[22:] for x in lr if 'RESTART' in x], dict((k, gates(hE).get(k)) for k in ('G3b.6', 'G3b.11', 'G21', 'D2')),
                 len(dE.get('loops') or []), str(lp1.get('by'))[:60], rE.get('verdict'),
                 len((rE.get('outputs') or {}).get('secondaries') or [])))
    group('M18b', m18b)

    def m18cd():   # the part 5 review's P5-07: the operator's file and the decision malformed
        restore('r5', FR, 'D', 'M18c')
        with open(os.path.join(W, 'recon', 'd2.txt'), 'w') as fh:
            fh.write('take %s\nkeep %s\n' % (DOFF, DOFF))
        rcc, _ = run('r5', ['--to', 'coarse'])
        rc_ = rec('r5', '3b', 'coarse')
        case('M18c (11.6) recon/d2.txt with two lines (take and keep): D2 DECISION "a person looks" naming the file, R7 taking nothing '
             'under auto, rc 4, nothing moved',
             rcc == 4 and gates(rc_).get('D2') == 'DECISION' and 'a person looks' in gval(rc_, 'D2')
             and '2 lines that are not comments' in gval(rc_, 'D2') and 'limits' not in r7of(rc_) and nothing_moved(W, l_D, DATES, REF),
             'rc %d; D2 %s' % (rcc, gval(rc_, 'D2')[:160]))
        restore('r5', FR, 'D', 'M18d')
        df = os.path.join(W, 'recon', 'd2_decision.json')
        with open(df, 'w') as fh:
            fh.write('{"loops": [1, ')
        rca, _ = run('r5', ['--to', 'coarse'])
        ra = rec('r5', '0a', 'recon')
        rcb, _ = run('r5', ['--only', 'reference'])
        rb = rec('r5', '2b', 'reference')
        rcc2, _ = run('r5', ['--only', 'coarse'])
        rc2 = rec('r5', '3b', 'coarse')
        with open(df, 'w') as fh:
            json.dump(dict(N0=12, reference=REF, loops=[dict(loop=1, dates=[DOFF])]), fh)
        rcd, _ = run('r5', ['--only', 'recon'])
        rd = rec('r5', '0a', 'recon')
        case('M18d (11.4, 11.7; P5-07, P5-09) recon/d2_decision.json not JSON: recon G0.4d FAIL, rc 2; the reference alone (--only): '
             'D1 FAIL, rc 2; coarse alone: D2 DECISION "a person looks", rc 4, nothing moved; a decision whose loop lists its dates (not '
             'R7\'s): recon G0.4d FAIL naming the loop, rc 2',
             rca == 2 and gates(ra).get('G0.4d') == 'FAIL' and 'is not JSON' in gval(ra, 'G0.4d') and rcb == 2
             and gates(rb).get('D1') == 'FAIL' and 'is not JSON' in gval(rb, 'D1') and rcc2 == 4 and gates(rc2).get('D2') == 'DECISION'
             and 'a person looks' in gval(rc2, 'D2') and 'is not JSON' in gval(rc2, 'D2')
             and not archives(W) and under(listing(W), ('offsets', 'coregSLC', 'SLC')) == under(l_D, ('offsets', 'coregSLC', 'SLC'))
             and rcd == 2 and gates(rd).get('G0.4d') == 'FAIL' and 'its loop 1 is not R7\'s' in gval(rd, 'G0.4d'),
             'recon rc %d %s; reference rc %d %s; coarse rc %d %s; recon (a list) rc %d %s' % (
                 rca, gval(ra, 'G0.4d')[:80], rcb, gval(rb, 'D1')[:60], rcc2, gval(rc2, 'D2')[:60], rcd, gval(rd, 'G0.4d')[:80]))
    group('M18c and M18d', m18cd)

    def m23():
        restore('r5', FR, 'D', 'M23')
        rcF, _ = run('r5', ['--only', 'coarse'])
        rF = rec('r5', '3b', 'coarse')
        case('M23 (11.10) --only coarse under auto: R7 reads LINOG_RESTART=no, L0 alone FAILs: D2 DECISION naming it, rc 4, before '
             'anything moves',
             rcF == 4 and failing(rF) == ['L0'] and gates(rF).get('D2') == 'DECISION' and 'L0' in gval(rF, 'D2')
             and 'LINOG_RESTART=no' in gval(rF, 'D2') and 'the way on: run the frame again without --only' in gval(rF, 'D2')
             and nothing_moved(W, l_D, DATES, REF),
             'rc %d; failing %s; D2 %s' % (rcF, failing(rF), gval(rF, 'D2')[:120]))
        write_d2(W, 'take %s' % DOFF)
        rcG, _ = run('r5', ['--only', 'coarse'])
        rG = rec('r5', '3b', 'coarse')
        case('M23b the operator\'s take under --only coarse: the same, L0 alone, D2 DECISION, rc 4, nothing moved',
             rcG == 4 and failing(rG) == ['L0'] and ((r7of(rG).get('d2_txt') or {}).get('verb')) == 'take'
             and gates(rG).get('D2') == 'DECISION' and nothing_moved(W, l_D, DATES, REF),
             'rc %d; failing %s; d2.txt %s' % (rcG, failing(rG), r7of(rG).get('d2_txt')))
    group('M23', m23)

    def m29():
        restore('r5', FR, 'D', 'M29a')
        os.makedirs(os.path.join(W, '_archive', 'd2_t29a'))
        rca, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2TAG': 't29a'})
        ra = rec('r5', '3b', 'coarse')
        oka = rca == 4 and failing(ra) == ['L6'] and '_archive/d2_t29a exists already' in gval(ra, 'D2') \
            and os.listdir(os.path.join(W, '_archive', 'd2_t29a')) == [] and os.path.isdir(os.path.join(W, 'SLC', DOFF)) \
            and not os.path.exists(os.path.join(W, 'recon', 'd2_decision.json'))
        rcb, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2TAG': 't29b', 'LINOG_MOCK_D2FAILAT': '3'})
        rb = rec('r5', '3b', 'coarse')
        ab = os.path.join(W, '_archive', 'd2_t29b')
        mv = open(os.path.join(ab, 'MOVES.txt')).read().splitlines() if os.path.isfile(os.path.join(ab, 'MOVES.txt')) else []
        zb = [x for x in mv if x.startswith('mv ')]
        okb = rcb == 2 and rb.get('verdict') == 'FAIL' and gates(rb).get('G3b.11') == 'FAIL' \
            and '(after 2 move(s) of the take)' in gval(rb, 'G3b.11') and len(zb) == 3 and zb[2].startswith('mv SLC/%s ->' % DOFF) \
            and mv[-1].startswith('# FAILED at the line above') and '2 move(s) made, nothing deleted' in mv[-1] \
            and os.path.islink(os.path.join(ab, DOFF, 'raw', os.path.basename(zb[0].split()[1]))) \
            and os.path.isdir(os.path.join(ab, DOFF, 'unzipped')) and os.path.isdir(os.path.join(W, 'SLC', DOFF)) \
            and os.path.isdir(os.path.join(W, 'offsets', DOFF)) and r7of(rb).get('moved') == 2 and r7of(rb).get('taken') is False \
            and not os.path.exists(os.path.join(W, 'recon', 'd2_decision.json')) \
            and not os.path.exists(os.path.join(W, 'status', 'restart.json'))
        restore('r5', FR, 'D', 'M29c')
        mark = os.path.join(T, 'r7_29c.mark')
        ph = subprocess.Popen(['bash', S.ENTRY, '084', FR, '--decide', 'auto', '--to', 'coarse'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, start_new_session=True,
                              env=popen_env('r5', {'LINOG_MOCK_D2SLEEP': '3', 'LINOG_MOCK_MARK': mark, 'LINOG_MOCK_D2TAG': 't29c'}))
        t0 = time.time()
        while not os.path.exists(mark) and ph.poll() is None and time.time() - t0 < 600:
            time.sleep(0.2)
        time.sleep(0.5)
        if ph.poll() is None:
            os.killpg(ph.pid, signal.SIGTERM)
        outc = ph.communicate(timeout=600)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 %s --decide auto --to coarse (r5, LINOG_MOCK_D2SLEEP, SIGTERM during the take) '
                     'rc %d\n%s' % (FR, ph.returncode, outc))
        rc_ = rec('r5', '3b', 'coarse')
        ac = os.path.join(W, '_archive', 'd2_t29c')
        mvc = open(os.path.join(ac, 'MOVES.txt')).read().splitlines() if os.path.isfile(os.path.join(ac, 'MOVES.txt')) else []
        dc = d2dec(W)
        nmv = sum(1 for x in mvc if x.startswith('mv '))
        okc = os.path.exists(mark) and ph.returncode == 143 and rc_.get('verdict') == 'ERROR' \
            and gates(rc_).get('G3b.11') in (None, 'PASS') and r7of(rc_).get('taken') is True and r7of(rc_).get('moved') == nmv \
            and bool(mvc) and mvc[-1] == '# %d moves made' % nmv and nmv >= 8 and len(dc.get('loops') or []) == 1 \
            and os.path.isfile(os.path.join(W, 'status', 'restart.json')) and not os.path.isdir(os.path.join(W, 'SLC', DOFF))
        rcd, outd = run('r5', ['--to', 'coarse'])
        rd = rec('r5', '3b', 'coarse')
        okd = rcd == 0 and 'restart request kept as status/restart_stale_' in outd and rd.get('verdict') == 'PASS' \
            and gates(rd).get('G3b.6') == 'PASS' and gates(rd).get('G21') == 'PASS' \
            and len((rd.get('outputs') or {}).get('secondaries') or []) == 10 and not os.path.exists(os.path.join(W, 'status', 'restart.json')) \
            and gates(rec('r5', '0a', 'recon')).get('G0.4d') == 'INFO'
        case('M29 (11.3, 11.10) a failed take: (a) the archive name taken (LINOG_MOCK_D2TAG, _archive/d2_t29a made first): L6 alone '
             'FAILs, D2 DECISION before anything moves, rc 4; (b) the third move made to fail (LINOG_MOCK_D2FAILAT=3): G3b.11 FAIL, rc 2, '
             'MOVES.txt naming the three moves tried and the failure, the two made in _archive/d2_t29b/, SLC/ and offsets/ of the date in '
             'place, no decision, no restart; (c) SIGTERM to the run\'s group 0.5 s into a take held 3 s (LINOG_MOCK_D2SLEEP): the take '
             'whole (MOVES.txt\'s last line, the decision, status/restart.json, the record\'s r7 taken with every move), then the stop: '
             'rc 143, coarse ERROR (the console gone, the gates after the take may be missing); the next run keeps the request aside, '
             'recon drops the date, coarse PASS by reuse on the 10 left, rc 0',
             oka and okb and okc and okd,
             '(a) %s rc %d %s; (b) %s rc %d %s %s; (c) %s rc %s %s %s; (d) %s rc %d %s' % (
                 oka, rca, failing(ra), okb, rcb, gval(rb, 'G3b.11')[:90], mv[-1:], okc, ph.returncode, rc_.get('verdict'), mvc[-1:],
                 okd, rcd, gates(rd).get('G3b.6')))
    group('M29', m29)

    def m20():
        restore('r5', FR, 'D', 'M20a')
        H = [D[1], D[3], D[6]]
        F4 = sorted(H + [DOFF])
        l7 = l7_expect(PAIRS1, F4, DATES)
        rca, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:' + ','.join(H)})
        ra = rec('r5', '3b', 'coarse')
        oka = rca == 4 and r7of(ra).get('F') == F4 and r7of(ra).get('hooked') == sorted(H) \
            and failing(ra) == (['L2'] if l7 else ['L2', 'L7']) and nothing_moved(W, l_D, DATES, REF) \
            and (not l7 or 'the way on: the operator\'s take (11.6) passes L2 with a WARN' in gval(ra, 'D2'))
        write_d2(W, 'take %s' % ' '.join(F4))
        rcb, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:' + ','.join(H)})
        rid, lr = ledger_run(W)
        hb = (hist(W, '3b', 'coarse', 'G3b.11') or [{}])[-1]
        db = d2dec(W)
        rb = rec('r5', '3b', 'coarse')
        okb = l7 and rcb == 0 and sum('after=coarse' in x and 'auto_run RESTART' in x for x in lr) == 1 \
            and gates(hb).get('D2w') == 'WARN' and '(ADMIT_EXCL_MAX_FRAC); passed by the operator\'s take' in gval(hb, 'D2w') \
            and gates(hb).get('G3b.11') == 'PASS' \
            and sorted(((db.get('loops') or [{}])[0]).get('dates') or {}) == F4 and rb.get('verdict') == 'PASS' \
            and len((rb.get('outputs') or {}).get('secondaries') or []) == 7 and not (set(F4) & set(modes_of(W)))
        case('M20 (11.3) L2: 4 of 12 dates flagged under auto (%s by the hook, %s by G21): D2 DECISION, L2 failing%s, its way on the '
             'operator\'s take (P5-02), rc 4, nothing moved; recon/d2.txt "take" of the 4: the operator\'s take passes L2 with D2w '
             'WARN, loop 1, the restart, coarse PASS on the 7 secondaries left' % (', '.join(H), DOFF, '' if l7 else
                                                                                  ' (with L7, as stack1\'s pairs give)'),
             oka and okb,
             '(a) %s rc %d F %s failing %s; (b) %s rc %d D2w %s; loop dates %s; final %s %d' % (
                 oka, rca, r7of(ra).get('F'), failing(ra), okb, rcb, gval(hb, 'D2w')[:80],
                 sorted(((db.get('loops') or [{}])[0]).get('dates') or {}), rb.get('verdict'),
                 len((rb.get('outputs') or {}).get('secondaries') or [])))
        restore('r5', FR, 'D', 'M20c')
        H4 = [d for d in DATES if d < REF]
        F5 = sorted(H4 + [DOFF])
        l7c = l7_expect(PAIRS1, F5, DATES)
        write_d2(W, 'take %s' % ' '.join(F5))
        rcc, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:' + ','.join(H4)})
        rc4 = rec('r5', '3b', 'coarse')
        l2 = dict((x['id'], x) for x in r7of(rc4).get('limits') or []).get('L2') or {}
        case('M20 L4: the operator\'s take of the %d dates before the reference %s (and %s) would make it the earliest date left (N23): '
             'L4 failing%s, L2 passed with its WARN flag, D2 DECISION, rc 4, nothing moved' % (len(H4), REF, DOFF,
                                                                                            '' if l7c else ' with L7'),
             rcc == 4 and failing(rc4) == (['L4'] if l7c else ['L4', 'L7']) and 'the earliest date left' in gval(rc4, 'D2')
             and l2.get('ok') is True and l2.get('warn') is True and nothing_moved(W, l_D, DATES, REF),
             'rc %d; failing %s; L2 %s' % (rcc, failing(rc4), l2))
    group('M20', m20)

    def m31():
        restore('r5', FR, 'D', 'M31')
        F8 = sorted(FBDD + [DOFF])
        l7 = l7_expect(PAIRS1, F8, DATES)
        write_d2(W, 'take %s' % ' '.join(F8))
        rc, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:' + ','.join(FBDD)})
        r = rec('r5', '3b', 'coarse')
        case('M31 (11.3) L8: the operator\'s take of every FBD date (%s) with %s would leave the mixed frame FBS-only: L8 failing%s, '
             'D2 DECISION naming the branch, rc 4, nothing moved' % (', '.join(FBDD), DOFF, '' if l7 else ' with L7'),
             rc == 4 and failing(r) == (['L7', 'L8'] if not l7 else ['L8']) and 'FBD+FBS, after the take FBS' in gval(r, 'D2')
             and nothing_moved(W, l_D, DATES, REF),
             'rc %d; failing %s; D2 %s' % (rc, failing(r), gval(r, 'D2')[:160]))
    group('M31', m31)

    def m21():
        restore('r5', FR, 'D', 'M21')
        d2_, d3_ = D[6], D[10]
        x7a = [] if l7_expect(PAIRS1, [DOFF, d2_], DATES) else ['L7']
        x7d = [] if l7_expect(PAIRS1, [DOFF, d2_, d3_], DATES) else ['L7']
        rca, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '2:%s' % d2_})
        rid, lr = ledger_run(W)
        ra = rec('r5', '3b', 'coarse')
        da = d2dec(W)
        oka = rca == 4 and sum('auto_run RESTART' in x for x in lr) == 1 and failing(ra) == ['L0', 'L1'] + x7a \
            and r7of(ra).get('F') == [d2_] and len(da.get('loops') or []) == 1 and os.path.isdir(os.path.join(W, 'offsets', d2_)) \
            and len(archives(W)) == 1 and DOFF not in modes_of(W)
        rcb, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '2:%s' % d2_})
        rb = rec('r5', '3b', 'coarse')
        okb = rcb == 4 and failing(rb) == ['L1'] + x7a and '1 loop(s) on record; R7 takes the first only' in gval(rb, 'D2') \
            and len(d2dec(W).get('loops') or []) == 1 and len(archives(W)) == 1
        write_d2(W, 'take %s' % d2_)
        rcc, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '2:%s' % d2_})
        rid, lr = ledger_run(W)
        dc = d2dec(W)
        rc_ = rec('r5', '3b', 'coarse')
        arc = archives(W)
        before = os.path.join(W, '_archive', arc[-1], 'd2_decision_before.json') if len(arc) == 2 else ''
        okc = not x7a and rcc == 0 and sum('auto_run RESTART' in x for x in lr) == 1 and len(dc.get('loops') or []) == 2 \
            and sorted(dc['loops'][1].get('dates') or {}) == [d2_] and str(dc['loops'][1].get('by')).startswith('the operator') \
            and sorted(dc.get('dates') or []) == sorted([DOFF, d2_]) and len(arc) == 2 and os.path.isfile(before) \
            and len(json.load(open(before)).get('loops') or []) == 1 and rc_.get('verdict') == 'PASS' \
            and len((rc_.get('outputs') or {}).get('secondaries') or []) == 9 \
            and '2 date(s) over 2 loop(s)' in gval(rec('r5', '0a', 'recon'), 'G0.4d')
        write_d2(W, 'take %s' % d3_)
        rcd, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '3:%s' % d3_})
        rd = rec('r5', '3b', 'coarse')
        okd = rcd == 4 and failing(rd) == ['L1'] + x7d and 'never a third' in gval(rd, 'D2') and len(d2dec(W).get('loops') or []) == 2 \
            and os.path.isdir(os.path.join(W, 'offsets', d3_)) and len(archives(W)) == 2
        case('M21 (11.10, R7-a) the loops: (a) a second flag after R7\'s first take, in the same run (LINOG_MOCK_D2FLAG=2:%s): one '
             'restart, then D2 DECISION with L0 (coarse has asked once) and L1 failing, nothing more moved, rc 4; (b) a new run under '
             'auto: L1 alone; (c) the operator\'s take of it: loop 2, the earlier decision copied into its archive folder, recon '
             'dropping both, coarse PASS on 9 secondaries, rc 0; (d) a third flag with the operator\'s take: L1 ("never a third"), '
             'D2 DECISION, nothing moved, rc 4' % d2_,
             oka and okb and okc and okd,
             '(a) %s rc %d failing %s; (b) %s rc %d %s; (c) %s rc %d loops %d archives %s; (d) %s rc %d %s' % (
                 oka, rca, failing(ra), okb, rcb, failing(rb), okc, rcc, len(dc.get('loops') or []), arc, okd, rcd, failing(rd)))
    group('M21', m21)

    def m18():
        restore('r5', FR, 'D', 'M18')
        t0 = md5(os.path.join(W, 'status', 'P3a_topo.json'))
        rc, out = run('r5', ['--to', 'igram'])
        rid, lr = ledger_run(W)
        h18 = (hist(W, '3b', 'coarse', 'G3b.11') or [{}])[-1]
        dd = d2dec(W)
        lp = (dd.get('loops') or [{}])[0]
        v = (lp.get('dates') or {}).get(DOFF) or {}
        arc = archives(W)
        ad = os.path.join(W, '_archive', arc[0]) if len(arc) == 1 else '/nonexistent'
        mv = open(os.path.join(ad, 'MOVES.txt')).read().splitlines() if os.path.isfile(os.path.join(ad, 'MOVES.txt')) else []
        R = dict((ph, rec('r5', i, ph)) for i, ph in PHASES18)
        rj = json.load(open(os.path.join(W, 'recon', 'RECON.json')))
        drop = [x for x in rj.get('dropped') or [] if x.get('scene') == v.get('granule')]
        stem, zp = v.get('stem') or '-', v.get('zip') or '-'
        mine = ('raw/%s' % zp, 'unzipped/%s' % stem, 'SLC/%s' % DOFF, 'offsets/%s' % DOFF, 'coregSLC/Coarse/%s' % DOFF)
        now = listing(W)
        p1 = under(now, ('raw', 'unzipped', 'SLC')) == under(l_D, ('raw', 'unzipped', 'SLC'), mine)
        p3 = under(now, ('offsets', 'coregSLC', 'merged/geom_reference', 'geom_reference')) == \
            under(l_D, ('offsets', 'coregSLC', 'merged/geom_reference', 'geom_reference'), mine)
        md = modes_of(W)
        rc_ = R['coarse']
        ok1 = rc == 0 and sum('auto_run RESTART' in x for x in lr) == 1 \
            and sum('auto_run RESTART id=%s after=coarse record=restart_%s_1.json' % (rid, rid) in x for x in lr) == 1 \
            and sum('auto_run END id=%s rc=0' % rid in x for x in lr) == 1 and not any('auto_topo START' in x for x in lr) \
            and sum('auto_coarse START' in x for x in lr) == 2 \
            and (json.load(open(os.path.join(W, 'status', 'restart_%s_1.json' % rid))) if os.path.isfile(
                os.path.join(W, 'status', 'restart_%s_1.json' % rid)) else {}).get('by') == 'coarse'
        ok2 = h18.get('verdict') == 'PASS' and gates(h18).get('G21') == 'INFO' and 'taken by R7, loop 1' in gval(h18, 'G21') \
            and gates(h18).get('G3b.11') == 'PASS' and gates(h18).get('D2') == 'INFO' and r7of(h18).get('taken') is True
        fmed = ((h18.get('outputs') or {}).get('g21') or {}).get('median')
        ok3 = dd.get('N0') == 12 and dd.get('reference') == REF and len(dd.get('loops') or []) == 1 and lp.get('loop') == 1 \
            and lp.get('by') == 'R7 under --decide auto' and sorted(lp.get('dates') or {}) == [DOFF] and v.get('mode') == 'FBS' \
            and 'OFF-FRAME' in str(v.get('g21')) and (v.get('rwin') or {}).get('k') == 0 \
            and fmed and lp.get('g21_frame_median') == fmed and v.get('g21_median') and v.get('g21_ratio') \
            and abs(v['g21_ratio'] - v['g21_median'] / fmed) <= 0.1 and v['g21_ratio'] > 5 \
            and sorted(x['id'] for x in lp.get('limits') or [] if x['ok']) == ['L%d' % i for i in range(9)]
        nmv = sum(1 for x in mv if x.startswith('mv '))
        ok4 = nmv in (8, 9) and [x.split()[1] for x in mv if x.startswith('mv ')][:5] == list(mine) and mv[-1] == '# %d moves made' % nmv \
            and os.path.islink(os.path.join(ad, DOFF, 'raw', zp)) and os.path.isdir(os.path.join(ad, DOFF, 'unzipped', stem)) \
            and os.path.isfile(os.path.join(ad, DOFF, 'SLC', DOFF, '%s.slc' % DOFF)) \
            and os.path.isfile(os.path.join(ad, DOFF, 'SLC', DOFF, '%s.slc.prefilter' % DOFF)) \
            and os.path.isdir(os.path.join(ad, DOFF, 'offsets', DOFF)) and os.path.isdir(os.path.join(ad, DOFF, 'coregSLC', 'Coarse', DOFF)) \
            and all(os.path.isdir(os.path.join(ad, 'stack2', x)) for x in ('configs', 'run_files', 'baselines'))
        ok5 = gates(R['recon']).get('G0.4d') == 'INFO' and len(drop) == 1 and drop[0].get('reason', '').startswith('R7 (D2), loop 1: ') \
            and p1 and len(md) == 11 and DOFF not in md and sum(1 for x in md.values() if x == 'FBS') == 7 \
            and refjson(W).get('reference') == REF and 'kept through coarse\'s D2 loop' in gval(R['reference'], 'D1') \
            and md5(os.path.join(W, 'status', 'P3a_topo.json')) == t0
        ok6 = rc_.get('verdict') == 'PASS' and gates(rc_).get('G3b.6') == 'PASS' and '(11.5)' in gval(rc_, 'G3b.6') \
            and 'not run' in gval(rc_, 'G3b.8') and 'not run' in gval(rc_, 'G3b.9') and gates(rc_).get('G21') == 'PASS' \
            and gates(rc_).get('G7') == 'PASS' and len((rc_.get('outputs') or {}).get('secondaries') or []) == 10 and p3 \
            and all(R[ph].get('verdict') == 'PASS' for ph in ('refine', 'invert', 'datum', 'fine', 'bgrid', 'igram'))
        case('M18 (11.10) R7 under --decide auto from the ask run\'s DECISION, to igram: rc 0; one restart after coarse (the ledger\'s '
             'RESTART line, restart_<run>_1.json by coarse), topo never started, coarse twice; the take\'s record: G21 INFO "taken by '
             'R7, loop 1", G3b.11 PASS, D2 INFO, PASS; recon/d2_decision.json: N0 12, the reference %s, loop 1 by R7 with the date\'s '
             'granule, mode, G21 row, median |az| and ratio and the frame median (P5-04), rwin record (k 0), the 9 limits held; '
             '_archive/d2_<UTC>/ with MOVES.txt (raw/<zip>, '
             'unzipped/<stem>, SLC, offsets, coregSLC/Coarse in that order, then stack2\'s) and each trace; recon\'s G0.4d INFO and '
             'the granule DROPPED "R7 (D2), loop 1: ..."; raw/, unzipped/ and SLC/ of the 11 dates as before (size and mtime); '
             'recon/modes.json 11 dates (7 FBS); the reference kept (D1); topo\'s record unchanged; coarse PASS by reuse (G3b.6, '
             'run_02 and run_03 not run), G21 and G7 PASS on 10 secondaries, their products and topo\'s as before; refine to igram '
             'PASS' % REF,
             ok1 and ok2 and ok3 and ok4 and ok5 and ok6,
             'rc %d; ledger %s; take %s; decision %s; moves %d %s; recon/modes/ref/topo %s; coarse %s %s' % (
                 rc, ok1, ok2, ok3, len(mv), ok4, ok5, ok6, dict((ph, R[ph].get('verdict')) for _, ph in PHASES18[10:])))
        rb = R['bandlimit']
        gi = (R['igram'].get('outputs') or {}).get('g11') or {}
        case('M26 (11.10) the mixed frame\'s loop: the FBS date\'s .slc and .slc.prefilter in its archive folder; bandlimit\'s second '
             'pass PASS with G1bl.11 INFO naming it (its progress lines kept, not acted on); D1f PASS (the FBS reference kept); igram\'s '
             'G11m PASS on 7 FBS dates, recon/modes.json\'s 7',
             os.path.isfile(os.path.join(ad, DOFF, 'SLC', DOFF, '%s.slc.prefilter' % DOFF)) and rb.get('verdict') == 'PASS'
             and gates(rb).get('G1bl.11') == 'INFO' and DOFF in gval(rb, 'G1bl.11') and gates(R['reference']).get('D1f') == 'PASS'
             and gates(R['igram']).get('G11m') == 'PASS' and gi.get('fbs_census') == 7 and gi.get('fbs_modes') == 7,
             'bandlimit %s G1bl.11 %s; D1f %s; G11m %s (%s, %s)' % (rb.get('verdict'), gval(rb, 'G1bl.11')[:80],
                                                                   gates(R['reference']).get('D1f'), gates(R['igram']).get('G11m'),
                                                                   gi.get('fbs_census'), gi.get('fbs_modes')))
        if not (ok1 and ok6):
            case('M27 and M22 not run: M18\'s loop did not end with coarse PASS by reuse (their frame is M18\'s)', False)
            return
        l1 = listing(W)
        rc2, out2 = run('r5', ['--to', 'igram'])
        rid2, lr2 = ledger_run(W)
        l2_ = listing(W)
        ch = sorted(k for k in set(l1) | set(l2_) if l1.get(k) != l2_.get(k) and k not in ('logs/STATUS.txt', 'status/.lock'))
        case('M27 (11.10) the same run again with nothing changed: every one of the 18 phases to igram CURRENT (skipped), no restart, '
             'rc 0; nothing written but the ledger and the lock (%d files compared)' % len(l1),
             rc2 == 0 and out2.count('skip: PASS on record, inputs unchanged') == 18 and not any('RESTART' in x for x in lr2)
             and not ch,
             'rc %d; skipped %d; changed %s' % (rc2, out2.count('skip: PASS on record, inputs unchanged'), ch[:6]))
        d22 = D[6]
        write_d2(W, 'take %s' % d22)
        l22 = listing(W)
        rc3, _ = run('r5', ['--to', 'coarse', '--force', 'coarse'], {'LINOG_MOCK_D2FLAG': '2:%s' % d22})
        r22 = rec('r5', '3b', 'coarse')
        l7 = l7_expect(PAIRS1, [DOFF, d22], DATES)
        lim5 = dict((x['id'], x) for x in r7of(r22).get('limits') or []).get('L5') or {}
        case('M22 (11.3) the operator\'s take of a second flag (%s, loop 2) on the frame past igram: L5 failing (refine\'s to igram\'s '
             'outputs in the frame)%s, D2 DECISION, rc 4, nothing moved' % (d22, '' if l7 else ' with L7'),
             rc3 == 4 and failing(r22) == (['L5'] if l7 else ['L5', 'L7']) and 'refineSecondaryTiming/pairs' in lim5.get('text', '')
             and 'Igrams' in lim5.get('text', '') and len(archives(W)) == 1 and os.path.isdir(os.path.join(W, 'offsets', d22))
             and len(d2dec(W).get('loops') or []) == 1
             and under(listing(W), ('offsets', 'coregSLC', 'SLC')) == under(l22, ('offsets', 'coregSLC', 'SLC')),
             'rc %d; failing %s; L5 %s' % (rc3, failing(r22), lim5.get('text', '')[:120]))
    group('M18', m18)

    def m19():
        restore('r5', FR, 'S3a', 'M19')
        n53, gdate = D[10], D[7]   # 20081130 FBS; 20080530 FBD, its records at r0 (rwin's k 0)
        rc, _ = run('r5', ['--to', 'coarse'], {'LINOG_MOCK_N53': n53, 'LINOG_MOCK_GATEOFF': '%s,%s:%r' % (G8, gdate, -S.GATE)})
        rid, lr = ledger_run(W)
        h = (hist(W, '3b', 'coarse', 'G3b.11') or [{}])[-1]
        dd = d2dec(W)
        lp = (dd.get('loops') or [{}])[0]
        vv = lp.get('dates') or {}
        g7 = ((h.get('outputs') or {}).get('g7') or {})
        calls = g7.get('calls') or {}
        rf = rec('r5', '3b', 'coarse')
        okh = h.get('verdict') == 'PASS' and gates(h).get('G3b.9') == 'PASS' and 'not run' not in gval(h, 'G3b.9') \
            and gates(h).get('G21') == 'PASS' and gates(h).get('G7') == 'INFO' and 'taken by R7, loop 1' in gval(h, 'G7') \
            and n53 in gval(h, 'G7') and gdate in gval(h, 'G7') and 'rwin k 0' in gval(h, 'G7') and gates(h).get('G3b.11') == 'PASS'
        okc = all(calls.get(d, {}).get('bang') == calls.get(d, {}).get('tot') and calls.get(d, {}).get('tot', 0) >= 3
                  and 31.0 <= (calls.get(d, {}).get('raw_dx') or 0) <= 34.0 for d in (n53, gdate)) \
            and gval(h, 'G7').count('raw dx +3') >= 2 and ((g7.get('dates') or {}).get(D[8]) or [None, None])[1] == 'ok'
        okd = sorted(vv) == sorted([n53, gdate]) and (vv.get(n53) or {}).get('mode') == 'FBS' and (vv.get(gdate) or {}).get('mode') == 'FBD' \
            and ((vv.get(gdate) or {}).get('rwin') or {}).get('k') == 0 and ((vv.get(n53) or {}).get('g7') or {}).get('bang', 0) >= 3 \
            and lp.get('by') == 'R7 under --decide auto'
        okf = rc == 0 and sum('auto_run RESTART id=%s after=coarse' % rid in x for x in lr) == 1 and rf.get('verdict') == 'PASS' \
            and gates(rf).get('G7') == 'PASS' and gates(rf).get('G3b.6') == 'PASS' and D[8] in modes_of(W) \
            and len((rf.get('outputs') or {}).get('secondaries') or []) == 9
        case('M19 and M80 (11.10, 18.4) a fresh run_03 under auto, N53 planted on %s (FBS, 32 samples, LINOG_MOCK_N53) and %s (FBD) a '
             'gate off with its records at r0 (LINOG_MOCK_GATEOFF, rwin\'s k 0, a cause no record shows): G7 calls both out on every '
             'voting window, raw dx 31 to 34 (18.4\'s line), %s (corrected by rwin) ok; R7 takes both in loop 1 (G7 INFO "taken by R7, '
             'loop 1" with each date\'s raw dx, calls and rwin record, G3b.11 PASS; the decision\'s G7 calls, modes and rwin k 0); one '
             'restart; the second pass\'s coarse '
             'PASS by reuse on the 9 left, G7 PASS; rc 0' % (n53, gdate, D[8]),
             okh and okc and okd and okf,
             'rc %d; take %s %s; calls %s; decision %s; final %s %s' % (
                 rc, okh, gval(h, 'G7')[:100], dict((d, calls.get(d)) for d in (n53, gdate)), okd, okf, rf.get('verdict')))
        if okf:
            snap('r5', FR, 'G')
            took.append((n53, gdate))
    took = []
    group('M19', m19)

    def m24(n53, gdate):
        dG = D[3]   # 20071013, a secondary left
        lG = listing(W)
        rf = rec('r5', '3b', 'coarse')
        res = {}

        def guard(tag, args, plant, want):
            restore('r5', FR, 'G', 'M24%s' % tag)
            plant()
            l0 = listing(W)
            rc, _ = run('r5', args)
            r = rec('r5', '3b', 'coarse')
            ok = rc == 4 and gates(r).get('G3b.6') == 'DECISION' and want in gval(r, 'G3b.6') and 'G3b.9' not in gates(r) \
                and under(listing(W), ('offsets', 'coregSLC')) == under(l0, ('offsets', 'coregSLC'))
            res[tag] = (ok, rc, gval(r, 'G3b.6')[-160:])

        def touch(rel):
            p = os.path.join(W, rel)
            unlink_copy(p)
            st_ = os.stat(p)
            os.utime(p, ns=(st_.st_atime_ns, st_.st_mtime_ns + 10 ** 9))

        def edit_cfg():
            lines = [x for x in open(os.path.join(W, 'run_files', 'run_03_geo2rdr_coarseResamp')) if dG in x]
            c = re.search(r'-c\s+(\S+)', lines[0]).group(1)
            with open(c, 'a') as fh:
                fh.write('# a line the self-test added\n')

        def edit_rec(fn):
            p = os.path.join(W, 'status', 'P3b_coarse.json')
            r = json.load(open(p))
            fn(r)
            with open(p, 'w') as fh:
                json.dump(r, fh, indent=1)
        fa = ['--only', 'coarse', '--force', 'coarse']
        guard('a', ['--to', 'coarse'], lambda: touch('offsets/%s/azimuth.off' % dG), '%s: offsets/%s/azimuth.off' % (dG, dG))
        guard('b', ['--only', 'coarse'], lambda: touch('SLC/%s/%s.slc' % (dG, dG)), '%s: its SLC identity changed' % dG)
        guard('c', ['--only', 'coarse'], lambda: touch('SLC/%s/data.dat' % dG) if os.path.isfile(os.path.join(W, 'SLC', dG, 'data.dat'))
              else touch('SLC/%s/data' % dG), '%s: its SLC identity changed' % dG)
        guard('d', ['--only', 'coarse'], edit_cfg, '%s: its run_02 or run_03 config changed' % dG)
        guard('e', fa, lambda: os.makedirs(os.path.join(W, 'offsets', '20990101')), 'hold other entries: 20990101')
        guard('f', fa, lambda: edit_rec(lambda r: r.update(gates=[g for g in r['gates'] if g['id'] != 'G3b.10'])),
              'G3b.10 None on the earlier record')
        guard('g', fa, lambda: edit_rec(lambda r: r['outputs'].pop('reuse', None)), 'holds no config md5s')
        restore('r5', FR, 'G', 'M24h')
        rc, _ = run('r5', fa)
        rh = rec('r5', '3b', 'coarse')
        okh = rc == 0 and rh.get('verdict') == 'PASS' and gates(rh).get('G3b.6') == 'PASS' and '(11.5)' in gval(rh, 'G3b.6') \
            and gates(rh).get('G21') == 'PASS' and gates(rh).get('G7') == 'PASS' \
            and under(listing(W), ('offsets', 'coregSLC')) == under(lG, ('offsets', 'coregSLC')) \
            and ((rh.get('outputs') or {}).get('reused_from') or {}).get('start') == rf.get('start')
        case('M24 (11.5, 11.10) the reuse guards on the frame after the loop, each G3b.6 DECISION with its reason, run_03 not run, the '
             'products unchanged, rc 4: (a) a secondary\'s azimuth.off touched; (b) its .slc touched; (c) its shelve touched; (d) its '
             'run_03 config changed; (e) a stray offsets/20990101/; (f) the record without G3b.10 (a run that ended before it); (g) '
             'the record without outputs.reuse (as v0.12\'s); (h) the positive control, coarse forced again: G3b.6 PASS by reuse, '
             'G21 and G7 PASS, rc 0',
             all(v[0] for v in res.values()) and len(res) == 7 and okh,
             '%s; (h) %s rc %d %s' % ('; '.join('(%s) %s rc %d %s' % (k, v[0], v[1], v[2][-90:]) for k, v in sorted(res.items())), okh, rc,
                                     gval(rh, 'G3b.6')[:80]))
    def state(ph):
        """The driver's --state of a phase (this Python, the standard library: as linog_auto.sh reads it)."""
        p = subprocess.run([sys.executable, '-B', os.path.join(S.HERE, 'lp_%s.py' % ph), '--path', '084', '--frame', FR, '--state'],
                           env=popen_env('r5', {}), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t = p.stdout.decode('utf-8', 'replace').strip().splitlines()
        return t[-1] if t else ''

    def m25b():   # the part 5 review's P5-01: admit's own count on a frame with R7's dates
        restore('r5', FR, 'G', 'M25b')
        n7 = len(d2dec(W).get('dates') or [])
        dead2 = [D[3], D[6]]   # 20071013 and 20080414: dead by their random pairs, no other date made thin or dead
        rca, _ = run('r5', ['--to', 'admit'], {'LINOG_MOCK_BADDATE': ','.join(dead2)})
        ra = rec('r5', '5a', 'admit')
        oka = n7 == 2 and rca == 4 and ra.get('verdict') == 'DECISION' and gates(ra).get('R3') == 'DECISION' \
            and '4 of 12 dates excluded: R3\'s 2 and R7\'s 2' in gval(ra, 'R3') and all(d in gval(ra, 'R3') for d in dead2) \
            and gates(ra).get('G5a.8') == 'INFO' and '2 date(s) taken by coarse' in gval(ra, 'G5a.8') \
            and not os.path.exists(os.path.join(W, 'recon', 'admission.json'))
        S.aside(T, os.path.join(W, 'Igrams'), 'M25b')
        rcb, _ = run('r5', ['--to', 'admit'], {'LINOG_MOCK_BADDATE': D[3]})
        rb = rec('r5', '5a', 'admit')
        adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
        okb = rcb == 0 and rb.get('verdict') == 'PASS' and gates(rb).get('R3') == 'INFO' and D[3] in gval(rb, 'R3') \
            and (adm.get('cfg') or {}).get('mintpy.network.excludeDate') == D[3]
        df = os.path.join(W, 'recon', 'd2_decision.json')
        st0 = state('admit')
        os.rename(df, df + '.aside')
        st1 = state('admit')
        os.rename(df + '.aside', df)
        st2 = state('admit')
        shutil.copy2(df, os.path.join(T, 'm25b_decision.json'))
        with open(df, 'w') as fh:
            fh.write('not JSON')
        rcc, _ = run('r5', ['--only', 'admit'])
        rc_ = rec('r5', '5a', 'admit')
        shutil.copy2(os.path.join(T, 'm25b_decision.json'), df)
        okc = st0 == 'CURRENT' and st1 == 'STALE' and st2 == 'CURRENT' and rcc == 2 and gates(rc_).get('G5a.8') == 'FAIL' \
            and 'is not JSON' in gval(rc_, 'G5a.8') and 'R3' not in gates(rc_)
        case('M25b (11.7, R7-e; the part 5 review\'s P5-01) admit on the frame after M19\'s loop (R7 took 2 of N0 12), igram, report '
             'and admit run: (a) 2 dead dates (LINOG_MOCK_BADDATE %s): R3 DECISION, "4 of 12 dates excluded: R3\'s 2 and R7\'s 2" '
             '(v0.12\'s count, 2 of 10, would take them), G5a.8 INFO, rc 4, no admission.json; (b) 1 dead date: 3 of 12, R3 INFO, '
             'admit PASS, admission.json excluding it; (c) admit\'s fingerprint holds the decision\'s md5 (--state CURRENT, STALE '
             'with the file aside, CURRENT again); (d) the decision not JSON: --only admit FAILs at G5a.8 before R3, rc 2' % ', '.join(dead2),
             oka and okb and okc,
             '(a) %s rc %d R3 %s; (b) %s rc %d R3 %s excludeDate %s; (c) %s %s %s %s, rc %d G5a.8 %s' % (
                 oka, rca, gval(ra, 'R3')[:120], okb, rcb, gates(rb).get('R3'), (adm.get('cfg') or {}).get('mintpy.network.excludeDate'),
                 okc, st0, st1, st2, rcc, gval(rc_, 'G5a.8')[:80]))

    if took:
        group('M24', lambda: m24(*took[0]))
        group('M25b', m25b)
    else:
        case('M24 and M25b not run: M19\'s loop did not end in coarse PASS (its frame is their base)', False)

    # =============================================================================== the FBD-only frame 3364, min_dates 6
    def fbd():
        WF = fd('f5', FR_FBD)
        rc, _ = run('f5', ['--to', 'coarse'], frame=FR_FBD)
        r0 = rec('f5', '3b', 'coarse', FR_FBD)
        MF = modes_of(WF)
        reff = refjson(WF).get('reference')
        secs = [d for d in sorted(MF) if d != reff]
        if rc != 0 or r0.get('verdict') != 'PASS' or len(MF) != 6 or set(MF.values()) != {'FBD'}:
            case('M20 (L3) and M32 not run: the FBD-only frame did not reach coarse PASS', False,
                 'rc %d; coarse %s; %d dates' % (rc, r0.get('verdict'), len(MF)))
            return
        snap('f5', FR_FBD, 'F3b')
        lF = listing(WF)
        pf1 = (rec('f5', '2a', 'stack1', FR_FBD).get('outputs') or {}).get('pair_list') or []
        early = min(MF)
        cand = [d for d in secs if d != early and l7_expect(pf1, [d], sorted(MF))]
        dF = (cand or [d for d in secs if d != early])[0]
        x7 = [] if cand else ['L7']
        rca, _ = run('f5', ['--to', 'coarse', '--force', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:%s' % dF}, frame=FR_FBD)
        ra = rec('f5', '3b', 'coarse', FR_FBD)
        write_d2(WF, 'take %s' % dF)
        rcb, _ = run('f5', ['--to', 'coarse'], {'LINOG_MOCK_D2FLAG': '1:%s' % dF}, frame=FR_FBD)
        rb = rec('f5', '3b', 'coarse', FR_FBD)
        case('M20 (11.3) L3 on the FBD-only frame (6 dates, the path table\'s min_dates 6): a flag on %s (the hook) under auto would '
             'leave 5: L3 failing%s, D2 DECISION, rc 4; the operator\'s take of it: the same; nothing moved; G21 and G7 PASS on the '
             'FBD-only frame (a gate 16 samples)' % (dF, ' (with L7: stack1\'s pairs on 6 dates lose a date\'s only pair, P5-11)'
                                                    if x7 else ''),
             rca == 4 and failing(ra) == ['L3'] + x7 and '5 dates left, min_dates 6' in gval(ra, 'D2') and rcb == 4
             and failing(rb) == ['L3'] + x7 and (r7of(rb).get('d2_txt') or {}).get('verb') == 'take' and gates(r0).get('G21') == 'PASS'
             and gates(r0).get('G7') == 'PASS' and nothing_moved(WF, lF, secs),
             '(a) rc %d failing %s; (b) rc %d failing %s' % (rca, failing(ra), rcb, failing(rb)))
        restore('f5', FR_FBD, 'F3b', 'M32')
        for x in ('offsets', 'coregSLC'):
            S.aside(T, os.path.join(WF, x), 'M32')
        d1, d2_, d3 = secs[0], secs[2], secs[3]
        rcm, _ = run('f5', ['--to', 'coarse'], {'LINOG_MOCK_AZNAN': d1, 'LINOG_MOCK_COARSEEMPTY': d2_, 'LINOG_MOCK_D2FLAG': '1:%s' % d3},
                     frame=FR_FBD)
        rm = rec('f5', '3b', 'coarse', FR_FBD)
        r7m = r7of(rm)
        calls = ((rm.get('outputs') or {}).get('g7') or {}).get('calls') or {}
        case('M32 (11.2, 11.10) unmeasured flags on the FBD-only frame under auto, run_03 run again: G21\'s row for %s with no ratio '
             '(LINOG_MOCK_AZNAN: its rows under the fill line) and G7\'s call-out of %s resting on EMPTY windows (LINOG_MOCK_COARSEEMPTY), '
             'a measured flag (%s, the hook) beside them: G21 and G7 DECISION, D2 DECISION naming both unmeasured, R7 taking nothing '
             '(no limits read, nothing moved, no decision), rc 4' % (d1, d2_, d3),
             rcm == 4 and gates(rm).get('G3b.9') == 'PASS' and gates(rm).get('G21') == 'DECISION' and gates(rm).get('G7') == 'DECISION'
             and gates(rm).get('D2') == 'DECISION' and 'R7 takes nothing' in gval(rm, 'D2') and sorted(r7m.get('unmeasured') or []) ==
             sorted([d1, d2_]) and r7m.get('F') == [d3] and 'limits' not in r7m and calls.get(d2_, {}).get('unread', 0) >= 3
             and calls.get(d2_, {}).get('bang') == 0 and not archives(WF)
             and not os.path.exists(os.path.join(WF, 'recon', 'd2_decision.json'))
             and not os.path.exists(os.path.join(WF, 'status', 'restart.json')),
             'rc %d; %s; unmeasured %s; F %s; %s calls %s' % (rcm, dict((k, gates(rm).get(k)) for k in ('G3b.9', 'G21', 'G7', 'D2')),
                                                             r7m.get('unmeasured'), r7m.get('F'), d2_, calls.get(d2_)))
    group('M20-L3 and M32', fbd)


def fcall(S, code, args):
    """Run code in this Python (the standard library and the pipeline's modules only), JSON on stdout."""
    p = subprocess.run([sys.executable, '-B', '-c', code] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'), 'PYTHONDONTWRITEBYTECODE': '1'})
    if p.returncode:
        return None, p.stderr.decode('utf-8', 'replace')[-600:]
    try:
        return json.loads(p.stdout.decode()), p.stderr.decode('utf-8', 'replace')
    except ValueError:
        return None, p.stdout.decode('utf-8', 'replace')[-600:]
