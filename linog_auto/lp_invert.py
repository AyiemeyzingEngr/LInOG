#!/usr/bin/env python3
"""lp_invert.py -- linog_auto Phase 4b: run_05_invertMisreg, the per-date misregistration from the pairs.

Runs inside lp_env.sh. The one line, `invertMisreg.py -i <frame>/refineSecondaryTiming/pairs/ -o .../dates/`, inverts
every folder under pairs/ (a glob: an extra folder there would enter the inversion) and writes dates/<date>/misreg for
every date, with the EARLIEST date pinned at 0 (N23, linog_reference_datum_bug; G16 in datum rebases onto the
reference). Two false successes on p448 f0300 read rc 0 with an empty log (paste-rule 5): the gate is the shelves
themselves and the log's "Design matrix is full rank." line, not the exit code. The log size is recorded beside B58's
law (about 878 + 773 x pairs bytes).

Gates
  G4b.1  refine PASS on record, its outputs as it recorded them; pairs/ holds exactly its pairs           FAIL
  G4b.2  environment                                                                                  ERROR
  G4b.3  invertMisreg.py at its pin                                                                    FAIL
  G4b.4  the run file's command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G4b.5  run_05: the one line, -i pairs/ -o dates/ of this frame                                       FAIL
  G4b.6  nothing in the way: refineSecondaryTiming/dates absent                                        DECISION
  G4b.7  run_05: rc 0                                                                                  FAIL
  G4b.8  the log: "Design matrix is full rank.", no "rank deficient"; RMSE in azimuth and range        FAIL
  G4b.9  dates/<date>/misreg.dat for every date, readable; the earliest date reads 0 and 0             FAIL
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'invert', '4b', 1
RUNF = 'run_05_invertMisreg'


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4b: run_05 (invertMisreg)')
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
    tm = P3.tools(s, env, r, isce=('invertMisreg.py',))
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rr = P1.record(recdir, '4a', 'refine') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    fp = C.md5_obj(dict(logic=LOGIC, refine=rr.get('outputs', {}).get('digest'), runs=P3.runfile_md5s(W, [RUNF]),
                        tools={k: v[1] for k, v in tm.items()}))
    if a.state:
        # datum rewrites the shelves in place (G16), so this phase's outputs are checked by name only
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'), names_only=True)
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rr = P3.prior3(st, 'G4b.1', recdir, '4a', 'refine')
    if not rr:
        return st.finish()
    planned = rr.get('outputs', {}).get('planned')
    if planned:
        st.gate('G4b.1', 'refine PASS on record', 'PASS', 'dry-run refine was a plan only')
    else:
        ch = P3.listing_changed(W, P3.OUTS['refine'], rr['outputs'].get('files'))
        pd = os.path.join(W, 'refineSecondaryTiming', 'pairs')
        have = sorted(os.listdir(pd)) if os.path.isdir(pd) else []
        want = sorted(rr['outputs'].get('misreg', {}))
        if have != want:
            ch.append('pairs/ holds %d entries, refine recorded %d pairs%s' % (len(have), len(want), (
                ': extra %s' % ', '.join(sorted(set(have) - set(want))[:5])) if set(have) - set(want) else ''))
        st.gate('G4b.1', 'refine PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                'pairs/ as refine recorded it: %d pairs, nothing else' % len(want))
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G4b.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4b.3', tm, 'invertMisreg.py'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R05', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G4b.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    if planned:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned refine')
    lines = P3.run_lines(wd, RUNF) or []
    wantl = 'invertMisreg.py -i %s/ -o %s/' % (pd, os.path.join(W, 'refineSecondaryTiming', 'dates'))
    ok = [x.strip() for x in lines] == [wantl]
    st.gate('G4b.5', 'the run file', 'PASS' if ok else 'FAIL', '%s: %s' % (RUNF, lines[0].strip() if lines else 'no line'),
            wantl, '' if ok else 'want exactly that one line')
    if not ok:
        return st.finish()
    if a.dryrun:
        P3.way_gate(st, 'G4b.6', W, PHASE, True)
        return P3.plan_only(st, {RUNF: lines}, 'invert')
    if not P3.way_gate(st, 'G4b.6', W, PHASE, False):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G4b.7', W, s, r, RUNF, lines, logroot, logroot, 'invert')
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    lg = res[0]['log']
    txt = open(lg, errors='replace').read()
    full = 'Design matrix is full rank.' in txt and 'rank deficient' not in txt
    raz = re.search(r'RMSE in azimuth\s*:\s*([-+.\deE]+)', txt)
    rrg = re.search(r'RMSE in range\s*:\s*([-+.\deE]+)', txt)
    npairs = len(want)
    law = 878 + 773 * npairs
    st.gate('G4b.8', 'the inversion\'s log', 'PASS' if full and raz and rrg else 'FAIL', '%s; RMSE azimuth %s, range %s px; log %d B '
            '(B58: about %d B for %d pairs)' % ('full rank' if full else 'NOT full rank', raz.group(1) if raz else '?',
                                                rrg.group(1) if rrg else '?', res[0]['log_bytes'], law, npairs),
            '"Design matrix is full rank."', '' if full else P3.tail(lg, 8))
    if not (full and raz and rrg):
        return st.finish()
    dates = rr['outputs'].get('dates') or []
    vals, bad = {}, []
    for d in dates:
        p = os.path.join(W, 'refineSecondaryTiming', 'dates', d, 'misreg')
        if not os.path.isfile(p + '.dat'):
            bad.append('%s: no misreg.dat' % d)
            continue
        try:
            vals[d] = P3.shelf_consts(p)
        except Exception as e:  # noqa: BLE001
            bad.append('%s: %s: %s' % (d, type(e).__name__, e))
    dd = os.path.join(W, 'refineSecondaryTiming', 'dates')
    extra = sorted(set(os.listdir(dd)) - set(dates)) if os.path.isdir(dd) else []
    if extra:
        bad.append('dates/ holds more: %s' % ', '.join(extra))
    first = dates[0] if dates else None
    if first in vals and (abs(vals[first][0]) > 1e-9 or abs(vals[first][1]) > 1e-9):
        bad.append('the earliest date %s reads az %.6f rg %.6f, not 0 and 0' % ((first,) + vals[first]))
    st.gate('G4b.9', 'the dates\' misreg shelves', 'FAIL' if bad else 'PASS', '%d of %d dates; %s (the earliest) reads 0 and 0; '
            'reference %s reads az %s rg %s' % (len(vals), len(dates), first, ref, '%+.4f' % vals[ref][0] if ref in vals else '?',
                                                 '%+.4f' % vals[ref][1] if ref in vals else '?'), 'every date; N23', '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(dates=dates, first=first, reference=ref, misreg={d: [v[0], v[1]] for d, v in sorted(vals.items())},
                             rmse=dict(azimuth=float(raz.group(1)), range=float(rrg.group(1))), log_bytes=res[0]['log_bytes'],
                             files=lst, digest=P3.digest(lst), md5s=P3.shelf_md5s(W, 'refineSecondaryTiming/dates'))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_invert', main)
