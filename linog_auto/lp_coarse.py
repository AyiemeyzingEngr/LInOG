#!/usr/bin/env python3
"""lp_coarse.py -- linog_auto Phase 3b: run_02_focus_split and run_03_geo2rdr_coarseResamp, then G21 and G7.

Runs inside lp_env.sh. run_02's configs hold only [Common] on a --nofocus stack (nothing to run; the 12 frames ran it
at 0 s); run_03 puts every secondary on the reference grid through the DEM geometry: offsets/<date>/range.off and
azimuth.off (float64) and coregSLC/Coarse/<date>/<date>.slc, 8 B x W x L each. Then the kit's two registration gates,
from the frame folder: G21 (linog_frame_align_gate.py: a granule centred away from the frame along track reads its
median |azimuth.off| far above the frame's) and G7 v4 (linog_coarse_reg_gate.py <REF> --reselect: residual offsets at
textured windows; N53, a one-gate (32-sample) range shift of a date in resampleSecondary, shows here).
geo2rdr's log counts (its "valid data", "outside the image" and "converged" totals) are not read: it adds to them inside
a parallel loop with no reduction, as topozero does (F61, F65; record 80.3), so they are lower bounds that change from
run to run. Its offsets do not: S25 found run_03's 69 products of I4 and of the delivered frame byte-identical (record 81).
v0.13 (the ascending record 17.4): G3b.12 reads G10 v3's measurement on the coarse products after G7 (lp_reg3.py; its md5 in
the record's tools, not the fingerprint), INFO: each date's shift against the reference's own SLC, the coarse
misregistration R9 then removes, for the test root's predictions (17.10) and R9's check.

D2 (record 7.4; v0.13 R7, the ascending record 11.2 to 11.7 and 18.4): F, the dates G21 flags with the dates G7 calls out,
measured flags only (a G21 row with no ratio, or a G7 call-out that a majority of the voting windows makes only by reading
EMPTY, READERR or MISSING, is v0.12's D2 DECISION, and R7 takes nothing; so is G7 below its quorum, and an ERROR stays an
ERROR). Under --decide auto, in a run of the driver without --only (LINOG_RESTART=allowed, read here before anything
moves), R7 takes F when its limits hold, L0 to L8 (r7_limits); then, under the signal hold, F's traces move into
_archive/d2_<UTC>/ (MOVES.txt names each move before it is made: raw/<zip>, unzipped/<stem>/, SLC/<d>/, offsets/<d>/,
coregSLC/Coarse/<d>/ by date, and stack2's configs/, run_files/, baselines/ and pairs.pdf), recon/d2_decision.json takes the
loop (N0, the reference kept, each date's granule, mode, readings and rwin record, the limits; written to a temporary name
and put in place), and status/restart.json asks the driver to run the frame again from the top; G21 and G7 then read INFO
("taken by R7, loop n"), G3b.11 PASS and D2 INFO, so the phase PASSes and the restart is read. recon drops F's granules
(G0.4d), the reference phase keeps the reference, and this phase reuses the other dates' products (G3b.6 below). One loop by
itself: a second needs the operator's take, and there is no third. Under --decide ask, D2 is a DECISION with R7's proposal.
recon/d2.txt (either mode, its md5 in the fingerprint): "take <dates>" is R7's take by the operator (L2 may be passed, with a
WARN); "keep <dates>" keeps the flagged dates (G21, G7 and D2 INFO, the phase PASSes); a line naming another set than F is
not applied (WARN): the DECISION stays under ask, R7 decides as if the file were absent under auto.
G3b.6 (11.5): offsets/ and coregSLC/ in the frame are this phase's own when its previous record (read before this run's
replaces it; v0.13's, not RUNNING, G3b.8 to G3b.10 PASS) lists every current secondary with its files as listed, the folders
hold no other date, and each current secondary's run_02 and run_03 config md5, the SLC identity of each secondary and of the
reference, the reference date, topo's digest and the md5s of stripmapWrapper.py, geo2rdr.py and resampleSlc.py are the
recorded ones: then run_02 and run_03 are not run (G3b.8 and G3b.9 carried as PASS), and G3b.10, G21 and G7 read the
products again; otherwise products present is a DECISION, as v0.12 (a v0.12 record never qualifies).

Gates
  G3b.1  topo PASS on record, its outputs as it recorded them                                        FAIL
  G3b.2  environment                                                                                  ERROR
  G3b.3  stripmapWrapper.py, geo2rdr.py, resampleSlc.py and the kit's G21, G7, linog_reg_common at their pins   FAIL
  G3b.4  the run files' command resolves to the pinned env's stripmapStack (F13)                      FAIL
  G3b.5  the run files: run_02 and run_03 one line per secondary (the stack's dates without <REF>), run_02's
         configs without a function (--nofocus), run_03's naming SLC/<REF>, offsets/<d>, coregSLC/Coarse/<d>  FAIL
  G3b.6  nothing in the way: offsets/, coregSLC/ absent, or this phase's own by the reuse rule (v0.13)   DECISION
  G3b.7  disk: free >= 3 x 8 B x W x L per secondary + disk_gib_margin                                  FAIL
  G3b.8  run_02: rc 0 on every line                                                                    FAIL
  G3b.9  run_03: rc 0 on every line                                                                    FAIL
  G3b.10 per secondary: offsets range.off and azimuth.off 8 B x W x L with .xml; the coarse SLC 8 B x W x L
         with .xml; referenceShelve/ and secondaryShelve/ with data.dat                                 FAIL
  G21    the kit's frame alignment: every date's median |azimuth.off| within 5x the frame's           DECISION (D2) / INFO (R7)
  G21e   (v0.13, 11.7 option (d)) G21's printed reference is a hand reading                           INFO
  G7     the kit's coarse registration: no date called out by a majority of the voting windows;
         fewer windows than the quorum: the survey once more at depth G7_NCAND_RETRY      DECISION (D2) / INFO (R7) / ERROR
  G3b.12 (v0.13) G10 v3 on the coarse products: each date's dx and dy, the modes' offset                INFO
  G3b.11 (v0.13, R7) the take: the moves, the decision, the restart asked                             PASS / FAIL
  D2t    (v0.13) recon/d2.txt naming another set than the flags: not applied                         WARN
  D2w    (v0.13) a limit (L2) passed by the operator's take                                            WARN
  D2     a flagged date: R7's take or the operator's keep (INFO), else DECISION with R7's proposal  INFO / DECISION
--dryrun DIR: a plan only (no G21 or G7, so no R7). Exit 0 PASS (WARN included), 2 FAIL, 3 ERROR, 4 DECISION.
Self-test only (under a path table other than the package's own, lp_common.selftest_hook): LINOG_MOCK_D2FLAG=<loop>:<dates>
adds those dates to F, as G7 call-outs, in that loop; LINOG_MOCK_D2TAG=<tag> names the archive folder d2_<tag>;
LINOG_MOCK_D2FAILAT=<n> fails the take's n-th move; LINOG_MOCK_D2SLEEP=<s> holds the take that long after its first move,
writing LINOG_MOCK_MARK first.
"""
import argparse
import json
import os
import re
import shutil
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3

