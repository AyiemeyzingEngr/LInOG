#!/usr/bin/env python3
"""lp_selftest13r2a.py -- linog_auto v0.13 r2, brief A: drop1's split rule, balanced (the ascending record 18.3), its guard on
the velocity (19.6, as 20.1 approved it; 22.2's notes 4 and 5) and the basis that keeps a decision file of the old rule from
being applied (D1d); called by lp_selftest.py as the suite 13r2a.

The frame: P084 F3320 of nine of felix's dates (ORBITS[9:18], 20080830 to 20100420), each granule at the Phase 3 frame's size
(1000 samples x 18432 lines; the multilooked grid 83 x 658, the Phase 5 cases' ground), in a root of its own (r2a), with the
shipped rules (cfg/mintpy_mock.cfg: DROP1_PEERS_SIDE 5, DROP1_PEERS_BALANCE 0.005, the cap ADMIT_CULL_MAX_FRAC at 10 %). Its
network under -t 730 -b 1500 with felix's baselines is 35 pairs, every date in 7 or more, so each pair's drop alone keeps it
one component with every date in 2 pairs or more. The frame runs once to bgrid (the copy S4e); each layout runs from that copy
with its plants at igram: LINOG_MOCK_COHPAIR gives every pair its coherence, LINOG_MOCK_BADPAIR the flagged pairs random phase
(R1 flags them over land and the grid), LINOG_MOCK_D1BAD their drops' gain in coherent land (the mock's other drops gain
nothing). The pairs are named from the frame's own sorted pair list (stack1's): F its 18th, G its 9th; the other pairs take a
layout's coherences in that order:
  B (balanced)  F 0.600; 5 pairs at 0.590 to 0.598 and 5 at 0.602 to 0.610 (their mean 0.600); the other 24 at 0.500 to 0.555
                and 0.650 to 0.760. F's drop gains 300 cells.
  S (short)     F 0.520; 4 pairs at 0.500 to 0.515 and 30 at 0.525 to 0.670. F's drop gains 300.
  U (unbalanced, and the pool's lowest)  G 0.450, under all 33 unflagged pairs; F 0.600, 5 pairs at 0.5982 to 0.5998 (within
                0.002 of it) and 5 at 0.632 to 0.650 (spread to 0.05: the 10 peers' mean 0.620, 0.020 above F); the other 23 at
                0.500 to 0.540 and 0.660 to 0.770. G's drop gains 500 cells, F's 300.
The mock's velocities move no cell by 1 mm/yr, so every test's n_dv_gt1 reads 0. M86 and M87 set the counts the guard reads in
the tests' own result.json by hand (the guard reads what drop1 records and runs no inversion, 19.6), and drop1, run again,
reads those tests again. M78 writes the decision file and drop1's record as v0.12 r2 (v0.13 r1's lp_drop1.py and drop1_basis,
LOGIC 1) would have written them on the same frame: V012_BASIS and V012_FP below are those two formulas, frozen.
Cases:
  M75  (18.3) layout U: G, under all the pool's coherence, with the largest net of the run (+500): kept, untestable ("0
       unflagged pairs below"), no cull; drop1 PASS, no decision file.
  M76  (18.3) layout B: F with 5 unflagged pairs on each side, their mean within 0.002 of its coherence, its net over every
       peer's: named (D1r), the guard PASS (0 at 0: at equality culled), R2's guards take the cull of 1 of 35; under --decide ask
       a DECISION, nothing moved; then under auto (the tests read again, none run) culled: the decision file, the restart, admit
       applies it, drop1 reads the cull in place.
  M76b (18.3, 22.2's note 4) lp_drop1's functions alone: the split at or below and above, ties to the earlier name, the two
       untestable texts as 18.3 gives them, the balance at its bound, the settings' checks of the two new keys and of
       DROP1_PEERS = 2 x DROP1_PEERS_SIDE, the fingerprint's rule "split5, balance 0.005", TEST_LOGIC 1 under LOGIC 2.
  M77  (18.3) F untestable two ways, its net over every one of its 10 nearest (v0.12 r2 would name it in both): layout S, 4
       unflagged pairs below it and 30 above; layout U, 5 below within 0.002 and 5 above spread to 0.05 (their mean 0.02 above).
  M78  (18.3's D1d) on M76's frame after its cull, the decision file and drop1's record as v0.12 r2 would have left them (its
       basis without DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE; LOGIC 1 and v0.12 r2's fingerprint): drop1 STALE; a run: admit
       re-reads the file, another basis, not applied (WARN, F back, 35 kept), mcfg stops at G5c.4 (mintpy/ in the way).
  M78b (D1d) r2's own file put back: admit applies it again (34 kept); then DROP1_PEERS_BALANCE 0.004: admit reads the file
       again (its fingerprint holds both keys while the file exists), another basis, not applied.
  M78c (18.3; 28.3 and 28.4's test root) on layout U's frame, drop1's record as v0.12 r2 wrote it: STALE, decides again, every
       test read again (none run), no cull again; the next run skips it (STALE once).
  M86  (19.6) layout B, F's n_dv_gt1 set over all its 10 peers' (900 against 500): under ask a DECISION carrying both counts
       (D1g INFO); under auto kept, D1g WARN naming it and both counts, no cull ("kept by the guard"), no decision file, no
       restart, PASS.
  M87  (19.6) layout B, F's n_dv_gt1 under its peers' highest (400 against 500): culled within R2's guards under auto (D1g
       PASS, the decision file, the restart, the cull in place).
v0.12's cases this brief changes (lp_selftest12.py; 18.3 names lp_selftest56.py, but v0.12's drop1 cases are lp_selftest12's,
as lp_selftest56's own docstring says, and none of lp_selftest56's changes):
  every case whose flagged pair AB (0.55) must be tested: under v0.12 r2 its 5 peers all sat above it (0.59), which the split
  rule keeps untestable; the plant LINOG_MOCK_COHPAIR now gives BC 0.50 and CD 0.53 (2 below, AC, AD and BD at 0.59 above), and
  the cases' cfgs DROP1_PEERS_SIDE 2 (DROP1_PEERS 4: the 6-pair frame's pool of 5 holds no 5 a side): AB is tested against CD,
  BC, AC and AD (their mean 0.5525, 0.0025 above it), so 6 inversions where there were 7. Changed in their plants, cfgs or
  counts, each keeping what it tests: T320 (6 tests, 4 peers, D1r "named", D1g PASS), T321 (the plant, CD still the peer
  whose drop gains more), T322 (AB and CD at 0.55, each with BC 0.50 and BD 0.52 below, AC and AD above) and T322b (the
  shipped cap with DROP1_PEERS_SIDE 2), T324 (4 peers), T324b (6 read again), T326 (6 tests), T329 (5 others complete), T330
  (its cfg with DROP1_PEERS_SIDE 2; 5 read again), T329b (5 read again), T333 (its threshold cfg with DROP1_PEERS_SIDE 2) and
  T339 (6 inversions and keys); T320b, T323, T323b, T325, T326b, T330b, T334, T335, T336 and T337 read as before with P1's
  plant and the cfgs' DROP1_PEERS_SIDE 2; T327 and T328 are unchanged;
  T331 (lp_drop1's functions) reads the split, its texts and its ties for v0.12 r2's nearest peers;
  T331b reads the minimum peer count through the split rule, the zero test's "no flagged pair testable" and the settings'
  checks of the new keys, admit's basis also by the side and the balance;
  T332 (the peers by coherence): DROP1_PEERS_SIDE 1, CD 0.54 below and BC 0.56 above: its peers CD and BC;
  T338 (the minimum peer count in a run, v0.12 r2) reads the split's settings in the fingerprint instead: DROP1_PEERS_SIDE 3
  keeps AB untestable (2 below), then 2 names it from the tests already made (none run);
  T339b keeps AB by DROP1_PEERS_BALANCE 0 (its peers' mean 0.0025 off) where v0.12 r2 kept it by DROP1_MIN_PEERS 6, over its
  peers.
"""
import glob
import json
import os
import shutil
import socket
import subprocess

