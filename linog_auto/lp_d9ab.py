#!/usr/bin/env python3
"""lp_d9ab.py -- linog_auto Phase 5dab (v0.8): D9's A/B after sbas, by the rule of record 62.0 (RD8's test, section 63).

Runs inside lp_env.sh, after sbas and before wmask. A is the frame's mintpy/ (sbas's products, with unwrapError as admit
decided), read only; A's mask is sbas's own (mintpy/watermask/maskTempCoh.orig.h5 once wmask has run, since wmask
rewrites mintpy/maskTempCoh.h5). B is a copy made here, <frame>/d9ab/<UTC>/B/mintpy/ (in a dry run DIR/d9ab/<UTC>/...):
A's inputs/ifgramStack.h5, inputs/geometryRadar.h5, smallbaselineApp.cfg, avgSpatialCoh.h5 and maskConnComp.h5, each
checked by md5, with three keys set in B's template (mintpy.unwrapError.method bridging, mintpy.unwrapError.ramp linear,
mintpy.plot no), which then differs from A's in those three lines only. MintPy runs on B from correct_unwrap_error to
geocode (`nice -n 10 smallbaselineApp.py`, in a session of its own, stopped after D9AB_TIMEOUT_S), and the phase compares
B with A as RD8's rd8_ab.py did: the pairs bridging changed and the pixels it moved; T_int (MintPy's arithmetic) before and
after, over the kit's valid area, inside and outside A's mask; the masks, the temporal coherence and the velocity.
The rule of record 62.0, registered before RD8 ran:
  bridging if and only if MintPy on B ends rc 0 with unwrapPhase_bridging, maskTempCoh.h5, temporalCoherence.h5 and
  velocity.h5; B's mask keeps at least ceil(min(D9AB_MIN_GAIN_CAP, D9AB_MIN_GAIN_FRAC x length x width)) px more than
  A's; and the velocity std over the pixels both masks keep is no larger in B. Otherwise no.
The decision (record 63.8). unwrapError bridging (the operator's choice, or R5's): the A/B is not run, A being the
bridging run. unwrapError no: the A/B runs; its no PASSes, and so does its bridging when the operator chose no in
recon/admission.txt (INFO). Its bridging when no is MintPy's default (the operator named no method):
  v0.10, R5 (record 108.3), under --decide auto in a run of the driver without --only (LINOG_RESTART=allowed): the
      verdict is taken. This phase writes recon/d9ab_decision.json (the method, the A/B, the network admit kept: its
      network_md5), the earlier such file moved into the frame's _archive/ first; moves the frame's mintpy/ as it is (sbas's
      no-bridging products, with whatever a later phase wrote into it) into _archive/mintpy_nobridging_<UTC>/ (a rename,
      nothing deleted); asks the driver to restart (status/restart.json); and PASSes (INFO). The driver allows one restart a
      run: after it, LINOG_RESTART is no, so a second bridging verdict in the same run is a DECISION. The driver then runs the frame again from the top: admit takes bridging from
      the decision file (in its fingerprint), mcfg and sbas run again, and this phase reads bridging as chosen. A dry run
      says so and moves nothing.
  under --decide ask, or under auto outside such a run: a DECISION, as v0.9 (the operator writes the method into
      recon/admission.txt). An A/B completed on the same
inputs (its ab.json's key: sbas's files as recorded, A's mask and template, the rule's settings, MintPy's pins; not the
time limit) is read again, not run again, so the run after the operator's choice takes seconds. Complete means: A
unchanged while it ran, and MintPy on B at rc 0 through its steps within the time limit; a failed or timed-out A/B is
made again the next time d9ab runs. B stays as evidence
(1.299 GiB on F3320). The decision's digest, which deliver's fingerprint holds, is what RUN_MANIFEST.json carries of it
(the method, its source, the verdict and the rule's numbers), not the key.

Gates
  G5dab.1  sbas PASS on record, its files as it recorded them; G5dab.1a admit PASS on record          FAIL
  G5dab.1j admit's recon/admission.json: unwrapError.method and its source                              FAIL
  G5dab.2  environment; MintPy at its pin                                                        ERROR / FAIL
  G5dab.3  smallbaselineApp.py on the PATH is the pinned env's; G5dab.3n nice on the PATH               FAIL
  G5dab.4  A: its template's unwrapError.method is admit's (a dry run whose sbas is to run again: a plan);
           the files to copy and A's products present; A's mask sbas's (the original when wmask has
           written the water mask)                                                                      FAIL
  D9m      bridging (the operator's): the A/B not run                                                   INFO
  G5dab.5  a new A/B: free space at the record folder, twice the copy plus D9AB_FREE_GIB or more        FAIL
  G5dab.6  the copy: each file equal to A's by md5; B's template differs from A's in the three lines    FAIL
  G5dab.7  MintPy on B: rc 0 and the steps correct_unwrap_error to geocode; else WARN (the rule then
           reads no by its first condition)                                                     PASS / WARN
  G5dab.8  the comparison: ab.json written, or a completed A/B of the same key read again              PASS
  G5dab.9  the frame's mintpy/ unchanged while the phase ran (its listing before and after): else FAIL; when
           MintPy ran on B, the A/B is void and its ab.json says complete false (never read again)      FAIL
  D9ab     the rule's verdict, and the decision (v0.10: R5 under auto)                   PASS / INFO / DECISION
  G5dab.10 R5: mintpy/ moved into _archive/, the decision file written, the restart asked (auto, a bridging verdict) FAIL
--state: STALE also when the A/B's evidence files (ab.json, ab_pairs.tsv, the MintPy log) changed since. --dryrun DIR:
the same A/B with B under DIR, the frame only read; a plan only when the frame's sbas has not run. Exit 0 PASS, 2 FAIL,
3 ERROR, 4 DECISION.
"""
import argparse
import glob
import json
import math
import os
import shutil
import signal
import subprocess
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'd9ab', '5dab', 2   # v0.10: R5 (v0.8: 1)
COPY = ('inputs/ifgramStack.h5', 'inputs/geometryRadar.h5', 'smallbaselineApp.cfg', 'avgSpatialCoh.h5', 'maskConnComp.h5')
PRODUCTS = ('maskTempCoh.h5', 'temporalCoherence.h5', 'velocity.h5')
SET = (('mintpy.unwrapError.method', 'bridging'), ('mintpy.unwrapError.ramp', 'linear'), ('mintpy.plot', 'no'))
EVIDENCE = ('ab.json', 'ab_pairs.tsv', 'mintpy_B.log')
TWO_PI = 2.0 * math.pi
ORIG = 'mintpy/watermask/maskTempCoh.orig.h5'
DECISION_FILE = os.path.join('recon', 'd9ab_decision.json')   # v0.10, R5: admit reads it
RESTART_FILE = os.path.join('status', 'restart.json')         # v0.10, R5: the driver reads it after this phase
RULE = ('bridging if MintPy on B ends rc 0 with unwrapPhase_bridging and its three products, B\'s mask keeps at least %d px more '
        'than A\'s, and the velocity std over the pixels both masks keep is no larger in B; otherwise no (record 62.0)')