PHASE, IDX, LOGIC = 'coarse', '3b', 1
RUNS = ('run_02_focus_split', 'run_03_geo2rdr_coarseResamp')
KIT = ('linog_frame_align_gate.py', 'linog_coarse_reg_gate.py', 'linog_reg_common.py')
REUSE_TOOLS = ('stripmapWrapper.py', 'geo2rdr.py', 'resampleSlc.py')   # 11.5 (d): what run_02 and run_03 run
RESTART_FILE = os.path.join('status', 'restart.json')
STACK2_OUT = ('configs', 'run_files', 'baselines', 'pairs.pdf')        # 11.3 step 4: stack2 makes them again
LATER = ('refineSecondaryTiming/pairs', 'refineSecondaryTiming/dates', 'refineSecondaryTiming/dates_predatum_bak_*',
         'merged/SLC', 'merged/baselines', 'Igrams', 'mintpy')        # L5: a tree past coarse
UNREAD = ('EMPTY', 'READERR', 'MISSING')                               # G7 cells that count against a date unmeasured
G21E = ('G21\'s printed reference ("p447 f0310 read 103x on 20101213; its worst healthy ratio was 2.45x") is a hand reading: '
        'by G21\'s own method on the delivered offsets, P447 F0310\'s 20101213 reads 82.5x and the frame\'s worst other date '
        '2.16x (the ascending record 8 and 9.1)')


# ------------------------------------------------------------------------------------------------ G3b.6, the reuse rule
def cfg_md5s(W, lines):
    """{date: md5 of the config its run-file line names} (11.5 (d))."""
    out = {}
    for x in lines or []:
        c = P3.cfg_of(x)
        out[P3.tag_of(x)] = C.md5_file(c) if c and os.path.isfile(c) else None
    return out


def reuse_data(W, s3, ref, topo_digest, tm, L2, L3):
    """What a later run's reuse rule compares (11.5 (d)), recorded at G3b.10."""
    c2, c3 = cfg_md5s(W, L2), cfg_md5s(W, L3)
    return dict(v13=True, cfgs=dict((d, [c2.get(d), c3.get(d)]) for d in s3), slc=dict((d, P3.slc_identity(W, [d])) for d in
                list(s3) + [ref]), reference=ref, topo=topo_digest, tools=dict((n, tm[n][1]) for n in REUSE_TOOLS))


def reuse_check(W, own0, s3, ref, topo_digest, tm, L2, L3):
    """11.5's rule: (True, how) when offsets/ and coregSLC/ are this phase's own, else (False, [why])."""
    why = []
    if not own0:
        return False, ['no earlier record of this phase']
    o = own0.get('outputs') or {}
    rz = o.get('reuse') or {}
    g = dict((x['id'], x['verdict']) for x in own0.get('gates', []))
    if own0.get('verdict') == 'RUNNING':
        why.append('its earlier record is RUNNING (that run ended before its END)')
    if not rz.get('v13'):
        why.append('its earlier record holds no config md5s (v0.12\'s, or a run that ended before G3b.10)')
    why += ['%s %s on the earlier record' % (k, g.get(k)) for k in ('G3b.8', 'G3b.9', 'G3b.10') if g.get(k) != 'PASS']
    if why:
        return False, why
    listed = dict((x[0], tuple(x[1:])) for x in o.get('files') or [])
    now = dict((x[0], tuple(x[1:])) for x in P3.listing(W, P3.OUTS[PHASE]))
    for d in s3:
        mine = [k for k in set(listed) | set(now) if k.startswith('offsets/%s/' % d) or k.startswith('coregSLC/Coarse/%s/' % d)]
        if not any(k in listed for k in mine):
            why.append('%s: not in the earlier record\'s listing' % d)
            continue
        ch = sorted(k for k in mine if listed.get(k) != now.get(k))
        if ch:
            why.append('%s: %s %s since the earlier record' % (d, ', '.join(ch[:3]), 'changed, added or gone'))
    held = set()
    for top in ('offsets', os.path.join('coregSLC', 'Coarse')):
        p = os.path.join(W, top)
        held |= set(os.listdir(p)) if os.path.isdir(p) else set()
    other = sorted(held - set(s3))
    if other:
        why.append('offsets/ or coregSLC/Coarse/ hold other entries: %s' % ', '.join(other[:6]))
    cur = reuse_data(W, s3, ref, topo_digest, tm, L2, L3)
    why += ['%s: its run_02 or run_03 config changed' % d for d in s3 if (rz.get('cfgs') or {}).get(d) != cur['cfgs'][d]]
    why += ['%s: its SLC identity changed (the .slc, .xml, .vrt or shelve)' % d for d in cur['slc']
            if (rz.get('slc') or {}).get(d) != cur['slc'][d]]
    if rz.get('reference') != ref:
        why.append('the reference %s, recorded %s' % (ref, rz.get('reference')))
    if rz.get('topo') != topo_digest:
        why.append('topo\'s digest changed')
    if rz.get('tools') != cur['tools']:
        why.append('stripmapWrapper.py, geo2rdr.py or resampleSlc.py changed')
    return (not why), why


# ------------------------------------------------------------------------------------------------ R7 (11.2 to 11.6)
def g21_rows(out):
    """{date: (row, measured)} of G21's flagged rows: measured when the row carries its ratio (OFF-FRAME)."""
    rows = {}
    for d, row in (P3.g21_verdict(out).get('flagged') or {}).items():
        rows[d] = (row, 'OFF-FRAME' in row)
    return rows


G7_CELL = re.compile(r'(%s)|([+-]\d+\.\d)\s*([+-]\d+\.\d)(!?)' % '|'.join(UNREAD))   # "%+5.1f%+6.1f%s": glued past 999.9


def g21_nums(row):
    """(the date's median |az|, its ratio to the frame's) from a G21 row that carries them, else (None, None)."""
    t = row.split()
    try:
        return float(t[1]), float(t[2].rstrip('x'))
    except (IndexError, ValueError):
        return None, None


def way_on(ids, loops, operator, F, W):
    """The D2 DECISION's way on when R7's limits fail (the part 5 review's P5-02): a new run where only L0 fails; the
    operator's take where L1 (a second loop) or L2 is what fails (11.6); else keep, or by hand (11.1)."""
    f = ' '.join(F)
    d2 = os.path.join(W, C.D2_TXT)
    if ids == {'L0'}:
        return ('the way on: run the frame again without --only (L0: this run cannot restart): under --decide auto R7 then takes '
                'them, as the operator\'s "take %s" in %s does under either mode (11.6)' % (f, d2))
    if ids <= {'L0', 'L1', 'L2'} and loops < 2 and not operator:
        what = ' and '.join(x for x, y in (('makes the second loop (L1)', 'L1' in ids), ('passes L2 with a WARN', 'L2' in ids),
                                           ('in a new run (L0)', 'L0' in ids)) if y)
        return ('the way on: the operator\'s take (11.6) %s: write the one line "take %s" into %s and run again without --only; '
                '"keep %s" keeps them' % (what, f, d2, f))
    return 'a person decides: recon/d2.txt "keep %s" keeps them; anything else is by hand (11.1)' % f


