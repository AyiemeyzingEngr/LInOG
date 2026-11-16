#!/usr/bin/env python3
"""lp_selftest13.py -- linog_auto v0.13's own self-test cases (called by lp_selftest.py; the ascending automation record's
case numbers, M1 to M89, with M90 and M91 for 12.3's items 2 and 3).

phase13_0: Phase 0, recon for any path and the framing check.
  9.5's M2 to M3m: G0.16 on a mock P447 F0310 cell (12 granules; the path table's footprint bbox_0310 as its anchor) and,
     M3m, on path 84's F3310 cell; M3g with no footprint and the frame outside the frame law's range.
  13.7's M33 to M47: a derived path (P446 F0290, which the mock table lacks), the date law from the frame's own granules,
     the direction by the frame rule, G0.17's residue, partial and misnamed entries, G0.14 on the frame's own corners, a
     moved granule and a moved majority on a derived path, the beam guard G0.18, the path runner, an unreadable folder,
     the records read by offset under both Pythons.
  M90 (12.3, item 2): the root its caller does not own, refused before anything is written, unless LINOG_ROOT names it.
  M91 (12.3, item 3): the driver's python3 checked for 3.6 or later.
phase13_review: the part 1 review's fixes (review/p1/REPORT.md): M95 and M95b (B1: a course-kit tree at the default frame
  folder refused by G0.20, skipped by the path runner; stage's lineage beside another tool's LINEAGE.txt), M90b (M1: the
  path runner's root check), M34d (M2: a summary date that is not a date or absent, G0.4; an error after the record is
  written ends it ERROR), M42b and M41b (m2: the frame law's band at step 2, G0.16a's WARN), M96 and M96b (m3: dem_<frame>,
  LINOG_DEM, recon's fingerprint and other frames' keys), M97 (m4: a granule placed by Vincenty's geodesic).
The mock granules are lp_selftest.mkzip's (v0.13: IMG members stored, (b), (c), times and corners at the real scale).
"""
import configparser
import datetime
import glob
import json
import os
import shutil
import stat
import subprocess
import sys

LAW_A = (0.92026, 0.0496858)


def law_date(orb, eo, ed):
    """The date law of an anchor (ed, eo): ed + 46 days a cycle of 671 orbits."""
    k, rem = divmod(orb - eo, 671)
    assert rem == 0, (orb, eo)
    return (datetime.datetime.strptime(ed, '%Y%m%d') + datetime.timedelta(days=46 * k)).strftime('%Y%m%d')


