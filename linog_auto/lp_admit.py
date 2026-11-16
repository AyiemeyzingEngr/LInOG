#!/usr/bin/env python3
"""lp_admit.py -- linog_auto Phase 5a: which pairs and dates MintPy inverts (D3), and how it treats unwrapping errors (D9).
v0.12 (LOGIC 4, record 124.7, Ariel's word 125.0): R2 culls no pair by itself. Every pair R1 flags, over land or over the
whole grid (none under the land floor), goes to the phase drop1 after sbas, which tests each against its peers (Doc JD's
drop-one test, 119.5) and applies R2's guards to its cull. The cull drop1 takes under --decide auto is
recon/drop1_decision.json: admit takes it (in its fingerprint, with drop1's peers, minimum peer count and threshold while
the file is present) when it was taken on the network the rules leave now, on
the same interferograms (igram's digest) and the same basis (the flagged pairs, R1's land floor, drop1's peers, minimum
peer count (r2, record 127), threshold and cap: drop1_basis(); v0.13 r2, the ascending record 18.3: the split rule's
DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE, in the basis and, while the file is present, in the fingerprint); otherwise it
is not applied (D1d WARN) and drop1 tests the network again.
admission.json's decisions.drop1 is the handoff (the flagged pairs, the decision file); decisions.r2 says R2 culls none.

Runs inside lp_env.sh. The kit's linog_admit.py (8cff02ed, G18 and G20) reads every pair's filt_*.int, .cor and
.unw.conncomp and prints a proposal; it writes nothing. This phase runs it from the frame folder (G20, as v0.9) and then,
v0.10 (record 108.3, approved in 109.0), decides D3 by three rules in this order:
  R1  the kit's statistics over land. Land: the finite heights of geom_reference/hgt.rdr (|h| > 1e5 m read as no height)
      off the water tool's flat_masks() (linog_watermask.py at its pin: a 5 x 5 standard deviation under 1 cm, dilated by
      5 x 5, then a 3 x 3 opening; water = its two masks). The kit's own per-pair arithmetic (its conc() taken from the
      pinned file's source) over the land: coherence over the land, R and the spectral peak with the phasors off the land
      set to 0, LARGEST as the land pixels of the component that holds the most of them, over the land's (0 when the
      components lie only off the land); the kit's own rule on
      them (its argparse defaults: LARGEST under 0.20 or R under 0.25 flags a pair; the date screen at 3.0x the frame's
      median peak). The same arithmetic over the whole grid must print the kit's own lines (G5a.7, the mirror). With fewer
      than ADMIT_LAND_MIN_PX land pixels, no pair is flagged and no date screened (WARN).
  R3  dead and thin dates leave the network (mintpy.network.excludeDate): a date with fewer than 2 pairs in the network as
      it stands (all such at once), or with more than ADMIT_DEAD_SHARE of its pairs flagged (one at a time, the highest
      share first, then the most flagged, then the earliest), until none is left. It holds when the rest keeps min_dates
      (the path table) in one component, every date in 2 pairs or more, at most ADMIT_EXCL_MAX_FRAC of the dates
      excluded (v0.13, R7-e: R3's and the dates of recon/d2_decision.json together, over the network's and R7's; the file's
      md5 in the fingerprint when it exists), and D1's reference date; otherwise a DECISION, in either --decide mode.
  R2  v0.10 and v0.11: on the network R3 leaves, the flagged pairs are culled whole (excludeDate12) when they are
      ADMIT_CULL_MAX_FRAC of its pairs or fewer, and the network left is one component with every date in 2 pairs or more;
      otherwise no pair is culled (WARN, naming the cull). v0.12: the flagged pairs (land and grid) go to drop1, whose
      cull these guards bound; r2() stays (the self-test calls it).
  The kit's date screen no longer stops admit: a screened date stays in the network (R4: the phase dfit tests it on the
  velocity fit after wmask) unless R3 finds it dead. --decide auto takes the rules' exclusions; --decide ask asks them
  (DECISION) when there are any. recon/admission.txt, the operator's, takes the place of the rules (INFO), and the rules'
  result is recorded beside it.
  D9  unwrapError: no, MintPy's default, unless recon/admission.txt names the method (bridging takes a linear ramp), or
      (v0.10, R5) recon/d9ab_decision.json records d9ab's bridging verdict taken under --decide auto on this same network.
      The mean component fraction of the kept pairs over the kit's G19 valid area is recorded as evidence.
recon/admission.txt (the operator's, optional): MintPy's own key = value lines, any of
  mintpy.network.excludeDate = no | YYYYMMDD[,YYYYMMDD...]
  mintpy.network.excludeDate12 = no | auto | YYYYMMDD_YYYYMMDD[,...]
  mintpy.unwrapError.method = no | bridging
Every value is checked against the network. The decisions go into recon/admission.json, which mcfg reads (its cfg keys
are v0.9's four) and dfit (decisions.r4).

Gates
  G5a.1  igram PASS on record; Igrams as igram recorded it                                            FAIL
  G5a.2  environment                                                                                   ERROR
  G5a.3  the kit's linog_admit.py at its pin; G5a.3w the water tool linog_watermask.py at its pin      FAIL
  G5a.4  recon/admission.txt, when present: known keys, values in the network                         FAIL
  G5a.8  (v0.13, R7-e) recon/d2_decision.json, when present: R7's dates, which R3's share counts      INFO / FAIL
  G20    the kit's admission: every pair read; rc 1 with the printout whole (its whole-grid proposal would
         split the network): WARN                                                                FAIL / WARN
  G5a.6  the water and the land (R1): hgt.rdr read; the land's pixels against ADMIT_LAND_MIN_PX  FAIL / WARN / INFO
  G5a.7  the kit's arithmetic recomputed over the whole grid prints the kit's lines (the mirror)        FAIL
  R1     the kit over land: the flagged pairs and the screened dates (and the whole grid's, beside)    INFO
  R3     dead and thin dates                                                           PASS / INFO / DECISION
  R2     the pair cull: v0.12, the flagged pairs handed to drop1                                PASS / INFO
  D1d    v0.12: recon/drop1_decision.json, when present: applied (INFO); not applied: the operator's file or R3 decides
         (INFO), another network, other interferograms or another basis (WARN); unreadable          INFO / WARN / FAIL
  D3     the exclusions: the rules' (PASS, INFO), asked under ask (DECISION), or the operator's (INFO); v0.12: with
         drop1's cull taken from recon/drop1_decision.json (INFO)
  G5a.5  the network after them: one component, every kept date with 2 pairs or more                  FAIL
  R4     the screened dates left in the network, for dfit's A/B                                        INFO
  D9     unwrapError: no (PASS), the operator's or R5's (INFO); an R5 decision on another network (WARN)
--dryrun DIR: the same, with recon/admission.json and the kit's log under DIR; a plan only when the frame's igram has
not run. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import ast
import glob
import hashlib
import json
import math
import os
import re
import warnings

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'admit', '5a', 4   # v0.12: R2's cull is drop1's (v0.10: 3, R1 to R3 decide D3; v0.8: 2)
KIT = 'linog_admit.py'
WATER = 'linog_watermask.py'
KEYS = ('mintpy.network.excludeDate', 'mintpy.network.excludeDate12', 'mintpy.unwrapError.method')
RULES = ('ADMIT_LAND_MIN_PX', 'ADMIT_DEAD_SHARE', 'ADMIT_EXCL_MAX_FRAC', 'ADMIT_CULL_MAX_FRAC')
DECISION_FILE = os.path.join('recon', 'd9ab_decision.json')   # R5: d9ab writes it under --decide auto
D1_FILE = os.path.join('recon', 'drop1_decision.json')         # v0.12: drop1 writes it under --decide auto
HGT = os.path.join('geom_reference', 'hgt.rdr')
NOHEIGHT = 1e5   # |h| beyond this is no height (the water tool reads geometryRadar.h5 so, RD10 hgt.rdr)
KIT_ARGS = (('--screen-mult', 'screen_mult'), ('--min-largest', 'min_largest'), ('--min-R', 'min_R'))


# ---------------------------------------------------------------- the kit's printout (as v0.9), and its lines
def parse_kit(out):
    """The kit's printout: pairs, dates, the untrustworthy pairs, the RESULT and the two cfg lines."""
    r = {}
    m = re.search(r'^G20 ADMISSION GATE\s+pairs=(\d+)\s+dates=(\d+)\s+frame median peak=([\d.]+) cycles', out, re.M)
    if m:
        r.update(pairs=int(m.group(1)), dates=int(m.group(2)), median_peak=float(m.group(3)))
    m = re.search(r'^\s+pairs in\s+(\d+)\s+dropped by date (\d+)\s+dropped by pair (\d+)\s+kept (\d+)', out, re.M)
    if m:
        r.update(kept=int(m.group(4)), by_date=int(m.group(2)), by_pair=int(m.group(3)))
    m = re.search(r'^\s+dates kept (\d+)\s+network components (\d+)\s+min degree (\d+) \((\d{8})\)', out, re.M)
    if m:
        r.update(dates_kept=int(m.group(1)), components=int(m.group(2)), min_degree=int(m.group(3)), min_degree_date=m.group(4))
    m = re.search(r'^mintpy\.network\.excludeDate\s+=\s*(\S+)\s*$', out, re.M)
    r['excludeDate'] = m.group(1) if m else None
    m = re.search(r'^mintpy\.network\.excludeDate12\s+=\s*(\S+)\s*$', out, re.M)
    r['excludeDate12'] = m.group(1) if m else None
    r['untrustworthy'] = [dict(pair=x.group(1), coh=num(x.group(2)), R=num(x.group(3)), largest=num(x.group(4)))
                          for x in re.finditer(r'^(\d{8}_\d{8})\s+(\S+)\s+(\S+)\s+(\S+)\s+(yes|no)\s*$', out, re.M)]
    screen = re.findall(r'^(\d{8})\s+\d+\s+[\d.]+\s+([\d.]+)x\s+.*PHASE SCREEN', out, re.M)
    r['screen'] = [d for d, _ in screen]
    top = sorted(((float(x), d) for d, x in re.findall(r'^(\d{8})\s+\d+\s+[\d.]+\s+([\d.]+)x', out, re.M)), reverse=True)[:3]
    r['top_dates'] = [dict(date=d, ratio=v) for v, d in top]
    return r


