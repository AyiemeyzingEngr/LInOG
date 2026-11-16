#!/usr/bin/env python3
"""lp_extract.py -- linog_auto Phase 1a: extract the kept granules, flat, into unzipped/<zip stem>/.

Reads each zip through its raw/ link (the stage links). A granule is written into unzipped/.<stem>.part/
and renamed to unzipped/<stem>/ only when every member is written, so a folder without the dot is always
whole. Members are written by basename: the kit's tools (gen_phase1_dates.py, sort_modes.sh,
linog_scene_inventory.py) expect them at the top of the folder, RD2 measured all 24 P84 F3320 zips with
their members at the top, and a zip that keeps them under a folder is written flat the same way.
zipfile checks every member's CRC while reading. Nothing is overwritten, moved or deleted.

v0.13 (ascending record 4.2, R6; 18.5, R6-d): every branch recon gives runs on, FBS-only, FBS+FBD and FBD-only (v0.2 to
v0.12 took FBS-only alone); an FBD granule holds exactly one IMG-HV member, under IMG-HH's size law (verify's G4 reads it).

Gates
  G1a.1 recon and stage PASS on record, RECON.json unchanged since recon wrote it        FAIL
        branch FBS-only, FBS+FBD or FBD-only (v0.13)                                       ERROR
  G1a.2 a raw/ link per kept granule, resolving to the recorded zip; the zip readable  FAIL
  G1a.3 nothing in the way: no .part leftover; an existing unzipped/<stem>/ matches its zip (then reused);
        nothing in unzipped/ but the kept granules (the kit's later tools read unzipped/*/summary.txt)  DECISION
  G1a.4 exactly one VOL-, LED-, IMG-HH-, TRL- member and summary.txt (the unpacker takes the first IMG-HH
        and the first LED it finds); no two members with one name; no IMG-HV on an FBS date; v0.13: exactly one
        IMG-HV on an FBD date                                                                          FAIL
  G1a.5 IMG-HH size = 720 + lines x (412 + 8 x width): width from recon (CEOS), lines from summary.txt; v0.13: IMG-HV's
        the same on an FBD date                                                                        FAIL
  G1a.6 summary.txt date = recon date; off-nadir within the tolerance of recon's modal beam          FAIL
  G1a.7 free disk for what is still to write, plus the path table's disk_gib_margin   FAIL
  G1a.8 written = zip: every member of every granule on disk at its zip size                        FAIL
--dryrun DIR: the plan from DIR's recon record, checked against the zips; writes only DIR/status/P1a_extract.json
(its outputs carry the planned granules, so the unpack dry run can plan from them).
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import os
import re
import shutil
import sys
import time
import zipfile

import lp_common as C
import lp_p1 as P1

TOOLS = ('lp_extract.py', 'lp_p1.py', 'lp_common.py')
NEED = ('VOL-', 'LED-', 'IMG-HH-', 'TRL-')
BRANCHES = ('FBS-only', 'FBS+FBD', 'FBD-only')   # v0.13: R6 and R6-d (v0.2 to v0.12: FBS-only)


def zip_plan(zpath):
    """Members {basename: size}, summary.txt keys, problems, and whether any member sits under a folder."""
    mem, probs = {}, []
    with zipfile.ZipFile(zpath) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        for i in infos:
            b = os.path.basename(i.filename)
            if b in mem:
                probs.append('two members named %s' % b)
            mem[b] = i.file_size
        sm = [i for i in infos if os.path.basename(i.filename) == 'summary.txt']
        kv = dict(re.findall(r'(\w+)="([^"]*)"', zf.read(sm[0]).decode('latin-1'))) if sm else {}
        nested = any('/' in i.filename.strip('/') for i in infos)
    return mem, kv, probs, nested


def have_files(U):
    if not os.path.isdir(U):
        return None
    return {n: os.path.getsize(os.path.join(U, n)) for n in os.listdir(U) if os.path.isfile(os.path.join(U, n))}


def extract_one(zpath, part, U):
    os.makedirs(part)
    with zipfile.ZipFile(zpath) as zf:
        for i in zf.infolist():
            if i.is_dir():
                continue
            with zf.open(i) as src, open(os.path.join(part, os.path.basename(i.filename)), 'wb') as out:
                shutil.copyfileobj(src, out, 16 << 20)
    os.rename(part, U)


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 1a: extract')
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
    rj_md5 = C.md5_file(rj) if os.path.exists(rj) else None
    r_stage = P1.record(recdir, '0b', 'stage')
    fp = C.md5_obj(dict(recon_json=rj_md5, stage_fp=(r_stage or {}).get('fingerprint'),
                        tools=C.tool_md5s(*TOOLS), root=cfg['root']))
    if a.state:
        def missing(r):
            out, gs = [], (r or {}).get('outputs', {}).get('granules', [])
            for g in gs:
                for name, size in g['members'].items():
                    p = os.path.join(g['folder'], name)
                    if not (os.path.isfile(p) and os.path.getsize(p) == size):
                        out.append(p)
            ud = os.path.join(W, 'unzipped')
            return out + (sorted(set(os.listdir(ud)) - set(g['stem'] for g in gs)) if os.path.isdir(ud) else [])
        print(P1.state_with_outputs(recdir, 'extract', '1a', fp, missing))
        return 0

    st = C.Status(recdir, 'extract', '1a', path, frame)
    P1.begin(st)
    st.rec['version'] = P1.VERSION1
    st.rec.update(fingerprint=fp, tools=C.tool_md5s(*TOOLS), inputs=dict(recon_json=rj, recon_json_md5=rj_md5))
    st.write()
    print('%s  Phase 1a extract  p%s f%s  %s' % (P1.VERSION1, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: plan only)' if a.dryrun else ''))

    r_recon, why = P1.record(recdir, '0a', 'recon'), []
    if not r_recon or r_recon.get('verdict') != 'PASS':
        why.append('recon %s' % ((r_recon or {}).get('verdict') or 'has no record'))
    elif r_recon.get('outputs', {}).get('recon_json_md5') != rj_md5:
        why.append('RECON.json changed since recon wrote it')
    if not r_stage or r_stage.get('verdict') != 'PASS':
        why.append('stage %s' % ((r_stage or {}).get('verdict') or 'has no record'))
    if why:
        st.gate('G1a.1', 'recon and stage PASS', 'FAIL', '; '.join(why))
        return st.finish()
    R, _ = P1.recon_json(recdir)
    kept, beam, tol = R['kept'], float(R['modal_offnadir']), float(cfg.get('offnadir_tol', 0.5))
    if R['branch'] not in BRANCHES:
        st.gate('G1a.1', 'recon and stage PASS', 'ERROR', '%d kept, branch %s' % (len(kept), R['branch']),
                ', '.join(BRANCHES), 'recon gave a branch this version has no steps for')
        return st.finish()
    st.gate('G1a.1', 'recon and stage PASS', 'PASS', '%d kept, branch %s' % (len(kept), R['branch']))

    plan, bad2, bad4, bad5, bad6, way, layout = [], [], [], [], [], [], {'at the top': 0, 'under a folder': 0}
    for k in kept:
        s = P1.stem(k['zip'])
        z = k['zip'] if a.dryrun else os.path.join(W, 'raw', os.path.basename(k['zip']))
        if not a.dryrun and (not os.path.lexists(z) or os.path.realpath(z) != os.path.realpath(k['zip'])):
            bad2.append('%s: raw/ link missing or not pointing at %s' % (s, k['zip']))
            continue
        try:
            mem, kv, probs, nested = zip_plan(z)
        except Exception as e:  # noqa: BLE001
            bad2.append('%s: %s' % (s, e))
            continue
        layout['under a folder' if nested else 'at the top'] += 1
        cnt = dict((p, sum(n.startswith(p) for n in mem)) for p in NEED)
        miss = [p.rstrip('-') for p in NEED if not cnt[p]] + ([] if 'summary.txt' in mem else ['summary.txt'])
        many = ['%d %s' % (cnt[p], p.rstrip('-')) for p in NEED if cnt[p] > 1]
        nhv = sum(n.startswith('IMG-HV-') for n in mem)
        hv = []
        if k['mode'] == 'FBS' and nhv:
            hv.append('IMG-HV on an FBS date')
        elif k['mode'] == 'FBD' and nhv != 1:   # v0.13: the FBD date's IMG-HV member, which verify's G4 reads
            hv.append('%d IMG-HV members on an FBD date, want 1' % nhv)
        if probs or miss or many or hv:
            bad4.append('%s: %s' % (s, '; '.join(probs + (['missing ' + ', '.join(miss)] if miss else [])
                                                 + (['more than one: ' + ', '.join(many)] if many else []) + hv)))
        lines = int(kv.get('Pdi_NoOfLines') or 0)
        want = 720 + lines * (412 + 8 * int(k['width']))
        for pol in ('HH', 'HV') if k['mode'] == 'FBD' else ('HH',):
            img = sorted(n for n in mem if n.startswith('IMG-%s-' % pol))
            if not img or not lines or mem[img[0]] != want:
                bad5.append('%s: IMG-%s %s B, want 720 + %d x (412 + 8 x %d) = %d' % (
                    s, pol, mem[img[0]] if img else 'absent', lines, int(k['width']), want))
        dsum = kv.get('Lbi_ObservationDate') or kv.get('Img_SceneCenterDateTime', '')[:8]
        try:
            on = float(kv.get('Img_OffNadirAngle'))
        except (TypeError, ValueError):
            on = None
        if dsum != k['date'] or on is None or abs(on - beam) > tol:
            bad6.append('%s: date %s (recon %s), off-nadir %s (beam %s +/- %s)' % (s, dsum, k['date'], on, beam, tol))
        U = os.path.join(W, 'unzipped', s)
        part = os.path.join(W, 'unzipped', '.%s.part' % s)
        act = 'extract'
        if os.path.lexists(part):
            way.append('%s: left by an interrupted run' % part)
            act = 'blocked'
        if os.path.lexists(U):
            have = have_files(U)
            if have is not None and all(have.get(n) == sz for n, sz in mem.items()):
                act = act if act == 'blocked' else 'reuse'
            else:
                way.append('%s: exists and does not match its zip' % U)
                act = 'blocked'
        plan.append(dict(stem=s, date=k['date'], mode=k['mode'], width=int(k['width']), lines=lines, zip=z,
                         folder=U, part=part, members=mem, nested=nested, action=act))

    ud, stems = os.path.join(W, 'unzipped'), set(P1.stem(k['zip']) for k in kept)
    for e in sorted(os.listdir(ud)) if os.path.isdir(ud) else []:
        if e not in stems and not (e.startswith('.') and e.endswith('.part') and e[1:-5] in stems):
            way.append('%s: in unzipped/ but not a kept granule' % os.path.join(ud, e))
    st.gate('G1a.2', 'zips readable through raw/', 'FAIL' if bad2 else 'PASS',
            '%d of %d; members %s' % (len(plan), len(kept), ', '.join('%s %d' % kv for kv in layout.items())),
            'all', '\n'.join(bad2))
    st.gate('G1a.4', 'members present, once', 'FAIL' if bad4 else 'PASS',
            '%d of %d complete' % (len(plan) - len(bad4), len(plan)), 'all', '\n'.join(bad4))
    nfbd = sum(p['mode'] == 'FBD' for p in plan)
    st.gate('G1a.5', 'IMG-HH size law' + (' (and IMG-HV on FBD dates)' if nfbd else ''), 'FAIL' if bad5 else 'PASS',
            '%d of %d = 720 + lines x (412 + 8 x width)%s' % (len(plan) - len(set(b.split(':')[0] for b in bad5)), len(plan),
                                                             ', IMG-HH and IMG-HV on %d FBD dates' % nfbd if nfbd else ''),
            'all', '\n'.join(bad5))
    st.gate('G1a.6', 'summary date and beam', 'FAIL' if bad6 else 'PASS',
            '%d of %d agree with recon' % (len(plan) - len(bad6), len(plan)), 'all', '\n'.join(bad6))
    todo = [p for p in plan if p['action'] == 'extract']
    margin = float(cfg.get('disk_gib_margin', 10))
    need = sum(sum(p['members'].values()) for p in todo) / 2.0 ** 30 + margin
    free = P1.free_gib(W)
    st.gate('G1a.7', 'free disk', 'PASS' if free >= need else 'FAIL', '%.1f GiB free, %.1f GiB needed' % (free, need),
            '>= what is to write + disk_gib_margin %.0f GiB' % margin)
    st.gate('G1a.3', 'nothing in the way', 'DECISION' if way else 'PASS',
            '%d to extract, %d already whole, %d in the way' % (len(todo), sum(p['action'] == 'reuse' for p in plan),
                                                               len(way)), '0 in the way',
            '\n'.join(way) + ('\nnothing was changed; move these into %s/ by hand, then re-run'
                              % os.path.join(W, '_archive') if way else ''))
    if any(g['verdict'] in ('FAIL', 'DECISION') for g in st.rec['gates']):
        return st.finish()
    if a.dryrun:
        print('   would extract %d granules (%.1f GB) into %s/unzipped/, flat' % (
            len(todo), sum(sum(p['members'].values()) for p in todo) / 1e9, W))
        for p in todo[:3]:
            print('      %s -> unzipped/%s/ (%d members)' % (os.path.basename(p['zip']), p['stem'], len(p['members'])))
        if len(todo) > 3:
            print('      ... %d more' % (len(todo) - 3))
        gran = [dict(stem=p['stem'], date=p['date'], mode=p['mode'], width=p['width'], lines=p['lines'],
                     folder=p['folder'], members=p['members']) for p in plan]
        st.rec['outputs'] = dict(planned=len(todo), dryrun=True, granules=gran, granules_md5=C.md5_obj(gran))
        return st.finish('plan only (dry run)')

    os.makedirs(os.path.join(W, 'unzipped'), exist_ok=True)
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        t = time.time()
        try:
            extract_one(p['zip'], p['part'], p['folder'])
        except Exception as e:  # noqa: BLE001
            st.gate('G1a.8', 'written = zip', 'FAIL', '%s: %s' % (p['stem'], e), 'all',
                    '%s is left as it is; move it into %s/ before the next run' % (p['part'], os.path.join(W, '_archive')))
            return st.finish()
        print('   [%2d/%d] %s  %.0f MB  %.0f s' % (i, len(todo), p['stem'], sum(p['members'].values()) / 1e6,
                                               time.time() - t))
        sys.stdout.flush()
    bad8 = []
    for p in plan:
        have = have_files(p['folder']) or {}
        wrong = [n for n, sz in p['members'].items() if have.get(n) != sz]
        if wrong:
            bad8.append('%s: %s' % (p['stem'], ', '.join(wrong)))
    st.gate('G1a.8', 'written = zip', 'FAIL' if bad8 else 'PASS', '%d of %d granules whole, %.0f s' % (
        len(plan) - len(bad8), len(plan), time.time() - t0), 'all', '\n'.join(bad8))
    gran = [dict(stem=p['stem'], date=p['date'], mode=p['mode'], width=p['width'], lines=p['lines'],
                 folder=p['folder'], members=p['members']) for p in plan]
    st.rec['outputs'] = dict(granules=gran, granules_md5=C.md5_obj(gran), extracted=len(todo),
                             reused=len(plan) - len(todo), bytes=sum(sum(p['members'].values()) for p in plan))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_extract', main)
