#!/usr/bin/env python3
"""lp_p3.py -- shared helpers for linog_auto Phases 3 and 4 (v0.4): the eight run files of the stack configuration.

What it holds: the run-file settings and pins (linog_run.cfg), the scripts the run files name and the modules
stripmapWrapper.py imports, the kit's gates, the reference geometry, the run files and their tags, a job pool that
runs a run file's lines as the kit's `parallel -j` does and records each line's exit code, time and peak memory,
the resource checks (disk, memory, load), the output listings behind --state, and the parsers of the kit gates'
verdict lines (anchored at line start, B55).

Every ISCE job runs from the frame folder (A30: the shelves and the .xml files carry relative image names) with
<ENV_PREFIX>/share/isce2/stripmapStack first on the PATH (F13) and OMP_NUM_THREADS, MKL_NUM_THREADS and
OPENBLAS_NUM_THREADS set together (linog_felix_parallelism). Standard library only; the phases that read shelves
do it inside lp_env.sh. The Phase 0 to 2 files are byte-identical to v0.3.

v0.9 (record 81): ISCE2's cfft1d_jpl plans the FFTs of ampcor (refine) and of crossmul and icu (igram) by timing them
(FFTW_MEASURE), so their results changed from run to run (I4, record 80; S25: 9 distinct ampcor results in 46 runs).
The pinned wisdom (lp_fftw.py, linog_fftw.cfg) reaches those two steps' jobs only, as WISDOM_FILE in their environment
(job_env); every other step's jobs run without it, as before. fftw_gate checks the file, the env's libfftw3f and the
modules at their pins, and the file's coverage of every problem in a fresh process, before any job; fftw_logs_gate reads
every job's log after the step: the wisdom line naming the file, the import's 1 after it, and no STOP line (a failed
import STOPs with exit status 0).
"""
import collections
import ctypes
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2

VERSION3 = 'linog_auto v0.9 (2026-10-04)'   # the release that last changed this module (v0.5 before)
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = ('lp_p3.py', 'lp_p2.py', 'lp_p1.py', 'lp_common.py')
STEPS = ('R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R07', 'R08')
RUN_KEYS = tuple('%s_%s' % (k, x) for k in STEPS for x in ('J', 'OMP', 'PEAK_KB')) + (
    'WRAPPER_MD5', 'INVERT_MD5', 'REFCOPY_MD5', 'TOPO_MD5', 'GEO2RDR_MD5', 'RESAMPLE_MD5', 'REFINE_MD5',
    'BASELINEGRID_MD5', 'CROSSMUL_MD5', 'FILTCOH_MD5', 'UNWRAP_MD5', 'KIT_G21_MD5', 'KIT_G7_MD5', 'KIT_REGCOMMON_MD5',
    'KIT_G8_MD5', 'KIT_G16_MD5', 'KIT_G9_MD5', 'KIT_G10_MD5', 'KIT_G11_MD5', 'KIT_DATECOH_MD5', 'G7_NCAND_RETRY',
    'G8_AZ_PX', 'G8_SHARE', 'G8_RG_PX', 'COH_MARK', 'HGT_FILL_ABS')
ISCE_PIN = {'stripmapWrapper.py': 'WRAPPER_MD5', 'invertMisreg.py': 'INVERT_MD5', 'referenceStackCopy.py': 'REFCOPY_MD5',
            'topo.py': 'TOPO_MD5', 'geo2rdr.py': 'GEO2RDR_MD5', 'resampleSlc.py': 'RESAMPLE_MD5',
            'refineSecondaryTiming.py': 'REFINE_MD5', 'baselineGrid.py': 'BASELINEGRID_MD5', 'crossmul.py': 'CROSSMUL_MD5',
            'FilterAndCoherence.py': 'FILTCOH_MD5', 'unwrap.py': 'UNWRAP_MD5'}
KIT_PIN = {'linog_frame_align_gate.py': 'KIT_G21_MD5', 'linog_coarse_reg_gate.py': 'KIT_G7_MD5',
           'linog_reg_common.py': 'KIT_REGCOMMON_MD5', 'linog_pair_misreg_census.py': 'KIT_G8_MD5',
           'linog_redatum_misreg_v2.py': 'KIT_G16_MD5', 'linog_misreg_gate.py': 'KIT_G9_MD5',
           'linog_fine_reg_gate.py': 'KIT_G10_MD5', 'linog_coherence_census.py': 'KIT_G11_MD5',
           'linog_date_coherence.py': 'KIT_DATECOH_MD5'}