def kit_lines(out):
    """The kit's printed lines by kind (RD10's admit_log): the header, the per-date rows, the untrustworthy pairs, RESULT."""
    L = [ln.rstrip() for ln in out.splitlines()]
    return dict(head=[ln for ln in L if ln.startswith('G20 ADMISSION GATE')], rows=[ln for ln in L if re.match(r'^\d{8} ', ln)],
                urows=[ln for ln in L if re.match(r'^\d{8}_\d{8} ', ln)],
                res=[ln for ln in L if ln.startswith('  pairs in ') or ln.startswith('  dates kept ')])


def num(x):
    try:
        return float(x)
    except ValueError:
        return float('nan')


def as_list(v):
    return [] if v in (None, '', 'no', 'auto', 'none') else [x.strip() for x in v.split(',') if x.strip()]


def read_operator(p, dates, pairs):
    """(values, problems) of recon/admission.txt."""
    vals, bad = {}, []
    for i, ln in enumerate(open(p), 1):
        s = ln.split('#', 1)[0].strip()
        if not s:
            continue
        m = re.match(r'^([\w.]+)\s*=\s*(\S*)\s*$', s)
        if not m or m.group(1) not in KEYS:
            bad.append('line %d: %r is not one of %s' % (i, s, ', '.join(KEYS)))
            continue
        k, v = m.group(1), m.group(2)
        if k in vals:
            bad.append('line %d: %s given twice' % (i, k))
        vals[k] = v
        if k.endswith('excludeDate'):
            bad += ['line %d: %s is not a date of the network' % (i, d) for d in as_list(v) if d not in dates]
        elif k.endswith('excludeDate12'):
            bad += ['line %d: %s is not a pair of the network' % (i, x) for x in as_list(v) if x not in pairs]
        elif v not in ('no', 'bridging'):
            bad.append('line %d: unwrapError.method %r (no or bridging)' % (i, v))
    return vals, bad


def kept_pairs(pairs, ex_dates, ex_pairs):
    return [p for p in pairs if p not in ex_pairs and not any(d in ex_dates for d in p.split('_'))]


# ---------------------------------------------------------------- R2 and R3 (standard library: the self-test calls them)
def degrees(pairs):
    deg = {}
    for p in pairs:
        for d in p.split('_'):
            deg[d] = deg.get(d, 0) + 1
    return deg


def ncomp(pairs):
    dates = sorted(set(d for p in pairs for d in p.split('_')))
    return len(P3.network_components(dates, [p.split('_') for p in pairs])) if pairs else 0


def network_md5(pairs):
    """The network a decision was taken on (R5's decision file names it): the kept pairs, sorted."""
    return C.md5_obj(sorted(pairs))


def drop1_basis(flagged, under, m):
    """v0.12: what a drop1 cull rests on beside the network and the interferograms: the pairs handed to drop1, R1's land
    floor, and the rule's settings (peers, threshold, cap; r2, record 127: the minimum peer count; v0.13 r2, the ascending
    record 18.3: the split rule's DROP1_PEERS_SIDE and DROP1_PEERS_BALANCE, so a file made under v0.12 r2's rule, whose basis
    knew neither, is not applied under the new one). A decision file on another basis is not applied (D1d)."""
    return C.md5_obj(dict(flagged=sorted(flagged), under_floor=bool(under), peers=m.get('DROP1_PEERS'), thr=m.get('DROP1_TCOH_MIN'),
                          cap=m.get('ADMIT_CULL_MAX_FRAC'), min_peers=m.get('DROP1_MIN_PEERS'), side=m.get('DROP1_PEERS_SIDE'),
                          balance=m.get('DROP1_PEERS_BALANCE')))


