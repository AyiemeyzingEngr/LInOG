#!/usr/bin/env python3
"""MOCK smallbaselineApp.py (linog_auto self-test only; nothing here runs on real data). MintPy 1.6.2's step list, banners
and the files a stripmapStack run writes, from the template, on the frame's own grid:
  load_data         prep_isce as 1.6.2's load_data calls it (the metadata file, the geometry folder of demFile, the
                    baseline folder, unwFile, the geometry files' names; update mode: nothing rewritten that is
                    already there), then inputs/ifgramStack.h5 (date, dropIfgram, bperp, unwrapPhase, coherence,
                    connectComponent; HEADING from the metadata file's data.rsc; every MACRO_CASE template key as an
                    attribute) and inputs/geometryRadar.h5 (latitude, longitude, height, incidenceAngle, azimuthAngle;
                    shadowMask when its file is named). A metadata file that matches nothing gives MintPy's two
                    warnings (F40); an .unw without its .rsc raises KeyError 'STARTING_RANGE' (G12). updateMode no:
                    always reloads.
  modify_network    waterMask.h5 from geometryRadar.h5's waterMask when it has one (1.6.2: smallbaselineApp.py 219-233; the
                    geometry's waterMask only under LINOG_MOCK_WATERMASK=1, v0.12 r2), then dropIfgram from excludeDate and
                    excludeDate12
  reference_point   maskConnComp.h5 (v0.8: the kept pairs' connected components all non-zero, as 1.6.2's generate_mask.py
                    --nonzero writes it first), then REF_Y, REF_X on the stack: reference.yx (refused, as 1.6.2 refuses it,
                    when the pixel's connected component is 0 in a kept pair), or (auto) the highest mean coherence
  quick_overview    avgSpatialCoh.h5
  correct_unwrap_error   bridging: unwrapPhase_bridging in the stack
  invert_network    timeseries.h5 (REF_Y, REF_X), temporalCoherence.h5, numInvIfgram.h5, maskTempCoh.h5
  deramp, correct_topography, residual_RMS   timeseries_ramp.h5, timeseries_ramp_demErr.h5, demErr.h5,
                    timeseriesResidual.h5
  velocity          velocity.h5
  geocode           geo/geo_velocity.h5, geo_temporalCoherence.h5, geo_maskTempCoh.h5, geo_geometryRadar.h5,
                    geo_timeseries_ramp_demErr.h5 on the SNWE and laloStep grid (v0.7: each geocoded from its radar file
                    by the mock mintpy.cli.geocode, nearest neighbour through the geometry's latitude and longitude)
After a call of more than one step, with mintpy.plot not no: 1.6.2's plot banner and pic/ (plot_result).
v0.7, the self-test's scene (linog_mock3.scene): load_data gives geometryRadar.h5 a textured land and a sea flat at
44 m (the mock topo's hgt.rdr is flat outside the kit gates' three windows, and texturing it would move the windows),
and invert_network gives the sea's decorrelated half a temporal coherence of 0.3; the time series carry REF_DATE and
their dates, as MintPy's do.
Planted: LINOG_MOCK_F40=1 prints F40's two warnings in load_data; LINOG_MOCK_SBASFAIL=<step> raises at the start of
that step, <step>:late after its files are written; LINOG_MOCK_PLOTFAIL=1 raises in the plots.
v0.8, the A/B after sbas (d9ab) runs this mock on its copy with unwrapError bridging: bridging copies unwrapPhase into
unwrapPhase_bridging (B's products then equal A's), and, planted for a run with bridging only: LINOG_MOCK_B_GAIN=1 gives
the copy's unwrapPhase a smooth field with an unwrapping error on a block of the first kept pair, which bridging corrects
(one pair changed; T_int falls there), and the sea's decorrelated half a temporal coherence of 0.9 in invert_network
(B's mask gains it); LINOG_MOCK_B_VSTD=<mm/yr> adds noise of that std to B's
velocity; LINOG_MOCK_P6SLEEP=smallbaselineApp with LINOG_MOCK_MARK (linog_mock6.planted_fail) sleeps at the start;
LINOG_MOCK_B_TOUCH=<file> appends a line to that file (in A's mintpy/: the A/B is then void).
v0.12 (drop1): invert_network applies linog_mock3.d1_plant (LINOG_MOCK_D1BAD), as the mock ifgram_inversion.py does.
v0.10 (admit's rules, dfit): invert_network's dates are the kept pairs' (a date excludeDate drops leaves the series, as in
MintPy); LINOG_MOCK_TS=<rate mm/yr>[:<date>:<amp mm>] gives the series a uniform rate (v0.13 r2: on MintPy's decimal years,
the ascending record 15.4) and, on that date, a ramp across
the columns from -amp to +amp (an atmospheric date: its exclusion from the fit lowers the velocity's spread); residual_RMS
writes exclude_date.txt with LINOG_MOCK_RMSOUT=<date> (MintPy's own outlier) and otherwise removes one it finds there, as
1.6.2's timeseries_rms does; velocity is linog_mock6.fit_velocity on timeseries_ramp_demErr.h5 without the template's
mintpy.timeFunc.excludeDate (auto: exclude_date.txt), the mock timeseries2velocity's arithmetic.
"""
import argparse
import glob
import importlib.util
import os
import re
import sys

