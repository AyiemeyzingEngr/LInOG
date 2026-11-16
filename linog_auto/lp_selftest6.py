#!/usr/bin/env python3
"""lp_selftest6.py -- the Phase 5e and 6 cases of the linog_auto self-test (v0.7: wmask, deliver, accept, package; v0.8:
d9ab, D9's A/B after sbas, and RUN_MANIFEST.json's new fields), called by lp_selftest.py after the Phase 4.5 and 5 cases,
on their frame (p3: four dates, 6 pairs, the multilooked grid 83 x 658), put back to the copy kept after T100's run to
sbas (S5d); the files under mintpy/ are copied, never linked, since the kit's tools write some of them in place.

The kit's linog_watermask.py (907cf856), linog_phase6.sh (43d6c15b), linog_los2hv.py (ada17e14), linog_embed_stats.py
(c35e935a) and linog_gen_interactive_kmz.py (45dc2d01) run as felix pins them, and so does the pipeline's verifier copy.
MintPy and GDAL are mocks (selftest_kit/mock_mintpy, mock_isce/osgeo, linog_mock6): mintpy.utils.readfile and writefile,
`python -m mintpy.cli.geocode` (nearest neighbour through the geometry, --update as MintPy's run_or_skip decides it),
dem_error.py, remove_ramp.py, timeseries2velocity.py, save_kmz.py, save_gdal.py (a mock GeoTIFF), gdal_edit.py, view.py
and gdalinfo. The frame's ground is the mock's scene (linog_mock3.scene): a sea flat at 44 m in the south-east corner,
half of it decorrelated, a bright pier, and a dark strip along the near-range edge. Planted: LINOG_MOCK_GEOCODE_NOUPDATE,
LINOG_MOCK_P6FAIL, LINOG_MOCK_AUX, LINOG_MOCK_GDALINFO_FAIL, and linog_phase6.cfg copies with a pin or a name changed;
v0.8: LINOG_MOCK_B_GAIN, LINOG_MOCK_B_VSTD, LINOG_MOCK_SBASFAIL and LINOG_MOCK_P6SLEEP=smallbaselineApp in MintPy's run
on the A/B's copy (the mock smallbaselineApp.py), and a linog_phase6.cfg copy with GNSS stations in and out of the grid.
The HDF5 and GeoTIFF checks run in the mock env's Python; this module needs the standard library only.
v0.10: dfit (R4) between wmask and deliver, in every list of these phases (T125 its gates and deliver's G6a.1f; T126 28
phases; the dry runs); RUN_MANIFEST.json and deliver's record v0.10, LOGIC 4 (T167; v0.11: v0.11, LOGIC 5, and the phase rerun
after package, so a run with no --to ends there and T126 and T153 count 29 and 28 phases; v0.12: drop1 after sbas, 30 and 29, deliver
v0.12, LOGIC 6); d9ab's bridging under --decide auto is
R5's (T146r: the frame restarted once and run with bridging), so T146 and T146c's first run are under --decide ask, and
T146s runs --only d9ab under auto (no restart there: a DECISION); T146d the same A/B in a dry run (nothing moved), T146e a
decision file taken on another network (D9 WARN), T146f R5 unable to make _archive/ (G5dab.10 FAIL, nothing moved).
v0.12 r2 (record 127): T149k, SIGKILL to d9ab alone while MintPy runs on B: MintPy on B ends with it (record 77.12's [VERIFY]).
v0.13 r2 (the ascending record 15.4's M61): T167 reads deliver's record and RUN_MANIFEST.json's label as v0.13 r2 (G6a.11's
reading names its release), LOGIC still 6; G6a.11 reads N/A on this FBS-only frame (T125's list leaves it out).
"""
import glob
import json
import math
import os
import re
import shutil
import signal
import socket
import subprocess
import time

ROOT, FRAME, TAG = 'p3', '3320', 'P084F3320'
P6PH = (('5dab', 'd9ab'), ('5e', 'wmask'), ('5f', 'dfit'), ('6a', 'deliver'), ('6b', 'accept'), ('6c', 'package'))
MIN_GAIN = 164   # ceil(min(2500, 0.003 x 83 x 658)): the rule's (b) on the mock grid
KIT6 = (('linog_watermask.py', 'KIT_WATERMASK_MD5'), ('linog_phase6.sh', 'KIT_PHASE6_MD5'), ('linog_los2hv.py', 'KIT_LOS2HV_MD5'),
        ('linog_embed_stats.py', 'KIT_EMBED_MD5'), ('linog_gen_interactive_kmz.py', 'KIT_KMZ_MD5'), ('linog_verify_frame.py', 'KIT_VERIFY_MD5'))
PROBE = r'''
import json, sys, zipfile
what, args = sys.argv[1], sys.argv[2:]
if what == 'h5attrs':
    import h5py
    with h5py.File(args[0], 'r') as f:
        d = {k: (v.decode() if isinstance(v, bytes) else str(v)) for k, v in f.attrs.items() if k in args[1:]}
    print(json.dumps(d))
elif what == 'h5count':   # nonzero values of a dataset
    import h5py, numpy as np
    with h5py.File(args[0], 'r') as f:
        print(json.dumps(dict(n=int(np.count_nonzero(f[args[1]][()])), shape=list(f[args[1]].shape))))
elif what == 'tiff':
    import numpy as np, linog_mock6 as M6
    out = {}
    for p in args:
        h, a = M6.read_tiff(p)
        out[p.rsplit('/', 1)[-1]] = dict(nodata=h.get('nodata'), mean=(h.get('metadata') or {}).get('STATISTICS_MEAN'),
                                         finite=int(np.isfinite(a).sum()), shape=list(a.shape))
    print(json.dumps(out))
elif what == 'rings':   # v0.8: around20.py's formula, apart from lp_deliver: cells and medians (mm/yr) per ring, and the reference's cell
    import math, numpy as np, linog_mock6 as M6
    h, a = M6.read_tiff(args[0])
    lat0, lon0 = float(args[1]), float(args[2])
    edges = [float(x) for x in args[3].split(',')]
    gt = h['geotransform']
    H, W = a.shape
    rr, cc = np.mgrid[0:H, 0:W]
    latc = gt[3] + (rr + 0.5) * gt[5]
    lonc = gt[0] + (cc + 0.5) * gt[1]
    d = np.hypot((latc - lat0) * 111.32, (lonc - lon0) * 111.32 * math.cos(math.radians(lat0)))
    ok = np.isfinite(a)
    sels = [ok & (d >= lo) & (d < hi) for lo, hi in zip(edges[:-1], edges[1:])] + [ok]
    cy, cx = int((lat0 - gt[3]) / gt[5]), int((lon0 - gt[0]) / gt[1])
    disc = None
    if len(args) >= 7:   # a station and a radius: the disc's cells and median around it and around the reference (refcheck's disc)
        la, lo, r = float(args[4]), float(args[5]), float(args[6])
        ds = np.hypot((latc - la) * 111.32, (lonc - lo) * 111.32 * math.cos(math.radians(la)))
        s_, r_ = ok & (ds < r), ok & (d < r)
        disc = [int(s_.sum()), float(np.median(a[s_].astype('f8') * 1e3)) if s_.any() else None, int(r_.sum()),
                float(np.median(a[r_].astype('f8') * 1e3)) if r_.any() else None]
    print(json.dumps(dict(cells=[int(x.sum()) for x in sels], medians=[float(np.median(a[x].astype('f8') * 1e3)) if x.any() else None
                                                                        for x in sels],
                          cell=[cy, cx], value=float(a[cy, cx]) * 1e3 if 0 <= cy < H and 0 <= cx < W and np.isfinite(a[cy, cx]) else None,
                          disc=disc)))
elif what == 'kmz':
    z = zipfile.ZipFile(args[0])
    kml = z.read('doc.kml').decode()
    print(json.dumps(dict(names=z.namelist(), placemarks=kml.count('<Placemark>'))))
'''