def r7_count(W):
    """v0.13, R7-e (11.7): (the dates coarse's D2 loop took, the decision's md5, the reason it is unreadable) from
    recon/d2_decision.json: (0, None, None) without the file; (0, 'unreadable', why) when it is not R7's (G5a.8 FAILs)."""
    try:
        dec, m5 = C.d2_decision(W)
    except ValueError as e:
        return 0, 'unreadable', str(e)
    return len(C.d2_dates(dec)), m5, None


def r3(dates, pairs, flagged, ref, min_dates, dead_share, excl_max, r7=0):
    """R3 (record 108.3): dead and thin dates leave the network until none is left. dates: the network's dates; pairs: its
    pairs; flagged: the pairs R1 flags over land; ref: D1's reference date; r7 (v0.13, R7-e, 11.7): the dates coarse's D2
    loop took before, which the share counts with R3's own, over the network's dates and R7's. Returns dict(excluded=
    [dict(date, why, pairs, flagged)], pairs (the network left), dates_left, ok, problems)."""
    flagged = set(flagged)
    out, ex = [], []
    left = list(pairs)
    while True:
        deg = degrees(left)
        alive = [d for d in dates if d not in ex]
        thin = [d for d in alive if deg.get(d, 0) < 2]
        if thin:
            for d in thin:
                out.append(dict(date=d, why='thin: %d pair%s in the network as it stands' % (deg.get(d, 0), '' if deg.get(d, 0) == 1 else 's'),
                                pairs=deg.get(d, 0), flagged=sum(1 for p in left if d in p.split('_') and p in flagged)))
            ex += thin
            left = [p for p in left if not any(x in ex for x in p.split('_'))]
            continue
        dead = []
        for d in alive:
            n = deg.get(d, 0)
            f = sum(1 for p in left if d in p.split('_') and p in flagged)
            if n and f > dead_share * n:
                dead.append((-(f / float(n)), -f, d, n))
        if not dead:
            break
        dead.sort()
        share, nf, d, n = dead[0]
        out.append(dict(date=d, why='dead: %d of its %d pairs flagged over land (more than %g)' % (-nf, n, dead_share), pairs=n, flagged=-nf))
        ex.append(d)
        left = [p for p in left if d not in p.split('_')]
    dleft = sorted(set(x for p in left for x in p.split('_')))
    bad = []
    if out:
        if len(dleft) < min_dates:
            bad.append('%d dates left, under min_dates %d' % (len(dleft), min_dates))
        if ncomp(left) != 1:
            bad.append('the network left is in %d components' % ncomp(left))
        if len(ex) + r7 > excl_max * (len(dates) + r7):
            bad.append(('%d of %d dates excluded (%.1f %%), over %g %%' % (len(ex), len(dates), 100.0 * len(ex) / max(len(dates), 1),
                                                                        100 * excl_max)) if not r7 else
                       '%d of %d dates excluded: R3\'s %d and R7\'s %d (recon/d2_decision.json) of the network\'s %d and R7\'s (%.1f %%), '
                       'over %g %%' % (len(ex) + r7, len(dates) + r7, len(ex), r7, len(dates),
                                       100.0 * (len(ex) + r7) / max(len(dates) + r7, 1), 100 * excl_max))
        if ref in ex:
            bad.append('D1\'s reference date %s would be excluded' % ref)
    return dict(excluded=out, dates=sorted(ex), pairs=left, dates_left=dleft, ok=not bad, problems=bad)


def r2(net, flagged, cap):
    """R2 (record 108.3): the flagged pairs of the network net taken whole, or none. dict(cull, taken, frac, why)."""
    cull = sorted(p for p in net if p in set(flagged))
    if not cull:
        return dict(cull=[], taken=False, frac=0.0, why='no pair flagged in the network R3 leaves')
    frac = len(cull) / float(len(net))
    left = [p for p in net if p not in cull]
    deg = degrees(left)
    dates = sorted(set(d for p in net for d in p.split('_')))
    low = sorted(d for d in dates if deg.get(d, 0) < 2)
    bad = []
    if frac > cap:
        bad.append('%d of %d pairs (%.1f %%), over %g %%' % (len(cull), len(net), 100 * frac, 100 * cap))
    if ncomp(left) != 1:
        bad.append('the network left would be in %d components' % ncomp(left))
    if low:
        bad.append('dates left with fewer than 2 pairs: %s' % ', '.join(low))
    return dict(cull=cull, taken=not bad, frac=frac, why='; '.join(bad) or '%d of %d pairs (%.1f %%), one component, every date in 2 pairs '
                'or more' % (len(cull), len(net), 100 * frac))


# ---------------------------------------------------------------- R1: the kit's arithmetic over land (numpy, scipy)
def fn_from(path, name, pin, ns):
    """The source text of function `name` in the pinned tool at path, compiled into ns (RD10's way). (function, its text's
    md5)."""
    got = C.md5_file(path)
    if got != pin:
        raise ValueError('%s md5 %s, not the pinned %s' % (path, got, pin))
    src = open(path).read()
    node = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(node) != 1:
        raise ValueError('%s holds %d functions %s()' % (path, len(node), name))
    seg = ast.get_source_segment(src, node[0])
    exec(compile(seg, '%s:%s' % (path, name), 'exec'), ns)   # noqa: S102 -- the pinned tool's own text
    return ns[name], hashlib.md5(seg.encode()).hexdigest()


def kit_defaults(path):
    """The kit's own thresholds: the defaults of its --screen-mult, --min-largest and --min-R arguments, read from its source."""
    out = {}
    for n in ast.walk(ast.parse(open(path).read())):
        if isinstance(n, ast.Call) and getattr(n.func, 'attr', None) == 'add_argument' and n.args and isinstance(n.args[0], ast.Constant):
            for flag, key in KIT_ARGS:
                if n.args[0].value == flag:
                    for kw in n.keywords:
                        if kw.arg == 'default':
                            out[key] = float(ast.literal_eval(kw.value))
    miss = [k for _, k in KIT_ARGS if k not in out]
    if miss:
        raise ValueError('%s: no default found for %s' % (path, ', '.join(miss)))
    return out


def kit_functions(env, m, q):
    """conc() of the kit's linog_admit.py and flat_masks() of its linog_watermask.py, from their pinned source, with numpy and
    scipy.ndimage; and the kit's thresholds. dict(conc, flat_masks, conc_md5, flat_masks_md5, defaults)."""
    import numpy as np
    from scipy import ndimage as ndi
    ns = dict(np=np, ndi=ndi)
    conc, c5 = fn_from(os.path.join(env['KIT'], KIT), 'conc', m['KIT_ADMIT_MD5'], ns)
    flat, f5 = fn_from(os.path.join(env['KIT'], WATER), 'flat_masks', q['KIT_WATERMASK_MD5'], ns)
    return dict(conc=conc, flat_masks=flat, conc_md5=c5, flat_masks_md5=f5, defaults=kit_defaults(os.path.join(env['KIT'], KIT)))