ROOT, FRAME, CFG = 'r2a', '3320', 'paths_r2a.cfg'
ORB9 = slice(9, 18)   # ORBITS[9:18]: 20080830 to 20100420
V012 = 'linog_auto v0.12 r2 (2026-10-09)'
V012_SET_KEYS = ('DROP1_PEERS', 'DROP1_MIN_PEERS', 'DROP1_TCOH_MIN', 'DROP1_WORKERS', 'DROP1_TIMEOUT_S', 'DROP1_FREE_GIB')
V012_RULE = ('a flagged pair is culled when its net (coherent land gained minus lost when it is dropped) exceeds every one of its '
             'peers\' nets and it was tested against DROP1_MIN_PEERS peers or more; the cull taken whole when it is ADMIT_CULL_MAX_FRAC '
             'of the pairs or fewer and leaves one component with every date in 2 pairs or more, otherwise none (record 124.7; the '
             'minimum, 127)')
R2_KEYS = ('rule_id', 'side', 'balance', 'guard', 'named')   # what v0.13 r2's decision file adds to v0.12 r2's


def V012_BASIS(C, flagged, under, m):
    """lp_admit.drop1_basis as v0.13 r1 (v0.12 r2's rule) has it: no DROP1_PEERS_SIDE, no DROP1_PEERS_BALANCE."""
    return C.md5_obj(dict(flagged=sorted(flagged), under_floor=bool(under), peers=m.get('DROP1_PEERS'), thr=m.get('DROP1_TCOH_MIN'),
                          cap=m.get('ADMIT_CULL_MAX_FRAC'), min_peers=m.get('DROP1_MIN_PEERS')))


def V012_FP(C, D1, W, m, rec):
    """drop1's fingerprint as v0.13 r1's lp_drop1.py (LOGIC 1) computes it on this frame's records and files."""
    rs, ra, ri = rec('5d', 'sbas'), rec('5a', 'admit'), rec('4f', 'igram')
    ao = ra.get('outputs') or {}
    df = os.path.join(W, 'recon', 'drop1_decision.json')
    op_d3 = str(((ao.get('decisions') or {}).get('d3') or {}).get('source') or '').startswith('the operator')
    return C.md5_obj(dict(logic=1, sbas=(rs.get('outputs') or {}).get('digest'), admit=ao.get('decisions_md5'), handoff=ao.get('drop1_md5'),
                          network=ao.get('network_md5'), igram=(ri.get('outputs') or {}).get('digest'),
                          settings=dict((k, m.get(k)) for k in V012_SET_KEYS + ('ADMIT_CULL_MAX_FRAC', 'ADMIT_LAND_MIN_PX')),
                          mintpy=m['MINTPY_VERSION'], defaults=m['MINTPY_DEFAULTS_MD5'], decision=C.md5_file(df) if os.path.isfile(df) else None,
                          operator=op_d3, beside=D1.beside_md5(W)))