def g7_calls(out):
    """{date: dict(tot, meas, bang, unread, cells, raw, raw_dx)} of the kit's G7 rows: a measured cell is the residual dy
    and dx against the voting window's median, the second with '!' when the window calls the date out; EMPTY, READERR and
    MISSING count against the date unmeasured. raw: per voting window (the table's columns, in order) the residual plus
    the window's printed median, the date's own offset ([dy, dx], None where unread); raw_dx their median dx (18.4's line)."""
    med, voting, calls = {}, [], {}
    for ln in out.splitlines():
        m = re.match(r'^\s*window (\d+)\s+row \d+\s+col \d+\s+DEMstd \S+\s+median ratio \S+\s+median dy ([+-]\d+\.\d) dx '
                     r'([+-]\d+\.\d)', ln)
        if m:
            med[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
        m = re.match(r'^  DATE((?:\s+w\d+)+)\s+sprY', ln)
        if m:
            voting = [int(x[1:]) for x in m.group(1).split()]
    for ln in out.splitlines():
        m = re.match(r'^  (\d{8})  (.*?)\s+(\d+)\s+(\d+)\s+(\S+)\s+(FAIL|ok)\s*$', ln)
        if not m:
            continue
        cells = list(G7_CELL.finditer(m.group(2)))
        meas = [c for c in cells if c.group(1) is None]
        raw = []
        for i, c in enumerate(cells):
            w = voting[i] if i < len(voting) else None
            raw.append([round(float(c.group(2)) + med[w][0], 1), round(float(c.group(3)) + med[w][1], 1)]
                       if c.group(1) is None and w in med else None)
        rx = sorted(x[1] for x in raw if x)
        calls[m.group(1)] = dict(tot=len(cells), meas=len(meas), unread=len(cells) - len(meas), bang=sum(1 for c in meas if c.group(4)),
                                 verdict=m.group(6), cells=' '.join(m.group(2).split()), raw=raw,
                                 raw_dx=(rx[len(rx) // 2] if len(rx) % 2 else 0.5 * (rx[len(rx) // 2 - 1] + rx[len(rx) // 2])) if rx
                                 else None)
    return calls


def r7_limits(W, F, ref, dec0, dates, modes, pairs1, min_dates, frac, operator):
    """11.3's limits, read before anything moves: [dict(id, ok, warn, text)]. dates: the frame's dates now; pairs1: stack1's
    recorded pair list; operator: the take is the operator's (recon/d2.txt)."""
    loops = len((dec0 or {}).get('loops') or [])
    prev = sorted(C.d2_dates(dec0))
    n0 = (dec0 or {}).get('N0') or len(dates)
    left = sorted(d for d in dates if d not in F)
    out = []

    def lim(i, ok, text, warn=False):
        out.append(dict(id=i, ok=bool(ok), warn=bool(warn), text=text))
    lim('L0', os.environ.get('LINOG_RESTART') == 'allowed', 'LINOG_RESTART=%s: %s' % (
        os.environ.get('LINOG_RESTART'), 'the driver will run the frame again' if os.environ.get('LINOG_RESTART') == 'allowed'
        else 'no restart in this run (--only, or this phase asked one already): the moves would leave a frame no run goes on with'))
    lim('L1', loops < (2 if operator else 1), '%d loop(s) on record; %s' % (
        loops, 'the operator\'s take may make the second, never a third' if operator else 'R7 takes the first only (R7-a)'))
    n7 = len(prev) + len(F)
    ok2 = n7 <= frac * n0 + 1e-9
    lim('L2', ok2 or operator, '%d of N0 %d dates over all loops (%.1f %%), the limit %g %% (ADMIT_EXCL_MAX_FRAC)%s' % (
        n7, n0, 100.0 * n7 / max(n0, 1), 100 * frac, '' if ok2 else '; passed by the operator\'s take' if operator else ''),
        warn=operator and not ok2)
    lim('L3', len(left) >= min_dates, '%d dates left, min_dates %d' % (len(left), min_dates))
    early = left[0] if left else None
    lim('L4', ref not in F and ref != early, 'the reference %s %s' % (ref, 'among the flagged dates' if ref in F else
                                                                        'would be the earliest date left (N23)' if ref == early
                                                                        else 'kept, not the earliest date left'))
    later = [x for x in LATER if P3.present(W, [x])]
    lim('L5', not later, 'later phases\' outputs in the frame: %s' % (', '.join(later) or 'none'))
    lim('L6', True, '')   # filled by r7_paths
    net = [tuple(p) for p in pairs1 or [] if p[0] not in F and p[1] not in F]
    deg = dict((d, 0) for d in left)
    for a, b in net:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    comps = P3.network_components(left, net)
    thin = sorted(d for d in left if deg.get(d, 0) < 2)
    lim('L7', len(comps) == 1 and not thin, 'stack1\'s %d pairs less F\'s leave %d in %d component(s); dates in fewer than 2 pairs: '
        '%s' % (len(pairs1 or []), len(net), len(comps), ', '.join(thin) or 'none'))
    ms = set(modes.get(d) for d in dates)
    ml = set(modes.get(d) for d in left)
    nomode = sorted(d for d in dates if modes.get(d) not in ('FBS', 'FBD'))   # the part 5 review's P5-10
    lim('L8', not nomode and not ({'FBS', 'FBD'} <= ms and 'FBD' not in ml), 'the branch %s, after the take %s%s' % (
        '+'.join(sorted(m for m in ms if m)), '+'.join(sorted(m for m in ml if m)),
        '; no mode in recon/modes.json for %s' % ', '.join(nomode) if nomode else ''))
    return out


def r7_paths(W, F, R, tag):
    """The take's moves (11.3 steps 3 and 4): [(src, dst)] relative to W, and L6's findings."""
    kept = dict((k.get('date'), k) for k in R.get('kept') or [])
    adir = os.path.join('_archive', 'd2_%s' % tag)
    moves, bad = [], []
    if os.path.lexists(os.path.join(W, adir)):
        bad.append('%s exists already' % adir)
    arch = os.path.join(W, '_archive')
    if os.path.lexists(arch) and (os.path.islink(arch) or not os.path.isdir(arch)):   # the part 5 review's P5-03
        bad.append('_archive is not a folder of the frame (%s)' % ('a link' if os.path.islink(arch) else 'a file'))
    elif os.path.isdir(arch) and os.stat(arch).st_dev != os.stat(W).st_dev:
        bad.append('_archive/ is on another filesystem than the frame: the moves would be copies')
    for d in sorted(F):
        k = kept.get(d)
        if not k:
            bad.append('%s: not among recon/RECON.json\'s kept granules' % d)
            continue
        z = os.path.basename(k.get('zip') or '')
        for rel, kind in ((os.path.join('raw', z), 'link'), (os.path.join('unzipped', P1.stem(z)), 'dir'), (os.path.join('SLC', d), 'dir'),
                          (os.path.join('offsets', d), 'dir'), (os.path.join('coregSLC', 'Coarse', d), 'dir')):
            p = os.path.join(W, rel)
            ok = os.path.islink(p) if kind == 'link' else (os.path.isdir(p) and not os.path.islink(p))
            if not ok:
                bad.append('%s: %s' % (rel, 'absent' if not os.path.lexists(p) else 'not a %s' % ('link' if kind == 'link' else 'folder')))
                continue
            moves.append((rel, os.path.join(adir, d, rel)))
    for rel in STACK2_OUT:
        p = os.path.join(W, rel)
        if not os.path.lexists(p):
            if rel != 'pairs.pdf':
                bad.append('%s: absent (stack2 made it)' % rel)
            continue
        if os.path.islink(p) or (rel != 'pairs.pdf' and not os.path.isdir(p)):
            bad.append('%s: not a folder' % rel)
            continue
        moves.append((rel, os.path.join(adir, 'stack2', rel)))
    return adir, moves, bad


class TakeError(Exception):
    """The take stopped by an error: n, the moves made before it (MOVES.txt names each)."""

    def __init__(self, n, err):
        Exception.__init__(self, '%s: %s (after %d move(s) of the take)' % (type(err).__name__, err, n))
        self.n = n


def r7_take(W, adir, moves, dec0, loop, failat=None, sleep=None):
    """11.3's take, steps 1 to 6, under the signal hold: MOVES.txt, the earlier decision copied, the moves (renames), the
    decision put in place, status/restart.json. Returns (decision_md5, n_moved); raises TakeError with the moves made, which
    MOVES.txt names, its last line the failure."""
    ad = os.path.join(W, adir)
    mv = os.path.join(ad, 'MOVES.txt')
    n = 0
    try:   # the part 5 review's P5-03: a failure before the first move is the take's too, with 0 moves
        os.makedirs(ad)
        fh = open(mv, 'w')
    except Exception as e:  # noqa: BLE001
        raise TakeError(0, e)
    with fh:
        try:
            fh.write('# R7 (lp_coarse.py, the ascending record 11.3), loop %d, %s: each line written before its rename\n' % (
                loop['loop'], loop['utc']))
            fh.flush()
            if dec0 is not None:
                fh.write('copy %s -> %s\n' % (C.D2_DECISION, os.path.join(adir, 'd2_decision_before.json')))
                fh.flush()
                shutil.copy2(os.path.join(W, C.D2_DECISION), os.path.join(ad, 'd2_decision_before.json'))
            for src, dst in moves:
                fh.write('mv %s -> %s\n' % (src, dst))
                fh.flush()
                os.fsync(fh.fileno())
                if failat is not None and n + 1 == failat:
                    raise OSError('self-test: the take\'s move %d made to fail (LINOG_MOCK_D2FAILAT)' % failat)
                os.makedirs(os.path.dirname(os.path.join(W, dst)), exist_ok=True)
                os.rename(os.path.join(W, src), os.path.join(W, dst))
                n += 1
                if sleep and n == 1:
                    if os.environ.get('LINOG_MOCK_MARK'):
                        with open(os.environ['LINOG_MOCK_MARK'], 'w') as mk:
                            mk.write('the take held %s s\n' % sleep)
                    time.sleep(float(sleep))
        except Exception as e:  # noqa: BLE001
            try:
                fh.write('# FAILED at the line above: %s: %s; %d move(s) made, nothing deleted\n' % (type(e).__name__, e, n))
            except Exception:  # noqa: BLE001  (MOVES.txt itself unwritable: the error says so)
                pass
            raise TakeError(n, e)
        fh.write('# %d moves made\n' % n)
    dec = dict(version=C.VERSION, N0=(dec0 or {}).get('N0') or loop['n_before'], reference=loop['reference'],
               loops=list((dec0 or {}).get('loops') or []) + [loop])
    dec['dates'] = sorted(C.d2_dates(dec))
    df = os.path.join(W, C.D2_DECISION)
    with open(df + '.tmp', 'w') as fh:
        json.dump(dec, fh, indent=1, sort_keys=True)
        fh.write('\n')
        fh.flush()
        os.fsync(fh.fileno())   # the part 5 review's P5-17: the decision whole on disk before it takes the name
    os.replace(df + '.tmp', df)
    md = C.md5_file(df)
    with open(os.path.join(W, RESTART_FILE) + '.tmp', 'w') as fh:
        json.dump(dict(from_phase='recon', by='coarse', reason='R7 (D2), loop %d: %d date(s) taken (%s); their traces in %s' % (
            loop['loop'], len(loop['dates']), ', '.join(sorted(loop['dates'])), adir), decision=C.D2_DECISION, decision_md5=md,
            written=C.utc()), fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(os.path.join(W, RESTART_FILE) + '.tmp', os.path.join(W, RESTART_FILE))
    return md, n


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 3b: run_02, run_03, G21, G7, R7')
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
    tm = P3.tools(s, env, r, isce=('stripmapWrapper.py', 'geo2rdr.py', 'resampleSlc.py'), kit=KIT)
    geo, _ = P3.geometry(recdir)
    ref = (geo or {}).get('ref')
    rt = P1.record(recdir, '3a', 'topo') or {}
    r2 = P1.record(recdir, '2c', 'stack2') or {}
    wd = r2.get('outputs', {}).get('workdir') or W
    secs = sorted(P3.tag_of(x) for x in (P3.run_lines(W, RUNS[1]) or []))
    fpd = dict(logic=LOGIC, reference=ref, topo=rt.get('outputs', {}).get('digest'), runs=P3.runfile_md5s(W, RUNS),
               slc=P3.slc_identity(W, sorted(set(secs + ([ref] if ref else [])))),
               tools={k: v[1] for k, v in tm.items()}, settings={k: r[k] for k in ('G7_NCAND_RETRY',)})
    for k, rel in (('d2_txt', C.D2_TXT), ('d2_decision', C.D2_DECISION)):   # v0.13, R7: only when present (11.5, 11.6)
        if os.path.isfile(os.path.join(W, rel)):
            fpd[k] = C.md5_file(os.path.join(W, rel))
    fp = C.md5_obj(fpd)
    if a.state:
        def missing(rec):
            return P3.listing_changed(W, P3.OUTS[PHASE], (rec or {}).get('outputs', {}).get('files'))
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    own0 = P1.record(recdir, IDX, PHASE) or {}   # v0.13 (11.5 (a)): read before this run's record replaces it
    st = P3.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(run_cfg=r['run_cfg_file'], run_cfg_md5=r['run_cfg_md5'],
                  settings={k: r[k] for k in ('R02_J', 'R02_OMP', 'R03_J', 'R03_OMP', 'R03_PEAK_KB', 'G7_NCAND_RETRY')},
                  tools={k: dict(path=v[0], md5=v[1]) for k, v in tm.items()}), a.dryrun)
    P3.header(PHASE, IDX, path, frame, W, a.dryrun)
    rt = P3.prior3(st, 'G3b.1', recdir, '3a', 'topo')
    if not rt:
        return st.finish()
    planned = rt.get('outputs', {}).get('planned')
    if planned:
        st.gate('G3b.1', 'topo PASS on record', 'PASS', 'dry-run topo was a plan only')
    else:
        ch = P3.listing_changed(W, P3.OUTS['topo'], rt['outputs'].get('files'))
        if not geo:
            ch.append('recon/reference.json gives no reference geometry')
        st.gate('G3b.1', 'topo PASS on record', 'FAIL' if ch else 'PASS', '; '.join(ch[:5]) or
                'merged/geom_reference and geom_reference as topo recorded them (%d files)' % len(rt['outputs'].get('files', [])))
        if ch:
            return st.finish()
    if not P2.env_gate(st, 'G3b.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G3b.3', tm, 'run_03\'s scripts and the kit\'s G21 and G7'):
        return st.finish()
    jenv = P3.job_env(s, r, 'R03', os.path.join(recdir, 'logs', 'p3', 'mplconfig'))
    if not P3.which_gate(st, 'G3b.4', s, jenv, P3.RUN[RUNS[1]][1]):
        return st.finish()
    if planned:
        return P3.plan_only(st, {n: P3.run_lines(wd, n) for n in RUNS}, 'after a planned topo')

    L2, L3 = P3.run_lines(wd, RUNS[0]) or [], P3.run_lines(wd, RUNS[1]) or []
    s2, s3 = [P3.tag_of(x) for x in L2], [P3.tag_of(x) for x in L3]
    ndates = r2.get('outputs', {}).get('dates')
    bad = []
    if sorted(s2) != sorted(s3) or len(set(s3)) != len(s3) or ref in s3:
        bad.append('run_02 names %s, run_03 %s (reference %s)' % (s2, s3, ref))
    if ndates is not None and len(s3) != ndates - 1:
        bad.append('%d secondaries, stack2 recorded %s dates' % (len(s3), ndates))
    for x in L2:
        c = P3.cfg_of(x)
        if not c or not os.path.isfile(c) or '[Function' in open(c).read():
            bad.append('%s: not a --nofocus focus_split config (a function inside, or missing)' % c)
    for x, d in zip(L3, s3):
        k = P3.cfg_kv(P3.cfg_of(x))
        want = dict(reference=os.path.join(W, 'SLC', ref), secondary=os.path.join(W, 'SLC', d),
                    outdir=os.path.join(W, 'offsets', d), coreg=os.path.join(W, 'coregSLC', 'Coarse', d))
        diff = ['%s %s' % (kk, k.get(kk)) for kk, vv in want.items() if k.get(kk) != vv]
        if diff:
            bad.append('%s: %s' % (os.path.basename(P3.cfg_of(x) or '?'), '; '.join(diff)))
    st.gate('G3b.5', 'the run files', 'FAIL' if bad else 'PASS', 'run_02 %d lines (configs empty, --nofocus), run_03 %d lines; '
            'reference %s' % (len(L2), len(L3), ref), 'one line per secondary; SLC/<REF>, offsets/<d>, coregSLC/Coarse/<d>',
            '\n'.join(bad[:10]))
    if bad:
        return st.finish()
    Wd, L = geo['width'], geo['lines']
    need = len(s3) * 3 * 8 * Wd * L
    if a.dryrun:
        P3.way_gate(st, 'G3b.6', W, PHASE, True)
        print('   run_03 would write about %.1f GiB (%d secondaries x 3 x %d B)' % (P3.gib(need), len(s3), 8 * Wd * L))
        return P3.plan_only(st, {RUNS[0]: L2, RUNS[1]: L3}, 'coarse')
    topo_digest = (rt.get('outputs') or {}).get('digest')
    reused = False
    if P3.present(W, P3.OUTS[PHASE]):   # v0.13 (11.5): this phase's own products, reused, or in the way as v0.12
        ok, why = reuse_check(W, own0, s3, ref, topo_digest, tm, L2, L3)
        if not ok:
            own, later = P3.in_the_way(W, PHASE)
            st.gate('G3b.6', 'nothing in the way', 'DECISION', 'in the frame already: %s%s' % (
                ', '.join(own), ('; and later phases\': %s' % ', '.join(later)) if later else ''), ', '.join(P3.OUTS[PHASE]) +
                ' absent, or this phase\'s own by 11.5\'s rule', 'not this phase\'s own by the reuse rule: %s\na refused reuse is final '
                '(the next run reads this record, which lists no products: 11.5 (a)): move offsets/ and coregSLC/ (and the later '
                'phases\' outputs listed) into %s/_archive/ and run again; run_02 and run_03 make them anew' % ('; '.join(why[:6]), W))
            return st.finish()
        reused = True
        st.gate('G3b.6', 'nothing in the way', 'PASS', 'offsets/ and coregSLC/ are this phase\'s own (the run of %s, %s): run_02 and '
                'run_03 not run; G3b.10, G21 and G7 read them again (11.5)' % (own0.get('start'), own0.get('verdict')),
                'absent, or this phase\'s own by 11.5\'s rule')
    else:
        st.gate('G3b.6', 'nothing in the way', 'PASS', '%s absent' % ', '.join(P3.OUTS[PHASE]), 'all absent')
    logroot = P2.new_dir(os.path.join(recdir, 'logs', 'p3', PHASE))
    st.rec['outputs'] = dict(logdir=logroot, steps={})
    if reused:
        o0 = own0.get('outputs') or {}
        for gid, n in (('G3b.8', RUNS[0]), ('G3b.9', RUNS[1])):
            st.gate(gid, '%s rc 0' % n, 'PASS', 'not run: the products of the run of %s reused (G3b.6)' % own0.get('start'),
                    'rc 0 on every line')
        st.rec['outputs'].update(steps=o0.get('steps') or {}, reused_from=dict(start=own0.get('start'), verdict=own0.get('verdict'),
                                                                               pid=own0.get('pid')))
    else:
        if not P3.disk_gate(st, 'G3b.7', W, need, float(cfg.get('disk_gib_margin', 0))):
            return st.finish()
        for gid, n, ls in (('G3b.8', RUNS[0], L2), ('G3b.9', RUNS[1], L3)):
            ok, summ, _ = P3.run_step(st, gid, W, s, r, n, ls, logroot, logroot, 'coarse')
            st.rec['outputs']['steps'][n] = summ
            if not ok:
                return st.finish()
    B = 8 * Wd * L
    specs = []
    for d in s3:
        specs += [('offsets/%s/range.off' % d, B), ('offsets/%s/range.off.xml' % d, None), ('offsets/%s/azimuth.off' % d, B),
                  ('offsets/%s/azimuth.off.xml' % d, None), ('coregSLC/Coarse/%s/%s.slc' % (d, d), B),
                  ('coregSLC/Coarse/%s/%s.slc.xml' % (d, d), None), ('coregSLC/Coarse/%s/referenceShelve/data.dat' % d, None),
                  ('coregSLC/Coarse/%s/secondaryShelve/data.dat' % d, None)]
    bad = P3.expect(W, specs)
    st.gate('G3b.10', 'offsets and coarse SLCs', 'FAIL' if bad else 'PASS', '%d secondaries: range.off, azimuth.off and the coarse '
            'SLC at %d B each, with .xml and both shelves' % (len(s3), B), '8 B x %d x %d' % (Wd, L), '\n'.join(bad[:12]))
    if bad:
        return st.finish()
    lst = P3.listing(W, P3.OUTS[PHASE])
    st.rec['outputs'].update(reference=ref, secondaries=s3, files=lst, digest=P3.digest(lst),
                             reuse=reuse_data(W, s3, ref, topo_digest, tm, L2, L3))
    st.write()

    # G21, the along-track frame alignment
    lg = os.path.join(logroot, 'G21_frame_align.log')
    rc, out = P3.kit_run(env, KIT[0], [], W, lg)
    g = P3.g21_verdict(out)
    st.rec['outputs']['g21'] = dict(rc=rc, verdict=g['verdict'], nbad=g['nbad'], n=g['n'], median=g['median'],
                                    flagged=g['flagged'], log=lg)
    rows21 = g21_rows(out)
    g21ok = rc == 0 and g['verdict'] == 'PASS'
    if not g21ok and not (rc == 1 and g['verdict'] == 'FAIL'):
        st.gate('G21', 'frame alignment (kit)', 'ERROR', 'rc %d, verdict line %s' % (rc, g['verdict']), 'rc 0 or 1 with a verdict',
                'log %s\n%s' % (lg, P3.tail(lg)))
        return st.finish()
    st.gate('G21e', 'G21\'s printed reference (11.7)', 'INFO', G21E, 'a reading')

    def g21_gate0():   # G21's own verdict, recorded when G7 ends the phase in ERROR before R7 reads the flags
        if g21ok:
            st.gate('G21', 'frame alignment (kit)', 'PASS', '0 of %s dates beyond 5x the frame median |az| %s lines' % (g['n'], g['median']),
                    'linog_frame_align_gate.py rc 0')
        else:
            st.gate('G21', 'frame alignment (kit)', 'DECISION', '%d of %d dates beyond 5x the frame median |az| %s lines: %s' % (
                g['nbad'], g['n'], g['median'], ', '.join(sorted(g['flagged']))), 'linog_frame_align_gate.py rc 0', 'log %s' % lg)

    # G7, the coarse registration (N53)
    lg7 = os.path.join(logroot, 'G7_coarse_reg.log')
    rc7, out7 = P3.kit_run(env, KIT[1], [ref, '--reselect'], W, lg7)
    g7 = P3.reg_verdict(out7)
    tries = [dict(ncand='default', rc=rc7, verdict=g7['verdict'], log=lg7)]
    if rc7 == 1 and g7['verdict'] == 'QUORUM':
        lg7 = os.path.join(logroot, 'G7_coarse_reg_ncand%s.log' % r['G7_NCAND_RETRY'])
        rc7, out7 = P3.kit_run(env, KIT[1], [ref, '--reselect'], W, lg7, extra={'LINOG_REG_NCAND': r['G7_NCAND_RETRY']})
        g7 = P3.reg_verdict(out7)
        tries.append(dict(ncand=r['G7_NCAND_RETRY'], rc=rc7, verdict=g7['verdict'], log=lg7))
    failed = sorted(d for d, (cells, v) in g7['dates'].items() if v == 'FAIL')
    calls = g7_calls(out7)
    st.rec['outputs']['g7'] = dict(tries=tries, verdict=g7['verdict'], nbad=g7['nbad'], n=g7['n'], windows=g7['windows'],
                                   dates={d: list(v) for d, v in g7['dates'].items()}, calls=calls)
    retry = ' (at depth %s, after %s windows at the default depth)' % (r['G7_NCAND_RETRY'], tries[0].get('verdict')) \
        if len(tries) > 1 else ''
    g7ok = rc7 == 0 and g7['verdict'] == 'PASS' and g7['n'] == len(s3)
    g7flag = rc7 == 1 and g7['verdict'] == 'FAIL' and bool(failed)
    g7quorum = rc7 == 1 and g7['verdict'] == 'QUORUM'
    if not (g7ok or g7flag or g7quorum):
        g21_gate0()
        st.gate('G7', 'coarse registration (kit)', 'ERROR', 'rc %d, verdict %s, %s of %d dates reported' % (
            rc7, g7['verdict'], g7['n'], len(s3)), 'rc 0 or 1 with a verdict line for every secondary', 'log %s\n%s' % (lg7, P3.tail(lg7)))
        return st.finish()
    st.rec['outputs']['g3b12'] = g3b12(st, W, ref, s3, geo)   # a reading of every date's product, before any move

    # R7: F, the measured flags; the unmeasured ones and G7's quorum keep v0.12's DECISION
    dec0, derr = None, None
    try:
        dec0, _ = C.d2_decision(W)
    except ValueError as e:
        derr = str(e)
    loop_n = len((dec0 or {}).get('loops') or []) + 1
    F21 = sorted(d for d, (row, meas) in rows21.items() if meas)
    U21 = sorted(d for d, (row, meas) in rows21.items() if not meas)
    F7 = sorted(d for d in failed if calls.get(d, {}).get('bang', 0) * 2 > calls.get(d, {}).get('tot', 0))
    U7 = sorted(d for d in failed if d not in F7)
    plant = C.selftest_hook('LINOG_MOCK_D2FLAG') if os.environ.get('LINOG_MOCK_D2FLAG') else None
    hooked = []
    if plant and plant.split(':')[0] == str(loop_n):
        hooked = sorted(x for x in plant.split(':', 1)[1].split(',') if x in s3)
    F = sorted(set(F21) | set(F7) | set(hooked))
    rwin = dict((x.get('date'), x) for x in ((P1.record(W, '1br', 'rwin') or {}).get('outputs') or {}).get('dates') or [])
    dmode = os.environ.get('LINOG_DECIDE', 'ask')
    try:
        verb, tdates, tmd5, tline = C.d2_txt(W)
        terr = None
    except ValueError as e:
        verb, tdates, tmd5, tline, terr = None, None, None, None, str(e)
    st.rec['outputs']['r7'] = dict(F=F, unmeasured=sorted(set(U21) | set(U7)), g21=F21, g7=F7, hooked=hooked, loop=loop_n,
                                   d2_txt=dict(verb=verb, dates=tdates, md5=tmd5) if verb else None, taken=False)

    def readings(d):
        parts = []
        if d in rows21:
            parts.append('G21: %s' % ' '.join(rows21[d][0].split()))
        if d in calls and d in failed:
            c = calls[d]
            parts.append('G7: called out by %d of %d voting windows, raw dx %s (the median over the windows; residuals %s)' % (
                c['bang'], c['tot'], '%+.1f' % c['raw_dx'] if c['raw_dx'] is not None else 'not read', c['cells']))
        if d in hooked:
            parts.append('the self-test\'s planted flag (LINOG_MOCK_D2FLAG)')
        k = rwin.get(d) or {}
        if k:
            parts.append('rwin k %s, r0 %s m (%s)' % (k.get('k'), k.get('r0_after'), k.get('action')))
        return '; '.join(parts)

    def g21_gate(verdict, how):
        if g21ok:
            st.gate('G21', 'frame alignment (kit)', 'PASS', '0 of %s dates beyond 5x the frame median |az| %s lines' % (g['n'], g['median']),
                    'linog_frame_align_gate.py rc 0')
        else:
            st.gate('G21', 'frame alignment (kit)', verdict, '%d of %d dates beyond 5x the frame median |az| %s lines: %s%s' % (
                g['nbad'], g['n'], g['median'], ', '.join(sorted(g['flagged'])), (' (%s)' % how) if how else ''),
                'linog_frame_align_gate.py rc 0',
                'an off-frame granule images other ground (p447 f0310 20101213: 82.5x by G21\'s own method on the delivered offsets, '
                'the ascending record 8 and 9.1)\n' + '\n'.join(g['flagged'][d] for d in sorted(g['flagged'])) + '\nlog %s' % lg)

    def flag_gates(verdict, how):
        """G21 and G7 with their flags: verdict DECISION (v0.12) or INFO (taken or kept)."""
        g21_gate(verdict, how)
        f7 = sorted(set(failed) | set(hooked))
        if g7ok and not hooked:
            st.gate('G7', 'coarse registration (kit)', 'WARN' if len(tries) > 1 else 'PASS', '0 of %d dates called out%s' % (
                g7['n'], retry), 'linog_coarse_reg_gate.py %s --reselect rc 0' % ref)
        elif g7quorum:
            st.gate('G7', 'coarse registration (kit)', 'DECISION', 'only %s window(s) against a quorum of %s, also at depth %s' % (
                g7['windows'], g7['quorum'], r['G7_NCAND_RETRY']), 'a quorum of textured windows',
                'the gate cannot measure this frame (water or flat void-fill); G21 and per-date coherence remain the nets; '
                'going on without G7 is a human choice\nlog %s' % lg7)
        else:
            st.gate('G7', 'coarse registration (kit)', verdict, '%d of %d dates called out by the voting windows: %s%s%s' % (
                len(f7), g7['n'], ', '.join(f7), retry, (' (%s)' % how) if how else ''), 'linog_coarse_reg_gate.py rc 0',
                'N53 reads as a one-gate (+/-32 sample) range residual on every window; rwin corrects a date\'s range window at '
                'Phase 1, so a call-out after it has a cause no record has seen (18.4)\n' +
                '\n'.join('%s  %s' % (d, readings(d)) for d in f7) + '\nlog %s' % lg7)

    if g21ok and g7ok and not hooked:
        flag_gates('DECISION', '')
        return st.finish()
    if not F and not U21 and not U7 and not g7quorum:   # a FAIL verdict with no flag row read: not R7's to take
        U21 = ['(G21 FAIL with no flagged row read)'] if not g21ok else U21
    if derr or terr:
        flag_gates('DECISION', '')
        st.gate('D2', 'exclusion', 'DECISION', 'flagged %s; %s' % (', '.join(F + U21 + U7), derr or terr), 'R7\'s files readable',
                'a person looks: %s' % (derr or terr))
        return st.finish()
    if U21 or U7 or g7quorum:   # 11.2: not R7's to take
        flag_gates('DECISION', '')
        st.gate('D2', 'exclusion', 'DECISION', 'flagged by %s%s' % (' and '.join(x for x, y in (('G21', not g21ok), ('G7', not g7ok)) if y),
                '; unmeasured: %s' % ', '.join(sorted(set(U21) | set(U7))) if (U21 or U7) else ''),
                'no date flagged; R7 takes measured flags only (11.2)',
                ('R7 takes nothing: %s (a G21 row with no ratio, or a G7 call-out resting on EMPTY, READERR or MISSING windows, '
                 'or G7 below its quorum)\n' % ', '.join(sorted(set(U21) | set(U7))) if (U21 or U7) else 'G7 below its quorum: '
                 'R7 takes nothing (11.8); going on without G7 is a person\'s choice\n') + 'the products stay in the frame and the next '
                'run reads them again (11.5); to exclude a date by hand (11.1), list its granule in %s and move its traces into '
                '%s/_archive/: raw/<zip>, unzipped/<stem>/, SLC/<d>/, offsets/<d>/, coregSLC/Coarse/<d>/, and stack2\'s configs/, '
                'run_files/, baselines/ and pairs.pdf' % (os.path.join(W, 'recon', 'exclude.txt'), W))
        return st.finish()
    # the operator's file
    match = bool(verb) and set(tdates) == set(F)
    if verb and not match:
        st.gate('D2t', 'recon/d2.txt', 'WARN', '"%s" names %s, the flags are %s: not applied' % (tline, ', '.join(tdates), ', '.join(F)),
                'the flagged dates exactly, as a set (11.6)')
    if match and verb == 'keep':
        flag_gates('INFO', 'kept by the operator, recon/d2.txt %s' % tmd5[:8])
        st.gate('D2', 'exclusion', 'INFO', '%s kept by the operator (recon/d2.txt "%s", md5 %s)' % (', '.join(F), tline, tmd5),
                'R7-d (11.6)')
        st.rec['outputs']['r7'].update(kept_by_operator=True)
        return st.finish()
    operator = match and verb == 'take'
    R, _ = P1.recon_json(W)
    rows, _, _ = P2.modes_rows(W)
    modes = dict((d, (rows.get(d) or {}).get('mode')) for d in list(s3) + [ref])
    r1 = P1.record(W, '2a', 'stack1') or {}
    pairs1 = (r1.get('outputs') or {}).get('pair_list') or []
    import lp_p5 as P5
    m5 = P5.load_mintpy()
    lims = r7_limits(W, F, ref, dec0, sorted(list(s3) + [ref]), modes, pairs1, int(cfg.get('min_dates', 5)),
                     float(m5['ADMIT_EXCL_MAX_FRAC']), operator)
    tagh = C.selftest_hook('LINOG_MOCK_D2TAG') if os.environ.get('LINOG_MOCK_D2TAG') else None
    tag = tagh or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    adir, moves, bad6 = r7_paths(W, F, R, tag)
    for x in lims:
        if x['id'] == 'L6':
            x.update(ok=not bad6, text='; '.join(bad6) or '%d moves into %s, every target free, on the frame\'s filesystem' % (
                len(moves), adir))
    st.rec['outputs']['r7']['limits'] = lims
    failing = [x for x in lims if not x['ok']]
    proposal = 'R7\'s proposal (11.2): take %s (%s); the limits: %s' % (', '.join(F), '; '.join('%s: %s' % (d, readings(d)) for d in F),
                                                                       '; '.join('%s %s%s: %s' % (x['id'], 'holds' if x['ok'] else 'FAILS',
                                                                                                  ' (WARN)' if x['warn'] else '', x['text'])
                                                                                 for x in lims))
    if not operator and dmode != 'auto':
        flag_gates('DECISION', '')
        st.gate('D2', 'exclusion', 'DECISION', 'flagged: %s (--decide ask)' % ', '.join(F), 'no date flagged', proposal + '\nto take '
                'them: write the one line "take %s" into %s (or "keep %s" to keep them), then run again (a run without --only)' % (
                    ' '.join(F), os.path.join(W, C.D2_TXT), ' '.join(F)))
        return st.finish()
    if failing:
        flag_gates('DECISION', '')
        st.gate('D2', 'exclusion', 'DECISION', 'flagged: %s; R7 cannot take them: %s' % (', '.join(F), ', '.join(x['id'] for x in failing)),
                'L0 to L8 hold (11.3)', proposal + '\n' + way_on(set(x['id'] for x in failing), len((dec0 or {}).get('loops') or []),
                                                                 operator, F, W))
        return st.finish()
    for x in lims:
        if x['warn']:
            st.gate('D2w', 'R7\'s limit %s' % x['id'], 'WARN', x['text'], 'passed by the operator\'s take (11.6)')
    kept = dict((k.get('date'), k) for k in R.get('kept') or [])
    loop = dict(loop=loop_n, utc=C.utc(), by=('the operator (recon/d2.txt "%s", md5 %s)' % (tline, tmd5)) if operator else
                'R7 under --decide auto', archive=adir, reference=ref, n_before=len(s3) + 1, limits=lims, g21_frame_median=g['median'],
                dates=dict((d, dict(granule=(kept.get(d) or {}).get('scene'), zip=os.path.basename((kept.get(d) or {}).get('zip') or ''),
                                    stem=P1.stem((kept.get(d) or {}).get('zip') or ''), mode=modes.get(d), why=readings(d),
                                    g21=rows21[d][0] if d in rows21 else None, g7=calls.get(d) if d in failed else None,
                                    g21_median=g21_nums(rows21[d][0])[0] if d in rows21 else None,
                                    g21_ratio=g21_nums(rows21[d][0])[1] if d in rows21 else None,
                                    rwin=dict((k, (rwin.get(d) or {}).get(k)) for k in ('k', 'r0_leader', 'col0', 'r0_after', 'action'))))
                           for d in F))
    fa = C.selftest_hook('LINOG_MOCK_D2FAILAT') if os.environ.get('LINOG_MOCK_D2FAILAT') else None
    slp = C.selftest_hook('LINOG_MOCK_D2SLEEP') if os.environ.get('LINOG_MOCK_D2SLEEP') else None
    st.rec['outputs']['r7'].update(taking=True, archive=adir, moves=len(moves))
    st.write()
    with P3.Deferred():
        try:
            md, n = r7_take(W, adir, moves, dec0, loop, failat=int(fa) if fa else None, sleep=slp)
            err = None
        except TakeError as e:
            md, n, err = None, e.n, str(e)
        except Exception as e:  # noqa: BLE001  (after the moves: the decision or the restart file)
            md, n, err = None, len(moves), '%s: %s (after the take\'s %d moves)' % (type(e).__name__, e, len(moves))
        st.rec['outputs']['r7'].update(taking=False, taken=err is None, decision_md5=md, moved=n, error=err)
        if err:
            flag_gates('DECISION', '')
            st.gate('G3b.11', 'R7: the take', 'FAIL', err, 'the moves, the decision, the restart (11.3)',
                    'a person looks at %s (each move it made is named there before it was made); nothing was deleted' %
                    os.path.join(W, adir, 'MOVES.txt'))
        else:
            how = 'taken by R7, loop %d%s' % (loop_n, ', the operator\'s take' if operator else '')
            flag_gates('INFO', how)
            st.gate('G3b.11', 'R7: the take', 'PASS', '%d moves into %s (MOVES.txt); %s written (%s); %s asked' % (
                n, adir, C.D2_DECISION, md[:8], RESTART_FILE), 'the moves, the decision, the restart (11.3)')
            st.gate('D2', 'exclusion', 'INFO', '%s %s: the frame runs again from the top (recon drops them, the reference %s kept, '
                    'this phase reuses the other dates\' products)' % (', '.join(F), how, ref), 'R7 (11.2)')
        st.write()
    return st.finish()


def g3b12(st, W, ref, secs, geo):
    """v0.13, G3b.12 (17.4): G10 v3's reading of the coarse products, coregSLC/Coarse/<d>/<d>.slc against SLC/<REF>/<REF>.slc,
    INFO; an error inside it is recorded (INFO, not read), as a reading."""
    import traceback
    try:
        import lp_reg3 as R3
        st.rec.setdefault('tools', {}).update(C.tool_md5s('lp_reg3.py'))
        rows, _, _ = P2.modes_rows(W)
        modes = dict((d, (rows.get(d) or {}).get('mode')) for d in list(secs) + [ref])
        hgt, why = R3.load_hgt(W)
        if hgt is None:
            raise ValueError(why)
        refp = os.path.join(W, 'SLC', ref, '%s.slc' % ref)
        sp = dict((d, os.path.join(W, 'coregSLC', 'Coarse', d, '%s.slc' % d)) for d in secs)
        n, wins, named, survey, rd = R3.g10v3_read(refp, sp, geo['width'], geo['lines'], hgt)
        summ = R3.g10v3_summary(n, wins, rd, modes, ref, geo['width'])
        rows_ = summ['dates']
        xs = [v['dx'] for v in rows_.values() if v['dx'] is not None]
        ys = [v['dy'] for v in rows_.values() if v['dy'] is not None]
        m = summ.get('mode')
        st.gate('G3b.12', 'coarse registration v3 (17.4)', 'INFO', ('%d dates on %d voting windows: dx %+.3f to %+.3f, dy %+.3f to '
                '%+.3f%s' % (len(xs), summ['voting'], min(xs), max(xs), min(ys), max(ys), '; FBD less FBS dx %+.4f dy %+.4f' % (
                    m['dx'], m['dy']) if m else '')) if xs else 'NOT MEASURED: %d window(s) vote' % summ['voting'],
                'a reading (the coarse misregistration R9 removes)',
                '\n'.join('%s %s dx %s dy %s' % (d, v['mode'], '%+.3f' % v['dx'] if v['dx'] is not None else '-',
                                                   '%+.3f' % v['dy'] if v['dy'] is not None else '-') for d, v in sorted(rows_.items())))
        return dict(window=n, named=named, survey=survey, readings=rd, **summ)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        st.gate('G3b.12', 'coarse registration v3 (17.4)', 'INFO', 'not read: %s: %s' % (type(e).__name__, e), 'a reading',
                '\n'.join(tb[-6:]))
        return dict(error='%s: %s' % (type(e).__name__, e))


if __name__ == '__main__':
    P1.main_guard('lp_coarse', main)