def say(s=''):
    print(s, flush=True)


def fmt(x, n=4):
    return 'none' if x is None else '%.*f' % (n, x)


def pct(x, n=2):
    return 'none' if x is None else '%.*f %%' % (n, 100.0 * x)


def settings(m):
    return dict((k, m[k]) for k in ('D9AB_MIN_GAIN_CAP', 'D9AB_MIN_GAIN_FRAC', 'D9AB_TIMEOUT_S', 'G19_EDGE'))


def rule_settings(m):
    """The settings a completed comparison depends on (the key): not the time limit, which cannot change one that ended."""
    return dict((k, m[k]) for k in ('D9AB_MIN_GAIN_CAP', 'D9AB_MIN_GAIN_FRAC', 'G19_EDGE'))


def min_gain(m, L, W):
    """MintPy's smallest component on an L x W grid (label_conn_comp: min(2500, size x 3e-3)), the rule's (b); the product
    in MintPy's order (L x W first), since the ceiling can differ by one otherwise."""
    return int(math.ceil(min(float(m['D9AB_MIN_GAIN_CAP']), L * W * float(m['D9AB_MIN_GAIN_FRAC']))))


def clean(o):
    """o with every NaN or infinite float as None (ab.json stays JSON that jq and JavaScript read)."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return dict((k, clean(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def decision_digest(meth, src, sm):
    """What RUN_MANIFEST.json carries of D9's decision: deliver's fingerprint holds this, so a changed method, source,
    verdict or reading makes the delivery STALE, and a re-read of the same A/B does not."""
    keep = ('verdict', 'compared', 'gain', 'min_gain', 'mask_a', 'mask_b', 'std_common_a', 'std_common_b', 'pairs_changed', 'moved_px')
    return C.md5_obj(clean(dict(method=meth, source=src, result=dict((k, (sm or {}).get(k)) for k in keep) if sm else None)))


def watermark(p):
    """The LINOG_WATERMASK attribute of a mask file (wmask writes it), or None."""
    import h5py
    with h5py.File(p, 'r') as f:
        v = f.attrs.get('LINOG_WATERMASK')
    return v.decode() if isinstance(v, bytes) else v


def a_mask(W):
    """(path, what, problem): A's mask as sbas made it. wmask rewrites mintpy/maskTempCoh.h5 with the water mask and keeps
    sbas's in mintpy/watermask/maskTempCoh.orig.h5; B's mask comes from MintPy alone, so A's is sbas's."""
    cur = os.path.join(W, 'mintpy', 'maskTempCoh.h5')
    if not os.path.isfile(cur):
        return None, None, 'mintpy/maskTempCoh.h5 absent'
    if not watermark(cur):
        return cur, 'mintpy/maskTempCoh.h5 (sbas\'s)', None
    orig = os.path.join(W, ORIG)
    if not os.path.isfile(orig):
        return None, None, 'mintpy/maskTempCoh.h5 carries the water mask and %s is absent' % ORIG
    if watermark(orig):
        return None, None, '%s carries LINOG_WATERMASK: it is not sbas\'s mask' % ORIG
    return orig, '%s (sbas\'s, kept by wmask)' % ORIG, None


def done_before(recdir, key):
    """The folder (relative to recdir) of a completed A/B with this key, or None: its ab.json complete, the latest first."""
    for f in sorted(glob.glob(os.path.join(recdir, 'd9ab', '*', 'ab.json')), reverse=True):
        try:
            j = json.load(open(f))
        except (OSError, ValueError):
            continue
        if j.get('key') == key and j.get('complete') is True:
            return os.path.relpath(os.path.dirname(f), recdir)
    return None


def new_folder(recdir):
    base = os.path.join(recdir, 'd9ab', time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    d, n = base, 1
    while True:
        try:
            os.mkdir(d)
            return d
        except FileExistsError:
            n += 1
            d = '%s_%d' % (base, n)


def run_b(cmd, cwd, log, extra_env, timeout):
    """cmd from cwd in a session of its own, its output into log; stopped (SIGTERM, then SIGKILL after 30 s) after timeout
    seconds, and when this phase is stopped (the group ends before the record says ERROR). As P3.run_pool starts its
    jobs: libc loaded here, not in the forked child; the stop signals held while the process starts, so a stop in that
    moment lands after it is registered and is handled like any other; in the child, SIGTERM when this phase dies
    (PR_SET_PDEATHSIG: a SIGKILL of the phase, the OOM killer). (rc, output, stopped at the time limit)."""
    e = dict(os.environ)
    e.update(extra_env)
    t0 = time.time()
    p, late = None, False
    with open(log, 'wb') as fh:
        fh.write(('# %s  %s  (cwd %s)\n' % (C.utc(), ' '.join(cmd), cwd)).encode('utf-8', 'replace'))
        fh.flush()
        start = fh.tell()

        def end_group():
            for sig, wait in ((signal.SIGTERM, 30), (signal.SIGKILL, 10)):
                try:
                    os.killpg(p.pid, sig)
                    p.wait(timeout=wait)
                    return
                except (OSError, subprocess.TimeoutExpired):
                    continue
        P3._libc()
        try:
            with P3.Deferred():
                p = subprocess.Popen(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                                     start_new_session=True, preexec_fn=P3._job_init)
            try:
                rc = p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                late = True
                end_group()
                rc = p.poll() if p.poll() is not None else -9
        except BaseException:
            if p is not None:
                end_group()
            with open(log, 'a') as fh2:
                fh2.write('# stopped after %.1f s: the command\'s group ended (rc %s)\n' % (
                    time.time() - t0, p.poll() if p is not None else 'none: not started'))
            raise
    with open(log, 'rb') as fh:
        fh.seek(start)
        out = fh.read().decode('utf-8', 'replace')
    with open(log, 'a') as fh:
        fh.write('# rc %d  %.1f s%s\n' % (rc, time.time() - t0, '  (stopped at the time limit, %d s)' % timeout if late else ''))
    return rc, out, late


# ---------------------------------------------------------------- the comparison (RD8's rd8_ab.py, ported)
def first2d(path, ds=None):
    import h5py
    with h5py.File(path, 'r') as h:
        k = ds if ds else list(h.keys())[0]
        return h[k][()]


def wrap(x):
    """mintpy.utils.utils0.wrap"""
    import numpy as np
    return -np.pi + np.mod(x + np.pi, TWO_PI)


def triplets(pairs):
    """ifgramStack.get_design_matrix4triplet: +1 (t1, t2), +1 (t2, t3), -1 (t1, t3); None without a triangle."""
    import itertools
    import numpy as np
    ix = dict((tuple(p.split('_')), i) for i, p in enumerate(pairs))
    dates = sorted(set(d for p in pairs for d in p.split('_')))
    rows = []
    for d1, d2, d3 in itertools.combinations(dates, 3):
        try:
            a, b, c = ix[(d1, d2)], ix[(d2, d3)], ix[(d1, d3)]
        except KeyError:
            continue
        row = np.zeros(len(pairs), np.int8)
        row[a], row[b], row[c] = 1, 1, -1
        rows.append(row)
    return np.stack(rows).astype(np.float32) if rows else None


def tint(stack, refp, Cm, rows):
    """calc_num_triplet_with_nonzero_integer_ambiguity's count per pixel (RD7's function, bit-identical to MintPy's on the
    12 delivered frames and on F3320): each pair referenced where it is not 0, the closure C u, round((closure - wrap) /
    2 pi) != 0."""
    import numpy as np
    n, L, W = stack.shape
    out = np.zeros((L, W), np.float32)
    for r0 in range(0, L, rows):
        r1 = min(L, r0 + rows)
        u = stack[:, r0:r1, :].reshape(n, -1).copy()
        for i in range(n):
            m = u[i, :] != 0.
            u[i, :][m] -= refp[i]
        cp = np.dot(Cm, u)
        ci = np.round((cp - wrap(cp)) / TWO_PI)
        out[r0:r1, :] = np.sum(ci != 0, axis=0).reshape(-1, W)
    return out


def tcompare(tu, tb, m, ntri):
    ok = m & (tu < ntri) & (tb < ntri)
    if not ok.any():
        return dict(px=0)
    mu, mb = float(tu[ok].mean()), float(tb[ok].mean())
    return dict(px=int(ok.sum()), mean_u=mu, mean_b=mb, better=int((tb[ok] < tu[ok]).sum()), worse=int((tb[ok] > tu[ok]).sum()),
                change=(mb - mu) / mu if mu > 0 else None)


def std_mm(v, m):
    import numpy as np
    x = v[m & np.isfinite(v)].astype(np.float64) * 1000.
    return float(x.std()) if x.size else None


def compare(A, B, amask, brc, edge, out, flips, gain_min, title):
    """RD8's A/B: A the frame's mintpy/ (read only), B the copy after MintPy ran on it with bridging (rc brc); amask A's mask
    file. Prints its readings, writes out/ab_pairs.tsv and out/ab_velocity.png, and returns the readings and the rule's
    verdict (dict)."""
    import h5py
    import numpy as np
    R = dict(brc=brc, rule_min_gain=gain_min)
    say('   the stack (B\'s inputs/ifgramStack.h5, copied from A\'s):')
    with h5py.File(os.path.join(B, 'inputs', 'ifgramStack.h5'), 'r') as h:
        in_b = 'unwrapPhase_bridging' in h
        have_b = in_b and brc == 0                    # a run that did not end rc 0 may leave pairs unprocessed: not read
        d12 = ['%s_%s' % (a.decode(), b.decode()) for a, b in h['date'][()]]
        keep = h['dropIfgram'][()]
        ref = (int(float(h.attrs['REF_Y'])), int(float(h.attrs['REF_X'])))
        idx = np.where(keep)[0]
        U = h['unwrapPhase'][()][idx].astype(np.float32)
        Bb = h['unwrapPhase_bridging'][()][idx].astype(np.float32) if have_b else None
        coh = h['coherence'][()][idx].astype(np.float32)
    if Bb is not None and Bb.shape != U.shape:
        say('     unwrapPhase_bridging is %s, unwrapPhase %s: NOT read' % (list(Bb.shape), list(U.shape)))
        Bb, have_b = None, False
    kept = [d12[i] for i in idx]
    n, L, W = U.shape
    mn = coh.min(axis=0)
    av = coh.mean(axis=0, dtype=np.float64).astype(np.float32)
    del coh
    V = np.zeros((L, W), bool)
    V[edge:L - edge, edge:W - edge] = True
    V &= np.isfinite(mn) & (av > 0)
    nv = int(V.sum())
    R['stack'] = dict(pairs=len(d12), kept=n, grid=[L, W], ref=list(ref), valid=nv, bridging_dataset=in_b, bridging_read=have_b)
    say('     %d pairs, %d kept; grid %d x %d; REF %d,%d; the kit\'s valid area %d px; unwrapPhase_bridging %s' % (
        len(d12), n, L, W, ref[0], ref[1], nv, ('present' if have_b else 'present, NOT read (MintPy\'s run on B ended rc %d, or its shape '
                                                'differs)' % brc) if in_b else 'ABSENT (MintPy\'s run on B did not write it)'))
    moved = np.zeros((L, W), bool)
    per = []
    if have_b:
        y, x = ref
        worst = 0.0
        for j in range(n):
            u, b = U[j], Bb[j]
            m = V & (u != 0) & np.isfinite(u) & np.isfinite(b)
            c = -float(u[y, x]) if b[y, x] == 0 else float(np.median(b[m].astype(np.float64) - u[m])) if m.any() else 0.
            d = b[m].astype(np.float64) - u[m].astype(np.float64)
            k = np.rint((d - c) / TWO_PI)
            worst = max(worst, float(np.abs(d - c - TWO_PI * k).max()) if d.size else 0.)
            mv = np.zeros((L, W), bool)
            mv[m] = k != 0
            moved |= mv
            per.append((kept[j], int(mv.sum()), 'ref' if b[y, x] == 0 else 'median'))
        ch = [q for q in per if q[1]]
        R['bridging'] = dict(pairs_changed=len(ch), moved_px=int(moved.sum()), mean_share=float(np.mean([q[1] for q in per])) / max(nv, 1),
                             worst_residual=worst, anchors_ref=sum(1 for q in per if q[2] == 'ref'))
        bb = R['bridging']
        say('     bridging changed %d pairs, %s of the valid area\'s pixel-pairs on average; %d px moved in any pair (%s of the valid '
            'area); largest residual from a multiple of 2 pi %.2e rad; anchored at REF in %d of %d pairs' % (
                bb['pairs_changed'], pct(bb['mean_share']), bb['moved_px'], pct(bb['moved_px'] / float(max(nv, 1))), worst,
                bb['anchors_ref'], n))
        for q in sorted(ch, key=lambda t: -t[1])[:4]:
            say('       %s: %d px (%s of the valid area)' % (q[0], q[1], pct(q[1] / float(max(nv, 1)))))
    mkA = first2d(amask).astype(bool)
    Cm = triplets(kept)
    if Cm is not None:
        rows = max(1, int(32e6 // (4 * max(Cm.shape[0], n) * W)))
        tu = tint(U, U[:, ref[0], ref[1]].copy(), Cm, rows)
        ntri = Cm.shape[0]
        R['tint'] = dict(ntri=int(ntri))
        fa = os.path.join(A, 'numTriNonzeroIntAmbiguity.h5')
        if os.path.isfile(fa):
            ft = first2d(fa)
            m = V & np.isfinite(ft)
            R['tint']['a_file_equal'] = float((ft[m] == tu[m]).mean()) if m.any() else None
            R['tint']['a_file_px'] = int(m.sum())
        ok = V & (tu < ntri)
        R['tint']['u_valid'] = dict(px=int(ok.sum()), mean=float(tu[ok].mean()) if ok.any() else None)
        say('   T_int (%d triplets) before bridging over the valid area: %s px, mean %s; A\'s own numTriNonzeroIntAmbiguity.h5 %s' % (
            ntri, R['tint']['u_valid']['px'], fmt(R['tint']['u_valid']['mean']), 'equal on %s of %s px' % (
                pct(R['tint'].get('a_file_equal')), R['tint'].get('a_file_px')) if 'a_file_px' in R['tint'] else 'absent'))
        thr = int(math.ceil(ntri / 2.))
        hi = V & (tu >= thr) & (tu < ntri)
        g = first2d(os.path.join(A, 'inputs', 'geometryRadar.h5'), 'height')
        pad = np.pad(g, 2, mode='edge')
        win = np.stack([pad[dy:dy + L, dx:dx + W] for dy in range(5) for dx in range(5)])
        rng = win.max(axis=0) - win.min(axis=0)
        del win, pad

        def hstat(m):
            if not m.any():
                return dict(px=0)
            return dict(px=int(m.sum()), h_median=float(np.median(g[m])), h_p5=float(np.percentile(g[m], 5)),
                        h_p95=float(np.percentile(g[m], 95)), range5_median=float(np.median(rng[m])), in_maskA=float(mkA[m].mean()),
                        tint_mean=float(tu[m].mean()))
        vv = V & (tu < ntri)
        s_all = float(tu[vv].sum())
        R['high'] = dict(threshold=thr, high=hstat(hi), rest=hstat(vv & ~hi), share_of_valid=float(hi.sum()) / max(int(vv.sum()), 1),
                         share_of_sum=float(tu[hi].sum()) / s_all if s_all > 0 else None, dem_min=float(np.nanmin(g)))
        hh, hr = R['high']['high'], R['high']['rest']
        say('   the valid area\'s pixels with T_int of %d or more: %d px (%s of the valid area), carrying %s of the sum of T_int over it; '
            'there the DEM height median %s m (5th to 95th percentile %s to %s m; the DEM\'s least %s m), its 5 x 5 range median %s m, in '
            'A\'s mask %s; elsewhere in the valid area: height median %s m, 5 x 5 range median %s m, in A\'s mask %s, T_int mean %s' % (
                thr, hh['px'], pct(R['high']['share_of_valid']), pct(R['high']['share_of_sum']), fmt(hh.get('h_median'), 1),
                fmt(hh.get('h_p5'), 1), fmt(hh.get('h_p95'), 1), fmt(R['high']['dem_min'], 1), fmt(hh.get('range5_median'), 2),
                pct(hh.get('in_maskA')), fmt(hr.get('h_median'), 1), fmt(hr.get('range5_median'), 2), pct(hr.get('in_maskA')),
                fmt(hr.get('tint_mean'), 3)))
        if have_b:
            tb = tint(Bb, Bb[:, ref[0], ref[1]].copy(), Cm, rows)
            for key, m, label in (('valid', V, 'the valid area'), ('maskA', V & mkA, 'the valid area inside A\'s mask'),
                                  ('outside', V & ~mkA, 'the valid area outside A\'s mask'), ('moved', V & moved, 'the pixels bridging moved')):
                c = tcompare(tu, tb, m, ntri)
                R['tint'][key] = c
                say('   T_int over %s: %s px, %s -> %s (%s), %s better, %s worse' % (
                    label, c.get('px'), fmt(c.get('mean_u'), 3), fmt(c.get('mean_b'), 3), pct(c.get('change')), c.get('better', 'none'),
                    c.get('worse', 'none')))
    else:
        say('   T_int: no triangle in the kept pairs')
    missB = [x for x in PRODUCTS if not os.path.isfile(os.path.join(B, x))]
    P = {}
    if brc != 0:
        say('   B\'s products: NOT read (MintPy\'s run on B ended rc %d; the log says where)' % brc)
    elif missB:
        say('   B\'s products: ABSENT %s (MintPy\'s run on B did not reach them)' % ', '.join(missB))
    else:
        mkB = first2d(os.path.join(B, 'maskTempCoh.h5')).astype(bool)
        tcA, tcB = first2d(os.path.join(A, 'temporalCoherence.h5')), first2d(os.path.join(B, 'temporalCoherence.h5'))
        veA, veB = first2d(os.path.join(A, 'velocity.h5'), 'velocity'), first2d(os.path.join(B, 'velocity.h5'), 'velocity')
        common = mkA & mkB & np.isfinite(veA) & np.isfinite(veB)     # the rule's (c): the same pixels on both sides
        P = dict(maskA=int(mkA.sum()), maskB=int(mkB.sum()), gained=int((mkB & ~mkA).sum()), lost=int((mkA & ~mkB).sum()),
                 common=int(common.sum()), both=int((mkA & mkB).sum()), grid=int(mkA.size),
                 tcoh_valid=[float(np.nanmean(tcA[V])), float(np.nanmean(tcB[V]))] if V.any() else None,
                 tcoh_moved=[float(np.nanmean(tcA[V & moved])), float(np.nanmean(tcB[V & moved]))] if (V & moved).any() else None,
                 vstd_A=std_mm(veA, mkA), vstd_B=std_mm(veB, mkB), vstd_common=[std_mm(veA, common), std_mm(veB, common)])
        dv = (veB - veA)[common].astype(np.float64) * 1000.
        dvm = (veB - veA)[common & moved].astype(np.float64) * 1000.
        P['dv_common'] = dict(px=int(dv.size), median_abs=float(np.median(np.abs(dv))) if dv.size else None,
                              p99_abs=float(np.percentile(np.abs(dv), 99)) if dv.size else None,
                              max_abs=float(np.abs(dv).max()) if dv.size else None)
        P['dv_moved'] = dict(px=int(dvm.size), median_abs=float(np.median(np.abs(dvm))) if dvm.size else None,
                             p99_abs=float(np.percentile(np.abs(dvm), 99)) if dvm.size else None)
        say('   maskTempCoh: A %d px (%s of the grid), B %d px (%s); B gains %d and loses %d; both keep %d (%d with both velocities '
            'finite)' % (P['maskA'], pct(P['maskA'] / float(P['grid'])), P['maskB'], pct(P['maskB'] / float(P['grid'])), P['gained'],
                         P['lost'], P['both'], P['common']))
        say('   temporal coherence, mean over the valid area: %s; over the pixels bridging moved: %s' % (
            'A %s, B %s' % (fmt(P['tcoh_valid'][0]), fmt(P['tcoh_valid'][1])) if P['tcoh_valid'] else 'no valid area',
            'A %s, B %s' % (fmt(P['tcoh_moved'][0]), fmt(P['tcoh_moved'][1])) if P['tcoh_moved'] else 'none moved'))
        say('   velocity std, mm/yr: inside A\'s mask (A) %s; inside B\'s mask (B) %s; inside the pixels both keep: A %s, B %s' % (
            fmt(P['vstd_A'], 3), fmt(P['vstd_B'], 3), fmt(P['vstd_common'][0], 3), fmt(P['vstd_common'][1], 3)))
        say('   the velocity\'s change B - A inside the pixels both keep, mm/yr: |change| median %s, 99th percentile %s, largest %s; over '
            'the moved pixels among them (%d px): median %s, 99th percentile %s' % (
                fmt(P['dv_common']['median_abs'], 3), fmt(P['dv_common']['p99_abs'], 3), fmt(P['dv_common']['max_abs'], 3),
                P['dv_moved']['px'], fmt(P['dv_moved']['median_abs'], 3), fmt(P['dv_moved']['p99_abs'], 3)))
        ga, gb = os.path.join(A, 'geo', 'geo_maskTempCoh.h5'), os.path.join(B, 'geo', 'geo_maskTempCoh.h5')
        if os.path.isfile(ga) and watermark(ga):   # after wmask: sbas's geocoded mask is the original wmask kept
            ga = os.path.join(A, 'watermask', 'geo_maskTempCoh.orig.h5')
        if os.path.isfile(ga) and os.path.isfile(gb) and not watermark(ga):
            a_, b_ = first2d(ga).astype(bool), first2d(gb).astype(bool)
            P['geo_mask'] = [int(a_.sum()), int(b_.sum()), int(a_.size)]
            say('   geo_maskTempCoh: A %d, B %d of %d cells (%s, %s)' % (a_.sum(), b_.sum(), a_.size, pct(a_.mean()), pct(b_.mean())))
        for side, d in (('A', A), ('B', B)):
            q = os.path.join(d, 'exclude_date.txt')
            P['exclude_' + side] = ' '.join(open(q).read().split()) if os.path.isfile(q) else None
            q = os.path.join(d, 'reference_date.txt')
            P['ref_date_' + side] = open(q).read().split()[0] if os.path.isfile(q) and open(q).read().split() else None
            q = os.path.join(d, 'rms_timeseriesResidual_ramp.txt')
            if os.path.isfile(q):
                v = [float(ln.split()[1]) for ln in open(q) if ln.strip() and not ln.startswith('#') and len(ln.split()) >= 2]
                P['rms_median_' + side] = float(np.median(v)) if v else None
        say('   the reference date: A %s, B %s; the residual RMS median, m: A %s, B %s; outlier dates (exclude_date.txt): A %s, B %s' % (
            P.get('ref_date_A') or 'none', P.get('ref_date_B') or 'none', fmt(P.get('rms_median_A')), fmt(P.get('rms_median_B')),
            'no file' if P.get('exclude_A') is None else (P['exclude_A'] or 'empty'),
            'no file' if P.get('exclude_B') is None else (P['exclude_B'] or 'empty')))
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fud, flr = flips

            def fl(a):
                a = a[::-1, :] if fud else a
                return a[:, ::-1] if flr else a
            vA = np.where(mkA, veA * 1000., np.nan)
            vB = np.where(mkB, veB * 1000., np.nan)
            dd = np.where(common, (veB - veA) * 1000., np.nan)
            mm = np.zeros((L, W), np.int8)
            mm[mkA & mkB] = 1
            mm[mkB & ~mkA] = 2
            mm[mkA & ~mkB] = 3
            both = np.concatenate([vA[np.isfinite(vA)], vB[np.isfinite(vB)]])
            lim = float(np.percentile(np.abs(both), 99)) if both.size else 1.
            fin = dd[np.isfinite(dd)]
            dl = float(np.percentile(np.abs(fin), 99)) if fin.size else 1.
            fig, ax = plt.subplots(1, 4, figsize=(20, 5.2))
            for a_, im, t, cm, vr in ((ax[0], vA, 'A: unwrapError no (mm/yr)', 'jet', (-max(lim, 1e-6), max(lim, 1e-6))),
                                      (ax[1], vB, 'B: bridging (mm/yr)', 'jet', (-max(lim, 1e-6), max(lim, 1e-6))),
                                      (ax[2], dd, 'B - A, both masks (mm/yr)', 'RdBu_r', (-max(dl, 1e-6), max(dl, 1e-6)))):
                h_ = a_.imshow(fl(im), cmap=cm, vmin=vr[0], vmax=vr[1], interpolation='nearest')
                a_.set_title(t, fontsize=10)
                fig.colorbar(h_, ax=a_, shrink=0.8)
            ax[3].imshow(fl(mm), cmap=matplotlib.colors.ListedColormap(['#dddddd', '#4a90b8', '#2ca02c', '#d62728']), vmin=-0.5,
                         vmax=3.5, interpolation='nearest')
            ax[3].set_title('masks: blue both, green B only, red A only', fontsize=10)
            ry, rx = (L - 1 - ref[0] if fud else ref[0]), (W - 1 - ref[1] if flr else ref[1])
            for a_ in ax:
                a_.plot(rx, ry, 'ks', ms=5)
            fig.suptitle(title)
            fig.tight_layout()
            fig.savefig(os.path.join(out, 'ab_velocity.png'), dpi=90)
            plt.close(fig)
            say('   figure: ab_velocity.png (%d B)' % os.path.getsize(os.path.join(out, 'ab_velocity.png')))
        except Exception as e:  # noqa: BLE001  the figure is a convenience; the readings stand without it
            say('   figure: not made (%s: %s)' % (type(e).__name__, str(e)[:120]))
    R['products'] = P
    if brc != 0:
        verdict, why = 'no', 'MintPy\'s run on B ended rc %d, not 0 (its log says where)' % brc
    elif not in_b:
        verdict, why = 'no', 'MintPy\'s run on B wrote no unwrapPhase_bridging'
    elif not have_b:
        verdict, why = 'no', 'B\'s unwrapPhase_bridging could not be read'
    elif not P:
        verdict, why = 'no', 'B\'s products are not all there'
    else:
        gain = P['maskB'] - P['maskA']
        sa, sb = P['vstd_common']
        if gain >= gain_min and sa is not None and sb is not None and sb <= sa:
            verdict, why = 'bridging', ('B\'s mask keeps %+d px against A\'s (%d asked) and the velocity std inside the pixels both keep is '
                                        '%.3f against %.3f mm/yr (B no larger asked)' % (gain, gain_min, sb, sa))
        else:
            verdict, why = 'no', ('B\'s mask keeps %+d px against A\'s (%d asked); the velocity std inside the pixels both keep is %s '
                                  'against %s mm/yr (B no larger asked)' % (gain, gain_min, fmt(sb, 3), fmt(sa, 3)))
    compared = brc == 0 and have_b and bool(P)
    R['rule'] = dict(verdict=verdict, why=why, compared=compared, text=RULE % gain_min)
    say('   D9 by the A/B rule of record 62.0 (%s): %s -- %s%s' % (RULE % gain_min, verdict, why, '' if compared else
                                                                    ' (the products were NOT compared)'))
    with open(os.path.join(out, 'ab_pairs.tsv'), 'w') as fh:
        fh.write('pair\tmoved_px\tanchor\n')
        for q in per:
            fh.write('%s\t%d\t%s\n' % q)
    return R


def summary(R):
    """The few numbers the record, the gate and RUN_MANIFEST.json carry."""
    P = R.get('products') or {}
    rule = R.get('rule') or {}
    sc = P.get('vstd_common') or [None, None]
    return dict(verdict=rule.get('verdict'), why=rule.get('why'), compared=rule.get('compared'), min_gain=R.get('rule_min_gain'),
                gain=(P['maskB'] - P['maskA']) if P else None, mask_a=P.get('maskA'), mask_b=P.get('maskB'), gained=P.get('gained'),
                lost=P.get('lost'), std_common_a=sc[0], std_common_b=sc[1], std_own_a=P.get('vstd_A'), std_own_b=P.get('vstd_B'),
                pairs_changed=(R.get('bridging') or {}).get('pairs_changed'), moved_px=(R.get('bridging') or {}).get('moved_px'),
                tint_valid=[(R.get('tint') or {}).get('valid', {}).get(k) for k in ('mean_u', 'mean_b')],
                tint_mask_a=[(R.get('tint') or {}).get('maskA', {}).get(k) for k in ('mean_u', 'mean_b')], brc=R.get('brc'))


def take_r5(W, ra, key, folder_rel, sm, utc_tag):
    """R5 (record 108.3): the A/B's bridging taken under --decide auto. Every check first (admit's network on record,
    _archive/ a folder on mintpy/'s disk, the target names free), then, in order: an earlier recon/d9ab_decision.json moved
    into _archive/, the frame's mintpy/ moved into _archive/mintpy_nobridging_<UTC>/ (a rename: mintpy/ as it is, sbas's
    no-bridging products with whatever a later phase wrote into it), recon/d9ab_decision.json written, status/restart.json
    written. A stop or a failure after the move and before the decision leaves the frame without mintpy/ and without the
    decision: the next run makes mintpy/ again without bridging (mcfg and sbas), and d9ab makes or reads its A/B again. Returns dict(decision,
    decision_md5, moved_to, restart, earlier); raises on a failure (the phase then FAILs at G5dab.10, rc 2)."""
    net = ((ra or {}).get('outputs') or {}).get('network_md5')
    if not net:
        raise ValueError('admit\'s record has no network_md5 (admit is to run under v0.10 first)')
    arch = os.path.join(W, '_archive')
    os.makedirs(arch, exist_ok=True)
    df = os.path.join(W, DECISION_FILE)
    src = os.path.join(W, 'mintpy')
    dst = os.path.join(arch, 'mintpy_nobridging_%s' % utc_tag)
    old = os.path.join(arch, 'd9ab_decision_%s.json' % utc_tag) if os.path.lexists(df) else None
    if not os.path.isdir(src) or os.path.islink(src):
        raise ValueError('%s is not a folder' % src)
    if os.path.lexists(dst):
        raise ValueError('%s exists already' % dst)
    if old and os.path.lexists(old):
        raise ValueError('%s exists already' % old)
    if os.stat(src).st_dev != os.stat(arch).st_dev:
        raise ValueError('mintpy/ and _archive/ are on two filesystems: the move would be a copy')
    if old:
        os.rename(df, old)
    os.makedirs(dst)
    os.rename(src, os.path.join(dst, 'mintpy'))
    dec = dict(method='bridging', source='R5: d9ab\'s A/B under --decide auto', folder=folder_rel, key=key, network=net,
               result=clean(sm), taken=C.utc(), frame=W, pipeline=P6.HERE, moved_to=os.path.relpath(dst, W), earlier=os.path.relpath(old, W) if old else None,
               rule=RULE % (sm.get('min_gain') or 0))
    P5.write_json(df, dec)
    rs = dict(from_phase='admit', by='d9ab', reason='R5: bridging taken; mintpy/ moved to %s' % os.path.relpath(dst, W),
              decision=DECISION_FILE, decision_md5=C.md5_file(df), written=C.utc())
    P5.write_json(os.path.join(W, RESTART_FILE), rs)
    return dict(decision=DECISION_FILE, decision_md5=C.md5_file(df), moved_to=os.path.relpath(dst, W), restart=RESTART_FILE,
                earlier=os.path.relpath(old, W) if old else None)


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5dab: D9\'s A/B after sbas (record 62.0 and 63.8)')
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
    rs = P1.record(recdir, '5d', 'sbas') or {}
    if a.dryrun and (P1.record(W, '5d', 'sbas') or {}).get('verdict') == 'PASS':
        rs = P1.record(W, '5d', 'sbas') or {}
    ra = P1.record(recdir, '5a', 'admit') or {}
    d9 = ((ra.get('outputs') or {}).get('decisions') or {}).get('d9') or {}
    fp = C.md5_obj(dict(logic=LOGIC, sbas=(rs.get('outputs') or {}).get('digest'), admit=(ra.get('outputs') or {}).get('decisions_md5'),
                        d9=[d9.get('method'), d9.get('source')], settings=settings(m), mintpy=m['MINTPY_VERSION'],
                        defaults=m['MINTPY_DEFAULTS_MD5']))

    def evidence_changed(rec):
        o = (rec or {}).get('outputs') or {}
        return P3.listing_changed(W, [x[0] for x in o.get('files') or []], o.get('files'))
    if a.state:
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, evidence_changed))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   settings=settings(m)))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    rs, from_frame = P6.prior6(st, 'G5dab.1', recdir, W, '5d', 'sbas', P5.OUTS['sbas'], bool(a.dryrun))
    if not rs:
        return st.finish()
    if a.dryrun and (not from_frame or (rs.get('outputs') or {}).get('planned')):
        return P5.plan_only(st, ['would copy %s from mintpy/ into d9ab/<UTC>/B/mintpy/, set %s there, run MintPy on it from '
                                 'correct_unwrap_error to geocode, and compare it with mintpy/ by the rule of record 62.0' % (
                                     ', '.join(COPY), ', '.join('%s = %s' % kv for kv in SET))],
                            'the frame\'s sbas has not run, so there is no A to compare')
    ra = P3.prior3(st, 'G5dab.1a', recdir, '5a', 'admit')
    if not ra:
        return st.finish()
    aj = os.path.join(recdir, 'recon', 'admission.json')
    try:
        adm = json.load(open(aj))
        meth = adm['cfg']['mintpy.unwrapError.method']
        src = ((adm.get('decisions') or {}).get('d9') or {}).get('source')
    except (OSError, ValueError, KeyError) as e:
        st.gate('G5dab.1j', 'admit\'s decisions', 'FAIL', '%s: %s' % (aj, e), 'recon/admission.json with unwrapError.method')
        return st.finish()
    operator = str(src or '').startswith('the operator')
    st.gate('G5dab.1j', 'admit\'s decisions', 'PASS', '%s: unwrapError.method = %s (%s)' % (aj, meth, src or 'no source recorded'))
    if not P5.env_gate(st, 'G5dab.2', env, s, m):
        return st.finish()
    if not P5.which_gate(st, 'G5dab.3', s, ('smallbaselineApp.py',)):
        return st.finish()
    if not shutil.which('nice'):
        st.gate('G5dab.3n', 'nice on the PATH', 'FAIL', 'nice not found', 'coreutils\' nice (MintPy on B runs at nice 10)')
        return st.finish()
    A = os.path.join(W, 'mintpy')
    tA = os.path.join(A, 'smallbaselineApp.cfg')
    tvals = P5.cfg_dict(open(tA).read()) if os.path.isfile(tA) else {}
    amask, awhat, aprob = a_mask(W)
    miss = [x for x in COPY + PRODUCTS[1:] if not os.path.isfile(os.path.join(A, x))]
    bad = []
    if tvals.get('mintpy.unwrapError.method') != meth:
        if a.dryrun:
            return P5.plan_only(st, ['the frame\'s template says unwrapError.method = %s and admit (this dry run) decided %s: mcfg and sbas '
                                     'are to run again, and the A/B, when the method is no, after them' % (tvals.get('mintpy.unwrapError.method'), meth)],
                                'the frame\'s sbas is to run again with admit\'s method')
        bad.append('A\'s template says unwrapError.method = %s, admit decided %s (sbas is to run again)' % (
            tvals.get('mintpy.unwrapError.method'), meth))
    if miss:
        bad.append('absent in mintpy/: %s' % ', '.join(miss))
    if aprob:
        bad.append(aprob)
    st.gate('G5dab.4', 'A (the frame\'s mintpy/, read only)', 'FAIL' if bad else 'PASS', '; '.join(bad) or (
        'unwrapError.method %s as admit decided; the %d files to copy and A\'s products present; A\'s mask %s' % (meth, len(COPY), awhat)),
        'A\'s template as admit decided; every file present; sbas\'s mask')
    if bad:
        return st.finish()
    if meth == 'bridging':
        st.gate('D9m', 'the method', 'INFO', 'unwrapError.method bridging (%s): the A/B compares a run without bridging with one with it, '
                'and this frame\'s run is the one with it: not run' % (src or 'admit'), 'no: the A/B runs; bridging: not run')
        st.rec['outputs'] = dict(method=meth, source=src, ab=None, files=[], digest=P3.digest([]),
                                 decision_md5=decision_digest(meth, src, None))
        return st.finish()
    amask_md5 = C.md5_file(amask)
    key = C.md5_obj(dict(logic=LOGIC, sbas=(rs.get('outputs') or {}).get('digest'), amask=amask_md5, template=C.md5_file(tA),
                         settings=rule_settings(m), mintpy=m['MINTPY_VERSION'], defaults=m['MINTPY_DEFAULTS_MD5']))
    before = P3.listing(W, ('mintpy',))
    prior = done_before(recdir, key)
    reused = bool(prior)
    st.rec['outputs'] = dict(method=meth, source=src, key=key, a_mask=awhat)
    if reused:
        folder = os.path.join(recdir, prior)
        R = json.load(open(os.path.join(folder, 'ab.json')))
        st.gate('G5dab.8', 'the comparison', 'PASS', 'a completed A/B of the same inputs read again: %s (key %s; MintPy on B rc %s in %s s, '
                'written %s)' % (prior, key, R.get('brc'), R.get('mintpy_seconds'), R.get('written')), 'ab.json complete, its key this one')
    else:
        free = P1.free_gib(recdir)
        need = sum(os.path.getsize(os.path.join(A, x)) for x in COPY) / 2. ** 30
        want = 2.0 * need + float(m['D9AB_FREE_GIB'])   # B: the copy and MintPy's products on it (1.299 GiB on F3320, twice the copy)
        ok = free >= want
        st.gate('G5dab.5', 'free space', 'PASS' if ok else 'FAIL', '%.1f GiB free at %s; the copy %.3f GiB' % (free, recdir, need),
                '%.1f GiB or more (twice the copy, plus %s)' % (want, m['D9AB_FREE_GIB']))
        if not ok:
            return st.finish()
        folder = new_folder(recdir)
        prior = os.path.relpath(folder, recdir)
        B = os.path.join(folder, 'B', 'mintpy')
        os.makedirs(os.path.join(B, 'inputs'))
        st.rec['outputs'].update(folder=prior, copying=True)
        st.write()
        for x in COPY:
            shutil.copy2(os.path.join(A, x), os.path.join(B, x))
        sums = dict((x, C.md5_file(os.path.join(A, x))) for x in COPY)
        bad = [x for x in COPY if C.md5_file(os.path.join(B, x)) != sums[x]]
        txt, sbad = P5.set_values(open(os.path.join(B, 'smallbaselineApp.cfg')).read(), dict(SET))
        if not sbad:
            with open(os.path.join(B, 'smallbaselineApp.cfg'), 'w') as fh:
                fh.write(txt)
        la, lb = open(tA).read().splitlines(), open(os.path.join(B, 'smallbaselineApp.cfg')).read().splitlines()
        ndiff = sum(1 for x, y in zip(la, lb) if x != y) + abs(len(la) - len(lb))
        bv = P5.cfg_dict(open(os.path.join(B, 'smallbaselineApp.cfg')).read())
        if sbad or ndiff != len(SET) or any(bv.get(k) != v for k, v in SET):
            bad.append('B\'s template: %s; %d lines differ from A\'s, %d asked; %s' % ('; '.join(sbad) or 'set', ndiff, len(SET),
                                                                                      ', '.join('%s = %s' % (k, bv.get(k)) for k, _ in SET)))
        st.gate('G5dab.6', 'the copy', 'FAIL' if bad else 'PASS', '%s: %s; B\'s template differs from A\'s in %d lines (%s)' % (
            prior, '; '.join('%s %d B' % (x, os.path.getsize(os.path.join(B, x))) for x in COPY), ndiff,
            ', '.join('%s = %s' % kv for kv in SET)), 'each file equal to A\'s by md5; three lines differ', '\n'.join(bad))
        st.rec['outputs'].update(copying=False, copies=sums)
        if bad:
            return st.finish()
        lg = os.path.join(folder, 'mintpy_B.log')
        cmd = ['nice', '-n', '10', 'smallbaselineApp.py', 'smallbaselineApp.cfg', '--start', 'correct_unwrap_error', '--end', 'geocode']
        say('   MintPy on B: %s  (from %s; the log %s; stopped after %s s)' % (' '.join(cmd), B, lg, m['D9AB_TIMEOUT_S']))
        st.rec['outputs'].update(running=True, log=lg)
        st.write()
        tb = time.time()
        brc, out, late = run_b(cmd, B, lg, dict(P5.mpl_env(recdir), PYTHONUNBUFFERED='1'), int(m['D9AB_TIMEOUT_S']))
        limit = int(m['D9AB_TIMEOUT_S'])
        secs = time.time() - tb
        st.rec['outputs'].update(running=False)
        steps = P5.steps_run(out)
        want = P5.steps_between('correct_unwrap_error', 'geocode')
        good = brc == 0 and steps == want
        st.gate('G5dab.7', 'MintPy on B', 'PASS' if good else 'WARN', 'rc %d in %.0f s%s; steps %s; Traceback lines %d' % (
            brc, secs, ' (stopped at the time limit)' if late else '', ' '.join(steps) or 'none', out.count('Traceback')),
            'rc 0; %s' % ' '.join(want), '' if good else 'the rule reads no by its first condition (record 62.0); the log %s says why:\n%s' % (
                lg, P3.tail(lg, 8)))
        if brc == 0 and steps != want:
            brc = 1   # the rule's (a): MintPy ran to its end with the steps asked
        say('   the comparison (A %s, read only; B %s):' % (A, B))
        os.environ.update(P5.mpl_env(recdir))   # before matplotlib is imported: its cache in the record folder, not in HOME
        R = compare(A, B, amask, brc, int(m['G19_EDGE']), folder, P5.expected_flips(cfg['direction']),
                    min_gain(m, *grid_of(B)), 'P%s F%s: the bridging A/B (d9ab); radar grid, north up' % (path, frame))
        # A's listing now, before ab.json: an A/B during which the frame's mintpy/ changed is void. ab.json is read again
        # only when complete: A unchanged, and MintPy on B ended rc 0 through its steps within the time limit (a failed or
        # timed-out run is made again, with the limit then set, the next time d9ab runs)
        after = P3.listing(W, ('mintpy',))
        same = after == before
        R.update(key=key, written=C.utc(), mintpy_seconds=round(secs, 1), a_mask=awhat, a=A, b=B, copies=sums, method=meth, source=src,
                 pipeline=P6.HERE, version=P5.VERSION_P5, frame_unchanged=same, timed_out=late, time_limit_s=limit,
                 complete=same and brc == 0 and not late)
        P5.write_json(os.path.join(folder, 'ab.json'), clean(R))
        st.gate('G5dab.8', 'the comparison', 'PASS', '%s/ab.json, ab_pairs.tsv%s%s' % (prior, ', ab_velocity.png' if os.path.isfile(
            os.path.join(folder, 'ab_velocity.png')) else '', '' if R['complete'] else '; not to be read again (%s)' % (
                'A changed' if not same else 'MintPy on B stopped at the time limit' if late else 'MintPy on B ended rc %d' % brc)),
                'ab.json written')
    if reused:
        after = P3.listing(W, ('mintpy',))
        same = after == before
    moved = sorted(set(x[0] for x in set(map(tuple, before)) ^ set(map(tuple, after))))
    st.gate('G5dab.9', 'the frame\'s mintpy/', 'PASS' if same else 'FAIL', '%d files, %s while this phase ran' % (
        len(after), 'unchanged' if same else 'CHANGED'), 'unchanged (A is only read)',
        '' if same else ('changed, added or gone while this phase read its earlier A/B: %s. MintPy did not run, so that A/B is not void, '
                         'but something writes into the frame\'s mintpy/ now: find it, and run again' if reused else
                         'changed, added or gone while MintPy ran on B: %s. The A/B is void (its ab.json says complete false and is not '
                         'read again): find what wrote into mintpy/ during it, and run again') % ', '.join(moved)[:400])
    if not same:
        st.rec['outputs'].update(folder=prior, void=not reused)
        return st.finish()
    sm = summary(R)
    rels = [os.path.relpath(os.path.join(folder, n), W) for n in EVIDENCE + ('ab_velocity.png',) if os.path.isfile(os.path.join(folder, n))] \
        if not a.dryrun else []
    lst = P3.listing(W, rels) if rels else []
    verdict = sm['verdict']
    dmode = os.environ.get('LINOG_DECIDE', 'ask')
    r5 = None
    manual = ('Read %s (ab_velocity.png, ab.json; B\'s products in B/mintpy/). Then write one line into %s:\n'
              '  mintpy.unwrapError.method = bridging     (or = no, to keep these products)\n'
              'and run again. With no, this phase reads its A/B again and passes. With bridging, admit takes it, mcfg stops '
              'at G5c.4 with mintpy/ in the way: move mintpy/ into %s/_archive/ and run again (mcfg and sbas run '
              'again with bridging)' % (folder, os.path.join(W, 'recon', 'admission.txt'), W))
    if verdict == 'bridging' and not operator and dmode == 'auto' and a.dryrun:
        v, note = 'INFO', ('dry run: under --decide auto R5 takes this bridging: a run writes %s, moves mintpy/ into %s/_archive/'
                           'mintpy_nobridging_<UTC>/ and restarts from admit (mcfg and sbas again with bridging)' % (DECISION_FILE, W))
    elif verdict == 'bridging' and not operator and dmode == 'auto' and os.environ.get('LINOG_RESTART') == 'allowed':
        tag = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        try:
            r5 = take_r5(W, ra, key, prior, sm, tag)
        except Exception as e:  # noqa: BLE001
            st.gate('G5dab.10', 'R5: bridging taken', 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:300]),
                    'mintpy/ moved into _archive/, the decision file written, the restart asked',
                    'look at %s, %s and mintpy/; the rest is v0.9\'s manual path: %s' % (DECISION_FILE, os.path.join(W, '_archive'), manual))
            st.rec['outputs'].update(folder=prior, reused=reused, result=sm)
            return st.finish()
        st.gate('G5dab.10', 'R5: bridging taken', 'PASS', '%s written (%s); mintpy/ moved to %s; %s asked%s' % (
            r5['decision'], r5['decision_md5'][:8], r5['moved_to'], r5['restart'], '; the earlier decision moved to %s' % r5['earlier']
            if r5['earlier'] else ''), 'record 108.3, R5')
        v, note = 'INFO', ('R5 under --decide auto: bridging taken (record 108.3). The driver runs the frame again from admit: admit takes '
                           'bridging from %s, mcfg and sbas run again, and this phase then reads it as chosen' % DECISION_FILE)
    elif verdict == 'bridging' and not operator:
        v, note = 'DECISION', ('the A/B reads bridging, and unwrapError no is MintPy\'s default here (recon/admission.txt names no method): '
                               'bridging changes the products, so the choice is the operator\'s (record 63.8)%s. ' % (
                                   ' under --decide ask' if dmode != 'auto' else '; under --decide auto R5 takes it only in a run of '
                                   'linog_auto.sh without --only, which restarts the frame from admit') + manual)
    elif verdict == 'bridging':
        v, note = 'INFO', 'the operator chose no in recon/admission.txt (%s): no stands' % src
    else:
        v, note = 'PASS', ''
    st.gate('D9ab', 'D9 by the A/B', v, 'the rule: %s (%s)%s; unwrapError stays %s (%s)%s' % (
        verdict, sm['why'], '' if sm['compared'] else ', the products NOT compared', meth, src, '; the A/B read again' if reused else ''),
        RULE % (sm['min_gain'] or 0), note)
    st.rec['outputs'].update(folder=prior, reused=reused, result=sm, log=os.path.join(folder, 'mintpy_B.log'), files=lst,
                             digest=P3.digest(lst), decision_md5=decision_digest(meth, src, sm), r5=r5)
    if a.dryrun:
        st.rec['outputs'].update(dryrun=True)
    return st.finish()


def grid_of(B):
    import h5py
    with h5py.File(os.path.join(B, 'inputs', 'ifgramStack.h5'), 'r') as f:
        return f['unwrapPhase'].shape[1:]


if __name__ == '__main__':
    P1.main_guard('lp_d9ab', main)
