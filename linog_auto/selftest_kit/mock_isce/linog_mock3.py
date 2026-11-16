"""MOCK radar products for the Phase 3 and 4 self-test (linog_auto only; nothing here runs on real data).

The kit's G7 and G10 read 512 x 512 windows at rows chosen on a hardcoded 18432-line frame, so the Phase 3 test frame
is 1000 samples x 18432 lines. Every SLC-like file here is sparse except three bands of rows that hold one fixed
"ground" amplitude pattern (the same for every date) times a small per-date noise, with a per-date random phase:
the rows the gates read (their three textured windows and their frame-amplitude grid). geom_reference/hgt.rdr is
textured over exactly those windows, so the gates find three viable windows, a quorum. Planted cases come from the
environment (lp_env.sh passes LINOG_*):
  LINOG_MOCK_N53=<date>        that date's coarse SLC shifted 32 samples in range (N53; v0.13: a comma list of dates)
  LINOG_MOCK_OFFFRAME=<date>   that date's azimuth.off 100 x the others' (an off-frame granule, G21; v0.13: a comma list)
  v0.13 (R7's cases, part 5):
  LINOG_MOCK_AZNAN=<dates>     those dates' azimuth.off rows at -999999.0, below G21's fill line (a row with no ratio)
  LINOG_MOCK_COARSEEMPTY=<dates> those dates' coarse SLCs all zeros (G7's windows read EMPTY on them)
  LINOG_MOCK_GATEOFF=<date>:<m>[,...] that date's first sample truly at the leader's r0 + m metres (a range window the
                               records may or may not show): its coarse SLC moved by (the shelve's startingRange - (r0 + m))
                               / SLR(REF) samples, so rwin's correction (startingRange set to r0 + k x gate) cancels it
                               and an uncorrected one-gate window reads 32 samples on an FBS reference (M79, M80)
  LINOG_MOCK_THIN=1            hgt.rdr textured over two windows only (G7 below its quorum)
  LINOG_MOCK_JOBFAIL=<pair>    refineSecondaryTiming raises for that pair
  LINOG_MOCK_P3SLEEP=<pair> with LINOG_MOCK_MARK=<file>: refineSecondaryTiming writes the file and sleeps 60 s there
  LINOG_MOCK_GDALFAIL=1        gdal_translate fails (referenceStackCopy.py goes on, as the real one does)
  LINOG_MOCK_NOUNW=<pair>      unwrap writes nothing for that pair and exits 0
  LINOG_MOCK_DEADDATE=<date>   every pair of that date at coherence 0.2
  LINOG_MOCK_BIGAZ=<pair>:<px> refineSecondaryTiming adds px to that pair's azimuth offset (G9p)
  LINOG_MOCK_APPLYSLEEP=<s>    the mock env's python3 writes LINOG_MOCK_MARK and sleeps before the kit's G16 --apply
  LINOG_MOCK_BADPAIR=<pair>    that pair's filt_<pair>.int holds random phase (G18/G20 flag it; v0.6)
  LINOG_MOCK_FRAGMENT=1        every pair's main connected component on the top 30 % of lines only (D9; v0.6)
  LINOG_MOCK_CCTOP=<pair>      that pair unwrapped on the top 27 % of lines only (G19; v0.6)
  LINOG_MOCK_CCBOTTOM=<pair>   that pair unwrapped from line 400 down only (G19; v0.6)
  LINOG_MOCK_CCSMALL=<pairs>   those pairs unwrapped on the top 10 % of lines only (G18 culls them; v0.6)
v0.9: fft_wisdom() is ISCE2's cfft1d_jpl on its first call in a process, for the mock steps whose real modules plan
their FFTs through it (refineSecondaryTiming's ampcor, crossmul, FilterAndCoherence's icu), with the wisdom imported by
the real libfftw3f the mock env carries (MOCK_FFTW_LIB, set by its activate.d); env_line() prints WISDOM_FILE as a
step's job sees it. Planted:
  LINOG_MOCK_NOWISDOM=<pair>   that pair's wisdom lines say length 0, as if WISDOM_FILE had not reached the job
  LINOG_MOCK_WISDOMSTOP=<pair> that pair's import returns 0: STOP cannot import fftw wisdom file, exit status 0
  LINOG_MOCK_ONEWISDOM=<pair>  icu prints no wisdom line for that pair
  LINOG_MOCK_WISDOMTOUCH=<pair> that pair's job appends a line to WISDOM_FILE after its import (the file changed during the step)
v0.12: d1_plant() is drop1's cases' (the mock smallbaselineApp's invert_network and the mock ifgram_inversion.py apply it):
  LINOG_MOCK_D1BAD=<pair>:<cells>[,...] while that pair is kept in an inversion, the temporal coherence falls to 0.55 on a
                               block of about that many land cells (10 lines from line 20 + 30 x its place in the list,
                               columns from 10, at most 60 wide), so dropping it gains them back
  LINOG_MOCK_D1FAIL=<pair>     the mock ifgram_inversion.py exits 1 when it inverts without that pair
  LINOG_MOCK_D1SLEEP=<pair>:<s> the mock ifgram_inversion.py sleeps that long first when it inverts without that pair
                               (with LINOG_MOCK_MARK=<file>: 'pid <its pid>' written there first)
  LINOG_MOCK_COHPAIR=<pair>:<c>[,...] the mock FilterAndCoherence gives that pair coherence c (drop1's peers)
v0.7: scene() is the Phase 5e and 6 cases' ground on the multilooked grid (line 0 north, column 0 east, a descending
frame's): the sea in the south-east corner, the western half of it decorrelated, a bright pier in the rest, and a
dark near-range strip along column 0 over the land. crossmul writes each pair's .amp from it (2 bands, BIP, as ISCE's
.amp), and the mock smallbaselineApp gives the sea a flat height and the decorrelated part a low temporal coherence.
"""
import os
import shelve
import signal
import sys

