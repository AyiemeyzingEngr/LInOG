#!/usr/bin/env python3
"""lp_prep.py -- linog_auto Phase 5b: MintPy's prep_isce.py, the metadata files load_data reads (G12).

Runs inside lp_env.sh, from the frame folder (Phase 5 has two working folders: prep_isce the frame, MintPy mintpy/),
with the kit's arguments (linog_frame.sh ph_prep) and the metadata file named with its .dat (F40: `data` without it
matches no file, and load_data then only warns and goes on with stale or no .rsc):
  prep_isce.py -m <frame>/SLC/<REF>/data.dat -g <frame>/geom_reference -b <frame>/baselines
               -f "<frame>/Igrams/*/filt_*.unw" --geom-files hgt.rdr lat.rdr lon.rdr los.rdr shadowMask.rdr incLocal.rdr
It writes a .rsc beside each unwrapped interferogram and each of the six geometry files, and SLC/<REF>/data.rsc
(STARTING_RANGE, which load_data needs, G12; POLARIZATION, a free cross-check of verify's HH, G4; HEADING).

Gates
  G5b.1  admit PASS on record; igram PASS, Igrams as igram recorded it                               FAIL
  G5b.2  environment; MintPy at its pin                                                  ERROR / FAIL
  G5b.3  prep_isce.py on the PATH is the pinned env's                                                FAIL
  G5b.4  the metadata file SLC/<REF>/data.dat, with data.dir and data.bak (the reference's shelve)   FAIL
  G5b.5  nothing in the way: no .unw.rsc, no geom_reference .rsc, no SLC/*/data.rsc                   DECISION
  G5b.6  prep_isce.py: rc 0                                                                           FAIL
  N20    one .unw.rsc per pair                                                                        FAIL
  N13    the six geometry .rsc                                                                        FAIL
  G12    SLC/<REF>/data.rsc: STARTING_RANGE; POLARIZATION HH; HEADING                                 FAIL
  G5b.7  F21: rwin, verify and stack2 still CURRENT beside the new data.rsc                           FAIL
--dryrun DIR: a plan only (prep_isce writes into the frame). Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import glob
import os
import subprocess
import sys

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5

PHASE, IDX, LOGIC = 'prep', '5b', 1
GEOM = ('hgt.rdr', 'lat.rdr', 'lon.rdr', 'los.rdr', 'shadowMask.rdr', 'incLocal.rdr')


def read_rsc(p):
    d = {}
    for ln in open(p):
        w = ln.split(None, 1)
        if len(w) == 2:
            d[w[0]] = w[1].strip()
    return d


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5b: prep_isce.py (G12, N13, N20)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m = P1.load_env(), P2.load_stack(), P5.load_mintpy()
    geo, _ = P3.geometry(W)
    ref = (geo or {}).get('ref')
    ri = P1.record(W, '4f', 'igram') or {}
    # prep_isce reads the frame's files only: admit comes before it for the order of the run, not as an input
    fp = C.md5_obj(dict(logic=LOGIC, igram=ri.get('outputs', {}).get('digest'), reference=ref, mintpy=m['MINTPY_VERSION']))
    if a.state:
        print(P5.state(recdir, W, PHASE, IDX, fp))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5']))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    if not P5.prior5(st, 'G5b.1', recdir, recdir, '5a', 'admit', outs=True, dry=bool(a.dryrun)):
        return st.finish()
    ri, have = P5.igram_prior(st, 'G5b.1i', W, recdir, a.dryrun)
    if not ri:
        return st.finish()
    if not P5.env_gate(st, 'G5b.2', env, s, m):
        return st.finish()
    if not P5.which_gate(st, 'G5b.3', s, ('prep_isce.py',)):
        return st.finish()
    if not have:
        return P5.plan_only(st, ['would run prep_isce.py from the frame folder: -m SLC/<REF>/data.dat -g geom_reference -b baselines '
                                 '-f "Igrams/*/filt_*.unw" --geom-files %s' % ' '.join(GEOM)], 'the frame has no interferograms yet')
    sd = os.path.join(W, 'SLC', ref or '?')
    meta = os.path.join(sd, 'data.dat')
    miss = [n for n in ('data.dat', 'data.dir', 'data.bak') if not os.path.isfile(os.path.join(sd, n))]
    st.gate('G5b.4', 'the metadata file', 'FAIL' if miss or not ref else 'PASS', '%s%s' % (
        meta, '; missing: %s' % ', '.join(miss) if miss else ' with data.dir and data.bak'),
        'the reference\'s shelve, named with .dat (F40)')
    if miss or not ref:
        return st.finish()
    pairs = P5.pairs_of(W)
    args = ['prep_isce.py', '-m', meta, '-g', os.path.join(W, 'geom_reference'), '-b', os.path.join(W, 'baselines'),
            '-f', os.path.join(W, 'Igrams', '*', 'filt_*.unw'), '--geom-files'] + list(GEOM)
    if a.dryrun:
        P5.way_gate(st, 'G5b.5', W, PHASE, True)
        print('   would run from %s:\n     %s' % (W, ' '.join(args)))
        print('   and then find %d .unw.rsc, 6 geometry .rsc and SLC/%s/data.rsc' % (len(pairs), ref))
        st.rec['outputs'] = dict(planned=True, dryrun=True, command=args)
        return st.finish('plan only (dry run): prep_isce writes into the frame')
    if not P5.way_gate(st, 'G5b.5', W, PHASE, False):
        return st.finish()
    lg = P1.new_log(os.path.join(W, 'logs', 'p5', 'prep', 'prep_isce.log'))
    rc, out = P5.run_logged(args, W, lg, P5.mpl_env(W))
    st.gate('G5b.6', 'prep_isce.py', 'PASS' if rc == 0 else 'FAIL', 'rc %d; log %s' % (rc, lg), 'rc 0', '' if rc == 0 else P3.tail(lg, 8))
    if rc != 0:
        return st.finish()
    unw = sorted(glob.glob(os.path.join(W, 'Igrams', '*', '*.unw.rsc')))
    have = set(os.path.basename(os.path.dirname(p)) for p in unw)
    lack = [p for p in pairs if p not in have]
    st.gate('N20', 'one .unw.rsc per pair', 'FAIL' if len(unw) != len(pairs) or lack else 'PASS', '%d .unw.rsc for %d pairs%s' % (
        len(unw), len(pairs), '; none for %s' % ', '.join(lack[:5]) if lack else ''), '= pairs')
    grsc = sorted(glob.glob(os.path.join(W, 'geom_reference', '*.rsc')))
    want = sorted(os.path.join(W, 'geom_reference', g + '.rsc') for g in GEOM)
    st.gate('N13', 'the six geometry .rsc', 'FAIL' if grsc != want else 'PASS', '%d: %s' % (
        len(grsc), ', '.join(os.path.basename(x) for x in grsc)), ', '.join(g + '.rsc' for g in GEOM))
    drsc = os.path.join(sd, 'data.rsc')
    d = read_rsc(drsc) if os.path.isfile(drsc) else {}
    pol = d.get('POLARIZATION') or d.get('polarization')
    bad = [k for k in ('STARTING_RANGE', 'HEADING') if k not in d] + ([] if pol == 'HH' else ['POLARIZATION %s, want HH' % pol])
    st.gate('G12', 'SLC/%s/data.rsc' % ref, 'FAIL' if bad or not d else 'PASS', 'STARTING_RANGE %s, POLARIZATION %s, HEADING %s' % (
        d.get('STARTING_RANGE'), pol, d.get('HEADING')), 'present; POLARIZATION HH (verify, G4)', '; '.join(bad))
    if len(unw) != len(pairs) or lack or grsc != want or bad or not d:
        return st.finish()
    states = {}
    for ph in ('rwin', 'verify', 'stack2'):
        p = subprocess.run([sys.executable, '-B', os.path.join(P5.HERE, 'lp_%s.py' % ph), '--path', path, '--frame', frame, '--state'],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        states[ph] = p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1] if p.stdout else 'rc %d' % p.returncode
    bad = [k for k, v in states.items() if v != 'CURRENT']
    st.gate('G5b.7', 'F21: the phases before still CURRENT', 'FAIL' if bad else 'PASS', ', '.join('%s %s' % kv for kv in states.items()),
            'CURRENT (data.rsc is not part of a shelve\'s identity)', 'a new .rsc made an earlier phase STALE' if bad else '')
    lst = P3.listing(W, P5.OUTS[PHASE])
    # what mcfg takes from prep: the .rsc files' contents (a re-run that writes the same bytes leaves mcfg CURRENT)
    content = C.md5_obj([[x[0], C.md5_file(os.path.join(W, x[0]))] for x in lst])
    st.rec['outputs'] = dict(log=lg, unw_rsc=len(unw), geom_rsc=len(grsc), data_rsc=d, files=lst, digest=P3.digest(lst), states=states,
                             content_md5=content)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_prep', main)
