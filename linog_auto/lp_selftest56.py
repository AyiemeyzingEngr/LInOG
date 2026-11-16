#!/usr/bin/env python3
"""lp_selftest56.py -- the Phase 4.5 and 5 cases of the linog_auto self-test (v0.6: report, admit, prep, mcfg, sbas; v0.8: D9
no by default, T104 to T104c),
called by lp_selftest.py after the Phase 3 and 4 cases, on their frame (p3: four dates, 6 pairs, 1000 x 18432, the
multilooked grid 83 x 658), put back to the copy kept after igram (S4f), or after bgrid (S4e) when a case plants
something igram makes.

The kit's linog_admit.py (8cff02ed) and linog_refpix.py (cf7e059d) run as felix pins them. MintPy is a mock
(selftest_kit/mock_mintpy): the package with its version and MintPy 1.6.2's own defaults file (ddae810f), and mock
prep_isce.py and smallbaselineApp.py in the env's bin that write the files a stripmapStack frame gives, with 1.6.2's
step banners, from the template (HEADING from data.rsc; MACRO_CASE template keys into the stack). The mock geometry
is a descending frame's: line 0 north, column 0 east. Planted: LINOG_MOCK_BADPAIR and LINOG_MOCK_FRAGMENT at igram
(the mock FilterAndCoherence and unwrap), LINOG_MOCK_F40, LINOG_MOCK_HEADING and LINOG_MOCK_SBASFAIL in Phase 5, a
flipped lon.rdr, the template edited by hand, and linog_mintpy.cfg copies with a pin changed. The JPEG and HDF5
checks run in the mock env's Python (numpy, matplotlib, h5py); this module needs the standard library only.
v0.6.1 (S14, F49 and F50): LINOG_MOCK_RANDMAG and LINOG_MOCK_NANPAIR at igram, the kit's own
linog_save_insar_images.py (402141d9) run on the same pairs for a byte comparison, and the mock isce loading ISCE's
logging as isce/__init__.py does (T122, T123).
v0.10 (admit's rules R1 to R3, record 108.3): T100 reads the rules' gates (G5a.3w, G5a.6, G5a.7, R1, R3, R2, R4); the T103
family runs with the cull cap at 20 % (cfg/mintpy_cap20.cfg), since the one pair G18 marks is 1 of 6 (16.7 %), over the
shipped 10 %, and T103d runs the shipped cap (the cull refused, WARN, every pair kept); in T117 R3 finds the dead dates
past its limits. The cases run with cfg/mintpy_mock.cfg (R1's land floor scaled to the mock grid).
v0.12 (record 124.7): admit hands the flagged pair to drop1 instead of culling it, so T103, T103c and T103d keep 6 of 6
(R2 INFO, D3 PASS), and T103b moves mintpy/ aside before the operator's run (mcfg's G5c.4, the first run having gone on
to sbas); drop1's own cases are lp_selftest12's.
"""
import glob
import json
import os
import re
import shutil
import subprocess

ROOT, FRAME = 'p3', '3320'
P45 = (('4g', 'report'), ('5a', 'admit'), ('5b', 'prep'), ('5c', 'mcfg'), ('5d', 'sbas'))
PAIR = '20080830_20081130'   # 20080830 and 20081130 keep 2 pairs each without it
KIT_IMG_MD5 = '402141d9f81697012d42119aec440b88'   # the course kit's linog_save_insar_images.py, whose pages the report keeps
PROBE = r'''
import json, sys
what, args = sys.argv[1], sys.argv[2:]
if what == 'jpeg':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.image as mpimg
    a = mpimg.imread(args[0]).astype(float)
    a = a.mean(axis=2) if a.ndim == 3 else a
    h, w = a.shape
    q = lambda r0, r1, c0, c1: float(a[r0:r1, c0:c1].mean())
    print(json.dumps(dict(shape=[h, w], tr=q(0, h // 4, w - w // 4, w), tl=q(0, h // 4, 0, w // 4), br=q(h - h // 4, h, w - w // 4, w))))
elif what == 'h5attrs':
    import h5py
    with h5py.File(args[0], 'r') as f:
        d = {k: (v.decode() if isinstance(v, bytes) else str(v)) for k, v in f.attrs.items() if k in args[1:]}
        d['_datasets'] = sorted(f.keys())
        if 'dropIfgram' in f:
            d['_drop'] = ['%s_%s' % (x[0].decode(), x[1].decode()) for x, k in zip(f['date'][:], f['dropIfgram'][:]) if not k]
    print(json.dumps(d))
elif what == 'fliplon':
    import numpy as np
    gw, gl = int(args[1]), int(args[2])
    a = np.fromfile(args[0], '<f8', count=gw * gl).reshape(gl, gw)
    np.fliplr(a).astype('<f8').tofile(args[0])
    print(json.dumps(dict(col0=float(a[:, 0].mean()), colN=float(a[:, -1].mean()))))
elif what == 'jpegblock':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.image as mpimg
    a = mpimg.imread(args[0]).astype(float)
    r0, r1, c0, c1 = (int(v) for v in args[1:5])
    print(json.dumps(dict(shape=list(a.shape[:2]), mean=float(a[r0:r1, c0:c1].mean()), min=float(a[r0:r1, c0:c1].min()))))
elif what == 'stretchtop':   # the kit's stretch on a pair's magnitudes, in this Python's numpy
    import numpy as np
    gw, gl = int(args[1]), int(args[2])
    mag = np.abs(np.fromfile(args[0], '<c8', count=gw * gl))
    v = mag[mag > 1e-6]
    a, b = np.percentile(v, 1.0), np.percentile(v, 99.0)
    top = float(((np.clip(mag, a, b) - a) / (b - a)).max())
    print(json.dumps(dict(numpy=np.__version__, percentile=type(a).__name__, top=top,
                          steps=int(round((top - 1.0) / float(np.finfo(np.float32).eps))))))
elif what == 'iscelog':   # the mock isce's logging, then matplotlib's start-up, as the report's process had them in S14
    import io, logging, os
    import isce  # noqa: F401
    buf = io.StringIO()
    root = logging.getLogger()
    for h in root.handlers:
        if type(h) is logging.StreamHandler:   # the console handler (stdout); the file handler writes isce.log here
            h.setStream(buf)
    import matplotlib  # noqa: F401
    lines = buf.getvalue().splitlines()
    log = os.path.join(os.getcwd(), 'isce.log')
    print(json.dumps(dict(root=logging.getLevelName(root.level), handlers=sorted(type(h).__name__ for h in root.handlers),
                          debug=len([x for x in lines if ' - matplotlib - DEBUG - ' in x]), first=lines[0] if lines else '',
                          isce_log_lines=len(open(log).read().splitlines()) if os.path.isfile(log) else None)))
elif what == 'kitimg':   # the kit's own linog_save_insar_images.py on a pair, handed the array the report shows
    import contextlib, hashlib, importlib.util, io, os, re, shutil
    import numpy as np
    src, work, fud, flr, kitpy = args[0], args[1], args[2] == 'True', args[3] == 'True', args[4]
    x = open(src + '.xml').read()
    gw, gl = (int(re.search(r'name="%s">\s*<value>(\d+)' % n, x).group(1)) for n in ('width', 'length'))
    z = np.fromfile(src, '<c8', count=gw * gl).reshape(gl, gw)
    z = np.flipud(z) if fud else z
    z = np.fliplr(z) if flr else z
    os.makedirs(work)
    dst = os.path.join(work, os.path.basename(src))
    np.flipud(z).astype('<c8').tofile(dst)   # the kit flips up-down itself: its image is then the report's
    shutil.copy(src + '.xml', dst + '.xml')
    spec = importlib.util.spec_from_file_location('linog_save_insar_images', kitpy)
    k = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(k)
    with contextlib.redirect_stdout(io.StringIO()):
        k.save_images(dst)
    md = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None
    print(json.dumps(dict(phase=md(dst.replace('.int', '_phase.jpg')), combined=md(dst.replace('.int', '_combined.jpg')))))
'''


