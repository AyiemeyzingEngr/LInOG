#!/usr/bin/env python3
"""lp_kmz.py -- linog_auto v0.11: the KMZs' zip entries (item 4, record 122.4 and 122.6). Standard library only.

MintPy's save_kmz.py (linog_phase6.sh's step 7) writes each velocity KMZ with ZipFile(kmz, 'w') and fz.write(), so every
entry carries its file's mtime; the kit's linog_gen_interactive_kmz.py (step 10) writes each time-series KMZ with
writestr(), so its one entry carries the clock's time. A rerun on the same data therefore makes KMZs whose bytes differ in
those times alone (record 115.4, 121.1). fix_times() sets every entry's DOS time and date to one fixed value in the
central directory and in the local header (8 bytes an entry), changes nothing else, and checks that before the caller
moves the new file over the old. members() and compare() read two KMZs entry by entry for the rerun check (lp_rerun.py)
and lp_compare.py.

fix_times(src, dst) refuses (KmzError, nothing written) an archive it cannot read entry by entry: no end-of-central-
directory record, bytes after the archive comment, more than one disk, ZIP64, a central directory that does not end where
its record says, a local header not where the central directory points, an extra field in any header (one may carry
another timestamp, such as Info-ZIP's 0x5455), or no entry at all. Its checks after writing: the file on disk is the bytes
made; only the time fields changed; zipfile's CRC test passes; every other field of every entry (name, order,
compression, CRC-32, sizes, attributes, flags, extra field, comment, offset) equals the source's; every entry at the
fixed time.
"""
import os
import struct
import zipfile

FIXED = (1980, 1, 1, 0, 0, 0)   # the zip format's first date: no reader takes it for a processing time (122.8, Ariel's word)
FIXED_TEXT = '1980-01-01 00:00:00'
KEEP = ('filename', 'compress_type', 'CRC', 'compress_size', 'file_size', 'external_attr', 'internal_attr', 'create_system',
        'create_version', 'extract_version', 'flag_bits', 'extra', 'comment', 'header_offset')
CONTENT = ('filename', 'compress_type', 'CRC', 'compress_size', 'file_size')


class KmzError(Exception):
    """A KMZ this module refuses to rewrite, or a rewrite that failed its checks."""


