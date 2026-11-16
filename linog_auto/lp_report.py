#!/usr/bin/env python3
"""lp_report.py -- linog_auto Phase 4g (Phase 4.5): the interferogram report, north up from the frame's own geometry.

Runs inside lp_env.sh (numpy and matplotlib from the pinned env). The kit's report (linog_process_all_igrams_v2.sh,
linog_save_insar_images.py 402141d9, linog_create_grid.py 025340aa) flips every frame up-down (line 54, np.flipud),
which is north up for the ascending frames it was written for; on a descending frame line 0 is north and column 0
east, so the kit's pages would come out turned 180 deg (F36). This phase keeps the kit's rendering and layout and takes
the flip from the frame's geom_reference/lat.rdr and lon.rdr (D4): up-down when line 0 is south, left-right when
column 0 is east; it FAILs when that disagrees with the path table's direction (MintPy's auto_flip_direction:
ascending flips up-down, descending left-right). For each pair of Igrams/: filt_<pair>.int read at full resolution,
phase in jet and phase-and-magnitude in HSV (the magnitude stretched between its 1st and 99th percentiles), one pixel
per pixel at 600 dpi, into Igrams/reports/pairs/filt_<pair>_phase.jpg and _combined.jpg; then pages of 12 pairs
(3 rows of 4, phase and combined side by side), US Letter landscape at 300 dpi, as
Igrams/reports/P<PATH>F<FRAME>_Igram_Report_Page_<n>.jpg, the direction and the flip on each page's title.
Nothing outside Igrams/reports/ is written; the kit's flat links in Igrams/ are not made.

Gates
  G4g.1  igram PASS on record; Igrams as igram recorded it                                            FAIL
  G4g.2  environment; matplotlib                                                                       ERROR
  G4g.3  the grid's orientation from lat.rdr and lon.rdr agrees with the path table's direction       FAIL
  G4g.4  nothing in the way: Igrams/reports absent                                                     DECISION
  G4g.5  every pair: two JPEGs of gw x gl pixels                                                       FAIL
  G4g.6  pages: ceil(pairs / 12), each a JPEG                                                          FAIL
--dryrun DIR: the report rendered into DIR/Igrams/reports (the frame is only read); a plan only when the frame's igram
has not run. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
v0.6.1: the two arrays of a pair get imshow's own first steps before imsave (F49), and matplotlib's log stays quiet
after `import isce` (F50).
"""
import argparse
import math
import os
import shutil
import sys
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5

PHASE, IDX, LOGIC = 'report', '4g', 2   # 2 (v0.6.1): the phase image of a pair with NaN (F49)


def stretch(mag, lo, hi):
    """The kit's stretch_magnitude: the magnitude above 1e-6 clipped to its lo..hi percentiles, scaled to 0..1."""
    import numpy as np
    v = mag[mag > 1e-6]
    if v.size == 0:
        return np.zeros_like(mag)
    a, b = np.percentile(v, lo), np.percentile(v, hi)
    if a == b:
        return np.zeros_like(mag)
    return (np.clip(mag, a, b) - a) / (b - a)


def render_pair(src, gw, gl, flipud, fliplr, out_phase, out_comb, dpi, lo, hi):
    """The kit's two images of a pair, written with matplotlib's imsave: the array pixel for pixel, jet over the phase's
    own range, the HSV image as it is, dpi in the JPEG. Where the kit's figure (figsize gw/dpi x gl/dpi, one axes filling
    it, imshow nearest) comes out gw x gl, the JPEGs are identical to the kit's (tested at 778 x 658 and 83 x 658);
    at about 5 % of sizes that figure loses a column or a line to float rounding (79 px wide renders 78), and imsave
    does not (F45).
    Before imsave, the two arrays get what imshow does to them first (matplotlib 3.10, _normalize_image_array): NaN
    masked in the phase, and the HSV image clipped to 0..1 (F49). With felix's numpy 1.26, np.percentile of float32
    magnitudes returns float64 while the stretch stays in float32, so its top can come out one float32 step above 1:
    imshow clips that (the kit's pages), imsave refuses it (S14: 19 of 157 pairs). Unmasked, one NaN made the whole
    phase image blank. hsv_to_rgb assigns no colour to a NaN hue (np.empty_like: whatever the memory held, in the
    kit's image too), so those pixels are set to NaN, which imsave draws transparent: white in the JPEG."""
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.colors as mcolors
    import matplotlib.image as mpimg
    z = np.fromfile(src, dtype=np.complex64, count=gw * gl)
    if z.size != gw * gl:
        raise ValueError('%s holds %d values, want %d' % (src, z.size, gw * gl))
    z = z.reshape(gl, gw)
    if flipud:
        z = np.flipud(z)
    if fliplr:
        z = np.fliplr(z)
    phase, mag = np.angle(z), np.abs(z)
    with np.errstate(invalid='ignore'):   # NaN in the data: hsv_to_rgb casts NaN hues to int
        rgb = mcolors.hsv_to_rgb(np.dstack(((phase + np.pi) / (2 * np.pi), np.ones_like(phase), stretch(mag, lo, hi))))
        np.clip(rgb, 0.0, 1.0, out=rgb)   # imshow's clip of RGB floats (F49)
        rgb[np.isnan(phase)] = np.nan     # no colour for a NaN hue: transparent, white in the JPEG (F49)
    mpimg.imsave(out_phase, np.ma.masked_invalid(phase), cmap='jet', dpi=dpi)   # imshow's mask of NaN (F49)
    mpimg.imsave(out_comb, rgb, dpi=dpi)


