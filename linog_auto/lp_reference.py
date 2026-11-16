#!/usr/bin/env python3
"""lp_reference.py -- linog_auto Phase 2b: the coregistration reference (D1) and G17.

D1 (record 7.4 with Q3): among the dates of degree >= max degree - D1_DEGREE_SLACK in pass 1's network, the earliest
date excluded (invertMisreg pins it at zero, N23), the modal width first, then the date nearest the temporal
midpoint (ties: higher degree, smaller MAXBP, earlier date). The midpoint alone (no width preference) and the kit
list's first entry (degree first) are computed and recorded beside it, because the rules on record can disagree (F14).
recon/reference.txt, written by the operator, holds the choice: its first line that is not a comment reads
"YYYYMMDD <why>". Without that file, --decide auto (LINOG_DECIDE=auto) takes D1's pick, and ask (the default; D-C
for the test frame) stops with DECISION NEEDED and the table.

v0.13 (ascending record 4.7, 18.5): on an FBS+FBD frame D1 picks among the FBS dates (the network's quantities over all
dates), D1c WARNs when no FBS date is in the degree band (the highest-degree FBS date is taken), and D1f FAILs an FBD
reference, whether D1 or recon/reference.txt names it; on an FBD-only frame the rule is v0.12's and the geometry's range
looks are linog_mixed.cfg's STACK_RLKS_FBD (R6-d). LOGIC stays 1: an FBS-only frame's pick is the same.
v0.13 (R7-b, 11.7): the reference, in order: recon/reference.txt (the operator's), then the reference recon/d2_decision.json
keeps through coarse's D2 loop (either decide mode; D1's pick on the network left printed beside it), then D1's pick under
--decide auto (DECISION under ask). The kept reference enters the fingerprint only when the file exists.
v0.13 r2 (the ascending record 25.4, 25.6, 25-b): G17 reads the .slc.xml's width and lines as isce2 2.6.3 loads them,
coordinate1's and coordinate2's size (lp_xmlwidth), not its width and length properties, and FAILs a file whose fields
disagree within itself (the width property and coordinate1's size, coordinate1's endingValue or xmax against startingValue
+ size x delta): the backups' state of P448 F0280's .xml.bak9376 (the width property 9,344, coordinate1 9,376) passed the
property's reading. Where the fields agree the widths and the verdict are v0.13's; LOGIC and the fingerprint stay
(reference comes before admit).

Runs inside lp_env.sh (G17 reads the reference's shelve).
Gates
  G2b.1 stack1 PASS on record, its pass folder as it wrote it                                     FAIL
  G2b.2 environment                                                                               ERROR
  D1    the reference: the operator's recon/reference.txt, or D1's pick under --decide auto         PASS / DECISION / FAIL
  D1b   the three rules name one date                                                             WARN when not
  D1c   v0.13, an FBS+FBD frame: an FBS date in the degree band (else the highest-degree FBS date)     WARN when not
  D1f   v0.13, an FBS+FBD frame: the reference is an FBS date                                          FAIL
  G17   the reference SLC: width and lines equal in modes.json, the file size, .slc.xml (v0.13 r2: as isce2 loads it, its
        fields agreeing: 25-b), .slc.vrt (source <REF>.slc, relative to the vrt) and the shelve; the shelve's image
        SLC/<REF>/<REF>.slc                                                                          FAIL
Writes recon/reference.json (atomically, on PASS) and its status record; nothing else.
--dryrun DIR: from the dry-run stack1 record; with no reference.txt, ask mode is reported (INFO) and D1's pick is used,
so the dry run can go on to stack2. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_xmlwidth as XW

TOOLS = ('lp_reference.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py', 'lp_xmlwidth.py')   # recorded, not fingerprinted
LOGIC = 1   # raised when what this phase writes or decides changes; the lp_*.py md5s are recorded, not fingerprinted


def operator_choice(W):
    """(date, why, line, md5) from recon/reference.txt; (None, None, None, None) without it; ValueError if unreadable."""
    f = os.path.join(W, 'recon', 'reference.txt')
    if not os.path.exists(f):
        return None, None, None, None
    lines = [ln.strip() for ln in open(f, errors='replace') if ln.strip() and not ln.strip().startswith('#')]
    m = re.match(r'^(\d{8})\s+(\S.*)$', lines[0]) if lines else None
    if not m:
        raise ValueError('recon/reference.txt: the first line that is not a comment must read "YYYYMMDD <why>", got %r'
                         % (lines[0] if lines else ''))
    return m.group(1), m.group(2), lines[0], C.md5_file(f)


def g17(W, R, row):
    """Width and lines of the reference SLC as five readers see them; (ok, values, notes)."""
    import shelve
    s = os.path.join(W, 'SLC', R, R + '.slc')
    vals, notes = dict(modes=(row['width'], row['lines'])), []
    size = os.path.getsize(s) if os.path.isfile(s) else None
    rem = size % (8 * row['lines']) if size else None
    # the file's size as 8 B x width x lines: the width it gives for modes.json's line count, and that count when it divides
    vals['bytes'] = (size // (8 * row['lines']) if size else None, row['lines'] if size and rem == 0 else None)
    # v0.13 r2 (25-b): the width and lines isce2 loads (coordinate1's and coordinate2's size), the file against itself; the
    # comparison with the other readers below is the gate's own (lp_xmlwidth gets no want here)
    xw, xl, xprob = XW.check(s + '.xml')
    vals['xml'] = (xw, xl)
    notes.extend('xml: %s' % x for x in xprob)
    src = None
    try:
        v = open(s + '.vrt').read()
        vx, vy = re.search(r'rasterXSize="(\d+)"', v), re.search(r'rasterYSize="(\d+)"', v)
        vals['vrt'] = (int(vx.group(1)) if vx else None, int(vy.group(1)) if vy else None)
        src = re.search(r'<SourceFilename relativeToVRT="(\d)">([^<]*)<', v)
    except OSError as e:
        vals['vrt'] = (None, None)
        notes.append('vrt: %s' % e)
    image = None
    try:
        with shelve.open(os.path.join(W, 'SLC', R, 'data'), 'r') as db:
            f = db['frame']
        vals['shelve'] = (P2.as_int(P2.get(f, 'numberOfSamples', 'getNumberOfSamples')),
                          P2.as_int(P2.get(f, 'numberOfLines', 'getNumberOfLines')))
        fn = P2.get(P2.get(f, 'image', 'getImage'), 'filename', 'getFilename')
        image = None if fn is P2.ABSENT else fn
    except Exception as e:  # noqa: BLE001
        vals['shelve'] = (None, None)
        notes.append('shelve: %s: %s' % (type(e).__name__, str(e)[:120]))
    widths = {k: v[0] for k, v in vals.items()}
    lines = {k: v[1] for k, v in vals.items()}
    ok = len(set(widths.values())) == 1 and None not in widths.values() and rem == 0 and \
        len(set(lines.values())) == 1 and None not in lines.values() and src is not None and src.group(1) == '1' and src.group(2) == R + '.slc' and \
        image == 'SLC/%s/%s.slc' % (R, R) and not xprob
    out = dict((k, list(v)) for k, v in vals.items())
    out.update(slc_bytes=size, slc_bytes_remainder=rem, vrt_source=src.group(2) if src else None,
               vrt_relative=src.group(1) if src else None, shelve_image=image)
    return ok, out, notes


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 2b: the reference (D1) and G17')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    s = P2.load_stack()
    decide = os.environ.get('LINOG_DECIDE', 'ask')
    r1 = P1.record(recdir, '2a', 'stack1')
    rows, m_md5, _ = P2.modes_rows(W)
    looks_note = P2.fbd_only_looks(s, rows, recdir)   # v0.13, R6-d: an FBD-only frame's range looks
    rt = os.path.join(W, 'recon', 'reference.txt')
    rt_md5 = C.md5_file(rt) if os.path.exists(rt) else None
    rj = os.path.join(recdir, 'recon', 'reference.json')
    # pass 1's network, modes.json's rows, every SLC file (G17), the operator's file and the D1 settings; not the decide
    # mode: a reference on record stays when a later run asks instead of deciding (only a new choice waits for the operator)
    n1 = (r1 or {}).get('outputs', {})
    try:   # v0.13, R7 (11.7): the reference kept through coarse's D2 loop
        d2dec, _ = C.d2_decision(W)
        d2err = None
    except ValueError as e:
        d2dec, d2err = None, str(e)
    kept = (d2dec or {}).get('reference')
    fpd = dict(logic=LOGIC, network=[n1.get('dates'), n1.get('pairs_md5'), n1.get('bperp')], modes=P2.modes_digest(rows),
               slc=P2.slc_identity(W, sorted(rows)), reference_txt=rt_md5, settings=P2.settings_of(s, P2.REF_KEYS))
    if kept or d2err:   # only when present: a frame without R7's file keeps its fingerprint
        fpd['d2_reference'] = kept or 'unreadable'
    fp = C.md5_obj(fpd)
    if a.state:
        def missing(r):
            want = (r or {}).get('outputs', {}).get('reference_json_md5')
            return [] if os.path.exists(rj) and C.md5_file(rj) == want else [rj]
        print(P1.state_with_outputs(recdir, 'reference', '2b', fp, missing))
        return 0

    st = P2.LiveStatus(recdir, 'reference', '2b', path, frame)
    P1.begin(st)
    st.rec['version'] = P2.VERSION2
    st.rec.update(fingerprint=fp, logic=LOGIC, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(stack1_fp=(r1 or {}).get('fingerprint'), reference_txt=rt, reference_txt_md5=rt_md5,
                              decide=decide, modes_json_md5=m_md5, stack_cfg_md5=s['stack_cfg_md5'], looks=looks_note,
                              d2_reference=kept))
    st.write()
    print('%s  Phase 2b reference  p%s f%s  %s' % (P2.VERSION2, path, frame, C.utc()))
    print('   frame folder %s%s   decide %s' % (W, '   (DRY RUN)' if a.dryrun else '', decide))
    if decide not in ('ask', 'auto'):
        st.gate('D1', 'decide mode', 'ERROR', 'LINOG_DECIDE=%s' % decide, 'ask or auto')
        return st.finish()
    o1 = (r1 or {}).get('outputs', {})
    why = []
    if not r1 or r1.get('verdict') != 'PASS':
        why.append('stack1 %s' % ((r1 or {}).get('verdict') or 'has no record'))
    elif a.dryrun and o1.get('planned'):
        st.gate('G2b.1', 'stack1 PASS on record', 'PASS', 'dry-run stack1 was a plan only')
        print('   would choose the reference by D1 from pass 1\'s network, then G17')
        st.rec['outputs'] = dict(planned=True, dryrun=True)
        return st.finish('plan only (dry run)')
    else:
        r8 = os.path.join(o1.get('pass_dir') or '/nonexistent', 'run_files', 'run_08_igram')
        if not (os.path.isfile(r8) and C.md5_file(r8) == o1.get('run08_md5')):
            why.append('pass 1 folder %s changed or gone' % o1.get('pass_dir'))
        if sorted(rows) != o1.get('dates'):
            why.append('modes.json dates differ from pass 1\'s')
    if why:
        st.gate('G2b.1', 'stack1 PASS on record', 'FAIL', '; '.join(why))
        return st.finish()
    st.gate('G2b.1', 'stack1 PASS on record', 'PASS', '%d dates, %d pairs in %s' % (len(o1['dates']), o1['pairs'], o1['pass_dir']))
    env = P1.load_env()
    if not P2.env_gate(st, 'G2b.2', env, s):
        return st.finish()

    r = P2.d1(rows, o1['bperp'], [tuple(x) for x in o1['pair_list']], int(s['D1_DEGREE_SLACK']), float(s['NEAR_B_M']))
    P2.print_candidates(r)
    print('   D1 pick %s; the midpoint alone %s; the kit list\'s first entry %s%s' % (
        r['pick'], r['midpoint_alone'], r['kit_first'], '   (FBS+FBD: the candidates among the frame\'s %d FBS dates, 4.7)' % r['fbs']
        if r['mixed'] else ''))
    picks = dict(d1=r['pick'], midpoint_alone=r['midpoint_alone'], kit_first=r['kit_first'])
    try:
        od, owhy, oline, omd5 = operator_choice(W)
    except ValueError as e:
        st.gate('D1', 'the reference', 'FAIL', str(e), 'YYYYMMDD <why>')
        return st.finish()
    ref, by = None, None
    if d2err:
        st.gate('D1', 'the reference', 'FAIL', d2err, 'recon/d2_decision.json as coarse wrote it')
        return st.finish()
    if od:
        if od not in rows:
            st.gate('D1', 'the reference', 'FAIL', 'recon/reference.txt names %s, not a date of this stack' % od, 'a stack date')
        elif r['mixed'] and rows[od].get('mode') != 'FBS':   # v0.13, D1f
            st.gate('D1', 'the reference', 'FAIL', 'recon/reference.txt names %s, an %s date' % (od, rows[od].get('mode')),
                    'an FBS date (D1f)')
        elif od == r['earliest']:
            st.gate('D1', 'the reference', 'FAIL', 'recon/reference.txt names %s, the earliest date' % od, 'not the earliest',
                    'invertMisreg.py pins the earliest date at zero, so the datum step cannot tell a rebased tree (N23)')
        else:
            ref, by = od, 'operator'
            note = (['the operator chose another date than D1\'s pick'] if od != r['pick'] else []) + \
                (['%s is %s wide, not the modal %s' % (od, rows[od]['width'], r['modal_width'])]
                 if rows[od]['width'] != r['modal_width'] else [])
            st.gate('D1', 'the reference', 'PASS', '%s from recon/reference.txt ("%s"); D1 picks %s' % (od, owhy, r['pick']),
                    'the operator\'s choice', '; '.join(note))
    elif kept:   # v0.13, R7-b (11.7): the reference kept through coarse's D2 loop, in either decide mode
        if kept not in rows:
            st.gate('D1', 'the reference', 'FAIL', 'recon/d2_decision.json keeps %s, not a date of this stack' % kept, 'a stack date')
        elif r['mixed'] and rows[kept].get('mode') != 'FBS':
            st.gate('D1', 'the reference', 'FAIL', 'recon/d2_decision.json keeps %s, an %s date' % (kept, rows[kept].get('mode')),
                    'an FBS date (D1f)')
        elif kept == r['earliest']:
            st.gate('D1', 'the reference', 'FAIL', 'recon/d2_decision.json keeps %s, now the earliest date' % kept, 'not the earliest',
                    'invertMisreg.py pins the earliest date at zero (N23): R7\'s L4 refuses such a take; a person looks')
        else:
            ref, by = kept, 'R7'
            st.gate('D1', 'the reference', 'PASS', '%s kept through coarse\'s D2 loop (recon/d2_decision.json); D1 on this network '
                    'picks %s' % (kept, r['pick']), 'R7-b: the reference kept (11.7)',
                    '' if kept == r['pick'] else 'D1\'s pick on the network left differs; the kept reference stands, so topo and '
                    'the grid stand (11.7)')
    elif not r['pick']:
        st.gate('D1', 'the reference', 'FAIL', 'no candidate', ('an FBS date (FBS+FBD, 4.7) of ' if r['mixed'] else '')
                + 'degree >= max - %s, not the earliest date' % s['D1_DEGREE_SLACK'])
    elif decide == 'auto':
        ref, by = r['pick'], 'rule'
        st.gate('D1', 'the reference', 'PASS', '%s by D1 (--decide auto)' % ref, 'D1 with Q3')
    elif a.dryrun:
        ref, by = r['pick'], 'rule (dry run)'
        st.gate('D1', 'the reference', 'INFO', 'no recon/reference.txt: a real run in ask mode stops here with DECISION NEEDED; '
                'the dry run goes on with D1\'s pick %s' % ref, 'the operator\'s choice')
    else:
        st.gate('D1', 'the reference', 'DECISION', 'the reference is the operator\'s choice on this frame (--decide ask): '
                'D1 picks %s, the midpoint alone %s, the kit list %s' % (r['pick'], r['midpoint_alone'], r['kit_first']),
                'recon/reference.txt', 'write %s with one line "YYYYMMDD <why>" (%s, not %s), then run again'
                % (rt, 'an FBS date of this stack (FBS+FBD: D1f)' if r['mixed'] else 'a stack date', r['earliest']))
    agree = len(set(picks.values())) == 1
    kept_note = 'D1\'s pick on the network left (the kept reference %s stands, R7-b): ' % ref if by == 'R7' else ''
    st.gate('D1b', 'the three rules agree', 'INFO' if kept_note else 'PASS' if agree else 'WARN',
            kept_note + ', '.join('%s %s' % kv for kv in picks.items()),
            'one date', '' if agree else 'F14: the rules on record differ; the choice and all three are recorded')
    fbd_only = bool(rows) and all(x.get('mode') == 'FBD' for x in rows.values())
    if r['mixed'] and r.get('no_fbs'):   # the part 3 review's P3-04: no FBS reference can be had
        st.gate('D1c', 'an FBS date in the degree band', 'FAIL', 'no FBS date but the stack\'s earliest, %s (N23)' % r['earliest'],
                'an FBS date that is not the earliest', 'an FBS+FBD frame takes an FBS reference (D1f) and invertMisreg.py pins the '
                'earliest date at zero (N23): excluding the FBS date (recon/exclude.txt) runs the frame FBD-only; a person decides')
    elif r['mixed']:   # v0.13 (4.7): D1c and D1f on an FBS+FBD frame
        st.gate('D1c', 'an FBS date in the degree band', 'INFO' if kept_note else 'WARN' if r['d1c'] else 'PASS', kept_note +
                (('no FBS date has degree >= %d: the FBS dates of the highest degree, %d, the modal width first, then nearest the '
                  'midpoint: %s' % (r['max_degree'] - r['slack'], r['candidates'][0]['degree'] if r['candidates'] else 0, r['pick']))
                 if r['d1c'] else '%d FBS dates in the band' % len(r['candidates'])),
                'degree >= max - %s among the FBS dates' % s['D1_DEGREE_SLACK'],
                'on P448 F0280 the two best-connected dates were FBD (memory linog_fbsfbd_shelve_mismatch)' if r['d1c'] else '')
    elif fbd_only:   # 18.5's FBD-only row (the part 3 review's P3-05): one mode, D1 by v0.12's rule
        st.gate('D1c', 'an FBS date in the degree band', 'N/A', 'an FBD-only frame (R6-d): one mode, D1 by v0.12\'s rule')
        st.gate('D1f', 'the reference is an FBS date', 'N/A', 'an FBD-only frame (R6-d): no FBS date')
    if r['mixed']:
        named = ref or (od if od in rows else None)
        mref = rows[named].get('mode') if named else None   # D1f
        st.gate('D1f', 'the reference is an FBS date', 'N/A' if not named else 'PASS' if mref == 'FBS' else 'FAIL',
                '%s, %s' % (named, mref) if named else 'no reference named yet',
                'FBS (a 4640-wide grid was decided against, 24 Aug; memory linog_fbsfbd_shelve_mismatch)')
        if ref and mref != 'FBS':
            ref = None
    st.rec['outputs'] = dict(picks=picks, candidates=r['candidates'], tmid=r['tmid'], modal_width=r['modal_width'],
                             max_degree=r['max_degree'], min_degree=r['min_degree'], earliest=r['earliest'], mixed=r['mixed'],
                             d1c=r['d1c'], no_fbs=r.get('no_fbs'), looks=looks_note)
    if not ref:
        return st.finish()

    ok, vals, notes = g17(W, ref, rows[ref])
    st.gate('G17', 'the reference SLC', 'PASS' if ok else 'FAIL', '%s: %s' % (ref, ', '.join(
        '%s %s x %s' % (k, v[0], v[1]) for k, v in vals.items() if isinstance(v, list))),
        'one width and one line count; size = 8 B x width x lines; vrt source <REF>.slc relative; image SLC/<REF>/<REF>.slc',
        'size %s B (remainder %s); vrt source %s (relativeToVRT %s); shelve image %s%s' % (
            vals['slc_bytes'], vals['slc_bytes_remainder'], vals['vrt_source'], vals['vrt_relative'], vals['shelve_image'],
            ('\n' + '\n'.join(notes)) if notes else ''))
    if not ok:
        return st.finish()
    rl, al = int(s['STACK_RLKS']), int(s['STACK_ALKS'])
    geom = dict(width=rows[ref]['width'] // rl, length=rows[ref]['lines'] // al, rlks=rl, alks=al)
    out = dict(version=P2.VERSION2, created=C.utc(), path=path, frame=frame, reference=ref, decided_by=by, decide=decide,
               operator=dict(line=oline, why=owhy, file_md5=omd5) if od else None, picks=picks, candidates=r['candidates'],
               tmid=r['tmid'], modal_width=r['modal_width'], max_degree=r['max_degree'], g17=vals, geometry=geom,
               stack1_fingerprint=r1.get('fingerprint'), pass1_dir=o1['pass_dir'], dryrun=bool(a.dryrun))
    m5 = P2.write_json(rj, out)
    print('   reference %s (%s); geometry %d x %d (Rule 4: int(width/%d) x int(lines/%d)); %s md5 %s' % (
        ref, by, geom['width'], geom['length'], rl, al, rj, m5))
    st.rec['outputs'].update(reference=ref, decided_by=by, geometry=geom, reference_json=rj, reference_json_md5=m5)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_reference', main)