def land_of(W, gw, gl, flat_masks):
    """The frame's water and land from geom_reference/hgt.rdr (float64, gl x gw). dict(water, land arrays; counts)."""
    import numpy as np
    p = os.path.join(W, HGT)
    xw, xl = P3.xml_dims(p + '.xml')
    if not os.path.isfile(p) or os.path.getsize(p) != 8 * gw * gl or (xw, xl) != (gw, gl):
        raise ValueError('%s is %s B with .xml %s x %s; want %d x %d float64 (%d B)' % (
            p, os.path.getsize(p) if os.path.isfile(p) else 'absent', xw, xl, gw, gl, 8 * gw * gl))
    h = np.fromfile(p, dtype='<f8', count=gw * gl).reshape(gl, gw).astype(float)
    h[np.abs(h) > NOHEIGHT] = np.nan
    lo, hi = flat_masks(h)
    fin = np.isfinite(h)
    water = lo | hi
    land = fin & ~water
    return dict(water=water, land=land, n=dict(grid=int(gw * gl), water=int(water.sum()), water_low=int(lo.sum()), water_high=int(hi.sum()),
                                              land=int(land.sum()), no_height=int((~fin).sum())))


def pair_values(ip, land, conc, gw, gl):
    """One pair as the kit reads it (its lines 55 to 79): over the whole grid and over land. None when the .int is short
    (the kit skips such a pair)."""
    import numpy as np
    G = gw * gl
    z = np.fromfile(ip, dtype=np.complex64, count=G)
    if z.size < G:
        return None
    z = z.reshape(gl, gw)
    ok = np.isfinite(z) & (np.abs(z) > 0)
    u = np.zeros_like(z)
    u[ok] = z[ok] / np.abs(z[ok])
    v = dict(whole={}, land={})
    for k, msk in (('whole', None), ('land', land)):
        uu = u if msk is None else np.where(msk, u, np.zeros_like(u))
        v[k]['R'] = max(conc(uu, 0), conc(uu, 1))
        S = np.abs(np.fft.fft2(uu)) ** 2
        S[0, 0] = 0.0
        kk = int(np.argmax(S))
        fy, fx = kk // gw, kk % gw
        if fy > gl // 2:
            fy -= gl
        if fx > gw // 2:
            fx -= gw
        v[k]['pk'] = math.hypot(fy, fx)
        v[k]['coh'] = float('nan')
        v[k]['lg'] = float('nan')
    d = os.path.dirname(ip)
    cf = glob.glob(os.path.join(d, 'filt_*.cor'))
    if cf:
        c = np.fromfile(cf[0], dtype=np.float32, count=G)
        cc = c[np.isfinite(c) & (c > 0)]
        if cc.size:
            v['whole']['coh'] = float(cc.mean())
        if c.size == G:
            c = c.reshape(gl, gw)
            x = c[np.isfinite(c) & (c > 0) & land]
            if x.size:
                v['land']['coh'] = float(x.mean())
    gf = glob.glob(os.path.join(d, 'filt_*snaphu.unw.conncomp'))
    if gf:
        g = np.fromfile(gf[0], dtype=np.uint8, count=G)
        if g.size == G and (g > 0).sum():   # the kit's rule: a pair with no component anywhere has no LARGEST
            bc = np.bincount(g.astype(np.int64))
            bc[0] = 0
            v['whole']['lg'] = float(bc.max()) / float(g.size)
            g2 = g.reshape(gl, gw)[land]
            if g2.size:   # over land: components only off the land give 0, not NaN
                bc = np.bincount(g2.astype(np.int64))
                bc[0] = 0
                v['land']['lg'] = float(bc.max()) / float(land.sum())
    return v


def decide(S, kd):
    """linog_admit.py's decision (its lines 83 to 142) on S {pair: dict(coh, R, pk, lg)}, in the kit's order, and the lines
    it prints. kd: the kit's thresholds."""
    import numpy as np
    from collections import defaultdict
    frame_pk = float(np.median([v['pk'] for v in S.values()]))
    bydate = defaultdict(list)
    for pr, v in S.items():
        for d in pr.split('_'):
            bydate[d].append(v)
    head = 'G20 ADMISSION GATE   pairs=%d  dates=%d  frame median peak=%.2f cycles' % (len(S), len(bydate), frame_pk)
    rows, screen, ratio = [], [], {}
    for d in sorted(bydate):
        v = bydate[d]
        mp = float(np.median([x['pk'] for x in v]))
        mr = float(np.median([x['R'] for x in v]))
        with warnings.catch_warnings():   # the kit's nanmedian of a date whose coherences are all NaN: nan, as the kit prints it
            warnings.simplefilter('ignore', RuntimeWarning)
            mc = float(np.nanmedian([x['coh'] for x in v]))
        rat = mp / frame_pk if frame_pk else 0
        tag = '*** PHASE SCREEN -> excludeDate' if rat >= kd['screen_mult'] else ''
        if tag:
            screen.append(d)
        ratio[d] = rat
        rows.append(('%s %3d  %6.2f  %5.1fx  %6.3f  %7.4f   %s' % (d, len(v), mp, rat, mr, mc, tag)).rstrip())
    bad = sorted([pr for pr, v in S.items() if (v['lg'] == v['lg'] and v['lg'] < kd['min_largest']) or v['R'] < kd['min_R']],
                 key=lambda p: S[p]['R'])
    dbd = set(pr for pr in S if any(d in screen for d in pr.split('_')))
    bad_extra = [pr for pr in bad if pr not in dbd]
    urows = [('%-22s %6.4f %6.3f   %6.1f     %s' % (pr, S[pr]['coh'], S[pr]['R'], 100 * S[pr]['lg'] if S[pr]['lg'] == S[pr]['lg'] else -1,
                                                    'yes' if pr in dbd else 'no')).rstrip() for pr in bad]
    keep = [pr for pr in S if pr not in dbd and pr not in set(bad_extra)]
    deg = defaultdict(int)
    for pr in keep:
        for d in pr.split('_'):
            deg[d] += 1
    adj = defaultdict(set)
    for pr in keep:
        x, y = pr.split('_')
        adj[x].add(y)
        adj[y].add(x)
    seen, comp = set(), 0
    for d in adj:
        if d in seen:
            continue
        comp += 1
        st = [d]
        while st:
            n = st.pop()
            if n in seen:
                continue
            seen.add(n)
            st.extend(adj[n] - seen)
    mind = (min(deg.values()), sorted(deg, key=lambda d: deg[d])[0]) if deg else (0, '-')
    res = ['  pairs in  %d   dropped by date %d   dropped by pair %d   kept %d' % (len(S), len(dbd), len(bad_extra), len(keep)),
           '  dates kept %d   network components %s   min degree %d (%s)' % (len(deg), comp, mind[0], mind[1])]
    return dict(head=[head], rows=rows, urows=urows, res=res, screen=screen, ratio=ratio, bad=bad, frame_pk=frame_pk,
                values=dict((pr, S[pr]) for pr in bad))