# run file -> (settings key, the commands its lines name, the modules stripmapWrapper.py imports for it)
RUN = collections.OrderedDict((
    ('run_01_reference', ('R01', ('stripmapWrapper.py',), ('topo.py',))),
    ('run_02_focus_split', ('R02', ('stripmapWrapper.py',), ())),
    ('run_03_geo2rdr_coarseResamp', ('R03', ('stripmapWrapper.py',), ('geo2rdr.py', 'resampleSlc.py'))),
    ('run_04_refineSecondaryTiming', ('R04', ('stripmapWrapper.py',), ('refineSecondaryTiming.py',))),
    ('run_05_invertMisreg', ('R05', ('invertMisreg.py',), ())),
    ('run_06_fineResamp', ('R06', ('stripmapWrapper.py', 'referenceStackCopy.py'), ('resampleSlc.py',))),
    ('run_07_grid_baseline', ('R07', ('stripmapWrapper.py',), ('baselineGrid.py',))),
    ('run_08_igram', ('R08', ('stripmapWrapper.py',), ('crossmul.py', 'FilterAndCoherence.py', 'unwrap.py'))),
))
# each phase's own outputs, in pipeline order: a phase that must run finds none of its own, and lists later ones too
ORDER = (('3a', 'topo'), ('3b', 'coarse'), ('4a', 'refine'), ('4b', 'invert'), ('4c', 'datum'), ('4d', 'fine'),
         ('4e', 'bgrid'), ('4f', 'igram'))
OUTS = collections.OrderedDict((
    ('topo', ('merged/geom_reference', 'geom_reference')),
    ('coarse', ('offsets', 'coregSLC')),
    ('refine', ('refineSecondaryTiming/pairs',)),
    ('invert', ('refineSecondaryTiming/dates',)),
    ('datum', ('refineSecondaryTiming/dates_predatum_bak_*',)),
    ('fine', ('merged/SLC',)),
    ('bgrid', ('merged/baselines',)),
    ('igram', ('Igrams',)),
))
TAG = re.compile(r'config_[A-Za-z0-9]+(?:_[A-Za-z][A-Za-z0-9]*)*_(\d{8}(?:_\d{8})?)\s*$')


def run_cfg_file():
    return os.environ.get('LINOG_RUN_CFG') or os.path.join(HERE, 'linog_run.cfg')


def load_run():
    """linog_run.cfg as a dict (KEY=value lines; # comments)."""
    f = run_cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in RUN_KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['run_cfg_file'], d['run_cfg_md5'] = f, C.md5_file(f)
    return d


def tools(s, env, r, isce=(), kit=()):
    """{name: (path, md5 or None, pin)}: the stripmapStack scripts and modules by name, and the kit's gates."""
    out = {}
    for n in isce:
        p = os.path.join(P2.stack_dir(s), n)
        out[n] = (p, C.md5_file(p) if os.path.isfile(p) else None, r[ISCE_PIN[n]])
    for n in kit:
        p = os.path.join(env['KIT'], n)
        out[n] = (p, C.md5_file(p) if os.path.isfile(p) else None, r[KIT_PIN[n]])
    return out


def pins_gate(st, gid, tm, what):
    bad = ['%s md5 %s, pinned %s' % (p, got, pin) for p, got, pin in tm.values() if got != pin]
    st.gate(gid, '%s at their pins' % what, 'FAIL' if bad else 'PASS', '%d of %d' % (len(tm) - len(bad), len(tm)),
            ', '.join(sorted(tm)), '\n'.join(bad))
    return not bad


def job_env(s, r, key, mpl, wisdom=None):
    """The jobs' environment: this one (lp_env.sh's), stripmapStack first on the PATH, the thread caps of the step; v0.9:
    WISDOM_FILE = wisdom (the pinned file) for refine's and igram's jobs, and no WISDOM_FILE for any other."""
    e = dict(os.environ)
    e['PATH'] = P2.stack_dir(s) + os.pathsep + e.get('PATH', '/usr/bin:/bin')
    e.pop('WISDOM_FILE', None)
    if wisdom:
        e['WISDOM_FILE'] = wisdom
    omp = int(r['%s_OMP' % key])
    for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        if omp > 0:
            e[k] = str(omp)
        else:
            e.pop(k, None)
    os.makedirs(mpl, exist_ok=True)
    e['MPLCONFIGDIR'] = mpl
    return e


def which_gate(st, gid, s, jenv, cmds):
    """F13: every command the run file names resolves, on the jobs' PATH, to the pinned env's stripmapStack."""
    bad, got = [], []
    for c in cmds:
        w = shutil.which(c, path=jenv['PATH'])
        want = os.path.join(P2.stack_dir(s), c)
        got.append('%s -> %s' % (c, w))
        if not w or os.path.realpath(w) != os.path.realpath(want):
            bad.append('%s resolves to %s, want %s' % (c, w, want))
    st.gate(gid, 'the run files\' commands on the PATH', 'FAIL' if bad else 'PASS', '; '.join(got),
            'stripmapStack of ENV_PREFIX first (F13)', '\n'.join(bad))
    return not bad


def fftw_pins(which):
    """v0.9: the pinned FFTW wisdom, library and modules (linog_fftw.cfg) for a fingerprint, with the modules the phase's
    jobs load (which); dict(error=...) when the file cannot be read (the phase reads STALE then, and its gate says why)."""
    import lp_fftw as F
    try:
        p = F.pins(F.load())
    except (OSError, KeyError, ValueError) as e:
        return dict(error='%s: %s' % (type(e).__name__, e))
    p['modules'] = dict((m, p['modules'][m]) for m in which)
    return p


