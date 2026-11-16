#!/usr/bin/env python3
"""lp_p1.py -- shared helpers for linog_auto Phase 1 (v0.2): the environment pins, the records of the
phases before, versioned logs, the output check behind --state, and the crash path (a phase that raises
ends its record ERROR with the traceback tail, instead of leaving it RUNNING).

Standard library only. Phase 0's files (lp_common.py, lp_recon.py, lp_stage.py, linog_paths.cfg) are
byte-identical to v0.1, so a frame staged by v0.1 keeps its Phase 0 records CURRENT under v0.2.
v0.13 (ascending record 4.2, 12.3 item 4, 18.5): env_check(), the pinned env by its name and its prefix, for Phase 1's four
env gates (unpack, rwin, bandlimit, verify); load_mixed(), linog_mixed.cfg (the FBS+FBD and FBD-only settings); file_id().
"""
import json
import os
import shutil
import signal
import sys
import traceback

import lp_common as C

VERSION1 = C.VERSION
CURRENT = {}   # the Status of the phase in progress, for crash()
HERE = os.path.dirname(os.path.abspath(__file__))
ENV_KEYS = ('CONDA_SH', 'CONDA_ENV', 'UNPACKER', 'UNPACKER_MD5', 'KIT', 'KIT_UNPACK_VERIFY_MD5',
            'KIT_SHELVE_GATE_MD5', 'GATE_GRID_M', 'GATE_R0REF_M', 'BW_FBS_MHZ', 'BW_FBD_MHZ')
# v0.13: linog_mixed.cfg (4.2, 4.3, 18.5): bandlimit's two settings and the kit's two pins, the FBD-only frame's range looks
MIXED_KEYS = ('KEEP_FRACTION', 'TAPER_WIDTH', 'KIT_FBS_BANDLIMIT_MD5', 'KIT_FBS_DOWNSAMPLE_MD5', 'STACK_RLKS_FBD')


def mixed_cfg_file():
    return os.environ.get('LINOG_MIXED_CFG') or os.path.join(HERE, 'linog_mixed.cfg')


def load_mixed():
    """v0.13: linog_mixed.cfg as a dict (KEY=value lines; # comments), with its file and md5."""
    f = mixed_cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in MIXED_KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['mixed_cfg_file'], d['mixed_cfg_md5'] = f, C.md5_file(f)
    return d


def env_check(env):
    """v0.13 (12.3, item 4): (ok, value, note) for a Phase 1 env gate. The pinned env by its name (CONDA_DEFAULT_ENV is
    linog_env.cfg's CONDA_ENV) and by its prefix (CONDA_PREFIX is linog_stack.cfg's ENV_PREFIX, as Phase 2's G2a.2 reads it),
    so another account's env of the same name, or another conda's, stops at the gate. The caller imports isce first."""
    import lp_p2 as P2
    name = os.environ.get('CONDA_DEFAULT_ENV')
    cp = os.environ.get('CONDA_PREFIX') or ''
    val = 'env %s at %s' % (name, cp or '(no CONDA_PREFIX)')
    try:
        want = P2.load_stack()['ENV_PREFIX']
    except (OSError, KeyError) as e:
        return False, val, 'cannot read ENV_PREFIX: %s' % e
    ok_name = name == env['CONDA_ENV']
    ok_pre = bool(cp) and os.path.realpath(cp) == os.path.realpath(want)
    note = '' if ok_name and ok_pre else ('run this phase through lp_env.sh' if not ok_name else
                                          'CONDA_PREFIX %s is not ENV_PREFIX %s (linog_stack.cfg)' % (cp or '(unset)', want))
    return ok_name and ok_pre, val, note


def file_id(p):
    """[size, mtime_ns] of a file, or None when it is absent."""
    try:
        s = os.stat(p)
    except OSError:
        return None
    return [s.st_size, s.st_mtime_ns]


def env_cfg_file():
    return os.environ.get('LINOG_ENV_CFG') or os.path.join(HERE, 'linog_env.cfg')


