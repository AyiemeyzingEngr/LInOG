"""MOCK helpers for the Phase 5e and 6 self-test (linog_auto v0.7 only; nothing here runs on real data): the mock MintPy
commands the kit's linog_phase6.sh calls (in the mock env's bin) and the mock GDAL share them.

A mock GeoTIFF is b'MOCKTIFF1\\n', one JSON line (width, height, dtype, geotransform, nodata, the band's metadata) and the
band's raw values, C order. The mock osgeo.gdal opens it, edits it in place (GA_Update) and computes its statistics;
gdalinfo prints it as GDAL does (the lines the kit's verifier greps for).

Planted (the environment, as lp_env.sh passes LINOG_*):
  LINOG_MOCK_P6FAIL=<command>   that mock command (dem_error.py, save_kmz.py, ...) exits 1 before it writes anything
  LINOG_MOCK_AUX=1              the mock view.py leaves a <png>.aux.xml beside its PNG (PAM's sidecar)
  LINOG_MOCK_GDALINFO_FAIL=1    the mock gdalinfo prints no metadata (the verifier's N6 reads no STATISTICS_MEAN)
  LINOG_MOCK_GEOCODE_NOUPDATE=1 (mintpy.cli.geocode) --update ignored
  LINOG_MOCK_P6SLEEP=<command> with LINOG_MOCK_MARK=<file>: that mock command (view.py, or geocode for mintpy.cli.geocode)
                                writes the file and sleeps LINOG_MOCK_SLEEP_S seconds (default 20) before its work
"""
import json
import os
import struct
import sys
import zlib

import numpy as np

MAGIC = b'MOCKTIFF1\n'


def planted_fail(name):
    if os.environ.get('LINOG_MOCK_P6FAIL') == name:
        print('MOCK %s: failed (planted)' % name)
        sys.exit(1)
    if os.environ.get('LINOG_MOCK_P6SLEEP') == name and os.environ.get('LINOG_MOCK_MARK'):
        import time
        with open(os.environ['LINOG_MOCK_MARK'], 'w') as fh:
            fh.write('MOCK %s: sleeping, pid %d\n' % (name, os.getpid()))
        time.sleep(float(os.environ.get('LINOG_MOCK_SLEEP_S') or 20))


def is_tiff(path):
    try:
        with open(path, 'rb') as fh:
            return fh.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def read_tiff(path):
    with open(path, 'rb') as fh:
        if fh.read(len(MAGIC)) != MAGIC:
            raise IOError('%s is not a mock GeoTIFF' % path)
        head = json.loads(fh.readline().decode())
        a = np.frombuffer(fh.read(), dtype=head['dtype']).reshape(head['height'], head['width']).copy()
    return head, a


def write_tiff(path, head, a):
    head = dict(head, width=int(a.shape[1]), height=int(a.shape[0]), dtype=a.dtype.str)
    tmp = path + '.mocktmp'
    with open(tmp, 'wb') as fh:
        fh.write(MAGIC + json.dumps(head, sort_keys=True).encode() + b'\n' + np.ascontiguousarray(a).tobytes())
    os.replace(tmp, path)


def geotransform(attrs):
    return [float(attrs['X_FIRST']), float(attrs['X_STEP']), 0.0, float(attrs['Y_FIRST']), 0.0, float(attrs['Y_STEP'])]


def stats(a, nodata):
    v = a[np.isfinite(a)]
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        v = v[v != nodata]
    if not v.size:
        return None
    return float(v.min()), float(v.max()), float(v.mean()), float(v.std()), 100.0 * v.size / a.size


def png(path, w=8, h=8):
    """A small valid greyscale PNG."""
    raw = b''.join(b'\x00' + bytes(range(w)) for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0)) +
                 chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def h5_read(path, name=None):
    import h5py
    with h5py.File(path, 'r') as f:
        k = name or [x for x in f.keys()][0]
        return f[k][()], {a: (v.decode() if isinstance(v, bytes) else v) for a, v in f.attrs.items()}


