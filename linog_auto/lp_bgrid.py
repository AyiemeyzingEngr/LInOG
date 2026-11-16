#!/usr/bin/env python3
"""lp_bgrid.py -- linog_auto Phase 4e: run_07_grid_baseline, the baseline grid of every date against the reference.

Runs inside lp_env.sh. One line per secondary, then one for the reference (S + 1; A19: per date, not per pair), each
reading merged/SLC/<date>/referenceShelve and secondaryShelve (run_06's copies) and writing
merged/baselines/<date>/<date> (float32, nLines x nPixels from its log's "dims" line; 30 x 30 on the rehearsal's p449
frame) with .xml, .vrt and .full.vrt. The flat baselines/*.txt of the stack configuration are not touched (MintPy reads
those); stack2's own record watches them.

Gates
  G4e.1  fine PASS on record, merged/SLC as it recorded it                                           FAIL
  G4e.2  environment                                                                                  ERROR
  G4e.3  stripmapWrapper.py and baselineGrid.py at their pins                                         FAIL
  G4e.4  the run file's command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G4e.5  run_07: one line per date (the secondaries, then the reference), each naming merged/SLC/<d>'s
         shelves and merged/baselines/<d>/<d>                                                          FAIL
  G4e.6  nothing in the way: merged/baselines absent                                                    DECISION
  G4e.7  run_07: rc 0 on every line                                                                    FAIL
  G4e.8  merged/baselines/<d>/<d>: 4 B x its "dims" for every date, with .xml, .vrt and .full.vrt      FAIL
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'bgrid', '4e', 1
RUNF = 'run_07_grid_baseline'


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4e: run_07 (baseline grids)')
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
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'baselineGrid.py'))
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rf = P1.record(recdir, '4d', 'fine') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    fp = C.md5_obj(dict(logic=LOGIC, reference=ref, fine=rf.get('outputs', {}).get('digest'), runs=P3.runfile_md5s(W, [RUNF]),
                        tools={k: v[1] for k, v in tm.items()}))
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R07_J', 'R07_OMP', 'R07_PEAK_KB')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rf = P3.prior3(st, 'G4e.1', recdir, '4d', 'fine')
    if not rf:
        return st.finish()
    planned = rf.get('outputs', {}).get('planned')
    if planned:
        st.gate('G4e.1', 'fine PASS on record', 'PASS', 'dry-run fine was a plan only')
    else:
        ch = P3.listing_changed(W, P3.OUTS['fine'], rf['outputs'].get('files'))
        st.gate('G4e.1', 'fine PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                'merged/SLC as fine recorded it (%d files)' % len(rf['outputs'].get('files', [])))
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G4e.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4e.3', tm, 'run_07\'s scripts'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R07', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G4e.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    if planned:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned fine')
    dates = rf['outputs'].get('dates') or []
    lines = P3.run_lines(wd, RUNF) or []
    tags = [P3.tag_of(x) for x in lines]
    bad = []
    if tags != [d for d in dates if d != ref] + [ref]:
        bad.append('run_07 names %s, want the secondaries then %s' % (tags, ref))
    for x, d in zip(lines, tags):
        k = P3.cfg_kv(P3.cfg_of(x))
        m = os.path.join(W, 'merged', 'SLC', d)
        want = dict(reference=os.path.join(m, 'referenceShelve'), secondary=os.path.join(m, 'secondaryShelve'),
                    baseline_file=os.path.join(W, 'merged', 'baselines', d, d))
        diff = ['%s %s' % (kk, k.get(kk)) for kk, vv in want.items() if k.get(kk) != vv]
        if diff:
            bad.append('%s: %s' % (d, '; '.join(diff)))
    st.gate('G4e.5', 'the run file', 'FAIL' if bad else 'PASS', '%s: %d lines, the secondaries then the reference' % (RUNF, len(lines)),
            'merged/SLC/<d> shelves; merged/baselines/<d>/<d>', '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    if a.dryrun:
        P3.way_gate(st, 'G4e.6', W, PHASE, True)
        return P3.plan_only(st, {RUNF: lines}, 'bgrid')
    if not P3.way_gate(st, 'G4e.6', W, PHASE, False):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G4e.7', W, s, r, RUNF, lines, logroot, logroot, 'bgrid')
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    specs, dims, bad = [], {}, []
    for x, d in zip(res, tags):
        m = re.search(r'dims:\s*(\d+)L\s*x\s*(\d+)P', open(x['log'], errors='replace').read())
        if not m:
            bad.append('%s: no "dims: nL x mP" line in %s' % (d, x['log']))
            continue
        dims[d] = [int(m.group(1)), int(m.group(2))]
        b = 'merged/baselines/%s/%s' % (d, d)
        specs += [(b, 4 * dims[d][0] * dims[d][1]), (b + '.xml', None), (b + '.vrt', None), (b + '.full.vrt', None)]
    bad += P3.expect(W, specs)
    ds = sorted(set('%dL x %dP' % tuple(v) for v in dims.values()))
    st.gate('G4e.8', 'merged/baselines', 'FAIL' if bad else 'PASS', '%d dates; grids %s' % (len(dims), ', '.join(ds)),
            '4 B x the logged dims; .xml, .vrt, .full.vrt', '\n'.join(bad[:10]))
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(reference=ref, dates=dates, dims=dims, files=lst, digest=P3.digest(lst))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_bgrid', main)