def dos(dt):
    """(time, date) as the zip format packs them: time (h << 11) | (m << 5) | s // 2, date ((y - 1980) << 9) | (mo << 5) | d."""
    y, mo, d, h, mi, s = dt
    if y < 1980:
        raise ValueError('a zip entry cannot hold a year before 1980: %r' % (dt,))
    return (h << 11) | (mi << 5) | (s // 2), ((y - 1980) << 9) | (mo << 5) | d


def entries(b):
    """[(central header offset, local header offset, name)] of the archive's bytes b, in the central directory's order."""
    e = b.rfind(b'PK\x05\x06')
    if e < 0 or len(b) - e < 22:
        raise KmzError('no end-of-central-directory record')
    disk, cdisk, n_here, n, cd_size, cd_off, clen = struct.unpack('<HHHHIIH', b[e + 4:e + 22])
    if e + 22 + clen != len(b):
        raise KmzError('%d bytes after the archive comment' % (len(b) - e - 22 - clen))
    if disk or cdisk or n_here != n:
        raise KmzError('more than one disk')
    if n == 0xFFFF or 0xFFFFFFFF in (cd_size, cd_off) or (e >= 20 and b[e - 20:e - 16] == b'PK\x06\x07'):
        raise KmzError('ZIP64')   # the ZIP64 locator sits right before the end record
    out, p = [], cd_off
    for i in range(n):
        if b[p:p + 4] != b'PK\x01\x02':
            raise KmzError('entry %d: no central header at %d' % (i, p))
        nl, xl, cl = struct.unpack('<HHH', b[p + 28:p + 34])
        lo = struct.unpack('<I', b[p + 42:p + 46])[0]
        name = b[p + 46:p + 46 + nl].decode('utf-8', 'replace')
        if xl:
            raise KmzError('entry %s: an extra field of %d B in its central header (v0.11 fixes the DOS time only)' % (name, xl))
        if b[lo:lo + 4] != b'PK\x03\x04':
            raise KmzError('entry %s: no local header at %d' % (name, lo))
        lnl, lxl = struct.unpack('<HH', b[lo + 26:lo + 30])
        if lxl:
            raise KmzError('entry %s: an extra field of %d B in its local header (v0.11 fixes the DOS time only)' % (name, lxl))
        if b[lo + 30:lo + 30 + lnl].decode('utf-8', 'replace') != name:
            raise KmzError('entry %s: its local header names %r' % (name, b[lo + 30:lo + 30 + lnl]))
        out.append((p, lo, name))
        p += 46 + nl + xl + cl
    if p != cd_off + cd_size:
        raise KmzError('the central directory ends at %d, its record says %d' % (p, cd_off + cd_size))
    if not out:
        raise KmzError('no entries')
    return out


def members(path):
    """[{field: value}] of each entry, in order (KEEP's fields and date_time)."""
    with zipfile.ZipFile(path) as z:
        return [dict([(k, getattr(i, k)) for k in KEEP] + [('date_time', i.date_time)]) for i in z.infolist()]


def fix_times(src, dst, dt=FIXED):
    """Write dst: src with every entry's time and date set to dt, nothing else changed; check it (KmzError on any failure).
    Returns dict(entries, bytes_changed, written=[each entry's time as src holds it, 'YYYY-mm-dd HH:MM:SS'], same=bool)."""
    a = open(src, 'rb').read()
    ents = entries(a)
    t, d = dos(dt)
    b = bytearray(a)
    spots = set()
    for cd, lo, _ in ents:
        struct.pack_into('<HH', b, cd + 12, t, d)
        struct.pack_into('<HH', b, lo + 10, t, d)
        spots.update(range(cd + 12, cd + 16))
        spots.update(range(lo + 10, lo + 14))
    b = bytes(b)
    before = members(src)
    with open(dst, 'wb') as fh:
        fh.write(b)
        fh.flush()
        os.fsync(fh.fileno())
    changed = [i for i in range(len(a)) if a[i] != b[i]] if len(a) == len(b) else None
    if changed is None or not set(changed) <= spots:
        raise KmzError('%s: bytes outside the time fields changed' % os.path.basename(src))
    if open(dst, 'rb').read() != b:
        raise KmzError('%s: the file written is not the bytes made' % os.path.basename(src))
    with zipfile.ZipFile(dst) as z:
        bad = z.testzip()
    if bad is not None:
        raise KmzError('%s: zipfile\'s CRC test failed on %s' % (os.path.basename(src), bad))
    after = members(dst)
    if len(after) != len(before) or any(x[k] != y[k] for x, y in zip(before, after) for k in KEEP):
        raise KmzError('%s: a field other than the time changed' % os.path.basename(src))
    if any(y['date_time'] != tuple(dt) for y in after):
        raise KmzError('%s: an entry not at %r' % (os.path.basename(src), tuple(dt)))
    return dict(entries=len(ents), bytes_changed=len(changed), same=not changed,
                written=['%04d-%02d-%02d %02d:%02d:%02d' % tuple(x['date_time']) for x in before])


def compare(new, ref):
    """Two KMZs entry by entry: dict(content_equal, entries=(n_new, n_ref), first_difference, times_differ, attributes_differ).
    content_equal: the same entries in the same order with the same name, compression, CRC-32 and sizes."""
    a, b = members(new), members(ref)
    first = None
    if len(a) != len(b):
        first = '%d entries, the reference %d' % (len(a), len(b))
    else:
        for x, y in zip(a, b):
            k = [k for k in CONTENT if x[k] != y[k]]
            if k:
                first = '%s: %s differ' % (x['filename'], ', '.join(k))
                break
    pairs = list(zip(a, b))
    return dict(content_equal=first is None, entries=[len(a), len(b)], first_difference=first,
                times_differ=any(x['date_time'] != y['date_time'] for x, y in pairs),
                attributes_differ=any(x[k] != y[k] for x, y in pairs for k in ('external_attr', 'create_system', 'flag_bits')))
