#!/usr/bin/env python3
"""MOCK view.py (linog_auto self-test only, v0.7): `view.py FILE DATASET --dem ... --mask ... -v MIN MAX -u UNIT --dpi N
--nodisplay --noverbose -o OUT.png` (the kit's step 9): a small PNG at OUT. LINOG_MOCK_AUX=1 leaves OUT.aux.xml beside it.
v0.13 r2 (the ascending record 15.4, M58): LINOG_MOCK_H5BREAK=<file> writes over that file, when it is there, a few bytes that
are not HDF5 (a file damaged after geocode, step 5, read by nothing in the script's later steps: only by deliver's G6a.11)."""
import os
import sys

import linog_mock6 as M6

M6.planted_fail('view.py')
pos, opt = M6.args(sys.argv[1:], {'--dem': 1, '--mask': 1, '-v': 2, '-u': 1, '--dpi': 1, '-o': 1})
M6.png(opt['-o'])
if os.environ.get('LINOG_MOCK_AUX'):
    open(opt['-o'] + '.aux.xml', 'w').write('<PAMDataset><!-- MOCK sidecar (planted) --></PAMDataset>\n')
if os.environ.get('LINOG_MOCK_H5BREAK') and os.path.isfile(os.environ['LINOG_MOCK_H5BREAK']):
    with open(os.environ['LINOG_MOCK_H5BREAK'], 'wb') as fh:
        fh.write(b'MOCK: not an HDF5 file (LINOG_MOCK_H5BREAK, planted)\n')
    print('MOCK view.py: %s written over (planted)' % os.environ['LINOG_MOCK_H5BREAK'])
print('MOCK view.py: %s %s -> %s' % (pos[0], pos[1] if len(pos) > 1 else '', opt['-o']))
