#!/usr/bin/env python3
"""lp_igram.py -- linog_auto Phase 4f: run_08_igram, the interferograms of the network, then G11 and the per-date view.

Runs inside lp_env.sh. One line per pair: crossmul (merged/SLC, or the reference's own SLC/<REF> image for its pairs,
opened through its .xml FILE_NAME relative to the frame folder, A30), FilterAndCoherence (Goldstein 0.8), and unwrap
(snaphu inside ISCE, not a program on the PATH, A22) into Igrams/<pair>/: <pair>.int and .amp, filt_<pair>.int,
filt_<pair>.cor, filt_<pair>_snaphu.unw and .unw.conncomp, on the multilooked grid (int(W / rlks) x int(L / alks)).
crossmul holds about 7 GB per job (A25), so a job runs only when MemAvailable holds it. crossmul did not reproduce its
bytes run to run (A31): it and icu plan their FFTs through ISCE2's cfft1d_jpl, by timing them unless a wisdom file is
given (S25: crossmul 9 distinct results in 12 runs without one, 1 with it). v0.9 (record 81) checks the pinned wisdom
(lp_fftw.py, linog_fftw.cfg) first, gives it to every job as WISDOM_FILE and reads every job's log for crossmul's and
icu's import of it; the outputs are still checked by size. LOGIC 2: the fingerprint carries the pins. G17 is read
again first: crossmul opens the reference's .slc.vrt, which no run step makes. G11 is the kit's census (linog_coherence_census.py, --fbs-dir SLC on an
FBS-only stack: every date is FBS) and linog_date_coherence.py the per-date view; a date none of whose pairs reaches
COH_MARK is listed with WARN, and FAILs when it is the reference (the datum bug's signature).
v0.13 (the ascending record 4.8, 18.5, 21.4): the census's FBS dates come from recon/modes.json: one empty folder per FBS
date under logs/igram/fbs_dates_<UTC>/, passed as --fbs-dir (on an FBD-only frame its one entry, _none/, matches no date, so
every pair classes FBD-FBD: the census stops on an empty folder, its N36 guard); G11m checks the census's "FBS dates N"
against recon/modes.json's FBS count (on an FBD-only frame 1, the placeholder, and the class table: every pair FBD-FBD).
G17 before run_08 also requires the reference .xml's FILE_NAME to name SLC/<REF>/<REF>.slc (crossmul opens FILE_NAME's .vrt,
G17 reads SLC/<REF>/<REF>.slc.vrt), and G11d's FAIL text names N25 beside the datum bug.
v0.13 r2 (the ascending record 25.4, 25.6, 25-b): G17 also reads that .xml's width as isce2 2.6.3 loads it, the one crossmul
loads (coordinate1's size, lp_xmlwidth), against the geometry's width, and FAILs a file whose fields disagree within itself;
before r2 it read no width field of the .xml, so a file in the backups' state of P448 F0280's .xml.bak9376 passed it. An
edit of that .xml after Phase 2b already turns reference, topo, coarse, fine and igram STALE (their fingerprints hold its
size and mtime, lp_p3.slc_identity): this is a second check. Where the fields agree the verdict is v0.13's; LOGIC and the
fingerprint stay (igram comes before admit).

Gates
  G4f.1  bgrid PASS on record; merged/SLC as fine recorded it                                        FAIL
  G4f.2  environment                                                                                  ERROR
  G4f.3  stripmapWrapper.py, crossmul.py, FilterAndCoherence.py, unwrap.py and the kit's G11 and
         date-coherence scripts at their pins                                                          FAIL
  G4f.4  the run file's command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G4f.4w the FFTW wisdom (v0.9): the file, the env's libfftw3f and crossmul's and icu's modules at their
         pins; in a fresh process the file imports and covers every problem, none without it            FAIL
  G17    the reference: SLC/<REF>/<REF>.slc.vrt W wide; its .xml FILE_NAME resolves from the frame (v0.13: to
         SLC/<REF>/<REF>.slc itself); v0.13 r2: its .xml W wide as isce2 loads it, its fields agreeing  FAIL
  G4f.5  run_08: one line per pair of the network, each config crossmul -> filter -> unwrap into
         Igrams/<pair>/, looks as the geometry                                                         FAIL
  G4f.6  nothing in the way: Igrams absent                                                              DECISION
  G4f.7  disk                                                                                           FAIL
  G4f.8  run_08: rc 0 on every line (jobs held by memory: WARN)                                        FAIL
  G4f.8w every line's log: crossmul's and icu's wisdom lines naming the pinned file, each import 1, no STOP;
         the file still at the md5 G4f.4w found                                                        FAIL
  G4f.9  every pair's six products at their sizes (8, 8, 8, 4, 8, 1 B x gw x gl) with .xml            FAIL
  G11    the kit's census: every pair read, run_08's lines MATCH; the mean coherence recorded          FAIL
  G11m   (v0.13) the census's FBS dates = recon/modes.json's FBS count (an FBD-only frame: 1, the _none/ placeholder,
         and every pair FBD-FBD)                                                                        FAIL
  G11d   per date: no date without a pair above COH_MARK (WARN); not the reference (FAIL)           WARN / FAIL
--dryrun DIR: a plan only. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
Self-test only (under a path table other than the package's own, lp_common.selftest_hook): LINOG_MOCK_G11_SLC=1 passes SLC as
the census's --fbs-dir, v0.12's call (M14: G11m FAILs it on a mixed frame).
"""
import argparse
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'igram', '4f', 2   # v0.9: the pinned FFTW wisdom (LOGIC 1 before)
RUNF = 'run_08_igram'
FFT = ('crossmul', 'icu')   # v0.9: the modules of this step's jobs that plan through cfft1d_jpl, in log order
KIT = ('linog_coherence_census.py', 'linog_date_coherence.py')
PRODUCTS = (('%s.int', 8), ('%s.amp', 8), ('filt_%s.int', 8), ('filt_%s.cor', 4), ('filt_%s_snaphu.unw', 8),
            ('filt_%s_snaphu.unw.conncomp', 1))


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 4f: run_08 (interferograms), G11')
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
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'crossmul.py', 'FilterAndCoherence.py', 'unwrap.py'), kit=KIT)
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rb = P1.record(recdir, '4e', 'bgrid') or {}
    rf = P1.record(recdir, '4d', 'fine') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    fp = C.md5_obj(dict(logic=LOGIC, reference=ref, fine=rf.get('outputs', {}).get('digest'), bgrid=rb.get('outputs', {}).get('digest'),
                        runs=P3.runfile_md5s(W, [RUNF]), slc=P3.slc_identity(W, [ref] if ref else []),
                        tools={k: v[1] for k, v in tm.items()}, settings={k: r[k] for k in ('COH_MARK',)}, fftw=P3.fftw_pins(FFT)))
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R08_J', 'R08_OMP', 'R08_PEAK_KB', 'COH_MARK')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rb = P3.prior3(st, 'G4f.1', recdir, '4e', 'bgrid')
    if not rb:
        return st.finish()
    planned = rb.get('outputs', {}).get('planned')
    if planned:
        st.gate('G4f.1', 'bgrid PASS on record', 'PASS', 'dry-run bgrid was a plan only')
    else:
        ch = P3.listing_changed(W, P3.OUTS['fine'], rf.get('outputs', {}).get('files'))
        if not geo:
            ch.append('recon/reference.json gives no reference geometry')
        st.gate('G4f.1', 'bgrid PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or 'merged/SLC as fine recorded it')
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G4f.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G4f.3', tm, 'run_08\'s scripts and the kit\'s G11'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R08', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G4f.4', s, jenv, P3.RUN[RUNF][1]):
        return st.finish()
    wis, fx = P3.fftw_gate(st, 'G4f.4w', s, FFT)
    st.rec['inputs']['fftw'] = fx
    if not wis:
        return st.finish()
    if planned and not geo:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned bgrid; no reference geometry yet')
    Wd, L, gw, gl = geo['width'], geo['lines'], geo['gw'], geo['gl']
    sd = os.path.join(W, 'SLC', ref)
    vrt = os.path.join(sd, '%s.slc.vrt' % ref)
    m = re.search(r'rasterXSize="(\d+)"', open(vrt).read()) if os.path.isfile(vrt) else None
    fname = P3.xml_file_name(os.path.join(sd, '%s.slc.xml' % ref))
    target = fname if fname and os.path.isabs(fname) else os.path.join(W, fname or '')
    own = os.path.join(sd, '%s.slc' % ref)
    bad = []
    if not m or int(m.group(1)) != Wd:
        bad.append('%s rasterXSize %s, want %d' % (vrt, m.group(1) if m else 'absent', Wd))
    if not fname or not os.path.isfile(target) or os.path.getsize(target) != 8 * Wd * L:
        bad.append('.slc.xml FILE_NAME %s: %s' % (fname, 'resolves to %s' % target if fname else 'absent'))
    elif os.path.realpath(target) != os.path.realpath(own):   # v0.13 (21.4): crossmul opens FILE_NAME's .vrt
        bad.append('.slc.xml FILE_NAME %s names %s, not %s (crossmul opens that file\'s .vrt, G17 reads %s)' % (
            fname, os.path.realpath(target), own, vrt))
    elif os.path.realpath(target + '.vrt') != os.path.realpath(vrt):   # the .vrt crossmul opens is the one read here (P4-16)
        bad.append('.slc.xml FILE_NAME %s: crossmul would open %s, G17 reads %s' % (fname, os.path.realpath(target + '.vrt'),
                                                                                     os.path.realpath(vrt)))
    # v0.13 r2 (25-b): the width crossmul loads from that .xml (coordinate1's size), against the geometry's, and the file
    # against itself
    import lp_xmlwidth as XW
    st.rec.setdefault('tools', {}).update(C.tool_md5s('lp_xmlwidth.py'))   # recorded, not fingerprinted
    xw, _, xprob = XW.check(os.path.join(sd, '%s.slc.xml' % ref), Wd, 'the geometry\'s width')
    bad += ['%s.slc.xml: %s' % (ref, x) for x in xprob]
    st.gate('G17', 'the reference .slc.vrt and FILE_NAME', 'FAIL' if bad else 'PASS', '%s rasterXSize %s; FILE_NAME %s resolves '
            'from the frame (%d B); .slc.xml %s wide as isce2 loads it' % (
                os.path.basename(vrt), m.group(1) if m else '?', fname, os.path.getsize(target) if os.path.isfile(target) else -1, xw),
            'W wide; crossmul opens it (A30)', '\n'.join(bad))
    if bad:
        return st.finish()
    if planned:
        return P3.plan_only(st, {RUNF: P3.run_lines(wd, RUNF)}, 'after a planned bgrid')
    lines = P3.run_lines(wd, RUNF) or []
    pairs = [P3.tag_of(x) for x in lines]
    net = sorted('%s_%s' % tuple(p) for p in P2.read_pass(wd)['pairs'])
    bad = []
    if sorted(pairs) != net:
        bad.append('run_08 names %d pairs, the network %d' % (len(pairs), len(net)))
    for x, pr in zip(lines, pairs):
        txt = open(P3.cfg_of(x) or os.devnull).read()
        k = P3.cfg_kv(P3.cfg_of(x))
        fn = [ln.strip().split()[0] for ln in txt.splitlines() if re.match(r'^\w+\s*:\s*$', ln.strip())]
        ig = os.path.join(W, 'Igrams', pr)
        if fn != ['crossmul', 'FilterAndCoherence', 'unwrap'] or k.get('outdir') != os.path.join(ig, pr) or \
                k.get('alks') != str(geo['alks']) or k.get('rlks') != str(geo['rlks']) or \
                k.get('filt') != os.path.join(ig, 'filt_%s.int' % pr) or k.get('unwprefix') != os.path.join(ig, 'filt_%s' % pr):
            bad.append('%s: functions %s, outdir %s, looks %s x %s' % (pr, fn, k.get('outdir'), k.get('alks'), k.get('rlks')))
    st.gate('G4f.5', 'the run file', 'FAIL' if bad else 'PASS', '%s: %d lines, the network\'s pairs; crossmul, filter, unwrap into '
            'Igrams/<pair>/ at %s x %s looks' % (RUNF, len(lines), geo['alks'], geo['rlks']), 'one line per pair', '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    per = sum(b for _, b in PRODUCTS) * gw * gl
    if a.dryrun:
        P3.way_gate(st, 'G4f.6', W, PHASE, True)
        print('   run_08 would write about %.1f GiB (%d pairs x %d B on the %d x %d grid)' % (P3.gib(per * len(pairs)), len(pairs),
                                                                                             per, gw, gl))
        return P3.plan_only(st, {RUNF: lines}, 'igram')
    if not P3.way_gate(st, 'G4f.6', W, PHASE, False):
        return st.finish()
    if not P3.disk_gate(st, 'G4f.7', W, per * len(pairs), float(cfg.get('disk_gib_margin', 0))):
        return st.finish()
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    ok, summ, res = P3.run_step(st, 'G4f.8', W, s, r, RUNF, lines, logroot, logroot, 'igram', wisdom=wis)
    st.rec['outputs'] = dict(logdir=logroot, steps={RUNF: summ})
    if not ok:
        return st.finish()
    okw, st.rec['outputs']['fftw'] = P3.fftw_logs_gate(st, 'G4f.8w', res, wis, len(FFT), ' and '.join(FFT), fx['wisdom_md5'])
    if not okw:
        return st.finish()
    specs = []
    for pr in pairs:
        for pat, b in PRODUCTS:
            f = 'Igrams/%s/%s' % (pr, pat % pr)
            specs += [(f, b * gw * gl), (f + '.xml', None)]
    bad = P3.expect(W, specs)
    st.gate('G4f.9', 'the interferograms', 'FAIL' if bad else 'PASS', '%d pairs x 6 products on the %d x %d grid (%d B per pair)' % (
        len(pairs), gw, gl, per), '8, 8, 8, 4, 8, 1 B x gw x gl; .xml', '\n'.join(bad[:12]))
    if bad:
        return st.finish()
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(reference=ref, pairs=len(pairs), files=lst, digest=P3.digest(lst))
    lg = os.path.join(logroot, 'G11_coherence_census.log')
    rows_m, _, _ = P2.modes_rows(W)
    fbs_m = sorted(d for d, v in rows_m.items() if v.get('mode') == 'FBS')
    fdir = os.path.join(W, 'logs', 'igram', 'fbs_dates_%s' % C.utc().replace('-', '').replace(':', ''))
    for d in (fbs_m or ['_none']):   # v0.13 (4.8, 18.5): the FBS dates of recon/modes.json; _none/ on an FBD-only frame
        os.makedirs(os.path.join(fdir, d), exist_ok=True)
    fbs_arg = fdir
    if os.environ.get('LINOG_MOCK_G11_SLC') and C.selftest_hook('LINOG_MOCK_G11_SLC'):
        fbs_arg = 'SLC'   # M14: v0.12's call, every date under SLC/ an FBS date, which G11m must refuse on a mixed frame
    krc, out = P3.kit_run(env, KIT[0], ['--fbs-dir', fbs_arg], W, lg)
    mf = re.search(r'^igrams found: (\d+)', out, re.M)
    mm = re.search(r'^run_08_igram lines: (\d+)\s+(MATCH|\*\*\* MISMATCH)', out, re.M)
    mc = re.search(r'^MEAN COHERENCE ([\d.]+)\s+pairs > [\d.]+: (\d+)/(\d+)', out, re.M)
    ok = krc == 0 and mf and int(mf.group(1)) == len(pairs) and mm and mm.group(2) == 'MATCH' and mc and int(mc.group(3)) == len(pairs)
    st.gate('G11', 'coherence census (kit)', 'PASS' if ok else 'FAIL', 'mean coherence %s, pairs above 0.30: %s of %s; igrams %s, '
            'run_08 %s' % (mc.group(1) if mc else '?', mc.group(2) if mc else '?', mc.group(3) if mc else '?',
                           mf.group(1) if mf else '?', mm.group(2) if mm else '?'), 'rc 0; every pair read; MATCH',
            '' if ok else 'log %s\n%s' % (lg, P3.tail(lg)))
    st.rec['outputs']['g11'] = dict(rc=krc, log=lg, mean=float(mc.group(1)) if mc else None, above=int(mc.group(2)) if mc else None,
                                    fbs_dir=fdir, fbs_arg=fbs_arg)
    if not ok:
        return st.finish()
    # G11m (v0.13, 4.8): the census read recon/modes.json's FBS dates
    mn = re.search(r'FBS dates (\d+), from ', out)
    cls = dict((m.group(1), int(m.group(2))) for m in re.finditer(r'^(FBS|FBD|MIXED)\s+(\d+)\s', out, re.M))
    if fbs_m:
        okm = bool(mn) and int(mn.group(1)) == len(fbs_m)
        val = 'the census\'s FBS dates %s, recon/modes.json\'s %d; classes %s' % (mn.group(1) if mn else '?', len(fbs_m), cls)
    else:
        okm = bool(mn) and int(mn.group(1)) == 1 and cls.get('FBS', 0) == 0 and cls.get('MIXED', 0) == 0 and cls.get('FBD') == len(pairs)
        val = 'an FBD-only frame: the census\'s FBS dates %s (the _none/ placeholder); classes %s, every pair FBD-FBD %s' % (
            mn.group(1) if mn else '?', cls, okm)
    st.gate('G11m', 'the census\'s modes (4.8)', 'PASS' if okm else 'FAIL', val, 'FBS dates = recon/modes.json\'s FBS count (an '
            'FBD-only frame: 1 and every pair FBD)', '' if okm else 'log %s' % lg)
    st.rec['outputs']['g11'].update(fbs_census=int(mn.group(1)) if mn else None, fbs_modes=len(fbs_m), classes=cls)
    if not okm:
        return st.finish()
    lg = os.path.join(logroot, 'G11_date_coherence.log')
    krc, out = P3.kit_run(env, KIT[1], [], W, lg)
    rows = {m.group(1): dict(n=int(m.group(2)), mean=float(m.group(3)), min=float(m.group(4)), max=float(m.group(5)),
                             above=int(m.group(6)))
            for m in (re.match(r'^(\d{8})\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s*$', x) for x in out.splitlines()) if m}
    mark = float(r['COH_MARK'])
    dead = sorted(d for d, v in rows.items() if v['max'] < mark)
    dates = rf.get('outputs', {}).get('dates') or []
    bad = krc != 0 or sorted(rows) != sorted(dates)
    verdict = 'FAIL' if bad or ref in dead else ('WARN' if dead else 'PASS')
    worst = sorted(rows.items(), key=lambda kv: kv[1]['mean'])[:3]
    st.gate('G11d', 'per-date coherence (kit)', verdict, '%d dates; none without a pair above %s%s; lowest date means %s' % (
        len(rows), mark, '' if not dead else ' EXCEPT %s' % ', '.join(dead),
        ', '.join('%s %.3f' % (d, v['mean']) for d, v in worst)), 'every date has a pair above %s; the reference above all' % mark,
        ('rc %d; %d of %d dates read; log %s' % (krc, len(rows), len(dates), lg)) if bad else
        ('a date at the estimator floor on every pair is dead (an off-frame or bad acquisition); on the reference it is the '
         'datum bug\'s signature, or N25\'s (a reference held by one tie, misread: P448 F0280\'s 20091111, the ascending '
         'record 21.4)' if dead else ''))
    st.rec['outputs']['date_coh'] = dict(rc=krc, log=lg, rows=rows, dead=dead)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_igram', main)
