#!/usr/bin/env python3
"""lp_p2.py -- shared helpers for linog_auto Phase 2 (v0.3; v0.5): the stack settings and pins (linog_stack.cfg), the
stack tools inside the pinned env, the frame's DEM, the stackStripMap command and its log, what a pass folder holds,
the network (degree, bperp), D1, the reference rule, and LiveStatus (F25: the record after every gate, Phases 2 to 4).

Standard library only. The files of Phase 0 and of extract and unpack (lp_common.py, lp_p1.py, lp_recon.py,
lp_stage.py, lp_extract.py, lp_unpack.py, lp_env.sh, linog_paths.cfg, linog_env.cfg) are byte-identical to v0.4
(install.sh compares them), so a frame processed by v0.4 keeps those records CURRENT under v0.5; v0.5 adds rwin and
changes verify.
"""
import collections
import datetime
import json
import os
import re
import subprocess
import sys
import time

import lp_common as C

VERSION2 = 'linog_auto v0.13 (2026-10-16)'   # the release that last changed this module (v0.5 before; v0.13: D1 among FBS dates, R6-d's looks)
HERE = os.path.dirname(os.path.abspath(__file__))
STACK_KEYS = ('ENV_PREFIX', 'STACK_DIR_REL', 'STACKSTRIPMAP_MD5', 'STACK_PY_MD5', 'KIT_NET_TABLE_MD5', 'STACK_T_DAYS',
              'STACK_B_M', 'STACK_ALKS', 'STACK_RLKS', 'STACK_UNW', 'PAIR_FLIP_M', 'D1_DEGREE_SLACK', 'NEAR_B_M', 'THIN_DEGREE')
# the settings each phase's fingerprint holds: the values it uses, not the file (a comment or another phase's key
# changes nothing); nor the pipeline's own code: a phase's LOGIC number is raised when what it writes or decides changes
STACK1_KEYS = ('ENV_PREFIX', 'STACK_DIR_REL', 'STACK_T_DAYS', 'STACK_B_M', 'STACK_ALKS', 'STACK_RLKS', 'STACK_UNW', 'THIN_DEGREE')
REF_KEYS = ('D1_DEGREE_SLACK', 'NEAR_B_M', 'STACK_ALKS', 'STACK_RLKS')
STACK2_KEYS = ('ENV_PREFIX', 'STACK_DIR_REL', 'STACK_T_DAYS', 'STACK_B_M', 'STACK_ALKS', 'STACK_RLKS', 'STACK_UNW', 'PAIR_FLIP_M')
LINE_BP = re.compile(r'^\s*(\d{8})\s*:\s*(-?\d+\.\d+)\s*$', re.M)
PAIR = re.compile(r'config_igram_(\d{8})_(\d{8})\b')
RUN_NAMES = ('run_01_reference', 'run_02_focus_split', 'run_03_geo2rdr_coarseResamp', 'run_04_refineSecondaryTiming',
             'run_05_invertMisreg', 'run_06_fineResamp', 'run_07_grid_baseline', 'run_08_igram')


ABSENT = object()


class LiveStatus(C.Status):
    """A status record written again after every gate (F25, v0.5), so a RUNNING record shows the gates taken so far;
    the same atomic write (temporary file, then replace). lp_common.py stays byte-identical, so Phase 0 and 1 records
    stay CURRENT."""

    def gate(self, *a, **k):
        C.Status.gate(self, *a, **k)
        self.write()


def get(o, *names):
    """The first of names that o has (a get... name is called); ABSENT if none. As lp_verify.py reads a shelve."""
    for n in names:
        try:
            v = getattr(o, n)
        except Exception:  # noqa: BLE001
            continue
        return v() if n.startswith('get') and callable(v) else v
    return ABSENT