def load_env():
    """linog_env.cfg as a dict (KEY=value lines; # comments)."""
    f = env_cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in ENV_KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    d['env_cfg_file'], d['env_cfg_md5'] = f, C.md5_file(f)
    return d


def record(recdir, index, phase):
    f = os.path.join(recdir, 'status', 'P%s_%s.json' % (index, phase))
    return json.load(open(f)) if os.path.exists(f) else None


def prior(st, gid, recdir, need):
    """Gate: every (index, phase) in need reads PASS. Returns the records, or None after a FAIL gate."""
    recs, bad = {}, []
    for index, phase in need:
        r = record(recdir, index, phase)
        recs[phase] = r
        if not r or r.get('verdict') != 'PASS':
            bad.append('P%s %s %s' % (index, phase, r.get('verdict') if r else 'has no record'))
    names = ' and '.join(p for _, p in need)
    if bad:
        st.gate(gid, names + ' PASS on record', 'FAIL', '; '.join(bad))
        return None
    st.gate(gid, names + ' PASS on record', 'PASS', ', '.join('P%s %s' % n for n in need))
    return recs


def recon_json(recdir):
    rj = os.path.join(recdir, 'recon', 'RECON.json')
    return json.load(open(rj)), C.md5_file(rj)


def stem(zip_path):
    b = os.path.basename(zip_path)
    return b[:-4] if b.lower().endswith('.zip') else b


def new_log(path):
    """path.vN with the first N not yet used (a log is never overwritten)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = 1
    while os.path.exists('%s.v%d' % (path, n)):
        n += 1
    return '%s.v%d' % (path, n)


def free_gib(p):
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return shutil.disk_usage(p).free / 2.0 ** 30


def state_with_outputs(recdir, phase, index, fp, missing):
    """C.state(), and a CURRENT record whose outputs are gone reads STALE. missing(record) -> list."""
    s = C.state(recdir, phase, index, fp)
    if s == 'CURRENT':
        r = record(recdir, index, phase)
        if missing(r):
            return 'STALE'
    return s


class Stopped(BaseException):
    """A signal to stop (SIGTERM, or SIGHUP when not ignored): a BaseException, so no `except Exception` hides it."""


def begin(st):
    """Register the phase's Status for crash(); SIGTERM (and SIGHUP unless nohup ignores it) ends the record too."""
    CURRENT['st'] = st

    def _stop(signum, frame):
        raise Stopped('stopped by signal %d' % signum)
    signal.signal(signal.SIGTERM, _stop)
    if signal.getsignal(signal.SIGHUP) != signal.SIG_IGN:
        signal.signal(signal.SIGHUP, _stop)


def _quiet():
    """After the console pipe broke (the operator's tee died), send further output nowhere, so the exit is clean."""
    try:
        fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(fd, sys.stdout.fileno())
        os.dup2(fd, sys.stderr.fileno())
    except (OSError, ValueError):
        pass


def crash(tag, e):
    """From __main__ on an exception or a stop: end the record ERROR with the traceback tail, writing the record
    before printing anything (the console may be gone); a second signal cannot interrupt it. Exit code 3."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal.SIG_IGN)
    st = CURRENT.get('st')
    if st is not None and not st.rec.get('end'):
        tb = traceback.format_exc().strip().splitlines()
        st.rec['gates'].append(dict(id='ERR', name='unexpected error', verdict='ERROR',
                                    value='%s: %s' % (type(e).__name__, e), threshold='', note='\n'.join(tb[-6:])))
        try:
            st.finish()
        except OSError:
            _quiet()
    try:
        sys.stderr.write('%s: %s: %s\n' % (tag, type(e).__name__, e))
        sys.stderr.flush()
    except OSError:
        _quiet()
    return 3


def main_guard(tag, main):
    try:
        rc = main()
    except BrokenPipeError as e:
        _quiet()
        rc = crash(tag, e)
    except (Exception, KeyboardInterrupt, Stopped) as e:  # noqa: BLE001
        rc = crash(tag, e)
    sys.exit(rc)
