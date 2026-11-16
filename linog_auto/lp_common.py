#!/usr/bin/env python3
"""lp_common.py -- shared helpers for linog_auto, the LInOG ALOS-1 automated pipeline.

Config (linog_paths.cfg + environment), frame folders, status records, fingerprints.
Standard library only, Python 3.6 or later.

v0.13 (R8, ascending record 13.2 and 13.4): load_cfg(path, frame) gives a path the table lacks a derived entry (entry =
derived: the residue by the path formula, the direction by the frame rule, no date-law anchor, which recon derives from the
frame's own granules); a table entry (entry = table) keeps its four keys required, and a section that names the path in
another form ([p84], [P084], [p0084]) is an error. A key dem_<frame> takes the place of dem for its frame (14.4);
LINOG_DEM still wins over both. residue_of(path), path_of(orbit) and dir_by_frame(frame) live here.

Status record: <frame>/status/P<index>_<phase>.json, written at START (verdict RUNNING)
and at END (PASS, FAIL, DECISION or ERROR), atomically (temp file + rename). A phase
is skipped on a later run only when its record reads PASS and the fingerprint of its
current inputs equals the recorded one; otherwise it runs again.

Command line (used by linog_auto.sh):
    lp_common.py framedir <PATH> <FRAME>      print the frame folder (the path table's entry for that frame)
    lp_common.py reason <status.json>         print verdict and reason of a record
    lp_common.py summary <frame folder>       one line per status record
"""
import configparser
import datetime
import getpass
import glob
import hashlib
import json
import os
import re
import socket
import sys

VERSION = 'linog_auto v0.13 (2026-10-16)'   # the release that last changed this module
HERE = os.path.dirname(os.path.abspath(__file__))
RC = {'PASS': 0, 'FAIL': 2, 'ERROR': 3, 'DECISION': 4}
ORB_CYCLE = 671                                  # orbits a repeat cycle (46 days)
PATH_KEYS = ('direction', 'residue', 'epoch_date', 'epoch_orbit')   # a table entry holds all four (R8, 13.2)
SECTION_RE = re.compile(r'^[pP]0*(\d+)$')        # a section that names a path, in any form


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def md5_file(p, block=1 << 20):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(block), b''):
            h.update(b)
    return h.hexdigest()


def md5_obj(o):
    return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()


def norm_path(p):
    s = str(p).strip()
    if not s.isdigit() or not 1 <= int(s) <= 671:
        raise ValueError('path must be a number 1-671, got %r' % p)
    return '%03d' % int(s)


def norm_frame(f):
    s = str(f).strip()
    if not s.isdigit() or not 0 <= int(s) <= 7199:
        raise ValueError('frame must be a number 0-7199, got %r' % f)
    return '%04d' % int(s)


def cfg_file():
    return os.environ.get('LINOG_AUTO_CFG') or os.path.join(HERE, 'linog_paths.cfg')


def selftest_hooks():
    """v0.13 (the part 2 review's P2-08): the self-test's LINOG_MOCK_* hooks that write data or stop a phase act only under a
    path table other than the package's own (the self-test's mock table, named by LINOG_AUTO_CFG); a run on felix, which
    reads the package's table, ignores them whatever the environment holds."""
    f = os.environ.get('LINOG_AUTO_CFG')
    return bool(f) and os.path.realpath(f) != os.path.realpath(os.path.join(HERE, 'linog_paths.cfg'))


def selftest_hook(name):
    """A LINOG_MOCK_* hook's value when selftest_hooks() allows it, else None; printed when it is set."""
    v = os.environ.get(name)
    if v and selftest_hooks():
        print('   SELF-TEST HOOK %s=%s (the self-test\'s path table %s)' % (name, v, os.environ.get('LINOG_AUTO_CFG')))
        sys.stdout.flush()
        return v
    if v:
        print('   %s=%s ignored: the package\'s own path table (hooks act only under the self-test\'s)' % (name, v))
        sys.stdout.flush()
    return None


D2_DECISION = os.path.join('recon', 'd2_decision.json')   # v0.13, R7 (ascending record 11.3): the D2 loop's record
D2_TXT = os.path.join('recon', 'd2.txt')                   # v0.13, R7 (11.6): the operator's "take <dates>" or "keep <dates>"
D2_VERBS = ('take', 'keep')