def as_int(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return int(v) if v == int(v) else None


def stack_cfg_file():
    return os.environ.get('LINOG_STACK_CFG') or os.path.join(HERE, 'linog_stack.cfg')


def load_stack():
    """linog_stack.cfg as a dict (KEY=value lines; # comments)."""
    f = stack_cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in STACK_KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['stack_cfg_file'], d['stack_cfg_md5'] = f, C.md5_file(f)
    return d


def settings_of(s, keys):
    return {k: s[k] for k in keys}


def modes_digest(rows):
    """What Phase 2 reads of recon/modes.json: date, mode, width and lines of each date (not its time stamps)."""
    return C.md5_obj([[d, rows[d].get('mode'), rows[d].get('width'), rows[d].get('lines')] for d in sorted(rows)])


SHELF = ('data', 'data.dat', 'data.dir', 'data.bak', 'data.db')


def slc_identity(W, dates, shelve_only=False):
    """md5 of [date, [[name, size, mtime_ns], ...]] of SLC/<date>/, in name order: the files the unpacker writes and the
    ISCE steps read (<date>.slc, its .xml and .vrt, the shelve's files), or the shelve's files only (what stackStripMap
    reads). F21 (v0.5): only these names, so a file written beside them later (MintPy's data.rsc, a GDAL .aux.xml)
    changes nothing; for a folder that holds only these files the value is the one v0.3 and v0.4 computed."""
    out = []
    for d in dates:
        sd, fs = os.path.join(W, 'SLC', d), []
        names = set(SHELF) if shelve_only else set(SHELF + (d + '.slc', d + '.slc.xml', d + '.slc.vrt'))
        for n in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
            if n not in names:
                continue
            st = os.stat(os.path.join(sd, n))
            fs.append([n, st.st_size, st.st_mtime_ns])
        out.append([d, fs])
    return C.md5_obj(out)


def stack_dir(s):
    """stripmapStack in the pinned env, ENV_PREFIX/STACK_DIR_REL: the same folder inside the env (the phase) and outside it
    (the state check, which runs on the ssh shell's python3), so both hash the same tools. env_gate() checks that the
    activated env's CONDA_PREFIX is ENV_PREFIX."""
    return os.path.join(s['ENV_PREFIX'], s['STACK_DIR_REL'])


def tool_md5s(s, env):
    """{name: (path, md5 or None, pin)} for stackStripMap.py, Stack.py and the kit's net table."""
    sd = stack_dir(s)
    out = {}
    for name, folder, pin in (('stackStripMap.py', sd, s['STACKSTRIPMAP_MD5']), ('Stack.py', sd, s['STACK_PY_MD5']),
                              ('linog_net_table.py', env['KIT'], s['KIT_NET_TABLE_MD5'])):
        p = os.path.join(folder, name)
        out[name] = (p, C.md5_file(p) if os.path.isfile(p) else None, pin)
    return out


def tools_gate(st, gid, tm):
    bad = ['%s md5 %s, pinned %s' % (p, got, pin) for p, got, pin in tm.values() if got != pin]
    st.gate(gid, 'stack tools at their pins', 'FAIL' if bad else 'PASS', '%d of %d' % (len(tm) - len(bad), len(tm)),
            'stackStripMap.py, Stack.py, linog_net_table.py', '\n'.join(bad))
    return not bad


def env_gate(st, gid, env, s):
    """The pinned env at its pinned prefix and `import isce` (an ERROR gate, as Phase 1's)."""
    try:
        import isce  # noqa: F401
        cp = os.environ.get('CONDA_PREFIX') or ''
        ok_env = os.environ.get('CONDA_DEFAULT_ENV') == env['CONDA_ENV']
        ok_pre = bool(cp) and os.path.realpath(cp) == os.path.realpath(s['ENV_PREFIX'])
        note = '' if ok_env and ok_pre else ('run this phase through lp_env.sh' if not ok_env else
                                             'CONDA_PREFIX %s is not ENV_PREFIX %s (linog_stack.cfg)' % (cp or '(unset)', s['ENV_PREFIX']))
        st.gate(gid, 'environment', 'PASS' if ok_env and ok_pre else 'ERROR', 'env %s at %s, isce %s, python %s %s' % (
            os.environ.get('CONDA_DEFAULT_ENV'), cp or '(no CONDA_PREFIX)', getattr(isce, '__version__', '?'), sys.executable,
            sys.version.split()[0]), '%s at ENV_PREFIX' % env['CONDA_ENV'], note)
    except Exception as e:  # noqa: BLE001
        st.gate(gid, 'environment', 'ERROR', 'import isce failed: %s' % e, env['CONDA_ENV'])
    return not any(x['verdict'] == 'ERROR' for x in st.rec['gates'])


def frame_dem(W):
    """(the one DEM file in <frame>/DEM, problems): a *.wgs84 with .vrt and .xml beside it, every link resolving."""
    d = os.path.join(W, 'DEM')
    if not os.path.isdir(d):
        return None, ['no DEM/ in the frame']
    dems = sorted(n for n in os.listdir(d) if n.endswith('.wgs84'))
    if len(dems) != 1:
        return None, ['%d *.wgs84 in DEM/ (%s), want 1' % (len(dems), ', '.join(dems))]
    dem = os.path.join(d, dems[0])
    bad = [p for p in (dem, dem + '.vrt', dem + '.xml') if not os.path.isfile(p)]
    return dem, ['missing or not resolving: %s' % ', '.join(bad)] if bad else []


def dem_identity(dem):
    if not dem:
        return None
    t = os.path.realpath(dem)
    return [t] + [(os.path.getsize(p), int(os.path.getmtime(p))) if os.path.exists(p) else None
                  for p in (t, t + '.vrt', t + '.xml')]


def stack_args(s, W, dem, workdir, ref=None):
    return ['-W', 'interferogram', '--nofocus', '-s', os.path.join(W, 'SLC'), '-d', dem, '-t', s['STACK_T_DAYS'],
            '-b', s['STACK_B_M'], '-a', s['STACK_ALKS'], '-r', s['STACK_RLKS'], '-u', s['STACK_UNW'], '-w', workdir] + \
        (['-m', ref] if ref else [])


def run_stackstripmap(s, args, cwd, log, mpl):
    """stackStripMap.py by absolute path with this Python (-B: no __pycache__ in the env); (rc, seconds)."""
    os.makedirs(mpl, exist_ok=True)
    env = dict(os.environ, MPLCONFIGDIR=mpl)
    t0 = time.time()
    with open(log, 'w') as fh:
        fh.write('# %s %s\n' % (C.utc(), ' '.join([sys.executable, '-B', os.path.join(stack_dir(s), 'stackStripMap.py')] + args)))
        fh.flush()
        rc = subprocess.call([sys.executable, '-B', os.path.join(stack_dir(s), 'stackStripMap.py')] + args, cwd=cwd,
                             stdout=fh, stderr=subprocess.STDOUT, env=env)
    return rc, time.time() - t0


def parse_log(log):
    txt = open(log, errors='replace').read()
    m = re.search(r'^acquisitionDates\s*=\s*\[(.*)\]\s*$', txt, re.M)
    acq = re.findall(r"'(\d{8})'", m.group(1)) if m else None
    p = re.search(r'^number of pairs:\s*(\d+)', txt, re.M)
    md = re.search(r'SLCs with min degree connection of ([\d.]+)', txt)
    return dict(acq=acq, notfound='reference date was not found' in txt,
                bp={a: float(b) for a, b in LINE_BP.findall(txt)}, pairs=int(p.group(1)) if p else None,
                min_degree=float(md.group(1)) if md else None, not_connected='is not connected' in txt,
                tail='\n'.join(txt.strip().splitlines()[-12:]))


def nfiles(d):
    return len([n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n))]) if os.path.isdir(d) else 0


