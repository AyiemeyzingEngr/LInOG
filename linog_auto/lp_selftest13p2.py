#!/usr/bin/env python3
"""lp_selftest13p2.py -- linog_auto v0.13's Phase 2 and topo cases for FBS+FBD and FBD-only frames (called by lp_selftest.py
as the suite 13p2; the ascending automation record's case numbers).

phase13_2: the mixed mock frame 3350 and the FBD-only mock frame 3360 (lp_selftest13p1's) through Phase 2 and topo:
  M12 (4.7): D1 among the FBS dates (the candidates FBS only), D1f an FBD date named in recon/reference.txt FAILs, D1c the
     highest-degree FBS date with a WARN when no FBS date is in the degree band (lp_p2.d1 on a table, and the frame with one
     FBS date of 14); M13 a modes.json row changed after verify: stack1's G2a.1 FAIL;
  M73, M89 (17.7, 20.10): G3a.14 on the mixed frame: PASS in place; the reference 32 samples off on 3 or more windows FAIL;
     12 off WARN; relief in one cell only and 32 off FAIL; a flat DEM NOT MEASURED (WARN); M88 the ratio line on one window
     at a spurious peak (G3a.14's verdict on its own: NOT MEASURED, where without the line it reads FAIL);
  M81's Phase 2 and topo lines (18.5, R6-d): the FBD-only frame at 6 range looks (stack1, stack2's run file, the reference's
     geometry), D1 by v0.12's rule (the modal width first), G3a.14 PASS in place, FAIL 16 samples off, WARN 6 off (an FBD
     gate is 16 samples).
The mock topo writes simamp.rdr from the reference's amplitude (selftest_kit/mock_stack3/topo.py), moved by
LINOG_MOCK_SIMSHIFT; LINOG_MOCK_RELIEF1 and LINOG_MOCK_FLATDEM plant hgt.rdr's texture.
"""
import json
import os
import shutil

import lp_selftest13p1 as P13

FR, FR_FBD = '3350', '3360'


