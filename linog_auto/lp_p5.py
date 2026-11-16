#!/usr/bin/env python3
"""lp_p5.py -- shared helpers for linog_auto Phase 4.5 and Phase 5 (v0.6; v0.8: D9's A/B settings in place of its two
anchors, and the phase d9ab): the interferogram report and MintPy.

What it holds: the settings and pins of linog_mintpy.cfg, the phases' own outputs (the listings behind --state and the
"nothing in the way" gates), MintPy's template (read, written in place, and a digest that leaves out the one value
the sbas phase sets, reference.yx), MintPy and the kit's tools run with a log that names the command and its exit
code, the frame's geometry read from geom_reference/ (orientation and heading), SNWE on the 1/1200 deg lattice, and
D9's statistic (the mean component fraction of the kept pairs over the kit's G19 valid area, computed as
linog_refpix.py computes it, from the pairs' files).

The phases run inside lp_env.sh (numpy, h5py, matplotlib and MintPy come from the pinned env); this module imports
numpy only inside the functions that need it, so --state and the dry-run plans need the standard library only.
The Phase 0 to 4 files are byte-identical to v0.5. v0.8: KEYS reads D9AB_MIN_GAIN_CAP, D9AB_MIN_GAIN_FRAC, D9AB_TIMEOUT_S
and D9AB_FREE_GIB (the A/B after sbas, record 62.0 and 63.8) where v0.6 read UNWERR_BRIDGING_MAX and UNWERR_NO_MIN;
component_fraction stays, as admit's evidence. v0.10: KEYS reads admit's rules (ADMIT_LAND_MIN_PX, ADMIT_DEAD_SHARE,
ADMIT_EXCL_MAX_FRAC, ADMIT_CULL_MAX_FRAC; record 108.3) and dfit's DFIT_TIMEOUT_S, and sbas's "in the way" list holds
mintpy/exclude_date.txt; nothing else changed.
"""
import collections
import os
import re
import subprocess
import sys
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

VERSION_P5 = 'linog_auto v0.10 (2026-10-07)'   # the release that last changed this module (v0.8 before: KEYS, v0.10)
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = ('lp_p5.py', 'lp_p3.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py')
KEYS = ('MINTPY_VERSION', 'MINTPY_DEFAULTS_MD5', 'MINTPY_DEFAULT_KEYS', 'KIT_ADMIT_MD5', 'KIT_REFPIX_MD5', 'REPORT_PAIR_DPI',
        'REPORT_PAGE_DPI', 'REPORT_PER_PAGE', 'REPORT_STRETCH_LOW', 'REPORT_STRETCH_HIGH', 'D9AB_MIN_GAIN_CAP', 'D9AB_MIN_GAIN_FRAC',
        'D9AB_TIMEOUT_S', 'D9AB_FREE_GIB', 'G19_EDGE', 'SNWE_LATTICE', 'SNWE_MARGIN_PX', 'HEADING_TOL_DEG',
        'ADMIT_LAND_MIN_PX', 'ADMIT_DEAD_SHARE', 'ADMIT_EXCL_MAX_FRAC', 'ADMIT_CULL_MAX_FRAC', 'DFIT_TIMEOUT_S')   # v0.10
