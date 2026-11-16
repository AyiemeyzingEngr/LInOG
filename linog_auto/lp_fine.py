#!/usr/bin/env python3
"""lp_fine.py -- linog_auto Phase 4d: run_06_fineResamp, every date onto the reference grid, then G10.

Runs inside lp_env.sh. The first line copies the reference (` referenceStackCopy.py -i SLC/<REF>/<REF>.slc -o
merged/SLC/<REF>/<REF>.slc`, gdal_translate to ENVI: an .hdr, no .slc.xml); the others resample each secondary with
its rebased misreg (refineSecondaryTiming/dates/<date>/misreg). referenceStackCopy.py ignores the exit codes of its cp
and gdal_translate (A16), so the reference copy is checked by its size. G10 v2 (the kit's linog_fine_reg_gate.py <REF>
--reselect) measures the residual registration on merged/SLC at textured windows; it cannot see an off-frame granule
(G21 does). Its window survey is repeated once at depth G7_NCAND_RETRY when it finds fewer windows than the quorum.
v0.13 (the ascending record 17.4, 18.5): G10 v3 measures, after v2, every date's sub-sample shift against the reference's
copy on merged/SLC at the 3 x 3 cells' most textured windows (lp_reg3.py, numpy; its md5 in the record's tools, not the
fingerprint, so a frame fine ran under v0.12 stays CURRENT), a reading with WARN (v2 keeps the FAIL, G10-b); G10m reads the
offset between the modes on an FBS+FBD frame. v2's FAIL note gives 17.8's way on.

Gates
  G4d.1  datum PASS on record, dates/ as it left it; coarse's offsets as coarse recorded them         FAIL
  G4d.2  environment                                                                                  ERROR
  G4d.3  stripmapWrapper.py, referenceStackCopy.py, resampleSlc.py and the kit's G10 at their pins     FAIL
  G4d.4  the run file's commands resolve to the pinned env's stripmapStack (F13)                      FAIL
  G4d.5  run_06: the reference copy first, then one line per secondary; each config naming SLC/<REF>,
         merged/SLC/<d>, offsets/<d> and dates/<d>/misreg                                             FAIL
  G4d.6  nothing in the way: merged/SLC absent                                                          DECISION
  G4d.7  disk: free >= 8 B x W x L per date + disk_gib_margin                                           FAIL
  G4d.8  run_06: rc 0 on every line                                                                    FAIL
  G4d.9  merged/SLC/<date>/<date>.slc 8 B x W x L for every date (the reference's copy too, A16);
         .slc.xml for the secondaries, .hdr for the reference; referenceShelve/ and secondaryShelve/    FAIL
  G10    the kit's fine registration: no date called out by a majority of the voting windows          FAIL
  G10v3  (v0.13) every date's |dx| at most 0.125 samples on a mixed frame (rho 32 / 14), 0.0625 on an FBS-only or
         FBD-only frame (32 / 28, 16 / 14), |dy| at most 0.25 lines, on the voting windows (3 or more, ratio 1.25):
         INFO; WARN naming the dates otherwise, or NOT MEASURED                                           INFO / WARN
  G10m   (v0.13, a mixed frame) the FBD dates' median less the FBS dates': INFO; WARN when |dx| is over 0.1
         samples with its 95 % interval clear of 0; N/A on one mode                                      INFO / WARN
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import os

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'fine', '4d', 1
RUNF = 'run_06_fineResamp'
KIT = ('linog_fine_reg_gate.py', 'linog_reg_common.py')


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4d: run_06 (fineResamp), G10')
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
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'referenceStackCopy.py', 'resampleSlc.py'), kit=KIT)
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rd = P1.record(recdir, '4c', 'datum') or {}
    rc_ = P1.record(recdir, '3b', 'coarse') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    dates = sorted((rd.get('outputs', {}).get('after') or {}))
    fp = C.md5_obj(dict(logic=LOGIC, reference=ref, datum=rd.get('outputs', {}).get('md5s_after'), coarse=rc_.get('outputs', {}).get('digest'),
                        runs=P3.runfile_md5s(W, [RUNF]), slc=P3.slc_identity(W, dates), tools={k: v[1] for k, v in tm.items()},
                        settings={k: r[k] for k in ('G7_NCAND_RETRY',)}))
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R06_J', 'R06_OMP', 'R06_PEAK_KB', 'G7_NCAND_RETRY')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rd = P3.prior3(st, 'G4d.1', recdir, '4c', 'datum')
    if not rd:
        return st.finish()
    planned = rd.get('outputs', {}).get('planned')
    if planned:
        st.gate('G4d.1', 'datum PASS on record', 'PASS', 'dry-run datum was a plan only')
    else:
        ch = []
        if P3.shelf_md5s(W, 'refineSecondaryTiming/dates') != rd['outputs'].get('md5s_after'):
            ch.append('refineSecondaryTiming/dates/ is not the datum on record')
        ch += P3.listing_changed(W, ['offsets'], [x for x in (rc_.get('outputs', {}).get('files') or []) if x[0].startswith('offsets/')])
        if not geo:
            ch.append('recon/reference.json gives no reference geometry')
        st.gate('G4d.1', 'datum PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                'dates/ as datum left it (reference %s at 0 and 0); offsets/ as coarse recorded it' % ref)
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G4d.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4d.3', tm, 'run_06\'s scripts and the kit\'s G10'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R06', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G4d.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    if planned:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned datum')
    lines = P3.run_lines(wd, RUNF) or []
    secs = [d for d in dates if d != ref]
    first = ' referenceStackCopy.py -i %s -o %s' % (os.path.join(W, 'SLC', ref, '%s.slc' % ref),
                                                  os.path.join(W, 'merged', 'SLC', ref, '%s.slc' % ref))
    bad = []
    if not lines or lines[0].strip() != first.strip():
        bad.append('line 1 reads %r, want %r' % (lines[0] if lines else None, first))
    tags = [P3.tag_of(x) for x in lines[1:]]
    if sorted(tags) != secs:
        bad.append('lines 2.. name %s, want the %d secondaries' % (tags, len(secs)))
    for x, d in zip(lines[1:], tags):
        k = P3.cfg_kv(P3.cfg_of(x))
        want = dict(reference=os.path.join(W, 'SLC', ref), secondary=os.path.join(W, 'SLC', d), coreg=os.path.join(W, 'merged', 'SLC', d),
                    offsets=os.path.join(W, 'offsets', d), poly=os.path.join(W, 'refineSecondaryTiming', 'dates', d, 'misreg'))
        diff = ['%s %s' % (kk, k.get(kk)) for kk, vv in want.items() if k.get(kk) != vv]
        if diff:
            bad.append('%s: %s' % (d, '; '.join(diff)))
    st.gate('G4d.5', 'the run file', 'FAIL' if bad else 'PASS', '%s: the reference copy, then %d secondaries' % (RUNF, len(tags)),
            'SLC/<REF>, merged/SLC/<d>, offsets/<d>, dates/<d>/misreg', '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    Wd, L = geo['width'], geo['lines']
    B = 8 * Wd * L
    if a.dryrun:
        P3.way_gate(st, 'G4d.6', W, PHASE, True)
        print('   run_06 would write about %.1f GiB (%d dates x %d B)' % (P3.gib(B * len(dates)), len(dates), B))
        return P3.plan_only(st, {RUNF: lines}, 'fine')
    if not P3.way_gate(st, 'G4d.6', W, PHASE, False):
        return st.finish()
    if not P3.disk_gate(st, 'G4d.7', W, B * len(dates), float(cfg.get('disk_gib_margin', 0))):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G4d.8', W, s, r, RUNF, lines, logroot, logroot, 'fine')
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    specs = []
    for d in dates:
        specs += [('merged/SLC/%s/%s.slc' % (d, d), B), ('merged/SLC/%s/referenceShelve/data.dat' % d, None),
                  ('merged/SLC/%s/secondaryShelve/data.dat' % d, None)]
        specs.append(('merged/SLC/%s/%s.hdr' % (d, d), None) if d == ref else ('merged/SLC/%s/%s.slc.xml' % (d, d), None))
    bad = P3.expect(W, specs)
    txt = ''.join(open(x['log'], errors='replace').read() for x in res if x)
    npoly, nlist = txt.count('Polynomial doppler provided'), txt.count('List of coefficients provided')
    st.gate('G4d.9', 'merged/SLC', 'FAIL' if bad else 'PASS', '%d dates at %d B (the reference\'s copy included); logs: "Polynomial '
            'doppler provided" %d, "List of coefficients provided" %d' % (len(dates), B, npoly, nlist),
            '8 B x %d x %d; .slc.xml, or .hdr for the reference; both shelves (A16, A18)' % (Wd, L), '\n'.join(bad[:12]))
    if bad:
        return st.finish()
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(reference=ref, dates=dates, files=lst, digest=P3.digest(lst), doppler_lines=[npoly, nlist])
    lg = os.path.join(logroot, 'G10_fine_reg.log')
    krc, out = P3.kit_run(env, KIT[0], [ref, '--reselect'], W, lg)
    g = P3.reg_verdict(out)
    tries = [dict(ncand='default', rc=krc, verdict=g['verdict'], log=lg)]
    if krc == 1 and g['verdict'] == 'QUORUM':
        lg = os.path.join(logroot, 'G10_fine_reg_ncand%s.log' % r['G7_NCAND_RETRY'])
        krc, out = P3.kit_run(env, KIT[0], [ref, '--reselect'], W, lg, extra={'LINOG_REG_NCAND': r['G7_NCAND_RETRY']})
        g = P3.reg_verdict(out)
        tries.append(dict(ncand=r['G7_NCAND_RETRY'], rc=krc, verdict=g['verdict'], log=lg))
    failed = sorted(d for d, (cells, v) in g['dates'].items() if v == 'FAIL')
    st.rec['outputs']['g10'] = dict(tries=tries, verdict=g['verdict'], nbad=g['nbad'], n=g['n'], windows=g['windows'],
                                    dates={d: list(v) for d, v in g['dates'].items()})
    if krc == 0 and g['verdict'] == 'PASS' and g['n'] == len(secs):
        st.gate('G10', 'fine registration (kit)', 'WARN' if len(tries) > 1 else 'PASS', '0 of %d dates called out%s' % (
            g['n'], ' (at depth %s)' % r['G7_NCAND_RETRY'] if len(tries) > 1 else ''), 'linog_fine_reg_gate.py %s --reselect rc 0' % ref)
    elif krc in (0, 1) and g['verdict'] in ('FAIL', 'QUORUM'):
        st.gate('G10', 'fine registration (kit)', 'FAIL', '%s: %s' % (g['verdict'], ', '.join(failed) if failed else
                '%s window(s), quorum %s' % (g['windows'], g['quorum'])), 'rc 0',
                '\n'.join('%s  %s' % (d, g['dates'][d][0]) for d in failed) + '\nlog %s' % lg + (WAY_ON if failed else ''))
    else:
        st.gate('G10', 'fine registration (kit)', 'ERROR', 'rc %d, verdict %s, %s of %d dates reported' % (
            krc, g['verdict'], g['n'], len(secs)), 'rc 0 or 1 with a verdict line', 'log %s\n%s' % (lg, P3.tail(lg)))
    st.rec['outputs']['g10v3'] = g10v3(st, W, ref, dates, geo)
    return st.finish()


WAY_ON = ('\nthe way on (17.8), by hand: the date into recon/exclude.txt; its traces moved into _archive/ as 11.1 lists them, with '
          'offsets/<d>/ and coregSLC/Coarse/<d>/; refineSecondaryTiming/ and merged/SLC/ moved whole (every pair\'s partner set and '
          'every date\'s R9 value change with the network); stack2\'s products moved; then a run from the top: recon to stack2 by '
          'reuse, topo CURRENT (the reference kept), coarse by 11.5\'s reuse, refine again, invert, datum (R9 on an FBS+FBD frame, '
          'G16 on one mode), fine')


def g10v3(st, W, ref, dates, geo):
    """v0.13, G10 v3 and G10m (17.4): the reading on merged/SLC, its verdict lines, the record's outputs.g10v3. An error inside
    the reading gives G10v3 WARN (NOT MEASURED) with its traceback: a reading, it does not make the phase run again."""
    import traceback
    try:
        import lp_reg3 as R3
        st.rec.setdefault('tools', {}).update(C.tool_md5s('lp_reg3.py'))
        rows, _, _ = P2.modes_rows(W)
        modes = dict((d, (rows.get(d) or {}).get('mode')) for d in dates)
        ms = set(m for m in modes.values() if m)
        mixed = ms == {'FBS', 'FBD'}
        rho = 32.0 / 14.0 if mixed else (32.0 / 28.0 if ms == {'FBS'} else 16.0 / 14.0)
        hgt, why = R3.load_hgt(W)
        if hgt is None:
            raise ValueError(why)
        refp = os.path.join(W, 'merged', 'SLC', ref, '%s.slc' % ref)
        secs = dict((d, os.path.join(W, 'merged', 'SLC', d, '%s.slc' % d)) for d in dates if d != ref)
        n, wins, named, survey, rd = R3.g10v3_read(refp, secs, geo['width'], geo['lines'], hgt)
        summ = R3.g10v3_summary(n, wins, rd, modes, ref, geo['width'])
        for gid, v, val, thr, note in R3.g10v3_verdicts(summ, mixed, rho):
            nm = 'fine registration v3 (17.4)' if gid == 'G10v3' else 'the modes\' offset (17.4)'
            st.gate(gid, nm, v, val, thr, '; '.join(x for x in (note, ('no viable window in %s' % ', '.join(named)) if named and gid == 'G10v3'
                                                                 else '') if x))
        return dict(window=n, rho=rho, mixed=mixed, named=named, survey=survey, readings=rd, **summ)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        st.gate('G10v3', 'fine registration v3 (17.4)', 'WARN', 'NOT MEASURED: %s: %s' % (type(e).__name__, e), 'a reading',
                '\n'.join(tb[-6:]))
        return dict(error='%s: %s' % (type(e).__name__, e))


if __name__ == '__main__':
    P1.main_guard('lp_fine', main)
