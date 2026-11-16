#!/usr/bin/env python3
"""lp_p6.py -- shared helpers for linog_auto Phase 5e and Phase 6 (v0.7; v0.8: the keys of RUN_MANIFEST.json's lead product
and readings): the water mask, the delivery, its acceptance and the review package.

What it holds: the settings and pins of linog_phase6.cfg; the names that depend on the frame (the tag P<PATH>F<FRAME>,
the delivery folder mintpy/geo/LInOG_Upload_<TAG>/, the package folder _xfer/<PREFIX>_<TAG>_<VERSION>_<date>_review/);
each phase's own outputs (the listings behind --state and the "nothing in the way" gates); the kit's tools and their
pins; the prior phase as these phases read it (a dry run reads the frame's own record when the frame has run that far);
the look direction from geom_reference/los.rdr (D7, F55); the 16 names of the delivery; GeoTIFF checks through the env's
GDAL; and the hash-of-hashes and manifest helpers of the package (the proven staging of the 12 frames).

The phases run inside lp_env.sh; numpy, h5py and GDAL are imported only inside the functions that need them, so --state
and the dry-run plans need the standard library only. The files of Phases 0 to 5 are byte-identical to v0.6.1.
"""
import collections
import glob
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time

import lp_common as C
import lp_p1 as P1
import lp_p3 as P3
import lp_p5 as P5

VERSION_P6 = 'linog_auto v0.13 r2 (2026-10-19)'   # the release that last changed this module (v0.8 before; v0.13: the package
# prefix; v0.13 r2: KEYS takes G6a.11's settings)
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = ('lp_p6.py', 'lp_p5.py', 'lp_p3.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py')
KEYS = ('KIT_WATERMASK_MD5', 'KIT_PHASE6_MD5', 'KIT_LOS2HV_MD5', 'KIT_EMBED_MD5', 'KIT_KMZ_MD5', 'KIT_VERIFY_MD5', 'VERIFY_COPY',
        'DELIVERY_FILES', 'DELIVERY_TIF', 'DELIVERY_PNG', 'DELIVERY_KMZ', 'LOS_HEADING_TOL_DEG', 'LOS_INCIDENCE_TOL_DEG', 'XFER',
        'PACKAGE_PREFIX', 'PACKAGE_PREFIX_ASC', 'PACKAGE_VERSION', 'LEAD_PRODUCT', 'LEAD_REASON', 'READ_RINGS_KM', 'READ_RING_PRODUCTS', 'READ_DISCS_KM',
        'READ_DISC_PRODUCTS', 'GNSS_STATIONS',
        # v0.13 r2: G6a.11, the mode step (lp_modestep.KEYS: the ascending record 15.2's settings, 16.2's size line)
        'MODESTEP_MIN_PER_MODE', 'MODESTEP_MIN_PIXELS', 'MODESTEP_PLANARITY_VOID', 'MODESTEP_ROUTE1_VOID', 'MODESTEP_L95_MAX',
        'MODESTEP_ALPHA', 'MODESTEP_TESTS', 'MODESTEP_PARTIAL_R_MAX', 'MODESTEP_B95_MAX_M_YR')
KIT6 = collections.OrderedDict((('linog_watermask.py', 'KIT_WATERMASK_MD5'), ('linog_phase6.sh', 'KIT_PHASE6_MD5'),
                                ('linog_los2hv.py', 'KIT_LOS2HV_MD5'), ('linog_embed_stats.py', 'KIT_EMBED_MD5'),
                                ('linog_gen_interactive_kmz.py', 'KIT_KMZ_MD5'), ('linog_verify_frame.py', 'KIT_VERIFY_MD5')))
