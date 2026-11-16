"""MOCK topo (linog_auto self-test only): the files real topo writes (rehearsal R8), merged/geom_reference full size and
sparse, geom_reference multilooked with hgt.rdr textured over the kit gates' three windows (two with LINOG_MOCK_THIN),
lat.rdr and lon.rdr laid as a descending frame (line 0 north, column 0 east) and los.rdr at 38.8 and -101.1 deg (v0.6).
v0.10 (admit's R1 reads the land from hgt.rdr): off the three windows hgt.rdr rises 0.02 m a line (a 5 x 5 standard
deviation of 3 cm: land to the water tool's flat_masks(); 0.1 m inside a 512-line window, under the kit gates' 1 m, so
their windows stay the three), and the scene's sea (linog_mock3.scene) is flat at 44 m (water).
v0.13 (ascending record 17.9, M73): merged/geom_reference/simamp.rdr carries the reference's amplitude in the rows that hold
samples (the mock's stand-in for ISCE's shaded relief of the DEM: G3a.14 reads that simamp and the reference share one
ground), zeros elsewhere. Planted: LINOG_MOCK_SIMSHIFT=<samples> moves simamp so that the reference reads that many samples
off (a reference moved in range); LINOG_MOCK_RELIEF1=1 textures hgt.rdr over the first 128 samples of range in the first window's rows
only (one window of relief on the narrow grid: the window at column 0 holds it, the one at 128 does not); LINOG_MOCK_FLATDEM=1 leaves it untextured (no window of relief).
v0.13 (17.9, part 4), LINOG_MOCK_V13=1 on a full-height frame: simamp.rdr is ISCE's Simamplitude of the mock ground's heights
(linog_mock3.relief13 and shade13: 100 + 3 x the height step in range) in linog_mock3.BANDS13's rows, the ground every
date's SLC carries, and geom_reference/hgt.rdr those heights multilooked there (the 3 x 3 cells of G10 v3, the kit gates'
windows among them); LINOG_MOCK_SIMSHIFT moves simamp as above; LINOG_MOCK_WATER=1 (M69) leaves hgt.rdr flat but over the
first 256 samples of range of the first four bands (the early and mid thirds of azimuth: two of G10 v3's nine cells, four
of the kit's windows).
v0.13 r2 (P6R-06), LINOG_MOCK_ASC=1 (the mock orbit's vz > 0): lat.rdr and lon.rdr laid as an ascending frame (line 0
south, column 0 west) and los.rdr's azimuth at 101.06 deg (heading -11.06, as LINOG_MOCK_HEADING=-11.06 gives the mock
prep_isce), so that an ascending frame reads north up by report's rule and deliver's D7c."""
import argparse
import os

import numpy as np

import linog_mock3 as M


def write_simamp13(out, W, L):
    """v0.13 (V13): simamp from the mock ground's heights in BANDS13's rows, moved by LINOG_MOCK_SIMSHIFT samples."""
    shift = int(M.env('LINOG_MOCK_SIMSHIFT') or 0)
    with open(out, 'r+b') as fo:
        for b0, b1 in M.BANDS13:
            amp = M.crop13(M.shade13(M.relief13(b0, b1, W)), b0, b1, W).astype('<f4')
            if shift:
                amp = np.roll(amp, -shift, axis=1)
            fo.seek(b0 * W * 4)
            fo.write(amp.tobytes())


