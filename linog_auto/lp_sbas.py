#!/usr/bin/env python3
"""lp_sbas.py -- linog_auto Phase 5d: the MintPy time series, with the reference pixel pinned by the kit's G19.

Runs inside lp_env.sh, MintPy from mintpy/ (Phase 5's second working folder), in the order that works (the recipe:
prep_isce, load_data, modify_network, G19, then the rest), which inverts once:
  1. smallbaselineApp.py smallbaselineApp.cfg --dostep load_data, then --dostep modify_network (updateMode no: a
     fresh stack, G15; the pairs admit excluded dropped). One step a call: after a call of more than one step MintPy
     plots into pic/, and at this point there is nothing to plot.
  2. the kit's linog_refpix.py (cf7e059d) from the frame folder with --edge G19_EDGE: the pixel of highest 5 x 5
     minimum coherence inside the main component of the kept pairs (G19); MintPy's own pick is random among pixels
     above 0.85 temporal average. recon/refpix.txt (the operator's, optional: one line `mintpy.reference.yx = y,x`)
     takes the place of the kit's pick. Either must be unwrapped (connected component above 0) in every kept pair:
     MintPy's reference_point refuses a pixel its maskConnComp.h5 masks out.
  3. mintpy.reference.yx = y,x on its one line of the template (the only change to mcfg's template)
  4. smallbaselineApp.py smallbaselineApp.cfg --start reference_point --end geocode; MintPy then plots into pic/ (so
     did the kit's second pass). An error after its plot banner, with every step run, is a WARN: the products are made.
The kit's driver inverts twice (load_data to geocode with a random reference, then reference_point to geocode with
G19's); the products after the second pass are the ones this order gives.

Gates
  G5d.1  mcfg PASS on record, its template as it wrote it (reference.yx aside)                       FAIL
  G5d.2  environment; MintPy at its pin                                                  ERROR / FAIL
  G5d.3  smallbaselineApp.py on the PATH is the pinned env's; the kit's linog_refpix.py at its pin    FAIL
  G5d.3o recon/refpix.txt, when present: one mintpy.reference.yx = y,x line                           FAIL
  G5d.4  nothing in the way: mintpy/timeseries.h5, velocity.h5 and geo/ absent                        DECISION
  G5d.5  load_data, then modify_network: rc 0 each; F40's two warnings absent                         FAIL
  G15    ifgramStack.h5 written by this run's load_data, after every .unw (N19); updateMode no          FAIL
  G24    the stack's HEADING in the direction's band; ORBIT_DIRECTION as the template writes it        FAIL
  G5d.6  the stack: its pairs the network's; kept (dropIfgram) = admit's kept pairs                    FAIL
  G19    the reference pixel, the kit's (rc 0) or the operator's: inside the grid; unwrapped in every kept
         pair; on its template line, the rest of the template as mcfg wrote it; the kit's mean component
         fraction beside admit's D9. No usable pick from the kit: DECISION (recon/refpix.txt); the
         operator's pixel not usable: FAIL                                                  FAIL / DECISION
  G5d.7  reference_point to geocode: rc 0; those steps; F40's warnings absent; an error in the plots
         after the last step: WARN                                                               FAIL / WARN
  G5d.8  the products: timeseries.h5 REF_Y, REF_X the pixel; temporalCoherence.h5, maskTempCoh.h5,
         timeseries_ramp_demErr.h5, velocity.h5; geo/: geo_velocity.h5, geo_temporalCoherence.h5,
         geo_maskTempCoh.h5, geo_geometryRadar.h5 (N14); unwrapPhase_bridging in the stack when bridging  FAIL
--state: STALE also when the template changed since this phase ran (reference.yx included: recon/refpix.txt is the
way to choose the pixel). --dryrun DIR: a plan only. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import glob
import json
import os
import re
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5

PHASE, IDX, LOGIC = 'sbas', '5d', 1
KIT = 'linog_refpix.py'
GEO = ('geo_velocity.h5', 'geo_temporalCoherence.h5', 'geo_maskTempCoh.h5', 'geo_geometryRadar.h5')
RADAR = ('timeseries.h5', 'temporalCoherence.h5', 'maskTempCoh.h5', 'timeseries_ramp_demErr.h5', 'velocity.h5')


def mintpy_call(mdir, args, log, W):
    rc, out = P5.run_logged(['smallbaselineApp.py', 'smallbaselineApp.cfg'] + args, mdir, log, P5.mpl_env(W))
    return rc, out, P5.steps_run(out), P5.f40_lines(out)


def read_refpix(p):
    """((y, x) or None, problems) of the operator's recon/refpix.txt."""
    vals, bad = [], []
    for i, ln in enumerate(open(p), 1):
        s = ln.split('#', 1)[0].strip()
        if not s:
            continue
        m = re.match(r'^mintpy\.reference\.yx\s*=\s*(\d+)\s*,\s*(\d+)$', s)
        if m:
            vals.append((int(m.group(1)), int(m.group(2))))
        else:
            bad.append('line %d: %r is not "mintpy.reference.yx = y,x"' % (i, s))
    if len(vals) != 1:
        bad.append('%d mintpy.reference.yx lines, want 1' % len(vals))
    return (vals[0] if not bad else None), bad


