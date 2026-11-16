#!/usr/bin/env python3
"""lp_topo.py -- linog_auto Phase 3a: run_01_reference, topo on the reference (the 12 frames' step 10).

Runs inside lp_env.sh. The run file's one line, `stripmapWrapper.py -c <frame>/configs/config_reference_<REF>` (the
stripped 14-line config, stack2's water-mask strip), runs from the frame folder with stripmapStack first on the PATH
(F13), uncapped as the 12 frames ran it. topo writes the full-resolution geometry into merged/geom_reference and the
multilooked copy into geom_reference (Rule 4: the small tree is the right one, and G7 and G10 choose their windows on
its hgt.rdr). ISCE also writes sim.log in the frame and appends to isce.log (F16).

Gates
  G3a.1  stack2 PASS on record, its configuration in the frame; run_01 and config_reference as it recorded them;
         recon/reference.json as stack2 read it                                                       FAIL
  G3a.2  environment                                                                                  ERROR
  G3a.3  stripmapWrapper.py and topo.py at their pins                                                 FAIL
  G3a.4  the run file's command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G3a.5  the geometry: reference.json's width x lines and Rule 4's grid; run_01 is one line naming
         configs/config_reference_<REF>                                                                FAIL
  G3a.6  the frame's DEM (topo reads it)                                                              FAIL
  G3a.7  nothing in the way: merged/geom_reference and geom_reference absent                          DECISION
  G3a.8  disk: free >= what topo writes + disk_gib_margin                                              FAIL
  G3a.9  run_01: rc 0                                                                                  FAIL
  G3a.10 merged/geom_reference: hgt, lat, lon 8 B x W x L; los, incLocal 8 B (2 x float32); shadowMask 1 B;
         simamp 4 B; each with .xml and .vrt                                                          FAIL
  G3a.11 geom_reference: hgt, lat, lon, los, incLocal 8 B x gw x gl, shadowMask 1 B, each .xml and .vrt;
         hgt.rdr.xml reads gw x gl                                                                    FAIL
  G3a.12 geom_reference/hgt.rdr: no ISCE fill (|h| > HGT_FILL_ABS, E62)                                WARN
  G3a.13 convergence line of the log, N of W x L (recorded: not a quality score; it moves with the
         reference scene, linog_topo_convergence; and it is a lower bound that changes from run to run:
         topozero adds to its total inside a parallel loop with no reduction, F61, record 79)          INFO
  G3a.14 v0.13 (Gap 2b, ascending record 17.7, 18.5, 20.10): the reference SLC (the file its shelve names) against
         merged/geom_reference/simamp.rdr, both 4 x 4 looks, at the 3 x 3 cells' windows of relief (lp_reg3.py): with 3 or
         more windows counted (peak ratio >= 1.25), PASS at |dx| <= a quarter of a gate in the reference's samples (8 on
         FBS, 4 on FBD), WARN under half a gate, FAIL at half a gate (16, 8) or more; 1 or 2 windows: FAIL when every one
         reads half a gate or more with one sign, else WARN; none: NOT MEASURED, WARN. Under LOGIC 1 (22.2, item 8): a
         frame topo ran under v0.12 stays CURRENT. v0.13 r2 (the ascending record 25.4, 25.6, 25-b): the reference
         SLC's width read from SLC/<REF>/<REF>.slc.xml as isce2 2.6.3 loads it (coordinate1's size, lp_xmlwidth), not
         its width property, and a file whose fields disagree within itself FAILs; where they agree, the width and the
         verdict are v0.13's, under the same LOGIC                                                         FAIL / WARN
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import array
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'topo', '3a', 1
RUNF = 'run_01_reference'
BIG = (('hgt', 8), ('lat', 8), ('lon', 8), ('los', 8), ('incLocal', 8), ('shadowMask', 1), ('simamp', 4))
SMALL = (('hgt', 8), ('lat', 8), ('lon', 8), ('los', 8), ('incLocal', 8), ('shadowMask', 1))


def ref_pixel(W, ref):
    """The reference's range pixel (m): recon/modes.json's slr_m (v0.13's verify), else its shelve's rangePixelSize."""
    import json
    try:
        for row in json.load(open(os.path.join(W, 'recon', 'modes.json'))).get('dates', []):
            if row.get('date') == ref and row.get('slr_m'):
                return float(row['slr_m']), 'recon/modes.json'
    except (OSError, ValueError):
        pass
    import shelve
    with shelve.open(os.path.join(W, 'SLC', ref, 'data'), 'r') as db:
        ins = P2.get(db['frame'], 'instrument', 'getInstrument')
    return float(P2.get(ins, 'rangePixelSize', 'getRangePixelSize')), 'the shelve'


def g3a14(st, W, ref, Wd, L):
    """v0.13, G3a.14 (Gap 2b): the reading and its verdict (lp_reg3.py); the record's outputs.g3a14. lp_reg3.py's md5 goes
    into the record's tools (17.4), not the fingerprint. An error inside the reading ends this gate ERROR with its traceback
    (the part 3 review's P3-15), after run_01's outputs are listed by the caller."""
    import traceback
    try:
        import lp_reg3 as R3
        st.rec.setdefault('tools', {}).update(C.tool_md5s('lp_reg3.py'))
        return _g3a14(st, W, ref, Wd, L, R3)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        st.gate('G3a.14', 'the reference against simamp (Gap 2b)', 'ERROR', '%s: %s' % (type(e).__name__, e), 'a reading',
                '\n'.join(tb[-6:]) + '\nrun_01\'s outputs stay as they are; the reading can be repeated by a person with '
                'lp_reg3.g3a14_read on them before topo is run again')
        return dict(verdict='ERROR', error='%s: %s' % (type(e).__name__, e))


def _g3a14(st, W, ref, Wd, L, R3):
    slc = os.path.join(W, 'SLC', ref, ref + '.slc')   # the file the reference's shelve names (G17: SLC/<REF>/<REF>.slc)
    sim = os.path.join(W, 'merged', 'geom_reference', 'simamp.rdr')
    shadow = os.path.join(W, 'merged', 'geom_reference', 'shadowMask.rdr')
    # v0.13 r2 (25-b): the reference SLC's .xml as isce2 loads it (coordinate1's size) and against itself; simamp's .xml, which
    # isce2's topo writes, by its width property as before (25.6)
    import lp_xmlwidth as XW
    st.rec.setdefault('tools', {}).update(C.tool_md5s('lp_xmlwidth.py'))   # recorded, not fingerprinted (as lp_reg3.py's)
    ws = R3.xml_int(sim + '.xml', 'width')
    wx, _, xprob = XW.check(slc + '.xml')
    slr, by = ref_pixel(W, ref)
    gate = R3.gate_samples(slr)   # 32 and 16 samples whatever the pixel's last digits (the part 3 review's P3-13)
    hgt, why = R3.load_hgt(W)
    if ws != Wd or wx != Wd or xprob or hgt is None:
        st.gate('G3a.14', 'the reference against simamp (Gap 2b)', 'FAIL', 'simamp %s wide, the reference SLC %s, the geometry %d; %s' % (
            ws, wx, Wd, why if hgt is None else 'geom_reference/hgt.rdr %s' % why), 'one width', '\n'.join(
                'SLC/%s/%s.slc.xml: %s' % (ref, ref, x) for x in xprob))
        return dict(gate_samples=gate, verdict='FAIL', xml_problems=xprob)
    n, rd, named, survey = R3.g3a14_read(slc, sim, shadow, Wd, L, hgt)
    v, val, note, counted = R3.g3a14_verdict(rd, gate)
    q, h = gate / 4.0, gate / 2.0
    st.gate('G3a.14', 'the reference against simamp (Gap 2b)', v, val,
            '3 or more windows of %d x %d looks at a ratio of %.2f or more; |dx| <= %g PASS (a quarter gate), >= %g FAIL (half a gate) in '
            'the reference\'s samples (%.6f m, from %s)' % (n // R3.LOOKS, n // R3.LOOKS, R3.RATIO_MIN, q, h, slr, by),
            '; '.join(([note] if note else []) + (['no viable window in %s' % ', '.join(named)] if named else []) +
                      (['dy (recorded, not judged) %s' % ', '.join('%+.2f' % x['dy'] for x in rd)] if rd else [])))
    return dict(window=n, looks=R3.LOOKS, gate_samples=gate, quarter=q, half=h, slr_m=slr, slr_from=by, verdict=v, value=val,
                readings=rd, counted=len(counted), named=named, survey=survey, tools=C.tool_md5s('lp_reg3.py'))


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 3a: run_01 (topo)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, r = P1.load_env(), P2.load_stack(), P3.load_run()
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'topo.py'))
    geo, geo_bad = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    o2 = r2.get('outputs', {})
    wd = o2.get('workdir') or W
    crel = 'configs/config_reference_%s' % ref
    # what topo reads: the reference SLC, the DEM, the run file and its config, the geometry, the two scripts
    fp = C.md5_obj(dict(logic=LOGIC, geometry=[geo.get(k) for k in ('ref', 'width', 'lines', 'rlks', 'alks')] if geo else None,
                        runs=P3.runfile_md5s(W, [RUNF]), slc=P3.slc_identity(W, [ref] if ref else []),
                        dem=P2.dem_identity(P2.frame_dem(W)[0]), tools={k: v[1] for k, v in tm.items()}))
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R01_J', 'R01_OMP', 'R01_PEAK_KB', 'HGT_FILL_ABS')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    if not r2 or r2.get('verdict') != 'PASS':
        st.gate('G3a.1', 'stack2 PASS on record', 'FAIL', 'P2c stack2 %s' % (r2.get('verdict') or 'has no record'))
        return st.finish()
    if a.dryrun and o2.get('planned'):
        st.gate('G3a.1', 'stack2 PASS on record', 'PASS', 'dry-run stack2 was a plan only')
        return P3.plan_only(st, {RUNF: None}, 'stack2 planned only')
    why = []
    if not a.dryrun and os.path.realpath(wd) != os.path.realpath(W):
        why.append('stack2\'s configuration is in %s, not the frame' % wd)
    files = {n: m for n, size, m in o2.get('files') or []}
    for rel in ('run_files/%s' % RUNF, crel):
        p = os.path.join(wd, rel)
        if rel not in files or not os.path.isfile(p) or C.md5_file(p) != files[rel]:
            why.append('%s is not as stack2 recorded it' % rel)
    if geo and r2.get('inputs', {}).get('reference_json_md5') not in (None, geo['json_md5']) and not a.dryrun:
        why.append('recon/reference.json changed since stack2 read it')
    st.gate('G3a.1', 'stack2 PASS on record', 'FAIL' if why else 'PASS', '; '.join(why) or
            'reference %s; %s and %s as stack2 recorded them' % (ref, RUNF, os.path.basename(crel)))
    if why:
        return st.finish()
    if not P2.env_gate(st, 'G3a.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G3a.3', tm, 'topo\'s scripts'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R01', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G3a.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    lines = P3.run_lines(wd, RUNF) or []
    want = 'stripmapWrapper.py -c %s' % os.path.join(wd, crel)
    bad = list(geo_bad) if geo else ['no geometry']
    if [x.strip() for x in lines] != [want]:
        bad.append('%s reads %r, want %r' % (RUNF, lines, want))
    st.gate('G3a.5', 'the reference geometry', 'FAIL' if bad else 'PASS', 'reference %s %d x %d; looks %d x %d; grid %d x %d' % (
        ref, geo['width'], geo['lines'], geo['rlks'], geo['alks'], geo['gw'], geo['gl']) if geo else 'none',
        'Rule 4: int(W / rlks) x int(L / alks); one line naming %s' % os.path.basename(crel), '\n'.join(bad))
    if bad:
        return st.finish()
    dem, dem_bad = P2.frame_dem(W)
    st.gate('G3a.6', 'the frame DEM', 'FAIL' if dem_bad else 'PASS', '; '.join(dem_bad) or dem, 'one *.wgs84 + .vrt + .xml')
    if dem_bad:
        return st.finish()
    Wd, L, gw, gl = geo['width'], geo['lines'], geo['gw'], geo['gl']
    need = sum(b for _, b in BIG) * Wd * L + sum(b for _, b in SMALL) * gw * gl
    if a.dryrun:
        P3.way_gate(st, 'G3a.7', W, PHASE, True)
        print('   topo would write about %.1f GiB (merged/geom_reference %d x %d, geom_reference %d x %d)' % (
            P3.gib(need), Wd, L, gw, gl))
        return P3.plan_only(st, {RUNF: lines}, 'topo')
    if not P3.way_gate(st, 'G3a.7', W, PHASE, False):
        return st.finish()
    if not P3.disk_gate(st, 'G3a.8', W, need, float(cfg.get('disk_gib_margin', 0))):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G3a.9', W, s, r, RUNF, lines, logroot, logroot, 'topo')
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    specs = []
    for n, b in BIG:
        specs += [('merged/geom_reference/%s.rdr' % n, b * Wd * L), ('merged/geom_reference/%s.rdr.xml' % n, None),
                  ('merged/geom_reference/%s.rdr.vrt' % n, None)]
    bad = P3.expect(W, specs)
    st.gate('G3a.10', 'merged/geom_reference', 'FAIL' if bad else 'PASS', '%d rasters at their sizes (%d B for 8 B x %d x %d)' % (
        len(BIG), 8 * Wd * L, Wd, L) if not bad else '%d problems' % len(bad),
        'hgt lat lon 8 B, los incLocal 2 x 4 B, shadowMask 1 B, simamp 4 B per sample; .xml and .vrt', '\n'.join(bad))
    if bad:
        return st.finish()
    specs = []
    for n, b in SMALL:
        specs += [('geom_reference/%s.rdr' % n, b * gw * gl), ('geom_reference/%s.rdr.xml' % n, None),
                  ('geom_reference/%s.rdr.vrt' % n, None)]
    bad = P3.expect(W, specs)
    dims = P3.xml_dims(os.path.join(W, 'geom_reference', 'hgt.rdr.xml'))
    if dims != (gw, gl):
        bad.append('geom_reference/hgt.rdr.xml reads %s x %s, want %d x %d' % (dims[0], dims[1], gw, gl))
    nsmall = len(os.listdir(os.path.join(W, 'geom_reference'))) if os.path.isdir(os.path.join(W, 'geom_reference')) else 0
    st.gate('G3a.11', 'geom_reference', 'FAIL' if bad else 'PASS', '%d rasters %d x %d, hgt.rdr %d B; %d entries' % (
        len(SMALL), gw, gl, 8 * gw * gl, nsmall), 'Rule 4: 8 B x gw x gl (shadowMask 1 B); hgt.rdr.xml gw x gl', '\n'.join(bad))
    if bad:
        return st.finish()
    h = array.array('d')
    with open(os.path.join(W, 'geom_reference', 'hgt.rdr'), 'rb') as fh:
        h.frombytes(fh.read())
    lim = float(r['HGT_FILL_ABS'])
    fill = sum(1 for v in h if abs(v) > lim)
    valid = sorted(v for v in h if abs(v) <= lim)
    stats = dict(samples=len(h), fill=fill, min=round(valid[0], 1) if valid else None, max=round(valid[-1], 1) if valid else None,
                 p75=round(valid[int(0.75 * (len(valid) - 1))], 1) if valid else None)
    st.gate('G3a.12', 'geom_reference/hgt.rdr fill', 'WARN' if fill else 'PASS', '%d of %d samples beyond %g m; heights %s to %s m, '
            'p75 %s m' % (fill, len(h), lim, stats['min'], stats['max'], stats['p75']), 'no ISCE fill (E62)')
    txt = open(res[0]['log'], errors='replace').read()
    m = re.search(r'Total convergence:\s*(\d+)\s+out of\s+(\d+)', txt)
    conv = dict(converged=int(m.group(1)), of=int(m.group(2))) if m else None
    if conv:
        st.gate('G3a.13', 'topo convergence', 'INFO' if conv['of'] == Wd * L else 'WARN', '%d of %d = %.2f %% (reference %s)' % (
            conv['converged'], conv['of'], 100.0 * conv['converged'] / conv['of'], ref), 'of W x L = %d; recorded, not scored: topozero counts in a parallel loop without a reduction, '
            'so this is a lower bound that changes from run to run (F61)' % (Wd * L))
    else:
        st.gate('G3a.13', 'topo convergence', 'INFO', 'no "Total convergence" line in %s' % res[0]['log'], 'recorded, not scored')
    g14 = g3a14(st, W, ref, Wd, L)
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(g3a14=g14)
    st.rec['outputs'].update(reference=ref, files=lst, digest=P3.digest(lst), hgt=stats, convergence=conv,
                             geometry=dict(width=Wd, lines=L, gw=gw, gl=gl),
                             cwd_logs={n: os.path.getsize(os.path.join(W, n)) for n in ('isce.log', 'sim.log')
                                       if os.path.isfile(os.path.join(W, n))})
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_topo', main)
