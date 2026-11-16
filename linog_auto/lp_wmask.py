#!/usr/bin/env python3
"""lp_wmask.py -- linog_auto Phase 5e: the water and swath-edge masks (G22, G23), the kit's linog_watermask.py.

Runs inside lp_env.sh. After sbas, the last MintPy call that writes the masks, and before deliver, which delivers from
them (the kit's ph_watermask): `linog_watermask.py <frame> --apply` from $S (907cf856), unchanged (design D-B). The
tool finds the SRTM-flat water bodies of inputs/geometryRadar.h5's height and masks the valid pixels on them whose
amplitude (the median of 10 pairs' .amp) is within 6 dB of the water's own (G22, finding N60: the Goldstein filter
spreads land phase 2 to 3 km into water, and no coherence threshold removes it), and the dark strips along the grid's
edges (G23). It backs both masks up to mintpy/watermask/*.orig.h5, writes the mask into mintpy/maskTempCoh.h5 and,
1 s later, mintpy/geo/geo_maskTempCoh.h5 (so Phase 6's geocode --update keeps it), and writes
mintpy/watermask/summary.json last; it refuses to remove the reference pixel. sbas's listing leaves the two masks out
for this reason, so sbas stays CURRENT after it.

Gates
  G5e.1  sbas PASS on record, its files as it recorded them                                         FAIL
  G5e.1d d9ab PASS on record (v0.8: D9 settled by the A/B, or by the operator, before the masks)     FAIL
  G5e.2  environment; MintPy at its pin; scipy (the tool's ndimage)                           ERROR / FAIL
  G5e.3  the kit's linog_watermask.py at its pin                                                     FAIL
  G5e.4  the tool's inputs: the two masks, geometryRadar.h5, timeseries.h5, the template; the pairs' .amp FAIL
  G5e.5  nothing in the way: mintpy/watermask absent, neither mask carrying LINOG_WATERMASK         DECISION
  G22    the tool: rc 0; its lines (grid, water, radar and geo masks before and after, 'wrote ...')  FAIL
  G5e.6  the reference pixel kept, and the tool's REF = timeseries.h5's = sbas's pick               FAIL
  G23    the swath-edge strips: per edge, no-data and dark offsets; valid px left 20 dB below       PASS / WARN
  G5e.7  summary.json: rule v2, the tool's md5 its pin, applied, both masks' md5 as it recorded     FAIL
  G5e.8  both masks carry LINOG_WATERMASK = the rule (apply)                                         FAIL
  G5e.9  sbas's six files unchanged by the tool (apply)                                               FAIL
The --apply runs in a session of its own with the stop signals held (as the datum's): a stop lands after the tool has
ended, the masks whole; the next run then stops at G5e.5 with the originals named. --state: STALE also when the masks or
mintpy/watermask/ changed since. --dryrun DIR: the tool's own dry run (--outdir DIR/mintpy/watermask_dryrun), reading the
frame when its sbas is PASS; the frame is not touched. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import json
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'wmask', '5e', 1
TOOL = 'linog_watermask.py'
RULE_V2 = 'LInOG masks v2'
NEED = ('mintpy/maskTempCoh.h5', 'mintpy/geo/geo_maskTempCoh.h5', 'mintpy/inputs/geometryRadar.h5', 'mintpy/timeseries.h5',
        'mintpy/smallbaselineApp.cfg')
RE = dict(grid=re.compile(r'^radar grid (\d+) x (\d+), px ([\d.]+) m az x ([\d.]+) m rg \| amplitude: median of (\d+) pairs x 2 bands '
                          r'\((\d+) \.amp files\)', re.M),
          water=re.compile(r'^valid \(maskTempCoh\) (\d+) px \| SRTM-flat water (\d+) px, valid on it (\d+)', re.M),
          radar=re.compile(r'^radar maskTempCoh: (\d+) -> (\d+) px  \(removed (\d+)\)', re.M),
          ref=re.compile(r'^reference pixel y/x (\d+)/(\d+), REF_DATE (\S+): flag (\d+), valid before (\w+) after (\w+)', re.M),
          grid_ok=re.compile(r'^geo grid of the geocoded flag vs geo_maskTempCoh: (IDENTICAL|DIFFERS.*)$', re.M),
          geo=re.compile(r'^geo geo_maskTempCoh: (\d+) -> (\d+) px  \(removed (\d+):', re.M),
          edge=re.compile(r'^edge strips \(G23; interior land median ([-\d.]+) dB over (\d+) px\): (.*)$', re.M),
          wrote=re.compile(r'^wrote (\S+) and (\S+); record (\S+)$', re.M),
          abort=re.compile(r'^\*\*\* ABORT: (.*)$', re.M),
          bodies=re.compile(r'^  \.\.\. (\d+) more bodies', re.M))


def mask_attr(p):
    """The LINOG_WATERMASK attribute of a mask file, or None."""
    import h5py
    with h5py.File(p, 'r') as f:
        v = f.attrs.get('LINOG_WATERMASK')
    return v.decode() if isinstance(v, bytes) else v


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5e: the water and swath-edge masks (G22, G23)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m, q = P1.load_env(), P2.load_stack(), P5.load_mintpy(), P6.load_p6()
    tm = P6.tools(env, q, (TOOL,))
    rs = P1.record(recdir, '5d', 'sbas') or {}
    fp = C.md5_obj(dict(logic=LOGIC, sbas=rs.get('outputs', {}).get('digest'), kit=tm[TOOL][1], mintpy=m['MINTPY_VERSION']))
    if a.state:
        print(P6.state(recdir, W, PHASE, IDX, fp, P6.WMASK_OUTS))
        return 0

    st = P6.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(p6_cfg=q['p6_cfg_file'], p6_cfg_md5=q['p6_cfg_md5'],
                                                                   tools={TOOL: dict(path=tm[TOOL][0], md5=tm[TOOL][1])}))
    P6.header(PHASE, IDX, path, frame, W, a.dryrun)
    rs, from_frame = P6.prior6(st, 'G5e.1', recdir, W, '5d', 'sbas', P5.OUTS['sbas'], bool(a.dryrun))
    if not rs:
        return st.finish()
    # v0.8: D9 is settled before the masks and the delivery are made from sbas's products (a dry run reads its own d9ab
    # record first, then the frame's); not in the fingerprint: the masks do not depend on it
    rd = (P1.record(recdir, '5dab', 'd9ab') if a.dryrun else None) or P1.record(W, '5dab', 'd9ab') or {}
    ok = rd.get('verdict') == 'PASS'
    st.gate('G5e.1d', 'd9ab PASS on record (D9 settled)', 'PASS' if ok else 'FAIL', 'P5dab d9ab %s%s' % (
        rd.get('verdict') or 'has no record', ': %s' % ((rd.get('outputs') or {}).get('result') or {}).get('verdict', 'not run')
        if ok else ''), 'PASS', '' if ok else 'run d9ab first (it runs after sbas): D9\'s A/B, or the operator\'s bridging')
    if not ok:
        return st.finish()
    if a.dryrun and (not from_frame or rs.get('outputs', {}).get('planned')):
        return P5.plan_only(st, ['would run %s %s --apply from $S after sbas, then check its summary.json and both masks' % (TOOL, W)],
                            'the frame\'s sbas has not run, so there are no masks to read')
    if not P5.env_gate(st, 'G5e.2', env, s, m):
        return st.finish()
    try:
        import scipy
        from scipy import ndimage  # noqa: F401
        st.gate('G5e.2s', 'scipy (the tool\'s ndimage)', 'PASS', 'scipy %s at %s' % (scipy.__version__, os.path.dirname(scipy.__file__)))
    except Exception as e:  # noqa: BLE001
        st.gate('G5e.2s', 'scipy (the tool\'s ndimage)', 'ERROR', 'import scipy.ndimage failed: %s' % e)
        return st.finish()
    if not P3.pins_gate(st, 'G5e.3', {TOOL: tm[TOOL]}, 'the kit\'s G22 and G23 tool'):
        return st.finish()
    miss = [x for x in NEED if not os.path.isfile(os.path.join(W, x))]
    amps = [p for p in P6.rel_files(W, 'Igrams/*/*.amp') if os.path.isfile(p + '.xml')]
    st.gate('G5e.4', 'the tool\'s inputs', 'FAIL' if miss or not amps else 'PASS', '%s; %d .amp files with their .xml in Igrams/' % (
        'the two masks, geometryRadar.h5, timeseries.h5 and the template present' if not miss else 'absent: ' + ', '.join(miss), len(amps)),
        'all present; at least one pair\'s .amp (the tool takes the median of 10)')
    if miss or not amps:
        return st.finish()
    radar, geo = (os.path.join(W, x) for x in NEED[:2])
    marks = [x for x, p in (('mintpy/maskTempCoh.h5', radar), ('mintpy/geo/geo_maskTempCoh.h5', geo)) if mask_attr(p)]
    wdir = os.path.join(W, 'mintpy', 'watermask')
    if a.dryrun:
        st.gate('G5e.5', 'nothing in the way', 'INFO', 'dry run: in the frame now: %s' % (', '.join(
            (['mintpy/watermask'] if os.path.lexists(wdir) else []) + ['%s carries LINOG_WATERMASK' % x for x in marks]) or 'none of them'),
            'mintpy/watermask absent, the masks without LINOG_WATERMASK')
    elif os.path.lexists(wdir) or marks:
        st.gate('G5e.5', 'nothing in the way', 'DECISION', 'in the frame already: %s' % ', '.join(
            (['mintpy/watermask'] if os.path.lexists(wdir) else []) + ['%s carries LINOG_WATERMASK' % x for x in marks]),
            'mintpy/watermask absent, the masks without LINOG_WATERMASK',
            'an earlier write of the masks with no PASS record of this phase; the originals are in mintpy/watermask/*.orig.h5. '
            'Put both masks back from them, move mintpy/watermask into %s/_archive/, and run again' % W)
        return st.finish()
    else:
        st.gate('G5e.5', 'nothing in the way', 'PASS', 'mintpy/watermask absent; neither mask carries LINOG_WATERMASK', 'all absent')

    logd = os.path.join(W if not a.dryrun else recdir, 'logs', 'p5', 'wmask')
    os.makedirs(logd, exist_ok=True)
    lg = P1.new_log(os.path.join(logd, 'linog_watermask.log'))
    if a.dryrun:
        out = os.path.join(recdir, 'mintpy', 'watermask_dryrun')
        if os.path.lexists(out):
            os.rename(out, P2.new_dir(os.path.join(recdir, '_archive', 'watermask_dryrun')))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        args = [W, '--outdir', out]
    else:
        out = wdir
        args = [W, '--apply']
    if a.dryrun:
        rc, txt = P3.kit_run(env, TOOL, args, logd, lg, P5.mpl_env(recdir))
    else:
        # --apply rewrites both masks in place: as the datum's --apply (lp_datum), the tool runs in a session of its own
        # with SIGINT, SIGTERM and SIGHUP held here, so a stop lands after the tool has ended and the masks are whole
        st.rec['outputs'] = dict(log=lg, tool_dir=out, applying=True)
        st.write()
        with P3.Deferred():
            rc, txt = P3.kit_run(env, TOOL, args, logd, lg, P5.mpl_env(recdir), session=True)
            st.rec['outputs'].update(applying=False, rc=rc)
            st.write()
    g = dict((k, r.search(txt)) for k, r in RE.items())
    problems = []
    if rc != 0:
        problems.append('rc %d%s' % (rc, (': ' + g['abort'].group(1)) if g['abort'] else ''))
    for k in ('grid', 'water', 'radar', 'ref', 'grid_ok', 'geo', 'edge', 'wrote'):
        if not g[k]:
            problems.append('no "%s" line' % k)
    if g['grid_ok'] and g['grid_ok'].group(1) != 'IDENTICAL':
        problems.append('the geocoded flag\'s grid %s' % g['grid_ok'].group(1))
    val = '; '.join(problems) if problems else (
        'radar maskTempCoh %s -> %s px (removed %s); geo %s -> %s (removed %s); SRTM-flat water %s px, valid on it %s; grid %s x %s, '
        'amplitude of %s pairs (%s .amp)' % (g['radar'].group(1), g['radar'].group(2), g['radar'].group(3), g['geo'].group(1),
                                           g['geo'].group(2), g['geo'].group(3), g['water'].group(2), g['water'].group(3),
                                           g['grid'].group(1), g['grid'].group(2), g['grid'].group(5), g['grid'].group(6)))
    st.gate('G22', 'the water mask', 'FAIL' if problems else 'PASS', val, 'rc 0; every line of the tool; the flag\'s geo grid identical',
            'log %s\n%s' % (lg, P3.tail(lg, 8)) if problems else 'log %s' % lg)
    st.rec['outputs'].update(log=lg, tool_dir=out)   # the Status starts with outputs {}
    if problems:
        return st.finish()
    # ---- the reference pixel: kept, and the one sbas pinned
    ta = P5.h5_attrs(os.path.join(W, 'mintpy', 'timeseries.h5'))
    tyx = (int(ta.get('REF_Y', -1)), int(ta.get('REF_X', -1)))
    syx = tuple((rs.get('outputs', {}).get('refpix') or {}).get('yx') or (None, None))
    gyx = (int(g['ref'].group(1)), int(g['ref'].group(2)))
    ok = g['ref'].group(6) == 'True' and gyx == tyx and (syx == (None, None) or tuple(syx) == tyx)
    st.gate('G5e.6', 'the reference pixel', 'PASS' if ok else 'FAIL', 'y/x %d/%d (the tool), timeseries.h5 %d/%d, sbas %s; flag %s, valid before %s, '
            'after %s' % (gyx[0], gyx[1], tyx[0], tyx[1], '%s/%s' % syx if syx[0] is not None else '-', g['ref'].group(4),
                          g['ref'].group(5), g['ref'].group(6)), 'kept (valid after); the same pixel in the tool, timeseries.h5 and sbas')
    if not ok:
        return st.finish()
    # ---- summary.json: the tool's own record
    sj = os.path.join(out, 'summary.json')
    try:
        sm = json.load(open(sj))
    except (OSError, ValueError) as e:
        st.gate('G5e.7', 'summary.json', 'FAIL', '%s: %s' % (sj, e), 'written last by the tool')
        return st.finish()
    tr, tg = (g['wrote'].group(1), g['wrote'].group(2))
    bad = []
    if not str(sm.get('rule', '')).startswith(RULE_V2):
        bad.append('rule %r, want %s' % (str(sm.get('rule'))[:40], RULE_V2))
    if sm.get('tool_md5') != tm[TOOL][2]:
        bad.append('tool_md5 %s, pin %s' % (sm.get('tool_md5'), tm[TOOL][2]))
    if bool(sm.get('applied')) != (not a.dryrun):
        bad.append('applied %s' % sm.get('applied'))
    for k, p in (('maskTempCoh.h5', tr), ('geo/geo_maskTempCoh.h5', tg)):
        if not os.path.isfile(p) or sm.get('md5', {}).get(k) != C.md5_file(p):
            bad.append('%s md5 %s, %s now' % (k, sm.get('md5', {}).get(k), C.md5_file(p) if os.path.isfile(p) else 'absent'))
    if list(sm.get('ref_yx') or []) != list(tyx):
        bad.append('ref_yx %s, timeseries.h5 %s' % (sm.get('ref_yx'), list(tyx)))
    if int(sm.get('radar_after', 0)) <= 0 or int(sm.get('geo_after', 0)) <= 0:
        bad.append('a mask left empty: radar %s, geo %s' % (sm.get('radar_after'), sm.get('geo_after')))
    rf = sm.get('radar_flags', {})
    st.gate('G5e.7', 'summary.json', 'FAIL' if bad else 'PASS', '%s; radar %s -> %s px (flags: water masked %s, kept on water %s, '
            'no reference %s, strip %s); geo %s -> %s; %d water bodies with valid px' % (
                sj, sm.get('radar_before'), sm.get('radar_after'), rf.get('1'), rf.get('3'), rf.get('4'), rf.get('6'), sm.get('geo_before'),
                sm.get('geo_after'), len(sm.get('bodies') or [])), 'rule v2; the tool\'s md5 its pin; both masks as it recorded them',
            '\n'.join(bad))
    if bad:
        return st.finish()
    e = sm.get('edge') or {}
    deep = e.get('deep_after') or {}
    strips = ', '.join('%s %s+%s' % (x.get('edge'), x.get('nodata'), x.get('dark')) for x in e.get('strips', []))
    st.gate('G23', 'the swath-edge strips', 'WARN' if deep.get('near') or deep.get('far') else 'PASS', 'per edge no-data+dark px: %s; '
            '%s valid px masked in them; valid px 20 dB or more below the interior after the masks: %s near an edge, %s farther' % (
                strips, e.get('masked_valid'), deep.get('near'), deep.get('far')), 'the tool\'s rule v2; none left 20 dB below (else WARN, as '
            'the verifier)')
    summary = dict(radar_before=sm.get('radar_before'), radar_after=sm.get('radar_after'), geo_before=sm.get('geo_before'),
                   geo_after=sm.get('geo_after'), radar_flags=rf, geo_flags=sm.get('geo_flags'), bodies=len(sm.get('bodies') or []),
                   edge=dict(strips=strips, masked_valid=e.get('masked_valid'), deep_after=deep), ref_yx=list(tyx),
                   summary_json=sj, summary_md5=C.md5_file(sj))
    st.rec['outputs'].update(summary=summary)
    if a.dryrun:
        st.rec['outputs'].update(planned=True, dryrun=True)
        return st.finish('dry run: the tool\'s own dry run in %s (the frame not touched)' % out)
    # ---- the frame after the write
    bad = []
    for k, p in (('mintpy/maskTempCoh.h5', radar), ('mintpy/geo/geo_maskTempCoh.h5', geo)):
        v = mask_attr(p)
        if v != sm.get('rule'):
            bad.append('%s LINOG_WATERMASK %r' % (k, (v or '')[:40]))
    st.gate('G5e.8', 'the masks in the frame', 'FAIL' if bad else 'PASS', '; '.join(bad) or 'both carry LINOG_WATERMASK rule v2, md5 as '
            'summary.json', 'both carry the rule', '')
    ch = P3.listing_changed(W, P5.OUTS['sbas'], rs.get('outputs', {}).get('files'))
    st.gate('G5e.9', 'sbas\'s files', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or 'the six files sbas recorded, unchanged',
            'unchanged by the tool')
    lst = P3.listing(W, P6.WMASK_OUTS)
    st.rec['outputs'].update(files=lst, digest=P3.digest(lst))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_wmask', main)