import h5py
import numpy as np

import linog_mock3 as M3
from mintpy.cli import geocode as G

STEP_LIST = ['load_data', 'modify_network', 'reference_point', 'quick_overview', 'correct_unwrap_error', 'invert_network',
             'correct_LOD', 'correct_SET', 'correct_ionosphere', 'correct_troposphere', 'deramp', 'correct_topography',
             'residual_RMS', 'reference_date', 'velocity', 'geocode', 'google_earth', 'hdfeos5']   # 1.6.2 template.py


def read_template(p):
    d = {}
    for ln in open(p):
        s = ln.strip()
        if not s or s.startswith(('#', '%')) or '=' not in s:
            continue
        k, v = s.split('=', 1)
        d[k.strip()] = v.split('#', 1)[0].strip()
    return d


def dims(p):
    x = open(p + '.xml').read()
    return tuple(int(re.search(r'name="%s">\s*<value>\s*(\d+)' % n, x).group(1)) for n in ('width', 'length'))


def rsc(p):
    d = {}
    for ln in open(p):
        w = ln.split(None, 1)
        if len(w) == 2:
            d[w[0]] = w[1].strip()
    return d


def val(t, k):
    v = t.get(k, 'auto')
    return None if v in ('auto', 'no', 'none', '') else v


def prep(t, meta):
    """1.6.2 load_data.prepare_metadata for isce: prep_isce with the template's files, in update mode."""
    spec = importlib.util.spec_from_file_location('mock_prep_isce', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prep_isce.py'))
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    gkeys = ('demFile', 'lookupYFile', 'lookupXFile', 'incAngleFile', 'azAngleFile', 'shadowMaskFile', 'waterMaskFile')
    gfiles = [os.path.basename(t['mintpy.load.' + k]) for k in gkeys if val(t, 'mintpy.load.' + k)]
    P.run(meta, os.path.abspath(os.path.dirname(t['mintpy.load.demFile'])), t.get('mintpy.load.baselineDir'),
          [t['mintpy.load.unwFile']], gfiles, update=True)


def load_data(t):
    meta = t.get('mintpy.load.metaFile', 'auto')
    metas = sorted(glob.glob(meta))
    if os.environ.get('LINOG_MOCK_F40') or not metas:
        print('WARNING: No input metadata file found: %s' % meta)
        print("UserWarning: prep_isce.py failed. Assuming its result exists and continue...")
    else:
        prep(t, metas[0])
    unw = sorted(glob.glob(t['mintpy.load.unwFile']))
    if not unw:
        raise SystemExit('ERROR: no interferogram found with %s' % t['mintpy.load.unwFile'])
    for f in unw:
        if not os.path.isfile(f + '.rsc'):
            raise KeyError('STARTING_RANGE')
    drsc = os.path.join(os.path.dirname(meta), 'data.rsc')
    head = rsc(drsc).get('HEADING', 'nan') if os.path.isfile(drsc) else 'nan'
    upd = t.get('mintpy.load.updateMode', 'auto')
    stack, geom = os.path.join('inputs', 'ifgramStack.h5'), os.path.join('inputs', 'geometryRadar.h5')
    if upd != 'no' and os.path.isfile(stack) and os.path.isfile(geom):
        print('update mode: ON; both files exist and are complete: skip loading')
        return
    os.makedirs('inputs', exist_ok=True)
    w, l = dims(unw[0])
    pairs = [os.path.basename(os.path.dirname(f)) for f in unw]
    cor = dict((os.path.basename(os.path.dirname(f)), f) for f in glob.glob(t['mintpy.load.corFile']))
    cc = dict((os.path.basename(os.path.dirname(f)), f) for f in glob.glob(t['mintpy.load.connCompFile']))
    n = len(pairs)
    with h5py.File(stack, 'w') as f:
        f.create_dataset('date', data=np.array([[p[:8].encode(), p[9:].encode()] for p in pairs]))
        f.create_dataset('dropIfgram', data=np.ones(n, bool))
        f.create_dataset('bperp', data=np.zeros(n, np.float32))
        u = f.create_dataset('unwrapPhase', (n, l, w), np.float32)
        c = f.create_dataset('coherence', (n, l, w), np.float32)
        k = f.create_dataset('connectComponent', (n, l, w), np.int16)
        for i, p in enumerate(pairs):
            u[i] = np.fromfile(unw[i], '<f4', count=2 * w * l).reshape(l, 2 * w)[:, w:] if os.path.getsize(unw[i]) >= 8 * w * l \
                else 0
            c[i] = np.fromfile(cor[p], '<f4', count=w * l).reshape(l, w)
            k[i] = np.fromfile(cc[p], np.uint8, count=w * l).reshape(l, w)
        f.attrs.update(dict(FILE_TYPE='ifgramStack', LENGTH=str(l), WIDTH=str(w), HEADING=head, PLATFORM='Alos', PROCESSOR='isce'))
        for key, v in t.items():
            if key.isupper():
                f.attrs[key] = v
    with h5py.File(geom, 'w') as f:
        for name, key, dt, band in (('latitude', 'mintpy.load.lookupYFile', '<f8', 1), ('longitude', 'mintpy.load.lookupXFile', '<f8', 1),
                                    ('height', 'mintpy.load.demFile', '<f8', 1), ('incidenceAngle', 'mintpy.load.incAngleFile', '<f4', 1),
                                    ('azimuthAngle', 'mintpy.load.azAngleFile', '<f4', 2), ('shadowMask', 'mintpy.load.shadowMaskFile',
                                                                                         'u1', 1)):
            p = val(t, key)
            if not p or not os.path.isfile(p):
                continue
            a = np.fromfile(p, dt, count=band * w * l)
            a = a[(band - 1) * w * l:band * w * l].reshape(l, w)
            if name == 'height':   # v0.7: the scene's ground (see the module's docstring)
                sc = M3.scene(l, w)
                a = a + 3.0 * np.random.RandomState(7).normal(size=a.shape)
                a[sc['sea']] = 44.0
            f.create_dataset(name, data=a.astype(np.float32 if dt != 'u1' else np.bool_))
        if os.environ.get('LINOG_MOCK_WATERMASK'):   # v0.12 r2: a geometry holding a waterMask (1 on land, 0 on the scene's sea)
            f.create_dataset('waterMask', data=~M3.scene(l, w)['sea'])
        f.attrs.update(dict(FILE_TYPE='geometry', LENGTH=str(l), WIDTH=str(w)))
    print('Loaded %d interferograms of %d x %d into %s and %s' % (n, l, w, stack, geom))


def modify_network(t):
    with h5py.File('inputs/geometryRadar.h5', 'r') as f:   # v0.12 r2: 1.6.2 writes waterMask.h5 when the geometry holds a waterMask
        wm = f['waterMask'][()] if 'waterMask' in f else None
        ga = dict(f.attrs)
    if wm is not None:
        print('generate waterMask.h5 from inputs/geometryRadar.h5 for conveniency')
        write1('waterMask.h5', 'waterMask', wm, dict(ga, FILE_TYPE='waterMask'))
    ed = [x for x in (val(t, 'mintpy.network.excludeDate') or '').split(',') if x]
    e12 = [x for x in (val(t, 'mintpy.network.excludeDate12') or '').split(',') if x]
    with h5py.File('inputs/ifgramStack.h5', 'r+') as f:
        d12 = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][:]]
        keep = np.array([not (p in e12 or p[:8] in ed or p[9:] in ed) for p in d12])
        f['dropIfgram'][:] = keep
    print('number of interferograms to keep: %d of %d' % (keep.sum(), len(keep)))


