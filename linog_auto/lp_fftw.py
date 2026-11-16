#!/usr/bin/env python3
"""lp_fftw.py -- the pinned FFTW wisdom for ISCE2's FFT steps (linog_auto v0.9; record 80.3, 80.5 and 81).

ISCE2's cfft1d_jpl (components/isceobj/Util/src/cfft1d_jpl.F), from which ampcor (refine), crossmul and icu (igram)
take their FFTs, plans each size it is asked for with FFTW_MEASURE: the planner times its candidates, so the plan, and
with it the last bits of the result, can change from run to run (FFTW's FAQ, 3.8). S25 (4 Oct 2026) ran ampcor 46 times
at once on one pair of I4's: 9 distinct results without wisdom, 1 with fftw/wisdom_felix.wis; crossmul 9 of 12, then 1.
On its first call in a process cfft1d_jpl reads WISDOM_FILE, prints `wisdomFile, length = <file> <length>`, imports the
file and prints the import's return value; when that is 0 it stops with `STOP cannot import fftw wisdom file`, and
gfortran's STOP exits with status 0. ISCE2's C wrapper opens the file without a check, so a missing file crashes the job.

linog_fftw.cfg pins the wisdom file (WISDOM, relative to this pipeline folder unless absolute), the library ISCE2's
modules load (ENV_PREFIX/lib/libfftw3f.so.3 resolves to ENV_PREFIX/FFTW_LIB_REL: its md5 and its version string) and
the three modules (relative to the isce package folder, with their md5s). The problems are those cfft1d_jpl can plan:
in place, complex single precision, sizes 2**SIZE_MIN to 2**SIZE_MAX, both directions, at the offsets OFFSET_MIN to
OFFSET_MAX bytes (step OFFSET_STEP) from an aligned start, since FFTW keys wisdom on the array's alignment class.

  lp_fftw.py facts                   the files linog_fftw.cfg names, as found in this environment (json)
  lp_fftw.py probe LIB WIS|- KEY=V.. in this process: LIB's version; import WIS (- imports nothing); plan every problem
                                     with FFTW_MEASURE|FFTW_WISDOM_ONLY and count the plans made (json)
  lp_fftw.py check [WIS|-]           probe in a fresh process with the pinned library: rc 0 when the pinned (or named) file
                                     imports and covers every problem; with -, rc 0 when none is covered
  lp_fftw.py gen OUT.wis             plan every problem with FFTW_MEASURE and export the wisdom (S25 made the pinned file so
                                     on felix, with fftw25.py; the self-test makes its own on its host's library)
  lp_fftw.py logs LOG...             the wisdom lines and STOP lines of job logs (json)

Standard library only (ctypes). Writes only gen's OUT.
"""
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import time

VERSION_FFTW = 'linog_auto v0.9 (2026-10-04)'
HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ('WISDOM', 'WISDOM_MD5', 'FFTW_LIB_REL', 'FFTW_LIB_MD5', 'FFTW_VERSION', 'AMPCOR_SO', 'AMPCOR_SO_MD5', 'CROSSMUL_SO',
        'CROSSMUL_SO_MD5', 'ICU_SO', 'ICU_SO_MD5', 'SIZE_MIN', 'SIZE_MAX', 'OFFSET_MIN', 'OFFSET_MAX', 'OFFSET_STEP', 'PROBLEMS')
MODULES = ('ampcor', 'crossmul', 'icu')
MEASURE = 0
WISDOM_ONLY = 1 << 21
HEAD = re.compile(r'^\s*wisdomFile, length =\s*(.*?)\s+(-?\d+)\s*$')
RET = re.compile(r'^\s*(-?\d+)\s*$')
STOP = re.compile(r'^\s*STOP\b')


def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def cfg_file():
    return os.environ.get('LINOG_FFTW_CFG') or os.path.join(HERE, 'linog_fftw.cfg')


def load():
    """linog_fftw.cfg as a dict (KEY=value lines; # comments), with the wisdom's absolute path and the problems' count."""
    f = cfg_file()
    d = {}
    for ln in open(f):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            d[k.strip()] = v.strip()
    miss = [k for k in KEYS if k not in d]
    if miss:
        raise KeyError('%s lacks %s' % (f, ', '.join(miss)))
    for k in ('SIZE_MIN', 'SIZE_MAX', 'OFFSET_MIN', 'OFFSET_MAX', 'OFFSET_STEP', 'PROBLEMS'):
        d[k] = int(d[k])
    d['fftw_cfg_file'], d['fftw_cfg_md5'] = f, md5f(f)
    d['wisdom_path'] = d['WISDOM'] if os.path.isabs(d['WISDOM']) else os.path.join(HERE, d['WISDOM'])
    n = len(problems(d))
    if n != d['PROBLEMS']:
        raise ValueError('%s: the sizes, offsets and two directions make %d problems, PROBLEMS says %d' % (f, n, d['PROBLEMS']))
    return d


