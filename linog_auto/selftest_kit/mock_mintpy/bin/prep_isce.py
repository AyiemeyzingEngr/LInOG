#!/usr/bin/env python3
"""MOCK prep_isce.py (linog_auto self-test only; nothing here runs on real data): the .rsc files MintPy 1.6.2's prep_isce.py
writes for a stripmapStack frame: data.rsc beside the metadata file (from the shelve: STARTING_RANGE, POLARIZATION,
HEADING, ...), <file>.rsc beside each interferogram of -f and each geometry file of --geom-files. The metadata file is
the shelve: `-m .../data.dat` reads the shelve `data` (MintPy strips the extension). Update mode, MintPy's default
(--force turns it off), as 1.6.2 has it: data.rsc is left as it is when it is newer than the metadata file, and any
other .rsc when what it would write is already in it; load_data's own call of prep_isce (the mock smallbaselineApp
calls run() below) therefore rewrites nothing the prep phase wrote. Planted values:
  LINOG_MOCK_HEADING=<deg>   HEADING in data.rsc (default -168.94, a descending ALOS-1 frame)
  LINOG_MOCK_POL=<pol>       POLARIZATION in data.rsc (default HH)
"""
import argparse
import glob
import os
import re
import sys


def dims(p):
    x = open(p + '.xml').read()
    return tuple(int(re.search(r'name="%s">\s*<value>\s*(\d+)' % n, x).group(1)) for n in ('width', 'length'))


def read_rsc(p):
    d = {}
    for ln in open(p):
        w = ln.split(None, 1)
        if len(w) == 2:
            d[w[0]] = w[1].strip()
    return d


def write_rsc(p, d, update=True):
    """1.6.2's write_roipac_rsc: in update mode, nothing written when every key/value is in the file already."""
    d = dict((k, str(v)) for k, v in d.items())
    if update and os.path.isfile(p) and set(d.items()).issubset(set(read_rsc(p).items())):
        return False
    with open(p, 'w') as fh:
        for k in sorted(d):
            fh.write('%-30s %s\n' % (k, d[k]))
    return True


def run(meta_file, geom_dir, baseline_dir, obs_patterns, geom_files, update=True):
    shelf = os.path.splitext(meta_file)[0]
    if not any(os.path.isfile(shelf + e) for e in ('.dat', '.db', '')):
        raise SystemExit('MOCK prep_isce.py: no shelve for %s' % meta_file)
    meta = dict(PLATFORM='Alos', STARTING_RANGE='845217.5596', WAVELENGTH='0.2360571', PRF='2159.827',
                POLARIZATION=os.environ.get('LINOG_MOCK_POL', 'HH'), HEADING=os.environ.get('LINOG_MOCK_HEADING', '-168.94'),
                beam_mode='SM', PROCESSOR='isce')
    drsc = os.path.join(os.path.dirname(meta_file), 'data.rsc')
    if update and os.path.isfile(drsc) and os.path.getmtime(drsc) > os.path.getmtime(meta_file):
        meta = read_rsc(drsc)       # 1.6.2 extract_isce_metadata: skip, read the existing data.rsc
        print('data.rsc is newer than %s: skip' % meta_file)
    else:
        write_rsc(drsc, meta, update=False)
        print('write metadata to %s' % drsc)
    n = w_n = 0
    for pat in obs_patterns:
        for f in sorted(glob.glob(pat)):
            w, l = dims(f)
            w_n += write_rsc(f + '.rsc', dict(meta, WIDTH=w, FILE_LENGTH=l, DATE12=os.path.basename(os.path.dirname(f))[2:]), update)
            n += 1
    g_n = 0
    for g in geom_files:
        p = os.path.join(geom_dir, g)
        if os.path.isfile(p):
            w, l = dims(p)
            g_n += write_rsc(p + '.rsc', dict(meta, WIDTH=w, FILE_LENGTH=l), update)
    print('prep_isce.py (MOCK): %d interferograms (%d .rsc written), %d geometry files (%d .rsc written)' % (n, w_n, len(geom_files), g_n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', dest='obs_files', nargs='+', default=[])
    ap.add_argument('-m', '--meta-file', dest='meta_file', required=True)
    ap.add_argument('-b', '--baseline-dir', dest='baseline_dir')
    ap.add_argument('-g', '--geometry-dir', dest='geom_dir', required=True)
    ap.add_argument('--geom-files', dest='geom_files', nargs='*', default=[])
    ap.add_argument('--force', dest='update_mode', action='store_false')
    a = ap.parse_args()
    run(a.meta_file, a.geom_dir, a.baseline_dir, a.obs_files, a.geom_files, a.update_mode)


if __name__ == '__main__':
    sys.exit(main())