def read_date_txt(p):
    """The dates of an exclude_date.txt (MintPy's read_date_txt: the first word of each line, # lines skipped)."""
    out = []
    for ln in open(p) if os.path.isfile(p) else []:
        w = ln.split('#', 1)[0].split()
        if w:
            out.append(w[0][:8])
    return sorted(set(out))


def template_exclude(tpath, key='mintpy.timeFunc.excludeDate'):
    """v0.10: the dates mintpy.timeFunc.excludeDate names in a template, as MintPy 1.6.2 reads them: auto (its default)
    means exclude_date.txt in the working folder, when there; no means none; a .txt file is read; else comma dates. v0.13 r3:
    key, another such key (dem_error's mintpy.topographicResidual.excludeDate)."""
    v = 'auto'
    for ln in open(tpath) if tpath and os.path.isfile(tpath) else []:
        x = ln.split('#', 1)[0].strip()
        if x.split('=', 1)[0].strip() == key and '=' in x:
            v = x.split('=', 1)[1].strip() or 'auto'
    if v == 'auto':
        v = 'exclude_date.txt'
    if v in ('no', 'none', ''):
        return []
    if v.endswith('.txt'):
        return read_date_txt(v)
    return sorted(set(d.strip() for d in v.split(',') if d.strip()))


def yyyymmdd2years(s):
    """v0.13 r2 (the ascending record 15.4, 16.4): MintPy 1.6.2's ptime.yyyymmdd2years, year + (day of year - 1) / 365.25,
    the time base of MintPy's velocity fit and dem_error and of the reading G6a.11 (every mock time base on it)."""
    import datetime
    x = datetime.datetime.strptime(s, '%Y%m%d')
    return x.year + (x.timetuple().tm_yday - 1) / 365.25


def fit_velocity(ts_path, ex=()):
    """v0.10: the mock timeseries2velocity's arithmetic, shared with the mock smallbaselineApp's velocity step: the least-
    squares rate (m/yr) and intercept of each pixel over the dates not in ex, with velocityStd, interceptStd and residue
    from the fit's rms. Returns (dict of float32 arrays, attributes, the dates used). v0.13 r2: time in MintPy's decimal years
    from the first date (v0.7 to v0.13 r1: days since the first date / 365.25)."""
    import h5py
    with h5py.File(ts_path, 'r') as f:
        ts, dates, attrs = f['timeseries'][:].astype(np.float64), [d.decode() for d in f['date'][:]], dict(f.attrs)
    keep = [i for i, d in enumerate(dates) if d not in set(ex)]
    t = np.array([yyyymmdd2years(dates[i]) - yyyymmdd2years(dates[0]) for i in keep])
    n, L, W = ts.shape
    y = ts[keep].reshape(len(keep), -1)
    A = np.c_[t, np.ones(len(keep))]
    x = np.linalg.lstsq(A, y, rcond=None)[0] + 0.0   # + 0.0: no negative zeros (a zero series gives 0.0, as before v0.10)
    e = y - A @ x
    rms = np.sqrt((e ** 2).sum(axis=0) / max(len(keep) - 2, 1))
    out = dict(velocity=x[0], intercept=x[1], velocityStd=rms / max(np.ptp(t), 1e-6), interceptStd=rms, residue=rms)
    return dict((k, v.reshape(L, W).astype(np.float32)) for k, v in out.items()), attrs, [dates[i] for i in keep]


def args(argv, flags_with_value):
    """(positional, {flag: value or list}) of a simple command line."""
    pos, opt, i = [], {}, 0
    while i < len(argv):
        x = argv[i]
        if x in flags_with_value:
            n = flags_with_value[x]
            opt[x] = argv[i + 1:i + 1 + n] if n > 1 else argv[i + 1]
            i += 1 + n
        elif x.startswith('-'):
            opt[x] = True
            i += 1
        else:
            pos.append(x)
            i += 1
    return pos, opt