def cfg_dict(path):
    """linog_mintpy.cfg's KEY=value lines (not CFG.*) as strings, as lp_p5.load_mintpy reads them."""
    d = {}
    for ln in open(path):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln and not ln.startswith('CFG.'):
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def layouts(pl):
    """The three layouts on the sorted pair list pl: dict(name: (coherence by pair, flagged pairs, D1BAD plant, parts))."""
    F, G = pl[17], pl[8]
    o = [p for p in pl if p != F]
    b = {F: 0.600}
    b.update((p, round(0.590 + 0.002 * i, 4)) for i, p in enumerate(o[:5]))
    b.update((p, round(0.602 + 0.002 * i, 4)) for i, p in enumerate(o[5:10]))
    b.update((p, round(0.500 + 0.005 * i, 4)) for i, p in enumerate(o[10:22]))
    b.update((p, round(0.650 + 0.010 * i, 4)) for i, p in enumerate(o[22:]))
    s = {F: 0.520}
    s.update((p, round(0.500 + 0.005 * i, 4)) for i, p in enumerate(o[:4]))
    s.update((p, round(0.525 + 0.005 * i, 4)) for i, p in enumerate(o[4:]))
    o2 = [p for p in pl if p not in (F, G)]
    u = {F: 0.600, G: 0.450}
    u.update((p, x) for p, x in zip(o2[:5], (0.5982, 0.5986, 0.5990, 0.5994, 0.5998)))
    u.update((p, x) for p, x in zip(o2[5:10], (0.632, 0.637, 0.641, 0.645, 0.650)))
    u.update((p, round(0.500 + 0.004 * i, 4)) for i, p in enumerate(o2[10:21]))
    u.update((p, round(0.660 + 0.010 * i, 4)) for i, p in enumerate(o2[21:]))
    return dict(B=(b, [F], '%s:300' % F, dict(below=o[:5], above=o[5:10])),
                S=(s, [F], '%s:300' % F, dict(below=o[:4], above=o[4:9])),
                U=(u, [G, F], '%s:500,%s:300' % (G, F), dict(below=o2[:5], above=o2[5:10], g_above=sorted(o2[10:15]))))


def plants(lay):
    coh, flagged, bad, _ = lay
    return {'LINOG_MOCK_BADPAIR': ','.join(flagged), 'LINOG_MOCK_D1BAD': bad,
            'LINOG_MOCK_COHPAIR': ','.join('%s:%.4f' % (p, coh[p]) for p in sorted(coh))}


def v012_nearest(F, coh, pool, n=10):
    """v0.12 r2's peers of F: the n pool pairs nearest it in coherence, ties to the earlier name (v0.13 r1's pick_peers)."""
    return sorted(pool, key=lambda p: (abs(coh[p] - coh[F]), p))[:n]