def fftw_gate(st, gid, s, which):
    """v0.9 (record 81), before any job of refine or igram: the wisdom file, the env's libfftw3f (the file
    ENV_PREFIX/lib/libfftw3f.so.3 resolves to) and the modules that plan through cfft1d_jpl (which) at linog_fftw.cfg's
    pins, each module loading that library (ldd); then, in a fresh process with that library, its version as pinned, the
    file imported (1) and every problem cfft1d_jpl can plan covered by it, and without the file none covered (so the check
    can fail). Returns (the wisdom's path, facts) when all hold; else (None, facts), after a FAIL gate."""
    import lp_fftw as F
    try:
        d = F.load()
    except (OSError, KeyError, ValueError) as e:
        st.gate(gid, 'FFTW wisdom (v0.9)', 'FAIL', 'linog_fftw.cfg: %s: %s' % (type(e).__name__, e), 'the pinned wisdom')
        return None, None
    fx = F.facts(d, s['ENV_PREFIX'], which)
    bad = F.problems_of(fx, d)
    w = wo = {}
    if not bad:
        w, wo = F.check(fx['lib'], fx['wisdom'], d), F.check(fx['lib'], None, d)
        for r_, what in ((w, 'with the file'), (wo, 'without it')):
            if 'error' in r_:
                bad.append('%s: %s' % (what, r_['error']))
        if not bad:
            if w.get('version') != d['FFTW_VERSION']:
                bad.append('libfftw3f reports %s, pinned %s' % (w.get('version'), d['FFTW_VERSION']))
            if w.get('imported') != 1 or w.get('covered') != w.get('total'):
                bad.append('with the file: import %s, %s of %s problems covered%s' % (
                    w.get('imported'), w.get('covered'), w.get('total'),
                    '; the first not covered: %s' % w['first_missing'] if w.get('first_missing') else ''))
            if wo.get('covered') != 0:
                bad.append('without the file %s of %s problems covered: the check cannot tell' % (wo.get('covered'), wo.get('total')))
    fx.update(pins=F.pins(d), with_file=w, without_file=wo)
    val = '%s %s; %s %s, %s; %s; with the file %s of %s problems, without it %s' % (
        os.path.basename(fx['wisdom']), (fx['wisdom_md5'] or 'absent')[:8], os.path.basename(fx['lib']),
        (fx['lib_md5'] or 'absent')[:8], w.get('version', 'not read'),
        ', '.join('%s %s' % (m, (v['md5'] or 'absent')[:8]) for m, v in sorted(fx['modules'].items())),
        w.get('covered', '-'), w.get('total', d['PROBLEMS']), wo.get('covered', '-'))
    st.gate(gid, 'FFTW wisdom (v0.9)', 'FAIL' if bad else 'PASS', val, 'linog_fftw.cfg\'s pins; %d of %d with the file, 0 without' % (
        d['PROBLEMS'], d['PROBLEMS']), '\n'.join(bad))
    return (None if bad else fx['wisdom']), fx


def fftw_logs_gate(st, gid, res, wis, per_job, who, md5=None):
    """v0.9, after the step: every job's log holds per_job wisdom lines (cfft1d_jpl's first call in each of who) naming wis,
    each followed by the import's 1, and no STOP line (a failed import STOPs with exit status 0, so rc 0 is not enough);
    and the file still has the md5 fftw_gate found before the jobs (it is read again: a file replaced during the step
    would import and pass). Returns (ok, dict(jobs, good, bad=[[line, tag, why]], md5_after))."""
    import lp_fftw as F
    bad = []
    for x in res:
        if x:
            why = F.judge_log(x['log'], wis, per_job)
            if why:
                bad.append([x['seq'], x['tag'], why])
    n = len([x for x in res if x])
    after = F.md5f(wis) if os.path.isfile(wis) else None
    moved = md5 is not None and after != md5
    st.gate(gid, 'the jobs imported the wisdom', 'FAIL' if bad or moved else 'PASS', '%d of %d job logs: %d wisdom line(s) (%s) '
            'naming the pinned file, import 1, no STOP; the file %s' % (n - len(bad), n, per_job, who, 'changed during the step '
                                                                          '(md5 %s, %s before)' % (after, md5) if moved else 'unchanged'),
            'every job (v0.9)', '\n'.join('line %d (%s): %s' % tuple(b) for b in bad[:8]))
    return not bad and not moved, dict(jobs=n, good=n - len(bad), per_job=per_job, wisdom=wis, md5_after=after, bad=bad[:20])


def geometry(recdir):
    """(geometry, problems) from recon/reference.json: the reference, its width and lines (G17's), the looks, and the
    multilooked grid (Rule 4: int(width / rlks) x int(lines / alks))."""
    rj = os.path.join(recdir, 'recon', 'reference.json')
    if not os.path.exists(rj):
        return None, ['no recon/reference.json']
    J = json.load(open(rj))
    g17, geo = J.get('g17') or {}, J.get('geometry') or {}
    try:
        w, ln = int(g17['modes'][0]), int(g17['modes'][1])
        rl, al = int(geo['rlks']), int(geo['alks'])
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return None, ['recon/reference.json lacks g17 or geometry (%s)' % e]
    g = dict(ref=J.get('reference'), width=w, lines=ln, rlks=rl, alks=al, gw=w // rl, gl=ln // al, slc_bytes=8 * w * ln,
             json_md5=C.md5_file(rj))
    bad = [] if (g['gw'], g['gl']) == (int(geo.get('width', -1)), int(geo.get('length', -1))) else \
        ['reference.json geometry %s x %s, Rule 4 gives %d x %d' % (geo.get('width'), geo.get('length'), g['gw'], g['gl'])]
    return g, bad


