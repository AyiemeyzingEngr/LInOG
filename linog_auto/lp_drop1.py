#!/usr/bin/env python3
"""lp_drop1.py -- linog_auto Phase 5d1 (v0.12): the drop-one peer test of the pairs R1 flags (item 1: Doc JD's test,
record 119.5; the rule, 120.5; the plan, 124.7; Ariel's word on its four choices, 125.0).
v0.13 r2 (LOGIC 2; the ascending record 18.3 and 19.6, Ariel's word in 18.0 and 20.1): the split rule, balanced, in place
of v0.12 r2's 10 nearest peers, and the guard on the velocity under --decide auto. The inversions, the measure, each
test's key and R2's guards are v0.12 r2's, so the tests a v0.12 r2 run made are read again and only the peers it lacks
are inverted.

Runs inside lp_env.sh, after sbas and before d9ab. admit (v0.12, LOGIC 4) no longer culls the land-flagged pairs by R2
alone: it hands every pair R1 flags, over land or over the whole grid, to this phase (recon/admission.json,
decisions.drop1; none under R1's land floor). The flagged pairs in the network sbas inverted are tested here, each
against its peers:
  the pairs tested   each flagged pair of the network whose drop alone keeps the network one component with every
                     date in 2 pairs or more (otherwise recorded as not testable, and kept);
  its peers          (v0.13 r2, the split rule: record 18.3) the DROP1_PEERS_SIDE unflagged pairs of the network nearest
                     it at or below its mean coherence over R1's land (the stack's coherence) and the DROP1_PEERS_SIDE
                     nearest above it (ties to the earlier name), each one whose drop alone keeps the network as above;
                     peers are shared between the flagged pairs, and each pair is inverted once (v0.12 r2: the
                     DROP1_PEERS nearest it, on either side);
  the zero test      one inversion with no pair dropped: this phase's own inversion against sbas's, the measure's noise
                     floor (D1z: WARN when the cells it changes reach the closest decision's margin; not used by the rule);
  the inversions     MintPy's ifgram_inversion.py on a copy of mintpy/inputs/ifgramStack.h5 with that pair's dropIfgram
                     off, under a copy of the frame's smallbaselineApp.cfg, in drop1/<UTC>/tests/<pair>/ (E1's form,
                     record 119.3 and 119.6), with copies of the files MintPy 1.6.2's inversion reads around a stack, as
                     sbas's inversion had them (r2, record 127): avgSpatialCoh.h5 one folder above the stack
                     (<test>/avgSpatialCoh.h5; a cell at 0 there is not inverted) and, when the frame has one,
                     mintpy/waterMask.h5 in the folder it runs in (<test>/waterMask.h5; the template's waterMaskFile auto
                     reads it there, and finds nothing otherwise); the inversion opens neither geometryRadar.h5 nor
                     maskConnComp.h5. DROP1_WORKERS at a time, each stopped after DROP1_TIMEOUT_S (and sent SIGTERM when
                     its job dies);
  the measure (E1's) coherent land is temporal coherence of DROP1_TCOH_MIN or more on R1's land (geom_reference/hgt.rdr
                     off the water tool's flat masks, as admit reads it); a test's net is the coherent land cells it
                     gains minus those it loses against sbas's own mintpy/temporalCoherence.h5; on land coherent in both,
                     |dv| (a line through each timeseries.h5, mm/yr): the cells beyond 1 mm/yr (n_dv_gt1, the guard's
                     reading since v0.13 r2), p99 and max (recorded, not used);
  the rule           (v0.13 r2, the split rule, balanced: 18.3) a flagged pair is untestable, and kept, with fewer than
                     DROP1_PEERS_SIDE such pairs on a side, or when those peers' mean coherence lies more than
                     DROP1_PEERS_BALANCE from its own; a tested pair is named when its net exceeds every one of its
                     peers' nets. A tested pair has 2 x DROP1_PEERS_SIDE peers: DROP1_PEERS is then that (any other
                     value is refused) and DROP1_MIN_PEERS at most that (v0.12 r2, record 127: the minimum peer count,
                     which then never keeps a tested pair).
  the guard          (v0.13 r2: 19.6, as 20.1 approved it; 22.2's note 5) under --decide auto a named pair is culled only
                     when dropping it alone moves the velocity no more than dropping one of its peers does: its n_dv_gt1
                     at most the highest of its peers' (at equality it is culled); a named pair over that is kept (D1g
                     WARN, naming it and both counts), as R2's no-cull fallback keeps pairs, and the others are culled
                     within R2's guards. Under --decide ask, and when the operator's file decides D3, the cull is every
                     named pair's and the counts go into it. R2's guards apply to the cull as a whole: at most
                     ADMIT_CULL_MAX_FRAC of the network's pairs, one component, every date in 2 pairs or more; otherwise
                     no pair is culled (WARN), as R2 did.
Each test's stack copy and the files beside it are removed once its inversion ends, and its timeseries.h5 once read;
the measures (result.json, drop1.json, drop1.tsv), each inversion's temporalCoherence.h5, numInvIfgram.h5 and log stay
(choice 4, 125.0). Scratch a stopped run left (those copies, time series, base.npz) is removed by the next run that
reads the stack (G5d1.4c), before anything else is decided.
A test completed on the same inputs (its key: sbas's files as recorded, the template, the stack's kept pairs, the pair
dropped, the threshold, R1's land, MintPy's pins, the files copied beside the stack; and TEST_LOGIC, 1 since v0.12, which
the phase's LOGIC 2 leaves alone) is read again, not run again.
A cull rests on its basis (lp_admit.drop1_basis: the flagged pairs, R1's land floor, DROP1_PEERS, DROP1_MIN_PEERS,
DROP1_TCOH_MIN, ADMIT_CULL_MAX_FRAC; v0.13 r2: DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE), the network tested and igram's
digest; admit applies a decision file only on the same three (D1d), so a file made under v0.12 r2's rule is not applied.
The decision, as d9ab's R5 (record 108.3):
  the cull in place   admit applied recon/drop1_decision.json (its decisions.drop1.decision) and the file's network after
                      the cull, interferograms and basis are this run's; or, the operator's recon/admission.txt deciding
                      D3, a completed run of this phase in drop1/ took a cull on this basis and these interferograms that
                      leaves this network (the operator wrote it in): D1c INFO, PASS, no inversion run again.
  the operator's file recon/admission.txt names the exclusions (D3 the operator's): the test runs and its figures are
                      recorded, not applied (Doc JD, 119.5).
  a cull, --decide auto, in a run of the driver that allows this phase a restart (LINOG_RESTART=allowed): this phase
                      writes recon/drop1_decision.json (the cull; the network, interferograms and basis it was taken on
                      and the network after it; the table, the zero test, the guards), the earlier such file moved into
                      _archive/ first; moves the frame's mintpy/ into _archive/mintpy_predrop1_<UTC>/ (a rename); asks
                      the driver to restart (status/restart.json); INFO. SIGINT, SIGTERM and SIGHUP wait for the end of
                      that step (a SIGKILL or a failed write does not: see take_cull).
                      On the restart admit takes the cull from the file, mcfg and sbas run again, and this phase reads
                      the cull as in place (v0.13 r2: with the guard's reading the file holds, D1g).
  the guard keeps     (v0.13 r2, --decide auto) every pair the rule names over its peers' highest n_dv_gt1: nothing to
                      cull, D1g WARN, PASS (state "kept by the guard").
  a cull otherwise    (--decide ask, or auto outside such a run): a DECISION naming the pairs (v0.13 r2: with each one's
                      n_dv_gt1 against its peers' highest); the operator writes them into recon/admission.txt, moves
                      mintpy/ into _archive/ and runs again.
  under R1's land floor (admit's record: D1f WARN), or no flagged pair in the network: PASS, nothing tested.

Gates
  G5d1.1  sbas PASS on record, its files as it recorded them; G5d1.1a admit PASS on record                  FAIL
  G5d1.1j admit's recon/admission.json: v0.12's handoff (decisions.drop1), the kept pairs                     FAIL
  G5d1.2  environment; MintPy at its pin                                                         ERROR / FAIL
  G5d1.3  ifgram_inversion.py on the PATH is the pinned env's; G5d1.3s the settings                           FAIL
  D1n     the flagged pairs: land, grid, in the network                                                       INFO
  G5d1.4k the stack's kept pairs admit's (else G5d1.4 FAIL: mcfg and sbas are to run again; a dry run plans)   PASS
  G5d1.4c scratch an earlier stopped run of this phase left under drop1/: removed                             INFO
  D1c     the cull in place                                                                                  INFO
  D1f     under R1's land floor: nothing tested                                                              WARN
  G5d1.4  the stack's grid hgt.rdr's; R1's land; sbas's products present and read                            FAIL
  D1t     the tests: the flagged pairs tested and not, the peers, the zero test; reused, to run              INFO
  G5d1.5  free space at the record folder                                                                     FAIL
  G5d1.6  the template copy equal to the frame's                                                              FAIL
  G5d1.7  the inversions: each rc 0 within DROP1_TIMEOUT_S (a failed one is run again the next time)         FAIL
  D1z     the zero test: its gain and loss against sbas's, against the closest decision's margin     INFO / WARN
  D1r     the rule, each flagged pair: named or kept, its split (below, above), its peers' range and mean     INFO
  D1g     (v0.13 r2) the guard: each named pair's n_dv_gt1 against its peers' highest   N/A / PASS / INFO / WARN
  R2c     the cull's guards (R2's)                                                                PASS / INFO / WARN
  G5d1.9  the frame's mintpy/ unchanged while this phase ran                                                  FAIL
  D1      the decision                                                                     PASS / INFO / DECISION
  G5d1.10 the cull taken: the decision file written, mintpy/ moved, the restart asked                         FAIL
The fingerprint: sbas's files, admit's decisions, network and handoff, igram's digest, the settings, MintPy's pins, the
decision file, whether the operator's file decides D3 (its cull recorded, or taken by this phase), (r2) the md5s of
mintpy/avgSpatialCoh.h5 and mintpy/waterMask.h5 (absent: None), which sbas's listing leaves out, and (v0.13 r2) the rule,
"split5, balance 0.005" at linog_mintpy.cfg's values: with LOGIC 2, a frame's drop1 reads STALE once after v0.12 r2 and
decides again.
--state: STALE also when the evidence files changed since. --dryrun DIR: the tests with their folders under DIR (the
frame only read; a plan only when the frame's sbas has not run, or this dry run's admit keeps another network than the
frame's stack); nothing taken: under --decide auto INFO naming the cull a run would take, under ask the DECISION a run
would give. --job FILE: one test (run by this phase's pool). Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import datetime
import glob
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time

import lp_admit as A
import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'drop1', '5d1', 2   # v0.13 r2: the split rule, balanced, and the guard (18.3, 19.6); v0.12: 1
# v0.13 r2 (18.3): each test's key keeps its own logic number. The inversions, the measure and the keys' inputs are v0.12
# r2's, so a test a v0.12 r2 run made is read again; only the phase's LOGIC moved (its decision is made again).
TEST_LOGIC = 1
VERSION_DROP1 = 'linog_auto v0.13 r2 (2026-10-19)'
DECISION_FILE = os.path.join('recon', 'drop1_decision.json')   # admit reads it
RESTART_FILE = os.path.join('status', 'restart.json')          # the driver reads it after this phase
STACK = os.path.join('mintpy', 'inputs', 'ifgramStack.h5')
AVG = os.path.join('mintpy', 'avgSpatialCoh.h5')
WATER = os.path.join('mintpy', 'waterMask.h5')
# r2 (record 127): the files MintPy 1.6.2's ifgram_inversion.py reads around a stack (its source: ../avgSpatialCoh.h5 from the
# stack's folder, ifgram_inversion.py 743-761; waterMask.h5 in the working folder when the template's waterMaskFile is auto,
# cli/ifgram_inversion.py 206-208 and ifgram_inversion.py 724-734), placed as sbas's inversion had them: <test>/avgSpatialCoh.h5
# always (sbas's reference_point writes it); <test>/waterMask.h5 when mintpy/waterMask.h5 is there (modify_network writes it when
# geometryRadar.h5 holds a waterMask). The inversion opens neither geometryRadar.h5 nor maskConnComp.h5, so they are not copied
# (v0.12 r1 did). Their md5s are in this phase's fingerprint and in each test's key.
BESIDE = (AVG,)
OPTIONAL = (WATER,)
TEMPLATE = os.path.join('mintpy', 'smallbaselineApp.cfg')
TCOH = os.path.join('mintpy', 'temporalCoherence.h5')
TSERIES = os.path.join('mintpy', 'timeseries.h5')
KEEP = ('temporalCoherence.h5', 'numInvIfgram.h5', 'inv.log', 'result.json', 'job.json')
EVIDENCE = ('drop1.json', 'drop1.tsv')
SET_KEYS = ('DROP1_PEERS', 'DROP1_MIN_PEERS', 'DROP1_PEERS_SIDE', 'DROP1_PEERS_BALANCE', 'DROP1_TCOH_MIN', 'DROP1_WORKERS',
            'DROP1_TIMEOUT_S', 'DROP1_FREE_GIB')   # v0.13 r2: DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE (18.3)
RULE = ('v0.13 r2 (the ascending record 18.3, 19.6): a flagged pair is tested against the DROP1_PEERS_SIDE unflagged pairs nearest '
        'it at or below its mean land coherence and the DROP1_PEERS_SIDE nearest above, and is untestable and kept with fewer on a '
        'side or when those peers\' mean coherence lies more than DROP1_PEERS_BALANCE from its own; a tested pair is named when its '
        'net (coherent land gained minus lost when it is dropped) exceeds every peer\'s; under --decide auto a named pair is culled '
        'only when its n_dv_gt1 is at most its peers\' highest (else kept, WARN), under ask the named pairs\' cull is a DECISION '
        'with the counts; the cull taken whole when it is ADMIT_CULL_MAX_FRAC of the pairs or fewer and leaves one component with '
        'every date in 2 pairs or more, otherwise none (record 124.7)')
TSV_COLS = ('pair', 'group', 'mean_coh_land', 'gained_land', 'lost_land', 'net_land', 'net_pct', 'p99_dv', 'max_dv', 'n_dv_gt1',
            'kept', 'rc', 'seconds', 'maxrss_kb', 'folder')


def say(s=''):
    print(s, flush=True)


def beside_md5(W):
    """r2: {name: md5 or None} of the files MintPy's inversion reads around a stack, as the frame holds them (BESIDE, OPTIONAL)."""
    return dict((os.path.relpath(x, 'mintpy'), C.md5_file(os.path.join(W, x)) if os.path.isfile(os.path.join(W, x)) else None)
                for x in BESIDE + OPTIONAL)