def nlines(p):
    return sum(1 for ln in open(p) if ln.strip()) if os.path.isfile(p) else None


def read_pass(wd):
    """What a stackStripMap working folder holds: config and run-file counts, the run files' line counts, the
    baseline files (name -> mean of top and bottom), and the pair list of run_08_igram."""
    rf = os.path.join(wd, 'run_files')
    runs = {n: nlines(os.path.join(rf, n)) for n in RUN_NAMES}
    bl = {}
    bd = os.path.join(wd, 'baselines')
    for n in sorted(os.listdir(bd)) if os.path.isdir(bd) else []:
        try:
            v = dict(ln.split() for ln in open(os.path.join(bd, n)) if ln.strip())
            bl[n] = (float(v['PERP_BASELINE_TOP']) + float(v['PERP_BASELINE_BOTTOM'])) / 2
        except (ValueError, KeyError, OSError):
            bl[n] = None
    r8 = os.path.join(rf, 'run_08_igram')
    pairs = sorted({tuple(sorted(m.groups())) for m in PAIR.finditer(open(r8).read())}) if os.path.isfile(r8) else []
    return dict(configs=nfiles(os.path.join(wd, 'configs')), run_files=nfiles(rf), runs=runs, baselines=bl,
                pairs=[list(x) for x in pairs], run08_md5=C.md5_file(r8) if os.path.isfile(r8) else None,
                pdf=os.path.getsize(os.path.join(wd, 'pairs.pdf')) if os.path.isfile(os.path.join(wd, 'pairs.pdf')) else None)