def run_lines(W, name):
    """The non-empty lines of run_files/<name> (a line's leading space kept: bash runs it as written); None if absent."""
    p = os.path.join(W, 'run_files', name)
    if not os.path.isfile(p):
        return None
    return [ln.rstrip('\n') for ln in open(p) if ln.strip()]


def tag_of(line):
    m = TAG.search(line.strip())
    if m:
        return m.group(1)
    w = line.split()
    return os.path.basename(w[0]).replace('.py', '') if w else 'line'


def cfg_of(line):
    m = re.search(r'-c\s+(\S+)', line)
    return m.group(1) if m else None


def cfg_kv(p):
    """key : value lines of a stackStripMap config, line by line (a key in two functions: the last one read)."""
    out = {}
    try:
        for ln in open(p):
            m = re.match(r'^[ \t]*(\w+)[ \t]*:[ \t]*(.*?)[ \t]*$', ln.rstrip('\n'))
            if m:
                out[m.group(1)] = m.group(2)
    except (OSError, TypeError):
        pass
    return out


def runfile_md5s(W, names):
    """md5 of each run file and of every config its lines name (what the phase runs)."""
    out = {}
    for n in names:
        p = os.path.join(W, 'run_files', n)
        out[n] = C.md5_file(p) if os.path.isfile(p) else None
        for ln in run_lines(W, n) or []:
            c = cfg_of(ln)
            if c:
                out[os.path.basename(c)] = C.md5_file(c) if os.path.isfile(c) else None
    return out


def _rc(status):
    if hasattr(os, 'waitstatus_to_exitcode'):
        return os.waitstatus_to_exitcode(status)
    return -os.WTERMSIG(status) if os.WIFSIGNALED(status) else os.WEXITSTATUS(status)


STOPSIGS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
PR_SET_PDEATHSIG = 1
_LIBC = []


class Deferred(object):
    """SIGINT, SIGTERM and SIGHUP held for a step that must not be cut in half (a job's start and its registration,
    the datum's --apply); a signal that arrives meanwhile is delivered when the step ends. v0.5 (as lp_rwin.Held):
    blocking them in this thread alone does not hold them once a library has started threads (numpy's OpenBLAS, when
    ISCE objects are unpickled), since another thread can take a signal sent to the process and its Python handler
    then runs here; so the Python handlers are swapped for a recorder as well, restored at the end, and the first
    recorded signal raised again. A signal ignored on entry stays ignored; when the step raises, its exception goes on.
    The jobs still start with the signals blocked (inherited over fork, unblocked by _job_init)."""

    def __enter__(self):
        self.got, self.oldh = [], {}
        for s in STOPSIGS:
            h = signal.getsignal(s)
            if h is not signal.SIG_IGN:
                self.oldh[s] = signal.SIG_DFL if h is None else h
                signal.signal(s, self._note)
        self.old = signal.pthread_sigmask(signal.SIG_BLOCK, STOPSIGS)
        return self

    def _note(self, signum, frame):
        self.got.append(signum)

    def __exit__(self, et, ev, tb):
        # unblocked first, with the recorder still in place, then the handlers back, then one recorded signal raised
        # again: two different signals held in the kernel would otherwise raise twice, the second inside the stop path
        signal.pthread_sigmask(signal.SIG_SETMASK, self.old)
        for s, h in self.oldh.items():
            signal.signal(s, h)
        if et is None and self.got:
            signal.raise_signal(self.got[0])
        return False


def _ignore_stops():
    """SIGINT, SIGTERM and SIGHUP ignored from here on (a run_pool that is stopping). A second stop signal can arrive
    between these calls (a second Ctrl-C) and its handler raise; the calls are then made again, so the kills that
    follow are never skipped. The exception already on its way goes on after the finally block."""
    while True:
        try:
            for sig in STOPSIGS:
                signal.signal(sig, signal.SIG_IGN)
            return
        except BaseException:  # noqa: BLE001  (KeyboardInterrupt or Stopped of a second signal: already stopping)
            continue


def _libc():
    if not _LIBC:
        try:
            _LIBC.append(ctypes.CDLL(None, use_errno=True))
        except OSError:
            _LIBC.append(None)
    return _LIBC[0]


def _job_init():
    """In each job, before exec: the stop signals unblocked (the pool holds them while it starts the job), and SIGTERM
    when the phase itself dies (PR_SET_PDEATHSIG; a SIGKILL of the phase, the OOM killer), so no line goes on writing
    into the frame after the phase that started it is gone."""
    signal.pthread_sigmask(signal.SIG_SETMASK, [])
    lib = _libc()
    if lib is not None:
        lib.prctl(PR_SET_PDEATHSIG, int(signal.SIGTERM), 0, 0, 0)