import numpy as np

LINES_FULL = 18432
BANDS = ((0, 512), (7167, 7680), (14335, 14848))
WINDOWS = (0, 7168, 14336)   # the candidate window rows inside the bands


def env(k):
    return os.environ.get(k, '')


_FFT_DONE = set()


def fft_wisdom(module, pair):
    """cfft1d_jpl's first call in this process for module (ampcor, crossmul or icu: each real module has its own copy):
    `wisdomFile, length = <WISDOM_FILE> <length>` as gfortran prints it; with a file, its import through MOCK_FFTW_LIB and
    the return value on the next line; a missing file crashes the process (ISCE2's C wrapper fopens it without a check),
    and a return value of 0 STOPs with exit status 0 (gfortran's STOP)."""
    if module in _FFT_DONE:
        return
    _FFT_DONE.add(module)
    if module == 'icu' and env('LINOG_MOCK_ONEWISDOM') == pair:
        return
    w = '' if env('LINOG_MOCK_NOWISDOM') == pair else os.environ.get('WISDOM_FILE', '')
    sys.stdout.write(' wisdomFile, length = %s%12d\n' % (w, len(w)))
    sys.stdout.flush()
    if not w:
        return
    if not os.path.exists(w):
        os.kill(os.getpid(), signal.SIGSEGV)
    ret = 0
    if env('LINOG_MOCK_WISDOMSTOP') != pair:
        import ctypes
        L = ctypes.CDLL(os.environ['MOCK_FFTW_LIB'])
        L.fftwf_import_wisdom_from_filename.argtypes = [ctypes.c_char_p]
        L.fftwf_import_wisdom_from_filename.restype = ctypes.c_int
        ret = L.fftwf_import_wisdom_from_filename(w.encode())
    sys.stdout.write('%12d\n' % ret)
    sys.stdout.flush()
    if ret and env('LINOG_MOCK_WISDOMTOUCH') == pair:
        with open(w, 'a') as fh:
            fh.write('\n')
    if ret == 0:
        sys.stderr.write('STOP cannot import fftw wisdom file\n')
        sys.stderr.flush()
        os._exit(0)


