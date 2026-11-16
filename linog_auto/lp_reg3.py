#!/usr/bin/env python3
"""lp_reg3.py -- linog_auto v0.13: G10 v3's estimator (ascending record 17.4, 17.5) and the readings built on it: G3a.14,
the reference's position after topo against topo's simulated amplitude (Gap 2b, 17.7, 18.5, 20.10).

numpy, imported inside the functions (the module is imported by phases that run in the pinned env; its md5 goes into
their records' tools, not their fingerprints, 17.4).

est(ref, sec): the shift of sec against ref, in ref's lines and samples, at sub-sample (g10_est.py's est(), as RA4 ran
it on felix, f6e4ce24...): each patch demodulated by its own spectral centroid (lag-1 autocorrelation) and oversampled by
2 before it is detected; the mean-removed amplitudes cross-correlated by FFT; the integer peak, its ratio to the second
peak outside +/-16 samples (v2's statistic, read on the 2x grid with the suppression doubled) and its significance; the
peak refined by a matrix DFT of the cross-power spectrum on a 1/64-sample grid over +/-0.75 sample, then by a parabola
through that grid's peak and its neighbours. No median is taken out.

G3a.14 (Gap 2b): the reference SLC as ISCE reads it (the file its shelve names) and merged/geom_reference/simamp.rdr (ISCE's
Simamplitude of the DEM in the reference's geometry), their widths checked equal; both multilooked 4 x 4 (amplitude
averaged) at windows of relief: the frame cut into 3 x 3 cells (near, mid and far range by early, mid and late azimuth),
in each cell the most textured viable window by v2's rules (geom_reference/hgt.rdr's std over the window at least 1 m,
the reference's fill at least 0.99, its mean amplitude at least half the frame's 75th percentile) on v2's candidate grid,
512 x 512 samples (128 x 128 looks) every 1,024 lines and 512 samples, or on a frame under 1,536 samples wide 256 x 256
(64 x 64 looks) every 512 lines and 128 samples with the last column at the width less 256; est() on the looked windows,
simamp as the reference, the SLC as the secondary; a window counted only at a peak ratio of 1.25 (20.10); the median of
the counted windows' dx, in full-resolution samples. In the reference's own samples (149.896229 m / its pixel: 32 on
FBS, 16 on FBD; 18.5) a quarter of a gate passes, half a gate fails:
  3 or more counted windows: PASS at |dx| <= a quarter gate (8 FBS samples), WARN under half a gate, FAIL at half a gate
  (16) or more; 1 or 2: FAIL when every one reads half a gate or more with one sign, else WARN ("few windows"); none:
  NOT MEASURED, WARN. Azimuth is recorded, not judged; topo's shadowMask.rdr pixels are counted by window, not masked.
"""
import os
import re

GATE_M = 299792458.0 / 2.0 * 1e-6   # one microsecond of range delay, 149.896229 m

SUPP, UPS = 16, 64                  # est(): v2's suppression radius; the refinement grid, 1/64 sample
LOOKS = 4                           # G3a.14's multilook, both axes
RATIO_MIN = 1.25                    # 20.10: a window counts only at this peak ratio (v2's vote line)
DEM_MIN, SEL_FILL, AMP_FRAC, AMP_GRID, FILLROWS = 1.0, 0.99, 0.50, 6, 64   # v2's window rules (linog_reg_common.py 38f9e163)
NARROW = 1536                       # a frame under this width takes the narrow grid


def gate_samples(slr):
    """One range gate in samples of a pixel slr (m), rounded to 1e-6 so that a pixel carried at 9 decimals (4.684257156 m,
    9.368514313 m) gives 32 and 16 exactly and the quarter and half gate lines hold at 8 and 16, 4 and 8 (the part 3
    review's P3-13)."""
    return round(GATE_M / float(slr), 6)


# ------------------------------------------------------------------------------------------------ the estimator
def centroid(s):
    """The spectral centroid of a complex patch in cycles a sample, (azimuth, range), from its lag-1 autocorrelation."""
    import numpy as np
    cy = np.angle(np.vdot(s[:-1, :], s[1:, :])) / (2 * np.pi)
    cx = np.angle(np.vdot(s[:, :-1], s[:, 1:])) / (2 * np.pi)
    return cy, cx