def phase13_2(T, case, S):
    print('-- v0.13 Phase 2 and topo (R6, R6-d): D1 among the FBS dates, D1c, D1f, the FBD-only looks; G3a.14 (Gap 2b)')
    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M12-M89 not run: the mock granules\' samples need numpy, and neither Python tried has it', False)
        return
    HERE = S.HERE
    import sys
    sys.path.insert(0, HERE)
    import lp_p2 as P2
    import lp_reg3 as R3
    ORB = S.ORBITS[:12]
    D = [S.date_of(o) for o in ORB]
    FBS = [D[i] for i in range(12) if i not in S.FBD_3350]
    FBDD = [D[i] for i in S.FBD_3350]
    AUTO = ['--decide', 'auto']

    def fd(root, frame=FR):
        return S.fdir(T, frame, root)

    def run(root, args, extra=None, frame=FR, archive=None):
        e = dict({'LINOG_ROOT': os.path.join(T, root)}, **(extra or {}))
        if archive:
            e['LINOG_ARCHIVE'] = archive
        return S.run(T, ['084', frame] + args, env_extra=e)

    def rec(root, idx, ph, frame=FR):
        return S.rec(T, frame, idx, ph, root)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gval(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def refjson(root, frame=FR):
        p = os.path.join(fd(root, frame), 'recon', 'reference.json')
        return json.load(open(p)) if os.path.isfile(p) else {}

    def topo_again(root, tag, extra=None, frame=FR):
        """topo forced again with a plant: its outputs moved into _archive/ first (G3a.7 refuses a tree in the way)."""
        for n in ('merged/geom_reference', 'geom_reference'):
            p = os.path.join(fd(root, frame), n)
            if os.path.exists(p):
                S.aside(T, p, '13p2_%s_%s' % (tag, n.replace('/', '_')))
        rc, _ = run(root, ['--only', 'topo', '--force', 'topo'] + AUTO, extra=extra, frame=frame)
        return rc, rec(root, '3a', 'topo', frame)

    # ------------------------------------------------------------------------------------------- M12, M13 (Phase 2)
    rc, out = run('mz', ['--to', 'reference'] + AUTO)
    rr, rj = rec('mz', '2b', 'reference'), refjson('mz')
    cands = (rr.get('outputs') or {}).get('candidates') or []
    case('M12 the mixed frame 3350 to the reference under --decide auto: D1 picks an FBS date, every candidate FBS (the network\'s '
         'quantities over all 12 dates); D1c PASS, D1f PASS; the geometry at 12 x 28 looks',
         rc == 0 and rj.get('reference') in FBS and cands and all(c.get('mode') == 'FBS' for c in cands)
         and gates(rr).get('D1c') == 'PASS' and gates(rr).get('D1f') == 'PASS' and (rj.get('geometry') or {}).get('rlks') == 12,
         'rc %d; reference %s; candidates %s; D1c %s, D1f %s' % (rc, rj.get('reference'), [(c['date'], c['mode'], c['degree']) for c in cands],
                                                              gates(rr).get('D1c'), gates(rr).get('D1f')))
    rt = os.path.join(fd('mz'), 'recon', 'reference.txt')
    with open(rt, 'w') as fh:
        fh.write('%s an FBD date, named by the self-test (M12b)\n' % FBDD[1])
    rc1, _ = run('mz', ['--to', 'reference'])
    r1 = rec('mz', '2b', 'reference')
    S.aside(T, rt, 'M12b')
    rc2, _ = run('mz', ['--to', 'reference'] + AUTO)
    case('M12b recon/reference.txt names an FBD date: D1 FAIL and D1f FAIL naming it (rc 2), no reference.json written; the file moved '
         'away -> D1\'s FBS pick again',
         rc1 == 2 and gates(r1).get('D1') == 'FAIL' and gates(r1).get('D1f') == 'FAIL' and FBDD[1] in gval(r1, 'D1f')
         and rc2 == 0 and refjson('mz').get('reference') in FBS,
         'rc %d (D1 %s, D1f %s: %s), then %d' % (rc1, gates(r1).get('D1'), gates(r1).get('D1f'), gval(r1, 'D1f')[:60], rc2))
    # D1c on a table: no FBS date in the degree band
    rows = dict((d, dict(mode='FBS' if i in (0, 5) else 'FBD', width=1000)) for i, d in enumerate(D[:6]))
    bp = dict((d, 0.0) for d in D[:6])
    pairs = [(D[i], D[j]) for i in range(1, 5) for j in range(i + 1, 5)] + [(D[0], D[1]), (D[4], D[5])]
    r = P2.d1(rows, bp, pairs, 1, 1500.0)
    case('M12c D1c on a network whose FBS dates are its earliest (excluded) and a date of degree 1: no FBS date in the degree band, '
         'so D1 takes the highest-degree FBS date (not the earliest) and the reference phase WARNs (d1c)',
         r['mixed'] and r['d1c'] and r['pick'] == D[5] and all(c['mode'] == 'FBS' for c in r['candidates']),
         'pick %s, d1c %s, degrees %s' % (r['pick'], r['d1c'], r['degree']))
    a82 = P13.make_variant(T, S, 'fbd1', {}, frame=FR_FBD, orbs=S.ORBITS[:13], fbd=range(13),
                           width=lambda i: S.W_MX if i == 12 else S.W_MX + 48, extra=[[S.ORBITS[13], dict(fbd=False)]])
    rc, _ = run('fz1', ['--to', 'reference'] + AUTO, frame=FR_FBD, archive=a82)
    r82, j82 = rec('fz1', '2b', 'reference', FR_FBD), refjson('fz1', FR_FBD)
    case('M82 (Phase 2) the FBD-only frame with one FBS date added: the reference is that FBS date (D1f PASS), by D1c\'s WARN (its '
         'degree below the band: the part 3 review\'s P3-11 asks the line)',
         rc == 0 and j82.get('reference') == S.date_of(S.ORBITS[13]) and gates(r82).get('D1f') == 'PASS'
         and gates(r82).get('D1c') == 'WARN' and 'no FBS date has degree >=' in gval(r82, 'D1c'),
         'rc %d; reference %s; D1c %s (%s)' % (rc, j82.get('reference'), gates(r82).get('D1c'), gval(r82, 'D1c')[:90]))
    mj = os.path.join(fd('mz'), 'recon', 'modes.json')
    keep = os.path.join(T, '_archive', 'M13_modes.json')
    shutil.copy2(mj, keep)
    m = json.load(open(mj))
    for row in m['dates']:
        if row['date'] == FBDD[0]:
            row['mode'] = 'FBS'
    json.dump(m, open(mj, 'w'), indent=1)
    rc1, _ = run('mz', ['--only', 'stack1'] + AUTO)
    r13 = rec('mz', '2a', 'stack1')
    shutil.copy2(keep, mj)
    rc2, _ = run('mz', ['--to', 'stack2'] + AUTO)
    case('M13 a recon/modes.json row changed for an FBD date after verify, then --only stack1: G2a.1 FAIL (modes.json changed since '
         'verify wrote it), rc 2; the file back -> PASS',
         rc1 == 2 and gates(r13).get('G2a.1') == 'FAIL' and 'changed since verify' in gval(r13, 'G2a.1') and rc2 == 0,
         'rc %d (%s), then %d' % (rc1, gval(r13, 'G2a.1')[:80], rc2))

    # ------------------------------------------------------------------------------------------- M73, M88, M89 (topo)
    rc, _ = run('mz', ['--to', 'topo'] + AUTO)
    t0 = rec('mz', '3a', 'topo')
    g0 = (t0.get('outputs') or {}).get('g3a14') or {}
    case('M73 G3a.14 on the mixed frame (FBS reference, a gate 32 samples): the reference against simamp at the windows of relief, '
         '3 or more counted at a ratio of 1.25: PASS within a quarter of a gate (8 samples), rc 0',
         rc == 0 and gates(t0).get('G3a.14') == 'PASS' and g0.get('counted', 0) >= 3 and abs(g0.get('gate_samples', 0) - 32.0) < 1e-6,
         'rc %d; %s; %d windows counted' % (rc, gval(t0, 'G3a.14')[:120], g0.get('counted', 0)))
    res = {}
    for tag, extra in (('s32', {'LINOG_MOCK_SIMSHIFT': '32'}), ('s12', {'LINOG_MOCK_SIMSHIFT': '12'}),
                       ('one32', {'LINOG_MOCK_SIMSHIFT': '32', 'LINOG_MOCK_RELIEF1': '1'}), ('flat', {'LINOG_MOCK_FLATDEM': '1'})):
        rcx, tx = topo_again('mz', tag, extra)
        res[tag] = (rcx, gates(tx).get('G3a.14'), gval(tx, 'G3a.14'), ((tx.get('outputs') or {}).get('g3a14') or {}).get('counted'))
    rc5, t5 = topo_again('mz', 'clean')
    case('M89 the reference 32 samples off on 3 or more counted windows: G3a.14 FAIL (rc 2), the median reading +32',
         res['s32'][0] == 2 and res['s32'][1] == 'FAIL' and (res['s32'][3] or 0) >= 3 and 'dx +3' in res['s32'][2],
         'rc %d; %s' % (res['s32'][0], res['s32'][2][:110]))
    case('M73b 12 samples off: WARN (rc 0); relief in one cell only, 32 off: FAIL on one window (rc 2); a flat DEM: NOT MEASURED (WARN, '
         'rc 0); topo again in place: PASS',
         res['s12'][:2] == (0, 'WARN') and res['one32'][:2] == (2, 'FAIL') and res['one32'][3] == 1
         and res['flat'][:2] == (0, 'WARN') and 'NOT MEASURED' in res['flat'][2] and rc5 == 0 and gates(t5).get('G3a.14') == 'PASS',
         '%s; then rc %d %s' % (dict((k, (v[0], v[1], v[3])) for k, v in res.items()), rc5, gates(t5).get('G3a.14')))
    spur = [dict(r0=0, c0=0, cell=[0, 0], demstd=10.3, dx=-144.0, dy=0.0, ratio=1.09)]   # RA4's window (20.5): 10.3 m
    v1, val1, _, _ = R3.g3a14_verdict(spur, 32.0)
    v0, _, _, _ = R3.g3a14_verdict(spur, 32.0, ratio_min=0.0)
    case('M88 one flat window correlating on a spurious peak at -144 samples at a ratio of 1.09: G3a.14 NOT MEASURED (WARN) under the '
         'ratio line (20.10), where without the line it reads FAIL', v1 == 'WARN' and 'NOT MEASURED' in val1 and v0 == 'FAIL',
         '%s (%s); without the line %s' % (v1, val1, v0))

    # ------------------------------------------------------------------------------------------- M81's Phase 2 and topo
    a81 = P13.make_variant(T, S, 'fbd', {}, frame=FR_FBD, orbs=S.ORBITS[:13], fbd=range(13),
                           width=lambda i: S.W_MX if i == 12 else S.W_MX + 48)
    rc, _ = run('fz', ['--to', 'topo'] + AUTO, frame=FR_FBD, archive=a81)
    s1, s2, rf, tp = (rec('fz', '2a', 'stack1', FR_FBD), rec('fz', '2c', 'stack2', FR_FBD), rec('fz', '2b', 'reference', FR_FBD),
                      rec('fz', '3a', 'topo', FR_FBD))
    j81 = refjson('fz', FR_FBD)
    geo = j81.get('geometry') or {}
    nar = S.date_of(S.ORBITS[12])
    case('M81b (R6-d) the FBD-only frame through Phase 2 at 6 range looks: stack1 and stack2 record the swap, stack2\'s run file '
         'reads rlks 6 (G2c.9), the reference\'s geometry 1048 // 6 x 512 // 28; D1 by v0.12\'s rule (not the 1000-wide date); '
         'D1c and D1f N/A (one mode; 18.5\'s row, the part 3 review\'s P3-05)',
         rc == 0 and 'STACK_RLKS_FBD' in str((s1.get('inputs') or {}).get('looks')) and 'STACK_RLKS_FBD' in str((s2.get('inputs') or {}).get('looks'))
         and 'rlks 6' in gval(s2, 'G2c.9') and geo.get('rlks') == 6 and geo.get('width') == (S.W_MX + 48) // 6
         and j81.get('reference') not in (None, nar) and gates(rf).get('D1c') == 'N/A' and gates(rf).get('D1f') == 'N/A',
         'rc %d; G2c.9 %s; geometry %s; reference %s' % (rc, gval(s2, 'G2c.9')[-40:], geo, j81.get('reference')))
    g81 = (tp.get('outputs') or {}).get('g3a14') or {}
    r16, t16 = topo_again('fz', 'f16', {'LINOG_MOCK_SIMSHIFT': '16'}, frame=FR_FBD)
    r6, t6 = topo_again('fz', 'f6', {'LINOG_MOCK_SIMSHIFT': '6'}, frame=FR_FBD)
    case('M81c G3a.14 on the FBD-only frame (an FBD gate 16 samples): PASS in place; the reference 16 samples off FAIL (rc 2); '
         '6 off WARN (over a quarter gate, 4)',
         gates(tp).get('G3a.14') == 'PASS' and abs(g81.get('gate_samples', 0) - 16.0) < 1e-6 and r16 == 2
         and gates(t16).get('G3a.14') == 'FAIL' and r6 == 0 and gates(t6).get('G3a.14') == 'WARN',
         'in place %s (%s); 16: rc %d %s; 6: rc %d %s' % (gates(tp).get('G3a.14'), gval(tp, 'G3a.14')[:60], r16, gates(t16).get('G3a.14'),
                                                          r6, gates(t6).get('G3a.14')))

    # ------------------------------------------------------------------------- the part 3 review's fixes (review/p3/REPORT.md)
    phase13_2_review(T, case, S, P2, R3, run, rec, gates, gval, fd, D)


def phase13_2_review(T, case, S, P2, R3, run, rec, gates, gval, fd, D):
    """The part 3 review's fixes: M12d (P3-01: D1's modal width among the FBS dates where the FBD dates hold the frame's mode,
    and the kit list), M12e (P3-03: D1c ranks by the modal width first), M12f (P3-04: no FBS date but the earliest, on a table
    and on a mock frame), M88b (P3-02, P3-13: G3a.14's verdict at its lines, 1 or 2 windows, the ratio line, the gate from a
    pixel at 9 decimals), M81d (P3-09: an FBD-only frame's dry run before verify takes 6 range looks)."""
    print('-- v0.13 part 3 review: D1\'s FBS modal width, D1c\'s order, no FBS date but the earliest, G3a.14\'s lines, an FBD-only '
          'dry run\'s looks')
    # M12d (P3-01): FBD 4 x 1048 (the frame's mode), FBS 3 x 1000 (their mode), 2 x 1096, 2 x 1144, 1 x 1192; the FBS date
    # in the degree band nearest the midpoint 1096 wide, so a modal width over all dates (1048: no FBS date) or none picks it
    import datetime as _dt
    ds = D[:12]
    fbd_i = (1, 4, 7, 10)
    bp = dict((d, 0.0) for d in ds)
    pairs = [(ds[i], ds[j]) for i in range(12) for j in range(i + 1, min(12, i + 4))]
    deg, _ = P2.network(ds, bp, pairs)
    t = dict((d, _dt.datetime.strptime(d, '%Y%m%d')) for d in ds)
    tmid = t[ds[0]] + (t[ds[-1]] - t[ds[0]]) / 2
    fbs_d = [d for i, d in enumerate(ds) if i not in fbd_i]
    band = sorted([d for d in fbs_d if deg[d] >= max(deg.values()) - 1 and d != ds[0]], key=lambda d: abs((t[d] - tmid).days))
    order = band + [d for d in fbs_d if d not in band]
    wl = [1096, 1000, 1000, 1000, 1096, 1144, 1144, 1192]
    rows = dict((d, dict(mode='FBD', width=1048)) for i, d in enumerate(ds) if i in fbd_i)
    rows.update((d, dict(mode='FBS', width=w)) for d, w in zip(order, wl))
    r = P2.d1(rows, bp, pairs, 1, 1500.0)
    allw = __import__('collections').Counter(rows[d]['width'] for d in ds).most_common(1)[0][0]
    fbsw = __import__('collections').Counter(rows[d]['width'] for d in ds if rows[d]['mode'] == 'FBS').most_common(1)[0][0]
    case('M12d (the part 3 review\'s P3-01) a mixed table where the FBD dates hold the frame\'s modal width (1048) and the FBS dates '
         'two widths: D1\'s modal width is the FBS dates\' (%d), its pick an FBS date at that width, the kit list\'s first entry too' % fbsw,
         allw == 1048 and fbsw == 1000 and len(band) >= 2 and rows[band[0]]['width'] == 1096
         and r['modal_width'] == fbsw and r['pick'] and r['pick'] != band[0] and rows[r['pick']]['mode'] == 'FBS'
         and rows[r['pick']]['width'] == fbsw and r['kit_first'] and rows[r['kit_first']]['width'] == fbsw
         and rows[r['kit_first']]['mode'] == 'FBS',
         'all-dates mode %s, FBS mode %s; pick %s (%s); kit_first %s (%s); modal %s' % (
             allw, fbsw, r['pick'], rows.get(r['pick'], {}).get('width'), r['kit_first'], rows.get(r['kit_first'], {}).get('width'),
             r['modal_width']))
    # M12e (P3-03): D1c among the highest-degree FBS dates, the modal width first
    d6 = D[:6]
    rows6 = {d6[0]: dict(mode='FBS', width=1000), d6[1]: dict(mode='FBD', width=1048), d6[2]: dict(mode='FBS', width=1096),
             d6[3]: dict(mode='FBS', width=1000), d6[4]: dict(mode='FBD', width=1048), d6[5]: dict(mode='FBD', width=1048)}
    pr6 = [(d6[1], d6[4]), (d6[1], d6[5]), (d6[4], d6[5]), (d6[0], d6[1]), (d6[2], d6[4]), (d6[3], d6[5]), (d6[0], d6[4]),
           (d6[1], d6[2]), (d6[0], d6[5]), (d6[3], d6[4])]
    r6 = P2.d1(rows6, dict((d, 0.0) for d in d6), pr6, 0, 1500.0)
    hi = max(r6['degree'][d] for d in (d6[2], d6[3]))
    case('M12e (P3-03, the build\'s reading of 4.7) D1c: no FBS date in the degree band; among the FBS dates of the highest degree '
         '(not the earliest) the modal FBS width first, then the midpoint',
         r6['d1c'] and r6['pick'] == d6[3] and rows6[r6['pick']]['width'] == 1000 and r6['degree'][d6[2]] == r6['degree'][d6[3]] == hi,
         'pick %s (%s wide), d1c %s; degrees %s' % (r6['pick'], rows6.get(r6['pick'], {}).get('width'), r6['d1c'],
                                                    dict((d, r6['degree'][d]) for d in d6)))
    # M12f (P3-04): the only FBS date the stack's earliest, on a table and through the reference phase
    rowsf = dict((d, dict(mode='FBS' if i == 0 else 'FBD', width=1000)) for i, d in enumerate(d6))
    rf = P2.d1(rowsf, dict((d, 0.0) for d in d6), [(d6[i], d6[j]) for i in range(6) for j in range(i + 1, 6)], 1, 1500.0)
    import lp_selftest13p1 as P13
    af = P13.make_variant(T, S, 'fbs0', dict((i, {}) for i in range(12)), frame='3350', orbs=S.ORBITS[:12], fbd=range(1, 12))
    rc, _ = run('fz0', ['--to', 'reference', '--decide', 'auto'], archive=af)
    r0 = rec('fz0', '2b', 'reference')
    case('M12f (P3-04) a mixed frame whose only FBS date is the stack\'s earliest: d1() no_fbs, no pick; the reference phase FAILs D1 '
         '("no candidate", an FBS date ...) and D1c ("no FBS date but the stack\'s earliest (N23)"), rc 2',
         rf['no_fbs'] and rf['pick'] is None and rf['mixed'] and rc == 2 and gates(r0).get('D1') == 'FAIL'
         and 'an FBS date' in [g for g in r0.get('gates', []) if g['id'] == 'D1'][0].get('threshold', '')
         and gates(r0).get('D1c') == 'FAIL' and 'no FBS date but the stack\'s earliest' in gval(r0, 'D1c'),
         'no_fbs %s, pick %s; rc %d; D1 %s; D1c %s %s' % (rf['no_fbs'], rf['pick'], rc, gates(r0).get('D1'), gates(r0).get('D1c'),
                                                          gval(r0, 'D1c')[:70]))
    # M88b (P3-02, P3-13): the verdict at its lines
    W_ = lambda dx, ratio=2.0, i=0: dict(r0=0, c0=128 * i, cell=[0, i % 3], demstd=5.0, dx=dx, dy=0.0, ratio=ratio)  # noqa: E731
    g32, g16 = R3.gate_samples(4.684257156), R3.gate_samples(9.368514313)
    V = lambda rd, g=32.0: R3.g3a14_verdict(rd, g)[:2]  # noqa: E731
    checks = [
        ('three at exactly 8 FBS samples: PASS', V([W_(8.0, i=0), W_(8.0, i=1), W_(8.0, i=2)]), 'PASS'),
        ('three at exactly 16: FAIL', V([W_(16.0, i=0), W_(16.0, i=1), W_(16.0, i=2)]), 'FAIL'),
        ('three at 15.99: WARN', V([W_(15.99, i=0), W_(15.99, i=1), W_(15.99, i=2)]), 'WARN'),
        ('FBD three at exactly 4: PASS', V([W_(4.0, i=0), W_(4.0, i=1), W_(4.0, i=2)], 16.0), 'PASS'),
        ('FBD three at exactly 8: FAIL', V([W_(8.0, i=0), W_(8.0, i=1), W_(8.0, i=2)], 16.0), 'FAIL'),
        ('one in place and one 12 off: WARN few windows', V([W_(0.0, i=0), W_(12.0, i=1)]), 'WARN'),
        ('two at +20 and -20: WARN (not one sign)', V([W_(20.0, i=0), W_(-20.0, i=1)]), 'WARN'),
        ('two at +20: FAIL', V([W_(20.0, i=0), W_(20.0, i=1)]), 'FAIL'),
        ('one at +3: WARN (few windows, not PASS by the median)', V([W_(3.0)]), 'WARN'),
        ('two counted and one at ratio 1.2499: few windows', V([W_(0.0, i=0), W_(0.0, i=1), W_(0.0, 1.2499, 2)]), 'WARN'),
        ('three with one at ratio exactly 1.25: counted, PASS', V([W_(0.0, i=0), W_(0.0, i=1), W_(0.0, 1.25, 2)]), 'PASS'),
        ('the gate from 4.684257156 m: 32; 16.0 FAIL', V([W_(16.0, i=0), W_(16.0, i=1), W_(16.0, i=2)], g32), 'FAIL'),
        ('the gate from 9.368514313 m: 16; 4.0 PASS', V([W_(4.0, i=0), W_(4.0, i=1), W_(4.0, i=2)], g16), 'PASS')]
    bad = [(n, got) for n, got, want in checks if got[0] != want]
    fewv = V([W_(0.0, i=0), W_(12.0, i=1)])[1]
    case('M88b (P3-02, P3-13) G3a.14\'s verdict at its lines: exactly a quarter gate PASS and exactly half FAIL (8 and 16 FBS samples, 4 '
         'and 8 FBD); 1 or 2 windows FAIL only when every one reads half a gate with one sign, else WARN "few windows"; a window '
         'at ratio exactly 1.25 counts, at 1.2499 not; the gate from a pixel carried at 9 decimals is 32 and 16 samples (%d checks)' % len(checks),
         not bad and g32 == 32.0 and g16 == 16.0 and 'few windows' in fewv,
         'wrong: %s; gates %r %r' % (bad, g32, g16))
    # M81d (P3-09): an FBD-only frame's dry run before its first verify: stack1 plans 6 range looks from RECON.json's branch
    a81 = P13.make_variant(T, S, 'fbd', {}, frame='3360', orbs=S.ORBITS[:13], fbd=range(13),
                           width=lambda i: S.W_MX if i == 12 else S.W_MX + 48)
    dd = os.path.join(T, 'dry_m81d')
    rc0, _ = run('fz_dry', ['--to', 'bandlimit'], frame='3360', archive=a81)   # through Phase 1 but verify (no modes.json yet)
    rc, _ = run('fz_dry', ['--dry-run', dd, '--to', 'stack1'], frame='3360', archive=a81)
    s1 = {}
    f1 = os.path.join(dd, 'status', 'P2a_stack1.json')
    if os.path.isfile(f1):
        s1 = json.load(open(f1))
    case('M81d (P3-09) an FBD-only frame run to bandlimit (verify not yet, so no recon/modes.json), then a dry run to stack1: stack1\'s '
         'plan takes STACK_RLKS_FBD (6) from recon\'s branch in DIR/recon/RECON.json',
         rc0 == 0 and not os.path.exists(os.path.join(fd('fz_dry', '3360'), 'recon', 'modes.json'))
         and 'STACK_RLKS_FBD' in str((s1.get('inputs') or {}).get('looks')),
         'rc %d then %d; stack1 dry record %s, looks %s' % (rc0, rc, s1.get('verdict'), (s1.get('inputs') or {}).get('looks')))