def mirror(K, kl):
    """Where the recomputed whole-grid printout K differs from the kit's own lines kl: [text]."""
    diff = []
    for k in ('head', 'rows', 'urows', 'res'):
        a, b = K[k], kl[k]
        if len(a) != len(b):
            diff.append('%s: %d lines, the kit %d' % (k, len(a), len(b)))
        for x, y in zip(a, b):
            if x != y:
                diff.append('%s: "%s" against the kit\'s "%s"' % (k, x, y))
    return diff


def read_pairs(W, land, conc, gw, gl):
    """{pair: values} in the kit's order (sorted Igrams/*/filt_*.int; a folder name not of 17 characters skipped)."""
    out = {}
    for ip in sorted(glob.glob(os.path.join(W, 'Igrams', '*', 'filt_*.int'))):
        pr = os.path.basename(os.path.dirname(ip))
        if len(pr) != 17 or '_' not in pr:
            continue
        v = pair_values(ip, land, conc, gw, gl)
        if v is not None:
            out[pr] = v
    return out


def clean(o):
    """o with every NaN or infinite float as None (admission.json stays JSON that jq and JavaScript read)."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return dict((k, clean(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def fmt_flag(x):
    return '%s (coherence %.4f, R %.3f, LARGEST %s)' % (x[0], x[1]['coh'], x[1]['R'], '%.1f %%' % (100 * x[1]['lg']) if x[1]['lg'] == x[1]['lg']
                                                       else 'none')


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5a: D3 (the rules R1 to R3) and D9 (unwrapError)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m, q = P1.load_env(), P2.load_stack(), P5.load_mintpy(), P6.load_p6()
    tm = P5.tools(env, m)
    wt = P6.tools(env, q, (WATER,))
    decide_mode = os.environ.get('LINOG_DECIDE', 'ask')
    optxt = os.path.join(W, 'recon', 'admission.txt')
    dfile = os.path.join(W, DECISION_FILE)
    d1file = os.path.join(W, D1_FILE)
    ri = P1.record(W, '4f', 'igram') or {}
    rt = P1.record(W, '3a', 'topo') or {}
    geo0, _ = P3.geometry(W)
    settings = dict((k, m[k]) for k in ('G19_EDGE',) + RULES)
    settings['min_dates'] = cfg.get('min_dates', '5')
    n7, d2md5, d2err = r7_count(W)   # v0.13, R7-e (11.7): R3's share counts the dates coarse's D2 loop took
    fpd = dict(logic=LOGIC, igram=ri.get('outputs', {}).get('digest'), topo=rt.get('outputs', {}).get('digest'), kit=tm[KIT][1],
               water=wt[WATER][1], settings=settings, reference=(geo0 or {}).get('ref'),
               operator=C.md5_file(optxt) if os.path.isfile(optxt) else None,
               r5=C.md5_file(dfile) if os.path.isfile(dfile) else None,
               drop1=dict(file=C.md5_file(d1file), peers=m.get('DROP1_PEERS'), thr=m.get('DROP1_TCOH_MIN'),
                          min_peers=m.get('DROP1_MIN_PEERS'), side=m.get('DROP1_PEERS_SIDE'), balance=m.get('DROP1_PEERS_BALANCE'))
               if os.path.isfile(d1file) else None)   # v0.12: a decision's basis re-read when drop1's settings change (v0.13 r2:
    # the split rule's two settings too, 18.3's D1d: only while the file exists, so a frame without one keeps its fingerprint)
    if d2md5:   # only when the file exists: LOGIC stays 4 and a frame without it keeps its fingerprint
        fpd['d2_decision'] = d2md5
    fp = C.md5_obj(fpd)
    if a.state:
        print(P5.state(recdir, W, PHASE, IDX, fp))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   settings=settings, decide=decide_mode,
                                                                   tools={KIT: dict(path=tm[KIT][0], md5=tm[KIT][1]),
                                                                          WATER: dict(path=wt[WATER][0], md5=wt[WATER][1])}))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun, '   decide %s' % decide_mode)
    ri, have = P5.igram_prior(st, 'G5a.1', W, recdir, a.dryrun)
    if not ri:
        return st.finish()
    if not P2.env_gate(st, 'G5a.2', env, s):
        return st.finish()
    if not P3.pins_gate(st, 'G5a.3', {KIT: tm[KIT]}, 'the kit\'s admission tool'):
        return st.finish()
    if not P3.pins_gate(st, 'G5a.3w', {WATER: wt[WATER]}, 'the water tool (R1\'s land)'):
        return st.finish()
    if not have:
        return P5.plan_only(st, ['would run %s on every pair of Igrams/, read the kit\'s statistics over land (R1), then R3 and R2, and '
                                 'decide D3 and D9 (decide %s)' % (KIT, decide_mode)], 'the frame has no interferograms yet')
    geo, _ = P3.geometry(W)
    if not geo:
        st.gate('G5a.1g', 'the reference geometry', 'FAIL', 'recon/reference.json gives no geometry')
        return st.finish()
    gw, gl, ref = geo['gw'], geo['gl'], geo['ref']
    pairs = P5.pairs_of(W)
    dates = sorted(set(d for p in pairs for d in p.split('_')))
    op, obad = ({}, [])
    if os.path.isfile(optxt):
        op, obad = read_operator(optxt, dates, pairs)
        st.gate('G5a.4', 'recon/admission.txt', 'FAIL' if obad else 'PASS', '; '.join('%s = %s' % kv for kv in sorted(op.items())) or
                'no keys', 'known keys, values in the network', '\n'.join(obad[:8]))
        if obad:
            return st.finish()
    else:
        st.gate('G5a.4', 'recon/admission.txt', 'INFO', 'absent: no choice recorded by the operator', 'optional')
    if d2err:   # v0.13, R7-e (the part 5 review's P5-09): R3's share cannot count R7's dates from an unreadable decision
        st.gate('G5a.8', 'R7\'s dates (recon/d2_decision.json)', 'FAIL', d2err, 'the decision as coarse wrote it (11.3)',
                'a person looks: R3\'s 25 % counts R7\'s dates with its own (11.7); recon and the reference stop on this file too')
        return st.finish()
    if d2md5:   # only when the file exists, as its fingerprint key
        st.gate('G5a.8', 'R7\'s dates (recon/d2_decision.json)', 'INFO', '%d date(s) taken by coarse\'s D2 loop, counted in R3\'s '
                'share with R3\'s own (11.7); the file\'s md5 %s' % (n7, d2md5), 'R7-e')
    lg = P1.new_log(os.path.join(recdir, 'logs', 'p5', 'admit', 'linog_admit.log'))
    krc, out = P3.kit_run(env, KIT, ['--dir', 'Igrams', '--width', str(gw), '--length', str(gl)], W, lg)
    k = parse_kit(out)
    # the kit exits 1 when the network left by its own (whole-grid) proposal has more than one component: with its printout
    # whole, that is a property of the whole-grid proposal, which v0.10 does not take; anything else is a FAIL
    parsed = k.get('pairs') == len(pairs) and k.get('excludeDate') is not None and k.get('excludeDate12') is not None \
        and k.get('components') is not None
    split = parsed and krc == 1 and k.get('components', 0) > 1
    g20 = 'PASS' if parsed and krc == 0 else 'WARN' if split else 'FAIL'
    st.gate('G20', 'the kit\'s admission (G18, G20)', g20, '%s pairs of %d read, %s dates; frame median '
            'peak %s cycles; highest dates %s; untrustworthy pairs %d; proposal excludeDate = %s, excludeDate12 = %s; network '
            'components %s, min degree %s (%s); rc %d (the whole grid: R1 reads the land)' % (
                k.get('pairs'), len(pairs), k.get('dates'), k.get('median_peak'), ', '.join('%s %.1fx' % (x['date'], x['ratio'])
                                                                                        for x in k.get('top_dates', [])),
                len(k.get('untrustworthy', [])), k.get('excludeDate'), k.get('excludeDate12'), k.get('components'),
                k.get('min_degree'), k.get('min_degree_date'), krc), 'every pair read; rc 0: one component',
            ('' if g20 == 'PASS' else 'the kit\'s whole-grid proposal leaves the network in %s components (rc 1); v0.10 takes R1 to R3, '
             'not that proposal' % k.get('components') if split else 'log %s\n%s' % (lg, P3.tail(lg))))
    st.rec['outputs'] = dict(kit=dict(rc=krc, log=lg, **{x: k.get(x) for x in ('pairs', 'dates', 'median_peak', 'kept', 'components',
                                                                                 'min_degree', 'min_degree_date', 'excludeDate',
                                                                                 'excludeDate12', 'untrustworthy', 'top_dates',
                                                                                 'screen')}))
    if g20 == 'FAIL':
        return st.finish()

    # ---- R1: the kit's statistics over land, the mirror
    try:
        kf = kit_functions(env, m, q)
        L = land_of(W, gw, gl, kf['flat_masks'])
    except Exception as e:  # noqa: BLE001
        st.gate('G5a.6', 'the water and the land (R1)', 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:300]),
                'geom_reference/hgt.rdr read; the kit\'s conc() and the water tool\'s flat_masks() from their pinned source')
        return st.finish()
    n = L['n']
    floor = int(m['ADMIT_LAND_MIN_PX'])
    under = n['land'] < floor
    st.gate('G5a.6', 'the water and the land (R1)', 'WARN' if under else 'INFO', 'land %d px of %d (%.1f %%); water %d px (below 60 m %d, '
            'at 60 m or more %d); no height %d px; the water tool\'s flat_masks() %s, the kit\'s conc() %s' % (
                n['land'], n['grid'], 100.0 * n['land'] / max(n['grid'], 1), n['water'], n['water_low'], n['water_high'], n['no_height'],
                kf['flat_masks_md5'][:8], kf['conc_md5'][:8]), '%d land px or more (R1\'s floor)' % floor,
            'under the floor: no pair is flagged and no date screened over land; R3 reads the thin dates only' if under else '')
    import time
    t0 = time.time()
    PV = read_pairs(W, L['land'], kf['conc'], gw, gl)
    Kw = decide(dict((pr, v['whole']) for pr, v in PV.items()), kf['defaults'])
    Kl = decide(dict((pr, v['land']) for pr, v in PV.items()), kf['defaults']) if PV else None
    dif = mirror(Kw, kit_lines(out)) if PV else ['no pair read']
    st.gate('G5a.7', 'the kit\'s arithmetic, recomputed', 'FAIL' if dif else 'PASS', '%d pairs read again in %.0f s; over the whole grid the '
            'printout %s' % (len(PV), time.time() - t0, 'is the kit\'s line for line (%d per-date rows, %d untrustworthy pairs, the header '
                             'and RESULT)' % (len(Kw['rows']), len(Kw['urows'])) if not dif else 'differs from the kit\'s in %d places' % len(dif)),
            'the kit\'s own lines (RD10\'s mirror)', '\n'.join(dif[:6]))
    if dif:
        return st.finish()
    flag_l = [] if under else list(Kl['bad'])
    screen_l = [] if under else list(Kl['screen'])
    vals_l = dict((pr, PV[pr]['land']) for pr in Kl['bad'])
    st.gate('R1', 'the kit over land', 'INFO', '%s pairs flagged over land%s; screened dates %s; over the whole grid %d flagged, '
            'screened %s; frame median peak %.2f cycles over land, %.2f over the whole grid' % (
                len(flag_l), (': ' + '; '.join(fmt_flag((pr, vals_l[pr])) for pr in flag_l[:8]) + (' and %d more' % (len(flag_l) - 8)
                                                                                                   if len(flag_l) > 8 else '')) if flag_l else '',
                ', '.join('%s %.1fx' % (d, Kl['ratio'][d]) for d in screen_l) or 'none', len(Kw['bad']),
                ', '.join(Kw['screen']) or 'none', Kl['frame_pk'], Kw['frame_pk']),
            'the kit\'s rule (LARGEST under %g or R under %g; the screen at %gx) over land' % (
                kf['defaults']['min_largest'], kf['defaults']['min_R'], kf['defaults']['screen_mult']),
            'under the floor: the land figures are recorded, not used' if under else '')
    r1 = dict(land=n, floor=floor, under_floor=under, flagged=flag_l, screened=screen_l,
              flagged_values=dict((pr, clean(vals_l[pr])) for pr in Kl['bad']), screened_ratio=dict((d, Kl['ratio'][d]) for d in Kl['screen']),
              land_flagged_all=list(Kl['bad']), land_screened_all=list(Kl['screen']), whole_flagged=list(Kw['bad']), whole_screened=list(Kw['screen']),
              frame_peak_land=Kl['frame_pk'], frame_peak_whole=Kw['frame_pk'], functions=dict(conc=kf['conc_md5'], flat_masks=kf['flat_masks_md5']),
              kit=kf['defaults'])

    # ---- R3, and R2's handoff to drop1 (v0.12; when the operator's file names the exclusions, the rules are recorded, not acted on)
    opx = 'mintpy.network.excludeDate' in op or 'mintpy.network.excludeDate12' in op
    R3 = r3(dates, pairs, flag_l, ref, int(cfg.get('min_dates', 5)), float(m['ADMIT_DEAD_SHARE']), float(m['ADMIT_EXCL_MAX_FRAC']),
            r7=n7)
    if not R3['excluded']:
        st.gate('R3', 'dead and thin dates', 'PASS', 'none: every date in 2 pairs or more, none with more than %g of its pairs flagged' % (
            float(m['ADMIT_DEAD_SHARE'])), 'record 108.3')
    else:
        st.gate('R3', 'dead and thin dates', 'INFO' if R3['ok'] or opx else 'DECISION', '%s; %d dates and %d pairs left (min degree %s)' % (
            '; '.join('%s %s' % (x['date'], x['why']) for x in R3['excluded']), len(R3['dates_left']), len(R3['pairs']),
            min(degrees(R3['pairs']).values()) if R3['pairs'] else 0),
            'the rest: min_dates %s or more in one component, every date in 2 pairs or more, at most %g %% of the dates, D1\'s reference '
            '%s kept' % (cfg.get('min_dates', 5), 100 * float(m['ADMIT_EXCL_MAX_FRAC']), ref),
            '' if R3['ok'] else 'past R3\'s limits (%s): a person\'s choice, in either --decide mode; %s' % ('; '.join(R3['problems']),
            'recon/admission.txt names the exclusions, and D3 takes them' if opx else 'write it into %s (MintPy key = value lines: '
            'mintpy.network.excludeDate, excludeDate12), then run again' % optxt))
    flagged_all = [] if under else sorted(set(flag_l) | set(Kw['bad']))
    in_net = sorted(p for p in R3['pairs'] if p in set(flagged_all)) if R3['ok'] else []
    why2 = 'v0.12 (record 124.7): R2 culls no pair by itself; %s' % (
        'under R1\'s land floor: no pair to drop1' if under else '%d flagged pair%s of the network R3 leaves (over land %d, over the whole grid '
        '%d) go%s to drop1\'s peer test after sbas' % (len(in_net), '' if len(in_net) == 1 else 's', len(set(flag_l) & set(in_net)),
                                                     len(set(Kw['bad']) & set(in_net)), 'es' if len(in_net) == 1 else '')
        if in_net else 'no flagged pair in the network R3 leaves')
    if R3['ok']:
        st.gate('R2', 'the pair cull (v0.12: drop1)', 'INFO' if in_net else 'PASS', why2 + (': %s' % ', '.join(in_net[:12]) + (
            ' and %d more' % (len(in_net) - 12) if len(in_net) > 12 else '') if in_net else ''),
            'record 124.7: every pair R1 flags, land or grid, is tested against its peers after sbas (drop1); R2\'s guards bound that cull')
    rule_dates = list(R3['dates'])
    # drop1's decision (v0.12): taken under --decide auto on the network the rules leave, on the same interferograms
    d1, d1note, d1v = None, '', 'WARN'
    if os.path.isfile(d1file):
        try:
            d1 = json.load(open(d1file))
        except ValueError as e:
            st.gate('D1d', 'drop1\'s decision', 'FAIL', '%s unreadable: %s' % (d1file, e))
            return st.finish()
    net_rules = kept_pairs(pairs, rule_dates, [])
    d1cull = sorted((d1 or {}).get('cull') or [])
    igd = ri.get('outputs', {}).get('digest')
    basis = drop1_basis(flagged_all, under, m)
    d1_ok = False
    if d1:
        if opx:
            d1note, d1v = '%s not applied: the operator\'s recon/admission.txt names the exclusions' % D1_FILE, 'INFO'
        elif not R3['ok']:
            d1note, d1v = '%s not applied: R3 is past its limits' % D1_FILE, 'INFO'
        elif d1.get('network') != network_md5(net_rules):
            d1note = '%s records a cull taken on another network (%s, the rules\' network now %s): not applied; drop1 tests this one' % (
                D1_FILE, str(d1.get('network'))[:8], network_md5(net_rules)[:8])
        elif d1.get('igram') != igd:
            d1note = '%s records a cull taken on other interferograms (igram\'s digest %s, now %s): not applied; drop1 tests these' % (
                D1_FILE, str(d1.get('igram'))[:8], str(igd)[:8])
        elif d1.get('basis') != basis:
            d1note = ('%s records a cull taken on another basis (the flagged pairs, R1\'s land floor or drop1\'s settings have changed since; '
                      '%s, now %s): not applied; drop1 tests again' % (D1_FILE, str(d1.get('basis'))[:8], basis[:8]))
        elif not d1cull or any(x not in set(net_rules) for x in d1cull):
            d1note = '%s names no cull, or pairs outside the network: not applied' % D1_FILE
        else:
            d1_ok = True
        st.gate('D1d', 'drop1\'s decision', 'INFO' if d1_ok else d1v, ('%s: %d pair%s culled (%s), taken under --decide auto on this network: '
                                                                       'applied' % (D1_FILE, len(d1cull), '' if len(d1cull) == 1 else 's',
                                                                                    ', '.join(d1cull[:8]))) if d1_ok else d1note,
                'v0.12: taken on the network the rules leave, on the same interferograms')
    rule_pairs = d1cull if d1_ok else []
    rules = dict(excludeDate=rule_dates, excludeDate12=rule_pairs, kept=len(kept_pairs(pairs, rule_dates, rule_pairs)), ok=R3['ok'])

    # ---- D3
    dec = dict(r1=r1, r3=dict(excluded=R3['excluded'], ok=R3['ok'], problems=R3['problems'], dates_left=len(R3['dates_left'])),
               r2=dict(cull=[], taken=False, frac=0.0, why=why2),
               drop1=dict(flagged=flagged_all, land=[] if under else list(flag_l), whole=list(Kw['bad']), under_floor=under, in_network=in_net,
                          basis=basis, decision=dict(file=D1_FILE, md5=C.md5_file(d1file), applied=d1_ok, cull=d1cull, note=d1note) if d1 else None))
    howto = ('write your choice into %s as MintPy key = value lines, then run again:\n'
             '  mintpy.network.excludeDate = %s\n  mintpy.network.excludeDate12 = %s' % (
                 optxt, ','.join(rule_dates) or 'no', ','.join(rule_pairs) or 'auto'))
    if opx:
        # a key the operator left out excludes nothing
        e_dates = as_list(op.get('mintpy.network.excludeDate', 'no'))
        e_pairs = as_list(op.get('mintpy.network.excludeDate12', 'auto'))
        src, v = 'the operator (recon/admission.txt)', 'INFO'
    elif not R3['ok']:
        e_dates, e_pairs, src, v = rule_dates, rule_pairs, None, 'DECISION'
    elif not rule_dates and not rule_pairs:
        e_dates, e_pairs, src, v = [], [], 'the rules R1 to R3: nothing to exclude', 'PASS'
    elif not rule_dates:   # v0.12: drop1's cull alone, taken under --decide auto
        e_dates, e_pairs, src, v = [], rule_pairs, 'the rules R1 to R3 and drop1\'s peer test (%s, taken under --decide auto)' % D1_FILE, 'INFO'
    elif decide_mode == 'auto':
        e_dates, e_pairs, src, v = rule_dates, rule_pairs, 'the rules R1 to R3 (--decide auto)%s' % (
            '; drop1\'s peer test (%s)' % D1_FILE if rule_pairs else ''), 'INFO'
    else:
        e_dates, e_pairs, src, v = rule_dates, rule_pairs, None, 'DECISION'
    kept = kept_pairs(pairs, e_dates, e_pairs)
    agree = sorted(e_dates) == sorted(rule_dates) and sorted(e_pairs) == sorted(rule_pairs)
    if v == 'DECISION':
        st.gate('D3', 'the exclusions', 'DECISION', 'the rules: excludeDate = %s, excludeDate12 = %s (%d of %d pairs kept)%s' % (
            ','.join(rule_dates) or 'no', ','.join(rule_pairs) or 'auto', len(kept), len(pairs), '' if R3['ok'] else '; R3 past its limits'),
            'record 108.3: R1 to R3', ('R3 is past its limits: that is always your choice;\n' if not R3['ok'] else
                                       'the rules\' exclusions are taken by --decide auto; under ask they are yours;\n') + howto)
    else:
        st.gate('D3', 'the exclusions', v, 'excludeDate = %s, excludeDate12 = %s: %d of %d pairs kept (%s)%s' % (
            ','.join(e_dates) or 'no', ','.join(e_pairs) or 'auto', len(kept), len(pairs), src,
            '' if src and not src.startswith('the operator') else '; the rules: excludeDate = %s, excludeDate12 = %s, %d kept: %s' % (
                ','.join(rule_dates) or 'no', ','.join(rule_pairs) or 'auto', rules['kept'], 'agree' if agree else 'DIFFER')),
            'record 108.3: R1 to R3; v0.12: drop1\'s cull (124.7)', '')
    dec['d3'] = dict(excludeDate=e_dates, excludeDate12=e_pairs, source=src, rules=dict(rules, agree=agree),
                     proposal=dict(excludeDate=rule_dates, excludeDate12=rule_pairs),
                     kit=dict(excludeDate=as_list(k['excludeDate']), excludeDate12=as_list(k['excludeDate12'])))
    deg = degrees(kept)
    comps = ncomp(kept)
    lost = [d for d in dates if d not in deg and d not in e_dates]
    low = sorted(d for d, nn in deg.items() if nn < 2)
    bad = comps != 1 or lost or low
    # while D3 waits for the operator, this network is the rules': shown (INFO), not judged
    st.gate('G5a.5', 'the network after the exclusions', ('INFO' if v == 'DECISION' else 'FAIL') if bad else 'PASS', '%s%d pairs, %d dates, '
            '%d component(s); min degree %d (%s)%s' % ('the rules\': ' if v == 'DECISION' else '', len(kept), len(deg), comps,
                                                      min(deg.values()) if deg else 0, min(deg, key=lambda d: (deg[d], d)) if deg else '-',
                                                      '; dates left without a pair: %s' % ', '.join(lost) if lost else ''),
            'one component; every kept date in 2 pairs or more', ('dates with one pair: %s' % ', '.join(low)) if low else '')
    if bad or v == 'DECISION':
        st.rec['outputs'].update(decisions=dec)
        return st.finish()
    # ---- R4: the screened dates left in the network go to dfit's A/B
    cand = sorted(d for d in screen_l if d in deg)
    st.gate('R4', 'screened dates (to dfit)', 'INFO', ', '.join('%s %.1fx' % (d, Kl['ratio'][d]) for d in cand) or 'none',
            'a date the screen proposes stays in the network; the velocity fit tests it after wmask (record 108.3, R4)')
    dec['r4'] = dict(dates=cand, ratios=dict((d, Kl['ratio'][d]) for d in cand), screened=screen_l)
    # ---- D9
    try:
        cf = P5.component_fraction(W, kept, gw, gl, int(m['G19_EDGE']))
    except (OSError, ValueError) as e:
        st.gate('D9', 'unwrapError', 'FAIL', 'the component fraction cannot be computed: %s' % e)
        return st.finish()
    net = network_md5(kept)
    r5 = None
    if os.path.isfile(dfile):
        try:
            r5 = json.load(open(dfile))
        except ValueError as e:
            st.gate('D9', 'unwrapError', 'FAIL', '%s unreadable: %s' % (dfile, e))
            return st.finish()
    note9 = ''
    if 'mintpy.unwrapError.method' in op:
        meth, src9, v9 = op['mintpy.unwrapError.method'], 'the operator (recon/admission.txt)', 'INFO'
    elif r5 and r5.get('method') == 'bridging' and r5.get('network') == net:
        meth, src9, v9 = 'bridging', 'R5: d9ab\'s A/B under --decide auto (%s, %s)' % (DECISION_FILE, r5.get('folder')), 'INFO'
    elif r5:
        meth, src9, v9 = 'no', 'MintPy\'s default; the A/B after sbas (d9ab) tests bridging', 'WARN'
        note9 = ('%s records %s taken on another network (%s, this one %s): not applied; d9ab tests this network' % (
            DECISION_FILE, r5.get('method'), str(r5.get('network'))[:8], net[:8]))
    else:
        meth, src9, v9 = 'no', 'MintPy\'s default; the A/B after sbas (d9ab) tests bridging', 'PASS'
    val = 'mean component fraction %.4f over %d valid px of %d kept pairs (max %.4f; per-pair median of the main component %.4f)' % (
        cf['mean'], cf['valid'], cf['pairs'], cf['max'], cf['per_pair_median'])
    st.gate('D9', 'unwrapError', v9, val + '; unwrapError.method = %s (%s)' % (meth, src9),
            'v0.8 (record 63.8): no, MintPy\'s default, unless recon/admission.txt names it; v0.10: R5\'s decision under auto; the A/B '
            'after sbas (d9ab) applies the rule of record 62.0; the fraction is evidence', note9)
    dec['d9'] = dict(statistic=cf, proposal='no', method=meth, source=src9, r5=dict(file=DECISION_FILE, md5=C.md5_file(dfile)) if r5 else None,
                     rule='v0.8: no unless the operator names it; v0.10: R5 (d9ab under --decide auto); the A/B after sbas (record 62.0)')
    cfgv = {'mintpy.network.excludeDate': ','.join(e_dates) or 'no', 'mintpy.network.excludeDate12': ','.join(e_pairs) or 'auto',
            'mintpy.unwrapError.method': meth, 'mintpy.unwrapError.ramp': 'linear' if meth == 'bridging' else 'auto'}
    J = dict(frame='p%s/f%s' % (path, frame), written=C.utc(), decide=decide_mode, pairs=len(pairs), kept=len(kept), kept_pairs=kept,
             decisions=dec, cfg=cfgv, operator_file=optxt if os.path.isfile(optxt) else None, network_md5=net, version='v0.12 (LOGIC 4)')
    out_json = os.path.join(recdir, 'recon', 'admission.json')
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    P5.write_json(out_json, J)
    lst = P3.listing(recdir, P5.OUTS[PHASE])
    # what the later phases take from admit: the values for the template and the kept pairs (not the file's write time,
    # so a re-run that decides the same leaves mcfg and sbas CURRENT); dfit reads r4 (its own digest)
    st.rec['outputs'].update(decisions=dec, cfg=cfgv, kept=len(kept), json=out_json, json_md5=C.md5_file(out_json), files=lst,
                             digest=P3.digest(lst), decisions_md5=C.md5_obj(dict(cfg=cfgv, kept_pairs=kept)), network_md5=net,
                             r4_md5=C.md5_obj(dec['r4']), drop1_md5=C.md5_obj(dict(flagged=flagged_all, under_floor=under)))
    print('   recon/admission.json: %s' % ', '.join('%s = %s' % kv for kv in sorted(cfgv.items())))
    if a.dryrun:
        st.rec['outputs'].update(planned=True, dryrun=True)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_admit', main)