def phase13_0(T, case, S):
    print('-- v0.13 Phase 0: recon for any path (R8), the framing check G0.16, G0.14 by the corners, the beam guard, the root, '
          'the driver\'s python3')
    HERE = S.HERE
    R13 = os.path.join(T, 'v13p0')
    os.makedirs(R13)
    real = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    real.read(os.path.join(HERE, 'linog_paths.cfg'))
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    hdr = base.split('\n[p084]', 1)[0]

    def section(name, drop=(), extra=None, src=None):
        """A [p...] section as the installed table writes it (keys in its order), less drop, with extra."""
        sec = (src or real)[name]
        ls = ['[%s]' % name] + ['%s = %s' % (k, v) for k, v in sec.items() if k not in drop]
        ls += ['%s = %s' % kv for kv in (extra or {}).items()]
        return '\n'.join(ls) + '\n'

    def table(name, sections, defaults_extra=''):
        p = os.path.join(T, 'cfg', name)
        with open(p, 'w') as fh:
            fh.write(hdr.rstrip('\n') + '\n' + defaults_extra + '\n' + '\n'.join(sections))
        return name
    p084 = '[p084]' + base.split('\n[p084]', 1)[1]
    t13 = table('paths13.cfg', [p084, section('p447'), section('p448')])

    def arc_of(name):
        return os.path.join(R13, 'arc_' + name, 'alos')

    def frame(name, path, frame_, sfx, n=12, eo=None, ed=None, plants=None, fbd=(), first_k=0, every=None, **kw):
        """An archive of n granules of one cell: orbits on the path's law from (ed, eo), FBD at the indices in fbd; plants
        maps an index to mkzip's keyword arguments (g016 for G0.16's)."""
        a = arc_of(name)
        orbs = [eo + 671 * (first_k + k) for k in range(n)]
        for i, o in enumerate(orbs):
            args = dict(sfx=sfx, fbd=i in fbd, date=law_date(o, eo, ed))
            args.update(kw)
            args.update((plants or {}).get(i, {}))
            S.mkzip(os.path.join(a, '%02d' % (i % 3)), o, frame_, **args)
        return a, orbs

    def recon(cfg, a, root, path, frame_, extra=None, args=()):
        e = {'LINOG_ROOT': os.path.join(R13, root), 'LINOG_ARCHIVE': a}
        e.update(extra or {})
        rc, out = S.run(T, [path, frame_, '--to', 'recon'] + list(args), cfg=cfg, env_extra=e)
        W = os.path.join(R13, root, 'p' + path, 'f' + frame_)
        rf = os.path.join(W, 'status', 'P0a_recon.json')
        r = json.load(open(rf)) if os.path.isfile(rf) else {}
        jf = os.path.join(W, 'recon', 'RECON.json')
        R = json.load(open(jf)) if os.path.isfile(jf) else {}
        return rc, out, r, R, W

    def g(r, gid):
        return [x for x in r.get('gates', []) if x['id'] == gid] or [{}]

    def gv(r, gid):
        return g(r, gid)[0].get('verdict')

    def gval(r, gid):
        return g(r, gid)[0].get('value', '')

    def gnote(r, gid):
        return g(r, gid)[0].get('note', '')

    # ------------------------------------------------------------------ 9.5: the P447 F0310 cell
    EO, ED = 5230, '20070117'                     # p447's anchor (the table's)
    F310 = dict(path='447', frame='0310')
    cases9 = []

    def c9(cid, desc, plants=None, n=12, cfg=t13, expect=None, fr='0310', path='447', sfx='A', eo=EO, ed=ED, **kw):
        a, orbs = frame(cid, path, fr, sfx, n=n, eo=eo, ed=ed, plants=plants, **kw)
        rc, out, r, R, W = recon(cfg, a, 'root_' + cid, path, fr)
        ok, det = expect(rc, r, R, orbs)
        case('%s %s' % (cid, desc), ok, det)
        return rc, r, R, orbs

    def scene(orb, fr='0310'):
        return 'ALPSRP%05d%s' % (orb, fr)

    def drops(R):
        return sorted(d['scene'] for d in R.get('dropped', []) if 'G0.16' in d.get('reason', ''))

    def dev(R, sc):
        return ((R.get('framing') or {}).get('granules') or {}).get(sc, {}).get('dev_c_km')

    c9('M2', 'one granule\'s (b) and (c) 30.4 km back along track, times unchanged: DROPPED at G0.16 (step 7), its dev_c in the '
       'reason; G0.10 and G0.12 count the 11 others', plants={4: dict(g016=dict(along_km=-30.4))},
       expect=lambda rc, r, R, o: (rc == 0 and gv(r, 'G0.16') == 'PASS' and drops(R) == [scene(o[4])] and
                                   'dev_c -30.' in [d['reason'] for d in R['dropped'] if d['scene'] == scene(o[4])][0]
                                   and 'FBS 11, FBD 0' in gval(r, 'G0.10') and gval(r, 'G0.12').startswith('11,') and len(R['kept']) == 11,
                                   'rc %d; G0.16 %s %s; dropped %s; G0.10 %s; G0.12 %s' % (rc, gv(r, 'G0.16'), gval(r, 'G0.16')[:40],
                                                                                    drops(R), gval(r, 'G0.10'), gval(r, 'G0.12')[:20])))
    c9('M2b', 'one granule 3 km across track only: kept', plants={4: dict(g016=dict(across_km=3.0))},
       expect=lambda rc, r, R, o: (rc == 0 and gv(r, 'G0.16') == 'PASS' and not drops(R) and len(R['kept']) == 12,
                                   'rc %d; G0.16 %s; kept %d; dx %s' % (rc, gv(r, 'G0.16'), len(R.get('kept', [])),
                                                                       ((R.get('framing') or {}).get('granules') or {}).get(scene(o[4]), {}).get('dx_km'))))
    c9('M3', 'four of twelve 30 km back: DECISION (step 6, the share 0.333), nothing dropped',
       plants=dict((i, dict(g016=dict(along_km=-30.0))) for i in (1, 4, 7, 10)),
       expect=lambda rc, r, R, o: (rc == 4 and gv(r, 'G0.16') == 'DECISION' and gval(r, 'G0.16').startswith('step 6') and not drops(R)
                                   and len(R['kept']) == 12, 'rc %d; G0.16 %s %s' % (rc, gv(r, 'G0.16'), gval(r, 'G0.16')[:70])))
    c9('M3a', 'nine of twelve 30 km back: DECISION at the anchor (step 5), the three good granules kept',
       plants=dict((i, dict(g016=dict(along_km=-30.0))) for i in range(3, 12)),
       expect=lambda rc, r, R, o: (rc == 4 and gv(r, 'G0.16') == 'DECISION' and gval(r, 'G0.16').startswith('step 5')
                                   and not drops(R) and len(R['kept']) == 12, 'rc %d; G0.16 %s' % (rc, gval(r, 'G0.16')[:90])))
    c9('M3b', 'one granule\'s (c) position zero: DECISION (step 2)', plants={4: dict(g016=dict(zero_c=True))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 2') and 'position field is zero' in gnote(r, 'G0.16')
                                   and scene(o[4]) in gnote(r, 'G0.16'), 'rc %d; %s; %s' % (rc, gval(r, 'G0.16'), gnote(r, 'G0.16')[:100])))
    c9('M3c', 'one granule\'s (c) taken from the record 2,000 lines on, its line number and time unchanged: dv about 6.3 km, DECISION '
       '(step 3)', plants={4: dict(g016=dict(c_lines=2000))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 3') and scene(o[4]) in gnote(r, 'G0.16')
                                   and 6.1 < abs(float(gnote(r, 'G0.16').split(' dv ')[1].split()[0])) < 6.5,
                                   'rc %d; %s; %s' % (rc, gval(r, 'G0.16')[:60], gnote(r, 'G0.16').splitlines()[0][:80] if gnote(r, 'G0.16') else '')))
    c9('M3d', 'one granule\'s IMG-HH deflated: DECISION (step 2)', plants={4: dict(stored=False)},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 2') and 'not stored' in gnote(r, 'G0.16'),
                                   'rc %d; %s; %s' % (rc, gval(r, 'G0.16'), gnote(r, 'G0.16')[:90])))
    c9('M3e', 'one granule\'s (b) and (c) longitudes 0.4 deg east (inside the band): dx about 42 km, DECISION (step 4)',
       plants={4: dict(g016=dict(lon_deg=0.4))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 4') and scene(o[4]) in gnote(r, 'G0.16')
                                   and 40 < abs(float(gnote(r, 'G0.16').split(' dx ')[1].split()[0])) < 44,
                                   'rc %d; %s; %s' % (rc, gval(r, 'G0.16')[:50], gnote(r, 'G0.16').splitlines()[0][:60] if gnote(r, 'G0.16') else '')))
    c9('M3f', 'four kept: G0.16 INFO (not judged) and recon FAILs at G0.12 (rc 2)', n=4,
       expect=lambda rc, r, R, o: (rc == 2 and gv(r, 'G0.16') == 'INFO' and gv(r, 'G0.12') == 'FAIL',
                                   'rc %d; G0.16 %s; G0.12 %s' % (rc, gv(r, 'G0.16'), gv(r, 'G0.12'))))
    c9('M3fb', 'five, one 30 km back: DROPPED (share 0.2), then G0.12 FAILs on four dates (rc 2)', n=5,
       plants={2: dict(g016=dict(along_km=-30.0))},
       expect=lambda rc, r, R, o: (rc == 2 and drops(R) == [scene(o[2])] and gv(r, 'G0.12') == 'FAIL' and gval(r, 'G0.12').startswith('4,'),
                                   'rc %d; dropped %s; G0.12 %s %s' % (rc, drops(R), gv(r, 'G0.12'), gval(r, 'G0.12')[:10])))
    c9('M3fc', 'eight, two back: both DROPPED (share exactly 0.25)', n=8, plants=dict((i, dict(g016=dict(along_km=-30.0))) for i in (2, 5)),
       expect=lambda rc, r, R, o: (gv(r, 'G0.16') == 'PASS' and drops(R) == sorted([scene(o[2]), scene(o[5])]),
                                   'rc %d; G0.16 %s; dropped %s' % (rc, gv(r, 'G0.16'), drops(R))))
    c9('M3fd', 'eight, three back (share 0.375): DECISION', n=8, plants=dict((i, dict(g016=dict(along_km=-30.0))) for i in (2, 5, 6)),
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 6') and not drops(R),
                                   'rc %d; %s' % (rc, gval(r, 'G0.16')[:60])))
    # M3g: no footprint and the frame outside the frame law's range (13.7, as M43's third case)
    nolaw = table('paths13_nolaw.cfg', [p084, section('p447', drop=('bbox_0310', 'bbox_0290'))])
    with open(os.path.join(T, 'cfg', nolaw)) as fh:
        txt = fh.read()
    assert txt.count('framing_law_A = 0.92026 0.0496858 80 440') == 1
    with open(os.path.join(T, 'cfg', nolaw), 'w') as fh:
        fh.write(txt.replace('framing_law_A = 0.92026 0.0496858 80 440', 'framing_law_A = 0.92026 0.0496858 80 280'))
    c9('M3g', 'no footprint and the frame outside the law\'s range, one granule 30 km back: the anchor not read (INFO), the band '
       'unchecked, DECISION naming the granule, nothing dropped (step 5)', plants={4: dict(g016=dict(along_km=-30.0))}, cfg=nolaw,
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 5: no footprint') and scene(o[4]) in gnote(r, 'G0.16')
                                   and not drops(R) and R.get('anchor_source') == 'none',
                                   'rc %d; %s; source %s' % (rc, gval(r, 'G0.16')[:80], R.get('anchor_source'))))
    c9('M3h', 'one granule at 2,169.2 Hz among granules at 2,145.9 Hz (its span 4.249 s, its (b) to (c) 0.31 km shorter): kept, '
       '|dv| within 0.01 km', plants={4: dict(g016=dict(prf=2169.2))},
       expect=lambda rc, r, R, o: (rc == 0 and not drops(R) and abs(((R.get('framing') or {}).get('granules') or {}).get(scene(o[4]), {})
                                                                    .get('dv_km', 9)) <= 0.01
                                   and abs(((R.get('framing') or {}).get('granules') or {}).get(scene(o[4]), {}).get('span_s', 0) - 4.249) < 0.001,
                                   'rc %d; dv %s; span %s' % (rc, ((R.get('framing') or {}).get('granules') or {}).get(scene(o[4]), {}).get('dv_km'),
                                                             ((R.get('framing') or {}).get('granules') or {}).get(scene(o[4]), {}).get('span_s'))))
    c9('M3i', 'one granule\'s middle record with a line number one off: DECISION (step 2)', plants={4: dict(g016=dict(mid_line_off=1))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 2') and 'middle record not aligned' in gnote(r, 'G0.16'),
                                   'rc %d; %s' % (rc, gnote(r, 'G0.16')[:100])))
    c9('M3j', 'one granule\'s (b) and (c) 1.0 deg east, outside the band (9.5\'s 0.6 deg leaves the cell\'s centre 0.21 deg beyond '
       'the footprint\'s east edge, inside the +-0.5 deg band): DECISION (step 2)', plants={4: dict(g016=dict(lon_deg=1.0))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 2') and 'outside the footprint' in gnote(r, 'G0.16'),
                                   'rc %d; %s' % (rc, gnote(r, 'G0.16')[:100])))
    c9('M3k', 'one granule\'s two times equal: DECISION (step 2)', plants={4: dict(g016=dict(equal_times=True))},
       expect=lambda rc, r, R, o: (rc == 4 and gval(r, 'G0.16').startswith('step 2') and 'not later' in gnote(r, 'G0.16'),
                                   'rc %d; %s' % (rc, gnote(r, 'G0.16')[:100])))
    c9('M3l', 'one granule 11.2 km back, between the arc reading\'s line (11.12 km) and the registered one (11.27 km): kept',
       plants={4: dict(g016=dict(along_km=-11.2))},
       expect=lambda rc, r, R, o: (rc == 0 and not drops(R) and dev(R, scene(o[4])) is not None and -11.27 < dev(R, scene(o[4])) < -11.1,
                                   'rc %d; dev_c %s' % (rc, dev(R, scene(o[4])))))
    # M3m: M2 on a descending track, F3310's cell (path 84, felix's corners, the table's bbox_3310)
    c9('M3m', 'M2 on a descending track (P084 F3310, heading 191 deg): DROPPED', path='084', fr='3310', sfx='D', eo=10488, ed='20080113',
       plants={4: dict(g016=dict(along_km=-30.4))},
       expect=lambda rc, r, R, o: (rc == 0 and drops(R) == [scene(o[4], '3310')] and abs((R.get('framing') or {}).get('cell', {})
                                                                                     .get('heading_deg', 0) - 191.0) < 0.05,
                                   'rc %d; dropped %s; heading %s' % (rc, drops(R), (R.get('framing') or {}).get('cell', {}).get('heading_deg'))))

    # ------------------------------------------------------------------ 13.7: a derived path, P446 F0290 (residue 285)
    import lp_common as C
    res446 = C.residue_of(446)
    EO446 = res446 + 671 * 7                       # an anchor on the path's lattice; the date law is the mock's own
    ED446 = '20070105'
    a33, o33 = frame('M33', '446', '0290', 'A', eo=EO446, ed=ED446, fbd=(1, 4, 7, 10))
    rc, out, r, R, W33 = recon(t13, a33, 'root_M33', '446', '0290')
    pe = os.path.join(W33, 'recon', 'path_entry.cfg')
    cpe = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    okpe = os.path.isfile(pe) and bool(cpe.read(pe)) and cpe.has_section('p446')
    sec = cpe['p446'] if okpe else {}
    law_anchor = (R.get('framing') or {}).get('cell', {}).get('anchor_km')
    case('M33 a derived path (P446 F0290, 12 granules, FBS and FBD; the table lacks [p446]): G0.17 WARN (residue 285, A); G0.5 PASS '
         '(the law all 12 share), G0.6 PASS, G0.13 INFO, G0.18 PASS; G0.16 PASS, its anchor from the frame law within 0.5 km; G0.14 '
         'PASS by the derived footprint; RECON.json entry derived, anchor source "law"; recon/path_entry.cfg a [p446] section with '
         'expect_0290 = 12 and no bbox_ key',
         rc == 0 and gv(r, 'G0.17') == 'WARN' and 'residue 285' in gval(r, 'G0.17') and 'direction A' in gval(r, 'G0.17')
         and gv(r, 'G0.5') == 'PASS' and gv(r, 'G0.6') == 'PASS' and gv(r, 'G0.13') == 'INFO' and gv(r, 'G0.18') == 'PASS'
         and gv(r, 'G0.16') == 'PASS' and law_anchor is not None and abs(law_anchor) <= 0.5 and gv(r, 'G0.14') == 'PASS'
         and R.get('entry') == 'derived' and R.get('anchor_source') == 'law' and okpe and sec.get('expect_0290') == '12'
         and sec.get('residue') == '285' and sec.get('direction') == 'A' and not any(k.startswith('bbox_') for k in sec)
         and sec.get('epoch_orbit') == str(o33[0]),
         'rc %d; G0.17 %s; G0.5 %s; G0.16 %s anchor %s; G0.14 %s; entry %s source %s; path_entry %s %s' % (
             rc, gv(r, 'G0.17'), gv(r, 'G0.5'), gv(r, 'G0.16'), law_anchor, gv(r, 'G0.14'), R.get('entry'), R.get('anchor_source'),
             okpe, dict(sec) if okpe else None))
    # every phase's --state on the derived frame prints a state word; the five that read direction get A from the loader
    phases = S.PHASES_ALL()
    words, bad = [], []
    env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', t13), LINOG_ROOT=os.path.join(R13, 'root_M33'), LINOG_ARCHIVE=a33,
               LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
               LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'))
    for ph in phases:
        p = subprocess.run(['python3', '-E', '-B', os.path.join(HERE, 'lp_%s.py' % ph), '--path', '446', '--frame', '0290', '--state'],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        w = p.stdout.decode('utf-8', 'replace').strip().splitlines()
        words.append(w[-1] if w else '')
        if p.returncode != 0 or not w or not w[-1].isupper():
            bad.append('%s rc %d %s' % (ph, p.returncode, (w or [''])[-1][:60]))
    p = subprocess.run(['python3', '-E', '-B', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import lp_common as C; '
                        'print(C.load_cfg("446", "0290")["direction"])', HERE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    five = [ph for ph in ('deliver', 'd9ab', 'mcfg', 'report', 'sbas')
            if "cfg['direction']" in open(os.path.join(HERE, 'lp_%s.py' % ph)).read()
            and 'C.load_cfg(path, frame)' in open(os.path.join(HERE, 'lp_%s.py' % ph)).read()]
    case('M33 (later phases) every one of the %d phases\' --state on the derived frame prints a state word (exit 0); deliver, d9ab, '
         'mcfg, report and sbas read cfg[\'direction\'] from C.load_cfg(path, frame), which gives A there' % len(phases),
         not bad and p.stdout.decode().strip() == 'A' and len(five) == 5,
         'states %s; %s; loader %s; the five %s' % (sorted(set(words)), '; '.join(bad) or 'all exit 0', p.stdout.decode().strip(), five))
    # M33b: the proposed entry added to the table
    t33b = table('paths13_446.cfg', [p084, section('p447'), section('p448'),
                                     '[p446]\n' + ''.join('%s = %s\n' % kv for kv in sec.items())] if okpe else [p084])
    env['LINOG_AUTO_CFG'] = os.path.join(T, 'cfg', t33b)
    st0 = subprocess.run(['python3', '-E', '-B', os.path.join(HERE, 'lp_recon.py'), '--path', '446', '--frame', '0290', '--state'],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip()
    rc, out, r, R, _ = recon(t33b, a33, 'root_M33', '446', '0290')
    case('M33b M33\'s path_entry.cfg added to the table: recon STALE, then G0.17 PASS, G0.13 PASS, G0.16\'s anchor still from the law '
         '(no bbox_0290), G0.14 without a table footprint beside',
         st0 == 'STALE' and rc == 0 and gv(r, 'G0.17') == 'PASS' and gv(r, 'G0.13') == 'PASS' and R.get('anchor_source') == 'law'
         and R.get('entry') == 'table' and R.get('footprint_table') is None and 'table\'s footprint' not in gnote(r, 'G0.14'),
         'state %s; rc %d; G0.17 %s; G0.13 %s; source %s; footprint_table %s' % (st0, rc, gv(r, 'G0.17'), gv(r, 'G0.13'),
                                                                                R.get('anchor_source'), R.get('footprint_table')))
    # M34: the anchor of a derived entry
    for cid, desc, plants, want in (
            ('M34', 'one granule\'s summary.txt date 46 days late: G0.5 FAIL naming it alone', {5: 'late'}, [5]),
            ('M34b', 'the earliest granule\'s 46 days late: G0.5 FAIL naming it alone, the law the other 11\'s', {0: 'late'}, [0]),
            ('M34c', '6 of 12 dates one way and 6 another: G0.5 FAIL naming all 12', dict((i, 'late') for i in range(6)), list(range(12)))):
        a = arc_of(cid)
        orbs = [EO446 + 671 * k for k in range(12)]
        for i, o in enumerate(orbs):
            d = law_date(o, EO446, ED446)
            if plants.get(i) == 'late':
                d = (datetime.datetime.strptime(d, '%Y%m%d') + datetime.timedelta(days=46)).strftime('%Y%m%d')
            S.mkzip(os.path.join(a, '%02d' % (i % 3)), o, '0290', sfx='A', date=d)
        rc, out, r, R, _ = recon(t13, a, 'root_' + cid, '446', '0290')
        named = sorted(ln.split()[0] for ln in gnote(r, 'G0.5').splitlines() if ln.strip())
        wantn = sorted('ALPSRP%05d0290-H1.1__A.zip' % orbs[i] for i in want)
        case('%s %s' % (cid, desc), rc == 2 and gv(r, 'G0.5') == 'FAIL' and named == wantn
             and ((cid != 'M34b') or (R.get('entry_derived') or {}).get('anchor', {}).get('orbit') == orbs[1]),
             'rc %d; G0.5 %s; named %d %s; anchor %s' % (rc, gval(r, 'G0.5')[:70], len(named), named[:2],
                                                       ((R.get('entry_derived') or {}).get('anchor') or {}).get('scene')))
    # M35: the direction
    a, orbs = frame('M35', '447', '0310', 'A', eo=EO, ed=ED, plants={3: dict(sfx='D')})
    rc, out, r, R, _ = recon(t13, a, 'root_M35', '447', '0310')
    case('M35 one granule\'s suffix __D on an ascending frame: G0.6 FAIL', rc == 2 and gv(r, 'G0.6') == 'FAIL'
         and scene(orbs[3]) in gnote(r, 'G0.6'), 'rc %d; G0.6 %s %s' % (rc, gv(r, 'G0.6'), gnote(r, 'G0.6')[:40]))
    a, orbs = frame('M35b', '085', '3300', 'D', eo=671 * 15, ed='20070310')
    rc, out, r, R, _ = recon(t13, a, 'root_M35b', '085', '3300')
    case('M35b a derived frame 3300 with __D suffixes (path 85, residue 0): direction D, G0.6 PASS, its anchor from the descending law',
         rc == 0 and R.get('direction') == 'D' and gv(r, 'G0.6') == 'PASS' and R.get('anchor_source') == 'law'
         and abs((R.get('framing') or {}).get('cell', {}).get('heading_deg', 0) - 191.0) < 0.05,
         'rc %d; direction %s; G0.6 %s; source %s' % (rc, R.get('direction'), gv(r, 'G0.6'), R.get('anchor_source')))
    db = [C.dir_by_frame(f) for f in (1799, 1800, 5399, 5400)]
    case('M35c dir_by_frame at 1799, 1800, 5399 and 5400: A, D, D, A', db == ['A', 'D', 'D', 'A'], '%s' % db)
    # M36: the formula's edges
    rt = all(C.path_of(C.residue_of(p_)) == p_ for p_ in range(1, 672))
    case('M36 residue_of(85) 0, residue_of(671) 392, path_of(392) 671, the round trip on paths 1 to 671; the tables\' 8 sections on it',
         C.residue_of(85) == 0 and C.residue_of(671) == 392 and C.path_of(392) == 671 and rt
         and all(int(real['p' + s_]['residue']) == C.residue_of(int(s_)) for s_ in ('084', '083', '086', '087', '447', '448', '449', '450')),
         '%d %d %d round trip %s' % (C.residue_of(85), C.residue_of(671), C.path_of(392), rt))
    # M37: a wrong table residue
    t37 = table('paths13_r534.cfg', [p084, section('p447', drop=('residue',), extra={'residue': '534'})])
    a37 = arc_of('M3l')       # any p447 archive; G0.17 stops recon before a granule is read
    rc, out, r, R, _ = recon(t37, a37, 'root_M37', '447', '0310')
    case('M37 [p447] with residue 534: G0.17 FAIL (the formula gives 533); G0.2 to G0.16 not reached',
         rc == 2 and gv(r, 'G0.17') == 'FAIL' and not any(x['id'] in ('G0.2', 'G0.16', 'G0.4') for x in r.get('gates', [])),
         'rc %d; G0.17 %s; gates %s' % (rc, gval(r, 'G0.17')[:60], [x['id'] for x in r.get('gates', [])]))
    t38 = table('paths13_noeo.cfg', [p084, section('p447', drop=('epoch_orbit',))])
    rc, out, r, R, W38 = recon(t38, a37, 'root_M38', '447', '0310')
    t38b = table('paths13_p84.cfg', [p084, section('p447'), '[p84]\ndirection = D\nresidue = 423\nepoch_date = 20080113\nepoch_orbit = 10488\n'])
    rc2, out2, _, _, _ = recon(t38b, a37, 'root_M38b', '084', '3320')
    case('M38 [p447] without epoch_orbit: ERROR, rc 3, as v0.12 (the frame folder not made); a table holding [p84] beside [p084]: '
         'ERROR naming the section, rc 3',
         rc == 3 and "'epoch_orbit'" in out and not os.path.exists(W38) and rc2 == 3 and '[p84]' in out2,
         'rc %d (%s); rc %d (%s)' % (rc, [ln for ln in out.splitlines() if 'epoch_orbit' in ln][:1],
                                     rc2, [ln for ln in out2.splitlines() if 'p84' in ln][:1]))
    # M39: G0.14 by the derived footprint
    for cid, desc, west, want in (('M39', 'corners 0.05 deg past the DEM\'s west edge: G0.14 FAIL (west -0.05)', 119.95, '-0.050'),
                                  ('M39b', 'a margin of exactly 0.1 deg in decimal (west edge 120.1 on the DEM\'s 120.0, 0.09999999999999432 '
                                   'in float64): FAIL, as lp_recon.py\'s float comparison', 120.1, '0.100')):
        a, orbs = frame(cid, '446', '0290', 'A', eo=EO446, ed=ED446,
                        g016=dict(centre=(15.329, 120.43), corners=(15.0, 15.66, west, 120.9)))
        rc, out, r, R, _ = recon(t13, a, 'root_' + cid, '446', '0290')
        m = (R.get('dem') or {}).get('margins', {})
        case('%s %s' % (cid, desc), rc == 2 and gv(r, 'G0.14') == 'FAIL' and ('W %s' % want) in gval(r, 'G0.14') and m.get('W', 1) < 0.1,
             'rc %d; G0.14 %s; W margin %r' % (rc, gval(r, 'G0.14')[:50], m.get('W')))
    # M40: unusable corners, without and with a table footprint
    for cid, plant, why in (('M40', dict(g016=dict(last_line_off=1)), 'last record not aligned'),
                            ('M40b', dict(g016=dict(zero_corner=True)), 'a corner is zero'),
                            ('M40c', dict(g016=dict(corner_far_deg=1.5)), 'more than 1.00 deg')):
        a, orbs = frame(cid, '446', '0290', 'A', eo=EO446, ed=ED446, plants={4: plant})
        rc, out, r, R, _ = recon(t13, a, 'root_' + cid, '446', '0290')
        a2, orbs2 = frame(cid + 't', '447', '0310', 'A', eo=EO, ed=ED, plants={4: plant})
        rc2, out2, r2, R2, _ = recon(t13, a2, 'root_' + cid + 't', '447', '0310')
        case('%s one kept granule: %s: without a table footprint (P446 F0290) G0.14 DECISION naming it; with one (P447 F0310) PASS by '
             'the union, WARN naming it' % (cid, why),
             rc == 4 and gv(r, 'G0.14') == 'DECISION' and why in gnote(r, 'G0.14') and ('ALPSRP%05d0290' % orbs[4]) in gnote(r, 'G0.14')
             and gv(r2, 'G0.14') == 'WARN' and why in gnote(r2, 'G0.14') and scene(orbs2[4]) in gnote(r2, 'G0.14') and rc2 == 0,
             'rc %d G0.14 %s; rc %d G0.14 %s (%s)' % (rc, gv(r, 'G0.14'), rc2, gv(r2, 'G0.14'), gnote(r2, 'G0.14')[:60]))
    # M41: the table's footprint 0.06 deg short on the east
    a41, o41 = frame('M41', '447', '0310', 'A', eo=EO, ed=ED)
    rc0, _, _, R0, _ = recon(t13, a41, 'root_M41a', '447', '0310')
    E_ = ((R0.get('footprint') or {}).get('SNWE') or [0, 0, 0, 0])[3]
    bb = real['p447']['bbox_0310'].split()
    t41 = table('paths13_m41.cfg', [p084, section('p447', drop=('bbox_0310',), extra={'bbox_0310': '%s %s %s %.6f' % (
        bb[0], bb[1], bb[2], E_ - 0.06)})])
    rc, out, r, R, _ = recon(t41, a41, 'root_M41', '447', '0310')
    case('M41 the table\'s bbox_0310 0.06 deg short of the corners on the east: G0.14 PASS by the derived footprint, WARN naming the side',
         rc == 0 and gv(r, 'G0.14') == 'WARN' and 'more than 0.05 deg on E' in gnote(r, 'G0.14')
         and abs((R.get('footprint_differences') or {}).get('E', 0) - 0.06) < 1e-6,
         'rc %d; G0.14 %s; differences %s' % (rc, gv(r, 'G0.14'), R.get('footprint_differences')))
    # M42, M43: moved granules on a derived path (the law's anchor)
    a, orbs = frame('M42', '446', '0290', 'A', eo=EO446, ed=ED446, plants={4: dict(g016=dict(along_km=-30.0))})
    rc, out, r, R, _ = recon(t13, a, 'root_M42', '446', '0290')
    case('M42 a derived path, one granule 30 km back: G0.16 DROPPED (step 7, the law\'s anchor within 0.5 km)',
         rc == 0 and drops(R) == ['ALPSRP%05d0290' % orbs[4]] and abs((R.get('framing') or {}).get('cell', {}).get('anchor_km', 9)) <= 0.5
         and R.get('anchor_source') == 'law', 'rc %d; dropped %s; anchor %s' % (rc, drops(R), (R.get('framing') or {}).get('cell', {}).get('anchor_km')))
    t43 = table('paths13_nolaw290.cfg', [p084, section('p447'), section('p448')])
    with open(os.path.join(T, 'cfg', t43)) as fh:
        txt = fh.read()
    with open(os.path.join(T, 'cfg', t43), 'w') as fh:
        fh.write(txt.replace('framing_law_A = 0.92026 0.0496858 80 440', 'framing_law_A = 0.92026 0.0496858 80 280'))
    for cid, km, cfg, want in (('M43', 11.0, t13, 'step 5: the anchor'), ('M43b', 8.0, t13, 'step 5: the anchor'),
                               ('M43c', 12.0, t43, 'step 5: no footprint'), ('M43d', 11.0, t43, 'PASS')):
        a, orbs = frame(cid, '446', '0290', 'A', eo=EO446, ed=ED446,
                        plants=dict((i, dict(g016=dict(along_km=-km))) for i in range(3, 12)))
        rc, out, r, R, _ = recon(cfg, a, 'root_' + cid, '446', '0290')
        named = sorted(ln.split()[0] for ln in gnote(r, 'G0.16').splitlines() if ln.startswith('ALPSRP'))
        ok = (rc == 0 and gv(r, 'G0.16') == 'PASS' and not drops(R)) if want == 'PASS' else (
            rc == 4 and gval(r, 'G0.16').startswith(want) and not drops(R)
            and (cid != 'M43c' or named == sorted('ALPSRP%05d0290-H1.1__A.zip' % orbs[i] for i in range(3))))
        case('%s nine of twelve granules %g km back on a derived path%s: %s' % (
            cid, km, ' with the law\'s range leaving the frame out' if cfg == t43 else '',
            {'M43': 'DECISION at the law\'s anchor', 'M43b': 'DECISION at the law\'s anchor',
             'M43c': 'DECISION naming the 3 good (no anchor: the no-footprint rule)', 'M43d': 'PASS (the window 13.3 F names)'}[cid]),
             ok, 'rc %d; G0.16 %s %s; named %s' % (rc, gv(r, 'G0.16'), gval(r, 'G0.16')[:60], len(named)))
    # M44: the beam guard
    a44, o44 = frame('M44', '446', '0290', 'A', n=5, eo=EO446, ed=ED446, offnadir=41.5, width=10976)
    rc, out, r, R, W44 = recon(t13, a44, 'root_M44', '446', '0290')
    case('M44 five granules at 41.5 deg (a beam linog_auto has not run): G0.18 DECISION, nothing dropped',
         rc == 4 and gv(r, 'G0.18') == 'DECISION' and len(R.get('kept', [])) == 5, 'rc %d; G0.18 %s' % (rc, gval(r, 'G0.18')[:60]))
    with open(os.path.join(W44, 'recon', 'beam.txt'), 'w') as fh:
        fh.write('# self-test M44b\n41.5 accepted for the self-test (a person\'s word)\n')
    rc, out, r, R, _ = recon(t13, a44, 'root_M44', '446', '0290')
    case('M44b recon/beam.txt "41.5 <reason>": G0.18 INFO, the frame goes on, G0.16 without an anchor (the law is the standard beam\'s)',
         rc == 0 and gv(r, 'G0.18') == 'INFO' and gv(r, 'G0.16') == 'PASS' and R.get('anchor_source') == 'none'
         and (R.get('beam') or {}).get('accepted_by') == 'recon/beam.txt',
         'rc %d; G0.18 %s; G0.16 %s; source %s' % (rc, gv(r, 'G0.18'), gv(r, 'G0.16'), R.get('anchor_source')))
    with open(os.path.join(W44, 'recon', 'beam.txt'), 'w') as fh:
        fh.write('50.0 a beam the frame does not hold\n')
    rc, out, r, R, _ = recon(t13, a44, 'root_M44', '446', '0290')
    case('M44c recon/beam.txt "50.0 <reason>": WARN "not applied", the DECISION stays',
         rc == 4 and gv(r, 'G0.18f') == 'WARN' and 'not applied' in gval(r, 'G0.18f') and gv(r, 'G0.18') == 'DECISION',
         'rc %d; G0.18f %s; G0.18 %s' % (rc, gval(r, 'G0.18f')[:60], gv(r, 'G0.18')))
    a, orbs = frame('M44d', '447', '0310', 'A', n=28, eo=EO, ed=ED,
                    plants=dict((i, dict(offnadir=41.5, width=10976)) for i in (3, 9, 15, 21)))
    rc, out, r, R, _ = recon(t13, a, 'root_M44d', '447', '0310')
    case('M44d 24 granules at 34.3 deg with 4 at 41.5 deg: G1 drops the four, G0.18 PASS',
         rc == 0 and gv(r, 'G1') == 'PASS' and '24 kept, 4 dropped' in gval(r, 'G1') and gv(r, 'G0.18') == 'PASS',
         'rc %d; G1 %s; G0.18 %s' % (rc, gval(r, 'G1'), gv(r, 'G0.18')))
    # M45: the path runner
    PR = os.path.join(HERE, 'linog_path.sh')

    def prun(args, cfg=t13, extra=None):
        e = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        e.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfg), LINOG_AUTO_HOST=S.socket.gethostname(),
                 LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                 LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'))
        e.update(extra or {})
        p = subprocess.run(['bash', PR] + args, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        o = p.stdout.decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_path.sh %s (cfg %s) rc %d\n%s' % (' '.join(args), cfg, p.returncode, o))
        return p.returncode, o
    r1, o1 = prun(['446'])
    r2, o2 = prun(['999'])
    r3, o3 = prun(['446', '0290', '--to', 'recon'], extra={'LINOG_ROOT': os.path.join(R13, 'root_M45'), 'LINOG_ARCHIVE': a33})
    case('M45 linog_path.sh 446 with no frame: rc 3, "path 446 is not in the path table (R8 derives its entry): name its frames"; '
         'linog_path.sh 999: rc 3, "not a path number"; linog_path.sh 446 0290: the frame runs (recon PASS, rc 0)',
         r1 == 3 and 'path 446 is not in the path table (R8 derives its entry): name its frames' in o1 and r2 == 3
         and 'not a path number' in o2 and r3 == 0 and '== frame 0290' in o3,
         'rc %d, %d, %d' % (r1, r2, r3))
    # M46: an unreadable folder of the archive
    if os.geteuid() == 0:
        case('M46 a batch folder of the archive at mode 000: G0.2 FAIL naming it (skipped: the suite runs as root, euid 0, which reads '
             'any mode; on felix it runs as arieln)', True, 'skipped as root')
    else:
        a46, o46 = frame('M46', '447', '0310', 'A', eo=EO, ed=ED)
        locked = os.path.join(a46, '01')
        os.chmod(locked, 0)
        try:
            rc, out, r, R, _ = recon(t13, a46, 'root_M46', '447', '0310')
        finally:
            os.chmod(locked, 0o755)
        case('M46 a batch folder of the archive at mode 000: G0.2 FAIL naming it', rc == 2 and gv(r, 'G0.2') == 'FAIL'
             and locked in gnote(r, 'G0.2'), 'rc %d; G0.2 %s' % (rc, gnote(r, 'G0.2')[:80]))
    # M47: the middle and last records of a stored 200 MB member, read by offset under both Pythons
    a47 = arc_of('M47')
    z47 = S.mkzip(os.path.join(a47, '00'), EO, '0310', sfx='A', date=ED, width=9344, lines=2662)
    probe = r'''
import io, json, sys, zipfile
sys.path.insert(0, sys.argv[1])
import lp_recon as R
class Count(io.RawIOBase):
    def __init__(self, f): self.f, self.n = f, 0
    def read(self, n=-1):
        b = self.f.read(n); self.n += len(b); return b
    def seek(self, *a): return self.f.seek(*a)
    def tell(self): return self.f.tell()
    def readable(self): return True
    def seekable(self): return True
raw = open(sys.argv[2], 'rb')
z = zipfile.ZipFile(raw)
zi = [i for i in z.infolist() if i.filename.startswith('IMG-HH')][0]
head = z.open(zi).read(4096)
nrec, rl = R.ascii_int(head, 180, 6), R.ascii_int(head, 186, 6)
d0 = R.member_data_offset(raw, zi)
cw = Count(raw)
got = R.records_by_offset(cw, d0, 720, rl, nrec)
mine = cw.n
zc = Count(open(sys.argv[2], 'rb'))
z2 = zipfile.ZipFile(zc)
same = True
for key, (idx, b) in sorted(got.items()):
    with z2.open(zi) as fh:
        fh.seek(720 + idx * rl)
        same &= fh.read(412) == b
print(json.dumps(dict(python=sys.version.split()[0], size=zi.file_size, read_by_offset=mine, zipfile_read=zc.n, same=same,
                      idx=[got['mid'][0], got['last'][0]])))
'''
    outs = []
    for py in sorted(set([sys.executable, S.MOCKPY[0] or sys.executable])):
        p = subprocess.run([py, '-I', '-B', '-c', probe, HERE, z47], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            outs.append(json.loads(p.stdout.decode().strip().splitlines()[-1]))
        except (ValueError, IndexError):
            outs.append(dict(error=p.stdout.decode()[-300:]))
    case('M47 the middle and last records of a stored 200 MB member, read by offset (lp_recon.records_by_offset) under this host\'s '
         'Pythons: the bytes zipfile itself returns, 412 B read a record (a counting wrapper on the file object)',
         outs and all(o.get('same') and o.get('read_by_offset') == 2 * 412 and o.get('size', 0) > 2e8 for o in outs),
         '; '.join('python %s: %s B member, %s B read by offset, %s B through zipfile\'s seek, same %s' % (
             o.get('python'), o.get('size'), o.get('read_by_offset'), o.get('zipfile_read'), o.get('same')) if 'error' not in o
             else o['error'] for o in outs))

    # ------------------------------------------------------------------ M90, M91: 12.3's items 2 and 3
    a90, o90 = frame('M90', '447', '0310', 'A', eo=EO, ed=ED)
    if os.geteuid() == 0:
        foreign = os.path.join(R13, 'root_foreign')
        os.makedirs(foreign)
        os.chown(foreign, 54321, 54321)
        rootdesc = 'a root owned by uid 54321'
    else:
        foreign = '/linog_selftest_absent_%d/root' % os.getpid()
        rootdesc = 'a root under / (uid 0) that does not exist'
    t90 = table('paths13_foreign.cfg', [p084, section('p447')])
    with open(os.path.join(T, 'cfg', t90)) as fh:
        txt = fh.read()
    root_line = [ln for ln in txt.splitlines() if ln.startswith('root = ')][0]
    with open(os.path.join(T, 'cfg', t90), 'w') as fh:
        fh.write(txt.replace(root_line + '\n', 'root = %s\n' % foreign))
    e = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
    e.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', t90), LINOG_AUTO_HOST=S.socket.gethostname(), LINOG_ARCHIVE=a90,
             LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'))
    p = subprocess.run(['bash', S.ENTRY, '447', '0310', '--to', 'recon'], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o90r, rc90 = p.stdout.decode('utf-8', 'replace'), p.returncode
    made = os.path.exists(os.path.join(foreign, 'p447'))
    D90 = os.path.join(R13, 'dry_M90')
    p2 = subprocess.run(['bash', S.ENTRY, '447', '0310', '--to', 'recon', '--dry-run', D90], env=e, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
    dr = json.load(open(os.path.join(D90, 'status', 'P0a_recon.json'))) if os.path.isfile(os.path.join(D90, 'status', 'P0a_recon.json')) else {}
    rc3, out3, r3, R3, _ = recon(t90, a90, 'root_M90', '447', '0310')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## M90 linog_auto.sh 447 0310 --to recon (cfg %s, root %s) rc %d\n%s' % (t90, foreign, rc90, o90r))
    case('M90 (12.3, item 2) the path table\'s root is %s, no LINOG_ROOT: the driver stops before it writes anything (rc 2, recon\'s '
         'G0.19 FAIL printed, no p447/ made); a dry run records G0.19 FAIL in DIR; the same frame with LINOG_ROOT naming a root: '
         'G0.19 PASS "LINOG_ROOT names it", recon PASS' % rootdesc,
         rc90 == 2 and 'G0.19   FAIL' in o90r and "recon's G0.19 refused the root" in o90r and not made
         and gv(dr, 'G0.19') == 'FAIL' and rc3 == 0 and gv(r3, 'G0.19') == 'PASS' and 'LINOG_ROOT names it' in gval(r3, 'G0.19'),
         'rc %d (made %s); dry run G0.19 %s; with LINOG_ROOT rc %d G0.19 %s' % (rc90, made, gv(dr, 'G0.19'), rc3, gv(r3, 'G0.19')))
    fake = os.path.join(R13, 'oldpy')
    os.makedirs(fake)
    with open(os.path.join(fake, 'python3'), 'w') as fh:
        fh.write('#!/bin/sh\n# self-test M91: a python3 older than 3.6 first on the PATH\necho 3.5.10\nexit 1\n')
    os.chmod(os.path.join(fake, 'python3'), 0o755)
    e2 = dict(e, PATH=fake + ':' + os.environ.get('PATH', '/usr/bin:/bin'))
    p = subprocess.run(['bash', S.ENTRY, '447', '0310', '--to', 'recon'], env=e2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o91 = p.stdout.decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## M91 linog_auto.sh 447 0310 (a python3 3.5.10 first on the PATH) rc %d\n%s' % (p.returncode, o91))
    p2 = subprocess.run(['bash', S.ENTRY, '447', '0310', '--to', 'recon'], env=dict(e, LINOG_ROOT=os.path.join(R13, 'root_M91')),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o91b = p2.stdout.decode('utf-8', 'replace')
    case('M91 (12.3, item 3) a python3 3.5 first on the PATH: the driver stops before it resolves the frame, rc 3, naming it; with the '
         'host\'s python3: the header prints the driver\'s python and the run goes on (rc 0)',
         p.returncode == 3 and 'is not Python 3.6 or later' in o91 and '3.5.10' in o91 and '== linog_auto' not in o91
         and p2.returncode == 0 and "(the driver's: --state, recon, stage, extract, package)" in o91b,
         'rc %d (%s); rc %d' % (p.returncode, [ln for ln in o91.splitlines() if 'Python 3.6' in ln][:1], p2.returncode))

    # ------------------------------------------------------------------ the part 1 review's fixes (B1, M1, M2, m2 to m4)
    phase13_review(T, case, S, R13, real, table, section, p084, t13, t90, foreign, frame, recon, prun, arc_of,
                   g, gv, gval, gnote, scene, drops, dev, EO, ED, EO446, ED446, a90)


def tree_snap(top):
    """Every entry under top: a file's md5, a link's target, a folder (the B1 case's before and after)."""
    import hashlib
    out = {}
    for d, dirs, files in os.walk(top):
        for n in dirs:
            p_ = os.path.join(d, n)
            out[os.path.relpath(p_, top) + ('' if os.path.islink(p_) else '/')] = \
                ('link ' + os.readlink(p_)) if os.path.islink(p_) else 'dir'
        for n in files:
            p_ = os.path.join(d, n)
            out[os.path.relpath(p_, top)] = ('link ' + os.readlink(p_)) if os.path.islink(p_) else \
                hashlib.md5(open(p_, 'rb').read()).hexdigest()
    return out


def patch_summary(zpath, key, value):
    """Rewrite one summary.txt key of a mock zip (value None: the key left out); the other members copied as they are."""
    import zipfile
    tmp = zpath + '.tmp'
    with zipfile.ZipFile(zpath) as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for zi in zin.infolist():
            data = zin.read(zi)
            if zi.filename.endswith('summary.txt'):
                ls = []
                for ln in data.decode().splitlines():
                    if ln.startswith(key + '='):
                        if value is None:
                            continue
                        ln = '%s="%s"' % (key, value)
                    ls.append(ln)
                data = ('\n'.join(ls) + '\n').encode()
            zout.writestr(zi, data, compress_type=zi.compress_type)
    os.replace(tmp, zpath)


def vincenty_direct(lat1, lon1, az1, s, a=6378137.0, f=1 / 298.257223563):
    """Vincenty's (1975) direct problem on WGS84: the point s m from (lat1, lon1) at azimuth az1 deg. An independent
    geodesic for M97 (the part 1 review's m4), not the ENU code under test (lp_recon.en, lp_selftest.en_inv)."""
    import math
    b = (1 - f) * a
    al1 = math.radians(az1)
    u1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    s1 = math.atan2(math.tan(u1), math.cos(al1))
    sa = math.cos(u1) * math.sin(al1)
    c2a = 1 - sa * sa
    uu = c2a * (a * a - b * b) / (b * b)
    A = 1 + uu / 16384 * (4096 + uu * (-768 + uu * (320 - 175 * uu)))
    B = uu / 1024 * (256 + uu * (-128 + uu * (74 - 47 * uu)))
    sig = s / (b * A)
    for _ in range(200):
        c2m = math.cos(2 * s1 + sig)
        ss, cs = math.sin(sig), math.cos(sig)
        ds = B * ss * (c2m + B / 4 * (cs * (-1 + 2 * c2m * c2m) - B / 6 * c2m * (-3 + 4 * ss * ss) * (-3 + 4 * c2m * c2m)))
        new = s / (b * A) + ds
        done = abs(new - sig) < 1e-13
        sig = new
        if done:
            break
    c2m = math.cos(2 * s1 + sig)
    ss, cs = math.sin(sig), math.cos(sig)
    t = math.sin(u1) * ss - math.cos(u1) * cs * math.cos(al1)
    lat2 = math.atan2(math.sin(u1) * cs + math.cos(u1) * ss * math.cos(al1), (1 - f) * math.sqrt(sa * sa + t * t))
    lam = math.atan2(ss * math.sin(al1), math.cos(u1) * cs - math.sin(u1) * ss * math.cos(al1))
    C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
    L = lam - (1 - C) * f * sa * (sig + C * ss * (c2m + C * cs * (-1 + 2 * c2m * c2m)))
    return math.degrees(lat2), lon1 + math.degrees(L)


def phase13_review(T, case, S, R13, real, table, section, p084, t13, t90, foreign, frame, recon, prun, arc_of,
                   g, gv, gval, gnote, scene, drops, dev, EO, ED, EO446, ED446, a90):
    """The part 1 review's fixes (review/p1/REPORT.md): B1 (M95), M1 (M90b), M2 (M34d), m2 (M41b, M42b), m3 (M96 to M96c),
    m4 (M97)."""
    import lp_common as C
    print('-- v0.13 part 1 review: the frame folder (G0.20), the runner\'s root check, the summary date, the law\'s band, '
          'G0.16a, dem_<frame>, an independent geodesic')
    # M95 (B1): a course-kit tree at the default frame folder
    EO448, ED448 = int(real['p448']['epoch_orbit']), real['p448']['epoch_date']
    a95, o95 = frame('M95', '448', '0310', 'A', eo=EO448, ed=ED448)
    R95 = os.path.join(R13, 'root_M95')
    P95 = os.path.join(R95, 'p448')
    K = os.path.join(P95, 'f0310')
    for d in ('logs', 'mintpy/geo', 'SLC/20070203', 'raw_fbs_unpacked/20070203', 'merged/SLC'):
        os.makedirs(os.path.join(K, d))
    with open(os.path.join(K, 'logs', 'STATUS.txt'), 'w') as fh:
        fh.write('2026-08-27T10:00:00Z  linog_run 01_skeleton END rc=0\n')
    with open(os.path.join(K, 'mintpy', 'geo', 'geo_velocity.h5'), 'w') as fh:
        fh.write('delivered (self-test M95: a course-kit tree)\n')
    with open(os.path.join(P95, 'LINEAGE.txt'), 'w') as fh:
        fh.write('p448 combined FBS+FBD lineage (the course kit; self-test M95)\n')
    snap0 = tree_snap(P95)
    e95 = {'LINOG_ROOT': R95, 'LINOG_ARCHIVE': a95}
    rcA, oA = S.run(T, ['448', '0310', '--to', 'stage'], cfg=t13, env_extra=e95)
    snapA = tree_snap(P95)
    D95 = os.path.join(R13, 'dry_M95')
    rcB, oB = S.run(T, ['448', '0310', '--to', 'recon', '--dry-run', D95], cfg=t13, env_extra=e95)
    fB = os.path.join(D95, 'status', 'P0a_recon.json')
    drB = json.load(open(fB)) if os.path.isfile(fB) else {}
    snapB = tree_snap(P95)
    rcC, oC = prun(['448', '--to', 'stage'], extra=e95)
    snapC = tree_snap(P95)
    keptC = all(snapC.get(k) == v for k, v in snap0.items())
    newC = sorted(set(k.split('/')[0] for k in snapC if k not in snap0))
    case('M95 (the part 1 review\'s B1) a course-kit tree at the default frame folder <root>/p448/f0310 (logs/STATUS.txt, mintpy/, '
         'SLC/, raw_fbs_unpacked/, merged/; no status/P0a_recon.json): linog_auto.sh 448 0310 stops before it writes (G0.20 FAIL, '
         'rc 2); its dry run records G0.20 FAIL in DIR (rc 2); linog_path.sh 448 with no frame skips F0310 by name and runs the '
         'other four; every file of the kit tree and the path\'s LINEAGE.txt byte for byte as before',
         rcA == 2 and 'G0.20   FAIL' in oA and "recon's G0.20 refused the frame folder" in oA and snapA == snap0
         and rcB == 2 and gv(drB, 'G0.20') == 'FAIL' and snapB == snap0
         and rcC == 5 and 'skipped frame 0310' in oC and '(skipped, G0.20: 0310)' in oC and '== frame 0310' not in oC
         and all(('== frame %s' % f_) in oC for f_ in ('0280', '0290', '0300', '0320')) and keptC
         and newC == ['_path_runs', 'f0280', 'f0290', 'f0300', 'f0320'],
         'rc %d (%s); dry rc %d G0.20 %s; runner rc %d, skipped %s; kit tree and LINEAGE.txt kept %s; new under p448: %s' % (
             rcA, [ln.strip()[:60] for ln in oA.splitlines() if 'G0.20' in ln][:1], rcB, gv(drB, 'G0.20'), rcC,
             'skipped frame 0310' in oC, keptC and snapA == snap0 and snapB == snap0, newC))
    # M95b: stage under a path folder whose LINEAGE.txt is another tool's
    a95b, o95b = frame('M95b', '448', '0320', 'A', eo=EO448, ed=ED448)
    rcD, oD = S.run(T, ['448', '0320', '--to', 'stage'], cfg=t13, env_extra={'LINOG_ROOT': R95, 'LINOG_ARCHIVE': a95b})
    fD = os.path.join(P95, 'f0320', 'status', 'P0b_stage.json')
    sD = json.load(open(fD)) if os.path.isfile(fD) else {}
    own = os.path.join(P95, 'LINEAGE_linog_auto.txt')
    lines = open(own).read().splitlines() if os.path.isfile(own) else []
    case('M95b stage of a new frame (F0320) under that path folder: LINEAGE.txt is not linog_auto\'s, so G0b.7 INFO names '
         'LINEAGE_linog_auto.txt beside it (its header and the frame\'s line); the kit\'s LINEAGE.txt byte for byte as before',
         rcD == 0 and gv(sD, 'G0b.7') == 'INFO' and gval(sD, 'G0b.7').endswith('LINEAGE_linog_auto.txt')
         and tree_snap(P95).get('LINEAGE.txt') == snap0['LINEAGE.txt'] and len(lines) == 3
         and 'frames built by linog_auto' in lines[0] and 'f0320 staged by' in lines[2],
         'rc %d; G0b.7 %s %s; LINEAGE_linog_auto.txt %d lines' % (rcD, gv(sD, 'G0b.7'), gval(sD, 'G0b.7'), len(lines)))
    # M90b (M1): the path runner with a root its caller does not own
    rcE, oE = prun(['447', '0310', '--to', 'recon'], cfg=t90, extra={'LINOG_ARCHIVE': a90})
    wrote = os.path.exists(os.path.join(foreign, 'p447'))
    case('M90b (the part 1 review\'s M1) linog_path.sh 447 0310 with the table\'s root not the caller\'s and no LINOG_ROOT: rc 2, '
         'recon\'s G0.19 FAIL printed, nothing written under the root (no p447/, no _path_runs/)',
         rcE == 2 and 'G0.19   FAIL' in oE and "recon's G0.19 refused the root" in oE and not wrote and '== frame' not in oE,
         'rc %d; p447/ made %s' % (rcE, wrote))
    # M34d (M2): a summary date that is not a date, and one absent
    a34 = arc_of('M34d')
    orbs = [EO446 + 671 * k for k in range(12)]
    for i, o in enumerate(orbs):
        S.mkzip(os.path.join(a34, '%02d' % (i % 3)), o, '0290', sfx='A', date=law_date(o, EO446, ED446))
    zp = lambda a, o, fr: glob.glob(os.path.join(a, '*', 'ALPSRP%05d%s-*.zip' % (o, fr)))[0]
    patch_summary(zp(a34, orbs[5], '0290'), 'Lbi_ObservationDate', '2007XX05')
    patch_summary(zp(a34, orbs[7], '0290'), 'Lbi_ObservationDate', None)
    rc, out, r, R, _ = recon(t13, a34, 'root_M34d', '446', '0290')
    n4 = gnote(r, 'G0.4')
    a34t, o34t = frame('M34dt', '447', '0310', 'A', eo=EO, ed=ED)
    patch_summary(zp(a34t, o34t[3], '0310'), 'Lbi_ObservationDate', '2007XX17')
    rct, outt, rt, Rt, _ = recon(t13, a34t, 'root_M34dt', '447', '0310')
    a34x, o34x = frame('M34dx', '447', '0310', 'A', eo=EO, ed=ED)    # a clean archive: the next run PASSes
    rcx, outx, rx, Rx, _ = recon(t13, a34x, 'root_M34dx', '447', '0310', extra={'LINOG_MOCK_RECON_RAISE': '1'})
    errx = g(rx, 'ERR')[0]
    rcy, outy, ry, Ry, _ = recon(t13, a34x, 'root_M34dx', '447', '0310')
    case('M34d (the part 1 review\'s M2) a derived P446 F0290 with one summary date "2007XX05" and one granule without '
         'Lbi_ObservationDate: G0.4 DECISION naming both (rc 4), the record finished DECISION, G0.5 PASS on the other 10; a table '
         'P447 F0310 with "2007XX17": G0.4 DECISION (rc 4); an error after the record is written (a test hook): the record '
         'ERROR with gate ERR, rc 3, and the next run goes on (not stopped at RUNNING)',
         rc == 4 and r.get('verdict') == 'DECISION' and gv(r, 'G0.4') == 'DECISION' and '2 of 12 unreadable' in gval(r, 'G0.4')
         and ('ALPSRP%05d0290' % orbs[5]) in n4 and 'is not a date (YYYYMMDD)' in n4
         and ('ALPSRP%05d0290' % orbs[7]) in n4 and 'gives no Lbi_ObservationDate' in n4
         and gv(r, 'G0.5') == 'PASS' and 'of 10 granules' in gval(r, 'G0.5')
         and rct == 4 and rt.get('verdict') == 'DECISION' and gv(rt, 'G0.4') == 'DECISION' and scene(o34t[3]) in gnote(rt, 'G0.4')
         and rcx == 3 and rx.get('verdict') == 'ERROR' and errx.get('verdict') == 'ERROR' and 'LINOG_MOCK_RECON_RAISE' in errx.get('value', '')
         and rcy == 0 and ry.get('verdict') == 'PASS',
         'rc %d %s; G0.4 %s; G0.5 %s; table rc %d %s; hook rc %d %s (%s); next rc %d %s' % (
             rc, r.get('verdict'), gval(r, 'G0.4'), gval(r, 'G0.5')[:50], rct, rt.get('verdict'), rcx, rx.get('verdict'),
             errx.get('value', '')[:50], rcy, ry.get('verdict')))
    # M42b (m2): one granule beyond the frame law's band on a derived path
    c0 = S.mock_centre('446', '0290', 'A')
    a, orbs = frame('M42b', '446', '0290', 'A', eo=EO446, ed=ED446, plants={4: dict(g016=dict(centre=(c0[0] + 1.0, c0[1])))})
    rc, out, r, R, _ = recon(t13, a, 'root_M42b', '446', '0290')
    case('M42b (the part 1 review\'s m2) a derived path, one granule 1.0 deg north of the frame law\'s latitude: G0.16 DECISION at '
         'step 2 naming it ("beyond +-0.82 deg of the frame law\'s latitude"), nothing dropped (rc 4)',
         rc == 4 and gv(r, 'G0.16') == 'DECISION' and gval(r, 'G0.16').startswith('step 2')
         and "beyond +-0.82 deg of the frame law's latitude" in gnote(r, 'G0.16') and ('ALPSRP%05d0290' % orbs[4]) in gnote(r, 'G0.16')
         and not drops(R), 'rc %d; G0.16 %s %s; %s' % (rc, gv(r, 'G0.16'), gval(r, 'G0.16')[:50], gnote(r, 'G0.16')[:90]))
    # M41b (m2): a table footprint 3 km north of where the frame law puts the frame
    import configparser as _cp
    lat_law = 0.92026 + 0.0496858 * 290
    res446 = C.residue_of(446)
    bb = '%.6f %.6f %.6f %.6f' % (lat_law - 0.32 + 0.0272, lat_law + 0.32 + 0.0272, c0[1] - 0.38, c0[1] + 0.38)
    t41b = table('paths13_m41b.cfg', [p084, section('p447'), section('p448'),
                                      '[p446]\ndirection = A\nresidue = %d\nepoch_date = %s\nepoch_orbit = %d\nbbox_0290 = %s\n'
                                      % (res446, ED446, EO446, bb)])
    a41b, o41b = frame('M41b', '446', '0290', 'A', eo=EO446, ed=ED446)
    rc, out, r, R, _ = recon(t41b, a41b, 'root_M41b', '446', '0290')
    case('M41b (the part 1 review\'s m2) a table footprint 0.0272 deg (3 km) north of the frame law\'s place: G0.16a WARN, the '
         'anchors differing by about 2.95 km (beyond framing_law_check_km)',
         gv(r, 'G0.16a') == 'WARN' and 'differ +2.9' in gval(r, 'G0.16a') and rc in (0, 4),
         'rc %d; G0.16a %s %s; G0.16 %s %s' % (rc, gv(r, 'G0.16a'), gval(r, 'G0.16a'), gv(r, 'G0.16'), gval(r, 'G0.16')[:50]))
    # M96 (m3): dem_<frame>, LINOG_DEM, and recon's fingerprint
    dem2 = S.mock_dem(T, 'mock13_m96.dem.wgs84', 18.0, 500)
    txt13 = open(os.path.join(T, 'cfg', t13)).read()
    assert txt13.count('\n[p084]\n') == 1
    t96 = 'paths13_m96.cfg'
    with open(os.path.join(T, 'cfg', t96), 'w') as fh:
        fh.write(txt13.replace('\n[p084]\n', '\n[p084]\ndem_3330 = %s\n' % dem2))
    t96c = 'paths13_m96c.cfg'
    with open(os.path.join(T, 'cfg', t96c), 'w') as fh:
        fh.write(txt13.replace('\n[p084]\n', '\n[p084]\ndem_3320 = %s\n' % dem2))

    def load(cfgname, fr, env=None):
        e = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        e.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfgname))
        e.update(env or {})
        p = subprocess.run(['python3', '-E', '-B', '-c', 'import sys, json; sys.path.insert(0, sys.argv[1]); import lp_common as C; '
                            'c = C.load_cfg("084", sys.argv[2]); print(json.dumps([c["dem"], c.get("dem_key")]))', S.HERE, fr],
                           env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            return json.loads(p.stdout.decode().strip().splitlines()[-1])
        except (ValueError, IndexError):
            return [p.stdout.decode()[-200:], None]
    l30, l20, lenv = load(t96, '3330'), load(t96, '3320'), load(t96, '3330', {'LINOG_DEM': '/x/other.dem.wgs84'})
    base_dem = load(t13, '3330')[0]
    case('M96 (the part 1 review\'s m3; 14.4) dem_3330 in [p084]: F3330 reads it (dem_key dem_3330), F3320 the table\'s dem (no '
         'dem_key); with LINOG_DEM set, LINOG_DEM wins over dem_3330 (dem_key LINOG_DEM)',
         l30 == [dem2, 'dem_3330'] and l20 == [base_dem, None] and lenv == ['/x/other.dem.wgs84', 'LINOG_DEM'],
         'F3330 %s; F3320 %s; LINOG_DEM %s' % (l30, l20, lenv))
    a96, o96 = frame('M96', '084', '3320', 'D', eo=10488, ed='20080113')
    rc96, _, r96, _, _ = recon(t13, a96, 'root_M96', '084', '3320')
    e = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
    e.update(LINOG_ROOT=os.path.join(R13, 'root_M96'), LINOG_ARCHIVE=a96)
    states = []
    for cfgname in (t13, t96, t96c):
        e['LINOG_AUTO_CFG'] = os.path.join(T, 'cfg', cfgname)
        states.append(subprocess.run(['python3', '-E', '-B', os.path.join(S.HERE, 'lp_recon.py'), '--path', '084', '--frame', '3320',
                                      '--state'], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip())
    case('M96b (m3; a departure from 14.4\'s text, recorded: recon\'s fingerprint leaves out another frame\'s bbox_, expect_ and '
         'dem_ keys) F3320 recon PASS under the table; under the table with dem_3330 added CURRENT; with dem_3320 added STALE',
         rc96 == 0 and r96.get('verdict') == 'PASS' and states == ['CURRENT', 'CURRENT', 'STALE'],
         'rc %d; states %s' % (rc96, states))
    # M97 (m4): a granule placed by an independent geodesic (Vincenty), not the ENU code under test
    o0 = S.mock_centre('447', '0310', 'A')
    pv = vincenty_direct(o0[0], o0[1], (S.HEADING['A'] + 180.0) % 360.0, 30400.0)
    a97, o97 = frame('M97', '447', '0310', 'A', eo=EO, ed=ED, plants={4: dict(g016=dict(centre=pv))})
    rc, out, r, R, _ = recon(t13, a97, 'root_M97', '447', '0310')
    d97 = dev(R, scene(o97[4]))
    case('M97 (the part 1 review\'s m4) one granule\'s (c) 30.4 km back along the heading by Vincenty\'s geodesic on WGS84 (not the '
         'mock\'s ENU): DROPPED at G0.16, its dev_c within 0.01 km of -30.4 (9.5\'s tolerance)',
         rc == 0 and drops(R) == [scene(o97[4])] and d97 is not None and abs(d97 + 30.4) <= 0.01,
         'rc %d; dropped %s; dev_c %s km; (c) %.6f %.6f from %.6f %.6f' % (rc, drops(R), d97, pv[0], pv[1], o0[0], o0[1]))