def env_line(step):
    """The step's job as it sees WISDOM_FILE (v0.9: only refine's and igram's jobs get it)."""
    print('MOCK %s: WISDOM_FILE %s' % (step, os.environ.get('WISDOM_FILE', 'unset')))


def ground(width, seed=11):
    rng = np.random.RandomState(seed)
    return [np.abs(rng.normal(size=(b1 - b0, width))) + 0.2 for b0, b1 in BANDS]


def write_slc(path, width, lines, date, shift_cols=0, noise=0.1):
    """A sparse complex64 file, lines x width; the bands filled when the frame is full height."""
    with open(path, 'wb') as fh:
        fh.truncate(lines * width * 8)
    if lines < LINES_FULL:
        return
    rng = np.random.RandomState(int(date) % (2 ** 31))
    with open(path, 'r+b') as fh:
        for (b0, b1), a in zip(BANDS, ground(width)):
            amp = a * (1 + noise * rng.normal(size=a.shape))
            if shift_cols:
                amp = np.roll(amp, shift_cols, axis=1)
            z = (amp * np.exp(1j * rng.uniform(-np.pi, np.pi, size=a.shape))).astype(np.complex64)
            fh.seek(b0 * width * 8)
            fh.write(z.tobytes())


# ---- v0.13 (the ascending record 17.9): one ground for the full-height mixed and FBD-only frames (LINOG_MOCK_V13=1) ----
# Every date's raw SLC holds one ground F = A x S in the rows below (S a complex field band-limited to 0.4375 cycles a
# sample in range and AZ_HALF13 a line in azimuth, sqrt(GAMMA13) of it common to every date and the rest the date's own;
# A the brightness the relief gives by ISCE's simamplitude shading, 100 + 3 x the height step in range), plus a small
# noise of its own; the coregistered products (the mock resampleSlc) hold the date's F band-limited to the reference's
# band (0.21875 on an FBS reference: 14 MHz of 32 after bandlimit; 0.4375 on an FBD one), shifted by the date's residual
# misregistration in the reference's pixels, by its spectrum. The mock topo writes simamp.rdr from the same heights.
BANDS13 = ((0, 512), (3071, 3584), (7167, 7680), (10239, 10752), (14335, 14848))   # 5 rows of windows: 9 cells of G10 v3
RAW13 = BANDS13 + ((9000, 9256),)   # the raw records' rows: the bands, and G4's and bandlimit's occupancy rows from 9000
MARGIN13 = 64                       # rows and columns made beyond a band, so a sub-pixel shift has no edge
FBD_RG13 = 0.80                     # px (reference units): the coarse misregistration common to the FBD dates (17.2's form A)
RELIEF_M13, RELIEF_SMOOTH13 = 60.0, 6.0   # the relief's std (m) and its smoothing (samples)
AZ_HALF13 = 0.40                    # cycles a line: every field's azimuth band, about 0.8 of the PRF as ALOS's SLCs hold (17.4:
#                                     the intensity's band about 1.6 times the PRF); a field white in azimuth has no spectral
#                                     centroid there, and G10 v3's estimator demodulates by it before it oversamples
GAMMA13 = 0.60                      # each date's speckle: sqrt(GAMMA13) of the ground's common field and sqrt(1 - GAMMA13) of
#                                     its own (17.9: "the date's own band-limited speckle"), so a pair keeps a coherence of
#                                     about 0.6, inside the 0.25 to 0.6 at which the desk tested the estimator (17.5; the part 4
#                                     review's P4-03); the brightness A stays common, as the relief that makes it


def v13():
    return env('LINOG_MOCK_V13') == '1'


def _gauss(shape, seed):
    return np.random.RandomState(seed % (2 ** 31)).normal(size=shape)


