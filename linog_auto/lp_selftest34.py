#!/usr/bin/env python3
"""lp_selftest34.py -- the Phase 3 and 4 cases of the linog_auto self-test (v0.4; v0.5: rwin before verify, 17 phases,
T93 reads a running record; v0.6: a copy of the frame after igram, S4f, for the Phase 4.5 and 5 cases, and T65 and T82
run to igram, as v0.6's default runs on to sbas), called by lp_selftest.py.

The frame: four of felix's P084 F3320 dates (20080830, 20081130, 20090302, 20090602; 6 pairs under -t 730 -b 1500),
1000 samples x 18432 lines, so the kit's G7 and G10, which read windows of a full-height ALOS frame, run unchanged. The
real stripmapWrapper.py, invertMisreg.py and referenceStackCopy.py of the isce2 package and the kit's nine Phase 3
and 4 scripts run as felix pins them; the modules stripmapWrapper.py imports (topo, geo2rdr, resampleSlc,
refineSecondaryTiming, baselineGrid, crossmul, FilterAndCoherence, unwrap) and gdal_translate are mocks that write the
files the rehearsal measured, sparse except the rows the gates read (selftest_kit/mock_stack3, mock_isce/linog_mock3).
Phases 0 to 2 run first on that frame (--decide auto: D1 picks 20090302). The clean run goes phase by phase, and a
copy of the frame is kept after stack2, topo, coarse, datum, bgrid and igram (big files hard-linked: the pipeline never
rewrites them); a planted case puts the frame back to one of those copies at the same path (the configuration holds
absolute paths, B51) after moving the frame it replaces into _archive/.
v0.9: refine's and igram's jobs get the pinned FFTW wisdom (the mock env's, made by lp_selftest.build_fftw); T93 and T64
take the new gates G4a.4w, G4a.7w, G4f.4w and G4f.8w, and T154 to T166 and T168 to T171 test lp_fftw.py, the jobs'
environment, the dry run, seven planted pins, three planted job logs, the file changed during a step, a WISDOM_FILE in the
operator's shell and the STALE map.
"""
import glob
import json
import os
import shutil
import signal
import socket
import subprocess
import time

ROOT, FRAME = 'p3', '3320'
REF = '20090302'
DATES = ['20080830', '20081130', '20090302', '20090602']
P34 = (('3a', 'topo'), ('3b', 'coarse'), ('4a', 'refine'), ('4b', 'invert'), ('4c', 'datum'), ('4d', 'fine'), ('4e', 'bgrid'),
       ('4f', 'igram'))


def link_or_copy(src, dst):
    if os.path.getsize(src) > (1 << 20):
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)


def md5q(p):
    """md5 of a file, None when it is absent (a failed earlier case must not stop the group)."""
    import hashlib
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None