def masked_in(ih, yx):
    """The kept pairs whose connected component is 0 at yx (MintPy's maskConnComp.h5, the pixels unwrapped in every
    kept pair, masks such a pixel out)."""
    import h5py
    with h5py.File(ih, 'r') as f:
        d12 = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][:]]
        drop = f['dropIfgram'][:]
        cc = f['connectComponent'][:, yx[0], yx[1]]
    return [p for p, k, c in zip(d12, drop, cc) if k and c == 0]


def unwrapped_everywhere(ih):
    """(pixels unwrapped in every kept pair, [(pair, its unwrapped pixels)] fewest first): maskConnComp.h5's count, one
    pair at a time."""
    import h5py
    per, common = [], None
    with h5py.File(ih, 'r') as f:
        d12 = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][:]]
        drop = f['dropIfgram'][:]
        for i, (p, k) in enumerate(zip(d12, drop)):
            if not k:
                continue
            nz = f['connectComponent'][i] != 0
            per.append((p, int(nz.sum())))
            common = nz if common is None else (common & nz)
    return (int(common.sum()) if common is not None else 0), sorted(per, key=lambda x: (x[1], x[0]))


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5d: the MintPy time series (G15, G19, G24, N14)')
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
    tm = P5.tools(env, m)
    optxt = os.path.join(W, 'recon', 'refpix.txt')
    rm = P1.record(recdir, '5c', 'mcfg') or {}
    ra = P1.record(recdir, '5a', 'admit') or {}
    # the operator's pixel as read (a comment edit changes nothing); MintPy's version and defaults, as mcfg's
    op_fp = read_refpix(optxt)[0] if os.path.isfile(optxt) else None
    fp = C.md5_obj(dict(logic=LOGIC, mcfg=rm.get('outputs', {}).get('cfg_digest'), admit=ra.get('outputs', {}).get('decisions_md5'),
                        kit=tm[KIT][1], heading_tol=m['HEADING_TOL_DEG'], direction=cfg['direction'], edge=m['G19_EDGE'],
                        operator=list(op_fp) if op_fp else None, mintpy=m['MINTPY_VERSION'], defaults=m['MINTPY_DEFAULTS_MD5']))
    tfile = os.path.join(recdir, 'mintpy', 'smallbaselineApp.cfg')

    def template_changed(rec):
        # the template as this phase left it: any line mcfg wrote (its digest), and reference.yx (the pixel this phase set)
        o = (rec or {}).get('outputs', {})
        yx = (o.get('refpix') or {}).get('yx')
        if o.get('planned') or not yx:
            return []
        if not os.path.isfile(tfile):
            return ['gone: mintpy/smallbaselineApp.cfg']
        txt = open(tfile).read()
        out = [] if P5.cfg_digest(txt) == o.get('cfg_digest') else ['changed: mintpy/smallbaselineApp.cfg (other than reference.yx)']
        now = P5.cfg_dict(txt).get('mintpy.reference.yx')
        if now != '%d,%d' % tuple(yx):
            out.append('changed: mintpy.reference.yx reads %s, this phase set %d,%d (recon/refpix.txt chooses the pixel)' % (
                now, yx[0], yx[1]))
        return out
    if a.state:
        print(P5.state(recdir, W, PHASE, IDX, fp, extra=template_changed))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   tools={KIT: dict(path=tm[KIT][0], md5=tm[KIT][1])},
                                                                   operator_file=optxt if os.path.isfile(optxt) else None))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    rm = P5.prior5(st, 'G5d.1', recdir, W, '5c', 'mcfg', outs=False, dry=bool(a.dryrun))
    if not rm:
        return st.finish()
    mdir = os.path.join(recdir, 'mintpy')
    if not rm.get('outputs', {}).get('planned'):
        dg = P5.cfg_digest(open(tfile).read()) if os.path.isfile(tfile) else None
        ok = dg == rm.get('outputs', {}).get('cfg_digest')
        st.gate('G5d.1t', 'mcfg\'s template', 'PASS' if ok else 'FAIL', '%s %s' % (tfile, 'as mcfg wrote it (reference.yx aside)' if ok
                                                                                  else 'changed since mcfg wrote it' if dg else 'absent'),
                'the digest mcfg recorded')
        if not ok:
            return st.finish()
    mi = P5.env_gate(st, 'G5d.2', env, s, m)
    if not mi:
        return st.finish()
    if not P5.which_gate(st, 'G5d.3', s, ('smallbaselineApp.py',)) or not P3.pins_gate(st, 'G5d.3k', {KIT: tm[KIT]}, 'the kit\'s G19 tool'):
        return st.finish()
    op_yx = None
    if os.path.isfile(optxt):
        op_yx, obad = read_refpix(optxt)
        st.gate('G5d.3o', 'recon/refpix.txt', 'FAIL' if obad else 'INFO', 'mintpy.reference.yx = %d,%d (the operator\'s)' % op_yx if op_yx
                else 'unreadable', 'one mintpy.reference.yx = y,x line', '\n'.join(obad[:5]))
        if obad:
            return st.finish()
    if a.dryrun:
        P5.way_gate(st, 'G5d.4', W, PHASE, True)
        md = os.path.join(W, 'mintpy')
        print('   would run from %s: smallbaselineApp.py smallbaselineApp.cfg --dostep load_data, then --dostep modify_network' % md)
        print('   then %s --edge %s from %s, and %s into mintpy.reference.yx' % (
            KIT, m['G19_EDGE'], W, 'the operator\'s %d,%d (recon/refpix.txt)' % op_yx if op_yx else 'its pick'))
        print('   then smallbaselineApp.py smallbaselineApp.cfg --start reference_point --end geocode (%s), and MintPy\'s plots' %
              ' '.join(P5.steps_between('reference_point', 'geocode')))
        st.rec['outputs'] = dict(planned=True, dryrun=True)
        return st.finish('plan only (dry run)')
    if not P5.way_gate(st, 'G5d.4', W, PHASE, False):
        return st.finish()
    logd = os.path.join(W, 'logs', 'p5', 'sbas')
    t_load = time.time()
    rcs, steps, warn, logs = [], [], [], []
    for step in ('load_data', 'modify_network'):
        lg = P1.new_log(os.path.join(logd, 'smallbaseline_%s.log' % step))
        rc, out, sp, wn = mintpy_call(mdir, ['--dostep', step], lg, W)
        rcs.append(rc)
        steps += sp
        warn += wn
        logs.append(lg)
        if rc != 0:
            break
    bad = any(rcs) or steps != ['load_data', 'modify_network'] or warn
    st.gate('G5d.5', 'load_data, then modify_network', 'FAIL' if bad else 'PASS', 'rc %s; steps %s; F40 warnings %d' % (
        ', '.join(str(x) for x in rcs), ' '.join(steps) or 'none', len(warn)), 'rc 0 each; load_data modify_network; no F40 warning',
        ('logs %s\n' % ', '.join(logs)) + '\n'.join(warn[:3]) + ('' if not any(rcs) else '\n' + P3.tail(logs[-1], 8)))
    st.rec['outputs'] = dict(logs=list(logs))
    if bad:
        return st.finish()
    ih = os.path.join(mdir, 'inputs', 'ifgramStack.h5')
    unw = glob.glob(os.path.join(W, 'Igrams', '*', 'filt_*.unw'))
    newest = max(os.stat(p).st_mtime_ns for p in unw) if unw else 0
    tcfg = P5.cfg_dict(open(tfile).read())
    mt = os.stat(ih).st_mtime_ns if os.path.isfile(ih) else 0
    fresh = mt >= int((t_load - 1) * 1e9)
    ok = fresh and mt > newest and tcfg.get('mintpy.load.updateMode') == 'no'
    st.gate('G15', 'a fresh stack', 'PASS' if ok else 'FAIL', 'ifgramStack.h5 %s by this load_data, %s the newest of %d .unw; updateMode %s' % (
        'written' if fresh else 'NOT written', 'after' if mt > newest else 'NOT after', len(unw), tcfg.get('mintpy.load.updateMode')),
        'written by this run\'s load_data, after every .unw (N19); updateMode no (G15: MintPy compares names and sizes only)')
    if not ok:
        return st.finish()
    import h5py
    import numpy as np
    at = P5.h5_attrs(ih)
    hok, hwant, hd = P5.heading_ok(at.get('HEADING', 'nan'), cfg['direction'], float(m['HEADING_TOL_DEG']))
    od, want_od = str(at.get('ORBIT_DIRECTION')), tcfg.get('ORBIT_DIRECTION')
    st.gate('G24', 'the stack\'s direction', 'PASS' if hok and od == want_od else 'FAIL', 'HEADING %s (%+.1f deg from %s), ORBIT_DIRECTION '
            '%s' % (at.get('HEADING'), hd, hwant, od), 'HEADING within %s deg of %s; ORBIT_DIRECTION %s' % (m['HEADING_TOL_DEG'], hwant, want_od))
    if not (hok and od == want_od):
        return st.finish()
    with h5py.File(ih, 'r') as f:
        d12 = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][:]]
        drop = f['dropIfgram'][:]
        shape = f['unwrapPhase'].shape
    adm = json.load(open(os.path.join(recdir, 'recon', 'admission.json')))
    kept = [p for p, k in zip(d12, drop) if k]
    net = P5.pairs_of(W)
    bad = []
    if sorted(d12) != net:
        bad.append('the stack holds %d pairs, the frame %d' % (len(d12), len(net)))
    if sorted(kept) != sorted(adm['kept_pairs']):
        bad.append('kept %d, admit kept %d (differ: %s)' % (len(kept), len(adm['kept_pairs']),
                                                             ', '.join(sorted(set(kept) ^ set(adm['kept_pairs'])))[:200]))
    st.gate('G5d.6', 'the stack', 'FAIL' if bad else 'PASS', '%d pairs, %d kept, %d dropped (%s); %d x %d' % (
        len(d12), len(kept), len(d12) - len(kept), ', '.join(p for p, k in zip(d12, drop) if not k) or 'none', shape[1], shape[2]),
        'the frame\'s pairs; kept = admit\'s', '\n'.join(bad))
    if bad:
        return st.finish()
    # ---- G19: the kit's pick (always run, for the record), or the operator's pixel
    lg = P1.new_log(os.path.join(logd, 'linog_refpix.log'))
    krc, kout = P3.kit_run(env, KIT, ['--edge', str(m['G19_EDGE'])], W, lg)
    mm = re.findall(r'^mintpy\.reference\.yx\s+=\s*(\d+),(\d+)\s*$', kout, re.M)
    mf = re.search(r'^component fraction over valid area: max ([\d.]+)\s+mean ([\d.]+)', kout, re.M)
    mt_ = re.search(r'^--- top \d+ candidates at component fraction >= ([\d.]+)', kout, re.M)
    kyx = (int(mm[-1][0]), int(mm[-1][1])) if mm and krc == 0 else None
    yx, src = (op_yx, 'the operator\'s (recon/refpix.txt)') if op_yx else (kyx, 'the kit\'s G19')
    d9 = (adm.get('decisions', {}).get('d9') or {}).get('statistic', {}).get('mean')
    problems, usable = [], False
    if not yx:
        problems.append('no pick: the kit rc %d%s' % (krc, '' if mm else ', no mintpy.reference.yx line'))
    elif not (0 <= yx[0] < shape[1] and 0 <= yx[1] < shape[2]):
        problems.append('%d,%d is outside the %d x %d grid' % (yx[0], yx[1], shape[1], shape[2]))
    else:
        masked = masked_in(ih, yx)
        if masked:
            problems.append('%d,%d is not unwrapped (connected component 0) in %d kept pair(s): %s; MintPy\'s maskConnComp.h5 masks '
                            'it out and reference_point refuses it' % (yx[0], yx[1], len(masked), ', '.join(masked[:6])))
        else:
            usable = True
    if usable:
        txt2, sbad = P5.set_values(open(tfile).read(), {'mintpy.reference.yx': '%d,%d' % yx})
        if not sbad:
            tmp = tfile + '.tmp%d' % os.getpid()
            with open(tmp, 'w') as fh:
                fh.write(txt2)
            os.replace(tmp, tfile)
        online = P5.cfg_dict(open(tfile).read()).get('mintpy.reference.yx') == '%d,%d' % yx
        dig = P5.cfg_digest(open(tfile).read()) == rm['outputs'].get('cfg_digest')
        if sbad or not online or not dig:
            problems.append('the template: %s; on its line %s; the rest as mcfg wrote it %s' % ('; '.join(sbad) or 'set', online, dig))
    verdict = 'PASS' if not problems else 'FAIL' if (op_yx or usable) else 'DECISION'
    note = '' if not problems else '\n'.join(problems) + ('\nlog %s\n%s' % (lg, P3.tail(lg, 6)))
    if problems and not usable:
        ncommon, per = unwrapped_everywhere(ih)
        if ncommon == 0:
            note += ('\nno pixel is unwrapped in every kept pair (MintPy\'s maskConnComp.h5 would be empty), so no reference pixel can '
                     'work: exclude pairs in %s (mintpy.network.excludeDate12), then move mintpy/ into %s/_archive/ and run again; '
                     'the kept pairs unwrapped over the fewest pixels: %s' % (
                         os.path.join(W, 'recon', 'admission.txt'), W, ', '.join('%s %d' % x for x in per[:5])))
        elif verdict == 'DECISION':
            note += ('\n%d pixels are unwrapped in every kept pair; choose one: write %s with one line\n  mintpy.reference.yx = y,x\n'
                     '(the kit\'s table in its log lists candidates), then run again' % (ncommon, optxt))
        else:
            note += '\n%d pixels are unwrapped in every kept pair; the pixel in %s must be one of them' % (ncommon, optxt)
    st.gate('G19', 'the reference pixel', verdict, 'y,x %s (%s%s); the kit: rc %d, pick %s at component fraction >= %s; the kit\'s mean '
            'component fraction %s (admit\'s D9: %s)' % ('%d,%d' % yx if yx else '?', src, '; the kit picked %d,%d' % kyx if op_yx and kyx
                                                        else '', krc, '%d,%d' % kyx if kyx else '-', mt_.group(1) if mt_ else '?',
                                                        mf.group(2) if mf else '?', '%.4f' % d9 if d9 is not None else '?'),
            'inside the %d x %d grid; unwrapped in every kept pair; on mintpy.reference.yx; the rest of the template as mcfg wrote it'
            % (shape[1], shape[2]), note)
    st.rec['outputs'].update(refpix=dict(yx=yx, source=src, kit_yx=kyx, kit_rc=krc, log=lg, kit_threshold=float(mt_.group(1)) if mt_ else None,
                                         kit_mean_fraction=float(mf.group(2)) if mf else None,
                                         kit_max_fraction=float(mf.group(1)) if mf else None))
    if problems:
        return st.finish()
    lg2 = P1.new_log(os.path.join(logd, 'smallbaseline_refpoint_geocode.log'))
    rc, out, steps, warn = mintpy_call(mdir, ['--start', 'reference_point', '--end', 'geocode'], lg2, W)
    want = P5.steps_between('reference_point', 'geocode')
    plotfail = rc != 0 and steps == want and P5.PLOT_BANNER in out   # the banner prints only after every step has run
    bad = (rc != 0 and not plotfail) or steps != want or warn
    st.rec['outputs']['logs'].append(lg2)
    st.gate('G5d.7', 'reference_point to geocode', 'FAIL' if bad else 'WARN' if plotfail else 'PASS', 'rc %d; %d steps; F40 warnings %d%s' % (
        rc, len(steps), len(warn), '; MintPy\'s plots %s' % ('failed after the last step (pic/ incomplete)' if plotfail else
                                                            'made' if P5.PLOT_BANNER in out else 'not made')),
            'rc 0; %s' % ' '.join(want), ('log %s\n' % lg2) + '\n'.join(warn[:3]) + ('' if not rc else '\n' + P3.tail(lg2, 8)))
    if bad:
        return st.finish()
    miss = [n for n in RADAR if not os.path.isfile(os.path.join(mdir, n))] + \
        ['geo/' + n for n in GEO if not os.path.isfile(os.path.join(mdir, 'geo', n))]
    bad = list(miss)
    ts = os.path.join(mdir, 'timeseries.h5')
    if os.path.isfile(ts):
        t = P5.h5_attrs(ts)
        if (str(t.get('REF_Y')), str(t.get('REF_X'))) != (str(yx[0]), str(yx[1])):
            bad.append('timeseries.h5 REF_Y, REF_X %s,%s, the pixel %d,%d' % (t.get('REF_Y'), t.get('REF_X'), yx[0], yx[1]))
    with h5py.File(ih, 'r') as f:
        has_b = 'unwrapPhase_bridging' in f
    want_b = tcfg.get('mintpy.unwrapError.method') == 'bridging'
    if has_b != want_b:
        bad.append('unwrapPhase_bridging in the stack %s, unwrapError.method %s' % (has_b, tcfg.get('mintpy.unwrapError.method')))
    cover = None
    gm = os.path.join(mdir, 'geo', 'geo_maskTempCoh.h5')
    if os.path.isfile(gm):
        with h5py.File(gm, 'r') as f:
            k = [x for x in f.keys()][0]
            mk = f[k][:]
        cover = dict(true=int(np.count_nonzero(mk)), total=int(mk.size))
    st.gate('G5d.8', 'the products', 'FAIL' if bad else 'PASS', '%s; geo/: %s (N14)%s; reference %d,%d on timeseries.h5%s' % (
        ', '.join(RADAR), ', '.join(GEO), '' if not cover else '; geo_maskTempCoh TRUE %d of %d px (%.2f %% of the rectangle)' % (
            cover['true'], cover['total'], 100.0 * cover['true'] / max(cover['total'], 1)), yx[0], yx[1],
        '; unwrapPhase_bridging present' if has_b else ''), 'all present; REF_Y, REF_X the pixel; bridging as the template says',
        '\n'.join(bad[:8]))
    lst = P3.listing(W, P5.OUTS[PHASE])
    st.rec['outputs'].update(kept=len(kept), dropped=len(d12) - len(kept), heading=at.get('HEADING'), coverage_rect=cover, files=lst,
                             digest=P3.digest(lst), cfg_digest=P5.cfg_digest(open(tfile).read()), plots_failed=plotfail)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_sbas', main)