KIT_PIN = {'linog_admit.py': 'KIT_ADMIT_MD5', 'linog_refpix.py': 'KIT_REFPIX_MD5'}
# each phase's own outputs, in pipeline order. prep's .rsc files sit beside the files they describe; mcfg's bootstrap
# load writes mintpy/inputs/, which sbas rewrites, so mcfg owns the cfg only; sbas's listing leaves out the two masks
# the water-mask phase will rewrite (v0.7) and the files Phase 6 rewrites (demErr.h5, timeseriesResidual.h5).
ORDER = (('4g', 'report'), ('5a', 'admit'), ('5b', 'prep'), ('5c', 'mcfg'), ('5d', 'sbas'))
OUTS = collections.OrderedDict((
    ('report', ('Igrams/reports',)),
    ('admit', ('recon/admission.json',)),
    ('prep', ('Igrams/*/*.unw.rsc', 'geom_reference/*.rsc', 'SLC/*/data.rsc')),
    ('mcfg', ('mintpy/smallbaselineApp.cfg',)),
    ('sbas', ('mintpy/inputs/ifgramStack.h5', 'mintpy/inputs/geometryRadar.h5', 'mintpy/timeseries.h5',
              'mintpy/temporalCoherence.h5', 'mintpy/velocity.h5', 'mintpy/geo/geo_velocity.h5')),
))
# what "in the way" means for each (outputs in the frame that a run of the phase would write over): sbas's first files
# are the bootstrap load's, which mcfg writes, so sbas looks at the inversion's
WAY = collections.OrderedDict((
    ('report', ('Igrams/reports',)),
    ('admit', ()),
    ('prep', ('Igrams/*/*.unw.rsc', 'geom_reference/*.rsc', 'SLC/*/data.rsc')),
    ('mcfg', ('mintpy',)),
    ('sbas', ('mintpy/timeseries.h5', 'mintpy/velocity.h5', 'mintpy/geo', 'mintpy/exclude_date.txt')),
))
# v0.10: mintpy/exclude_date.txt too (MintPy's residual_RMS writes it, and dfit, R4): an sbas run in its presence would have
# MintPy's correct_topography (dem_error.py, topographicResidual.excludeDate auto) read it before residual_RMS rewrites it
# the phases that read each phase's outputs: moving a phase's outputs aside means re-running these too (the report
# feeds none of them; admit's decisions and prep's .rsc files feed the template and the stack)
READERS = {'report': (), 'admit': ('mcfg', 'sbas'), 'prep': ('mcfg', 'sbas'), 'mcfg': ('sbas',), 'sbas': ()}
F40_WARN = ('No input metadata file found', 'prep_isce.py failed')
STEP_LIST = ('load_data', 'modify_network', 'reference_point', 'quick_overview', 'correct_unwrap_error', 'invert_network',
             'correct_LOD', 'correct_SET', 'correct_ionosphere', 'correct_troposphere', 'deramp', 'correct_topography',
             'residual_RMS', 'reference_date', 'velocity', 'geocode', 'google_earth', 'hdfeos5')   # MintPy 1.6.2 (template.py)
STEP_LINE = re.compile(r'^\*+ step - (\w+) \*+\s*$', re.M)   # smallbaselineApp's banner before each step
# after a call of more than one step, with mintpy.plot yes (its default), smallbaselineApp plots into pic/ and prints
# this banner first (1.6.2 run_smallbaselineApp: plot_result() after app.run()): an error after it is the plot's
PLOT_BANNER = '******************** plot & save to pic ********************'


def steps_between(start, end):
    return list(STEP_LIST[STEP_LIST.index(start):STEP_LIST.index(end) + 1])


def steps_run(out):
    """The steps smallbaselineApp printed it ran ('******************** step - NAME ********************')."""
    return STEP_LINE.findall(out)


def f40_lines(out):
    return [ln.strip() for ln in out.splitlines() if any(w in ln for w in F40_WARN)]


def mintpy_cfg_file():
    return os.environ.get('LINOG_MINTPY_CFG') or os.path.join(HERE, 'linog_mintpy.cfg')


