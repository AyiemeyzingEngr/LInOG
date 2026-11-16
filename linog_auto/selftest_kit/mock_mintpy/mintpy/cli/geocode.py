"""MOCK mintpy.cli.geocode (linog_auto self-test only, v0.7; v0.8: REF_Y, REF_X on the geo grid, rounded, as 1.6.2 writes them): `python -m mintpy.cli.geocode FILE... -l LOOKUP -t TEMPLATE
--outdir DIR [--update]`, as the kit's linog_phase6.sh (step 5) and linog_watermask.py call it.

Each dataset of each file goes onto the grid of the template's mintpy.geocode.SNWE and laloStep (the mock
smallbaselineApp's geocode step uses the same grid), by nearest neighbour through the lookup file's latitude and
longitude (the mock geometry is affine, so the map from (lat, lon) to (line, column) is fitted exactly); float data
outside the radar footprint is NaN, integer and boolean data 0. The output is DIR/geo_<name>. --update skips a file
whose output is at least as new as the file and the lookup file, as MintPy 1.6.2's run_or_skip decides it.
Planted: LINOG_MOCK_GEOCODE_NOUPDATE=1 ignores --update (every output written again); LINOG_MOCK_P6FAIL=geocode and
LINOG_MOCK_P6SLEEP=geocode (linog_mock6.planted_fail).
"""
import argparse
import os
import sys

import h5py
import numpy as np


def template(p):
    d = {}
    for ln in open(p):
        s = ln.strip()
        if s and not s.startswith(('#', '%')) and '=' in s:
            k, v = s.split('=', 1)
            d[k.strip()] = v.split('#', 1)[0].strip()
    return d


def grid(snwe, step):
    """(rows, cols, attributes) of the geo grid: Y_FIRST the north edge, X_FIRST the west edge."""
    sn = [float(x) for x in snwe.split(',')]
    st = [float(x) for x in step.split(',')]
    rows, cols = int(round((sn[1] - sn[0]) / abs(st[0]))), int(round((sn[3] - sn[2]) / abs(st[1])))
    return rows, cols, dict(Y_FIRST=str(sn[1]), X_FIRST=str(sn[2]), Y_STEP=str(st[0]), X_STEP=str(st[1]), LENGTH=str(rows),
                            WIDTH=str(cols), Y_UNIT='degrees', X_UNIT='degrees')


def index_map(lat, lon, rows, cols, ga):
    """(line, column, inside) of the radar pixel nearest each geo cell's centre."""
    L, W = lat.shape
    rr, cc = np.mgrid[0:L, 0:W]
    ok = np.isfinite(lat) & np.isfinite(lon) & (lat != 0) & (lon != 0)
    A = np.c_[lat[ok], lon[ok], np.ones(int(ok.sum()))]
    cr = np.linalg.lstsq(A, rr[ok].astype(float), rcond=None)[0]
    ck = np.linalg.lstsq(A, cc[ok].astype(float), rcond=None)[0]
    la = float(ga['Y_FIRST']) + float(ga['Y_STEP']) * (np.arange(rows) + 0.5)
    lo = float(ga['X_FIRST']) + float(ga['X_STEP']) * (np.arange(cols) + 0.5)
    LA, LO = np.meshgrid(la, lo, indexing='ij')
    r = np.rint(cr[0] * LA + cr[1] * LO + cr[2]).astype(np.int64)
    c = np.rint(ck[0] * LA + ck[1] * LO + ck[2]).astype(np.int64)
    inside = (r >= 0) & (r < L) & (c >= 0) & (c < W)
    return np.clip(r, 0, L - 1), np.clip(c, 0, W - 1), inside


def geocode_array(a, im):
    r, c, inside = im
    out = a[..., r, c]
    if out.dtype.kind == 'f':
        out = out.astype(a.dtype)
        out[..., ~inside] = np.nan
    else:
        out = out.copy()
        out[..., ~inside] = 0
    return out


def lookup(p):
    with h5py.File(p, 'r') as f:
        return f['latitude'][()].astype(float), f['longitude'][()].astype(float)


def geocode_file(infile, outfile, im, ga, lat, lon):
    with h5py.File(infile, 'r') as f:
        attrs = dict(f.attrs)
        data = {k: f[k][()] for k in f.keys()}
    with h5py.File(outfile, 'w') as g:
        for k, v in data.items():
            if v.ndim >= 2 and v.shape[-2:] == lat.shape:
                g.create_dataset(k, data=geocode_array(v, im))
            else:
                g.create_dataset(k, data=v)
        for k, v in attrs.items():
            g.attrs[k] = v
        for k, v in ga.items():
            g.attrs[k] = v
        if 'REF_Y' in attrs and 'REF_X' in attrs:   # MintPy writes the reference pixel's position in geocoded files
            y, x = int(attrs['REF_Y']), int(attrs['REF_X'])
            g.attrs['REF_LAT'], g.attrs['REF_LON'] = str(lat[y, x]), str(lon[y, x])
            # v0.8: and REF_Y, REF_X on the geo grid, the rounded index (1.6.2 update_attribute4radar2geo: np.rint)
            g.attrs['REF_Y'] = str(int(np.rint((lat[y, x] - float(ga['Y_FIRST'])) / float(ga['Y_STEP']))))
            g.attrs['REF_X'] = str(int(np.rint((lon[y, x] - float(ga['X_FIRST'])) / float(ga['X_STEP']))))


def main(argv=None):
    import linog_mock6 as M6
    M6.planted_fail('geocode')
    ap = argparse.ArgumentParser(prog='geocode.py')
    ap.add_argument('file', nargs='+')
    ap.add_argument('-l', '--lookup', dest='lookupFile', required=True)
    ap.add_argument('-t', '--template', dest='templateFile')
    ap.add_argument('--outdir', '--output-dir', dest='outdir', default='')
    ap.add_argument('--update', dest='updateMode', action='store_true')
    a = ap.parse_args(argv)
    t = template(a.templateFile) if a.templateFile else {}
    rows, cols, ga = grid(t['mintpy.geocode.SNWE'], t['mintpy.geocode.laloStep'])
    lat, lon = lookup(a.lookupFile)
    im = index_map(lat, lon, rows, cols, ga)
    update = a.updateMode and not os.environ.get('LINOG_MOCK_GEOCODE_NOUPDATE')
    for infile in a.file:
        outfile = os.path.join(a.outdir or os.path.dirname(infile), 'geo_' + os.path.basename(infile))
        if update and os.path.isfile(outfile) and max(os.path.getmtime(infile), os.path.getmtime(a.lookupFile)) <= os.path.getmtime(outfile):
            print('%s exists and is newer than %s --> skip.' % (outfile, [infile, a.lookupFile]))
            print('update mode is ON, skip geocoding.')
            continue
        os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
        geocode_file(infile, outfile, im, ga, lat, lon)
        print('MOCK geocode: %s -> %s (%d x %d)' % (infile, outfile, rows, cols))
    return 0


if __name__ == '__main__':
    sys.exit(main())