def over2(s):
    """The patch demodulated by its centroid and oversampled by 2 in both axes (its spectrum zero-padded about 0)."""
    import numpy as np
    M, N = s.shape
    cy, cx = centroid(s)
    y = np.arange(M)[:, None]
    x = np.arange(N)[None, :]
    d = s * np.exp(-2j * np.pi * (cy * y + cx * x))
    F = np.fft.fftshift(np.fft.fft2(d))
    G = np.zeros((2 * M, 2 * N), dtype=np.complex128)
    G[M // 2:M // 2 + M, N // 2:N // 2 + N] = F
    return np.fft.ifft2(np.fft.ifftshift(G)) * 4.0


def peak_ratio(C, iy, ix, supp):
    import numpy as np
    ny, nx = C.shape
    D = C.copy()
    ys = [(iy + k) % ny for k in range(-supp, supp + 1)]
    xs = [(ix + k) % nx for k in range(-supp, supp + 1)]
    D[np.ix_(ys, xs)] = C.min()
    second = float(D.max())
    return None if second <= 0 else float(C.max() / second)


def dft_region(CP, y0, x0, ups, n):
    """The cross-correlation at (y0 + (k - n//2)/ups, x0 + (l - n//2)/ups), k, l < n, from the cross-power spectrum CP
    (the inverse DFT evaluated off the grid by two matrix products)."""
    import numpy as np
    M, N = CP.shape
    fy = np.fft.fftfreq(M)
    fx = np.fft.fftfreq(N)
    ys = y0 + (np.arange(n) - n // 2) / ups
    xs = x0 + (np.arange(n) - n // 2) / ups
    Ey = np.exp(2j * np.pi * ys[:, None] * fy[None, :])
    Ex = np.exp(2j * np.pi * fx[:, None] * xs[None, :])
    return (Ey @ CP @ Ex).real, ys, xs


def est(ref, sec):
    """G10 v3: (dy, dx) of sec against ref in the reference's lines and samples, the ratio and sigma (v2's statistics, read
    on the 2x grid with the suppression doubled); g10_est.py's est() line for line."""
    import numpy as np
    A = np.abs(over2(ref))
    B = np.abs(over2(sec))
    A -= A.mean()
    B -= B.mean()
    CP = np.fft.fft2(B) * np.conj(np.fft.fft2(A))
    C = np.fft.ifft2(CP).real
    ny, nx = C.shape
    iy, ix = np.unravel_index(int(np.argmax(C)), C.shape)
    sd = C.std()
    sigma = None if sd == 0 else float((C.max() - C.mean()) / sd)
    ratio = peak_ratio(C, iy, ix, 2 * SUPP)
    y0 = iy if iy < ny // 2 else iy - ny
    x0 = ix if ix < nx // 2 else ix - nx
    n = 3 * UPS // 2 + 1                       # +/-1.5 cells of the 2x grid (0.75 sample) around the integer peak
    R, ys, xs = dft_region(CP, y0, x0, UPS // 2, n)   # 1/32 of a 2x cell = 1/64 sample
    ky, kx = np.unravel_index(int(np.argmax(R)), R.shape)
    h = 1.0 / (UPS // 2)

    def para(v, k):           # a parabola through the fine grid's peak and its two neighbours
        if 0 < k < len(v) - 1:
            den = v[k - 1] - 2 * v[k] + v[k + 1]
            return 0.0 if den == 0 else 0.5 * (v[k - 1] - v[k + 1]) / den
        return 0.0
    py = para(R[:, kx], ky) * h
    px = para(R[ky, :], kx) * h
    return dict(dy=float((ys[ky] + py) / 2.0), dx=float((xs[kx] + px) / 2.0), ratio=ratio, sigma=sigma, int_dy=y0 / 2.0,
                int_dx=x0 / 2.0)


# ------------------------------------------------------------------------------------------------ windows and reads
def xml_int(path, name):
    try:
        m = re.search(r'name="%s".*?<value>\s*(\d+)' % name, open(path, errors='replace').read(), re.S)
    except OSError:
        return None
    return int(m.group(1)) if m else None


def load_hgt(W):
    """geom_reference/hgt.rdr (the multilooked heights, float64) as an array, or (None, why)."""
    import numpy as np
    p = os.path.join(W, 'geom_reference', 'hgt.rdr')
    if not os.path.isfile(p):
        return None, 'geom_reference/hgt.rdr absent'
    dw, dl = xml_int(p + '.xml', 'width'), xml_int(p + '.xml', 'length')
    if not (dw and dl) or dw * dl * 8 != os.path.getsize(p):
        return None, 'geom_reference/hgt.rdr is %d B, its xml %s x %s' % (os.path.getsize(p), dl, dw)
    return np.fromfile(p, dtype=np.float64).reshape(dl, dw), '%d x %d' % (dl, dw)


def grid(width, lines):
    """(window edge, candidate rows, candidate columns): v2's grid, or the narrow grid under 1,536 samples."""
    if width >= NARROW:
        n = 512
        return n, list(range(0, lines - n, 1024)), list(range(0, width - n, 512))
    n = 256
    cols = list(range(0, width - n, 128))
    if width - n not in cols:
        cols.append(width - n)
    return n, list(range(0, lines - n, 512)), cols


def cell(r0, c0, n, width, lines):
    """The 3 x 3 cell of a window by its centre: (azimuth third, range third), early and near first."""
    return min(2, int(3 * (r0 + n / 2.0) / lines)), min(2, int(3 * (c0 + n / 2.0) / width))


def cpatch(path, r0, c0, width, n, rows=None, dtype='complex64'):
    """An n x n patch (or n of its rows spread over it) of a raster of width samples."""
    import numpy as np
    bps = np.dtype(dtype).itemsize
    idx = list(range(n)) if rows is None else sorted(set(np.linspace(0, n - 1, rows).round().astype(int).tolist()))
    o = np.zeros((len(idx), n), dtype=dtype)
    with open(path, 'rb') as fh:
        for j, i in enumerate(idx):
            fh.seek(((r0 + i) * width + c0) * bps)
            b = fh.read(n * bps)
            if len(b) < n * bps:
                raise IOError('short read at line %d of %s' % (r0 + i, path))
            o[j] = np.frombuffer(b, dtype=dtype)
    return o


def frame_scale(slc, width, lines, n):
    """The frame's amplitude scale (v2's frame_amp_scale): the 75th percentile of the mean amplitude of AMP_GRID x AMP_GRID
    spread windows with fill at least SEL_FILL; None when none qualifies."""
    import numpy as np
    amps = []
    for r0 in np.linspace(0, lines - n - 1, AMP_GRID).astype(int):
        for c0 in np.linspace(0, width - n - 1, AMP_GRID).astype(int):
            try:
                m = np.abs(cpatch(slc, int(r0), int(c0), width, n, rows=FILLROWS))
            except IOError:
                continue
            if (m != 0).mean() >= SEL_FILL:
                amps.append(float(m.mean()))
    return float(np.percentile(amps, 75)) if amps else None


def pick_windows(slc, width, lines, hgt, accept=None):
    """G10 v3's and G3a.14's windows (17.4): per 3 x 3 cell the most textured viable window. accept(r0, c0, n), when given,
    is asked of a cell's viable candidates from the most textured down, and the first it takes is the cell's (G3a.14: a
    simamp patch that is finite and not constant; the part 3 review's P3-08, as RA4's gap2b tried a cell's next candidate).
    Returns (n, windows, named, survey): windows [{r0, c0, cell, demstd, fill, amp}], named the cells with no viable window,
    survey the frame's amplitude scale, the number of candidates and, for each named cell, its candidates' reasons counted."""
    import collections
    import numpy as np
    n, rows, cols = grid(width, lines)
    dl, dw = hgt.shape
    rlk, alk = width / float(dw), lines / float(dl)
    scale = frame_scale(slc, width, lines, n)
    viable, survey = collections.defaultdict(list), []
    for r0 in rows:
        for c0 in cols:
            b = hgt[int(r0 / alk):int((r0 + n) / alk) + 1, int(c0 / rlk):int((c0 + n) / rlk) + 1]
            sd = float(np.nanstd(b)) if b.size >= 4 else 0.0
            why = []
            if sd < DEM_MIN:
                why.append('DEM std %.2f m' % sd)
            fill = amp = None
            if not why:
                m = np.abs(cpatch(slc, r0, c0, width, n, rows=FILLROWS))
                fill, amp = float((m != 0).mean()), float(m.mean())
                if fill < SEL_FILL:
                    why.append('fill %.3f' % fill)
                if scale is None or amp < AMP_FRAC * scale:
                    why.append('amplitude %.3g, the frame\'s P75 %s' % (amp, scale))
            k = cell(r0, c0, n, width, lines)
            survey.append(dict(r0=r0, c0=c0, cell=k, why='; '.join(why)))
            if not why:
                viable[k].append(dict(r0=r0, c0=c0, cell=list(k), demstd=sd, fill=fill, amp=amp))
    best = {}
    for k, cs in viable.items():
        for c in sorted(cs, key=lambda c: (-c['demstd'], c['r0'], c['c0'])):
            ok, why = accept(c['r0'], c['c0'], n) if accept else (True, '')
            if ok:
                best[k] = c
                break
            [x for x in survey if (x['r0'], x['c0']) == (c['r0'], c['c0'])][0]['why'] = why
    name = lambda a, r: '%s %s' % (('early', 'mid', 'late')[a], ('near', 'mid', 'far')[r])  # noqa: E731
    named = [name(a, r) for a in range(3) for r in range(3) if (a, r) not in best]
    reasons = dict((name(*k), dict(collections.Counter(re.sub(r'[-+]?\d+(\.\d+)?(e[-+]?\d+)?', 'N', x['why']) or 'viable' for x in survey
                                                       if x['cell'] == k))) for k in sorted(set(x['cell'] for x in survey))
                   if k not in best)
    return n, [best[k] for k in sorted(best)], named, dict(scale=scale, candidates=len(survey), named_cells=reasons)


def looked(a, k=LOOKS):
    """k x k looks of an amplitude (or real) array, averaged."""
    m, n = a.shape[0] // k * k, a.shape[1] // k * k
    return a[:m, :n].reshape(m // k, k, n // k, k).mean(axis=(1, 3))


def g3a14_read(slc, sim, shadow, width, lines, hgt):
    """G3a.14's windows and readings: (n, readings, named, survey). Each reading: the window, est()'s dx and dy in
    full-resolution samples and lines (the SLC against simamp), its ratio and sigma, the shadowMask pixels flagged."""
    import numpy as np

    def sim_ok(r0, c0, n):
        s = cpatch(sim, r0, c0, width, n, dtype='<f4').astype(np.float64)
        if not np.isfinite(s).all():
            return False, 'simamp not finite (%d samples)' % int((~np.isfinite(s)).sum())
        if not s.std() > 0:
            return False, 'simamp constant'
        return True, ''
    n, wins, named, survey = pick_windows(slc, width, lines, hgt, accept=sim_ok)
    out = []
    fin = lambda v: float(v) if v is not None and np.isfinite(v) else None  # noqa: E731
    for w in wins:
        r0, c0 = w['r0'], w['c0']
        a = np.abs(cpatch(slc, r0, c0, width, n))
        s = cpatch(sim, r0, c0, width, n, dtype='<f4').astype(np.float64)
        flagged = None
        if shadow and os.path.isfile(shadow):
            try:
                flagged = int((cpatch(shadow, r0, c0, width, n, dtype='u1') != 0).sum())
            except IOError:
                flagged = None
        r = est(looked(s).astype(np.complex64), looked(a).astype(np.complex64))
        dx, dy, ratio = fin(r['dx']), fin(r['dy']), fin(r['ratio'])
        if dx is None or dy is None:   # a reading that is not a number is not counted (the record stays strict JSON)
            ratio = None
        out.append(dict(w, dx=None if dx is None else dx * LOOKS, dy=None if dy is None else dy * LOOKS, ratio=ratio,
                        sigma=fin(r['sigma']), shadow_px=flagged))
    return n, out, named, survey


def g3a14_verdict(readings, gate_samples, ratio_min=RATIO_MIN):
    """G3a.14's verdict (17.7, 18.5, 20.10): (verdict, value, note, counted). gate_samples: one range gate in the reference's
    samples (32 FBS, 16 FBD); a quarter of a gate passes, half a gate fails. A window counts at a ratio of ratio_min.
    Standard library only (the self-test calls it in its own Python, which may have no numpy)."""
    q, h = gate_samples / 4.0, gate_samples / 2.0
    counted = [x for x in readings if x.get('ratio') is not None and x['ratio'] >= ratio_min]
    low = [x for x in readings if x not in counted]
    note = '; '.join('window at line %d, sample %d (%s) not counted: ratio %s, DEM std %.1f m' % (
        x['r0'], x['c0'], '/'.join(str(c) for c in x['cell']), None if x.get('ratio') is None else round(x['ratio'], 3),
        x['demstd']) for x in low)
    dxs = [x['dx'] for x in counted]
    if not counted:
        return 'WARN', 'NOT MEASURED: no window counted (%d read)' % len(readings), note, counted
    med = float(_median(dxs))
    rd = ', '.join('%+.2f' % v for v in dxs)
    if len(counted) >= 3:
        v = 'PASS' if abs(med) <= q else 'FAIL' if abs(med) >= h else 'WARN'
        return v, 'dx %+.2f samples, the median of %d windows (%s); a quarter gate %g, half %g' % (med, len(counted), rd, q, h), note, counted
    one_sign = all(x >= h for x in dxs) or all(x <= -h for x in dxs)
    if one_sign:
        return 'FAIL', 'dx %+.2f samples on %d window(s) (%s), every one at half a gate (%g) or more, one sign' % (
            med, len(counted), rd, h), note, counted
    return 'WARN', 'few windows: %d counted (%s)' % (len(counted), rd), note, counted


# ------------------------------------------------------------------------------------------------ G10 v3 (17.4)
MIN_FILL, ALLOW_MISS = 0.90, 1      # v2's: a date's patch counts at fill 0.90; a window viable with all but one at full fill
BOOT_N, BOOT_SEED = 2000, 13        # the mode statistics' interval: dates resampled 2,000 times, a fixed seed (22.2)
LINE_MIXED, LINE_ONE, LINE_AZ = 0.125, 0.0625, 0.25   # G10v3's per-date lines (samples, samples, lines; 17.4, 18.5)
MODE_LINE = 0.1                     # G10m: |dx by mode| over 0.1 samples, its interval clear of 0: WARN


def g10v3_read(ref, secs, width, lines, hgt):
    """G10 v3's windows and readings (17.4): ref the reference's image, secs {date: image} on its grid. Each window: per
    3 x 3 cell the most textured viable one by v2's rules, all secondaries but one at full fill too. Returns (n, windows,
    named, survey, readings {date: [dict(window index, dx, dy, ratio, sigma, fill)]})."""
    import numpy as np

    def secs_ok(r0, c0, n):
        nfull = 0
        for d, p in sorted(secs.items()):
            try:
                m = np.abs(cpatch(p, r0, c0, width, n, rows=FILLROWS))
            except IOError:
                continue
            nfull += float((m != 0).mean()) >= SEL_FILL
        if nfull < len(secs) - ALLOW_MISS:
            return False, 'only %d of %d secondaries at full fill' % (nfull, len(secs))
        return True, ''
    n, wins, named, survey = pick_windows(ref, width, lines, hgt, accept=secs_ok)
    fin = lambda v: float(v) if v is not None and np.isfinite(v) else None  # noqa: E731
    rd = dict((d, []) for d in secs)
    for k, w in enumerate(wins):
        a = cpatch(ref, w['r0'], w['c0'], width, n)
        for d, p in sorted(secs.items()):
            try:
                b = cpatch(p, w['r0'], w['c0'], width, n)
            except IOError as e:
                rd[d].append(dict(window=k, dx=None, dy=None, ratio=None, sigma=None, fill=0.0, error=str(e)))
                continue
            fill = float((b != 0).mean())
            r = est(a, b)
            dx, dy = fin(r['dx']), fin(r['dy'])
            rd[d].append(dict(window=k, dx=dx, dy=dy, ratio=fin(r['ratio']) if dx is not None and dy is not None else None,
                              sigma=fin(r['sigma']), fill=fill))
    return n, wins, named, survey, rd


def _median(v):
    v = sorted(v)
    return None if not v else (v[len(v) // 2] if len(v) % 2 else 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2]))


def g10v3_summary(n, wins, rd, modes, ref, width):
    """17.4's per-date and by-mode readings: the windows that vote (the median ratio over the dates whose patch is at fill
    MIN_FILL at least RATIO_MIN, v2's vote), each date's dx and dy as the medians over its voting windows at fill MIN_FILL
    (a date with no such reading is named by G10v3's WARN, the build's reading of 17.4), their spread, the range slope (two range
    thirds or more), and on a mixed frame the FBD median less the FBS median with a 95 % interval by resampling the dates."""
    import numpy as np
    votes = []
    for k in range(len(wins)):   # v2's vote: the median ratio over the dates whose patch is at MIN_FILL (the part 4 review's P4-01)
        rs = [x['ratio'] for d in rd for x in rd[d] if x['window'] == k and x['ratio'] is not None and x['fill'] >= MIN_FILL]
        mr = _median(rs)
        votes.append(dict(window=k, median_ratio=mr, votes=bool(mr is not None and mr >= RATIO_MIN)))
    vk = set(v['window'] for v in votes if v['votes'])
    per = {}
    for d in sorted(rd):
        xs = [x for x in rd[d] if x['window'] in vk and x['fill'] >= MIN_FILL and x['dx'] is not None]
        dx, dy = _median([x['dx'] for x in xs]), _median([x['dy'] for x in xs])
        thirds = set(wins[x['window']]['cell'][1] for x in xs)
        slope = None
        if len(thirds) >= 2 and len(xs) >= 2:
            cols = np.array([wins[x['window']]['c0'] + n / 2.0 for x in xs])
            slope = float(np.polyfit(cols, np.array([x['dx'] for x in xs]), 1)[0])   # samples a sample of range
        per[d] = dict(dx=dx, dy=dy, n=len(xs), spread_dx=(max(x['dx'] for x in xs) - min(x['dx'] for x in xs)) if xs else None,
                      spread_dy=(max(x['dy'] for x in xs) - min(x['dy'] for x in xs)) if xs else None, slope=slope,
                      mode=modes.get(d))
    out = dict(windows=[dict(w, **v) for w, v in zip(wins, votes)], voting=len(vk), dates=per)
    ms = set(m for d, m in modes.items() if m)
    if ms == {'FBS', 'FBD'}:
        rng = np.random.RandomState(BOOT_SEED)
        fb = [d for d in per if per[d]['mode'] == 'FBS' and d != ref and per[d]['dx'] is not None]
        fd = [d for d in per if per[d]['mode'] == 'FBD' and d != ref and per[d]['dx'] is not None]
        if fb and fd:
            def delta(a, b, key):
                return float(np.median([per[d][key] for d in b]) - np.median([per[d][key] for d in a]))
            bx, by = [], []
            for _ in range(BOOT_N):
                a = list(rng.choice(fb, len(fb)))
                b = list(rng.choice(fd, len(fd)))
                bx.append(delta(a, b, 'dx'))
                by.append(delta(a, b, 'dy'))
            out['mode'] = dict(dx=delta(fb, fd, 'dx'), dy=delta(fb, fd, 'dy'), dx_ci=[float(np.percentile(bx, 2.5)), float(np.percentile(bx, 97.5))],
                               dy_ci=[float(np.percentile(by, 2.5)), float(np.percentile(by, 97.5))], n_fbs=len(fb), n_fbd=len(fd),
                               boot=BOOT_N, seed=BOOT_SEED)
    return out


def g10v3_verdicts(summ, mixed, rho):
    """G10v3 and G10m (17.4, 18.5): [(gid, verdict, value, threshold, note)]. On a mixed frame every date's |dx| at most
    0.125 samples (rho = 32 / 14), on an FBS-only or FBD-only frame 0.0625 (rho = 32 / 28 or 16 / 14), |dy| at most 0.25
    lines: INFO, else WARN naming the dates; fewer than 3 voting windows: NOT MEASURED, WARN. G10m on a mixed frame: INFO
    with the mode offset, WARN when |dx| is over 0.1 samples with its interval clear of 0; N/A otherwise."""
    import math
    line = LINE_MIXED if mixed else LINE_ONE
    out = []
    if summ['voting'] < 3:
        out.append(('G10v3', 'WARN', 'NOT MEASURED: %d window(s) vote (ratio %.2f), fewer than 3; v2\'s verdict stands' % (
            summ['voting'], RATIO_MIN), '3 or more voting windows', ''))
    else:
        rows = summ['dates']
        off = sorted(d for d, v in rows.items() if v['dx'] is None or v['dy'] is None or abs(v['dx']) > line or abs(v['dy']) > LINE_AZ)
        xs = [v['dx'] for v in rows.values() if v['dx'] is not None]
        ys = [v['dy'] for v in rows.values() if v['dy'] is not None]
        val = '%d of %d dates within |dx| %g samples and |dy| %g lines on %d voting windows; dx %+.3f to %+.3f, dy %+.3f to %+.3f' % (
            len(rows) - len(off), len(rows), line, LINE_AZ, summ['voting'], min(xs) if xs else float('nan'),
            max(xs) if xs else float('nan'), min(ys) if ys else float('nan'), max(ys) if ys else float('nan'))
        out.append(('G10v3', 'WARN' if off else 'INFO', val, '|dx| <= %g (rho %.3f: no pair below %.2f of its coherence), '
                    '|dy| <= %g' % (line, rho, abs(math.sin(math.pi * 2 * line / rho) / (math.pi * 2 * line / rho)), LINE_AZ),
                    '\n'.join('%s %s dx %s dy %s (%d windows)' % (d, rows[d]['mode'], '%+.3f' % rows[d]['dx'] if rows[d]['dx'] is not None else '-',
                                                              '%+.3f' % rows[d]['dy'] if rows[d]['dy'] is not None else '-', rows[d]['n'])
                              for d in off[:12])))
    m = summ.get('mode')
    if not mixed:
        out.append(('G10m', 'N/A', 'one mode', '', ''))
    elif summ['voting'] < 3:   # the build's reading of 17.4: the mode offset is G10 v3's measurement, not measured with it
        out.append(('G10m', 'WARN', 'NOT MEASURED: G10 v3 not measured (%d voting window(s), fewer than 3)' % summ['voting'],
                    '3 or more voting windows', ''))
    elif not m:
        out.append(('G10m', 'WARN', 'NOT MEASURED: no FBS and FBD dates both read', '', ''))
    else:
        clear = m['dx_ci'][0] > 0 or m['dx_ci'][1] < 0
        sinc = 1.0 if m['dx'] == 0 else abs(math.sin(math.pi * m['dx'] / rho) / (math.pi * m['dx'] / rho))
        out.append(('G10m', 'WARN' if abs(m['dx']) > MODE_LINE and clear else 'INFO',
                    'FBD less FBS: dx %+.4f samples (95 %% %+.4f to %+.4f), dy %+.4f lines (%+.4f to %+.4f); sinc(dx / rho) %.4f; '
                    '%d FBS, %d FBD dates' % (m['dx'], m['dx_ci'][0], m['dx_ci'][1], m['dy'], m['dy_ci'][0], m['dy_ci'][1], sinc,
                                              m['n_fbs'], m['n_fbd']),
                    '|dx| <= %g or its interval holding 0' % MODE_LINE,
                    'a mode offset after R9 has another cause: for Ariel\'s review' if abs(m['dx']) > MODE_LINE and clear else ''))
    return out
