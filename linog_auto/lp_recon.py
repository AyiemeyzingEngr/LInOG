#!/usr/bin/env python3
"""lp_recon.py -- linog_auto Phase 0a: reconnaissance of one path and frame.

Read-only on the archive. Granules are selected by ORBIT RESIDUE, never by folder (E63).
Each zip is opened for its central directory, summary.txt and the head of IMG-HH (its file descriptor and first image
record); v0.13 also reads the middle and last image records' 412 B prefixes by their offsets in the zip, when IMG-HH is
stored (ascending record 9.3, 13.4). Nothing is extracted. Writes recon/RECON.json, recon/RECON.md, recon/path_entry.cfg
and status/P0a_recon.json in the frame folder, or all four under --dryrun DIR.

Gates
  G0.1  CEOS decode self-test (3 positive, 5 negative controls)         ERROR if it fails
  G0.17 the path entry (v0.13, R8): a table residue = the path formula  FAIL on a mismatch; WARN on a derived entry
  G0.19 the root (v0.13): the caller's own, or named by LINOG_ROOT      FAIL otherwise, before anything is written
  G0.20 the frame folder (v0.13, the part 1 review's B1): absent, empty, or linog_auto's own (status/P0a_recon.json,
        or only the driver's status/ and logs/ and a person's recon/exclude.txt and recon/beam.txt)
                                                                        FAIL otherwise, before anything is written
  G0.2  granules on this path and frame in the archive                  FAIL if none, or a folder it cannot read
  G0.3  one copy per granule                                            DECISION if duplicated
  G0.4  every granule readable (zip, summary.txt, IMG-HH; v0.13: summary.txt's Lbi_ObservationDate a YYYYMMDD date)
                                                                        DECISION: exclude or replace
  G0.4x a person's exclusions (recon/exclude.txt) applied               INFO, WARN for a granule not found
  G0.4d (v0.13, R7, 11.4) coarse's D2 loop: the granules of recon/d2_decision.json DROPPED ("R7 (D2), loop n: ...");
        its md5 in the fingerprint when it exists                       INFO, WARN for a date not found; FAIL unreadable
  G0.5  date law (the table's anchor, or v0.13 the frame's own) = Lbi_ObservationDate   FAIL on any mismatch
  G0.6  pass direction: file suffix = path table (or frame rule) = frame-number rule    FAIL on any mismatch
  G0.7  CEOS width (record length at byte 728) = Pdi_NoOfPixels         FAIL on any mismatch
  G0.8  mode witnesses: IMG-HV member = IMG-HV in the product list      FAIL on any mismatch
  G0.9  product level H1.1; other products dropped and listed           INFO
  G1    beam: modal off-nadir; granules beyond the tolerance dropped    PASS, drops listed
  G0.18 the beam guard (v0.13, R8-e): the modal beam one linog_auto has run (beams_run), or accepted in
        recon/beam.txt                                                  DECISION otherwise, nothing dropped
  G0.16 the framing check (v0.13, 9.3 with R8-c): field (c) along the cell's own track; a granule beyond
        framing_max_km DROPPED (R6-b); unusable fields, the cross-check, across track, the anchor or the share  DECISION
  G0.16a the anchor by the frame law beside the table's (v0.13)         WARN beyond framing_law_check_km
  G0.10 mode mix -> branch FBS-only, FBS+FBD or FBD-only               INFO
  G0.11 widths per mode; off-modal widths counted in range gates        INFO, WARN if not whole gates
  G0.12 kept dates                                                      FAIL < min_dates, WARN < warn_dates
  G0.13 in-path count against the path table's expectation             WARN on mismatch
  G0.14 DEM covers the footprint with the margin (v0.13: the footprint from the kept granules' own CEOS corners,
        the table's bbox_<frame> beside it)                            FAIL; WARN; DECISION on unusable corners
  G0.15 free disk for the kept dates                                    FAIL if short

Human decisions go in <frame>/recon/exclude.txt, one granule per line with a reason:
    ALPSRP<orbit><frame>  <reason>
and (v0.13) in <frame>/recon/beam.txt, one line: <degrees> <reason>, to accept a modal beam beams_run lacks.
They enter the fingerprint and RECON.json. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION. v0.13: an unexpected error or a
stop (SIGINT, SIGTERM, SIGHUP unless ignored) after the record is written ends it ERROR (gate ERR), exit 3.
--rootcheck (v0.13, for the driver and the path runner): G0.19 alone, printed; writes nothing; exit 0 PASS, 2 FAIL.
--framecheck (v0.13): G0.20 alone, printed; writes nothing; exit 0 PASS, 2 FAIL. Both flags together (the driver,
before it makes the frame's status/ and logs/): both gates printed, exit 2 when either FAILs.
Self-test only (under a path table other than the package's own): LINOG_MOCK_RECON_RAISE=1 raises an error after G0.2
(M34d: the record ends ERROR).
"""
import argparse
import collections
import datetime
import json
import math
import os
import pwd
import re
import shutil
import signal
import statistics
import struct
import sys
import traceback
import zipfile

import lp_common as C

STRICT = re.compile(r'^ALPSRP(\d{5})(\d{4})-([A-Z]\d\.\d)__([AD])\.zip$')
LOOSE = re.compile(r'^ALPSRP(\d{5})(\d{4})')
REC_PREFIX, BPS, CEOS_OFF, NMIN, NMAX = 412, 8, 728, 1000, 20000
FDR_LEN = 720                                   # the IMG file descriptor record
HEAD = 4096                                     # the head of IMG-HH read through zipfile (descriptor, first record)
ORB_CYCLE, DAY_CYCLE = 671, 46
GATE_SAMPLES = {'FBS': 32, 'FBD': 16}          # one ALOS range gate in each mode's samples
BYTES = {'Int16': 2, 'Float32': 4, 'Int32': 4, 'Float64': 8}
TOOLS = ('lp_recon.py', 'lp_common.py')
CURRENT = {}                                    # the run's Status once written (crash() ends it ERROR)
DATE8 = re.compile(r'^\d{8}$')
# the image record's prefix by offset (ISCE's image_record.xml; RA2's REC): B4 big-endian; positions read signed
REC_FIELDS = (('rec_len', 8, 'u'), ('line', 12, 'u'), ('year', 36, 'u'), ('doy', 40, 'u'), ('ms', 44, 'u'),
              ('lat_first', 192, 's'), ('lat_centre', 196, 's'), ('lat_last', 200, 's'),
              ('lon_first', 204, 's'), ('lon_centre', 208, 's'), ('lon_last', 212, 's'))
# WGS84 (9.3's geometry, as s9_framing.py v3 and r8_desk.py)
EA, EF = 6378137.0, 1 / 298.257223563
E2 = EF * (2 - EF)
dir_by_frame = C.dir_by_frame                   # v0.13: the frame rule lives in lp_common.py (R8)


# ------------------------------------------------------------------ decode --
def nsamp(reclen):
    if reclen is None or (reclen - REC_PREFIX) % BPS:
        return None
    n = (reclen - REC_PREFIX) // BPS
    return n if NMIN <= n <= NMAX else None


def selftest():
    """Rule 19: prove the decode before any real byte uses it (as linog_preflight_summary.py)."""
    ok = 0
    for reclen, want in ((0x0001259C, 9344), (0x0001269C, 9376), (0x0000929C, 4640)):
        ok += nsamp(reclen) == want
    for reclen in (0, 1, 0xFFFFFFFF, REC_PREFIX + BPS * (NMAX + 1), REC_PREFIX + 3):
        ok += nsamp(reclen) is None
    return ok == 8, ok