def hgt13(gl, gw, W, L, alks, rlks):
    """v0.13 (V13): the looked heights, the ground's relief averaged over each look in BANDS13's rows, 100 + 0.02 m a line
    elsewhere (as v0.10); LINOG_MOCK_WATER=1: flat (100 m) but over the first 256 samples of range of the first four bands
    (the looks wholly inside them), so that of G10 v3's narrow-grid windows only those at columns 0 and 128 (the near third)
    hold relief and the one at 256 none, while the kit's 512-wide windows at column 0 hold it in four bands."""
    hgt = 100.0 + 0.02 * np.arange(gl, dtype=float)[:, None] * np.ones((1, gw))
    water = M.env('LINOG_MOCK_WATER') == '1'
    if water:
        hgt[:] = 100.0
    for k, (b0, b1) in enumerate(M.BANDS13):
        a0, a1 = -(-b0 // alks), b1 // alks   # the looks wholly inside the band
        if a1 <= a0:
            continue
        h = M.crop13(M.relief13(b0, b1, W), b0, b1, W)[(a0 * alks - b0):(a1 * alks - b0), :gw * rlks]
        hl = h.reshape(a1 - a0, alks, gw, rlks).mean(axis=(1, 3))
        c1 = (256 * gw) // W if water else gw
        if water and k >= 4:
            continue
        hgt[a0:a1, :c1] = hl[:, :c1]
    return hgt


def write_simamp(refdir, out, W, L):
    """v0.13: simamp from the reference's amplitude in the rows holding samples (the bands on a full-height frame, every row
    on a short one), moved by LINOG_MOCK_SIMSHIFT samples; the rest left sparse."""
    d = M.date_of(refdir)
    slc = os.path.join(refdir, d + '.slc') if d else None
    if not slc or not os.path.isfile(slc):
        return
    shift = int(M.env('LINOG_MOCK_SIMSHIFT') or 0)
    rows = list(M.BANDS) if L >= M.LINES_FULL else [(0, L)]
    with open(slc, 'rb') as fi, open(out, 'r+b') as fo:
        for b0, b1 in rows:
            fi.seek(b0 * W * 8)
            z = np.frombuffer(fi.read((b1 - b0) * W * 8), dtype=np.complex64)
            if z.size != (b1 - b0) * W:
                continue
            amp = np.abs(z.reshape(b1 - b0, W)).astype('<f4')
            if shift:
                amp = np.roll(amp, -shift, axis=1)
            fo.seek(b0 * W * 4)
            fo.write(amp.tobytes())


def main(iargs=None):
    ap = argparse.ArgumentParser()
    for k in ('--reference', '--dem', '--output'):
        ap.add_argument(k)
    ap.add_argument('--alks', type=int, default=1)
    ap.add_argument('--rlks', type=int, default=1)
    a, _ = ap.parse_known_args(iargs)
    M.env_line('topo')   # v0.9: no WISDOM_FILE in this step's jobs
    W, L = M.frame_dims(a.reference)
    os.makedirs(a.output, exist_ok=True)
    for n, b, dt, nb in (('hgt', 8, 'DOUBLE', 1), ('lat', 8, 'DOUBLE', 1), ('lon', 8, 'DOUBLE', 1), ('los', 8, 'FLOAT', 2),
                         ('incLocal', 8, 'FLOAT', 2), ('shadowMask', 1, 'BYTE', 1), ('simamp', 4, 'FLOAT', 1)):
        p = os.path.join(a.output, n + '.rdr')
        M.sparse(p, b * W * L)
        M.write_xml(p, W, L, dt, nb)
    v13 = M.v13() and L >= M.LINES_FULL
    if v13:
        write_simamp13(os.path.join(a.output, 'simamp.rdr'), W, L)   # v0.13, part 4: the one ground's shaded relief
    else:
        write_simamp(a.reference, os.path.join(a.output, 'simamp.rdr'), W, L)   # v0.13
    open('sim.log', 'a').write('MOCK simamp\n')
    small = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(a.output))), 'geom_reference')
    os.makedirs(small, exist_ok=True)
    gw, gl = W // a.rlks, L // a.alks
    hgt = 100.0 + 0.02 * np.arange(gl, dtype=float)[:, None] * np.ones((1, gw))   # v0.10: land, gently sloping
    rng = np.random.RandomState(5)
    alk = L / float(gl)
    for r0 in ([] if M.env('LINOG_MOCK_FLATDEM') else M.WINDOWS[:1] if M.env('LINOG_MOCK_RELIEF1') else
               M.WINDOWS[:2] if M.env('LINOG_MOCK_THIN') else M.WINDOWS):
        a0, a1 = int(r0 / alk), int((r0 + 512) / alk) + 1
        c1 = max(1, int(128 * gw / float(W))) if M.env('LINOG_MOCK_RELIEF1') else gw   # v0.13: one window only
        hgt[a0:a1 + 1, :c1] = 100 + 5 * rng.normal(size=(len(hgt[a0:a1 + 1]), c1))
    if v13:
        hgt = hgt13(gl, gw, W, L, a.alks, a.rlks)
    hgt[M.scene(gl, gw)['sea']] = 44.0   # v0.10: the scene's sea, flat (water to admit's R1)
    yy, xx = np.mgrid[0:gl, 0:gw] / np.array([float(gl), float(gw)])[:, None, None]
    if M.env('LINOG_MOCK_ASC'):   # v0.13 r2 (P6R-06): an ascending frame, as the mock orbit's vz > 0 says
        lat = 14.55 + 0.55 * yy + 0.02 * xx    # line 0 south (flying north)
        lon = 121.10 + 0.65 * xx + 0.05 * yy   # column 0 west (near range, looking east)
        az = 101.06                            # heading -11.06 (MintPy's azimuth2heading_angle, right-looking)
    else:
        lat = 15.10 - 0.55 * yy - 0.02 * xx    # descending: line 0 north (v0.6's report, SNWE)
        lon = 121.75 - 0.65 * xx - 0.05 * yy   # column 0 east (near range, looking west)
        az = -101.1
    small_data = dict(hgt=hgt.astype('<f8'), lat=lat.astype('<f8'), lon=lon.astype('<f8'),
                      los=np.concatenate([np.full((gl, gw), 38.8, '<f4'), np.full((gl, gw), az, '<f4')]),
                      incLocal=np.concatenate([np.full((gl, gw), 50.5, '<f4'), np.zeros((gl, gw), '<f4')]))
    for n, b, dt, nb in (('hgt', 8, 'DOUBLE', 1), ('lat', 8, 'DOUBLE', 1), ('lon', 8, 'DOUBLE', 1), ('los', 8, 'FLOAT', 2),
                         ('incLocal', 8, 'FLOAT', 2), ('shadowMask', 1, 'BYTE', 1)):
        p = os.path.join(small, n + '.rdr')
        if n in small_data:
            small_data[n].tofile(p)
        else:
            M.sparse(p, b * gw * gl)
        M.write_xml(p, gw, gl, dt, nb)
        for ext in ('.full.xml', '.full.vrt', '.aux.xml'):
            open(p + ext, 'w').write('MOCK\n')
        open(os.path.join(small, n + '.hdr'), 'w').write('ENVI\n')
    print('Total convergence: %d out of %d' % (W * L * 3 // 5, W * L))
