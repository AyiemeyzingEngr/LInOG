"""MOCK ALOS_SLC sensor (linog_auto self-test only).

Reads the CEOS record length (IMG-HH byte 728) and the summary.txt beside the image, writes a SPARSE .slc of
samples x lines x 8 B (a full-height 18432-line frame gets the mock ground in three bands, linog_mock3), and fills a Frame with the attribute names and values RD2 read on felix (26 Sept 2026,
20081130): PRF 2159.8272138229, a 28 MHz chirp, passDirection None, and 28 state vectors 60 s apart with vz -7340 m/s.
r0 as ISCE's ALOS_SLC.extractImage sets it (v0.5): c/2 x the leader's 'Range gate delay in microsec', read from the
LED-* file with ISCE's own CEOS parser and record definitions (CEOS.py and db/alos_slc/, copied from isce2 2.6.3);
the image records' 'Slant range to 1st data sample' is not read, as ISCE reads it only when the delay is missing.
v0.13 (ascending record 4.11): the sampling rate, the wavelength, the pulse length and the chirp slope come from the leader's
scene record, by mode, as ISCE2's ALOS_SLC.populateMetadata reads them (FBD shelves read 16 MHz and a 14 MHz chirp), and
the pixel is c / (2 fs); a short frame (under 18432 lines) whose IMG-HH records carry samples gets them in its .slc, as
ISCE's writeRawData does (big-endian float32 I and Q pairs after each record's 412 B prefix, written as complex64), and a
frame whose records hold zeros keeps its sparse .slc.
Planted cases come from the environment (lp_env.sh passes LINOG_*):
  LINOG_MOCK_FAIL=<date>  raise for that date      LINOG_MOCK_ASC=1     vz > 0 (an ascending orbit)
  LINOG_MOCK_R0OFF=1      r0 50 m beyond the leader's   LINOG_MOCK_PRF=<Hz>  that PRF
  LINOG_MOCK_BW=<MHz>     that chirp bandwidth     LINOG_MOCK_SLEEP=<date>  wait 60 s there (a run to stop)
  v0.13: LINOG_MOCK_HV=<date>  that date read from IMG-HV (the HV lottery, silently); <date>:log  the same, and a line
         naming the IMG-HV file printed (the unpacker's log then names it)
         LINOG_MOCK_WAVELENGTH=<date>:<factor>  that date's wavelength times factor
         LINOG_MOCK_FS16=<date>  that date's shelve at 16 MHz (and its pixel c / 32 MHz) whatever the leader says
         LINOG_MOCK_SCALE=<date>:<factor>  that date's samples times factor (G4's 1e-4 clause, the part 2 review's P2-07)
         LINOG_MOCK_SLR=<date>:<metres> or FBS:<metres>  that date's pixel, or every 32 MHz date's, c / (2 fs) plus metres
         LINOG_MOCK_V13=1  (17.9, part 4) a full-height frame's SLC from the IMG-HH records of linog_mock3.RAW13's rows (the
         one ground, mkzip rows13), and each date's PRF 100000 / (46.1 + 0.1 x (date mod 6)), as felix's six PRFs
v0.13: the frame's own PRF is set beside the instrument's (refineSecondaryTiming.py's azratio reads frame.PRF).
v0.13 (part 5, M79 and M80): the frame keeps the leader's r0 as _mock_r0_leader beside startingRange, which rwin may move,
for the mock resample's LINOG_MOCK_GATEOFF.
"""
import datetime
import os
import re
import struct
import sys
import time

from isceobj.Scene.Frame import Frame, Image, Instrument, Orbit, Platform, StateVector
from isceobj.Sensor import CEOS

C = 299792458.0   # isceobj.Planet.AstronomicalHandbook.Const.c
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'alos_slc')
LINES_FULL = 18432


