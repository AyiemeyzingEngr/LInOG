"""MOCK baselineGrid (linog_auto self-test only): a 30 x 30 float32 grid with .xml, .vrt and .full.vrt, and the log line."""
import argparse
import os

import numpy as np

import linog_mock3 as M


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--secondary', '--baseline_file'):
        ap.add_argument(k)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('baselineGrid')   # v0.9: no WISDOM_FILE in this step's jobs
    os.makedirs(os.path.dirname(a.baseline_file), exist_ok=True)
    np.zeros((30, 30), dtype='<f4').tofile(a.baseline_file)
    M.write_xml(a.baseline_file, 30, 30, 'FLOAT')
    open(a.baseline_file + '.full.vrt', 'w').write('<VRTDataset/>\n')
    print('Baseline file %s dims: 30L x 30P' % a.baseline_file)