def phase6(T, case, S):
    import lp_selftest34 as S34
    W = S.fdir(T, FRAME, ROOT)
    E = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MINTPY_CFG': os.path.join(T, 'cfg', 'mintpy_mock.cfg')}   # v0.10: the mock floor
    q = S.real_pins('linog_phase6.cfg')
    py = S.MOCKPY[0]
    site = os.path.join(T, 'mockconda', 'envs', 'linog_isce2', 'lib', 'site-packages')

    def run(args, extra=None, decide='auto'):
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p3.cfg', env_extra=dict(E, **(extra or {})), keep_default=True)

    def rec(idx, ph):
        return S.rec(T, FRAME, idx, ph, ROOT)

    def recs():
        return dict((ph, rec(i, ph)) for i, ph in P6PH)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def val(r, gid):
        return dict((x['id'], x.get('value', '')) for x in r.get('gates', [])).get(gid, '')

    def note(r, gid):
        return dict((x['id'], x.get('note', '')) for x in r.get('gates', [])).get(gid, '')

    def copy_fn(src, dst):   # the kit's tools write some of mintpy/'s files in place: those are always copies
        if os.path.getsize(src) > (1 << 20) and '%smintpy%s' % (os.sep, os.sep) not in src:
            os.link(src, dst)
        else:
            shutil.copy2(src, dst)

    def restore(tag):
        S.aside(T, W, 'p6_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', 'S5d'), W, symlinks=True, copy_function=copy_fn)

    def probe(*args):
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': site}
        p = subprocess.run([py, '-B', '-c', PROBE] + [str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        try:
            return json.loads(p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': p.stdout.decode('utf-8', 'replace')[-300:]}

    def listing(d):
        out = []
        for dp, dn, fn in os.walk(d):
            dn.sort()
            for n in sorted(fn):
                qq = os.path.join(dp, n)
                st = os.lstat(qq)
                out.append((os.path.relpath(qq, d), st.st_size, st.st_mtime_ns))
        return out

    def p6_copy(name, key, value):
        src = os.path.join(S.HERE, 'linog_phase6.cfg')
        dst = os.path.join(T, 'cfg', name)
        n = 0
        with open(dst, 'w') as fh:
            for ln in open(src):
                if ln.startswith(key + '='):
                    ln, n = '%s=%s\n' % (key, value), n + 1
                fh.write(ln)
        assert n == 1, (key, n)
        return dst

    def md5s(*paths):
        return [S34.md5q(p) for p in paths]

    def m_copy(name, key, value):
        src = os.path.join(T, 'cfg', 'mintpy_mock.cfg')   # v0.10: the mock floor kept
        dst = os.path.join(T, 'cfg', name)
        n = 0
        with open(dst, 'w') as fh:
            for ln in open(src):
                if ln.startswith(key + '='):
                    ln, n = '%s=%s\n' % (key, value), n + 1
                fh.write(ln)
        assert n == 1, (key, n)
        return dst

    def cfgv6(path):
        d = {}
        for ln in open(path) if os.path.isfile(path) else []:
            mm = re.match(r'^\s*([A-Za-z][\w.]*)\s*=\s*([^#]*?)\s*(#.*)?$', ln)
            if mm:
                d[mm.group(1)] = mm.group(2)
        return d

    def stopped(args, extra, mark, sig=signal.SIGTERM):
        """A run started in a session of its own whose planted mock command writes mark and sleeps; sig to the run's
        process group once mark exists (the kit's commands in a session of their own do not get it); wait."""
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM') and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p3.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_MOCK_MARK=mark, **dict(E, **extra))
        p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', 'auto'] + args, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 300:
            time.sleep(0.2)
        time.sleep(0.5)
        if p.poll() is None:
            os.killpg(p.pid, sig)
        out = p.communicate(timeout=300)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 %s --decide auto %s  (%s, signal %d after %.1f s)  rc %d\n%s' % (
                FRAME, ' '.join(args), ' '.join('%s=%s' % kv for kv in sorted(extra.items())), sig, time.time() - t0, p.returncode, out))
        return p.returncode, out

    def ppid_of(pid):
        try:
            return int(open('/proc/%d/stat' % int(pid)).read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return 0

    def running(pid):   # a zombie has ended
        try:
            return open('/proc/%d/stat' % int(pid)).read().rsplit(')', 1)[1].split()[0] not in ('Z', 'X')
        except (OSError, ValueError, IndexError):
            return False

    def killed9(args, extra, mark):
        """v0.12 r2 (record 77.12's [VERIFY]): as stopped(), but once the planted mock MintPy on B has written mark, SIGKILL to
        d9ab's own process (the mock's parent, checked by its command line), never to the run's group; then whether the mock
        still runs 15 s later. Returns rc, the console, and dict(mock, d9ab, killed, mock_alive, seconds)."""
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM') and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p3.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_MOCK_MARK=mark, **dict(E, **extra))
        if os.path.exists(mark):   # a mark left by an earlier run of the same tree would name a process long gone
            os.remove(mark)
        p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', 'auto'] + args, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 300:
            time.sleep(0.2)
        time.sleep(1.0)
        info = dict(killed=False)
        if os.path.exists(mark) and p.poll() is None:
            m = re.search(r'pid (\d+)', open(mark).read())
            mpid = int(m.group(1)) if m else 0
            dpid = ppid_of(mpid) if mpid else 0
            try:
                dcmd = open('/proc/%d/cmdline' % dpid, 'rb').read().replace(b'\0', b' ').decode('utf-8', 'replace') if dpid else ''
            except OSError:
                dcmd = ''
            info.update(mock=mpid, d9ab=dpid, d9ab_cmd=dcmd[-60:])
            if dpid and 'lp_d9ab.py' in dcmd:
                os.kill(dpid, signal.SIGKILL)
                t1 = time.time()
                while running(mpid) and time.time() - t1 < 15:
                    time.sleep(0.2)
                info.update(killed=True, mock_alive=running(mpid), seconds=round(time.time() - t1, 1))
        out = p.communicate(timeout=300)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 %s --decide auto %s  (%s; SIGKILL to d9ab: %s)  rc %d\n%s' % (
                FRAME, ' '.join(args), ' '.join('%s=%s' % kv for kv in sorted(extra.items())), info, p.returncode, out))
        return p.returncode, out, info

    print('-- Phases 5e and 6 (wmask, deliver, accept, package): the kit\'s linog_watermask.py, linog_phase6.sh and its three '
          'tools, the pipeline\'s verifier copy; a mock MintPy and GDAL; the Phase 5 frame after sbas (83 x 658, the mock\'s scene)')
    same = [n for n, k in KIT6 if S.md5(os.path.join(S.KITSRC, 'kit3', n)) == q.get(k)]
    case('T124 the self-test runs the kit\'s Phase 5e and 6 tools and its verifier as felix pins them (md5s = linog_phase6.cfg), and '
         'the verifier copy is the package\'s', len(same) == len(KIT6) and os.path.isfile(os.path.join(S.HERE, q.get('VERIFY_COPY', '-'))),
         '%d of %d; copy %s' % (len(same), len(KIT6), q.get('VERIFY_COPY')))
    if not os.path.isdir(os.path.join(T, 'snap_p3', 'S5d')):
        case('T125-T153b not run: no copy of the frame after sbas (the Phase 4.5 and 5 cases stopped early)', False)
        return

    # ---- clean: the frame after sbas, with no --to (v0.7 to v0.10's default: package; v0.11's: rerun, a first run here)
    restore('T125')
    rc, out = run([])
    R = recs()
    g = {}
    for r in R.values():
        g.update(gates(r))
    want = ('G5dab.1', 'G5dab.1j', 'G5dab.2', 'G5dab.2m', 'G5dab.3', 'G5dab.4', 'G5dab.5', 'G5dab.6', 'G5dab.7', 'G5dab.8',
            'G5dab.9', 'D9ab', 'G5e.1', 'G5e.1d', 'G5e.2', 'G5e.2m', 'G5e.2s', 'G5e.3', 'G5e.4', 'G5e.5', 'G22', 'G5e.6', 'G5e.7', 'G5e.8', 'G5e.9',
            'G5f.1', 'G5f.1j', 'G5f.2', 'G5f.3', 'G5f.4', 'G5f.6', 'G5f.7',
            'G6a.1', 'G6a.1r', 'G6a.1f', 'G6a.2m', 'G6a.3', 'G6a.3c', 'G6a.4', 'G6a.5', 'G6a.6', 'G6a.8', 'N6', 'N44', 'G22d', 'D5', 'D7', 'G6a.7',
            'G6b.1', 'G6b.2m', 'G6b.3', 'G6b.3k', 'G6b.3c', 'G6b.4', 'G6b.5', 'G6b.6', 'G6b.8',
            'G6c.1', 'G6c.1d', 'G6c.1r', 'G6c.2', 'G6c.3', 'G6c.4', 'G6c.5', 'G6c.6')
    wrong = dict((k, g.get(k)) for k in want if g.get(k) != 'PASS')
    case('T125 clean, the frame after sbas with no --to (v0.11\'s default: rerun, a first run here): rc 0; 23 phases skipped (v0.13: bandlimit among them); d9ab, wmask, dfit, deliver, accept '
         'and package PASS; %d gates PASS (v0.10: dfit\'s, with no screened date: A alone, equal to velocity.h5; deliver\'s G6a.1f), G23 '
         'and G6b.7 PASS or WARN, G6a.9 (the readings) and G5f.5 (no candidate) INFO' % len(want),
         rc == 0 and out.count('skip: PASS on record') == 23 and all(R[ph].get('verdict') == 'PASS' for ph in R) and not wrong
         and g.get('G23') in ('PASS', 'WARN') and g.get('G6b.7') in ('PASS', 'WARN') and g.get('G6a.9') == 'INFO' and g.get('G5f.5') == 'INFO'
         and (R['dfit'].get('outputs') or {}).get('candidates') == [] and ((R['dfit'].get('outputs') or {}).get('a_mirror') or {}).get('equal') is True,
         'rc %d; %d skipped; %s; not PASS: %s; G23 %s, G6b.7 %s, G6a.9 %s' % (rc, out.count('skip: PASS on record'), [
             (ph, R[ph].get('verdict')) for ph in R], wrong, g.get('G23'), g.get('G6b.7'), g.get('G6a.9')))
    o9 = R['d9ab'].get('outputs') or {}
    res = o9.get('result') or {}
    fd = os.path.join(W, o9.get('folder') or '-')
    ab = json.load(open(os.path.join(fd, 'ab.json'))) if os.path.isfile(os.path.join(fd, 'ab.json')) else {}
    tb = cfgv6(os.path.join(fd, 'B', 'mintpy', 'smallbaselineApp.cfg'))
    case('T125f d9ab on the clean frame (the mock\'s bridging leaves the stack as it is): B in d9ab/<UTC>/B/mintpy/ with the five copies '
         'equal to A\'s and bridging, ramp linear and plot no in its template; MintPy on B rc 0 through its 12 steps; the rule no (gain 0, '
         '%d px asked; std 0 = 0), compared; ab.json complete with its key, ab_pairs.tsv; A\'s mintpy/ unchanged; D9ab PASS' % MIN_GAIN,
         res.get('verdict') == 'no' and res.get('compared') is True and res.get('gain') == 0 and res.get('min_gain') == MIN_GAIN
         and res.get('brc') == 0 and ab.get('complete') is True and ab.get('key') == o9.get('key') and os.path.isfile(os.path.join(fd, 'ab_pairs.tsv'))
         and all(os.path.isfile(os.path.join(fd, 'B', 'mintpy', x)) for x in ('inputs/ifgramStack.h5', 'inputs/geometryRadar.h5', 'avgSpatialCoh.h5',
                                                                                'maskConnComp.h5', 'maskTempCoh.h5', 'velocity.h5'))
         and tb.get('mintpy.unwrapError.method') == 'bridging' and tb.get('mintpy.unwrapError.ramp') == 'linear' and tb.get('mintpy.plot') == 'no'
         and 'rc 0' in val(R['d9ab'], 'G5dab.7') and gates(R['d9ab']).get('G5dab.9') == 'PASS' and o9.get('reused') is False
         and 'unchanged' in val(R['d9ab'], 'G5dab.9') and 'the rule: no' in val(R['d9ab'], 'D9ab'),
         'result %s; folder %s; ab.json complete %s; B template %s; G5dab.7 %s; G5dab.9 %s' % (
             dict((k, res.get(k)) for k in ('verdict', 'compared', 'gain', 'min_gain', 'brc', 'std_common_a', 'std_common_b')), o9.get('folder'),
             ab.get('complete'), [tb.get(k) for k, _ in (('mintpy.unwrapError.method', 0), ('mintpy.unwrapError.ramp', 0), ('mintpy.plot', 0))],
             val(R['d9ab'], 'G5dab.7')[:80], val(R['d9ab'], 'G5dab.9')))
    sj = os.path.join(W, 'mintpy', 'watermask', 'summary.json')
    sm = json.load(open(sj)) if os.path.isfile(sj) else {}
    rf = sm.get('radar_flags') or {}
    strips = dict((x.get('edge', '').split(' ')[0] + x.get('edge', '').split(' ')[1] if ' ' in x.get('edge', '') else x.get('edge'),
                   (x.get('nodata'), x.get('dark'))) for x in (sm.get('edge') or {}).get('strips', []))
    ra = probe('h5attrs', os.path.join(W, 'mintpy', 'maskTempCoh.h5'), 'LINOG_WATERMASK')
    ga = probe('h5attrs', os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5'), 'LINOG_WATERMASK')
    case('T125b the water mask on the mock\'s scene: rule v2 applied; the sea\'s valid pixels masked (flag 1) and the pier kept (flag 3); '
         'the near-range strip masked along column 0 (flag 6: G23\'s dark run of 6 px); the radar and geo masks smaller, both carrying '
         'LINOG_WATERMASK; the originals kept in mintpy/watermask/',
         str(sm.get('rule', '')).startswith('LInOG masks v2') and sm.get('applied') is True and int(rf.get('1', 0)) > 0
         and int(rf.get('3', 0)) > 0 and int(rf.get('6', 0)) > 0 and strips.get('col0') == (0, 6)
         and 0 < int(sm.get('radar_after', 0)) < int(sm.get('radar_before', 0)) and 0 < int(sm.get('geo_after', 0)) < int(sm.get('geo_before', 0))
         and ra.get('LINOG_WATERMASK', '').startswith('LInOG masks v2') and ga.get('LINOG_WATERMASK', '').startswith('LInOG masks v2')
         and all(os.path.isfile(os.path.join(W, 'mintpy', 'watermask', n)) for n in ('maskTempCoh.orig.h5', 'geo_maskTempCoh.orig.h5')),
         'flags %s; strips %s; radar %s -> %s, geo %s -> %s; attrs %s %s' % (rf, strips, sm.get('radar_before'), sm.get('radar_after'),
                                                                           sm.get('geo_before'), sm.get('geo_after'), bool(ra), bool(ga)))
    up = os.path.join(W, 'mintpy', 'geo', 'LInOG_Upload_%s' % TAG)
    top = sorted(n for n in os.listdir(up) if os.path.isfile(os.path.join(up, n))) if os.path.isdir(up) else []
    tifs = [os.path.join(up, n) for n in top if n.endswith('.tif')]
    tf = probe('tiff', *tifs) if tifs else {}
    gm = probe('h5count', os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5'), 'mask')
    page = 'P084F3320_Igram_Report_Page_1.jpg'
    pa, pb = os.path.join(up, 'reports', page), os.path.join(W, 'Igrams', 'reports', page)
    linked = os.path.isfile(pa) and os.path.isfile(pb) and os.path.samefile(pa, pb)
    hv = probe('h5attrs', os.path.join(W, 'mintpy', 'geo', 'geo_velocity_Horizontal.h5'), 'PROJECTION_NOTE', 'LOOK_AZIMUTH_DEG',
               'GROUND_RANGE_TOWARD_SATELLITE_DEG', 'PROJECTION_COMPONENT', 'PROJECTION_ASSUMPTION')
    vv = probe('h5attrs', os.path.join(W, 'mintpy', 'geo', 'geo_velocity_Vertical_ramp.h5'), 'PROJECTION_NOTE', 'PROJECTION_COMPONENT')
    mp = os.path.join(W, 'RUN_MANIFEST.json')
    man = json.load(open(mp)) if os.path.isfile(mp) else {}
    man0 = man   # T150 places its stations around this reference
    hd = man.get('headings') or {}
    km = probe('kmz', os.path.join(up, '%s_TimeSeries_demErr.kmz' % TAG))
    t0 = tf.get('%s_Velocity_demErr.tif' % TAG, {})
    case('T125c the delivery: the 16 names and nothing else at the top; the six GeoTIFFs NoData nan with STATISTICS_MEAN; the demErr '
         'GeoTIFF\'s valid cells = geo_maskTempCoh.h5\'s (G22d); the report\'s page in reports/ as a hard link (D5); the H/V labels '
         '"Single descending track", toward the satellite 101.10 deg, look azimuth 281.10 (D7); RUN_MANIFEST.json with both headings '
         '(MintPy\'s -168.94, los.rdr\'s -168.9, F55); the time-series KMZ with points',
         top == sorted(x[0] for x in man.get('delivery', {}).get('files', [])) and len(top) == 16 and len(tifs) == 6 and all(v.get('nodata') == 'nan' and v.get('mean') is not None for v in tf.values())
         and t0.get('finite') == gm.get('n') and gm.get('n', 0) > 0 and linked
         and hv.get('PROJECTION_NOTE') == 'Single descending track: projection, NOT a decomposition.' and hv.get('LOOK_AZIMUTH_DEG') == '281.10'
         and hv.get('GROUND_RANGE_TOWARD_SATELLITE_DEG') == '101.10' and hv.get('PROJECTION_COMPONENT') == 'Horizontal'
         and '(E)' in hv.get('PROJECTION_ASSUMPTION', '') and vv.get('PROJECTION_NOTE', '').startswith('Single descending track')
         and (hd.get('mintpy') or {}).get('deg') == -168.94 and (hd.get('los') or {}).get('deg') == -168.9
         and man.get('frame', {}).get('tag') == TAG and man.get('look', {}).get('toward_satellite_compass') == 'E'
         and km.get('placemarks', 0) > 0,
         '%d files (%d tif); tiffs %s; demErr valid %s, geo mask %s; D5 link %s; H/V %s | %s; headings %s; KMZ %s' % (
             len(top), len(tifs), sorted((k[len(TAG) + 1:], v.get('nodata'), v.get('mean') is not None) for k, v in tf.items()),
             t0.get('finite'), gm.get('n'), linked, hv, vv, hd, km))
    rp = (man.get('decisions') or {}).get('reference_pixel') or {}
    d9m = (man.get('decisions') or {}).get('d9') or {}
    rd = man.get('readings') or {}
    fr = rp.get('geo_cell_fractional') or [0.5, 0.5]
    rings = rd.get('rings') or []
    fstat = [r_ for r_ in rings if r_.get('ring') == 'frame']
    lp = man.get('lead_product') or {}
    gn = rd.get('gnss') or []
    rg = probe('rings', os.path.join(up, '%s_Velocity_demErr.tif' % TAG), rp.get('lat'), rp.get('lon'), '0,0.5,1,2,5,10,20') \
        if rp.get('lat') is not None else {}
    mine = [(r_.get('demErr') or {}).get('cells') for r_ in rings], [(r_.get('demErr') or {}).get('median') for r_ in rings]
    same_rings = bool(rg.get('cells')) and rg['cells'] == mine[0] and all(
        (x is None and y is None) or (x is not None and y is not None and abs(x - y) < 1e-9) for x, y in zip(rg['medians'], mine[1]))
    rv = ((rd.get('reference') or {}).get('value') or {}).get('demErr')
    same_rings = same_rings and ((rv is None and rg.get('value') is None) or (rv is not None and rg.get('value') is not None
                                                                              and abs(rv - rg['value']) < 1e-9))
    case('T125g RUN_MANIFEST.json v0.8: the reference\'s latitude and longitude as numbers; geo_cell the floor of its fractional index, '
         'geo_cell_mintpy the rounded one (the mock geocode writes REF_Y, REF_X as MintPy 1.6.2 does); D9 no with the A/B (rule no, %d px '
         'asked); lead_product Velocity_demErr_ramp with its Vertical_ramp and Horizontal_ramp GeoTIFFs and its reason; readings: the '
         'reference cell\'s value, six rings and the frame row (its demErr cells = the GeoTIFF\'s valid cells; every ring\'s cells and median, '
         'and the reference cell\'s value, as around20.py\'s formula gives them on the demErr GeoTIFF), PIMO with its three discs' % MIN_GAIN,
         isinstance(rp.get('lat'), float) and isinstance(rp.get('lon'), float) and rp.get('geo_cell') == [int(math.floor(fr[0])), int(math.floor(fr[1]))]
         and rp.get('geo_cell_mintpy') == [int(round(fr[0])), int(round(fr[1]))] and d9m.get('unwrapError') == 'no'
         and (d9m.get('ab') or {}).get('rule') == 'no' and (d9m.get('ab') or {}).get('min_gain_px') == MIN_GAIN
         and lp.get('product') == 'Velocity_demErr_ramp' and lp.get('files') == ['%s_Velocity_%s.tif' % (TAG, x) for x in ('demErr_ramp', 'Vertical_ramp',
                                                                                                                       'Horizontal_ramp')]
         and not lp.get('missing') and 'ionosphere' in lp.get('reason', '') and len(rings) == 7 and rd.get('reference', {}).get('cell') == rp.get('geo_cell')
         and fstat and fstat[0].get('demErr', {}).get('cells') == t0.get('finite') and len(gn) == 1 and gn[0].get('station') == 'PIMO'
         and len(gn[0].get('discs') or []) == 3 and all(set(('Vertical', 'Vertical_ramp', 'demErr', 'demErr_ramp')) <= set(x) for x in gn[0]['discs'])
         and same_rings and rg.get('cell') == rp.get('geo_cell'),
         'reference %s; D9 %s; lead %s; readings: reference %s, %d rings, frame %s, PIMO %s' % (
             dict((k, rp.get(k)) for k in ('lat', 'lon', 'geo_cell', 'geo_cell_fractional', 'geo_cell_mintpy', 'geo_cell_centre_m')),
             dict(unwrapError=d9m.get('unwrapError'), ab=dict((k, (d9m.get('ab') or {}).get(k)) for k in ('rule', 'min_gain_px', 'gain_px'))),
             dict((k, lp.get(k)) for k in ('product', 'files', 'missing')), rd.get('reference'), len(rings),
             fstat[0].get('demErr') if fstat else None, dict((k, gn[0].get(k)) for k in ('inside', 'cell', 'km_from_reference')) if gn else None)
         + '; around20\'s formula %s, the manifest %s' % (rg, mine))
    # v0.9: RUN_MANIFEST.json's fftw block, from refine's and igram's records on this frame (the clean run's, S4f)
    fc = {}
    fcp = os.path.join(T, 'cfg', 'fftw_mock.cfg')
    for ln in open(fcp) if os.path.isfile(fcp) else []:
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.strip().split('=', 1)
            fc[k] = v
    fm = man.get('fftw') or {}
    okf = bool(fc) and all(fm.get(ph) and fm[ph].get('wisdom') == fc['WISDOM'] and fm[ph].get('wisdom_md5') == fc['WISDOM_MD5']
                           and fm[ph].get('lib_md5') == fc['FFTW_LIB_MD5'] and fm[ph].get('version') == fc['FFTW_VERSION']
                           and fm[ph].get('covered') == int(fc['PROBLEMS']) and fm[ph].get('jobs') == 6 and fm[ph].get('jobs_imported') == 6
                           for ph in ('refine', 'igram')) \
        and sorted((fm.get('refine') or {}).get('modules') or {}) == ['ampcor'] \
        and sorted((fm.get('igram') or {}).get('modules') or {}) == ['crossmul', 'icu'] \
        and man.get('manifest', '').startswith('RUN_MANIFEST.json (linog_auto v0.13 r3') and 'null' in fm.get('note', '') \
        and R['deliver'].get('version') == 'linog_auto v0.13 r3 (2026-10-30)' and R['deliver'].get('logic') == 7
    case('T167 RUN_MANIFEST.json (v0.9\'s block): fftw names the wisdom refine\'s and igram\'s jobs ran with (the mock pins: the file, its md5, the '
         'library\'s md5 and version; %s of %s problems), their modules (ampcor; crossmul and icu), 6 of 6 jobs imported in each; the '
         'manifest\'s label v0.13 r3; deliver\'s record v0.13 r3, LOGIC 7 (v0.13 r3: chain A\'s DEM-error fit without the fit\'s '
         'dates; v0.13 r2: G6a.11\'s reading, LOGIC kept, DB1-b; v0.12: '
         'drop1\'s decision; v0.11\'s 5: the KMZs\' fixed entry times)' % (
             fc.get('PROBLEMS'), fc.get('PROBLEMS')), okf,
         'fftw %s; label %s' % (dict((ph, dict((k, (fm.get(ph) or {}).get(k)) for k in ('wisdom_md5', 'version', 'covered', 'jobs',
                                                                                      'jobs_imported', 'modules'))) for ph in ('refine', 'igram')),
                                man.get('manifest')) + '; deliver %s, LOGIC %s' % (R['deliver'].get('version'), R['deliver'].get('logic')))
    ob = R['accept'].get('outputs', {})
    iscelog = os.path.isfile(os.path.join(W, 'isce.log'))
    case('T125d accept: the verifier copy ran from logs/p6/accept/ (rc 0; FAIL 0; its summary equals its lines); N22\'s modes from '
         'recon/modes.json (D6); the frame unchanged by it (G6b.8), no isce.log at the frame root',
         ob.get('rc') == 0 and (ob.get('counts') or {}).get('FAIL', 0) == 0 and (ob.get('counts') or {}).get('PASS', 0) >= 20
         and str(ob.get('n22_source', '')).startswith('recon/modes.json (') and ob.get('cwd') == os.path.join(W, 'logs', 'p6', 'accept')
         and gates(R['accept']).get('G6b.8') == 'PASS' and not iscelog,
         'rc %s; counts %s; N22 %s; WARN: %s; isce.log at the root %s' % (ob.get('rc'), ob.get('counts'), ob.get('n22_source'),
                                                                           note(R['accept'], 'G6b.7').replace('\n', ' | ')[:300], iscelog))
    op = R['package'].get('outputs', {})
    X = os.path.join(W, op.get('package') or '-')
    day = (R['package'].get('start') or '')[:10].replace('-', '')
    mf = os.path.join(X, 'TRANSFER_MANIFEST_%s.txt' % TAG)
    c = subprocess.run(['md5sum', '-c', os.path.basename(mf)], cwd=X, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) \
        if os.path.isfile(mf) else None
    ok_lines = c.stdout.decode().count(': OK\n') if c else 0
    hh = subprocess.run('cut -c1-32 %s | LC_ALL=C sort | md5sum | cut -c1-32' % os.path.basename(mf), shell=True, cwd=X,
                        stdout=subprocess.PIPE).stdout.decode().strip() if os.path.isfile(mf) else None
    lines = open(mf).read().splitlines() if os.path.isfile(mf) else []
    payload = [os.path.join(X, ln.split('  ', 1)[1]) for ln in lines]
    counts = dict((d, len([n for n in os.listdir(os.path.join(X, d)) if os.path.isfile(os.path.join(X, d, n))]))
                  for d in ('.', 'LInOG_Upload_%s' % TAG, 'LInOG_Upload_%s/reports' % TAG, 'Igrams', 'Igrams/reports')) if os.path.isdir(X) else {}
    case('T125e package: _xfer/LINOG_DESC_P084F3320_v0.1_<today>_review/ as chapter 9.4 lays it out (16 + reports/1 in LInOG_Upload, '
         '12 pair JPEGs flat in Igrams/, the page in Igrams/reports/, RUN_MANIFEST.json and the manifest at the root); the manifest\'s 31 '
         'lines pass `md5sum -c` there; `cut -c1-32 <manifest> | LC_ALL=C sort | md5sum` prints the record\'s hash of hashes; every payload '
         'file a hard link (2 or more links)',
         op.get('package') == '_xfer/LINOG_DESC_%s_v0.1_%s_review' % (TAG, day) and counts == {'.': 2, 'LInOG_Upload_%s' % TAG: 16,
                                                                                            'LInOG_Upload_%s/reports' % TAG: 1, 'Igrams': 12,
                                                                                            'Igrams/reports': 1}
         and len(lines) == 31 and c is not None and c.returncode == 0 and ok_lines == 31 and hh == op.get('hash_of_hashes')
         and all(ln.split('  ', 1)[1].startswith('./') for ln in lines) and not any('TRANSFER_MANIFEST' in ln for ln in lines)
         and all(os.stat(p).st_nlink >= 2 for p in payload),
         '%s; counts %s; %d lines, md5sum -c rc %s, %d OK; hash of hashes %s (record %s); links %s' % (
             op.get('package'), counts, len(lines), c.returncode if c else None, ok_lines, hh, op.get('hash_of_hashes'),
             sorted(set(os.stat(p).st_nlink for p in payload if os.path.exists(p)))))

    # ---- D6's check (lp_d6check.sh, install.sh step 4b): a frame without recon/modes.json (as the 12 delivered frames), then
    # the FBS-only frame with it (F39: the kit classes its secondaries FBD)
    F1 = os.path.join(T, 'd6frames', 'p084', 'f3320')
    shutil.copytree(W, F1, symlinks=True, copy_function=os.link, ignore=lambda d, names: ['modes.json'] if d.endswith('recon') else [])
    denv = dict((k, v) for k, v in os.environ.items() if not k.startswith('LINOG_'))
    denv['LINOG_ENV_CFG'] = os.path.join(T, 'cfg', 'env_mock.cfg')
    d1 = subprocess.run(['bash', os.path.join(S.HERE, 'lp_d6check.sh'), os.path.join(T, 'd6_T139'), F1], env=denv,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    d2 = subprocess.run(['bash', os.path.join(S.HERE, 'lp_d6check.sh'), os.path.join(T, 'd6_T139b'), W], env=denv,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o1, o2 = d1.stdout.decode('utf-8', 'replace'), d2.stdout.decode('utf-8', 'replace')
    k2 = open(os.path.join(T, 'd6_T139b', 'kit.txt')).read() if os.path.isfile(os.path.join(T, 'd6_T139b', 'kit.txt')) else ''
    c2 = open(os.path.join(T, 'd6_T139b', 'copy.txt')).read() if os.path.isfile(os.path.join(T, 'd6_T139b', 'copy.txt')) else ''
    case('T139 D6\'s check (lp_d6check.sh): on a copy of the delivered frame without recon/modes.json (as the 12 delivered frames have '
         'none) the copy prints the kit\'s lines, rc 0; on the FBS-only frame with it the kit FAILs N22 (every secondary FBD, F39) and '
         'the copy PASSes it: NOT the kit\'s lines, rc 1; both frames unchanged',
         d1.returncode == 0 and 'D6: the copy prints the kit\'s lines on the 1 frames' in o1 and 'raw_fbs_unpacked/' in o1
         and d2.returncode == 1 and 'D6: NOT the kit\'s lines' in o2 and re.search(r'FAIL N22 +range datum: 0 FBS \+ 3 FBD', k2)
         and re.search(r'PASS N22 +range datum: 3 FBS \+ 0 FBD', c2) and o1.count('unchanged') == 1 and o2.count('unchanged') == 1,
         'rc %d: %s | rc %d: %s' % (d1.returncode, ' / '.join(x.strip() for x in o1.splitlines() if 'D6:' in x or 'source lines' in x),
                                    d2.returncode, ' / '.join(x.strip() for x in o2.splitlines() if 'D6:' in x or 'differ' in x)))

    m0 = dict((ph, S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))) for i, ph in P6PH)
    l0 = listing(os.path.join(W, 'mintpy'))
    rc, out = run([])
    case('T126 re-run with no --to: all 31 phases skipped (v0.13: bandlimit after rwin; v0.12: drop1 after sbas; v0.11: rerun after package), rc 0; the 6 records '
         'and mintpy/ unchanged',
         rc == 0 and out.count('skip: PASS on record') == 31 and all(m0[ph] and S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))
                                                                     == m0[ph] for i, ph in P6PH) and listing(os.path.join(W, 'mintpy')) == l0,
         'rc %d; %d skipped' % (rc, out.count('skip: PASS on record')))

    # ---- dry runs: after sbas (the delivery not made), and on the delivered frame (T125's)
    D2 = os.path.join(T, 'dry_p6b')
    l0, g0 = listing(W), S34.md5q(os.path.join(W, 'logs', 'STATUS.txt'))
    rc, out = run(['--dry-run', D2])
    dr = dict((ph, json.load(open(os.path.join(D2, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D2, 'status', 'P%s_%s.json' % (i, ph))) else {}) for i, ph in P6PH)
    db = dr['accept'].get('outputs', {})
    d9 = dr['d9ab'].get('outputs', {})
    pm2 = json.load(open(os.path.join(D2, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(D2, 'RUN_MANIFEST.json')) else {}
    case('T127b dry run of the delivered frame: rc 0; d9ab\'s A/B with B under DIR, A\'s mask sbas\'s original (the frame\'s mask carries '
         'the water mask), the rule no; wmask the tool\'s own dry run from the originals (applied false); deliver a plan with '
         'the delivery named in the way (INFO) and the preview\'s readings from the frame\'s delivery; accept the verifier on the frame, FAIL 0; '
         'package a plan with the sources\' hash of hashes = the package\'s; the frame unchanged (listing and ledger)',
         rc == 0 and all(dr[ph].get('verdict') == 'PASS' for ph in dr)
         and str(d9.get('folder', '')).startswith('d9ab/') and os.path.isfile(os.path.join(D2, d9.get('folder', '-'), 'ab.json'))
         and 'maskTempCoh.orig.h5' in str(d9.get('a_mask')) and (d9.get('result') or {}).get('verdict') == 'no'
         and len((pm2.get('readings') or {}).get('rings') or []) == 7 and 'dry run' in (pm2.get('readings') or {}).get('source', '')
         and json.load(open(os.path.join(D2, 'mintpy', 'watermask_dryrun', 'summary.json'))).get('applied') is False
         and 'LInOG_Upload' in val(dr['deliver'], 'G6a.5') and (db.get('counts') or {}).get('FAIL') == 0
         and dr['package'].get('outputs', {}).get('hash_of_hashes') == op.get('hash_of_hashes')
         and listing(W) == l0 and S34.md5q(os.path.join(W, 'logs', 'STATUS.txt')) == g0,
         'rc %d; %s; d9ab %s, mask %s, rule %s; readings %s; accept %s; package %s; frame unchanged %s' % (
             rc, [(ph, dr[ph].get('verdict'), dr[ph].get('reason', '')[:70]) for ph in dr], d9.get('folder'), d9.get('a_mask'),
             (d9.get('result') or {}).get('verdict'), bool(pm2.get('readings')), db.get('counts'), dr['package'].get('outputs', {}).get('hash_of_hashes'),
             listing(W) == l0))
    # T134 on this frame: an earlier package in the way
    os.makedirs(os.path.join(W, '_archive', 'T134'), exist_ok=True)
    os.rename(os.path.join(W, 'status', 'P6c_package.json'), os.path.join(W, '_archive', 'T134', 'P6c_package.json'))
    rc, out = run([])
    rp = rec('6c', 'package')
    case('T134 an earlier package of the same frame and version under _xfer/ with no record of this phase: package DECISION at G6c.2 '
         'naming it, rc 4; nothing written into it',
         rc == 4 and rp.get('verdict') == 'DECISION' and gates(rp).get('G6c.2') == 'DECISION' and op.get('package', '-') in val(rp, 'G6c.2')
         and len(os.listdir(X)) == 4, 'rc %d; G6c.2 %s' % (rc, val(rp, 'G6c.2')))
    rc, out = run(['--to', 'deliver', '--force', 'deliver'])
    rd = rec('6a', 'deliver')
    case('T135 --force deliver after a clean run: deliver DECISION at G6a.5 naming the delivery and, after it, the package (the phases '
         'that read it), rc 4', rc == 4 and gates(rd).get('G6a.5') == 'DECISION' and 'LInOG_Upload_%s' % TAG in val(rd, 'G6a.5')
         and '_xfer/LINOG_DESC_%s_v0.1_' % TAG in val(rd, 'G6a.5'), 'rc %d; G6a.5 %s' % (rc, val(rd, 'G6a.5')[:200]))

    restore('T127')
    D = os.path.join(T, 'dry_p6')
    l0, g0 = listing(W), S34.md5q(os.path.join(W, 'logs', 'STATUS.txt'))
    rc, out = run(['--dry-run', D])
    dr = dict((ph, json.load(open(os.path.join(D, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D, 'status', 'P%s_%s.json' % (i, ph))) else {}) for i, ph in P6PH)
    dw = json.load(open(os.path.join(D, 'mintpy', 'watermask_dryrun', 'summary.json'))) \
        if os.path.isfile(os.path.join(D, 'mintpy', 'watermask_dryrun', 'summary.json')) else {}
    pm = json.load(open(os.path.join(D, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(D, 'RUN_MANIFEST.json')) else {}
    da = dr['accept'].get('outputs', {})
    case('T127 dry run of the frame after sbas (no --to): rc 0; d9ab\'s A/B under DIR (the rule no); wmask the tool\'s own dry run into '
         'DIR (applied false, the same flags as T125b); deliver a plan and DIR/RUN_MANIFEST.json (a preview, both headings, no readings: no '
         'delivery yet, G6a.9 INFO); accept the verifier\'s baseline (FAIL > 0: no delivery, no water mask yet); package a plan only; the '
         'frame unchanged (listing and ledger)',
         rc == 0 and all(dr[ph].get('verdict') == 'PASS' for ph in dr) and dw.get('applied') is False
         and ((dr['d9ab'].get('outputs') or {}).get('result') or {}).get('verdict') == 'no' and pm.get('readings') is None
         and gates(dr['deliver']).get('G6a.9') == 'INFO' and 'not read' in val(dr['deliver'], 'G6a.9')
         and dw.get('radar_flags') == sm.get('radar_flags') and pm.get('dry_run') and (pm.get('headings') or {}).get('mintpy', {}).get('deg') == -168.94
         and (da.get('counts') or {}).get('FAIL', 0) > 0 and 'plan only' in dr['package'].get('reason', '')
         and listing(W) == l0 and S34.md5q(os.path.join(W, 'logs', 'STATUS.txt')) == g0,
         'rc %d; %s; wmask dry flags %s; accept %s; frame unchanged %s' % (
             rc, [(ph, dr[ph].get('verdict'), dr[ph].get('reason', '')[:60]) for ph in dr], dw.get('radar_flags'), da.get('counts'),
             listing(W) == l0))

    # ---- the water mask in the way, and a mask rewritten after it
    restore('T128')
    rc, out = run(['--to', 'wmask'])
    os.makedirs(os.path.join(W, '_archive', 'T128'), exist_ok=True)
    os.rename(os.path.join(W, 'status', 'P5e_wmask.json'), os.path.join(W, '_archive', 'T128', 'P5e_wmask.json'))
    m1 = md5s(os.path.join(W, 'mintpy', 'maskTempCoh.h5'), os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5'))
    rc2, out2 = run(['--to', 'wmask'])
    rw = rec('5e', 'wmask')
    case('T128 the masks carry the water mask and mintpy/watermask/ is there, with no record of wmask: DECISION at G5e.5 naming both, '
         'rc 4; the masks unchanged', rc == 0 and rc2 == 4 and gates(rw).get('G5e.5') == 'DECISION' and 'mintpy/watermask' in val(rw, 'G5e.5')
         and 'carries LINOG_WATERMASK' in val(rw, 'G5e.5') and md5s(os.path.join(W, 'mintpy', 'maskTempCoh.h5'),
                                                                   os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5')) == m1,
         'rc %d then %d; G5e.5 %s' % (rc, rc2, val(rw, 'G5e.5')))
    restore('T129')
    rc, out = run(['--to', 'wmask'])
    shutil.copy2(os.path.join(W, 'mintpy', 'watermask', 'maskTempCoh.orig.h5'), os.path.join(W, 'mintpy', 'maskTempCoh.h5'))
    rc2, out2 = run([])
    rw = rec('5e', 'wmask')
    case('T129 maskTempCoh.h5 rewritten without the water mask after wmask (as a later MintPy call does): wmask STALE; its re-run stops at '
         'G5e.5 (DECISION: mintpy/watermask there), rc 4; deliver not run', rc == 0 and rc2 == 4 and 'P5e wmask: record STALE' in out2
         and gates(rw).get('G5e.5') == 'DECISION' and 'auto_deliver START' not in open(os.path.join(W, 'logs', 'STATUS.txt')).read(),
         'rc %d then %d; G5e.5 %s' % (rc, rc2, val(rw, 'G5e.5')[:150]))

    # ---- the kit's Phase 6: geocode --update ignored, a step failing, a PAM sidecar
    restore('T130')
    rc, out = run([], {'LINOG_MOCK_GEOCODE_NOUPDATE': '1'})
    rd = rec('6a', 'deliver')
    case('T130 geocode ignores --update (the script\'s step 5 rewrites geo_maskTempCoh.h5 from the radar mask): deliver FAIL at G6a.8 '
         'naming the geo mask, rc 2; accept not run', rc == 2 and rec('5e', 'wmask').get('verdict') == 'PASS'
         and gates(rd).get('G6a.8') == 'FAIL' and 'geo_maskTempCoh.h5' in val(rd, 'G6a.8') and not rec('6b', 'accept'),
         'rc %d; G6a.8 %s' % (rc, val(rd, 'G6a.8')[:160]))
    restore('T131')
    rc, out = run([], {'LINOG_MOCK_P6FAIL': 'save_kmz.py'})
    rd = rec('6a', 'deliver')
    rc2, out2 = run([])
    rd2 = rec('6a', 'deliver')
    case('T131 the kit\'s script stops at step 7 (save_kmz.py exits 1; the script runs under set -e): deliver FAIL at G6a.6, its note naming '
         'the log, rc 2; the same run again: deliver DECISION at G6a.5 (the partial delivery and the chains in the way), rc 4',
         rc == 2 and gates(rd).get('G6a.6') == 'FAIL' and 'linog_phase6.log' in note(rd, 'G6a.6') and 'steps 1 2 3 4 5 6 7' in val(rd, 'G6a.6')
         and rc2 == 4 and gates(rd2).get('G6a.5') == 'DECISION' and 'LInOG_Upload_%s' % TAG in val(rd2, 'G6a.5'),
         'rc %d, G6a.6 %s; rc %d, G6a.5 %s' % (rc, val(rd, 'G6a.6')[:100], rc2, val(rd2, 'G6a.5')[:120]))
    restore('T132')
    rc, out = run([], {'LINOG_MOCK_AUX': '1'})
    rd = rec('6a', 'deliver')
    case('T132 a PAM sidecar beside each PNG (view.py leaves <png>.aux.xml): deliver FAIL at N6 naming 6 extra files and 6 .aux.xml, rc 2',
         rc == 2 and gates(rd).get('N6') == 'FAIL' and ', 6 .aux.xml' in val(rd, 'N6') and '22 files' in val(rd, 'N6'),
         'rc %d; N6 %s' % (rc, val(rd, 'N6')))

    # ---- the verifier FAILs, then passes
    restore('T133')
    rc, out = run([], {'LINOG_MOCK_GDALINFO_FAIL': '1'})
    rb = rec('6b', 'accept')
    rc2, out2 = run([])
    case('T133 gdalinfo prints no metadata (the verifier\'s N6 reads no STATISTICS_MEAN): accept FAIL at G6b.6 listing N6, rc 2; the run '
         'again: accept re-runs and PASSes, package PASS, rc 0', rc == 2 and gates(rb).get('G6b.6') == 'FAIL' and 'N6 0/6 TIFFs' in note(rb, 'G6b.6')
         and rc2 == 0 and rec('6b', 'accept').get('verdict') == 'PASS' and rec('6c', 'package').get('verdict') == 'PASS',
         'rc %d, G6b.6 %s %s; rc %d' % (rc, val(rb, 'G6b.6'), note(rb, 'G6b.6')[:120], rc2))

    # ---- pins and names in linog_phase6.cfg
    restore('T136')
    rc, out = run([], {'LINOG_PHASE6_CFG': p6_copy('p6_nocopy.cfg', 'VERIFY_COPY', 'linog_verify_frame_d6_absent.py')})
    rb = rec('6b', 'accept')
    case('T136 the verifier copy named in linog_phase6.cfg is not the package\'s (not in MANIFEST.md5): wmask and deliver PASS, accept FAIL '
         'at G6b.3, rc 2', rc == 2 and rec('6a', 'deliver').get('verdict') == 'PASS' and gates(rb).get('G6b.3') == 'FAIL',
         'rc %d; G6b.3 %s' % (rc, val(rb, 'G6b.3')[:120]))
    restore('T137')
    rc, out = run([], {'LINOG_PHASE6_CFG': p6_copy('p6_badphase6.cfg', 'KIT_PHASE6_MD5', '0' * 32)})
    rd = rec('6a', 'deliver')
    case('T137 the kit\'s linog_phase6.sh off its pin (a linog_phase6.cfg with another md5): wmask PASS, deliver FAIL at G6a.3 before the '
         'script runs (no delivery folder), rc 2', rc == 2 and rec('5e', 'wmask').get('verdict') == 'PASS' and gates(rd).get('G6a.3') == 'FAIL'
         and not os.path.exists(os.path.join(W, 'mintpy', 'geo', 'LInOG_Upload_%s' % TAG)), 'rc %d; G6a.3 %s' % (rc, gates(rd).get('G6a.3')))
    # ---- a default dry run of a frame whose MintPy has not run (the frame after igram)
    S.aside(T, W, 'p6_T140')
    shutil.copytree(os.path.join(T, 'snap_p3', 'S4f'), W, symlinks=True, copy_function=S34.link_or_copy)
    D3 = os.path.join(T, 'dry_p6c')
    l0 = listing(W)
    rc, out = run(['--dry-run', D3])
    dr = dict((ph, json.load(open(os.path.join(D3, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D3, 'status', 'P%s_%s.json' % (i, ph))) else {}) for i, ph in P6PH)
    case('T140 a dry run with no --to of the frame after igram (MintPy not run): rc 0; d9ab, wmask, dfit and deliver a plan only (the frame\'s sbas '
         'has not run), accept the verifier\'s baseline, package a plan only; the frame unchanged',
         rc == 0 and all(dr[ph].get('verdict') == 'PASS' for ph in dr) and 'plan only' in dr['wmask'].get('reason', '')
         and 'plan only' in dr['d9ab'].get('reason', '') and 'plan only' in dr['dfit'].get('reason', '')
         and 'the frame\'s sbas has not run' in dr['deliver'].get('reason', '') and dr['accept'].get('outputs', {}).get('planned')
         and 'plan only' in dr['package'].get('reason', '') and listing(W) == l0,
         'rc %d; %s' % (rc, [(ph, dr[ph].get('verdict'), dr[ph].get('reason', '')[:70]) for ph in dr]))

    # ---- stops: SIGTERM while the kit's script runs (its view.py asleep), and while the water mask tool applies
    restore('T141')
    mk = os.path.join(T, 'mark_T141')
    rc, out = stopped([], {'LINOG_MOCK_P6SLEEP': 'view.py', 'LINOG_MOCK_SLEEP_S': '6'}, mk)
    rd = rec('6a', 'deliver')
    lg = (sorted(glob.glob(os.path.join(W, 'logs', 'p6', 'deliver', 'linog_phase6.log.v*'))) or ['-'])[-1]
    time.sleep(7)
    png = os.path.join(W, 'mintpy', 'geo', 'LInOG_Upload_%s' % TAG, '%s_Velocity_Hillshade_demErr.png' % TAG)
    tail = open(lg).read().splitlines()[-1] if os.path.isfile(lg) else ''
    rc2, out2 = run([])
    case('T141 SIGTERM to the run while the kit\'s script is in step 9 (view.py asleep): rc 143, deliver ERROR; the script\'s group ended '
         'with it (the log\'s last line says so, and the sleeping view.py never wrote its PNG); the next run: deliver DECISION at G6a.5 (the '
         'partial delivery in the way), rc 4', rc == 143 and rd.get('verdict') == 'ERROR' and 'the command\'s group ended' in tail
         and not os.path.exists(png) and rc2 == 4 and gates(rec('6a', 'deliver')).get('G6a.5') == 'DECISION',
         'rc %d; deliver %s; log tail %r; png %s; then rc %d' % (rc, rd.get('verdict'), tail, os.path.exists(png), rc2))
    restore('T142')
    mk = os.path.join(T, 'mark_T142')
    rc, out = stopped(['--to', 'wmask'], {'LINOG_MOCK_P6SLEEP': 'geocode', 'LINOG_MOCK_SLEEP_S': '3'}, mk)
    rw = rec('5e', 'wmask')
    sm2 = json.load(open(os.path.join(W, 'mintpy', 'watermask', 'summary.json'))) \
        if os.path.isfile(os.path.join(W, 'mintpy', 'watermask', 'summary.json')) else {}
    whole = sm2.get('md5', {}).get('maskTempCoh.h5') == S34.md5q(os.path.join(W, 'mintpy', 'maskTempCoh.h5')) and \
        sm2.get('md5', {}).get('geo/geo_maskTempCoh.h5') == S34.md5q(os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5'))
    rc2, out2 = run(['--to', 'wmask'])
    case('T142 SIGTERM to the run while the water mask tool applies (its geocode asleep): the stop is held until the tool ends (a session '
         'of its own), so both masks are whole (md5 = summary.json) and the record then reads ERROR, rc 143; the next run stops at G5e.5 '
         '(DECISION, the originals named), rc 4', rc == 143 and rw.get('verdict') == 'ERROR' and (rw.get('outputs') or {}).get('applying') is False
         and (rw.get('outputs') or {}).get('rc') == 0 and whole and rc2 == 4 and gates(rec('5e', 'wmask')).get('G5e.5') == 'DECISION',
         'rc %d; wmask %s, outputs %s; masks whole %s; then rc %d' % (rc, rw.get('verdict'), dict((k, v) for k, v in (rw.get('outputs') or {}).items()
                                                                                             if k in ('applying', 'rc')), whole, rc2))

    # ---- the report made again after the delivery; a ramp-first copy cut short; los.rdr off MintPy's heading
    restore('T143')
    rc, out = run([])
    os.makedirs(os.path.join(W, '_archive', 'T143'), exist_ok=True)
    os.rename(os.path.join(W, 'Igrams', 'reports'), os.path.join(W, '_archive', 'T143', 'reports'))
    rc2, out2 = run([])
    rd = rec('6a', 'deliver')
    case('T143 the report made again after a clean run to package (its folder moved aside): report re-runs and PASSes; deliver STALE (the '
         'report\'s digest is in its fingerprint: D5 links its pages) and stops at G6a.5, rc 4', rc == 0 and rc2 == 4
         and rec('4g', 'report').get('verdict') == 'PASS' and 'P6a deliver: record STALE' in out2 and gates(rd).get('G6a.5') == 'DECISION',
         'rc %d then %d; deliver %s %s' % (rc, rc2, rd.get('verdict'), gates(rd).get('G6a.5')))
    restore('T144')
    with open(os.path.join(W, 'mintpy', 'demErr.h5'), 'rb') as fh:
        open(os.path.join(W, 'mintpy', 'demErr_rampfirst.h5'), 'wb').write(fh.read(700))
    rc, out = run([])
    rd = rec('6a', 'deliver')
    case('T144 a ramp-first copy cut short (700 B of demErr.h5, as a stop during step 1\'s cp leaves it): deliver FAIL at G6a.5r naming it '
         'before the script runs (the script would keep it), rc 2', rc == 2 and gates(rd).get('G6a.5r') == 'FAIL'
         and 'demErr_rampfirst.h5' in val(rd, 'G6a.5r') and not os.path.exists(os.path.join(W, 'mintpy', 'timeseries_demErr.h5')),
         'rc %d; G6a.5r %s' % (rc, val(rd, 'G6a.5r')[:120]))
    S.aside(T, W, 'p6_T145')
    shutil.copytree(os.path.join(T, 'snap_p3', 'S4f'), W, symlinks=True, copy_function=S34.link_or_copy)
    rc, out = run([], {'LINOG_MOCK_HEADING': '-160'})
    rd = rec('6a', 'deliver')
    case('T145 MintPy\'s HEADING -160 (inside G24\'s 30 deg, 8.9 deg from los.rdr\'s -168.9): sbas and wmask PASS, deliver FAIL at D7c before '
         'the script runs, rc 2', rc == 2 and rec('5d', 'sbas').get('verdict') == 'PASS' and rec('5e', 'wmask').get('verdict') == 'PASS'
         and gates(rd).get('D7c') == 'FAIL' and 'heading -8.900 deg' in val(rd, 'D7c') and not os.path.exists(os.path.join(W, 'mintpy', 'timeseries_demErr.h5')),
         'rc %d; D7c %s' % (rc, val(rd, 'D7c')[:140]))

    # ---- v0.8: D9's A/B (d9ab) reading bridging, the operator's two answers, the rule's other conditions, a stop
    def folders():
        return sorted(os.path.basename(x) for x in glob.glob(os.path.join(W, 'd9ab', '*')))
    adm_txt = os.path.join(W, 'recon', 'admission.txt')
    restore('T146')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1'}, decide='ask')
    r9 = rec('5dab', 'd9ab')
    res = (r9.get('outputs') or {}).get('result') or {}
    case('T146 bridging gains B\'s mask the sea\'s decorrelated half and corrects a planted unwrapping error (LINOG_MOCK_B_GAIN): the rule '
         'reads bridging (gain %d px or more, std no larger), 1 pair changed; unwrapError no is MintPy\'s default here, so under --decide ask '
         'd9ab DECISION at D9ab naming recon/admission.txt, rc 4 (v0.10: under auto, R5 takes it, T146r); wmask not run' % MIN_GAIN,
         rc == 4 and r9.get('verdict') == 'DECISION' and gates(r9).get('D9ab') == 'DECISION' and res.get('verdict') == 'bridging'
         and (res.get('gain') or 0) >= MIN_GAIN and res.get('pairs_changed') == 1 and (res.get('moved_px') or 0) > 0
         and 'admission.txt' in note(r9, 'D9ab') and not rec('5e', 'wmask') and len(folders()) == 1,
         'rc %d; d9ab %s, D9ab %s; result %s; folders %s' % (rc, r9.get('verdict'), gates(r9).get('D9ab'), dict(
             (k, res.get(k)) for k in ('verdict', 'gain', 'min_gain', 'pairs_changed', 'moved_px', 'std_common_a', 'std_common_b', 'tint_valid')), folders()))
    with open(adm_txt, 'w') as fh:
        fh.write('# the operator keeps no after the A/B (self-test T146b)\nmintpy.unwrapError.method = no\n')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1'})
    r9 = rec('5dab', 'd9ab')
    man = json.load(open(os.path.join(W, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')) else {}
    d9m = (man.get('decisions') or {}).get('d9') or {}
    case('T146b recon/admission.txt names no: admit re-runs (D9 INFO), mcfg and sbas stay CURRENT (admit decided the same); d9ab reads its A/B '
         'again (no new folder, no MintPy run) and PASSes with D9ab INFO (the operator\'s no stands); the run goes on to package, rc 0; '
         'RUN_MANIFEST.json: unwrapError no, the operator\'s, the A/B\'s rule bridging',
         rc == 0 and 'P5a admit: record STALE' in out and 'P5c mcfg: record CURRENT' in out and 'P5d sbas: record CURRENT' in out
         and r9.get('verdict') == 'PASS' and gates(r9).get('D9ab') == 'INFO' and (r9.get('outputs') or {}).get('reused') is True
         and len(folders()) == 1 and rec('6c', 'package').get('verdict') == 'PASS' and d9m.get('unwrapError') == 'no'
         and str(d9m.get('source', '')).startswith('the operator') and (d9m.get('ab') or {}).get('rule') == 'bridging',
         'rc %d; d9ab %s, D9ab %s, reused %s; folders %s; package %s; manifest d9 %s' % (
             rc, r9.get('verdict'), gates(r9).get('D9ab'), (r9.get('outputs') or {}).get('reused'), folders(), rec('6c', 'package').get('verdict'),
             dict(unwrapError=d9m.get('unwrapError'), source=d9m.get('source'), rule=(d9m.get('ab') or {}).get('rule'))))
    restore('T146c')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1'}, decide='ask')
    with open(adm_txt, 'w') as fh:
        fh.write('# the operator takes bridging after the A/B (self-test T146c)\nmintpy.unwrapError.method = bridging\n')
    rc2, out2 = run([])
    rm = rec('5c', 'mcfg')
    os.makedirs(os.path.join(W, '_archive', 'T146c'), exist_ok=True)
    os.rename(os.path.join(W, 'mintpy'), os.path.join(W, '_archive', 'T146c', 'mintpy'))
    rc3, out3 = run([])
    r9 = rec('5dab', 'd9ab')
    man = json.load(open(os.path.join(W, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')) else {}
    d9m = (man.get('decisions') or {}).get('d9') or {}
    case('T146c recon/admission.txt names bridging after d9ab\'s DECISION (under ask): admit takes it and mcfg stops at G5c.4 (mintpy/ in the way), rc 4; '
         'mintpy/ moved into _archive/: mcfg and sbas run with bridging, d9ab PASS without an A/B (D9m INFO), the run to package PASS, rc 0; '
         'RUN_MANIFEST.json: unwrapError bridging, the operator\'s, no A/B',
         rc == 4 and rc2 == 4 and gates(rm).get('G5c.4') == 'DECISION' and rc3 == 0 and r9.get('verdict') == 'PASS'
         and gates(r9).get('D9m') == 'INFO' and not (r9.get('outputs') or {}).get('result') and rec('6c', 'package').get('verdict') == 'PASS'
         and d9m.get('unwrapError') == 'bridging' and str(d9m.get('source', '')).startswith('the operator') and (d9m.get('ab') or {}).get('rule') is None,
         'rc %d, %d (mcfg G5c.4 %s), %d; d9ab %s, D9m %s; package %s; manifest d9 %s' % (
             rc, rc2, gates(rm).get('G5c.4'), rc3, r9.get('verdict'), gates(r9).get('D9m'), rec('6c', 'package').get('verdict'),
             dict(unwrapError=d9m.get('unwrapError'), source=d9m.get('source'), ab=d9m.get('ab'))))
    # ---- v0.10, R5: the same A/B under --decide auto in a run without --only: d9ab takes bridging, the frame restarts once
    restore('T146r')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1'})
    led = open(os.path.join(W, 'logs', 'STATUS.txt')).read()
    rid = (re.findall(r'auto_run START id=(\S+)', led) or ['-'])[-1]
    dj = json.load(open(os.path.join(W, 'recon', 'd9ab_decision.json'))) if os.path.isfile(os.path.join(W, 'recon', 'd9ab_decision.json')) else {}
    ra, r9 = rec('5a', 'admit'), rec('5dab', 'd9ab')
    nb = sorted(glob.glob(os.path.join(W, '_archive', 'mintpy_nobridging_*', 'mintpy')))
    man = json.load(open(os.path.join(W, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')) else {}
    d9m = (man.get('decisions') or {}).get('d9') or {}
    r5m = d9m.get('r5') or {}
    tb = cfgv6(os.path.join(W, 'mintpy', 'smallbaselineApp.cfg'))
    case('T146r R5 (v0.10): the same A/B under --decide auto, no --only: d9ab writes recon/d9ab_decision.json (bridging, admit\'s network), '
         'moves mintpy/ into _archive/mintpy_nobridging_<UTC>/ and asks a restart; the driver runs the frame again from the top once '
         '(the ledger\'s RESTART line after=d9ab; the request kept as status/restart_<run>_1.json): admit takes bridging from R5 (D9 INFO), '
         'mcfg and sbas run with it (the template\'s unwrapError bridging), d9ab PASS without a new A/B (D9m), the run to package PASS, rc 0; '
         'RUN_MANIFEST.json: unwrapError bridging from R5 with the A/B that read it (r5: rule bridging, gain %d px or more)' % MIN_GAIN,
         rc == 0 and led.count('auto_run RESTART id=%s after=d9ab record=restart_%s_1.json' % (rid, rid)) == 1 and led.count('auto_run RESTART') == 1
         and os.path.isfile(os.path.join(W, 'status', 'restart_%s_1.json' % rid)) and not os.path.exists(os.path.join(W, 'status', 'restart.json'))
         and dj.get('method') == 'bridging' and dj.get('network') == (ra.get('outputs') or {}).get('network_md5') and str(dj.get('folder', '')).startswith('d9ab/')
         and len(nb) == 1 and os.path.isfile(os.path.join(nb[0], 'velocity.h5')) and gates(ra).get('D9') == 'INFO'
         and 'R5: d9ab\'s A/B under --decide auto' in val(ra, 'D9') and tb.get('mintpy.unwrapError.method') == 'bridging'
         and r9.get('verdict') == 'PASS' and gates(r9).get('D9m') == 'INFO' and len(folders()) == 1 and rec('6c', 'package').get('verdict') == 'PASS'
         and d9m.get('unwrapError') == 'bridging' and str(d9m.get('source', '')).startswith('R5') and r5m.get('rule') == 'bridging'
         and (r5m.get('gain_px') or 0) >= MIN_GAIN and r5m.get('file') == 'recon/d9ab_decision.json',
         'rc %d; restarts in the ledger %d; decision %s; moved %s; D9 %s; template %s; d9ab %s D9m %s; folders %s; package %s; manifest d9 %s' % (
             rc, led.count('auto_run RESTART'), dict((k, dj.get(k)) for k in ('method', 'folder', 'network')), [os.path.relpath(x, W) for x in nb],
             val(ra, 'D9')[-90:], tb.get('mintpy.unwrapError.method'), r9.get('verdict'), gates(r9).get('D9m'), folders(),
             rec('6c', 'package').get('verdict'), dict(unwrapError=d9m.get('unwrapError'), source=str(d9m.get('source'))[:40], r5=r5m)))
    restore('T146s')
    rc, out = run(['--only', 'd9ab'], {'LINOG_MOCK_B_GAIN': '1'})
    r9 = rec('5dab', 'd9ab')
    case('T146s the same under --decide auto but with --only d9ab (no restart there): d9ab DECISION at D9ab, its note naming the run '
         'without --only; nothing moved or written (mintpy/ in place, no recon/d9ab_decision.json, no status/restart.json), rc 4',
         rc == 4 and r9.get('verdict') == 'DECISION' and gates(r9).get('D9ab') == 'DECISION' and 'without --only' in note(r9, 'D9ab')
         and os.path.isdir(os.path.join(W, 'mintpy')) and not os.path.exists(os.path.join(W, 'recon', 'd9ab_decision.json'))
         and not os.path.exists(os.path.join(W, 'status', 'restart.json')) and not glob.glob(os.path.join(W, '_archive', 'mintpy_nobridging_*')),
         'rc %d; d9ab %s, D9ab %s; note %s' % (rc, r9.get('verdict'), gates(r9).get('D9ab'), note(r9, 'D9ab')[:160]))
    restore('T146d')
    D9D = os.path.join(T, 'dry_p6_T146d')
    l0 = listing(W)
    rc, out = run(['--dry-run', D9D, '--to', 'd9ab'], {'LINOG_MOCK_B_GAIN': '1'})
    r9 = json.load(open(os.path.join(D9D, 'status', 'P5dab_d9ab.json'))) if os.path.isfile(os.path.join(D9D, 'status', 'P5dab_d9ab.json')) else {}
    case('T146d the same A/B in a dry run under --decide auto (the install\'s F3310 dry run is one): d9ab\'s rule bridging, D9ab INFO saying '
         'what a run would take (R5), nothing moved or written: the frame\'s listing unchanged, no recon/d9ab_decision.json, rc 0',
         rc == 0 and r9.get('verdict') == 'PASS' and gates(r9).get('D9ab') == 'INFO' and 'dry run: under --decide auto R5 takes this bridging' in note(r9, 'D9ab')
         and ((r9.get('outputs') or {}).get('result') or {}).get('verdict') == 'bridging' and listing(W) == l0
         and not os.path.exists(os.path.join(W, 'recon', 'd9ab_decision.json')) and os.path.isdir(os.path.join(W, 'mintpy')),
         'rc %d; d9ab %s, D9ab %s; rule %s; frame unchanged %s' % (rc, r9.get('verdict'), gates(r9).get('D9ab'),
                                                                 ((r9.get('outputs') or {}).get('result') or {}).get('verdict'), listing(W) == l0))
    restore('T146e')
    with open(os.path.join(W, 'recon', 'd9ab_decision.json'), 'w') as fh:
        json.dump(dict(method='bridging', source='self-test T146e', folder='d9ab/x', network='0' * 32), fh)
    rc, out = run(['--to', 'admit'])
    ra = rec('5a', 'admit')
    case('T146e a recon/d9ab_decision.json taken on another network: admit re-runs (the file is in its fingerprint), D9 WARN naming it, '
         'unwrapError no (d9ab tests this network), admit PASS, rc 0', rc == 0 and 'P5a admit: record STALE' in out and gates(ra).get('D9') == 'WARN'
         and 'taken on another network' in note(ra, 'D9') and ((ra.get('outputs') or {}).get('cfg') or {}).get('mintpy.unwrapError.method') == 'no',
         'rc %d; D9 %s; note %s' % (rc, gates(ra).get('D9'), note(ra, 'D9')[:120]))
    restore('T146f')
    if os.path.lexists(os.path.join(W, '_archive')):
        S.aside(T, os.path.join(W, '_archive'), 'p6_T146f_frame_archive')
    open(os.path.join(W, '_archive'), 'w').write('self-test T146f: a file where R5 needs a folder\n')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1'})
    r9 = rec('5dab', 'd9ab')
    case('T146f R5 cannot make _archive/ (a file there): d9ab FAIL at G5dab.10, rc 2, before anything moves: mintpy/ in place, no '
         'recon/d9ab_decision.json, no status/restart.json, no RESTART line', rc == 2 and gates(r9).get('G5dab.10') == 'FAIL'
         and os.path.isdir(os.path.join(W, 'mintpy')) and not os.path.exists(os.path.join(W, 'recon', 'd9ab_decision.json'))
         and not os.path.exists(os.path.join(W, 'status', 'restart.json')) and 'auto_run RESTART' not in open(os.path.join(W, 'logs', 'STATUS.txt')).read(),
         'rc %d; G5dab.10 %s %s' % (rc, gates(r9).get('G5dab.10'), val(r9, 'G5dab.10')[:120]))
    os.rename(os.path.join(W, '_archive'), os.path.join(T, '_archive', 'p6_T146f_file'))
    restore('T147')
    rc, out = run([], {'LINOG_MOCK_B_GAIN': '1', 'LINOG_MOCK_B_VSTD': '2'})
    r9 = rec('5dab', 'd9ab')
    res = (r9.get('outputs') or {}).get('result') or {}
    case('T147 B\'s mask gains as T146 but its velocity carries 2 mm/yr of noise (LINOG_MOCK_B_VSTD): the rule\'s (c) fails, no; d9ab PASS, '
         'the run to package, rc 0', rc == 0 and r9.get('verdict') == 'PASS' and res.get('verdict') == 'no' and (res.get('gain') or 0) >= MIN_GAIN
         and (res.get('std_common_b') or 0) > (res.get('std_common_a') or 0) and rec('6c', 'package').get('verdict') == 'PASS',
         'rc %d; result %s' % (rc, dict((k, res.get(k)) for k in ('verdict', 'gain', 'std_common_a', 'std_common_b'))))
    restore('T148')
    rc, out = run([], {'LINOG_MOCK_SBASFAIL': 'invert_network'})
    r9 = rec('5dab', 'd9ab')
    res = (r9.get('outputs') or {}).get('result') or {}
    case('T148 MintPy on B fails at invert_network: G5dab.7 WARN naming the log, the rule no by its first condition (the products not '
         'compared); d9ab PASS; the run to package, rc 0', rc == 0 and r9.get('verdict') == 'PASS' and gates(r9).get('G5dab.7') == 'WARN'
         and 'mintpy_B.log' in note(r9, 'G5dab.7') and res.get('verdict') == 'no' and res.get('compared') is False and res.get('brc') == 1
         and rec('6c', 'package').get('verdict') == 'PASS', 'rc %d; G5dab.7 %s; result %s' % (
             rc, val(r9, 'G5dab.7')[:100], dict((k, res.get(k)) for k in ('verdict', 'compared', 'brc'))))
    restore('T149')
    mk = os.path.join(T, 'mark_T149')
    rc, out = stopped(['--to', 'd9ab'], {'LINOG_MOCK_P6SLEEP': 'smallbaselineApp', 'LINOG_MOCK_SLEEP_S': '8'}, mk)
    r9 = rec('5dab', 'd9ab')
    pid = re.search(r'pid (\d+)', open(mk).read()).group(1) if os.path.isfile(mk) else None
    alive = bool(pid) and os.path.exists('/proc/%s' % pid)
    lg = (r9.get('outputs') or {}).get('log') or '-'
    tail = open(lg).read().splitlines()[-1] if os.path.isfile(lg) else ''
    n0 = len(folders())
    rc2, out2 = run(['--to', 'd9ab'])
    r9b = rec('5dab', 'd9ab')
    case('T149 SIGTERM to the run while MintPy runs on B (the mock asleep): rc 143, d9ab ERROR; MintPy\'s group ended with it (the log\'s last '
         'line says so, the process gone); the next run makes a new A/B (the stopped one left no ab.json) and PASSes, rc 0',
         rc == 143 and r9.get('verdict') == 'ERROR' and 'the command\'s group ended' in tail and not alive and rc2 == 0
         and r9b.get('verdict') == 'PASS' and len(folders()) == n0 + 1 == 2 and (r9b.get('outputs') or {}).get('reused') is False,
         'rc %d; d9ab %s; log tail %r; the mock pid %s alive %s; then rc %d, d9ab %s, folders %s' % (
             rc, r9.get('verdict'), tail, pid, alive, rc2, r9b.get('verdict'), folders()))
    restore('T149k')
    rc, out, info = killed9(['--to', 'd9ab'], {'LINOG_MOCK_P6SLEEP': 'smallbaselineApp', 'LINOG_MOCK_SLEEP_S': '60'},
                            os.path.join(T, 'mark_T149k'))
    case('T149k (v0.12 r2; record 77.12\'s [VERIFY]) SIGKILL to d9ab itself, never to the run\'s group, while MintPy runs on B (the mock '
         'asleep for 60 s, its parent d9ab): MintPy on B ends within 15 s (PR_SET_PDEATHSIG through P3._job_init sends it SIGTERM when '
         'd9ab dies); the run ends, not rc 0',
         info.get('killed') is True and info.get('mock_alive') is False and rc != 0,
         'rc %d; %s' % (rc, info))
    restore('T150')
    ref = (man0.get('decisions') or {}).get('reference_pixel') or {}
    la, lo = ref.get('lat'), ref.get('lon')
    cf = p6_copy('p6_gnss.cfg', 'GNSS_STATIONS', 'NEAR:%.6f:%.6f,FAR:10.0:125.0' % (la - 0.004, lo - 0.003)) if la is not None else None
    rc, out = run([], {'LINOG_PHASE6_CFG': cf}) if cf else (None, '')
    man = json.load(open(os.path.join(W, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')) else {}
    gn = dict((g_.get('station'), g_) for g_ in ((man.get('readings') or {}).get('gnss') or []))
    ne, fa = gn.get('NEAR') or {}, gn.get('FAR') or {}
    d05 = [x for x in ne.get('discs') or [] if x.get('r_km') == 0.5]
    tag_d = 'demErr'
    ok05 = bool(d05) and d05[0].get(tag_d, {}).get('station_cells', 0) > 0 and d05[0].get(tag_d, {}).get('reference_cells', 0) > 0 \
        and abs(d05[0][tag_d]['difference'] - (d05[0][tag_d]['station_median'] - d05[0][tag_d]['reference_median'])) < 1e-9
    upd = os.path.join(W, 'mintpy', 'geo', 'LInOG_Upload_%s' % TAG, '%s_Velocity_demErr.tif' % TAG)
    pr = probe('rings', upd, la, lo, '0,0.5', '%.6f' % (la - 0.004), '%.6f' % (lo - 0.003), 0.5).get('disc') if la is not None else None   # as the cfg names it
    ok05 = ok05 and bool(pr) and [d05[0][tag_d]['station_cells'], d05[0][tag_d]['reference_cells']] == [pr[0], pr[2]] \
        and abs(d05[0][tag_d]['station_median'] - pr[1]) < 1e-9 and abs(d05[0][tag_d]['reference_median'] - pr[3]) < 1e-9
    case('T150 a linog_phase6.cfg with a station 0.5 km from the reference and one far outside the grid: RUN_MANIFEST.json reads the near one '
         'inside the grid (its 0.5 km demErr disc: the cells and medians around it and around the reference as refcheck\'s disc gives them '
         'on the GeoTIFF, the difference their medians\' difference) and the far one outside (no cells, no difference); deliver PASS, rc 0',
         rc == 0 and ne.get('inside') is True and 0.3 < (ne.get('km_from_reference') or 0) < 0.8 and ok05 and fa.get('inside') is False
         and all(x.get(tag_d, {}).get('station_cells') == 0 and x.get(tag_d, {}).get('difference') is None for x in fa.get('discs') or [{}]),
         'rc %s; NEAR %s, 0.5 km %s, the probe %s; FAR %s' % (rc, dict((k, ne.get(k)) for k in ('inside', 'cell', 'km_from_reference')),
                                                               d05[0].get(tag_d) if d05 else None, pr, dict((k, fa.get(k)) for k in ('inside', 'cell'))))

    # ---- v0.8, after the review: the frame's mintpy/ written during the A/B; MintPy on B at the time limit; a re-read after
    # wmask; a changed D9 source after the delivery
    restore('T151')
    touch = os.path.join(W, 'mintpy', 'd9ab_touch.txt')
    rc, out = run(['--to', 'd9ab'], {'LINOG_MOCK_B_TOUCH': touch})
    r9 = rec('5dab', 'd9ab')
    f1 = os.path.join(W, (r9.get('outputs') or {}).get('folder') or '-', 'ab.json')
    j1 = json.load(open(f1)) if os.path.isfile(f1) else {}
    rc2, out2 = run(['--to', 'd9ab'])
    r9b = rec('5dab', 'd9ab')
    case('T151 something writes into the frame\'s mintpy/ while MintPy runs on B (LINOG_MOCK_B_TOUCH): d9ab FAIL at G5dab.9 naming the file, '
         'the A/B void (its ab.json complete false, frame_unchanged false), rc 2; the next run does not read it again: a new A/B, PASS, rc 0',
         rc == 2 and r9.get('verdict') == 'FAIL' and gates(r9).get('G5dab.9') == 'FAIL' and 'd9ab_touch.txt' in note(r9, 'G5dab.9')
         and j1.get('complete') is False and j1.get('frame_unchanged') is False and rc2 == 0 and r9b.get('verdict') == 'PASS'
         and (r9b.get('outputs') or {}).get('reused') is False and len(folders()) == 2,
         'rc %d; G5dab.9 %s %s; ab.json complete %s; then rc %d, d9ab %s, reused %s, folders %s' % (
             rc, gates(r9).get('G5dab.9'), note(r9, 'G5dab.9')[:120], j1.get('complete'), rc2, r9b.get('verdict'),
             (r9b.get('outputs') or {}).get('reused'), folders()))
    restore('T152')
    mk = os.path.join(T, 'mark_T152')
    rc, out = run(['--to', 'd9ab'], {'LINOG_MINTPY_CFG': m_copy('mintpy_d9ab_t3.cfg', 'D9AB_TIMEOUT_S', '3'), 'LINOG_MOCK_P6SLEEP': 'smallbaselineApp',
                                     'LINOG_MOCK_SLEEP_S': '30', 'LINOG_MOCK_MARK': mk})
    r9 = rec('5dab', 'd9ab')
    res = (r9.get('outputs') or {}).get('result') or {}
    pid = re.search(r'pid (\d+)', open(mk).read()).group(1) if os.path.isfile(mk) else None
    case('T152 MintPy on B still running at D9AB_TIMEOUT_S (3 s in a linog_mintpy.cfg copy; the mock asleep 30 s): stopped (its group '
         'ended), G5dab.7 WARN "stopped at the time limit", the rule no by its first condition, d9ab PASS, rc 0; the mock process gone',
         rc == 0 and r9.get('verdict') == 'PASS' and gates(r9).get('G5dab.7') == 'WARN' and 'stopped at the time limit' in val(r9, 'G5dab.7')
         and res.get('verdict') == 'no' and res.get('compared') is False and bool(pid) and not os.path.exists('/proc/%s' % pid),
         'rc %d; G5dab.7 %s; result %s; mock pid %s' % (rc, val(r9, 'G5dab.7')[:100], dict((k, res.get(k)) for k in ('verdict', 'compared', 'brc')), pid))
    rc2, out2 = run(['--to', 'd9ab'])
    r9b = rec('5dab', 'd9ab')
    res2 = (r9b.get('outputs') or {}).get('result') or {}
    case('T152b the same frame again at the default limit: d9ab STALE (its settings), the timed-out A/B not read again (its ab.json incomplete): '
         'a new A/B, compared, PASS, rc 0', rc2 == 0 and 'P5dab d9ab: record STALE' in out2 and (r9b.get('outputs') or {}).get('reused') is False
         and res2.get('compared') is True and len(folders()) == 2, 'rc %d; reused %s; result %s; folders %s' % (
             rc2, (r9b.get('outputs') or {}).get('reused'), dict((k, res2.get(k)) for k in ('verdict', 'compared', 'brc')), folders()))
    restore('T153')
    rc, out = run([])
    m0 = dict((ph, S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))) for i, ph in P6PH if ph != 'd9ab')
    rc2, out2 = run(['--force', 'd9ab'])
    r9 = rec('5dab', 'd9ab')
    case('T153 --force d9ab after a clean run to package (the water mask applied): d9ab reads its A/B again (A\'s mask now the original '
         'wmask kept, the same bytes: the same key), PASS; wmask, dfit, deliver, accept and package stay CURRENT (the decision\'s digest the same): '
         '30 phases skipped (v0.13: bandlimit among them; v0.12: drop1; v0.11: rerun), rc 0', rc == 0 and rc2 == 0 and (r9.get('outputs') or {}).get('reused') is True
         and 'maskTempCoh.orig.h5' in str((r9.get('outputs') or {}).get('a_mask')) and out2.count('skip: PASS on record') == 30
         and all(S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph))) == m0[ph] for i, ph in P6PH if ph != 'd9ab'),
         'rc %d then %d; d9ab reused %s, mask %s; %d skipped' % (rc, rc2, (r9.get('outputs') or {}).get('reused'),
                                                            (r9.get('outputs') or {}).get('a_mask'), out2.count('skip: PASS on record')))
    with open(adm_txt, 'w') as fh:
        fh.write('# the operator names no after the delivery (self-test T153b)\nmintpy.unwrapError.method = no\n')
    rc3, out3 = run([])
    rd = rec('6a', 'deliver')
    case('T153b recon/admission.txt names no after the delivery: admit and d9ab run again (the A/B read again, its source now the '
         'operator\'s), mcfg, sbas and wmask CURRENT; deliver STALE (D9\'s source is in the manifest\'s decision) and stops at G6a.5, rc 4',
         rc3 == 4 and 'P5a admit: record STALE' in out3 and 'P5d sbas: record CURRENT' in out3 and 'P5e wmask: record CURRENT' in out3
         and 'P6a deliver: record STALE' in out3 and gates(rd).get('G6a.5') == 'DECISION' and rec('5dab', 'd9ab').get('verdict') == 'PASS',
         'rc %d; deliver %s %s' % (rc3, rd.get('verdict'), gates(rd).get('G6a.5')))

    stray = sorted(os.path.relpath(p, T) for p in glob.glob(os.path.join(T, ROOT, 'p084', 'f' + FRAME, '*.aux.xml')))
    case('T138 no isce.log or .aux.xml written at the frame root by the Phase 5e and 6 cases, and the kit folder unchanged (the kit\'s '
         'tools write nothing beside themselves; v0.13: bandlimit\'s two kit files among them)', not stray and not os.path.exists(os.path.join(W, 'isce.log'))
         and sorted(os.listdir(os.path.join(T, 'kit'))) == sorted([n for n in os.listdir(os.path.join(S.KITSRC, 'kit3'))
                                                                   if not re.match(r'^__pycache__$', n)] +
                                                                  ['linog_unpack_verify.py', 'linog_shelve_gate.py', 'linog_net_table.py',
                                                                   'linog_fbs_bandlimit.py', 'linog_fbs_downsample.py']),
         'stray %s; kit %s' % (stray, sorted(os.listdir(os.path.join(T, 'kit')))))
