#!/usr/bin/env python3
"""lp_stage.py -- linog_auto Phase 0b: frame skeleton and staging, from recon/RECON.json.

Creates p<PATH>/ (with LINEAGE.txt) and the frame folder, links the DEM into DEM/,
makes the relative link data -> raw (E6), and links every KEPT granule into raw/.
v0.13 (R8, ascending record 13.4): each frame's LINEAGE line names that frame's direction (the header line names the
first frame's only); the DEM is the path table's for the frame (dem_<frame> in place of dem, 14.4).
Nothing is moved, deleted or overwritten: an existing entry that differs from the plan
stops the phase with DECISION and is listed. A second run changes nothing.
v0.13 (the part 1 review's B1): linog_auto appends only to a lineage file it wrote: p<PATH>/LINEAGE.txt when it is absent
or its first line is linog_auto's header, else p<PATH>/LINEAGE_linog_auto.txt beside another tool's (the course kit's
path folders hold the 12 delivered ascending frames); G0b.7 names the file.

Gates
  G0b.1 recon on record is PASS and current                 FAIL otherwise
  G0b.2 raw/ holds exactly the kept granules, right targets FAIL
  G0b.3 no dangling link in raw/ or DEM/                    FAIL
  G0b.4 nothing in the way (entries that differ from plan)  DECISION
  G0b.5 DEM links resolve to the path table's DEM           FAIL
  G0b.6 data -> raw is relative                             FAIL
  G0b.7 the path's lineage file (v0.13)                      INFO
--dryrun DIR prints the plan and writes only DIR/status/P0b_stage.json.
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import json
import os
import sys

import lp_common as C

TOOLS = ('lp_stage.py', 'lp_common.py')
SUBDIRS = ('raw', 'DEM', 'logs', 'status', 'recon')


def link_state(link, target):
    """'absent', 'ok', or a description of what is in the way."""
    if not os.path.lexists(link):
        return 'absent'
    if not os.path.islink(link):
        return 'not a link: %s' % link
    got = os.readlink(link)
    return 'ok' if got == target else 'points to %s, plan %s' % (got, target)


def lineage_file(P):
    """v0.13: (the lineage file linog_auto appends to, a note): p<PATH>/LINEAGE.txt when absent or linog_auto's (its
    first line names linog_auto), else LINEAGE_linog_auto.txt beside it, so another tool's file is never written."""
    lin = os.path.join(P, 'LINEAGE.txt')
    if not os.path.lexists(lin):
        return lin, ''
    try:
        with open(lin, errors='replace') as fh:
            first = fh.readline().strip()
    except OSError as e:
        first = '(unreadable: %s)' % e
    if os.path.isfile(lin) and not os.path.islink(lin) and 'frames built by linog_auto' in first:
        return lin, ''
    return os.path.join(P, 'LINEAGE_linog_auto.txt'), ('LINEAGE.txt is not linog_auto\'s (its first line: "%s"): '
                                                        'linog_auto\'s lines go beside it' % first[:80])


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 0b: stage')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    rj = os.path.join(recdir, 'recon', 'RECON.json')
    rs = os.path.join(recdir, 'status', 'P0a_recon.json')
    rj_md5 = C.md5_file(rj) if os.path.exists(rj) else None
    rs_fp = json.load(open(rs)).get('fingerprint') if os.path.exists(rs) else None
    dem = cfg['dem']
    fp = C.md5_obj(dict(recon_json=rj_md5, recon_fp=rs_fp, tools=C.tool_md5s(*TOOLS), root=cfg['root'],
                        dem=dem))
    if a.state:
        print(C.state(recdir, 'stage', '0b', fp))
        return 0

    st = C.Status(recdir, 'stage', '0b', path, frame)
    st.rec.update(fingerprint=fp, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(recon_json=rj, recon_json_md5=rj_md5, root=cfg['root'], dem=dem))
    st.write()
    print('%s  Phase 0b stage  p%s f%s  %s' % (C.VERSION, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: plan only)' if a.dryrun else ''))

    if not (os.path.exists(rs) and os.path.exists(rj)):
        st.gate('G0b.1', 'recon PASS and current', 'FAIL', 'no recon record under %s' % recdir)
        return st.finish()
    rec = json.load(open(rs))
    if rec.get('verdict') != 'PASS' or rec.get('outputs', {}).get('recon_json_md5') != rj_md5:
        st.gate('G0b.1', 'recon PASS and current', 'FAIL', 'recon %s; RECON.json md5 %s, record says %s' % (
            rec.get('verdict'), rj_md5, rec.get('outputs', {}).get('recon_json_md5')))
        return st.finish()
    R = json.load(open(rj))
    kept = R['kept']
    st.gate('G0b.1', 'recon PASS and current', 'PASS', '%d kept, branch %s' % (len(kept), R['branch']))

    P = os.path.join(cfg['root'], 'p' + path)
    plan_dirs = [P, W] + [os.path.join(W, d) for d in SUBDIRS]
    plan_links = [(os.path.join(W, 'raw', os.path.basename(k['zip'])), k['zip']) for k in kept]
    dem_links = [(os.path.join(W, 'DEM', os.path.basename(dem) + e), dem + e) for e in ('', '.vrt', '.xml')]
    data_link = (os.path.join(W, 'data'), 'raw')

    if a.dryrun:
        print('   would create %d folders (those absent): %s' % (
            sum(not os.path.isdir(d) for d in plan_dirs), ', '.join(d for d in plan_dirs if not os.path.isdir(d))))
        print('   would link %d granules into %s/raw, the DEM trio into DEM/, and data -> raw' % (
            len(plan_links), W))
        for link, target in plan_links[:3]:
            print('      %s -> %s' % (os.path.basename(link), target))
        if len(plan_links) > 3:
            print('      ... %d more' % (len(plan_links) - 3))
        for link, target in dem_links:
            print('      DEM/%s -> %s' % (os.path.basename(link), target))
        way = [(l, s) for l, t in plan_links + dem_links + [data_link] for s in [link_state(l, t)]
               if s not in ('absent', 'ok')]
        st.gate('G0b.4', 'nothing in the way', 'DECISION' if way else 'PASS', '%d conflicting entries' % len(way),
                '0', '\n'.join('%s: %s' % x for x in way))
        lin, lnote = lineage_file(P)
        st.gate('G0b.7', 'the path\'s lineage file', 'INFO', 'would append to %s' % os.path.relpath(lin, cfg['root']), '', lnote)
        st.rec['outputs'] = dict(planned_links=len(plan_links), dryrun=True)
        return st.finish('plan only (dry run)' if not way else '')

    # ---- make it so: create what is absent, never touch what exists
    way = []
    for d in plan_dirs:
        if os.path.lexists(d) and not os.path.isdir(d):
            way.append((d, 'exists and is not a folder'))
    for link, target in plan_links + dem_links + [data_link]:
        s = link_state(link, target)
        if s not in ('absent', 'ok'):
            way.append((link, s))
    raw = os.path.join(W, 'raw')
    extra = sorted(set(os.listdir(raw)) - set(os.path.basename(l) for l, _ in plan_links)) \
        if os.path.isdir(raw) else []
    way += [(os.path.join(raw, e), 'in raw/ but not a kept granule') for e in extra]
    st.gate('G0b.4', 'nothing in the way', 'DECISION' if way else 'PASS', '%d conflicting entries' % len(way),
            '0', '\n'.join('%s: %s' % x for x in way)
            + ('\nnothing was changed; resolve these by hand (move to _archive), then re-run' if way else ''))
    if way:
        return st.finish()

    made_dirs = made_links = 0
    for d in plan_dirs:
        if not os.path.isdir(d):
            os.makedirs(d)
            made_dirs += 1
    for link, target in plan_links + dem_links + [data_link]:
        if not os.path.lexists(link):
            os.symlink(target, link)
            made_links += 1
    lin, lnote = lineage_file(P)
    if not os.path.exists(lin):
        with open(lin, 'w') as fh:
            fh.write('p%s: ALOS-1 PALSAR path %d (%s), frames built by linog_auto.\n'
                     'Each frame keeps its own records in status/, recon/ and logs/.\n'
                     % (path, int(path), 'descending' if R['direction'] == 'D' else 'ascending'))
    if made_links:
        with open(lin, 'a') as fh:
            fh.write('%s  f%s staged by %s: %s, %d granules, branch %s, %d links made\n'
                     % (C.utc(), frame, C.VERSION, 'descending' if R['direction'] == 'D' else 'ascending', len(kept),
                        R['branch'], made_links))

    # ---- check what is there now
    names = sorted(os.listdir(raw))
    wrong = [l for l, t in plan_links if link_state(l, t) != 'ok']
    st.gate('G0b.2', 'raw/ = kept granules', 'PASS' if (len(names) == len(kept) and not wrong) else 'FAIL',
            '%d entries, %d kept, %d wrong' % (len(names), len(kept), len(wrong)), 'equal, 0 wrong',
            '\n'.join(wrong))
    dang = [l for l, _ in plan_links + dem_links if not os.path.exists(l)]
    st.gate('G0b.3', 'no dangling links', 'FAIL' if dang else 'PASS', '%d dangling' % len(dang), '0',
            '\n'.join(dang))
    dem_ok = all(os.path.realpath(l) == os.path.realpath(t) for l, t in dem_links)
    st.gate('G0b.5', 'DEM links', 'PASS' if dem_ok else 'FAIL', os.path.basename(dem))
    st.gate('G0b.6', 'data -> raw relative', 'PASS' if os.readlink(data_link[0]) == 'raw' else 'FAIL',
            os.readlink(data_link[0]))
    st.gate('G0b.7', 'the path\'s lineage file', 'INFO', os.path.relpath(lin, cfg['root']), '', lnote)
    st.rec['outputs'] = dict(frame_dir=W, links=len(names), made_dirs=made_dirs, made_links=made_links, lineage=lin,
                             raw_list_md5=C.md5_obj(sorted((n, os.readlink(os.path.join(raw, n))) for n in names)))
    print('   made %d folders and %d links%s' % (made_dirs, made_links,
                                                  '' if made_dirs or made_links else ' (nothing to do)'))
    return st.finish()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, FileNotFoundError) as e:
        sys.stderr.write('lp_stage: %s\n' % e)
        sys.exit(3)