def reference_point(t):
    with h5py.File('inputs/ifgramStack.h5', 'r') as f:   # v0.8: maskConnComp.h5 first (1.6.2: generate_mask.py --nonzero)
        keep = f['dropIfgram'][:]
        mc = np.all(f['connectComponent'][:][keep] != 0, axis=0)
        a = dict(f.attrs)
    write1('maskConnComp.h5', 'mask', mc, dict(a, FILE_TYPE='mask'))
    with h5py.File('inputs/ifgramStack.h5', 'r+') as f:
        keep = f['dropIfgram'][:]
        yx = val(t, 'mintpy.reference.yx')
        if yx:
            y, x = (int(v) for v in yx.split(','))
            print('input reference point in y/x: (%d, %d)' % (y, x))
            if (f['connectComponent'][:, y, x][keep] == 0).any():     # 1.6.2: maskConnComp.h5 from the kept pairs
                raise ValueError('input reference point is in masked OUT area defined by maskConnComp.h5!')
        else:
            av = f['coherence'][:][keep].mean(axis=0)
            k = int(np.argmax(av))
            y, x = k // av.shape[1], k % av.shape[1]
            print('random select pixel with coherence > 0.85')
        f.attrs.update(dict(REF_Y=str(y), REF_X=str(x)))
    print('reference point: y, x = %d, %d' % (y, x))


