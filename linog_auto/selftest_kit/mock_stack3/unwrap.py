"""MOCK unwrap (linog_auto self-test only): filt_<pair>_snaphu.unw (2 x float32) and .unw.conncomp (1 B: label 1 but for
the first two lines; LINOG_MOCK_FRAGMENT=1: label 1 on the top 30 % of lines, label 2 on the next 25 %;
LINOG_MOCK_CCTOP=<pair>: label 1 on the top 27 % only; LINOG_MOCK_CCBOTTOM=<pair>: from line 400 down only;
LINOG_MOCK_CCSMALL=<pair>[,<pair>...]: on the top 10 % only), the reference shelve copy, and the log lines;
LINOG_MOCK_NOUNW=<pair> writes nothing and exits 0."""
import argparse
import os
import re

import linog_mock3 as M


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--ifg', '--coh', '--unwprefix', '--reference', '--defomax', '--alks', '--rlks', '--method'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('unwrap')   # v0.9: no WISDOM_FILE in this step's jobs
    ig = os.path.dirname(os.path.abspath(a.unwprefix))
    if M.env('LINOG_MOCK_NOUNW') == os.path.basename(ig):
        print('MOCK: no unwrapped output (planted)')
        return
    x = open(a.ifg + '.xml').read()
    gw, gl = (int(re.search(r'name="%s">\s*<value>(\d+)' % n, x).group(1)) for n in ('width', 'length'))
    M.copy_shelve(os.path.dirname(a.reference), os.path.join(ig, 'referenceShelve'))
    u = a.unwprefix + '_snaphu.unw'
    M.sparse(u, 8 * gw * gl)
    M.write_xml(u, gw, gl, 'FLOAT', 2)
    import numpy as np
    cc = np.ones((gl, gw), np.uint8)
    cc[:2, :] = 0   # unwrapped nowhere on the first two lines
    pr = os.path.basename(ig)
    if M.env('LINOG_MOCK_FRAGMENT'):   # the main component on the top 30 % of lines only, a second one below it
        cc[int(0.30 * gl):, :] = 0
        cc[int(0.30 * gl):int(0.55 * gl), :] = 2
    if M.env('LINOG_MOCK_CCTOP') == pr:          # unwrapped on the top 27 % of lines only
        cc[int(0.27 * gl):, :] = 0
    if M.env('LINOG_MOCK_CCBOTTOM') == pr:       # unwrapped from line 400 down only
        cc[:400, :] = 0
    if pr in M.env('LINOG_MOCK_CCSMALL').split(','):   # unwrapped on the top 10 % of lines only (G18: largest < 20 %)
        cc[int(0.10 * gl):, :] = 0
    cc.tofile(u + '.conncomp')
    M.write_xml(u + '.conncomp', gw, gl, 'BYTE')
    print('snaphu v1.4.2 (MOCK)')
    print('Growing connected components on second pass')