def _lowpass(z, half):
    """z band-limited along range (axis 1) to |f| < half cycles a sample (an ideal filter)."""
    Z = np.fft.fft(z, axis=1)
    Z[:, np.abs(np.fft.fftfreq(z.shape[1])) >= half] = 0
    return np.fft.ifft(Z, axis=1)


def _cfield(n, w, seed, half):
    """A complex Gaussian field, unit power, band-limited along range to half and along azimuth to AZ_HALF13."""
    z = _lowpass(_gauss((n, w), seed) + 1j * _gauss((n, w), seed + 1), half)
    Z = np.fft.fft(z, axis=0)
    Z[np.abs(np.fft.fftfreq(n)) >= AZ_HALF13, :] = 0
    z = np.fft.ifft(Z, axis=0)
    return z / np.sqrt(np.mean(np.abs(z) ** 2))


def relief13(b0, b1, width):
    """The heights (m) over rows b0 - MARGIN13 to b1 + MARGIN13 and columns -MARGIN13 to width + MARGIN13: a smooth random
    field, its std RELIEF_M13 (WATER: flat outside the near range third of the first two azimuth thirds, see topo.py)."""
    n, w = b1 - b0 + 2 * MARGIN13, width + 2 * MARGIN13
    f = _gauss((n, w), 7001 + b0)
    ky, kx = np.fft.fftfreq(n)[:, None], np.fft.fftfreq(w)[None, :]
    h = np.real(np.fft.ifft2(np.fft.fft2(f) * np.exp(-2 * (np.pi * RELIEF_SMOOTH13) ** 2 * (kx ** 2 + ky ** 2))))
    return 100.0 + h * (RELIEF_M13 / h.std())


def shade13(h):
    """ISCE's Simamplitude (simamplitude.f90): shade(j) = (h(j + 1) - h(j)) x 3 + 100 along range; the last column repeats."""
    s = (h[:, 1:] - h[:, :-1]) * 3.0 + 100.0
    return np.concatenate([s, s[:, -1:]], axis=1)


def ground13(b0, b1, width, half=0.4375, date=None):
    """F = A x S over the band with its margins (see relief13): A = max(0.05, shade / 100); S the band's common field, or with
    a date sqrt(GAMMA13) of it and sqrt(1 - GAMMA13) of the date's own (the same for its raw samples and its products)."""
    h = relief13(b0, b1, width)
    a = np.maximum(0.05, shade13(h) / 100.0)
    s = _cfield(h.shape[0], h.shape[1], 9001 + b0, half)
    if date is not None:
        s = np.sqrt(GAMMA13) * s + np.sqrt(1.0 - GAMMA13) * _cfield(h.shape[0], h.shape[1], int(date) % 99991 * 13 + b0, half)
    return a * s


def crop13(z, b0, b1, width):
    return z[MARGIN13:MARGIN13 + (b1 - b0), MARGIN13:MARGIN13 + width]


def raw13(date, pol, b0, b1, width):
    """A date's raw samples over the band (complex64, rows b0 to b1): the ground F with the date's own speckle share (HH)
    plus 5 % noise of its own; HV half the amplitude of a field of its own (G4: the SLC nearer IMG-HH)."""
    seed = int(date) % 99991 * 7 + b0
    if pol == 'HV':
        n, w = b1 - b0 + 2 * MARGIN13, width + 2 * MARGIN13
        z = 0.5 * _cfield(n, w, seed + 5, 0.4375)
    else:
        z = ground13(b0, b1, width, date=date) + 0.05 * _cfield(b1 - b0 + 2 * MARGIN13, width + 2 * MARGIN13, seed + 3, 0.4375)
    return crop13(z, b0, b1, width).astype(np.complex64)


