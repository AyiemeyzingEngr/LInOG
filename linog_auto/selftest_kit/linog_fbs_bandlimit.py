#!/usr/bin/env python3
"""Band-limit ALOS FBS SLCs to FBD's 14 MHz IN PLACE, at native width.

No decimation: width, length, .slc.xml and the ISCE shelve all stay valid,
so the stack grid, looks and geometry are unchanged. Only pixel values change.

FBS: 28 MHz chirp bandwidth at 32 MHz range sampling.
FBD: 14 MHz at 16 MHz.  Target 14 MHz -> keep_fraction = 14/32*2 = 0.4375.
Nothing is decimated, so there is no Nyquist fold and the exact value is
usable (the decimating path needed 0.4000 to keep the taper below the fold).
"""
import os, sys, glob, shutil, argparse
import numpy as np
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linog_fbs_downsample import create_hanning_bandpass

p = argparse.ArgumentParser()
p.add_argument("indir")
p.add_argument("--keep-fraction", type=float, default=0.4375)
p.add_argument("--taper-width",   type=float, default=0.05)
p.add_argument("--dates", default="")
p.add_argument("--dry-run", action="store_true")
a = p.parse_args()
want = set(a.dates.split(",")) if a.dates else None

for d in sorted(glob.glob(os.path.join(a.indir, "*"))):
    if not os.path.isdir(d): continue
    date = os.path.basename(d)
    if want and date not in want: continue
    xs = glob.glob(os.path.join(d, "*.slc.xml"))
    if not xs: print("skip (no xml) " + d); continue
    xml = xs[0]; slc = xml[:-4]; bak = slc + ".prefilter"
    root = ET.parse(xml).getroot(); w = l = None
    for pr in root.iter('property'):
        n = pr.get('name', '').lower()
        if   n == 'width':  w = int(pr.find('value').text)
        elif n == 'length': l = int(pr.find('value').text)
    print("%s  %dx%d  keep=%.4f%s" % (date, w, l, a.keep_fraction,
          "  [DRY RUN]" if a.dry_run else ""), flush=True)
    if a.dry_run: continue
    if not os.path.exists(bak): shutil.copy2(slc, bak)
    filt = create_hanning_bandpass(w, keep_fraction=a.keep_fraction,
                                   taper_width=a.taper_width)
    arr = np.fromfile(bak, dtype=np.complex64).reshape(l, w)
    out = np.empty_like(arr)
    for i in range(0, l, 1024):
        blk = arr[i:i+1024, :]
        out[i:i+1024, :] = np.fft.ifft(np.fft.fft(blk, axis=1) * filt, axis=1)
    out.tofile(slc)
    print("   written in place, dims unchanged, pristine copy at %s"
          % os.path.basename(bak), flush=True)
print("--- BANDLIMIT DONE")