def want_runs(S, P):
    return dict(zip(RUN_NAMES, (1, S, S, P, 1, S + 1, S + 1, P)))


def modes_rows(W):
    """recon/modes.json: (rows by date, md5, verdict); ({}, None, None) when absent."""
    mj = os.path.join(W, 'recon', 'modes.json')
    if not os.path.exists(mj):
        return {}, None, None
    m = json.load(open(mj))
    return {r['date']: r for r in m.get('dates', [])}, C.md5_file(mj), m.get('verdict')


def network(dates, bp, pairs):
    """Degree and MAXBP (the largest |bperp difference| over a date's own pairs) of every date."""
    deg, mx = collections.Counter(), collections.defaultdict(float)
    for x, y in pairs:
        deg[x] += 1
        deg[y] += 1
        s = abs(bp[x] - bp[y])
        mx[x], mx[y] = max(mx[x], s), max(mx[y], s)
    return {d: deg[d] for d in dates}, {d: round(mx[d], 1) for d in dates}


def d1(rows, bp, pairs, slack, near_b):
    """D1 (record 7.4 with Q3): candidates of degree >= max - slack, the earliest date excluded (N23); among them the
    modal width first, then the date nearest the temporal midpoint (ties: higher degree, smaller MAXBP, earlier date).
    Also the midpoint alone (no width preference) and the kit list's first entry (degree first, then the midpoint,
    modal width, degree > 3). bp: bperp of every date relative to the stack's first date.
    v0.13 (ascending record 4.7): on an FBS+FBD frame the network's quantities (the maximum degree, the earliest date, the
    temporal midpoint) are taken over all dates, then only FBS dates are candidates, the modal width taken among the FBS
    dates; the two other rules take the FBS filter the same way (the kit's own list, linog_net_table.py: FBS dates at the FBS
    modal width, degree above 3, by degree, then the midpoint). D1c: no FBS date in the degree band, so the FBS dates of the
    highest degree, not the earliest, ranked as D1 ranks its candidates (the modal width first, then the midpoint: the build's
    reading of 4.7's D1c sentence, the part 3 review's P3-03), and the caller WARNs; no_fbs: the frame's only FBS dates are
    the stack's earliest, so no FBS reference can be had (the caller FAILs D1c, P3-04). An FBS-only or FBD-only frame:
    v0.12's rule (R6-d, 18.5)."""
    ds = sorted(rows)
    t = {d: datetime.datetime.strptime(d, '%Y%m%d') for d in ds}
    tmid = t[ds[0]] + (t[ds[-1]] - t[ds[0]]) / 2
    dt = {d: abs((t[d] - tmid).days) for d in ds}
    deg, mx = network(ds, bp, pairs)
    mixed = len(set(rows[d].get('mode') for d in ds)) > 1
    pool = [d for d in ds if rows[d].get('mode') == 'FBS'] if mixed else ds
    modal = collections.Counter(rows[d]['width'] for d in (pool or ds)).most_common(1)[0][0]
    top = max(deg.values())
    key = lambda d: (dt[d], -deg[d], mx[d], d)  # noqa: E731
    cand = sorted([d for d in pool if deg[d] >= top - slack and d != ds[0]], key=key)
    d1c = no_fbs = False
    if mixed and not cand:   # D1c: no FBS date in the degree band
        fb = [d for d in pool if d != ds[0]]
        if fb:
            hi = max(deg[d] for d in fb)
            cand, d1c = sorted([d for d in fb if deg[d] == hi], key=key), True
        else:
            no_fbs = True    # the only FBS dates are the stack's earliest (N23)
    modal_c = [d for d in cand if rows[d]['width'] == modal]
    pick = (modal_c or cand or [None])[0]
    kitl = [d for d in sorted(pool, key=lambda d: (-deg[d], dt[d])) if rows[d]['width'] == modal and deg[d] > 3]
    table = [dict(date=d, mode=rows[d].get('mode'), width=rows[d]['width'], degree=deg[d], bperp=round(bp[d], 1), dt_days=dt[d],
                  maxbp=mx[d], notes='; '.join(x for x, c in (('near -b limit', mx[d] > near_b),
                                                             ('not modal width', rows[d]['width'] != modal)) if c))
             for d in cand]
    return dict(pick=pick, midpoint_alone=cand[0] if cand else None, kit_first=kitl[0] if kitl else None,
                tmid=tmid.strftime('%Y%m%d'), modal_width=modal, max_degree=top, min_degree=min(deg.values()),
                slack=slack, earliest=ds[0], candidates=table, degree=deg, maxbp=mx, dt_days=dt, mixed=mixed, d1c=d1c,
                no_fbs=no_fbs, fbs=len(pool) if mixed else None)