def leader_scene(led):
    """The leader's scene header record (after the file descriptor), as ISCE reads it."""
    with open(led, 'rb') as fh:
        fdr = CEOS.CEOSDB(xml=os.path.join(DB, 'leader_file.xml'), dataFile=fh)
        fdr.parse()
        fdr.finalizeParser()
        fh.seek(fdr.getEndOfRecordPosition())
        sc = CEOS.CEOSDB(xml=os.path.join(DB, 'scene_record.xml'), dataFile=fh)
        sc.parse()
        sc.finalizeParser()
    return sc.metadata


def leader_delay_us(led):
    """The leader's 'Range gate delay in microsec' (file descriptor, then the scene header record), as ISCE reads it."""
    return leader_scene(led)['Range gate delay in microsec']


def num(x, default):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if v else default


def plant(env, key, date):
    """The planted value for date of a LINOG_MOCK_<key>=<date>[:<value>] variable, or None."""
    v = env.get(key, '')
    if not v:
        return None
    d, _, rest = v.partition(':')
    return rest if d == date else None


def copy_rows13(img, out, ns, nl):
    """v0.13: a full-height frame's samples in linog_mock3.RAW13's rows, the rest of the SLC left sparse; False when the
    records there hold zeros."""
    import numpy as np
    import linog_mock3
    rec = 412 + 8 * ns
    any_ = False
    with open(img, 'rb') as fi, open(out, 'wb') as fo:
        fo.truncate(ns * nl * 8)
        for b0, b1 in linog_mock3.RAW13:
            fi.seek(720 + b0 * rec)
            raw = np.frombuffer(fi.read((b1 - b0) * rec), dtype=np.uint8)
            if raw.size != (b1 - b0) * rec:
                return False
            data = raw.reshape(b1 - b0, rec)[:, 412:]
            if not data.any():
                continue
            any_ = True
            iq = np.ascontiguousarray(data).view('>f4').reshape(b1 - b0, ns, 2)
            fo.seek(b0 * ns * 8)
            fo.write((iq[..., 0] + np.complex64(1j) * iq[..., 1]).astype(np.complex64).tobytes())
    return any_


def copy_samples(img, out, ns, nl, scale=1.0):
    """A short frame's samples, as ISCE's writeRawData writes them (times scale, a plant); False (nothing written) when the
    records hold zeros."""
    rec = 412 + 8 * ns
    if nl >= LINES_FULL or nl * rec > (64 << 20):
        return False
    import numpy as np
    raw = np.fromfile(img, dtype=np.uint8, count=nl * rec, offset=720)
    if raw.size != nl * rec:
        return False
    data = raw.reshape(nl, rec)[:, 412:]
    if not data.any():
        return False
    iq = np.ascontiguousarray(data).view('>f4').reshape(nl, ns, 2)
    ((iq[..., 0] + np.complex64(1j) * iq[..., 1]) * np.float32(scale)).astype(np.complex64).tofile(out)
    return True


