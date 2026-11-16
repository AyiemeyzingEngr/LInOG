#!/usr/bin/env python3
"""lp_compare.py -- linog_auto v0.11, item 5: the comparison tools of record 119, beside the pipeline (not a phase).

It only reads what it compares, and writes only under --out (split --run also under --scratch). Run it with the pinned
env's python3 (numpy, h5py and GDAL; ISCE's classes for shelves); `packages` needs them only for its readings.

  lp_compare.py packages NEW REF [--out DIR]
      two review packages (_xfer/<PREFIX>_<TAG>_<VERSION>_<date>_review/): each one's TRANSFER_MANIFEST_<TAG>.txt checked
      against its files (md5sum -c); the names both ways; the files by md5; KMZs whose md5s differ, by their entries
      (lp_kmz.compare: names, order, compression, CRC-32 and sizes; times and attributes reported, not judged); the leaves
      of RUN_MANIFEST.json that differ; the network key of both RUN_MANIFEST.json (record 122.5); and, for each GeoTIFF that
      differs, on the cells valid in both: the median, p01 and p99 of NEW minus REF in mm/yr, the shares beyond 1 and 5
      mm/yr, the maximum beside them, and the cells gained and lost. The rerun phase (lp_rerun.py) runs the same functions.
  lp_compare.py shelves NEW_FRAME REF_FRAME [--dates D,D,...] --out DIR
      each date's SLC/<date>/data shelve (ISCE's frame, doppler, fmrate): byte for byte, then unpickled with the object ids
      (objid) ignored (record 119.2, steps 3b and 3c-3). It works in --out (ISCE's classes may open isce.log in the working
      folder, F50), and needs lp_env.sh's PYTHONPATH (<isce>/components) to unpickle them.
  lp_compare.py cycles NEW_FRAME REF_FRAME [--out DIR]
      mintpy/inputs/ifgramStack.h5 of both: the pairs and dropIfgram; per pair, unwrapPhase NEW minus REF with its median
      offset removed: the median, p99 and share of cells beyond pi (a whole-cycle jump) (step 3c-3).
  lp_compare.py split NEW_FRAME REF_FRAME (--cf DIR | --scratch DIR [--run]) [--out DIR]
      the velocity change split between the network and the rest (record 119.3, step 3d). CF is NEW's stack inverted with
      REF's network (REF's dropIfgram): made by ifgram_inversion.py on a copy of NEW's inputs under --scratch (with --run;
      without it, the plan only), or one made before (--cf DIR, holding timeseries.h5 and temporalCoherence.h5). The
      velocities are linear fits to each timeseries.h5, in mm/yr: network NEW - CF, the rest CF - REF, total NEW - REF, on
      every cell and on the cells both trees' maskTempCoh.orig.h5 (else maskTempCoh.h5) keep; temporal coherence at
      mintpy.networkInversion.minTempCoh (auto: 0.7), gained and lost, on land and on water (watermask/waterMask.h5, its
      larger class taken as land, as E1, record 120).
Exit 0 when it ran, whatever it found; 2 when an input is missing or unreadable; 3 on an unexpected error.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import lp_kmz as K

VERSION = 'linog_auto v0.11 (2026-10-09) lp_compare'
SIX = ('demErr', 'demErr_ramp', 'Vertical', 'Vertical_ramp', 'Horizontal', 'Horizontal_ramp')
MISSING = 'not recorded'
# the network key (record 122.5): what makes the products, read from RUN_MANIFEST.json
NETWORK = (('kept', ('dates', 'kept')), ('excludeDate12', ('decisions', 'd3', 'excludeDate12')),
           ('excludeDate', ('decisions', 'd3', 'excludeDate')), ('reference_date', ('decisions', 'reference_date', 'value')),
           ('reference_yx', ('decisions', 'reference_pixel', 'yx')), ('unwrapError', ('decisions', 'd9', 'unwrapError')),
           ('dates_out_of_fit', ('velocity_fit', 'dates_out_of_fit')))


class InputError(Exception):
    """An input missing or unreadable (exit 2)."""


def md5_file(p, block=1 << 20):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(block), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- packages
def manifest_of(pkg):
    """(the manifest's name, {./relative path: md5}) of a package: its one TRANSFER_MANIFEST_*.txt at the top."""
    if not os.path.isdir(pkg):
        raise InputError('%s: not a folder' % pkg)
    ms = sorted(n for n in os.listdir(pkg) if re.match(r'^TRANSFER_MANIFEST_.+\.txt$', n) and os.path.isfile(os.path.join(pkg, n)))
    if len(ms) != 1:
        raise InputError('%s: %d TRANSFER_MANIFEST_*.txt at its top, want 1' % (pkg, len(ms)))
    out = {}
    for i, ln in enumerate(open(os.path.join(pkg, ms[0]), errors='replace')):
        ln = ln.rstrip('\n')
        if ln:
            m = re.match(r'^([0-9a-f]{32})  (\./.+)$', ln)
            if not m:
                raise InputError('%s line %d is not "md5  ./path": %r' % (os.path.join(pkg, ms[0]), i + 1, ln[:80]))
            out[m.group(2)] = m.group(1)
    return ms[0], out


def hash_of_hashes(hs):
    return hashlib.md5(''.join(h + '\n' for h in sorted(hs)).encode()).hexdigest()


def check_package(pkg):
    """md5sum -c in Python, and the files its manifest does not list: dict(manifest, manifest_md5, lines, failing,
    unlisted, hash_of_hashes)."""
    name, lines = manifest_of(pkg)
    failing = [rel for rel, h in sorted(lines.items()) if not os.path.isfile(os.path.join(pkg, rel)) or md5_file(os.path.join(pkg, rel)) != h]
    have = set()
    for d, ds, fs in os.walk(pkg):
        ds.sort()
        for f in fs:
            rel = './' + os.path.relpath(os.path.join(d, f), pkg)
            if not (d == pkg and f == name):
                have.add(rel)
    return dict(manifest=name, manifest_md5=md5_file(os.path.join(pkg, name)), lines=len(lines), failing=failing,
                unlisted=sorted(have - set(lines)), hash_of_hashes=hash_of_hashes(lines.values()))


def leaves(o, path=''):
    """{path: value} of a JSON document's leaves (lists by index)."""
    out = {}
    if isinstance(o, dict):
        for k in o:
            out.update(leaves(o[k], '%s.%s' % (path, k) if path else str(k)))
    elif isinstance(o, list):
        if not o:
            out[path] = []
        for i, v in enumerate(o):
            out.update(leaves(v, '%s[%d]' % (path, i)))
    else:
        out[path] = o
    return out


def json_diff(new, ref):
    a, b = leaves(new), leaves(ref)
    return dict(leaves=[len(a), len(b)], only_new=sorted(set(a) - set(b)), only_ref=sorted(set(b) - set(a)),
                differ=sorted(k for k in set(a) & set(b) if a[k] != b[k]))


def norm_list(v):
    """excludeDate12, excludeDate, the fit's dates: None, '', 'auto', 'no' and [] all mean none (122.5)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        xs = [str(x).strip() for x in v]
    else:
        xs = [x.strip() for x in str(v).replace(' ', ',').split(',')]
    return sorted(x for x in xs if x and x.lower() not in ('auto', 'no', 'none'))


def get(j, path):
    for k in path:
        if not isinstance(j, dict) or k not in j:
            return MISSING
        j = j[k]
    return j


def network_key(man):
    """The network key of a RUN_MANIFEST.json (record 122.5), each field normalised, or MISSING."""
    out = {}
    for name, path in NETWORK:
        v = get(man, path)
        if v is MISSING:
            out[name] = MISSING
        elif name in ('excludeDate12', 'excludeDate', 'dates_out_of_fit'):
            out[name] = norm_list(v)
        elif name == 'unwrapError':
            out[name] = 'no' if v in (None, '', 'auto', 'no') else str(v)
        elif name == 'reference_yx':
            out[name] = [int(x) for x in v] if isinstance(v, (list, tuple)) else v
        else:
            out[name] = v
    return out


def compare_keys(kn, kr):
    """dict(complete, equal, fields={name: same | DIFFERS | not recorded})."""
    f = dict((n, MISSING if MISSING in (kn[n], kr[n]) else ('same' if kn[n] == kr[n] else 'DIFFERS')) for n, _ in NETWORK)
    complete = MISSING not in f.values()
    return dict(complete=complete, equal=complete and all(v == 'same' for v in f.values()), fields=f, new=kn, ref=kr)


def read_tif(p):
    """(values as float64, geotransform) of a GeoTIFF's band 1, through GDAL with PAM off (no .aux.xml)."""
    from osgeo import gdal
    gdal.UseExceptions()
    gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')
    ds = gdal.Open(p)
    a = ds.GetRasterBand(1).ReadAsArray().astype('f8')
    gt = [float(v) for v in ds.GetGeoTransform()]
    ds = None
    return a, gt


def tif_readings(new, ref):
    """NEW minus REF of two GeoTIFFs in m/yr, in mm/yr, on the cells valid (finite) in both."""
    import numpy as np
    a, ga = read_tif(new)
    b, gb = read_tif(ref)
    if a.shape != b.shape or ga != gb:
        return dict(grids_differ='%s %s against %s %s' % (list(a.shape), ga, list(b.shape), gb))
    fa, fb = np.isfinite(a), np.isfinite(b)
    both = fa & fb
    out = dict(cells_new=int(fa.sum()), cells_ref=int(fb.sum()), cells_both=int(both.sum()), gained=int((fa & ~fb).sum()),
               lost=int((fb & ~fa).sum()), units='mm/yr, NEW minus REF')
    if both.any():
        d = (a - b)[both] * 1000.0
        q = np.percentile(d, [1, 50, 99])
        out.update(p01=float(q[0]), median=float(q[1]), p99=float(q[2]), share_gt1=float((np.abs(d) > 1).mean()),
                   share_gt5=float((np.abs(d) > 5).mean()), max_abs=float(np.abs(d).max()))
    return out


def compare_packages(new, ref, readings=True):
    """Everything `packages` reports, as a dict (the rerun phase records it)."""
    cn, cr = check_package(new), check_package(ref)
    _, ln = manifest_of(new)
    _, lr = manifest_of(ref)
    names_new, names_ref = set(ln), set(lr)
    common = sorted(names_new & names_ref)
    equal = [r for r in common if ln[r] == lr[r]]
    differ = [r for r in common if ln[r] != lr[r]]
    kmz, kmz_equal = {}, []
    for r in differ:
        if r.endswith('.kmz'):
            try:
                kmz[r] = K.compare(os.path.join(new, r), os.path.join(ref, r))
            except Exception as e:  # noqa: BLE001  an unreadable KMZ is a difference, named
                kmz[r] = dict(content_equal=False, first_difference='%s: %s' % (type(e).__name__, e))
            if kmz[r].get('content_equal'):
                kmz_equal.append(r)
    man = [r for r in differ if os.path.basename(r) == 'RUN_MANIFEST.json']
    rest = [r for r in differ if r not in kmz_equal and r not in man]
    out = dict(new=os.path.abspath(new), ref=os.path.abspath(ref), check_new=cn, check_ref=cr,
               names=dict(new=len(names_new), ref=len(names_ref), only_new=sorted(names_new - names_ref),
                          only_ref=sorted(names_ref - names_new)),
               equal=len(equal), differ=differ, kmz=kmz, kmz_equal_by_entries=kmz_equal, other_differ=rest)
    mn, mr = os.path.join(new, 'RUN_MANIFEST.json'), os.path.join(ref, 'RUN_MANIFEST.json')
    jn = json.load(open(mn)) if os.path.isfile(mn) else {}
    jr = json.load(open(mr)) if os.path.isfile(mr) else {}
    out['run_manifest'] = dict(json_diff(jn, jr), labels=[jn.get('manifest'), jr.get('manifest')]) if jn and jr else None
    out['network'] = compare_keys(network_key(jn), network_key(jr))
    out['same_files'] = not rest and not out['names']['only_new'] and not out['names']['only_ref']
    out['readings'] = {}
    if readings:
        for r in rest:
            m = re.search(r'_Velocity_(%s)\.tif$' % '|'.join(SIX), r)
            if m:
                try:
                    out['readings'][m.group(1)] = tif_readings(os.path.join(new, r), os.path.join(ref, r))
                except Exception as e:  # noqa: BLE001  readings, not a verdict: a failure is named
                    out['readings'][m.group(1)] = dict(error='%s: %s' % (type(e).__name__, str(e)[:200]))
    return out


def report_packages(c):
    """The lines `packages` prints (and the rerun phase logs)."""
    ls = ['== packages: NEW %s' % c['new'], '            REF %s' % c['ref']]
    for k, lab in (('check_new', 'NEW'), ('check_ref', 'REF')):
        x = c[k]
        ls.append('   %s manifest %s: %d lines, md5sum -c %d failing, %d files not listed; hash of hashes %s' % (
            lab, x['manifest'], x['lines'], len(x['failing']), len(x['unlisted']), x['hash_of_hashes']))
    n = c['names']
    ls.append('   names: NEW %d, REF %d; only NEW %d, only REF %d' % (n['new'], n['ref'], len(n['only_new']), len(n['only_ref'])))
    ls.append('   files: %d equal by md5; %d differ: %d KMZs equal by entries, RUN_MANIFEST.json %s, %d others' % (
        c['equal'], len(c['differ']), len(c['kmz_equal_by_entries']), 'differs' if any(os.path.basename(r) == 'RUN_MANIFEST.json'
                                                                                     for r in c['differ']) else 'equal',
        len(c['other_differ'])))
    for r in c['other_differ'][:20]:
        ls.append('      differs: %s' % r)
    for r, k in sorted(c['kmz'].items()):
        ls.append('      KMZ %s: content %s%s; times %s; attributes %s' % (
            os.path.basename(r), 'equal' if k.get('content_equal') else 'DIFFERS', '' if k.get('content_equal') else ' (%s)' % k.get('first_difference'),
            'differ' if k.get('times_differ') else 'equal', 'differ' if k.get('attributes_differ') else 'equal'))
    rm = c.get('run_manifest')
    if rm:
        ls.append('   RUN_MANIFEST.json: %s against %s; leaves %d and %d; %d differ, %d only NEW, %d only REF' % (
            rm['labels'][0], rm['labels'][1], rm['leaves'][0], rm['leaves'][1], len(rm['differ']), len(rm['only_new']), len(rm['only_ref'])))
    nk = c['network']
    ls.append('   network key: %s' % ('complete and equal' if nk['equal'] else 'complete, DIFFERS' if nk['complete'] else 'not complete'))
    for f, v in nk['fields'].items():
        ls.append('      %-16s %-12s NEW %s  REF %s' % (f, v, str(nk['new'][f])[:60], str(nk['ref'][f])[:60]))
    for p, r in c['readings'].items():
        if 'median' in r:
            ls.append('   %-15s both %d; median %+.3f, p01 %+.3f, p99 %+.3f mm/yr; beyond 1: %.4f, beyond 5: %.5f; max %.2f; gained %d, lost %d' % (
                p, r['cells_both'], r['median'], r['p01'], r['p99'], r['share_gt1'], r['share_gt5'], r['max_abs'], r['gained'], r['lost']))
        else:
            ls.append('   %-15s %s' % (p, r))
    ls.append('   so: %s' % ('every file equal but RUN_MANIFEST.json (KMZs by their entries)' if c['same_files'] else
                             '%d files differ beyond RUN_MANIFEST.json' % (len(c['other_differ']) + len(c['names']['only_new']) + len(c['names']['only_ref']))))
    return ls


# ---------------------------------------------------------------- shelves
def load_shelf(frame, d):
    import dbm
    db = dbm.open(os.path.join(frame, 'SLC', d, 'data'), 'r')
    try:
        return dict((k.decode(errors='replace'), bytes(db[k])) for k in db.keys())
    finally:
        db.close()


def flat(o, path, out, depth=0):
    """trace3b's flattening: {attribute path: value} of an unpickled object (arrays by their values up to 5,000)."""
    import numpy as np
    if depth > 10:
        out[path] = '<deep>'
        return
    if o is None or isinstance(o, (bool, int, float, complex, str, bytes)):
        out[path] = o
        return
    if isinstance(o, np.ndarray):
        out[path + '.shape'], out[path + '.dtype'] = str(o.shape), str(o.dtype)
        if o.size <= 5000:
            for i, v in enumerate(o.ravel().tolist()):
                out[path + '[%d]' % i] = v
        else:
            out[path + '.sum'] = float(np.sum(o.astype(np.float64)))
        return
    if isinstance(o, dict):
        for k in o:
            flat(o[k], path + '/' + str(k), out, depth + 1)
        return
    if isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            flat(v, path + '[%d]' % i, out, depth + 1)
        return
    if hasattr(o, '__dict__'):
        out[path + '::' + type(o).__name__] = ''
        for k, v in vars(o).items():
            flat(v, path + '.' + k, out, depth + 1)
        return
    out[path] = repr(o)[:60]


def shelf_diff(xn, xr):
    """(leaves, [(path, REF, NEW)] that differ, object ids left out; NaN equal to NaN)."""
    a, b = {}, {}
    flat(xn, '', a)
    flat(xr, '', b)
    keys = sorted(set(a) | set(b))
    out = []
    for k in keys:
        x, y = a.get(k, '<absent>'), b.get(k, '<absent>')
        if isinstance(x, float) and isinstance(y, float) and x != x and y != y:
            continue
        if x != y and 'objid' not in k:
            out.append((k, y, x))
    return len(keys), out


def compare_shelves(new, ref, dates=None):
    import pickle
    dn = sorted(d for d in os.listdir(os.path.join(new, 'SLC')) if d.isdigit()) if os.path.isdir(os.path.join(new, 'SLC')) else []
    dr = sorted(d for d in os.listdir(os.path.join(ref, 'SLC')) if d.isdigit()) if os.path.isdir(os.path.join(ref, 'SLC')) else []
    if not dn or not dr:
        raise InputError('no SLC/<date>/ folders: NEW %d, REF %d' % (len(dn), len(dr)))
    want = sorted(set(dn) & set(dr)) if not dates else [d for d in dates if d in dn and d in dr]
    out = dict(dates_new=len(dn), dates_ref=len(dr), only_new=sorted(set(dn) - set(dr)), only_ref=sorted(set(dr) - set(dn)), rows=[])
    for d in want:
        try:
            sn, sr = load_shelf(new, d), load_shelf(ref, d)
        except Exception as e:  # noqa: BLE001
            out['rows'].append(dict(date=d, error='shelve not read: %s: %s' % (type(e).__name__, str(e)[:120])))
            continue
        for key in sorted(set(sn) | set(sr)):
            row = dict(date=d, key=key)
            if key not in sn or key not in sr:
                row['state'] = 'on one side only'
            elif sn[key] == sr[key]:
                row['state'] = 'bytes identical'
            else:
                try:
                    n, diff = shelf_diff(pickle.loads(sn[key]), pickle.loads(sr[key]))
                    row.update(state='bytes differ', leaves=n, differ=len(diff),
                               first=[(k, repr(y)[:40], repr(x)[:40]) for k, y, x in diff[:6]])
                except Exception as e:  # noqa: BLE001
                    row.update(state='bytes differ; unpickle failed: %s: %s' % (type(e).__name__, str(e)[:120]))
            out['rows'].append(row)
    return out


def report_shelves(c):
    ls = ['== shelves: dates NEW %d, REF %d; only NEW %s; only REF %s' % (c['dates_new'], c['dates_ref'], c['only_new'] or 'none',
                                                                       c['only_ref'] or 'none')]
    for r in c['rows']:
        if 'error' in r:
            ls.append('   %s: %s' % (r['date'], r['error']))
            continue
        ls.append('   %s %-8s %s%s' % (r['date'], r['key'], r['state'], '; leaves %d, %d differ but object ids' % (r['leaves'], r['differ'])
                                       if 'leaves' in r else ''))
        for k, y, x in r.get('first') or []:
            ls.append('      %-50s REF %-40s NEW %s' % (k[-50:], y, x))
    nd = [r for r in c['rows'] if r.get('differ')]
    ls.append('   so: %d shelve keys read; %d differ beyond object ids' % (len(c['rows']), len(nd)))
    return ls


# ---------------------------------------------------------------- cycles
def nm(row):
    if isinstance(row, bytes):
        return row.decode()
    return '_'.join(x.decode() if isinstance(x, bytes) else str(x) for x in row)


def compare_cycles(new, ref):
    import h5py
    import numpy as np
    pn, pr = os.path.join(new, 'mintpy', 'inputs', 'ifgramStack.h5'), os.path.join(ref, 'mintpy', 'inputs', 'ifgramStack.h5')
    for p in (pn, pr):
        if not os.path.isfile(p):
            raise InputError('%s: absent' % p)
    rows = []
    with h5py.File(pn, 'r') as fa, h5py.File(pr, 'r') as fb:
        na, nb = [nm(r) for r in fa['date'][()]], [nm(r) for r in fb['date'][()]]
        da, db = fa['dropIfgram'][()].astype(bool), fb['dropIfgram'][()].astype(bool)
        common = [x for x in na if x in nb]
        kept = dict(new=int(da.sum()), ref=int(db.sum()),
                    differ=[dict(pair=x, new=bool(da[na.index(x)]), ref=bool(db[nb.index(x)])) for x in common
                            if bool(da[na.index(x)]) != bool(db[nb.index(x)])])
        for x in common:
            a = fa['unwrapPhase'][na.index(x)].astype(np.float64)
            b = fb['unwrapPhase'][nb.index(x)].astype(np.float64)
            ok = np.isfinite(a) & np.isfinite(b) & (a != 0) & (b != 0)
            d = a[ok] - b[ok]
            if d.size == 0:
                rows.append(dict(pair=x, cells=0, byte_equal=bool(np.array_equal(a, b))))
                continue
            off = float(np.median(d))
            r = np.abs(d - off)
            rows.append(dict(pair=x, cells=int(ok.sum()), offset=off, median=float(np.median(r)), p99=float(np.percentile(r, 99)),
                             beyond_pi=float((r > np.pi).mean()), byte_equal=bool(np.array_equal(a, b))))
    return dict(pairs_new=len(na), pairs_ref=len(nb), only_new=sorted(set(na) - set(nb)), only_ref=sorted(set(nb) - set(na)),
                kept=kept, rows=rows)


def report_cycles(c):
    rows = [r for r in c['rows'] if r.get('cells')]
    ls = ['== cycles: pairs NEW %d, REF %d; only NEW %d, only REF %d; kept NEW %d, REF %d; dropIfgram differs on %d' % (
        c['pairs_new'], c['pairs_ref'], len(c['only_new']), len(c['only_ref']), c['kept']['new'], c['kept']['ref'], len(c['kept']['differ']))]
    for x in c['kept']['differ'][:20]:
        ls.append('   %s kept: NEW %s, REF %s' % (x['pair'], x['new'], x['ref']))
    ls.append('   byte-equal pairs %d of %d' % (sum(1 for r in c['rows'] if r.get('byte_equal')), len(c['rows'])))
    if rows:
        p99 = sorted(r['p99'] for r in rows)
        ls.append('   p99 |NEW - REF - offset| across pairs (rad): min %.2e, median %.2e, max %.2e' % (p99[0], p99[len(p99) // 2], p99[-1]))
        jumps = [r for r in rows if r['beyond_pi'] > 0]
        ls.append('   pairs with cells beyond pi (a whole cycle): %d; the largest share %.4f' % (len(jumps), max(r['beyond_pi'] for r in rows)))
        for r in sorted(rows, key=lambda r: -r['beyond_pi'])[:8]:
            ls.append('      %s  cells %d  offset %+.3f  median %.2e  p99 %.2e  beyond pi %.4f' % (
                r['pair'], r['cells'], r['offset'], r['median'], r['p99'], r['beyond_pi']))
    return ls


# ---------------------------------------------------------------- split
def first(path):
    import h5py
    with h5py.File(path, 'r') as f:
        return f[list(f.keys())[0]][()]


def velocity(path):
    """(dates, the linear fit's rate in mm/yr per cell) of a timeseries.h5 (cmp3.py's fit)."""
    import h5py
    import numpy as np
    with h5py.File(path, 'r') as f:
        dates = [x.decode() if isinstance(x, bytes) else str(x) for x in f['date'][()]]
        y = f['timeseries'][()].astype(np.float64)
    t = np.array([(datetime.datetime.strptime(d, '%Y%m%d') - datetime.datetime(2000, 1, 1)).days / 365.25 for d in dates])
    A = np.vstack([t, np.ones_like(t)]).T
    n, r, c = y.shape
    y = y.reshape(n, -1)
    ok = np.all(np.isfinite(y), axis=0) & np.any(y != 0, axis=0)
    v = np.full(y.shape[1], np.nan)
    if ok.any():
        v[ok] = np.linalg.lstsq(A, y[:, ok], rcond=None)[0][0] * 1000.0
    return dates, v.reshape(r, c)


def stats(d, m):
    import numpy as np
    x = d[m & np.isfinite(d)]
    if x.size == 0:
        return dict(n=0)
    q = np.percentile(x, [1, 50, 99])
    return dict(n=int(x.size), mean=float(x.mean()), std=float(x.std()), p01=float(q[0]), p50=float(q[1]), p99=float(q[2]),
                max_abs=float(np.abs(x).max()), share_gt1=float((np.abs(x) > 1).mean()), share_gt5=float((np.abs(x) > 5).mean()))


def min_tempcoh(cfg):
    for ln in open(cfg) if os.path.isfile(cfg) else []:
        if ln.strip().startswith('mintpy.networkInversion.minTempCoh'):
            v = ln.split('=', 1)[1].split('#')[0].strip()
            return 0.7 if v in ('auto', '') else float(v)
    return 0.7


def tempcoh_mask(mintpy):
    for n in ('watermask/maskTempCoh.orig.h5', 'maskTempCoh.h5'):
        if os.path.isfile(os.path.join(mintpy, n)):
            return first(os.path.join(mintpy, n)).astype(bool), n
    raise InputError('%s: neither watermask/maskTempCoh.orig.h5 nor maskTempCoh.h5' % mintpy)


def split_plan(new, ref, scratch):
    """What --run would copy and run, and the network it would invert: dict."""
    import h5py
    mn, mr = os.path.join(new, 'mintpy'), os.path.join(ref, 'mintpy')
    sn, sr = os.path.join(mn, 'inputs', 'ifgramStack.h5'), os.path.join(mr, 'inputs', 'ifgramStack.h5')
    for p in (sn, sr, os.path.join(mn, 'inputs', 'geometryRadar.h5'), os.path.join(mn, 'smallbaselineApp.cfg')):
        if not os.path.isfile(p):
            raise InputError('%s: absent' % p)
    with h5py.File(sn, 'r') as fa, h5py.File(sr, 'r') as fb:
        na, nb = [nm(r) for r in fa['date'][()]], [nm(r) for r in fb['date'][()]]
        da, db = fa['dropIfgram'][()].astype(bool), fb['dropIfgram'][()].astype(bool)
    if na != nb:
        raise InputError('the two stacks hold different pairs (%d and %d): the split needs one stack whose kept pairs differ' % (len(na), len(nb)))
    copy = [os.path.join(mn, 'inputs', 'ifgramStack.h5'), os.path.join(mn, 'inputs', 'geometryRadar.h5'), os.path.join(mn, 'smallbaselineApp.cfg')]
    need = sum(os.path.getsize(p) for p in copy)
    free = shutil.disk_usage(scratch if os.path.isdir(scratch) else os.path.dirname(os.path.abspath(scratch)) or '.').free
    return dict(pairs=len(na), kept_new=int(da.sum()), kept_ref=int(db.sum()),
                differ=[dict(pair=x, new=bool(da[i]), ref=bool(db[i])) for i, x in enumerate(na) if da[i] != db[i]],
                copy=copy, bytes=need, free=free, cf=os.path.join(os.path.abspath(scratch), 'cf'),
                command='ifgram_inversion.py inputs/ifgramStack.h5 -t smallbaselineApp.cfg (in %s)' % os.path.join(os.path.abspath(scratch), 'cf'),
                drop_ref=[bool(x) for x in db])


def split_run(plan):
    """Copy NEW's inputs into plan['cf'], set its dropIfgram to REF's, run the inversion there; (rc, log)."""
    import h5py
    import numpy as np
    cf = plan['cf']
    if os.path.isdir(cf) and os.listdir(cf):
        raise InputError('%s exists and is not empty: give a new --scratch' % cf)
    os.makedirs(os.path.join(cf, 'inputs'), exist_ok=True)
    for p in plan['copy']:
        shutil.copy2(p, os.path.join(cf, 'inputs' if p.endswith('.h5') else '', os.path.basename(p)))
    with h5py.File(os.path.join(cf, 'inputs', 'ifgramStack.h5'), 'r+') as f:
        f['dropIfgram'][...] = np.array(plan['drop_ref'], bool)
        kept = int(f['dropIfgram'][()].sum())
    log = os.path.join(cf, 'inversion.log')
    with open(log, 'w') as fh:
        rc = subprocess.run(['ifgram_inversion.py', 'inputs/ifgramStack.h5', '-t', 'smallbaselineApp.cfg'], cwd=cf, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    with open(os.path.join(cf, 'split.status'), 'w') as fh:
        fh.write('exit=%d end=%s kept=%d\n' % (rc, datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'), kept))
    return rc, log


def compare_split(new, ref, cf):
    import numpy as np
    mn, mr = os.path.join(new, 'mintpy'), os.path.join(ref, 'mintpy')
    for p in (os.path.join(mn, 'timeseries.h5'), os.path.join(mr, 'timeseries.h5'), os.path.join(cf, 'timeseries.h5'),
              os.path.join(mn, 'temporalCoherence.h5'), os.path.join(mr, 'temporalCoherence.h5'), os.path.join(cf, 'temporalCoherence.h5')):
        if not os.path.isfile(p):
            raise InputError('%s: absent' % p)
    dN, vN = velocity(os.path.join(mn, 'timeseries.h5'))
    dR, vR = velocity(os.path.join(mr, 'timeseries.h5'))
    dC, vC = velocity(os.path.join(cf, 'timeseries.h5'))
    mN, nN = tempcoh_mask(mn)
    mR, nR = tempcoh_mask(mr)
    both = mN & mR
    allm = np.ones(vN.shape, bool)
    out = dict(dates=dict(new=len(dN), ref=len(dR), cf=len(dC), equal=dN == dR == dC), masks=[nN, nR], cells_both_masks=int(both.sum()),
               velocity={})
    for lab, d in (('network: NEW - CF', vN - vC), ('the rest: CF - REF', vC - vR), ('total: NEW - REF', vN - vR)):
        out['velocity'][lab] = dict(all=stats(d, allm), both_masks=stats(d, both))
    thr = min_tempcoh(os.path.join(mn, 'smallbaselineApp.cfg'))
    tN, tC, tR = (first(os.path.join(x, 'temporalCoherence.h5')) >= thr for x in (mn, cf, mr))
    out['tempcoh'] = dict(threshold=thr, new=int(tN.sum()), cf=int(tC.sum()), ref=int(tR.sum()),
                          network=dict(new_only=int((tN & ~tC).sum()), cf_only=int((tC & ~tN).sum())),
                          rest=dict(cf_only=int((tC & ~tR).sum()), ref_only=int((tR & ~tC).sum())))
    wm = os.path.join(mn, 'watermask', 'waterMask.h5')
    if os.path.isfile(wm):
        raw = first(wm).astype(bool)
        land = raw if raw.sum() >= raw.size / 2 else ~raw
        lost, gain = tC & ~tN, tN & ~tC
        d = np.abs(vN - vC)
        cls = {}
        for lab, m in (('land, coherent in both', land & tN & tC), ('water, coherent in both', ~land & tN & tC)):
            x = d[m & np.isfinite(d)]
            cls[lab] = dict(n=int(x.size)) if not x.size else dict(n=int(x.size), p50=float(np.median(x)), p99=float(np.percentile(x, 99)),
                                                                 max=float(x.max()), gt1=int((x > 1).sum()), gt5=int((x > 5).sum()))
        out['land'] = dict(land=int(land.sum()), water=int((~land).sum()), lost_land=int((lost & land).sum()), lost_water=int((lost & ~land).sum()),
                           gained_land=int((gain & land).sum()), gained_water=int((gain & ~land).sum()), network_by_class=cls)
    return out


def report_split(c):
    ls = ['== split: dates NEW %d, REF %d, CF %d (equal %s); masks %s; cells kept by both %d' % (
        c['dates']['new'], c['dates']['ref'], c['dates']['cf'], c['dates']['equal'], ' and '.join(c['masks']), c['cells_both_masks'])]
    for lab, v in c['velocity'].items():
        for k in ('all', 'both_masks'):
            s = v[k]
            ls.append('   %-20s %-10s n %7d' % (lab, k, s['n']) + ('  mean %+.3f std %.3f p01 %+.3f p50 %+.3f p99 %+.3f max %.2f >1 %.4f >5 %.5f' % (
                s['mean'], s['std'], s['p01'], s['p50'], s['p99'], s['max_abs'], s['share_gt1'], s['share_gt5']) if s['n'] else ''))
    t = c['tempcoh']
    ls.append('   temporal coherence >= %.2f: NEW %d, CF %d, REF %d; network NEW-only %d, CF-only %d; the rest CF-only %d, REF-only %d' % (
        t['threshold'], t['new'], t['cf'], t['ref'], t['network']['new_only'], t['network']['cf_only'], t['rest']['cf_only'], t['rest']['ref_only']))
    if c.get('land'):
        x = c['land']
        ls.append('   land %d, water %d; keeping NEW\'s network over CF\'s: lost land %d, water %d; gained land %d, water %d' % (
            x['land'], x['water'], x['lost_land'], x['lost_water'], x['gained_land'], x['gained_water']))
        for lab, s in x['network_by_class'].items():
            ls.append('      |NEW - CF| %-24s n %d%s' % (lab, s['n'], '  p50 %.3f p99 %.3f max %.2f >1 %d >5 %d' % (
                s['p50'], s['p99'], s['max'], s['gt1'], s['gt5']) if s['n'] else ''))
    return ls


# ---------------------------------------------------------------- the command line
def write_out(out, cmd, result, lines):
    if not out:
        return
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'compare_%s.json' % cmd), 'w') as fh:
        json.dump(dict(tool=VERSION, command=cmd, result=result), fh, indent=1, default=str)
        fh.write('\n')
    with open(os.path.join(out, 'compare_%s.txt' % cmd), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


def main(argv):
    ap = argparse.ArgumentParser(description='linog_auto v0.11 item 5: the comparison tools of record 119 (read-only)')
    sub = ap.add_subparsers(dest='cmd')
    for c in ('packages', 'shelves', 'cycles', 'split'):
        p = sub.add_parser(c)
        p.add_argument('new')
        p.add_argument('ref')
        p.add_argument('--out', metavar='DIR')
        if c == 'shelves':
            p.add_argument('--dates', metavar='D,D,...')
        if c == 'split':
            p.add_argument('--cf', metavar='DIR')
            p.add_argument('--scratch', metavar='DIR')
            p.add_argument('--run', action='store_true')
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2
    print('%s  %s  %s' % (VERSION, a.cmd, datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')))
    out = os.path.abspath(a.out) if a.out else None
    for opt, d in (('--out', out), ('--scratch', os.path.abspath(a.scratch) if getattr(a, 'scratch', None) else None)):
        for p in (a.new, a.ref):
            if d and (d + os.sep).startswith(os.path.abspath(p) + os.sep):
                raise InputError('%s %s is inside %s, which this tool only reads' % (opt, d, p))
    if a.cmd == 'packages':
        res = compare_packages(a.new, a.ref)
        lines = report_packages(res)
    elif a.cmd == 'shelves':
        if not out:
            raise InputError('shelves needs --out DIR: it works there, since ISCE\'s classes may open isce.log in the working folder (F50)')
        here = os.getcwd()
        work = out
        os.makedirs(work, exist_ok=True)
        os.chdir(work)   # ISCE's classes, unpickled, may open isce.log in the working folder (F50): here, not where it was run
        try:
            res = compare_shelves(os.path.abspath(os.path.join(here, a.new)), os.path.abspath(os.path.join(here, a.ref)),
                                  [d for d in (a.dates or '').split(',') if d] or None)
        finally:
            os.chdir(here)
        lines = report_shelves(res)
    elif a.cmd == 'cycles':
        res = compare_cycles(a.new, a.ref)
        lines = report_cycles(res)
    else:
        if bool(a.cf) == bool(a.scratch):
            raise InputError('split takes --cf DIR (an inversion made before) or --scratch DIR (one to make), one of them')
        if a.scratch:
            plan = split_plan(a.new, a.ref, a.scratch)
            pl = ['== split plan: %d pairs; kept NEW %d, REF %d; dropIfgram differs on %d: %s' % (
                plan['pairs'], plan['kept_new'], plan['kept_ref'], len(plan['differ']), ', '.join(
                    '%s (NEW %s, REF %s)' % (x['pair'], x['new'], x['ref']) for x in plan['differ'][:6])),
                  '   copies %d B into %s (%.1f GiB free there), sets its dropIfgram to REF\'s, runs %s' % (
                      plan['bytes'], plan['cf'], plan['free'] / 2.0 ** 30, plan['command'])]
            for ln in pl:
                print(ln)
            if not a.run:
                print('   plan only: --run makes it (about one inversion of the frame; F3320 took 1 min 34 s, record 119)')
                write_out(out, 'split', dict(plan=dict((k, v) for k, v in plan.items() if k != 'drop_ref')), pl)
                return 0
            if plan['bytes'] > plan['free']:
                raise InputError('%d B to copy, %d B free under %s' % (plan['bytes'], plan['free'], a.scratch))
            rc, log = split_run(plan)
            print('   the inversion: rc %d, log %s' % (rc, log))
            if rc != 0:
                raise InputError('ifgram_inversion.py rc %d (log %s)' % (rc, log))
            cf = plan['cf']
        else:
            cf = os.path.abspath(a.cf)
        res = compare_split(a.new, a.ref, cf)
        res['cf'] = cf
        lines = report_split(res)
    for ln in lines:
        print(ln)
    write_out(out, a.cmd, res, lines)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except InputError as e:
        sys.stderr.write('lp_compare: %s\n' % e)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        sys.stderr.write('lp_compare: %s: %s\n' % (type(e).__name__, e))
        sys.exit(3)