def phase13_r2a(T, case, S):
    import lp_admit as A
    import lp_common as C
    import lp_drop1 as D1
    print('-- v0.13 r2 (brief A): drop1\'s split rule, balanced (18.3), its guard (19.6) and D1d; P084 F3320 of 9 dates (35 pairs) '
          'in its own root')
    W = S.fdir(T, FRAME, ROOT)
    MC = os.path.join(T, 'cfg', 'mintpy_mock.cfg')
    DF = os.path.join(W, 'recon', 'drop1_decision.json')
    m = cfg_dict(MC)

    # M76b: lp_drop1's functions alone (standard library; no frame)
    mc = {'F': 0.5, 'e': 0.5, 'b1': 0.498, 'b2': 0.496, 'b3': 0.494, 'b4': 0.492, 'b0': 0.49, 'a1': 0.502, 'a2': 0.504, 'a3': 0.506,
          'a4': 0.508, 'a5': 0.51, 'a6': 0.51, 'x': 0.7}
    sp = D1.pick_peers('F', mc, sorted(k for k in mc if k != 'F'), 5)
    tie = D1.pick_peers('F', dict(mc, a6=0.502), sorted(k for k in mc if k != 'F'), 1)
    q = dict((k, 0.5) for k in ('F', 'a', 'b'))
    q.update(a=0.5078125, b=0.5)   # exact in binary: the mean 0.50390625 lies 0.00390625 above F
    at_bound = D1.rule(['F'], dict(F=9, a=0, b=0), {'F': (['b'], ['a'])}, q, 1, 0.00390625)
    over_bound = D1.rule(['F'], dict(F=9, a=0, b=0), {'F': (['b'], ['a'])}, q, 1, 0.0039)
    m2 = {'F': 0.4198, 'b1': 0.41, 'b2': 0.40, 'a1': 0.43, 'a2': 0.44, 'a3': 0.45, 'a4': 0.46, 'a5': 0.47}
    sh = D1.rule(['F'], dict((k, 0) for k in m2), {'F': D1.pick_peers('F', m2, [k for k in m2 if k != 'F'], 5)}, m2, 5, 0.005)
    # 18.3's example on F3310's pool: at 0.5993 the 5 below lie within 0.0105 and the 5 above reach 0.6487, their mean 0.6151
    m3 = {'F': 0.5993, 'b1': 0.5993, 'b2': 0.5990, 'b3': 0.5980, 'b4': 0.5950, 'b5': 0.5888, 'a1': 0.6200, 'a2': 0.6300, 'a3': 0.6322,
          'a4': 0.6400, 'a5': 0.6487}
    ub = D1.rule(['F'], dict((k, 0) for k in m3), {'F': D1.pick_peers('F', m3, [k for k in m3 if k != 'F'], 5)}, m3, 5, 0.005)
    s0 = dict(DROP1_PEERS='10', DROP1_MIN_PEERS='10', DROP1_PEERS_SIDE='5', DROP1_PEERS_BALANCE='0.005', DROP1_TCOH_MIN='0.70',
              DROP1_WORKERS='8', DROP1_TIMEOUT_S='1800', DROP1_FREE_GIB='10', ADMIT_CULL_MAX_FRAC='0.10', mintpy_cfg_file='linog_mintpy.cfg')
    sv, sb = D1.read_settings(s0)
    bad = dict((tag, D1.read_settings(x)[1]) for tag, x in (
        ('peers', dict(s0, DROP1_PEERS='12')), ('side', dict((k, v) for k, v in s0.items() if k != 'DROP1_PEERS_SIDE')),
        ('bal', dict(s0, DROP1_PEERS_BALANCE='1.5')), ('balneg', dict(s0, DROP1_PEERS_BALANCE='-0.1')),
        ('min', dict(s0, DROP1_MIN_PEERS='11'))))
    ok76b = (sp == (['e', 'b1', 'b2', 'b3', 'b4'], ['a1', 'a2', 'a3', 'a4', 'a5']) and tie == (['e'], ['a1'])
             and at_bound[0]['testable'] is True and at_bound[0]['culled'] is True and over_bound[0]['testable'] is False
             and sh[0]['why'] == 'untestable: 2 unflagged pairs below its coherence 0.4198, 5 asked: kept' and sh[0]['margin'] is None
             and ub[0]['why'] == 'untestable: its peers\' mean coherence 0.6151, 0.0158 above its 0.5993 (0.005 asked): kept'
             and not sb and sv.get('DROP1_PEERS_SIDE') == 5 and sv.get('DROP1_PEERS_BALANCE') == 0.005
             and any('not 2 x DROP1_PEERS_SIDE = 10' in x for x in bad['peers']) and any('DROP1_PEERS_SIDE absent' in x for x in bad['side'])
             and any('not from 0 to under 1' in x for x in bad['bal']) and any('not from 0 to under 1' in x for x in bad['balneg'])
             and any('over DROP1_PEERS = 10' in x for x in bad['min']) and D1.rule_id(s0) == 'split5, balance 0.005'
             and D1.LOGIC == 2 and D1.TEST_LOGIC == 1
             and A.drop1_basis(['x'], False, s0) != A.drop1_basis(['x'], False, dict(s0, DROP1_PEERS_BALANCE='0.004'))
             and A.drop1_basis(['x'], False, s0) != A.drop1_basis(['x'], False, dict(s0, DROP1_PEERS_SIDE='4'))
             and A.drop1_basis(['x'], False, s0) != V012_BASIS(C, ['x'], False, s0))
    case('M76b (18.3, 22.2\'s note 4) lp_drop1\'s functions alone: the split takes the 5 nearest at or below the pair\'s coherence (one '
         'equal to it among them) and the 5 nearest above, ties to the earlier name; the balance at its bound tests the pair, a hair '
         'inside it keeps it; the two untestable texts as 18.3 gives them ("2 unflagged pairs below its coherence 0.4198, 5 asked", '
         '"its peers\' mean coherence 0.6151, 0.0158 above its 0.5993 (0.005 asked)"); the settings: both new keys read, DROP1_PEERS 12 '
         'refused (not 2 x DROP1_PEERS_SIDE), the side absent, a balance of 1.5 or -0.1, DROP1_MIN_PEERS over DROP1_PEERS; the '
         'fingerprint\'s rule "split5, balance 0.005"; LOGIC 2 with TEST_LOGIC 1; admit\'s basis moves with the side and the '
         'balance, and differs from v0.12 r2\'s',
         ok76b, 'split %s; tie %s; bound %s/%s; %s | %s; settings %s %s; rule %s' % (
             sp, tie, at_bound[0]['why'], over_bound[0]['why'], sh[0]['why'], ub[0]['why'], sb, bad, D1.rule_id(s0)))

    if not S.MOCKPY[0]:
        case('M75-M87 not run: the mock ISCE steps and the mock MintPy need numpy, and neither Python tried has it', False)
        return
    arc = os.path.join(T, 'archive_r2a', 'alos')
    for orb in S.ORBITS[ORB9]:
        S.mkzip(os.path.join(arc, '30'), orb, FRAME, width=S.P3_WIDTH, lines=S.P3_LINES)
    p3 = open(os.path.join(T, 'cfg', 'paths_p3.cfg')).read()
    a3 = 'archive = %s\n' % os.path.join(T, 'archive_p3', 'alos')
    assert p3.count(a3) == 1, 'paths_p3.cfg names the Phase 3 archive once'
    with open(os.path.join(T, 'cfg', CFG), 'w') as fh:
        fh.write(p3.replace(a3, 'archive = %s\n' % arc))

    def run(args, extra=None, decide='auto', mcfg=None):
        e = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MINTPY_CFG': mcfg or MC}
        e.update(extra or {})
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg=CFG, env_extra=e, keep_default=True)

    def state_of(ph, mcfg=None):
        """The phase's state as the driver reads it: its --state under the driver's python3 (-E -B)."""
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', CFG), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_ROOT=os.path.join(T, ROOT), LINOG_MINTPY_CFG=mcfg or MC)
        p = subprocess.run(['python3', '-E', '-B', os.path.join(S.HERE, 'lp_%s.py' % ph), '--path', '084', '--frame', FRAME, '--state'],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = p.stdout.decode('utf-8', 'replace').strip().splitlines()
        return lines[-1] if lines else ''

    def rec(idx, ph):
        return S.rec(T, FRAME, idx, ph, ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gl(r, gid):
        return [x for x in (r or {}).get('gates', []) if x['id'] == gid]

    def val(r, gid):
        x = gl(r, gid)
        return x[-1].get('value', '') + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def out(r):
        return (r or {}).get('outputs') or {}

    def jload(p):
        try:
            return json.load(open(p))
        except (OSError, ValueError):
            return {}

    def jsave(p, obj):
        with open(p, 'w') as fh:
            json.dump(obj, fh, indent=1)
            fh.write('\n')

    def copy_fn(src, dst):   # as lp_selftest12: mintpy/'s files always copied (the mock and the kit write some in place)
        if os.path.getsize(src) > (1 << 20) and '%smintpy%s' % (os.sep, os.sep) not in src:
            os.link(src, dst)
        else:
            shutil.copy2(src, dst)

    def snap(name):
        shutil.copytree(W, os.path.join(T, 'snap_r2a', name), symlinks=True, copy_function=copy_fn)

    def restore(name, tag):
        if os.path.exists(W):
            S.aside(T, W, 'r2a_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_r2a', name), W, symlinks=True, copy_function=copy_fn)

    def ledger():
        p = os.path.join(W, 'logs', 'STATUS.txt')
        return open(p).read() if os.path.isfile(p) else ''

    def last_run(led):
        ids = [x.split('id=')[1].split()[0] for x in led.splitlines() if 'auto_run START id=' in x]
        return ids[-1] if ids else '-'

    def history(ph, idx):
        h = sorted(glob.glob(os.path.join(W, 'status', 'history', 'P%s_%s.*.json' % (idx, ph))))
        return jload(h[-1]) if h else {}

    def table(r):
        return dict((x['pair'], x) for x in out(r).get('table') or [])

    def run_tests(r):
        """{pair or 'zero': its drop1.json test entry} of drop1's evidence folder on record."""
        return (jload(os.path.join(W, out(r).get('folder') or '-', 'drop1.json')).get('tests') or {})

    def set_counts(r, counts):
        """The n_dv_gt1 each test recorded, set by hand in its result.json (the folder that made it, as drop1.json names it)."""
        tt = run_tests(r)
        for p, n in counts.items():
            f = os.path.join(W, (tt.get(p) or {}).get('folder') or '-', 'result.json')
            j = jload(f)
            j['n_dv_gt1'] = n
            jsave(f, j)
        return sorted(counts)

    # ------------------------------------------------------------------ the frame to bgrid, once
    rc0, _ = run(['--to', 'bgrid'])
    r1, r2 = rec('2a', 'stack1'), rec('2c', 'stack2')
    pl = sorted('%s_%s' % tuple(x) for x in (out(r1).get('pair_list') or []))
    deg = {}
    for p in pl:
        for d in p.split('_'):
            deg[d] = deg.get(d, 0) + 1
    if not (rc0 == 0 and len(pl) == 35 and out(r2).get('pairs') == 35 and min(deg.values() or [0]) >= 3):
        case('M75-M87 not run: the 9-date frame did not reach bgrid with its 35 pairs (rc %d, %d pairs, stack2 %s, least degree %s)' % (
            rc0, len(pl), out(r2).get('pairs'), min(deg.values() or [0])), False)
        return
    snap('S4e')
    L = layouts(pl)
    F, G = pl[17], pl[8]

    # ------------------------------------------------------------------ M76: layout B under ask, then under auto
    LB = L['B']
    PB = plants(LB)
    restore('S4e', 'M76')
    rc, _ = run(['--to', 'drop1'], PB, decide='ask')
    rd, ra = rec('5d1', 'drop1'), rec('5a', 'admit')
    x = table(rd).get(F) or {}
    hand = ((out(ra).get('decisions') or {}).get('drop1') or {})
    ok_a = (rc == 4 and rd.get('verdict') == 'DECISION' and out(rd).get('state') == 'cull asked' and hand.get('in_network') == [F]
            and x.get('below') == LB[3]['below'][::-1] and x.get('above') == LB[3]['above'] and abs(x.get('offset') or 1) < 0.002
            and x.get('testable') is True and x.get('culled') is True and x.get('net') == 300 and x.get('peers_max') == 0
            and x.get('margin') == 300 and len(x.get('peers') or []) == 10
            and any(g['value'].startswith('named: +300 exceeds every peer\'s (max +0 of 10); its coherence 0.6000, its peers 5 below and '
                                          '5 above: 0.5900 to 0.6100') for g in gl(rd, 'D1r'))
            and gates(rd).get('D1g') == 'PASS' and '%s: n_dv_gt1 0 at its peers\' highest 0' % F in val(rd, 'D1g')
            and gates(rd).get('R2c') == 'INFO' and '1 of 35 pairs (2.9 %)' in val(rd, 'R2c')
            and 'the rule names 1 pair (%s)' % F in val(rd, 'D1') and 'admission.txt' in val(rd, 'D1')
            and out(rd).get('tests') == 12 and out(rd).get('ran') == 12 and out(rd).get('rule_id') == 'split5, balance 0.005'
            and rd.get('logic') == 2 and not os.path.exists(DF) and os.path.isdir(os.path.join(W, 'mintpy')))
    da = dict(rc=rc, verdict=rd.get('verdict'), state=out(rd).get('state'), row={k: x.get(k) for k in ('below', 'above', 'offset', 'net',
                                                                                                     'peers_max', 'culled')},
              d1r=[g['value'][:110] for g in gl(rd, 'D1r')], d1g=val(rd, 'D1g')[:90], r2c=val(rd, 'R2c')[:60], tests=out(rd).get('tests'))
    snap('S5d1B')
    restore('S5d1B', 'M76b')
    rc, _ = run(['--to', 'drop1'], PB)
    led = ledger()
    rid = last_run(led)
    h1, rd, ra = history('drop1', '5d1'), rec('5d1', 'drop1'), rec('5a', 'admit')
    dec = jload(DF)
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    ok_b = (rc == 0 and out(h1).get('state') == 'cull taken' and gates(h1).get('G5d1.10') == 'PASS' and gates(h1).get('D1g') == 'PASS'
            and out(h1).get('reused') == 12 and out(h1).get('ran') == 0 and dec.get('cull') == [F] and dec.get('named') == [F]
            and dec.get('rule_id') == 'split5, balance 0.005' and (dec.get('guard') or [{}])[0].get('over') is False
            and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1 and gates(ra).get('D1d') == 'INFO' and adm.get('kept') == 34
            and F not in (adm.get('kept_pairs') or []) and out(rd).get('state') == 'cull in place' and gates(rd).get('D1c') == 'INFO'
            and gates(rd).get('D1g') == 'PASS' and rd.get('verdict') == 'PASS')
    db = dict(rc=rc, pass1=out(h1).get('state'), reused=out(h1).get('reused'), ran=out(h1).get('ran'), cull=dec.get('cull'),
              d1d=gates(ra).get('D1d'), kept=adm.get('kept'), drop1=out(rd).get('state'), d1g=gates(rd).get('D1g'))
    case('M76 (18.3) layout B: %s at 0.600 with 5 unflagged pairs on each side (0.590 to 0.598, 0.602 to 0.610; their mean within '
         '0.002 of it) and a net (+300) over every peer\'s: under --decide ask named (D1r "named: ... its peers 5 below and 5 above: '
         '0.5900 to 0.6100"), the guard PASS (n_dv_gt1 0 at its peers\' highest 0), R2\'s guards take the cull (1 of 35), a DECISION '
         'naming it, 12 inversions, nothing moved, LOGIC 2; then under --decide auto the 12 tests read again (none run), the guard at '
         'equality culls it (22.2\'s note 5): the decision file (its guard and rule), the restart, admit applies it (34 kept), drop1 '
         'reads the cull in place (D1c, D1g PASS from the file), rc 0' % F, ok_a and ok_b, 'ask %s | auto %s' % (da, db))

    # ------------------------------------------------------------------ M78: the old rule's decision file and record on M76's frame
    dec_r2 = jload(DF)
    hand = ((jload(os.path.join(W, 'recon', 'admission.json')).get('decisions') or {}).get('drop1') or {})
    b012 = V012_BASIS(C, hand.get('flagged') or [], hand.get('under_floor'), m)
    old = dict((k, v) for k, v in dec_r2.items() if k not in R2_KEYS)
    old.update(basis=b012, version=V012, rule=V012_RULE)
    jsave(DF, old)
    rf = os.path.join(W, 'status', 'P5d1_drop1.json')
    r = jload(rf)
    fp012 = V012_FP(C, D1, W, m, rec)
    r.update(logic=1, version=V012, fingerprint=fp012)
    jsave(rf, r)
    st1 = state_of('drop1')
    rc, txt = run(['--to', 'drop1'])
    ra, rm = rec('5a', 'admit'), rec('5c', 'mcfg')
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    ok78 = (bool(dec_r2.get('basis')) and b012 != dec_r2.get('basis') and st1 == 'STALE' and rc == 4 and 'P5a admit: record STALE' in txt
            and gates(ra).get('D1d') == 'WARN' and 'another basis' in val(ra, 'D1d') and adm.get('kept') == 35
            and F in (adm.get('kept_pairs') or []) and rm.get('verdict') == 'DECISION' and gates(rm).get('G5c.4') == 'DECISION'
            and jload(DF).get('basis') == b012)
    case('M78 (18.3\'s D1d) on M76\'s frame after its cull, recon/drop1_decision.json as v0.12 r2 would have written it (its basis by '
         'v0.12 r2\'s drop1_basis, without DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE) and drop1\'s record as v0.12 r2 left it (LOGIC 1, '
         'v0.12 r2\'s fingerprint of these files): drop1 STALE; a run under --decide auto: admit reads the file again, another basis: '
         'not applied (D1d WARN), %s back in the network (35 kept); mcfg stops at G5c.4 (mintpy/ of 34 pairs in the way), rc 4' % F,
         ok78, 'basis r2 %s, v0.12 r2 %s; drop1 %s; rc %d; D1d %s %s; kept %s; mcfg %s %s' % (
             str(dec_r2.get('basis'))[:8], b012[:8], st1, rc, gates(ra).get('D1d'), val(ra, 'D1d')[:90], adm.get('kept'),
             rm.get('verdict'), gates(rm).get('G5c.4')))
    jsave(DF, dec_r2)
    rc1, t1 = run(['--only', 'admit'])
    a1, k1 = rec('5a', 'admit'), jload(os.path.join(W, 'recon', 'admission.json')).get('kept')
    B4 = os.path.join(T, 'cfg', 'mintpy_bal004.cfg')
    with open(B4, 'w') as fh:
        n = 0
        for ln in open(MC):
            if ln.startswith('DROP1_PEERS_BALANCE='):
                ln, n = 'DROP1_PEERS_BALANCE=0.004\n', n + 1
            fh.write(ln)
    assert n == 1
    rc2, t2 = run(['--only', 'admit'], mcfg=B4)
    a2, k2 = rec('5a', 'admit'), jload(os.path.join(W, 'recon', 'admission.json')).get('kept')
    case('M78b (D1d) the file as v0.13 r2 wrote it put back: admit (--only) applies it again (D1d INFO, 34 kept); then '
         'DROP1_PEERS_BALANCE 0.004: admit reads the file again (record STALE: its fingerprint holds both new keys while the file '
         'exists), another basis, not applied (WARN, 35 kept)',
         rc1 == 0 and gates(a1).get('D1d') == 'INFO' and k1 == 34 and rc2 == 0 and 'P5a admit: record STALE' in t2
         and gates(a2).get('D1d') == 'WARN' and 'another basis' in val(a2, 'D1d') and k2 == 35,
         'rc %d D1d %s kept %s; rc %d STALE %s D1d %s kept %s' % (rc1, gates(a1).get('D1d'), k1, rc2, 'P5a admit: record STALE' in t2,
                                                                 gates(a2).get('D1d'), k2))

    # ------------------------------------------------------------------ M86: F's count over its peers' highest, ask then auto
    restore('S5d1B', 'M86')
    rd0 = rec('5d1', 'drop1')
    peers = (table(rd0).get(F) or {}).get('peers') or []
    cnt = dict((p, 50 * (i + 1)) for i, p in enumerate(peers))   # 50 to 500
    cnt[F] = 900
    set_counts(rd0, cnt)
    rc, _ = run(['--to', 'drop1'], PB, decide='ask')
    rq = rec('5d1', 'drop1')
    ok_q = (rc == 4 and rq.get('verdict') == 'DECISION' and out(rq).get('state') == 'cull asked' and gates(rq).get('D1g') == 'INFO'
            and '%s: n_dv_gt1 900 over its peers\' highest 500' % F in val(rq, 'D1g') and 'kept under --decide auto' in val(rq, 'D1g')
            and '%s: n_dv_gt1 900 over its peers\' highest 500' % F in val(rq, 'D1') and 'over it, kept under --decide auto: %s' % F in val(rq, 'D1')
            and out(rq).get('reused') == 12 and out(rq).get('ran') == 0 and not os.path.exists(DF))
    rc2, _ = run(['--to', 'drop1'], PB)
    rw = rec('5d1', 'drop1')
    ok_w = (rc2 == 0 and rw.get('verdict') == 'PASS' and out(rw).get('state') == 'kept by the guard' and gates(rw).get('D1g') == 'WARN'
            and val(rw, 'D1g').startswith('kept: %s: n_dv_gt1 900 over its peers\' highest 500' % F) and gates(rw).get('R2c') == 'PASS'
            and out(rw).get('kept_by_guard') == [F] and out(rw).get('cull') == [] and out(rw).get('reused') == 12 and out(rw).get('ran') == 0
            and not os.path.exists(DF) and 'RESTART' not in ledger() and os.path.isdir(os.path.join(W, 'mintpy')))
    case('M86 (19.6, 20.1) layout B, %s named by its net, its n_dv_gt1 set over all 10 of its peers\' (900 against 50 to 500, in the '
         'tests\' result.json): under --decide ask a DECISION carrying both counts (D1g INFO, "kept under --decide auto"); under auto '
         'kept, D1g WARN naming it and both counts, no cull (state "kept by the guard", R2c none to cull), PASS, rc 0, no decision '
         'file, no restart; the 12 tests read again each time (none run)' % F, ok_q and ok_w,
         'ask rc %d %s D1g %s %s | auto rc %d %s %s D1g %s %s' % (rc, rq.get('verdict'), gates(rq).get('D1g'), val(rq, 'D1g')[:80], rc2,
                                                                 rw.get('verdict'), out(rw).get('state'), gates(rw).get('D1g'), val(rw, 'D1g')[:80]))

    # ------------------------------------------------------------------ M87: F's count under its peers' highest, auto
    restore('S5d1B', 'M87')
    rd0 = rec('5d1', 'drop1')
    cnt[F] = 400
    set_counts(rd0, cnt)
    rc, _ = run(['--to', 'drop1'], PB)
    led = ledger()
    rid = last_run(led)
    h1, rd = history('drop1', '5d1'), rec('5d1', 'drop1')
    dec = jload(DF)
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    case('M87 (19.6) layout B, %s named, its n_dv_gt1 under its peers\' highest (400 against 500): under --decide auto culled within '
         'R2\'s guards (D1g PASS, R2c INFO): the decision file with the guard\'s reading, the restart, admit applies it (34 kept), drop1 '
         'reads the cull in place, rc 0' % F,
         rc == 0 and out(h1).get('state') == 'cull taken' and gates(h1).get('D1g') == 'PASS'
         and '%s: n_dv_gt1 400 under its peers\' highest 500' % F in val(h1, 'D1g') and gates(h1).get('R2c') == 'INFO'
         and dec.get('cull') == [F] and ((dec.get('guard') or [{}])[0].get('n_dv_gt1'), (dec.get('guard') or [{}])[0].get('peers_max')) == (400, 500)
         and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1 and adm.get('kept') == 34
         and out(rd).get('state') == 'cull in place' and rd.get('verdict') == 'PASS',
         'rc %d; pass 1 %s D1g %s %s; cull %s guard %s; kept %s; drop1 %s' % (
             rc, out(h1).get('state'), gates(h1).get('D1g'), val(h1, 'D1g')[:70], dec.get('cull'), dec.get('guard'), adm.get('kept'),
             out(rd).get('state')))

    # ------------------------------------------------------------------ M77 (a): layout S, 4 below and 30 above
    LS = L['S']
    restore('S4e', 'M77a')
    rc, _ = run(['--to', 'drop1'], plants(LS))
    rd = rec('5d1', 'drop1')
    x = table(rd).get(F) or {}
    tt = run_tests(rd)
    coh = LS[0]
    pool = [p for p in pl if p != F]
    near = v012_nearest(F, coh, pool)
    nets = dict((p, (tt.get(p) or {}).get('net')) for p in near)
    ok_s = (rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'no cull' and x.get('testable') is False
            and x.get('why') == 'untestable: 4 unflagged pairs below its coherence 0.5200, 5 asked: kept' and x.get('net') == 300
            and sorted(x.get('below') or []) == sorted(LS[3]['below']) and sorted(x.get('above') or []) == sorted(LS[3]['above'])
            and len([p for p in pool if coh[p] > coh[F]]) == 30 and len([p for p in pool if coh[p] <= coh[F]]) == 4
            and len(near) == 10 and sum(1 for p in near if nets[p] is None) == 1 and all(nets[p] == 0 for p in near if nets[p] is not None)
            and gates(rd).get('D1g') == 'N/A' and gates(rd).get('R2c') == 'PASS' and out(rd).get('tests') == 11 and not os.path.exists(DF))
    ds = dict(rc=rc, state=out(rd).get('state'), why=x.get('why'), near_nets=[nets[p] for p in near], tests=out(rd).get('tests'))

    # ------------------------------------------------------------------ M75 and M77 (b): layout U
    LU = L['U']
    restore('S4e', 'M75')
    rc, _ = run(['--to', 'drop1'], plants(LU))
    rd, ra = rec('5d1', 'drop1'), rec('5a', 'admit')
    tb = table(rd)
    xg, xf = tb.get(G) or {}, tb.get(F) or {}
    tt = run_tests(rd)
    coh = LU[0]
    pool = [p for p in pl if p not in (F, G)]
    near = v012_nearest(F, coh, pool)
    allnets = dict((k, v.get('net')) for k, v in tt.items())
    ok_g = (rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'no cull'
            and sorted(((out(ra).get('decisions') or {}).get('drop1') or {}).get('in_network') or []) == sorted([F, G])
            and all(coh[p] > coh[G] for p in pool) and xg.get('testable') is False and xg.get('margin') is None
            and xg.get('why') == 'untestable: 0 unflagged pairs below its coherence 0.4500, 5 asked: kept'
            and sorted(xg.get('above') or []) == LU[3]['g_above'] and xg.get('net') == 500
            and all(v is not None and v < 500 for k, v in allnets.items() if k != G)
            and any(g['value'].startswith('untestable: 0 unflagged pairs below its coherence 0.4500') for g in gl(rd, 'D1r'))
            and gates(rd).get('D1g') == 'N/A' and gates(rd).get('R2c') == 'PASS' and out(rd).get('cull') == []
            and not os.path.exists(DF) and 'RESTART' not in ledger())
    case('M75 (18.3) layout U: the flagged %s at 0.450, under all 33 unflagged pairs\' coherence, its drop gaining the run\'s largest '
         'net (+500): kept, untestable ("0 unflagged pairs below its coherence 0.4500, 5 asked: kept"), margin None, no cull (D1g N/A, '
         'R2c none to cull), drop1 PASS, rc 0, no decision file, no restart' % G, ok_g,
         'rc %d; %s %s; G %s; nets %s' % (rc, rd.get('verdict'), out(rd).get('state'), xg.get('why'), sorted(allnets.values())[-3:]))
    nets = dict((p, allnets.get(p)) for p in near)
    ok_u = (xf.get('testable') is False and xf.get('net') == 300
            and xf.get('why') == 'untestable: its peers\' mean coherence 0.6200, 0.0200 above its 0.6000 (0.005 asked): kept'
            and sorted(xf.get('below') or []) == sorted(LU[3]['below']) and sorted(xf.get('above') or []) == sorted(LU[3]['above'])
            and max(coh[F] - coh[p] for p in LU[3]['below']) <= 0.002 and max(coh[p] for p in LU[3]['above']) - coh[F] <= 0.05 + 1e-9
            and sorted(near) == sorted(LU[3]['below'] + LU[3]['above']) and all(nets[p] == 0 for p in near))
    case('M77 (18.3) a flagged pair untestable two ways, its net (+300) over every one of its 10 nearest, so v0.12 r2\'s rule would '
         'name it in both: layout S, %s with 4 unflagged pairs below it and 30 above ("4 unflagged pairs below its coherence 0.5200, '
         '5 asked"; 9 peers inverted, each 0; the 10th of v0.12 r2\'s nearest, not inverted, gains nothing by the mock\'s plants), no '
         'cull, PASS; layout U, %s with 5 below within 0.002 and 5 above spread to 0.05 ("its peers\' mean coherence 0.6200, 0.0200 '
         'above its 0.6000 (0.005 asked)"; its 10 peers v0.12 r2\'s 10 nearest, each 0), no cull' % (F, F), ok_s and ok_u,
         'S %s | U why %s, nearest nets %s' % (ds, xf.get('why'), [nets[p] for p in near]))

    # ------------------------------------------------------------------ M78c: layout U's frame with v0.12 r2's drop1 record
    rf = os.path.join(W, 'status', 'P5d1_drop1.json')
    s0_ = state_of('drop1')
    r = jload(rf)
    r.update(logic=1, version=V012, fingerprint=V012_FP(C, D1, W, m, rec))
    jsave(rf, r)
    s1_ = state_of('drop1')
    rc, txt = run(['--to', 'drop1'], plants(LU))
    rd = rec('5d1', 'drop1')
    rc2, txt2 = run(['--to', 'drop1'], plants(LU))
    case('M78c (18.3; the test root\'s run, 28.3 and 28.4) layout U\'s frame, drop1 PASS (CURRENT), its record then as v0.12 r2 wrote '
         'it (LOGIC 1, v0.12 r2\'s fingerprint): STALE; a run decides again under v0.13 r2: its 18 tests read again (none run), no cull '
         'again, PASS, rc 0; the next run skips it (STALE once), rc 0',
         s0_ == 'CURRENT' and s1_ == 'STALE' and rc == 0 and 'P5d1 drop1: record STALE' in txt and rd.get('verdict') == 'PASS'
         and rd.get('logic') == 2 and out(rd).get('state') == 'no cull' and out(rd).get('reused') == 18 and out(rd).get('ran') == 0
         and rc2 == 0 and 'P5d1 drop1: record CURRENT' in txt2,
         'before %s, as v0.12 r2 %s; rc %d %s %s reused %s ran %s; again rc %d CURRENT %s' % (
             s0_, s1_, rc, rd.get('verdict'), out(rd).get('state'), out(rd).get('reused'), out(rd).get('ran'), rc2,
             'P5d1 drop1: record CURRENT' in txt2))
