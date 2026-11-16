#!/usr/bin/env python3
"""lp_stack2.py -- linog_auto Phase 2c: stack configuration, pass 2 with the reference (the 12 frames' stackcfg2):
a trial in a folder of its own, checked; then the same command in the frame, checked against the trial; then the
water-mask strip (record 7.2) with its .bak_watermask copy.

Runs inside lp_env.sh. stackStripMap.py by absolute path (F13). The trial runs into <frame>/stack/pass2.vN/ (a new
folder each run), so a network or a layout that fails a gate never reaches the frame's configs/. The frame run is the
kit frames' command, from the frame folder with -w <frame>: configs/, run_files/, baselines/ and pairs.pdf there, and
ISCE appends to isce.log (F16). Pass 2 computes the baselines against the reference and pass 1 against the first date,
so a pair within PAIR_FLIP_M of -b can be in one pass's network and not the other's (RD3: the two passes' |dB| differ
by up to 0.343 m on P084 F3320): such pairs are listed with WARN and pass 2's network is the stack's; any other
difference FAILs. Then config_reference_<REF> is copied to config_reference_<REF>.bak_watermask and rewritten with its
first 14 lines, [Function-2] createWaterMask removed, as on the 12 frames (Function-2 reads geom_reference/lat.rdr,
Rule 4's other tree).
v0.13 (R6-d, ascending record 18.5): on an FBD-only frame the range looks are linog_mixed.cfg's STACK_RLKS_FBD (6) in place of
STACK_RLKS (12), under that key, so the stack call and G2c.9's check of the run file take them (lp_p2.fbd_only_looks).

Gates
  G2c.1  reference PASS on record; recon/reference.json as it wrote it; pass 1's folder unchanged    FAIL
  G2c.2  environment                                                                              ERROR
  G2c.3  stack tools at their pins                                                                FAIL
  G2c.4  the frame's DEM, as stack1 found it                                                      FAIL
  G2c.5  nothing in the way: configs/, run_files/, baselines/, pairs.pdf absent in the frame        DECISION
  G2c.6  the trial: stackStripMap -m <REF> into stack/pass2.vN, rc 0 (a network that is not
         connected: DECISION, as in stack1)                                                        FAIL / DECISION
  G2c.7  its network: the stack's dates, <REF> taken (no "not found" line), one bperp line per
         secondary; the pairs of pass 1, or differing only within PAIR_FLIP_M of -b                 FAIL / WARN
  G2c.8  its folder: configs 2P + 4S + 2, 16 run files (lines 1, S, S, P, 1, S+1, S+1, P), S baselines
         named <REF>_*, every config_fineResamp naming SLC/<REF>, run_01 naming config_reference_<REF>  FAIL
  G2c.9  its config_reference_<REF>: 21 lines, [Function-1] at line 4 (topo: reference SLC/<REF>, the
         DEM, output merged/geom_reference, alks, rlks), [Function-2] createWaterMask at line 15    FAIL
  G2c.10 the frame run: rc 0, and the frame's files are the trial's with the folder name changed       FAIL
  G2c.11 the strip: .bak_watermask = the original 21 lines; config_reference_<REF> = its first 14    FAIL
Writes in the frame: stack/pass2.vN/ (the trial), configs/, run_files/, baselines/, pairs.pdf, isce.log (appended), the
.bak_watermask copy, logs/stack/; its status record. Nothing is moved or deleted. The record lists every file of the
configuration with its size and md5: a later phase may add files beside them (Phase 3's logs), but a listed file that
changes or goes makes the record STALE.
--dryrun DIR: the trial into DIR/stack/pass2.vN, G2c.6 to G2c.9, and the strip on the trial's copy; the frame is only
read. Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import collections
import json
import os
import re
import shutil

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2

TOOLS = ('lp_stack2.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py')
LOGIC = 1   # raised when what this phase writes or decides changes; the lp_*.py md5s are recorded, not fingerprinted
OUTS = ('configs', 'run_files', 'baselines', 'pairs.pdf')


def names(wd):
    """The files of configs/, run_files/, baselines/ and pairs.pdf under wd, relative to wd."""
    out = []
    for n in OUTS:
        p = os.path.join(wd, n)
        if os.path.isfile(p):
            out.append(n)
        elif os.path.isdir(p):
            out += ['%s/%s' % (n, f) for f in sorted(os.listdir(p)) if os.path.isfile(os.path.join(p, f))]
    return out


def manifest(wd):
    """[[name, size, md5]] of those files."""
    return [[n, os.path.getsize(os.path.join(wd, n)), C.md5_file(os.path.join(wd, n))] for n in names(wd)]


def changed(wd, files):
    """The files of a manifest that are gone or differ now."""
    out = []
    for n, size, m in files or []:
        p = os.path.join(wd, n)
        if not os.path.isfile(p) or os.path.getsize(p) != size or C.md5_file(p) != m:
            out.append(p)
    return out


def same_as_trial(trial, W):
    """What differs between the frame's configuration and the trial's with the trial's folder name replaced by the
    frame's (pairs.pdf: present in both; its bytes hold a time stamp)."""
    a, b = names(trial), names(W)
    bad = ['only in the trial: %s' % n for n in a if n not in b] + ['only in the frame: %s' % n for n in b if n not in a]
    for n in a:
        if n in b and n != 'pairs.pdf':
            x = open(os.path.join(trial, n), 'rb').read().replace(trial.encode(), W.encode())
            if x != open(os.path.join(W, n), 'rb').read():
                bad.append('differs: %s' % n)
    return bad