def product13(b0, b1, width, date, dy, dx, half):
    """A coregistered product over the band: F with the date's own speckle share, band-limited to half, shifted by (dy, dx)
    (lines, samples of the reference), plus 2 % noise of the date's own: the date's feature at the reference's (r, c) lies at
    (r + dy, c + dx)."""
    z = _lowpass(ground13(b0, b1, width, date=date), half)
    n, w = z.shape
    ky, kx = np.fft.fftfreq(n)[:, None], np.fft.fftfreq(w)[None, :]
    z = np.fft.ifft2(np.fft.fft2(z) * np.exp(-2j * np.pi * (ky * dy + kx * dx)))
    z = z + 0.02 * _cfield(n, w, int(date) % 99991 * 11 + b0, half)
    return crop13(z, b0, b1, width).astype(np.complex64)


def decor13(b0, b1, width, date, half):
    """A product band with nothing of the ground (LINOG_MOCK_DECOR): a field of the date's own at the ground's mean brightness,
    band-limited to half."""
    n, w = b1 - b0 + 2 * MARGIN13, width + 2 * MARGIN13
    a = float(np.mean(np.maximum(0.05, shade13(relief13(b0, b1, width)) / 100.0)))
    z = a * _cfield(n, w, int(date) % 99991 * 17 + b0, half)
    return crop13(z, b0, b1, width).astype(np.complex64)


def truth13(date, fbd):
    """The mock's coarse misregistration of a date (az lines, rg px, reference units, before any datum): truth(), and
    FBD_RG13 more in range on an FBD date."""
    az, rg = truth(date)
    return az, rg + (FBD_RG13 if fbd else 0.0)


def shelf_frame(shelf_dir):
    db = shelve.open(os.path.join(shelf_dir, 'data'), 'r')
    try:
        return db['frame']
    finally:
        db.close()


def listed(k, date):
    """v0.13: date is among the comma list of LINOG_MOCK_<k>."""
    return date in [x for x in env(k).split(',') if x]


def gateoff(date):
    """v0.13 (M79, M80): LINOG_MOCK_GATEOFF's metres for date, or None."""
    for x in env('LINOG_MOCK_GATEOFF').split(','):
        d, _, m = x.partition(':')
        if d == date and m:
            return float(m)
    return None


def shelf_r0(shelf_dir):
    """v0.13: (the shelve's startingRange, the leader's r0 the mock unpacker kept beside it)."""
    f = shelf_frame(shelf_dir)
    r0 = float(f.getStartingRange())
    return r0, float(getattr(f, '_mock_r0_leader', r0))


def slr_prf(shelf_dir):
    """(range pixel, the frame's PRF) of a shelve, as refineSecondaryTiming.py reads them (instrument and frame)."""
    f = shelf_frame(shelf_dir)
    prf = getattr(f, 'PRF', None)
    if prf is None:
        prf = f.instrument.PRF
    return float(f.instrument.getRangePixelSize()), float(prf)


def sparse(path, nbytes):
    with open(path, 'wb') as fh:
        fh.truncate(nbytes)


def write_xml(path, width, length, dtype='FLOAT', bands=1, file_name=None, scheme=None):
    """An .xml and .vrt beside path, in ISCE's layout (width, length, number_bands, data_type, file_name; v0.7: the
    byte order and scheme when given, as ISCE writes them for a .amp)."""
    p = '    <property name="%s">\n        <value>%s</value>\n    </property>\n'
    with open(path + '.xml', 'w') as fh:
        fh.write('<imageFile>\n' + (p % ('byte_order', 'l') if scheme else '') + p % ('data_type', dtype) +
                 p % ('file_name', file_name or os.path.abspath(path)) + p % ('length', length) + p % ('number_bands', bands) +
                 (p % ('scheme', scheme) if scheme else '') + p % ('width', width) + '</imageFile>\n')
    gdt = {'FLOAT': 'Float32', 'CFLOAT': 'CFloat32', 'DOUBLE': 'Float64', 'BYTE': 'Byte'}[dtype]
    with open(path + '.vrt', 'w') as fh:
        fh.write('<VRTDataset rasterXSize="%d" rasterYSize="%d">\n  <VRTRasterBand dataType="%s" band="1" '
                 'subClass="VRTRawRasterBand">\n    <SourceFilename relativeToVRT="1">%s</SourceFilename>\n'
                 '  </VRTRasterBand>\n</VRTDataset>\n' % (width, length, gdt, os.path.basename(path)))


