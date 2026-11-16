#!/usr/bin/env python3
"""lp_bandlimit.py -- linog_auto Phase 1bs (v0.13; ascending record 4.3, R6): the FBS dates of an FBS+FBD frame band-limited
to FBD's 14 MHz in place, at native width, by the course kit's own tool, after rwin and before verify.

The FBS dates stay in SLC/<date>/ (R6-a, 4.1); each is filtered there by the kit's linog_fbs_bandlimit.py, which imports
its filter from linog_fbs_downsample.py, both at their pins in linog_mixed.cfg, one call a date, from the frame folder:
    python3 -B <KIT>/linog_fbs_bandlimit.py SLC --keep-fraction <K> --taper-width <T> --dates <date>
(-B: the tool imports its filter module from the kit folder, which would otherwise get a __pycache__.) The tool copies
<date>.slc to <date>.slc.prefilter when the copy is absent, reads the copy, filters every line along range in blocks of
1,024 lines and writes <date>.slc in place, dimensions unchanged; it touches no .xml, .vrt or shelve. Named an FBD date it
filters that too, and with an empty --dates every folder under SLC/ (4.3's desk test), so the phase names one 8-digit FBS
date a call and checks the FBD dates after. On an FBS-only frame (FBS stays at 28 MHz, as on F3320 and F3310) and on an
FBD-only frame (R6-d, 18.5: no FBS date) the phase records N/A, so verify's G1c.1 reads one rule on every branch.
A date never goes through the tool twice once it is done: status/P1bs_bandlimit.progress (JSON lines) holds a started
line before each call (the date, the unpacked file's md5, the kit pins, keep_fraction, taper_width) and a done line after
the date's checks (the .slc's size, mtime and md5, the .prefilter's size and mtime). The md5 the started line holds is the
date's unpacked identity: no phase between unpack and this one writes an .slc (rwin writes shelves only).

Gates
  G1bl.1  unpack and rwin PASS on record, rwin made from that unpack record; each date's mode (recon's IMG-HV witness)
          the one its leader's sampling rate gives (rwin's fs_mhz): 32 MHz FBS, 16 MHz FBD                     FAIL
  G1bl.2  the environment: the pinned env at its prefix (12.3, item 4) and numpy (ERROR); the kit's two files at their
          pins (FAIL)
  G1bl.3  nothing in the way: no .prefilter beside an FBD date, nor beside an FBS date this phase has no line for; a done
          date's files as its done line records them, made with today's pins and settings (a done date unpacked again,
          its .prefilter gone and its .slc the unpacked file, is band-limited anew: the review's P2-03); no FBS file to
          write with more than one hard link (P2-09); on a one-mode frame, no .prefilter or progress line left (P2-05)
                                                                                                              DECISION
  G1bl.4  (before any call) a date stopped mid-way is resumed only from the unpacked file: its .prefilter's md5 or its
          .slc's the started line's, whatever pins and settings it started under (4.3; the review's P2-01: a new started
          line records today's); a full-size .prefilter beside an unfiltered .slc that is not the unpacked file, or
          neither file the unpacked one                                                                       DECISION
  G1bl.9  free disk for the copies still to make (8 B x width x lines a date), plus the path table's disk_gib_margin  FAIL
  per FBS date, after its call (the first date that fails stops the phase; later dates are not called):
  G1bl.10 the call: the tool's rc 0, its "written in place" and "--- BANDLIMIT DONE" lines                          FAIL
  G1bl.4  identity: <date>.slc.prefilter's md5 = the started line's (the unpacked file)                            FAIL
  G1bl.5  recompute: 8 lines spread over the image, each filtered here from the .prefilter (ifft(fft(line) x H), H the
          pinned filter module's at today's settings, cast to complex64), against the written lines: relative RMS at
          most 1e-6 (a second filter on top reads 7.4e-2, none 1.0; 4.3, desk D.1), and at least one of them lit (P2-11) FAIL
  G1bl.6  spectrum: the share of power at |f| > 7 MHz (0.21875 cycles a sample) over 64 lines spread over the image:
          at most 0.01 in <date>.slc (one pass on a flat band reads 0.0066), at least 0.40 in the .prefilter       FAIL
  G1bl.7  occupancy (the kit's G5 v2, linog_spectral95.py, ported): the 95 % range-spectrum occupancy of the .prefilter
          (PRE) and the .slc (POST) over 256 lines from line 9000, the middle 256 on a frame without them, and the
          median over the frame's FBD dates; NOT_NARROWED (POST > PRE - 0.10), RATIO_OFF (POST / FBD median not inside
          0.35 to 0.75)                                                                                            FAIL
  after the FBS dates:
  G1bl.8  every FBD date untouched: its .slc's size and mtime as at the phase's start, no .prefilter beside it; its md5
          (read once) and its power share at |f| > 7 MHz (0.4375 cycles a sample at 16 MHz) recorded               FAIL
  G1bl.11 (R7, 11.7) progress lines of a date outside the plan (excluded by R7's D2 loop or a person): kept, listed   INFO
--state (standard library, the driver's python3): the fingerprint holds the inputs only (unpack's and rwin's fingerprints,
unpack's dates_md5, each date's fs_mhz, linog_mixed.cfg's four values of this phase, this phase's tools and LOGIC); a
CURRENT record reads STALE when an FBS .slc or .prefilter, or an FBD .slc, no longer has the size and mtime it records.
A STALE run then meets the rules above: done dates whose files match are skipped, nothing called.
--dryrun DIR: G1bl.1, G1bl.2, G1bl.3 and G1bl.9 on the records and the frame's files, and the plan; nothing called;
writes only DIR/status/P1bs_bandlimit.json.
Writes: SLC/<date>/<date>.slc (in place, by the tool) and <date>.slc.prefilter of each FBS date; logs/bandlimit/; the progress
file; _archive/bandlimit_<UTC>/SLC/<date>/ (a partial .prefilter left by a stopped call); its status record. Nothing deleted.
Runs inside lp_env.sh (numpy); --state is standard library.
Self-test only (they act only under a path table other than the package's own, lp_common.selftest_hooks; the review's
P2-08): LINOG_MOCK_BL_TWICE=<date> filters the written .slc a second time before the checks; LINOG_MOCK_BL_UNDO=<date>
puts the .prefilter back as the .slc before the checks; LINOG_MOCK_BL_FBD=<date> passes that FBD date to the tool after the
FBS dates; LINOG_MOCK_BL_KILL=<date>:copy or <date>:after makes that date's copy here instead of the tool, and the phase
kills itself (SIGKILL) half way through the copy, or after it.
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

import lp_common as C
import lp_p1 as P1

PHASE, IDX, LOGIC = 'bandlimit', '1bs', 1
VERSION = C.VERSION
TOOLS = ('lp_bandlimit.py', 'lp_p1.py', 'lp_common.py')
KIT_TOOL, KIT_FILTER = 'linog_fbs_bandlimit.py', 'linog_fbs_downsample.py'
SETTING_KEYS = ('KEEP_FRACTION', 'TAPER_WIDTH', 'KIT_FBS_BANDLIMIT_MD5', 'KIT_FBS_DOWNSAMPLE_MD5')
FS_MODE = {'FBS': 32.0, 'FBD': 16.0}   # MHz, the leader's range sampling rate by mode
FS_TOL_MHZ = 0.01
N_RECOMP, RMS_MAX = 8, 1e-6            # G1bl.5
N_SPEC, F_EDGE_FBS, F_EDGE_FBD = 64, 0.21875, 0.4375   # G1bl.6 and G1bl.8: 7 MHz at 32 and at 16 MHz
HI_SLC_MAX, HI_PRE_MIN = 0.01, 0.40
OCC_LINES, OCC_LINE0, OCC_FRAC = 256, 9000, 0.95       # G1bl.7, as linog_spectral95.py
NARROW_MIN, RATIO_LO, RATIO_HI = 0.10, 0.35, 0.75
DATE_RE = re.compile(r'^\d{8}$')


class LiveStatus(C.Status):
    """The record written again after every gate, as rwin's and verify's (the review's P2-22): a RUNNING record left by a
    SIGKILL shows the gates taken so far."""

    def gate(self, *a, **k):
        C.Status.gate(self, *a, **k)
        self.write()


def prog_file(W):
    return os.path.join(W, 'status', 'P1bs_bandlimit.progress')


def prog_lines(W):
    """The progress file's lines, in order (unreadable lines left out)."""
    out, f = [], prog_file(W)
    if os.path.exists(f):
        for ln in open(f):
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get('event') in ('started', 'done') and r.get('date'):
                out.append(r)
    return out


def last_of(prog, d):
    """(the date's last started line, the done line after it), each None when absent; a done line with no started
    line before it counts as done."""
    started = done = None
    for r in prog:
        if r['date'] != d:
            continue
        if r['event'] == 'started':
            started, done = r, None
        else:
            done = r
    return started, done


def append(W, r):
    os.makedirs(os.path.join(W, 'status'), exist_ok=True)
    with open(prog_file(W), 'a') as fh:
        fh.write(json.dumps(r, sort_keys=True) + '\n')
        fh.flush()
        os.fsync(fh.fileno())


def paths(W, d):
    slc = os.path.join(W, 'SLC', d, d + '.slc')
    return slc, slc + '.prefilter'


def spread(n_lines, n):
    """n line numbers spread over the image, first and last included (all lines on a shorter image)."""
    if n_lines <= n:
        return list(range(n_lines))
    return sorted(set(int(round(i * (n_lines - 1) / float(n - 1))) for i in range(n)))


def kit_md5s(env):
    return dict((n, C.md5_file(os.path.join(env['KIT'], n)) if os.path.isfile(os.path.join(env['KIT'], n)) else None)
                for n in (KIT_TOOL, KIT_FILTER))


def settings(mx):
    return dict((k, mx[k]) for k in SETTING_KEYS)


def inputs_of(r_unp, r_rw):
    uo, ro = (r_unp or {}).get('outputs') or {}, (r_rw or {}).get('outputs') or {}
    return dict(unpack_fingerprint=(r_unp or {}).get('fingerprint'), dates_md5=uo.get('dates_md5'),
                rwin_fingerprint=(r_rw or {}).get('fingerprint'),
                fs=[[x.get('date'), x.get('fs_mhz')] for x in (ro.get('dates') or [])])


def missing_files(W, r):
    """What a CURRENT record no longer finds as it recorded: FBS .slc and .prefilter, FBD .slc (size and mtime)."""
    o = (r or {}).get('outputs') or {}
    bad = []
    for x in o.get('fbs') or []:
        slc, pre = paths(W, x['date'])
        if P1.file_id(slc) != (x.get('slc') or {}).get('id') or P1.file_id(pre) != (x.get('prefilter') or {}).get('id'):
            bad.append(x['date'])
    for x in o.get('fbd') or []:
        if P1.file_id(paths(W, x['date'])[0]) != x.get('id'):
            bad.append(x['date'])
    return bad


# ---- the readings (numpy, inside the env) ----------------------------------------------------------------------------

def load_filter(env):
    """The pinned filter module, imported from the kit folder without writing its bytecode."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('linog_fbs_downsample_pinned', os.path.join(env['KIT'], KIT_FILTER))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.create_hanning_bandpass


def read_lines(path, width, rows):
    import numpy as np
    out = np.empty((len(rows), width), dtype=np.complex64)
    with open(path, 'rb') as fh:
        for i, r in enumerate(rows):
            fh.seek(r * width * 8)
            b = fh.read(width * 8)
            if len(b) < width * 8:
                raise ValueError('%s: line %d short (%d of %d B)' % (path, r, len(b), width * 8))
            out[i] = np.frombuffer(b, dtype=np.complex64)
    return out


def recompute_rms(pre, slc, width, lines, H):
    """G1bl.5: (relative RMS of the written lines against the filter applied here to the .prefilter, lines with power)."""
    import numpy as np
    rows = spread(lines, N_RECOMP)
    a, b = read_lines(pre, width, rows), read_lines(slc, width, rows)
    want = np.fft.ifft(np.fft.fft(a, axis=1) * H, axis=1).astype(np.complex64)
    num = float(np.sum(np.abs(b.astype(np.complex128) - want.astype(np.complex128)) ** 2))
    den = float(np.sum(np.abs(want.astype(np.complex128)) ** 2))
    lit = int(np.sum(np.any(a != 0, axis=1)))
    if den == 0.0:
        return (0.0 if num == 0.0 else float('inf')), lit, len(rows)
    return (num / den) ** 0.5, lit, len(rows)


def hi_share(path, width, lines, edge):
    """G1bl.6, G1bl.8: the share of the mean range power spectrum at |f| > edge cycles a sample over 64 lines spread
    over the image; None when the lines hold no power."""
    import numpy as np
    a = read_lines(path, width, spread(lines, N_SPEC))
    P = (np.abs(np.fft.fft(a, axis=1)) ** 2).mean(axis=0)
    tot = float(P.sum())
    if tot == 0.0:
        return None
    return float(P[np.abs(np.fft.fftfreq(width)) > edge].sum()) / tot


def occ95(path, width, lines):
    """G1bl.7: linog_spectral95.py's occ95 (the 95 % occupancy of the line-averaged, centred range spectrum, as 2k / W),
    over 256 lines from line 9000, or the middle 256 lines on a frame without them; None when unreadable or dark."""
    import numpy as np
    n = min(OCC_LINES, lines)
    line0 = OCC_LINE0 if lines >= OCC_LINE0 + OCC_LINES else (lines - n) // 2
    if not (path and os.path.exists(path) and width and n):
        return None
    a = np.fromfile(path, dtype=np.complex64, count=width * n, offset=line0 * width * 8)
    if a.size < width * n:
        return None
    P = (np.abs(np.fft.fft(a.reshape(n, width), axis=1)) ** 2).mean(axis=0)
    tot = P.sum()
    if not tot > 0:
        return None
    P = np.fft.fftshift(P) / tot
    c, k, cum = width // 2, 0, 0.0
    while cum < OCC_FRAC and k < c:
        k += 1
        cum = P[c - k:c + k + 1].sum()
    return (2.0 * k) / width


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 1bs: the band-limit of the FBS dates (v0.13)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env = P1.load_env()
    mx = P1.load_mixed()
    r_unp, r_rw = P1.record(recdir, '1b', 'unpack'), P1.record(recdir, '1br', 'rwin')
    ins = inputs_of(r_unp, r_rw)
    fp = C.md5_obj(dict(logic=LOGIC, tools=C.tool_md5s(*TOOLS), inputs=ins, settings=settings(mx)))
    if a.state:
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, lambda r: missing_files(W, r)))
        return 0

    try:
        prev = P1.record(recdir, IDX, PHASE) or {}
    except ValueError:
        prev = {}
    st = LiveStatus(recdir, PHASE, IDX, path, frame)
    P1.begin(st)
    st.rec['version'] = VERSION
    st.rec.update(fingerprint=fp, logic=LOGIC, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(ins, kit=env['KIT'], mixed_cfg=mx['mixed_cfg_file'], mixed_cfg_md5=mx['mixed_cfg_md5'],
                              settings=settings(mx)))
    st.write()
    print('%s  Phase 1bs bandlimit (the FBS dates to 14 MHz)  p%s f%s  %s' % (VERSION, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: the frame is only read)' if a.dryrun else ''))

    # G1bl.1: the records, and each date's mode against its leader's sampling rate
    uo, ro = (r_unp or {}).get('outputs') or {}, (r_rw or {}).get('outputs') or {}
    dates = uo.get('dates') or []
    why = []
    if not r_unp or r_unp.get('verdict') != 'PASS' or not dates:
        why.append('unpack %s' % ((r_unp or {}).get('verdict') or 'has no record'))
    if not r_rw or r_rw.get('verdict') != 'PASS':
        why.append('rwin %s' % ((r_rw or {}).get('verdict') or 'has no record'))
    elif r_unp and ((r_rw.get('inputs') or {}).get('unpack_fingerprint') != r_unp.get('fingerprint') or
                    (r_rw.get('inputs') or {}).get('dates_md5') != uo.get('dates_md5')):
        why.append('rwin ran on another unpack record (run rwin again)')
    if why:
        st.gate('G1bl.1', 'unpack and rwin PASS on record', 'FAIL', '; '.join(why))
        return st.finish()
    R, _ = P1.recon_json(recdir)
    fs = dict((x.get('date'), x.get('fs_mhz')) for x in (ro.get('dates') or []))
    if not fs and ro.get('read'):   # rwin's dry record keeps its readings in outputs.rows (the review's P2-04)
        fs = dict((x.get('date'), x.get('fs_mhz')) for x in (ro.get('rows') or []) if x.get('fs_mhz') is not None)
    plan_only = a.dryrun and not fs   # a dry run before the frame's own rwin read its leaders
    bad1, nfs = [], {'FBS': 0, 'FBD': 0}
    for d in dates:
        m, f = d.get('mode'), fs.get(d['date'])
        if m not in FS_MODE:
            bad1.append('%s: mode %s' % (d['date'], m))
            continue
        nfs[m] += 1
        if plan_only:
            continue
        if f is None or abs(float(f) - FS_MODE[m]) > FS_TOL_MHZ:
            bad1.append('%s: %s by recon\'s IMG-HV witness, its leader samples at %s MHz (%s wants %.0f)' % (
                d['date'], m, f, m, FS_MODE[m]))
    st.gate('G1bl.1', 'unpack and rwin PASS on record; modes = sampling rates', 'FAIL' if bad1 else 'PASS',
            '%d dates (FBS %d, FBD %d), branch %s%s' % (len(dates), nfs['FBS'], nfs['FBD'], R['branch'],
                                                         '; the sampling rates not read yet (rwin is a plan)' if plan_only else
                                                         '; every mode the one its leader\'s sampling rate gives'),
            'FBS 32 MHz, FBD 16 MHz (rwin\'s fs_mhz)', '\n'.join(bad1))
    if bad1:
        return st.finish()
    fbs = sorted((d for d in dates if d['mode'] == 'FBS'), key=lambda d: d['date'])
    fbd = sorted((d for d in dates if d['mode'] == 'FBD'), key=lambda d: d['date'])
    if not fbs or not fbd:
        prog0 = prog_lines(W)
        kept = set(d['date'] for d in dates)
        left = sorted(d['date'] for d in dates if os.path.lexists(paths(W, d['date'])[1]))
        lined = sorted(set(r['date'] for r in prog0) & kept)
        if left or lined:   # the review's P2-05: a frame once mixed keeps band-limited files under a one-mode record
            st.gate('G1bl.3', 'nothing in the way', 'DECISION', 'a %s frame with band-limit traces: %d .prefilter, %d dates in '
                    'the progress file' % (R['branch'], len(left), len(lined)), 'none on a one-mode frame',
                    '%s\nthe frame was band-limited as FBS+FBD and is %s now (dates excluded?): its FBS files may be at 14 MHz; '
                    'whether to unpack them again is a person\'s choice' % (
                        '\n'.join(['.prefilter beside %s' % d for d in left] + ['progress lines for %s' % d for d in lined]),
                        R['branch']))
            return st.finish()
        why_na = ('no FBD date: FBS stays at 28 MHz, as on F3320 and F3310' if fbs else
                  'no FBS date to band-limit (FBD-only, R6-d)')
        st.gate('G1bl.0', 'the branch', 'N/A', '%s, %d dates: %s' % (R['branch'], len(dates), why_na))
        st.rec['outputs'] = dict(branch=R['branch'], na=why_na, fbs=[], fbd=[], dryrun=bool(a.dryrun))
        return st.finish('N/A: %s' % why_na)

    # G1bl.2: the environment and the kit's two files
    ok, ev, note = False, 'not checked', ''
    try:
        import isce  # noqa: F401  (the env's own python, as Phase 1's other env gates)
        import numpy
        ok, ev, note = P1.env_check(env)
        ev = '%s, numpy %s, python %s %s' % (ev, numpy.__version__, sys.executable, sys.version.split()[0])
    except Exception as e:  # noqa: BLE001
        ok, note = False, 'import isce or numpy failed: %s: %s' % (type(e).__name__, e)
    km = kit_md5s(env)
    pins = {KIT_TOOL: mx['KIT_FBS_BANDLIMIT_MD5'], KIT_FILTER: mx['KIT_FBS_DOWNSAMPLE_MD5']}
    badp = ['%s md5 %s, pinned %s (linog_mixed.cfg)' % (os.path.join(env['KIT'], n), km[n], pins[n]) for n in pins if km[n] != pins[n]]
    st.gate('G1bl.2', 'environment and the kit\'s two files', 'ERROR' if not ok else 'FAIL' if badp else 'PASS',
            '%s; %s and %s %s' % (ev, KIT_TOOL, KIT_FILTER, 'at their pins' if not badp else 'NOT at their pins'),
            '%s at ENV_PREFIX, numpy; the pins of linog_mixed.cfg' % env['CONDA_ENV'], '\n'.join(([note] if note else []) + badp))
    if not ok or badp:
        return st.finish()

    # G1bl.3: the plan, from the progress file and the frame's files
    prog = prog_lines(W)
    today = settings(mx)
    plan, way, noresume = [], [], []
    for d in fbs:
        slc, pre = paths(W, d['date'])
        started, done = last_of(prog, d['date'])
        p = dict(date=d['date'], width=int(d['width']), lines=int(d['lines']), slc=slc, pre=pre, started=started, done=done)
        if done and not os.path.lexists(pre) and os.path.isfile(slc) and C.md5_file(slc) == done.get('md5_unpacked'):
            # the review's P2-03: the date was unpacked again after its done line (its files archived by a person): anew
            p['action'], p['redo'] = 'todo', True
        elif done:
            if done.get('settings') != today:
                way.append('%s: done with other pins or settings (%s; today %s): archiving and redoing it is a person\'s '
                           'choice (move SLC/%s/ whole into _archive/ and run again: unpack makes the date again and this '
                           'phase band-limits it anew)' % (d['date'], done.get('settings'), today, d['date']))
                p['action'] = 'blocked'
            elif P1.file_id(slc) != (done.get('slc') or {}).get('id') or P1.file_id(pre) != (done.get('prefilter') or {}).get('id'):
                way.append('%s: its .slc or .prefilter is not as its done line records it (%s, %s; now %s, %s): something '
                           'rewrote the date' % (d['date'], (done.get('slc') or {}).get('id'), (done.get('prefilter') or {}).get('id'),
                                                 P1.file_id(slc), P1.file_id(pre)))
                p['action'] = 'blocked'
            else:
                p['action'] = 'skip'
        elif started:
            # 4.3: resumed from the unpacked file whatever pins and settings it started under (the tool filters from the
            # unpacked copy, so they leave nothing behind); a new started line records today's (the review's P2-01)
            p['restart'] = started.get('settings') != today
            if os.path.isfile(pre) and C.md5_file(pre) == started.get('md5'):
                p['action'] = 'resume'
            elif os.path.isfile(slc) and C.md5_file(slc) == started.get('md5'):
                if os.path.lexists(pre) and not (os.path.isfile(pre) and os.path.getsize(pre) < os.path.getsize(slc)):
                    # the review's P2-06: a full-size .prefilter that is not the unpacked file beside an unfiltered .slc
                    noresume.append('%s: stopped mid-way; its .slc is the unpacked file, but a full-size .prefilter beside it '
                                    'is not (md5 %s)' % (d['date'], started.get('md5')))
                    p['action'] = 'blocked'
                else:
                    p['action'], p['partial'] = 'resume', os.path.lexists(pre)
            else:
                noresume.append('%s: stopped mid-way, and neither its .prefilter nor its .slc is the unpacked file (md5 %s)' % (
                    d['date'], started.get('md5')))
                p['action'] = 'blocked'
        elif os.path.lexists(pre):
            way.append('%s: a .prefilter beside an FBS date this phase has no line for' % d['date'])
            p['action'] = 'blocked'
        else:
            p['action'] = 'todo'
        if p['action'] in ('todo', 'resume'):   # the review's P2-09: the tool writes the .slc in place
            for f in (slc, pre):
                if os.path.isfile(f) and os.stat(f).st_nlink > 1:
                    way.append('%s: %s has %d hard links: the tool writes it in place, which would change every linked copy '
                               '(a tree made with cp -al?)' % (d['date'], os.path.basename(f), os.stat(f).st_nlink))
                    p['action'] = 'blocked'
                    break
        plan.append(p)
    for d in fbd:
        if os.path.lexists(paths(W, d['date'])[1]):
            way.append('%s: a .prefilter beside an FBD date' % d['date'])
    outside = sorted(set(r['date'] for r in prog) - set(d['date'] for d in fbs))
    if outside:   # v0.13, R7 (11.7): the lines of a date R7 or a person excluded, kept and listed, not acted on
        st.gate('G1bl.11', 'progress lines outside the plan', 'INFO', '%d date(s) in the progress file are not this frame\'s FBS '
                'dates now: %s' % (len(outside), ', '.join(outside)), 'kept, not acted on (11.7)',
                'dates excluded after they were band-limited (R7\'s D2 loop or recon/exclude.txt); their files moved with them')
    todo = [p for p in plan if p['action'] in ('todo', 'resume')]
    st.gate('G1bl.3', 'nothing in the way', 'DECISION' if way else 'PASS',
            '%d FBS dates to do (%d resumed, %d anew after a new unpack), %d done earlier, %d in the way; %d FBD dates' % (
                len(todo), sum(p['action'] == 'resume' for p in plan), sum(bool(p.get('redo')) for p in plan),
                sum(p['action'] == 'skip' for p in plan), len(way), len(fbd)), '0 in the way',
            '\n'.join(way) + ('\nnothing was changed; move the files named into %s/ by hand, then re-run'
                              % os.path.join(W, '_archive') if way else ''))
    if noresume:
        st.gate('G1bl.4', 'identity (the unpacked file)', 'DECISION', '%d date(s) stopped mid-way cannot be resumed' % len(noresume),
                'the .prefilter or the .slc is the unpacked file', '\n'.join(noresume) + '\nnothing was changed; which copy to keep '
                'is a person\'s choice: move the date\'s files into %s/, unpack it again, then re-run' % os.path.join(W, '_archive'))
    margin = float(cfg.get('disk_gib_margin', 10))
    need = sum(8.0 * p['width'] * p['lines'] for p in todo) / 2.0 ** 30 + margin
    free = P1.free_gib(W)
    st.gate('G1bl.9', 'free disk', 'PASS' if free >= need else 'FAIL', '%.1f GiB free, %.1f GiB needed' % (free, need),
            '>= the copies still to make + disk_gib_margin %.0f GiB' % margin)
    if any(g['verdict'] in ('FAIL', 'DECISION', 'ERROR') for g in st.rec['gates']):
        return st.finish()
    if a.dryrun:
        print('   would band-limit %d FBS dates (%s) in SLC/<date>/ with %s at keep fraction %s, taper %s; %d done earlier; '
              'then check %d FBD dates untouched' % (len(todo), ' '.join(p['date'] for p in todo) or '-', KIT_TOOL,
                                                     mx['KEEP_FRACTION'], mx['TAPER_WIDTH'],
                                                     sum(p['action'] == 'skip' for p in plan), len(fbd)))
        st.rec['outputs'] = dict(branch=R['branch'], planned=[p['date'] for p in todo], dryrun=True,
                                 skipped=[p['date'] for p in plan if p['action'] == 'skip'], fbd=[], fbs=[])
        return st.finish('plan only (dry run)')

    # the FBD dates as at the phase's start (G1bl.8), and their median occupancy when an FBS date is to do (G1bl.7)
    fbd0 = dict((d['date'], P1.file_id(paths(W, d['date'])[0])) for d in fbd)
    filt = load_filter(env)
    fbd_occ = {}
    if todo:
        for d in fbd:
            fbd_occ[d['date']] = occ95(paths(W, d['date'])[0], int(d['width']), int(d['lines']))
    import numpy as np
    occs = [v for v in fbd_occ.values() if v]
    fbd_med = float(np.median(occs)) if occs else None
    tool = os.path.join(env['KIT'], KIT_TOOL)
    hooks = dict((k, C.selftest_hook(k)) for k in ('LINOG_MOCK_BL_KILL', 'LINOG_MOCK_BL_TWICE', 'LINOG_MOCK_BL_UNDO',
                                                   'LINOG_MOCK_BL_FBD'))
    o = st.rec['outputs'] = dict(branch=R['branch'], fbs=[], fbd=[], fbd_median95=fbd_med, archived=[])
    fbs_dates = set(x['date'] for x in fbs)
    counts = dict(done=0, resumed=0, skipped=0)
    for p in plan:
        if p['action'] != 'skip':
            continue
        dn = p['done']
        o['fbs'].append(dict(date=p['date'], action='skipped', md5_unpacked=dn.get('md5_unpacked'), slc=dn.get('slc'),
                             prefilter=dn.get('prefilter'), readings=dn.get('readings'), done=dn.get('utc')))
        counts['skipped'] += 1
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        d, slc, pre, w, ln = p['date'], p['slc'], p['pre'], p['width'], p['lines']
        if not DATE_RE.match(d) or d not in fbs_dates:   # an empty --dates would filter every folder under SLC/
            st.gate('G1bl.10', 'the call', 'FAIL', '%s: not one 8-digit FBS date' % d)
            return st.finish()
        t = time.time()
        if p['action'] == 'todo':
            size = os.path.getsize(slc) if os.path.isfile(slc) else None
            if size != w * ln * 8:
                st.gate('G1bl.4', 'identity (the unpacked file)', 'FAIL', '%s: %s.slc is %s B, unpack recorded %d x %d x 8 = %d' % (
                    d, d, size, w, ln, w * ln * 8), 'the size unpack recorded')
                return st.finish()
            m0 = C.md5_file(slc)
            append(W, dict(event='started', date=d, md5=m0, size=size, settings=today, utc=C.utc(), pid=os.getpid(),
                           **({'redo': True} if p.get('redo') else {})))
        else:
            m0 = p['started']['md5']
            if p.get('restart'):   # started under other pins or settings: today's are the call's (the review's P2-01)
                append(W, dict(event='started', date=d, md5=m0, size=p['started'].get('size'), settings=today, utc=C.utc(),
                               pid=os.getpid(), resumed_from=p['started'].get('settings')))
            if p.get('partial'):   # a copy cut short: aside, so the tool copies the unpacked file again
                bdir = os.path.join(W, '_archive', 'bandlimit_%s' % time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()), 'SLC', d)
                os.makedirs(bdir, exist_ok=True)
                dst = os.path.join(bdir, os.path.basename(pre))
                if os.path.lexists(dst):
                    st.gate('G1bl.3', 'nothing in the way', 'DECISION', '%s: %s exists' % (d, dst))
                    return st.finish()
                os.rename(pre, dst)
                o['archived'].append(os.path.relpath(dst, W))
                print('   %s: the partial %s moved into %s' % (d, os.path.basename(pre), os.path.relpath(bdir, W)))
        kill = hooks['LINOG_MOCK_BL_KILL'] or ''
        if kill.split(':')[0] == d:   # self-test: a stop during or after the tool's copy (the record stays RUNNING)
            if kill.endswith(':copy'):
                with open(slc, 'rb') as src, open(pre, 'wb') as dst:
                    dst.write(src.read((w * ln * 8) // 2))
            else:
                shutil.copy2(slc, pre)
            os.kill(os.getpid(), signal.SIGKILL)
        lg = P1.new_log(os.path.join(W, 'logs', 'bandlimit', d + '.log'))
        cmd = [sys.executable, '-B', tool, 'SLC', '--keep-fraction', mx['KEEP_FRACTION'], '--taper-width', mx['TAPER_WIDTH'],
               '--dates', d]
        with open(lg, 'w') as fh:
            fh.write('# %s (cwd %s)\n' % (' '.join(cmd), W))
            fh.flush()
            rc = subprocess.call(cmd, cwd=W, stdout=fh, stderr=subprocess.STDOUT)
        txt = open(lg, errors='replace').read()
        if hooks['LINOG_MOCK_BL_TWICE'] == d:   # self-test: a second filter on top (G1bl.5 sees it)
            Hm = filt(w, keep_fraction=float(mx['KEEP_FRACTION']), taper_width=float(mx['TAPER_WIDTH']))
            arr = np.fromfile(slc, dtype=np.complex64).reshape(ln, w)
            np.fft.ifft(np.fft.fft(arr, axis=1) * Hm, axis=1).astype(np.complex64).tofile(slc)
        if hooks['LINOG_MOCK_BL_UNDO'] == d:    # self-test: the unfiltered file put back (G1bl.5 and G1bl.6)
            shutil.copyfile(pre, slc)
        fails = {}
        if rc != 0 or 'written in place' not in txt or '--- BANDLIMIT DONE' not in txt:
            tail = [x for x in txt.strip().splitlines() if x.strip()][-4:]
            fails['G1bl.10'] = ('%s: the tool rc %d%s' % (d, rc, '' if 'written in place' in txt else ', no "written in place" line'),
                                'log %s, last lines:\n%s' % (lg, '\n'.join('  ' + x for x in tail)))
        m_pre = C.md5_file(pre) if os.path.isfile(pre) else None
        if m_pre != m0:
            fails['G1bl.4'] = ('%s: %s.slc.prefilter md5 %s, the started line\'s (the unpacked file) %s' % (d, d, m_pre, m0), '')
        rd = {}
        if 'G1bl.10' not in fails and 'G1bl.4' not in fails:
            H = filt(w, keep_fraction=float(mx['KEEP_FRACTION']), taper_width=float(mx['TAPER_WIDTH']))
            rms, lit, nr = recompute_rms(pre, slc, w, ln, H)
            hs, hp = hi_share(slc, w, ln, F_EDGE_FBS), hi_share(pre, w, ln, F_EDGE_FBS)
            op, oq = occ95(pre, w, ln), occ95(slc, w, ln)
            ratio = oq / fbd_med if oq and fbd_med else None
            flags = []
            if oq is None:
                flags.append('UNREADABLE')
            if op is None:
                flags.append('NO_PREFILTER')
            if op and oq and oq > op - NARROW_MIN:
                flags.append('NOT_NARROWED')
            if fbd_med is None:
                flags.append('NO_FBD_MEDIAN')
            elif oq and not (RATIO_LO * fbd_med < oq < RATIO_HI * fbd_med):
                flags.append('RATIO_OFF')
            rd = dict(rms=rms, lines_read=nr, lines_lit=lit, hi_slc=hs, hi_pre=hp, pre95=op, post95=oq, ratio=ratio, flags=flags)
            if not rms <= RMS_MAX or lit == 0:
                fails['G1bl.5'] = ('%s: relative RMS %.3g over %d lines (%d with power)%s' % (
                    d, rms, nr, lit, '' if lit else ': no line read holds power'), '')
            if hs is None or hp is None or hs > HI_SLC_MAX or hp < HI_PRE_MIN:
                fails['G1bl.6'] = ('%s: power above 7 MHz %s in the .slc, %s in the .prefilter' % (
                    d, None if hs is None else round(hs, 4), None if hp is None else round(hp, 4)), '')
            if flags:
                fails['G1bl.7'] = ('%s: PRE95 %s, POST95 %s, POST / FBD median %s: %s' % (
                    d, None if op is None else round(op, 4), None if oq is None else round(oq, 4),
                    None if ratio is None else round(ratio, 4), ','.join(flags)), '')
        print('   [%2d/%d] %s  %s  rc %d  %.0f s  rms %s  >7MHz %s / %s  PRE95 %s POST95 %s ratio %s%s' % (
            i, len(todo), d, 'resumed' if p['action'] == 'resume' else 'filtered', rc, time.time() - t,
            '%.2g' % rd['rms'] if rd else '-', '%.4f' % rd['hi_slc'] if rd.get('hi_slc') is not None else '-',
            '%.4f' % rd['hi_pre'] if rd.get('hi_pre') is not None else '-',
            '%.4f' % rd['pre95'] if rd.get('pre95') else '-', '%.4f' % rd['post95'] if rd.get('post95') else '-',
            '%.4f' % rd['ratio'] if rd.get('ratio') else '-', ('  FAIL ' + ' '.join(sorted(fails))) if fails else ''))
        sys.stdout.flush()
        if fails:
            for gid, name in (('G1bl.10', 'the call'), ('G1bl.4', 'identity (the unpacked file)'), ('G1bl.5', 'recompute'),
                              ('G1bl.6', 'spectrum above 7 MHz'), ('G1bl.7', 'occupancy (G5 v2)')):
                if gid in fails:
                    st.gate(gid, name, 'FAIL', fails[gid][0], '', fails[gid][1] + ('\n' if fails[gid][1] else '') +
                            'SLC/%s is left as it is (the .prefilter is the unpacked file when G1bl.4 passed)' % d)
            o['fbs'].append(dict(date=d, action='failed', md5_unpacked=m0, readings=rd, log=lg))
            return st.finish()
        m_slc = C.md5_file(slc)
        done = dict(event='done', date=d, md5_unpacked=m0, settings=today, utc=C.utc(),
                    slc=dict(id=P1.file_id(slc), md5=m_slc), prefilter=dict(id=P1.file_id(pre)), readings=rd)
        append(W, done)
        o['fbs'].append(dict(date=d, action='resumed' if p['action'] == 'resume' else 'done', md5_unpacked=m0, slc=done['slc'],
                             prefilter=done['prefilter'], readings=rd, log=lg, done=done['utc']))
        counts['resumed' if p['action'] == 'resume' else 'done'] += 1
    now = [x for x in o['fbs'] if x['action'] in ('done', 'resumed')]
    if todo:
        worst = max(x['readings']['rms'] for x in now)
        st.gate('G1bl.10', 'the call', 'PASS', '%d of %d calls rc 0, %.0f s' % (len(now), len(todo), time.time() - t0),
                'rc 0, "written in place", "--- BANDLIMIT DONE"')
        st.gate('G1bl.4', 'identity (the unpacked file)', 'PASS', '%d of %d .prefilter = the unpacked file' % (len(now), len(todo)),
                'md5 = the started line\'s')
        st.gate('G1bl.5', 'recompute', 'PASS', '%d of %d dates; largest relative RMS %.2g' % (len(now), len(todo), worst),
                '<= %g over %d lines' % (RMS_MAX, N_RECOMP))
        st.gate('G1bl.6', 'spectrum above 7 MHz', 'PASS', '%d of %d; .slc %.4f to %.4f, .prefilter %.4f to %.4f' % (
            len(now), len(todo), min(x['readings']['hi_slc'] for x in now), max(x['readings']['hi_slc'] for x in now),
            min(x['readings']['hi_pre'] for x in now), max(x['readings']['hi_pre'] for x in now)),
            '.slc <= %.2f, .prefilter >= %.2f' % (HI_SLC_MAX, HI_PRE_MIN))
        st.gate('G1bl.7', 'occupancy (G5 v2)', 'PASS', '%d of %d; FBD median %.4f, PRE95 %.4f to %.4f, POST95 %.4f to %.4f, ratio '
                '%.4f to %.4f' % (len(now), len(todo), fbd_med, min(x['readings']['pre95'] for x in now),
                                  max(x['readings']['pre95'] for x in now), min(x['readings']['post95'] for x in now),
                                  max(x['readings']['post95'] for x in now), min(x['readings']['ratio'] for x in now),
                                  max(x['readings']['ratio'] for x in now)),
                'POST <= PRE - %.2f; %.2f < POST / FBD median < %.2f' % (NARROW_MIN, RATIO_LO, RATIO_HI))
    else:
        st.gate('G1bl.10', 'the call', 'N/A', 'every FBS date done earlier (%d): nothing called' % counts['skipped'])

    # self-test: an FBD date passed to the tool (G1bl.8 must see it)
    hk = hooks['LINOG_MOCK_BL_FBD']
    if hk and hk in fbd0:
        with open(P1.new_log(os.path.join(W, 'logs', 'bandlimit', hk + '.log')), 'w') as fh:
            subprocess.call([sys.executable, '-B', tool, 'SLC', '--keep-fraction', mx['KEEP_FRACTION'], '--taper-width',
                             mx['TAPER_WIDTH'], '--dates', hk], cwd=W, stdout=fh, stderr=subprocess.STDOUT)
    # G1bl.8: the FBD dates untouched; md5 read once (an earlier record's, when its size and mtime still hold)
    before = dict((x.get('date'), x) for x in ((prev.get('outputs') or {}).get('fbd') or []))
    bad8 = []
    for d in fbd:
        slc, pre = paths(W, d['date'])
        fid = P1.file_id(slc)
        if fid != fbd0[d['date']] or os.path.lexists(pre):
            bad8.append('%s: %s.slc %s at the start, %s now; .prefilter %s' % (d['date'], d['date'], fbd0[d['date']], fid,
                                                                             'beside it' if os.path.lexists(pre) else 'absent'))
        b = before.get(d['date']) or {}
        m = b.get('md5') if b.get('id') == fid and b.get('md5') else (C.md5_file(slc) if os.path.isfile(slc) else None)
        hs = b.get('hi') if b.get('id') == fid and 'hi' in b else (hi_share(slc, int(d['width']), int(d['lines']), F_EDGE_FBD)
                                                                    if os.path.isfile(slc) else None)
        o['fbd'].append(dict(date=d['date'], id=fid, md5=m, hi=hs, occ95=fbd_occ.get(d['date'], b.get('occ95'))))
    st.gate('G1bl.8', 'the FBD dates untouched', 'FAIL' if bad8 else 'PASS',
            '%d of %d as at the start, no .prefilter; power above 7 MHz %s' % (
                len(fbd) - len(bad8), len(fbd), ', '.join('%s %s' % (x['date'], 'n/a' if x['hi'] is None else '%.4f' % x['hi'])
                                                         for x in o['fbd'])),
            'size and mtime as at the start; no .prefilter', '\n'.join(bad8))
    o.update(counts, settings=today, kit=dict((n, km[n]) for n in km))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_bandlimit', main)
