#!/usr/bin/env python3
"""lp_stack1.py -- linog_auto Phase 2a: stack configuration, pass 1 (no reference given, as the 12 frames' stackcfg1),
in a folder of its own, and the kit's network table on it.

Runs inside lp_env.sh (stackStripMap reads each date's shelve: `frame` only, never an image). stackStripMap.py is
called by absolute path in the pinned env (F13), with this Python and -B. Pass 1 writes into <frame>/stack/pass1.vN/,
a new folder each run, so nothing is overwritten and the frame's configs/, run_files/ and baselines/ receive only
pass 2's files (F12: no orphans, no MintPy prefix tie). The kit's net table reads its dates from a phase1_dates.json,
which this phase writes into the pass folder from recon/modes.json (F11).
v0.13 (R6-d, ascending record 18.5): on an FBD-only frame the range looks are linog_mixed.cfg's STACK_RLKS_FBD (6) in place of
STACK_RLKS (12), under that key (lp_p2.fbd_only_looks); every other frame as v0.12.

Gates
  G2a.1 verify PASS on record; recon/modes.json as verify wrote it, verdict PASS                  FAIL
  G2a.2 environment: the pinned env, `import isce`                                                ERROR
  G2a.3 stack tools at their pins: stackStripMap.py and Stack.py in the env, the kit's net table   FAIL
  G2a.4 the frame's DEM: one *.wgs84 in DEM/ with its .vrt and .xml, every link resolving          FAIL
  G2a.5 stackStripMap pass 1 rc 0; a network that is not connected under -t and -b stops with
        DECISION (thresholds or dates are a human choice)                                          FAIL / DECISION
  G2a.6 its log: acquisitionDates = the stack's dates, the first date taken as stack reference,
        one bperp line per secondary, P pairs                                                      FAIL
  G2a.7 the pass folder: configs 2P + 4S + 2, 16 run files, run_08 P lines, S baseline files, each
        file's mean of top and bottom = its log line                                               FAIL
  G2a.8 the kit's net table on it: rc 0, MATCH, the same degree for every date                       FAIL
  G2a.9 thin nodes: dates of degree <= THIN_DEGREE (F15), carried to the later exclusion steps    WARN
--dryrun DIR: when the frame's verify is PASS on record with its modes.json, pass 1 runs into DIR/stack/pass1.vN
(the frame is only read); otherwise the plan. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import json
import os
import subprocess
import sys

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2

TOOLS = ('lp_stack1.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py')
LOGIC = 1   # raised when what this phase writes or decides changes; the lp_*.py md5s are recorded, not fingerprinted


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 2a: stack configuration pass 1')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s = P1.load_env(), P2.load_stack()
    tm = P2.tool_md5s(s, env)
    dem, dem_bad = P2.frame_dem(W)
    r_ver = P1.record(W, '1c', 'verify')
    rows, m_md5, m_verdict = P2.modes_rows(W)
    looks_note = P2.fbd_only_looks(s, rows, recdir)   # v0.13, R6-d (18.5): an FBD-only frame's range looks
    real = bool(r_ver and r_ver.get('verdict') == 'PASS' and m_md5 and
                r_ver.get('outputs', {}).get('modes_json_md5') == m_md5)
    # what pass 1 reads (the shelves and modes.json's rows), its settings, the stack tools and the DEM
    fp = C.md5_obj(dict(logic=LOGIC, modes=P2.modes_digest(rows), shelves=P2.slc_identity(W, sorted(rows), shelve_only=True),
                        settings=P2.settings_of(s, P2.STACK1_KEYS), stack_tools={k: v[1] for k, v in tm.items()},
                        dem=P2.dem_identity(dem)))
    if a.state:
        def missing(r):
            o = (r or {}).get('outputs', {})
            r8 = os.path.join(o.get('pass_dir') or '/nonexistent', 'run_files', 'run_08_igram')
            return [] if os.path.isfile(r8) and C.md5_file(r8) == o.get('run08_md5') else [r8]
        print(P1.state_with_outputs(recdir, 'stack1', '2a', fp, missing))
        return 0

    st = P2.LiveStatus(recdir, 'stack1', '2a', path, frame)
    P1.begin(st)
    st.rec['version'] = P2.VERSION2
    st.rec.update(fingerprint=fp, logic=LOGIC, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(modes_json_md5=m_md5, stack_cfg=s['stack_cfg_file'], stack_cfg_md5=s['stack_cfg_md5'],
                              env_cfg=env['env_cfg_file'], env_cfg_md5=env['env_cfg_md5'],
                              stack_tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}, dem=dem, looks=looks_note))
    st.write()
    print('%s  Phase 2a stack1  p%s f%s  %s' % (P2.VERSION2, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: pass 1 into the dry folder; the frame is only read)' if a.dryrun else ''))

    if a.dryrun and not real:
        r_dv = P1.record(recdir, '1c', 'verify')
        ok = bool(r_dv and r_dv.get('verdict') == 'PASS')
        st.gate('G2a.1', 'verify PASS on record', 'PASS' if ok else 'FAIL', 'dry-run verify record %s; the frame has no '
                'verify PASS with modes.json yet' % ((r_dv or {}).get('verdict') or 'absent'))
        if not ok:
            return st.finish()
        if not P2.env_gate(st, 'G2a.2', env, s):
            return st.finish()
        P2.tools_gate(st, 'G2a.3', tm)
        st.gate('G2a.4', 'the frame DEM', 'FAIL' if dem_bad else 'PASS', dem or '-', 'one *.wgs84 + .vrt + .xml', '\n'.join(dem_bad))
        if any(x['verdict'] == 'FAIL' for x in st.rec['gates']):
            return st.finish()
        print('   would run stackStripMap.py %s -w %s/stack/pass1.vN, then the kit net table, once verify has written modes.json'
              % (' '.join(P2.stack_args(s, W, dem, '')[:-2]), recdir))
        st.rec['outputs'] = dict(planned=True, dryrun=True)
        return st.finish('plan only (dry run)')

    why = []
    if not r_ver or r_ver.get('verdict') != 'PASS':
        why.append('verify %s' % ((r_ver or {}).get('verdict') or 'has no record'))
    elif not m_md5:
        why.append('no recon/modes.json')
    elif r_ver.get('outputs', {}).get('modes_json_md5') != m_md5:
        why.append('recon/modes.json changed since verify wrote it')
    elif m_verdict != 'PASS':
        why.append('modes.json verdict %s' % m_verdict)
    if why:
        st.gate('G2a.1', 'verify PASS on record', 'FAIL', '; '.join(why))
        return st.finish()
    dates = sorted(rows)
    S = len(dates) - 1
    st.gate('G2a.1', 'verify PASS on record', 'PASS', '%d dates in modes.json (%s..%s), verdict PASS' % (
        len(dates), dates[0], dates[-1]))
    if not P2.env_gate(st, 'G2a.2', env, s):
        return st.finish()
    P2.tools_gate(st, 'G2a.3', tm)
    st.gate('G2a.4', 'the frame DEM', 'FAIL' if dem_bad else 'PASS', '%s -> %s' % (dem, os.path.realpath(dem)) if dem else '-',
            'one *.wgs84 + .vrt + .xml, resolving', '\n'.join(dem_bad))
    if any(x['verdict'] == 'FAIL' for x in st.rec['gates']):
        return st.finish()

    wd = P2.new_dir(os.path.join(recdir, 'stack', 'pass1'))
    args = P2.stack_args(s, W, dem, wd)
    lg = P1.new_log(os.path.join(recdir, 'logs', 'stack', 'stackcfg1.log'))
    print('   pass 1 in %s: stackStripMap.py %s' % (wd, ' '.join(args)))
    rc, secs = P2.run_stackstripmap(s, args, wd, lg, os.path.join(recdir, 'logs', 'stack', 'mplconfig'))
    L = P2.parse_log(lg)
    st.rec['outputs'] = dict(pass_dir=wd, log=lg, rc=rc, seconds=round(secs, 1))
    if rc != 0:
        if L['not_connected']:
            st.gate('G2a.5', 'stackStripMap pass 1', 'DECISION', 'rc %d: the network under -t %s -b %s is not connected' % (
                rc, s['STACK_T_DAYS'], s['STACK_B_M']), 'rc 0', 'the per-date baselines are in %s; wider thresholds in %s '
                'or dates excluded in recon/exclude.txt are a human choice\n%s' % (lg, s['stack_cfg_file'], L['tail']))
        else:
            st.gate('G2a.5', 'stackStripMap pass 1', 'FAIL', 'rc %d after %.1f s' % (rc, secs), 'rc 0', 'log %s\n%s' % (lg, L['tail']))
        return st.finish()
    st.gate('G2a.5', 'stackStripMap pass 1', 'PASS', 'rc 0 in %.1f s; log %s' % (secs, lg), 'rc 0')

    P = L['pairs'] or 0
    bad = []
    if L['acq'] != dates:
        bad.append('acquisitionDates %s, want the %d dates of modes.json' % (L['acq'], len(dates)))
    if not L['notfound']:
        bad.append('no "reference date was not found" line: pass 1 must take the first date')
    if sorted(L['bp']) != dates[1:]:
        bad.append('%d bperp lines, want one per secondary (%d)' % (len(L['bp']), S))
    if not P:
        bad.append('number of pairs %s' % L['pairs'])
    st.gate('G2a.6', 'pass 1 log', 'FAIL' if bad else 'PASS', '%d dates, stack reference %s, %d bperp lines, %d pairs' % (
        len(L['acq'] or []), dates[0], len(L['bp']), P), 'dates as modes.json; S lines; P > 0', '\n'.join(bad))
    if bad:
        return st.finish()

    R = P2.read_pass(wd)
    bp = dict(L['bp'], **{dates[0]: 0.0})
    want = P2.want_runs(S, P)
    bad = []
    if R['configs'] != 2 * P + 4 * S + 2:
        bad.append('configs %d, want 2P + 4S + 2 = %d' % (R['configs'], 2 * P + 4 * S + 2))
    if R['run_files'] != 16:
        bad.append('run_files %d, want 16 (8 run files + 8 .job)' % R['run_files'])
    if R['runs'] != want:
        bad.append('run-file lines %s, want %s' % (R['runs'], want))
    if len(R['pairs']) != P:
        bad.append('run_08_igram holds %d pairs, the log %d' % (len(R['pairs']), P))
    blog = {'%s_%s.txt' % (dates[0], d): v for d, v in L['bp'].items()}
    if sorted(R['baselines']) != sorted(blog):
        bad.append('baseline files %s, want %s' % (sorted(R['baselines'])[:3], sorted(blog)[:3]))
    agree = sum(1 for n, v in R['baselines'].items() if v is not None and n in blog and abs(v - blog[n]) <= 1e-6)
    if agree != S:
        bad.append('%d of %d baseline files agree with their log lines' % (agree, S))
    st.gate('G2a.7', 'pass 1 folder', 'FAIL' if bad else 'PASS', 'configs %d, run_files %d, run_08 %d lines, %d baselines (%d agree), pairs.pdf %s B' % (
        R['configs'], R['run_files'], R['runs'].get('run_08_igram') or 0, len(R['baselines']), agree, R['pdf']),
        '2P+4S+2 = %d, 16, P = %d, S = %d' % (2 * P + 4 * S + 2, P, S), '\n'.join(bad))
    if bad:
        return st.finish()

    p1 = os.path.join(wd, 'phase1_dates.json')
    P2.write_json(p1, [dict(date=d, mode=rows[d]['mode'], px=rows[d]['width']) for d in dates])
    nt = os.path.join(wd, 'net_table.txt')
    with open(nt, 'w') as fh:
        rcn = subprocess.call([sys.executable, '-B', tm['linog_net_table.py'][0], '--log', lg, '--pairs',
                               os.path.join(wd, 'run_files', 'run_08_igram'), '--dates', p1], cwd=wd, stdout=fh,
                              stderr=subprocess.STDOUT)
    ntxt = open(nt, errors='replace').read()
    deg, mx = P2.network(dates, bp, [tuple(x) for x in R['pairs']])
    kit = {}
    for ln in ntxt.splitlines():
        f = ln.split()
        if len(f) >= 4 and len(f[0]) == 8 and f[0].isdigit() and f[3].isdigit():
            kit[f[0]] = int(f[3])
    match = 'pairs parsed=%d   run_08_igram lines=%d   MATCH' % (P, P) in ntxt
    ok = rcn == 0 and match and kit == deg
    for ln in ntxt.rstrip().splitlines():
        print('      ' + ln)
    st.gate('G2a.8', 'the kit net table', 'PASS' if ok else 'FAIL', 'rc %d, %s, degrees agree on %d of %d dates' % (
        rcn, 'MATCH %d' % P if match else 'no MATCH line', sum(1 for d in dates if kit.get(d) == deg[d]), len(dates)),
        'rc 0, MATCH, all', 'output %s' % nt)
    if not ok:
        return st.finish()
    thin = sorted(d for d in dates if deg[d] <= int(s['THIN_DEGREE']))
    st.gate('G2a.9', 'thin nodes', 'WARN' if thin else 'PASS', ', '.join('%s degree %d' % (d, deg[d]) for d in thin) or 'none',
            'degree <= %s' % s['THIN_DEGREE'], 'a later step that drops a pair of these dates re-checks the network (F15)' if thin else '')
    st.rec['outputs'].update(dates=dates, secondaries=S, pairs=P, pair_list=R['pairs'], pairs_md5=C.md5_obj(R['pairs']),
                             run08_md5=R['run08_md5'], configs=R['configs'], run_files=R['run_files'], runs=R['runs'],
                             bperp={d: round(v, 4) for d, v in bp.items()}, degree=deg, maxbp=mx, min_degree=min(deg.values()),
                             max_degree=max(deg.values()), thin=thin, net_table=nt, phase1_dates=p1, pairs_pdf=R['pdf'])
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_stack1', main)