def write1(p, name, data, attrs):
    with h5py.File(p, 'w') as f:
        f.create_dataset(name, data=data)
        f.attrs.update(attrs)


def write_ts(out, src):
    """A time-series file from another, its dates and attributes kept (MintPy's deramp and dem_error write them so)."""
    with h5py.File(src, 'r') as f:
        ts, dates, a = f['timeseries'][:], f['date'][:], dict(f.attrs)
    with h5py.File(out, 'w') as f:
        f.create_dataset('timeseries', data=ts)
        f.create_dataset('date', data=dates)
        f.attrs.update(a)


def stack_attrs():
    with h5py.File('inputs/ifgramStack.h5', 'r') as f:
        a = dict(f.attrs)
        keep = f['dropIfgram'][:]
        coh = f['coherence'][:][keep]
        # v0.10: the kept pairs' dates (a date excludeDate drops leaves the time series, as in MintPy)
        dates = sorted(set(d for x, k in zip(f['date'][:], keep) if k for d in (x[0].decode(), x[1].decode())))
    return a, coh, dates


def run_step(s, t):
    plant = os.environ.get('LINOG_MOCK_SBASFAIL', '')
    if plant == s:
        raise RuntimeError('MOCK: step %s failed (planted)' % s)
    if s == 'load_data':
        load_data(t)
    elif s == 'modify_network':
        modify_network(t)
    elif s == 'reference_point':
        reference_point(t)
    elif s == 'quick_overview':
        a, coh, _ = stack_attrs()
        write1('avgSpatialCoh.h5', 'coherence', coh.mean(axis=0), a)
    elif s == 'correct_unwrap_error':
        m = t.get('mintpy.unwrapError.method', 'auto')
        if m in ('bridging', 'bridging+phase_closure'):
            with h5py.File('inputs/ifgramStack.h5', 'r+') as f:
                if 'unwrapPhase_bridging' in f:
                    del f['unwrapPhase_bridging']
                b = f['unwrapPhase'][:]
                if os.environ.get('LINOG_MOCK_B_GAIN'):
                    # v0.8 plant (as RD8's harness): the copy's unwrapPhase becomes a smooth field whose every triplet closes
                    # to 0.25 rad, with a block of the first kept pair off by -2 pi (an unwrapping error); bridging's output
                    # is the field without the error (the block moved by 2 pi in that pair)
                    d12 = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][:]]
                    dates = sorted(set(d for q in d12 for d in q.split('_')))
                    n, L, W = b.shape
                    yy, xx = np.mgrid[0:L, 0:W].astype(np.float32)
                    f0 = yy / L + 2. * xx / W
                    for i, q in enumerate(d12):
                        ia, ib = (dates.index(x) for x in q.split('_'))
                        b[i] = (0.8 * (ib - ia) * f0 + 0.25).astype(np.float32)
                    k0 = int(np.where(f['dropIfgram'][:])[0][0])
                    u = b.copy()
                    u[k0, L // 4:L // 2, W // 4:W // 2] -= 2. * np.pi
                    f['unwrapPhase'][:] = u
                f.create_dataset('unwrapPhase_bridging', data=b)
            print('bridging: unwrapPhase_bridging written%s' % (' (MOCK plant: a smooth field; a block of the first kept pair off by '
                                                                 '-2 pi in unwrapPhase, corrected in unwrapPhase_bridging)'
                                                                 if os.environ.get('LINOG_MOCK_B_GAIN') else ''))
        else:
            print('phase-unwrapping error correction is OFF.')
    elif s == 'invert_network':
        a, coh, dates = stack_attrs()
        l, w = coh.shape[1:]
        ts = np.zeros((len(dates), l, w), np.float32)
        if os.environ.get('LINOG_MOCK_TS'):   # v0.10 plant: a rate, and an atmospheric date
            import linog_mock6 as M6
            q = os.environ['LINOG_MOCK_TS'].split(':')
            # v0.13 r2 (the ascending record 15.4, 16.4): on MintPy's decimal years, as the mock velocity fit, so a planted rate
            # reads back exactly (v0.10 to v0.13 r1: days since the first date / 365.25)
            t = np.array([M6.yyyymmdd2years(d) - M6.yyyymmdd2years(dates[0]) for d in dates])
            ts += (float(q[0]) / 1000.0 * t)[:, None, None].astype(np.float32)
            if len(q) == 3 and q[1] in dates:
                ramp = float(q[2]) / 1000.0 * (2.0 * np.arange(w) / max(w - 1, 1) - 1.0)
                ts[dates.index(q[1])] += ramp[None, :].astype(np.float32)
            print('invert_network (MOCK plant): rate %s mm/yr%s' % (q[0], '; %s carries a ramp of %s mm' % (q[1], q[2]) if len(q) == 3 else ''))
        with h5py.File('timeseries.h5', 'w') as f:
            f.create_dataset('timeseries', data=ts)
            f.create_dataset('date', data=np.array([d.encode() for d in dates]))
            f.attrs.update(dict(a, FILE_TYPE='timeseries', REF_DATE=dates[0]))
        tc = np.clip(coh.mean(axis=0) + 0.2, 0, 1)
        tc[M3.scene(l, w)['decor']] = 0.3   # v0.7: the sea's decorrelated half
        with h5py.File('inputs/ifgramStack.h5', 'r') as f:   # v0.12: drop1's plant (linog_mock3.d1_plant)
            tc = M3.d1_plant(tc, [(x[0].decode(), x[1].decode()) for x in f['date'][:]], f['dropIfgram'][:])
        if os.environ.get('LINOG_MOCK_B_GAIN') and t.get('mintpy.unwrapError.method') == 'bridging':
            tc[M3.scene(l, w)['decor']] = 0.9   # v0.8 plant: B's mask gains the sea's decorrelated half
            print('invert_network (MOCK plant): temporal coherence 0.9 over the sea\'s decorrelated half')
        write1('temporalCoherence.h5', 'temporalCoherence', tc, dict(a, FILE_TYPE='temporalCoherence'))
        write1('numInvIfgram.h5', 'mask', np.full((l, w), coh.shape[0], np.int16), a)
        write1('maskTempCoh.h5', 'mask', tc >= 0.7, dict(a, FILE_TYPE='mask'))
    elif s == 'deramp':
        write_ts('timeseries_ramp.h5', 'timeseries.h5')
    elif s == 'correct_topography':
        a = dict(h5py.File('timeseries.h5', 'r').attrs)
        write_ts('timeseries_ramp_demErr.h5', 'timeseries_ramp.h5')
        write1('demErr.h5', 'dem', np.zeros(h5py.File('timeseries.h5', 'r')['timeseries'].shape[1:], np.float32), a)
    elif s == 'residual_RMS':
        a = dict(h5py.File('timeseries.h5', 'r').attrs)
        write1('timeseriesResidual.h5', 'timeseries', h5py.File('timeseries.h5', 'r')['timeseries'][:], a)
        if os.environ.get('LINOG_MOCK_RMSOUT'):   # v0.10 plant: MintPy's own outlier date
            with open('exclude_date.txt', 'w') as fh:
                fh.write(os.environ['LINOG_MOCK_RMSOUT'] + '\n')
            print('date(s) with RMS > 3.0 * median RMS (MOCK plant)\n%s\nsave date(s) to file: exclude_date.txt' % os.environ['LINOG_MOCK_RMSOUT'])
        else:
            print('date(s) with RMS > 3.0 * median RMS\nNone.')
            if os.path.isfile('exclude_date.txt'):
                os.remove('exclude_date.txt')   # as 1.6.2's timeseries_rms.analyze_rms does
    elif s == 'velocity':
        a = dict(h5py.File('timeseries.h5', 'r').attrs)
        import linog_mock6 as M6
        v = M6.fit_velocity('timeseries_ramp_demErr.h5', M6.template_exclude('smallbaselineApp.cfg'))[0]['velocity']
        if os.environ.get('LINOG_MOCK_B_VSTD') and t.get('mintpy.unwrapError.method') == 'bridging':   # v0.8 plant
            v += np.random.RandomState(8).normal(0., float(os.environ['LINOG_MOCK_B_VSTD']) / 1000., v.shape).astype(np.float32)
            print('velocity (MOCK plant): noise of %s mm/yr' % os.environ['LINOG_MOCK_B_VSTD'])
        write1('velocity.h5', 'velocity', v, dict(a, FILE_TYPE='velocity'))
    elif s == 'geocode':
        rows, cols, ga = G.grid(t['mintpy.geocode.SNWE'], t['mintpy.geocode.laloStep'])
        lat, lon = G.lookup('inputs/geometryRadar.h5')
        im = G.index_map(lat, lon, rows, cols, ga)
        os.makedirs('geo', exist_ok=True)
        for n in ('velocity.h5', 'temporalCoherence.h5', 'maskTempCoh.h5', 'inputs/geometryRadar.h5', 'timeseries_ramp_demErr.h5'):
            G.geocode_file(n, os.path.join('geo', 'geo_' + os.path.basename(n)), im, ga, lat, lon)
    else:
        print('%s: skip (MOCK)' % s)
    if plant == s + ':late':
        raise RuntimeError('MOCK: step %s failed after writing its files (planted)' % s)


def plot_result(t):
    print('\n******************** plot & save to pic ********************')
    os.makedirs('pic', exist_ok=True)
    for n in ('velocity.png', 'temporalCoherence.png', 'maskTempCoh.png'):
        if os.path.isfile(n.replace('.png', '.h5')):
            open(os.path.join('pic', n), 'w').write('MOCK plot\n')
    if os.environ.get('LINOG_MOCK_PLOTFAIL'):
        raise RuntimeError('MOCK: view.py failed while plotting (planted)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('customTemplateFile', nargs='?')
    ap.add_argument('--dostep')
    ap.add_argument('--start', default=STEP_LIST[0])
    ap.add_argument('--end', '--stop', dest='end', default=STEP_LIST[-1])
    a = ap.parse_args()
    if os.path.basename(os.getcwd()) != 'mintpy' or not a.customTemplateFile or not os.path.isfile(a.customTemplateFile):
        raise SystemExit('MOCK smallbaselineApp.py: run it from a mintpy/ folder with its template (cwd %s)' % os.getcwd())
    t = read_template(a.customTemplateFile)
    import linog_mock6 as M6   # v0.8: LINOG_MOCK_P6SLEEP=smallbaselineApp (the A/B's stop case)
    M6.planted_fail('smallbaselineApp')
    if os.environ.get('LINOG_MOCK_B_TOUCH') and t.get('mintpy.unwrapError.method') == 'bridging':   # v0.8: A written during B's run
        with open(os.environ['LINOG_MOCK_B_TOUCH'], 'a') as fh:
            fh.write('MOCK: written while MintPy ran on the A/B\'s copy (planted)\n')
    steps = [a.dostep] if a.dostep else STEP_LIST[STEP_LIST.index(a.start):STEP_LIST.index(a.end) + 1]
    print('Project name: %s' % os.path.splitext(os.path.basename(a.customTemplateFile))[0])
    print('Run routine processing with smallbaselineApp.py on steps: %s' % steps)
    for s in steps:
        print('\n\n******************** step - %s ********************' % s)
        run_step(s, t)
    if t.get('mintpy.plot', 'auto') != 'no' and len(steps) > 1:   # 1.6.2 run_smallbaselineApp
        plot_result(t)
    print('\nNormal end of smallbaselineApp processing!')


if __name__ == '__main__':
    sys.exit(main())
