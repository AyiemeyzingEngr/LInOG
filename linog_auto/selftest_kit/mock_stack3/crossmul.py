"""MOCK crossmul (linog_auto self-test only): opens both images through their .xml FILE_NAME from the working folder,
as ISCE does; writes <outdir>.int (sparse) and .amp on the multilooked grid of the reference's .xml. v0.7: the .amp
holds the self-test scene's amplitudes (linog_mock3.scene_amp: 2 bands, BIP, its .xml with the scheme and byte order,
as ISCE's), which the kit's linog_watermask.py reads. v0.9: crossmul's wisdom lines (linog_mock3.fft_wisdom)."""
import argparse
import os
import re

import linog_mock3 as M


def dims(p):
    x = open(p + '.xml').read()
    return tuple(int(re.search(r'name="%s">\s*<value>(\d+)' % n, x).group(1)) for n in ('width', 'length'))


def opened(p, W, L):
    """The image as crossmul opens it: its .xml FILE_NAME, a relative name resolved from the working folder (A30)."""
    m = re.search(r'name="file_name">\s*<value>([^<]+)</value>', open(p + '.xml').read())
    fn = m.group(1).strip() if m else None
    if not fn or not os.path.isfile(fn) or os.path.getsize(fn) != 8 * W * L:
        raise IOError('MOCK crossmul: %s.xml names %s, not an 8 x %d x %d B file from %s' % (p, fn, W, L, os.getcwd()))


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--secondary', '--outdir'):
        ap.add_argument(k)
    ap.add_argument('--alks', type=int, default=1)
    ap.add_argument('--rlks', type=int, default=1)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('crossmul')
    M.fft_wisdom('crossmul', os.path.basename(a.outdir))   # v0.9: crossmul plans its FFTs through cfft1d_jpl
    W, L = dims(a.reference)
    opened(a.reference, W, L)
    opened(a.secondary, W, L)
    os.makedirs(os.path.dirname(a.outdir), exist_ok=True)   # as the real crossmul.py makes Igrams/<pair>/
    gw, gl = W // a.rlks, L // a.alks
    M.sparse(a.outdir + '.int', 8 * gw * gl)
    M.write_xml(a.outdir + '.int', gw, gl, 'CFLOAT', 1)
    pr = os.path.basename(a.outdir)
    M.scene_amp(gl, gw, pr if re.match(r'^\d{8}_\d{8}$', pr) else '20000101_20000102').tofile(a.outdir + '.amp')   # v0.7
    M.write_xml(a.outdir + '.amp', gw, gl, 'FLOAT', 2, scheme='BIP')
    print(' Max threads used: MOCK')