def clean(o):
    """o with every NaN or infinite float as None (the JSON stays readable by jq and JavaScript)."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return dict((k, clean(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def write_json(p, obj):
    """obj into p whole (a temporary file renamed over it)."""
    tmp = '%s.tmp%d' % (p, os.getpid())
    with open(tmp, 'w') as fh:
        json.dump(clean(obj), fh, indent=1, default=str)
        fh.write('\n')
    os.replace(tmp, p)


def settings(m):
    return dict((k, m.get(k)) for k in SET_KEYS + ('ADMIT_CULL_MAX_FRAC', 'ADMIT_LAND_MIN_PX'))


def read_settings(m):
    """(values, problems): the DROP1_* settings of linog_mintpy.cfg as numbers."""
    v, bad = {}, []
    for k, typ, lo in (('DROP1_PEERS', int, 1), ('DROP1_MIN_PEERS', int, 1), ('DROP1_PEERS_SIDE', int, 1), ('DROP1_WORKERS', int, 1),
                       ('DROP1_TIMEOUT_S', int, 1), ('DROP1_TCOH_MIN', float, 0.0), ('DROP1_PEERS_BALANCE', float, 0.0),
                       ('DROP1_FREE_GIB', float, 0.0), ('ADMIT_CULL_MAX_FRAC', float, 0.0)):
        if k not in m:
            bad.append('%s absent from %s' % (k, m.get('mintpy_cfg_file')))
            continue
        try:
            v[k] = typ(m[k])
        except ValueError:
            bad.append('%s = %r is not a %s' % (k, m[k], 'whole number' if typ is int else 'number'))
            continue
        if v[k] < lo:
            bad.append('%s = %s, under %s' % (k, m[k], lo))
    if 'DROP1_TCOH_MIN' in v and not 0.0 < v['DROP1_TCOH_MIN'] < 1.0:
        bad.append('DROP1_TCOH_MIN = %s, not between 0 and 1' % v['DROP1_TCOH_MIN'])
    if 'DROP1_PEERS_BALANCE' in v and not 0.0 <= v['DROP1_PEERS_BALANCE'] < 1.0:   # v0.13 r2: a difference of coherences
        bad.append('DROP1_PEERS_BALANCE = %s, not from 0 to under 1' % v['DROP1_PEERS_BALANCE'])
    # v0.13 r2 (18.3, settled here): a tested pair has DROP1_PEERS_SIDE peers on each side, so DROP1_PEERS (v0.12 r2's count of
    # nearest peers) is then 2 x DROP1_PEERS_SIDE; another value would read as a setting the rule ignores, so it is refused
    if 'DROP1_PEERS' in v and 'DROP1_PEERS_SIDE' in v and v['DROP1_PEERS'] != 2 * v['DROP1_PEERS_SIDE']:
        bad.append('DROP1_PEERS = %d, not 2 x DROP1_PEERS_SIDE = %d (the split rule\'s peers: DROP1_PEERS_SIDE on each side)' % (
            v['DROP1_PEERS'], 2 * v['DROP1_PEERS_SIDE']))
    if v.get('DROP1_MIN_PEERS', 0) > v.get('DROP1_PEERS', 1 << 30):   # r2: more than the peers a pair gets, no pair could be culled
        bad.append('DROP1_MIN_PEERS = %d, over DROP1_PEERS = %d' % (v['DROP1_MIN_PEERS'], v['DROP1_PEERS']))
    return v, bad


def rule_id(m):
    """v0.13 r2 (18.3): the rule as this phase's fingerprint takes it, "split5, balance 0.005" at linog_mintpy.cfg's values."""
    return 'split%s, balance %s' % (m.get('DROP1_PEERS_SIDE'), m.get('DROP1_PEERS_BALANCE'))


# ---------------------------------------------------------------- the network (standard library: the self-test calls them)
def degrees(pairs):
    deg = {}
    for p in pairs:
        for d in p.split('_'):
            deg[d] = deg.get(d, 0) + 1
    return deg


def components(pairs):
    """The number of connected components of the network of these pairs (0 for none)."""
    adj = {}
    for p in pairs:
        a, b = p.split('_')
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen, n = set(), 0
    for d in sorted(adj):
        if d in seen:
            continue
        n += 1
        st = [d]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x)
            st.extend(adj[x] - seen)
    return n


def network_ok(left, dates):
    """(ok, why) of a network once pairs are dropped: one component and every one of dates in 2 pairs or more."""
    deg = degrees(left)
    low = sorted(d for d in dates if deg.get(d, 0) < 2)
    bad = []
    nc = components(left)
    if nc != 1:
        bad.append('%d components' % nc)
    if low:
        bad.append('dates with fewer than 2 pairs: %s' % ', '.join(low))
    return not bad, '; '.join(bad)


def testable(kept, pair):
    """(ok, why): the network without this pair alone is one component with every date in 2 pairs or more."""
    dates = sorted(set(d for p in kept for d in p.split('_')))
    return network_ok([p for p in kept if p != pair], dates)


def pick_peers(k, mc, pool, side):
    """v0.13 r2, the split rule (18.3's build line; 22.2's note 4): (below, above), the side pairs of pool nearest pair k at or
    below its mean land coherence mc[k] and the side pairs nearest above it, each list nearest first; ties to the earlier name.
    A side holds fewer when the pool does (the rule then keeps k, untestable)."""
    c = mc[k]
    below = sorted((p for p in pool if p != k and mc[p] <= c), key=lambda p: (c - mc[p], p))[:side]
    above = sorted((p for p in pool if p != k and mc[p] > c), key=lambda p: (mc[p] - c, p))[:side]
    return below, above


def short_text(short, c):
    """'2 unflagged pairs below its coherence 0.4198' (and ' and 3 above' when both sides are short): rule()'s words (18.3)."""
    t = '%d unflagged pair%s %s its coherence %.4f' % (short[0][0], '' if short[0][0] == 1 else 's', short[0][1], c)
    return t + (' and %d %s' % short[1] if len(short) > 1 else '')