ORDER = (('5e', 'wmask'), ('6a', 'deliver'), ('6b', 'accept'), ('6c', 'package'))
# the six products and their file suffixes (linog_phase6.sh's steps 6 to 9); the two corrections of the KMZs
SIX = ('demErr', 'demErr_ramp', 'Vertical', 'Vertical_ramp', 'Horizontal', 'Horizontal_ramp')
HV = ('Vertical', 'Vertical_ramp', 'Horizontal', 'Horizontal_ramp')
CORR = ('demErr', 'demErr_ramp')


def cfg_file():
    return os.environ.get('LINOG_PHASE6_CFG') or os.path.join(HERE, 'linog_phase6.cfg')


def load_p6():
    """linog_phase6.cfg as a dict (KEY=value lines; # comments)."""
    f = cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['p6_cfg_file'], d['p6_cfg_md5'] = f, C.md5_file(f)
    return d


def tag(path, frame):
    return 'P%sF%s' % (path, frame)


def upload_rel(path, frame):
    return 'mintpy/geo/LInOG_Upload_%s' % tag(path, frame)


def delivery_names(path, frame):
    """The 16 files linog_phase6.sh writes at the top of the delivery folder: 2 velocity KMZ (step 7), 6 GeoTIFF (8),
    6 hillshade PNG (9), 2 time-series KMZ (10, the kit's interactive tool)."""
    t = tag(path, frame)
    return sorted(['%s_Velocity_%s.kmz' % (t, c) for c in CORR] + ['%s_Velocity_%s.tif' % (t, s) for s in SIX] +
                  ['%s_Velocity_Hillshade_%s.png' % (t, s) for s in SIX] + ['%s_TimeSeries_%s.kmz' % (t, c) for c in CORR])


def deliver_outs(path, frame):
    """deliver's own outputs: the delivery folder, the demErr chains and their velocities, the geocoded files of step 5,
    the four H/V files of step 6, demErr.h5 and timeseriesResidual.h5 (chain A rewrites both; sbas's listing leaves
    them out for this reason), the ramp-first copies of step 1, and RUN_MANIFEST.json at the frame root."""
    g = 'mintpy/geo/'
    return ((upload_rel(path, frame), 'mintpy/timeseries_demErr.h5', 'mintpy/timeseries_demErr_ramp.h5',
             'mintpy/velocity_demErr.h5', 'mintpy/velocity_demErr_ramp.h5', 'mintpy/velocity_ramp_demErr.h5',
             'mintpy/demErr.h5', 'mintpy/timeseriesResidual.h5', 'mintpy/demErr_rampfirst.h5', 'mintpy/timeseriesResidual_rampfirst.h5',
             g + 'geo_timeseries_demErr.h5', g + 'geo_timeseries_demErr_ramp.h5', g + 'geo_velocity_demErr.h5',
             g + 'geo_velocity_demErr_ramp.h5') + tuple(g + 'geo_velocity_%s.h5' % s for s in HV) + ('RUN_MANIFEST.json',))


def deliver_way(path, frame):
    """What in the frame a run of deliver would write over: everything of deliver_outs except demErr.h5 and
    timeseriesResidual.h5 (sbas's, until chain A rewrites them) and the ramp-first copies (step 1 keeps copies already
    there: they hold sbas's ramp-first estimates, which chain A replaces in demErr.h5)."""
    keep = ('mintpy/demErr.h5', 'mintpy/timeseriesResidual.h5', 'mintpy/demErr_rampfirst.h5', 'mintpy/timeseriesResidual_rampfirst.h5')
    return tuple(x for x in deliver_outs(path, frame) if x not in keep)


WMASK_OUTS = ('mintpy/watermask', 'mintpy/maskTempCoh.h5', 'mintpy/geo/geo_maskTempCoh.h5')
ACCEPT_OUTS = ()   # accept writes no file in the frame but its log: its record holds the verifier's lines


