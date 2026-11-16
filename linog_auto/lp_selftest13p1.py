#!/usr/bin/env python3
"""lp_selftest13p1.py -- linog_auto v0.13's Phase 1 cases for FBS+FBD and FBD-only frames (called by lp_selftest.py as the
suite 13p1; the ascending automation record's case numbers).

phase13_1: Phase 1 on the mixed mock frame 3350 (12 dates, 4 FBD: 15.4) and the FBD-only mock frame 3360 (13 dates, one
narrower), recon to verify:
  M1 (4.11, to verify): the mixed frame through Phase 1 with every R6 gate PASS (M1's reference and G16 lines are parts 3
     and 4: D1f and M66); M8e, M8g a re-run and --force bandlimit (nothing called, nothing written), a dry run;
  M4, M4b, M5, M6 the mode and polarisation plants; M7, M8, M8b to M8f, M9 bandlimit's own; M10 an FBD .slc padded; M11 the
     shelves' instruments (G1c.8); M16 rwin on an FBD granule one gate off (Gap 2a);
  M81 to M83 (18.5, R6-d, to verify): the FBD-only frame (M15's extract ERROR withdrawn), one FBS date added, an FBD date
     framed 30 km off;
  M92 (12.3, item 4): Phase 1's four env gates on the env's prefix; M93 (14.2, item 1): the unpacker in the package; M94 the
     kit's two bandlimit files at linog_mixed.cfg's pins.
The granules carry band-limited samples in every record (lp_selftest.band_noise: FBS 28 of 32 MHz, FBD 14 of 16 MHz, IMG-HV
at half IMG-HH's amplitude); the mock sensor copies IMG-HH's into the SLC and takes the sampling rate, the wavelength and the
chirp from the leader (selftest_kit/mock_isce, ALOS_SLC.py). The kit's bandlimit tool runs at its pins (selftest_kit copies).
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess

FR, FR_FBD = '3350', '3360'


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None


def make_variant(T, S, name, plants, frame=FR, orbs=None, fbd=None, width=None, extra=()):
    """An archive of a mixed or FBD-only mock frame under T/archive_<name>/alos/28/: for frame 3350 the main archive's zips
    hard-linked but the planted ones (plants: index -> mkzip's keywords), made again; any other frame made whole; extra:
    more [orbit, keywords] granules. Returns the archive folder, or None when the samples could not be made (no numpy)."""
    orbs = S.ORBITS[:12] if orbs is None else orbs
    fbd = S.FBD_3350 if fbd is None else fbd
    src28 = os.path.join(T, 'archive', 'alos', '28')
    a = os.path.join(T, 'archive_%s' % name, 'alos')
    key = json.dumps(dict(frame=frame, orbs=list(orbs), fbd=sorted(fbd), plants=dict((str(k), v) for k, v in plants.items()),
                          widths=[width(i) if width else S.W_MX for i in range(len(orbs))], extra=list(extra)),
                     sort_keys=True, default=str)
    kf = os.path.join(T, 'archive_%s' % name, 'variant.json')
    if os.path.isdir(a):   # made by an earlier case: only with the same arguments (the part 3 review's P3-23)
        if not os.path.isfile(kf) or open(kf).read() != key:
            raise ValueError('make_variant: archive_%s exists with other arguments' % name)
        return a
    f = os.path.join(a, '28')
    os.makedirs(f)
    with open(kf, 'w') as fh:
        fh.write(key)
    specs = []
    for i, o in enumerate(orbs):
        kw = dict(fbd=(i in fbd), width=(width(i) if width else S.W_MX), lines=S.LINES_MX)
        if i in plants or frame != FR:
            kw.update(plants.get(i, {}))
            specs.append([f, o, frame, kw])
        else:
            for z in glob.glob(os.path.join(src28, 'ALPSRP%05d%s-*.zip' % (o, frame))):
                os.link(z, os.path.join(f, os.path.basename(z)))
    for o, kw in extra:
        specs.append([f, o, frame, dict(dict(width=S.W_MX, lines=S.LINES_MX), **kw)])
    ok = S.mkzips_data(specs) if specs else True
    return a if ok else None


def phase13_1(T, case, S):
    print('-- v0.13 Phase 1 (R6, R6-d): the mixed frame 3350 (8 FBS, 4 FBD) and the FBD-only frame 3360, recon to verify; '
          'bandlimit, G4, G1c.8, the env\'s prefix, the unpacker in the package')
    HERE = S.HERE
    V = ['--to', 'verify']
    ORB = S.ORBITS[:12]
    D = [S.date_of(o) for o in ORB]
    FBS = [D[i] for i in range(12) if i not in S.FBD_3350]
    FBDD = [D[i] for i in S.FBD_3350]
    pins = S.real_pins()
    mreal = dict(ln.strip().split('=', 1) for ln in open(os.path.join(HERE, 'linog_mixed.cfg'))
                 if ln.strip() and not ln.startswith('#') and '=' in ln)

    # M94 and M93 need no frame
    kit = [(n, k) for n, k in (('linog_fbs_bandlimit.py', 'KIT_FBS_BANDLIMIT_MD5'), ('linog_fbs_downsample.py', 'KIT_FBS_DOWNSAMPLE_MD5'))]
    same = [n for n, k in kit if md5(os.path.join(S.KITSRC, n)) == mreal.get(k)]
    case('M94 the self-test runs bandlimit\'s two kit files at linog_mixed.cfg\'s pins (the course kit\'s, 4.3)', len(same) == 2,
         '%d of 2 (%s)' % (len(same), ', '.join('%s %s' % (n, md5(os.path.join(S.KITSRC, n))) for n, _ in kit)))
    up = os.path.join(HERE, 'unpackFrame_ALOS.py')
    case('M93 (14.2, item 1) the unpacker in the package: unpackFrame_ALOS.py at UNPACKER_MD5, the course kit\'s copy byte for byte; '
         'linog_env.cfg\'s UNPACKER names <pipeline>/v0.13/unpackFrame_ALOS.py',
         md5(up) == pins.get('UNPACKER_MD5') == md5(os.path.join(S.KITSRC, 'unpackFrame_ALOS.py'))
         and pins.get('UNPACKER') == '/eggraid/home/arieln/projects/linog/insar/pipeline/v0.13/unpackFrame_ALOS.py',
         '%s; UNPACKER %s' % (md5(up), pins.get('UNPACKER')))
    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M1-M92 not run: the mock granules\' samples, the mock sensor and the kit\'s bandlimit tool need numpy, and neither '
             'Python tried has it', False)
        return

    def fd(root, frame=FR):
        return S.fdir(T, frame, root)

    def run(root, args, extra=None, cfg='paths.cfg', envcfg='env_mock.cfg', frame=FR, archive=None):
        e = dict({'LINOG_ROOT': os.path.join(T, root)}, **(extra or {}))
        if archive:
            e['LINOG_ARCHIVE'] = archive
        return S.run(T, ['084', frame] + args, cfg=cfg, env_extra=e, envcfg=envcfg)

    def rec(root, idx, ph, frame=FR):
        return S.rec(T, frame, idx, ph, root)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))

    def gval(r, gid):
        x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
        return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''

    def slc(root, d, frame=FR):
        return os.path.join(fd(root, frame), 'SLC', d, d + '.slc')

    def ids(root, dates, frame=FR):
        out = {}
        for d in dates:
            for p in (slc(root, d, frame), slc(root, d, frame) + '.prefilter'):
                if os.path.exists(p):
                    s_ = os.stat(p)
                    out[p] = (s_.st_size, s_.st_mtime_ns)
        return out

    def nlogs(root):
        return len(glob.glob(os.path.join(fd(root), 'logs', 'bandlimit', '*.log.v*')))

    def variant(name, plants, frame=FR, orbs=ORB, fbd=S.FBD_3350, width=None, extra=()):
        return make_variant(T, S, name, plants, frame, orbs, fbd, width, extra)

    def snap(root, name):
        """A copy of the frame (copy2: sizes and mtimes kept; nothing hard-linked, since bandlimit writes .slc files in place)."""
        dst = os.path.join(T, 'snap_13p1', name)
        shutil.copytree(fd(root), dst, symlinks=True)
        return dst

    def restore(root, name, tag):
        S.aside(T, fd(root), '13p1_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_13p1', name), fd(root), symlinks=True)

    # ---------------------------------------------------------------------------------------------- M1: the clean run
    rc, out = run('mx', V)
    rr, rx, rw, rb, rv = rec('mx', '0a', 'recon'), rec('mx', '1a', 'extract'), rec('mx', '1br', 'rwin'), rec('mx', '1bs', 'bandlimit'), \
        rec('mx', '1c', 'verify')
    fsm = dict((x['date'], x.get('fs_mhz')) for x in (rw.get('outputs') or {}).get('dates', []))
    bo = rb.get('outputs') or {}
    rows = dict((x['date'], x) for x in bo.get('fbs') or [])
    rd = [rows.get(d, {}).get('readings') or {} for d in FBS]
    prog = [json.loads(ln) for ln in open(os.path.join(fd('mx'), 'status', 'P1bs_bandlimit.progress'))] \
        if os.path.isfile(os.path.join(fd('mx'), 'status', 'P1bs_bandlimit.progress')) else []
    started = dict((x['date'], x['md5']) for x in prog if x['event'] == 'started')
    pre_ok = all(md5(slc('mx', d) + '.prefilter') == started.get(d) for d in FBS)
    nopre = not any(os.path.exists(slc('mx', d) + '.prefilter') for d in FBDD)
    pyc = glob.glob(os.path.join(T, 'kit', '__pycache__'))
    M, _ = S.modes(T, FR, 'mx')
    mrows = dict((x['date'], x) for x in M.get('dates', []))
    gv = gates(rv)
    case('M1 the mixed frame 3350 (8 FBS, 4 FBD) recon to verify: rc 0, the 7 records PASS; G0.10 FBS+FBD; extract\'s G1a.4 and '
         'G1a.5 with IMG-HV on the 4 FBD dates; rwin\'s fs_mhz 32 and 16 by mode',
         rc == 0 and S.verdicts(T, FR, 'mx') == ['PASS'] * 7 and 'FBS 8, FBD 4 -> FBS+FBD' in gval(rr, 'G0.10')
         and 'IMG-HH and IMG-HV on 4 FBD dates' in gval(rx, 'G1a.5') and gates(rx).get('G1a.4') == 'PASS'
         and [fsm.get(d) for d in FBS] == [32.0] * 8 and [fsm.get(d) for d in FBDD] == [16.0] * 4,
         'rc %d; %s; G0.10 %s; G1a.5 %s; fs %s' % (rc, S.verdicts(T, FR, 'mx'), gval(rr, 'G0.10'), gval(rx, 'G1a.5')[:70],
                                                 sorted(set(fsm.values()))))
    case('M1b bandlimit on the 8 FBS dates: G1bl.1 to G1bl.10 PASS; each .prefilter the unpacked file (the started line\'s md5), '
         'no .prefilter beside an FBD date; recompute RMS <= 1e-6, power above 7 MHz <= 0.01 in the .slc and >= 0.40 in the '
         '.prefilter, POST95 / FBD median inside 0.35 to 0.75; 8 started and 8 done lines; no __pycache__ in the kit folder',
         rb.get('verdict') == 'PASS' and all(gates(rb).get('G1bl.%d' % i) == 'PASS' for i in range(1, 11))
         and [rows.get(d, {}).get('action') for d in FBS] == ['done'] * 8 and len(bo.get('fbd') or []) == 4 and pre_ok and nopre
         and all(x.get('rms', 1) <= 1e-6 and x.get('hi_slc', 1) <= 0.01 and x.get('hi_pre', 0) >= 0.40
                 and 0.35 < (x.get('ratio') or 0) < 0.75 for x in rd)
         and [x['event'] for x in prog].count('started') == 8 and [x['event'] for x in prog].count('done') == 8 and not pyc,
         '%s; rms <= %.2g; >7MHz slc %.4f to %.4f, pre %.4f to %.4f; ratio %.4f to %.4f; FBD median %s; prefilter = unpacked %s; '
         'progress %d lines; pycache %s' % (
             rb.get('verdict'), max([x.get('rms', 1) for x in rd] or [1]), min([x.get('hi_slc', 1) for x in rd] or [1]),
             max([x.get('hi_slc', 1) for x in rd] or [1]), min([x.get('hi_pre', 0) for x in rd] or [0]),
             max([x.get('hi_pre', 0) for x in rd] or [0]), min([x.get('ratio') or 0 for x in rd] or [0]),
             max([x.get('ratio') or 0 for x in rd] or [0]), bo.get('fbd_median95'), pre_ok, len(prog), pyc))
    pol = [mrows.get(d, {}).get('pol') or {} for d in FBDD]
    case('M1c verify: G1c.1 names bandlimit, G4 PASS on the 4 FBD dates from IMG-HH (HH/HV about 2), G1c.8 PASS (one wavelength, '
         '32 and 16 MHz by mode, SLR(FBD) / SLR(FBS) = 2), modes.json 12 rows with fs_hz, wavelength_m, slr_m',
         gv.get('G1c.1') == 'PASS' and 'bandlimit 8 FBS dates, 4 FBD dates as it left them' in gval(rv, 'G1c.1')
         and gv.get('G4') == 'PASS' and '4 of 4 FBD dates from IMG-HH' in gval(rv, 'G4') and gv.get('G1c.8') == 'PASS'
         and 'SLR(FBD) / SLR(FBS) 2.000000000000' in gval(rv, 'G1c.8') and len(mrows) == 12
         and sorted(set(x.get('fs_hz') for x in mrows.values())) == [16e6, 32e6]
         and all(1.9 < (p.get('ratio') or 0) < 2.1 for p in pol),
         'G4 %s | G1c.8 %s | HH/HV %s' % (gval(rv, 'G4'), gval(rv, 'G1c.8')[:110], [round(p.get('ratio') or 0, 3) for p in pol]))

    # M8e: nothing called again, nothing rewritten
    i0, n0 = ids('mx', D), nlogs('mx')
    rc, out = run('mx', V)
    rc2, out2 = run('mx', V + ['--force', 'bandlimit'])
    rb2 = rec('mx', '1bs', 'bandlimit')
    case('M8e a re-run with every date done: the 7 phases skipped; --force bandlimit: nothing called (G1bl.10 N/A, 8 skipped), every '
         '.slc and .prefilter as before (size and mtime), verify CURRENT',
         rc == 0 and out.count('skip: PASS on record') == 7 and rc2 == 0 and gates(rb2).get('G1bl.10') == 'N/A'
         and (rb2.get('outputs') or {}).get('skipped') == 8 and ids('mx', D) == i0 and nlogs('mx') == n0
         and 'P1c verify: record CURRENT' in out2,
         'rc %d (%d skipped), %d; G1bl.10 %s; logs %d -> %d' % (rc, out.count('skip: PASS on record'), rc2, gates(rb2).get('G1bl.10'),
                                                              n0, nlogs('mx')))
    dry = os.path.join(T, 'dry_13p1')
    f0 = sorted(os.path.relpath(os.path.join(dp, n), fd('mx')) for dp, _, ns in os.walk(fd('mx')) for n in ns)
    rc, out = run('mx', ['--dry-run', dry] + V)
    bd = json.load(open(os.path.join(dry, 'status', 'P1bs_bandlimit.json'))) if os.path.isfile(os.path.join(dry, 'status', 'P1bs_bandlimit.json')) else {}
    f1 = sorted(os.path.relpath(os.path.join(dp, n), fd('mx')) for dp, _, ns in os.walk(fd('mx')) for n in ns)
    case('M8g a dry run on the band-limited frame: bandlimit\'s plan PASS, nothing to do, the 8 FBS dates done earlier; the frame '
         'unchanged',
         rc == 0 and bd.get('verdict') == 'PASS' and (bd.get('outputs') or {}).get('planned') == [] and
         len((bd.get('outputs') or {}).get('skipped') or []) == 8 and f0 == f1,
         'rc %d; %s; planned %s skipped %d; files %d -> %d' % (rc, bd.get('verdict'), (bd.get('outputs') or {}).get('planned'),
                                                             len((bd.get('outputs') or {}).get('skipped') or []), len(f0), len(f1)))

    # M7: an FBS .slc put back from its .prefilter
    d0 = FBS[0]
    bk = os.path.join(T, '_archive', 'M7_%s.slc' % d0)
    os.makedirs(os.path.dirname(bk), exist_ok=True)
    shutil.copy2(slc('mx', d0), bk)
    shutil.copyfile(slc('mx', d0) + '.prefilter', slc('mx', d0))
    rc, out = run('mx', ['--only', 'verify'])
    v7 = rec('mx', '1c', 'verify')
    rc2, out2 = run('mx', V)
    b7 = rec('mx', '1bs', 'bandlimit')
    shutil.copy2(bk, slc('mx', d0))
    rc3, out3 = run('mx', V)
    case('M7 one FBS .slc put back from its .prefilter after bandlimit: --only verify FAILs at G1c.1 naming it; a full run reads '
         'bandlimit STALE and its re-run DECISION (G1bl.3: the done line no longer matches); the band-limited file put back -> PASS',
         rc == 2 and gates(v7).get('G1c.1') == 'FAIL' and 'not as bandlimit left them (%s' % d0 in gval(v7, 'G1c.1')
         and rc2 == 4 and 'P1bs bandlimit: record STALE' in out2 and gates(b7).get('G1bl.3') == 'DECISION'
         and d0 in gval(b7, 'G1bl.3') and rc3 == 0,
         'rc %d, %d, %d; G1c.1 %s; G1bl.3 %s' % (rc, rc2, rc3, gval(v7, 'G1c.1')[:80], gval(b7, 'G1bl.3')[:90]))

    # M8f: the pins, the kit, the disk
    kb = os.path.join(T, 'kit_bl2')
    shutil.copytree(os.path.join(T, 'kit'), kb)
    with open(os.path.join(kb, 'linog_fbs_bandlimit.py'), 'a') as fh:
        fh.write('# changed by the self-test (M8f)\n')
    ecfg = open(os.path.join(T, 'cfg', 'env_mock.cfg')).read()
    with open(os.path.join(T, 'cfg', 'env_kitbl2.cfg'), 'w') as fh:
        fh.write('\n'.join(('KIT=%s' % kb) if ln.startswith('KIT=') else ln for ln in ecfg.splitlines()) + '\n')
    mcfg = open(os.path.join(HERE, 'linog_mixed.cfg')).read()
    m2 = os.path.join(T, 'cfg', 'mixed_bl2.cfg')
    with open(m2, 'w') as fh:
        fh.write(mcfg.replace('KIT_FBS_BANDLIMIT_MD5=%s' % mreal['KIT_FBS_BANDLIMIT_MD5'],
                              'KIT_FBS_BANDLIMIT_MD5=%s' % md5(os.path.join(kb, 'linog_fbs_bandlimit.py'))))
    with open(os.path.join(T, 'cfg', 'paths_bigmargin.cfg'), 'w') as fh:
        fh.write(open(os.path.join(T, 'cfg', 'paths.cfg')).read().replace('disk_gib_margin = 0\n', 'disk_gib_margin = 1e9\n'))
    O = ['--only', 'bandlimit', '--force', 'bandlimit']
    rc1, _ = run('mx', O, envcfg='env_kitbl2.cfg')
    g1 = gates(rec('mx', '1bs', 'bandlimit'))
    rc2, _ = run('mx', O, envcfg='env_kitbl2.cfg', extra={'LINOG_MIXED_CFG': m2})
    b2 = rec('mx', '1bs', 'bandlimit')
    rc3, _ = run('mx', O, cfg='paths_bigmargin.cfg')
    g3 = gates(rec('mx', '1bs', 'bandlimit'))
    rc4, _ = run('mx', V)
    case('M8f a kit file off its pin: G1bl.2 FAIL; the same file at a new pin after the dates were done: G1bl.3 DECISION on all 8 '
         '(done with other pins); free disk short: G1bl.9 FAIL; back to the package\'s: PASS',
         rc1 == 2 and g1.get('G1bl.2') == 'FAIL' and rc2 == 4 and gates(b2).get('G1bl.2') == 'PASS'
         and gates(b2).get('G1bl.3') == 'DECISION' and gval(b2, 'G1bl.3').count('done with other pins') == 8
         and rc3 == 2 and g3.get('G1bl.9') == 'FAIL' and rc4 == 0,
         'rc %d, %d, %d, %d' % (rc1, rc2, rc3, rc4))

    # M92: Phase 1's env gates on the prefix
    sm = open(os.path.join(T, 'cfg', 'stack_mock.cfg')).read()
    so = os.path.join(T, 'cfg', 'stack_otherprefix13.cfg')
    with open(so, 'w') as fh:
        fh.write('\n'.join('ENV_PREFIX=/nonexistent/linog_isce2' if ln.startswith('ENV_PREFIX=') else ln for ln in sm.splitlines()) + '\n')
    res92 = []
    # from the last phase back: each forced ERROR leaves its record ERROR, which the next phase's prior check would read first
    for idx, ph, gid in (('1c', 'verify', 'G1c.2'), ('1bs', 'bandlimit', 'G1bl.2'), ('1br', 'rwin', 'G1br.2'), ('1b', 'unpack', 'G1b.2')):
        rc, _ = run('mx', ['--only', ph, '--force', ph], extra={'LINOG_STACK_CFG': so})
        r = rec('mx', idx, ph)
        res92.append((ph, rc, gates(r).get(gid), 'is not ENV_PREFIX /nonexistent/linog_isce2' in gval(r, gid)))
    rc5, _ = run('mx', V)
    case('M92 (12.3, item 4) CONDA_PREFIX not linog_stack.cfg\'s ENV_PREFIX: unpack\'s G1b.2, rwin\'s G1br.2, bandlimit\'s G1bl.2 and '
         'verify\'s G1c.2 ERROR (rc 3), naming the prefix; the pinned prefix back -> PASS, nothing unpacked again',
         all(x[1] == 3 and x[2] == 'ERROR' and x[3] for x in res92) and rc5 == 0
         and (rec('mx', '1b', 'unpack').get('outputs') or {}).get('unpacked') == 0,
         '%s; then rc %d' % (res92, rc5))

    # M10: an FBD .slc padded without its shelve (N33)
    f10 = slc('mx', FBDD[0])
    st10 = os.stat(f10)
    with open(f10, 'ab') as fh:
        fh.write(b'\0' * (8 * S.W_MX))
    rc1, _ = run('mx', ['--only', 'verify'])
    v1 = rec('mx', '1c', 'verify')
    rc2, _ = run('mx', ['--only', 'bandlimit', '--force', 'bandlimit'])
    rc3, _ = run('mx', ['--only', 'verify'])
    v3 = rec('mx', '1c', 'verify')
    rc4, out4 = run('mx', V)
    u4 = rec('mx', '1b', 'unpack')
    with open(f10, 'r+b') as fh:
        fh.truncate(st10.st_size)
    os.utime(f10, ns=(st10.st_atime_ns, st10.st_mtime_ns))
    rc5, _ = run('mx', V)
    case('M10 an FBD .slc padded by a line without its shelve (N33): --only verify FAILs at G1c.1 (bandlimit recorded it); after '
         'bandlimit records it, at G6; a full run stops earlier, at unpack\'s G1b.3 (DECISION); the file back -> PASS',
         rc1 == 2 and gates(v1).get('G1c.1') == 'FAIL' and FBDD[0] in gval(v1, 'G1c.1') and rc2 == 0
         and rc3 == 2 and gates(v3).get('G1c.1') == 'PASS' and gates(v3).get('G6') == 'FAIL'
         and rc4 == 4 and gates(u4).get('G1b.3') == 'DECISION' and rc5 == 0,
         'rc %d, %d, %d, %d, %d; G6 %s' % (rc1, rc2, rc3, rc4, rc5, gval(v3, 'G6')[:90]))

    # ------------------------------------------------------------------------- bandlimit's own cases on fresh frames
    rc, _ = run('mxd', ['--to', 'rwin'])
    snap('mxd', 'rwin')
    sub = {}
    for tag, extra in (('twice', {'LINOG_MOCK_BL_TWICE': d0}), ('undo', {'LINOG_MOCK_BL_UNDO': d0}),
                       ('e64', {'LINOG_MIXED_CFG': os.path.join(T, 'cfg', 'mixed_e64.cfg')}), ('fbd', {'LINOG_MOCK_BL_FBD': FBDD[1]})):
        if tag == 'e64':
            with open(extra['LINOG_MIXED_CFG'], 'w') as fh:
                fh.write(mcfg.replace('KEEP_FRACTION=0.4375', 'KEEP_FRACTION=0.875'))
        if sub:
            restore('mxd', 'rwin', tag)
        rcx, _ = run('mxd', ['--to', 'bandlimit'], extra=extra)
        sub[tag] = (rcx, gates(rec('mxd', '1bs', 'bandlimit')), gval(rec('mxd', '1bs', 'bandlimit'), 'G1bl.8'))
    fails = dict((k, sorted(g for g, v in x[1].items() if v == 'FAIL')) for k, x in sub.items())
    case('M8d a second filter on top (a test hook): G1bl.5 FAIL alone; the .prefilter put back as the .slc: G1bl.5 and G1bl.6 FAIL (and '
         'G1bl.7); keep_fraction 0.875 in linog_mixed.cfg (E64\'s trap): G1bl.6 and G1bl.7 FAIL; each rc 2',
         rc == 0 and sub['twice'][0] == 2 and fails['twice'] == ['G1bl.5'] and sub['undo'][0] == 2
         and fails['undo'] == ['G1bl.5', 'G1bl.6', 'G1bl.7'] and sub['e64'][0] == 2 and fails['e64'] == ['G1bl.6', 'G1bl.7'],
         '%s' % dict((k, (sub[k][0], fails[k])) for k in ('twice', 'undo', 'e64')))
    case('M9 a test hook passes an FBD date to the tool after the FBS dates: G1bl.8 FAIL naming it (a .prefilter beside it, its .slc '
         'rewritten), rc 2', sub['fbd'][0] == 2 and fails['fbd'] == ['G1bl.8'] and FBDD[1] in sub['fbd'][2],
         'rc %d; %s; %s' % (sub['fbd'][0], fails['fbd'], sub['fbd'][2][:100]))
    # M8b: a started line whose .prefilter was replaced by a filtered copy (and its .slc filtered too)
    restore('mxd', 'rwin', 'm8b')
    rc1, _ = run('mxd', ['--to', 'bandlimit'], extra={'LINOG_MOCK_BL_KILL': '%s:after' % d0})
    p = subprocess.run([S.MOCKPY[0], '-B', os.path.join(T, 'kit', 'linog_fbs_bandlimit.py'), 'SLC', '--keep-fraction', '0.4375',
                        '--taper-width', '0.05', '--dates', d0], cwd=fd('mxd'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shutil.copyfile(slc('mxd', d0), slc('mxd', d0) + '.prefilter')
    rc2, _ = run('mxd', ['--to', 'bandlimit', '--recover'])
    b8 = rec('mxd', '1bs', 'bandlimit')
    case('M8b a date stopped after the tool\'s copy whose .prefilter and .slc were both filtered afterwards: neither is the unpacked file, '
         'so G1bl.4 DECISION naming it (rc 4), nothing called',
         rc1 == 137 and p.returncode == 0 and rc2 == 4 and gates(b8).get('G1bl.4') == 'DECISION' and d0 in gval(b8, 'G1bl.4'),
         'rc %d, tool %d, %d; G1bl.4 %s' % (rc1, p.returncode, rc2, gval(b8, 'G1bl.4')[:100]))
    # M8: a .prefilter in the way
    restore('mxd', 'rwin', 'm8')
    shutil.copy2(slc('mxd', FBS[2]), slc('mxd', FBS[2]) + '.prefilter')
    rc1, _ = run('mxd', ['--to', 'bandlimit'])
    b1 = rec('mxd', '1bs', 'bandlimit')
    np1 = os.path.isfile(os.path.join(fd('mxd'), 'status', 'P1bs_bandlimit.progress'))
    S.aside(T, slc('mxd', FBS[2]) + '.prefilter', 'M8')
    rc2, _ = run('mxd', ['--to', 'bandlimit'])
    case('M8 a .prefilter beside an FBS date before bandlimit\'s first run: G1bl.3 DECISION naming it, no line written, nothing '
         'called; moved -> PASS',
         rc1 == 4 and gates(b1).get('G1bl.3') == 'DECISION' and FBS[2] in gval(b1, 'G1bl.3') and not np1 and rc2 == 0,
         'rc %d then %d; %s' % (rc1, rc2, gval(b1, 'G1bl.3')[:90]))
    # M8c: stops mid-date, by a SIGKILL after the copy and during it
    restore('mxd', 'rwin', 'm8c')
    rc1, _ = run('mxd', ['--to', 'bandlimit'], extra={'LINOG_MOCK_BL_KILL': '%s:after' % d0})
    st1 = rec('mxd', '1bs', 'bandlimit').get('verdict')
    rc2, out2 = run('mxd', ['--to', 'bandlimit'])
    rc3, _ = run('mxd', ['--to', 'bandlimit', '--recover'], extra={'LINOG_MOCK_BL_KILL': '%s:copy' % FBS[1]})
    part = os.path.getsize(slc('mxd', FBS[1]) + '.prefilter') if os.path.exists(slc('mxd', FBS[1]) + '.prefilter') else None
    rc4, _ = run('mxd', ['--to', 'verify', '--recover'])
    b4 = rec('mxd', '1bs', 'bandlimit')
    acts = dict((x['date'], x['action']) for x in (b4.get('outputs') or {}).get('fbs') or [])
    arch = (b4.get('outputs') or {}).get('archived') or []
    case('M8c a stop after the tool\'s copy (SIGKILL, rc 137): the record RUNNING, a run without --recover stops (rc 4), the re-run '
         'calls the tool again from the copy; a stop half way through the copy: the partial .prefilter moved into '
         '_archive/bandlimit_<UTC>/, the re-run passes; verify PASS',
         rc1 == 137 and st1 == 'RUNNING' and rc2 == 4 and rc3 == 137 and part == S.W_MX * S.LINES_MX * 4 and rc4 == 0
         and gates(b4).get('G1bl.4') == 'PASS' and acts.get(FBS[1]) == 'resumed' and len(arch) == 1 and FBS[1] in arch[0]
         and rec('mxd', '1c', 'verify').get('verdict') == 'PASS',
         'rc %d (%s), %d, %d (partial %s B), %d; actions %s; archived %s' % (rc1, st1, rc2, rc3, part, rc4,
                                                                           dict((k, v) for k, v in acts.items() if v != 'done'), arch))

    # ------------------------------------------------------------------------ the archive's plants (fresh roots)
    a4 = variant('m4', {0: dict(fs_mhz=16.0)})
    rc, _ = run('m4', V, archive=a4)
    b = rec('m4', '1bs', 'bandlimit')
    nothing = not os.path.exists(os.path.join(fd('m4'), 'status', 'P1bs_bandlimit.progress')) and \
        not glob.glob(os.path.join(fd('m4'), 'SLC', '*', '*.prefilter'))
    case('M4 a 16 MHz granule with no IMG-HV member (recon calls it FBS): bandlimit\'s G1bl.1 FAIL naming it before any write (rc 2)',
         rc == 2 and gates(b).get('G1bl.1') == 'FAIL' and D[0] in gval(b, 'G1bl.1') and nothing
         and S.verdicts(T, FR, 'm4')[:5] == ['PASS'] * 5,
         'rc %d; %s' % (rc, gval(b, 'G1bl.1')[:110]))
    a41 = variant('m4b1', {2: dict(hv_member=False)})
    rc1, _ = run('m4b1', V, archive=a41)
    a42 = variant('m4b2', {5: dict(hv_short=8)})
    rc2, _ = run('m4b2', V, archive=a42)
    x2 = rec('m4b2', '1a', 'extract')
    case('M4b an FBD granule that lists IMG-HV without the member: recon\'s G0.8 FAIL; an FBD granule whose IMG-HV is 8 B short: '
         'extract\'s G1a.5 FAIL naming IMG-HV, nothing extracted',
         rc1 == 2 and gates(rec('m4b1', '0a', 'recon')).get('G0.8') == 'FAIL' and rc2 == 2 and gates(x2).get('G1a.5') == 'FAIL'
         and 'IMG-HV' in gval(x2, 'G1a.5') and S.nsub(T, FR, 'unzipped', 'm4b2') == -1,
         'rc %d, %d; G1a.5 %s' % (rc1, rc2, gval(x2, 'G1a.5')[:100]))
    rc, _ = run('mx5', V, extra={'LINOG_MOCK_HV': '%s:log' % FBDD[0]})
    u5 = rec('mx5', '1b', 'unpack')
    case('M5 the unpacker reads IMG-HV for an FBD date and its log names it: unpack\'s G1b.5 FAIL naming the date (rc 2)',
         rc == 2 and gates(u5).get('G1b.5') == 'FAIL' and FBDD[0] in gval(u5, 'G1b.5') and 'IMG-HV' in gval(u5, 'G1b.5'),
         'rc %d; %s' % (rc, gval(u5, 'G1b.5')[:100]))
    rc, _ = run('mx6', V, extra={'LINOG_MOCK_HV': FBDD[1]})
    v6 = rec('mx6', '1c', 'verify')
    case('M6 it reads IMG-HV and its log names IMG-HH: unpack, rwin and bandlimit PASS; verify\'s G4 FAIL naming the date (nearer '
         'IMG-HV), rc 2',
         rc == 2 and S.verdicts(T, FR, 'mx6')[:6] == ['PASS'] * 6 and gates(v6).get('G4') == 'FAIL'
         and FBDD[1] in gval(v6, 'G4') and 'nearer IMG-HV' in gval(v6, 'G4'),
         'rc %d; %s' % (rc, gval(v6, 'G4')[:110]))
    rc, _ = run('mx11', V, extra={'LINOG_MOCK_WAVELENGTH': '%s:1.000001' % FBS[3], 'LINOG_MOCK_FS16': FBS[4]})
    v11 = rec('mx11', '1c', 'verify')
    case('M11 a shelve\'s wavelength off by 1e-6 (relative), and a 16 MHz shelve on a date its leader and the IMG-HV witness call FBS: '
         'bandlimit PASS (its leader reads 32 MHz); verify\'s G1c.8 FAIL naming both (rc 2)',
         rc == 2 and rec('mx11', '1bs', 'bandlimit').get('verdict') == 'PASS' and gates(v11).get('G1c.8') == 'FAIL'
         and FBS[3] in gval(v11, 'G1c.8') and FBS[4] in gval(v11, 'G1c.8') and 'wavelength' in gval(v11, 'G1c.8'),
         'rc %d; %s' % (rc, gval(v11, 'G1c.8')[-160:]))
    a16 = variant('m16', {7: dict(r1_off_m=-S.GATE)})
    rc, _ = run('m16', V, archive=a16)
    w16 = rec('m16', '1br', 'rwin')
    k16 = dict((x['date'], x.get('k')) for x in (w16.get('outputs') or {}).get('dates') or [])
    case('M16 (Gap 2a) an FBD granule whose image records sit one gate (16 samples at 16 MHz) nearer than its leader: rwin sets its '
         'r0 by one gate (k -1), G1br.8 PASS; bandlimit and verify PASS (G1c.4 on the grid), rc 0',
         rc == 0 and (w16.get('outputs') or {}).get('change') == [D[7]] and k16.get(D[7]) == -1 and gates(w16).get('G1br.8') == 'PASS'
         and S.verdicts(T, FR, 'm16') == ['PASS'] * 7,
         'rc %d; change %s; k %s' % (rc, (w16.get('outputs') or {}).get('change'), k16.get(D[7])))

    # --------------------------------------------------------------------------------- M81 to M83: FBD-only (R6-d)
    O13 = S.ORBITS[:13]
    wfbd = lambda i: S.W_MX if i == 12 else S.W_MX + 48   # noqa: E731  (12 at 1048, one 3 FBD gates narrower, as 4640 and 4544)
    a81 = variant('fbd', {}, frame=FR_FBD, orbs=O13, fbd=range(13), width=wfbd)
    rc, _ = run('fbd', V, frame=FR_FBD, archive=a81)
    r81, b81, v81 = rec('fbd', '0a', 'recon', FR_FBD), rec('fbd', '1bs', 'bandlimit', FR_FBD), rec('fbd', '1c', 'verify', FR_FBD)
    M81, _ = S.modes(T, FR_FBD, 'fbd')
    case('M81 (R6-d) the FBD-only frame 3360 (12 dates at 1048 samples, one at 1000) recon to verify: rc 0; G0.10 FBD-only; extract '
         'PASS (M15\'s ERROR withdrawn); bandlimit N/A; G4 on all 13; G1c.8 PASS on one mode; modes.json all FBD',
         rc == 0 and S.verdicts(T, FR_FBD, 'fbd') == ['PASS'] * 7 and 'FBS 0, FBD 13 -> FBD-only' in gval(r81, 'G0.10')
         and gates(b81).get('G1bl.0') == 'N/A' and '13 of 13 FBD dates from IMG-HH' in gval(v81, 'G4')
         and gates(v81).get('G1c.8') == 'PASS' and 'n/a (one mode)' in gval(v81, 'G1c.8')
         and (M81.get('census') or {}).get('mode') == {'FBD': 13},
         'rc %d; %s; G0.10 %s; bandlimit %s; G4 %s' % (rc, S.verdicts(T, FR_FBD, 'fbd'), gval(r81, 'G0.10'), gval(b81, 'G1bl.0')[:60],
                                                     gval(v81, 'G4')[:60]))
    a82 = variant('fbd1', {}, frame=FR_FBD, orbs=O13, fbd=range(13), width=wfbd, extra=[[S.ORBITS[13], dict(fbd=False)]])
    rc, _ = run('fbd1', V, frame=FR_FBD, archive=a82)
    b82 = rec('fbd1', '1bs', 'bandlimit', FR_FBD)
    case('M82 the same frame with one FBS date added: the mixed branch (FBS 1, FBD 13); bandlimit filters the one FBS date against '
         'the 13 FBD dates\' median; verify PASS',
         rc == 0 and 'FBS 1, FBD 13 -> FBS+FBD' in gval(rec('fbd1', '0a', 'recon', FR_FBD), 'G0.10')
         and [x['action'] for x in (b82.get('outputs') or {}).get('fbs') or []] == ['done']
         and len((b82.get('outputs') or {}).get('fbd') or []) == 13 and rec('fbd1', '1c', 'verify', FR_FBD).get('verdict') == 'PASS',
         'rc %d; %s' % (rc, gval(b82, 'G1bl.7')[:110]))
    a83 = variant('fbd2', {}, frame=FR_FBD, orbs=O13, fbd=range(13), width=wfbd,
                  extra=[[S.ORBITS[13], dict(fbd=True, g016=dict(along_km=-30.4))]])
    rc, _ = run('fbd2', V, frame=FR_FBD, archive=a83)
    R83 = json.load(open(os.path.join(fd('fbd2', FR_FBD), 'recon', 'RECON.json'))) if os.path.isfile(os.path.join(fd('fbd2', FR_FBD), 'recon', 'RECON.json')) else {}
    case('M83 an FBD-only frame with a granule framed 30 km back (N34\'s 2010-12-13 kind): G0.16 drops it, 13 kept; the rest as M81',
         rc == 0 and len(R83.get('kept') or []) == 13 and gates(rec('fbd2', '0a', 'recon', FR_FBD)).get('G0.16') in ('PASS', 'INFO', 'WARN')
         and 'ALPSRP%05d%s' % (S.ORBITS[13], FR_FBD) in gval(rec('fbd2', '0a', 'recon', FR_FBD), 'G0.16')
         and S.verdicts(T, FR_FBD, 'fbd2') == ['PASS'] * 7,
         'rc %d; kept %d; G0.16 %s' % (rc, len(R83.get('kept') or []), gval(rec('fbd2', '0a', 'recon', FR_FBD), 'G0.16')[:120]))

    # --------------------------------------------------------------- the part 2 review's fixes (review/p2/REPORT.md)
    phase13_1_review(T, case, S, dict(run=run, rec=rec, gates=gates, gval=gval, slc=slc, fd=fd, snap=snap, restore=restore,
                                      variant=variant, ids=ids), FBS, FBDD, D, mcfg, mreal, V)


def phase13_1_review(T, case, S, H, FBS, FBDD, D, mcfg, mreal, V):
    """The part 2 review's fixes: M8h (P2-01: a date stopped under other settings resumes at today's), M8i (P2-03: a done
    date unpacked again is band-limited anew), M8j (P2-04: a dry run reads rwin's sampling rates), M8k (P2-05: band-limit
    traces on a one-mode frame), M8l (P2-06: M8b's literal case), M8m (P2-09: a hard-linked .slc), M8n (P2-07 c: a .prefilter
    beside an FBD date), M8o (P2-07 d: the tool's rc), M8p (P2-07 e: the .prefilter's floor), M1d (P2-07 g: the .prefilter
    against an md5 taken after rwin), M6b (P2-07 a: G4's 1e-4 clause), M11b (P2-07 b: G1c.8's pixel and ratio rules), M94b
    (P2-08: the hooks ignored under the package's own table)."""
    run, rec, gates, gval, slc, fd = H['run'], H['rec'], H['gates'], H['gval'], H['slc'], H['fd']
    print('-- v0.13 part 2 review: bandlimit\'s resume and redo, its dry run, a one-mode frame\'s traces, hard links, the '
          'tool\'s rc, the .prefilter\'s floor, G4\'s 1e-4 clause, G1c.8\'s pixel and ratio, the hooks\' guard')
    d0 = FBS[0]
    prog = lambda root: [json.loads(ln) for ln in open(os.path.join(fd(root), 'status', 'P1bs_bandlimit.progress'))] \
        if os.path.isfile(os.path.join(fd(root), 'status', 'P1bs_bandlimit.progress')) else []  # noqa: E731
    # M8h (P2-01): E64's keep fraction caught, the package's put back: the stopped date resumes at today's settings
    e64 = os.path.join(T, 'cfg', 'mixed_e64r.cfg')
    with open(e64, 'w') as fh:
        fh.write(mcfg.replace('KEEP_FRACTION=0.4375', 'KEEP_FRACTION=0.875'))
    rc0, _ = run('mxe', ['--to', 'rwin'])
    rc1, _ = run('mxe', ['--to', 'bandlimit'], extra={'LINOG_MIXED_CFG': e64})
    b1 = rec('mxe', '1bs', 'bandlimit')
    rc2, _ = run('mxe', V)
    b2 = rec('mxe', '1bs', 'bandlimit')
    pg = prog('mxe')
    st0 = [x for x in pg if x['date'] == d0 and x['event'] == 'started']
    dn0 = [x for x in pg if x['date'] == d0 and x['event'] == 'done']
    act = dict((x['date'], x['action']) for x in (b2.get('outputs') or {}).get('fbs') or [])
    case('M8h (the part 2 review\'s P2-01) keep_fraction 0.875 (E64) stops the first FBS date at G1bl.6 and G1bl.7 (rc 2); with '
         'the package\'s linog_mixed.cfg back the date resumes from its .prefilter (the unpacked file) under a new started line at '
         'today\'s settings, and the frame PASSes at 0.4375 (rc 0)',
         rc0 == 0 and rc1 == 2 and sorted(g for g, v in gates(b1).items() if v == 'FAIL') == ['G1bl.6', 'G1bl.7'] and rc2 == 0
         and act.get(d0) == 'resumed' and len(st0) == 2 and st0[0]['settings']['KEEP_FRACTION'] == '0.875'
         and st0[1]['settings']['KEEP_FRACTION'] == '0.4375' and st0[1].get('resumed_from', {}).get('KEEP_FRACTION') == '0.875'
         and len(dn0) == 1 and dn0[0]['settings']['KEEP_FRACTION'] == '0.4375' and gates(b2).get('G1bl.6') == 'PASS',
         'rc %d, %d, %d; fails %s; action %s; started %s; done %s' % (
             rc0, rc1, rc2, sorted(g for g, v in gates(b1).items() if v == 'FAIL'), act.get(d0),
             [x['settings']['KEEP_FRACTION'] for x in st0], [x['settings']['KEEP_FRACTION'] for x in dn0]))
    # M8i (P2-03): a done date's folder moved whole into _archive/: unpack makes it again, bandlimit band-limits it anew
    d5 = FBS[5]
    S.aside(T, os.path.join(fd('mxe'), 'SLC', d5), 'M8i')
    rc3, out3 = run('mxe', V)
    b3 = rec('mxe', '1bs', 'bandlimit')
    a3 = dict((x['date'], x['action']) for x in (b3.get('outputs') or {}).get('fbs') or [])
    redo = [x for x in prog('mxe') if x['date'] == d5 and x['event'] == 'started' and x.get('redo')]
    case('M8i (P2-03) a done FBS date\'s folder moved whole into _archive/ (a person\'s redo): unpack makes it again, bandlimit sees '
         'its .slc the unpacked file and no .prefilter, and band-limits it anew (a started line marked redo); verify PASS',
         rc3 == 0 and a3.get(d5) == 'done' and len(redo) == 1 and (rec('mxe', '1b', 'unpack').get('outputs') or {}).get('unpacked') == 1
         and rec('mxe', '1c', 'verify').get('verdict') == 'PASS' and 'anew after a new unpack' in gval(b3, 'G1bl.3'),
         'rc %d; action %s; redo lines %d; G1bl.3 %s' % (rc3, a3.get(d5), len(redo), gval(b3, 'G1bl.3')[:90]))
    # M8p (P2-07 e): the progress file and the .prefilters moved aside after a PASS: the filtered .slc copied as the .prefilter
    S.aside(T, os.path.join(fd('mxe'), 'status', 'P1bs_bandlimit.progress'), 'M8p')
    for d in FBS:
        S.aside(T, slc('mxe', d) + '.prefilter', 'M8p')
    rc4, _ = run('mxe', ['--to', 'bandlimit'])
    b4 = rec('mxe', '1bs', 'bandlimit')
    case('M8p (P2-07 e) a band-limited frame whose progress file and .prefilters are moved aside: the tool copies a filtered .slc as '
         'the .prefilter, so G1bl.6 FAILs on the .prefilter\'s floor (< 0.40 above 7 MHz), rc 2',
         rc4 == 2 and gates(b4).get('G1bl.6') == 'FAIL' and 'in the .prefilter' in gval(b4, 'G1bl.6')
         and float(gval(b4, 'G1bl.6').split(' in the .slc, ')[1].split(' ')[0]) < 0.40,
         'rc %d; %s' % (rc4, gval(b4, 'G1bl.6')[:120]))
    # M8j (P2-04): a dry run on a frame through rwin reads rwin's sampling rates
    rc5, _ = run('mxj', ['--to', 'rwin'])
    dj = os.path.join(T, 'dry_m8j')
    f0 = sorted(os.path.relpath(os.path.join(dp, n), fd('mxj')) for dp, _, ns in os.walk(fd('mxj')) for n in ns)
    rc6, _ = run('mxj', ['--dry-run', dj] + V)
    bj = json.load(open(os.path.join(dj, 'status', 'P1bs_bandlimit.json'))) if os.path.isfile(os.path.join(dj, 'status', 'P1bs_bandlimit.json')) else {}
    f1 = sorted(os.path.relpath(os.path.join(dp, n), fd('mxj')) for dp, _, ns in os.walk(fd('mxj')) for n in ns)
    case('M8j (P2-04, P2-07 f) a dry run with the 8 FBS dates to do, on a frame through rwin: bandlimit\'s plan PASS, its G1bl.1 '
         'reading every date\'s mode against rwin\'s sampling rates (from rwin\'s dry rows), 8 planned; the frame unchanged',
         rc5 == 0 and rc6 == 0 and bj.get('verdict') == 'PASS' and 'every mode the one its leader' in gval(bj, 'G1bl.1')
         and len((bj.get('outputs') or {}).get('planned') or []) == 8 and f0 == f1,
         'rc %d, %d; %s; planned %d; files %d -> %d' % (rc5, rc6, gval(bj, 'G1bl.1')[:90],
                                                       len((bj.get('outputs') or {}).get('planned') or []), len(f0), len(f1)))
    # M8n (P2-07 c), M8m (P2-09), M8l (P2-06), M8o (P2-07 d) on the fresh frame through rwin
    H['restore']('mxd', 'rwin', 'm8n')
    pf = slc('mxd', FBDD[0]) + '.prefilter'
    shutil.copy2(slc('mxd', FBDD[0]), pf)
    rc7, _ = run('mxd', ['--to', 'bandlimit'])
    b7 = rec('mxd', '1bs', 'bandlimit')
    S.aside(T, pf, 'M8n')
    hl = slc('mxd', d0) + '.hardlink_m8m'
    os.link(slc('mxd', d0), hl)
    rc8, _ = run('mxd', ['--to', 'bandlimit'])
    b8 = rec('mxd', '1bs', 'bandlimit')
    shutil.copy2(slc('mxd', d0), slc('mxd', d0) + '.m8m_copy')   # the .slc as a file of its own again (its link count 1),
    os.replace(slc('mxd', d0) + '.m8m_copy', slc('mxd', d0))      # the other link moved aside: the self-test never deletes
    S.aside(T, hl, 'M8m')
    np8 = not os.path.isfile(os.path.join(fd('mxd'), 'status', 'P1bs_bandlimit.progress'))
    case('M8n (P2-07 c) a .prefilter beside an FBD date before bandlimit\'s first run: G1bl.3 DECISION naming it (rc 4); M8m (P2-09) '
         'an FBS .slc with a second hard link: G1bl.3 DECISION naming it (the tool writes in place), nothing called',
         rc7 == 4 and gates(b7).get('G1bl.3') == 'DECISION' and ('%s: a .prefilter beside an FBD date' % FBDD[0]) in gval(b7, 'G1bl.3')
         and rc8 == 4 and gates(b8).get('G1bl.3') == 'DECISION' and ('%s: %s.slc has 2 hard links' % (d0, d0)) in gval(b8, 'G1bl.3')
         and np8,
         'rc %d %s; rc %d %s' % (rc7, gval(b7, 'G1bl.3')[:80], rc8, gval(b8, 'G1bl.3')[:80]))
    # M8l (P2-06): stopped after the copy; the .slc still the unpacked file, a full-size .prefilter that is not
    rc9, _ = run('mxd', ['--to', 'bandlimit'], extra={'LINOG_MOCK_BL_KILL': '%s:after' % d0})
    keep = os.path.join(T, '_archive', 'M8l_unpacked.slc')
    shutil.copy2(slc('mxd', d0) + '.prefilter', keep)
    p = subprocess.run([S.MOCKPY[0], '-B', os.path.join(T, 'kit', 'linog_fbs_bandlimit.py'), 'SLC', '--keep-fraction', '0.4375',
                        '--taper-width', '0.05', '--dates', d0], cwd=fd('mxd'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shutil.copyfile(slc('mxd', d0), slc('mxd', d0) + '.prefilter')
    shutil.copyfile(keep, slc('mxd', d0))
    rc10, _ = run('mxd', ['--to', 'bandlimit', '--recover'])
    b10 = rec('mxd', '1bs', 'bandlimit')
    case('M8l (P2-06, M8b\'s literal case) stopped after the copy, then the .prefilter replaced by a filtered copy of full size while '
         'the .slc is the unpacked file: G1bl.4 DECISION naming it (not taken for a partial copy), rc 4',
         rc9 == 137 and p.returncode == 0 and rc10 == 4 and gates(b10).get('G1bl.4') == 'DECISION'
         and 'a full-size .prefilter beside it is not' in gval(b10, 'G1bl.4') and d0 in gval(b10, 'G1bl.4'),
         'rc %d, tool %d, %d; %s' % (rc9, p.returncode, rc10, gval(b10, 'G1bl.4')[:110]))
    # M8o (P2-07 d): a kit tool at a new pin that exits 1
    H['restore']('mxd', 'rwin', 'm8o')
    kb3 = os.path.join(T, 'kit_bl3')
    shutil.copytree(os.path.join(T, 'kit'), kb3)
    src = open(os.path.join(kb3, 'linog_fbs_bandlimit.py')).read()
    with open(os.path.join(kb3, 'linog_fbs_bandlimit.py'), 'w') as fh:
        fh.write('import sys\nprint("self-test M8o: the tool fails")\nsys.exit(1)\n' + src)
    ecfg = open(os.path.join(T, 'cfg', 'env_mock.cfg')).read()
    with open(os.path.join(T, 'cfg', 'env_kitbl3.cfg'), 'w') as fh:
        fh.write('\n'.join(('KIT=%s' % kb3) if ln.startswith('KIT=') else ln for ln in ecfg.splitlines()) + '\n')
    m3 = os.path.join(T, 'cfg', 'mixed_bl3.cfg')
    with open(m3, 'w') as fh:
        fh.write(mcfg.replace('KIT_FBS_BANDLIMIT_MD5=%s' % mreal['KIT_FBS_BANDLIMIT_MD5'],
                              'KIT_FBS_BANDLIMIT_MD5=%s' % md5(os.path.join(kb3, 'linog_fbs_bandlimit.py'))))
    rc11, _ = run('mxd', ['--only', 'bandlimit', '--force', 'bandlimit'], envcfg='env_kitbl3.cfg', extra={'LINOG_MIXED_CFG': m3})
    b11 = rec('mxd', '1bs', 'bandlimit')
    rc12, _ = run('mxd', V)
    a12 = dict((x['date'], x['action']) for x in (rec('mxd', '1bs', 'bandlimit').get('outputs') or {}).get('fbs') or [])
    case('M8o (P2-07 d) the kit tool at a new pin exits 1: G1bl.10 FAIL naming the date and the rc (rc 2); the package\'s kit back: '
         'the date resumes under today\'s pins (P2-01) and the frame PASSes',
         rc11 == 2 and gates(b11).get('G1bl.10') == 'FAIL' and ('%s: the tool rc 1' % d0) in gval(b11, 'G1bl.10')
         and rc12 == 0 and a12.get(d0) == 'resumed',
         'rc %d %s; then rc %d, %s' % (rc11, gval(b11, 'G1bl.10')[:80], rc12, a12.get(d0)))
    # M8k (P2-05): band-limit traces on a one-mode frame (frame 3350 with every date FBS)
    afs = H['variant']('fbs12', dict((i, {}) for i in range(12)), fbd=())
    rc13, _ = run('fbs12', ['--to', 'rwin'], archive=afs)
    pk = slc('fbs12', D[3]) + '.prefilter'
    shutil.copy2(slc('fbs12', D[3]), pk)
    rc14, _ = run('fbs12', ['--to', 'bandlimit'], archive=afs)
    b14 = rec('fbs12', '1bs', 'bandlimit')
    S.aside(T, pk, 'M8k')
    rc15, _ = run('fbs12', ['--to', 'bandlimit'], archive=afs)
    b15 = rec('fbs12', '1bs', 'bandlimit')
    case('M8k (P2-05) an FBS-only frame with a .prefilter beside one date: G1bl.3 DECISION naming it (a frame band-limited once), '
         'not N/A; moved away: N/A, rc 0',
         rc13 == 0 and rc14 == 4 and gates(b14).get('G1bl.3') == 'DECISION' and D[3] in gval(b14, 'G1bl.3')
         and rc15 == 0 and gates(b15).get('G1bl.0') == 'N/A',
         'rc %d, %d (%s), %d (%s)' % (rc13, rc14, gval(b14, 'G1bl.3')[:70], rc15, gates(b15).get('G1bl.0')))
    # M1d (P2-07 g): each .prefilter against an md5 taken after rwin, before bandlimit
    rc16, _ = run('mxg', ['--to', 'rwin'])
    m_rw = dict((d, md5(slc('mxg', d))) for d in FBS)
    rc17, _ = run('mxg', V)
    same = [d for d in FBS if md5(slc('mxg', d) + '.prefilter') == m_rw[d]]
    case('M1d (P2-07 g) every .prefilter equals the .slc as rwin left it, by an md5 this case takes before bandlimit (not the '
         'phase\'s own started lines)', rc16 == 0 and rc17 == 0 and len(same) == 8, 'rc %d, %d; %d of 8' % (rc16, rc17, len(same)))
    # M6b (P2-07 a): an FBD date's samples times 1.001: nearer IMG-HH, but beyond 1e-4 of it
    rc18, _ = run('mx6b', V, extra={'LINOG_MOCK_SCALE': '%s:1.001' % FBDD[2]})
    v18 = rec('mx6b', '1c', 'verify')
    case('M6b (P2-07 a) an FBD date\'s SLC 1.001 times IMG-HH: nearer IMG-HH than IMG-HV, but not within 1e-4 of it: G4 FAIL naming '
         'the date, rc 2', rc18 == 2 and gates(v18).get('G4') == 'FAIL' and FBDD[2] in gval(v18, 'G4'),
         'rc %d; %s' % (rc18, gval(v18, 'G4')[:140]))
    # M11b (P2-07 b): one pixel 2e-6 m off; every FBS pixel 5e-7 m high (each inside 1e-6 m, the ratio off by 2.1e-7)
    rc19, _ = run('mx11b', V, extra={'LINOG_MOCK_SLR': '%s:2e-6' % FBDD[3]})
    v19 = rec('mx11b', '1c', 'verify')
    rc20, _ = run('mx11c', V, extra={'LINOG_MOCK_SLR': 'FBS:5e-7'})
    v20 = rec('mx11c', '1c', 'verify')
    case('M11b (P2-07 b) one FBD shelve\'s pixel 2e-6 m beyond c / (2 fs): G1c.8 FAIL naming it; every FBS pixel 5e-7 m high (inside '
         'the pixel rule\'s 1e-6 m): G1c.8 FAIL on SLR(FBD) / SLR(FBS) off 2 by 2.1e-7 (beyond 1e-7); each rc 2',
         rc19 == 2 and gates(v19).get('G1c.8') == 'FAIL' and FBDD[3] in gval(v19, 'G1c.8') and 'pixel' in gval(v19, 'G1c.8')
         and rc20 == 2 and gates(v20).get('G1c.8') == 'FAIL' and 'SLR(FBD) / SLR(FBS) = 1.99999978' in gval(v20, 'G1c.8')
         and 'pixel' not in gval(v20, 'G1c.8').split('SLR(FBD)')[0],
         'rc %d %s; rc %d %s' % (rc19, gval(v19, 'G1c.8')[-90:], rc20, gval(v20, 'G1c.8')[-90:]))
    # M94b (P2-08): the hooks act only under a path table other than the package's own
    HERE = S.HERE
    code = 'import sys; sys.path.insert(0, sys.argv[1]); import lp_common as C; print(C.selftest_hooks())'
    outs = []
    for cfgv in (None, os.path.join(HERE, 'linog_paths.cfg'), os.path.join(T, 'cfg', 'paths.cfg')):
        e = dict((k, v) for k, v in os.environ.items() if k != 'LINOG_AUTO_CFG')
        if cfgv:
            e['LINOG_AUTO_CFG'] = cfgv
        outs.append(subprocess.run(['python3', '-E', '-B', '-c', code, HERE], env=e, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT).stdout.decode().strip())
    e = dict((k, v) for k, v in os.environ.items() if k != 'LINOG_AUTO_CFG')
    e.update(LINOG_AUTO_CFG=os.path.join(HERE, 'linog_paths.cfg'), LINOG_MOCK_BL_TWICE=d0)
    ign = subprocess.run(['python3', '-E', '-B', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import lp_common as C; '
                          'print(C.selftest_hook("LINOG_MOCK_BL_TWICE"))', HERE], env=e, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout.decode()
    case('M94b (P2-08) the self-test\'s data-writing hooks act only under a path table other than the package\'s own: '
         'selftest_hooks() False with no LINOG_AUTO_CFG and with the package\'s linog_paths.cfg, True with the self-test\'s; '
         'a hook set under the package\'s table is ignored and says so',
         outs == ['False', 'False', 'True'] and 'ignored' in ign and ign.strip().endswith('None'),
         '%s; %s' % (outs, ign.strip().replace('\n', ' | ')[:120]))