def rule(tested, nets, split, mc, side, balance, min_peers=1):
    """The split rule, balanced (v0.13 r2, 18.3), on the nets: [dict(pair, net, coh, below, above, peers, peer_nets, peers_max,
    peers_lo, peers_hi, peers_mean, offset, testable, margin, culled, why)] for the tested pairs; split: {pair: (below, above)}
    as pick_peers gives them. Before the maximum, a pair is untestable and kept with fewer than side peers on a side, or when
    its peers' mean coherence lies more than balance from its own: its margin None (no decision rests on it, so the zero
    test's check passes it by). A testable pair is named when its net exceeds every peer's (culled True: the rule's reading,
    which the guard and R2's guards then bound; the key keeps v0.12's name, as RUN_MANIFEST.json reads it). min_peers is v0.12
    r2's minimum (record 127); a testable pair has 2 x side peers, so at the settings drop1 accepts it keeps none."""
    out = []
    for k in tested:
        below, above = split[k]
        peers = list(below) + list(above)
        pn = [nets[p] for p in peers]
        c = mc[k]
        pc = [mc[p] for p in peers]
        mean = sum(pc) / len(pc) if pc else None
        x = dict(pair=k, net=nets[k], coh=c, below=list(below), above=list(above), peers=peers, peer_nets=pn,
                 peers_max=max(pn) if pn else None, peers_lo=min(pc) if pc else None, peers_hi=max(pc) if pc else None,
                 peers_mean=mean, offset=mean - c if pc else None, testable=False, margin=None, culled=False)
        short = [(n, s) for n, s in ((len(below), 'below'), (len(above), 'above')) if n < side]
        if short:
            x['why'] = 'untestable: %s, %d asked: kept' % (short_text(short, c), side)
        elif not abs(mean - c) <= balance:   # a NaN mean reads as off, never as balanced (the r2 review's R2R-09)
            x['why'] = 'untestable: its peers\' mean coherence %.4f, %.4f %s its %.4f (%g asked): kept' % (
                mean, abs(mean - c), 'above' if mean > c else 'below', c, balance)
        elif len(pn) < min_peers:
            x['why'] = '%d peer%s, under the %d the rule asks (%+d against the peers\' max %+d)' % (
                len(pn), '' if len(pn) == 1 else 's', min_peers, nets[k], max(pn))
        else:
            mx = max(pn)
            cul = nets[k] > mx
            x.update(testable=True, margin=nets[k] - mx, culled=cul,
                     why='%+d %s every peer\'s (max %+d of %d)' % (nets[k], 'exceeds' if cul else 'does not exceed', mx, len(pn)))
        out.append(x)
    return out


def d1r_value(x):
    """D1r's value for one row of rule() (18.3: named or kept, with the split, the peers' range and their mean)."""
    head = x['why'] if x['why'].startswith('untestable') else '%s: %s' % ('named' if x['culled'] else 'kept', x['why'])
    return '%s; its coherence %.4f, its peers %d below and %d above%s' % (
        head, x['coh'], len(x['below']), len(x['above']), ': %.4f to %.4f, their mean %.4f (%+.4f)' % (
            x['peers_lo'], x['peers_hi'], x['peers_mean'], x['offset']) if x['peers'] else '')


def guard(table, counts):
    """v0.13 r2, the guard (19.6, as 20.1 approved it; 22.2's note 5): for each pair the rule names, its n_dv_gt1 (the land
    cells coherent in both runs whose velocity moves more than 1 mm/yr when that pair alone is dropped) against the highest
    of its peers': [dict(pair, n_dv_gt1, peers_max, over, why)]; over when its count exceeds that highest ("at most": at
    equality it is culled). It reads the tests' recorded counts and runs nothing. Settled here: a count not recorded (None,
    which no complete test gives) reads as over, so the guard never clears a pair on a missing reading."""
    out = []
    for x in table:
        if not x.get('culled'):
            continue
        k = x['pair']
        mine = counts.get(k)
        theirs = [counts.get(p) for p in x['peers']]
        mx = max(theirs) if theirs and None not in theirs else None
        if mine is None or mx is None:
            out.append(dict(pair=k, n_dv_gt1=mine, peers_max=mx, over=True,
                            why='%s: a count not recorded (its own %s, its peers\' highest %s)' % (k, mine, mx)))
            continue
        over = mine > mx
        out.append(dict(pair=k, n_dv_gt1=mine, peers_max=mx, over=over, why='%s: n_dv_gt1 %d %s its peers\' highest %d' % (
            k, mine, 'over' if over else 'at' if mine == mx else 'under', mx)))
    return out


def guard_gate(gd, auto):
    """D1g's (verdict, value, note): N/A with no pair named; PASS when every named pair is at or under its peers' highest
    n_dv_gt1; with one over it, WARN under --decide auto (it is kept) and INFO otherwise (the counts go into the decision)."""
    over, clear = [x for x in gd if x['over']], [x for x in gd if not x['over']]
    if not gd:
        return 'N/A', 'no pair named: nothing to read', ''
    if not over:
        return 'PASS', 'every named pair at or under its peers\' highest: %s' % '; '.join(x['why'] for x in gd), ''
    rest = '; at or under it, to R2\'s guards: %s' % '; '.join(x['why'] for x in clear) if clear else ''
    if auto:
        return ('WARN', 'kept: %s%s' % ('; '.join(x['why'] for x in over), rest),
                'dropping it alone moves the velocity on more land cells than dropping any of its peers does: kept, as R2\'s '
                'no-cull fallback keeps pairs (19.6); a person may still cull it through recon/admission.txt')
    return 'INFO', 'over its peers\' highest (kept under --decide auto): %s%s; the counts go into the decision' % (
        '; '.join(x['why'] for x in over), rest), ''


def guards(kept, cull, cap):
    """R2's guards on the cull as a whole: dict(taken, frac, why)."""
    if not cull:
        return dict(taken=False, frac=0.0, why='no pair to cull')
    frac = len(cull) / float(len(kept))
    dates = sorted(set(d for p in kept for d in p.split('_')))
    ok, why = network_ok([p for p in kept if p not in set(cull)], dates)
    bad = []
    if frac > cap:
        bad.append('%d of %d pairs (%.1f %%), over %g %%' % (len(cull), len(kept), 100 * frac, 100 * cap))
    if not ok:
        bad.append('the network left: %s' % why)
    return dict(taken=not bad, frac=frac, why='; '.join(bad) or '%d of %d pairs (%.1f %%), one component, every date in 2 pairs or more' % (
        len(cull), len(kept), 100 * frac))


def network_md5(pairs):
    """As lp_admit.network_md5: the kept pairs, sorted."""
    return C.md5_obj(sorted(pairs))