def package_prefix(q, direction):
    """v0.13 (the ascending record 11.13, 22-b): the review package's prefix by the path's direction (cfg['direction'],
    the path table's or the frame rule's): PACKAGE_PREFIX (LINOG_DESC) for a descending path, PACKAGE_PREFIX_ASC (LINOG_ASC)
    for an ascending one; anything else is an error, not a guess."""
    d = str(direction or '').strip().upper()
    if d == 'D':
        return q['PACKAGE_PREFIX']
    if d == 'A':
        return q['PACKAGE_PREFIX_ASC']
    raise ValueError('the package prefix: the direction %r is neither A nor D' % (direction,))


def package_name(path, frame, q, day, direction):
    return '%s_%s_%s_%s_review' % (package_prefix(q, direction), tag(path, frame), q['PACKAGE_VERSION'], day)


def package_glob(path, frame, q, direction):
    """Every package of this frame and version, whatever its date: _xfer/<PREFIX>_<TAG>_<VERSION>_*_review."""
    return '%s/%s_%s_%s_*_review' % (q['XFER'], package_prefix(q, direction), tag(path, frame), q['PACKAGE_VERSION'])


def manifest_name(path, frame):
    return 'TRANSFER_MANIFEST_%s.txt' % tag(path, frame)


def tools(env, q, names=None):
    """{name: (path, md5 or None, pin)}: the kit's Phase 5e and 6 tools in $S."""
    out = collections.OrderedDict()
    for n, key in KIT6.items():
        if names and n not in names:
            continue
        p = os.path.join(env['KIT'], n)
        out[n] = (p, C.md5_file(p) if os.path.isfile(p) else None, q[key])
    return out


def copy_gate(st, gid, q):
    """D6: the package's verifier copy as the package's MANIFEST.md5 lists it (install checks the package against it)."""
    p = os.path.join(HERE, q['VERIFY_COPY'])
    got = C.md5_file(p) if os.path.isfile(p) else None
    want = None
    mf = os.path.join(HERE, 'MANIFEST.md5')
    for ln in open(mf) if os.path.isfile(mf) else []:
        w = ln.split()
        if len(w) == 2 and w[1] == q['VERIFY_COPY']:
            want = w[0]
    ok = got is not None and got == want
    st.gate(gid, 'the verifier copy (D6)', 'PASS' if ok else 'FAIL', '%s md5 %s%s' % (p, got, ', as MANIFEST.md5 lists it' if ok else ''),
            'as the package\'s MANIFEST.md5 lists it (%s)' % want)
    return p if ok else None


def frame_rec(W, index, phase):
    return P1.record(W, index, phase) or {}


def prior6(st, gid, recdir, W, index, phase, outs, dry):
    """The phase this one reads, as P5.prior5 reads it, with its own outputs: PASS on record and its files as it recorded
    them. A dry run reads the frame's own record when the frame's phase is PASS (the frame has run that far, so the
    dry run can read its files), and the dry run's record otherwise (a plan). Returns (record or None, from the frame)."""
    if dry:
        fr = frame_rec(W, index, phase)
        if fr.get('verdict') == 'PASS' and not fr.get('outputs', {}).get('planned'):
            ch = P3.listing_changed(W, outs, fr.get('outputs', {}).get('files'))
            st.gate(gid, '%s PASS on record' % phase, 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                    'the frame\'s P%s %s PASS, its files as it recorded them (the dry run reads the frame)' % (index, phase))
            return (None if ch else fr), True
        r = P3.prior3(st, gid, recdir, index, phase)
        if r:
            st.gate(gid, '%s PASS on record' % phase, 'PASS', 'the dry run\'s P%s %s: %s' % (
                index, phase, 'a plan (the frame\'s own has not run)' if r.get('outputs', {}).get('planned') else 'PASS'))
        return r, False
    r = P3.prior3(st, gid, recdir, index, phase)
    if not r:
        return None, True
    if r.get('outputs', {}).get('planned'):
        st.gate(gid, '%s PASS on record' % phase, 'FAIL', 'the record in %s is a dry run\'s, not a run\'s' % recdir, 'a run\'s PASS',
                'a dry run was written into the frame\'s own records; run the phase for real')
        return None, True
    ch = P3.listing_changed(W, outs, r.get('outputs', {}).get('files'))
    st.gate(gid, '%s PASS on record' % phase, 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
            'P%s %s PASS, its files as it recorded them' % (index, phase))
    return (None if ch else r), True