def problems(d):
    """[(size, offset in bytes, sign)] in the order gen plans them."""
    return [(2 ** k, off, sign) for off in range(d['OFFSET_MIN'], d['OFFSET_MAX'] + 1, d['OFFSET_STEP'])
            for k in range(d['SIZE_MIN'], d['SIZE_MAX'] + 1) for sign in (-1, 1)]


def pins(d):
    """The pins as a dict for fingerprints and records: what the phase intends to use."""
    return dict(wisdom=d['WISDOM_MD5'], lib=d['FFTW_LIB_MD5'], version=d['FFTW_VERSION'],
                modules=dict((m, d['%s_SO_MD5' % m.upper()]) for m in MODULES), problems=d['PROBLEMS'])


def isce_dir():
    try:
        import importlib.util
        sp = importlib.util.find_spec('isce')
        return os.path.dirname(sp.origin) if sp is not None and sp.origin else None
    except (ImportError, ValueError):
        return None


def ldd_fftw(p):
    """(the libfftw3f file ldd resolves for p, real path; or None and why)."""
    try:
        out = subprocess.run(['ldd', p], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=60).stdout.decode('utf-8', 'replace')
    except (OSError, subprocess.SubprocessError) as e:
        return None, 'ldd failed: %s' % e
    for line in out.splitlines():
        m = re.match(r'\s*libfftw3f\.so[.\d]*\s*=>\s*(/\S+)', line)
        if m:
            return os.path.realpath(m.group(1)), None
        if re.match(r'\s*libfftw3f\.so[.\d]*\s*=>\s*not found', line):
            return None, 'ldd: libfftw3f not found'
    return None, 'no libfftw3f in ldd\'s output'


def facts(d, prefix, which=MODULES, idir=None):
    """The files linog_fftw.cfg names, as found: dict(wisdom, wisdom_md5, lib, lib_md5, link (where
    ENV_PREFIX/lib/libfftw3f.so.3 resolves), modules={name: dict(path, md5, lib)}, isce_dir)."""
    idir = idir or isce_dir()
    w = d['wisdom_path']
    lib = os.path.join(prefix, d['FFTW_LIB_REL'])
    link = os.path.join(prefix, 'lib', 'libfftw3f.so.3')
    out = dict(cfg=d['fftw_cfg_file'], cfg_md5=d['fftw_cfg_md5'], wisdom=w, wisdom_md5=md5f(w) if os.path.isfile(w) else None,
               lib=lib, lib_md5=md5f(lib) if os.path.isfile(lib) else None,
               link=os.path.realpath(link) if os.path.exists(link) else None, isce_dir=idir, modules={})
    for m in which:
        p = os.path.join(idir or '/nonexistent', d['%s_SO' % m.upper()])
        got, err = ldd_fftw(p) if os.path.isfile(p) else (None, 'absent')
        out['modules'][m] = dict(path=p, md5=md5f(p) if os.path.isfile(p) else None, lib=got or err)
    return out


def problems_of(fx, d):
    """What is not as linog_fftw.cfg pins it, one line each."""
    bad = []
    if fx['wisdom_md5'] != d['WISDOM_MD5']:
        bad.append('wisdom %s: md5 %s, pinned %s' % (fx['wisdom'], fx['wisdom_md5'] or 'absent', d['WISDOM_MD5']))
    if fx['lib_md5'] != d['FFTW_LIB_MD5']:
        bad.append('libfftw3f %s: md5 %s, pinned %s' % (fx['lib'], fx['lib_md5'] or 'absent', d['FFTW_LIB_MD5']))
    real = os.path.realpath(fx['lib'])
    if fx['link'] != real:
        bad.append('lib/libfftw3f.so.3 resolves to %s, not %s' % (fx['link'] or 'nothing', real))
    for m, v in sorted(fx['modules'].items()):
        if v['md5'] != d['%s_SO_MD5' % m.upper()]:
            bad.append('%s %s: md5 %s, pinned %s' % (m, v['path'], v['md5'] or 'absent', d['%s_SO_MD5' % m.upper()]))
        if v['lib'] != real:
            bad.append('%s loads %s, not %s' % (m, v['lib'], real))
    return bad