def fbd_only_looks(s, rows, recdir=None):
    """v0.13 (R6-d, ascending record 18.5): on an FBD-only frame (every row of recon/modes.json FBD) the range looks are
    linog_mixed.cfg's STACK_RLKS_FBD in place of STACK_RLKS, under that key, so every reader of the settings takes them (the
    stack call, G2c.9's check of the run file, the reference's geometry) and no other frame's fingerprint moves. Called by
    stack1, reference and stack2 right after they load the settings; returns the note to record (None on any other frame).
    With no modes.json yet (a dry run before the frame's first verify, which writes none), the branch recon recorded in
    recdir/recon/RECON.json decides (the part 3 review's P3-09)."""
    if not rows:
        try:
            br = json.load(open(os.path.join(recdir, 'recon', 'RECON.json'))).get('branch') if recdir else None
        except (OSError, ValueError):
            br = None
        if br != 'FBD-only':
            return None
    elif any(r.get('mode') != 'FBD' for r in rows.values()):
        return None
    import lp_p1 as P1
    mx = P1.load_mixed()
    note = 'FBD-only frame: range looks %s (linog_mixed.cfg STACK_RLKS_FBD) in place of STACK_RLKS %s (R6-d)' % (
        mx['STACK_RLKS_FBD'], s['STACK_RLKS'])
    s['STACK_RLKS'] = mx['STACK_RLKS_FBD']
    return note


def print_candidates(r):
    if r.get('d1c'):
        print('   D1c: no FBS date has degree >= %d; the FBS dates of the highest degree (not the earliest date %s), the modal width '
              'first, then nearest the temporal midpoint %s:' % (r['max_degree'] - r['slack'], r['earliest'], r['tmid']))
    else:
        print('   candidates (%sdegree >= %d, not the earliest date %s), nearest the temporal midpoint %s first:' % (
            'FBS dates of ' if r.get('mixed') else '', r['max_degree'] - r['slack'], r['earliest'], r['tmid']))
    print('      DATE      MODE WIDTH DEG  BPERP     dT(d)  MAXBP   NOTE')
    for c in r['candidates']:
        print('      %s  %-4s %5d %3d  %8.1f  %5d  %6.1f  %s' % (c['date'], c.get('mode') or '-', c['width'], c['degree'], c['bperp'],
                                                               c['dt_days'], c['maxbp'], c['notes']))
    sys.stdout.flush()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp%d' % os.getpid()
    with open(tmp, 'w') as fh:
        json.dump(obj, fh, indent=1, default=str)
        fh.write('\n')
    os.replace(tmp, path)
    return C.md5_file(path)


def new_dir(base):
    """base.vN with the first N not yet used, created (a pass folder is never reused or overwritten)."""
    n = 1
    while os.path.exists('%s.v%d' % (base, n)):
        n += 1
    os.makedirs('%s.v%d' % (base, n))
    return '%s.v%d' % (base, n)
