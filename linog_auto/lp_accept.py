#!/usr/bin/env python3
"""lp_accept.py -- linog_auto Phase 6b: the acceptance, the pipeline's copy of the kit's verifier on the frame (D6).

Runs inside lp_env.sh, after deliver: `python3 -B <pipeline>/linog_verify_frame_d6.py <frame>` from logs/p6/accept/
(the verifier imports isce, whose logging opens isce.log in the working folder: F50). The copy is the kit's
linog_verify_frame.py (7f2b53cf) with one change (D6, record 47.4 and 48.0): N22 takes each date's mode from
recon/modes.json, the pipeline's per-date table, and prints its source on a line of its own; on an FBS-only frame the
kit's own rule (the folders of raw_fbs_unpacked/) classes every secondary FBD and FAILs N22 (F39). v0.13 (the ascending
record 18.5, 18.6; LOGIC 2): on a frame whose datum record says method R9 the copy's N22 and G16 check dates/ against the
record's plan within 1e-6; elsewhere N22's range factor is spacing(the reference's mode) / spacing(the date's), 1 on an
FBD-only frame. v0.13 r2 (the part 6 review, the ascending record 26.1; LOGIC 3): the copy reads a NaN as off, R9's plan
with or without a pre-datum copy and only from a PASS datum record, names the record when it gives no plan and the dates
missing on either side, checks the plan against R9's arithmetic in the record (its line R9), names a date recon/modes.json
lacks, and names the reference by recon/reference.json before the kit's width heuristic (P6R-01 to 04, 08, 10, 14); the
datum record it reads, status/P4c_datum.json, is in this phase's fingerprint and in G6b.8's listing (P6R-13), and so is
lp_xmlwidth.py, the width helper the copy imports (25-b). The verifier only
reads: the structure, the datum, the interferograms, the template, the geocoded grid, the delivery (gdalinfo on each
GeoTIFF), the water mask (G22) and the swath-edge strips (G23). Each of its checks prints the value it measured.

Gates
  G6b.1  deliver PASS on record, its files as it recorded them                                         FAIL
  G6b.2  environment; MintPy at its pin (the env the verifier runs in)                          ERROR / FAIL
  G6b.3  the verifier copy as the package's MANIFEST.md5 lists it; G6b.3k the kit's verifier at its pin FAIL
  G6b.3c python3 and gdalinfo on the PATH resolve into the pinned env's bin                            FAIL
  G6b.4  the verifier ran whole: its summary line equals the lines it printed; rc 0 exactly when FAIL 0  FAIL
  G6b.5  N22's modes read from recon/modes.json, as many FBS dates as the table holds (D6)             FAIL
  G6b.6  the verifier's FAIL lines: none                                                               FAIL
  G6b.7  the verifier's WARN lines, each listed                                                 PASS / WARN
  G6b.8  the frame unchanged by the verifier (the delivery, the chains, the masks, MintPy's and prep's
         files, the datum's shelves, recon/modes.json, the frame's isce.log; v0.13 r2: the datum record)  FAIL
--state: STALE when deliver ran again since (its digest is in the fingerprint), when the delivery's files are no longer
as deliver recorded them, and (v0.13 r2) when the datum record the copy reads changed (its md5 is in the fingerprint).
--dryrun DIR: the verifier on the frame as it is, from DIR/logs/p6/accept/: a baseline, its
counts and N22's source INFO (the checks of phases not yet run FAIL there, and a frame before the datum prints no N22);
G6b.8 still holds the frame to be unchanged. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import collections
import json
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'accept', '6b', 3   # v0.13 (18.6): the verifier copy's N22 and G16 by R9's plan, the FBD-only factor;
# v0.13 r2 (the part 6 review): what the copy decides changes (P6R-01 to 04, 08, 10, 14) and the fingerprint holds the datum
# record and the width helper (P6R-13, 25-b)
KIT = ('linog_verify_frame.py',)
CMDS = ('python3', 'gdalinfo')
LINE = re.compile(r'^   (PASS|WARN|FAIL) (\S+) +(.*)$', re.M)          # Report.__call__: "   %-4s %-5s %s"
SUMMARY = re.compile(r'^ == (\S+) : PASS (\d+)  WARN (\d+)  FAIL (\d+) ==$', re.M)
FRAMES = re.compile(r'^FRAMES WITH FAILURES: (\d+) of (\d+)$', re.M)
N22SRC = re.compile(r'^        N22 modes from (.*)$', re.M)
MODES = re.compile(r'^recon/modes\.json \((\d+) FBS of (\d+) dates\)$')
DATUM_REC = 'status/P4c_datum.json'   # v0.13 r2 (P6R-13): the datum record the copy reads under R9
HELPER = 'lp_xmlwidth.py'            # v0.13 r2 (25-b): the width helper the copy imports (coreg_ref's fallback)
# what the verifier reads, listed before and after it runs (G6b.8)
READ = ('refineSecondaryTiming/dates', 'recon/modes.json', 'isce.log', 'geom_reference/*.rsc', 'Igrams/*/*.unw.rsc', DATUM_REC)


def modes_table(W):
    """(FBS dates, dates) in recon/modes.json, or None."""
    f = os.path.join(W, 'recon', 'modes.json')
    if not os.path.isfile(f):
        return None
    rows = json.load(open(f)).get('dates') or []
    return len([x for x in rows if x.get('mode') == 'FBS']), len(rows)


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 6b: the acceptance (the pipeline\'s verifier copy, D6)')
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
    tm = P6.tools(env, q, KIT)
    copy = os.path.join(P6.HERE, q['VERIFY_COPY'])
    rd = P1.record(recdir, '6a', 'deliver') or {}
    drec, helper = os.path.join(W, DATUM_REC), os.path.join(P6.HERE, HELPER)
    fp = C.md5_obj(dict(logic=LOGIC, deliver=rd.get('outputs', {}).get('digest'), copy=C.md5_file(copy) if os.path.isfile(copy) else None,
                        kit=tm[KIT[0]][1], datum_record=C.md5_file(drec) if os.path.isfile(drec) else None,
                        helper=C.md5_file(helper) if os.path.isfile(helper) else None))
    if a.state:
        sv = P6.state(recdir, W, PHASE, IDX, fp, P6.ACCEPT_OUTS)
        # CURRENT only while the delivery is as deliver recorded it (`--only accept` after a hand change: STALE)
        if sv == 'CURRENT' and P3.listing_changed(W, P6.deliver_outs(path, frame), rd.get('outputs', {}).get('files')):
            sv = 'STALE'
        print(sv)
        return 0

    st = P6.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(p6_cfg=q['p6_cfg_file'], p6_cfg_md5=q['p6_cfg_md5'], copy=copy,
                                                                   tools={KIT[0]: dict(path=tm[KIT[0]][0], md5=tm[KIT[0]][1])},
                                                                   datum_record=dict(path=drec, md5=C.md5_file(drec) if os.path.isfile(drec)
                                                                                     else None),
                                                                   helper=dict(path=helper, md5=C.md5_file(helper) if os.path.isfile(helper)
                                                                               else None)))
    P6.header(PHASE, IDX, path, frame, W, a.dryrun)
    rd, _ = P6.prior6(st, 'G6b.1', recdir, W, '6a', 'deliver', P6.deliver_outs(path, frame), bool(a.dryrun))
    if not rd:
        return st.finish()
    if not P5.env_gate(st, 'G6b.2', env, s, m):
        return st.finish()
    if not P6.copy_gate(st, 'G6b.3', q) or not P3.pins_gate(st, 'G6b.3k', tm, 'the kit\'s verifier (the copy\'s source)') \
            or not P6.which_gate(st, 'G6b.3c', s, CMDS, 'the verifier\'s commands on the PATH'):
        return st.finish()
    watch = P6.deliver_outs(path, frame) + P6.WMASK_OUTS + P5.OUTS['sbas'] + P5.OUTS['mcfg'] + READ
    before = P3.listing(W, watch)
    logd = os.path.join(recdir, 'logs', 'p6', 'accept')
    lg = P1.new_log(os.path.join(logd, 'linog_verify_frame_d6.log'))
    rc, out = P5.run_logged(['python3', '-B', copy, W], logd, lg)
    lines = LINE.findall(out)
    n = collections.Counter(v for v, _, _ in lines)
    sm, fw, src = SUMMARY.search(out), FRAMES.search(out), N22SRC.search(out)
    dry = bool(a.dryrun)
    bad = []
    if not sm:
        bad.append('no summary line')
    elif [int(sm.group(i)) for i in (2, 3, 4)] != [n['PASS'], n['WARN'], n['FAIL']]:
        bad.append('the summary reads PASS %s WARN %s FAIL %s, the lines %d, %d, %d' % (sm.group(2), sm.group(3), sm.group(4), n['PASS'],
                                                                                    n['WARN'], n['FAIL']))
    if not fw or fw.group(2) != '1' or fw.group(1) != ('1' if n['FAIL'] else '0'):
        bad.append('the last line %r' % (fw.group(0) if fw else None))
    if rc != (1 if n['FAIL'] else 0):
        bad.append('rc %d with %d FAIL lines' % (rc, n['FAIL']))
    st.gate('G6b.4', 'the verifier ran', 'FAIL' if bad else 'PASS', 'rc %d; %s: PASS %d  WARN %d  FAIL %d (%d lines)' % (
        rc, sm.group(1) if sm else os.path.basename(W), n['PASS'], n['WARN'], n['FAIL'], len(lines)),
        'the summary equals its lines; rc 0 exactly when FAIL 0', ('log %s\n' % lg) + '\n'.join(bad) + ('\n' + P3.tail(lg, 8) if bad else ''))
    st.rec['outputs'] = dict(log=lg, cwd=logd, rc=rc, counts=dict((k, n[k]) for k in ('PASS', 'WARN', 'FAIL')), lines=[list(x) for x in lines],
                             n22_source=src.group(1) if src else None,
                             copy=dict(path=copy, md5=C.md5_file(copy)), files=[], digest=P3.digest([]))
    if bad:
        return st.finish()
    mt = modes_table(W)
    mm = MODES.match(src.group(1)) if src else None
    ok = bool(mm) and mt is not None and (int(mm.group(1)), int(mm.group(2))) == mt
    st.gate('G6b.5', 'N22\'s modes (D6)', 'PASS' if ok else 'INFO' if dry else 'FAIL', 'N22 modes from %s; recon/modes.json holds %s' % (
        src.group(1) if src else 'no line', '%d FBS of %d dates' % mt if mt else 'nothing (absent)'),
        'recon/modes.json, the counts the table holds')
    fails = ['%s %s' % (t, x) for v, t, x in lines if v == 'FAIL']
    warns = ['%s %s' % (t, x) for v, t, x in lines if v == 'WARN']
    st.gate('G6b.6', 'the verifier\'s FAIL lines', 'INFO' if dry else 'FAIL' if fails else 'PASS', '%d%s' % (
        len(fails), ' (dry run: a baseline of the frame as it is)' if dry else ''), 'none', '\n'.join(fails))
    st.gate('G6b.7', 'the verifier\'s WARN lines', 'INFO' if dry else 'WARN' if warns else 'PASS', '%d' % len(warns), 'listed, not failed '
            '(the kit: WARN does not fail)', '\n'.join(warns))
    after = P3.listing(W, watch)
    ch = sorted(set(map(tuple, before)) ^ set(map(tuple, after)))
    st.gate('G6b.8', 'the frame unchanged by the verifier', 'FAIL' if ch else 'PASS', '%d files listed before and after%s' % (
        len(after), ': ' + '; '.join(x[0] for x in ch[:6]) if ch else ', the same'), 'the same (it only reads)')
    if dry:
        st.rec['outputs'].update(planned=True, dryrun=True)
        return st.finish('dry run: the verifier\'s baseline on the frame as it is: PASS %d  WARN %d  FAIL %d' % (n['PASS'], n['WARN'],
                                                                                                                  n['FAIL']))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_accept', main)