def _lib(path):
    L = ctypes.CDLL(path)
    L.fftwf_malloc.restype = ctypes.c_void_p
    L.fftwf_malloc.argtypes = [ctypes.c_size_t]
    L.fftwf_free.argtypes = [ctypes.c_void_p]
    L.fftwf_plan_dft_1d.restype = ctypes.c_void_p
    L.fftwf_plan_dft_1d.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_uint]
    L.fftwf_destroy_plan.argtypes = [ctypes.c_void_p]
    L.fftwf_export_wisdom_to_filename.argtypes = [ctypes.c_char_p]
    L.fftwf_export_wisdom_to_filename.restype = ctypes.c_int
    L.fftwf_import_wisdom_from_filename.argtypes = [ctypes.c_char_p]
    L.fftwf_import_wisdom_from_filename.restype = ctypes.c_int
    L.fftwf_alignment_of.argtypes = [ctypes.c_void_p]
    L.fftwf_alignment_of.restype = ctypes.c_int
    return L


def version(L):
    try:
        return (ctypes.c_char * 128).in_dll(L, 'fftwf_version').value.decode('ascii', 'replace')
    except (ValueError, AttributeError) as e:
        return 'unread (%s)' % e


def probe(lib, wis, d):
    """In this process: dict(version, import (None when nothing is imported), covered, total, first_missing, classes)."""
    L = _lib(lib)
    imp = None if wis in (None, '-') else L.fftwf_import_wisdom_from_filename(wis.encode())
    pr = problems(d)
    base = L.fftwf_malloc(2 ** d['SIZE_MAX'] * 8 + d['OFFSET_MAX'] + 128)
    if not base:
        raise MemoryError('fftwf_malloc failed')
    got, first = 0, None
    try:
        classes = sorted({L.fftwf_alignment_of(base + off) for _, off, _ in pr})
        for n, off, sign in pr:
            pl = L.fftwf_plan_dft_1d(n, base + off, base + off, sign, MEASURE | WISDOM_ONLY)
            if pl:
                got += 1
                L.fftwf_destroy_plan(pl)
            elif first is None:
                first = 'n %d, offset %d, sign %d' % (n, off, sign)
    finally:
        L.fftwf_free(base)
    return dict(version=version(L), imported=imp, covered=got, total=len(pr), first_missing=first, classes=classes)


def check(lib, wis, d, timeout=300):
    """probe in a fresh process (no wisdom this process may hold counts): its dict, or dict(error=...)."""
    args = [sys.executable, '-B', os.path.abspath(__file__), 'probe', lib, wis or '-'] + \
        ['%s=%s' % (k, d[k]) for k in ('SIZE_MIN', 'SIZE_MAX', 'OFFSET_MIN', 'OFFSET_MAX', 'OFFSET_STEP')]
    try:
        p = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return dict(error='%s: %s' % (type(e).__name__, e))
    txt = p.stdout.decode('utf-8', 'replace').strip()
    try:
        r = json.loads(txt.splitlines()[-1])
    except (ValueError, IndexError):
        return dict(error='probe rc %d: %s' % (p.returncode, txt[-300:]))
    if not isinstance(r, dict) or not all(k in r for k in ('version', 'imported', 'covered', 'total')):
        return dict(error='probe rc %d: not its result: %s' % (p.returncode, txt[-300:]))
    return r


def gen(lib, out, d):
    """Plan every problem with FFTW_MEASURE and export the wisdom to out. dict(plans, seconds, version, classes)."""
    L = _lib(lib)
    pr = problems(d)
    base = L.fftwf_malloc(2 ** d['SIZE_MAX'] * 8 + d['OFFSET_MAX'] + 128)
    if not base:
        raise MemoryError('fftwf_malloc failed')
    t0 = time.time()
    try:
        classes = sorted({L.fftwf_alignment_of(base + off) for _, off, _ in pr})
        for n, off, sign in pr:
            pl = L.fftwf_plan_dft_1d(n, base + off, base + off, sign, MEASURE)
            if not pl:
                raise RuntimeError('plan failed: n %d, offset %d, sign %d' % (n, off, sign))
            L.fftwf_destroy_plan(pl)
    finally:
        L.fftwf_free(base)
    if L.fftwf_export_wisdom_to_filename(out.encode()) != 1 or not os.path.isfile(out):
        raise IOError('the wisdom was not exported to %s' % out)
    return dict(plans=len(pr), seconds=round(time.time() - t0, 1), version=version(L), classes=classes, file=out,
                md5=md5f(out), size=os.path.getsize(out))