def zero_check(z, table, log):
    """D1z: the zero test's coherent land cells gained and lost against sbas's (its churn) against the closest decision's
    margin (|net - the peers' highest|). WARN when the churn is not 0 and reaches that margin: that decision is within the
    measure's noise. (verdict, value, reference, note, the zero test's record)."""
    churn = (z.get('gained') or 0) + (z.get('lost') or 0)
    close = min(((abs(x['margin']), x['pair']) for x in table if x.get('margin') is not None), default=None)
    noisy = churn > 0 and close is not None and churn >= close[0]
    zero = dict((k, z.get(k)) for k in ('gained', 'lost', 'net', 'p99_dv'))
    zero.update(churn=churn, closest_margin=close[0] if close else None, closest_pair=close[1] if close else None, noisy=noisy)
    value = ('no pair dropped: %+d coherent land px (gained %d, lost %d) against sbas\'s; p99 |dv| %s mm/yr; the closest decision\'s '
             'margin %s%s' % (z.get('net') or 0, z.get('gained') or 0, z.get('lost') or 0,
                              '%.3f' % z['p99_dv'] if z.get('p99_dv') is not None else '-',
                              '%d px (%s)' % close if close else '- (no flagged pair testable)',
                              ': the zero test\'s %d px changed reach it' % churn if noisy else ''))
    note = '' if not noisy else ('this phase\'s own inversion differs from sbas\'s by as many coherent land cells as the closest '
                                 'decision\'s margin: that decision is within the noise of the measure. Read the zero test\'s log (%s) '
                                 'before acting on it' % log)
    return ('WARN' if noisy else 'INFO', value, 'gained + lost under the closest margin (the measure\'s noise floor; recorded, '
            'not used by the rule)', note, zero)


# ---------------------------------------------------------------- the measure (numpy and h5py: the env's)
def first(path):
    import h5py
    with h5py.File(path, 'r') as f:
        return f[list(f.keys())[0]][()]


def velocity(path):
    """mm/yr: a line through each cell of a MintPy time series (E1's vel(); the time in years from 2000-01-01)."""
    import h5py
    import numpy as np
    with h5py.File(path, 'r') as f:
        dates = [x.decode() if isinstance(x, bytes) else str(x) for x in f['date'][()]]
        y = f['timeseries'][()].astype(np.float64)
    t = np.array([(datetime.datetime.strptime(d, '%Y%m%d') - datetime.datetime(2000, 1, 1)).days / 365.25 for d in dates])
    A = np.vstack([t, np.ones_like(t)]).T
    n, r, c = y.shape
    y = y.reshape(n, -1)
    ok = np.all(np.isfinite(y), axis=0) & np.any(y != 0, axis=0)
    v = np.full(y.shape[1], np.nan)
    if ok.any() and n >= 2:
        v[ok] = np.linalg.lstsq(A, y[:, ok], rcond=None)[0][0] * 1000.0
    return v.reshape(r, c)


def measure(d, land, tN, vN, base, thr):
    """A test's measure against sbas's: coherent land gained, lost and net; |dv| on land coherent in both."""
    import numpy as np
    tX = first(os.path.join(d, 'temporalCoherence.h5')) >= thr
    vX = velocity(os.path.join(d, 'timeseries.h5'))
    gained = int((land & tX & ~tN).sum())
    lost = int((land & tN & ~tX).sum())
    m = land & tN & tX & np.isfinite(vN) & np.isfinite(vX)
    dv = np.abs(vN - vX)[m]
    return dict(gained=gained, lost=lost, net=gained - lost, net_pct=100.0 * (gained - lost) / base if base else None,
                p99_dv=float(np.percentile(dv, 99)) if dv.size else None, max_dv=float(dv.max()) if dv.size else None,
                n_dv_gt1=int((dv > 1.0).sum()), compared=int(m.sum()), coherent_land=int((land & tX).sum()))


def job_main(jf):
    """One test (this phase's pool runs it inside lp_env.sh): the stack copied, with the files MintPy's inversion reads
    around it (the job's beside list: avgSpatialCoh.h5 one folder above the copy, and waterMask.h5 in the test's folder when
    the frame has one) placed as sbas's inversion had them, the pair's dropIfgram off, MintPy's ifgram_inversion.py in the
    test's folder (stopped after the time limit; SIGTERM to it when this job dies), the copies removed, the measure, the
    time series removed once read; result.json written whole at the end, complete only when the inversion ended rc 0 and
    the measure was made."""
    import resource
    import h5py
    import numpy as np
    J = json.load(open(jf))
    d = J['dir']
    copy = os.path.join(d, 'inputs', 'ifgramStack.h5')
    side = [(src, os.path.join(d, rel)) for src, rel in J['beside']]
    res = dict(pair=J['pair'], group=J['group'], key=J['key'], complete=False, started=C.utc(), folder=J['folder'], rc=None)
    t0 = time.time()
    try:
        os.makedirs(os.path.dirname(copy), exist_ok=True)
        for src, dst in side:
            shutil.copyfile(src, dst)
        shutil.copyfile(J['stack'], copy)
        with h5py.File(copy, 'r+') as f:
            names = ['%s_%s' % tuple(x.decode() if isinstance(x, bytes) else str(x) for x in row) for row in f['date'][()]]
            drop = f['dropIfgram'][()].astype(bool)
            if names != J['names'] or [bool(x) for x in drop] != J['kept_vector']:
                raise ValueError('the copy\'s pairs or dropIfgram differ from the stack this phase read')
            if J['pair']:
                drop[names.index(J['pair'])] = False
            f['dropIfgram'][...] = drop
        res['kept'] = int(drop.sum())
        cmd = ['ifgram_inversion.py', copy, '-t', J['template']]
        late = False
        P3._libc()   # loaded here, not in the child
        me = os.getpid()

        def init():   # in the child: SIGTERM when this job dies; a job already gone before that took hold: end here
            P3._job_init()
            if os.getppid() != me:
                os._exit(143)
        with open(os.path.join(d, 'inv.log'), 'ab') as log:
            log.write(('# %s  %s  (cwd %s)\n' % (C.utc(), ' '.join(cmd), d)).encode())
            log.flush()
            p = subprocess.Popen(cmd, cwd=d, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, preexec_fn=init)
            res['inv_pid'] = p.pid
            try:
                rc = p.wait(timeout=J['timeout'])
            except subprocess.TimeoutExpired:
                late = True
                p.terminate()
                try:
                    rc = p.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    p.kill()
                    rc = p.wait()
            log.write(('# rc %s  %.1f s%s\n' % (rc, time.time() - t0, '  (stopped at the time limit, %d s)' % J['timeout'] if late else '')).encode())
        res.update(rc=rc, late=late, inv_seconds=round(time.time() - t0, 1))
        for n in [copy] + [dst for _, dst in side]:
            os.remove(n)
        if rc == 0 and not late:
            B = np.load(J['base'])
            res.update(measure(d, B['land'], B['tN'], B['vN'], int(J['base_cells']), float(J['thr'])))
            res['complete'] = True
    except Exception as e:  # noqa: BLE001
        res['error'] = '%s: %s' % (type(e).__name__, str(e)[:300])
    finally:
        for n in [copy] + [dst for _, dst in side] + [os.path.join(d, 'timeseries.h5')]:
            try:
                if os.path.lexists(n):
                    os.remove(n)
            except OSError as e:
                res.setdefault('left', []).append('%s (%s)' % (n, e))
        res.update(seconds=round(time.time() - t0, 1), maxrss_kb=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, ended=C.utc())
        write_json(os.path.join(d, 'result.json'), res)
    return 0 if res['complete'] else 1


