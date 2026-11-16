#!/usr/bin/env python3
"""lp_dfit.py -- linog_auto Phase 5f (v0.10): R4, the screened dates on the velocity fit (record 108.3, 7.4's A/B); v0.13 r3
(the ascending record 96): the fit's dates out of the DEM-error fit too, MintPy's residual RMS rule run again until it stops.

Runs inside lp_env.sh, after wmask and before deliver. A date the kit's screen proposes over land (admit's R1: 3.0x the
frame's median spectral peak) stays in the network; this phase tests it on the velocity fit, as p449 F0290's delivery
tested 20101016 (its A/B lowered sigma from 0.478 to 0.432, -9.45 %, record 108.3). From the frame's own MintPy
products, read only:
  A    timeseries2velocity.py on mintpy/timeseries_ramp_demErr.h5 with MintPy's own exclusions (mintpy/exclude_date.txt as
       residual_RMS left it; none on F3310 and F3320), into this phase's folder: MintPy's fit, which must equal
       mintpy/velocity.h5 (G5f.6, the mirror; a WARN otherwise: A and B are made alike, so the A/B stands). A runs on
       every frame, candidate or not, so the fit's machinery is checked on each.
  B    the same with the date excluded too (--ex), one run per candidate (admit's decisions.r4: the screened dates left
       in the network).
  The date leaves the fit when B's velocity std (mm/yr) over the water-masked mintpy/maskTempCoh.h5, on the pixels where A
  and B are both finite, is lower than A's there (any fall, as approved); otherwise it stays, with a WARN. Each candidate is
  tested alone against A.
mintpy/exclude_date.txt is then made to hold the fit's dates: the union of MintPy's and the dates taken, one a line (the
final fit, without all of them, is run first, for the record and as a check). When the file already holds them it is left
as it is; otherwise the earlier file is first copied into this phase's folder (exclude_date_before.txt) and the file
written; when no date is out of the fit (MintPy wrote no file, and none is taken now) the file an earlier run of this phase
wrote is moved into the folder as exclude_date_before.txt. linog_phase6.sh (deliver) then fits its three velocities
without those dates and keeps them away from dem_error.py and remove_ramp.py (its lines 13 and 18): the demErr on every
date, the velocities on the fit's (N59: called directly, not through MintPy's --update). RUN_MANIFEST.json names the fit's
dates either way (deliver).
MintPy's own exclusions are told from this phase's by the record: when mintpy/exclude_date.txt is as this phase last left
or found it (its md5 as recorded, kept in every record from the first run on, through a failed or stopped run), MintPy's
dates are the ones recorded then; otherwise (the first run, or the file changed since, as a new sbas or a hand edit
leaves it) the file's dates are MintPy's. Before it writes or moves the file, this phase records the md5 the file will
have (None when moved), so a stop between the write and the record still finds the file as its own. A held file,
mintpy/_exclude_date.hold (linog_phase6.sh moves exclude_date.txt there at its line 13 and back at line 18, so it is left
there when a deliver stops between them), is a DECISION: the exclusions are in it, not in exclude_date.txt.
R4 is applied under both --decide modes: it changes the fit's dates only (not the network, the time series or the demErr),
by the A/B 7.4 set (record 108.3).
v0.13 r3 (LOGIC 2; the ascending record 95.3, 96.3, 97, after 64.4): a date out of the velocity fit still bends the velocity
through the DEM-error fit, which read every date until r2 (P448 F0290: 2.9 mm/yr at the 95th percentile, P450 F0300 the
same way). The rule: a date is out of both fits or of neither. After A (the mirror, as before):
  L1   the DEM-error loop from MintPy's dates, in this phase's folder (demfit/pass<k>/), on the ramp-first chain
       smallbaselineApp made: dem_error.py on mintpy/timeseries_ramp.h5 with the frame's template and geometry and an
       exclude_date.txt holding E in the pass's folder (MintPy's own key, mintpy.topographicResidual.excludeDate = auto,
       reads it there; its log must name exactly E: G5f.9's check), then timeseries_rms.py on that pass's residual with the
       template's residualRMS cutoff and deramp (auto: 3 and quadratic) and the mask smallbaselineApp's rule had
       (mintpy/watermask/maskTempCoh.orig.h5, wmask's copy of sbas's); a date the rule now names that is not in E joins E,
       and the loop runs again, at most DEMFIT_MAX_PASSES passes (G5f.10: a DECISION when it has not stopped by then). No
       loop when MintPy's rule took no date (G5f.9 INFO): the series is then sbas's.
  A1   timeseries2velocity.py on L1's last series without E1 (G5f.11); A itself when there was no loop.
  B    per candidate not in E1 (a candidate L1 took is not tested, G5f.11c): dem_error.py without E1 and the date (r4/<date>/),
       then the velocity fit without them on that series; taken when B's std falls below A1's (R4.N).
  L2   when R4 takes a date, the loop again from E1 and R4's dates (demfit2/), and the final fit on its series (G5f.8).
E then is the fit's dates: mintpy/exclude_date.txt holds it (G5f.7, as before), and deliver's linog_phase6_r3.sh reads it for
its dem_error as well as its velocities. The network is not touched.
The limit (97.6): linog_mintpy.cfg's DFIT_DEMFIT_MAX_PASSES (4 when absent), in the fingerprint. After a G5f.10 DECISION a person
writes recon/demfit.txt (the dates to take out of both fits, one a line, MintPy's own among them; in the fingerprint and the
decision): L1 is then one pass on that set, which the rule does not grow (G5f.10 INFO names what it would add), and L2, when R4
takes a date, one pass on that set and R4's (G5f.5o: the file's dates in the series, MintPy's among them, else FAIL).

Gates
  G5f.1  wmask PASS on record, its files as it recorded them                                           FAIL
  G5f.1a admit PASS on record (a gate only when it is not)                                             FAIL
  G5f.1j recon/admission.json read: the screened dates admit left in the network                FAIL / PASS
  G5f.2  environment; MintPy at its pin                                                   ERROR / FAIL
  G5f.3  timeseries2velocity.py (v0.13 r3: and dem_error.py, timeseries_rms.py) on the PATH is the pinned env's FAIL
  G5f.4  the inputs: mintpy/timeseries_ramp_demErr.h5, maskTempCoh.h5 (the water mask's), velocity.h5; v0.13 r3:
         timeseries_ramp.h5, smallbaselineApp.cfg (its residualRMS keys), inputs/geometryRadar.h5,
         watermask/maskTempCoh.orig.h5                                                                FAIL
  G5f.4h no mintpy/_exclude_date.hold (linog_phase6.sh's held file)                                DECISION
  G5f.5  MintPy's own exclusions; the candidates                                                       INFO
  G5f.6  A: rc 0, and A's velocity = mintpy/velocity.h5's (the mirror)                         FAIL / WARN / PASS
  G5f.9  v0.13 r3: the DEM-error loop (L1 demfit, L2 demfit2), one line a pass: dem_error.py and timeseries_rms.py rc 0,
         dem_error's log names exactly E; the dates the rule names, the median RMS; INFO: no loop      FAIL / INFO / PASS
  G5f.10 v0.13 r3: a loop's end: E unchanged by its last pass (PASS), or not within the limit (DECISION);
         the operator's set, one pass (INFO)                                                   PASS / DECISION / INFO
  G5f.5o v0.13 r3: the pass limit a whole number; recon/demfit.txt, when there, in the series and holding MintPy's
         dates                                                                                 FAIL / INFO
  G5f.11 v0.13 r3: A1, the velocity on L1's series without E1: rc 0                                    FAIL
  G5f.11c v0.13 r3: candidates L1 already took (not tested)                                           INFO
  R4.N   per candidate N: B (v0.13 r3: dem_error.py and the velocity fit, both without E1 and the date) rc 0, the
         log naming those dates; taken when its std falls below A1's (INFO), kept otherwise (WARN)  FAIL / INFO / WARN
  G5f.8  the final fit, on L2's series without all the fit's dates, when a date is taken: rc 0         FAIL
  G5f.7  mintpy/exclude_date.txt: as it should be (PASS), or written, or moved aside (INFO)            FAIL
--state: STALE also when this phase's evidence or mintpy/exclude_date.txt changed since. --dryrun DIR: the same fits,
with the folder under DIR and nothing written in the frame (what it would write is printed); a plan only when the frame's
wmask has not run. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import time

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

PHASE, IDX, LOGIC = 'dfit', '5f', 2   # v0.13 r3: 2, the DEM-error loop (r2 and earlier: 1)
VERSION_DFIT = 'linog_auto v0.13 r3 (2026-10-30)'   # the release that last changed this phase
DEMFIT_MAX_PASSES = 4   # v0.13 r3: the DEM-error loop stops by then or holds for a person (G5f.10); linog_mintpy.cfg's
# DFIT_DEMFIT_MAX_PASSES when it names one (the ascending record 97.6)
OPFILE = 'recon/demfit.txt'   # v0.13 r3 (97.6): the dates a person takes out of both fits, after a G5f.10 DECISION
TSR = 'mintpy/timeseries_ramp.h5'   # v0.13 r3: the ramp-first chain's input (smallbaselineApp's deramp)
TPL = 'mintpy/smallbaselineApp.cfg'
GEOM = 'mintpy/inputs/geometryRadar.h5'
RMSMASK = 'mintpy/watermask/maskTempCoh.orig.h5'   # sbas's mask as smallbaselineApp's residual_RMS read it (wmask's copy)
DEMCMD, RMSCMD = 'dem_error.py', 'timeseries_rms.py'
EXMSG = re.compile(r'exclude the following dates for DEM error estimation: \((\d+)\)\s*\n\s*\[([^\]]*)\]')
TS = 'mintpy/timeseries_ramp_demErr.h5'
MASK = 'mintpy/maskTempCoh.h5'
VEL = 'mintpy/velocity.h5'
EXCL = 'mintpy/exclude_date.txt'
CMD = 'timeseries2velocity.py'
HOLD = 'mintpy/_exclude_date.hold'   # linog_phase6.sh's line 13 moves exclude_date.txt here, its line 18 back
EVIDENCE = ('fit.json',)
CARRY = ('base', 'excl_md5_after', 'excl_pending')   # what the record knows of mintpy/exclude_date.txt, kept through a stopped run
# excl_pending: {'md5': the file's md5 after this phase's write, or None after its move}, recorded just before the write or
# the move and dropped with the record's update after it


def say(s=''):
    print(s, flush=True)


def read_dates(p):
    """The dates of an exclude_date.txt (MintPy's read_date_txt: one YYYYMMDD a line; # comments), sorted."""
    out = []
    for ln in open(p, errors='replace') if p and os.path.isfile(p) else []:
        s = ln.split('#', 1)[0].strip()
        if s:
            out.append(s.split()[0][:8])
    return sorted(set(out))


def md5q(p):
    return C.md5_file(p) if os.path.isfile(p) else None


def new_folder(recdir):
    base = os.path.join(recdir, 'dfit', time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    d, n = base, 1
    while True:
        try:
            os.mkdir(d)
            return d
        except FileExistsError:
            n += 1
            d = '%s_%d' % (base, n)


def fit(ts, out, ex, folder, name, timeout, extra_env):
    """timeseries2velocity.py ts -o out [--ex dates] from folder (no template: MintPy's defaults, which the template's auto
    values are; no exclude_date.txt is read there), its output in folder/name.log. (rc, seconds, the log)."""
    cmd = [CMD, ts, '-o', out] + (['--ex'] + list(ex) if ex else [])
    lg = os.path.join(folder, name + '.log')
    t0 = time.time()
    import lp_d9ab as D9
    rc, _, late = D9.run_b(cmd, folder, lg, extra_env, timeout)
    return (rc if not late else -9), time.time() - t0, lg


def vel(p):
    import h5py
    with h5py.File(p, 'r') as f:
        return f['velocity'][()]


def std_mm(v, m):
    x = v[m].astype('f8') * 1000.0
    return float(x.std()) if x.size else None


def ts_dates(p):
    import h5py
    with h5py.File(p, 'r') as f:
        return [d.decode() if isinstance(d, bytes) else str(d) for d in f['date'][()]]


def template_rms(W):
    """v0.13 r3: the frame template's residual-RMS settings as smallbaselineApp read them (auto: MintPy 1.6.2's defaults,
    cutoff 3, deramp quadratic, maskFile maskTempCoh.h5, which here is sbas's mask, wmask's copy of it), and its
    topographicResidual.excludeDate (auto or exclude_date.txt: dem_error reads the folder's file). (dict, problems)."""
    keys = {}
    for ln in open(os.path.join(W, TPL), errors='replace'):
        s = ln.split('#', 1)[0]
        if '=' in s:
            k, v = s.split('=', 1)
            keys[k.strip()] = v.strip()
    bad = []
    cut = keys.get('mintpy.residualRMS.cutoff', 'auto')
    ramp = keys.get('mintpy.residualRMS.deramp', 'auto')
    mfile = keys.get('mintpy.residualRMS.maskFile', 'auto')
    exd = keys.get('mintpy.topographicResidual.excludeDate', 'auto')
    try:
        cut = 3.0 if cut in ('auto', '') else float(cut)
    except ValueError:
        bad.append('mintpy.residualRMS.cutoff %r' % cut)
    ramp = 'quadratic' if ramp in ('auto', '') else ramp
    if ramp not in ('quadratic', 'linear', 'no'):
        bad.append('mintpy.residualRMS.deramp %r' % ramp)
    if mfile in ('auto', '', 'maskTempCoh.h5'):
        mask = os.path.join(W, RMSMASK)
    else:
        bad.append('mintpy.residualRMS.maskFile %r (r3 reads sbas\'s maskTempCoh.h5 only)' % mfile)
        mask = None
    if exd not in ('auto', '', 'exclude_date.txt'):
        bad.append('mintpy.topographicResidual.excludeDate %r (dem_error would not read the pass\'s exclude_date.txt)' % exd)
    return dict(cutoff=cut, deramp=ramp, mask=mask, topo_exclude=exd), bad


def dem_excluded(log):
    """v0.13 r3: the dates dem_error.py's log names as out of its fit ([] when it names none), or None when its line is not
    read whole."""
    txt = open(log, errors='replace').read() if os.path.isfile(log) else ''
    m = EXMSG.search(txt)
    if not m:
        return [] if 'exclude the following dates' not in txt else None
    ds = re.findall(r'\d{8}', m.group(2))
    return sorted(ds) if len(ds) == int(m.group(1)) else None


def rms_of(p):
    """v0.13 r3: {date: RMS} of a rms_timeseriesResidual_*.txt."""
    out = {}
    for ln in open(p, errors='replace') if os.path.isfile(p) else []:
        s = ln.split()
        if s and not ln.startswith('#') and len(s) >= 2 and s[0].isdigit():
            out[s[0][:8]] = float(s[1])
    return out


def dem_fit(W, pd, E, timeout, xenv):
    """v0.13 r3: dem_error.py on the ramp-first input (mintpy/timeseries_ramp.h5, the frame's template and geometry) without
    the dates E, in the new folder pd: pd/exclude_date.txt holds E while it runs (the template's
    topographicResidual.excludeDate, auto, reads it there) and is kept after as exclude_date_input.txt. (rc, the dates its
    log names, the corrected series, the log, seconds); rc -9 at the time limit."""
    import lp_d9ab as D9
    os.makedirs(pd)
    with open(os.path.join(pd, 'exclude_date.txt'), 'w') as fh:
        fh.write(''.join('%s\n' % d for d in E))
    t0 = time.time()
    lg = os.path.join(pd, 'dem_error.log')
    out = os.path.join(pd, 'ts_ramp_demErr.h5')
    rc, _, late = D9.run_b([DEMCMD, os.path.join(W, TSR), '-t', os.path.join(W, TPL), '-g', os.path.join(W, GEOM), '-o', out,
                            '--dem-err-file', os.path.join(pd, 'demErr.h5')], pd, lg, xenv, timeout)
    # the folder's exclude_date.txt is the input; timeseries_rms.py writes its own there: the input kept beside it
    os.replace(os.path.join(pd, 'exclude_date.txt'), os.path.join(pd, 'exclude_date_input.txt'))
    return (-9 if late else rc), dem_excluded(lg), out, lg, time.time() - t0


def demfit_loop(st, W, folder, E0, tpl, timeout, xenv, root, maxp=DEMFIT_MAX_PASSES, fixed=None):
    """v0.13 r3: the DEM-error loop from the dates E0, in folder/root/pass<k>/ (G5f.9 a pass, G5f.10 its end), at most maxp
    passes. fixed (97.6): the operator's file (its relative path and md5) when E0 is its set: one pass, E kept as the file has
    it, the dates the rule names beyond it recorded (G5f.10 INFO). (E, passes, ok, the last pass's series): ok False after a
    FAIL or a DECISION (the gate said which)."""
    import lp_d9ab as D9
    E, passes, ser = sorted(set(E0)), [], None
    for k in range(1, (1 if fixed else maxp) + 1):
        pd = os.path.join(folder, root, 'pass%d' % k)
        rc1, named, ser, lg1, sec1 = dem_fit(W, pd, E, timeout, xenv)
        rc2, rms, over = None, {}, None
        t0 = time.time()
        if rc1 == 0 and named == E:
            lg2 = os.path.join(pd, 'timeseries_rms.log')
            rc2, _, late2 = D9.run_b([RMSCMD, os.path.join(pd, 'timeseriesResidual.h5'), '-m', tpl['mask'], '-r', tpl['deramp'],
                                      '--cutoff', '%g' % tpl['cutoff']], pd, lg2, xenv, timeout)
            rc2 = -9 if late2 else rc2
            # MintPy 1.6.2's name (utils1.get_residual_rms): rms_<residual>[_ramp].txt beside the residual
            rms = rms_of(os.path.join(pd, 'rms_timeseriesResidual%s.txt' % ('' if tpl['deramp'] == 'no' else '_ramp')))
            over = read_dates(os.path.join(pd, 'exclude_date.txt'))   # MintPy removes the file when no date is over the cutoff
        sec = sec1 + time.time() - t0
        med = statistics.median(rms.values()) if rms else None   # as MintPy's np.median (the review's item 5)
        new = sorted(set(over or []) - set(E))
        row = dict(n=k, folder=os.path.relpath(pd, folder), excluded=E, dem_error_rc=rc1, dem_error_named=named, rms_rc=rc2,
                   over=over, new=new, median_rms_m=med, seconds=round(sec, 1), top=sorted(rms.items(), key=lambda kv: -kv[1])[:4])
        passes.append(row)
        fail = rc1 != 0 or named != E or rc2 != 0 or over is None or not rms
        st.gate('G5f.9', 'the DEM-error loop (%s), pass %d' % (root, k), 'FAIL' if fail else 'PASS',
                'dem_error.py on %s without %s: rc %s, its log names %s; timeseries_rms.py (cutoff %g, deramp %s, %s): rc %s; over the '
                'cutoff %s; new %s; median RMS %s m; %.0f s' % (
                    TSR, ', '.join(E) or 'no date', rc1, ', '.join(named) if named else ('no date' if named == [] else 'NOT READ'),
                    tpl['cutoff'], tpl['deramp'], os.path.relpath(tpl['mask'], W), rc2, ', '.join(over or []) or 'none',
                    ', '.join(new) or 'none', '%.5f' % med if med is not None else '-', sec),
                'rc 0 each; dem_error\'s log names exactly the dates out of the fit', 'logs in %s' % pd if fail else '')
        if fail:
            return E, passes, False, ser
        if fixed:
            st.gate('G5f.10', 'the DEM-error loop\'s end (%s)' % root, 'INFO', 'the operator\'s set, %s (md5 %s): %s out of both fits; the '
                    'rule names %s beyond it, kept in the fits by the file' % (fixed[0], fixed[1], ', '.join(E), ', '.join(new) or 'no date'),
                    'v0.13 r3 (97.6): a person\'s set after a DECISION, one pass')
            return E, passes, True, ser
        if not new:
            st.gate('G5f.10', 'the DEM-error loop\'s end (%s)' % root, 'PASS', 'stopped after pass %d: the dates out of the DEM-error fit '
                    '%s' % (k, ', '.join(E) or 'none'), 'a pass that names no new date, within %d' % maxp)
            return E, passes, True, ser
        E = sorted(set(E) | set(new))
    st.gate('G5f.10', 'the DEM-error loop\'s end (%s)' % root, 'DECISION', 'not stopped in %d passes: the last named %s; the dates out so '
            'far %s' % (maxp, ', '.join(passes[-1]['new']), ', '.join(E)), 'a pass that names no new date, within %d' % maxp,
            'each pass takes more dates out of the DEM-error fit and the rule names more: read the passes\' RMS lists (%s), then write '
            'the dates to take out of both fits, MintPy\'s own among them, one a line, into %s and run dfit again (one pass on that '
            'set; the network is not touched: recon/admission.txt is not the route)' % (os.path.join(folder, root), os.path.join(W, OPFILE)))
    return E, passes, False, ser


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5f: R4, the screened dates on the velocity fit')
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
    dry = bool(a.dryrun)
    rw = (P1.record(W, '5e', 'wmask') if dry else None) or P1.record(recdir, '5e', 'wmask') or {}
    rs = (P1.record(W, '5d', 'sbas') if dry else None) or P1.record(recdir, '5d', 'sbas') or {}
    ra = P1.record(recdir, '5a', 'admit') or {}
    prev = P1.record(W, IDX, PHASE) or {}   # the frame's own record (read before this run replaces it): its exclude_date.txt
    maxp_s = m.get('DFIT_DEMFIT_MAX_PASSES') or str(DEMFIT_MAX_PASSES)   # v0.13 r3 (97.6)
    opf = os.path.join(W, OPFILE)
    op_md5 = md5q(opf)
    fp = C.md5_obj(dict(logic=LOGIC, wmask=(rw.get('outputs') or {}).get('digest'), sbas=(rs.get('outputs') or {}).get('digest'),
                        r4=(ra.get('outputs') or {}).get('r4_md5'), mintpy=m['MINTPY_VERSION'], defaults=m['MINTPY_DEFAULTS_MD5'],
                        demfit_max_passes=maxp_s, demfit_file=op_md5))

    def changed(rec):
        o = (rec or {}).get('outputs') or {}
        out = P3.listing_changed(W, [x[0] for x in o.get('files') or []], o.get('files'))
        if 'excl_md5_after' in o and md5q(os.path.join(W, EXCL)) != o.get('excl_md5_after'):
            out.append('changed: %s' % EXCL)
        return out
    if a.state:
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, changed))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5'],
                                                                   timeout_s=m['DFIT_TIMEOUT_S'], demfit_max_passes=maxp_s,
                                                                   demfit_file=OPFILE if op_md5 else None, demfit_file_md5=op_md5))
    st.rec['version'] = VERSION_DFIT   # v0.13 r3: this phase's release
    po = prev.get('outputs') or {}
    carry = dict((k, po[k]) for k in CARRY if k in po)
    if not dry:   # the frame's record keeps what it knew of the file until this run knows better (a stop below keeps it)
        st.rec['outputs'] = dict(carry)
        st.write()
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    rw, from_frame = P6.prior6(st, 'G5f.1', recdir, W, '5e', 'wmask', P6.WMASK_OUTS, dry)
    if not rw:
        return st.finish()
    if dry and (not from_frame or (rw.get('outputs') or {}).get('planned')):
        return P5.plan_only(st, ['would fit the velocity (timeseries2velocity.py on %s) with MintPy\'s own exclusions (A) and with each '
                                 'screened date excluded too (B), and write %s when a date\'s B lowers the std over maskTempCoh' % (TS, EXCL)],
                            'the frame\'s wmask has not run, so there are no masked products to fit')
    ra = P3.prior3(st, 'G5f.1a', recdir, '5a', 'admit')
    if not ra:
        return st.finish()
    aj = os.path.join(recdir, 'recon', 'admission.json')
    try:
        adm = json.load(open(aj))
        r4 = ((adm.get('decisions') or {}).get('r4') or {})
        cands = list(r4.get('dates') or [])
    except (OSError, ValueError) as e:
        st.gate('G5f.1a', 'admit\'s decisions', 'FAIL', '%s: %s' % (aj, e), 'recon/admission.json')
        return st.finish()
    st.gate('G5f.1j', 'admit\'s screened dates', 'PASS', '%s: %s' % (aj, ', '.join(cands) or 'none') + (
        '' if 'r4' in (adm.get('decisions') or {}) else ' (no decisions.r4: admit ran before v0.10)'), 'recon/admission.json')
    if not P5.env_gate(st, 'G5f.2', env, s, m):
        return st.finish()
    if not P5.which_gate(st, 'G5f.3', s, (CMD, DEMCMD, RMSCMD)):
        return st.finish()
    miss = [x for x in (TS, MASK, VEL, TSR, TPL, GEOM, RMSMASK) if not os.path.isfile(os.path.join(W, x))]
    tpl, tbad = template_rms(W) if os.path.isfile(os.path.join(W, TPL)) else ({}, [])
    st.gate('G5f.4', 'the inputs', 'FAIL' if miss or tbad else 'PASS', '; '.join((['absent: %s' % ', '.join(miss)] if miss else []) + tbad)
            if miss or tbad else '%s, %s (the water mask\'s), %s; v0.13 r3: %s, %s, %s, %s; residualRMS cutoff %g, deramp %s' % (
                TS, MASK, VEL, TSR, TPL, GEOM, RMSMASK, tpl['cutoff'], tpl['deramp']),
            'all present; the template\'s residualRMS and topographicResidual.excludeDate as r3 reads them')
    if miss or tbad:
        return st.finish()
    import numpy as np
    exf = os.path.join(W, EXCL)
    if os.path.lexists(os.path.join(W, HOLD)):
        st.gate('G5f.4h', 'linog_phase6.sh\'s held file', 'DECISION', '%s exists%s' % (
            HOLD, ', beside %s' % EXCL if os.path.lexists(exf) else ', %s absent' % EXCL),
            'absent (linog_phase6.sh moves %s there at its line 13 and back at its line 18)' % EXCL,
            'a deliver stopped or failed between those two lines, so the fit\'s dates (MintPy\'s and this phase\'s) are in %s, not in '
            '%s. %s' % (HOLD, EXCL, 'Put it back, then run again:\n  mv -n %s %s' % (os.path.join(W, HOLD), exf) if not os.path.lexists(exf) else
                        'Both files exist: compare them, keep the one that holds the fit\'s dates as %s, move the other into the frame\'s '
                        '_archive/, then run again' % EXCL))
        return st.finish()
    now5 = md5q(exf)
    pend = carry.get('excl_pending')
    own = ('excl_md5_after' in carry and carry.get('excl_md5_after') == now5) or (
        isinstance(pend, dict) and 'md5' in pend and pend.get('md5') == now5)   # the file as this phase last left it, or as a stopped write of it did
    if own:
        base = list(carry.get('base') or [])
        bsrc = 'MintPy\'s, as this phase recorded them (%s as it last left or found it)' % EXCL
    else:
        base, bsrc = read_dates(exf), ('%s as MintPy\'s residual_RMS left it' % EXCL) if now5 else 'none (MintPy wrote no %s)' % EXCL
    if not dry:   # from here on the record knows the file as this run found it
        st.rec['outputs'].update(base=base, excl_md5_after=now5)
        st.rec['outputs'].pop('excl_pending', None)
        st.write()
    tsd = ts_dates(os.path.join(W, TS))
    test = [d for d in cands if d in tsd and d not in base]
    # v0.13 r3 (97.6): the pass limit (linog_mintpy.cfg's DFIT_DEMFIT_MAX_PASSES, else 4) and the operator's file, when there
    try:
        maxp = int(maxp_s)
    except ValueError:
        maxp = 0
    op = read_dates(opf) if op_md5 else None
    obad = ([] if maxp >= 1 else ['DFIT_DEMFIT_MAX_PASSES %r: not a whole number of at least 1' % maxp_s])
    if op is not None:
        obad += (['%s names %s, not in the series' % (OPFILE, ', '.join(sorted(set(op) - set(tsd))))] if set(op) - set(tsd) else []) + \
            (['%s leaves out MintPy\'s %s (its own outliers stay out of the fits)' % (OPFILE, ', '.join(sorted(set(base) - set(op))))]
             if set(base) - set(op) else []) + (['%s names no date' % OPFILE] if not op else [])
    if obad or op is not None:
        st.gate('G5f.5o', 'the loop\'s limit and the operator\'s file', 'FAIL' if obad else 'INFO', '; '.join(obad) or
                '%s (md5 %s): %s out of both fits, one pass on that set; the limit %d passes' % (OPFILE, op_md5, ', '.join(op), maxp),
                'v0.13 r3 (97.6): a whole number of passes; the file\'s dates in the series, MintPy\'s own among them')
        if obad:
            return st.finish()
    st.gate('G5f.5', 'MintPy\'s exclusions; the candidates', 'INFO', 'MintPy\'s: %s (%s); the time series %d dates; candidates %s%s' % (
        ', '.join(base) or 'none', bsrc, len(tsd), ', '.join(test) or 'none', '; not tested (not in the series, or MintPy\'s already): %s' % ', '.join(
            sorted(set(cands) - set(test))) if set(cands) - set(test) else ''), 'record 108.3, R4')
    folder = new_folder(recdir)
    rel = os.path.relpath(folder, recdir)
    timeout = int(m['DFIT_TIMEOUT_S'])
    xenv = dict(P5.mpl_env(recdir), PYTHONUNBUFFERED='1')
    tsp = os.path.join(W, TS)
    st.rec['outputs'].update(folder=rel, base=base, base_source=bsrc, candidates=test)
    st.write()
    rcA, secA, lgA = fit(tsp, os.path.join(folder, 'velocity_A.h5'), base, folder, 'fit_A', timeout, xenv)
    if rcA != 0 or not os.path.isfile(os.path.join(folder, 'velocity_A.h5')):
        st.gate('G5f.6', 'A: MintPy\'s fit', 'FAIL', 'rc %d in %.0f s%s' % (rcA, secA, ' (stopped at the time limit)' if rcA == -9 else ''),
                'rc 0; velocity_A.h5', 'log %s\n%s' % (lgA, P3.tail(lgA, 8)))
        return st.finish()
    vA, vM = vel(os.path.join(folder, 'velocity_A.h5')), vel(os.path.join(W, VEL))
    same = vA.shape == vM.shape and bool(np.array_equal(vA, vM, equal_nan=True))
    dmax = None if vA.shape != vM.shape else float(np.nanmax(np.abs(vA.astype('f8') - vM.astype('f8')))) * 1000.0 if np.isfinite(vA - vM).any() else 0.0
    st.gate('G5f.6', 'A: MintPy\'s fit', 'PASS' if same else 'WARN', 'rc 0 in %.0f s; --ex %s; velocity_A.h5 %s mintpy/velocity.h5%s' % (
        secA, ' '.join(base) or 'none', 'equals' if same else 'DIFFERS from', '' if same else ' (largest |difference| %s mm/yr)' % (
            '%.3g' % dmax if dmax is not None else 'shapes %s and %s' % (vA.shape, vM.shape))),
        'equal (A is MintPy\'s own fit)', '' if same else 'A and B are made alike, so the A/B stands; the velocity MintPy wrote is not '
        'reproduced by its own tool here: read %s' % lgA)
    mk = None
    import h5py
    with h5py.File(os.path.join(W, MASK), 'r') as f:
        mk = f[list(f.keys())[0]][()].astype(bool)
    tests, taken = [], []
    # v0.13 r3: the DEM-error loop first, from MintPy's dates (L1, demfit/), so each candidate is tested on the series its two
    # fits will have; R4's A is then the velocity on that series without E1 (A itself when no date is out: sbas's series)
    demfit = dict(max_passes=maxp, template=tpl, loops=[], operator_file=OPFILE if op else None, operator_file_md5=op_md5 if op else None)

    def stop(final_, fin_=None):
        st.rec['outputs'].update(tests=tests, taken=taken, final=final_, final_fit=fin_, demfit=demfit)
        return st.finish()
    E1, ser = list(base), tsp
    fx = (OPFILE, op_md5) if op else None
    if base or op:
        E1, passes, ok, ser = demfit_loop(st, W, folder, op or base, tpl, timeout, xenv, 'demfit', maxp, fx)
        demfit['loops'].append(dict(root='demfit', start=list(op or base), passes=passes, final=E1, stopped=ok))
        if not ok:
            return stop(E1)
    else:
        st.gate('G5f.9', 'the DEM-error loop (demfit)', 'INFO', 'MintPy\'s rule took no date: dem_error keeps every date (sbas\'s series '
                '%s), no loop' % TS, 'v0.13 r3: the fit\'s dates out of the DEM-error fit too')
    vA1 = vA
    if ser != tsp:
        rcA1, secA1, lgA1 = fit(ser, os.path.join(folder, 'velocity_A1.h5'), E1, folder, 'fit_A1', timeout, xenv)
        ok = rcA1 == 0 and os.path.isfile(os.path.join(folder, 'velocity_A1.h5'))
        st.gate('G5f.11', 'A1: the fit on the loop\'s series', 'PASS' if ok else 'FAIL', 'rc %d in %.0f s; %s --ex %s' % (
            rcA1, secA1, os.path.relpath(ser, folder), ' '.join(E1)), 'rc 0; velocity_A1.h5 (v0.13 r3: R4\'s A)',
            '' if ok else 'log %s\n%s' % (lgA1, P3.tail(lgA1, 8)))
        if not ok:
            return stop(E1)
        vA1 = vel(os.path.join(folder, 'velocity_A1.h5'))
    inloop = [d for d in test if d in E1]
    test1 = [d for d in test if d not in E1]
    if inloop:
        st.gate('G5f.11c', 'candidates the loop took', 'INFO', '%s out of both fits by MintPy\'s rule on the loop\'s series: not tested' %
                ', '.join(inloop), 'v0.13 r3')
    for i, d in enumerate(test1, 1):
        X = sorted(set(E1) | {d})
        rcD, named, tsd_, lgD, secD = dem_fit(W, os.path.join(folder, 'r4', d), X, timeout, xenv)
        out = os.path.join(folder, 'velocity_B_%s.h5' % d)
        rcB, secB, lgB = (fit(tsd_, out, X, folder, 'fit_B_%s' % d, timeout, xenv) if rcD == 0 and named == X else (None, 0.0, None))
        if rcD != 0 or named != X or rcB != 0 or not os.path.isfile(out):
            st.gate('R4.%d' % i, 'the fits without %s' % d, 'FAIL', 'dem_error.py without %s: rc %s, its log names %s; the velocity fit: rc %s' % (
                ', '.join(X), rcD, ', '.join(named) if named else ('no date' if named == [] else 'NOT READ'), rcB), 'rc 0 each; the log names '
                'exactly those dates', 'logs %s, %s' % (lgD, lgB or '(the fit not run)'))
            return stop(E1)
        vB = vel(out)
        common = mk & np.isfinite(vA1) & np.isfinite(vB)
        sa, sb = std_mm(vA1, common), std_mm(vB, common)
        fall = sa is not None and sb is not None and sb < sa
        ch = (sb - sa) / sa if sa else None
        tests.append(dict(date=d, ratio=(r4.get('ratios') or {}).get(d), std_a=sa, std_b=sb, change=ch, px=int(common.sum()), taken=fall,
                          seconds=round(secD + secB, 1), both_fits=True))
        if fall:
            taken.append(d)
        st.gate('R4.%d' % i, 'the fits without %s' % d, 'INFO' if fall else 'WARN', 'v0.13 r3, the date out of both fits: velocity std over '
                'maskTempCoh (%d px): A1 %s, B %s mm/yr (%s): %s' % (
                    common.sum(), '%.4f' % sa if sa is not None else 'none', '%.4f' % sb if sb is not None else 'none',
                    '%+.2f %%' % (100 * ch) if ch is not None else '-', 'the date leaves both fits' if fall else 'the date stays in both fits'),
                'B lower than A1: the date leaves the fits (record 108.3, R4; v0.13 r3: the velocity and DEM-error fits)',
                '' if fall else 'its exclusion does not lower the velocity\'s spread, so it stays; RUN_MANIFEST.json names it')
    E = sorted(set(E1) | set(taken))
    if taken:   # L2: the loop again from E1 and R4's dates, in demfit2/
        E, passes, ok, ser = demfit_loop(st, W, folder, E, tpl, timeout, xenv, 'demfit2', maxp, fx)
        demfit['loops'].append(dict(root='demfit2', start=sorted(set(E1) | set(taken)), passes=passes, final=E, stopped=ok))
        if not ok:
            return stop(E)
    final = E
    fin = None
    if taken:   # the final fit, on the loop's series without every date out of the fits: for the record, and as a check
        rcF, secF, lgF = fit(ser, os.path.join(folder, 'velocity_final.h5'), final, folder, 'fit_final', timeout, xenv)
        if rcF != 0 or not os.path.isfile(os.path.join(folder, 'velocity_final.h5')):
            st.gate('G5f.8', 'the final fit', 'FAIL', 'rc %d in %.0f s%s' % (rcF, secF, ' (stopped at the time limit)' if rcF == -9 else ''),
                    'rc 0; velocity_final.h5', 'the fit without %s failed: %s is not written. Log %s\n%s' % (
                        ', '.join(final), EXCL, lgF, P3.tail(lgF, 8)))
            return stop(final, dict(rc=rcF))
        vF = vel(os.path.join(folder, 'velocity_final.h5'))
        cm = mk & np.isfinite(vA1) & np.isfinite(vF)
        fin = dict(std_a=std_mm(vA1, cm), std_final=std_mm(vF, cm), px=int(cm.sum()), rc=rcF, series=os.path.relpath(ser, folder))
        st.gate('G5f.8', 'the final fit', 'PASS', 'rc 0 in %.0f s, on %s without %s: velocity std %s mm/yr over %d px (A1 %s)' % (
            secF, os.path.relpath(ser, folder), ', '.join(final), '%.4f' % fin['std_final'] if fin['std_final'] is not None else 'none',
            fin['px'], '%.4f' % fin['std_a'] if fin['std_a'] is not None else 'none'), 'rc 0')
    demfit.update(final=final, stopped=True, added=sorted(set(final) - set(base) - set(taken)),
                  series=os.path.relpath(ser, folder) if ser != tsp else TS)
    # the file is to hold the fit's dates (final): left when it does, written when it does not, moved aside when no date is out
    # of the fit and an earlier run of this phase wrote it (with MintPy's none). Not touched in a dry run.
    cur = read_dates(exf) if os.path.isfile(exf) else None
    earlier = sorted(set(cur or []) - set(final))   # dates the file holds that are no longer out of the fit: this phase's earlier ones
    what = 'MintPy\'s %s%s%s' % (', '.join(base) or 'none', '; R4\'s %s' % ', '.join(taken) if taken else '',
                               '; the DEM-error loop\'s %s' % ', '.join(demfit['added']) if demfit.get('added') else '')
    if (cur or []) == final:
        act, v = 'left', 'PASS'
        txt = ('as it should be, %s (%s)' % (', '.join(final), what)) if final else 'no file, and no date out of the fit: as MintPy left it' \
            if cur is None else 'the file holds no date, and none is out of the fit'
    elif final:
        act, v = 'write', 'INFO'
        txt = 'written: %s (%s)%s' % (', '.join(final), what, '; %s back in the fit (an earlier run of this phase had taken %s)' % (
            ', '.join(earlier), 'it' if len(earlier) == 1 else 'them') if earlier else '')
    else:
        act, v = 'move', 'INFO'
        txt = 'moved into %s/exclude_date_before.txt: no date is out of the fit now (MintPy wrote no file); %s back in the fit (an earlier ' \
              'run of this phase had taken %s)' % (rel, ', '.join(earlier), 'it' if len(earlier) == 1 else 'them')
    written = False
    if dry:
        if act != 'left':
            v, txt = 'INFO', 'dry run: a run would leave the file %s; the frame is not touched' % (
                'holding %s (%s)' % (', '.join(final), what) if final else 'moved aside (no date out of the fit)')
    elif act == 'write':
        if os.path.isfile(exf):
            shutil.copy2(exf, os.path.join(folder, 'exclude_date_before.txt'))
        body = ''.join('%s\n' % d for d in final).encode()
        st.rec['outputs']['excl_pending'] = dict(md5=hashlib.md5(body).hexdigest())   # recorded before the write (see CARRY)
        st.write()
        tmp = exf + '.tmp%d' % os.getpid()
        with open(tmp, 'wb') as fh:
            fh.write(body)
        os.replace(tmp, exf)
        written = True
    elif act == 'move':
        dst = os.path.join(folder, 'exclude_date_before.txt')
        if os.path.lexists(dst):
            raise ValueError('%s exists already' % dst)
        st.rec['outputs']['excl_pending'] = dict(md5=None)   # recorded before the move (see CARRY)
        st.write()
        os.rename(exf, dst)
        written = True
    after = md5q(exf)
    if not dry:   # the record knows the file as this run left it before the gate writes the record
        st.rec['outputs'].update(excl_md5_after=after)
        st.rec['outputs'].pop('excl_pending', None)
    bad = not dry and (read_dates(exf) if os.path.isfile(exf) else []) != final
    st.gate('G5f.7', EXCL, 'FAIL' if bad else v, txt + ('; the earlier file kept as %s/exclude_date_before.txt' % rel
                                                     if written and os.path.isfile(os.path.join(folder, 'exclude_date_before.txt')) else ''),
            'the fit\'s dates (MintPy\'s, R4\'s and the DEM-error loop\'s), one a line; linog_phase6_r3.sh fits the velocities and '
            'the DEM error without them',
            'the file does not hold %s' % (', '.join(final) or 'no date') if bad else '')
    if bad:
        return st.finish()
    res = dict(frame=W, written=C.utc(), base=base, base_source=bsrc, candidates=test, tests=tests, taken=taken, final=final,
               final_fit=fin, demfit=demfit, a_mirror=dict(equal=same, max_abs_mm_yr=dmax), mask=MASK, ts=TS, pipeline=P6.HERE, version=P5.VERSION_P5,
               dry_run=dry, excl_written=written)
    P5.write_json(os.path.join(folder, 'fit.json'), res)
    rels = [os.path.relpath(os.path.join(folder, n), W) for n in EVIDENCE if os.path.isfile(os.path.join(folder, n))] if not dry else []
    lst = P3.listing(W, rels) if rels else []
    st.rec['outputs'].update(tests=tests, taken=taken, final=final, final_fit=fin, a_mirror=dict(equal=same, max_abs_mm_yr=dmax),
                             excl_written=written, excl_md5_after=after, files=lst, digest=P3.digest(lst), demfit=demfit,
                             decision_md5=C.md5_obj(dict(base=base, taken=taken, final=final, demfit_added=demfit.get('added'),
                                                         demfit_file=op_md5 if op else None)))
    if dry:
        st.rec['outputs'].update(dryrun=True)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_dfit', main)
