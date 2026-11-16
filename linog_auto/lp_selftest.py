#!/usr/bin/env python3
"""lp_selftest.py -- self-test of linog_auto on mock data, before it touches a real archive.

    linog_auto.sh --selftest DIR        (or: python3 lp_selftest.py DIR)

Builds, under DIR only: a mock archive of small zips in the JAXA layout as RD2 measured it on felix (members at
the top of the zip: VOL, LED, IMG-HH, TRL, the browse jpg and summary.txt; frame 3310 keeps them under a folder,
the other form), with IMG-HH written full size for a few lines, 720 + lines x (412 + 8 x width) B, its CEOS file
descriptor and the prefixes of its first, middle and last records written from ISCE's record definitions, and LED
with the scene record's range gate delay and sampling rate (v0.5; archive_rw plants the one-gate cases RD4 found on
8 of P084 F3320's dates, archive_rwbad two cases rwin must refuse, archive_off a leader 50 m off the grid); a mock DEM
(120-123 E, 14-18 N); a path table whose root is DIR/root; and a mock ISCE environment (selftest_kit/): a mock
conda.sh activated as felix's is, a mock isce, the kit's real unpacker, post-unpack checks and network table, and
the real stackStripMap.py and Stack.py of the isce2 package felix runs, with a mock Baseline that returns felix's
measured P084 F3320 baselines. Phase 2 needs numpy and matplotlib for stackStripMap.py: the mock env runs on this
Python when it has them, otherwise on the pinned env's python3 (only read; the mock packages come first on its path).
Then runs linog_auto.sh through the cases, clean and planted, and checks each exit code and record. LINOG_ROOT,
LINOG_ARCHIVE and LINOG_DEM are removed from the environment it passes on, LINOG_ENV_CFG points at the mock
environment and LINOG_STACK_CFG at a copy of linog_stack.cfg whose ENV_PREFIX is the mock env, so no case can reach
the real tree or the real env. Phase 2 cases read their own archive: frame 3320's 24 granules, felix's dates.
v0.7: the Phase 5e and 6 cases (lp_selftest6.py) run the kit's own linog_watermask.py, linog_phase6.sh, linog_los2hv.py,
linog_embed_stats.py and linog_gen_interactive_kmz.py (byte copies in selftest_kit/kit3, at linog_phase6.cfg's pins)
on the Phase 5 cases' frame, with the mock MintPy's Phase 6 commands and a mock GDAL, and the pipeline's verifier copy.
v0.8: D9 no by default (lp_selftest56.py T104 to T104c); d9ab, D9's A/B after sbas, with the mock MintPy on its copy, and
RUN_MANIFEST.json's new fields (lp_selftest6.py T125f, T125g, T146 to T153b).
v0.9: the pinned FFTW wisdom of refine and igram (lp_selftest34.py T154 to T166 and T168 to T171, T93 and T64 with the
new gates; lp_selftest6.py T167). The mock env carries a real libfftw3f, copied from the pinned env's (only read, as on felix) or
else from this host's system library, and a wisdom file made with it here for a small problem set (sizes 4 to 64, two
offsets: 20 problems); its stand-ins of ISCE2's ampcor, crossmul and icu modules are text files that a mock ldd in the
env's bin says load that library, and the mock steps import the wisdom through it as cfft1d_jpl does (linog_mock3).
v0.10: admit's rules R1 to R3, d9ab's R5, the phase dfit (R4), the path runner and the path table's three new entries
(lp_selftest10.py, T200 to T224; and the cases of lp_selftest56.py and lp_selftest6.py whose expectations the rules change).
The mock topo's hgt.rdr carries land (a gentle slope) and the scene's sea flat at 44 m, so R1 reads 4,469 px of water and
50,145 px of land there. The Phase 5 and 6 runs read cfg/mintpy_mock.cfg: linog_mintpy.cfg with R1's land floor scaled to
the mock's 83 x 658 grid (5,000 px of its 54,614, as felix's 50,000 is of F3320's 511,924), so no case sits 145 px from the
floor; T202 runs felix's floor, then the floor at the mock's land count and one pixel above it.
v0.11: deliver's G6a.10 (the KMZs' entry times at 1980-01-01 00:00:00), the phase rerun (P6d), lp_compare.py and lp_kmz.py
(lp_selftest11.py, T300 to T315; T126, T153, T167, T210, T211 and T212 count 29 phases or read v0.11's deliver). The mock MintPy's bin adds
ifgram_inversion.py (lp_compare.py's split) and its save_kmz.py the plant LINOG_MOCK_KMZ_EXTRA (an extra field G6a.10 refuses).
v0.12: the phase drop1 (the drop-one peer test of the flagged pairs), admit's handoff to it and the driver's one restart per
asking phase (lp_selftest12.py, T320 to T339; lp_selftest10.py's stub driver, T212 to T215 with T212b and T213c; T103 to
T103d, T126, T153, T167, T211, T308 read v0.12's admit, 30 phases and v0.12's deliver; v0.13: 31 phases, bandlimit's). The mock's LINOG_MOCK_D1BAD
(linog_mock3.d1_plant) lowers the temporal coherence on a block of land while a pair is kept, in the mock invert_network and
ifgram_inversion.py alike; LINOG_MOCK_COHPAIR sets a pair's coherence, LINOG_MOCK_D1FAIL and D1SLEEP fail or hold an inversion.
v0.12 r2 (record 127): the minimum peer count (DROP1_MIN_PEERS: 1 in the mock's cfg, so a flagged pair's 5 peers suffice; T331b
and T338 set others; v0.13 r2: the split rule's peers, DROP1_PEERS_SIDE a side, set by lp_selftest12's cases and suite 13r2a) and the files beside each test's stack (T320, T330b, T339, T339b; the mock's LINOG_MOCK_WATERMASK gives the
geometry a waterMask, and its modify_network writes waterMask.h5 from it, as MintPy 1.6.2 does); T149k (lp_selftest6.py):
SIGKILL to d9ab alone while MintPy runs on B, which must end with it (record 77.12).
Exit 0 when every case passes, 1 otherwise.
"""
import datetime
import fcntl
import glob
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY = os.path.join(HERE, 'linog_auto.sh')
KITSRC = os.path.join(HERE, 'selftest_kit')
D0, O0 = datetime.date(2008, 1, 13), 10488
# the 24 orbits of P84 F3320 as read on felix by RD1 v2, 26 Sept 2026; x = native 9376 width there
ORBITS = [3778, 4449, 7133, 9146, 10488, 11159, 11830, 12501, 13172, 13843, 15185, 16527, 17869, 19211,
          19882, 20553, 21895, 22566, 23237, 23908, 25250, 25921, 26592, 27263]
W9376 = {11830, 16527, 19211, 19882, 21895, 23908, 25250, 25921}
LINES = 8           # mock lines per granule (felix: 18432); the IMG-HH size law holds for any count
P3_ORBITS = [13843, 15185, 16527, 17869]   # 20080830 20081130 20090302 20090602: 6 pairs under -t 730 -b 1500
P3_WIDTH, P3_LINES = 1000, 18432   # 1000: recon's CEOS decode accepts 1000 to 20000 samples
MOCK_LAND_MIN_PX = 5000   # v0.10: R1's floor scaled to the mock grid (felix: 50,000 px of F3320's 511,924; here of 54,614)
MOCK_DROP1_FREE_GIB = '0.5'   # v0.12: drop1's margin beyond its copies (felix: 10 GiB for 0.69 GB stacks; the mock's are 3 MB)
MOCK_DROP1_MIN_PEERS = '1'    # v0.12 r2: the mock frame's 6 pairs give a flagged pair 5 peers (felix: 10 of 100 or more); T338 sets 6 and 5
# (v0.13 r2: drop1 tests a pair against DROP1_PEERS_SIDE a side; lp_selftest12's cases set 2 a side on the 6-pair frame)
PHASE_LINE = ('auto_recon ', 'auto_stage ', 'auto_extract ', 'auto_unpack ', 'auto_rwin ', 'auto_bandlimit ', 'auto_verify ', 'auto_stack1 ',
              'auto_reference ', 'auto_stack2 ')


# v0.13 (ascending record 4.11, 15.4): the mixed mock frame 3350, 12 dates of which 4 FBD, with samples in every record (the
# readings of bandlimit, G4 and G1c.8 need them), at a size Phase 1 runs in seconds: 512 lines (G1bl.7's and G4's windows are
# the middle 256 and 200 lines on a frame without 9,256), 1000 samples on both modes (recon's CEOS decode takes 1000 to 20000)
FBD_3350 = (2, 5, 7, 8)
LINES_MX, W_MX = 512, 1000
DATA_OK = [None]   # v0.13: True when the frames with samples were made (numpy in this Python or the mock env's)