def which_gate(st, gid, s, cmds, what):
    """P5.which_gate's check under this phase's own name: each command on the PATH resolves into the pinned env's bin."""
    import shutil
    bad, got = [], []
    want_dir = os.path.realpath(os.path.join(s['ENV_PREFIX'], 'bin'))
    for c in cmds:
        w = shutil.which(c)
        got.append('%s -> %s' % (c, w))
        if not w or os.path.realpath(os.path.dirname(os.path.abspath(w))) != want_dir:
            bad.append('%s resolves to %s, want %s/%s' % (c, w, want_dir, c))
    st.gate(gid, what, 'FAIL' if bad else 'PASS', '; '.join(got), 'the pinned env\'s bin', '\n'.join(bad))
    return not bad


def state(recdir, W, phase, index, fp, outs):
    """--state: C.state(), and a CURRENT record whose files are gone or changed reads STALE."""
    def missing(rec):
        return P3.listing_changed(W, outs, (rec or {}).get('outputs', {}).get('files'))
    return P1.state_with_outputs(recdir, phase, index, fp, missing)


def way_gate(st, gid, W, phase, way, later, dry):
    """DECISION when this phase's outputs are in the frame already (P5.way_gate's rule, with the phase's own list)."""
    own = P3.present(W, way)
    lat = sorted(os.path.relpath(x, W) for rel in later for x in glob.glob(os.path.join(W, rel)))   # the folders themselves
    if dry:
        st.gate(gid, 'nothing in the way', 'INFO', 'dry run: in the frame now: %s' % (', '.join(own + lat) or 'none of them'),
                '%s absent' % ', '.join(way))
        return True
    if own:
        st.gate(gid, 'nothing in the way', 'DECISION', 'in the frame already: %s%s' % (
            ', '.join(own[:8]) + (' and %d more' % (len(own) - 8) if len(own) > 8 else ''),
            ('; and what the phases that read them made: %s' % ', '.join(lat[:6])) if lat else ''),
            '%s absent' % ', '.join(way[:4]) + (' ...' if len(way) > 4 else ''),
            'this run would write over them (an earlier run\'s, or a run whose inputs have changed since); move them%s into '
            '%s/_archive/ and run again' % (' and the outputs listed after them' if lat else '', W))
        return False
    st.gate(gid, 'nothing in the way', 'PASS', '%d paths absent' % len(way), 'all absent')
    return True


def begin(recdir, phase, index, path, frame, fp, logic, inputs):
    st = P3.begin(recdir, phase, index, path, frame, fp, logic, inputs, None)
    st.rec['version'] = VERSION_P6
    st.rec['tools'] = C.tool_md5s(*(('lp_%s.py' % phase,) + TOOLS))
    st.write()
    return st


def header(phase, index, path, frame, W, dry, extra=''):
    print('%s  Phase %s %s  p%s f%s  %s' % (VERSION_P6, index, phase, path, frame, C.utc()))
    print('   frame folder %s%s%s' % (W, extra, '   (DRY RUN: the frame is only read)' if dry else ''))
    sys.stdout.flush()


