#!/usr/bin/env python3
"""lp_rwin.py -- linog_auto Phase 1br: the range window. Each date's starting range (r0) set from its CEOS image records.

ISCE's ALOS_SLC reader, which the kit's unpacker uses, gives the shelve the leader's range gate delay as r0 (c/2 x the
delay) and reads the image records' 'Slant range to 1st data sample' only when the delay is missing; it writes every
sample of every record, fill included. On some granules the image records put column 0 one gate (149.896 m, 1 us) nearer
or farther than the leader's delay: RD4 read 51 of the 779 archive granules so, 8 of P084 F3320's 24 (F26, F27), and
RD5 showed that with r0 from the records G7 passes those eight (record sections 38 to 40). For every unpacked date this
phase reads the IMG-HH file descriptor, its first, middle and last image records and the leader, with ISCE's own CEOS
parser and record definitions, and sets the shelve's r0 to column 0 by the records when the two differ by one gate:

    column 0 = (slant range to 1st data sample) - (left fill) x c / (2 x sampling rate)
    k = round((column 0 - r0_leader) / gate);  column 0 - r0_leader - k x gate within 1 m (the records hold whole metres)
    r0 = r0_leader + k x gate   (the leader's fraction of a metre kept: r0 stays on the kit's gate grid)

Only what RD4 measured is corrected: records without fill (no granule of the 779 carried any, so the fill term is the
CEOS reading, never seen on felix) and |k| <= 1 (all 51 that differ). Anything else is a FAIL and nothing is written:
fill in a record, |k| > 1, a file descriptor that disagrees with unpack's lines and width, records that disagree (first,
middle, last), a difference that is not whole gates, a shelve r0 that is neither the leader's nor the target. A date
whose shelve already holds the target is left alone, so a re-run writes nothing; its other keys are then compared with
the copy made before its change. Before a shelve is written its files are copied into _archive/rwin_<UTC>/SLC/<date>/
and checked by md5. Each write, its read-back and the record that names it run with SIGINT, SIGTERM and SIGHUP deferred
(Held), so a stop lands after the record says what was written; the record names the date being written before the
write starts, for a SIGKILL.

Gates
  G1br.1  unpack PASS on record: its dates and granules                                              FAIL
  G1br.2  environment: the pinned env at its prefix; ISCE's CEOS parser and its ALOS SLC record definitions   ERROR
  G1br.3  every date: IMG-HH-* and LED-* in unzipped/<stem>/, readable; the file descriptor's records, pixels and
          record length = unpack's lines, width and 412 + 8 x width; the first, middle and last image records agree;
          no fill; first data sample, sampling rate and gate delay not zero                           FAIL
  G1br.4  every date: the shelve's r0 is the leader's (c/2 x gate delay, within 0.01 m) or already the target  FAIL
  G1br.5  every date: column 0 - r0_leader = k whole gates within 1 m, and |k| <= 1                     FAIL
  G1br.6  the shelves to change: copied into _archive/rwin_<UTC>/SLC/<date>/ first, md5s equal           FAIL
  G1br.7  the writes: r0 set, read back; the shelve's other keys byte for byte unchanged                 FAIL
  G1br.8  every date: the shelve's r0 = r0_leader + k x gate (within 1e-6 m), within 1 m of column 0; a date found
          already corrected: its other keys = its latest copy's, the copy's r0 the leader's; WARN when no copy  FAIL
Writes: SLC/<date>/data.dat, .dir, .bak of the dates it changes (dbm.dumb, as the unpacker wrote them);
_archive/rwin_<UTC>/ (the copies and backup.md5); its status record. Nothing is deleted.
--dryrun DIR: when the frame's own unpack is PASS on record, the table and the plan from the frame's records and shelves
(read-only); otherwise the plan only. Writes only DIR/status/P1br_rwin.json.
Standard library only for --state (the ssh shell's python3); the phase itself runs inside lp_env.sh.
Self-test only: LINOG_MOCK_RWIN_PAUSE=<date> writes LINOG_MOCK_MARK and waits 60 s before that date's write;
LINOG_MOCK_RWIN_HOLD=<date> writes it and waits 5 s inside the held write, after the shelve is written.
v0.13 (ascending record 12.3 item 4, 17.6): G1br.2 checks the env's prefix as well as its name (CONDA_PREFIX is
linog_stack.cfg's ENV_PREFIX). FBD dates run as FBS dates do (Gap 2a): the arithmetic takes each leader's sampling rate and
the gate in metres; each date's fs_mhz is recorded, and bandlimit reads it.
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import dbm.dumb
import glob
import os
import shelve
import shutil
import signal
import sys
import time

import lp_common as C
import lp_p1 as P1

PHASE, IDX, LOGIC = 'rwin', '1br', 1
VERSION = C.VERSION   # v0.13 (v0.5 to v0.12: 'linog_auto v0.5 (2026-09-27)')
TOOLS = ('lp_rwin.py', 'lp_p1.py', 'lp_common.py')
C2 = 299792458.0 / 2.0
GATE = C2 * 1e-6            # one microsecond of range delay, 149.896229 m: 32 FBS samples, 16 FBD samples
TOL_M = 1.0                 # the image records hold whole metres
LEADER_TOL_M = 0.01         # ISCE sets r0 = c/2 x the leader's delay: equal but for rounding
KMAX = 1                    # RD4: every granule that differs does so by one gate
PREFIX_B = 412              # prefix bytes of an ALOS L1.1 image record (extract's size law)
SHELF = ('data', 'data.dat', 'data.dir', 'data.bak', 'data.db')
STOPSIGS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)


class LiveStatus(C.Status):
    """The record written after every gate, so a RUNNING record shows the gates taken so far (F25)."""

    def gate(self, *a, **k):
        C.Status.gate(self, *a, **k)
        self.write()


class Held(object):
    """SIGINT, SIGTERM and SIGHUP deferred until the block ends. Blocking them in this thread is not enough: once ISCE's
    objects are unpickled numpy is loaded, and its OpenBLAS threads can take a signal sent to the process, whose Python
    handler then still runs here, inside the block. So the Python handlers are also swapped for a recorder; at the end
    they are restored and the first recorded signal is raised again, which stops the phase as before. A signal ignored on
    entry (nohup's SIGHUP) stays ignored. When the block raises, its exception goes on and a recorded signal is dropped
    (the phase ends anyway). lp_p3.Deferred is the same."""

    def __enter__(self):
        self.got, self.old = [], {}
        for s in STOPSIGS:
            h = signal.getsignal(s)
            if h is not signal.SIG_IGN:
                self.old[s] = signal.SIG_DFL if h is None else h
                signal.signal(s, self._note)
        self.mask = signal.pthread_sigmask(signal.SIG_BLOCK, STOPSIGS)
        return self

    def _note(self, signum, frame):
        self.got.append(signum)

    def __exit__(self, et, ev, tb):
        # unblocked first, with the recorder still in place, so signals the kernel held go to it too; then the handlers
        # back, and one recorded signal raised again (two different ones would otherwise raise twice, the second
        # inside the crash path)
        signal.pthread_sigmask(signal.SIG_SETMASK, self.mask)
        for s, h in self.old.items():
            signal.signal(s, h)
        if et is None and self.got:
            signal.raise_signal(self.got[0])
        return False


def granule(W, stem):
    gd = os.path.join(W, 'unzipped', stem or '?')
    return gd, sorted(glob.glob(os.path.join(gd, 'IMG-HH-*'))), sorted(glob.glob(os.path.join(gd, 'LED-*')))


def file_id(p):
    try:
        s = os.stat(p)
        return [os.path.basename(p), s.st_size, s.st_mtime_ns]
    except OSError:
        return [os.path.basename(p), None, None]


def granule_ids(W, dates):
    """What this phase reads of each granule: the names, sizes and mtimes of its IMG-HH and LED files."""
    out = []
    for d in dates:
        _, imgs, leds = granule(W, d.get('stem'))
        out.append([d.get('date'), d.get('stem'), [file_id(p) for p in imgs[:1] + leds[:1]]])
    return out


def shelf_md5_in(sd):
    return {n: C.md5_file(os.path.join(sd, n)) for n in SHELF if os.path.isfile(os.path.join(sd, n))}


def shelf_md5(W, d):
    return shelf_md5_in(os.path.join(W, 'SLC', d))


def shelf_raw(sd):
    db = dbm.dumb.open(os.path.join(sd, 'data'), 'r')
    try:
        return {k.decode(): bytes(db[k]) for k in db.keys()}
    finally:
        db.close()


def shelf_r0(sd):
    with shelve.open(os.path.join(sd, 'data'), flag='r') as db:
        return float(db['frame'].getStartingRange())


def shelf_set_r0(sd, r0):
    with shelve.open(os.path.join(sd, 'data'), flag='w') as db:
        f = db['frame']
        if hasattr(f, 'setStartingRange'):
            f.setStartingRange(r0)
        else:
            f.startingRange = r0
        db['frame'] = f


def latest_copy(W, d):
    """The newest copy of SLC/<d>/ that an earlier run made before changing it, or None."""
    cs = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(W, '_archive', 'rwin_*', 'SLC', d, 'data.dir')))
    return cs[-1] if cs else None


class Ceos(object):
    """ISCE's CEOS parser and its ALOS SLC record definitions (isceobj/Sensor/CEOS.py, db/alos_slc)."""

    def __init__(self):
        import isceobj.Sensor.CEOS as CEOS
        self.C = CEOS
        self.db = os.path.join(os.path.dirname(os.path.abspath(CEOS.__file__)), 'db', 'alos_slc')
        miss = [n for n in ('image_file.xml', 'image_record.xml', 'leader_file.xml', 'scene_record.xml')
                if not os.path.isfile(os.path.join(self.db, n))]
        if miss:
            raise FileNotFoundError('%s lacks %s' % (self.db, ', '.join(miss)))

    def rec(self, xml, fh):
        r = self.C.CEOSDB(xml=os.path.join(self.db, xml), dataFile=fh)
        r.parse()
        r.finalizeParser()   # CEOSDB opens its xml in __init__ and leaves it open
        return r

    def leader(self, path):
        with open(path, 'rb') as fh:
            fdr = self.rec('leader_file.xml', fh)
            fh.seek(fdr.getEndOfRecordPosition())
            m = self.rec('scene_record.xml', fh).metadata
        return float(m['Range gate delay in microsec']), float(m['Range sampling rate in MHz'])

    def image(self, path):
        """({n, rl, px} of the file descriptor, [(left, data, right, first data sample) of the first, middle and last
        image record]); the records are read only when the descriptor gives at least 3 records and a record length."""
        with open(path, 'rb') as fh:
            fdr = self.rec('image_file.xml', fh)
            m = fdr.metadata
            fd = dict(n=m.get('Number of SAR DATA records'), rl=m.get('SAR DATA record length'),
                      px=m.get('Number of pixels per line per SAR channel'))
            if not isinstance(fd['n'], int) or not isinstance(fd['rl'], int) or fd['n'] < 3 or fd['rl'] <= PREFIX_B:
                return fd, None
            start, out = fdr.getEndOfRecordPosition(), []
            for i in (0, fd['n'] // 2, fd['n'] - 1):
                fh.seek(start + i * fd['rl'])
                r = self.rec('image_record.xml', fh).metadata
                out.append((r.get('Actual count of left-fill pixels'), r.get('Actual count of data pixels'),
                            r.get('Actual count of right-fill pixels'), r.get('Slant range to 1st data sample')))
        return fd, out


def window(ceos, W, d):
    """One date's row: the records, the leader, the shelve's r0, and what the rule makes of them."""
    row = dict(date=d['date'], stem=d.get('stem'))
    gd, imgs, leds = granule(W, d.get('stem'))
    if not imgs or not leds:
        row['why3'] = 'no %s in %s' % ('IMG-HH-*' if not imgs else 'LED-*', gd)
        return row
    try:
        fd, recs = ceos.image(imgs[0])
        delay, fs = ceos.leader(leds[0])
    except Exception as e:  # noqa: BLE001
        row['why3'] = 'records unreadable: %s: %s' % (type(e).__name__, str(e)[:120])
        return row
    row.update(img=os.path.basename(imgs[0]), px=fd['px'], nrec=fd['n'], reclen=fd['rl'], gate_us=delay, fs_mhz=fs)
    w = d.get('width')
    if recs is None or (fd['n'], fd['px'], fd['rl']) != (d.get('lines'), w, PREFIX_B + 8 * w if isinstance(w, int) else None):
        row['why3'] = 'the file descriptor gives %s records of %s B, %s pixels; unpack\'s record %s lines, width %s' % (
            fd['n'], fd['rl'], fd['px'], d.get('lines'), w)
        return row
    left, data, right, r1 = recs[0]
    row.update(left=left, data=data, right=right, r1=r1, same=all(x == recs[0] for x in recs[1:]))
    w3 = []
    if not row['same']:
        w3.append('the first, middle and last image records differ: %s' % recs)
    if left or right:
        w3.append('fill in the records (left %s, right %s): RD4 read none on the 779 archive granules, the rule is not '
                  'measured with fill' % (left, right))
    if not r1 or not fs or not delay:
        w3.append('a zero or missing value: first data sample %s m, sampling rate %s MHz, gate delay %s us' % (r1, fs, delay))
    if w3:
        row['why3'] = '; '.join(w3)
        return row
    dr = C2 / (fs * 1e6)
    r0_leader = C2 * delay * 1e-6
    col0 = r1 - left * dr          # left is 0 here (fill is refused above); the term kept so the rule reads as written
    k = int(round((col0 - r0_leader) / GATE))
    e = col0 - r0_leader - k * GATE
    target = r0_leader + k * GATE
    row.update(r0_leader=r0_leader, col0=col0, k=k, e_m=round(e, 3), target=target)
    try:
        r0 = shelf_r0(os.path.join(W, 'SLC', d['date']))
    except Exception as ex:  # noqa: BLE001
        row['why4'] = 'shelve unreadable: %s: %s' % (type(ex).__name__, str(ex)[:120])
        return row
    row['r0'] = r0
    w5 = []
    if abs(e) > TOL_M:
        w5.append('column 0 - r0_leader = %.2f m is not whole gates (%.2f m off)' % (col0 - r0_leader, e))
    if abs(k) > KMAX:
        w5.append('k %+d: RD4 read one gate on all 51 archive granules that differ, the rule is not measured beyond it' % k)
    if w5:
        row['why5'] = '; '.join(w5)
    if abs(r0 - target) < 1e-6:
        row['action'] = 'already' if k else 'same'
    elif abs(r0 - r0_leader) <= LEADER_TOL_M:
        row['action'] = 'change' if k else 'same'
    else:
        row['why4'] = 'the shelve holds %.4f m: neither the leader\'s %.4f nor the target %.4f' % (r0, r0_leader, target)
    return row


def against_copy(W, r):
    """For a date found already corrected: (copy or None, problems) from its latest copy: the other keys byte for byte,
    and the copy's r0 the leader's."""
    cp = latest_copy(W, r['date'])
    if cp is None:
        return None, []
    try:
        raw0, raw1, r0c = shelf_raw(cp), shelf_raw(os.path.join(W, 'SLC', r['date'])), shelf_r0(cp)
    except Exception as e:  # noqa: BLE001
        return cp, ['its copy %s unreadable: %s: %s' % (os.path.relpath(cp, W), type(e).__name__, str(e)[:120])]
    bad = []
    if sorted(raw0) != sorted(raw1) or any(raw0[k] != raw1[k] for k in raw0 if k != 'frame'):
        bad.append('keys other than frame differ from its copy %s' % os.path.relpath(cp, W))
    if abs(r0c - r['r0_leader']) > LEADER_TOL_M:
        bad.append('its copy %s holds r0 %.4f, not the leader\'s %.4f' % (os.path.relpath(cp, W), r0c, r['r0_leader']))
    return cp, bad


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 1br: the range window from the CEOS image records')
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
    r_unp = P1.record(recdir, '1b', 'unpack')
    uo = (r_unp or {}).get('outputs', {})
    dates = uo.get('dates') or []
    # what the phase reads (unpack's record, the IMG-HH and LED files); the shelves it writes are checked by missing()
    fp = C.md5_obj(dict(logic=LOGIC, unpack_fp=(r_unp or {}).get('fingerprint'), dates_md5=uo.get('dates_md5'),
                        granules=granule_ids(W, dates) if not a.dryrun else None))
    if a.state:
        def missing(r):
            ds = ((r or {}).get('outputs') or {}).get('dates') or []
            return [x.get('date') for x in ds if shelf_md5(W, x.get('date')) != x.get('shelf_md5_after')] or \
                ([] if ds else ['no dates on record'])
        print(P1.state_with_outputs(recdir, PHASE, IDX, fp, missing))
        return 0

    try:
        prev = P1.record(recdir, IDX, PHASE) or {}
    except ValueError:   # an unreadable earlier record: this run's record replaces it
        prev = {}
    po = prev.get('outputs') or {}
    st = LiveStatus(recdir, PHASE, IDX, path, frame)
    P1.begin(st)
    st.rec['version'] = VERSION
    st.rec.update(fingerprint=fp, logic=LOGIC, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(unpack_fingerprint=(r_unp or {}).get('fingerprint'), dates_md5=uo.get('dates_md5'),
                              env_cfg=env['env_cfg_file'], env_cfg_md5=env['env_cfg_md5'],
                              previous=dict(verdict=prev.get('verdict'), start=prev.get('start'), writing=po.get('writing'),
                                            backup=po.get('backup')) if prev else None))
    st.write()
    print('%s  Phase 1br rwin (the range window)  p%s f%s  %s' % (VERSION, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: the frame is only read)' if a.dryrun else ''))
    if not r_unp or r_unp.get('verdict') != 'PASS' or not dates:
        st.gate('G1br.1', 'unpack PASS on record', 'FAIL', 'P1b unpack %s, %d dates' % (
            (r_unp or {}).get('verdict') or 'has no record', len(dates)))
        return st.finish()
    st.gate('G1br.1', 'unpack PASS on record', 'PASS', '%d dates%s' % (len(dates), ' (a plan)' if uo.get('planned') is not None
                                                                         and uo.get('dryrun') else ''))
    real = dates
    if a.dryrun:
        rf = P1.record(W, '1b', 'unpack') or {}
        rfo = rf.get('outputs', {})
        if rf.get('verdict') != 'PASS' or rfo.get('dryrun') or not rfo.get('dates'):
            print('   would read the CEOS records of %d dates after unpack and set each shelve\'s r0 to column 0 by its '
                  'records where they differ from the leader by one gate' % len(dates))
            st.rec['outputs'] = dict(planned=len(dates), dryrun=True, read=False)
            return st.finish('plan only (dry run)')
        real = rfo['dates']
    try:
        import isce  # noqa: F401  (ISCE's components on sys.path)
        ceos = Ceos()
        ok, ev, note = P1.env_check(env)
        st.gate('G1br.2', 'environment', 'PASS' if ok else 'ERROR', '%s, isce %s, python %s %s; CEOS definitions %s' % (
            ev, getattr(isce, '__version__', '?'), sys.executable, sys.version.split()[0], ceos.db),
            '%s at ENV_PREFIX' % env['CONDA_ENV'], note)
    except Exception as e:  # noqa: BLE001
        st.gate('G1br.2', 'environment', 'ERROR', 'ISCE\'s CEOS parser: %s: %s' % (type(e).__name__, e), env['CONDA_ENV'])
    if any(x['verdict'] == 'ERROR' for x in st.rec['gates']):
        return st.finish()

    rows = [window(ceos, W, d) for d in real]
    fmt = '   %-8s %5s %4s %4s %4s %8s %13s %11s %3s %13s  %s'
    print(fmt % ('date', 'px', 'left', 'rght', 'same', 'r1 (m)', 'shelve r0 (m)', 'col0-r0l (m)', 'k', 'r0 after (m)', 'action'))
    for r in rows:
        why = '; '.join(r[w] for w in ('why3', 'why4', 'why5') if r.get(w))
        print(fmt % (r['date'], r.get('px', '-'), r.get('left', '-'), r.get('right', '-'),
                     'yes' if r.get('same') else ('no' if 'same' in r else '-'), r.get('r1', '-'),
                     '%.4f' % r['r0'] if 'r0' in r else '-',
                     '%+.2f' % (r['col0'] - r['r0_leader']) if 'col0' in r else '-', '%+d' % r['k'] if 'k' in r else '-',
                     '%.4f' % r['target'] if 'target' in r else '-', ('FAIL: ' + why) if why else r.get('action')))
    sys.stdout.flush()
    pw = (st.rec['inputs'].get('previous') or {}).get('writing')
    for gid, key, name, thr in (('G1br.3', 'why3', 'the records of every date', 'IMG-HH and LED readable, the descriptor = unpack\'s; '
                                 'first, middle, last agree; no fill'),
                                ('G1br.4', 'why4', 'the shelve r0 of every date', 'the leader\'s (0.01 m) or already the target'),
                                ('G1br.5', 'why5', 'one whole gate or none', '|column 0 - r0_leader - k x 149.896229 m| <= 1 m, '
                                 '|k| <= %d' % KMAX)):
        bad = ['%s: %s' % (r['date'], r[key]) for r in rows if r.get(key)]
        if gid == 'G1br.4' and pw:
            bad.append('(the previous run, %s from %s, stopped while writing %s; that date\'s copy is in %s)' % (
                (st.rec['inputs']['previous'] or {}).get('verdict'), (st.rec['inputs']['previous'] or {}).get('start'), pw,
                (st.rec['inputs']['previous'] or {}).get('backup')))
        nbad = sum(1 for r in rows if r.get(key))
        st.gate(gid, name, 'FAIL' if nbad else 'PASS', '%d of %d dates' % (len(rows) - nbad, len(rows)), thr, '\n'.join(bad))
    kc = {}
    for r in rows:
        if 'k' in r:
            kc[r['k']] = kc.get(r['k'], 0) + 1
    change = [r for r in rows if r.get('action') == 'change']
    already = [r for r in rows if r.get('action') == 'already']
    st.rec['outputs'] = dict(dates=[], k_census=dict((str(k), v) for k, v in sorted(kc.items())),
                             change=[r['date'] for r in change], already=[r['date'] for r in already])
    if any(x['verdict'] == 'FAIL' for x in st.rec['gates']):
        st.rec['outputs']['rows'] = rows
        return st.finish()
    print('   to change: %d %s; already at the records\' r0: %d %s; unchanged: %d; k: %s' % (
        len(change), ' '.join(r['date'] for r in change) or '-', len(already), ' '.join(r['date'] for r in already) or '-',
        len(rows) - len(change) - len(already), ', '.join('%+d: %d' % kv for kv in sorted(kc.items()))))
    if a.dryrun:
        st.rec['outputs'].update(planned=len(change), dryrun=True, read=True, rows=rows)
        return st.finish('plan only (dry run): %d shelves would change' % len(change))

    # the copies earlier runs made (a date written by a run that was stopped reads 'already' now; its copy is there)
    st.rec['outputs']['backups_before'] = sorted(os.path.relpath(x, W) for x in glob.glob(os.path.join(W, '_archive', 'rwin_*')))
    # G1br.6: the shelves to change, copied first
    if change:
        base = os.path.join(W, '_archive', 'rwin_%s' % time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
        bdir, i = base, 1
        while os.path.lexists(bdir):   # two runs in one second
            i += 1
            bdir = '%s_%d' % (base, i)
        os.makedirs(bdir)
        st.rec['outputs']['backup'] = os.path.relpath(bdir, W)
        bad, lines = [], []
        for r in change:
            sd, bd = os.path.join(W, 'SLC', r['date']), os.path.join(bdir, 'SLC', r['date'])
            os.makedirs(bd)
            md0 = shelf_md5(W, r['date'])
            for name in sorted(md0):
                shutil.copy2(os.path.join(sd, name), os.path.join(bd, name))
                m = C.md5_file(os.path.join(bd, name))
                lines.append('%s  SLC/%s/%s' % (m, r['date'], name))
                if m != md0[name]:
                    bad.append('%s/%s: copy md5 %s, shelve %s' % (r['date'], name, m, md0[name]))
            r['shelf_md5_before'] = md0
        with open(os.path.join(bdir, 'backup.md5'), 'w') as fh:
            fh.write('\n'.join(lines) + '\n')
        st.gate('G1br.6', 'the shelves copied first', 'FAIL' if bad else 'PASS', '%d shelves (%d files) in %s' % (
            len(change), len(lines), os.path.relpath(bdir, W)), 'md5 of each copy = the shelve\'s', '\n'.join(bad))
        if bad:
            return st.finish()
    else:
        st.gate('G1br.6', 'the shelves copied first', 'N/A', 'no shelve to change')

    # G1br.7: the writes, one date at a time; the write, its read-back and the record that names it held together
    o = st.rec['outputs']
    o.update(writing=None, written=[], written_md5={}, read_back={})
    bad = []
    for r in change:
        sd = os.path.join(W, 'SLC', r['date'])
        mark = os.environ.get('LINOG_MOCK_MARK')
        if os.environ.get('LINOG_MOCK_RWIN_PAUSE') == r['date'] and mark:
            with open(mark, 'w') as fh:
                fh.write('pausing before %s\n' % r['date'])
            time.sleep(60)
        raw0 = shelf_raw(sd)
        others = sorted(k for k in raw0 if k != 'frame')
        with Held():   # a stop waits until the shelve is written, read back and named in the record
            o['writing'] = r['date']
            st.write()
            shelf_set_r0(sd, r['target'])
            if os.environ.get('LINOG_MOCK_RWIN_HOLD') == r['date'] and mark:
                with open(mark, 'w') as fh:
                    fh.write('holding %s\n' % r['date'])
                time.sleep(5)
            raw1, back = shelf_raw(sd), shelf_r0(sd)
            same = sorted(raw0) == sorted(raw1) and all(raw0[k] == raw1[k] for k in others)
            r['shelf_md5_after'], r['read_back'], r['others_same'] = shelf_md5(W, r['date']), back, same
            o['written'].append(r['date'])
            o['written_md5'][r['date']] = r['shelf_md5_after']
            o['read_back'][r['date']] = [back, same]
            o['writing'] = None
            st.write()
        print('   %s  r0 %.4f -> %.4f (k %+d): read back %.4f; %s unchanged: %s' % (
            r['date'], r['r0'], r['target'], r['k'], back, ' and '.join(others) or 'no other key', 'yes' if same else 'NO'))
        sys.stdout.flush()
        if abs(back - r['target']) > 1e-6 or not same:
            bad.append('%s: read back %.6f, want %.6f; other keys unchanged: %s' % (r['date'], back, r['target'], same))
    st.gate('G1br.7', 'the writes', 'FAIL' if bad else ('PASS' if change else 'N/A'), '%d of %d shelves written and read back' % (
        len(o['written']) - len(bad), len(change)), 'r0 = the target; the other keys byte for byte', '\n'.join(bad))
    if bad:
        return st.finish()

    # G1br.8: every date, as it stands now; a date found already corrected, against the copy made before its change
    fin, bad, nocopy, compared = [], [], [], 0
    for r in rows:
        sd = os.path.join(W, 'SLC', r['date'])
        now = shelf_r0(sd)
        if abs(now - r['target']) > 1e-6 or abs(now - r['col0']) > TOL_M:
            bad.append('%s: r0 %.6f, target %.6f, column 0 %.2f' % (r['date'], now, r['target'], r['col0']))
        cp = None
        if r.get('action') == 'already':
            cp, probs = against_copy(W, r)
            if cp is None:
                nocopy.append(r['date'])
            else:
                compared += 1
                bad.extend('%s: %s' % (r['date'], p) for p in probs)
        fin.append(dict(date=r['date'], stem=r['stem'], img=r.get('img'), px=r.get('px'), left=r.get('left'), data=r.get('data'),
                        right=r.get('right'), r1=r.get('r1'), gate_us=r.get('gate_us'), fs_mhz=r.get('fs_mhz'),
                        r0_leader=r.get('r0_leader'), col0=r.get('col0'), k=r.get('k'), e_m=r.get('e_m'),
                        r0_before=r.get('r0'), r0_after=now, action=r.get('action'), copy=os.path.relpath(cp, W) if cp else None,
                        shelf_md5_before=r.get('shelf_md5_before'), shelf_md5_after=shelf_md5(W, r['date'])))
    st.rec['outputs']['dates'] = fin
    note = bad + (['already corrected with no copy in _archive/rwin_*/ to compare its other keys with: %s' % ' '.join(nocopy)]
                  if nocopy else [])
    st.gate('G1br.8', 'r0 = column 0 by the records', 'FAIL' if bad else ('WARN' if nocopy else 'PASS'),
            '%d of %d dates; changed %d, already %d (%d compared with their copies)' % (
                len(rows) - len(set(x.split(':')[0] for x in bad)), len(rows), len(change), len(already), compared),
            'the target within 1e-6 m; column 0 within 1 m; an already corrected date = its copy but r0', '\n'.join(note))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_rwin', main)