def date_of(orb):
    return (D0 + datetime.timedelta(days=46 * ((orb - O0) // 671))).strftime('%Y%m%d')


CEOS_DB = os.path.join(KITSRC, 'mock_isce', 'isce', 'components', 'isceobj', 'Sensor', 'db', 'alos_slc')
C2 = 299792458.0 / 2.0
GATE = C2 * 1e-6                          # one microsecond of range delay: 32 FBS samples
R0DEF = 845217.5596 - 5 * 149.89632       # the kit's gate grid, -5 steps: where RD2 found path 84's r0


def ceos_rec(xml, values, total):
    """One CEOS record written field by field from ISCE's own definition (db/alos_slc, copied into the mock kit), so
    ISCE's CEOS parser reads it back: values not given are blank (ASCII) or zero (binary). As RD4's ceosgen.py."""
    import xml.etree.ElementTree as ET
    out = bytearray()
    for z in ET.parse(os.path.join(CEOS_DB, xml)).getroot():
        name, t, num = z.attrib['name'], int(z.attrib['type']), int(z.attrib['num'])
        v = values.get(name)
        if t == 0:
            out += b'\0' * num
        elif t == 1:
            out += ('' if v is None else str(v)).ljust(num)[:num].encode('ascii')
        elif t == 2:
            out += ('' if v is None else '%d' % v).rjust(num)[:num].encode('ascii')
        elif t == 5:
            out += ('' if v is None else '%.9f' % v).rjust(num)[:num].encode('ascii')
        elif t in (3, 4, 6, 9):
            out += struct.pack({3: '>B', 4: '>I', 6: '>H', 9: '>Q'}[t], v or 0)
        elif t == 8:
            out += struct.pack('>f', v or 0.0)
        else:
            raise ValueError('%s: type %d' % (xml, t))
    if len(out) > total:
        raise ValueError('%s: %d bytes defined, record %d' % (xml, len(out), total))
    return bytes(out + b'\0' * (total - len(out)))


def img_record(rec, i, width, left, right, r1):
    return ceos_rec('image_record.xml', {'Record Length': rec, 'SAR image data line number': i + 1,
                                         'Actual count of left-fill pixels': left, 'Actual count of data pixels': width - left - right,
                                         'Actual count of right-fill pixels': right, 'PRF': 2159827,
                                         'Slant range to 1st data sample': int(round(r1)), 'Data record window position': 0}, 412)


# v0.13 (ascending record 9.5, 13.7): the image records carry their centre and corner pixels' positions and their
# acquisition times at the real scale whatever the mock's line count, so G0.16 and G0.14 read them as on felix: (b), the
# first record's centre, 4.295 s (9,216 lines at 2,145.9227 Hz) and about 29.25 km behind (c), the middle record's; the
# corners 35 km to each side of the centre line, 29.25 km before (b)'s and after (c)'s along track (the last record's
# position). Path 84's frames F3290 to F3330 sit at felix's own corners (13.3 D's footprints, the union of their four
# corners); every other mock frame by the frame law (13.3 H) and the frame step: 0.0099 deg west a frame number on path 84,
# 0.0101 deg west a frame number ascending, 0.537 deg west a path. IMG members are written stored (compress type 0), the
# zeros between the three records left as holes in the zip file (SparseFile).
KM_S = 6.8095                       # along-track ground speed, km/s (9.4: 6,809 to 6,814 m/s)
PRF_MOCK = 2145.9227                # Hz, the shelves' lowest PRF (2.2); (b) to (c) is 9216 lines of it
MID_LINES = 9216                    # the middle record's index on a real 18,432-line granule
HALF_W = 35.0                       # km, the centre pixel to the near and the far range
HEADING = {'A': 349.0, 'D': 191.0}  # deg, the cells' headings (9.4: 348.88 to 349.08, 190.93 to 191.12)
FELIX_FP = {('084', '3290'): (16.000571, 16.644439, 121.319138, 122.092713), ('084', '3300'): (15.507408, 16.153224, 121.220371, 121.995216),
            ('084', '3310'): (15.005393, 15.648691, 121.119897, 121.892585), ('084', '3320'): (14.502029, 15.145254, 121.019932, 121.795535),
            ('084', '3330'): (14.015342, 14.659689, 120.923601, 121.696612)}   # r8_desk_out.json D 'derived', S N W E
LAW = {'A': (0.92026, 0.0496858), 'D': (179.79800, -0.0496893)}            # linog_paths.cfg framing_law_A, _D
EA, E2 = 6378137.0, (1 / 298.257223563) * (2 - 1 / 298.257223563)


def path_of(orbit):
    p = (46 * (orbit % 671) + 85) % 671
    return p or 671


def ecef(lat, lon):
    import math
    p, l = math.radians(lat), math.radians(lon)
    n = EA / math.sqrt(1 - E2 * math.sin(p) ** 2)
    return n * math.cos(p) * math.cos(l), n * math.cos(p) * math.sin(l), n * (1 - E2) * math.sin(p)


def en(lat, lon, o):
    """lp_recon.en: east and north of (lat, lon) from o, m."""
    import math
    x, y, z = ecef(lat, lon)
    x0, y0, z0 = ecef(*o)
    dx, dy, dz = x - x0, y - y0, z - z0
    p, l = math.radians(o[0]), math.radians(o[1])
    return (-math.sin(l) * dx + math.cos(l) * dy, -math.sin(p) * math.cos(l) * dx - math.sin(p) * math.sin(l) * dy + math.cos(p) * dz)


def en_inv(o, e, n):
    """The (lat, lon) whose en() from o is (e, n) m: Newton on the local radii, to well under a millimetre."""
    import math
    lat, lon = o
    for _ in range(6):
        e1, n1 = en(lat, lon, o)
        s = math.sin(math.radians(lat))
        rm = EA * (1 - E2) / (1 - E2 * s * s) ** 1.5
        rn = EA / math.sqrt(1 - E2 * s * s) * math.cos(math.radians(lat))
        lat += math.degrees((n - n1) / rm)
        lon += math.degrees((e - e1) / rn)
    return lat, lon


def mock_centre(path, frame, sfx):
    """(c)'s nominal position for a mock frame: felix's footprint centre on path 84's five, else the frame law and step."""
    if (path, frame) in FELIX_FP:
        S_, N_, W_, E_ = FELIX_FP[(path, frame)]
        return (S_ + N_) / 2, (W_ + E_) / 2
    F, P = int(frame), int(path)
    a, b = LAW[sfx]
    if sfx == 'D':
        return a + b * F, 121.408 - 0.0099 * (F - 3320) - 0.537 * (P - 84)
    return a + b * F, 121.131 - 0.0101 * (F - 300) - 0.537 * (P - 448)


def mock_geo(path, frame, sfx, along_km=0.0, across_km=0.0, lon_deg=0.0, prf=PRF_MOCK, c_lines=0, centre=None):
    """(b), (c), the last record's centre and the four corners ((first, near), (first, far), (last, near), (last, far))
    of a mock granule, each (lat, lon), and the (b) to (c) span in s. along_km and across_km move the whole granule
    (+ along the flight, + right of it); lon_deg adds to (b) and (c)'s longitudes only; c_lines moves (c) alone that many
    lines along track (its line number and time unchanged)."""
    import math
    o = centre or mock_centre(path, frame, sfx)
    h = math.radians(HEADING[sfx])
    ua, ur = (math.sin(h), math.cos(h)), (math.cos(h), -math.sin(h))
    span = MID_LINES / prf
    half = KM_S * span
    def at(al, ac):
        return en_inv(o, 1e3 * (al * ua[0] + ac * ur[0]), 1e3 * (al * ua[1] + ac * ur[1]))
    a0 = along_km
    c = at(a0 + c_lines * KM_S / prf, across_km)
    b = at(a0 - half, across_km)
    last = at(a0 + half, across_km)
    corn = lambda al, ac: [at(al - half, ac - HALF_W), at(al - half, ac + HALF_W), at(al + half, ac - HALF_W), at(al + half, ac + HALF_W)]
    corners = corn(a0, across_km)
    if (path, frame) in FELIX_FP and centre is None:
        # felix's footprint: the unmoved granule's four corners mapped onto it side by side, the same map for a moved one
        S_, N_, W_, E_ = FELIX_FP[(path, frame)]
        c0 = corn(0.0, 0.0)
        la, lo = [x[0] for x in c0], [x[1] for x in c0]
        s0, s1, w0, w1 = min(la), max(la), min(lo), max(lo)
        corners = [(S_ + (x[0] - s0) * (N_ - S_) / (s1 - s0), W_ + (x[1] - w0) * (E_ - W_) / (w1 - w0)) for x in corners]
    if lon_deg:
        b, c = (b[0], b[1] + lon_deg), (c[0], c[1] + lon_deg)
    return dict(b=b, c=c, last=last, corners=corners, span=span)


class SparseFile(object):
    """A file for zipfile to write into: a block of zeros is skipped by a seek (a hole), any other block written."""
    def __init__(self, path):
        self.f = open(path, 'wb')

    def write(self, b):
        if b and not b.strip(b'\0'):
            self.f.seek(len(b), 1)
            return len(b)
        return self.f.write(b)

    def __getattr__(self, k):
        return getattr(self.f, k)

    def close(self):
        end = self.f.seek(0, 2)
        self.f.truncate(end)
        self.f.close()


def band_noise(orb, pol, nl, width, amp, half_band=0.4375):
    """v0.13 (ascending record 4.11): complex Gaussian noise band-limited to |f| < half_band cycles a sample (28 of 32 MHz on
    FBS, 14 of 16 MHz on FBD: both 0.4375), scaled to a mean amplitude of about amp, as IMG records' big-endian float32
    I and Q pairs (nl x 8 x width bytes). numpy: build() runs it in this Python when it has numpy, else in the mock env's."""
    import numpy as np
    rng = np.random.RandomState((orb * 7 + {'HH': 1, 'HV': 2}[pol]) % (2 ** 31))
    z = rng.normal(size=(nl, width)) + 1j * rng.normal(size=(nl, width))
    Z = np.fft.fft(z, axis=1)
    Z[:, np.abs(np.fft.fftfreq(width)) >= half_band] = 0
    z = np.fft.ifft(Z, axis=1)
    z *= amp / np.abs(z).mean()
    iq = np.empty((nl, width, 2), dtype='>f4')
    iq[..., 0], iq[..., 1] = z.real, z.imag
    return iq.tobytes()   # line by line: width x (I, Q), 8 x width bytes a line


def mkzip(folder, orb, frame, sfx='D', product='H1.1', offnadir=34.3, width=None, fbd=False,
          date=None, corrupt=False, nested=False, img_short=0, lines=None, r0_off_m=0.0, r1_off_m=0.0, left=0,
          last_r1_off_m=0.0, fdr_blank_rl=False, g016=None, stored=True, data=False, amp=1000.0, hv_short=0, fs_mhz=None,
          hv_member=True, rows13=False):
    """A granule zip. IMG-HH: the CEOS file descriptor, then lines records of 412 + 8 x width B, of which the first,
    middle and last carry their prefix (fill counts, slant range to the first data sample; v0.13 their line numbers,
    acquisition times and the centre and corner pixels' positions at the real scale, mock_geo); the rest are zeros. LED:
    the file descriptor and the scene header record (range gate delay, sampling rate 32 MHz). By default the leader's
    r0 is on the kit's grid at -5 steps and column 0 by the records is the leader's r0 (whole metres). Planted:
    r0_off_m moves both, r1_off_m moves the records only (-1 gate: the F26 case), left puts that many fill samples
    before the first data sample, last_r1_off_m moves the last record's first data sample only, fdr_blank_rl leaves the
    file descriptor's record length blank. v0.13 (G0.16 and G0.14's cases): g016 a dict of mock_geo's along_km,
    across_km, lon_deg, prf, c_lines, centre, and zero_c (the middle record's position fields 0), mid_line_off (its line
    number off), equal_times ((c)'s time = (b)'s), last_line_off, zero_corner (the first record's first-pixel latitude 0),
    corner_far_deg (that corner moved), corners (S N W E: the corners spread to that box); stored=False deflates IMG-*.
    v0.13 (4.11): the leader's scene record carries the wavelength, the pulse length and the chirp by mode (FBS 28 MHz,
    FBD 14 MHz over 27 us) beside the sampling rate; data=True fills every record of IMG-HH (and an FBD granule's IMG-HV,
    at half the amplitude) with band-limited noise (band_noise, numpy); hv_short cuts that many bytes off IMG-HV; fs_mhz puts
    that sampling rate in the leader whatever the mode; hv_member=False lists IMG-HV in summary.txt without the member.
    v0.13 (17.9, part 4): rows13=True writes, on a full-height frame, the samples of linog_mock3.RAW13's rows only (the one
    ground, linog_mock3.raw13: IMG-HH the ground and a noise of the date's own, IMG-HV half the amplitude), zeros elsewhere
    (holes in the zip), so the mock sensor copies them into the SLC and every Phase 1 reader finds them."""
    os.makedirs(folder, exist_ok=True)
    sid = 'ALPSRP%05d%s' % (orb, frame)
    p = os.path.join(folder, '%s-%s__%s.zip' % (sid, product, sfx))
    if corrupt:
        with open(p, 'wb') as fh:
            fh.write(b'not a zip file')
        return p
    width = width or (4640 if fbd else (9376 if orb in W9376 else 9344))
    nl = lines or LINES
    tail = '-%s__%s' % (product, sfx)
    files = ['VOL-' + sid + tail, 'LED-' + sid + tail, 'IMG-HH-' + sid + tail] + \
        (['IMG-HV-' + sid + tail] if fbd else []) + ['TRL-' + sid + tail]
    s = ['Scs_SceneID="%s"' % sid, 'Lbi_ObservationDate="%s"' % (date or date_of(orb)),
         'Img_SceneCenterDateTime="%s 02:13:21.000"' % (date or date_of(orb)),
         'Img_OffNadirAngle="%.1f"' % offnadir, 'Pdi_NoOfPixels="%d"' % width, 'Pdi_NoOfLines="%d"' % nl] + \
        ['Pdi_L15ProductFileName%02d="%s"' % (i + 1, f) for i, f in enumerate(files)]
    rec = 412 + 8 * width
    fs = fs_mhz or (16.0 if fbd else 32.0)
    r0 = R0DEF + r0_off_m
    r1 = r0 + left * C2 / (fs * 1e6) + r1_off_m
    G = dict(g016 or {})
    geo = mock_geo('%03d' % path_of(orb), frame, sfx, along_km=G.get('along_km', 0.0), across_km=G.get('across_km', 0.0),
                   lon_deg=G.get('lon_deg', 0.0), prf=G.get('prf', PRF_MOCK), c_lines=G.get('c_lines', 0), centre=G.get('centre'))
    if G.get('corners'):
        S_, N_, W_, E_ = G['corners']
        la, lo = [x[0] for x in geo['corners']], [x[1] for x in geo['corners']]
        s0, s1, w0, w1 = min(la), max(la), min(lo), max(lo)
        geo['corners'] = [(S_ + (x[0] - s0) * (N_ - S_) / (s1 - s0), W_ + (x[1] - w0) * (E_ - W_) / (w1 - w0)) for x in geo['corners']]
    if G.get('corner_far_deg'):
        geo['corners'][1] = (geo['corners'][1][0] + G['corner_far_deg'], geo['corners'][1][1])
    tc = datetime.datetime.strptime((date or date_of(orb)) + ' 02:13:21', '%Y%m%d %H:%M:%S')
    tb = tc if G.get('equal_times') else tc - datetime.timedelta(seconds=geo['span'])
    tl = tc + datetime.timedelta(seconds=geo['span'])
    u = lambda x: int(round(x * 1e6)) & 0xFFFFFFFF          # millionths of a degree, B4 (two's complement)

    def times(t):
        return {'Sensor acquisition year': t.year, 'Sensor acquisition day of year': t.timetuple().tm_yday,
                'Sensor acquisition milliseconds of day': int(round((t - t.replace(hour=0, minute=0, second=0, microsecond=0))
                                                                    .total_seconds() * 1000))}
    pos = {0: (geo['b'], geo['corners'][0], geo['corners'][1], tb), nl // 2: (geo['c'], None, None, tc),
           nl - 1: (geo['last'], geo['corners'][2], geo['corners'][3], tl)}
    fdr = ceos_rec('image_file.xml', {'Record Length': 720, 'Number of SAR DATA records': nl,
                                      'SAR DATA record length': None if fdr_blank_rl else rec,
                                      'Number of left border pixels per line': 0,
                                      'Number of pixels per line per SAR channel': width,
                                      'Number of right border pixels per line': 0,
                                      'Number of bytes of prefix data per record': 412}, 720)
    prefixes = {}
    for i in sorted(set((0, nl // 2, nl - 1))):
        a = 720 + i * rec
        assert a + 412 <= 720 + nl * rec - img_short, 'img_short cuts into the last record prefix'
        cen, first, last, t = pos[i]
        if i == nl // 2 and G.get('zero_c'):
            cen = (0.0, 0.0)
        if first is None:                                    # the middle record: corners from its centre, +-35 km
            first, last = cen, cen
        if i == 0 and G.get('zero_corner'):
            first = (0.0, first[1])
        line = i + 1 + (G.get('mid_line_off', 0) if i == nl // 2 else 0) + (G.get('last_line_off', 0) if i == nl - 1 and i else 0)
        v = {'Record Length': rec, 'SAR image data line number': line,
             'Actual count of left-fill pixels': left, 'Actual count of data pixels': width - left,
             'Actual count of right-fill pixels': 0, 'PRF': 2159827,
             'Slant range to 1st data sample': int(round(r1 + (last_r1_off_m if i == nl - 1 else 0.0))),
             'Data record window position': 0,
             'Latitude of first pixel': u(first[0]), 'Latitude of center pixel': u(cen[0]), 'Latitude of last pixel': u(last[0]),
             'Longitude of first pixel': u(first[1]), 'Longitude of center pixel': u(cen[1]), 'Longitude of last pixel': u(last[1])}
        v.update(times(t))
        prefixes[a] = ceos_rec('image_record.xml', v, 412)
    led = ceos_rec('leader_file.xml', {'Record Length': 720}, 720) + ceos_rec(
        'scene_record.xml', {'Record Length': 4096, 'Range sampling rate in MHz': fs, 'Range gate delay in microsec': r0 / C2 * 1e6,
                             'Radar wavelength': 0.2360571, 'Range pulse length in microsec': 27.0,
                             'Nominal range pulse (chirp) amplitude coefficient linear term': (14.0 if fbd else 28.0) * 1e6 / 27e-6}, 4096)
    pre = sid + tail + '/' if nested else ''
    total = 720 + nl * rec - img_short

    def rows13_marks(pol):
        """v0.13: the RAW13 bands' records (each record's prefix, zeros where it has none, then its samples)."""
        sys.path.insert(0, os.path.join(KITSRC, 'mock_isce'))
        import linog_mock3 as M3
        import numpy as np
        out = []
        d = date or date_of(orb)
        for b0, b1 in M3.RAW13:
            z = M3.raw13(d, pol, b0, b1, width)
            iq = np.empty((b1 - b0, width, 2), dtype='>f4')
            iq[..., 0], iq[..., 1] = z.real, z.imag
            buf = bytearray((b1 - b0) * rec)
            for k in range(b1 - b0):
                pr = prefixes.get(720 + (b0 + k) * rec)
                if pr:
                    buf[k * rec:k * rec + 412] = pr
                buf[k * rec + 412:(k + 1) * rec] = iq[k].tobytes()
            out.append((720 + b0 * rec, bytes(buf)))
        return out

    def img_chunks(block=1 << 20, pol='HH'):
        """The IMG member in blocks: the descriptor, the three prefixes, zeros elsewhere (v0.13: RAW13's samples)."""
        marks = sorted([(0, fdr)] + list(prefixes.items()) + (rows13_marks(pol) if rows13 else []))
        pos_ = 0
        while pos_ < total:
            n = min(block, total - pos_)
            buf = bytearray(n)
            for at, data in marks:
                lo, hi = max(at, pos_), min(at + len(data), pos_ + n)
                if lo < hi:
                    buf[lo - pos_:hi - pos_] = data[lo - at:hi - at]
            yield bytes(buf)
            pos_ += n
    def img_data(pol):
        """v0.13: the member with every record's samples (band_noise) after the descriptor and the prefixes."""
        buf = bytearray(720 + nl * rec)
        for at, b in [(0, fdr)] + list(prefixes.items()):
            buf[at:at + len(b)] = b
        smp = band_noise(orb, pol, nl, width, amp if pol == 'HH' else amp / 2.0)
        for i in range(nl):
            buf[720 + i * rec + 412:720 + (i + 1) * rec] = smp[i * 8 * width:(i + 1) * 8 * width]
        cut = img_short if pol == 'HH' else hv_short
        return bytes(buf[:len(buf) - cut] if cut else buf)
    sf = SparseFile(p)
    with zipfile.ZipFile(sf, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            if f.startswith('IMG-HV') and not hv_member:
                continue
            if f.startswith('IMG'):
                zi = zipfile.ZipInfo(pre + f, date_time=(2026, 10, 16, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
                if data:
                    b = img_data('HV' if f.startswith('IMG-HV') else 'HH')
                    zi.file_size = len(b)
                    with z.open(zi, 'w') as w:
                        w.write(b)
                    continue
                zi.file_size = total - (hv_short if f.startswith('IMG-HV') else 0)
                with z.open(zi, 'w') as w:
                    n_left = zi.file_size
                    for b in img_chunks(pol='HV' if f.startswith('IMG-HV') else 'HH'):
                        w.write(b[:n_left])
                        n_left -= min(len(b), n_left)
            else:
                z.writestr(pre + f, led if f.startswith('LED') else b'x' * 64)
        z.writestr(pre + 'E%s.jpg' % sid, b'\xff\xd8 mock browse image \xff\xd9')
        z.writestr(pre + 'summary.txt', '\n'.join(s) + '\n')
    sf.close()
    return p


V13_KEYS = ('beams_run', 'framing_max_km', 'framing_max_share', 'framing_anchor_km', 'framing_bc_max_km', 'framing_xt_max_km',
            'framing_law_A', 'framing_law_D', 'framing_law_beam', 'framing_law_band_deg', 'framing_law_check_km',
            'footprint_check_deg', 'footprint_corner_max_deg')


def mock_dem(T, name, north, Y, X=300):
    """A mock DEM trio (Int16 zeros, 0.01 deg) from 120 E and from north down Y rows; v0.13: its own name for each extent."""
    dem = os.path.join(T, 'dem', name)
    with open(dem, 'wb') as fh:
        fh.truncate(X * Y * 2)
    with open(dem + '.vrt', 'w') as fh:
        fh.write('<VRTDataset rasterXSize="%d" rasterYSize="%d">\n  <SRS>EPSG:4326</SRS>\n'
                 '  <GeoTransform>120.0, 0.01, 0.0, %.1f, 0.0, -0.01</GeoTransform>\n'
                 '  <VRTRasterBand dataType="Int16" band="1" subClass="VRTRawRasterBand">\n'
                 '    <SourceFilename relativeToVRT="1">%s</SourceFilename>\n'
                 '  </VRTRasterBand>\n</VRTDataset>\n' % (X, Y, north, name))
    with open(dem + '.xml', 'w') as fh:
        fh.write('<imageFile><property name="width"><value>%d</value></property></imageFile>\n' % X)
    return dem


def mkzips_data(specs):
    """v0.13: granules with samples (mkzip data=True: numpy), made in this Python when it has numpy, else by the mock env's
    Python (MOCKPY, chosen by pick_python) running this module; specs: [folder, orbit, frame, mkzip's keywords]. True when
    made."""
    try:
        import numpy  # noqa: F401
        for f, o, fr, kw in specs:
            mkzip(f, o, fr, **dict(dict(data=not kw.get('rows13')), **kw))
        return True
    except ImportError:
        pass
    if not MOCKPY[0]:
        return False
    code = ('import json, sys; sys.path.insert(0, %r); import lp_selftest as S\n'
            'for f, o, fr, kw in json.load(sys.stdin): S.mkzip(f, o, fr, **dict(dict(data=not kw.get("rows13")), **kw))' % HERE)
    p = subprocess.run([MOCKPY[0], '-B', '-c', code], input=json.dumps(specs).encode(), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'),
                                                      'PYTHONDONTWRITEBYTECODE': '1'})
    return p.returncode == 0


def build(T):
    arc = os.path.join(T, 'archive', 'alos')
    for i, orb in enumerate(ORBITS):                                   # frame 3320: the real 24
        mkzip(os.path.join(arc, str(10 + i % 5)), orb, '3320')
    for orb in ORBITS[:19]:                                            # frame 3330: 19
        mkzip(os.path.join(arc, '20'), orb, '3330')
    for i, orb in enumerate(ORBITS[:23]):                              # frame 3310: 23, one off-beam, nested
        if i == 4:
            mkzip(os.path.join(arc, '21'), orb, '3310', offnadir=41.5, width=10976, nested=True)
        else:
            mkzip(os.path.join(arc, '21'), orb, '3310', nested=True)
    mkzip(os.path.join(arc, '21'), ORBITS[23], '3310', product='P1.1', nested=True)  # plus one polarimetric
    for i, orb in enumerate(ORBITS[:23]):                              # frame 3300: one wrong date
        mkzip(os.path.join(arc, '22'), orb, '3300', date='20000101' if i == 7 else None)
    for i, orb in enumerate(ORBITS[:7]):                               # frame 3290: one corrupt zip
        mkzip(os.path.join(arc, '23'), orb, '3290', corrupt=(i == 3))
    for orb in ORBITS[:8]:                                             # frame 3280: one duplicate
        mkzip(os.path.join(arc, '24'), orb, '3280')
    mkzip(os.path.join(arc, '25'), ORBITS[2], '3280')
    for orb in ORBITS[:3]:                                             # frame 3340: 3 only
        mkzip(os.path.join(arc, '26'), orb, '3340')
    # frame 3350: 12, four FBD (v0.13, 15.4; v0.12: three), with samples when numpy is at hand (else zeros, and the mixed
    # cases do not run)
    mixed = [[os.path.join(arc, '28'), orb, '3350', dict(fbd=(i in FBD_3350), width=W_MX, lines=LINES_MX)]
             for i, orb in enumerate(ORBITS[:12])]
    DATA_OK[0] = mkzips_data(mixed)
    if not DATA_OK[0]:
        for f, o, fr, kw in mixed:
            mkzip(f, o, fr, **kw)
    mkzip(os.path.join(arc, '27'), 5726, '0290', sfx='A')              # an ascending p449 granule
    mkzip(os.path.join(arc, '27'), 175 + 671 * 20, '3320')             # path 83, same frame
    os.makedirs(os.path.join(T, 'dem'))
    dem = mock_dem(T, 'mock.dem.wgs84', 18.0, 400)      # 120-123 E, 14-18 N, as the shared SRTM DEM
    dem12 = mock_dem(T, 'mock12.dem.wgs84', 18.0, 600)  # v0.13: 120-123 E, 12-18 N, frame 3350's (dem_3350, 14.4)
    real = open(os.path.join(HERE, 'linog_paths.cfg')).read()
    p084 = real.split('[p084]', 1)[1].split('\n[', 1)[0]
    # v0.13: the table's own G0.16, frame-law, beam and footprint settings (its [defaults] less root, archive, dem and disk)
    v13 = ''.join(ln + '\n' for ln in real.split('[defaults]', 1)[1].split('\n[', 1)[0].splitlines()
                  if ln.split('=', 1)[0].strip() in V13_KEYS)
    assert v13.count('\n') == len(V13_KEYS), v13
    os.makedirs(os.path.join(T, 'cfg'))
    for name, per_date in (('paths.cfg', '0.0001'), ('paths_bigdisk.cfg', '1e9')):
        with open(os.path.join(T, 'cfg', name), 'w') as fh:
            fh.write('[defaults]\nroot = %s\narchive = %s\ndem = %s\ndem_margin_deg = 0.1\nmin_dates = 5\n'
                     'warn_dates = 12\ndisk_gib_per_date = %s\ndisk_gib_margin = 0\noffnadir_tol = 0.5\n%s\n'
                     '[p084]%s\n# v0.13 self-test: the mixed mock frame 3350 lies at 13.3 N, on its own mock DEM (14.4\'s dem_<frame>),\n'
                     '# as the FBD-only mock frame 3360 at 12.8 N does\ndem_3350 = %s\ndem_3360 = %s\n' % (
                         os.path.join(T, 'root'), arc, dem, per_date, v13, p084.rstrip('\n'), dem12, dem12))
    # v0.10: linog_mintpy.cfg with R1's land floor scaled to the mock's 83 x 658 grid (the Phase 5 and 6 runs read it)
    mreal = open(os.path.join(HERE, 'linog_mintpy.cfg')).read()
    assert mreal.count('\nADMIT_LAND_MIN_PX=50000\n') == 1 and mreal.count('\nDROP1_FREE_GIB=10\n') == 1 \
        and mreal.count('\nDROP1_MIN_PEERS=10\n') == 1
    with open(os.path.join(T, 'cfg', 'mintpy_mock.cfg'), 'w') as fh:   # v0.12: drop1's free-space margin scaled to the mock's stacks
        fh.write(mreal.replace('\nADMIT_LAND_MIN_PX=50000\n', '\nADMIT_LAND_MIN_PX=%d\n' % MOCK_LAND_MIN_PX)
                 .replace('\nDROP1_FREE_GIB=10\n', '\nDROP1_FREE_GIB=%s\n' % MOCK_DROP1_FREE_GIB)
                 .replace('\nDROP1_MIN_PEERS=10\n', '\nDROP1_MIN_PEERS=%s\n' % MOCK_DROP1_MIN_PEERS))
    # Phase 2's own archive: frame 3320's 24 granules only, felix's dates (T11 adds a 25th to the main archive, which
    # would change the network: 161 pairs, not felix's 157)
    a2 = os.path.join(T, 'archive_p2', 'alos')
    for i, orb in enumerate(ORBITS):
        mkzip(os.path.join(a2, str(10 + i % 5)), orb, '3320')
    with open(os.path.join(T, 'cfg', 'paths_p2.cfg'), 'w') as fh:
        fh.write(open(os.path.join(T, 'cfg', 'paths.cfg')).read().replace('archive = %s\n' % arc, 'archive = %s\n' % a2))
    # Phases 3 and 4: four of felix's dates, 520 samples x 18432 lines (the kit's G7 and G10 read the full ALOS height)
    a3 = os.path.join(T, 'archive_p3', 'alos')
    for orb in P3_ORBITS:
        mkzip(os.path.join(a3, '30'), orb, '3320', width=P3_WIDTH, lines=P3_LINES)
    with open(os.path.join(T, 'cfg', 'paths_p3.cfg'), 'w') as fh:
        fh.write(open(os.path.join(T, 'cfg', 'paths.cfg')).read().replace('archive = %s\n' % arc, 'archive = %s\n' % a3)
                 .replace('min_dates = 5\n', 'min_dates = 4\n'))   # a 4-date test frame (the table's own threshold)
    return arc


def PHASES_ALL():
    """The driver's phase list, in its order (v0.13)."""
    import re
    return re.search(r'^PHASES="([^"]*)"', open(ENTRY).read(), re.M).group(1).split()


def real_pins(name='linog_env.cfg'):
    d = {}
    for ln in open(os.path.join(HERE, name)):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def md5(p):
    import hashlib
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


MOCKPY = [None]   # the Python the mock env runs on (set by pick_python)
FFTWLIB = [None]  # v0.9: the real libfftw3f the mock env carries a copy of (set by build_env; None: none on this host)
FFTW_SMALL = dict(SIZE_MIN=2, SIZE_MAX=6, OFFSET_MIN=0, OFFSET_MAX=4, OFFSET_STEP=4, PROBLEMS=20)


def pick_fftw():
    """v0.9: a real libfftw3f for the mock env: the pinned env's (ENV_PREFIX/FFTW_LIB_REL of linog_stack.cfg and
    linog_fftw.cfg; only read, never written), as on felix, else this host's system library; None if neither loads."""
    import ctypes
    spins, fpins = real_pins('linog_stack.cfg'), real_pins('linog_fftw.cfg')
    cands = []
    if spins.get('ENV_PREFIX') and fpins.get('FFTW_LIB_REL'):
        cands.append(os.path.join(spins['ENV_PREFIX'], fpins['FFTW_LIB_REL']))
    for d in ('/usr/lib/x86_64-linux-gnu', '/usr/lib64', '/usr/lib', '/usr/local/lib', '/lib/x86_64-linux-gnu'):
        cands += sorted(glob.glob(os.path.join(d, 'libfftw3f.so.3*')))
    for c in cands:
        c = os.path.realpath(c)
        if not os.path.isfile(c):
            continue
        try:
            ctypes.CDLL(c).fftwf_plan_dft_1d
            return c
        except (OSError, AttributeError):
            continue
    return None


def build_fftw(T, env, site):
    """v0.9: the mock env's FFTW: a copy of a real libfftw3f at lib/libfftw3f.so.3.7.11 (lib/libfftw3f.so.3 linking to it),
    stand-ins of ISCE2's three modules at linog_fftw.cfg's places in the mock isce (and one that loads another library),
    a mock ldd, a wisdom file made here with that library for FFTW_SMALL's 20 problems, a garbage file, and fftw_mock.cfg
    with seven planted variants (the wisdom changed, the library's md5, a module loading another library, a file that does
    not import, a file that covers 16 of the 20 problems, another version string, the pinned library not the one
    lib/libfftw3f.so.3 resolves to). Returns True when a library was found."""
    import lp_fftw as F
    lib = pick_fftw()
    FFTWLIB[0] = lib
    if not lib:
        return False
    ld = os.path.join(env, 'lib')
    shutil.copy2(lib, os.path.join(ld, 'libfftw3f.so.3.7.11'))
    os.symlink('libfftw3f.so.3.7.11', os.path.join(ld, 'libfftw3f.so.3'))
    fp = real_pins('linog_fftw.cfg')
    mods = {}
    for m in ('AMPCOR', 'CROSSMUL', 'ICU'):
        p = os.path.join(site, 'isce', fp['%s_SO' % m])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w') as fh:
            fh.write('MOCK %s (linog_auto self-test): a stand-in for ISCE2\'s module; the mock ldd says it loads the env\'s '
                     'libfftw3f\n' % os.path.basename(p))
        mods[m] = (fp['%s_SO' % m], md5(p))
    other = os.path.join(os.path.dirname(os.path.join(site, 'isce', fp['AMPCOR_SO'])), 'ampcor_other.abi3.so')
    with open(other, 'w') as fh:
        fh.write('MOCK ampcor_other.abi3.so (linog_auto self-test): OTHERLIB, the mock ldd says it loads another libfftw3f\n')
    with open(os.path.join(env, 'bin', 'ldd'), 'w') as fh:
        fh.write('#!/usr/bin/env bash\n'
                 '# MOCK ldd (linog_auto self-test, v0.9): for the mock env\'s stand-ins of ISCE2\'s FFT modules (first word MOCK)\n'
                 '# the libfftw3f they load: the env\'s, or another when the file says OTHERLIB; any other file goes to the real ldd.\n'
                 'f=${@: -1}\n'
                 'if [ "$(head -c 4 "$f" 2>/dev/null)" = MOCK ]; then\n'
                 '  if grep -q OTHERLIB "$f"; then printf \'\\tlibfftw3f.so.3 => %s (0x00007f0000000000)\\n\' /usr/lib/other/libfftw3f.so.3\n'
                 '  else printf \'\\tlibfftw3f.so.3 => %s (0x00007f0000000000)\\n\' "$CONDA_PREFIX/lib/libfftw3f.so.3"; fi\n'
                 '  printf \'\\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f0000000000)\\n\'; exit 0\nfi\n'
                 'exec /usr/bin/ldd "$@"\n')
    os.chmod(os.path.join(env, 'bin', 'ldd'), 0o755)
    with open(os.path.join(env, 'etc', 'conda', 'activate.d', 'fftw-mock.sh'), 'w') as fh:
        fh.write('export MOCK_FFTW_LIB="$CONDA_PREFIX/lib/libfftw3f.so.3"   # the mock steps import the wisdom through it\n')
    fd = os.path.join(T, 'fftw')
    os.makedirs(fd)
    # the partial file first: FFTW keeps the wisdom of every plan made in this process and exports it all, so the
    # smaller set must be exported before the full one is planned
    part = os.path.join(fd, 'wisdom_partial.wis')
    F.gen(os.path.join(ld, 'libfftw3f.so.3.7.11'), part, dict(FFTW_SMALL, SIZE_MAX=FFTW_SMALL['SIZE_MAX'] - 1))
    wis = os.path.join(fd, 'wisdom_mock.wis')
    g = F.gen(os.path.join(ld, 'libfftw3f.so.3.7.11'), wis, FFTW_SMALL)
    shutil.copy2(os.path.join(ld, 'libfftw3f.so.3.7.11'), os.path.join(ld, 'libfftw3f_copy.so.3'))
    bad = os.path.join(fd, 'wisdom_bad.wis')
    txt = open(wis).read()
    i = txt.index('#x') + 2
    open(bad, 'w').write(txt[:i] + ('0' if txt[i] != '0' else '1') + txt[i + 1:])
    shutil.copy2(wis, os.path.join(fd, 'wisdom_touch.wis'))   # T171 appends to it during refine's step
    garbage = os.path.join(fd, 'garbage.wis')
    open(garbage, 'w').write('(not fftw wisdom: a planted file for the self-test)\n')
    base = dict(WISDOM=wis, WISDOM_MD5=md5(wis), FFTW_LIB_REL='lib/libfftw3f.so.3.7.11', FFTW_LIB_MD5=md5(os.path.join(ld, 'libfftw3f.so.3.7.11')),
                FFTW_VERSION=g['version'], **dict(FFTW_SMALL))
    for m, (rel, h) in mods.items():
        base['%s_SO' % m], base['%s_SO_MD5' % m] = rel, h
    variants = (('fftw_mock.cfg', {}), ('fftw_badwis.cfg', dict(WISDOM=bad)),
                ('fftw_badlib.cfg', dict(FFTW_LIB_MD5='0' * 32)),
                ('fftw_badmod.cfg', dict(AMPCOR_SO=os.path.join(os.path.dirname(fp['AMPCOR_SO']), 'ampcor_other.abi3.so'), AMPCOR_SO_MD5=md5(other))),
                ('fftw_garbage.cfg', dict(WISDOM=garbage, WISDOM_MD5=md5(garbage))),
                ('fftw_partial.cfg', dict(WISDOM=part, WISDOM_MD5=md5(part))), ('fftw_version.cfg', dict(FFTW_VERSION='fftw-0.0.0-mock')),
                ('fftw_link.cfg', dict(FFTW_LIB_REL='lib/libfftw3f_copy.so.3')),
                ('fftw_touch.cfg', dict(WISDOM=os.path.join(fd, 'wisdom_touch.wis'))))
    for name, over in variants:
        with open(os.path.join(T, 'cfg', name), 'w') as fh:
            fh.write('# linog_auto self-test: %s, linog_fftw.cfg for the mock env (library %s, %s; %d problems)\n' % (
                name, lib, g['version'], FFTW_SMALL['PROBLEMS']))
            for k, v in sorted(dict(base, **over).items()):
                fh.write('%s=%s\n' % (k, v))
    return True


def has_numpy(py, T):
    """True when py imports numpy and matplotlib (the real stackStripMap.py needs both). matplotlib's config folder is
    put under T and no bytecode is written, so the check leaves nothing in HOME or in the env."""
    try:
        return subprocess.run([py, '-B', '-c', 'import numpy, matplotlib'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1',
                                   'MPLCONFIGDIR': os.path.join(T, 'mplconfig_check')}, timeout=120).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def pick_python(spins, T):
    """This Python if it has numpy and matplotlib, else the pinned env's python3 (ENV_PREFIX/bin/python3 of
    linog_stack.cfg; only run, never written to); None if neither."""
    cands = [sys.executable]
    if spins.get('ENV_PREFIX'):
        cands.append(os.path.join(spins['ENV_PREFIX'], 'bin', 'python3'))
    for py in cands:
        if os.path.isfile(py) and has_numpy(py, T):
            MOCKPY[0] = py
            return py, cands
    return None, cands


def build_env(T):
    """A mock conda with env linog_isce2 (felix's activation: no PYTHONPATH, no stripmapStack on the PATH), the mock
    isce, the kit's unpacker and checks, and three env cfgs: good, a changed unpacker, no conda.sh."""
    root = os.path.join(T, 'mockconda')
    env = os.path.join(root, 'envs', 'linog_isce2')
    site = os.path.join(env, 'lib', 'site-packages')
    for d in (os.path.join(root, 'etc', 'profile.d'), os.path.join(env, 'bin'),
              os.path.join(env, 'etc', 'conda', 'activate.d'), os.path.join(env, 'share', 'isce2')):
        os.makedirs(d)
    shutil.copytree(os.path.join(KITSRC, 'mock_isce'), site)
    with open(os.path.join(root, 'etc', 'profile.d', 'conda.sh'), 'w') as fh:
        fh.write('# MOCK conda.sh (linog_auto self-test): `conda activate NAME` as felix does it (RD2, 26 Sept 2026):\n'
                 '# CONDA_DEFAULT_ENV, CONDA_PREFIX, <prefix>/bin first on the PATH, then activate.d; no PYTHONPATH.\n'
                 'conda() {\n'
                 '  [ "$1" = activate ] && [ -d "%s/envs/$2" ] || { echo "mock conda: cannot activate $2" >&2; return 1; }\n'
                 '  export CONDA_DEFAULT_ENV=$2 CONDA_PREFIX="%s/envs/$2"\n'
                 '  export PATH="$CONDA_PREFIX/bin:$PATH"\n'
                 '  for f in "$CONDA_PREFIX"/etc/conda/activate.d/*.sh; do [ -f "$f" ] && . "$f"; done\n'
                 '  return 0\n}\n' % (root, root))
    py = os.path.join(env, 'bin', 'python3')
    with open(py, 'w') as fh:
        fh.write('#!/usr/bin/env bash\n# MOCK env python3 (linog_auto self-test): %s with the mock '
                 'site-packages on its path; no bytecode (it may be the real env\'s python)\n'
                 'export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}%s" PYTHONDONTWRITEBYTECODE=1\n'
                 'if [ -n "${LINOG_MOCK_APPLYSLEEP:-}" ] && [[ " $* " == *linog_redatum_misreg_v2.py*--apply* ]]; then\n'
                 '  echo "sleeping before --apply" > "$LINOG_MOCK_MARK"; sleep "$LINOG_MOCK_APPLYSLEEP"; fi\n'
                 'exec %s "$@"\n'
                 % (MOCKPY[0] or sys.executable, site, MOCKPY[0] or sys.executable))
    os.chmod(py, 0o755)
    shutil.copy2(py, os.path.join(env, 'bin', 'python'))   # v0.7: linog_phase6.sh calls `python`, as felix's env has it
    sd = os.path.join(env, 'share', 'isce2', 'stripmapStack')
    os.makedirs(sd)
    for n in ('stackStripMap.py', 'Stack.py', 'stripmapWrapper.py', 'invertMisreg.py', 'referenceStackCopy.py'):
        shutil.copy2(os.path.join(KITSRC, 'mock_stack', n), os.path.join(sd, n))
    for n in sorted(os.listdir(os.path.join(KITSRC, 'mock_stack3'))):
        if n.endswith('.py'):
            shutil.copy2(os.path.join(KITSRC, 'mock_stack3', n), os.path.join(sd, n))
    for n in ('stripmapWrapper.py', 'invertMisreg.py', 'referenceStackCopy.py'):
        os.chmod(os.path.join(sd, n), 0o755)
    shutil.copy2(os.path.join(KITSRC, 'mock_bin', 'gdal_translate'), os.path.join(env, 'bin', 'gdal_translate'))
    # v0.6: a mock MintPy 1.6.2 (its version and its own defaults file, as Phase 5 pins them) in the mock site-packages,
    # and its two commands (mock prep_isce.py and smallbaselineApp.py) in the env's bin, where felix's env has them
    shutil.copytree(os.path.join(KITSRC, 'mock_mintpy', 'mintpy'), os.path.join(site, 'mintpy'))
    for n in sorted(os.listdir(os.path.join(KITSRC, 'mock_mintpy', 'bin'))):
        shutil.copy2(os.path.join(KITSRC, 'mock_mintpy', 'bin', n), os.path.join(env, 'bin', n))
        os.chmod(os.path.join(env, 'bin', n), 0o755)
    with open(os.path.join(env, 'etc', 'conda', 'activate.d', 'isce2-activate.sh'), 'w') as fh:
        fh.write('export ISCE_HOME=%s\n' % os.path.join(site, 'isce'))
    for d, name in (('bin', 'unpackFrame_ALOS.py'), ('kit', 'linog_unpack_verify.py'), ('kit', 'linog_shelve_gate.py'),
                    ('kit', 'linog_net_table.py'), ('kit', 'linog_fbs_bandlimit.py'), ('kit', 'linog_fbs_downsample.py')):   # v0.13: bandlimit's two
        os.makedirs(os.path.join(T, d), exist_ok=True)
        shutil.copy2(os.path.join(KITSRC, name), os.path.join(T, d, name))
    for name in sorted(os.listdir(os.path.join(KITSRC, 'kit3'))):
        shutil.copy2(os.path.join(KITSRC, 'kit3', name), os.path.join(T, 'kit', name))
    for d in ('bin', 'kit'):   # v0.13 r1: the self-test's own copies writable by its account, whatever the package's modes (T40b)
        for name in os.listdir(os.path.join(T, d)):
            q = os.path.join(T, d, name)
            os.chmod(q, (os.stat(q).st_mode & 0o777) | 0o600)
    rreal = open(os.path.join(HERE, 'linog_run.cfg')).read().splitlines()
    mods = dict(TOPO_MD5='topo.py', GEO2RDR_MD5='geo2rdr.py', RESAMPLE_MD5='resampleSlc.py', REFINE_MD5='refineSecondaryTiming.py',
                BASELINEGRID_MD5='baselineGrid.py', CROSSMUL_MD5='crossmul.py', FILTCOH_MD5='FilterAndCoherence.py',
                UNWRAP_MD5='unwrap.py')
    with open(os.path.join(T, 'cfg', 'run_mock.cfg'), 'w') as fh:
        fh.write('# linog_auto self-test: linog_run.cfg with the mock stripmapStack modules\' md5s and small memory peaks\n')
        for ln in rreal:
            k = ln.split('=', 1)[0]
            if k in mods:
                ln = '%s=%s' % (k, md5(os.path.join(KITSRC, 'mock_stack3', mods[k])))
            elif k.endswith('_PEAK_KB'):
                ln = '%s=1000' % k
            fh.write(ln + '\n')
    os.makedirs(os.path.join(T, 'bin2'))
    with open(os.path.join(T, 'bin2', 'unpackFrame_ALOS.py'), 'w') as fh:
        fh.write(open(os.path.join(KITSRC, 'unpackFrame_ALOS.py')).read() + '\n')
    build_fftw(T, env, site)   # v0.9
    pins = real_pins()
    base = dict(pins, CONDA_SH=os.path.join(root, 'etc', 'profile.d', 'conda.sh'), CONDA_ENV='linog_isce2',
                UNPACKER=os.path.join(T, 'bin', 'unpackFrame_ALOS.py'), KIT=os.path.join(T, 'kit'))
    u2 = os.path.join(T, 'bin2', 'unpackFrame_ALOS.py')
    sreal = open(os.path.join(HERE, 'linog_stack.cfg')).read()
    for name, over in (('stack_mock.cfg', dict(ENV_PREFIX=env)), ('stack_otherprefix.cfg', dict(ENV_PREFIX=os.path.join(T, 'elsewhere')))):
        with open(os.path.join(T, 'cfg', name), 'w') as fh:
            fh.write('# linog_auto self-test: %s, linog_stack.cfg with ENV_PREFIX=%s\n' % (name, over['ENV_PREFIX']))
            fh.write('\n'.join('ENV_PREFIX=%s' % over['ENV_PREFIX'] if ln.startswith('ENV_PREFIX=') else ln
                               for ln in sreal.splitlines()) + '\n')
    for name, over in (('env_mock.cfg', {}), ('env_badunpacker.cfg', dict(UNPACKER=u2)),
                       ('env_newunpacker.cfg', dict(UNPACKER=u2, UNPACKER_MD5=md5(u2))),
                       ('env_noconda.cfg', dict(CONDA_SH=os.path.join(root, 'etc', 'profile.d', 'absent.sh')))):
        with open(os.path.join(T, 'cfg', name), 'w') as fh:
            fh.write('# linog_auto self-test: mock environment (%s); pins copied from linog_env.cfg\n' % name)
            for k, v in sorted(dict(base, **over).items()):
                fh.write('%s=%s\n' % (k, v))
    return pins


def run(T, args, cfg='paths.cfg', env_extra=None, envcfg='env_mock.cfg', keep_default=False):
    env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
           and not k.startswith('LINOG_MOCK_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfg), LINOG_AUTO_HOST=socket.gethostname(),
               LINOG_ENV_CFG=os.path.join(T, 'cfg', envcfg), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
               LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'))
    env.update(env_extra or {})
    if len(args) >= 2 and args[0] != '--selftest' and '--to' not in args and '--only' not in args and not keep_default:
        args = args + ['--to', 'stack2']   # the Phase 0 to 2 cases were written for v0.3, whose default was stack2
    p = subprocess.run(['bash', ENTRY] + args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh %s  (cfg %s, env %s%s)  rc %d\n%s' % (
            ' '.join(args), cfg, envcfg, ''.join(' %s=%s' % kv for kv in sorted((env_extra or {}).items())),
            p.returncode, out))
    return p.returncode, out


def rec(T, frame, idx, phase, root='root'):
    f = os.path.join(T, root, 'p084', 'f' + frame, 'status', 'P%s_%s.json' % (idx, phase))
    return json.load(open(f)) if os.path.exists(f) else {}


def fdir(T, frame, root='root'):
    return os.path.join(T, root, 'p084', 'f' + frame)


def nraw(T, frame, root='root'):
    d = os.path.join(fdir(T, frame, root), 'raw')
    return len(os.listdir(d)) if os.path.isdir(d) else -1


def nsub(T, frame, sub, root):
    d = os.path.join(fdir(T, frame, root), sub)
    return len([e for e in os.listdir(d) if not e.startswith('.')]) if os.path.isdir(d) else -1


def nlines(p):
    return sum(1 for _ in open(p)) if os.path.exists(p) else 0


def ledger(T, frame, root='root'):
    """(phase lines, run lines) of the frame's logs/STATUS.txt."""
    p = os.path.join(fdir(T, frame, root), 'logs', 'STATUS.txt')
    ls = open(p).read().splitlines() if os.path.exists(p) else []
    return sum(any(k in x for k in PHASE_LINE) for x in ls), sum('auto_run ' in x for x in ls)


def modes(T, frame, root):
    p = os.path.join(fdir(T, frame, root), 'recon', 'modes.json')
    return (json.load(open(p)), md5(p)) if os.path.exists(p) else ({}, None)


def verdicts(T, frame, root):
    """Phases 0 and 1's verdicts, in the pipeline's order (v0.13: bandlimit between rwin and verify)."""
    return [rec(T, frame, i, ph, root).get('verdict') for i, ph in
            (('0a', 'recon'), ('0b', 'stage'), ('1a', 'extract'), ('1b', 'unpack'), ('1br', 'rwin'), ('1bs', 'bandlimit'),
             ('1c', 'verify'))]


def aside(T, src, tag):
    """Move src into DIR/_archive/<tag>_<basename> (the self-test never deletes)."""
    d = os.path.join(T, '_archive')
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, '%s_%s' % (tag, os.path.basename(src)))
    shutil.move(src, dst)
    return dst


def stopped_run(T, root, sig, date):
    """Start a full run that sleeps in the mock sensor on date, send sig to its process group there, wait."""
    env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM')
           and not k.startswith('LINOG_MOCK_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
               LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_ROOT=os.path.join(T, root),
               LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_MOCK_SLEEP=date)
    # SIGINT back to its default in the run: a self-test started in the background (nohup ... &) has SIGINT ignored,
    # which every child inherits and bash cannot trap, so T39's Ctrl-C would reach nothing
    p = subprocess.Popen(['bash', ENTRY, '084', '3320', '--to', 'verify'], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True, preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
    lg = os.path.join(fdir(T, '3320', root), 'logs', 'unpack', date + '.log.v1')
    t0 = time.time()
    while not os.path.exists(lg) and p.poll() is None and time.time() - t0 < 120:
        time.sleep(0.2)
    time.sleep(1.5)
    if p.poll() is None:
        os.killpg(p.pid, sig)
    out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 3320  (LINOG_ROOT=%s, LINOG_MOCK_SLEEP=%s, signal %d after %.1f s)  rc %d\n%s'
                 % (root, date, sig, time.time() - t0, p.returncode, out))
    return p.returncode, out


def stopped_run2(T, root, extra, mark, sig=signal.SIGTERM):
    """Start a Phase 2 run (paths_p2.cfg) whose mock Baseline writes mark and sleeps; send sig to its process group
    once mark exists; wait."""
    env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM')
           and not k.startswith('LINOG_MOCK_')}
    env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p2.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
               LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_ROOT=os.path.join(T, root),
               LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_MOCK_MARK=mark, **extra)
    p = subprocess.Popen(['bash', ENTRY, '084', '3320', '--decide', 'auto'], env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 120:
        time.sleep(0.2)
    time.sleep(0.5)
    if p.poll() is None:
        os.killpg(p.pid, sig)
    out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
    with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
        fh.write('\n\n######## linog_auto.sh 084 3320 --decide auto  (LINOG_ROOT=%s, %s, signal %d after %.1f s)  rc %d\n%s'
                 % (root, ' '.join('%s=%s' % kv for kv in sorted(extra.items())), sig, time.time() - t0, p.returncode, out))
    return p.returncode, out


def last_ledger(T, root):
    p = os.path.join(fdir(T, '3320', root), 'logs', 'STATUS.txt')
    return open(p).read().splitlines()[-1] if os.path.exists(p) else ''


def in_env(T, args):
    env = {k: v for k, v in os.environ.items() if not k.startswith('LINOG_')}
    env['LINOG_ENV_CFG'] = os.path.join(T, 'cfg', 'env_mock.cfg')
    return subprocess.run(['bash', os.path.join(HERE, 'lp_env.sh')] + args, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode


def main(T):
    T = os.path.abspath(T)
    if os.path.exists(T) and os.listdir(T):
        print('selftest: %s exists and is not empty; give a new folder' % T)
        return 1
    os.makedirs(T, exist_ok=True)
    os.environ.pop('LINOG_MIXED_CFG', None)   # v0.13: every run reads the package's linog_mixed.cfg unless a case names another
    mockpy, tried = pick_python(real_pins('linog_stack.cfg'), T)   # v0.13: first, so build() can make samples with its numpy
    arc = build(T)
    pins = build_env(T)
    lin = os.path.join(T, 'root', 'p084', 'LINEAGE.txt')
    res = []

    def case(name, cond, detail=''):
        res.append((name, bool(cond), detail))
        print('   %-4s %-60s %s' % ('PASS' if cond else 'FAIL', name, detail))
        sys.stdout.flush()

    print('linog_auto self-test in %s (mock archive %s)' % (T, arc))
    SUITES = [x for x in os.environ.get('LINOG_SELFTEST_SUITES', '').replace(' ', '').split(',') if x]
    if SUITES:
        print('   (v0.13 development: only the suites %s, LINOG_SELFTEST_SUITES)' % ','.join(SUITES))

    def want(name):
        return not SUITES or name in SUITES

    if want('0'):
        print('-- Phase 0 (recon, stage), every run --to stage')
        S = ['--to', 'stage']
        rc, out = run(T, ['084', '3320'] + S)
        case('T1  clean frame 3320: rc 0, recon and stage PASS, 24 links',
             rc == 0 and rec(T, '3320', '0a', 'recon').get('verdict') == 'PASS'
             and rec(T, '3320', '0b', 'stage').get('verdict') == 'PASS' and nraw(T, '3320') == 24,
             'rc %d raw %d' % (rc, nraw(T, '3320')))
        case('T1b branch FBS-only, widths 16 x 9344 + 8 x 9376, ledger 4 phase lines, lineage 3 lines',
             rec(T, '3320', '0a', 'recon').get('outputs', {}).get('branch') == 'FBS-only'
             and '{9344: 16, 9376: 8}' in out and ledger(T, '3320') == (4, 2) and nlines(lin) == 3,
             'ledger %s lineage %d' % (ledger(T, '3320'), nlines(lin)))
        rc, out = run(T, ['084', '3320'] + S)
        case('T2  re-run: both phases skipped, ledger and lineage unchanged',
             rc == 0 and out.count('skip: PASS on record') == 2 and ledger(T, '3320')[0] == 4 and nlines(lin) == 3,
             'rc %d' % rc)
        rc, out = run(T, ['084', '3320', '--force', 'stage'] + S)
        case('T3  --force stage: PASS, nothing to do, lineage unchanged',
             rc == 0 and 'nothing to do' in out and nlines(lin) == 3, 'rc %d' % rc)
        rc, out = run(T, ['084', '3330'] + S)
        case('T4  frame 3330: DEM margin 0.015 deg < 0.1 -> FAIL at recon (G0.14), no stage',
             rc == 2 and 'G0.14' in rec(T, '3330', '0a', 'recon').get('reason', '')
             and not rec(T, '3330', '0b', 'stage') and nraw(T, '3330') == -1, 'rc %d' % rc)
        rc, out = run(T, ['084', '3310'] + S)
        r = rec(T, '3310', '0a', 'recon').get('outputs', {})
        case('T5  frame 3310: off-beam and P1.1 dropped, 22 kept and staged',
             rc == 0 and r.get('kept') == 22 and r.get('dropped') == 2 and nraw(T, '3310') == 22,
             'rc %d kept %s dropped %s' % (rc, r.get('kept'), r.get('dropped')))
        rc, out = run(T, ['084', '3300'] + S)
        case('T6  frame 3300: one summary date off the date law -> FAIL (G0.5)',
             rc == 2 and 'G0.5' in rec(T, '3300', '0a', 'recon').get('reason', ''), 'rc %d' % rc)
        rc, out = run(T, ['084', '3290'] + S)
        case('T7  frame 3290: corrupt zip -> DECISION (G0.4), stage not run',
             rc == 4 and 'G0.4' in rec(T, '3290', '0a', 'recon').get('reason', '') and nraw(T, '3290') == -1,
             'rc %d' % rc)
        os.makedirs(os.path.join(fdir(T, '3290'), 'recon'), exist_ok=True)
        with open(os.path.join(fdir(T, '3290'), 'recon', 'exclude.txt'), 'w') as fh:
            fh.write('# selftest\nALPSRP%05d3290  corrupt in the archive (selftest T7b)\n' % ORBITS[3])
        rc, out = run(T, ['084', '3290'] + S)
        case('T7b exclusion written: recon re-runs, PASS with 6 kept (WARN < 12), 6 links',
             rc == 0 and nraw(T, '3290') == 6 and 'WARN' in out, 'rc %d raw %d' % (rc, nraw(T, '3290')))
        rc, out = run(T, ['084', '3280'] + S)
        case('T8  frame 3280: the same granule in two folders -> DECISION (G0.3)',
             rc == 4 and 'G0.3' in rec(T, '3280', '0a', 'recon').get('reason', ''), 'rc %d' % rc)
        sf = os.path.join(fdir(T, '3320'), 'status', 'P0b_stage.json')
        r = json.load(open(sf))
        r['verdict'] = 'RUNNING'
        json.dump(r, open(sf, 'w'))
        rc, out = run(T, ['084', '3320'] + S)
        case('T9  a RUNNING record without END -> stop, DECISION (rc 4)', rc == 4 and 'RUNNING' in out, 'rc %d' % rc)
        rc, out = run(T, ['084', '3320', '--recover'] + S)
        case('T9b --recover: stage re-runs and PASSes', rc == 0 and rec(T, '3320', '0b', 'stage').get('verdict') == 'PASS',
             'rc %d' % rc)
        dry = os.path.join(T, 'dry3310')
        rc, out = run(T, ['084', '3310', '--dry-run', dry] + S, env_extra={'LINOG_ROOT': os.path.join(T, 'root2')})
        case('T10 dry run in a fresh root: rc 0, records only under the dry folder, root2 not created',
             rc == 0 and os.path.exists(os.path.join(dry, 'recon', 'RECON.json'))
             and os.path.exists(os.path.join(dry, 'status', 'P0b_stage.json'))
             and not os.path.exists(os.path.join(T, 'root2')), 'rc %d' % rc)
        mkzip(os.path.join(arc, '11'), 27934, '3320')
        n_lin = nlines(lin)
        rc, out = run(T, ['084', '3320'] + S)
        case('T11 archive gains a 25th granule: recon and stage STALE, re-run, 25 links, lineage +1',
             rc == 0 and nraw(T, '3320') == 25 and nlines(lin) == n_lin + 1 and out.count('record STALE') == 2,
             'rc %d raw %d lineage %d -> %d' % (rc, nraw(T, '3320'), n_lin, nlines(lin)))
        rc, out = run(T, ['084', '3320'] + S, env_extra={'LINOG_AUTO_HOST': 'not-this-host'})
        case('T12 wrong host -> rc 3, nothing run', rc == 3 and 'wrong host' in out, 'rc %d' % rc)
        rc, out = run(T, ['085', '3320'] + S)
        g13 = dict((x['id'], x['verdict']) for x in json.load(open(os.path.join(T, 'root', 'p085', 'f3320', 'status', 'P0a_recon.json')))
                   .get('gates', [])) if os.path.isfile(os.path.join(T, 'root', 'p085', 'f3320', 'status', 'P0a_recon.json')) else {}
        case('T13 path not in the table (v0.13, R8: a derived entry, residue 0) -> G0.17 WARN, G0.2 FAIL (no granule has residue 0), rc 2',
             rc == 2 and g13.get('G0.17') == 'WARN' and g13.get('G0.2') == 'FAIL', 'rc %d; G0.17 %s G0.2 %s' % (rc, g13.get('G0.17'), g13.get('G0.2')))
        rc, out = run(T, ['084', '3340'] + S)
        g14 = dict((x['id'], (x['verdict'], x['value'])) for x in rec(T, '3340', '0a', 'recon').get('gates', []))
        case('T14 frame 3340 with 3 dates -> FAIL (G0.12); v0.13: no footprint in the table -> G0.14 by the granules\' corners (the mock '
             'places frame 3340 by the frame law at 13.8 N: south of the mock DEM, FAIL)',
             rc == 2 and 'G0.12' in rec(T, '3340', '0a', 'recon').get('reason', '') and g14.get('G0.14', ('',))[0] == 'FAIL'
             and "3 granules' corners" in g14.get('G0.14', ('', ''))[1], 'rc %d; G0.14 %s' % (rc, g14.get('G0.14')))
        rc, out = run(T, ['084', '3320'] + S, cfg='paths_bigdisk.cfg', env_extra={'LINOG_ROOT': os.path.join(T, 'root3')})
        case('T15 disk budget too large -> FAIL (G0.15)',
             rc == 2 and 'G0.15' in rec(T, '3320', '0a', 'recon', root='root3').get('reason', ''), 'rc %d' % rc)
        lockf = os.path.join(fdir(T, '3320'), 'status', '.lock')
        fd = os.open(lockf, os.O_RDWR | os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)      # held by this process, released below
        try:
            rc, out = run(T, ['084', '3320'] + S)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        case('T16 another run holds the lock -> rc 4, nothing run', rc == 4 and 'holds' in out, 'rc %d' % rc)
        stray = os.path.join(fdir(T, '3320'), 'raw', 'stray.txt')
        with open(stray, 'w') as fh:
            fh.write('x')
        n0 = nraw(T, '3320')
        rc, out = run(T, ['084', '3320', '--force', 'stage'] + S)
        case('T17 a stray file in raw/ -> DECISION (G0b.4), nothing changed, stray kept',
             rc == 4 and 'G0b.4' in rec(T, '3320', '0b', 'stage').get('reason', '') and 'stray.txt' in out
             and nraw(T, '3320') == n0 and os.path.exists(stray), 'rc %d' % rc)
        os.makedirs(os.path.join(fdir(T, '3320'), '_archive'), exist_ok=True)
        shutil.move(stray, os.path.join(fdir(T, '3320'), '_archive', 'stray.txt'))
        with open(os.path.join(fdir(T, '3320'), 'recon', 'exclude.txt'), 'w') as fh:
            fh.write('ALPSRP%05d3320  excluded after staging (selftest T18)\n' % ORBITS[0])
        rc, out = run(T, ['084', '3320'] + S)
        case('T18 a staged granule excluded afterwards: recon PASS 24 kept; stage DECISION, its link kept',
             rc == 4 and rec(T, '3320', '0a', 'recon').get('outputs', {}).get('kept') == 24
             and 'G0b.4' in rec(T, '3320', '0b', 'stage').get('reason', '')
             and 'not a kept granule' in out and nraw(T, '3320') == 25, 'rc %d raw %d' % (rc, nraw(T, '3320')))

    if want('13'):   # v0.13 Phase 0: R8, G0.16, G0.14, G0.18, the root and the driver's python3 (lp_selftest13.py)
        import lp_selftest13
        try:
            lp_selftest13.phase13_0(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 Phase 0 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])

    def phase1():
        print('-- Phase 1 (extract, unpack, rwin, verify) in the mock ISCE environment, every run --to verify')
        V = ['--to', 'verify']
        kit = [(n, k) for n, k in (('unpackFrame_ALOS.py', 'UNPACKER_MD5'), ('linog_unpack_verify.py', 'KIT_UNPACK_VERIFY_MD5'),
                                   ('linog_shelve_gate.py', 'KIT_SHELVE_GATE_MD5'))]
        same = [n for n, k in kit if md5(os.path.join(KITSRC, n)) == pins.get(k)]
        case('T19 the self-test runs the kit files felix pins: md5s = linog_env.cfg', len(same) == 3,
             '%d of 3 (%s)' % (len(same), ', '.join(n for n, _ in kit if n not in same) or 'all equal'))
        P = 'p1'
        E1 = {'LINOG_ROOT': os.path.join(T, P)}
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        R = json.load(open(os.path.join(fdir(T, '3320', P), 'recon', 'RECON.json')))
        n = len(R['kept'])
        wc = {}
        for k in R['kept']:
            wc[str(k['width'])] = wc.get(str(k['width']), 0) + 1
        M, m5 = modes(T, '3320', P)
        uz = os.path.join(fdir(T, '3320', P), 'unzipped')
        flat = all(len(os.listdir(os.path.join(uz, s))) == 6 and all(os.path.isfile(os.path.join(uz, s, f))
                   for f in os.listdir(os.path.join(uz, s))) for s in os.listdir(uz)) if os.path.isdir(uz) else False
        v = rec(T, '3320', '1c', 'verify', P)
        g = dict((x['id'], x['verdict']) for x in v.get('gates', []))
        u = rec(T, '3320', '1b', 'unpack', P)
        case('T20 clean frame 3320, all phases: rc 0, 7 PASS (v0.13: bandlimit N/A on FBS-only), %d dates flat, SLC, modes.json' % n,
             rc == 0 and verdicts(T, '3320', P) == ['PASS'] * 7 and nsub(T, '3320', 'unzipped', P) == n and flat
             and nsub(T, '3320', 'SLC', P) == n and len(M.get('dates', [])) == n and M.get('verdict') == 'PASS'
             and M.get('census', {}).get('width') == wc, 'rc %d unzipped %d SLC %d rows %d widths %s' % (
                 rc, nsub(T, '3320', 'unzipped', P), nsub(T, '3320', 'SLC', P), len(M.get('dates', [])),
                 M.get('census', {}).get('width')))
        pp = u.get('inputs', {}).get('pythonpath', '')
        bl = rec(T, '3320', '1bs', 'bandlimit', P)
        case('T20b G3b DESCENDING, G4 N/A, kit checks PASS, env clean (PYTHONPATH components first), ledger 14 + 2 (v0.13: 7 '
             'phases, bandlimit N/A, verify\'s G1c.8 PASS)',
             g.get('G3b') == 'PASS' and g.get('G4') == 'N/A' and g.get('G1c.6') == 'PASS' and g.get('G1c.8') == 'PASS'
             and [x['verdict'] for x in bl.get('gates', [])] == ['PASS', 'N/A']
             and pp.split(':')[0].endswith(os.path.join('isce', 'components')) and ledger(T, '3320', P) == (14, 2),
             'G3b %s G4 %s kit %s ledger %s' % (g.get('G3b'), g.get('G4'), g.get('G1c.6'), ledger(T, '3320', P)))
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T21 re-run: all 7 phases skipped (v0.13: bandlimit among them), ledger phase lines and modes.json unchanged',
             rc == 0 and out.count('skip: PASS on record') == 7 and ledger(T, '3320', P) == (14, 4)
             and modes(T, '3320', P)[1] == m5, 'rc %d skips %d ledger %s' % (rc, out.count('skip: PASS on record'),
                                                                          ledger(T, '3320', P)))
        rc, out = run(T, ['084', '3310'] + V, env_extra=E1)
        x = rec(T, '3310', '1a', 'extract', P)
        g2 = [y['value'] for y in x.get('gates', []) if y['id'] == 'G1a.2']
        uz = os.path.join(fdir(T, '3310', P), 'unzipped')
        flat = os.path.isdir(uz) and all(all(os.path.isfile(os.path.join(uz, s, f)) for f in os.listdir(os.path.join(uz, s)))
                                         for s in os.listdir(uz))
        case('T22 frame 3310, members under a folder: written flat, 22 dates PASS',
             rc == 0 and verdicts(T, '3310', P) == ['PASS'] * 7 and flat and 'under a folder 22' in (g2 or [''])[0]
             and nsub(T, '3310', 'SLC', P) == 22, 'rc %d %s' % (rc, (g2 or ['?'])[0]))
        st0 = sorted(os.listdir(uz))[0]
        part = os.path.join(uz, '.%s.part' % st0)
        os.makedirs(part)
        rc, out = run(T, ['084', '3310', '--force', 'extract'] + V, env_extra=E1)
        ok = rc == 4 and 'G1a.3' in rec(T, '3310', '1a', 'extract', P).get('reason', '') and os.path.isdir(part) \
            and nsub(T, '3310', 'unzipped', P) == 22
        aside(T, part, 'T23')
        rc2, out = run(T, ['084', '3310', '--force', 'extract'] + V, env_extra=E1)
        case('T23 a .part folder left by a killed extract -> DECISION (G1a.3), kept; moved away -> PASS, 22 reused',
             ok and rc2 == 0 and rec(T, '3310', '1a', 'extract', P).get('outputs', {}).get('reused') == 22,
             'rc %d then %d' % (rc, rc2))
        d3 = R['kept'][3]['date']
        sd = os.path.join(fdir(T, '3320', P), 'SLC', d3)
        aside(T, sd, 'T24_whole')
        os.makedirs(sd)
        with open(os.path.join(sd, d3 + '.slc'), 'wb') as fh:
            fh.write(b'\0' * 100)
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        ok = rc == 4 and 'G1b.3' in rec(T, '3320', '1b', 'unpack', P).get('reason', '') and 'record STALE' in out
        aside(T, sd, 'T24_partial')
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T24 a partial SLC/<date> -> unpack STALE, DECISION (G1b.3); moved away -> that date re-made, PASS',
             ok and rc2 == 0 and rec(T, '3320', '1b', 'unpack', P).get('outputs', {}).get('unpacked') == 1
             and verdicts(T, '3320', P) == ['PASS'] * 7, 'rc %d then %d' % (rc, rc2))
        pf = os.path.join(fdir(T, '3320', P), 'status', 'P1b_unpack.progress')
        b = (nlines(pf), nsub(T, '3320', 'SLC', P))
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1, envcfg='env_badunpacker.cfg')
        ok = rc == 2 and 'G2' in rec(T, '3320', '1b', 'unpack', P).get('reason', '') and (nlines(pf), nsub(T, '3320', 'SLC', P)) == b
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T25 unpacker changed by one byte -> FAIL (G2), nothing written; pinned one back -> PASS',
             ok and rc2 == 0, 'rc %d then %d' % (rc, rc2))
        ex = os.path.join(fdir(T, '3320', P), 'SLC', '20000101')
        os.makedirs(ex)
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        ok = rc == 4 and 'not a kept date' in out and os.path.isdir(ex)
        aside(T, ex, 'T26')
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T26 a folder in SLC/ that is not a kept date -> DECISION (G1b.3), kept; moved away -> PASS',
             ok and rc2 == 0, 'rc %d then %d' % (rc, rc2))
        d5 = R['kept'][5]['date']
        sd = os.path.join(fdir(T, '3320', P), 'SLC', d5)
        code = ("import isce, shelve, sys; d = sys.argv[1]; s = shelve.open(d + '/data', 'r'); f = s['frame']; s.close(); "
                "t = shelve.open(d + '/stock', 'n'); t['frame'] = f; t.close()")
        rcs = in_env(T, ['python3', '-c', code, sd])
        for f in sorted(glob.glob(os.path.join(sd, 'data.*'))):
            aside(T, f, 'T27_%s' % d5)
        for f in sorted(glob.glob(os.path.join(sd, 'stock.*'))):
            os.rename(f, os.path.join(sd, 'data' + f[len(os.path.join(sd, 'stock')):]))
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        v = rec(T, '3320', '1c', 'verify', P)
        ok = rcs == 0 and rc == 2 and 'G3' in v.get('reason', '') and 'G1c.6' in v.get('reason', '')
        for f in sorted(glob.glob(os.path.join(sd, 'data.*'))):
            aside(T, f, 'T27_stock')
        for f in sorted(glob.glob(os.path.join(T, '_archive', 'T27_%s_data.*' % d5))):
            shutil.move(f, os.path.join(sd, os.path.basename(f)[len('T27_%s_' % d5):]))
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T27 a shelve with only frame (the stock unpacker) -> verify FAIL (G3 and the kit gate); restored -> PASS',
             ok and rc2 == 0, 'rc %d then %d' % (rc, rc2))
        lv = os.path.join(fdir(T, '3320', P), 'logs', 'verify')
        aside(T, lv, 'T28')
        with open(lv, 'w') as fh:
            fh.write('a file where a folder belongs (selftest T28)\n')
        rc, out = run(T, ['084', '3320', '--force', 'verify'] + V, env_extra=E1)
        v = rec(T, '3320', '1c', 'verify', P)
        ok = rc == 3 and v.get('verdict') == 'ERROR' and 'unexpected error' in v.get('reason', '')
        aside(T, lv, 'T28_file')
        shutil.move(os.path.join(T, '_archive', 'T28_verify'), lv)
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T28 a phase that raises -> its record ends ERROR (not RUNNING), rc 3; fixed -> PASS',
             ok and rc2 == 0, 'rc %d (%s) then %d' % (rc, v.get('verdict'), rc2))
        u0 = open(os.path.join(fdir(T, '3320', P), 'status', 'P1b_unpack.json')).read()
        rc, out = run(T, ['084', '3320', '--force', 'unpack'] + V, env_extra=E1, envcfg='env_noconda.cfg')
        case('T29 no conda.sh -> rc 3, "wrote no record", the earlier record untouched',
             rc == 3 and 'wrote no record' in out and 'no conda.sh' in out
             and open(os.path.join(fdir(T, '3320', P), 'status', 'P1b_unpack.json')).read() == u0, 'rc %d' % rc)

        tr = os.path.join(T, 'archive_trunc')
        os.makedirs(tr)
        for i, orb in enumerate(ORBITS):
            mkzip(tr, orb, '3320', img_short=(8 if i == 6 else 0))
        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1t'), 'LINOG_ARCHIVE': tr})
        case('T30 an IMG-HH 8 B short in the archive -> recon and stage PASS, extract FAIL (G1a.5), nothing extracted',
             rc == 2 and verdicts(T, '3320', 'p1t')[:3] == ['PASS', 'PASS', 'FAIL']
             and 'G1a.5' in rec(T, '3320', '1a', 'extract', 'p1t').get('reason', '') and nsub(T, '3320', 'unzipped', 'p1t') == -1,
             'rc %d' % rc)
        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1a'), 'LINOG_MOCK_ASC': '1'})
        v = rec(T, '3320', '1c', 'verify', 'p1a')
        bad = sorted(x['id'] for x in v.get('gates', []) if x['verdict'] == 'FAIL')
        case('T31 orbit vz > 0 on a D path -> verify FAIL at G3b only (the kit checks cannot see it)',
             rc == 2 and bad == ['G3b'] and modes(T, '3320', 'p1a')[0].get('verdict') == 'FAIL', 'rc %d FAIL %s' % (rc, bad))
        off = os.path.join(T, 'archive_off')
        for orb in ORBITS:
            mkzip(off, orb, '3320', r0_off_m=50.0)
        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1b'), 'LINOG_ARCHIVE': off,
                                                     'LINOG_MOCK_PRF': repr(100000.0 / 46), 'LINOG_MOCK_BW': '14'})
        v = rec(T, '3320', '1c', 'verify', 'p1b')
        bad = sorted(set(x['id'] for x in v.get('gates', []) if x['verdict'] == 'FAIL'))
        rw = rec(T, '3320', '1br', 'rwin', 'p1b')
        case('T32 leader and records 50 m off the grid (they agree), PRF 100000/46, 14 MHz on FBS -> rwin PASS (nothing to change); '
             'verify FAIL at G1c.4, G1c.5, G5 and the kit check',
             rc == 2 and rw.get('verdict') == 'PASS' and not rw.get('outputs', {}).get('change')
             and bad == ['G1c.4', 'G1c.5', 'G1c.6', 'G5'], 'rc %d; rwin %s; FAIL %s' % (rc, rw.get('verdict'), bad))
        d12 = R['kept'][12]['date']
        E2 = {'LINOG_ROOT': os.path.join(T, 'p1f')}
        rc, out = run(T, ['084', '3320'] + V, env_extra=dict(E2, LINOG_MOCK_FAIL=d12))
        pf = os.path.join(fdir(T, '3320', 'p1f'), 'status', 'P1b_unpack.progress')
        ok = rc == 2 and 'unpacker rc 1' in rec(T, '3320', '1b', 'unpack', 'p1f').get('reason', '') and nlines(pf) == 12
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E2)
        ok2 = rc2 == 4 and 'G1b.3' in rec(T, '3320', '1b', 'unpack', 'p1f').get('reason', '')
        aside(T, os.path.join(fdir(T, '3320', 'p1f'), 'SLC', d12), 'T33')
        rc3, out = run(T, ['084', '3320'] + V, env_extra=E2)
        uo = rec(T, '3320', '1b', 'unpack', 'p1f').get('outputs', {})
        case('T33 the unpacker raises on date 13 -> FAIL, 12 kept; its SLC folder -> DECISION; moved -> PASS, 13 more',
             ok and ok2 and rc3 == 0 and uo.get('done_before') == 12 and uo.get('unpacked') == n - 12,
             'rc %d, %d, %d; progress %d' % (rc, rc2, rc3, nlines(pf)))
        dry = os.path.join(T, 'dry_p1')
        rc, out = run(T, ['084', '3320', '--dry-run', dry] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1d')})
        dr = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(dry, 'status', 'P*.json')))]
        case('T34 dry run of all phases in a fresh root: rc 0, 7 records in the dry folder (v0.13: bandlimit N/A on FBS-only), plans '
             'of %d dates, root absent' % n,
             rc == 0 and [r.get('verdict') for r in dr] == ['PASS'] * 7 and (dr[5].get('outputs') or {}).get('na')
             and [r.get('outputs', {}).get('planned') for r in dr[2:5] + dr[6:]] == [n, n, n, n]
             and not os.path.exists(os.path.join(T, 'p1d')),
             'rc %d records %d' % (rc, len(dr)))
        # v0.13: T35 (frame 3350 stopped at extract's G1a.1) is M1 of lp_selftest13p1.py: the mixed frame runs Phase 1 (R6)
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1, envcfg='env_newunpacker.cfg')
        ok = rc == 4 and 'made by unpacker c037bd4e' in out and 'G1b.3' in rec(T, '3320', '1b', 'unpack', P).get('reason', '')
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T36 the pin moved to another unpacker: every SLC made by the old one -> DECISION (G1b.3); pin back -> PASS',
             ok and rc2 == 0, 'rc %d then %d' % (rc, rc2))
        ex = os.path.join(fdir(T, '3320', P), 'unzipped', 'ALPSRP000013320-H1.1__D')
        os.makedirs(ex)
        rc, out = run(T, ['084', '3320'] + V, env_extra=E1)
        ok = rc == 4 and 'not a kept granule' in out and 'record STALE' in out
        aside(T, ex, 'T37')
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E1)
        case('T37 a folder in unzipped/ that is not a kept granule -> extract STALE, DECISION (G1a.3); moved -> PASS',
             ok and rc2 == 0, 'rc %d then %d' % (rc, rc2))
        for tid, root, sig, rcw, what in (('T38', 'p1s', signal.SIGTERM, 143, 'Stopped'),
                                          ('T39', 'p1i', signal.SIGINT, 130, 'KeyboardInterrupt')):
            d2 = R['kept'][2]['date']
            rc, out = stopped_run(T, root, sig, d2)
            u = rec(T, '3320', '1b', 'unpack', root)
            led1 = last_ledger(T, root)
            ok = rc == rcw and u.get('verdict') == 'ERROR' and what in u.get('reason', '') \
                and 'rc=%d stopped in unpack' % rcw in led1
            rc2, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, root)})
            ok2 = rc2 == 4 and 'G1b.3' in rec(T, '3320', '1b', 'unpack', root).get('reason', '')
            aside(T, os.path.join(fdir(T, '3320', root), 'SLC', d2), tid)
            rc3, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, root)})
            case('%s %s during unpack -> record ERROR (not RUNNING), ledger rc %d; its date DECISION; moved -> PASS'
                 % (tid, 'SIGTERM' if sig == signal.SIGTERM else 'Ctrl-C (SIGINT)', rcw),
                 ok and ok2 and rc3 == 0, 'rc %d (%s; %s), %d, %d' % (rc, u.get('verdict'), led1[22:], rc2, rc3))
    try:
        if want('1'):
            phase1()
    except Exception as e:  # noqa: BLE001
        case('Phase 1 cases stopped early by %s: %s' % (type(e).__name__, e), False)

    def verdicts2(root):
        return [rec(T, '3320', i, ph, root).get('verdict') for i, ph in (('2a', 'stack1'), ('2b', 'reference'), ('2c', 'stack2'))]

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def flist(root):
        """(path, size, mtime) of every folder, file and link in frame 3320: a listing to show that a run left it as it was."""
        w = fdir(T, '3320', root)
        out = [('.', 0, os.lstat(w).st_mtime_ns)]
        for dp, dn, fn in os.walk(w):
            for n in sorted(dn) + sorted(fn):
                q = os.path.join(dp, n)
                st = os.lstat(q)
                out.append((os.path.relpath(q, w), 0 if n in dn else st.st_size, st.st_mtime_ns))
        return sorted(out)

    def phase1r():
        print('-- Phase 1br (rwin): each shelve\'s r0 from its CEOS image records (F26, F27), every run --to verify')
        V = ['--to', 'verify']
        rw = os.path.join(T, 'archive_rw')
        plant = {ORBITS[1]: dict(r1_off_m=-GATE), ORBITS[6]: dict(r1_off_m=-GATE), ORBITS[20]: dict(r1_off_m=GATE)}
        for orb in ORBITS:
            mkzip(rw, orb, '3320', **plant.get(orb, {}))
        A, B, Cd = (date_of(o) for o in (ORBITS[1], ORBITS[6], ORBITS[20]))
        E = {'LINOG_ROOT': os.path.join(T, 'p1r'), 'LINOG_ARCHIVE': rw}
        W = fdir(T, '3320', 'p1r')
        rc, out = run(T, ['084', '3320'] + V, env_extra=E)
        r = rec(T, '3320', '1br', 'rwin', 'p1r')
        o = r.get('outputs', {})
        pos = dict((x['date'], x.get('grid_pos')) for x in modes(T, '3320', 'p1r')[0].get('dates', []))
        bk = os.path.join(W, o.get('backup') or 'no-backup-on-record')
        bm = os.path.join(bk, 'backup.md5')
        bl = open(bm).read().splitlines() if os.path.isfile(bm) else []
        before = dict((x['date'], x.get('shelf_md5_before') or {}) for x in o.get('dates', []))
        okb = len(bl) == 9 and all(before.get(d) for d in (A, B, Cd)) and all(
            os.path.isfile(os.path.join(bk, 'SLC', d, n)) and md5(os.path.join(bk, 'SLC', d, n)) == m
            for d in (A, B, Cd) for n, m in before[d].items())
        g = gates(r)
        case('T84 three dates planted (the records one gate nearer than the leader on two, one gate farther on one): rwin PASS, '
             'those 3 changed after their shelves were copied (9 files, md5 equal); verify PASS, positions -6, -6, -4, the other 21 -5',
             rc == 0 and r.get('verdict') == 'PASS' and sorted(o.get('change', [])) == sorted([A, B, Cd]) and okb
             and all(g.get('G1br.%d' % i) == 'PASS' for i in range(1, 9)) and verdicts(T, '3320', 'p1r') == ['PASS'] * 7
             and [pos.get(A), pos.get(B), pos.get(Cd)] == [-6, -6, -4] and len(pos) == 24
             and sorted(set(v for d, v in pos.items() if d not in (A, B, Cd))) == [-5],
             'rc %d; rwin %s, change %s, k %s; backup %d lines, md5s %s; positions %s' % (
                 rc, r.get('verdict'), o.get('change'), o.get('k_census'), len(bl), okb, [pos.get(A), pos.get(B), pos.get(Cd)]))
        rc, out = run(T, ['084', '3320'] + V, env_extra=E)
        case('T85 re-run: all 7 phases skipped (the shelves as rwin left them; v0.13: bandlimit among them)',
             rc == 0 and out.count('skip: PASS on record') == 7,
             'rc %d skips %d' % (rc, out.count('skip: PASS on record')))
        sd = os.path.join(W, 'SLC', A)
        for f in sorted(glob.glob(os.path.join(sd, 'data*'))):
            aside(T, f, 'T86_%s' % A)
        for f in sorted(os.listdir(os.path.join(bk, 'SLC', A))) if os.path.isdir(os.path.join(bk, 'SLC', A)) else []:
            shutil.copy2(os.path.join(bk, 'SLC', A, f), os.path.join(sd, f))
        rc, out = run(T, ['084', '3320'] + V, env_extra=E)
        r2 = rec(T, '3320', '1br', 'rwin', 'p1r')
        o2 = r2.get('outputs', {})
        pos2 = dict((x['date'], x.get('grid_pos')) for x in modes(T, '3320', 'p1r')[0].get('dates', []))
        case('T86 the first date\'s shelve put back from its copy: rwin STALE, changes it again into a second copy (the others '
             'already); verify re-runs, PASS, the date at -6 again',
             rc == 0 and 'P1br rwin: record STALE' in out and o2.get('change') == [A] and sorted(o2.get('already', [])) == sorted([B, Cd])
             and o2.get('backup') not in (None, o.get('backup')) and o.get('backup') in o2.get('backups_before', [])
             and 'P1c verify: record STALE' in out and pos2.get(A) == -6,
             'rc %d; change %s, already %s, backup %s; position %s' % (rc, o2.get('change'), o2.get('already'), o2.get('backup'), pos2.get(A)))
        bk2 = os.path.join(W, o2.get('backup') or 'no-backup-on-record')
        for f in sorted(glob.glob(os.path.join(sd, 'data*'))):
            aside(T, f, 'T94_%s' % A)
        for f in sorted(os.listdir(os.path.join(bk2, 'SLC', A))) if os.path.isdir(os.path.join(bk2, 'SLC', A)) else []:
            shutil.copy2(os.path.join(bk2, 'SLC', A, f), os.path.join(sd, f))
        rc, out1 = run(T, ['084', '3320', '--only', 'verify'], env_extra=E)
        v = rec(T, '3320', '1c', 'verify', 'p1r')
        g1 = [x for x in v.get('gates', []) if x['id'] == 'G1c.1']
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E)
        case('T94 a shelve put back from its copy, then --only verify: verify FAIL at G1c.1 (the shelves are not as rwin left '
             'them, naming the date), nothing else run; a full run: rwin corrects it, verify PASS',
             rc == 2 and g1 and g1[0]['verdict'] == 'FAIL' and A in g1[0]['value'] and 'not as rwin left them' in g1[0]['value']
             and '-- P1br' not in out1 and 'P1br rwin: record STALE' in out and rc2 == 0 and verdicts(T, '3320', 'p1r') == ['PASS'] * 7,
             'rc %d (%s), then %d' % (rc, g1[0]['value'] if g1 else '-', rc2))

        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1o'), 'LINOG_MOCK_R0OFF': '1'})
        r = rec(T, '3320', '1br', 'rwin', 'p1o')
        W7 = fdir(T, '3320', 'p1o')
        g = dict((x['id'], x) for x in r.get('gates', []))
        case('T87 the unpacker\'s r0 50 m beyond the leader\'s (LINOG_MOCK_R0OFF): rwin FAIL at G1br.4 on every date, nothing '
             'written (no copy), verify not run',
             rc == 2 and g.get('G1br.4', {}).get('verdict') == 'FAIL' and g.get('G1br.4', {}).get('value', '').startswith('0 of ')
             and 'G1br.6' not in g and not os.path.exists(os.path.join(W7, '_archive')) and not rec(T, '3320', '1c', 'verify', 'p1o'),
             'rc %d; G1br.4 %s' % (rc, g.get('G1br.4', {}).get('value')))

        bad = os.path.join(T, 'archive_rwbad')
        # v0.13 (9.5): the blank descriptor record length (ORBITS[18]) no longer rides in the archive's zip, where recon's G0.16
        # meets it first (step 2: the middle record cannot be read by offset; T89c); T89b plants it in the extracted copy instead
        pb = {ORBITS[3]: dict(r1_off_m=60.0), ORBITS[9]: dict(last_r1_off_m=-GATE), ORBITS[12]: dict(left=32, r1_off_m=-GATE),
              ORBITS[15]: dict(r1_off_m=-2 * GATE)}
        for orb in ORBITS:
            mkzip(bad, orb, '3320', **pb.get(orb, {}))
        X, Y, Z, K2, F = (date_of(ORBITS[i]) for i in (3, 9, 12, 15, 18))
        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1x'), 'LINOG_ARCHIVE': bad})
        r = rec(T, '3320', '1br', 'rwin', 'p1x')
        g = dict((x['id'], x) for x in r.get('gates', []))
        nothing = not os.path.exists(os.path.join(fdir(T, '3320', 'p1x'), '_archive'))
        n5 = [ln.split(':')[0] for ln in g.get('G1br.5', {}).get('note', '').splitlines()]
        n3 = [ln.split(':')[0] for ln in g.get('G1br.3', {}).get('note', '').splitlines()]
        case('T88 one date\'s records 60 m from its leader (not whole gates), another two gates nearer (never measured): rwin FAIL '
             'at G1br.5 naming only those two; nothing written',
             rc == 2 and g.get('G1br.5', {}).get('verdict') == 'FAIL' and n5 == [X, K2] and nothing and 'G1br.6' not in g,
             'rc %d; G1br.5 %s' % (rc, n5))
        case('T89 (same run) a last image record one gate from the first, 32 fill samples (never seen on felix): rwin FAIL at G1br.3 '
             'naming only those two', rc == 2 and g.get('G1br.3', {}).get('verdict') == 'FAIL' and n3 == [Y, Z] and nothing,
             'G1br.3 %s' % n3)
        stem = 'ALPSRP%05d3320-H1.1__D' % ORBITS[18]
        img = glob.glob(os.path.join(fdir(T, '3320', 'p1x'), 'unzipped', stem, 'IMG-HH-*'))
        if img:
            with open(img[0], 'r+b') as fh:
                fh.seek(186)
                fh.write(b' ' * 6)
        rc, out = run(T, ['084', '3320', '--only', 'rwin', '--force', 'rwin'], env_extra={'LINOG_ROOT': os.path.join(T, 'p1x'),
                                                                                           'LINOG_ARCHIVE': bad})
        r = rec(T, '3320', '1br', 'rwin', 'p1x')
        g = dict((x['id'], x) for x in r.get('gates', []))
        n3 = [ln.split(':')[0] for ln in g.get('G1br.3', {}).get('note', '').splitlines()]
        case('T89b v0.13: the file descriptor\'s record length blanked in the extracted copy (unzipped/), --only rwin: rwin FAIL at '
             'G1br.3 naming those three (v0.12\'s T89), nothing written',
             bool(img) and rc == 2 and g.get('G1br.3', {}).get('verdict') == 'FAIL' and n3 == [Y, Z, F]
             and not os.path.exists(os.path.join(fdir(T, '3320', 'p1x'), '_archive')), 'rc %d; G1br.3 %s' % (rc, n3))
        bb = os.path.join(T, 'archive_rwfdr')
        for orb in ORBITS:
            mkzip(bb, orb, '3320', fdr_blank_rl=(orb == ORBITS[18]))
        rc, out = run(T, ['084', '3320'] + V, env_extra={'LINOG_ROOT': os.path.join(T, 'p1xf'), 'LINOG_ARCHIVE': bb})
        r = rec(T, '3320', '0a', 'recon', 'p1xf')
        g = dict((x['id'], x) for x in r.get('gates', []))
        case('T89c v0.13: the blank record length in the archive\'s zip: recon DECISION at G0.16 step 2 naming that granule (its middle '
             'record cannot be read by offset), Phase 1 not run',
             rc == 4 and g.get('G0.16', {}).get('verdict') == 'DECISION' and g.get('G0.16', {}).get('value', '').startswith('step 2')
             and stem in g.get('G0.16', {}).get('note', '') and not rec(T, '3320', '1a', 'extract', 'p1xf'),
             'rc %d; G0.16 %s' % (rc, g.get('G0.16', {}).get('value', '')[:60]))

        E9 = {'LINOG_ROOT': os.path.join(T, 'p1rs'), 'LINOG_ARCHIVE': rw}
        rc0, out = run(T, ['084', '3320', '--to', 'unpack'], env_extra=E9)
        L0 = flist('p1rs')
        dry = os.path.join(T, 'dry_rw')
        rc, out = run(T, ['084', '3320', '--dry-run', dry, '--to', 'rwin'], env_extra=E9)
        f = os.path.join(dry, 'status', 'P1br_rwin.json')
        dr = json.load(open(f)) if os.path.exists(f) else {}
        do = dr.get('outputs', {})
        case('T91 dry run after unpack: rwin reads the frame\'s records and shelves and plans the 3 changes; nothing written, the '
             'frame as it was', rc0 == 0 and rc == 0 and dr.get('verdict') == 'PASS' and do.get('planned') == 3 and do.get('read') is True
             and sorted(do.get('change', [])) == sorted([A, B, Cd]) and flist('p1rs') == L0,
             'rc %d, %d; %s planned %s, change %s; frame unchanged %s' % (rc0, rc, dr.get('verdict'), do.get('planned'),
                                                                          do.get('change'), flist('p1rs') == L0))
        mark = os.path.join(T, 'mark_T90')
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_MOCK_RWIN_PAUSE=B, LINOG_MOCK_MARK=mark, **E9)
        p = subprocess.Popen(['bash', ENTRY, '084', '3320', '--to', 'verify'], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
        t0 = time.time()
        while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 120:
            time.sleep(0.2)
        time.sleep(0.5)
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGTERM)
        out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 3320 --to verify  (p1rs, LINOG_MOCK_RWIN_PAUSE=%s, SIGTERM after %.1f s)  rc %d\n%s'
                     % (B, time.time() - t0, p.returncode, out))
        r = rec(T, '3320', '1br', 'rwin', 'p1rs')
        led1 = last_ledger(T, 'p1rs')
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E9)
        o2 = rec(T, '3320', '1br', 'rwin', 'p1rs').get('outputs', {})
        case('T90 SIGTERM while rwin waits before its second write: rc 143, rwin ERROR, its record names the one date written; the '
             'next run: that date already, the other two changed into a second copy, verify PASS',
             p.returncode == 143 and r.get('verdict') == 'ERROR' and 'Stopped' in r.get('reason', '')
             and r.get('outputs', {}).get('written') == [A] and 'rc=143 stopped in rwin' in led1 and rc2 == 0
             and o2.get('already') == [A] and sorted(o2.get('change', [])) == sorted([B, Cd]) and len(o2.get('backups_before', [])) == 1
             and verdicts(T, '3320', 'p1rs') == ['PASS'] * 7,
             'rc %s (%s, written %s; %s), then %d: already %s, change %s' % (p.returncode, r.get('verdict'),
                                                                            r.get('outputs', {}).get('written'), led1[22:], rc2,
                                                                            o2.get('already'), o2.get('change')))
        E5 = {'LINOG_ROOT': os.path.join(T, 'p1rt'), 'LINOG_ARCHIVE': rw}
        rc0, out = run(T, ['084', '3320', '--to', 'unpack'], env_extra=E5)
        mark = os.path.join(T, 'mark_T95')
        env5 = dict(env, LINOG_MOCK_RWIN_HOLD=A, LINOG_MOCK_THREAD='1', LINOG_MOCK_MARK=mark, **E5)
        env5.pop('LINOG_MOCK_RWIN_PAUSE', None)
        p = subprocess.Popen(['bash', ENTRY, '084', '3320', '--to', 'verify'], env=env5, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
        t0 = time.time()
        while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 120:
            time.sleep(0.2)
        time.sleep(0.5)
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGTERM)
        out = p.communicate(timeout=180)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 3320 --to verify  (p1rt, LINOG_MOCK_RWIN_HOLD=%s, LINOG_MOCK_THREAD=1, SIGTERM after '
                     '%.1f s)  rc %d\n%s' % (A, time.time() - t0, p.returncode, out))
        r = rec(T, '3320', '1br', 'rwin', 'p1rt')
        ro = r.get('outputs', {})
        sdA = os.path.join(fdir(T, '3320', 'p1rt'), 'SLC', A)
        nowA = dict((n, md5(os.path.join(sdA, n))) for n in ('data', 'data.dat', 'data.dir', 'data.bak', 'data.db')
                    if os.path.isfile(os.path.join(sdA, n)))
        rc2, out = run(T, ['084', '3320'] + V, env_extra=E5)
        r2 = rec(T, '3320', '1br', 'rwin', 'p1rt')
        o5 = r2.get('outputs', {})
        g8 = [x for x in r2.get('gates', []) if x['id'] == 'G1br.8']
        case('T95 SIGTERM while rwin holds a write, with a second thread in the process (as numpy\'s on felix): the write, its '
             'read-back and its record finish first (written, its md5s = the shelve, nothing being written); rc 143; the next '
             'run: that date already, compared with its copy, the other two changed',
             rc0 == 0 and p.returncode == 143 and r.get('verdict') == 'ERROR' and 'Stopped' in r.get('reason', '')
             and ro.get('written') == [A] and ro.get('writing') is None and (ro.get('written_md5') or {}).get(A) == nowA
             and (ro.get('read_back') or {}).get(A, [0, False])[1] is True and rc2 == 0 and o5.get('already') == [A]
             and sorted(o5.get('change', [])) == sorted([B, Cd]) and g8 and g8[0]['verdict'] == 'PASS' and '(1 compared' in g8[0]['value'],
             'rc %s (%s, written %s, writing %s, md5 on record = shelve: %s), then %d: already %s, change %s, G1br.8 %s' % (
                 p.returncode, r.get('verdict'), ro.get('written'), ro.get('writing'), (ro.get('written_md5') or {}).get(A) == nowA,
                 rc2, o5.get('already'), o5.get('change'), g8[0]['value'] if g8 else '-'))
    try:
        if want('1r'):
            phase1r()
    except Exception as e:  # noqa: BLE001
        import traceback
        case('rwin cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
    if want('13p1'):   # v0.13 Phase 1: FBS+FBD and FBD-only frames, bandlimit, G4, G1c.8, the env's prefix (lp_selftest13p1.py)
        import lp_selftest13p1
        try:
            lp_selftest13p1.phase13_1(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 Phase 1 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13p2'):   # v0.13 Phase 2 and topo: D1 among FBS dates, D1c, D1f, the FBD-only looks, G3a.14 (lp_selftest13p2.py;
        # without a numpy Python its own case FAILs, the part 3 review's P3-10)
        import lp_selftest13p2
        try:
            lp_selftest13p2.phase13_2(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 Phase 2 and topo cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13p4'):   # v0.13 Phases 3 and 4: R9, G10 v3, G10m, G3b.12, igram's classes and G17 on full-height frames (lp_selftest13p4.py)
        import lp_selftest13p4
        try:
            lp_selftest13p4.phase13_4(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 Phase 3 and 4 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13p5'):   # v0.13 R7, coarse's D2 loop: the take, the restart, the reuse rule, the limits (lp_selftest13p5.py)
        import lp_selftest13p5
        try:
            lp_selftest13p5.phase13_5(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 R7 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13p6'):   # v0.13 part 6's subset for the first install: accept under R9, the FBD-only factor, the package prefix
        import lp_selftest13p6
        try:
            lp_selftest13p6.phase13_6(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 part 6 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13r2a'):   # v0.13 r2 (brief A): drop1's split rule, balanced, its guard and D1d (lp_selftest13r2a.py)
        import lp_selftest13r2a
        try:
            lp_selftest13r2a.phase13_r2a(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 r2 drop1 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13r2b'):   # v0.13 r2 deliver: G6a.11, the mode step (DB1), RUN_MANIFEST.json's new fields, the mock MintPy's table
        import lp_selftest13r2b
        try:
            lp_selftest13r2b.phase13_r2b(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 r2 deliver cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])
    if want('13r2c'):   # v0.13 r2, part C: the part 6 review's items, an ascending frame through package, 25-b's .xml width helper
        import lp_selftest13r2c
        try:
            lp_selftest13r2c.phase13_r2c(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.13 r2 part C cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-800:])

    def phase2():
        print('-- Phase 2 (stack1, reference, stack2): the real stack code in the mock ISCE environment, felix\'s baselines')
        spins = {}
        for ln in open(os.path.join(HERE, 'linog_stack.cfg')):
            ln = ln.strip()
            if ln and not ln.startswith('#') and '=' in ln:
                spins[ln.split('=', 1)[0].strip()] = ln.split('=', 1)[1].strip()
        kit2 = (('mock_stack/stackStripMap.py', 'STACKSTRIPMAP_MD5'), ('mock_stack/Stack.py', 'STACK_PY_MD5'),
                ('linog_net_table.py', 'KIT_NET_TABLE_MD5'))
        same = [n for n, k in kit2 if md5(os.path.join(KITSRC, n)) == spins.get(k)]
        case('T41 the self-test runs the stack code felix pins (md5s = linog_stack.cfg), on a Python with numpy and matplotlib',
             len(same) == 3 and bool(mockpy), '%d of 3; python %s (tried %s)' % (len(same), mockpy, ', '.join(tried)))
        if not mockpy:
            case('T42-T62 not run: stackStripMap.py needs numpy and matplotlib, and neither Python tried has both', False)
            return
        def run2(args, env_extra=None):
            """Phase 2 runs read archive_p2 (felix's 24 dates of frame 3320) through paths_p2.cfg."""
            return run(T, args, cfg='paths_p2.cfg', env_extra=env_extra)
        P = 'p2'
        E1 = {'LINOG_ROOT': os.path.join(T, P)}
        W1 = fdir(T, '3320', P)
        rc, out = run2(['084', '3320'], env_extra=E1)
        s1, rr = rec(T, '3320', '2a', 'stack1', P), rec(T, '3320', '2b', 'reference', P)
        o1, pk = s1.get('outputs', {}), rr.get('outputs', {}).get('picks', {})
        case('T42 Phase 2, ask mode: stack1 PASS (157 pairs, 408 configs in stack/pass1.v1, thin 20061125); reference DECISION '
             'with the three picks; no stack2, no configs/ in the frame',
             rc == 4 and s1.get('verdict') == 'PASS' and o1.get('pairs') == 157 and o1.get('configs') == 408
             and os.path.basename(o1.get('pass_dir', '')) == 'pass1.v1' and o1.get('thin') == ['20061125']
             and rr.get('verdict') == 'DECISION' and pk == dict(d1='20090602', midpoint_alone='20090302', kit_first='20090602')
             and not rec(T, '3320', '2c', 'stack2', P) and not os.path.exists(os.path.join(W1, 'configs'))
             and not os.path.exists(os.path.join(W1, 'recon', 'reference.json')),
             'rc %d; stack1 %s, %s pairs, %s configs, thin %s; reference %s, picks %s' % (
                 rc, s1.get('verdict'), o1.get('pairs'), o1.get('configs'), o1.get('thin'), rr.get('verdict'), pk))
        rt = os.path.join(W1, 'recon', 'reference.txt')
        good = '# P084 F3320 reference (selftest)\n20090602  D1 pick, confirmed (selftest T43)\n'
        with open(rt, 'w') as fh:
            fh.write(good)
        rc, out = run2(['084', '3320'], env_extra=E1)
        rr, s2 = rec(T, '3320', '2b', 'reference', P), rec(T, '3320', '2c', 'stack2', P)
        o2 = s2.get('outputs', {})
        cr = os.path.join(W1, 'configs', 'config_reference_20090602')
        led = open(os.path.join(W1, 'logs', 'STATUS.txt')).read()
        case('T43 reference.txt names 20090602: reference PASS (operator), stack2 PASS: 408 configs, 16 run files, '
             '23 baselines 20090602_*, config_reference 14 lines + .bak_watermask 21',
             rc == 0 and rr.get('verdict') == 'PASS' and rr.get('outputs', {}).get('decided_by') == 'operator'
             and s2.get('verdict') == 'PASS' and o2.get('configs') == 408 and o2.get('run_files') == 16
             and len(o2.get('baselines', [])) == 23 and all(b.startswith('20090602_') for b in o2.get('baselines', []))
             and nlines(cr) == 14 and nlines(cr + '.bak_watermask') == 21 and 'auto_stack2 END rc=0' in led,
             'rc %d; reference %s (%s); stack2 %s, configs %s, baselines %d; config_reference %d lines, backup %d' % (
                 rc, rr.get('verdict'), rr.get('outputs', {}).get('decided_by'), s2.get('verdict'), o2.get('configs'),
                 len(o2.get('baselines', [])), nlines(cr), nlines(cr + '.bak_watermask')))
        rc, out = run2(['084', '3320'], env_extra=E1)
        case('T44 re-run: all 10 phases skipped (v0.13: bandlimit among them)', rc == 0 and out.count('skip: PASS on record') == 10,
             'rc %d skips %d' % (rc, out.count('skip: PASS on record')))
        with open(rt, 'w') as fh:
            fh.write('20061010  the earliest date (selftest T45)\n')
        rc, out = run2(['084', '3320'], env_extra=E1)
        ok = rc == 2 and 'earliest' in rec(T, '3320', '2b', 'reference', P).get('reason', '')
        with open(rt, 'w') as fh:
            fh.write(good)
        rc2, out = run2(['084', '3320'], env_extra=E1)
        case('T45 reference.txt names the earliest date -> reference FAIL (N23); restored -> PASS, stack2 skipped (same date, same network)',
             ok and rc2 == 0 and 'P2c stack2: record CURRENT' in out, 'rc %d then %d' % (rc, rc2))
        with open(rt, 'w') as fh:
            fh.write('20000101  not a date of the stack (selftest T46)\n')
        rc, out = run2(['084', '3320'], env_extra=E1)
        ok1 = rc == 2 and 'not a date of this stack' in rec(T, '3320', '2b', 'reference', P).get('reason', '')
        with open(rt, 'w') as fh:
            fh.write('the reference is 20090602\n')
        rc2, out = run2(['084', '3320'], env_extra=E1)
        ok2 = rc2 == 2 and 'must read' in rec(T, '3320', '2b', 'reference', P).get('reason', '')
        with open(rt, 'w') as fh:
            fh.write(good)
        rc3, out = run2(['084', '3320'], env_extra=E1)
        case('T46 reference.txt with a date outside the stack, then a line without a date -> FAIL twice; restored -> PASS',
             ok1 and ok2 and rc3 == 0, 'rc %d, %d, %d' % (rc, rc2, rc3))
        with open(os.path.join(W1, 'run_files', 'run_08_igram.log'), 'w') as fh:
            fh.write('a later phase\'s log beside the run files (selftest T55)\n')
        rc, out = run2(['084', '3320'], env_extra=E1)
        n_skip = out.count('skip: PASS on record')
        cfg1 = sorted(glob.glob(os.path.join(W1, 'configs', 'config_igram_*')))[0]
        with open(cfg1, 'a') as fh:
            fh.write('# edited by hand (selftest T55)\n')
        rc2, out = run2(['084', '3320'], env_extra=E1)
        ok = rc == 0 and n_skip == 10 and rc2 == 4 and 'P2c stack2: record STALE' in out \
            and 'G2c.5' in rec(T, '3320', '2c', 'stack2', P).get('reason', '')
        for n in ('configs', 'run_files', 'baselines', 'pairs.pdf'):
            aside(T, os.path.join(W1, n), 'T55')
        rc3, out = run2(['084', '3320'], env_extra=E1)
        case('T55 a new file beside the run files -> all 9 skipped; a config edited by hand -> stack2 STALE, DECISION (G2c.5); '
             'moved to _archive -> PASS', ok and rc3 == 0 and rec(T, '3320', '2c', 'stack2', P).get('verdict') == 'PASS',
             'rc %d (skips %d), %d, %d' % (rc, n_skip, rc2, rc3))
        E3 = {'LINOG_ROOT': os.path.join(T, 'p2a')}
        rc, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        ra = rec(T, '3320', '2b', 'reference', 'p2a')
        case('T47 a fresh frame, --decide auto: 9 phases PASS; reference by D1 20090602, D1b WARN (the midpoint alone 20090302)',
             rc == 0 and verdicts(T, '3320', 'p2a') == ['PASS'] * 7 and verdicts2('p2a') == ['PASS'] * 3
             and ra.get('outputs', {}).get('reference') == '20090602' and ra.get('outputs', {}).get('decided_by') == 'rule'
             and gates(ra).get('D1b') == 'WARN', 'rc %d; %s; reference %s by %s; D1b %s' % (
                 rc, verdicts2('p2a'), ra.get('outputs', {}).get('reference'), ra.get('outputs', {}).get('decided_by'),
                 gates(ra).get('D1b')))
        W3 = fdir(T, '3320', 'p2a')
        S48 = sorted(os.listdir(os.path.join(W3, 'stack')))
        bad = os.path.join(T, 'cfg', 'stack_badpin.cfg')
        with open(bad, 'w') as fh:
            fh.write(open(os.path.join(T, 'cfg', 'stack_mock.cfg')).read().replace(spins['STACKSTRIPMAP_MD5'], '0' * 32))
        rc, out = run2(['084', '3320', '--only', 'stack1', '--force', 'stack1', '--decide', 'auto'],
                      env_extra=dict(E3, LINOG_STACK_CFG=bad))
        ok = rc == 2 and 'G2a.3' in rec(T, '3320', '2a', 'stack1', 'p2a').get('reason', '') \
            and sorted(os.listdir(os.path.join(W3, 'stack'))) == S48
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T48 stackStripMap.py off its pin -> stack1 FAIL (G2a.3), no new pass folder; pin back -> PASS, reference and stack2 skipped',
             ok and rc2 == 0 and 'P2b reference: record CURRENT' in out and 'P2c stack2: record CURRENT' in out,
             'rc %d then %d' % (rc, rc2))
        rc, out = run2(['084', '3320', '--force', 'stack1', '--decide', 'auto'],
                      env_extra=dict(E3, LINOG_MOCK_BPERP='20110308:9000'))
        x = rec(T, '3320', '2a', 'stack1', 'p2a')
        ok = rc == 4 and x.get('verdict') == 'DECISION' and 'not connected' in x.get('reason', '')
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T49 20110308 moved 9 km off the tube -> stackStripMap: network not connected -> stack1 DECISION (G2a.5); unplanted -> PASS',
             ok and rc2 == 0, 'rc %d (%s) then %d' % (rc, x.get('verdict'), rc2))
        n_cf = nsub(T, '3320', 'configs', 'p2a')
        rc, out = run2(['084', '3320', '--force', 'stack2', '--decide', 'auto'], env_extra=E3)
        ok = rc == 4 and 'G2c.5' in rec(T, '3320', '2c', 'stack2', 'p2a').get('reason', '') and nsub(T, '3320', 'configs', 'p2a') == n_cf
        for n in ('configs', 'run_files', 'baselines', 'pairs.pdf'):
            aside(T, os.path.join(W3, n), 'T50')
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T50 --force stack2 over its own configs/ -> DECISION (G2c.5), nothing touched; moved to _archive -> PASS again',
             ok and rc2 == 0 and nsub(T, '3320', 'configs', 'p2a') == n_cf, 'rc %d then %d; configs %d then %d' % (
                 rc, rc2, n_cf, nsub(T, '3320', 'configs', 'p2a')))
        vrt = os.path.join(W3, 'SLC', '20090602', '20090602.slc.vrt')
        v0 = open(vrt).read()
        with open(vrt, 'w') as fh:
            fh.write(v0.replace('rasterXSize="9344"', 'rasterXSize="9000"'))
        rc, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        g = rec(T, '3320', '2b', 'reference', 'p2a')
        ok = rc == 2 and 'G17' in g.get('reason', '') and verdicts(T, '3320', 'p2a') == ['PASS'] * 7
        with open(vrt, 'w') as fh:
            fh.write(v0)
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T51 the reference .slc.vrt 9000 wide -> verify and stack1 re-run and PASS, reference FAIL (G17); restored -> PASS, stack2 skipped',
             ok and rc2 == 0 and 'P2c stack2: record CURRENT' in out, 'rc %d (%s) then %d' % (rc, g.get('verdict'), rc2))
        L0 = flist('p2a')
        dry = os.path.join(T, 'dry_p2')
        rc, out = run2(['084', '3320', '--dry-run', dry], env_extra=E3)
        dr = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(dry, 'status', 'P*.json')))]
        rj = os.path.join(dry, 'recon', 'reference.json')
        J = json.load(open(rj)) if os.path.exists(rj) else {}
        case('T52 dry run through stack2 on the frame (no reference.txt, ask): 10 records PASS (v0.13: bandlimit\'s), pass 1 and pass 2 '
             'in the dry folder, reference 20090602 by the rule (dry run), D1 INFO; the frame left as it was',
             rc == 0 and [r.get('verdict') for r in dr] == ['PASS'] * 10
             and os.path.isdir(os.path.join(dry, 'stack', 'pass1.v1')) and os.path.isdir(os.path.join(dry, 'stack', 'pass2.v1'))
             and J.get('reference') == '20090602' and J.get('decided_by') == 'rule (dry run)'
             and gates(dr[-2] if len(dr) > 1 else {}).get('D1') == 'INFO' and flist('p2a') == L0,
             'rc %d; records %s; reference %s (%s); frame unchanged %s' % (
                 rc, [r.get('verdict') for r in dr], J.get('reference'), J.get('decided_by'), flist('p2a') == L0))
        S0 = sorted(os.listdir(os.path.join(W3, 'stack')))
        rc, out = run2(['084', '3320', '--decide', 'maybe'], env_extra=E3)
        case('T53 --decide maybe -> rc 3, nothing run', rc == 3 and 'ask or auto' in out, 'rc %d' % rc)
        fd = os.open(os.path.join(W3, 'status', '.lock'), os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)      # held by this process, released below
        L1 = flist('p2a')
        try:
            rc, out = run2(['084', '3320', '--dry-run', os.path.join(T, 'dry_p2_locked')], env_extra=E3)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        case('T62 a dry run while another run holds the frame\'s lock -> rc 4, nothing run, the frame as it was',
             rc == 4 and 'holds' in out and not os.path.exists(os.path.join(T, 'dry_p2_locked')) and flist('p2a') == L1, 'rc %d' % rc)
        rc, out = run2(['084', '3320', '--force', 'stack1', '--decide', 'auto'],
                       env_extra=dict(E3, LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_otherprefix.cfg')))
        x = rec(T, '3320', '2a', 'stack1', 'p2a')
        ok = rc == 3 and x.get('verdict') == 'ERROR' and 'ENV_PREFIX' in json.dumps(x.get('gates', [])) \
            and sorted(os.listdir(os.path.join(W3, 'stack'))) == S0
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T54 ENV_PREFIX not the activated env\'s CONDA_PREFIX -> stack1 ERROR (G2a.2), no pass folder; back -> PASS',
             ok and rc2 == 0, 'rc %d (%s) then %d' % (rc, x.get('verdict'), rc2))
        rc, out = run2(['084', '3320'], env_extra=E3)
        case('T56 a frame decided by the rule (--decide auto), run again in ask mode: all 10 phases skipped (v0.13: bandlimit)',
             rc == 0 and out.count('skip: PASS on record') == 10, 'rc %d skips %d' % (rc, out.count('skip: PASS on record')))
        cm = os.path.join(T, 'cfg', 'stack_comment.cfg')
        with open(cm, 'w') as fh:
            fh.write(open(os.path.join(T, 'cfg', 'stack_mock.cfg')).read() + '# a comment added (selftest T57)\n')
        rc, out = run2(['084', '3320', '--decide', 'auto'], env_extra=dict(E3, LINOG_STACK_CFG=cm))
        case('T57 a comment added to linog_stack.cfg: all 10 phases skipped (the fingerprints hold the values, not the file; v0.13: bandlimit)',
             rc == 0 and out.count('skip: PASS on record') == 10, 'rc %d skips %d' % (rc, out.count('skip: PASS on record')))
        sd = os.path.join(W3, 'SLC', '20090602')
        extra = [os.path.join(sd, 'data.rsc'), os.path.join(sd, '20090602.slc.vrt.aux.xml')]
        for f in extra:
            with open(f, 'w') as fh:
                fh.write('written beside the reference SLC by the self-test (T92)\n')
        rc, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T92 MintPy\'s data.rsc and a GDAL .aux.xml beside the reference SLC (F21): all 10 phases skipped (v0.13: bandlimit)',
             rc == 0 and out.count('skip: PASS on record') == 10, 'rc %d skips %d' % (rc, out.count('skip: PASS on record')))
        for f in extra:
            aside(T, f, 'T92')
        rc, out = run2(['084', '3320', '--force', 'stack1', '--decide', 'auto'], env_extra=dict(E3, LINOG_MOCK_BASEFAIL='1'))
        x = rec(T, '3320', '2a', 'stack1', 'p2a')
        ok = rc == 2 and 'G2a.5' in x.get('reason', '')
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T58 the baseline computation fails -> stack1 FAIL (G2a.5); unplanted -> PASS, reference and stack2 skipped (same network)',
             ok and rc2 == 0 and 'P2b reference: record CURRENT' in out and 'P2c stack2: record CURRENT' in out,
             'rc %d (%s) then %d' % (rc, x.get('verdict'), rc2))
        for n in ('configs', 'run_files', 'baselines', 'pairs.pdf'):
            aside(T, os.path.join(W3, n), 'T59')
        rc, out = run2(['084', '3320', '--decide', 'auto'],
                       env_extra=dict(E3, LINOG_MOCK_SHIFT='20101206:-30', LINOG_MOCK_SHIFT_REF='20090602'))
        x = rec(T, '3320', '2c', 'stack2', 'p2a')
        cf59 = nsub(T, '3320', 'configs', 'p2a') != -1
        ok = rc == 2 and 'G2c.7' in x.get('reason', '') and not cf59 \
            and '20091018_20101206 in pass 2 only' in json.dumps(x.get('gates', []))
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T59 pass 2 finds a pair 7 m inside -b that pass 1 had 23 m outside -> stack2 FAIL (G2c.7) in the trial, the frame '
             'without configs/; unplanted -> PASS', ok and rc2 == 0 and rec(T, '3320', '2c', 'stack2', 'p2a').get('verdict') == 'PASS',
             'rc %d (%s, configs/ in the frame: %s) then %d' % (rc, x.get('verdict'), cf59, rc2))
        for n in ('configs', 'run_files', 'baselines', 'pairs.pdf'):
            aside(T, os.path.join(W3, n), 'T61')
        mark = os.path.join(T, 'mark_T61')
        rc, out = stopped_run2(T, 'p2a', dict(LINOG_MOCK_BASESLEEP='5'), mark)
        x = rec(T, '3320', '2c', 'stack2', 'p2a')
        ok = rc == 143 and x.get('verdict') == 'ERROR' and os.path.isdir(os.path.join(W3, 'baselines'))
        rc2, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        ok2 = rc2 == 4 and 'G2c.5' in rec(T, '3320', '2c', 'stack2', 'p2a').get('reason', '')
        for n in ('configs', 'run_files', 'baselines', 'pairs.pdf'):
            if os.path.lexists(os.path.join(W3, n)):
                aside(T, os.path.join(W3, n), 'T61b')
        rc3, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E3)
        case('T61 SIGTERM during the frame run of stack2 -> record ERROR, rc 143, baselines/ half written; next run DECISION '
             '(G2c.5); moved to _archive -> PASS', ok and ok2 and rc3 == 0, 'rc %d (%s), %d, %d' % (rc, x.get('verdict'), rc2, rc3))
        E4 = {'LINOG_ROOT': os.path.join(T, 'p2c'), 'LINOG_MOCK_BPERP': '20101206:-23.2', 'LINOG_MOCK_SHIFT': '20101206:0.5',
              'LINOG_MOCK_SHIFT_REF': '20090602'}
        rc, out = run2(['084', '3320', '--decide', 'auto'], env_extra=E4)
        a1, a3 = rec(T, '3320', '2a', 'stack1', 'p2c'), rec(T, '3320', '2c', 'stack2', 'p2c')
        o3 = a3.get('outputs', {})
        case('T60 a pair 0.21 m inside -b in pass 1 and 0.29 m outside in pass 2 -> stack2 WARN (G2c.7), pass 2\'s network '
             '(157 pairs, 408 configs), PASS', rc == 0 and a1.get('outputs', {}).get('pairs') == 158 and a3.get('verdict') == 'PASS'
             and gates(a3).get('G2c.7') == 'WARN' and o3.get('pairs') == 157 and o3.get('configs') == 408
             and [d.get('pair') for d in o3.get('network_diff', [])] == ['20091018_20101206'],
             'rc %d; pass 1 %s pairs; stack2 %s, G2c.7 %s, %s pairs, %s configs, differ %s' % (
                 rc, a1.get('outputs', {}).get('pairs'), a3.get('verdict'), gates(a3).get('G2c.7'), o3.get('pairs'),
                 o3.get('configs'), [d.get('pair') for d in o3.get('network_diff', [])]))
    try:
        if want('2'):
            phase2()
    except Exception as e:  # noqa: BLE001
        case('Phase 2 cases stopped early by %s: %s' % (type(e).__name__, e), False)
    if mockpy:
        import lp_selftest34
        try:
            if want('34'):
                lp_selftest34.phase34(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('Phase 3 and 4 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
        import lp_selftest56
        try:
            if want('56'):
                lp_selftest56.phase56(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('Phase 4.5 and 5 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
        import lp_selftest6
        try:
            if want('6'):
                lp_selftest6.phase6(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('Phase 5e and 6 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
        import lp_selftest10
        try:
            if want('10'):
                lp_selftest10.phase10(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.10 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
        import lp_selftest11
        try:
            if want('11'):
                lp_selftest11.phase11(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.11 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
        import lp_selftest12
        try:
            if want('12'):
                lp_selftest12.phase12(T, case, sys.modules[__name__])
        except Exception as e:  # noqa: BLE001
            import traceback
            case('v0.12 cases stopped early by %s: %s' % (type(e).__name__, e), False, traceback.format_exc()[-600:])
    else:
        case('T63-T83 and T99-T153 not run: the mock ISCE steps and the mock MintPy need numpy, and neither Python tried has it', False)
    stray = sorted(os.path.join(d, n) for d in sorted(set((HERE, os.getcwd()))) for n in os.listdir(d)
                   if (n == '__pycache__' and d == HERE) or n.startswith('isce.log'))
    case('T40 no __pycache__ in the pipeline folder, and no isce.log in it or in the folder the self-test ran from', not stray,
         '%s%s' % (' and '.join(sorted(set((HERE, os.getcwd())))), ': ' + ', '.join(stray) if stray else ''))
    # T40b (v0.13 r1): v0.13's package carried three files at mode 0444 (its two band-limit kit tools and the unpacker); the
    # self-test copied the two tools with their modes, and M8f's append to its copy stopped the Phase 1 cases under felix's
    # account (S42, 18 Oct); root, which every development run was, ignores the mode. By the mode bits (os.access: root passes)
    ro = []
    for top in (HERE, os.path.join(T, 'kit'), os.path.join(T, 'bin')):
        for dp, dn, fn in os.walk(top):
            dn[:] = [x for x in dn if x != '__pycache__']
            for n in fn:
                q = os.path.join(dp, n)
                if not os.path.islink(q) and os.path.isfile(q) and (os.stat(q).st_mode & 0o600) != 0o600:
                    ro.append('%s (%o)' % (os.path.relpath(q, HERE) if top == HERE else os.path.relpath(q, T), os.stat(q).st_mode & 0o777))
    case('T40b (v0.13 r1) every file of the pipeline folder, and the self-test\'s copies in kit/ and bin/, readable and writable by its '
         'owner by its mode bits (a read-only copy stopped the self-test under felix\'s account, S42)', not ro,
         ', '.join(ro[:8]) + (' and %d more' % (len(ro) - 8) if len(ro) > 8 else '') if ro else '%s, kit/ and bin/' % HERE)
    npass = sum(1 for _, ok, _ in res if ok)
    print('selftest: %d of %d cases PASS; console of every run in %s%s' % (
        npass, len(res), os.path.join(T, 'selftest_console.txt'), ' (only the suites %s)' % ','.join(SUITES) if SUITES else ''))
    return 0 if npass == len(res) else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        sys.exit(3)
    sys.exit(main(sys.argv[1]))
