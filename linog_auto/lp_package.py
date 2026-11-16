#!/usr/bin/env python3
"""lp_package.py -- linog_auto Phase 6c: the review package (D8), by hard links, with its manifest.

After accept: <frame>/_xfer/<PREFIX>_<TAG>_<VERSION>_<YYYYMMDD, UTC>_review/, laid out as the 12 frames' staging
(chapter 9.4, run as written in rehearsal R25, 17 Sept 2026), with D5's pages and F55's manifest:
  LInOG_Upload_<TAG>/           the delivery: its 16 files, and reports/ with the report's pages (D5)
  Igrams/                       the report's pair JPEGs, flat (filt_<pair>_phase.jpg, filt_<pair>_combined.jpg)
  Igrams/reports/               the report's pages
  RUN_MANIFEST.json             what made the delivery (F55)
  TRANSFER_MANIFEST_<TAG>.txt   written last: "md5  ./relative path" for every other file, in byte order (LC_ALL=C;
                                chapter 9.4's sort -k2 used the locale's: the order only, md5sum -c does not depend
                                on it); it does not list itself
Every payload file is a hard link of the file the records name (nothing is copied: one filesystem, G6c.4). The
package is checked by `md5sum -c`, and its hash of hashes (`cut -c1-32 <manifest> | LC_ALL=C sort | md5sum`) must
equal the sources' taken before the first link.

v0.13 (the ascending record 11.13, 22-b): the prefix by the path's direction, LINOG_DESC on a descending path, LINOG_ASC on an
ascending one. v0.13 r2 (the part 6 review, 26.1; LOGIC 2): a direction neither A nor D FAILs G6c.0 with a record, and
--state prints a state word, where it raised before any record (P6R-09; the path table's G0.6 at recon keeps it from a
run); G6c.2 looks for a package of this frame and version under any prefix, so a package of another direction's prefix
(LINOG_DESC_<TAG> beside LINOG_ASC_<TAG>) is in the way too (P6R-11).

Gates
  G6c.0  v0.13 r2: the path's direction A or D (the prefix by it)                                        FAIL
  G6c.1  accept PASS on record; deliver PASS on record, its files as it recorded them; report PASS, its files FAIL
  G6c.2  nothing in the way: no package of this frame and version under _xfer/, whatever its date and (v0.13 r2) its
         prefix                                                                                          DECISION
  G6c.3  the sources: the 16 files, the report's pages (in the delivery's reports/ and in Igrams/reports/)
         and pair JPEGs as the report's record lists them, RUN_MANIFEST.json; each a regular file        FAIL
  G6c.4  one filesystem: the sources and _xfer/ on one st_dev (else hard links are impossible)          FAIL
  G6c.5  the tree: each payload file the source's inode (a link, not a copy); each page in the delivery's reports/ the
         report's own page (the same inode); the counts per folder; no other file, folder or link        FAIL
  G6c.6  the manifest: one line per payload file, ./ paths, not self-listed; md5sum -c: 0 lines not OK;
         its hash of hashes = the sources'                                                               FAIL
  G6c.7  the filesystem's used space before and after (links: the folders and the manifest only)         INFO
--state: STALE when a file of the package changed or went, or the delivery's or the report's files are no longer as their
phases recorded them. --dryrun DIR: the plan (the name, the tree, the counts and
bytes when the frame has its delivery); nothing is written. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import collections
import glob
import os
import shutil
import subprocess

import lp_common as C
import lp_p1 as P1
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'package', '6c', 2   # v0.13 r2: G6c.0 and G6c.2 under any prefix decide what LOGIC 1 did not (P6R-09, 11)


def any_prefix_glob(path, frame, q):
    """v0.13 r2 (the part 6 review's P6R-11): every package of this frame and version under _xfer/, whatever its date and its
    prefix: _xfer/*_<TAG>_<VERSION>_*_review (the tag between underscores names this frame alone)."""
    return '%s/*_%s_%s_*_review' % (q['XFER'], P6.tag(path, frame), q['PACKAGE_VERSION'])


def recorded_package(recdir):
    """The package this phase recorded (its path relative to the frame), or None."""
    return ((P1.record(recdir, IDX, PHASE) or {}).get('outputs') or {}).get('package')


def plan(W, path, frame, rr):
    """[(source relative to W, destination relative to the package)] in the chapter's layout."""
    t, up = P6.tag(path, frame), P6.upload_rel(path, frame)
    pages, pairs = P6.pages_of(rr)
    out = [('%s/%s' % (up, n), 'LInOG_Upload_%s/%s' % (t, n)) for n in P6.delivery_names(path, frame)]
    out += [('%s/reports/%s' % (up, os.path.basename(p)), 'LInOG_Upload_%s/reports/%s' % (t, os.path.basename(p))) for p in pages]
    out += [(p, 'Igrams/%s' % os.path.basename(p)) for p in pairs]
    out += [(p, 'Igrams/reports/%s' % os.path.basename(p)) for p in pages]
    out.append(('RUN_MANIFEST.json', 'RUN_MANIFEST.json'))
    return out


def tree(root):
    """(files by folder, folders, links, other) of a package tree, relative to its root."""
    files, dirs, links, other = collections.Counter(), [], [], []
    for d, ds, fs in os.walk(root):
        ds.sort()
        rel = os.path.relpath(d, root)
        dirs.append(rel)
        for n in sorted(fs + [x for x in ds if os.path.islink(os.path.join(d, x))]):
            q = os.path.join(d, n)
            if os.path.islink(q):
                links.append(os.path.join(rel, n))
            elif os.path.isfile(q):
                files[rel] += 1
            else:
                other.append(os.path.join(rel, n))
    return files, dirs, links, other


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 6c: the review package (D8)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    q = P6.load_p6()
    rd, rr, ra = (P1.record(recdir, i, p) or {} for i, p in (('6a', 'deliver'), ('4g', 'report'), ('6b', 'accept')))
    try:   # v0.13 r2 (P6R-09): a direction neither A nor D is G6c.0's FAIL below, not an error before any record
        prefix, dir_bad = P6.package_prefix(q, cfg.get('direction')), None
    except ValueError as e:
        prefix, dir_bad = None, str(e)
    fp = C.md5_obj(dict(logic=LOGIC, deliver=rd.get('outputs', {}).get('digest'), report=rr.get('outputs', {}).get('digest'),
                        accept=ra.get('fingerprint'), keys=[q['XFER'], prefix, q['PACKAGE_VERSION']]))
    if a.state:
        rel = recorded_package(recdir)
        sv = P6.state(recdir, W, PHASE, IDX, fp, (rel,) if rel else ())
        # CURRENT only while the delivery and the report are as their phases recorded them
        if sv == 'CURRENT' and (P3.listing_changed(W, P6.deliver_outs(path, frame), rd.get('outputs', {}).get('files')) or
                                P3.listing_changed(W, P5.OUTS['report'], rr.get('outputs', {}).get('files'))):
            sv = 'STALE'
        print(sv)
        return 0

    st = P6.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(p6_cfg=q['p6_cfg_file'], p6_cfg_md5=q['p6_cfg_md5']))
    P6.header(PHASE, IDX, path, frame, W, a.dryrun)
    dry = bool(a.dryrun)
    st.gate('G6c.0', 'the path\'s direction', 'FAIL' if dir_bad else 'PASS', '%r from %s: %s' % (
        cfg.get('direction'), 'the path table\'s [p%s]' % path if cfg.get('entry') == 'table' else 'the frame rule (a derived entry)',
        dir_bad or 'the prefix %s' % prefix), 'A or D (the package\'s prefix by the path\'s direction, 11.13)')
    if dir_bad:
        return st.finish()
    ra, _ = P6.prior6(st, 'G6c.1', recdir, W, '6b', 'accept', P6.ACCEPT_OUTS, dry)
    if not ra:
        return st.finish()
    rd, fd = P6.prior6(st, 'G6c.1d', recdir, W, '6a', 'deliver', P6.deliver_outs(path, frame), dry)
    if not rd:
        return st.finish()
    rr, _ = P6.prior6(st, 'G6c.1r', recdir, W, '4g', 'report', P5.OUTS['report'], dry)
    if not rr:
        return st.finish()
    day = C.utc()[:10].replace('-', '')
    name = P6.package_name(path, frame, q, day, cfg['direction'])
    rel = '%s/%s' % (q['XFER'], name)
    X = os.path.join(W, rel)
    way = any_prefix_glob(path, frame, q)   # v0.13 r2 (P6R-11): any prefix, not only this direction's
    have = sorted(os.path.relpath(p, W) for p in glob.glob(os.path.join(W, way)))
    if dry:
        st.gate('G6c.2', 'nothing in the way', 'INFO', 'dry run: under %s/ now: %s' % (q['XFER'], ', '.join(have) or 'no package of %s %s'
                                                                                        % (P6.tag(path, frame), q['PACKAGE_VERSION'])),
                '%s absent' % way)
    elif have:
        st.gate('G6c.2', 'nothing in the way', 'DECISION', 'under %s/ already: %s' % (q['XFER'], ', '.join(have)),
                '%s absent' % way, 'a package of this frame and version from an earlier run%s; move it into '
                '%s/_archive/ (and keep it if it was sent), or raise PACKAGE_VERSION in linog_phase6.cfg, and run again' % (
                    '' if all(os.path.basename(x).startswith(prefix + '_') for x in have) else
                    ' (under another prefix than this path\'s %s: the path\'s direction changed, or another tool made it)' % prefix, W))
        return st.finish()
    else:
        st.gate('G6c.2', 'nothing in the way', 'PASS', 'no package of %s %s under %s/' % (P6.tag(path, frame), q['PACKAGE_VERSION'], q['XFER']),
                'absent')
    pl = plan(W, path, frame, rr)
    if dry and not fd:
        for s_, d_ in pl[:3] + [('...', '...')] + pl[-2:]:
            print('   would link %s -> %s/%s' % (s_, rel, d_))
        st.rec['outputs'] = dict(planned=True, dryrun=True, package=rel, files=[], links=len(pl))
        return st.finish('plan only (dry run): the frame has no delivery yet; %s with %d links and %s' % (rel, len(pl), P6.manifest_name(path, frame)))
    miss = [s_ for s_, _ in pl if not os.path.isfile(os.path.join(W, s_)) or os.path.islink(os.path.join(W, s_))]
    counts = collections.Counter(d_.rsplit('/', 1)[0] if '/' in d_ else '.' for _, d_ in pl)
    size = sum(os.path.getsize(os.path.join(W, s_)) for s_, _ in pl if s_ not in miss)
    st.gate('G6c.3', 'the sources', 'FAIL' if miss else 'PASS', '%d files, %d B: %s' % (
        len(pl), size, ', '.join('%s %d' % kv for kv in sorted(counts.items()))), 'each a regular file, as the records name it',
        'absent or not a regular file: ' + ', '.join(miss[:8]) if miss else '')
    if miss:
        return st.finish()
    xf = os.path.join(W, q['XFER'])
    devs = collections.Counter(os.stat(os.path.join(W, s_)).st_dev for s_, _ in pl)
    xdev = os.stat(xf if os.path.isdir(xf) else W).st_dev
    ok = set(devs) == {xdev}
    st.gate('G6c.4', 'one filesystem', 'PASS' if ok else 'FAIL', 'the sources on st_dev %s; %s on %s' % (
        ', '.join(str(k) for k in sorted(devs)), q['XFER'] + '/' if os.path.isdir(xf) else 'the frame', xdev),
        'one st_dev (hard links)')
    if not ok:
        return st.finish()
    h0, n0 = P6.md5_all([os.path.join(W, s_) for s_, _ in pl])
    if dry:
        print('   would make %s/ (%d links, then %s)' % (rel, len(pl), P6.manifest_name(path, frame)))
        st.rec['outputs'] = dict(planned=True, dryrun=True, package=rel, files=[], links=len(pl), bytes=size, hash_of_hashes=h0)
        return st.finish('plan only (dry run): %s, %d links, %d B, hash of hashes %s' % (rel, len(pl), size, h0))
    # ---- the links
    used0 = shutil.disk_usage(W).used
    for d_ in sorted(set(os.path.dirname(os.path.join(X, d_)) for _, d_ in pl)):
        os.makedirs(d_, exist_ok=True)
    for s_, d_ in pl:
        os.link(os.path.join(W, s_), os.path.join(X, d_))
    mname = P6.manifest_name(path, frame)
    lines = P6.manifest_lines(X, mname)
    with open(os.path.join(X, mname), 'w') as fh:
        fh.write(''.join(ln + '\n' for ln in lines))
    used1 = shutil.disk_usage(W).used
    # ---- the tree
    bad = []
    for s_, d_ in pl:
        a_, b_ = os.stat(os.path.join(W, s_)), os.stat(os.path.join(X, d_))
        if (a_.st_dev, a_.st_ino) != (b_.st_dev, b_.st_ino):
            bad.append('%s is not a link of %s' % (d_, s_))
    # D5's pages: the delivery's reports/ and Igrams/reports/ one file each (a report made again after the delivery would
    # leave the old pages in one and the new in the other)
    for p in P6.pages_of(rr)[0]:
        up = os.path.join(W, P6.upload_rel(path, frame), 'reports', os.path.basename(p))
        if not os.path.samefile(up, os.path.join(W, p)):
            bad.append('%s/reports/%s is not %s (the report was made again after the delivery)' % (P6.upload_rel(path, frame),
                                                                                              os.path.basename(p), p))
    files, dirs, links, other = tree(X)
    want = dict(counts)
    want['.'] = want.get('.', 0) + 1   # the manifest
    if dict(files) != want:
        bad.append('files per folder %s, want %s' % (dict(files), want))
    if sorted(dirs) != sorted(set(['.'] + [x for x in want if x != '.'] + ['LInOG_Upload_%s' % P6.tag(path, frame), 'Igrams'])):
        bad.append('folders %s' % sorted(dirs))
    if links or other:
        bad.append('links %s, other %s' % (links[:4], other[:4]))
    st.gate('G6c.5', 'the tree', 'FAIL' if bad else 'PASS', '%s: %d files (%s), %d folders, %d links; every payload file the source\'s inode' % (
        rel, sum(files.values()), ', '.join('%s %d' % kv for kv in sorted(files.items())), len(dirs), len(links)),
        'links, not copies; the layout of chapter 9.4 with D5\'s reports/', '\n'.join(bad[:8]))
    if bad:
        return st.finish()
    n, badm = P6.check_manifest(X, mname)
    self_listed = [ln for ln in lines if ln.endswith('/' + mname)]
    notdot = [ln for ln in lines if not ln.split('  ', 1)[1].startswith('./')]
    h1 = P6.hashes_md5([ln.split('  ', 1)[0] for ln in lines])
    notok = None
    if shutil.which('md5sum'):
        p = subprocess.run(['md5sum', '-c', mname], cwd=X, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode('utf-8', 'replace').splitlines()
        notok = len([x for x in out if not x.endswith(': OK')]) or (1 if p.returncode else 0)
    problems = []
    if n != len(pl) or badm:
        problems.append('%d lines for %d files; failing: %s' % (n, len(pl), ', '.join(badm[:5])))
    if self_listed or notdot:
        problems.append('self-listed %d; not ./ %d' % (len(self_listed), len(notdot)))
    if notok:
        problems.append('md5sum -c: %d lines not OK' % notok)
    if h1 != h0 or n0 != n:
        problems.append('hash of hashes %s (%d), the sources\' %s (%d)' % (h1, n, h0, n0))
    st.gate('G6c.6', 'the manifest', 'FAIL' if problems else 'PASS', '%s: %d lines, %d B; md5sum -c %s; hash of hashes %s = the sources\'' % (
        mname, n, os.path.getsize(os.path.join(X, mname)), 'not run (no md5sum)' if notok is None else '%d not OK' % notok, h1),
        'one line per payload file, ./ paths, not self-listed; md5sum -c 0 not OK; the sources\' hash of hashes', '\n'.join(problems))
    st.gate('G6c.7', 'the space used', 'INFO', '%+d KiB on the frame\'s filesystem while the package was made (%d B of files by '
            'links; other users included)' % ((used1 - used0) // 1024, size), 'links: the folders and the manifest only')
    lst = P3.listing(W, (rel,))
    st.rec['outputs'] = dict(package=rel, manifest=os.path.join(X, mname), manifest_md5=C.md5_file(os.path.join(X, mname)), lines=n,
                             bytes=size, hash_of_hashes=h1, counts=dict(files), files=lst, digest=P3.digest(lst))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_package', main)