def d2_decision(W):
    """v0.13, R7: (the decision, its md5) from <frame>/recon/d2_decision.json, or (None, None) when there is none; ValueError
    when it is unreadable or not R7's (a person looks). recon, reference, coarse and admit read it."""
    p = os.path.join(W, D2_DECISION)
    if not os.path.isfile(p):
        return None, None
    try:
        dec = json.load(open(p))
    except ValueError as e:
        raise ValueError('%s is not JSON: %s' % (p, e))
    if not isinstance(dec, dict) or not isinstance(dec.get('loops'), list):
        raise ValueError('%s holds no list of loops' % p)
    for i, lp in enumerate(dec['loops']):   # the part 5 review's P5-09: each loop as coarse writes it
        if not isinstance(lp, dict) or not isinstance(lp.get('loop'), int) or not isinstance(lp.get('dates'), dict):
            raise ValueError('%s: its loop %d is not R7\'s (a loop number and a dates mapping)' % (p, i + 1))
        for d, v in lp['dates'].items():
            if not re.match(r'^\d{8}$', str(d)) or not isinstance(v, dict) or not v.get('granule'):
                raise ValueError('%s: loop %s, %r: not a date with its granule' % (p, lp.get('loop'), d))
    if dec.get('reference') is not None and not re.match(r'^\d{8}$', str(dec.get('reference'))):
        raise ValueError('%s: its reference %r is not a date' % (p, dec.get('reference')))
    return dec, md5_file(p)


def d2_dates(dec):
    """v0.13, R7: {date: dict(loop, granule, zip, stem, mode, why, ...)} over a decision's loops."""
    out = {}
    for lp in (dec or {}).get('loops') or []:
        for d, v in sorted((lp.get('dates') or {}).items()):
            out[d] = dict(v, loop=lp.get('loop'))
    return out


def d2_txt(W):
    """v0.13, R7 (11.6): (verb, dates, md5, line) from <frame>/recon/d2.txt's one line that is not a comment, "take <dates>"
    or "keep <dates>" (YYYYMMDD each), or (None, None, None, None) when there is no file; ValueError when that line is not
    one of those (or there are two)."""
    p = os.path.join(W, D2_TXT)
    if not os.path.isfile(p):
        return None, None, None, None
    ls = [x.strip() for x in open(p, errors='replace') if x.strip() and not x.strip().startswith('#')]
    if len(ls) != 1:
        raise ValueError('%s: %d lines that are not comments, want one ("take <dates>" or "keep <dates>")' % (p, len(ls)))
    w = ls[0].replace(',', ' ').split()
    if len(w) < 2 or w[0].lower() not in D2_VERBS or not all(re.match(r'^\d{8}$', x) for x in w[1:]):
        raise ValueError('%s: %r is not "take <YYYYMMDD ...>" or "keep <YYYYMMDD ...>"' % (p, ls[0]))
    return w[0].lower(), sorted(set(w[1:])), md5_file(p), ls[0]


def residue_of(path):
    """The orbit residue of a path (R8, 13.2): 248 x (path - 85) mod 671, the inverse of path = (46 x residue + 85)
    mod 671 (46 x 248 = 1 mod 671); path 85 has residue 0."""
    return 248 * (int(path) - 85) % ORB_CYCLE


def path_of(orbit):
    """The path of an orbit: (46 x (orbit mod 671) + 85) mod 671, with 0 read as 671 (path_of(392) = 671)."""
    p = (46 * (int(orbit) % ORB_CYCLE) + 85) % ORB_CYCLE
    return p or ORB_CYCLE


def dir_by_frame(frame):
    """The frame rule: D (descending) for frames 1800 to 5399, else A (ascending)."""
    return 'D' if 1800 <= int(frame) < 5400 else 'A'


def load_cfg(path, frame=None):
    """Settings for one path (and frame): [defaults], then [pPPP] if the table holds it (entry = table, its four keys
    required), else a derived entry (entry = derived: residue by the path formula, direction by the frame rule when a
    frame is given, no epoch keys); dem_<frame> in place of dem for the frame; then the environment."""
    f = cfg_file()
    cp = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    if not cp.read(f):
        raise FileNotFoundError('cannot read the path table %s' % f)
    sec = 'p' + path
    other = sorted(x for x in cp.sections() if x != sec and SECTION_RE.match(x)
                   and int(SECTION_RE.match(x).group(1)) == int(path))
    if other:
        raise KeyError('%s: section [%s] names path %s in another form; the table writes it [%s] (R8, 13.2)'
                       % (f, '], ['.join(other), path, sec))
    s = dict(cp['defaults']) if cp.has_section('defaults') else {}
    if cp.has_section(sec):
        missing = [k for k in PATH_KEYS if k not in cp[sec]]
        if missing:
            raise KeyError('%s: path %s has no %s (a table entry holds all of %s; R8 derives only a path the table '
                           'lacks)' % (f, path, ', '.join(repr(k) for k in missing), ', '.join(PATH_KEYS)))
        s.update(cp[sec])
        s['entry'] = 'table'
    else:
        s['entry'] = 'derived'
        s['residue'] = str(residue_of(path))
        if frame is not None:
            s['direction'] = dir_by_frame(frame)
    if frame is not None:
        fk = 'dem_' + norm_frame(frame)
        if fk in s:
            s['dem'], s['dem_key'] = s[fk], fk
    for key, env in (('root', 'LINOG_ROOT'), ('archive', 'LINOG_ARCHIVE'), ('dem', 'LINOG_DEM')):
        if os.environ.get(env):
            s[key] = os.environ[env]
            if key == 'dem':
                s['dem_key'] = 'LINOG_DEM'
    for key in ('root', 'archive', 'dem'):
        if key not in s:
            raise KeyError('%s: path %s has no %r' % (f, path, key))
    s['cfg_file'], s['cfg_md5'], s['path'] = f, md5_file(f), path
    return s