def render_page(pairs, n, path, frame, tag, pdir, outdir, dpi, note):
    """The kit's create_grid: 3 rows of 4 pairs, phase and combined side by side, US Letter landscape."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 11, figsize=(11, 8.5), gridspec_kw={'width_ratios': [1, 1, 0.4, 1, 1, 0.4, 1, 1, 0.4, 1, 1]})
    fig.suptitle('Path %s Frame %s - Page %d  (%s)' % (path, frame, n, note), fontsize=14, weight='bold', y=0.96)
    for ax in axes.flatten():
        ax.axis('off')
    for i, pr in enumerate(pairs[:12]):
        row, k = i // 4, (i % 4) * 3
        for j, kind in enumerate(('phase', 'combined')):
            ax = axes[row, k + j]
            ax.imshow(mpimg.imread(os.path.join(pdir, 'filt_%s_%s.jpg' % (pr, kind))))
            ax.set_title('%s\n(%s)' % (pr, kind.capitalize()), fontsize=5, weight='bold')
            ax.axis('off')
    plt.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.05, wspace=0.05, hspace=0.25)
    out = os.path.join(outdir, '%s_Igram_Report_Page_%d.jpg' % (tag, n))
    plt.savefig(out, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return out


def jpeg_shape(p):
    """(height, width) of a JPEG read back, or None when it cannot be read."""
    try:
        import matplotlib.image as mpimg
        a = mpimg.imread(p)
        return a.shape[0], a.shape[1]
    except Exception:  # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4g: the interferogram report, north up (D4)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m = P1.load_env(), P2.load_stack(), P5.load_mintpy()
    geo, _ = P3.geometry(W)
    ri = P1.record(W, '4f', 'igram') or {}
    rt = P1.record(W, '3a', 'topo') or {}
    settings = {k: m[k] for k in ('REPORT_PAIR_DPI', 'REPORT_PAGE_DPI', 'REPORT_PER_PAGE', 'REPORT_STRETCH_LOW', 'REPORT_STRETCH_HIGH')}
    fp = C.md5_obj(dict(logic=LOGIC, igram=ri.get('outputs', {}).get('digest'), topo=rt.get('outputs', {}).get('digest'),
                        direction=cfg['direction'], settings=settings))
    if a.state:
        print(P5.state(recdir, W, PHASE, IDX, fp))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   settings=settings, direction=cfg['direction']))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    ri, have = P5.igram_prior(st, 'G4g.1', W, recdir, a.dryrun)
    if not ri:
        return st.finish()
    if not P2.env_gate(st, 'G4g.2', env, s):
        return st.finish()
    P5.quiet_root()   # matplotlib's start-up and font lookups at DEBUG after `import isce` (S14; F50)
    os.environ.update(P5.mpl_env(recdir))   # matplotlib's cache in the phase's logs, not in HOME
    try:
        import matplotlib
        st.gate('G4g.2p', 'matplotlib', 'PASS', 'matplotlib %s' % matplotlib.__version__, 'importable in the env')
    except Exception as e:  # noqa: BLE001
        st.gate('G4g.2p', 'matplotlib', 'ERROR', 'import matplotlib failed: %s' % e, 'importable in the env')
        return st.finish()
    if not have:
        return P5.plan_only(st, ['would render every pair of Igrams/ into Igrams/reports/ (two JPEGs a pair, pages of %s), north up '
                                 'by the frame\'s lat.rdr and lon.rdr' % m['REPORT_PER_PAGE']], 'the frame has no interferograms yet')
    if not geo:
        st.gate('G4g.3', 'the grid\'s orientation', 'FAIL', 'recon/reference.json gives no geometry')
        return st.finish()
    gw, gl = geo['gw'], geo['gl']
    try:
        o = P5.orientation(W)
    except (OSError, ValueError, TypeError) as e:
        st.gate('G4g.3', 'the grid\'s orientation', 'FAIL', 'cannot read geom_reference/lat.rdr and lon.rdr: %s' % e)
        return st.finish()
    want = P5.expected_flips(cfg['direction'])
    got = (o['flipud'], o['fliplr'])
    dname = 'descending' if cfg['direction'] == 'D' else 'ascending'
    bad = got != want or (o['width'], o['length']) != (gw, gl)
    note = '%s: %s' % (dname, 'north up by a left-right flip' if got == (False, True) else 'north up by an up-down flip'
                       if got == (True, False) else 'flips up-down %s, left-right %s' % got)
    st.gate('G4g.3', 'the grid\'s orientation', 'FAIL' if bad else 'PASS', 'line 0 %s (mean lat %.4f against %.4f at the last), '
            'column 0 %s (mean lon %.4f against %.4f at the last): flip up-down %s, left-right %s; %d x %d' % (
                o['line0'], o['lat_line0'], o['lat_lineN'], o['col0'], o['lon_col0'], o['lon_colN'], got[0], got[1],
                o['width'], o['length']), 'the path table\'s direction %s: up-down %s, left-right %s; grid %d x %d' % (
                cfg['direction'], want[0], want[1], gw, gl),
            'the geometry and the direction disagree: a grid flipped by rule would not be north up' if bad else '')
    st.rec['outputs'] = dict(orientation=o, direction=cfg['direction'])
    if bad:
        return st.finish()
    rdir = os.path.join(recdir, 'Igrams', 'reports')
    if a.dryrun:
        P5.way_gate(st, 'G4g.4', W, PHASE, True)
        if os.path.exists(rdir):
            dst = P2.new_dir(os.path.join(recdir, '_archive', 'reports'))
            shutil.move(rdir, dst)
            print('   an earlier dry run\'s report moved to %s' % dst)
    elif not P5.way_gate(st, 'G4g.4', W, PHASE, False):
        return st.finish()
    pdir = os.path.join(rdir, 'pairs')
    os.makedirs(pdir)
    pairs = P5.pairs_of(W)
    dpi, lo, hi = int(m['REPORT_PAIR_DPI']), float(m['REPORT_STRETCH_LOW']), float(m['REPORT_STRETCH_HIGH'])
    t0 = time.time()
    bad = []
    for i, pr in enumerate(pairs, 1):
        src = os.path.join(W, 'Igrams', pr, 'filt_%s.int' % pr)
        out_p, out_c = (os.path.join(pdir, 'filt_%s_%s.jpg' % (pr, k)) for k in ('phase', 'combined'))
        try:
            render_pair(src, gw, gl, got[0], got[1], out_p, out_c, dpi, lo, hi)
        except (OSError, ValueError) as e:
            bad.append('%s: %s' % (pr, e))
            continue
        for q in (out_p, out_c):
            sh = jpeg_shape(q)
            if sh != (gl, gw):
                bad.append('%s: %s read back as %s, want %d x %d' % (pr, os.path.basename(q), sh, gl, gw))
        if i % 25 == 0 or i == len(pairs):
            print('   rendered %d of %d pairs (%.0f s)' % (i, len(pairs), time.time() - t0))
            sys.stdout.flush()
    njpg = len([n for n in os.listdir(pdir) if n.endswith('.jpg')])
    nfail = len(set(b.split(':', 1)[0] for b in bad))
    if bad:
        st.rec['outputs']['render_failures'] = bad   # every one; the gate's note shows the first 10
    st.gate('G4g.5', 'the pairs rendered', 'FAIL' if bad or njpg != 2 * len(pairs) else 'PASS', '%d pairs: %d JPEGs of %d x %d '
            'px in %.0f s%s' % (len(pairs), njpg, gw, gl, time.time() - t0, '; %d pair%s failed' % (nfail, '' if nfail == 1 else 's')
                                if bad else ''), 'two per pair, one pixel per pixel',
            '\n'.join(bad[:10] + (['... and %d more in the record (outputs.render_failures)' % (len(bad) - 10)] if len(bad) > 10 else [])))
    if bad or njpg != 2 * len(pairs):
        return st.finish()
    per = int(m['REPORT_PER_PAGE'])
    npages = int(math.ceil(len(pairs) / float(per)))
    tag = 'P%sF%s' % (path, frame)
    pages, bad = [], []
    for n in range(npages):
        try:
            pages.append(render_page(pairs[n * per:(n + 1) * per], n + 1, path, frame, tag, pdir, rdir, int(m['REPORT_PAGE_DPI']),
                                     note))
        except (OSError, ValueError) as e:
            bad.append('page %d: %s' % (n + 1, e))
    bad += ['%s cannot be read back' % p for p in pages if not jpeg_shape(p)]
    st.gate('G4g.6', 'the pages', 'FAIL' if bad or len(pages) != npages else 'PASS', '%d page%s of up to %d pairs (%s%s), %.1f MB' % (
        len(pages), '' if len(pages) == 1 else 's', per, os.path.basename(pages[0]) if pages else '-',
        ' to %s' % os.path.basename(pages[-1]) if len(pages) > 1 else '', sum(os.path.getsize(p) for p in pages) / 1e6),
        'ceil(%d / %d) = %d, each a JPEG' % (len(pairs), per, npages), '\n'.join(bad[:5]))
    lst = P3.listing(recdir, P5.OUTS[PHASE])
    st.rec['outputs'].update(pairs=len(pairs), jpegs=njpg, pages=len(pages), files=lst, digest=P3.digest(lst), seconds=round(time.time() - t0, 1),
                             note=note)
    if a.dryrun:
        st.rec['outputs'].update(planned=True, dryrun=True)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_report', main)