class ALOS_SLC(object):
    def __init__(self):
        self._leaderFile = self._imageFile = self.output = None
        self.frame = Frame()
        self.doppler_coeff, self.azfmrate_coeff = [0.0], [0.0]

    def configure(self):
        pass

    def extractImage(self):
        env = os.environ
        date = os.path.basename(os.path.dirname(os.path.abspath(self.output)))
        if env.get('LINOG_MOCK_FAIL') == date:
            raise RuntimeError('mock unpack failure for %s' % date)
        if env.get('LINOG_MOCK_SLEEP') == date:
            time.sleep(60)
        img = self._imageFile
        hv = plant(env, 'LINOG_MOCK_HV', date)
        if hv is not None:   # v0.13: the HV lottery (memory linog_unpacker_polarization_bug)
            img = os.path.join(os.path.dirname(img), os.path.basename(img).replace('IMG-HH-', 'IMG-HV-'))
            if hv == 'log':
                print('MOCK ALOS_SLC: reading %s' % img)
                sys.stdout.flush()
        with open(img, 'rb') as fh:
            head = fh.read(732)
        ns = (struct.unpack('>I', head[728:732])[0] - 412) // 8
        t = open(os.path.join(os.path.dirname(self._imageFile), 'summary.txt'), errors='replace').read()
        nl = int(re.search(r'Pdi_NoOfLines="(\d+)"', t).group(1))
        m = re.search(r'Img_SceneCenterDateTime="(\d{8}) (\d\d:\d\d:\d\d\.\d+)"', t)
        mid = datetime.datetime.strptime(m.group(1) + ' ' + m.group(2), '%Y%m%d %H:%M:%S.%f')
        if nl >= LINES_FULL and env.get('LINOG_MOCK_V13') == '1' and copy_rows13(img, self.output, ns, nl):
            pass   # v0.13 (17.9): the one ground, from the records
        elif nl >= LINES_FULL:   # the Phase 3 test frame: the kit's G7 and G10 read windows of a full-height ALOS frame
            import linog_mock3
            linog_mock3.write_slc(self.output, ns, nl, date)
        elif not copy_samples(img, self.output, ns, nl, float(plant(env, 'LINOG_MOCK_SCALE', date) or 1.0)):
            with open(self.output, 'wb') as fh:
                fh.truncate(ns * nl * 8)
        md = leader_scene(self._leaderFile)
        fs = num(md.get('Range sampling rate in MHz'), 32.0) * 1e6
        if plant(env, 'LINOG_MOCK_FS16', date) is not None:
            fs = 16e6
        lam = num(md.get('Radar wavelength'), 0.2360571)
        f_lam = plant(env, 'LINOG_MOCK_WAVELENGTH', date)
        if f_lam:
            lam *= float(f_lam)
        pl = num(md.get('Range pulse length in microsec'), 27.0) * 1e-6
        slope = num(md.get('Nominal range pulse (chirp) amplitude coefficient linear term'), 28e6 / pl)
        if env.get('LINOG_MOCK_BW'):
            slope = float(env['LINOG_MOCK_BW']) * 1e6 / pl
        prf = float(env.get('LINOG_MOCK_PRF') or 100000.0 / 46.3)
        if env.get('LINOG_MOCK_V13') == '1' and not env.get('LINOG_MOCK_PRF'):
            prf = 100000.0 / (46.1 + 0.1 * (int(date) % 6))
        dslr = plant(env, 'LINOG_MOCK_SLR', date)
        if dslr is None and abs(fs - 32e6) < 1.0:
            dslr = plant(env, 'LINOG_MOCK_SLR', 'FBS')
        f = self.frame
        f.numberOfSamples, f.numberOfLines, f.passDirection = ns, nl, None
        f.PRF = prf   # v0.13: ISCE's frame carries its PRF beside the instrument's (refineSecondaryTiming.py reads frame.PRF)
        f.startingRange = C * 0.5 * md['Range gate delay in microsec'] * 1e-6 + (50.0 if env.get('LINOG_MOCK_R0OFF') else 0.0)
        f._mock_r0_leader = f.startingRange   # v0.13 (M79, M80): rwin may move startingRange; the mock resample reads both
        half = datetime.timedelta(seconds=(nl - 1) / prf / 2)
        f.sensingStart, f.sensingStop = mid - half, mid + half
        f.instrument = Instrument(PRF=prf, rangeSamplingRate=fs, pulseLength=pl, chirpSlope=slope,
                                  rangePixelSize=C / (2.0 * fs) + float(dslr or 0.0), radarWavelength=lam, incidenceAngle=38.745,
                                  platform=Platform(-1))
        f.image = Image(self.output, ns, nl)
        vz = 7340.0 if env.get('LINOG_MOCK_ASC') else -7340.0
        t0 = mid.replace(second=0, microsecond=0) - datetime.timedelta(minutes=13)
        f.orbit = Orbit([StateVector(t0 + datetime.timedelta(seconds=60 * k), [0.0, 0.0, 0.0], [652.5, 1856.8, vz])
                         for k in range(28)])
        self.doppler_coeff, self.azfmrate_coeff = [0.7157342, 0.0010574, 0.0], [-519.7604251, 0.0029455, -0.0]