def date_law(orbit, ed, eo):
    d = orbit - eo
    if d % ORB_CYCLE:
        return None
    base = datetime.date(int(ed[:4]), int(ed[4:6]), int(ed[6:8]))
    return (base + datetime.timedelta(days=DAY_CYCLE * (d // ORB_CYCLE))).strftime('%Y%m%d')


def modal(values):
    """Deterministic tie-break (N50): highest count, then smallest value."""
    c = collections.Counter(values)
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else None


def parse_summary(text):
    out = {}
    for line in text.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            out[k.strip().strip('"')] = v.strip().strip('"')
    return out


def valid_date8(d):
    """v0.13: d is a YYYYMMDD calendar date."""
    if not isinstance(d, str) or not DATE8.match(d):
        return False
    try:
        datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
    except ValueError:
        return False
    return True


def as_float(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def as_int(s):
    try:
        return int(float(str(s).strip()))
    except (TypeError, ValueError):
        return None


def ascii_int(b, o, n):
    try:
        return int(b[o:o + n].decode('ascii', 'replace').strip())
    except (ValueError, IndexError):
        return None


def rec_fields(b, at=0):
    """The image record's prefix fields from bytes b at offset at (None where b is short)."""
    out = {}
    for k, o, kind in REC_FIELDS:
        q = at + o
        if len(b) < q + 4:
            out[k] = None
        else:
            out[k] = struct.unpack('>i' if kind == 's' else '>I', b[q:q + 4])[0]
    return out


def member_data_offset(raw, zi):
    """Where a member's data starts in the zip file: its local header (30 B), name and extra field (as ra2.py)."""
    raw.seek(zi.header_offset)
    h = raw.read(30)
    if len(h) != 30 or h[:4] != b'PK\x03\x04':
        raise ValueError('no local header at %d' % zi.header_offset)
    n, m = struct.unpack('<HH', h[26:30])
    return zi.header_offset + 30 + n + m


def records_by_offset(raw, d0, l1, rl, nrec, size=None):
    """The middle (index floor(nrec/2)) and last (nrec - 1) records' prefixes, REC_PREFIX bytes each, by a seek in the
    zip file itself (13.4: not through zipfile's seek, which may read and discard up to the record). v0.13 (the part 1
    review's n3): with the member's size, a record whose prefix would end beyond the member raises ValueError (a short
    member would otherwise give the next member's bytes)."""
    out = {}
    for key, idx in (('mid', nrec // 2), ('last', nrec - 1)):
        if size is not None and l1 + idx * rl + REC_PREFIX > size:
            raise ValueError('record %d (%s) at byte %d is beyond the member (%d B; the descriptor gives %d records of %d B)'
                             % (idx, key, l1 + idx * rl, size, nrec, rl))
        raw.seek(d0 + l1 + idx * rl)
        out[key] = (idx, raw.read(REC_PREFIX))
    return out


# ------------------------------------------------------------------- inputs --
def read_excl(path):
    if not os.path.exists(path):
        return {}, None
    out = {}
    for line in open(path, errors='replace'):
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        out[parts[0][:15]] = parts[1] if len(parts) > 1 else '(no reason given)'
    return out, C.md5_file(path)


def read_beam(path):
    """recon/beam.txt (v0.13, G0.18): one line '<degrees> <reason>'; (degrees or None, reason, md5) or (None, None, None)."""
    if not os.path.exists(path):
        return None, None, None
    deg, why = None, ''
    for line in open(path, errors='replace'):
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        deg, why = as_float(parts[0]), parts[1] if len(parts) > 1 else ''
        break
    return deg, why, C.md5_file(path)


def scan(archive, frame, residue):
    """Every in-path zip of the frame; v0.13: the folders os.walk could not read, named (G0.2 FAILs on them)."""
    hits, offpath, frames_here, res_here, loose, unread = [], 0, collections.Counter(), collections.Counter(), 0, []
    for root, dirs, files in os.walk(archive, onerror=lambda e: unread.append('%s (%s)' % (e.filename, e.strerror))):
        for n in files:
            m = STRICT.match(n)
            if not m:
                if LOOSE.match(n) and LOOSE.match(n).group(2) == frame:
                    loose += 1
                continue
            orb, frm = int(m.group(1)), m.group(2)
            if orb % ORB_CYCLE == residue:
                frames_here[frm] += 1
            if frm == frame:
                res_here[orb % ORB_CYCLE] += 1
            if frm != frame:
                continue
            if orb % ORB_CYCLE != residue:
                offpath += 1
                continue
            p = os.path.join(root, n)
            try:
                s = os.stat(p)
                size, mtime = s.st_size, int(s.st_mtime)
            except OSError:
                size, mtime = -1, -1
            hits.append(dict(scene=n[:15], name=n, zip=p, orbit=orb, product=m.group(3),
                             suffix=m.group(4), size=size, mtime=mtime))
    hits.sort(key=lambda h: (h['orbit'], h['zip']))
    return hits, offpath, frames_here, res_here, loose, sorted(unread)


def read_granule(h):
    r = dict(h, err=[], date_summary=None, time_utc=None, offnadir=None, pdi_px=None, lines=None,
             nsamp=None, hv_member=None, hv_listed=None, members=None, img=None)
    raw = None
    try:
        raw = open(h['zip'], 'rb')
        zf = zipfile.ZipFile(raw)
    except Exception as e:  # noqa: BLE001
        if raw is not None:   # v0.13 (n5): a corrupt zip's file closed here, not at garbage collection
            raw.close()
        r['err'].append('cannot open zip: %s' % e)
        return r
    with raw, zf:
        infos = zf.infolist()
        names = [zi.filename for zi in infos]
        r['members'] = len(names)
        base = [os.path.basename(x.rstrip('/')) for x in names]
        smy = [zi for zi, b in zip(infos, base) if b.lower().startswith('summary')]
        hh = [zi for zi, b in zip(infos, base) if b.upper().startswith('IMG-HH')]
        r['hv_member'] = any(b.upper().startswith('IMG-HV') for b in base)
        kv = {}
        if smy:
            try:
                kv = parse_summary(zf.read(smy[0]).decode('latin-1'))
            except Exception as e:  # noqa: BLE001
                r['err'].append('summary.txt unreadable: %s' % e)
        else:
            r['err'].append('no summary.txt')
        r['date_summary'] = kv.get('Lbi_ObservationDate')
        if smy and not r['err']:   # v0.13 (the part 1 review's M2): G0.5, G0.12 and the date law need a date; none is a G0.4 case
            if r['date_summary'] is None:
                r['err'].append('summary.txt gives no Lbi_ObservationDate')
            elif not valid_date8(r['date_summary']):
                r['err'].append('summary.txt\'s Lbi_ObservationDate "%s" is not a date (YYYYMMDD)' % r['date_summary'])
        t = kv.get('Img_SceneCenterDateTime', '')
        r['time_utc'] = t.split()[1][:8] if len(t.split()) > 1 else None
        r['offnadir'] = as_float(kv.get('Img_OffNadirAngle'))
        r['pdi_px'] = as_int(kv.get('Pdi_NoOfPixels'))
        r['lines'] = as_int(kv.get('Pdi_NoOfLines'))
        r['hv_listed'] = any('IMG-HV' in str(v).upper() for k, v in kv.items()
                             if k.startswith('Pdi_L15ProductFileName'))
        if not hh:
            r['err'].append('no IMG-HH member')
        else:
            zi = hh[0]
            g = dict(stored=zi.compress_type == zipfile.ZIP_STORED and not zi.flag_bits & 1, compress=zi.compress_type,
                     encrypted=bool(zi.flag_bits & 1), size=zi.file_size, nrec=None, rl=None, npix=None,
                     first=None, mid=None, last=None, direct=None)
            r['img'] = g
            try:
                with zf.open(zi) as fh:
                    head = fh.read(HEAD)
                if len(head) < CEOS_OFF + 4:
                    r['err'].append('IMG-HH shorter than %d bytes' % (CEOS_OFF + 4))
                else:
                    reclen = struct.unpack('>I', head[CEOS_OFF:CEOS_OFF + 4])[0]
                    r['nsamp'] = nsamp(reclen)
                    if r['nsamp'] is None:
                        r['err'].append('CEOS record length %d implausible' % reclen)
                    l1 = struct.unpack('>I', head[8:12])[0]
                    g.update(nrec=ascii_int(head, 180, 6), rl=ascii_int(head, 186, 6), npix=ascii_int(head, 248, 8), l1=l1)
                    if l1 + REC_PREFIX <= len(head):
                        g['first'] = dict(rec_fields(head, l1), idx=0)
            except Exception as e:  # noqa: BLE001
                r['err'].append('IMG-HH unreadable: %s' % e)
            # v0.13: the middle and last records by offset, only from a stored member (the fields are G0.16's and
            # G0.14's; a failure here makes them unusable there, not the granule unreadable)
            if g['stored'] and g['first'] and not (g['nrec'] and g['rl'] and g.get('l1')):
                g['offset_error'] = 'the file descriptor gives no record count (%s) or record length (%s)' % (g['nrec'], g['rl'])
            if g['stored'] and g['first'] and g['nrec'] and g['rl'] and g.get('l1'):
                try:
                    d0 = member_data_offset(raw, zi)
                    raw.seek(d0)
                    g['direct'] = raw.read(len(head)) == head
                    l1 = g['first'].get('line')
                    for key, (idx, b) in records_by_offset(raw, d0, g['l1'], g['rl'], g['nrec'], zi.file_size).items():
                        f = dict(rec_fields(b), idx=idx)
                        f['aligned'] = (len(b) == REC_PREFIX and f.get('rec_len') == g['rl'] and isinstance(l1, int)
                                        and f.get('line') == l1 + idx)
                        g[key] = f
                except Exception as e:  # noqa: BLE001
                    g['direct'] = False
                    g['offset_error'] = '%s: %s' % (type(e).__name__, e)
    r['mode'] = 'FBD' if r['hv_member'] else 'FBS'
    return r


def dem_info(dem):
    """Extent from the DEM's .vrt, and whether the binary's size matches it."""
    out = dict(path=dem, ok=False, why='')
    vrt = dem + '.vrt'
    for f in (dem, vrt, dem + '.xml'):
        if not os.path.exists(f):
            out['why'] = 'missing %s' % f
            return out
    t = open(vrt, errors='replace').read()
    m = re.search(r'rasterXSize="(\d+)"\s+rasterYSize="(\d+)"', t)
    g = re.search(r'<GeoTransform>([^<]+)</GeoTransform>', t)
    d = re.search(r'dataType="(\w+)"', t)
    if not (m and g and d):
        out['why'] = 'cannot read size, GeoTransform or dataType from %s' % vrt
        return out
    X, Y = int(m.group(1)), int(m.group(2))
    x0, dx, _r1, y0, _r2, dy = [float(v) for v in g.group(1).split(',')]
    size = os.path.getsize(dem)
    want = X * Y * BYTES.get(d.group(1), 0)
    out.update(X=X, Y=Y, dtype=d.group(1), size=size, size_expected=want,
               W=x0, E=x0 + dx * X, N=y0, S=y0 + dy * Y, vrt_md5=C.md5_file(vrt))
    if size != want:
        out['why'] = 'binary is %d B, the .vrt describes %d B' % (size, want)
        return out
    out['ok'] = True
    return out


def dem_fingerprint(dem):
    try:
        return [dem, os.path.getsize(dem), C.md5_file(dem + '.vrt')]
    except OSError:
        return [dem, None, None]


def disk_free_gib(path):
    p = os.path.abspath(path)
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return shutil.disk_usage(p).free / 2.0 ** 30, p


# ------------------------------------------------------------ the root (G0.19) --
def root_check(cfg):
    """v0.13 (12.3 item 2): the root is the caller's own (its owner, or where it does not exist yet its nearest existing
    folder's, is the caller's effective uid), unless LINOG_ROOT names it. (verdict, value, threshold)."""
    root = cfg['root']
    if os.environ.get('LINOG_ROOT'):
        return 'PASS', 'LINOG_ROOT names it: %s' % root, "the caller's own, or LINOG_ROOT"
    p = os.path.abspath(root)
    while not os.path.lexists(p):
        p = os.path.dirname(p)
    st = os.stat(p)

    def name(uid):
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return 'uid %d' % uid
    me = os.geteuid()
    where = root if p == os.path.abspath(root) else '%s (not there yet; its nearest folder %s)' % (root, p)
    if st.st_uid == me:
        return 'PASS', 'the path table\'s root %s belongs to %s, the caller' % (where, name(me)), \
            "the caller's own, or LINOG_ROOT"
    return 'FAIL', ('the path table\'s root %s belongs to %s, not to the caller %s: set LINOG_ROOT to a root of your own '
                    '(a run stops here; nothing is written into the root)' % (where, name(st.st_uid), name(me))), \
        "the caller's own, or LINOG_ROOT"


# ------------------------------------------------------- the frame folder (G0.20) --
DRIVER_LINE = re.compile(r'^\S+  auto_\S+ ')            # logs/STATUS.txt's lines from linog_auto.sh (auto_run, auto_<phase>)
DRIVER_LOG = re.compile(r'^auto_P\w+_\w+\.log(\.v?\d+)?$')   # the driver's console copy of a phase (logs/auto_P0a_recon.log)
PERSON_RECON = ('exclude.txt', 'beam.txt')              # a person's decisions, which may come before recon's first run


def frame_check(W):
    """v0.13 (the part 1 review's B1): linog_auto writes only into a frame folder it made. PASS when W is not there yet, is
    empty, holds status/P0a_recon.json (recon's record: the first file a run writes after the driver's own), or holds only
    what the driver writes before recon's record (status/.lock and restart files, logs/STATUS.txt with nothing but the
    driver's auto_ lines, logs/auto_P*.log) and a person's recon/exclude.txt or recon/beam.txt. Any other folder is
    another tool's (the course kit's 12 delivered ascending frames sit at <root>/p<path>/f<frame>, linog_auto's own
    frame folders): FAIL, naming what is there. (verdict, value, threshold)"""
    thr = "absent, empty, or linog_auto's own (status/P0a_recon.json)"
    if not os.path.lexists(W):
        return 'PASS', '%s is not there yet' % W, thr
    if os.path.islink(W) or not os.path.isdir(W):
        return 'FAIL', ('%s is %s, not a folder linog_auto made: a run stops here; nothing is written'
                        % (W, 'a link' if os.path.islink(W) else 'not a folder')), thr
    if os.path.isfile(os.path.join(W, 'status', 'P0a_recon.json')):
        return 'PASS', "%s is linog_auto's own (status/P0a_recon.json)" % W, thr
    other = []
    try:
        for n in sorted(os.listdir(W)):
            q = os.path.join(W, n)
            if n not in ('status', 'logs', 'recon') or os.path.islink(q) or not os.path.isdir(q):
                other.append(n + ('/' if os.path.isdir(q) and not os.path.islink(q) else ''))
                continue
            for m in sorted(os.listdir(q)):
                qm = os.path.join(q, m)
                ok = os.path.isfile(qm) and not os.path.islink(qm) and (
                    (n == 'status' and (m == '.lock' or (m.startswith('restart') and m.endswith('.json'))))
                    or (n == 'logs' and DRIVER_LOG.match(m) is not None)
                    or (n == 'recon' and m in PERSON_RECON))
                if n == 'logs' and m == 'STATUS.txt' and os.path.isfile(qm) and not os.path.islink(qm):
                    with open(qm, errors='replace') as fh:
                        ok = all(DRIVER_LINE.match(ln) for ln in fh if ln.strip())
                if not ok:
                    other.append('%s/%s' % (n, m))
    except OSError as e:
        return 'FAIL', 'cannot list %s (%s): a run stops here; nothing is written' % (W, e), thr
    if not other:
        return 'PASS', ("%s holds only the driver's status/ and logs/ (or a person's recon/exclude.txt, beam.txt), no "
                        "recon record yet" % W), thr
    return 'FAIL', ('%s holds files linog_auto did not write (%s%s) and no status/P0a_recon.json: another tool made this '
                    'folder (the course kit\'s delivered frames sit at the default frame folders). linog_auto writes only into '
                    'its own frame folders: set LINOG_ROOT to a root of your own, or move this folder aside on its owner\'s '
                    'word (a run stops here; nothing is written)' % (W, ', '.join(other[:6]),
                                                                     ' and %d more' % (len(other) - 6) if len(other) > 6 else '')), thr


# ----------------------------------------------------------- the derived law --
def derived_law(live, residue):
    """R8 (13.4): each live granule's summary date carried back to its residue's first cycle (46 days less per 671
    orbits); the mode, when more than half the live granules share it, is the law, recorded as the earliest granule on
    it. Returns (law or None, {scene: first-cycle date or None}, anchor granule or None)."""
    first = {}
    for r in live:
        d = r.get('date_summary') or ''
        v = None
        if DATE8.match(d):
            try:
                v = (datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
                     - datetime.timedelta(days=DAY_CYCLE * ((r['orbit'] - residue) // ORB_CYCLE)))
            except ValueError:
                v = None
        first[r['scene']] = v
    c = collections.Counter(v for v in first.values() if v is not None)
    if not c:
        return None, first, None
    law, n = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    if 2 * n <= len(live):
        return None, first, None
    on = sorted((r for r in live if first[r['scene']] == law), key=lambda r: r['orbit'])
    return law, first, on[0]


# -------------------------------------------------------------- the geometry --
def ecef(lat, lon):
    p, l = math.radians(lat), math.radians(lon)
    n = EA / math.sqrt(1 - E2 * math.sin(p) ** 2)
    return n * math.cos(p) * math.cos(l), n * math.cos(p) * math.sin(l), n * (1 - E2) * math.sin(p)


def en(lat, lon, o):
    """East and north of (lat, lon) from the origin o, m (WGS84 to ECEF, rotated to ENU at o, up dropped)."""
    x, y, z = ecef(lat, lon)
    x0, y0, z0 = ecef(*o)
    dx, dy, dz = x - x0, y - y0, z - z0
    p, l = math.radians(o[0]), math.radians(o[1])
    return (-math.sin(l) * dx + math.cos(l) * dy,
            -math.sin(p) * math.cos(l) * dx - math.sin(p) * math.sin(l) * dy + math.cos(p) * dz)


def unit(h):
    return math.sin(math.radians(h)), math.cos(math.radians(h))


def dot(p, w):
    return p[0] * w[0] + p[1] * w[1]


def circ_median(hs):
    """The median heading, taken about the circular mean (equal to the plain median where no heading crosses north)."""
    m = math.degrees(math.atan2(sum(math.sin(math.radians(h)) for h in hs), sum(math.cos(math.radians(h)) for h in hs)))
    return (m + statistics.median(((h - m + 180.0) % 360.0) - 180.0 for h in hs)) % 360.0


def rec_time(f):
    """A record's acquisition time as a datetime, or None when year or day is not present."""
    if not f or not f.get('year') or not f.get('doy') or not 1 <= f['doy'] <= 366 or f.get('ms') is None:
        return None
    try:
        return datetime.datetime(f['year'], 1, 1) + datetime.timedelta(days=f['doy'] - 1, milliseconds=f['ms'])
    except (ValueError, OverflowError):
        return None


def centre(f):
    return (f['lat_centre'] / 1e6, f['lon_centre'] / 1e6)


def law_for(cfg, frame, direction):
    """The frame law for this frame's direction when the frame lies in its range: (intercept, slope, fmin, fmax)."""
    v = cfg.get('framing_law_' + direction.lower())   # configparser lowercases the keys: framing_law_A is framing_law_a
    if not v:
        return None
    a, b, f0, f1 = [float(x) for x in v.split()]
    return (a, b, f0, f1) if f0 <= int(frame) <= f1 else None


def framing(live, cfg, frame, direction, beam, tol):
    """G0.16 (9.3 with R8-c): returns dict(verdict, value, note, drops, record, law_beside)."""
    nmin = int(cfg.get('min_dates', 5))
    fmax, fshare = float(cfg.get('framing_max_km', 11.27)), float(cfg.get('framing_max_share', 0.25))
    fanchor, fbc = float(cfg.get('framing_anchor_km', 5.64)), float(cfg.get('framing_bc_max_km', 0.1))
    fxt, band_law = float(cfg.get('framing_xt_max_km', 10)), float(cfg.get('framing_law_band_deg', 0.82))
    lbeam = float(cfg.get('framing_law_beam', 34.3))
    out = dict(verdict='PASS', value='', note='', drops=[], record=dict(granules={}, cell={}), law_beside=None)
    bb = cfg.get('bbox_' + frame)
    bb = [float(x) for x in bb.split()] if bb else None
    law = law_for(cfg, frame, direction)
    law_ok = law is not None and beam is not None and abs(beam - lbeam) <= tol
    lat_law = law[0] + law[1] * int(frame) if law_ok else None
    src = 'table' if bb else 'law' if law_ok else 'none'
    out['record']['cell'].update(anchor_source=src, n_kept=len(live), lat_law=lat_law, bbox=bb)
    if len(live) < nmin:
        out.update(verdict='INFO', value='not judged: %d kept, fewer than min_dates %d (G0.12 decides)' % (len(live), nmin))
        return out
    # step 2: usable on every kept granule
    bad = []
    for r in live:
        g, why = r.get('img') or {}, []
        if not g.get('stored'):
            why.append('IMG-HH not stored (compress type %s%s)' % (g.get('compress'), ', encrypted' if g.get('encrypted') else ''))
        elif not g.get('direct'):
            why.append('IMG-HH not read by offset (%s)' % g.get('offset_error', 'its head read by offset differs from zipfile\'s'))
        f, m = g.get('first') or {}, g.get('mid') or {}
        if g.get('stored') and g.get('direct') and not m.get('aligned'):
            why.append('middle record not aligned (length %s line %s, descriptor %s, first line %s + %s)' % (
                m.get('rec_len'), m.get('line'), g.get('rl'), f.get('line'), m.get('idx')))
        if not why:
            if not all((f.get('lat_centre'), f.get('lon_centre'), m.get('lat_centre'), m.get('lon_centre'))):
                why.append('a position field is zero ((b) %s %s, (c) %s %s)' % (f.get('lat_centre'), f.get('lon_centre'),
                                                                                m.get('lat_centre'), m.get('lon_centre')))
            tb, tc = rec_time(f), rec_time(m)
            if tb is None or tc is None:
                why.append('an acquisition time not present')
            elif tc <= tb:
                why.append('(c)\'s time %s not later than (b)\'s %s' % (tc, tb))
            if not why:
                pb, pc = centre(f), centre(m)
                if bb and not all(bb[0] - 0.5 <= p[0] <= bb[1] + 0.5 and bb[2] - 0.5 <= p[1] <= bb[3] + 0.5 for p in (pb, pc)):
                    why.append('(b) %.4f %.4f or (c) %.4f %.4f outside the footprint +-0.5 deg' % (pb + pc))
                elif src == 'law' and not all(abs(p[0] - lat_law) <= band_law for p in (pb, pc)):
                    why.append('(b) %.4f or (c) %.4f N beyond +-%.2f deg of the frame law\'s latitude %.4f' % (
                        pb[0], pc[0], band_law, lat_law))
        if why:
            bad.append((r['name'], '; '.join(why)))
    if bad:
        out.update(verdict='DECISION', value='step 2: %d of %d kept granules unusable' % (len(bad), len(live)),
                   note='\n'.join('%s: %s' % x for x in bad) + '\nnothing dropped: exclude each in recon/exclude.txt with a '
                   'reason after checking its framing, or replace the zip; then re-run')
        out['record']['cell']['step'] = 2
        return out
    # the geometry, over the kept granules as G1 left them (the medians taken once)
    o = (statistics.median(centre(r['img']['mid'])[0] for r in live), statistics.median(centre(r['img']['mid'])[1] for r in live))
    v = {}
    for r in live:
        f, m = r['img']['first'], r['img']['mid']
        b, c = en(*centre(f), o), en(*centre(m), o)
        v[r['scene']] = dict(b=b, c=c, dt=(rec_time(m) - rec_time(f)).total_seconds(),
                             h=math.degrees(math.atan2(c[0] - b[0], c[1] - b[1])) % 360)
    H = circ_median([x['h'] for x in v.values()])
    u, nv = unit(H), (math.cos(math.radians(H)), -math.sin(math.radians(H)))
    for x in v.values():
        x['s_c'], x['s_b'], x['x'] = dot(x['c'], u), dot(x['b'], u), dot(x['c'], nv)
        x['vel'] = (x['s_c'] - x['s_b']) / x['dt']
    med = {k: statistics.median(x[k] for x in v.values()) for k in ('s_c', 's_b', 'x', 'vel', 'dt')}
    for x in v.values():
        x['dev_c'], x['dev_b'] = (x['s_c'] - med['s_c']) / 1e3, (x['s_b'] - med['s_b']) / 1e3
        x['dx'], x['dv'] = (x['x'] - med['x']) / 1e3, (x['vel'] - med['vel']) * med['dt'] / 1e3
    anchor = anchor_x = a_law = None
    if bb:
        fc = en((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, o)
        anchor, anchor_x = (med['s_c'] - dot(fc, u)) / 1e3, (med['x'] - dot(fc, nv)) / 1e3
    if law_ok:
        a_law = (med['s_c'] - en(lat_law, o[1], o)[1] / math.cos(math.radians(H))) / 1e3
        if src == 'law':
            anchor = a_law
        elif bb:
            out['law_beside'] = (a_law, anchor)
    rec = out['record']
    for r in live:
        x = v[r['scene']]
        rec['granules'][r['scene']] = dict(mode=r['mode'], b=list(centre(r['img']['first'])), c=list(centre(r['img']['mid'])),
                                           heading_deg=round(x['h'], 4), dev_c_km=round(x['dev_c'], 4),
                                           dev_b_km=round(x['dev_b'], 4), dv_km=round(x['dv'], 5), dx_km=round(x['dx'], 4),
                                           span_s=round(x['dt'], 3))
    rec['cell'].update(origin=[round(o[0], 6), round(o[1], 6)], heading_deg=round(H, 4),
                       anchor_km=None if anchor is None else round(anchor, 4),
                       anchor_across_km=None if anchor_x is None else round(anchor_x, 4),
                       anchor_law_km=None if a_law is None else round(a_law, 4),
                       median_speed_km_s=round(med['vel'] / 1e3, 6), median_span_s=round(med['dt'], 4))
    byname = {r['scene']: r['name'] for r in live}
    big = max(v, key=lambda s: abs(v[s]['dev_c']))
    summary = 'heading %.2f deg, origin %.4f %.4f; largest |dev_c| %.3f km (%s)' % (H, o[0], o[1], abs(v[big]['dev_c']), big)
    # step 3: the cross-check
    s3 = sorted(s for s, x in v.items() if abs(x['dv']) > fbc)
    if s3:
        out.update(verdict='DECISION', value='step 3: %d granules\' position fields disagree with their times (|dv| > %.2f km)'
                   % (len(s3), fbc), note='\n'.join('%s dv %+.4f km dev_c %+.3f km' % (byname[s], v[s]['dv'], v[s]['dev_c'])
                                                    for s in s3) + '\n' + summary)
        rec['cell']['step'] = 3
        return out
    # step 4: across track
    s4 = sorted(s for s, x in v.items() if abs(x['dx']) > fxt)
    if s4:
        out.update(verdict='DECISION', value='step 4: %d granules beyond %.1f km across track' % (len(s4), fxt),
                   note='\n'.join('%s dx %+.3f km' % (byname[s], v[s]['dx']) for s in s4) + '\n' + summary)
        rec['cell']['step'] = 4
        return out
    beyond = sorted(s for s, x in v.items() if abs(x['dev_c']) > fmax)
    lst = '\n'.join('%s dev_c %+.3f km dev_b %+.3f km' % (byname[s], v[s]['dev_c'], v[s]['dev_b']) for s in beyond)
    # step 5: the anchor
    if src == 'none':
        rec['cell']['step'] = 5
        if beyond:
            out.update(verdict='DECISION', value='step 5: no footprint and no frame law here (anchor not read); %d granules '
                       'beyond %.2f km named, nothing dropped' % (len(beyond), fmax), note=lst + '\n' + summary)
        else:
            out.update(verdict='PASS', value='no footprint and no frame law here (anchor not read, INFO); none beyond %.2f km; %s'
                       % (fmax, summary))
        return out
    if abs(anchor) > fanchor:
        out.update(verdict='DECISION', value='step 5: the anchor %+.3f km (%s) beyond %.2f km: the median may not be the frame\'s'
                   % (anchor, src, fanchor), note=summary + '\nnothing dropped' + ('\n' + lst if lst else ''))
        rec['cell']['step'] = 5
        return out
    # step 6: the share
    if beyond and len(beyond) / float(len(live)) > fshare:
        out.update(verdict='DECISION', value='step 6: %d of %d kept granules beyond %.2f km (share %.3f > %.2f)' % (
            len(beyond), len(live), fmax, len(beyond) / float(len(live)), fshare), note=lst + '\n' + summary + '\nnothing dropped')
        rec['cell']['step'] = 6
        return out
    # step 7: the drops
    rec['cell']['step'] = 7
    out['drops'] = [(s, 'G0.16 framing (R6-b): dev_c %+.3f km, dev_b %+.3f km along track, beyond %.2f km'
                     % (v[s]['dev_c'], v[s]['dev_b'], fmax)) for s in beyond]
    out.update(verdict='PASS', value='%d kept, %d DROPPED; anchor %+.3f km (%s); %s' % (
        len(live) - len(beyond), len(beyond), anchor, src, summary), note=lst)
    return out


def corners_of(r, cmax):
    """The four corners (first and last pixels of the first and last records) as (lat, lon), or (None, why)."""
    g = r.get('img') or {}
    f, m, l = g.get('first') or {}, g.get('mid') or {}, g.get('last') or {}
    if not g.get('stored') or not g.get('direct'):
        return None, 'IMG-HH not stored or not read by offset'
    if not l.get('aligned'):
        return None, 'last record not aligned (length %s line %s)' % (l.get('rec_len'), l.get('line'))
    if not m.get('aligned') or not (m.get('lat_centre') and m.get('lon_centre')):
        return None, 'no usable (c)'
    cs = [(f.get('lat_first'), f.get('lon_first')), (f.get('lat_last'), f.get('lon_last')),
          (l.get('lat_first'), l.get('lon_first')), (l.get('lat_last'), l.get('lon_last'))]
    if any(not a or not b for a, b in cs):
        return None, 'a corner is zero'
    c = centre(m)
    cs = [(a / 1e6, b / 1e6) for a, b in cs]
    far = [p for p in cs if abs(p[0] - c[0]) > cmax or abs(p[1] - c[1]) > cmax]
    if far:
        return None, 'a corner %.4f %.4f more than %.2f deg from its (c) %.4f %.4f' % (far[0] + (cmax,) + c)
    return cs, ''


def footprint(live, cfg, frame, dem):
    """G0.14 v0.13 (R8-b): (verdict, value, threshold, note, record)."""
    margin = float(cfg.get('dem_margin_deg', 0.1))
    cmax, chk = float(cfg.get('footprint_corner_max_deg', 1.0)), float(cfg.get('footprint_check_deg', 0.05))
    bb = cfg.get('bbox_' + frame)
    bb = [float(x) for x in bb.split()] if bb else None
    rec = dict(footprint=None, footprint_table=bb, granules={}, unusable={}, differences=None, margins=None)
    if not dem['ok']:
        return 'FAIL', 'DEM unusable: %s' % dem['why'], '', '', rec
    usable, unusable = {}, {}
    for r in live:
        cs, why = corners_of(r, cmax)
        if cs:
            usable[r['scene']] = cs
            rec['granules'][r['scene']] = [list(p) for p in cs]
        else:
            unusable[r['name']] = why
    rec['unusable'] = unusable
    notes = []
    if usable:
        lats = [p[0] for cs in usable.values() for p in cs]
        lons = [p[1] for cs in usable.values() for p in cs]
        fp = [min(lats), max(lats), min(lons), max(lons)]
    else:
        fp = None
    rec['footprint'] = dict(SNWE=fp, granules=len(usable)) if fp else None
    warn = False
    if unusable:
        notes.append('corners not usable: ' + '; '.join('%s: %s' % kv for kv in sorted(unusable.items())))
        if not bb:
            return ('DECISION', '%d of %d kept granules\' corners unusable and no footprint in the path table' % (len(unusable), len(live)),
                    '', '\n'.join(notes) + '\nexclude each in recon/exclude.txt or replace the zip; then re-run', rec)
        warn = True
        fp = [min(fp[0], bb[0]), max(fp[1], bb[1]), min(fp[2], bb[2]), max(fp[3], bb[3])] if fp else list(bb)
        notes.append('judged on the union of the table\'s footprint and the usable granules\' corners')
    if fp is None:
        if not bb:
            return 'INFO', 'no kept granule to read corners from, no footprint in the path table', '', '', rec
        fp, warn = list(bb), True
        notes.append('no kept granule\'s corners: the table\'s footprint alone')
    m = dict(S=fp[0] - dem['S'], N=dem['N'] - fp[1], W=fp[2] - dem['W'], E=dem['E'] - fp[3])
    rec['margins'] = m
    worst = min(m.values())
    if bb and usable:
        dlt = dict(S=bb[0] - fp[0], N=fp[1] - bb[1], W=bb[2] - fp[2], E=fp[3] - bb[3])
        rec['differences'] = {k: round(x, 6) for k, x in dlt.items()}
        mt = dict(S=bb[0] - dem['S'], N=dem['N'] - bb[1], W=bb[2] - dem['W'], E=dem['E'] - bb[3])
        notes.append('the table\'s footprint %s: margins S %.3f N %.3f W %.3f E %.3f deg; the derived reaches beyond it by '
                     'S %+.4f N %+.4f W %+.4f E %+.4f deg' % (' '.join('%.3f' % x for x in bb), mt['S'], mt['N'], mt['W'],
                                                              mt['E'], dlt['S'], dlt['N'], dlt['W'], dlt['E']))
        off = [k for k, x in dlt.items() if abs(x) > chk]
        if off:
            warn = True
            notes.append('the table\'s footprint differs from the derived by more than %.2f deg on %s' % (chk, ', '.join(off)))
    verdict = 'FAIL' if worst < margin else 'WARN' if warn else 'PASS'
    value = 'margins S %.3f N %.3f W %.3f E %.3f deg (footprint %s from %d granules\' corners)' % (
        m['S'], m['N'], m['W'], m['E'], ' '.join('%.4f' % x for x in fp), len(usable))
    notes.append('DEM %.3f-%.3f N %.3f-%.3f E' % (dem['S'], dem['N'], dem['W'], dem['E']))
    return verdict, value, '>= %.2f deg on every side' % margin, '\n'.join(notes), rec


def write_entry(rd, path, frame, cfg, verdict, reason, entry, epoch, live, hits, g016, fp_rec, gate_ids):
    """recon/path_entry.cfg (R8-d, 13.4): the path's section as the table writes one, each key under its source; the
    derived footprint as a comment only. No phase reads it."""
    sec = 'p' + path
    big = max((abs(x['dev_c_km']) for x in g016['record']['granules'].values()), default=None)
    ls = ['# recon/path_entry.cfg: the path table entry recon proposes for p%s f%s (%s, %s)' % (path, frame, C.VERSION, C.utc()),
          '# recon\'s verdict: %s' % verdict]
    if verdict != 'PASS':
        ls.append('# not for the table until the gates named are settled: %s' % (reason or ', '.join(gate_ids)))
    ls += ['# a person reviews this, merges it with the path\'s other frames (one direction, residue and epoch; each frame\'s',
           '# expect_<frame>) and adds it to a copy of the table named by LINOG_AUTO_CFG, or to the next version\'s table',
           '[%s]' % sec,
           '# direction: %s' % ('the path table\'s' if entry == 'table' else 'the frame rule (D for frames 1800 to 5399, else A), '
                                'with every kept granule\'s file suffix (G0.6)'),
           'direction = %s' % cfg['direction'],
           '# residue: %s' % ('the path table\'s, equal to 248 x (%d - 85) mod 671 (G0.17)' % int(path) if entry == 'table'
                              else 'the path formula 248 x (%d - 85) mod 671 (G0.17)' % int(path)),
           'residue = %s' % cfg['residue']]
    if epoch:
        ls += ['# date law: %s' % ('the path table\'s anchor (G0.5)' if entry == 'table' else
                                   'the law of the frame\'s own granules, its earliest granule %s (G0.5)' % epoch[2]),
               'epoch_date = %s' % epoch[0], 'epoch_orbit = %d' % epoch[1]]
    else:
        ls.append('# date law: none holds a majority of the frame\'s granules (G0.5): no epoch keys')
    cell = g016['record']['cell']
    ls += ['# in-path granules of the frame in the archive, every product (G0.13): %d; kept %d; G0.16 %s, its anchor\'s source %s, '
           'largest |dev_c| %s' % (len(hits), len(live), g016['verdict'], cell.get('anchor_source'),
                                   '%.3f km' % big if big is not None else 'not read'),
           'expect_%s = %d' % (frame, len(hits))]
    fp = (fp_rec.get('footprint') or {}).get('SNWE')
    if fp:
        ls.append('# the footprint by the kept granules\' own corners, a comment only (13.2: G0.16\'s anchor never comes from the '
                  'run\'s own granules): S N W E = %s' % ' '.join('%.4f' % x for x in fp))
    p = os.path.join(rd, 'path_entry.cfg')
    with open(p + '.tmp', 'w') as fh:
        fh.write('\n'.join(ls) + '\n')
    os.replace(p + '.tmp', p)
    return p


# --------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 0a: recon (read-only on the archive)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true', help='print the state word and exit')
    ap.add_argument('--dryrun', metavar='DIR', help='write the records under DIR, not in the frame folder')
    ap.add_argument('--rootcheck', action='store_true', help='G0.19 alone (the driver, before it writes): exit 0 or 2')
    ap.add_argument('--framecheck', action='store_true', help='G0.20 alone (v0.13): exit 0 or 2; with --rootcheck both')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    if a.rootcheck or a.framecheck:
        vs = []
        if a.rootcheck:
            v, val, thr = root_check(cfg)
            print('   %-7s %-8s %-30s %s   [%s]' % ('G0.19', v, 'the root', val, thr))
            vs.append(v)
        if a.framecheck:
            v, val, thr = frame_check(W)
            print('   %-7s %-8s %-30s %s   [%s]' % ('G0.20', v, 'the frame folder', val, thr))
            vs.append(v)
        return 0 if all(v == 'PASS' for v in vs) else 2
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    fc = frame_check(W)   # v0.13 (B1): read before recon writes its record, and recorded as G0.20 after G0.19
    if not a.state and not a.dryrun:
        rv, rval, rthr = root_check(cfg)
        if rv != 'PASS':   # a real run writes its record into the root: nothing is written there (12.3, item 2)
            print('   %-7s %-8s %-30s %s   [%s]' % ('G0.19', rv, 'the root', rval, rthr))
            sys.stdout.flush()
            return 2
        if fc[0] != 'PASS':   # nor into a frame folder another tool made (the part 1 review's B1)
            print('   %-7s %-8s %-30s %s   [%s]' % ('G0.20', fc[0], 'the frame folder', fc[1], fc[2]))
            sys.stdout.flush()
            return 2
    entry = cfg['entry']
    res = int(cfg['residue'])
    ed, eo = (cfg['epoch_date'], int(cfg['epoch_orbit'])) if entry == 'table' else (None, None)
    direction = cfg['direction'].strip().upper()
    exfile = os.path.join(W, 'recon', 'exclude.txt')
    excl, exmd5 = read_excl(exfile)
    try:   # v0.13, R7 (11.4): coarse's D2 loop leaves its dates in recon/d2_decision.json
        d2dec, d2md5 = C.d2_decision(W)
        d2err = None
    except ValueError as e:
        d2dec, d2md5, d2err = None, 'unreadable', str(e)
    bfile = os.path.join(W, 'recon', 'beam.txt')
    bdeg, bwhy, bmd5 = read_beam(bfile)
    hits, offpath, frames_here, res_here, loose, unread = scan(cfg['archive'], frame, res)
    # the fingerprint holds the path's settings for this frame: another frame's bbox_, expect_ or dem_ key is left out, so a key
    # added for one frame (14.4's dem_3330) leaves the other frames' recon CURRENT (v0.13)
    own = re.compile(r'^(bbox|expect|dem)_(\d{4})$')
    fpd = dict(cfg={k: v for k, v in cfg.items() if k not in ('cfg_file', 'cfg_md5')
                    and not (own.match(k) and own.match(k).group(2) != frame)},
               tools=C.tool_md5s(*TOOLS),
               granules=[(h['name'], h['size'], h['mtime']) for h in hits], unread=unread,
               exclusions=exmd5, beam=bmd5, dem=dem_fingerprint(cfg['dem']))
    if d2md5:   # v0.13, R7: only when the file exists, so a frame without it keeps its fingerprint
        fpd['d2_decision'] = d2md5
    fp = C.md5_obj(fpd)
    if a.state:
        print(C.state(recdir, 'recon', '0a', fp))
        return 0

    st = C.Status(recdir, 'recon', '0a', path, frame)
    CURRENT['st'] = st
    st.rec.update(fingerprint=fp, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(archive=cfg['archive'], cfg_file=cfg['cfg_file'], cfg_md5=cfg['cfg_md5'], entry=entry,
                              dem=cfg['dem'], dem_key=cfg.get('dem_key'), exclusions=exfile if exmd5 else None,
                              exclusions_md5=exmd5, beam=bfile if bmd5 else None, beam_md5=bmd5, candidates=len(hits),
                              d2_decision=os.path.join(W, C.D2_DECISION) if d2md5 else None, d2_decision_md5=d2md5))
    st.write()
    print('%s  Phase 0a recon  p%s f%s  %s' % (C.VERSION, path, frame, C.utc()))
    print('   archive %s   residue %d   direction %s   %s' % (cfg['archive'], res, direction,
          'anchor %s / orbit %d' % (ed, eo) if entry == 'table' else 'entry derived (R8): the anchor from the frame\'s granules'))
    print('   records %s%s' % (recdir, '   (DRY RUN: the frame folder is not touched)' if a.dryrun else ''))

    ok, n = selftest()
    st.gate('G0.1', 'CEOS decode self-test', 'PASS' if ok else 'ERROR', '%d of 8 controls' % n, '8 of 8')
    if not ok:
        return st.finish('CEOS decode self-test failed; nothing decoded')

    formula = C.residue_of(path)
    if entry == 'table':
        if res != formula:
            st.gate('G0.17', 'the path entry', 'FAIL', 'the table\'s residue %d for path %d, the path formula gives %d'
                    % (res, int(path), formula), 'residue = 248 x (path - 85) mod 671',
                    'the table entry is wrong or names another path; recon read no granule')
            return st.finish()
        st.gate('G0.17', 'the path entry', 'PASS', 'the table\'s [p%s]: residue %d = the path formula, direction %s' % (
            path, res, direction), 'residue = 248 x (path - 85) mod 671')
    else:
        st.gate('G0.17', 'the path entry', 'WARN', 'derived (R8): the path table lacks [p%s]; residue %d by the path formula, '
                'direction %s by the frame rule (frame %s), the date law from the frame\'s granules (G0.5)' % (
                    path, res, direction, frame), 'a table entry, or R8\'s derived one',
                'recon/path_entry.cfg proposes the entry for a person to review and add to the table')

    rv, rval, rthr = root_check(cfg)
    st.gate('G0.19', 'the root', rv, rval, rthr)
    if rv != 'PASS':
        return st.finish()
    st.gate('G0.20', 'the frame folder', *fc)
    if fc[0] != 'PASS':
        return st.finish()

    if unread:
        st.gate('G0.2', 'granules in path and frame', 'FAIL', '%d folder(s) of the archive could not be read' % len(unread),
                'every folder readable, >= 1 granule', '\n'.join(unread) + '\nthe stack would miss what they hold; fix the '
                'modes (or exclude nothing silently) and re-run')
        return st.finish()
    if not hits:
        st.gate('G0.2', 'granules in path and frame', 'FAIL', 0, '>= 1',
                'frames with residue %d here: %s\nresidues with frame %s here: %s\nother-named '
                'ALPSRP entries for frame %s: %d' % (res, dict(sorted(frames_here.items())) or '{}',
                frame, dict(sorted(res_here.items())) or '{}', frame, loose))
        return st.finish()
    st.gate('G0.2', 'granules in path and frame', 'PASS', '%d in-path (%d same-frame off-path)'
            % (len(hits), offpath), '>= 1')
    if os.environ.get('LINOG_MOCK_RECON_RAISE') and C.selftest_hook('LINOG_MOCK_RECON_RAISE'):   # self-test only (M34d)
        raise RuntimeError('self-test: LINOG_MOCK_RECON_RAISE after G0.2')

    bysc = collections.defaultdict(list)
    for h in hits:
        bysc[h['scene']].append(h['zip'])
    dup = {k: v for k, v in bysc.items() if len(v) > 1}
    st.gate('G0.3', 'one copy per granule', 'DECISION' if dup else 'PASS', '%d duplicated' % len(dup), '0',
            '\n'.join('%s: %s' % (k, ', '.join(v)) for k, v in sorted(dup.items()))
            + ('\nkeep one copy: exclude the other path or move it out of the archive' if dup else ''))

    recs = [read_granule(h) for h in hits]
    unknown_excl = sorted(set(excl) - set(bysc))
    for r in recs:
        r['status'], r['reason'] = 'KEPT', ''
        if r['scene'] in excl:
            r['status'], r['reason'] = 'DROPPED', 'excluded in recon/exclude.txt: %s' % excl[r['scene']]
    if excl:
        st.gate('G0.4x', 'human exclusions', 'WARN' if unknown_excl else 'INFO',
                '%d listed, %d applied' % (len(excl), len(excl) - len(unknown_excl)), '',
                ('not in the archive for this frame: %s' % ', '.join(unknown_excl)) if unknown_excl else '')
    if d2err:   # v0.13, R7 (11.4)
        st.gate('G0.4d', 'R7\'s exclusions (D2)', 'FAIL', d2err, 'recon/d2_decision.json as coarse wrote it',
                'a person looks: the file is coarse\'s record of its D2 loop, its dates\' traces in _archive/d2_<UTC>/ (MOVES.txt names '
                'each move); to undo a loop, move the traces back by MOVES.txt before the file goes aside')
        return st.finish()
    d2d = C.d2_dates(d2dec)
    if d2d:
        bysc_d = dict((v.get('granule'), (d, v)) for d, v in d2d.items())
        found = set()
        for r in recs:
            if r['status'] == 'KEPT' and r['scene'] in bysc_d:
                d, v = bysc_d[r['scene']]
                r['status'], r['reason'] = 'DROPPED', 'R7 (D2), loop %s: %s' % (v.get('loop'), v.get('why'))
                found.add(r['scene'])
        lost = sorted('%s (%s)' % (bysc_d[g][0], g) for g in set(bysc_d) - found)
        st.gate('G0.4d', 'R7\'s exclusions (D2)', 'WARN' if lost else 'INFO', '%d date(s) over %d loop(s) of %s, %d applied' % (
            len(d2d), len((d2dec or {}).get('loops') or []), C.D2_DECISION, len(found)), 'coarse\'s D2 loop (11.4)',
            ('not among this frame\'s kept granules: %s' % ', '.join(lost)) if lost else '')
    live = [r for r in recs if r['status'] == 'KEPT']

    bad = [r for r in live if r['err']]
    st.gate('G0.4', 'readable granules', 'DECISION' if bad else 'PASS',
            '%d of %d unreadable' % (len(bad), len(live)), '0',
            '\n'.join('%s: %s' % (r['name'], '; '.join(r['err'])) for r in bad)
            + ('\nexclude each in recon/exclude.txt with a reason, or replace the zip; then re-run'
               if bad else ''))
    for r in bad:
        r['status'], r['reason'] = 'DROPPED', 'unreadable: %s' % '; '.join(r['err'])
    live = [r for r in live if not r['err']]

    derived = None
    if not live:   # v0.13 (the part 1 review's n6): nothing to check; G0.12 fails the frame
        st.gate('G0.5', 'date law = summary date', 'N/A', 'no granule left to check (G0.4 and the exclusions dropped them all)',
                'all on one 46-day law' if entry != 'table' else 'all')
        if entry != 'table':
            derived = dict(residue=res, formula='248 x (%d - 85) mod 671' % int(path), direction=direction,
                           direction_rule='frame %s: D for frames 1800 to 5399, else A' % frame,
                           law_first_cycle=None, anchor=None, off=[])
    elif entry == 'table':
        for r in live:
            r['date_law'] = date_law(r['orbit'], ed, eo)
        dl = [r for r in live if r['date_law'] is None or r['date_law'] != r['date_summary']]
        st.gate('G0.5', 'date law = summary date', 'FAIL' if dl else 'PASS',
                '%d of %d agree' % (len(live) - len(dl), len(live)), 'all',
                '\n'.join('%s law %s summary %s' % (r['name'], r['date_law'] or 'OFF-LATTICE',
                                                    r['date_summary']) for r in dl))
    else:   # derived, with granules left
        law, first, on = derived_law(live, res)
        if law is not None:
            ed, eo = on['date_summary'], on['orbit']
            for r in live:
                r['date_law'] = date_law(r['orbit'], ed, eo)
        dl = [r for r in live if law is None or first[r['scene']] != law]
        derived = dict(residue=res, formula='248 x (%d - 85) mod 671' % int(path), direction=direction,
                       direction_rule='frame %s: D for frames 1800 to 5399, else A' % frame,
                       law_first_cycle=law.strftime('%Y%m%d') if law else None,
                       anchor=dict(scene=on['scene'], date=on['date_summary'], orbit=on['orbit']) if law else None,
                       off=[r['scene'] for r in dl])
        st.gate('G0.5', 'date law = summary date', 'FAIL' if dl else 'PASS',
                ('derived: the law of %d of %d granules, anchor %s %s orbit %d' % (len(live) - len(dl), len(live), on['scene'],
                                                                                    ed, eo)) if law else
                'derived: no law holds a majority of the %d granules' % len(live), 'all on one 46-day law',
                '\n'.join('%s summary %s, first cycle %s%s' % (
                    r['name'], r['date_summary'], first[r['scene']].strftime('%Y%m%d') if first[r['scene']] else 'not a date',
                    '' if law is None else ', the law %s' % law.strftime('%Y%m%d')) for r in dl))

    fdir = C.dir_by_frame(frame)
    dd = [r for r in live if r['suffix'] != direction or fdir != direction]
    st.gate('G0.6', 'pass direction', 'FAIL' if dd else 'PASS',
            '%s %s, frame rule %s, suffixes %s' % ('path table' if entry == 'table' else 'derived (the frame rule)', direction,
                                                    fdir, dict(collections.Counter(r['suffix'] for r in live))), 'all equal',
            '\n'.join(r['name'] for r in dd))

    wd = [r for r in live if r['nsamp'] is None or r['nsamp'] != r['pdi_px']]
    st.gate('G0.7', 'CEOS width = Pdi_NoOfPixels', 'FAIL' if wd else 'PASS',
            '%d of %d agree' % (len(live) - len(wd), len(live)), 'all',
            '\n'.join('%s CEOS %s Pdi %s' % (r['name'], r['nsamp'], r['pdi_px']) for r in wd))

    hv = [r for r in live if r['hv_member'] != r['hv_listed']]
    st.gate('G0.8', 'mode witnesses agree', 'FAIL' if hv else 'PASS',
            '%d of %d agree' % (len(live) - len(hv), len(live)), 'all',
            '\n'.join('%s HV member %s, HV listed %s' % (r['name'], r['hv_member'], r['hv_listed'])
                      for r in hv))

    np_ = [r for r in live if r['product'] != 'H1.1']
    for r in np_:
        r['status'] = 'DROPPED'
        r['reason'] = 'product %s%s, not an FBS/FBD L1.1 granule' % (
            r['product'], ' (polarimetric)' if r['product'].startswith('P') else '')
    st.gate('G0.9', 'product level H1.1', 'INFO', '%d dropped' % len(np_), '',
            '\n'.join('%s: %s' % (r['name'], r['reason']) for r in np_))
    live = [r for r in live if r['product'] == 'H1.1']

    tol = float(cfg.get('offnadir_tol', 0.5))
    angles = [round(r['offnadir'], 1) for r in live if r['offnadir'] is not None]
    beam = modal(angles)
    off = [r for r in live if r['offnadir'] is None or beam is None or abs(r['offnadir'] - beam) > tol]
    for r in off:
        r['status'], r['reason'] = 'DROPPED', 'off-beam: off-nadir %s, modal %s, tolerance %.1f' % (
            r['offnadir'], beam, tol)
    live = [r for r in live if r not in off]
    st.gate('G1', 'beam (off-nadir)', 'FAIL' if beam is None else 'PASS',
            'modal %s deg, %d kept, %d dropped' % (beam, len(live), len(off)), '+/- %.1f deg' % tol,
            '\n'.join('%s: %s' % (r['name'], r['reason']) for r in off))

    beams = [float(x) for x in str(cfg.get('beams_run', '34.3')).replace(',', ' ').split()]
    beam_rec = dict(modal=beam, beams_run=beams, accepted_by=None, file=bdeg, file_reason=bwhy)
    if beam is None:
        st.gate('G0.18', 'the beam guard', 'N/A', 'no modal beam (G1)', 'a beam in beams_run, or recon/beam.txt')
    elif any(abs(beam - b) <= tol for b in beams):
        beam_rec['accepted_by'] = 'beams_run'
        st.gate('G0.18', 'the beam guard', 'PASS', 'modal %.1f deg, a beam linog_auto has run (beams_run %s)' % (
            beam, ' '.join('%.1f' % b for b in beams)), 'a beam in beams_run, or recon/beam.txt')
    elif bdeg is not None and abs(bdeg - beam) <= tol:
        beam_rec['accepted_by'] = 'recon/beam.txt'
        st.gate('G0.18', 'the beam guard', 'INFO', 'modal %.1f deg accepted in recon/beam.txt: %s' % (beam, bwhy or '(no reason)'),
                'a beam in beams_run, or recon/beam.txt')
    else:
        if bmd5:
            st.gate('G0.18f', 'recon/beam.txt', 'WARN', 'not applied: it names %s deg, the modal beam is %.1f deg' % (
                'no readable angle' if bdeg is None else '%.1f' % bdeg, beam))
        st.gate('G0.18', 'the beam guard', 'DECISION', 'modal %.1f deg: not a beam linog_auto has run (beams_run %s)' % (
            beam, ' '.join('%.1f' % b for b in beams)), 'a beam in beams_run, or recon/beam.txt',
            'nothing dropped; accept it in recon/beam.txt as "<degrees> <reason>" on a person\'s word, or leave the frame')

    g016 = framing(live, cfg, frame, direction, beam, tol)
    st.gate('G0.16', 'framing (along track)', g016['verdict'], g016['value'],
            '|dev_c| <= %s km; share <= %s; anchor <= %s km' % (cfg.get('framing_max_km', '11.27'),
                                                              cfg.get('framing_max_share', '0.25'),
                                                              cfg.get('framing_anchor_km', '5.64')), g016['note'])
    if g016['law_beside']:
        al, at = g016['law_beside']
        lim = float(cfg.get('framing_law_check_km', 2))
        st.gate('G0.16a', 'anchor: frame law beside table', 'WARN' if abs(al - at) > lim else 'INFO',
                'law %+.3f km, table %+.3f km, differ %+.3f km' % (al, at, al - at), '<= %.1f km' % lim,
                'a table footprint built from a mis-framed majority would show here' if abs(al - at) > lim else '')
    dropped16 = dict(g016['drops'])
    for r in live:
        if r['scene'] in dropped16:
            r['status'], r['reason'] = 'DROPPED', dropped16[r['scene']]
    live = [r for r in live if r['scene'] not in dropped16]

    nfbs = sum(r['mode'] == 'FBS' for r in live)
    nfbd = sum(r['mode'] == 'FBD' for r in live)
    branch = 'FBS-only' if nfbs and not nfbd else 'FBD-only' if nfbd and not nfbs else 'FBS+FBD' if live else 'none'
    st.gate('G0.10', 'mode mix -> branch', 'INFO', 'FBS %d, FBD %d -> %s' % (nfbs, nfbd, branch))

    widths, wwarn, notes = {}, False, []
    for mode in ('FBS', 'FBD'):
        ws = [r['nsamp'] for r in live if r['mode'] == mode]
        if not ws:
            continue
        mw = modal(ws)
        widths[mode] = dict(modal=mw, census=dict(sorted(collections.Counter(ws).items())))
        for r in live:
            if r['mode'] == mode and r['nsamp'] != mw:
                dlt = r['nsamp'] - mw
                whole = dlt % GATE_SAMPLES[mode] == 0
                wwarn |= not whole
                notes.append('%s %s %d (%+d = %s gates)' % (r['date_summary'], mode, r['nsamp'], dlt,
                             ('%+d' % (dlt // GATE_SAMPLES[mode])) if whole else 'NOT whole'))
    st.gate('G0.11', 'widths by mode', 'WARN' if wwarn else 'INFO',
            '; '.join('%s modal %d %s' % (m, v['modal'], v['census']) for m, v in widths.items()), '',
            '\n'.join(notes))

    dates = sorted(r['date_summary'] for r in live)
    dts = [datetime.datetime.strptime(d, '%Y%m%d') for d in dates]
    gaps = [(dts[i + 1] - dts[i]).days for i in range(len(dts) - 1)]
    nmin, nwarn = int(cfg.get('min_dates', 5)), int(cfg.get('warn_dates', 12))
    v = 'FAIL' if len(dates) < nmin else 'WARN' if len(dates) < nwarn else 'PASS'
    st.gate('G0.12', 'kept dates', v, '%d, %s to %s, largest gap %s d' % (len(dates),
            dates[0] if dates else '-', dates[-1] if dates else '-', max(gaps) if gaps else '-'),
            '>= %d (warn < %d)' % (nmin, nwarn))

    exp = cfg.get('expect_' + frame)
    if exp is None:
        st.gate('G0.13', 'in-path count vs path table', 'INFO', '%d found, no expectation' % len(hits))
    else:
        st.gate('G0.13', 'in-path count vs path table', 'PASS' if int(exp) == len(hits) else 'WARN',
                '%d found' % len(hits), 'expected %s' % exp)

    dem = dem_info(cfg['dem'])
    gv, gval, gthr, gnote, fp_rec = footprint(live, cfg, frame, dem)
    st.gate('G0.14', 'DEM covers the footprint', gv, gval, gthr, gnote)
    if fp_rec.get('margins'):
        dem['margins'] = fp_rec['margins']

    need = len(dates) * float(cfg.get('disk_gib_per_date', 12)) + float(cfg.get('disk_gib_margin', 50))
    free, fsp = disk_free_gib(cfg['root'])
    st.gate('G0.15', 'free disk', 'PASS' if free >= need else 'FAIL', '%.1f GiB free at %s' % (free, fsp),
            '>= %.1f GiB' % need)

    # ---- tables and records
    print('\n   %-9s %-6s %-8s %-7s %-3s %-6s %-4s %-6s %-6s %-9s %s' % (
        'date', 'orbit', 'time', 'product', 'dir', 'offnad', 'mode', 'width', 'lines', 'MB', 'status'))
    for r in sorted(recs, key=lambda r: (r.get('date_summary') or '', r['orbit'])):
        print('   %-9s %-6d %-8s %-7s %-3s %-6s %-4s %-6s %-6s %-9.1f %s%s' % (
            r.get('date_summary') or '?', r['orbit'], r.get('time_utc') or '?', r['product'], r['suffix'],
            r['offnadir'] if r['offnadir'] is not None else '?', r.get('mode', '?'), r['nsamp'] or '?',
            r['lines'] or '?', r['size'] / 1e6, r['status'], (': ' + r['reason']) if r['reason'] else ''))
    kept = [r for r in recs if r['status'] == 'KEPT']
    out = dict(version=C.VERSION, created=C.utc(), path=path, frame=frame, direction=direction,
               residue=res, epoch=[ed, eo], archive=cfg['archive'], cfg_file=cfg['cfg_file'],
               cfg_md5=cfg['cfg_md5'], fingerprint=fp, branch=branch, modal_offnadir=beam, widths=widths,
               dates=dates, gaps_days=gaps, dem=dem, disk=dict(free_gib=round(free, 1), need_gib=need, at=fsp),
               exclusions=excl, exclusions_md5=exmd5, granules=recs,
               kept=[dict(scene=r['scene'], date=r['date_summary'], zip=r['zip'], mode=r['mode'],
                          width=r['nsamp']) for r in sorted(kept, key=lambda r: r['date_summary'])],
               dropped=[dict(scene=r['scene'], zip=r['zip'], reason=r['reason'])
                        for r in recs if r['status'] == 'DROPPED'],
               entry=entry, entry_derived=derived, beam=beam_rec, framing=dict(g016['record'], verdict=g016['verdict'],
                                                                               drops=[s for s, _ in g016['drops']]),
               footprint=fp_rec.get('footprint'), footprint_table=fp_rec.get('footprint_table'),
               footprint_differences=fp_rec.get('differences'), corners=fp_rec.get('granules'),
               corners_unusable=fp_rec.get('unusable'), anchor_source=g016['record']['cell'].get('anchor_source'),
               gates=st.rec['gates'])
    rd = os.path.join(recdir, 'recon')
    os.makedirs(rd, exist_ok=True)
    jf = os.path.join(rd, 'RECON.json')
    with open(jf + '.tmp', 'w') as fh:
        json.dump(out, fh, indent=1, default=str)
        fh.write('\n')
    os.replace(jf + '.tmp', jf)
    with open(os.path.join(rd, 'RECON.md'), 'w') as fh:
        fh.write('# RECON p%s f%s (%s, %s)\n\n' % (path, frame, C.VERSION, out['created']))
        fh.write('Branch **%s**; %d kept, %d dropped; modal off-nadir %s deg; entry %s.\n\n' % (
            branch, len(kept), len(out['dropped']), beam, entry))
        fh.write('| gate | verdict | check | value | threshold |\n|:--|:--|:--|:--|:--|\n')
        for g in st.rec['gates']:
            fh.write('| %s | %s | %s | %s | %s |\n' % (g['id'], g['verdict'], g['name'], g['value'],
                                                     g['threshold']))
        fh.write('\n| date | orbit | mode | width | status |\n|:--|--:|:--|--:|:--|\n')
        for r in sorted(recs, key=lambda r: (r.get('date_summary') or '', r['orbit'])):
            fh.write('| %s | %d | %s | %s | %s %s |\n' % (r.get('date_summary') or '?', r['orbit'],
                     r.get('mode', '?'), r['nsamp'] or '?', r['status'], r['reason']))
    vs = [g['verdict'] for g in st.rec['gates']]
    verdict = 'ERROR' if 'ERROR' in vs else 'FAIL' if 'FAIL' in vs else 'DECISION' if 'DECISION' in vs else 'PASS'
    named = ['%s %s' % (g['id'], g['verdict']) for g in st.rec['gates'] if g['verdict'] in ('ERROR', 'FAIL', 'DECISION')]
    if ed is None:
        epoch = None
    elif derived:
        epoch = (ed, eo, derived['anchor']['scene'])
    else:
        epoch = (ed, eo, None)
    pe = write_entry(rd, path, frame, cfg, verdict, ', '.join(named), entry, epoch, live, hits, g016, fp_rec, named)
    st.rec['outputs'] = dict(recon_json=jf, recon_json_md5=C.md5_file(jf), kept=len(kept),
                             dropped=len(out['dropped']), branch=branch, path_entry=pe, path_entry_md5=C.md5_file(pe))
    return st.finish()


class Stopped(BaseException):
    """A signal to stop (SIGTERM, or SIGHUP when not ignored): a BaseException, so no `except Exception` hides it."""


def _stop(signum, frame):
    raise Stopped('stopped by signal %d' % signum)


def crash(e):
    """v0.13 (the part 1 review's M2): an error or a stop after the record is written ends it ERROR (gate ERR, the
    traceback's tail in its note), as lp_p1.crash does for Phase 1, so the next run does not stop at a RUNNING record.
    Before the record (the table, the arguments) nothing is written: the message alone. Exit code 3."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal.SIG_IGN)
    st = CURRENT.get('st')
    if st is not None and not st.rec.get('end'):
        tb = traceback.format_exc().strip().splitlines()
        st.rec['gates'].append(dict(id='ERR', name='unexpected error', verdict='ERROR', value='%s: %s' % (type(e).__name__, e),
                                    threshold='', note='\n'.join(tb[-6:])))
        try:
            st.finish()
        except OSError:
            pass
        sys.stderr.write('lp_recon: %s: %s\n' % (type(e).__name__, e))
    else:
        sys.stderr.write('lp_recon: %s\n' % e)
    return 3


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _stop)
    if signal.getsignal(signal.SIGHUP) != signal.SIG_IGN:
        signal.signal(signal.SIGHUP, _stop)
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt, Stopped) as e:  # noqa: BLE001
        sys.exit(crash(e))