def phase34(T, case, S):
    W = S.fdir(T, FRAME, ROOT)
    E = {'LINOG_ROOT': os.path.join(T, ROOT)}
    rpins = S.real_pins('linog_run.cfg')

    def run(args, extra=None):
        return S.run(T, ['084', FRAME, '--decide', 'auto'] + args, cfg='paths_p3.cfg', env_extra=dict(E, **(extra or {})))

    def rec(idx, ph):
        return S.rec(T, FRAME, idx, ph, ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def snap(name):
        dst = os.path.join(T, 'snap_p3', name)
        shutil.copytree(W, dst, symlinks=True, copy_function=link_or_copy)
        return dst

    def restore(name, tag):
        S.aside(T, W, 'p3_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', name), W, symlinks=True, copy_function=link_or_copy)

    def in_env_w(args, extra=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        env.update(LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), **(extra or {}))
        p = subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh')] + args, cwd=W, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        return p.returncode, p.stdout.decode('utf-8', 'replace')

    print('-- Phases 3 and 4 (the eight run files): the real wrapper, invertMisreg and referenceStackCopy, the kit\'s gates, mock '
          'ISCE steps; a 4-date frame 1000 x 18432')
    kitpins = (('mock_stack/stripmapWrapper.py', 'WRAPPER_MD5'), ('mock_stack/invertMisreg.py', 'INVERT_MD5'),
               ('mock_stack/referenceStackCopy.py', 'REFCOPY_MD5'), ('kit3/linog_frame_align_gate.py', 'KIT_G21_MD5'),
               ('kit3/linog_coarse_reg_gate.py', 'KIT_G7_MD5'), ('kit3/linog_reg_common.py', 'KIT_REGCOMMON_MD5'),
               ('kit3/linog_pair_misreg_census.py', 'KIT_G8_MD5'), ('kit3/linog_redatum_misreg_v2.py', 'KIT_G16_MD5'),
               ('kit3/linog_misreg_gate.py', 'KIT_G9_MD5'), ('kit3/linog_fine_reg_gate.py', 'KIT_G10_MD5'),
               ('kit3/linog_coherence_census.py', 'KIT_G11_MD5'), ('kit3/linog_date_coherence.py', 'KIT_DATECOH_MD5'))
    same = [n for n, k in kitpins if S.md5(os.path.join(S.KITSRC, n)) == rpins.get(k)]
    case('T63 the self-test runs the three ISCE scripts and the nine kit gates felix pins (md5s = linog_run.cfg)',
         len(same) == len(kitpins), '%d of %d' % (len(same), len(kitpins)))

    # v0.9: lp_fftw.py on the mock env's real libfftw3f, and its reading of job logs (the lines as felix's jobs print them)
    import lp_fftw as F

    def fcfg(name):
        d = {}
        for ln in open(os.path.join(T, 'cfg', name)):
            if '=' in ln and not ln.startswith('#'):
                k, v = ln.strip().split('=', 1)
                d[k] = v
        return d
    fm = fcfg('fftw_mock.cfg') if os.path.isfile(os.path.join(T, 'cfg', 'fftw_mock.cfg')) else {}
    if not fm:
        case('T154-T166 not run: no libfftw3f on this host (the pinned env\'s or the system\'s), so no wisdom for the mock env', False)
    else:
        small = dict((k, int(fm[k])) for k in ('SIZE_MIN', 'SIZE_MAX', 'OFFSET_MIN', 'OFFSET_MAX', 'OFFSET_STEP', 'PROBLEMS'))
        envlib = os.path.join(T, 'mockconda', 'envs', 'linog_isce2', fm['FFTW_LIB_REL'])
        cw, co = F.check(envlib, fm['WISDOM'], small), F.check(envlib, None, small)
        cb = F.check(envlib, os.path.join(T, 'fftw', 'wisdom_bad.wis'), small)
        cg = F.check(envlib, os.path.join(T, 'fftw', 'garbage.wis'), small)
        lw = os.path.join(T, 'fftw', 'logs')
        os.makedirs(lw, exist_ok=True)
        wf = fm['WISDOM']
        logs = {'good': ' XXX start timer\n wisdomFile, length = %s%12d\n           1\n WARNING - number of samples\n' % (wf, len(wf)),
                'none': ' XXX start timer\n wisdomFile, length =            0\n Overall:       18432       28672           1\n',
                'stop': ' wisdomFile, length = %s%12d\n           0\nSTOP cannot import fftw wisdom file\n' % (wf, len(wf)),
                'other': ' wisdomFile, length = /x/other.wis%12d\n           1\n' % len('/x/other.wis'),
                'two': (' wisdomFile, length = %s%12d\n           1\n Overall: 1\n' % (wf, len(wf))) * 2}
        got = {}
        for k, v in logs.items():
            open(os.path.join(lw, k + '.log'), 'w').write(v)
            got[k] = F.judge_log(os.path.join(lw, k + '.log'), wf, 2 if k == 'two' else 1)
        okl = got['good'] == '' and got['two'] == '' and 'none (length = 0)' in got['none'] and got['stop'].startswith('STOP') \
            and 'import returned 0' in got['stop'] and '/x/other.wis' in got['other'] and F.judge_log(os.path.join(lw, 'two.log'), wf, 1) != ''
        case('T154 lp_fftw.py on the mock env\'s libfftw3f (%s): the wisdom made here covers %s of %s problems, none without it; one hex '
             'digit changed: import %s; a garbage file: import %s; job logs as felix\'s print them: a good one passes, length 0, a STOP, '
             'another file and a count off are named' % (cw.get('version'), small['PROBLEMS'], small['PROBLEMS'], cb.get('imported'),
                                                          cg.get('imported')),
             cw.get('imported') == 1 and cw.get('covered') == small['PROBLEMS'] and co.get('covered') == 0 and cb.get('imported') == 0
             and cg.get('imported') == 0 and cw.get('version') == fm['FFTW_VERSION'] and okl,
             'with %s; without %s; bad %s; garbage %s; logs %s' % (cw, co.get('covered'), cb.get('covered'), cg.get('covered'), got))

    # the clean frame, phase by phase, with a copy after stack2, topo, coarse, datum and bgrid
    steps, rcs = (('stack2', 'S2'), ('topo', 'S3a'), ('coarse', 'S3b'), ('datum', 'S4c'), ('bgrid', 'S4e'), ('igram', 'S4f')), []
    outs = []
    for to, sn in steps:
        rc, out = run(['--to', to])
        rcs.append(rc)
        outs.append(out)
        if rc != 0:
            break
        if sn:
            snap(sn)
    r0 = [S.rec(T, FRAME, i, ph, ROOT).get('verdict') for i, ph in (('0a', 'recon'), ('0b', 'stage'), ('1a', 'extract'),
          ('1b', 'unpack'), ('1br', 'rwin'), ('1c', 'verify'), ('2a', 'stack1'), ('2b', 'reference'), ('2c', 'stack2'))]
    rj = os.path.join(W, 'recon', 'reference.json')
    ref = json.load(open(rj)).get('reference') if os.path.exists(rj) else None
    case('T64a the Phase 3 frame through Phases 0 to 2 (auto): 9 records PASS, 6 pairs, D1 picks %s' % REF,
         rcs[:1] == [0] and r0 == ['PASS'] * 9 and ref == REF and rec('2c', 'stack2').get('outputs', {}).get('pairs') == 6,
         'rc %s; %s; reference %s' % (rcs[:1], r0, ref))
    R = {ph: rec(i, ph) for i, ph in P34}
    g = {}
    for ph, r in R.items():
        g.update(gates(r))
    want = dict(G21='PASS', G7='PASS', F15='PASS', G8='PASS', G16='PASS', G9='PASS', G10='PASS', G17='PASS', G11='PASS', G11d='PASS')
    want.update({'G4a.4w': 'PASS', 'G4a.7w': 'PASS', 'G4f.4w': 'PASS', 'G4f.8w': 'PASS'})   # v0.9
    wrong = {k: g.get(k) for k, v in want.items() if g.get(k) != v}
    ok = rcs == [0] * 6 and all(R[ph].get('verdict') == 'PASS' for ph in R) and not wrong
    case('T64 clean, phase by phase to igram: rc 0 x 6, the 8 records PASS; G21 G7 F15 G8 G16 G9 G10 G17 G11 G11d PASS; v0.9: '
         'G4a.4w G4a.7w G4f.4w G4f.8w PASS', ok,
         'rc %s; %s; gates off: %s' % (rcs, [(ph, R[ph].get('verdict')) for ph in R], wrong))
    od, oi, of = R['datum'].get('outputs', {}), R['igram'].get('outputs', {}), R['fine'].get('outputs', {})
    after = od.get('after', {})
    tools = {}
    for ph in ('topo', 'invert', 'fine'):
        tools.update(R[ph].get('inputs', {}).get('tools', {}))
    real = [n for n, k in (('stripmapWrapper.py', 'WRAPPER_MD5'), ('invertMisreg.py', 'INVERT_MD5'), ('referenceStackCopy.py', 'REFCOPY_MD5'))
            if (tools.get(n) or {}).get('md5') == rpins.get(k)]
    case('T64b the datum: %s at 0 and 0, every date = the plan; 4 merged SLCs, 6 pairs of 6 products; the real three scripts ran'
         % REF, after.get(REF) == [0.0, 0.0] and sorted(after) == DATES and of.get('dates') == DATES and oi.get('pairs') == 6
         and len(real) == 3 and os.path.isdir(os.path.join(W, od.get('backup') or '/nonexistent')),
         'after[REF] %s; dates %s; pairs %s; real %s; backup %s' % (after.get(REF), sorted(after), oi.get('pairs'), real, od.get('backup')))
    # v0.13 (the ascending record 17.9's M71): the FBS-only frame under v0.13's datum, coarse and fine
    import lp_common as C13
    rdat = R['datum']
    in71, r971 = rdat.get('inputs', {}), od.get('r9') or {}
    fp12 = C13.md5_obj(dict(logic=1, reference=REF, invert=R['invert'].get('outputs', {}).get('md5s'), modes=in71.get('modes'),
                            tools=dict((k, ((in71.get('tools') or {}).get(k) or {}).get('md5'))
                                       for k in ('linog_redatum_misreg_v2.py', 'linog_misreg_gate.py'))))
    md71 = r971.get('max_diff') or [None, None]
    case('M71 (17.9) the FBS-only frame under v0.13: datum as v0.12 (method G16, G4c.6 PASS), its fingerprint v0.12\'s expression '
         '(logic, reference, invert, modes, the kit\'s two tools: a v0.12 record reads CURRENT); G4c.10 INFO, R9 beside it equal '
         'within 1e-6 in range and azimuth (one SLR and one PRF on the mock); G3b.12 INFO; G10v3 INFO, G10m N/A',
         od.get('method') == 'G16' and gates(rdat).get('G4c.6') == 'PASS' and rdat.get('fingerprint') == fp12
         and gates(rdat).get('G4c.10') == 'INFO' and None not in md71 and max(md71) <= 1e-6
         and gates(R['coarse']).get('G3b.12') == 'INFO' and gates(R['fine']).get('G10v3') == 'INFO'
         and gates(R['fine']).get('G10m') == 'N/A',
         'method %s; fingerprint %s (v0.12\'s %s); max_diff %s; G3b.12 %s; G10v3 %s' % (
             od.get('method'), rdat.get('fingerprint'), fp12, md71, gates(R['coarse']).get('G3b.12'), gates(R['fine']).get('G10v3')))
    led = open(os.path.join(W, 'logs', 'STATUS.txt')).read()
    jl = os.path.join(R['igram'].get('outputs', {}).get('logdir') or '/nonexistent', 'run_08_igram', 'joblog.tsv')
    case('T64c ledger: auto_<phase> END rc=0 for the 8 phases; run_08\'s joblog has 6 lines rc 0; every line log kept',
         all('auto_%s END rc=0' % ph in led for _, ph in P34) and os.path.isfile(jl) and
         [x.split('\t')[2] for x in open(jl).read().splitlines()[1:]] == ['0'] * 6, jl)

    if fm:
        rr, ri = R['refine'], R['igram']
        fi_r, fi_i = (rr.get('inputs') or {}).get('fftw') or {}, (ri.get('inputs') or {}).get('fftw') or {}
        fo_r, fo_i = (rr.get('outputs') or {}).get('fftw') or {}, (ri.get('outputs') or {}).get('fftw') or {}
        import glob as G_
        jl4 = sorted(G_.glob(os.path.join(rr.get('outputs', {}).get('logdir') or '/nonexistent', 'run_04_refineSecondaryTiming', '0*.log')))
        jl8 = sorted(G_.glob(os.path.join(ri.get('outputs', {}).get('logdir') or '/nonexistent', 'run_08_igram', '0*.log')))
        seen = ['MOCK refineSecondaryTiming: WISDOM_FILE %s' % fm['WISDOM'] in open(f).read() for f in jl4] + \
            ['MOCK crossmul: WISDOM_FILE %s' % fm['WISDOM'] in open(f).read() for f in jl8]
        others = sorted(G_.glob(os.path.join(W, 'logs', 'p3', '*', 'run_0[1367]_*', '0*.log')))
        unset = [f for f in others if 'MOCK ' in open(f).read()]
        leak = [os.path.relpath(f, W) for f in unset if 'WISDOM_FILE unset' not in open(f).read()]
        case('T155 the clean run\'s wisdom (v0.9): refine and igram checked it (%s of %s problems with the file, 0 without) and gave it to '
             'every job: 6 of 6 refine logs with 1 import, 6 of 6 igram logs with 2 (crossmul, icu), each naming the mock file; topo\'s, '
             'coarse\'s, fine\'s and bgrid\'s jobs ran without WISDOM_FILE' % (fm['PROBLEMS'], fm['PROBLEMS']),
             (fi_r.get('with_file') or {}).get('covered') == int(fm['PROBLEMS']) and (fi_r.get('without_file') or {}).get('covered') == 0
             and (fi_i.get('with_file') or {}).get('covered') == int(fm['PROBLEMS']) and fo_r.get('jobs') == 6 and fo_r.get('good') == 6
             and fo_i.get('jobs') == 6 and fo_i.get('good') == 6 and fo_i.get('per_job') == 2 and len(jl4) == 6 and len(jl8) == 6 and all(seen)
             and sorted(fi_r.get('modules') or {}) == ['ampcor'] and sorted(fi_i.get('modules') or {}) == ['crossmul', 'icu']
             and len(unset) >= 4 and not leak,
             'refine %s / %s; igram %s / %s; logs %d, %d, WISDOM_FILE seen %s; other steps\' logs %d, with it %s' % (
                 fi_r.get('with_file'), dict((k, fo_r.get(k)) for k in ('jobs', 'good')), fi_i.get('with_file'),
                 dict((k, fo_i.get(k)) for k in ('jobs', 'good', 'per_job')), len(jl4), len(jl8), sum(seen), len(unset), leak))

    m0 = {ph: md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph))) for i, ph in P34}
    rc, out = run(['--to', 'igram'])
    case('T65 re-run to igram: all 18 phases skipped (v0.13: bandlimit among them), the 8 Phase 3 and 4 records unchanged (v0.6: the '
         'default runs on to sbas, T101)',
         rc == 0 and out.count('skip: PASS on record') == 18 and
         all(m0[ph] and md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph))) == m0[ph] for i, ph in P34),
         'rc %d; %d skipped' % (rc, out.count('skip: PASS on record')))

    D = os.path.join(T, 'dry_p3')
    lst0 = sorted(os.path.relpath(os.path.join(dp, n), W) for dp, dn, fn in os.walk(W) for n in fn)
    rc, out = S.run(T, ['084', FRAME, '--decide', 'auto', '--dry-run', D, '--to', 'igram'], cfg='paths_p3.cfg', env_extra=E)
    dr = [json.load(open(os.path.join(D, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D, 'status', 'P%s_%s.json' % (i, ph))) else {} for i, ph in P34]
    lst1 = sorted(os.path.relpath(os.path.join(dp, n), W) for dp, dn, fn in os.walk(W) for n in fn)
    case('T66 dry run through igram: rc 0, the 8 Phase 3 and 4 records PASS as plans in the dry folder, the frame unchanged',
         rc == 0 and all(x.get('verdict') == 'PASS' and x.get('outputs', {}).get('planned') for x in dr) and lst0 == lst1,
         'rc %d; %s; frame files %d -> %d' % (rc, [x.get('verdict') for x in dr], len(lst0), len(lst1)))
    if fm:
        gd = dict((ph, gates(x)) for (i, ph), x in zip(P34, dr))
        case('T156 the dry run (v0.9): refine\'s and igram\'s plans check the wisdom first (G4a.4w, G4f.4w PASS), nothing written',
             rc == 0 and gd.get('refine', {}).get('G4a.4w') == 'PASS' and gd.get('igram', {}).get('G4f.4w') == 'PASS' and lst0 == lst1,
             'refine %s; igram %s' % (gd.get('refine', {}).get('G4a.4w'), gd.get('igram', {}).get('G4f.4w')))

    # N53: a date's coarse SLC shifted 32 samples in range
    restore('S3a', 'T67')
    rc, out = run(['--to', 'coarse'], {'LINOG_MOCK_N53': '20081130'})
    rc_ = rec('3b', 'coarse')
    g7 = rc_.get('outputs', {}).get('g7', {})
    bad = sorted(d for d, v in (g7.get('dates') or {}).items() if v[1] == 'FAIL')
    def r7fail(r):   # v0.13: R7's limits that failed (the ascending record 11.3)
        return sorted(x['id'] for x in ((r.get('outputs') or {}).get('r7') or {}).get('limits') or [] if not x['ok'])

    def gtext(r, gid):
        x = [g for g in r.get('gates', []) if g['id'] == gid]
        return (x[-1]['value'] + ' | ' + x[-1].get('note', '')) if x else ''
    case('T67 N53 planted on 20081130: coarse DECISION (G7, D2) naming exactly that date, rc 4; G21 PASS; v0.13: R7 under auto cannot '
         'take it, L3 alone failing (3 dates left, min_dates 4)',
         rc == 4 and rc_.get('verdict') == 'DECISION' and gates(rc_).get('G7') == 'DECISION' and gates(rc_).get('D2') == 'DECISION'
         and bad == ['20081130'] and gates(rc_).get('G21') == 'PASS' and r7fail(rc_) == ['L3'],
         'rc %d; G7 %s; flagged %s; R7 failing %s' % (rc, gates(rc_).get('G7'), bad, r7fail(rc_)))
    rc, out = run(['--to', 'coarse'])
    r68 = rec('3b', 'coarse')
    g68 = gates(r68)
    bad68 = sorted(d for d, v in ((r68.get('outputs', {}).get('g7') or {}).get('dates') or {}).items() if v[1] == 'FAIL')
    case('T68 the same frame again, unplanted (v0.13, the ascending record 11.5, a case that changes: v0.12 stopped at G3b.6, its '
         'products in the way): coarse reuses its products (G3b.6 PASS, G3b.8 and G3b.9 "not run"), G7 reads them again and still '
         'names 20081130, R7\'s L3 fails: D2 DECISION, rc 4',
         rc == 4 and g68.get('G3b.6') == 'PASS' and 'not run' in gtext(r68, 'G3b.9') and 'not run' in gtext(r68, 'G3b.8')
         and g68.get('G7') == 'DECISION' and bad68 == ['20081130'] and g68.get('D2') == 'DECISION' and r7fail(r68) == ['L3'],
         'rc %d; G3b.6 %s; G7 %s %s; R7 failing %s' % (rc, g68.get('G3b.6'), g68.get('G7'), bad68, r7fail(r68)))

    restore('S3a', 'T69')
    rc, out = run(['--to', 'coarse'], {'LINOG_MOCK_OFFFRAME': '20090602'})
    rc_ = rec('3b', 'coarse')
    fl = sorted((rc_.get('outputs', {}).get('g21') or {}).get('flagged') or {})
    case('T69 an off-frame granule (20090602, 100x): coarse DECISION at G21 naming it; G7 still read, PASS; v0.13: R7\'s L3 fails',
         rc == 4 and gates(rc_).get('G21') == 'DECISION' and fl == ['20090602'] and gates(rc_).get('G7') == 'PASS'
         and r7fail(rc_) == ['L3'],
         'rc %d; G21 %s %s; G7 %s; R7 failing %s' % (rc, gates(rc_).get('G21'), fl, gates(rc_).get('G7'), r7fail(rc_)))

    restore('S2', 'T70')
    rc, out = run(['--to', 'coarse'], {'LINOG_MOCK_THIN': '1'})
    rc_ = rec('3b', 'coarse')
    tries = (rc_.get('outputs', {}).get('g7') or {}).get('tries') or []
    case('T70 two textured windows only: topo PASS; coarse DECISION at G7 after the survey again at depth 60 (2 tries)',
         rc == 4 and rec('3a', 'topo').get('verdict') == 'PASS' and gates(rc_).get('G7') == 'DECISION' and len(tries) == 2
         and tries[1].get('ncand') == '60', 'rc %d; tries %s' % (rc, [(x.get('ncand'), x.get('verdict')) for x in tries]))

    restore('S3b', 'T71')
    rc, out = run(['--to', 'refine'], {'LINOG_MOCK_JOBFAIL': '20081130_20090602'})
    rr = rec('4a', 'refine')
    failed = [x[1] for x in (rr.get('outputs', {}).get('steps', {}).get('run_04_refineSecondaryTiming') or {}).get('failed', [])]
    case('T71 one refineSecondaryTiming line fails: refine FAIL at G4a.7 naming that pair, rc 2',
         rc == 2 and gates(rr).get('G4a.7') == 'FAIL' and failed == ['20081130_20090602'], 'rc %d; failed %s' % (rc, failed))

    restore('S3b', 'T72')
    rc, out = run(['--to', 'invert'])
    k = os.path.join(T, 'kit', 'linog_redatum_misreg_v2.py')
    krc, kout = in_env_w(['python3', '-B', k, REF, '--fbs-dates', ','.join(DATES), '--apply'])
    rc2, out2 = run(['--to', 'datum'])
    rd = rec('4c', 'datum')
    case('T72 dates/ rebased by hand without a datum record: datum DECISION (G4c.4), nothing applied twice',
         rc == 0 and krc == 0 and rc2 == 4 and gates(rd).get('G4c.4') == 'DECISION' and 'G16' not in gates(rd),
         'invert rc %d; kit rc %d; datum rc %d %s' % (rc, krc, rc2, gates(rd).get('G4c.4')))

    restore('S4c', 'T73')
    rc, out = run(['--to', 'fine'], {'LINOG_MOCK_GDALFAIL': '1'})
    rf = rec('4d', 'fine')
    case('T73 the reference copy fails inside referenceStackCopy.py (rc 0 on every line): fine FAIL at G4d.9 (A16)',
         rc == 2 and gates(rf).get('G4d.8') == 'PASS' and gates(rf).get('G4d.9') == 'FAIL', 'rc %d; %s' % (rc, gates(rf)))

    restore('S4e', 'T74')
    rc, out = run(['--to', 'igram'], {'LINOG_MOCK_NOUNW': '20080830_20081130'})
    ri = rec('4f', 'igram')
    case('T74 one pair unwrapped to nothing with rc 0: igram FAIL at G4f.9, every line rc 0 (G4f.8 PASS)',
         rc == 2 and gates(ri).get('G4f.8') == 'PASS' and gates(ri).get('G4f.9') == 'FAIL', 'rc %d; %s' % (rc, gates(ri)))

    restore('S4e', 'T75')
    rc, out = run(['--to', 'igram'], {'LINOG_MOCK_DEADDATE': '20080830'})
    ri = rec('4f', 'igram')
    dead = (ri.get('outputs', {}).get('date_coh') or {}).get('dead')
    case('T75 every pair of 20080830 at 0.2: igram PASS with G11d WARN naming it, rc 0',
         rc == 0 and ri.get('verdict') == 'PASS' and gates(ri).get('G11d') == 'WARN' and dead == ['20080830'], 'rc %d; dead %s' % (rc, dead))
    restore('S4e', 'T75b')
    rc, out = run(['--to', 'igram'], {'LINOG_MOCK_DEADDATE': REF})
    ri = rec('4f', 'igram')
    g11d = [g for g in ri.get('gates', []) if g['id'] == 'G11d']
    case('T75b every pair of the reference at 0.2: igram FAIL at G11d (the datum bug\'s signature; v0.13, 21.4: its note names N25 '
         'beside it), rc 2',
         rc == 2 and gates(ri).get('G11d') == 'FAIL' and bool(g11d) and 'N25' in (g11d[-1].get('note') or ''),
         'rc %d; %s' % (rc, gates(ri).get('G11d')))

    # a stop while run_04 runs: every line's process group ends, the record ends ERROR, the next run finds the pairs in the way
    restore('S3b', 'T76')
    mark = os.path.join(T, 'p3_sleep.mark')
    env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM') and not k.startswith('LINOG_MOCK_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p3.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
               LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
               LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
               LINOG_MOCK_P3SLEEP='20081130_20090302',
               LINOG_MOCK_MARK=mark, **E)
    p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', 'auto', '--to', 'refine'], env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 180:
        time.sleep(0.2)
    time.sleep(0.5)
    live = rec('4a', 'refine')   # F25: read while run_04's lines run
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
    out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 3320 --to refine (p3, LINOG_MOCK_P3SLEEP, SIGTERM after %.1f s) rc %d\n%s' % (
            time.time() - t0, p.returncode, out))
    lg = [x.get('id') for x in live.get('gates', [])]
    case('T93 the refine record read while run_04\'s lines run (F25): RUNNING, with the gates taken so far, G4a.1 to G4a.6 (v0.9: '
         'and G4a.4w after G4a.4)', live.get('verdict') == 'RUNNING' and lg == ['G4a.1', 'G4a.2', 'G4a.3', 'G4a.4', 'G4a.4w', 'G4a.5', 'G4a.6'],
         '%s, gates %s' % (live.get('verdict'), lg))
    rr = rec('4a', 'refine')
    sleeper = open(mark).read() if os.path.exists(mark) else ''
    time.sleep(1)
    alive = subprocess.run(['pgrep', '-f', 'refineSecondaryTiming_20081130_20090302'], stdout=subprocess.PIPE).stdout.decode().split()
    lastled = open(os.path.join(W, 'logs', 'STATUS.txt')).read().splitlines()[-1]
    rc2, out2 = run(['--to', 'refine'])
    case('T76 SIGTERM while run_04 runs: rc 143, refine ERROR, no line left running; next run: refine DECISION (G4a.6)',
         p.returncode == 143 and rr.get('verdict') == 'ERROR' and 'sleeping' in sleeper and not alive and 'rc=143' in lastled
         and rc2 == 4 and gates(rec('4a', 'refine')).get('G4a.6') == 'DECISION',
         'rc %s; refine %s; alive %s; ledger %s; next rc %d' % (p.returncode, rr.get('verdict'), alive, lastled[-40:], rc2))

    # the phase itself killed (SIGKILL: the OOM killer) while run_04 runs: every line gets SIGTERM from the kernel
    # (PR_SET_PDEATHSIG), none goes on writing into the frame; the record stays RUNNING, the next run asks for --recover
    restore('S3b', 'T80')
    mark = os.path.join(T, 'p3_sleep80.mark')
    env.update(LINOG_MOCK_MARK=mark)
    p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', 'auto', '--to', 'refine'], env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 180:
        time.sleep(0.2)
    time.sleep(0.5)
    ph = subprocess.run(['pgrep', '-f', 'lp_refine.py --path 084 --frame %s$' % FRAME], stdout=subprocess.PIPE).stdout.decode().split()
    for x in ph:
        os.kill(int(x), signal.SIGKILL)
    out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 3320 --to refine (p3, LINOG_MOCK_P3SLEEP, SIGKILL of the phase %s) rc %d\n%s' % (
            ph, p.returncode, out))
    time.sleep(1.5)
    alive = subprocess.run(['pgrep', '-f', 'refineSecondaryTiming_20081130_20090302'], stdout=subprocess.PIPE).stdout.decode().split()
    rr = rec('4a', 'refine')
    rc2, out2 = run(['--to', 'refine'])
    case('T80 the refine phase SIGKILLed while run_04 runs: no line left running (PDEATHSIG); rc 137, record RUNNING; the '
         'next run stops for --recover, rc 4', len(ph) == 1 and not alive and p.returncode == 137 and rr.get('verdict') == 'RUNNING'
         and rc2 == 4 and '--recover' in out2, 'phase %s; alive %s; rc %s; refine %s; next rc %d' % (ph, alive, p.returncode,
                                                                                                 rr.get('verdict'), rc2))

    import lp_p3 as P3
    case('T77 jobs at once: J 12, 157 lines, 7,014,432 kB per job: 12 with 122 GB free, 7 with 50 GB, 0 with 5 GB',
         [P3.jobs_for(12, 157, 7014432, x) for x in (122000000, 50000000, 5000000)] == [12, 7, 0]
         and P3.jobs_for(46, 6, 1000, 10 ** 9) == 6, str([P3.jobs_for(12, 157, 7014432, x) for x in (122000000, 50000000, 5000000)]))
    t1 = ('  20081130   +0.0 +32.0!   +1.0 +32.0!   +0.0 +31.0!      1    1     2.21 FAIL\nFAIL  1 of 3 date(s) failed\n')
    v = P3.reg_verdict(t1)
    case('T78 the G7 parser: a FAIL row and the verdict line anchored at line start (B55)', v['verdict'] == 'FAIL' and
         v['dates'].get('20081130', ('', ''))[1] == 'FAIL' and P3.tag_of(' referenceStackCopy.py -i a -o b') == 'referenceStackCopy'
         and P3.tag_of('stripmapWrapper.py -c /x/configs/config_geo2rdr_coarseResamp_20081130') == '20081130'
         and P3.tag_of('stripmapWrapper.py -c /x/configs/config_igram_20080830_20081130') == '20080830_20081130', str(v))

    # an output of topo changed on the complete frame: topo STALE, then DECISION (in the way), nothing written
    restore('S4e', 'T79')
    rc, out = run(['--to', 'igram'])
    f = os.path.join(W, 'geom_reference', 'lat.rdr.aux.xml')
    with open(f, 'a') as fh:
        fh.write('<!-- changed by the self-test -->\n')
    rc2, out2 = run(['--to', 'igram'])
    case('T79 a file of geom_reference changed after a clean run: topo STALE, DECISION (G3a.7), the later phases not run',
         rc == 0 and rc2 == 4 and 'P3a topo: record STALE' in out2 and gates(rec('3a', 'topo')).get('G3a.7') == 'DECISION',
         'rc %d then %d' % (rc, rc2))

    # a stop while the datum's --apply rewrites dates/: the apply finishes (its own session, the phase holds the
    # signal), md5s_after is on record; the next run finds the complete apply and checks it again, never applies twice
    restore('S3b', 'T81')
    rc0, out0 = run(['--to', 'invert'])
    inv = rec('4b', 'invert').get('outputs', {}).get('md5s')
    mark = os.path.join(T, 'apply81.mark')
    env81 = dict(env, LINOG_MOCK_APPLYSLEEP='3', LINOG_MOCK_MARK=mark)
    env81.pop('LINOG_MOCK_P3SLEEP', None)
    p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', 'auto', '--to', 'datum'], env=env81, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 180:
        time.sleep(0.2)
    time.sleep(0.5)
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
    out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 3320 --to datum (p3, LINOG_MOCK_APPLYSLEEP, SIGTERM during --apply) rc %d\n%s' % (
            p.returncode, out))
    rd = rec('4c', 'datum')
    od = rd.get('outputs', {})
    now = P3.shelf_md5s(W, 'refineSecondaryTiming/dates')
    baks = sorted(x for x in os.listdir(os.path.join(W, 'refineSecondaryTiming')) if x.startswith('dates_predatum_bak_'))
    rc2, out2 = run(['--to', 'datum'])
    rd2 = rec('4c', 'datum')
    hist = sorted(os.listdir(os.path.join(W, 'status', 'history'))) if os.path.isdir(os.path.join(W, 'status', 'history')) else []
    after2 = rd2.get('outputs', {}).get('after', {})
    case('T81 SIGTERM during the datum\'s --apply: rc 143, datum ERROR with md5s_after = dates/ and one pre-datum copy; the '
         'next run: G4c.4 finds the complete apply, G16 and G9 PASS, not applied twice; the ERROR record kept in status/history/',
         rc0 == 0 and p.returncode == 143 and rd.get('verdict') == 'ERROR' and od.get('md5s_after') == now and od.get('md5s_before') == inv
         and len(baks) == 1 and od.get('backup', '').endswith(baks[0]) and rc2 == 0 and rd2.get('verdict') == 'PASS'
         and 'the run of' in dict((g['id'], g['value']) for g in rd2.get('gates', [])).get('G4c.4', '')
         and P3.shelf_md5s(W, 'refineSecondaryTiming/dates') == now and after2.get(REF) == [0.0, 0.0]
         and any(x.startswith('P4c_datum.') for x in hist),
         'rc %s then %d; datum %s then %s; copies %s; history %s' % (p.returncode, rc2, rd.get('verdict'), rd2.get('verdict'), baks,
                                                                     [x for x in hist if x.startswith('P4c')]))

    # files added beside the recorded outputs (prep_isce's .rsc sidecars, a report) change nothing: all 17 skipped
    restore('S4e', 'T82')
    rc, out = run(['--to', 'igram'])
    for rel in ('geom_reference/hgt.rdr.rsc', 'merged/geom_reference/lat.rdr.rsc', 'Igrams/reports/igram_report.txt',
                'Igrams/20080830_20081130/filt_20080830_20081130_snaphu.unw.rsc', 'offsets/20081130/range.off.rsc'):
        os.makedirs(os.path.dirname(os.path.join(W, rel)), exist_ok=True)
        with open(os.path.join(W, rel), 'w') as fh:
            fh.write('added by the self-test\n')
    rc2, out2 = run(['--to', 'igram'])
    case('T82 .rsc files and a report added beside the outputs after a clean run: all 18 phases skipped (v0.13: bandlimit), rc 0',
         rc == 0 and rc2 == 0 and out2.count('skip: PASS on record') == 18, 'rc %d then %d; %d skipped' % (
             rc, rc2, out2.count('skip: PASS on record')))

    # a pair 14 px off in azimuth (not a reference pair: G8 passes): the plan's spread is above 5 px, datum FAILs at G9p
    # before anything is rewritten
    restore('S3b', 'T83')
    rc, out = run(['--to', 'datum'], {'LINOG_MOCK_BIGAZ': '20080830_20081130:14'})
    rd = rec('4c', 'datum')
    inv = rec('4b', 'invert').get('outputs', {}).get('md5s')
    baks = [x for x in os.listdir(os.path.join(W, 'refineSecondaryTiming')) if x.startswith('dates_predatum_bak_')]
    case('T83 a pair 14 px off in azimuth: refine and invert PASS, datum FAIL at G9p (the plan\'s spread), rc 2; dates/ not '
         'rewritten, no copy made', rc == 2 and rec('4a', 'refine').get('verdict') == 'PASS' and gates(rd).get('G9p') == 'FAIL'
         and 'G16' not in gates(rd) and P3.shelf_md5s(W, 'refineSecondaryTiming/dates') == inv and not baks,
         'rc %d; G9p %s: %s; copies %s' % (rc, gates(rd).get('G9p'), dict((g['id'], g['value']) for g in rd.get('gates', [])).get('G9p'),
                                           baks))

    if not fm:
        return
    # v0.9: planted pins (the wisdom changed, the library's md5, a module loading another library, a file that does not
    # import): refine FAILs at G4a.4w before anything runs
    for tag, cfgname, want in (('T157', 'fftw_badwis.cfg', 'wisdom_bad.wis: md5'), ('T158', 'fftw_badlib.cfg', 'libfftw3f'),
                               ('T159', 'fftw_badmod.cfg', 'ampcor loads /usr/lib/other/libfftw3f.so.3'),
                               ('T160', 'fftw_garbage.cfg', 'with the file: import 0, 0 of'),
                               ('T168', 'fftw_partial.cfg', 'with the file: import 1, 16 of 20 problems covered; the first not covered: n 64'),
                               ('T169', 'fftw_version.cfg', 'pinned fftw-0.0.0-mock'),
                               ('T170', 'fftw_link.cfg', 'lib/libfftw3f.so.3 resolves to')):
        restore('S3b', tag)
        rc, out = run(['--to', 'refine'], {'LINOG_FFTW_CFG': os.path.join(T, 'cfg', cfgname)})
        rr = rec('4a', 'refine')
        note = dict((g['id'], g.get('note', '')) for g in rr.get('gates', [])).get('G4a.4w', '')
        ids = [g['id'] for g in rr.get('gates', [])]
        case('%s %s: refine FAIL at G4a.4w (%s), rc 2; no job ran, nothing written in refineSecondaryTiming/' % (
            tag, {'T157': 'the wisdom file changed', 'T158': 'the library off its pin', 'T159': 'ampcor loading another libfftw3f',
                  'T160': 'a file at its pin that does not import', 'T168': 'a file at its pin covering 16 of the 20 problems',
                  'T169': 'another version string pinned', 'T170': 'the pinned library not the one lib/libfftw3f.so.3 resolves to'}[tag], want),
             rc == 2 and gates(rr).get('G4a.4w') == 'FAIL' and want in note and ids[-1] == 'G4a.4w'
             and not os.path.exists(os.path.join(W, 'refineSecondaryTiming')), 'rc %d; gates %s; note %s' % (rc, ids, note[:300]))

    # planted job logs: a STOP with status 0, a job without WISDOM_FILE, an igram job with crossmul's wisdom line only
    restore('S3b', 'T161')
    rc, out = run(['--to', 'refine'], {'LINOG_MOCK_WISDOMSTOP': '20081130_20090602'})
    rr = rec('4a', 'refine')
    note = dict((g['id'], g.get('note', '')) for g in rr.get('gates', [])).get('G4a.7w', '')
    case('T161 one job\'s import returns 0 (STOP, exit status 0): run_04 rc 0 on every line (G4a.7 PASS), refine FAIL at G4a.7w naming '
         'that pair and the STOP, rc 2', rc == 2 and gates(rr).get('G4a.7') == 'PASS' and gates(rr).get('G4a.7w') == 'FAIL'
         and '20081130_20090602' in note and 'STOP' in note and 'G4a.8' not in gates(rr), 'rc %d; %s; note %s' % (rc, gates(rr), note[:200]))
    restore('S3b', 'T162')
    rc, out = run(['--to', 'refine'], {'LINOG_MOCK_NOWISDOM': '20080830_20090302'})
    rr = rec('4a', 'refine')
    note = dict((g['id'], g.get('note', '')) for g in rr.get('gates', [])).get('G4a.7w', '')
    case('T162 one job ran without the wisdom (length 0): refine FAIL at G4a.7w naming that pair, rc 2',
         rc == 2 and gates(rr).get('G4a.7w') == 'FAIL' and '20080830_20090302' in note and 'length = 0' in note,
         'rc %d; note %s' % (rc, note[:200]))
    restore('S4e', 'T163')
    rc, out = run(['--to', 'igram'], {'LINOG_MOCK_ONEWISDOM': '20080830_20081130'})
    ri = rec('4f', 'igram')
    note = dict((g['id'], g.get('note', '')) for g in ri.get('gates', [])).get('G4f.8w', '')
    case('T163 one igram job with crossmul\'s wisdom line but not icu\'s: igram FAIL at G4f.8w (1 of 2 lines), rc 2',
         rc == 2 and gates(ri).get('G4f.8') == 'PASS' and gates(ri).get('G4f.8w') == 'FAIL' and '1 wisdom line(s), want 2' in note,
         'rc %d; note %s' % (rc, note[:200]))

    # the wisdom file changed during the step (a job appends to it after its import): the md5 read again after the jobs
    restore('S3b', 'T171')
    rc, out = run(['--to', 'refine'], {'LINOG_FFTW_CFG': os.path.join(T, 'cfg', 'fftw_touch.cfg'),
                                       'LINOG_MOCK_WISDOMTOUCH': '20080830_20081130'})
    rr = rec('4a', 'refine')
    val = dict((g['id'], g.get('value', '')) for g in rr.get('gates', [])).get('G4a.7w', '')
    case('T171 the wisdom file changed during run_04 (a job appends to it after its import): refine FAIL at G4a.7w, "changed during '
         'the step" with both md5s, rc 2', rc == 2 and gates(rr).get('G4a.4w') == 'PASS' and gates(rr).get('G4a.7w') == 'FAIL'
         and 'changed during the step' in val and fm['WISDOM_MD5'] in val, 'rc %d; G4a.7w %s' % (rc, val[:300]))

    # a WISDOM_FILE exported in the operator's shell does not reach the jobs (lp_env.sh passes LINOG_* only)
    restore('S3b', 'T164')
    rc, out = run(['--to', 'refine'], {'WISDOM_FILE': '/nonexistent/operator.wis'})
    rr = rec('4a', 'refine')
    lgs = sorted(glob.glob(os.path.join(rr.get('outputs', {}).get('logdir') or '/nonexistent', 'run_04_refineSecondaryTiming', '0*.log')))
    case('T164 WISDOM_FILE=/nonexistent/operator.wis in the operator\'s shell: refine PASS, its 6 jobs name the pinned file',
         rc == 0 and rr.get('verdict') == 'PASS' and len(lgs) == 6 and all(('WISDOM_FILE %s' % fm['WISDOM']) in open(f).read()
                                                                           and 'operator.wis' not in open(f).read() for f in lgs),
         'rc %d; %s; %d logs' % (rc, rr.get('verdict'), len(lgs)))

    # the STALE map: on a frame clean to igram, other pins in linog_fftw.cfg make refine and igram STALE, nothing else
    restore('S4f', 'T165')

    def state(ph, cfgname):
        env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p3.cfg'), LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'),
                   LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'),
                   LINOG_FFTW_CFG=os.path.join(T, 'cfg', cfgname), **E)
        p = subprocess.run(['python3', '-E', '-B', os.path.join(S.HERE, 'lp_%s.py' % ph), '--path', '084', '--frame', FRAME, '--state'],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1] if p.stdout else 'rc %d' % p.returncode
    s0 = dict((ph, state(ph, 'fftw_mock.cfg')) for _, ph in P34)
    s1 = dict((ph, state(ph, 'fftw_badlib.cfg')) for _, ph in P34)
    case('T165 the STALE map: with the mock pins all 8 Phase 3 and 4 records CURRENT; with another library pinned, refine and igram '
         'STALE and the other 6 CURRENT (their fingerprints carry the pins; LOGIC 2)',
         all(v == 'CURRENT' for v in s0.values()) and s1.get('refine') == 'STALE' and s1.get('igram') == 'STALE'
         and all(v == 'CURRENT' for k, v in s1.items() if k not in ('refine', 'igram')), 'mock %s; another library %s' % (s0, s1))
    # T166: refine to igram again from the frame after coarse: both PASS, and their records name the wisdom of the clean run
    restore('S3b', 'T166')
    rc, out = run(['--to', 'igram'])
    r4, r8 = rec('4a', 'refine'), rec('4f', 'igram')
    case('T166 refine to igram again on the frame after coarse: rc 0, both PASS with G4a.7w and G4f.8w PASS, the same wisdom file and md5 '
         'on record as the clean run', rc == 0 and gates(r4).get('G4a.7w') == 'PASS' and gates(r8).get('G4f.8w') == 'PASS'
         and ((r4.get('inputs') or {}).get('fftw') or {}).get('wisdom_md5') == fm['WISDOM_MD5']
         and ((r8.get('inputs') or {}).get('fftw') or {}).get('wisdom') == fm['WISDOM'],
         'rc %d; %s %s' % (rc, gates(r4).get('G4a.7w'), gates(r8).get('G4f.8w')))