def network_diff(p1, p2, bp1, bp2, bmax, flip):
    """The pairs in one pass's network and not the other's, with |dB| in each pass and whether it is at the -b limit
    (within flip of bmax in either pass)."""
    s1, s2 = set(map(tuple, p1)), set(map(tuple, p2))
    out = []
    for x, y in sorted(s1 ^ s2):
        d1 = abs(bp1[x] - bp1[y]) if x in bp1 and y in bp1 else None
        d2 = abs(bp2[x] - bp2[y]) if x in bp2 and y in bp2 else None
        out.append(dict(pair='%s_%s' % (x, y), only_in='pass 1' if (x, y) in s1 else 'pass 2', db1=d1, db2=d2,
                        at_limit=any(v is not None and abs(v - bmax) <= flip for v in (d1, d2))))
    return out


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 2c: stack configuration pass 2')
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
    looks_note = P2.fbd_only_looks(s, P2.modes_rows(W)[0], recdir)   # v0.13, R6-d (18.5): an FBD-only frame's range looks
    tm = P2.tool_md5s(s, env)
    rr = P1.record(recdir, '2b', 'reference')
    r1 = P1.record(recdir, '2a', 'stack1')
    o1, orr = (r1 or {}).get('outputs', {}), (rr or {}).get('outputs', {})
    rj = os.path.join(recdir, 'recon', 'reference.json')
    rj_md5 = C.md5_file(rj) if os.path.exists(rj) else None
    try:
        ref_now = json.load(open(rj)).get('reference') if rj_md5 else None
    except ValueError:
        ref_now = None
    # the reference date, pass 1's network, the shelves, the settings, the two stack tools and the DEM decide pass 2;
    # not the reference record itself: a reference phase that runs again and names the same date leaves pass 2 CURRENT
    fp = C.md5_obj(dict(logic=LOGIC, reference=ref_now, dates=o1.get('dates'), pairs_md5=o1.get('pairs_md5'),
                        shelves=P2.slc_identity(W, o1.get('dates') or [], shelve_only=True),
                        settings=P2.settings_of(s, P2.STACK2_KEYS),
                        stack_tools={k: v[1] for k, v in tm.items() if k != 'linog_net_table.py'},
                        dem=P2.dem_identity(P2.frame_dem(W)[0])))
    if a.state:
        def missing(r):
            o = (r or {}).get('outputs', {})
            wd = o.get('workdir') or W
            return changed(wd, o['files']) if o.get('files') else [os.path.join(wd, 'configs')]
        print(P1.state_with_outputs(recdir, 'stack2', '2c', fp, missing))
        return 0

    st = P2.LiveStatus(recdir, 'stack2', '2c', path, frame)
    P1.begin(st)
    st.rec['version'] = P2.VERSION2
    st.rec.update(fingerprint=fp, logic=LOGIC, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(reference_json=rj, reference_json_md5=rj_md5, stack_cfg=s['stack_cfg_file'],
                              stack_cfg_md5=s['stack_cfg_md5'], settings=P2.settings_of(s, P2.STACK2_KEYS),
                              stack_tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}, looks=looks_note))
    st.write()
    print('%s  Phase 2c stack2  p%s f%s  %s' % (P2.VERSION2, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: pass 2 into the dry folder; the frame is only read)' if a.dryrun else ''))
    why = []
    if not rr or rr.get('verdict') != 'PASS':
        why.append('reference %s' % ((rr or {}).get('verdict') or 'has no record'))
    elif a.dryrun and orr.get('planned'):
        st.gate('G2c.1', 'reference PASS on record', 'PASS', 'dry-run reference was a plan only')
        print('   would run stackStripMap.py pass 2 with -m <reference>, a trial and then in %s, then the water-mask strip' % W)
        st.rec['outputs'] = dict(planned=True, dryrun=True)
        return st.finish('plan only (dry run)')
    elif not rj_md5 or orr.get('reference_json_md5') != rj_md5:
        why.append('recon/reference.json changed since reference wrote it, or absent')
    else:
        r8 = os.path.join(o1.get('pass_dir') or '/nonexistent', 'run_files', 'run_08_igram')
        if not (os.path.isfile(r8) and C.md5_file(r8) == o1.get('run08_md5')):
            why.append('pass 1 folder %s changed or gone' % o1.get('pass_dir'))
    if why:
        st.gate('G2c.1', 'reference PASS on record', 'FAIL', '; '.join(why))
        return st.finish()
    J = json.load(open(rj))
    REF = J['reference']
    dates, P1n = o1['dates'], o1['pairs']
    S = len(dates) - 1
    st.gate('G2c.1', 'reference PASS on record', 'PASS', 'reference %s (%s); pass 1: %d dates, %d pairs' % (
        REF, J['decided_by'], len(dates), P1n))
    if not P2.env_gate(st, 'G2c.2', env, s):
        return st.finish()
    if not P2.tools_gate(st, 'G2c.3', tm):
        return st.finish()
    dem, dem_bad = P2.frame_dem(W)
    st.gate('G2c.4', 'the frame DEM', 'FAIL' if dem_bad else 'PASS', '; '.join(dem_bad) or dem, 'one *.wgs84 + .vrt + .xml')
    if dem_bad:
        return st.finish()
    if a.dryrun:
        st.gate('G2c.5', 'nothing in the way', 'PASS', 'dry run: the frame is only read', 'configs/, run_files/, baselines/, pairs.pdf absent')
    else:
        way = [n for n in OUTS if os.path.lexists(os.path.join(W, n))]
        if way:
            st.gate('G2c.5', 'nothing in the way', 'DECISION', 'in the frame already: %s' % ', '.join(way),
                    'configs/, run_files/, baselines/, pairs.pdf absent',
                    'an earlier stack configuration; move them into %s/_archive/ (not a folder inside configs/) and run again'
                    % W)
            return st.finish()
        st.gate('G2c.5', 'nothing in the way', 'PASS', 'configs/, run_files/, baselines/, pairs.pdf absent', 'all absent')

    # the trial
    mpl = os.path.join(recdir, 'logs', 'stack', 'mplconfig')
    trial = P2.new_dir(os.path.join(recdir, 'stack', 'pass2'))
    args = P2.stack_args(s, W, dem, trial, ref=REF)
    lg = P1.new_log(os.path.join(recdir, 'logs', 'stack', 'stackcfg2_trial.log'))
    print('   pass 2, trial in %s: stackStripMap.py %s' % (trial, ' '.join(args)))
    rc, secs = P2.run_stackstripmap(s, args, trial, lg, mpl)
    L = P2.parse_log(lg)
    st.rec['outputs'] = dict(trial_dir=trial, trial_log=lg, reference=REF, rc=rc, seconds=round(secs, 1))
    if rc != 0:
        if L['not_connected']:
            st.gate('G2c.6', 'stackStripMap pass 2 (trial)', 'DECISION', 'rc %d: with -m %s the network under -t %s -b %s is not '
                    'connected' % (rc, REF, s['STACK_T_DAYS'], s['STACK_B_M']), 'rc 0', 'wider thresholds in %s or dates '
                    'excluded in recon/exclude.txt are a human choice\n%s' % (s['stack_cfg_file'], L['tail']))
        else:
            st.gate('G2c.6', 'stackStripMap pass 2 (trial)', 'FAIL', 'rc %d after %.1f s' % (rc, secs), 'rc 0', 'log %s\n%s' % (lg, L['tail']))
        return st.finish()
    st.gate('G2c.6', 'stackStripMap pass 2 (trial)', 'PASS', 'rc 0 in %.1f s; log %s' % (secs, lg), 'rc 0')

    R = P2.read_pass(trial)
    bp2 = dict(L['bp'], **{REF: 0.0})
    bad = []
    if L['acq'] != dates:
        bad.append('acquisitionDates %s, want pass 1\'s %d dates' % (L['acq'], len(dates)))
    if L['notfound']:
        bad.append('"reference date was not found": stackStripMap did not take %s' % REF)
    if sorted(L['bp']) != sorted(d for d in dates if d != REF):
        bad.append('%d bperp lines, want one per secondary of %s' % (len(L['bp']), REF))
    if L['pairs'] != len(R['pairs']):
        bad.append('the log says %s pairs, run_08_igram holds %d' % (L['pairs'], len(R['pairs'])))
    diff = network_diff(o1['pair_list'], R['pairs'], o1['bperp'], bp2, float(s['STACK_B_M']), float(s['PAIR_FLIP_M'])) \
        if not bad else []
    far = [d for d in diff if not d['at_limit']]
    if far:
        bad.append('pairs in one pass only, away from the -b limit: %d' % len(far))
    P = len(R['pairs'])
    lines = ['%s in %s only: |dB| %s m in pass 1, %s m in pass 2 (-b %s, PAIR_FLIP_M %s)' % (
        d['pair'], d['only_in'], '%.2f' % d['db1'] if d['db1'] is not None else '?', '%.2f' % d['db2'] if d['db2'] is not None else '?',
        s['STACK_B_M'], s['PAIR_FLIP_M']) for d in diff]
    if diff and not bad:
        deg1 = collections.Counter(x for p in o1['pair_list'] for x in p)
        deg2 = collections.Counter(x for p in R['pairs'] for x in p)
        lines.append('degrees in pass 2: ' + ', '.join('%s %d (pass 1 %d)' % (d, deg2[d], deg1[d]) for d in dates if deg2[d] != deg1[d]))
    st.gate('G2c.7', 'pass 2\'s network', 'FAIL' if bad else ('WARN' if diff else 'PASS'),
            '%d dates, reference %s, %d bperp lines, %d pairs (pass 1: %d); %s' % (
                len(L['acq'] or []), REF, len(L['bp']), P, P1n, 'the list of pass 1' if not diff else
                'pairs in one pass only: %d, at the -b limit: %d' % (len(diff), len(diff) - len(far))),
            'the dates and pairs of pass 1; a pair at the -b limit may differ', '\n'.join(bad + lines))
    if bad:
        return st.finish()

    want = P2.want_runs(S, P)
    cf = os.path.join(trial, 'configs')
    fr = sorted(n for n in os.listdir(cf) if n.startswith('config_fineResamp_'))
    frref = {}
    for n in fr:
        m = re.search(r'^reference\s*:\s*(\S+)\s*$', open(os.path.join(cf, n)).read(), re.M)
        frref[n] = m.group(1) if m else None
    want_ref = os.path.join(W, 'SLC', REF)
    r1f = os.path.join(trial, 'run_files', 'run_01_reference')
    r1l = open(r1f).read().strip() if os.path.isfile(r1f) else None
    bad = []
    if R['configs'] != 2 * P + 4 * S + 2:
        bad.append('configs %d, want 2P + 4S + 2 = %d' % (R['configs'], 2 * P + 4 * S + 2))
    if R['run_files'] != 16 or R['runs'] != want:
        bad.append('run_files %d, lines %s; want 16, %s' % (R['run_files'], R['runs'], want))
    bnames = sorted(R['baselines'])
    if len(bnames) != S or any(not n.startswith(REF + '_') for n in bnames):
        bad.append('%d baseline files, %d named %s_*' % (len(bnames), sum(n.startswith(REF + '_') for n in bnames), REF))
    if len(fr) != S or any(v != want_ref for v in frref.values()):
        bad.append('%d config_fineResamp files; references %s' % (len(fr), sorted(set(map(str, frref.values())))))
    if r1l != 'stripmapWrapper.py -c %s' % os.path.join(cf, 'config_reference_%s' % REF):
        bad.append('run_01_reference reads %r' % r1l)
    st.gate('G2c.8', 'pass 2 folder (trial)', 'FAIL' if bad else 'PASS', 'configs %d, run_files %d, %d baselines %s_*, %d fineResamp naming SLC/%s' % (
        R['configs'], R['run_files'], len(bnames), REF, len(fr), REF), '2P+4S+2 = %d; 16; S = %d' % (2 * P + 4 * S + 2, S), '\n'.join(bad))
    if bad:
        return st.finish()

    def layout(wd):
        cr = os.path.join(wd, 'configs', 'config_reference_%s' % REF)
        ls = open(cr).read().splitlines()
        kv = dict((m.group(1), m.group(2)) for m in (re.match(r'^(\w+)\s*:\s*(.*?)\s*$', x) for x in ls[:14]) if m)
        f1 = [i + 1 for i, x in enumerate(ls) if x.strip() == '[Function-1]']
        f2 = [i + 1 for i, x in enumerate(ls) if x.strip() == '[Function-2]']
        wantkv = dict(reference=want_ref, dem=dem, output=os.path.join(wd, 'merged', 'geom_reference'), alks=s['STACK_ALKS'],
                      rlks=s['STACK_RLKS'])
        b = []
        if len(ls) != 21 or f1 != [4] or f2 != [15] or 'topo' not in kv or ls[15].split(':')[0].strip() != 'createWaterMask':
            b.append('%d lines, [Function-1] at %s, [Function-2] at %s, line 16 %r' % (len(ls), f1, f2, ls[15] if len(ls) > 15 else None))
        for k, v in wantkv.items():
            if kv.get(k) != v:
                b.append('%s : %s, want %s' % (k, kv.get(k), v))
        return cr, ls, kv, f1, f2, b

    cr, lines, kv, f1, f2, bad = layout(trial)
    st.gate('G2c.9', 'config_reference_%s (trial)' % REF, 'FAIL' if bad else 'PASS', '%d lines, [Function-1] line %s, '
            '[Function-2] line %s (createWaterMask); reference, dem, output, alks %s, rlks %s as expected' % (
                len(lines), ','.join(map(str, f1)) or 'none', ','.join(map(str, f2)) or 'none', kv.get('alks'), kv.get('rlks')),
            '21 lines; topo at 4, createWaterMask at 15', '\n'.join(bad))
    if bad:
        return st.finish()

    if a.dryrun:
        wd = trial
        st.gate('G2c.10', 'the frame run', 'N/A', 'dry run: the trial is the pass; the frame is only read')
    else:
        wd = W
        lg2 = P1.new_log(os.path.join(recdir, 'logs', 'stack', 'stackcfg2.log'))
        args = P2.stack_args(s, W, dem, W, ref=REF)
        print('   pass 2 in the frame %s: stackStripMap.py %s' % (W, ' '.join(args)))
        rc, secs = P2.run_stackstripmap(s, args, W, lg2, mpl)
        st.rec['outputs'].update(frame_log=lg2, frame_rc=rc, frame_seconds=round(secs, 1))
        bad = ['rc %d; log %s\n%s' % (rc, lg2, P2.parse_log(lg2)['tail'])] if rc != 0 else same_as_trial(trial, W)
        st.gate('G2c.10', 'the frame run', 'FAIL' if bad else 'PASS', 'rc %d in %.1f s; %d files%s' % (
            rc, secs, len(names(W)), ', the trial\'s with the folder name changed' if not bad else ''),
            'rc 0; the trial\'s files', '\n'.join(bad[:30]) + ('\n... %d more' % (len(bad) - 30) if len(bad) > 30 else ''))
        if bad:
            return st.finish()
        cr, lines, kv, f1, f2, bad = layout(W)
        if bad:   # the same file as the trial's, name changed: cannot differ once G2c.10 passed
            st.gate('G2c.11', 'the water-mask strip', 'FAIL', 'config_reference_%s in the frame' % REF, '21 lines', '\n'.join(bad))
            return st.finish()

    bak = cr + '.bak_watermask'
    m_orig = C.md5_file(cr)
    shutil.copy2(cr, bak)
    tmp = cr + '.tmp%d' % os.getpid()
    with open(tmp, 'w') as fh:
        fh.write('\n'.join(lines[:14]) + '\n')
    os.replace(tmp, cr)
    new = open(cr).read().splitlines()
    ok = C.md5_file(bak) == m_orig and new == lines[:14] and '[Function-2]' not in open(cr).read() and new[-1].startswith('####')
    st.gate('G2c.11', 'the water-mask strip', 'PASS' if ok else 'FAIL', '%d of %d lines kept in %s; .bak_watermask md5 %s = the original' % (
        len(new), len(lines), cr, C.md5_file(bak)), '14 of 21; the backup unchanged', '' if ok else 'strip did not verify')
    st.rec['outputs'].update(workdir=wd, dates=len(dates), pairs=P, pairs_pass1=P1n, pairs_md5=C.md5_obj(R['pairs']),
                             network_diff=diff, configs=R['configs'], run_files=R['run_files'], runs=R['runs'],
                             baselines=bnames, config_reference=cr, config_reference_md5=C.md5_file(cr), bak_watermask=bak,
                             bak_watermask_md5=C.md5_file(bak), files=manifest(wd))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_stack2', main)
