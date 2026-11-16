#!/usr/bin/env python3
"""lp_rerun.py -- linog_auto Phase 6d (v0.11, item 3, record 122.6): the rerun check, the new package against an earlier one.

Runs inside lp_env.sh after package (GDAL and numpy for the readings; --state needs the standard library only). The
reference is
  the package recon/rerun_reference.txt names (the operator's: its first line that is not a # comment, a package folder,
  absolute or relative to the frame folder), else
  the package of the frame's newest archived tree (<root>/p<path>/_archive/f<frame>_*, newest by the UTC stamp that ends
  the tree's name, as the run block names them): the one its status/P6c_package.json records, else its one _xfer/*_review;
  a tree with neither, whose package or rerun record reads other than PASS (a DECISION left open there is not taken as
  the reference), or whose records cannot be read, is passed over for the next, and named; else
  none: a first run, nothing to compare.
The comparison is lp_compare.compare_packages, the tool beside the pipeline (item 5): each manifest against its files; the
names both ways; the files by md5, KMZs whose md5s differ by their entries (lp_kmz.compare), so a package of v0.10 (the
run's times in its KMZs) compares with one of v0.11; RUN_MANIFEST.json's leaves; the network key of both RUN_MANIFEST.json
(122.5); and the readings of each GeoTIFF that differs (mm/yr, NEW minus REF, on the cells valid in both).

Gates
  G6d.1  package PASS on record, its package as it recorded it                                         FAIL
  G6d.2  the reference: named, from the newest archived tree with a package, or none (a first run); FAIL when it is
         absent, the new package itself, not this frame's (its manifest not TRANSFER_MANIFEST_<TAG>.txt), or
         recon/rerun_reference.txt names no folder                                                      INFO / FAIL
  G6d.3  both manifests hold: md5sum -c on the reference and on the new package, every line OK          FAIL
  G6d.4  the names, both ways                                                                         PASS / INFO
  G6d.5  the files: equal by md5, or KMZs equal by their entries; RUN_MANIFEST.json left out           PASS / INFO
  G6d.6  RUN_MANIFEST.json's leaves that differ, listed, not judged                                       INFO
  G6d.7  the network key of both RUN_MANIFEST.json: complete and equal, differing, or not recorded whole   INFO
  G6d.8  the readings of each GeoTIFF that differs                                                INFO / WARN
  G6d.9  the verdict: every file equal but RUN_MANIFEST.json, PASS; files differ on another network, or on one
         the two manifests do not record whole, INFO with the readings; files differ on the same network,
         DECISION (a product changed with nothing in the network to explain it), in either --decide mode
         (122.8, Ariel's word), unless recon/rerun.txt takes it with the line `accept <the reference's folder
         name> <the reference's hash of hashes> <the new package's hash of hashes>`        PASS / INFO / DECISION
--state: STALE when the package changed, or the reference did (another archived tree, recon/rerun_reference.txt, or the
reference's manifest), or recon/rerun.txt did. --dryrun DIR: the same comparison on the frame's package as it is, the
record in DIR (G6d.9's DECISION an INFO there); the frame only read. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import glob
import os
import re

import lp_common as C
import lp_compare as X
import lp_p1 as P1
import lp_p6 as P6

PHASE, IDX, LOGIC = 'rerun', '6d', 1
VERSION_RERUN = 'linog_auto v0.11 (2026-10-09)'
STAMP = re.compile(r'_(\d{8}T\d{6}Z)$')
MAXLIST = 100


def op_file(W, name):
    p = os.path.join(W, 'recon', name)
    return p if os.path.isfile(p) else None


def named(W):
    """recon/rerun_reference.txt: (its first line that is not a comment, the folder it names, the file's md5), or Nones."""
    f = op_file(W, 'rerun_reference.txt')
    if not f:
        return None, None, None
    ls = [x.strip() for x in open(f, errors='replace') if x.strip() and not x.strip().startswith('#')]
    if not ls:
        return '', None, C.md5_file(f)
    return ls[0], os.path.normpath(ls[0] if os.path.isabs(ls[0]) else os.path.join(W, ls[0])), C.md5_file(f)


def archived(W, frame):
    """[(stamp, tree)] of the frame's trees under <root>/p<path>/_archive/, newest first by the UTC stamp ending the name."""
    out = []
    for t in glob.glob(os.path.join(os.path.dirname(W), '_archive', 'f%s_*' % frame)):
        m = STAMP.search(os.path.basename(t))
        if m and os.path.isdir(t) and not os.path.islink(t):
            out.append((m.group(1), t))
    return sorted(out, reverse=True)


def tree_package(tree):
    """(the package an archived tree holds, how it was found) or (None, why it is passed over)."""
    try:
        rp, rr = P1.record(tree, '6c', 'package'), P1.record(tree, '6d', 'rerun')
    except (OSError, ValueError) as e:
        return None, 'its records unreadable (%s)' % type(e).__name__
    if rp is not None and rp.get('verdict') != 'PASS':
        return None, 'its package record reads %s' % rp.get('verdict')
    if rr is not None and rr.get('verdict') != 'PASS':
        return None, 'its rerun record reads %s' % rr.get('verdict')
    rel = ((rp or {}).get('outputs') or {}).get('package')
    if rel and os.path.isdir(os.path.join(tree, rel)):
        return os.path.join(tree, rel), 'its status/P6c_package.json'
    xs = sorted(p for p in glob.glob(os.path.join(tree, '_xfer', '*_review')) if os.path.isdir(p))
    if len(xs) == 1:
        return xs[0], 'its one _xfer/*_review'
    return None, '%d packages in its _xfer/, none recorded' % len(xs)


def reference(W, frame):
    """dict(path, how, file_md5, passed): the reference this phase compares with (path None: none, or an empty file)."""
    line, p, fmd5 = named(W)
    if fmd5 is not None:
        if not line:
            return dict(path=None, how='recon/rerun_reference.txt names no folder', file_md5=fmd5, empty=True)
        return dict(path=p, how='recon/rerun_reference.txt names %s' % line, file_md5=fmd5)
    passed = []
    for stamp, tree in archived(W, frame):
        pk, how = tree_package(tree)
        rel = os.path.relpath(tree, os.path.dirname(W))
        if pk:
            return dict(path=pk, how='the newest archived tree with a package: %s (%s)%s' % (
                rel, how, '; passed over: %s' % ', '.join(passed) if passed else ''), tree=tree)
        passed.append('%s (%s)' % (rel, how))
    return dict(path=None, how='no recon/rerun_reference.txt and no archived tree of the frame with a package%s' % (
        ' (passed over: %s)' % ', '.join(passed) if passed else ''))


def ref_manifest_md5(ref):
    if not ref.get('path'):
        return None
    try:
        name, _ = X.manifest_of(ref['path'])
        return C.md5_file(os.path.join(ref['path'], name))
    except Exception as e:  # noqa: BLE001  read again by the run, which says why
        return 'unreadable: %s' % type(e).__name__


def accept_line(refname, rhh, hh):
    return 'accept %s %s %s' % (refname, rhh, hh)


def accepted(W, refname, rhh, hh):
    """recon/rerun.txt: (the accept line naming this reference, its hash of hashes and this package's, word by word; its #
    lines)."""
    f = op_file(W, 'rerun.txt')
    if not f:
        return None, []
    ls = [x.rstrip('\n') for x in open(f, errors='replace')]
    want = accept_line(refname, rhh, hh).split()
    hit = [' '.join(x.split()) for x in ls if x.split() == want]
    return (hit[0] if hit else None), [x.strip().lstrip('#').strip() for x in ls if x.strip().startswith('#')]


def cut(xs, n=MAXLIST):
    xs = list(xs)
    return xs[:n] + (['... and %d more' % (len(xs) - n)] if len(xs) > n else [])


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 6d: the rerun check (v0.11)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    dry = bool(a.dryrun)
    q = P6.load_p6()
    rpk = P1.record(recdir, '6c', 'package') or {}
    if dry and (P1.record(W, '6c', 'package') or {}).get('verdict') == 'PASS':
        rpk = P1.record(W, '6c', 'package')   # a dry run reads the frame's package when the frame has one (prior6's rule)
    ref = reference(W, frame)
    acc = op_file(W, 'rerun.txt')
    fp = C.md5_obj(dict(logic=LOGIC, package=(rpk.get('outputs') or {}).get('digest'), reference=ref.get('path'),
                        reference_manifest=ref_manifest_md5(ref), named=ref.get('file_md5'), accept=C.md5_file(acc) if acc else None))
    if a.state:
        print(P6.state(recdir, W, PHASE, IDX, fp, ()))
        return 0

    st = P6.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(p6_cfg=q['p6_cfg_file'], p6_cfg_md5=q['p6_cfg_md5'],
                                                                   reference=ref.get('path'), how=ref.get('how')))
    st.rec['version'] = VERSION_RERUN
    st.rec['tools'].update(C.tool_md5s('lp_compare.py', 'lp_kmz.py'))
    st.write()
    P6.header(PHASE, IDX, path, frame, W, a.dryrun)
    print('   rerun: %s, LOGIC %d' % (VERSION_RERUN, LOGIC))
    rel0 = (rpk.get('outputs') or {}).get('package')
    rp, _ = P6.prior6(st, 'G6d.1', recdir, W, '6c', 'package', (rel0,) if rel0 else (), dry)
    if not rp:
        return st.finish()
    o6 = rp.get('outputs') or {}
    if o6.get('planned') or not o6.get('package'):
        st.gate('G6d.2', 'the reference', 'INFO', 'the frame has no package yet: nothing to compare (%s)' % ref['how'])
        st.rec['outputs'] = dict(planned=True, dryrun=dry, reference=ref.get('path'))
        return st.finish('plan only (dry run): the frame is not packaged')
    NEWP = os.path.join(W, o6['package'])
    # ---- G6d.2 the reference
    if ref.get('empty'):
        st.gate('G6d.2', 'the reference', 'FAIL', ref['how'], 'a package folder, absolute or relative to the frame',
                'write the folder of the package to compare with on recon/rerun_reference.txt\'s first line, or move the file '
                'into %s/_archive/ to compare with the newest archived tree\'s package' % W)
        return st.finish()
    if not ref.get('path'):
        st.gate('G6d.2', 'the reference', 'INFO', '%s: a first run, nothing to compare' % ref['how'], 'an earlier package of the frame')
        st.rec['outputs'] = dict(package=o6['package'], reference=None, first_run=True, how=ref['how'])
        return st.finish()
    bad = None
    mine = P6.manifest_name(path, frame)
    if not os.path.isdir(ref['path']):
        bad = 'absent: %s' % ref['path']
    elif os.path.realpath(ref['path']) == os.path.realpath(NEWP):
        bad = 'the new package itself: %s' % ref['path']
    elif not os.path.isfile(os.path.join(ref['path'], mine)):
        bad = 'not this frame\'s package (no %s at its top): %s' % (mine, ref['path'])
    st.gate('G6d.2', 'the reference', 'FAIL' if bad else 'INFO', bad or '%s (%s)' % (ref['path'], ref['how']),
            'an earlier package of the frame', 'name another in recon/rerun_reference.txt' if bad else '')
    if bad:
        return st.finish()
    # ---- the comparison (lp_compare, item 5)
    try:
        c = X.compare_packages(NEWP, ref['path'])
    except (X.InputError, ValueError, OSError) as e:   # a manifest or RUN_MANIFEST.json that cannot be read
        st.gate('G6d.3', 'both manifests hold', 'FAIL', '%s: %s' % (type(e).__name__, e), 'one TRANSFER_MANIFEST_<TAG>.txt of '
                '"md5  ./path" lines at each package\'s top, and a readable RUN_MANIFEST.json')
        return st.finish()
    for ln in X.report_packages(c):
        print('   | ' + ln)
    cr, cn = c['check_ref'], c['check_new']
    probs = ['the reference: %d lines not OK (%s)' % (len(cr['failing']), ', '.join(cr['failing'][:5]))] if cr['failing'] else []
    probs += ['the new package: %d lines not OK (%s)' % (len(cn['failing']), ', '.join(cn['failing'][:5]))] if cn['failing'] else []
    st.gate('G6d.3', 'both manifests hold', 'FAIL' if probs else 'PASS', 'the reference\'s %s: %d lines OK, hash of hashes %s%s; the new '
            'package\'s %s: %d lines OK' % (cr['manifest'], cr['lines'] - len(cr['failing']), cr['hash_of_hashes'],
                                             ', %d files it does not list' % len(cr['unlisted']) if cr['unlisted'] else '',
                                             cn['manifest'], cn['lines'] - len(cn['failing'])),
            'md5sum -c: every line OK in both', '\n'.join(probs + (['the reference holds files its manifest does not list: %s'
                                                                   % ', '.join(cr['unlisted'][:5])] if cr['unlisted'] else [])))
    if probs:
        return st.finish()
    n = c['names']
    st.gate('G6d.4', 'the names', 'PASS' if not n['only_new'] and not n['only_ref'] else 'INFO', '%d and %d; only in the new package %d, '
            'only in the reference %d' % (n['new'], n['ref'], len(n['only_new']), len(n['only_ref'])), 'the same names',
            '\n'.join(['only new: ' + ', '.join(n['only_new'][:8])] * bool(n['only_new']) + ['only reference: ' + ', '.join(n['only_ref'][:8])] * bool(n['only_ref'])))
    mdiff = any(os.path.basename(r) == 'RUN_MANIFEST.json' for r in c['differ'])
    st.gate('G6d.5', 'the files', 'PASS' if not c['other_differ'] else 'INFO', '%d equal by md5; %d KMZs equal by their entries%s; '
            'RUN_MANIFEST.json %s; %d others differ' % (c['equal'], len(c['kmz_equal_by_entries']), ' (times %s)' % (
                'differ' if any(k.get('times_differ') for k in c['kmz'].values()) else 'equal') if c['kmz'] else '',
                'differs' if mdiff else 'equal', len(c['other_differ'])),
            'every file equal (KMZs by their entries) but RUN_MANIFEST.json', '\n'.join(cut(c['other_differ'], 12)))
    rm = c.get('run_manifest') or {}
    st.gate('G6d.6', 'RUN_MANIFEST.json\'s leaves', 'INFO', '%s against %s: %d leaves differ, %d only in the new, %d only in the reference' % (
        (rm.get('labels') or [None, None])[0], (rm.get('labels') or [None, None])[1], len(rm.get('differ') or []), len(rm.get('only_new') or []),
        len(rm.get('only_ref') or [])) if rm else 'not compared: a RUN_MANIFEST.json absent', 'listed, not judged',
            ', '.join((rm.get('differ') or [])[:12]))
    nk = c['network']
    dfields = [f for f, v in nk['fields'].items() if v == 'DIFFERS']
    mfields = [f for f, v in nk['fields'].items() if v == X.MISSING]
    st.gate('G6d.7', 'the network key', 'INFO', 'complete and equal' if nk['equal'] else (
        'differs: %s' % ', '.join('%s %s -> %s' % (f, str(nk['ref'][f])[:40], str(nk['new'][f])[:40]) for f in dfields) if nk['complete']
        else 'not recorded whole: %s%s' % (', '.join(mfields), '; differs: %s' % ', '.join(dfields) if dfields else '')),
            'kept pairs, excludeDate12, excludeDate, the reference date and pixel, D9, the fit\'s dates (record 122.5)')
    rd = c['readings']
    errs = dict((p, r['error']) for p, r in rd.items() if 'error' in r)
    st.gate('G6d.8', 'the readings', 'WARN' if errs else 'INFO', '; '.join(
        '%s %s' % (p, 'median %+.3f p01 %+.3f p99 %+.3f mm/yr, beyond 1 %.4f, beyond 5 %.5f, max %.2f, gained %d, lost %d' % (
            r['median'], r['p01'], r['p99'], r['share_gt1'], r['share_gt5'], r['max_abs'], r['gained'], r['lost']) if 'median' in r
            else str(r)[:120]) for p, r in sorted(rd.items())) or 'none: no GeoTIFF differs',
            'NEW minus REF on the cells valid in both; readings, not a gate', '\n'.join('%s: %s' % kv for kv in sorted(errs.items())))
    hh = o6.get('hash_of_hashes') or cn['hash_of_hashes']
    refname = os.path.basename(os.path.normpath(ref['path']))
    line, why = accepted(W, refname, cr['hash_of_hashes'], hh)
    if c['same_files']:
        verdict, value = 'PASS', 'the new package reproduces the reference: every file equal but RUN_MANIFEST.json (KMZs by their entries)'
        note = ''
    elif not nk['equal']:
        verdict, value = 'INFO', '%d files differ, on %s: read G6d.7 and G6d.8' % (
            len(c['other_differ']) + len(n['only_new']) + len(n['only_ref']), 'another network' if nk['complete'] else 'a network the '
            'two manifests do not record whole')
        note = ''
    elif line:
        verdict, value = 'INFO', '%d files differ on the same network, taken by the operator: recon/rerun.txt "%s"' % (
            len(c['other_differ']) + len(n['only_new']) + len(n['only_ref']), line)
        note = '\n'.join(why)
    else:
        verdict = 'INFO' if dry else 'DECISION'
        value = '%d files differ on the same network (%s): a product changed with nothing in the network to explain it' % (
            len(c['other_differ']) + len(n['only_new']) + len(n['only_ref']), ', '.join(cut(c['other_differ'], 4)))
        note = ('read G6d.5 and G6d.8 (and lp_compare.py for the trees); to take the change, write recon/rerun.txt with the line\n'
                '  %s\nand a # line saying why, then run this phase again (--only rerun)%s' % (
                    accept_line(refname, cr['hash_of_hashes'], hh), '; a dry run: a run would stop here (DECISION)' if dry else ''))
    st.gate('G6d.9', 'the verdict', verdict, value, 'every file equal but RUN_MANIFEST.json, or a difference the network explains', note)
    st.rec['outputs'] = dict(
        package=o6['package'], hash_of_hashes=hh, reference=dict(path=ref['path'], how=ref['how'], manifest=cr['manifest'],
                                                                 manifest_md5=cr['manifest_md5'], lines=cr['lines'],
                                                                 hash_of_hashes=cr['hash_of_hashes'], unlisted=cut(cr['unlisted'])),
        names=dict(new=n['new'], ref=n['ref'], only_new=cut(n['only_new']), only_ref=cut(n['only_ref'])),
        equal=c['equal'], differ=cut(c['differ']), other_differ=cut(c['other_differ']), kmz=c['kmz'],
        kmz_equal_by_entries=c['kmz_equal_by_entries'],
        run_manifest=dict(labels=rm.get('labels'), leaves=rm.get('leaves'), differ=cut(rm.get('differ') or []),
                          only_new=cut(rm.get('only_new') or []), only_ref=cut(rm.get('only_ref') or [])) if rm else None,
        network=nk, readings=rd, same_files=c['same_files'], verdict=value, accepted=line, dryrun=dry or None)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_rerun', main)
