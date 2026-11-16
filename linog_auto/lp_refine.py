#!/usr/bin/env python3
"""lp_refine.py -- linog_auto Phase 4a: run_04_refineSecondaryTiming, one line per pair of the network, then G8.

Runs inside lp_env.sh. Each line estimates the offset between two coarse SLCs (ampcor, a constant azimuth and range
term) and writes refineSecondaryTiming/pairs/<pair>/misreg (a shelve, dbm.dumb on felix: misreg.dat/.dir/.bak) with
azpoly and rgpoly; ISCE writes off.log in the frame. run_04 is single-threaded per job and the 12 frames ran it wide
(-j 46, OMP 2). G8 (linog_gate_catalogue): the kit's census, linog_pair_misreg_census.py, prints per-pair offsets and
the |rg| > 5 listing (N52) but no verdict (B57), so this phase decides from the shelves: FAIL when G8_SHARE or more of
the reference's pairs read |az| > G8_AZ_PX; the |rg| > G8_RG_PX pairs are listed with WARN (N53's signature). F15: the
pairs with a readable shelve must connect every date (invertMisreg inverts over them). v0.9 (record 81): ampcor plans its
FFTs through ISCE2's cfft1d_jpl, by timing them unless a wisdom file is given (S25: 9 distinct results in 46 runs without
one, 1 with it); the pinned wisdom (lp_fftw.py, linog_fftw.cfg) is checked first and goes to every job as WISDOM_FILE,
and every job's log must show it imported. LOGIC 2: the fingerprint carries the pins, so a frame refined by v0.8 reads STALE.

Gates
  G4a.1  coarse PASS on record, its outputs as it recorded them                                      FAIL
  G4a.2  environment                                                                                  ERROR
  G4a.3  stripmapWrapper.py, refineSecondaryTiming.py and the kit's G8 at their pins                  FAIL
  G4a.4  the run file's command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G4a.4w the FFTW wisdom (v0.9): the file, the env's libfftw3f and ampcor's module at their pins; in a
         fresh process the file imports and covers every problem, none without it                       FAIL
  G4a.5  run_04: one line per pair of run_08 (stack2's network), each config naming the two coarse SLCs
         (the reference's own SLC for the reference) and pairs/<pair>/misreg                           FAIL
  G4a.6  nothing in the way: refineSecondaryTiming/pairs absent                                        DECISION
  G4a.7  run_04: rc 0 on every line                                                                    FAIL
  G4a.7w every line's log: ampcor's wisdom line naming the pinned file, the import's 1, no STOP; the file
         still at the md5 G4a.4w found                                                                 FAIL
  G4a.8  every pair's misreg shelve (misreg.dat) readable, azpoly and rgpoly finite                    FAIL
  F15    the pairs connect every date of the stack                                                     FAIL
  G8     the reference's pairs: share with |az| > G8_AZ_PX below G8_SHARE; |rg| > G8_RG_PX listed    FAIL / WARN
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import math
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'refine', '4a', 2   # v0.9: the pinned FFTW wisdom (LOGIC 1 before)
RUNF = 'run_04_refineSecondaryTiming'
FFT = ('ampcor',)   # v0.9: the modules of this step's jobs that plan through cfft1d_jpl


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4a: run_04 (refineSecondaryTiming), G8')
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
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'refineSecondaryTiming.py'), kit=('linog_pair_misreg_census.py',))
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rc_ = P1.record(recdir, '3b', 'coarse') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    fp = C.md5_obj(dict(logic=LOGIC, reference=ref, coarse=rc_.get('outputs', {}).get('digest'), runs=P3.runfile_md5s(W, [RUNF]),
                        tools={k: v[1] for k, v in tm.items()}, settings={k: r[k] for k in ('G8_AZ_PX', 'G8_SHARE', 'G8_RG_PX')},
                        fftw=P3.fftw_pins(FFT)))
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R04_J', 'R04_OMP', 'R04_PEAK_KB', 'G8_AZ_PX', 'G8_SHARE', 'G8_RG_PX')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rc_ = P3.prior3(st, 'G4a.1', recdir, '3b', 'coarse')
    if not rc_:
        return st.finish()
    planned = rc_.get('outputs', {}).get('planned')
    if planned:
        st.gate('G4a.1', 'coarse PASS on record', 'PASS', 'dry-run coarse was a plan only')
    else:
        ch = P3.listing_changed(W, P3.OUTS['coarse'], rc_['outputs'].get('files'))
        st.gate('G4a.1', 'coarse PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                'offsets/ and coregSLC/ as coarse recorded them (%d files)' % len(rc_['outputs'].get('files', [])))
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G4a.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4a.3', tm, 'run_04\'s scripts and the kit\'s G8'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R04', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G4a.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    wis, fx = P3.fftw_gate(st, 'G4a.4w', s, FFT)
    st.rec['inputs']['fftw'] = fx
    if not wis:
        return st.finish()
    if planned:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned coarse')

    lines = P3.run_lines(wd, RUNF) or []
    pairs = [P3.tag_of(x) for x in lines]
    net = sorted('%s_%s' % tuple(p) for p in P2.read_pass(wd)['pairs'])
    secs = rc_['outputs'].get('secondaries') or []
    dates = sorted(set(secs + [ref]))
    bad = []
    if sorted(pairs) != net or len(set(pairs)) != len(pairs):
        bad.append('run_04 names %d pairs, run_08 %d; they differ' % (len(pairs), len(net)))
    for x, pr in zip(lines, pairs):
        k = P3.cfg_kv(P3.cfg_of(x))
        a1, a2 = pr.split('_') if '_' in pr else (None, None)
        want = {}
        for key, d in (('reference', a1), ('secondary', a2)):
            want[key] = os.path.join(W, 'SLC', d, '%s.slc' % d) if d == ref else os.path.join(W, 'coregSLC', 'Coarse', d, '%s.slc' % d)
        want['outfile'] = os.path.join(W, 'refineSecondaryTiming', 'pairs', pr, 'misreg')
        diff = ['%s %s' % (kk, k.get(kk)) for kk, vv in want.items() if k.get(kk) != vv]
        if diff:
            bad.append('%s: %s' % (pr, '; '.join(diff)))
    st.gate('G4a.5', 'the run file', 'FAIL' if bad else 'PASS', '%s: %d lines, the %d pairs of run_08; %d dates' % (
        RUNF, len(lines), len(net), len(dates)), 'one line per pair; coarse SLCs (the reference\'s own SLC); pairs/<pair>/misreg',
        '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    if a.dryrun:
        P3.way_gate(st, 'G4a.6', W, PHASE, True)
        return P3.plan_only(st, {RUNF: lines}, 'refine')
    if not P3.way_gate(st, 'G4a.6', W, PHASE, False):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G4a.7', W, s, r, RUNF, lines, logroot, logroot, 'refine', wisdom=wis)
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    okw, st.rec['outputs']['fftw'] = P3.fftw_logs_gate(st, 'G4a.7w', res, wis, 1, 'ampcor', fx['wisdom_md5'])
    if not okw:
        return st.finish()
    vals, bad = {}, []
    for pr in pairs:
        p = os.path.join(W, 'refineSecondaryTiming', 'pairs', pr, 'misreg')
        if not os.path.isfile(p + '.dat'):
            bad.append('%s: no misreg.dat' % pr)
            continue
        try:
            az, rg = P3.shelf_consts(p)
        except Exception as e:  # noqa: BLE001
            bad.append('%s: %s: %s' % (pr, type(e).__name__, e))
            continue
        if not (math.isfinite(az) and math.isfinite(rg)):
            bad.append('%s: az %s rg %s' % (pr, az, rg))
        vals[pr] = (az, rg)
    st.gate('G4a.8', 'the pairs\' misreg shelves', 'FAIL' if bad else 'PASS', '%d of %d readable (misreg.dat, azpoly, rgpoly)' % (
        len(vals), len(pairs)), 'every pair', '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    comps = P3.network_components(dates, [pr.split('_') for pr in vals])
    st.gate('F15', 'the network of the refined pairs', 'PASS' if len(comps) == 1 else 'FAIL', '%d component(s), %d dates, %d pairs' % (
        len(comps), len(dates), len(vals)), 'one component', '' if len(comps) == 1 else '\n'.join(' '.join(c) for c in comps))
    if len(comps) != 1:
        return st.finish()
    lg = os.path.join(logroot, 'G8_pair_misreg_census.log')
    krc, out = P3.kit_run(env, 'linog_pair_misreg_census.py', [ref], W, lg)
    m = re.search(r'^pairs read: (\d+)\s+unreadable: (\d+)', out, re.M)
    refp = {pr: v for pr, v in vals.items() if ref in pr.split('_')}
    big_az = sorted(pr for pr, (az, rg) in refp.items() if abs(az) > float(r['G8_AZ_PX']))
    big_rg = sorted((pr for pr, (az, rg) in vals.items() if abs(rg) > float(r['G8_RG_PX'])), key=lambda pr: -abs(vals[pr][1]))
    share = len(big_az) / float(len(refp)) if refp else 1.0
    kit_ok = krc == 0 and m and int(m.group(1)) == len(vals) and int(m.group(2)) == 0
    note = ['kit census rc %d: %s (log %s)' % (krc, m.group(0) if m else 'no "pairs read" line', lg)]
    if big_az:
        note.append('|az| > %s px: %s' % (r['G8_AZ_PX'], ', '.join('%s %+.3f' % (pr, vals[pr][0]) for pr in big_az)))
    if big_rg:
        note.append('|rg| > %s px (N52/N53): %s' % (r['G8_RG_PX'], ', '.join('%s %+.3f' % (pr, vals[pr][1]) for pr in big_rg[:15])))
    verdict = 'FAIL' if (share >= float(r['G8_SHARE']) or not refp or not kit_ok) else ('WARN' if big_rg else 'PASS')
    azs = [v[0] for v in vals.values()]
    rgs = [v[1] for v in vals.values()]
    st.gate('G8', 'reference-pair quality', verdict, '%d of %d reference pairs |az| > %s px (%.0f %%); %d of %d pairs |rg| > %s px; '
            'all pairs az %.3f..%.3f, rg %.3f..%.3f' % (len(big_az), len(refp), r['G8_AZ_PX'], 100 * share, len(big_rg), len(vals),
                                                     r['G8_RG_PX'], min(azs), max(azs), min(rgs), max(rgs)),
            'share < %s; the kit census reads every pair' % r['G8_SHARE'], '\n'.join(note))
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(reference=ref, pairs=len(vals), dates=dates, misreg={pr: [round(v[0], 6), round(v[1], 6)]
                             for pr, v in sorted(vals.items())}, g8=dict(rc=krc, log=lg, ref_pairs=len(refp), az_over=big_az,
                             rg_over=big_rg), files=lst, digest=P3.digest(lst),
                             cwd_logs={n: os.path.getsize(os.path.join(W, n)) for n in ('off.log',) if os.path.isfile(os.path.join(W, n))})
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_refine', main)