# ---------------------------------------------------------------- the look direction (D7, F55)
def los_direction(W):
    """From geom_reference/los.rdr (ISCE: band 1 incidence, band 2 the azimuth of the ground-to-satellite vector,
    anticlockwise from north; BSQ as ISCE writes it on felix, RD6): the medians over the valid pixels, the heading as
    MintPy's azimuth2heading_angle gives it for a right-looking sensor, the bearing toward the satellite along ground
    range (clockwise from north) and the look azimuth (from the satellite to the ground). RD6 read F3320 as incidence
    38.836 deg, heading -168.94, toward the satellite 101.1 deg."""
    import numpy as np
    xml = open(os.path.join(W, 'geom_reference', 'los.rdr.xml')).read()
    m = re.search(r'name="scheme">\s*<value>\s*([^<\s]+)\s*</value>', xml)
    if m and m.group(1).upper() != 'BSQ':
        raise ValueError('geom_reference/los.rdr.xml says scheme %s; this reader takes BSQ (RD6 read BSQ on felix)' % m.group(1))
    inc = P5.raster(W, 'geom_reference/los.rdr', '<f4', 1).astype('f8')
    az = P5.raster(W, 'geom_reference/los.rdr', '<f4', 2).astype('f8')
    v = np.isfinite(inc) & (inc > 0) & (inc < 90) & np.isfinite(az) & (az != 0)
    if not v.any():
        raise ValueError('geom_reference/los.rdr holds no valid pixel')
    az_m = float(np.median(az[v]))
    head = -(az_m - 90.0)
    head -= round(head / 360.0) * 360.0
    toward = (-az_m) % 360.0
    return dict(incidence_median=float(np.median(inc[v])), incidence_min=float(inc[v].min()), incidence_max=float(inc[v].max()),
                azimuth_angle_median=az_m, heading=head, toward_satellite_bearing=toward, look_azimuth=(toward + 180.0) % 360.0,
                valid_px=int(v.sum()), scheme=m.group(1).upper() if m else 'none in the .xml (BSQ assumed)',
                source='geom_reference/los.rdr (band 2 median; MintPy azimuth2heading_angle, right-looking)')


def stack_incidence(W):
    """The median of inputs/geometryRadar.h5's incidenceAngle over its valid pixels (MintPy loaded it from los.rdr band 1),
    or None."""
    import h5py
    import numpy as np
    p = os.path.join(W, 'mintpy', 'inputs', 'geometryRadar.h5')
    if not os.path.isfile(p):
        return None
    with h5py.File(p, 'r') as f:
        if 'incidenceAngle' not in f:
            return None
        a = f['incidenceAngle'][()].astype('f8')
    v = np.isfinite(a) & (a > 0) & (a < 90)
    return float(np.median(a[v])) if v.any() else None


def kit_ranges(script):
    """The -v MIN MAX of the pinned linog_phase6.sh's save_kmz.py and view.py lines (G14: the renders' range is the
    script's, fixed by its pin), as [(command, min, max)]."""
    out = []
    for ln in re.sub(r'\\\n\s*', ' ', open(script).read()).splitlines():   # a command continued over lines with \ is one line
        m = re.search(r'\b(save_kmz\.py|view\.py)\b.*?-v (-?[\d.]+) (-?[\d.]+)', ln)
        if m and not ln.lstrip().startswith('#'):
            out.append((m.group(1), float(m.group(2)), float(m.group(3))))
    return out