def phase56(T, case, S):
    import lp_selftest34 as S34
    W = S.fdir(T, FRAME, ROOT)
    E = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MINTPY_CFG': os.path.join(T, 'cfg', 'mintpy_mock.cfg')}   # v0.10: the mock floor
    mp = S.real_pins('linog_mintpy.cfg')
    py = S.MOCKPY[0]

    def run(args, extra=None, decide='auto', keep_default=False):
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p3.cfg', env_extra=dict(E, **(extra or {})),
                     keep_default=keep_default)

    def rec(idx, ph):
        return S.rec(T, FRAME, idx, ph, ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def val(r, gid):
        return dict((x['id'], x.get('value', '')) for x in r.get('gates', [])).get(gid, '')

    def restore(name, tag):
        S.aside(T, W, 'p56_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', name), W, symlinks=True, copy_function=S34.link_or_copy)

    def probe(*args, **kw):
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'MPLCONFIGDIR': os.path.join(T, 'mplconfig_probe'),
               'PYTHONDONTWRITEBYTECODE': '1'}
        if kw.get('site'):   # the mock env's site-packages and isce's components (the kit's `import isceobj`) on the path
            site = os.path.join(T, 'mockconda', 'envs', 'linog_isce2', 'lib', 'site-packages')
            env.update(PYTHONPATH='%s:%s' % (site, os.path.join(site, 'isce', 'components')), MPLBACKEND='Agg')
        if kw.get('cwd'):
            os.makedirs(kw['cwd'], exist_ok=True)
        p = subprocess.run([py, '-B', '-c', PROBE] + [str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                           cwd=kw.get('cwd'))
        try:
            return json.loads(p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': p.stdout.decode('utf-8', 'replace')[-300:]}

    def listing(d):
        out = []
        for dp, dn, fn in os.walk(d):
            dn.sort()
            for n in sorted(fn):
                q = os.path.join(dp, n)
                st = os.lstat(q)
                out.append((os.path.relpath(q, d), st.st_size, st.st_mtime_ns))
        return out

    def cfgv(path):
        d = {}
        for ln in open(path) if os.path.isfile(path) else []:
            m = re.match(r'^\s*([A-Za-z][\w.]*)\s*=\s*([^#]*?)\s*(#.*)?$', ln)
            if m:
                d[m.group(1)] = m.group(2)
        return d

    def mcfg_copy(name, key, value):
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

    tm = os.path.join(W, 'mintpy', 'smallbaselineApp.cfg')
    print('-- Phases 4.5 and 5 (report, admit, prep, mcfg, sbas): the kit\'s admit and refpix, a mock MintPy 1.6.2 with its own '
          'defaults file; the Phase 3 frame (6 pairs, 83 x 658)')
    kit = (('kit3/linog_admit.py', 'KIT_ADMIT_MD5'), ('kit3/linog_refpix.py', 'KIT_REFPIX_MD5'),
           ('mock_mintpy/mintpy/defaults/smallbaselineApp.cfg', 'MINTPY_DEFAULTS_MD5'))
    same = [n for n, k in kit if S.md5(os.path.join(S.KITSRC, n)) == mp.get(k)]
    case('T99 the self-test runs the kit\'s admit and refpix and MintPy 1.6.2\'s defaults file as felix pins them (md5s = '
         'linog_mintpy.cfg)', len(same) == len(kit), '%d of %d' % (len(same), len(kit)))
    if not os.path.isdir(os.path.join(T, 'snap_p3', 'S4f')) or not os.path.isdir(os.path.join(T, 'snap_p3', 'S4e')):
        case('T100-T123 not run: no copy of the frame after bgrid and igram (the Phase 3 and 4 cases stopped early)', False)
        return
    h5 = subprocess.run([py, '-B', '-c', 'import h5py, numpy, matplotlib'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1',
                             'MPLCONFIGDIR': os.path.join(T, 'mplconfig_probe')}).returncode == 0
    if not h5:
        case('T100-T123 not run: the mock MintPy needs h5py, and %s has none' % py, False)
        return

    # ---- the clean frame after igram, to sbas
    restore('S4f', 'T100')
    rc, out = run(['--to', 'sbas'])
    logl100 = [ln for ln in out.splitlines() if ' - DEBUG - ' in ln or ' - INFO - ' in ln]   # ISCE's log format (T123)
    R = {ph: rec(i, ph) for i, ph in P45}
    g = {}
    for r in R.values():
        g.update(gates(r))
    want = ('G4g.1', 'G4g.3', 'G4g.4', 'G4g.5', 'G4g.6', 'G5a.3', 'G5a.3w', 'G20', 'G5a.7', 'R3', 'R2', 'D3', 'G5a.5', 'D9', 'G5b.2m',
            'G5b.3', 'N20', 'N13', 'G12', 'G5b.7', 'G5c.5', 'G5c.6', 'G24c', 'G5c.7', 'G5d.1t', 'G5d.3k', 'G5d.5', 'G15', 'G24', 'G5d.6',
            'G19', 'G5d.7', 'G5d.8')
    wrong = dict((k, g.get(k)) for k in want if g.get(k) != 'PASS')
    info = dict((k, g.get(k)) for k in ('G5a.4', 'G5a.6', 'R1', 'R4') if g.get(k) != 'INFO')
    case('T100 clean, the frame after igram to sbas (auto): rc 0, the 5 records PASS; G4g.3 to G5d.8 PASS (%d gates, v0.10: the water '
         'tool\'s pin, the kit\'s arithmetic recomputed, R3 and R2 with nothing to exclude); G5a.4 (no operator file), G5a.6 (the land '
         'over the floor), R1 (no pair flagged over land) and R4 (no screened date) INFO' % len(want),
         rc == 0 and all(R[ph].get('verdict') == 'PASS' for ph in R) and not wrong and not info,
         'rc %d; %s; not PASS: %s; not INFO: %s' % (rc, [(ph, R[ph].get('verdict')) for ph in R], wrong, info))
    orp, oa, orm, ors = (R[ph].get('outputs', {}) for ph in ('report', 'admit', 'mcfg', 'sbas'))
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    t = cfgv(tm)
    yx = ors.get('refpix', {}).get('yx') or [None, None]
    ts = probe('h5attrs', os.path.join(W, 'mintpy', 'timeseries.h5'), 'REF_Y', 'REF_X')
    st = probe('h5attrs', os.path.join(W, 'mintpy', 'inputs', 'ifgramStack.h5'), 'HEADING', 'ORBIT_DIRECTION')
    sn = [float(x) for x in t.get('mintpy.geocode.SNWE', '0,0,0,0').split(',')] if t.get('mintpy.geocode.SNWE', 'auto') != 'auto' else []
    lat_ok = len(sn) == 4 and all(abs(round(v * 1200) - v * 1200) < 1e-3 for v in sn) and sn[0] < 14.55 and sn[1] > 15.09
    case('T100b the products: 12 JPEGs and 1 page; admission.json keeps 6 of 6 (excludeDate no, excludeDate12 auto, unwrapError no); '
         'the template: ORBIT_DIRECTION descending, SNWE on the 1/1200 deg lattice around the geometry, reference.yx the kit\'s pick = '
         'timeseries.h5 REF_Y, REF_X; the stack HEADING -168.94',
         orp.get('pairs') == 6 and orp.get('jpegs') == 12 and orp.get('pages') == 1
         and os.path.isfile(os.path.join(W, 'Igrams', 'reports', 'P084F3320_Igram_Report_Page_1.jpg'))
         and adm.get('kept') == 6 and adm.get('cfg', {}).get('mintpy.network.excludeDate') == 'no'
         and adm.get('cfg', {}).get('mintpy.network.excludeDate12') == 'auto' and adm.get('cfg', {}).get('mintpy.unwrapError.method') == 'no'
         and t.get('ORBIT_DIRECTION') == 'descending' and lat_ok and orm.get('snwe') == t.get('mintpy.geocode.SNWE')
         and yx[0] is not None and t.get('mintpy.reference.yx') == '%s,%s' % tuple(yx) and [ts.get('REF_Y'), ts.get('REF_X')] == [str(v) for v in yx]
         and st.get('HEADING') == '-168.94' and st.get('ORBIT_DIRECTION') == 'descending',
         'report %s/%s/%s; admit %s %s; ORBIT_DIRECTION %s; SNWE %s; yx %s, template %s, timeseries %s,%s; stack %s %s' % (
             orp.get('pairs'), orp.get('jpegs'), orp.get('pages'), adm.get('kept'), adm.get('cfg'), t.get('ORBIT_DIRECTION'),
             t.get('mintpy.geocode.SNWE'), yx, t.get('mintpy.reference.yx'), ts.get('REF_Y'), ts.get('REF_X'), st.get('HEADING'),
             st.get('ORBIT_DIRECTION')))
    led = open(os.path.join(W, 'logs', 'STATUS.txt')).read()
    logs = [os.path.join(W, 'logs', 'p5', d) for d in ('prep', 'mcfg', 'sbas')]
    d9, g19 = val(R['admit'], 'D9'), val(R['sbas'], 'G19')
    case('T100c the ledger: auto_<phase> END rc=0 for the 5 phases; prep, mcfg and sbas logs kept; D9 (fraction 1.0000: no) and '
         'the kit\'s G19 fraction agree', all('auto_%s END rc=0' % ph in led for _, ph in P45) and all(os.path.isdir(x) and os.listdir(x)
                                                                                                      for x in logs)
         and 'mean component fraction 1.0000' in d9 and 'the kit\'s mean component fraction 1.0000 (admit\'s D9: 1.0000)' in g19,
         'D9: %s | G19: %s' % (d9[:90], g19[:110]))

    m0 = dict((ph, S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))) for i, ph in P45)
    rc, out = run(['--to', 'sbas'])
    case('T101 re-run to sbas: all 23 phases skipped (v0.13: bandlimit among them), rc 0, the 5 records unchanged (v0.7\'s default, '
         'package, is T126\'s)',
         rc == 0 and out.count('skip: PASS on record') == 23 and all(m0[ph] and S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))
                                                                     == m0[ph] for i, ph in P45),
         'rc %d; %d skipped' % (rc, out.count('skip: PASS on record')))
    if rc == 0 and all(R[ph].get('verdict') == 'PASS' for ph in R):   # v0.7: the frame after sbas, for the Phase 5e and 6 cases
        shutil.copytree(W, os.path.join(T, 'snap_p3', 'S5d'), symlinks=True, copy_function=S34.link_or_copy)

    jc = probe('jpeg', os.path.join(W, 'Igrams', 'reports', 'pairs', 'filt_%s_combined.jpg' % PAIR))
    jp = probe('jpeg', os.path.join(W, 'Igrams', 'reports', 'pairs', 'filt_%s_phase.jpg' % PAIR))
    case('T102 the report is north up for a descending frame: the bright corner of line 0 and column 0 (north-east) is top right '
         'in the combined JPEG, 83 x 658 px; the page title names the flip',
         jc.get('shape') == [658, 83] and jp.get('shape') == [658, 83] and jc.get('tr', 0) > 60 and jc.get('tl', 255) < 20
         and jc.get('br', 255) < 20 and 'north up by a left-right flip' in orp.get('note', ''),
         'combined %s; phase %s; note %s' % (jc, jp.get('shape'), orp.get('note')))

    # ---- a hand edit after the run
    txt = open(tm).read()
    open(tm, 'w').write(re.sub(r'(?m)^(mintpy\.reference\.yx\s*=\s*)\d+,\d+', r'\g<1>30,40', txt, count=1))
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    case('T110 reference.yx edited by hand after the run: mcfg still CURRENT (its digest leaves reference.yx out), sbas STALE; its '
         're-run stops at G5d.4 (DECISION: the products in the way), rc 4, the edit kept',
         rc == 4 and 'P5c mcfg: record CURRENT' in out and 'P5d sbas: record STALE' in out and rs.get('verdict') == 'DECISION'
         and gates(rs).get('G5d.4') == 'DECISION' and cfgv(tm).get('mintpy.reference.yx') == '30,40',
         'rc %d; sbas %s %s' % (rc, rs.get('verdict'), gates(rs).get('G5d.4')))
    txt = open(tm).read()
    open(tm, 'w').write(re.sub(r'(?m)^(mintpy\.deramp\s*=\s*)linear', r'\g<1>no', txt, count=1))
    rc, out = run(['--to', 'sbas'])
    rm = rec('5c', 'mcfg')
    tail = open(os.path.join(W, 'logs', 'STATUS.txt')).read().split('auto_mcfg START')[-1]
    case('T109 a template value edited by hand (deramp linear -> no): mcfg STALE; its re-run stops at G5c.4 (DECISION: mintpy/ in '
         'the way), rc 4; the edit kept, sbas not run', rc == 4 and 'P5c mcfg: record STALE' in out and rm.get('verdict') == 'DECISION'
         and gates(rm).get('G5c.4') == 'DECISION' and cfgv(tm).get('mintpy.deramp') == 'no' and 'auto_sbas START' not in tail,
         'rc %d; mcfg %s %s; deramp %s' % (rc, rm.get('verdict'), gates(rm).get('G5c.4'), cfgv(tm).get('mintpy.deramp')))

    # ---- a MintPy step fails, then the same run again; then re-runs that must not reach MintPy's outputs
    restore('S4f', 'T113')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_SBASFAIL': 'invert_network'})
    rs = rec('5d', 'sbas')
    gs = gates(rs)
    case('T113 a MintPy step fails (invert_network raises): sbas FAIL at G5d.7, rc 2; G5d.5, G15, G24, G5d.6 and G19 PASS before it; '
         'the reason names the log', rc == 2 and rs.get('verdict') == 'FAIL' and gs.get('G5d.7') == 'FAIL'
         and all(gs.get(k) == 'PASS' for k in ('G5d.5', 'G15', 'G24', 'G5d.6', 'G19')) and 'smallbaseline_refpoint_geocode.log' in
         json.dumps(rs.get('gates', [])), 'rc %d; %s' % (rc, gs))
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    case('T113b the same run again without the plant: sbas re-runs from load_data (nothing in the way: the failed step wrote no '
         'timeseries.h5, velocity.h5 or geo/) and PASSes, rc 0', rc == 0 and rs.get('verdict') == 'PASS'
         and gates(rs).get('G5d.4') == 'PASS', 'rc %d; sbas %s' % (rc, rs.get('verdict')))
    m0 = dict((ph, S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))) for i, ph in P45)
    j0 = os.stat(os.path.join(W, 'recon', 'admission.json')).st_mtime_ns
    rc, out = run(['--to', 'sbas', '--force', 'admit'])
    case('T114 --force admit after a clean run: admit re-runs and decides the same (admission.json written again); prep, mcfg and '
         'sbas stay CURRENT (they read admit\'s decisions, not the file\'s time): 22 phases skipped (v0.13: bandlimit), rc 0',
         rc == 0 and out.count('skip: PASS on record') == 22 and rec('5a', 'admit').get('verdict') == 'PASS'
         and os.stat(os.path.join(W, 'recon', 'admission.json')).st_mtime_ns != j0
         and all(S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph))) == m0[ph] for i, ph in P45 if ph != 'admit'),
         'rc %d; %d skipped' % (rc, out.count('skip: PASS on record')))
    m0 = dict((ph, S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph)))) for i, ph in P45)
    rc, out = run(['--to', 'report', '--force', 'report'])
    rr = rec('4g', 'report')
    case('T119 --force report after a clean run: report DECISION at G4g.4 naming Igrams/reports only (no phase reads the report, '
         'so nothing of MintPy\'s is to be moved), rc 4', rc == 4 and gates(rr).get('G4g.4') == 'DECISION'
         and val(rr, 'G4g.4') == 'in the frame already: Igrams/reports', 'rc %d; G4g.4 %s' % (rc, val(rr, 'G4g.4')))
    os.makedirs(os.path.join(W, '_archive', 'T119'), exist_ok=True)
    os.rename(os.path.join(W, 'Igrams', 'reports'), os.path.join(W, '_archive', 'T119', 'reports'))
    rsc = sorted(os.path.relpath(p, W) for p in glob.glob(os.path.join(W, 'Igrams', '*', '*.unw.rsc')) +
                 glob.glob(os.path.join(W, 'geom_reference', '*.rsc')) + glob.glob(os.path.join(W, 'SLC', '*', 'data.rsc')))
    for rel in rsc:
        dst = os.path.join(W, '_archive', 'T120_rsc', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(os.path.join(W, rel), dst)
    rc, out = run(['--to', 'sbas'])
    case('T120 T119\'s report and the .rsc files moved aside: report and prep re-run and PASS (prep writes the same bytes); mcfg '
         'and sbas stay CURRENT (mcfg reads the .rsc contents, not their times), rc 0', rc == 0 and 'P5b prep: record STALE' in out
         and rec('4g', 'report').get('verdict') == 'PASS'
         and rec('5b', 'prep').get('verdict') == 'PASS' and 'P5c mcfg: record CURRENT' in out and 'P5d sbas: record CURRENT' in out
         and all(S34.md5q(os.path.join(W, 'status', 'P%s_%s.json' % (i, ph))) == m0[ph] for i, ph in (('5c', 'mcfg'), ('5d', 'sbas')))
         and len(rsc) == 13, 'rc %d; %d .rsc moved; report %s' % (rc, len(rsc), rec('4g', 'report').get('verdict')))

    restore('S4f', 'T113c')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_SBASFAIL': 'invert_network:late'})
    rs = rec('5d', 'sbas')
    rc2, out2 = run(['--to', 'sbas'])
    rs2 = rec('5d', 'sbas')
    case('T113c a MintPy step fails after writing timeseries.h5 (as ifgram_inversion can): sbas FAIL at G5d.7, rc 2; the run again '
         'stops at G5d.4 (DECISION) naming mintpy/timeseries.h5, rc 4', rc == 2 and gates(rs).get('G5d.7') == 'FAIL' and rc2 == 4
         and gates(rs2).get('G5d.4') == 'DECISION' and 'mintpy/timeseries.h5' in val(rs2, 'G5d.4'),
         'rc %d then %d; G5d.4 %s' % (rc, rc2, val(rs2, 'G5d.4')))

    # ---- the reference pixel: the operator's, MintPy's plots
    restore('S4f', 'T115')
    with open(os.path.join(W, 'recon', 'refpix.txt'), 'w') as fh:
        fh.write('# the operator\'s reference pixel (self-test T115)\nmintpy.reference.yx = 100,40\n')
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    ts = probe('h5attrs', os.path.join(W, 'mintpy', 'timeseries.h5'), 'REF_Y', 'REF_X')
    case('T115 recon/refpix.txt names 100,40: sbas PASS with G5d.3o INFO and G19 on the operator\'s pixel (the kit\'s pick noted); '
         'REF_Y, REF_X 100,40 in timeseries.h5 and on the template line, rc 0', rc == 0 and rs.get('verdict') == 'PASS'
         and gates(rs).get('G5d.3o') == 'INFO' and 'y,x 100,40 (the operator' in val(rs, 'G19') and 'the kit picked 20,20' in val(rs, 'G19')
         and [ts.get('REF_Y'), ts.get('REF_X')] == ['100', '40'] and cfgv(tm).get('mintpy.reference.yx') == '100,40',
         'rc %d; G19 %s; timeseries %s,%s' % (rc, val(rs, 'G19')[:120], ts.get('REF_Y'), ts.get('REF_X')))
    with open(os.path.join(W, 'recon', 'refpix.txt'), 'a') as fh:
        fh.write('# a comment added later (self-test T115b)\n')
    rc, out = run(['--to', 'sbas'])
    case('T115b a comment added to recon/refpix.txt: the pixel it names is the same, so all 23 phases skipped (v0.13: bandlimit), rc 0',
         rc == 0 and out.count('skip: PASS on record') == 23, 'rc %d; %d skipped' % (rc, out.count('skip: PASS on record')))
    with open(os.path.join(W, 'recon', 'refpix.txt'), 'w') as fh:
        fh.write('mintpy.reference.yx = 120,40\n')
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    case('T115c recon/refpix.txt names another pixel after the run: sbas STALE; its re-run stops at G5d.4 (DECISION: the products '
         'in the way), rc 4', rc == 4 and 'P5d sbas: record STALE' in out and gates(rs).get('G5d.4') == 'DECISION',
         'rc %d; G5d.4 %s' % (rc, gates(rs).get('G5d.4')))
    with open(os.path.join(W, 'recon', 'refpix.txt'), 'w') as fh:
        fh.write('mintpy.reference.yx = 120 40\n')
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    case('T115d recon/refpix.txt unreadable ("120 40"): sbas FAIL at G5d.3o before anything runs (no G5d.4, no MintPy call), rc 2',
         rc == 2 and gates(rs).get('G5d.3o') == 'FAIL' and 'G5d.4' not in gates(rs), 'rc %d; %s' % (rc, gates(rs)))
    restore('S4f', 'T121')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_PLOTFAIL': '1'})
    rs = rec('5d', 'sbas')
    case('T121 MintPy\'s plots fail after the last step (the products made): G5d.7 WARN, sbas PASS, rc 0; the single-step calls '
         '(load_data, modify_network, the bootstrap) plot nothing', rc == 0 and rs.get('verdict') == 'PASS'
         and gates(rs).get('G5d.7') == 'WARN' and 'failed after the last step' in val(rs, 'G5d.7')
         and os.path.isdir(os.path.join(W, 'mintpy', 'pic')) and 'plot & save' not in open(
             os.path.join(W, 'logs', 'p5', 'sbas', 'smallbaseline_modify_network.log.v1')).read(),
         'rc %d; G5d.7 %s' % (rc, val(rs, 'G5d.7')))

    # ---- D3: a pair G18 marks, under ask, then the operator's choice; under auto. v0.12 (record 124.7): admit culls no pair by
    # R2 alone, it hands the flagged pair to drop1 (after sbas; lp_selftest12's cases), so admit and sbas keep all 6 pairs
    C20 = {'LINOG_MINTPY_CFG': mcfg_copy('mintpy_cap20.cfg', 'ADMIT_CULL_MAX_FRAC', '0.20')}
    restore('S4e', 'T103')
    rc, out = run(['--to', 'sbas'], dict(C20, LINOG_MOCK_BADPAIR=PAIR), decide='ask')
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    hand = (adm.get('decisions') or {}).get('drop1') or {}
    case('T103 a pair of random phase (G18 marks it, over land too) under --decide ask, R2\'s cap at 20 %: igram and report PASS; v0.12: '
         'admit hands the pair to drop1 (R2 INFO, decisions.drop1 names it, LOGIC 4), D3 PASS (nothing excluded by admit), 6 of 6 kept; '
         'sbas PASS, rc 0',
         rc == 0 and rec('4f', 'igram').get('verdict') == 'PASS' and rec('4g', 'report').get('verdict') == 'PASS'
         and gates(ra).get('R2') == 'INFO' and ra.get('verdict') == 'PASS' and ra.get('logic') == 4 and gates(ra).get('D3') == 'PASS'
         and hand.get('in_network') == [PAIR] and PAIR in (hand.get('land') or []) and PAIR in (hand.get('whole') or [])
         and adm.get('kept') == 6 and rs.get('verdict') == 'PASS', 'rc %d; admit %s; R2 %s; D3 %s; to drop1 %s; kept %s' % (
             rc, ra.get('verdict'), val(ra, 'R2')[:80], gates(ra).get('D3'), hand.get('in_network'), adm.get('kept')))
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator\'s choice (self-test T103b)\nmintpy.network.excludeDate12 = %s\n' % PAIR)
    os.makedirs(os.path.join(W, '_archive'), exist_ok=True)
    os.rename(os.path.join(W, 'mintpy'), os.path.join(W, '_archive', 'T103b_mintpy'))   # mcfg's way, as the operator clears it
    rc, out = run(['--to', 'sbas'], C20, decide='ask')
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    stk = probe('h5attrs', os.path.join(W, 'mintpy', 'inputs', 'ifgramStack.h5'))
    case('T103b recon/admission.txt names the pair (mintpy/ moved aside first, as mcfg\'s G5c.4 asks): admit PASS (D3 INFO, the '
         'operator\'s), 5 of 6 kept; sbas PASS with the pair dropped in the stack (G5d.6), rc 0', rc == 0 and ra.get('verdict') == 'PASS'
         and gates(ra).get('D3') == 'INFO' and adm.get('kept') == 5
         and PAIR not in adm.get('kept_pairs', []) and rs.get('verdict') == 'PASS' and stk.get('_drop') == [PAIR]
         and rs.get('outputs', {}).get('dropped') == 1, 'rc %d; admit %s D3 %s; kept %s; stack drops %s' % (
             rc, ra.get('verdict'), gates(ra).get('D3'), adm.get('kept'), stk.get('_drop')))
    restore('S4e', 'T103c')
    rc, out = run(['--to', 'sbas'], dict(C20, LINOG_MOCK_BADPAIR=PAIR))
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    case('T103c the same pair under --decide auto (the 20 % cap): v0.12, admit hands it to drop1 (R2 INFO) and excludes nothing (D3 PASS, '
         'the rules R1 to R3: nothing to exclude), 6 of 6 kept; sbas PASS, rc 0', rc == 0 and gates(ra).get('R2') == 'INFO'
         and gates(ra).get('D3') == 'PASS' and 'nothing to exclude' in val(ra, 'D3') and adm.get('kept') == 6
         and adm.get('cfg', {}).get('mintpy.network.excludeDate12') == 'auto' and rs.get('verdict') == 'PASS',
         'rc %d; R2 %s; D3 %s; kept %s' % (rc, gates(ra).get('R2'), val(ra, 'D3')[:100], adm.get('kept')))
    restore('S4e', 'T103d')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_BADPAIR': PAIR})
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    stk = probe('h5attrs', os.path.join(W, 'mintpy', 'inputs', 'ifgramStack.h5'))
    case('T103d the same pair under the shipped cap (10 %): admit as under 20 % (R2 INFO, D3 PASS, 6 of 6 kept: the cap now bounds '
         'drop1\'s cull, T322); sbas PASS with no pair dropped, rc 0',
         rc == 0 and gates(ra).get('R2') == 'INFO' and 'drop1' in val(ra, 'R2') and gates(ra).get('D3') == 'PASS' and adm.get('kept') == 6
         and rs.get('verdict') == 'PASS' and stk.get('_drop') == [], 'rc %d; R2 %s; D3 %s; kept %s; drops %s' % (
             rc, val(ra, 'R2')[:90], gates(ra).get('D3'), adm.get('kept'), stk.get('_drop')))

    # ---- D9 (v0.8): admit takes no whatever the fraction; the operator's bridging goes through mcfg and sbas
    restore('S4e', 'T104')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_FRAGMENT': '1'}, decide='ask')
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    case('T104 every pair\'s main component on the top 30 % of lines (fraction 0.2864, under v0.6\'s bridging anchor), --decide ask: '
         'admit PASS with D9 PASS, unwrapError no (MintPy\'s default; the fraction kept as evidence); sbas PASS without bridging, rc 0 (v0.8)',
         rc == 0 and ra.get('verdict') == 'PASS' and gates(ra).get('D9') == 'PASS' and 'mean component fraction 0.2864' in val(ra, 'D9')
         and 'unwrapError.method = no (MintPy' in val(ra, 'D9') and rs.get('verdict') == 'PASS'
         and cfgv(tm).get('mintpy.unwrapError.method') == 'no' and 'unwrapPhase_bridging present' not in val(rs, 'G5d.8'),
         'rc %d; admit %s; D9 %s; sbas %s' % (rc, ra.get('verdict'), val(ra, 'D9')[:140], rs.get('verdict')))
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator chooses bridging after the run (self-test T104b)\nmintpy.unwrapError.method = bridging\n')
    rc, out = run(['--to', 'sbas'], decide='ask')
    ra, rm = rec('5a', 'admit'), rec('5c', 'mcfg')
    case('T104b recon/admission.txt names bridging after the run: admit STALE, re-runs with D9 INFO (the operator\'s); mcfg STALE stops '
         'at G5c.4 (DECISION: mintpy/ in the way), rc 4 (the path d9ab\'s DECISION note describes)',
         rc == 4 and 'P5a admit: record STALE' in out and gates(ra).get('D9') == 'INFO' and 'bridging (the operator' in val(ra, 'D9')
         and rm.get('verdict') == 'DECISION' and gates(rm).get('G5c.4') == 'DECISION',
         'rc %d; D9 %s %s; mcfg %s %s' % (rc, gates(ra).get('D9'), val(ra, 'D9')[-60:], rm.get('verdict'), gates(rm).get('G5c.4')))
    os.makedirs(os.path.join(W, '_archive', 'T104c'), exist_ok=True)
    os.rename(os.path.join(W, 'mintpy'), os.path.join(W, '_archive', 'T104c', 'mintpy'))
    rc, out = run(['--to', 'sbas'], decide='ask')
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    t = cfgv(tm)
    g19 = val(rs, 'G19')
    m1 = re.search(r'the kit\'s mean component fraction ([\d.]+) \(admit\'s D9: ([\d.]+)\)', g19)
    case('T104c mintpy/ moved into _archive/: mcfg and sbas run again with unwrapError bridging and a linear ramp in the template; sbas '
         'PASS with unwrapPhase_bridging in the stack; the kit\'s G19 fraction = admit\'s D9 (0.2864), rc 0',
         rc == 0 and gates(ra).get('D9') == 'INFO' and t.get('mintpy.unwrapError.method') == 'bridging'
         and t.get('mintpy.unwrapError.ramp') == 'linear' and rs.get('verdict') == 'PASS' and 'unwrapPhase_bridging present' in val(rs, 'G5d.8')
         and bool(m1) and m1.group(1) == m1.group(2) == '0.2864',
         'rc %d; D9 %s; unwrapError %s ramp %s; sbas %s; G19 %s' % (rc, gates(ra).get('D9'), t.get('mintpy.unwrapError.method'),
                                                                 t.get('mintpy.unwrapError.ramp'), rs.get('verdict'), g19[:100]))

    # ---- G19: no pixel unwrapped in every kept pair
    restore('S4e', 'T116')
    X, Y = '20080830_20090302', '20081130_20090602'
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# self-test T116: D9 falls between its anchors here\nmintpy.unwrapError.method = no\n')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_CCTOP': X, 'LINOG_MOCK_CCBOTTOM': Y})
    rs = rec('5d', 'sbas')
    case('T116 two pairs unwrapped on disjoint parts of the frame (no pixel in every kept pair): the kit walks down to 0.80 and picks '
         '20,20, masked in %s: G19 DECISION before MintPy is asked, saying no pixel can work and pointing to recon/admission.txt, '
         'rc 4' % Y, rc == 4 and rs.get('verdict') == 'DECISION' and gates(rs).get('G19') == 'DECISION' and Y in json.dumps(rs.get('gates', []))
         and 'no pixel is unwrapped in every kept pair' in json.dumps(rs.get('gates', [])) and 'admission.txt' in json.dumps(rs.get('gates', []))
         and not os.path.exists(os.path.join(W, 'mintpy', 'timeseries.h5')), 'rc %d; G19 %s' % (rc, val(rs, 'G19')[:140]))
    with open(os.path.join(W, 'recon', 'refpix.txt'), 'w') as fh:
        fh.write('mintpy.reference.yx = 20,20\n')
    rc, out = run(['--to', 'sbas'])
    rs = rec('5d', 'sbas')
    case('T116b recon/refpix.txt names that same masked pixel: sbas re-runs (its input changed) and FAILs at G19 (the operator\'s '
         'pixel is not usable), rc 2', rc == 2 and 'P5d sbas: record DECISION' in out and gates(rs).get('G19') == 'FAIL'
         and Y in json.dumps(rs.get('gates', [])), 'rc %d; G19 %s' % (rc, gates(rs).get('G19')))

    # ---- D3: the kit's proposal would split the network
    restore('S4e', 'T117')
    cross = '20080830_20090302,20080830_20090602,20081130_20090302,20081130_20090602'
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_CCSMALL': cross})
    ra = rec('5a', 'admit')
    case('T117 G18 marks the four pairs between {20080830, 20081130} and {20090302, 20090602}: the kit exits 1 (its whole-grid proposal '
         'leaves 2 components): G20 WARN; R3 (v0.10): each date dead in turn (2 of its 3 pairs, then the rest), past its limits (no date '
         'left; D1\'s reference excluded): R3 and D3 DECISION under --decide auto too, rc 4', rc == 4 and gates(ra).get('G20') == 'WARN'
         and gates(ra).get('R3') == 'DECISION' and gates(ra).get('D3') == 'DECISION' and 'components' in json.dumps(ra.get('gates', []))
         and 'reference date' in json.dumps(ra.get('gates', [])), 'rc %d; G20 %s; R3 %s: %s; D3 %s' % (
             rc, gates(ra).get('G20'), gates(ra).get('R3'), val(ra, 'R3')[:160], gates(ra).get('D3')))
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator keeps every pair (self-test T117b)\nmintpy.network.excludeDate12 = auto\nmintpy.unwrapError.method = bridging\n')
    rc, out = run(['--to', 'sbas'])
    ra, rs = rec('5a', 'admit'), rec('5d', 'sbas')
    adm = json.load(open(os.path.join(W, 'recon', 'admission.json'))) if os.path.isfile(os.path.join(W, 'recon', 'admission.json')) else {}
    case('T117b recon/admission.txt keeps every pair (and bridging): admit PASS (D3 and D9 the operator\'s, the rules recorded beside it: '
         'DIFFER), 6 kept, one component; sbas PASS, rc 0', rc == 0 and ra.get('verdict') == 'PASS' and gates(ra).get('D3') == 'INFO'
         and 'DIFFER' in val(ra, 'D3') and gates(ra).get('G5a.5') == 'PASS'
         and adm.get('kept') == 6 and rs.get('verdict') == 'PASS', 'rc %d; admit %s; kept %s; sbas %s' % (
             rc, ra.get('verdict'), adm.get('kept'), rs.get('verdict')))

    # ---- F40 and G24 in the bootstrap load
    restore('S4f', 'T105')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_F40': '1'})
    rm = rec('5c', 'mcfg')
    case('T105 load_data prints F40\'s two warnings (no metadata file found, prep_isce.py failed): mcfg FAIL at G5c.6, rc 2; sbas not '
         'run', rc == 2 and rm.get('verdict') == 'FAIL' and gates(rm).get('G5c.6') == 'FAIL' and 'F40 warnings 2' in val(rm, 'G5c.6')
         and not rec('5d', 'sbas'), 'rc %d; mcfg %s; G5c.6 %s' % (rc, rm.get('verdict'), val(rm, 'G5c.6')[:100]))
    restore('S4f', 'T106')
    rc, out = run(['--to', 'sbas'], {'LINOG_MOCK_HEADING': '-11'})
    rm = rec('5c', 'mcfg')
    case('T106 the metadata\'s HEADING an ascending frame\'s (-11) on a descending path: prep PASS, mcfg FAIL at G24c, rc 2',
         rc == 2 and rec('5b', 'prep').get('verdict') == 'PASS' and gates(rm).get('G24c') == 'FAIL', 'rc %d; G24c %s' % (
             rc, val(rm, 'G24c')))

    # ---- dry runs: a frame with interferograms, one without, and a dry-run folder inside or around the frame
    restore('S4f', 'T107')
    D = os.path.join(T, 'dry_p56')
    l0, g0 = listing(W), S34.md5q(os.path.join(W, 'logs', 'STATUS.txt'))
    rc, out = run(['--dry-run', D, '--to', 'sbas'])
    dr = dict((ph, json.load(open(os.path.join(D, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D, 'status', 'P%s_%s.json' % (i, ph))) else {}) for i, ph in P45)
    dt = cfgv(os.path.join(D, 'mintpy', 'smallbaselineApp.cfg'))
    case('T107 dry run of the frame after igram, to sbas: rc 0; the report rendered into DIR (12 JPEGs, 1 page), admission.json and '
         'the template (ORBIT_DIRECTION descending, SNWE auto) in DIR, prep and sbas plans; the frame unchanged (listing and ledger)',
         rc == 0 and all(dr[ph].get('verdict') == 'PASS' for ph in dr) and dr['report'].get('outputs', {}).get('jpegs') == 12
         and os.path.isfile(os.path.join(D, 'Igrams', 'reports', 'P084F3320_Igram_Report_Page_1.jpg'))
         and os.path.isfile(os.path.join(D, 'recon', 'admission.json')) and dt.get('ORBIT_DIRECTION') == 'descending'
         and dt.get('mintpy.geocode.SNWE') == 'auto' and dr['prep'].get('outputs', {}).get('planned') and dr['sbas'].get('outputs', {}).get('planned')
         and listing(W) == l0 and S34.md5q(os.path.join(W, 'logs', 'STATUS.txt')) == g0,
         'rc %d; %s; frame unchanged %s' % (rc, [(ph, dr[ph].get('verdict')) for ph in dr], listing(W) == l0))
    rc1, out1 = run(['--dry-run', os.path.join(W, 'dry_inside'), '--to', 'report'])
    rc2, out2 = run(['--dry-run', os.path.join(T, ROOT), '--to', 'report'])
    case('T118 a dry-run folder inside the frame folder, and one that holds it: refused before anything is written, rc 3 and 3; the '
         'frame unchanged', rc1 == 3 and rc2 == 3 and 'inside it' in out1 and 'holds the frame folder' in out2
         and not os.path.exists(os.path.join(W, 'dry_inside')) and listing(W) == l0, 'rc %d and %d' % (rc1, rc2))
    restore('S4e', 'T107b')
    D2 = os.path.join(T, 'dry_p56b')
    l0 = listing(W)
    rc, out = run(['--dry-run', D2, '--to', 'sbas'])
    dr = dict((ph, json.load(open(os.path.join(D2, 'status', 'P%s_%s.json' % (i, ph)))) if os.path.exists(
        os.path.join(D2, 'status', 'P%s_%s.json' % (i, ph))) else {}) for i, ph in P45)
    case('T107b dry run of a frame whose igram has not run: rc 0; report, admit, prep and mcfg "plan only (dry run): the frame has no '
         'interferograms yet", sbas a plan; nothing rendered; the frame unchanged', rc == 0
         and all('the frame has no interferograms yet' in dr[ph].get('reason', '') for ph in ('report', 'admit', 'prep', 'mcfg'))
         and dr['sbas'].get('verdict') == 'PASS' and not os.path.exists(os.path.join(D2, 'Igrams')) and listing(W) == l0,
         'rc %d; %s' % (rc, [(ph, dr[ph].get('verdict'), dr[ph].get('reason', '')[:60]) for ph in dr]))

    # ---- the geometry against the path table
    restore('S4f', 'T108')
    fl = probe('fliplon', os.path.join(W, 'geom_reference', 'lon.rdr'), 83, 658)
    rc, out = run(['--only', 'report'])
    rr = rec('4g', 'report')
    case('T108 lon.rdr flipped left-right (column 0 west on a descending path): report FAIL at G4g.3, rc 2; nothing rendered',
         rc == 2 and gates(rr).get('G4g.3') == 'FAIL' and not os.path.exists(os.path.join(W, 'Igrams', 'reports')),
         'rc %d; %s; G4g.3 %s' % (rc, fl, val(rr, 'G4g.3')[:100]))

    # ---- pins
    restore('S4f', 'T111')
    rc, out = run(['--to', 'sbas'], {'LINOG_MINTPY_CFG': mcfg_copy('mintpy_badadmit.cfg', 'KIT_ADMIT_MD5', '0' * 32)})
    ra = rec('5a', 'admit')
    case('T111 the kit\'s linog_admit.py off its pin (a linog_mintpy.cfg with another md5): report PASS, admit FAIL at G5a.3, rc 2',
         rc == 2 and rec('4g', 'report').get('verdict') == 'PASS' and gates(ra).get('G5a.3') == 'FAIL', 'rc %d; G5a.3 %s' % (
             rc, gates(ra).get('G5a.3')))
    restore('S4f', 'T112')
    rc, out = run(['--to', 'sbas'], {'LINOG_MINTPY_CFG': mcfg_copy('mintpy_badversion.cfg', 'MINTPY_VERSION', '1.6.3')})
    rp = rec('5b', 'prep')
    case('T112 MintPy not at its pinned version (a linog_mintpy.cfg that pins 1.6.3): admit PASS, prep FAIL at G5b.2m, rc 2',
         rc == 2 and rec('5a', 'admit').get('verdict') == 'PASS' and gates(rp).get('G5b.2m') == 'FAIL', 'rc %d; G5b.2m %s' % (
             rc, val(rp, 'G5b.2m')[:100]))

    # ---- S14 (F49, F50): magnitudes spread as a real frame's, a block of NaN, and ISCE's logging in the report's process
    restore('S4e', 'T122')
    RM, NP = '20080830_20090302', '20081130_20090602'
    rc, out = run(['--to', 'report'], {'LINOG_MOCK_RANDMAG': RM, 'LINOG_MOCK_NANPAIR': NP})
    rr = rec('4g', 'report')
    pdir = os.path.join(W, 'Igrams', 'reports', 'pairs')
    kitpy = os.path.join(S.KITSRC, 'kit3', 'linog_save_insar_images.py')
    top = probe('stretchtop', os.path.join(W, 'Igrams', RM, 'filt_%s.int' % RM), 83, 658)
    kr = probe('kitimg', os.path.join(W, 'Igrams', RM, 'filt_%s.int' % RM), os.path.join(T, 'kitimg_T122', RM), False, True, kitpy, site=True)
    kn = probe('kitimg', os.path.join(W, 'Igrams', NP, 'filt_%s.int' % NP), os.path.join(T, 'kitimg_T122', NP), False, True, kitpy, site=True)
    ours = dict(('%s_%s' % (pr, k), S34.md5q(os.path.join(pdir, 'filt_%s_%s.jpg' % (pr, k)))) for pr in (RM, NP) for k in ('phase', 'combined'))
    blk = probe('jpegblock', os.path.join(pdir, 'filt_%s_combined.jpg' % NP), 221, 227, 39, 45)   # the NaN block, flipped left-right
    case('T122 a pair with magnitudes spread as a real frame\'s (the stretch tops %s here, numpy %s) and a pair with a 10 x 10 '
         'block of NaN: report PASS, 12 JPEGs; both JPEGs of the first and the phase JPEG of the second byte for byte the kit\'s own '
         'linog_save_insar_images.py (%s) on the same arrays; the NaN block white in the combined JPEG (F49)' % (
             'one float32 step above 1' if top.get('steps') == 1 else 'at %s' % top.get('top'), top.get('numpy'), KIT_IMG_MD5[:8]),
         rc == 0 and rr.get('verdict') == 'PASS' and gates(rr).get('G4g.5') == 'PASS' and rr.get('outputs', {}).get('jpegs') == 12
         and (top.get('percentile') == 'float32' or top.get('steps') == 1)
         and S34.md5q(kitpy) == KIT_IMG_MD5 and kr.get('phase') == ours[RM + '_phase'] and kr.get('combined') == ours[RM + '_combined']
         and kn.get('phase') == ours[NP + '_phase'] and blk.get('mean', 0) > 230,
         'rc %d; report %s, G4g.5 %s: %s; stretch top %s (%s steps; percentile %s); kit %s: phase %s, combined %s; NaN pair: phase %s, '
         'combined %s (the kit\'s NaN pixels are left unassigned by hsv_to_rgb), block mean %s min %s' % (
             rc, rr.get('verdict'), gates(rr).get('G4g.5'), val(rr, 'G4g.5'), top.get('top'), top.get('steps'), top.get('percentile'),
             S34.md5q(kitpy) == KIT_IMG_MD5, kr.get('phase') == ours[RM + '_phase'], kr.get('combined') == ours[RM + '_combined'],
             kn.get('phase') == ours[NP + '_phase'], kn.get('combined') == ours[NP + '_combined'], blk.get('mean'), blk.get('min')))
    il = probe('iscelog', site=True, cwd=os.path.join(T, 'iscelog_T123'))
    nm = [ln for ln in out.splitlines() if ' - DEBUG - ' in ln or ' - INFO - ' in ln]
    here = sorted(os.path.join(d, n) for d in sorted(set((S.HERE, os.getcwd()))) for n in os.listdir(d) if n.startswith('isce.log'))
    case('T123 ISCE\'s logging (the mock isce reads ISCE 2.6.3\'s logging.conf as isce/__init__.py does: after `import isce` '
         'matplotlib prints %s lines of its start-up at DEBUG and they go into isce.log in the working folder): T100\'s run to sbas and '
         'T122\'s report, pages made, print no line in ISCE\'s log format, and no isce.log is in the folder they ran from (F50)' % il.get('debug'),
         il.get('root') == 'DEBUG' and il.get('debug', 0) > 0 and (il.get('isce_log_lines') or 0) >= il.get('debug', 0)
         and gates(rr).get('G4g.6') == 'PASS' and not logl100 and not nm and not here,
         'probe %s; ISCE-format lines: T100 %d%s, T122 %d%s; isce.log in %s: %s' % (
             il, len(logl100), (': ' + logl100[0][:100]) if logl100 else '', len(nm), (': ' + nm[0][:100]) if nm else '',
             ' and '.join(sorted(set((S.HERE, os.getcwd())))), here or 'none'))