def frame_dims(shelf_dir):
    db = shelve.open(os.path.join(shelf_dir, 'data'), 'r')
    try:
        f = db['frame']
        return int(f.numberOfSamples), int(f.numberOfLines)
    finally:
        db.close()


def date_of(path):
    """The 8-digit date in the last component of a folder path (SLC/<date>, coregSLC/Coarse/<date>)."""
    b = os.path.basename(os.path.normpath(path))
    return b if b.isdigit() and len(b) == 8 else None


def truth(date):
    """The mock stack's per-date misregistration (az, rg) in pixels, before any datum."""
    i = int(date) % 97
    return 0.03 * (i % 11) - 0.12, 0.02 * (i % 7) - 0.05


def copy_shelve(src_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    for n in os.listdir(src_dir):
        if n.startswith('data'):
            with open(os.path.join(src_dir, n), 'rb') as a, open(os.path.join(dst_dir, n), 'wb') as b:
                b.write(a.read())


def pairs_of(path):
    b = os.path.basename(os.path.normpath(path))
    return b if len(b) == 17 and b[8] == '_' else None


def d1_plant(tc, d12, keep):
    """v0.12, drop1's cases: LINOG_MOCK_D1BAD (the module's docstring) on the temporal coherence tc (lines x columns) of an
    inversion of the pairs d12 [(date1, date2)] with dropIfgram keep; returns tc."""
    import math
    names = ['%s_%s' % (a, b) for a, b in d12]
    for j, x in enumerate(y for y in env('LINOG_MOCK_D1BAD').split(',') if y):
        pr, n = x.split(':')
        if pr in names and bool(keep[names.index(pr)]):
            r0 = 20 + 30 * j   # the land lines (the scene's sea is the last sixth of the lines), off the strip (columns 0 to 5)
            tc[r0:r0 + 10, 10:10 + min(60, max(1, int(math.ceil(int(n) / 10.0))))] = 0.55
    return tc


def scene(gl, gw):
    """The Phase 5e and 6 cases' ground on the gl x gw multilooked grid (v0.7): dict of boolean arrays.
    sea    the south-east corner: the last gl // 6 lines, columns 0 to gw // 2 (column 0 is east)
    decor  the sea's western half (columns gw // 4 to gw // 2): decorrelated, low temporal coherence
    pier   3 x 3 px in the sea's eastern half, bright as land (G22 keeps it: 6 dB or more above its water)
    strip  columns 0 to 5 over the land lines: 40 dB below the land (G23's near-range strip)"""
    sea = np.zeros((gl, gw), bool)
    sea[gl - gl // 6:, :gw // 2] = True
    decor = sea.copy()
    decor[:, :gw // 4] = False
    pier = np.zeros((gl, gw), bool)
    r0 = gl - gl // 12
    pier[r0 - 1:r0 + 2, 9:12] = True
    strip = np.zeros((gl, gw), bool)
    strip[:gl - gl // 6, :6] = True
    return dict(sea=sea, decor=decor, pier=pier, strip=strip)


def scene_amp(gl, gw, pair):
    """A pair's .amp (2 bands, BIP, float32) over scene(): land 1 with 20 % noise per band (RandomState by the pair's
    dates), the sea 0.05 (26 dB below), the pier as land, the strip 0.01 of the land (40 dB below)."""
    sc = scene(gl, gw)
    rng = np.random.RandomState(int(pair[:8]) % 9973 + int(pair[-8:]) % 7919)
    a = 1.0 + 0.2 * rng.normal(size=(gl, gw, 2))
    a = np.abs(a) + 0.05
    a[sc['sea'] & ~sc['pier']] = 0.05
    a[sc['strip']] *= 0.01
    return a.astype('<f4')