STOPMSG = 'STOP cannot import fftw wisdom file'


def log_wisdom(path):
    """A job log's wisdom lines: dict(entries=[dict(file, length, ret, line)], stops=[line text], error). Lines are counted by
    newline alone (as grep -n counts them), and each line's pieces between carriage returns are read in turn (a progress
    counter rewrites its line with them). ret is the next piece after the header when it is a bare integer (the import's
    return value; cfft1d_jpl prints none without a file). A STOP is a piece that starts with STOP, or cfft1d_jpl's own
    message anywhere in a line (glued to output that had no newline)."""
    out = dict(entries=[], stops=[], error=None)
    try:
        with open(path, 'rb') as fh:
            text = fh.read().decode('utf-8', 'replace')
    except OSError as e:
        out['error'] = str(e)
        return out
    pieces = []
    for i, ln in enumerate(text.split('\n')):
        if STOPMSG in ln and not any(STOP.match(x) for x in ln.split('\r')):
            out['stops'].append(ln.strip()[:200])
        pieces += [(i + 1, x) for x in ln.split('\r') if x.strip()]
    for k, (n, x) in enumerate(pieces):
        m = HEAD.match(x)
        if m:
            r = RET.match(pieces[k + 1][1]) if k + 1 < len(pieces) else None
            out['entries'].append(dict(file=m.group(1), length=int(m.group(2)), ret=int(r.group(1)) if r and m.group(1) else None,
                                       line=n))
        elif STOP.match(x):
            out['stops'].append(x.strip()[:200])
    return out


def judge_log(path, wis, per_job):
    """'' when the log holds per_job wisdom lines naming wis, each followed by the import's 1, and no STOP line; else why."""
    w = log_wisdom(path)
    if w['error']:
        return 'unreadable: %s' % w['error']
    why = []
    if w['stops']:
        why.append('STOP: %s' % w['stops'][0])
    if len(w['entries']) != per_job:
        why.append('%d wisdom line(s), want %d' % (len(w['entries']), per_job))
    for e in w['entries']:
        if e['file'] != wis:
            why.append('line %d: wisdom %s' % (e['line'], repr(e['file']) if e['file'] else 'none (length = %d)' % e['length']))
        elif e['ret'] != 1:
            why.append('line %d: import returned %s' % (e['line'], e['ret']))
    return '; '.join(why)


def kv(args):
    d = {}
    for a in args:
        k, v = a.split('=', 1)
        d[k] = int(v)
    return d


def main(a):
    if a[:1] == ['probe'] and len(a) >= 3:
        print(json.dumps(probe(a[1], a[2], kv(a[3:])), sort_keys=True))
        return 0
    d = load()
    if a[:1] == ['facts'] and len(a) == 1:
        import lp_p2 as P2
        print(json.dumps(dict(facts(d, P2.load_stack()['ENV_PREFIX']), pins=pins(d)), indent=1, sort_keys=True))
        return 0
    if a[:1] == ['check'] and len(a) <= 2:
        import lp_p2 as P2
        lib = os.path.join(P2.load_stack()['ENV_PREFIX'], d['FFTW_LIB_REL'])
        wis = a[1] if len(a) == 2 else d['wisdom_path']
        r = check(lib, wis, d)
        print(json.dumps(r, sort_keys=True))
        if 'error' in r:
            return 2
        if wis == '-':
            return 0 if r['covered'] == 0 else 2
        return 0 if r['imported'] == 1 and r['covered'] == r['total'] else 2
    if a[:1] == ['gen'] and len(a) == 2:
        import lp_p2 as P2
        print(json.dumps(gen(os.path.join(P2.load_stack()['ENV_PREFIX'], d['FFTW_LIB_REL']), a[1], d), sort_keys=True))
        return 0
    if a[:1] == ['logs'] and len(a) >= 2:
        print(json.dumps(dict((p, log_wisdom(p)) for p in a[1:]), indent=1, sort_keys=True))
        return 0
    sys.stderr.write(__doc__)
    return 3


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, KeyError, ValueError, RuntimeError, MemoryError) as e:
        sys.stderr.write('lp_fftw: %s\n' % e)
        sys.exit(3)