# ---------------------------------------------------------------- folders, keys, earlier tests
def new_folder(recdir):
    base = os.path.join(recdir, 'drop1', time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    d, n = base, 1
    while True:
        try:
            os.mkdir(d)
            return d
        except FileExistsError:
            n += 1
            d = '%s_%d' % (base, n)


def done_tests(roots):
    """{key: (result, folder of the test)} of every completed test under roots' drop1/*/tests/*/ (the latest kept)."""
    out = {}
    for r in roots:
        for f in sorted(glob.glob(os.path.join(r, 'drop1', '*', 'tests', '*', 'result.json'))):
            try:
                j = json.load(open(f))
            except (OSError, ValueError):
                continue
            if j.get('complete') is True and j.get('key') and os.path.isfile(os.path.join(os.path.dirname(f), 'temporalCoherence.h5')):
                out[j['key']] = (j, os.path.dirname(f))
    return out


def done_runs(roots):
    """Completed runs of this phase (their drop1.json, complete), the latest first: [(json, folder)]."""
    out = []
    for r in roots:
        for f in glob.glob(os.path.join(r, 'drop1', '*', 'drop1.json')):
            try:
                j = json.load(open(f))
            except (OSError, ValueError):
                continue
            if j.get('complete') is True:
                out.append((j, os.path.dirname(f)))
    return sorted(out, key=lambda x: str(x[0].get('written')), reverse=True)


def leftovers(recdir):
    """The scratch a stopped run of this phase left under <recdir>/drop1/ (its own files, never evidence): the stack copies
    and the files placed beside them in its tests' folders, their time series, its base.npz."""
    pats = [os.path.join('tests', '*', 'inputs', 'ifgramStack.h5'), os.path.join('tests', '*', 'timeseries.h5'), 'base.npz'] + [
        os.path.join('tests', '*', os.path.relpath(x, 'mintpy')) for x in BESIDE + OPTIONAL]
    return sorted(set(x for q in pats for x in glob.glob(os.path.join(recdir, 'drop1', '*', q))))


def decision_digest(state, cull, taken, table, thr, peers_n, source, min_peers=None, guard_rows=None):
    """What deliver's fingerprint and RUN_MANIFEST.json take of this phase: a changed cull, verdict or test changes them;
    a re-read of the same tests does not. v0.13 r2 (19.6): the guard's clause, each named pair's n_dv_gt1 against its peers'
    highest, joins where the guard read a pair (settled here: a decision without one keeps v0.12 r2's form)."""
    d = dict(state=state, cull=sorted(cull or []), taken=taken, source=source, thr=thr, peers=peers_n, min_peers=min_peers,
             tested=[[x['pair'], x['net'], x['peers_max'], x['culled']] for x in table or []])
    if guard_rows:
        d['guard'] = [[x['pair'], x['n_dv_gt1'], x['peers_max'], x['over']] for x in guard_rows]
    return C.md5_obj(clean(d))


def take_cull(W, ra, cull, J, folder_rel, utc_tag):
    """The cull taken under --decide auto. Every check first (admit's network on record and this one, _archive/ a folder on
    mintpy/'s disk, the target names free, no restart asked and not read), then, with SIGINT, SIGTERM and SIGHUP held
    (P3.Deferred: such a stop waits for the end of the step), in order: an earlier recon/drop1_decision.json moved into
    _archive/, the frame's mintpy/ moved into _archive/mintpy_predrop1_<UTC>/mintpy (a rename), recon/drop1_decision.json
    written (the cull; the network, interferograms and basis it was taken on, and the network after it, which admit
    checks; the tests: the table, the zero test, the guards), status/restart.json written. A SIGKILL, or a write that
    fails (a full disk), after the rename leaves the frame without mintpy/ and without the decision: the next run makes
    mintpy/ again (mcfg, sbas) and tests again. J: this run's drop1.json content. Raises on a failure."""
    net = ((ra or {}).get('outputs') or {}).get('network_md5')
    if net != J['network']:
        raise ValueError('admit\'s record names network %s, the tests ran on %s' % (str(net)[:8], J['network'][:8]))
    arch = os.path.join(W, '_archive')
    os.makedirs(arch, exist_ok=True)
    df = os.path.join(W, DECISION_FILE)
    src = os.path.join(W, 'mintpy')
    dst = os.path.join(arch, 'mintpy_predrop1_%s' % utc_tag)
    old = os.path.join(arch, 'drop1_decision_%s.json' % utc_tag) if os.path.lexists(df) else None
    if not os.path.isdir(src) or os.path.islink(src):
        raise ValueError('%s is not a folder' % src)
    if os.path.lexists(dst):
        raise ValueError('%s exists already' % dst)
    if old and os.path.lexists(old):
        raise ValueError('%s exists already' % old)
    if os.stat(src).st_dev != os.stat(arch).st_dev:
        raise ValueError('mintpy/ and _archive/ are on two filesystems: the move would be a copy')
    if os.path.lexists(os.path.join(W, RESTART_FILE)):
        raise ValueError('%s exists already (a restart asked and not read)' % RESTART_FILE)
    dec = dict(cull=sorted(cull), network=J['network'], after=J['after'], igram=J['igram'], basis=J['basis'], pairs=J['pairs'],
               source='drop1\'s peer test under --decide auto', folder=folder_rel, table=J['table'], zero=J['zero'], guards=J['guards'],
               threshold=J['threshold'], peers_n=J['peers_n'], min_peers=J['min_peers'], settings=J['settings'], rule=RULE, frame=W,
               pipeline=P6.HERE, rule_id=J['rule_id'], side=J['side'], balance=J['balance'], guard=J['guard'], named=J['cull_proposed'],
               version=VERSION_DROP1, moved_to=os.path.relpath(dst, W), earlier=os.path.relpath(old, W) if old else None)
    with P3.Deferred():
        if old:
            os.rename(df, old)
        os.makedirs(dst)
        os.rename(src, os.path.join(dst, 'mintpy'))
        write_json(df, dict(dec, taken=C.utc()))
        rs = dict(from_phase='admit', by='drop1', reason='drop1: %d pair%s culled (%s); mintpy/ moved to %s' % (
            len(cull), '' if len(cull) == 1 else 's', ', '.join(sorted(cull)[:6]), os.path.relpath(dst, W)),
            decision=DECISION_FILE, decision_md5=C.md5_file(df), written=C.utc())
        write_json(os.path.join(W, RESTART_FILE), rs)
    return dict(decision=DECISION_FILE, decision_md5=C.md5_file(df), moved_to=os.path.relpath(dst, W), restart=RESTART_FILE,
                earlier=os.path.relpath(old, W) if old else None)


# ---------------------------------------------------------------- the phase
def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5d1: the drop-one peer test of the flagged pairs (record 124.7)')
    ap.add_argument('--path')
    ap.add_argument('--frame')
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    ap.add_argument('--job', metavar='FILE', help='one test (this phase\'s pool)')
    a = ap.parse_args()
    if a.job:
        return job_main(a.job)
    if not a.path or not a.frame:
        ap.error('--path and --frame are needed')
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m, q = P1.load_env(), P2.load_stack(), P5.load_mintpy(), P6.load_p6()
    rs = P1.record(recdir, '5d', 'sbas') or {}
    if a.dryrun and (P1.record(W, '5d', 'sbas') or {}).get('verdict') == 'PASS':
        rs = P1.record(W, '5d', 'sbas') or {}
    ra = P1.record(recdir, '5a', 'admit') or {}
    ri = P1.record(W, '4f', 'igram') or {}
    ao = ra.get('outputs') or {}
    df = os.path.join(W, DECISION_FILE)
    op_d3 = str(((ao.get('decisions') or {}).get('d3') or {}).get('source') or '').startswith('the operator')
    fp = C.md5_obj(dict(logic=LOGIC, sbas=(rs.get('outputs') or {}).get('digest'), admit=ao.get('decisions_md5'), handoff=ao.get('drop1_md5'),
                        network=ao.get('network_md5'), igram=(ri.get('outputs') or {}).get('digest'), settings=settings(m),
                        mintpy=m['MINTPY_VERSION'], defaults=m['MINTPY_DEFAULTS_MD5'], decision=C.md5_file(df) if os.path.isfile(df) else None,
                        operator=op_d3,   # the operator's file deciding D3 or not (its cull recorded, or taken), as d9ab's D9 source
                        beside=beside_md5(W),   # r2: the files copied beside each test's stack (sbas's listing leaves them out)
                        rule=rule_id(m)))   # v0.13 r2 (18.3): "split5, balance 0.005", with LOGIC 2

    def evidence_changed(rec):
        o = (rec or {}).get('outputs') or {}
        return P3.listing_changed(W, [x[0] for x in o.get('files') or []], o.get('files'))
    if a.state:
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, evidence_changed))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   settings=settings(m), decide=os.environ.get('LINOG_DECIDE', 'ask')))
    st.rec['version'] = VERSION_DROP1
    st.write()
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    say('   drop1: %s, LOGIC %d' % (VERSION_DROP1, LOGIC))
    rs, from_frame = P6.prior6(st, 'G5d1.1', recdir, W, '5d', 'sbas', P5.OUTS['sbas'], bool(a.dryrun))
    if not rs:
        return st.finish()
    if a.dryrun and (not from_frame or (rs.get('outputs') or {}).get('planned')):
        return P5.plan_only(st, ['would test each pair R1 flags against its %s nearest unflagged pairs on each side of its coherence (v0.13 '
                                 'r2, the split rule, balanced): ifgram_inversion.py on a copy of %s with the pair dropped, the coherent '
                                 'land gained and lost against sbas\'s' % (m.get('DROP1_PEERS_SIDE'), STACK)],
                            'the frame\'s sbas has not run, so there is nothing to test')
    ra = P3.prior3(st, 'G5d1.1a', recdir, '5a', 'admit')
    if not ra:
        return st.finish()
    aj = os.path.join(recdir, 'recon', 'admission.json')
    try:
        adm = json.load(open(aj))
        kept = list(adm['kept_pairs'])
        hand = (adm.get('decisions') or {}).get('drop1')
        if not isinstance(hand, dict) or 'flagged' not in hand:
            raise KeyError('decisions.drop1 (admit is to run under v0.12 first: its LOGIC 4 hands the flagged pairs here)')
    except (OSError, ValueError, KeyError, TypeError) as e:
        st.gate('G5d1.1j', 'admit\'s decisions', 'FAIL', '%s: %s' % (aj, e), 'recon/admission.json with kept_pairs and decisions.drop1')
        return st.finish()
    d3src = str(((adm.get('decisions') or {}).get('d3') or {}).get('source') or '')
    operator = d3src.startswith('the operator')
    flagged = sorted(hand.get('flagged') or [])
    st.gate('G5d1.1j', 'admit\'s decisions', 'PASS', '%s: %d pairs kept; D3 %s; %d flagged (over land %d, over the whole grid %d)%s' % (
        aj, len(kept), d3src or 'no source recorded', len(flagged), len(hand.get('land') or []), len(hand.get('whole') or []),
        '; under R1\'s land floor' if hand.get('under_floor') else ''), 'kept_pairs; decisions.drop1 (v0.12)')
    if not P5.env_gate(st, 'G5d1.2', env, s, m):
        return st.finish()
    if not P5.which_gate(st, 'G5d1.3', s, ('ifgram_inversion.py',)):
        return st.finish()
    sv, sbad = read_settings(m)
    st.gate('G5d1.3s', 'the settings', 'FAIL' if sbad else 'PASS', '; '.join(sbad) or ', '.join('%s %s' % (k, m[k]) for k in SET_KEYS),
            '%s (linog_mintpy.cfg)' % ', '.join(SET_KEYS))
    if sbad:
        return st.finish()
    thr, npeer, cap, mpeer = sv['DROP1_TCOH_MIN'], sv['DROP1_PEERS'], sv['ADMIT_CULL_MAX_FRAC'], sv['DROP1_MIN_PEERS']
    nside, bal, rid = sv['DROP1_PEERS_SIDE'], sv['DROP1_PEERS_BALANCE'], rule_id(m)   # v0.13 r2 (18.3)
    dmode = os.environ.get('LINOG_DECIDE', 'ask')
    knet = network_md5(kept)
    igd = (ri.get('outputs') or {}).get('digest')
    cbasis = A.drop1_basis(flagged, hand.get('under_floor'), m)
    in_net = [p for p in flagged if p in set(kept)]
    st.gate('D1n', 'the flagged pairs', 'INFO', '%d flagged (land %d, whole grid %d), %d in the network of %d pairs%s' % (
        len(flagged), len(hand.get('land') or []), len(hand.get('whole') or []), len(in_net), len(kept),
        (': ' + ', '.join(in_net[:10]) + (' and %d more' % (len(in_net) - 10) if len(in_net) > 10 else '')) if in_net else ''),
        'admit\'s R1 (record 108.3): over land, unless under the floor, and over the whole grid')

    # ---- the stack: sbas inverted admit's network (else mcfg and sbas are to run again)
    import h5py
    import numpy as np
    stack = os.path.join(W, STACK)
    try:
        with h5py.File(stack, 'r') as f:
            names = ['%s_%s' % tuple(x.decode() if isinstance(x, bytes) else str(x) for x in row) for row in f['date'][()]]
            kv = [bool(x) for x in f['dropIfgram'][()]]
            L, Wd = f['coherence'].shape[1:]
        skept = [n for n, k in zip(names, kv) if k]
    except Exception as e:  # noqa: BLE001
        st.gate('G5d1.4', 'the stack and the land', 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:300]), '%s read' % STACK)
        return st.finish()
    if sorted(skept) != sorted(kept):
        why = 'admit%s keeps %d pairs, the frame\'s stack %d: mcfg and sbas are to run again before the tests' % (
            ' (this dry run)' if a.dryrun else '', len(kept), len(skept))
        if a.dryrun:
            return P5.plan_only(st, ['would test the flagged pairs once sbas has run on admit\'s network'], why)
        st.gate('G5d1.4', 'the stack and the land', 'FAIL', '%s (differ: %s)' % (why, ', '.join(sorted(set(skept) ^ set(kept))[:6])),
                'the stack\'s kept pairs admit\'s')
        return st.finish()
    st.gate('G5d1.4k', 'the stack\'s network', 'PASS', '%s keeps %d of its %d pairs, admit\'s %d (network %s)' % (
        STACK, len(skept), len(names), len(kept), knet[:8]), 'the stack\'s kept pairs admit\'s')
    old = leftovers(recdir)   # this run's own record folder: a dry run removes nothing in the frame
    if old:
        gib = sum(os.path.getsize(x) for x in old) / 2. ** 30
        for x in old:
            os.remove(x)
        st.gate('G5d1.4c', 'scratch left by a stopped run', 'INFO', '%d files removed (%.2f GiB): %s' % (len(old), gib, ', '.join(
            os.path.relpath(x, recdir) for x in old[:4]) + (' and %d more' % (len(old) - 4) if len(old) > 4 else '')),
            'this phase\'s own scratch under drop1/: stack copies, the files beside them, time series, base.npz (choice 4, 125.0)')
    st.rec['outputs'] = dict(network_md5=knet, flagged=flagged, in_network=in_net, operator=operator, basis=cbasis, peers_n=npeer,
                             min_peers=mpeer, side=nside, balance=bal, rule_id=rid)

    def finish_pass(state, note, verdict='PASS', table=None, cull=None, taken=False, extra=None, files=None, folder=None, gd=None):
        dg = decision_digest(state, cull, taken, table, thr, npeer, d3src, mpeer, gd)
        st.gate('D1', 'the decision', verdict, state + ('; %s' % note if note else ''), RULE)
        lst = P3.listing(W, files) if files and not a.dryrun else []
        st.rec['outputs'].update(state=state, cull=sorted(cull or []), taken=taken, decision_md5=dg, files=lst, digest=P3.digest(lst),
                                 folder=folder, table=table or [], guard=gd or [], **(extra or {}))
        if a.dryrun:
            st.rec['outputs'].update(dryrun=True)
        return st.finish()

    # ---- the cull in place: admit took this phase's decision file (taken on this basis and these interferograms, the network
    # now its network minus its cull), or the operator's file names a completed test's cull
    roots = [W] + ([recdir] if a.dryrun else [])
    inplace = None
    drec = (hand.get('decision') or {})
    if drec.get('applied') and os.path.isfile(df):
        try:
            dj = json.load(open(df))
        except ValueError:
            dj = {}
        if dj.get('cull') and dj.get('after') == knet and dj.get('igram') == igd and dj.get('basis') == cbasis:
            inplace = (dj, 'admit took it from %s' % DECISION_FILE, dj.get('folder'), DECISION_FILE)
    if not inplace and operator:
        for j, fold in done_runs(roots):
            if j.get('cull') and j.get('after') == knet and j.get('igram') == igd and j.get('basis') == cbasis:
                inplace = (j, 'the operator\'s recon/admission.txt names it', os.path.relpath(fold, recdir), None)
                break
    if inplace:
        j, why, fold, dfile = inplace
        st.gate('D1c', 'the cull in place', 'INFO', '%d pair%s (%s) culled by the test in %s on the network of %d pairs; %s' % (
            len(j['cull']), '' if len(j['cull']) == 1 else 's', ', '.join(j['cull'][:8]), fold, j.get('pairs') or len(kept) + len(j['cull']), why),
            'no inversion run again')
        gd0 = j.get('guard') or []   # v0.13 r2: the guard's reading of that decision, so this record names a pair it kept
        if gd0:
            gv, gval, gnote = guard_gate(gd0, j.get('decide', 'auto') == 'auto' and not operator)
            st.gate('D1g', 'the guard (19.6), as that test read it', gv, gval, 'a named pair culled under --decide auto only when its '
                    'n_dv_gt1 is at most its peers\' highest (19.6, as 20.1 approved it)', gnote)
        return finish_pass('cull in place', 'the test in %s: %d culled' % (fold, len(j['cull'])), table=j.get('table'), cull=j['cull'],
                           taken=True, folder=fold, extra=dict(in_place=fold, zero=j.get('zero'), guards=j.get('guards'), decision_file=dfile),
                           gd=gd0)
    if hand.get('under_floor'):
        st.gate('D1f', 'R1\'s land floor', 'WARN', 'admit\'s record: under the land floor (%s px)' % m.get('ADMIT_LAND_MIN_PX'),
                'the measure needs land: nothing tested')
        return finish_pass('under the land floor', 'nothing tested')
    if not in_net:
        return finish_pass('none flagged', 'no flagged pair in the network: nothing tested')

    # ---- the land, the coherence of each pair over land, sbas's products
    try:
        geo, _ = P3.geometry(W)
        kf = A.kit_functions(env, m, q)
        Ld = A.land_of(W, geo['gw'], geo['gl'], kf['flat_masks'])
        land = Ld['land']
    except Exception as e:  # noqa: BLE001
        st.gate('G5d1.4', 'the stack and the land', 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:300]),
                'geom_reference/hgt.rdr and the water tool as admit reads them')
        return st.finish()
    bad = []
    if (L, Wd) != land.shape:
        bad.append('the stack\'s grid %d x %d, hgt.rdr\'s %d x %d' % (L, Wd, land.shape[0], land.shape[1]))
    for x in (TCOH, TSERIES, TEMPLATE) + BESIDE:
        if not os.path.isfile(os.path.join(W, x)):
            bad.append('%s absent' % x)
    if bad:
        st.gate('G5d1.4', 'the stack and the land', 'FAIL', '; '.join(bad), 'one grid; sbas\'s products present')
        return st.finish()
    nland = int(land.sum())
    with h5py.File(stack, 'r') as f:
        coh = f['coherence']
        mc = dict((n, float(np.nanmean(coh[i][land]))) for i, n in enumerate(names) if kv[i])
    tN = first(os.path.join(W, TCOH)) >= thr
    base = int((land & tN).sum())
    st.gate('G5d1.4', 'the stack and the land', 'PASS', '%s: %d pairs, %d kept (admit\'s); %d x %d; R1\'s land %d px; coherent land (temporal '
            'coherence %g or more, sbas\'s) %d px' % (STACK, len(names), len(kept), L, Wd, nland, thr, base),
            'the stack\'s kept pairs admit\'s; one grid')

    # ---- the tests
    fset = set(flagged)
    tested, untestable = [], []
    for k in in_net:
        ok, why = testable(kept, k)
        (tested if ok else untestable).append(k if ok else (k, why))
    pool = [p for p in kept if p not in fset and testable(kept, p)[0]]
    split = dict((k, pick_peers(k, mc, pool, nside)) for k in tested)   # v0.13 r2: (below, above), 18.3
    peers = dict((k, split[k][0] + split[k][1]) for k in tested)
    union = sorted(set(p for k in tested for p in peers[k]))
    tlist = [('zero', None)] + [('flagged', k) for k in tested] + [('peer', p) for p in union]
    sbas_dg = (rs.get('outputs') or {}).get('digest')
    tmd5 = C.md5_file(os.path.join(W, TEMPLATE))

    import hashlib
    lmd5 = hashlib.md5(np.packbits(land).tobytes()).hexdigest()
    side = [x for x in BESIDE + OPTIONAL if x in BESIDE or os.path.isfile(os.path.join(W, x))]   # r2: what sbas's inversion read
    side_md5 = dict((os.path.relpath(x, 'mintpy'), C.md5_file(os.path.join(W, x))) for x in side)

    def key_of(pair):   # v0.13 r2: TEST_LOGIC, not the phase's LOGIC (18.3: the tests v0.12 r2 made are read again)
        return C.md5_obj(dict(logic=TEST_LOGIC, sbas=sbas_dg, template=tmd5, kept=sorted(kept), drop=pair, thr=thr, mintpy=m['MINTPY_VERSION'],
                              defaults=m['MINTPY_DEFAULTS_MD5'], land=lmd5, beside=side_md5))
    keys = dict((p, key_of(p)) for _, p in tlist)
    prior = done_tests(roots)
    reuse = dict((p, prior[keys[p]]) for _, p in tlist if keys[p] in prior)
    todo = [(g, p) for g, p in tlist if p not in reuse]
    workers = max(1, min(sv['DROP1_WORKERS'], len(todo) or 1))
    ncpu = os.cpu_count() or 1
    threads = max(1, ncpu // workers)
    st.gate('D1t', 'the tests', 'INFO', '%d flagged pair%s tested%s; %d peer%s (each pair\'s %d nearest at or below its coherence and %d '
            'nearest above at most, shared; their mean coherence within %g of its own to test it); the zero test; %d inversion%s in all: '
            '%d read again, %d to run, %d at a time, %d thread%s each; beside each stack copy: %s%s' % (
                len(tested), '' if len(tested) == 1 else 's', '; not testable: %s' % '; '.join('%s (%s)' % x for x in untestable) if untestable else '',
                len(union), '' if len(union) == 1 else 's', nside, nside, bal, len(tlist), '' if len(tlist) == 1 else 's', len(reuse), len(todo),
                workers, threads, '' if threads == 1 else 's', ', '.join(sorted(side_md5)), '' if WATER in side else ' (the frame has no %s)' % WATER),
            'record 124.7: the flagged pairs, their peers, the zero test; the files MintPy\'s inversion reads around a stack (127); v0.13 r2: '
            'the split rule, balanced (18.3)')
    if not tested:
        return finish_pass('no cull', 'no flagged pair testable', extra=dict(untestable=untestable))
    folder = new_folder(recdir)
    rel = os.path.relpath(folder, recdir)
    st.rec['outputs'].update(folder=rel, running=bool(todo))
    st.write()
    ssize = os.path.getsize(stack)
    if todo:
        tsz = os.path.getsize(os.path.join(W, TSERIES))
        tcz = os.path.getsize(os.path.join(W, TCOH))
        bsz = sum(os.path.getsize(os.path.join(W, x)) for x in side)
        need = (workers * (ssize + bsz + tsz) + len(todo) * 2 * tcz) / 2. ** 30 + sv['DROP1_FREE_GIB']
        free = P1.free_gib(folder)
        st.gate('G5d1.5', 'free space', 'PASS' if free >= need else 'FAIL', '%.1f GiB free at %s; the stack %.3f GiB, the files beside it %.3f '
                'GiB, a time series %.3f GiB' % (free, folder, ssize / 2. ** 30, bsz / 2. ** 30, tsz / 2. ** 30),
                '%.1f GiB or more (%d copies and time series at once, the tests\' files, plus %g)' % (need, workers, sv['DROP1_FREE_GIB']))
        if free < need:
            return st.finish()
        tcopy = os.path.join(folder, 'smallbaselineApp.cfg')
        shutil.copy2(os.path.join(W, TEMPLATE), tcopy)
        same = C.md5_file(tcopy) == tmd5
        st.gate('G5d1.6', 'the template', 'PASS' if same else 'FAIL', '%s copied into %s (md5 %s)' % (TEMPLATE, rel, tmd5[:8]),
                'equal to the frame\'s')
        if not same:
            return st.finish()
        bfile = os.path.join(folder, 'base.npz')
        vN = velocity(os.path.join(W, TSERIES)).astype(np.float32)
        np.savez(bfile, land=land, tN=tN, vN=vN)
        lines, tags = [], []
        for g, p in todo:
            tag = p or 'zero'
            d = os.path.join(folder, 'tests', tag)
            os.makedirs(d)
            jf = os.path.join(d, 'job.json')
            write_json(jf, dict(dir=d, folder=os.path.relpath(d, recdir), pair=p, group=g, key=keys[p], stack=stack, names=names, kept_vector=kv,
                                beside=[[os.path.join(W, x), os.path.relpath(x, 'mintpy')] for x in side], template=tcopy, base=bfile,
                                base_cells=base, thr=thr, timeout=sv['DROP1_TIMEOUT_S']))
            lines.append('exec %s -B %s --job %s' % (shlex.quote(sys.executable), shlex.quote(os.path.abspath(__file__)), shlex.quote(jf)))
            tags.append(tag)
        jenv = dict(os.environ, PYTHONUNBUFFERED='1', MPLBACKEND='Agg', **P5.mpl_env(recdir))
        for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
            jenv[k] = str(threads)
        mem0 = P3.mem_available_kb()
        say('   the inversions: %d, %d at a time (%d threads each), in %s; MemAvailable %s kB' % (len(todo), workers, threads, folder, mem0))
        before = P3.listing(W, ('mintpy',))
        t0 = time.time()
        pres = P3.run_pool(lines, tags, folder, jenv, workers, os.path.join(folder, 'logs'))
        secs = time.time() - t0
        try:
            os.remove(bfile)
        except OSError:
            pass
        st.rec['outputs'].update(running=False, pool=P3.pool_summary(pres), seconds=round(secs, 1), mem_available_kb=mem0)
    else:
        before = P3.listing(W, ('mintpy',))
        secs, pres = 0.0, []
    # ---- the results
    R, failed = {}, []
    for g, p in tlist:
        if p in reuse:
            j, fold = reuse[p]
            R[p] = dict(j, group=g, folder=os.path.relpath(fold, recdir), reused=True)
            continue
        f = os.path.join(folder, 'tests', p or 'zero', 'result.json')
        try:
            j = json.load(open(f))
        except (OSError, ValueError):
            j = dict(pair=p, complete=False, error='no result.json')
        R[p] = dict(j, group=g, reused=False)
        if not j.get('complete'):
            failed.append('%s (rc %s%s%s)' % (p or 'zero', j.get('rc'), ', the time limit' if j.get('late') else '',
                                               ', %s' % j['error'] if j.get('error') else ''))
    st.gate('G5d1.7', 'the inversions', 'FAIL' if failed else 'PASS', '%d of %d complete (%d read again); %.0f s; max RSS %s kB' % (
        len(tlist) - len(failed), len(tlist), len(reuse), secs, max([x['maxrss_kb'] for x in pres if x] or [0])),
        'each rc 0 within %d s' % sv['DROP1_TIMEOUT_S'], '' if not failed else 'not complete: %s. The complete ones are read again the next '
        'time; logs under %s' % ('; '.join(failed[:6]), os.path.join(folder, 'tests')))
    rows = []
    for g, p in tlist:
        x = R[p]
        rows.append([p or 'zero', g, mc.get(p) if p else None, x.get('gained'), x.get('lost'), x.get('net'), x.get('net_pct'), x.get('p99_dv'),
                     x.get('max_dv'), x.get('n_dv_gt1'), x.get('kept'), x.get('rc'), x.get('seconds'), x.get('maxrss_kb'), x.get('folder')])
    with open(os.path.join(folder, 'drop1.tsv'), 'w') as fh:
        fh.write('\t'.join(TSV_COLS) + '\n')
        for r in rows:
            fh.write('\t'.join('' if v is None else ('%.4f' % v if isinstance(v, float) else str(v)) for v in r) + '\n')
    after = P3.listing(W, ('mintpy',))
    same = after == before
    J = dict(written=C.utc(), complete=False, key=C.md5_obj(sorted(keys.values())), network=knet, pairs=len(kept), igram=igd, basis=cbasis, threshold=thr,
             peers_n=npeer, min_peers=mpeer, beside=side_md5, flagged=flagged, tested=tested, untestable=untestable, peers=peers, land_px=nland,
             coherent_land_px=base,
             tests=dict((p or 'zero', dict((k, R[p].get(k)) for k in ('group', 'gained', 'lost', 'net', 'net_pct', 'p99_dv', 'max_dv', 'n_dv_gt1',
                                                                        'kept', 'rc', 'seconds', 'maxrss_kb', 'folder', 'reused', 'key'))) for _, p in tlist),
             mean_coh_land=dict((p, mc[p]) for _, p in tlist if p), settings=sv, rule=RULE, frame=W, pipeline=P6.HERE, version=VERSION_DROP1,
             frame_unchanged=same, rule_id=rid, side=nside, balance=bal, split=split, decide=dmode)
    if failed or not same:
        write_json(os.path.join(folder, 'drop1.json'), J)
        st.gate('G5d1.9', 'the frame\'s mintpy/', 'PASS' if same else 'FAIL', '%d files, %s while this phase ran' % (
            len(after), 'unchanged' if same else 'CHANGED'), 'unchanged (only read)', '' if same else 'something wrote into mintpy/ '
            'while the tests ran: find it, and run again')
        st.rec['outputs'].update(tests=len(tlist), failed=failed)
        return st.finish()
    z = R[None]
    nets = dict((p, R[p]['net']) for _, p in tlist if p)
    table = rule(tested, nets, split, mc, nside, bal, mpeer)
    zv, zval, zref, znote, zero = zero_check(z, table, os.path.join(recdir, z.get('folder') or rel, 'inv.log'))
    st.gate('D1z', 'the zero test', zv, zval, zref, znote)
    for x in table:
        st.gate('D1r', 'the rule: %s' % x['pair'], 'INFO', d1r_value(x),
                'v0.13 r2 (18.3): %d unflagged pairs on each side of its coherence, their mean within %g of it; then its net above every '
                'peer\'s' % (nside, bal))
    named = sorted(x['pair'] for x in table if x['culled'])
    # v0.13 r2, the guard (19.6, as 20.1 approved it; 22.2's note 5): under --decide auto the cull is the named pairs the guard
    # clears; under ask, and when the operator's file decides D3, it is every named pair's and the counts go into it
    gd = guard(table, dict((p, R[p].get('n_dv_gt1')) for _, p in tlist if p))
    auto = dmode == 'auto' and not operator
    over = sorted(x['pair'] for x in gd if x['over'])
    gv, gval, gnote = guard_gate(gd, auto)
    st.gate('D1g', 'the guard (19.6)', gv, gval, 'under --decide auto a named pair is culled only when its n_dv_gt1 is at most its '
            'peers\' highest (19.6, as 20.1 approved it)', gnote)
    kept_g = over if auto else []
    cull = sorted(p for p in named if p not in set(kept_g))
    G = guards(kept, cull, cap)
    st.gate('R2c', 'the cull\'s guards (R2\'s)', 'PASS' if not cull else 'INFO' if G['taken'] else 'WARN', (
        'none to cull' if not cull else ('taken: ' if G['taken'] else 'not taken: ') + G['why'] + '; the cull %s' % ', '.join(cull[:12]) + (
            ' and %d more' % (len(cull) - 12) if len(cull) > 12 else '')),
        'whole when %g %% of the pairs or fewer, one component, every date in 2 pairs or more; otherwise none' % (100 * cap),
        '' if not cull or G['taken'] else 'no pair is culled: MintPy\'s per-pixel masks (temporal coherence) stand in for it (R2)')
    J.update(complete=True, table=table, zero=zero, cull=cull if G['taken'] else [], cull_proposed=named, guards=G, guard=gd,
             kept_by_guard=kept_g, after=network_md5([p for p in kept if p not in set(cull)]) if G['taken'] else knet)
    write_json(os.path.join(folder, 'drop1.json'), J)
    st.gate('G5d1.9', 'the frame\'s mintpy/', 'PASS', '%d files, unchanged while this phase ran' % len(after), 'unchanged (only read)')
    files = [os.path.relpath(os.path.join(folder, n), W) for n in EVIDENCE]
    extra = dict(tests=len(tlist), reused=len(reuse), ran=len(todo), zero=zero, guards=G, workers=workers, threads=threads, untestable=untestable,
                 named=named, kept_by_guard=kept_g)

    def names(xs):
        return ', '.join(xs[:6]) + (' and %d more' % (len(xs) - 6) if len(xs) > 6 else '')
    counts = '; '.join(x['why'] for x in gd)   # the guard's counts, as the decision carries them (19.6)
    kg = '; kept by the guard (19.6): %s' % names(kept_g) if kept_g else ''
    if not cull:
        if kept_g:   # v0.13 r2: the guard keeps every pair the rule names, as R2's no-cull fallback keeps pairs
            return finish_pass('kept by the guard', 'the rule names %s; the guard keeps %s under --decide auto (%s): no cull' % (
                names(named), 'it' if len(named) == 1 else 'them', counts), table=table, extra=extra, files=files, folder=rel, gd=gd)
        # v0.13 r2 (18.3): a pair with fewer than DROP1_PEERS_SIDE unflagged pairs on a side, or unbalanced, is kept whatever its
        # net (margin None); a pair with fewer than DROP1_MIN_PEERS peers (v0.12 r2) cannot be tested at the settings drop1 takes
        short = [x['pair'] for x in table if x['why'].startswith('untestable: ') and 'unflagged pair' in x['why']]
        unbal = [x['pair'] for x in table if x['why'].startswith('untestable: its peers')]
        few = [x['pair'] for x in table if not x['testable'] and not x['why'].startswith('untestable')]
        parts = (['%d with fewer than %d unflagged pairs on a side (%s)' % (len(short), nside, names(short))] if short else []) + (
            ['%d unbalanced, their peers\' mean coherence more than %g from their own (%s)' % (len(unbal), bal, names(unbal))] if unbal else []) + (
            ['%d with fewer than %d peers (%s)' % (len(few), mpeer, names(few))] if few else [])
        rest = len(table) - len(short) - len(unbal) - len(few)
        note = 'no flagged pair\'s net above every peer\'s' if not parts else 'of %d flagged pair%s, kept: %s%s' % (
            len(table), '' if len(table) == 1 else 's', '; '.join(parts), '; %d with a net not above every peer\'s' % rest if rest else '')
        return finish_pass('no cull', note, table=table, extra=extra, files=files, folder=rel, gd=gd)
    if not G['taken']:
        return finish_pass('cull refused', G['why'] + kg, table=table, cull=cull, extra=extra, files=files, folder=rel, gd=gd)
    howto = ('write into %s, as MintPy key = value lines:\n  mintpy.network.excludeDate12 = %s\n  mintpy.network.excludeDate = %s\n'
             'then move %s into %s/_archive/ (mcfg makes it again) and run again; this phase then reads the cull as in place' % (
                 os.path.join(W, 'recon', 'admission.txt'), ','.join(cull), (adm.get('cfg') or {}).get('mintpy.network.excludeDate') or 'no',
                 os.path.join(W, 'mintpy'), W))
    gtxt = ' (n_dv_gt1 against its peers\' highest: %s%s)' % (counts, '; over it, kept under --decide auto: %s' % ', '.join(over)
                                                              if over and not auto else '') if gd else ''
    if operator:
        return finish_pass('recorded, not applied', 'the operator\'s recon/admission.txt decides D3 (Doc JD, 119.5); the rule would cull %s%s' % (
            ', '.join(cull), gtxt), table=table, cull=cull, extra=extra, files=files, folder=rel, gd=gd)
    if a.dryrun and dmode == 'auto':
        return finish_pass('dry run', 'under --decide auto a run of linog_auto.sh without --only takes the cull of %d (%s): %s written, '
                           'mintpy/ moved into _archive/mintpy_predrop1_<UTC>/, a restart from admit (with --only, a DECISION)%s' % (
                               len(cull), ', '.join(cull[:6]), DECISION_FILE, kg), verdict='INFO', table=table, cull=cull, extra=extra, files=[],
                           folder=rel, gd=gd)
    if dmode == 'auto' and os.environ.get('LINOG_RESTART') == 'allowed' and not a.dryrun:
        tag = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        try:
            tk = take_cull(W, ra, cull, J, rel, tag)
        except Exception as e:  # noqa: BLE001
            st.gate('G5d1.10', 'the cull taken', 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:300]),
                    'the decision file written, mintpy/ moved into _archive/, the restart asked',
                    'look at %s, %s and mintpy/; the manual path: %s' % (DECISION_FILE, os.path.join(W, '_archive'), howto))
            st.rec['outputs'].update(table=table, cull=cull)
            return st.finish()
        st.gate('G5d1.10', 'the cull taken', 'PASS', '%s written (%s); mintpy/ moved to %s; %s asked%s' % (
            tk['decision'], tk['decision_md5'][:8], tk['moved_to'], tk['restart'], '; the earlier decision moved to %s' % tk['earlier']
            if tk['earlier'] else ''), 'record 124.7, as R5 (108.3)')
        return finish_pass('cull taken', '%d pair%s (%s): the driver runs the frame again from admit, which takes the cull from %s%s' % (
            len(cull), '' if len(cull) == 1 else 's', ', '.join(cull[:6]), DECISION_FILE, kg), verdict='INFO', table=table, cull=cull,
            taken=True, extra=dict(extra, r5=tk, decision_file=DECISION_FILE), files=files, folder=rel, gd=gd)
    return finish_pass('cull asked', 'the rule names %d pair%s (%s)%s%s; %s: ' % (
        len(named), '' if len(named) == 1 else 's', ', '.join(named[:6]), gtxt, kg, 'under --decide ask the cull is yours' if dmode != 'auto' else
        'under --decide auto the cull is taken only in a run of linog_auto.sh without --only, which restarts the frame from admit') + howto,
        verdict='DECISION', table=table, cull=cull, extra=extra, files=files, folder=rel, gd=gd)


if __name__ == '__main__':
    P1.main_guard('lp_drop1', main)