def run_group(cmd, cwd, log, extra_env=None):
    """P5.run_logged with the command in a session of its own (the kit's linog_phase6.sh and the MintPy steps under it):
    a stop of this phase (Ctrl-C, SIGTERM, SIGHUP) ends the whole group, SIGTERM then SIGKILL after 30 s, before the
    record says ERROR, so nothing goes on writing into the frame after the run has let go of its lock. (rc, output)."""
    e = dict(os.environ)
    e.update(extra_env or {})
    t0 = time.time()
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, 'wb') as fh:
        fh.write(('# %s  %s  (cwd %s)\n' % (C.utc(), ' '.join(cmd), cwd)).encode('utf-8', 'replace'))
        fh.flush()
        start = fh.tell()
        p = subprocess.Popen(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = p.wait()
        except BaseException:
            for sig, wait in ((signal.SIGTERM, 30), (signal.SIGKILL, 10)):
                try:
                    os.killpg(p.pid, sig)
                    p.wait(timeout=wait)
                    break
                except (OSError, subprocess.TimeoutExpired):
                    continue
            with open(log, 'a') as fh2:
                fh2.write('# stopped after %.1f s: the command\'s group ended (rc %s)\n' % (time.time() - t0, p.poll()))
            raise
    with open(log, 'rb') as fh:
        fh.seek(start)
        out = fh.read().decode('utf-8', 'replace')
    with open(log, 'a') as fh:
        fh.write('# rc %d  %.1f s\n' % (rc, time.time() - t0))
    return rc, out


def compass(b):
    names = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
    return names[int((b % 360.0) / 22.5 + 0.5) % 16]


# ---------------------------------------------------------------- GeoTIFFs through the env's GDAL
def tif_facts(p):
    """(STATISTICS_MEAN or None, NoData, finite pixels, width, height) of a GeoTIFF band 1, read with PAM off (no
    .aux.xml is written by the read)."""
    import numpy as np
    from osgeo import gdal
    gdal.UseExceptions()
    gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')
    ds = gdal.Open(p)
    b = ds.GetRasterBand(1)
    mean = b.GetMetadataItem('STATISTICS_MEAN')
    nd = b.GetNoDataValue()
    a = b.ReadAsArray()
    out = (mean, nd, int(np.isfinite(a).sum()), ds.RasterXSize, ds.RasterYSize)
    ds = None
    return out


# ---------------------------------------------------------------- the package (the 12 frames' staging, 31 Aug 2026)
def md5_all(paths):
    """Path-independent content digest, the staging's hash-of-hashes: md5 of the files' md5s, sorted, one per line, as
    `md5sum FILES | cut -c1-32 | LC_ALL=C sort | md5sum` and `cut -c1-32 TRANSFER_MANIFEST_<TAG>.txt | LC_ALL=C sort |
    md5sum` print it (so the operator can repeat it on the laptop)."""
    hs = sorted(C.md5_file(p) for p in paths)
    return hashes_md5(hs), len(hs)


def hashes_md5(hs):
    return hashlib.md5(''.join(h + '\n' for h in sorted(hs)).encode()).hexdigest()


def manifest_lines(root, name):
    """'md5  ./relative' for every regular file under root but the manifest itself, sorted as LC_ALL=C sort would."""
    out = []
    for d, ds, fs in os.walk(root):
        ds.sort()
        for f in fs:
            q = os.path.join(d, f)
            rel = './' + os.path.relpath(q, root)
            if f == name and d == root:
                continue
            if os.path.isfile(q) and not os.path.islink(q):
                out.append((rel, C.md5_file(q)))
    out.sort(key=lambda x: x[0].encode())
    return ['%s  %s' % (h, rel) for rel, h in out]


def check_manifest(root, name):
    """md5sum -c on the package's manifest, in Python: (lines, failures)."""
    bad, n = [], 0
    for ln in open(os.path.join(root, name)):
        ln = ln.rstrip('\n')
        if not ln:
            continue
        n += 1
        h, rel = ln.split('  ', 1)
        q = os.path.join(root, rel)
        if not os.path.isfile(q) or C.md5_file(q) != h:
            bad.append(rel)
    return n, bad


def write_json(path, obj):
    P5.write_json(path, obj)


def jsonable(o):
    return json.loads(json.dumps(o, default=str))


def rel_files(W, rel):
    return sorted(p for p in glob.glob(os.path.join(W, rel)) if os.path.isfile(p) and not os.path.islink(p))


def pages_of(report_rec):
    """The report's pages and pair JPEGs as its record lists them (paths relative to the frame)."""
    files = [x[0] for x in (report_rec or {}).get('outputs', {}).get('files', [])]
    pages = sorted(f for f in files if re.match(r'^Igrams/reports/[^/]+_Igram_Report_Page_\d+\.jpg$', f))
    pairs = sorted(f for f in files if re.match(r'^Igrams/reports/pairs/filt_\d{8}_\d{8}_(phase|combined)\.jpg$', f))
    return pages, pairs