def frame_dir(cfg, path, frame):
    return os.path.join(cfg['root'], 'p' + path, 'f' + frame)


def tool_md5s(*names):
    return {n: md5_file(os.path.join(HERE, n)) for n in names}


class Status(object):
    """One phase's status record. gate() adds a checked item; finish() sets the verdict."""

    def __init__(self, recdir, phase, index, path, frame):
        self.dir = os.path.join(recdir, 'status')
        self.file = os.path.join(self.dir, 'P%s_%s.json' % (index, phase))
        self.rec = dict(phase=phase, index=index, version=VERSION, path=path, frame=frame,
                        host=socket.gethostname(), user=getpass.getuser(), pid=os.getpid(),
                        python=sys.executable, python_version=sys.version.split()[0],
                        start=utc(), end=None, verdict='RUNNING', rc=None, reason='',
                        fingerprint=None, inputs={}, outputs={}, gates=[], tools={})

    def write(self):
        os.makedirs(self.dir, exist_ok=True)
        tmp = self.file + '.tmp%d' % os.getpid()
        with open(tmp, 'w') as fh:
            json.dump(self.rec, fh, indent=1, default=str)
            fh.write('\n')
        os.replace(tmp, self.file)

    def gate(self, gid, name, verdict, value, threshold='', note=''):
        assert verdict in ('PASS', 'WARN', 'INFO', 'N/A', 'FAIL', 'DECISION', 'ERROR'), verdict
        self.rec['gates'].append(dict(id=gid, name=name, verdict=verdict, value=str(value),
                                      threshold=threshold, note=note))
        print('   %-7s %-8s %-30s %s%s' % (gid, verdict, name, value,
                                          ('   [%s]' % threshold) if threshold else ''))
        if note:
            for line in str(note).splitlines():
                print('                                            %s' % line)
        sys.stdout.flush()

    def finish(self, reason=''):
        v = [g['verdict'] for g in self.rec['gates']]
        verdict = ('ERROR' if 'ERROR' in v else 'FAIL' if 'FAIL' in v
                   else 'DECISION' if 'DECISION' in v else 'PASS')
        if not reason:
            bad = [g for g in self.rec['gates'] if g['verdict'] in ('ERROR', 'FAIL', 'DECISION')]
            reason = '; '.join('%s %s: %s' % (g['id'], g['name'], g['value']) for g in bad) or 'all gates passed'
        self.rec.update(end=utc(), verdict=verdict, rc=RC[verdict], reason=reason)
        self.write()
        print('   => P%s %s: %s (rc %d) -- %s' % (self.rec['index'], self.rec['phase'], verdict,
                                                 RC[verdict], reason))
        return RC[verdict]


def state(recdir, phase, index, fingerprint):
    """NONE, RUNNING, CURRENT (PASS with the same inputs), STALE, or the last verdict."""
    f = os.path.join(recdir, 'status', 'P%s_%s.json' % (index, phase))
    if not os.path.exists(f):
        return 'NONE'
    try:
        r = json.load(open(f))
    except ValueError:
        return 'UNREADABLE'
    if r.get('verdict') == 'RUNNING':
        return 'RUNNING'
    if r.get('verdict') != 'PASS':
        return r.get('verdict', 'UNKNOWN')
    return 'CURRENT' if r.get('fingerprint') == fingerprint else 'STALE'


def main(argv):
    if len(argv) >= 4 and argv[1] == 'framedir':
        path, frame = norm_path(argv[2]), norm_frame(argv[3])
        print(frame_dir(load_cfg(path, frame), path, frame))
        return 0
    if len(argv) >= 3 and argv[1] == 'reason':
        r = json.load(open(argv[2]))
        print('%s (rc %s): %s' % (r.get('verdict'), r.get('rc'), r.get('reason')))
        return 0
    if len(argv) >= 3 and argv[1] == 'summary':
        for f in sorted(glob.glob(os.path.join(argv[2], 'status', 'P*.json'))):
            r = json.load(open(f))
            print('   P%-3s %-8s %-8s %-20s %s' % (r.get('index'), r.get('phase'), r.get('verdict'),
                                                   r.get('end') or r.get('start'), r.get('reason')))
        return 0
    sys.stderr.write(__doc__)
    return 3


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except (ValueError, KeyError, FileNotFoundError) as e:
        sys.stderr.write('lp_common: %s\n' % e)
        sys.exit(3)