def _stop_jobs(running):
    """The stop path of run_pool: the stop signals ignored, every running line's process group sent SIGTERM, 20 s for
    them to end, then SIGKILL; each job is taken out of running once reaped, so a call cut short by a second signal
    can simply be made again (v0.5)."""
    _ignore_stops()
    for pid in list(running):
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            pass
    t_end = time.time() + 20
    while running and time.time() < t_end:
        try:
            pid, status, ru = os.wait4(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if pid == 0:
            time.sleep(0.2)
            continue
        if pid in running:
            i, p, fh, t0, lg = running.pop(pid)
            p.returncode = _rc(status)
            fh.close()
    for pid in list(running):
        try:
            os.killpg(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except OSError:
            pass
        running.pop(pid)[2].close()


def run_pool(lines, tags, cwd, env, j, logdir):
    """Run the lines with bash, at most j at once, each in its own session with its own log in logdir; the kit's
    `parallel -j` with a record per line. Returns [dict(seq, tag, rc, seconds, maxrss_kb, log, log_bytes)] in line
    order. A stop (Stopped, KeyboardInterrupt) ends every running line's process group before it goes on."""
    os.makedirs(logdir, exist_ok=True)
    todo, running, res = list(range(len(lines))), {}, [None] * len(lines)
    try:
        while todo or running:
            while todo and len(running) < max(1, j):
                i = todo.pop(0)
                lg = os.path.join(logdir, '%03d_%s.log' % (i + 1, tags[i]))
                fh = open(lg, 'w')
                fh.write('# %s  %s\n' % (C.utc(), lines[i].strip()))
                fh.flush()
                _libc()   # loaded here, not in the child
                with Deferred():   # a stop between the start and the registration would leave the job unkilled
                    p = subprocess.Popen(['bash', '-c', lines[i]], cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                         stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=_job_init)
                    running[p.pid] = (i, p, fh, time.time(), lg)
            pid, status, ru = os.wait4(-1, 0)
            if pid not in running:
                continue
            i, p, fh, t0, lg = running.pop(pid)
            p.returncode = rc = _rc(status)
            fh.close()
            res[i] = dict(seq=i + 1, tag=tags[i], rc=rc, seconds=round(time.time() - t0, 1), maxrss_kb=ru.ru_maxrss,
                          log=lg, log_bytes=os.path.getsize(lg))
    finally:
        while running:
            try:
                _stop_jobs(running)
            except BaseException:  # noqa: BLE001  (a second stop signal while the jobs are being stopped: again)
                continue
    with open(os.path.join(logdir, 'joblog.tsv'), 'w') as fh:
        fh.write('seq\ttag\trc\tseconds\tmaxrss_kb\tlog_bytes\n')
        for x in res:
            if x:
                fh.write('%d\t%s\t%d\t%.1f\t%d\t%d\n' % (x['seq'], x['tag'], x['rc'], x['seconds'], x['maxrss_kb'], x['log_bytes']))
    return res


def pool_summary(res):
    ok = [x for x in res if x and x['rc'] == 0]
    bad = [x for x in res if x and x['rc'] != 0]
    return dict(lines=len(res), ok=len(ok), failed=[[x['seq'], x['tag'], x['rc'], x['log']] for x in bad],
                max_seconds=max([x['seconds'] for x in res if x] or [0]),
                max_rss_kb=max([x['maxrss_kb'] for x in res if x] or [0]),
                sum_seconds=round(sum(x['seconds'] for x in res if x), 1))


def tail(p, n=6):
    try:
        return '\n'.join(open(p, errors='replace').read().strip().splitlines()[-n:])
    except OSError:
        return ''


def mem_available_kb():
    try:
        for ln in open('/proc/meminfo'):
            if ln.startswith('MemAvailable:'):
                return int(ln.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def load1():
    try:
        return float(open('/proc/loadavg').read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def jobs_for(j, nlines, peak_kb, avail_kb):
    """Jobs at once: the step's J, no more than its lines, no more than MemAvailable / the measured peak per job."""
    n = min(int(j), max(1, nlines))
    return n if avail_kb is None else min(n, int(avail_kb // max(1, int(peak_kb))))


def run_step(st, gid, W, s, r, name, lines, logroot, mpl_root, what, wisdom=None):
    """One run file: the resource line, the pool, the gate on every line's exit code. Returns (ok, summary, results).
    wisdom (v0.9): the pinned FFTW wisdom file, put into the jobs' environment as WISDOM_FILE (refine and igram)."""
    key = RUN[name][0]
    avail = mem_available_kb()
    j = jobs_for(r['%s_J' % key], len(lines), r['%s_PEAK_KB' % key], avail)
    omp = int(r['%s_OMP' % key])
    if j < 1:
        st.gate(gid, name, 'FAIL', 'MemAvailable %s kB holds no job of %s kB' % (avail, r['%s_PEAK_KB' % key]),
                'at least one job')
        return False, None, None
    env = job_env(s, r, key, os.path.join(mpl_root, 'mplconfig'), wisdom)
    ld = os.path.join(logroot, name)
    print('   %s: %d lines, %d at once (J %s), OMP %s; load %s, MemAvailable %s kB, nproc %s; logs %s%s' % (
        name, len(lines), j, r['%s_J' % key], omp if omp else 'uncapped', load1(), avail, os.cpu_count(), ld,
        '; WISDOM_FILE %s' % wisdom if wisdom else ''))
    sys.stdout.flush()
    t0, ld0 = time.time(), load1()
    res = run_pool(lines, [tag_of(x) for x in lines], W, env, j, ld)
    summ = pool_summary(res)
    summ.update(name=name, j=j, j_cfg=int(r['%s_J' % key]), omp=omp, wall_seconds=round(time.time() - t0, 1),
                load_before=ld0, load_after=load1(), mem_available_kb=avail, nproc=os.cpu_count(), logdir=ld)
    note = '\n'.join('line %d (%s) rc %d; log %s\n%s' % (q, t, rc, lg, tail(lg, 4)) for q, t, rc, lg in summ['failed'][:5])
    st.gate(gid, name, 'FAIL' if summ['failed'] else 'PASS', '%d of %d lines rc 0 in %.1f s at %d at once; slowest line '
            '%.1f s, largest peak %d kB' % (summ['ok'], len(lines), summ['wall_seconds'], j, summ['max_seconds'],
                                             summ['max_rss_kb']), 'every line rc 0 (%s)' % what, note)
    if j < int(r['%s_J' % key]) and j < len(lines):
        st.gate(gid + 'm', 'jobs held by memory', 'WARN', '%d at once, not %s: MemAvailable %s kB / %s kB per job' % (
            j, r['%s_J' % key], avail, r['%s_PEAK_KB' % key]), 'J of linog_run.cfg')
    return not summ['failed'], summ, res


def gib(b):
    return b / 2.0 ** 30


def disk_gate(st, gid, W, need_bytes, margin_gib):
    free = P1.free_gib(W)
    ok = free >= gib(need_bytes) + margin_gib
    st.gate(gid, 'disk', 'PASS' if ok else 'FAIL', '%.1f GiB free, this phase writes about %.1f GiB' % (free, gib(need_bytes)),
            'free >= writes + %s GiB (disk_gib_margin)' % margin_gib)
    return ok


def listing(W, rels):
    """[[relative path, size, mtime_ns]] of every file under the given entries of W (globs allowed; links not followed)."""
    out = []
    for rel in rels:
        for p in sorted(glob.glob(os.path.join(W, rel))):
            if os.path.isfile(p) and not os.path.islink(p):
                st = os.stat(p)
                out.append([os.path.relpath(p, W), st.st_size, st.st_mtime_ns])
            elif os.path.isdir(p) and not os.path.islink(p):
                for d, ds, fs in os.walk(p):
                    ds.sort()
                    for f in sorted(fs):
                        q = os.path.join(d, f)
                        if os.path.isfile(q) and not os.path.islink(q):
                            st = os.stat(q)
                            out.append([os.path.relpath(q, W), st.st_size, st.st_mtime_ns])
    return out


def listing_changed(W, rels, recorded, names_only=False):
    """What differs between the files under rels now and a recorded listing: a recorded file gone, or its size or mtime
    changed. A file added beside them (MintPy's prep_isce writes .rsc files into geom_reference/ and Igrams/<pair>/, a
    report goes into Igrams/reports/) changes nothing the phase wrote, so it is not counted (as stack2 does it)."""
    now = {x[0]: x[1:] for x in listing(W, rels)}
    rec = {x[0]: x[1:] for x in recorded or []}
    out = ['gone: %s' % n for n in sorted(set(rec) - set(now))]
    if not names_only:
        out += ['changed: %s' % n for n in sorted(set(now) & set(rec)) if now[n] != rec[n]]
    return out


SLC_READ = ('data.dat', 'data.dir', 'data.bak', 'data.db', 'data')


def slc_identity(W, dates):
    """md5 of [date, [[name, size, mtime_ns], ...]] over the files of SLC/<date>/ the ISCE steps read: <date>.slc, its
    .xml and .vrt, and the shelve's files (dbm.dumb on felix: data.dat, .dir, .bak). MintPy's data.rsc beside them is
    not one of them (G24 reads it at Phase 5)."""
    out = []
    for d in dates:
        sd, fs = os.path.join(W, 'SLC', d), []
        for n in (d + '.slc', d + '.slc.xml', d + '.slc.vrt') + SLC_READ:
            q = os.path.join(sd, n)
            if os.path.isfile(q):
                st = os.stat(q)
                fs.append([n, st.st_size, st.st_mtime_ns])
        out.append([d, fs])
    return C.md5_obj(out)


def fine_cfg_refs(W):
    """The dates the configs/config_fineResamp_* files name as their reference (the kit's need_ref reads the same)."""
    out = set()
    for c in glob.glob(os.path.join(W, 'configs', 'config_fineResamp_*')):
        for ln in open(c, errors='replace'):
            m = re.match(r'^\s*reference\s*:\s*.*/(\d{8})\s*$', ln)
            if m:
                out.add(m.group(1))
    return out


def digest(lst):
    return C.md5_obj(lst)


def present(W, rels):
    return [rel for rel in rels if glob.glob(os.path.join(W, rel))]


def in_the_way(W, phase):
    """(this phase's outputs present, later phases' outputs present)."""
    names = list(OUTS)
    i = names.index(phase)
    own = present(W, OUTS[phase])
    later = [x for n in names[i + 1:] for x in present(W, OUTS[n])]
    return own, later


def way_gate(st, gid, W, phase, dry):
    """DECISION when this phase's outputs are in the frame without a PASS record to go with them."""
    own, later = in_the_way(W, phase)
    if dry:
        st.gate(gid, 'nothing in the way', 'INFO', 'dry run: in the frame now: %s' % (', '.join(own + later) or 'none of them'),
                ', '.join(OUTS[phase]) + ' absent')
        return True
    if own:
        st.gate(gid, 'nothing in the way', 'DECISION', 'in the frame already: %s%s' % (
            ', '.join(own), ('; and later phases\': %s' % ', '.join(later)) if later else ''), ', '.join(OUTS[phase]) + ' absent',
            'outputs of an earlier run of this phase with no PASS record; move them (and the later phases\' outputs '
            'listed) into %s/_archive/ and run again' % W)
        return False
    st.gate(gid, 'nothing in the way', 'PASS', '%s absent' % ', '.join(OUTS[phase]), 'all absent')
    return True


def xml_dims(p):
    """(width, length) from an ISCE .xml (property width / length, or number_of_samples / number_of_lines)."""
    try:
        root = ET.parse(p).getroot()
    except (OSError, ET.ParseError):
        return None, None
    v = {}
    for prop in root.iter('property'):
        n = (prop.get('name') or '').lower()
        val = prop.find('value')
        if val is not None and val.text and n in ('width', 'length', 'number_of_samples', 'number_of_lines'):
            try:
                v.setdefault(n, int(float(val.text)))
            except ValueError:
                pass
    return v.get('width', v.get('number_of_samples')), v.get('length', v.get('number_of_lines'))


def xml_file_name(p):
    try:
        root = ET.parse(p).getroot()
    except (OSError, ET.ParseError):
        return None
    for prop in root.iter('property'):
        if (prop.get('name') or '').lower() == 'file_name':
            val = prop.find('value')
            return val.text.strip() if val is not None and val.text else None
    return None


def expect(W, specs):
    """specs: [(relative path, size or None)]; the problems (missing, or another size)."""
    bad = []
    for rel, size in specs:
        p = os.path.join(W, rel)
        if not os.path.isfile(p):
            bad.append('missing %s' % rel)
        elif size is not None and os.path.getsize(p) != size:
            bad.append('%s is %d B, want %d' % (rel, os.path.getsize(p), size))
    return bad


def kit_run(env, script, args, cwd, log, extra=None, session=False):
    """python3 -B <KIT>/script args from cwd (-B: no __pycache__ in KIT); (rc, output text). The tool writes straight
    into the log (a first line with the command, a last line with rc and time), so the log exists even when the phase
    is killed. LINOG_REG_NCAND reaches the tool only when the caller sets it (G7's and G10's retry): an operator's
    exported value would change the "default" survey unrecorded. session: the tool in a session of its own, out of
    reach of the terminal's and the run's process-group signals (the datum's --apply)."""
    e = {k: v for k, v in os.environ.items() if k != 'LINOG_REG_NCAND'}
    e.update(extra or {})
    cmd = ['python3', '-B', os.path.join(env['KIT'], script)] + list(args)
    t0 = time.time()
    with open(log, 'wb') as fh:
        fh.write(('# %s  %s  (cwd %s%s)\n' % (C.utc(), ' '.join(cmd), cwd, ''.join(
            ' %s=%s' % kv for kv in sorted((extra or {}).items())))).encode('utf-8', 'replace'))
        fh.flush()
        start = fh.tell()
        p = subprocess.run(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                           start_new_session=session)
    with open(log, 'rb') as fh:
        fh.seek(start)
        out = fh.read().decode('utf-8', 'replace')
    with open(log, 'a') as fh:
        fh.write('# rc %d  %.1f s\n' % (p.returncode, time.time() - t0))
    return p.returncode, out


def reg_verdict(txt):
    """G7/G10 (linog_reg_common.py): dict(verdict, nbad, n, quorum, windows, dates={date: (cells, verdict)})."""
    r = dict(verdict=None, nbad=None, n=None, quorum=None, windows=None, dates={})
    for ln in txt.splitlines():
        m = re.match(r'^(PASS|FAIL)\s+(\d+) of (\d+) date\(s\) failed\s*$', ln)
        if m:
            r.update(verdict=m.group(1), nbad=int(m.group(2)), n=int(m.group(3)))
        m = re.match(r'^\*\*\* FAIL: only (\d+) viable window\(s\), quorum is (\d+)', ln) or \
            re.match(r'^\*\*\* FAIL: (\d+) window\(s\) qualified to vote, quorum is (\d+)', ln)
        if m:
            r.update(verdict='QUORUM', windows=int(m.group(1)), quorum=int(m.group(2)))
        m = re.match(r'^  (\d{8})  (.*?)\s+(\d+)\s+(\d+)\s+(\S+)\s+(FAIL|ok)\s*$', ln)
        if m:
            cells = re.findall(r'([+-]\d+\.\d)([+-]\d+\.\d)(!?)', m.group(2))
            r['dates'][m.group(1)] = (' '.join('%s%s%s' % c for c in cells) or m.group(2).strip(), m.group(6))
    return r


def g21_verdict(txt):
    r = dict(verdict=None, nbad=None, n=None, flagged={}, median=None)
    for ln in txt.splitlines():
        m = re.match(r'^(PASS|FAIL)\s+(\d+) of (\d+) beyond', ln)
        if m:
            r.update(verdict=m.group(1), nbad=int(m.group(2)), n=int(m.group(3)))
        m = re.match(r'^G21 .*frame median \|az\| ([\d.]+) lines', ln)
        if m:
            r['median'] = float(m.group(1))
        m = re.match(r'^(\d{8})\s.*\*\*\*\s*(.*)$', ln)
        if m:
            r['flagged'][m.group(1)] = ln.strip()
    return r


def network_components(dates, pairs):
    adj = collections.defaultdict(set)
    for a, b in pairs:
        adj[a].add(b)
        adj[b].add(a)
    seen, comps = set(), []
    for d in dates:
        if d in seen:
            continue
        stack, grp = [d], []
        seen.add(d)
        while stack:
            x = stack.pop()
            grp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(sorted(grp))
    return comps


def shelf_consts(p):
    """(az, rg) constant terms of a misreg shelve (azpoly and rgpoly), as the kit reads them; needs ISCE on the path."""
    import shelve
    db = shelve.open(p, 'r')
    try:
        out = []
        for k in ('azpoly', 'rgpoly'):
            poly = db[k]
            c = None
            f = getattr(poly, 'getCoeffs', None)
            if callable(f):
                c = f()
            if c is None:
                c = getattr(poly, '_coeffs', None)
            out.append(float(c[0][0]))
        return tuple(out)
    finally:
        db.close()


def shelf_md5s(W, rel):
    """{relative path: md5} of the shelve files (misreg.dat/.dir/.bak, data.*) under W/rel."""
    out = {}
    for n, size, mt in listing(W, [rel]):
        out[n] = C.md5_file(os.path.join(W, n))
    return out


def prior3(st, gid, recdir, index, phase):
    """The phase before: PASS on record (the whole record returned), or a FAIL gate and None."""
    r = P1.record(recdir, index, phase)
    if not r or r.get('verdict') != 'PASS':
        st.gate(gid, '%s PASS on record' % phase, 'FAIL', 'P%s %s %s' % (index, phase, (r or {}).get('verdict') or 'has no record'))
        return None
    return r


def keep_previous(recdir, phase, index):
    """The phase's previous record, copied into status/history/P<index>_<phase>.<its start>_<its pid>.json before a new
    run replaces it (a re-run that stops in the way would otherwise erase what the earlier run found). Returns it."""
    f = os.path.join(recdir, 'status', 'P%s_%s.json' % (index, phase))
    if not os.path.isfile(f):
        return None
    try:
        old = json.load(open(f))
    except ValueError:
        old = {}
    tag = '%s_%s' % (re.sub(r'[^0-9TZ]', '', str(old.get('start') or C.utc())), old.get('pid') or os.getpid())
    hd = os.path.join(recdir, 'status', 'history')
    os.makedirs(hd, exist_ok=True)
    dst = os.path.join(hd, 'P%s_%s.%s.json' % (index, phase, tag))
    if not os.path.exists(dst):
        shutil.copy2(f, dst)
    return old


def begin(recdir, phase, index, path, frame, fp, logic, inputs, dry):
    keep_previous(recdir, phase, index)
    st = P2.LiveStatus(recdir, phase, index, path, frame)   # F25: the record after every gate
    P1.begin(st)
    st.rec['version'] = VERSION3
    st.rec.update(fingerprint=fp, logic=logic, tools=C.tool_md5s(*(('lp_%s.py' % phase,) + TOOLS)), inputs=inputs)
    st.write()
    return st


def header(phase, index, path, frame, W, dry, extra=''):
    print('%s  Phase %s %s  p%s f%s  %s' % (VERSION3, index, phase, path, frame, C.utc()))
    print('   frame folder %s%s%s' % (W, extra, '   (DRY RUN: a plan only; the frame is only read)' if dry else ''))
    sys.stdout.flush()


def plan_only(st, lines_by_name, note):
    """The dry run's end: what the phase would run, a PASS record marked planned."""
    for n, ls in lines_by_name.items():
        print('   would run %s: %s lines' % (n, len(ls) if ls is not None else 'no run file'))
    st.rec['outputs'] = dict(planned=True, dryrun=True, note=note)
    return st.finish('plan only (dry run)')