def load_mintpy():
    """linog_mintpy.cfg as a dict (KEY=value lines; # comments); CFG.<key>=value lines go into d['cfg'], in order."""
    f = mintpy_cfg_file()
    d, cfg = {}, collections.OrderedDict()
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            k, v = k.strip(), v.strip()
            if k.startswith('CFG.'):
                cfg[k[4:]] = v
            else:
                d[k] = v
    miss = [k for k in KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['cfg'], d['mintpy_cfg_file'], d['mintpy_cfg_md5'] = cfg, f, C.md5_file(f)
    return d


def tools(env, m):
    """{name: (path, md5 or None, pin)}: the kit's admit and G19 tools."""
    out = {}
    for n, key in KIT_PIN.items():
        p = os.path.join(env['KIT'], n)
        out[n] = (p, C.md5_file(p) if os.path.isfile(p) else None, m[key])
    return out


def listing(W, phase):
    return P3.listing(W, OUTS[phase])


def outputs_changed(W, phase, rec, names_only=False):
    return P3.listing_changed(W, OUTS[phase], (rec or {}).get('outputs', {}).get('files'), names_only)


def state(recdir, W, phase, index, fp, extra=None):
    """--state: C.state(), and a CURRENT record whose files are gone or changed reads STALE. extra(record) -> list adds
    a phase's own check (mcfg: its cfg's digest)."""
    def missing(rec):
        return outputs_changed(W, phase, rec) + (extra(rec) if extra else [])
    return P1.state_with_outputs(recdir, phase, index, fp, missing)


def prior5(st, gid, recdir, W, index, phase, outs=True, dry=False):
    """The phase this one reads: PASS on record, and (outs) its files as it recorded them. A dry run's plan counts only
    in a dry run (a real run that finds one in the frame's records FAILs). Returns the record or None."""
    r = P3.prior3(st, gid, recdir, index, phase)
    if not r:
        return None
    if r.get('outputs', {}).get('planned'):
        if not dry:
            st.gate(gid, '%s PASS on record' % phase, 'FAIL', 'the record in %s is a dry run\'s plan, not a run' % recdir,
                    'a run\'s PASS', 'a dry run was written into the frame\'s own records; run the phase for real')
            return None
        st.gate(gid, '%s PASS on record' % phase, 'PASS', 'dry-run %s was a plan only' % phase)
        return r
    ch = []
    if outs:
        rels = OUTS.get(phase) or P3.OUTS.get(phase) or ()
        ch = P3.listing_changed(W, rels, r.get('outputs', {}).get('files'))
    st.gate(gid, '%s PASS on record' % phase, 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
            'P%s %s PASS, its files as it recorded them' % (index, phase))
    return None if ch else r


def frame_igram(W):
    """True when the frame's own igram record is PASS. Phases 4.5 and 5 read the frame's interferograms, in a dry run
    too; a dry run of a frame without them gets a plan only."""
    return (P1.record(W, '4f', 'igram') or {}).get('verdict') == 'PASS'


def igram_prior(st, gid, W, recdir, dry):
    """igram as these phases read it: PASS on the frame's record, Igrams as igram recorded it. A dry run of a frame whose
    igram has not run reads the dry run's own igram record (a plan). (record or None, the frame has its interferograms)."""
    if not dry or frame_igram(W):
        return prior5(st, gid, W, W, '4f', 'igram', outs=True), True
    return prior5(st, gid, recdir, W, '4f', 'igram', outs=False, dry=True), False


def plan_only(st, lines, note):
    """A dry run's end when the frame has no interferograms yet: what the phase would do, a PASS record marked planned."""
    for ln in lines:
        print('   ' + ln)
    st.rec['outputs'] = dict(planned=True, dryrun=True, note=note)
    return st.finish('plan only (dry run): %s' % note)


def way_gate(st, gid, W, phase, dry):
    """DECISION when this phase's outputs are in the frame already: a run would write over them. The note names the
    outputs of the phases that read them (READERS), which have to be made again too."""
    own = P3.present(W, WAY[phase])
    later = [x for n in READERS[phase] for x in P3.present(W, WAY[n])]
    if dry:
        st.gate(gid, 'nothing in the way', 'INFO', 'dry run: in the frame now: %s' % (', '.join(own + later) or 'none of them'),
                ', '.join(WAY[phase]) + ' absent')
        return True
    if own:
        st.gate(gid, 'nothing in the way', 'DECISION', 'in the frame already: %s%s' % (
            ', '.join(own), ('; and what the phases that read them made: %s' % ', '.join(later)) if later else ''),
            ', '.join(WAY[phase]) + ' absent',
            'this run would write over them (an earlier run\'s, or a run whose inputs have changed since); move them%s into '
            '%s/_archive/ and run again' % (' and the outputs listed after them' if later else '', W))
        return False
    st.gate(gid, 'nothing in the way', 'PASS', '%s absent' % (', '.join(WAY[phase]) or 'nothing'), 'all absent')
    return True


def begin(recdir, phase, index, path, frame, fp, logic, inputs):
    st = P3.begin(recdir, phase, index, path, frame, fp, logic, inputs, None)
    st.rec['version'] = VERSION_P5
    st.rec['tools'] = C.tool_md5s(*(('lp_%s.py' % phase,) + TOOLS))
    st.write()
    return st


def header(phase, index, path, frame, W, dry, extra=''):
    print('%s  Phase %s %s  p%s f%s  %s' % (VERSION_P5, index, phase, path, frame, C.utc()))
    print('   frame folder %s%s%s' % (W, extra, '   (DRY RUN: the frame is only read)' if dry else ''))
    sys.stdout.flush()


def quiet_root():
    """After `import isce`: ISCE 2.6.3's defaults/logging/logging.conf (read by isce/__init__.py with fileConfig) puts
    the root logger at DEBUG with a console handler (stdout) and a file handler that opens isce.log in the working
    folder at its first record. So every library imported after isce prints its start-up at DEBUG and writes it into
    isce.log there: matplotlib's in the report, h5py's in prep, mcfg and sbas (S14; F50). The root logger goes to
    WARNING. ISCE's own logger 'isce' has its own two handlers and propagate 0, and stays as ISCE set it."""
    import logging
    logging.getLogger().setLevel(logging.WARNING)


def env_gate(st, gid, env, s, m):
    """The pinned env (P2's gate), then MintPy importable at its pinned version, h5py and numpy with it."""
    if not P2.env_gate(st, gid, env, s):
        return None
    quiet_root()
    try:
        import mintpy
        import h5py
        import numpy
        ver = getattr(mintpy, '__version__', '?')
        libs = 'h5py %s, numpy %s' % (h5py.__version__, numpy.__version__)
        dflt = os.path.join(os.path.dirname(mintpy.__file__), 'defaults', 'smallbaselineApp.cfg')
        dmd5 = C.md5_file(dflt) if os.path.isfile(dflt) else None
        bad = []
        if ver != m['MINTPY_VERSION']:
            bad.append('mintpy %s, pinned %s' % (ver, m['MINTPY_VERSION']))
        if dmd5 != m['MINTPY_DEFAULTS_MD5']:
            bad.append('%s md5 %s, pinned %s' % (dflt, dmd5, m['MINTPY_DEFAULTS_MD5']))
        st.gate(gid + 'm', 'MintPy at its pin', 'FAIL' if bad else 'PASS', 'mintpy %s at %s; defaults file md5 %s; %s' % (
            ver, os.path.dirname(mintpy.__file__), dmd5, libs), 'mintpy %s, defaults %s' % (m['MINTPY_VERSION'],
                                                                                          m['MINTPY_DEFAULTS_MD5']), '\n'.join(bad))
        return None if bad else dict(version=ver, defaults=dflt, defaults_md5=dmd5, package=os.path.dirname(mintpy.__file__))
    except Exception as e:  # noqa: BLE001
        st.gate(gid + 'm', 'MintPy at its pin', 'ERROR', 'import mintpy, h5py, numpy failed: %s' % e, m['MINTPY_VERSION'])
        return None


def which_gate(st, gid, s, cmds):
    """Each MintPy command on the phase's PATH resolves into the pinned env's bin (G13's family: the name, not a
    shadow)."""
    bad, got = [], []
    want_dir = os.path.realpath(os.path.join(s['ENV_PREFIX'], 'bin'))
    import shutil
    for c in cmds:
        w = shutil.which(c)
        got.append('%s -> %s' % (c, w))
        # the folder the PATH found it in (a link there to the package's script is still the env's command)
        if not w or os.path.realpath(os.path.dirname(os.path.abspath(w))) != want_dir:
            bad.append('%s resolves to %s, want %s/%s' % (c, w, want_dir, c))
    st.gate(gid, 'MintPy\'s commands on the PATH', 'FAIL' if bad else 'PASS', '; '.join(got), 'the pinned env\'s bin',
            '\n'.join(bad))
    return not bad


def run_logged(cmd, cwd, log, extra_env=None):
    """cmd from cwd, its output straight into log (a first line with the command, a last with rc and time), so the log
    exists even when the phase is stopped. (rc, output text)."""
    e = dict(os.environ)
    e.update(extra_env or {})
    t0 = time.time()
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, 'wb') as fh:
        fh.write(('# %s  %s  (cwd %s)\n' % (C.utc(), ' '.join(cmd), cwd)).encode('utf-8', 'replace'))
        fh.flush()
        start = fh.tell()
        p = subprocess.run(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
    with open(log, 'rb') as fh:
        fh.seek(start)
        out = fh.read().decode('utf-8', 'replace')
    with open(log, 'a') as fh:
        fh.write('# rc %d  %.1f s\n' % (p.returncode, time.time() - t0))
    return p.returncode, out


def mpl_env(recdir):
    d = os.path.join(recdir, 'logs', 'p5', 'mplconfig')
    os.makedirs(d, exist_ok=True)
    return {'MPLCONFIGDIR': d}


# ---------------------------------------------------------------- MintPy's template
KV = re.compile(r'^([A-Za-z][\w.]*)\s*=\s*(.*?)\s*$')


def split_value(rest):
    """The value of a template line (MintPy's reading: everything before a #, stripped)."""
    return rest.split('#', 1)[0].strip()


def read_cfg(path_or_text, is_text=False):
    """[(key, value, line number)] of a MintPy template, in file order (comments and blank lines skipped)."""
    txt = path_or_text if is_text else open(path_or_text).read()
    out = []
    for i, ln in enumerate(txt.splitlines(), 1):
        s = ln.strip()
        if not s or s.startswith(('#', '%')):
            continue
        m = KV.match(s)
        if m:
            out.append((m.group(1), split_value(m.group(2)), i))
    return out


LINE = re.compile(r'^(\s*)([A-Za-z][\w.]*)(\s*=\s*)(.*?)(\s+#.*)?$')


def set_values(text, values, extras=()):
    """The template text with each key of values set on its own line, in place (the spacing and the comment after it
    kept); extras [(KEY, value)] appended at the end in a marked block. Returns (text, problems): a key found on no
    line, or on more than one."""
    lines = text.splitlines()
    seen = collections.Counter()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith(('#', '%')):
            continue
        m = LINE.match(ln)
        if m and m.group(2) in values:
            seen[m.group(2)] += 1
            lines[i] = m.group(1) + m.group(2) + m.group(3) + values[m.group(2)] + (m.group(5) or '')
    bad = ['%s: on %d lines' % (k, seen[k]) for k in values if seen[k] != 1]
    if extras:
        lines += ['', '########## linog_auto: extra metadata for the stack (MACRO_CASE keys load_data writes into '
                      'ifgramStack.h5)']
        lines += ['%-30s = %s' % kv for kv in extras]
    return '\n'.join(lines) + '\n', bad


def cfg_digest(text):
    """md5 of the template text with the value of mintpy.reference.yx put back to auto: the one line the sbas phase
    changes (the kit's G19 pick), so the cfg mcfg wrote still reads as mcfg wrote it."""
    out = []
    for ln in text.splitlines():
        m = re.match(r'^(\s*mintpy\.reference\.yx\s*=\s*)([^#]*?)(\s*(#.*)?)$', ln)
        out.append((m.group(1) + 'auto' + (m.group(3) or '')) if m else ln)
    return C.md5_obj('\n'.join(out))


def cfg_dict(text):
    d = {}
    for k, v, _ in read_cfg(text, is_text=True):
        d[k] = v
    return d


# ---------------------------------------------------------------- the frame's geometry
def raster(W, rel, dtype, band=1):
    """A geom_reference raster as a numpy array (lines x width), its size from the .xml (BSQ; band = 1 or 2)."""
    import numpy as np
    p = os.path.join(W, rel)
    w, l, nb = xml_dims(p + '.xml')
    n = w * l
    a = np.fromfile(p, dtype=dtype, count=n * band)
    if a.size < n * band:
        raise ValueError('%s holds %d values, want %d' % (p, a.size, n * band))
    return a[(band - 1) * n:band * n].reshape(l, w)


def xml_dims(p):
    """(width, length, bands) of an ISCE .xml."""
    txt = open(p).read()
    def g(name, dflt=None):
        m = re.search(r'name="%s">\s*<value>\s*([^<\s]+)\s*</value>' % name, txt)
        return int(m.group(1)) if m else dflt
    return g('width'), g('length'), g('number_bands', 1)


def orientation(W):
    """How the radar grid lies on the ground, from geom_reference/lat.rdr and lon.rdr: dict(line0 = north or south,
    col0 = east or west, flipud, fliplr, corners). North up: flip up-down when line 0 is south; west left: flip
    left-right when column 0 is east (MintPy's auto_flip_direction: ascending flips up-down, descending left-right)."""
    import numpy as np
    lat = raster(W, 'geom_reference/lat.rdr', '<f8')
    lon = raster(W, 'geom_reference/lon.rdr', '<f8')
    ok = np.isfinite(lat) & np.isfinite(lon) & (lat != 0) & (lon != 0)
    if ok.sum() < 4:
        raise ValueError('geom_reference/lat.rdr and lon.rdr hold no valid pixels')
    def mean(a, sl):
        v = a[sl][ok[sl]]
        return float(v.mean()) if v.size else float('nan')
    r0, r1 = mean(lat, (0, slice(None))), mean(lat, (-1, slice(None)))
    c0, c1 = mean(lon, (slice(None), 0)), mean(lon, (slice(None), -1))
    L, Wd = lat.shape
    corners = [(float(lat[y, x]), float(lon[y, x])) for y, x in ((0, 0), (0, Wd - 1), (L - 1, 0), (L - 1, Wd - 1))]
    return dict(line0='north' if r0 > r1 else 'south', col0='east' if c0 > c1 else 'west', flipud=r0 < r1, fliplr=c0 > c1,
                lat_line0=r0, lat_lineN=r1, lon_col0=c0, lon_colN=c1, corners=corners, width=Wd, length=L)


def expected_flips(direction):
    """(flipud, fliplr) for north up and west left, by the path table's direction (A or D), for right-looking ALOS."""
    return (True, False) if direction == 'A' else (False, True)


def heading_ok(heading, direction, tol):
    """G24: a right-looking ALOS heading in the band of the direction (ascending about -11 deg, descending -169)."""
    want = -11.0 if direction == 'A' else -169.0
    d = (float(heading) - want + 180.0) % 360.0 - 180.0
    return abs(d) <= tol, want, d


def snwe(lat, lon, lattice, margin):
    """The kit's ph_pin: SNWE from the geometry's latitude and longitude (finite, non-zero), snapped outward on the
    1/lattice deg lattice with a margin of margin pixels. (text, values)."""
    import math
    import numpy as np
    la = lat[np.isfinite(lat) & (lat != 0)]
    lo = lon[np.isfinite(lon) & (lon != 0)]
    f = float(lattice)
    v = ((math.floor(la.min() * f) - margin) / f, (math.ceil(la.max() * f) + margin) / f,
         (math.floor(lo.min() * f) - margin) / f, (math.ceil(lo.max() * f) + margin) / f)
    return '%.7f,%.7f,%.7f,%.7f' % v, v


def on_lattice(v, lattice):
    return all(abs(round(x * lattice) - x * lattice) < 1e-3 for x in v)


# ---------------------------------------------------------------- D9's statistic
def component_fraction(W, pairs, gw, gl, edge):
    """linog_refpix.py's "component fraction over valid area: mean" over the given (kept) pairs, from the pairs' files:
    per pixel, the share of pairs in whose main connected component (the label >= 1 holding the most pixels) it lies;
    the mean over the valid area (edge pixels in from each side; the minimum coherence finite and the mean above 0).
    Returns dict(mean, max, valid, pairs, per_pair_median)."""
    import numpy as np
    mn = np.ones((gl, gw), np.float32)
    sm = np.zeros((gl, gw), np.float64)
    inm = np.zeros((gl, gw), np.float32)
    per = []
    for pr in pairs:
        d = os.path.join(W, 'Igrams', pr)
        c = np.fromfile(os.path.join(d, 'filt_%s.cor' % pr), dtype='<f4', count=gw * gl).reshape(gl, gw)
        g = np.fromfile(os.path.join(d, 'filt_%s_snaphu.unw.conncomp' % pr), dtype=np.uint8, count=gw * gl).reshape(gl, gw)
        np.minimum(mn, c, out=mn)
        sm += c
        bc = np.bincount(g.ravel().astype(np.int64))
        if bc.size > 1:
            bc[0] = 0
            main = g == int(np.argmax(bc))
            inm += main
            per.append(float(main.sum()) / float(g.size))
        else:
            per.append(0.0)
    n = max(len(pairs), 1)
    av = (sm / n).astype(np.float32)
    inm /= n
    valid = np.zeros((gl, gw), bool)
    valid[edge:gl - edge, edge:gw - edge] = True
    valid &= np.isfinite(mn) & (av > 0)
    if not valid.any():
        return dict(mean=float('nan'), max=float('nan'), valid=0, pairs=len(pairs), per_pair_median=float('nan'))
    return dict(mean=float(inm[valid].mean()), max=float(inm[valid].max()), valid=int(valid.sum()), pairs=len(pairs),
                per_pair_median=float(np.median(per)) if per else float('nan'))


def pairs_of(W):
    """The pair folders of Igrams/ (YYYYMMDD_YYYYMMDD), sorted."""
    d = os.path.join(W, 'Igrams')
    return sorted(n for n in (os.listdir(d) if os.path.isdir(d) else []) if re.match(r'^\d{8}_\d{8}$', n))


def write_json(path, obj):
    P2.write_json(path, obj)


def h5_attrs(path):
    import h5py
    with h5py.File(path, 'r') as f:
        return {k: (v.decode() if isinstance(v, bytes) else v) for k, v in f.attrs.items()}
