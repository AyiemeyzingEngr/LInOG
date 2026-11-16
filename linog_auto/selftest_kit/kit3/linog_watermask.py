#!/usr/bin/env python3
"""linog_watermask.py <frame_dir> (--apply | --outdir DIR)

LInOG water and swath-edge masks, gates G22 (finding N60) and G23 (WM-D3),
23-24 September 2026. Rule v2 = rule v1 (water) + G23 (swath edge).

Why: ISCE2's Goldstein filter (alpha 0.8, 32 x 32 px windows, about 2.8 km)
spreads land phase into near-shore water, and nothing in the chain masks water
(ISCE2's createWaterMask is stripped at step 09, MintPy waterMaskFile = no).
Water pixels up to 2.3-2.6 km offshore therefore pass minTempCoh 0.7 and reach
every product. Their median temporal coherence (0.864) is above that of land
more than 3 km inland, so no coherence threshold removes them.

Rule v1: water bodies = SRTM-flat surfaces of geometryRadar.h5 height (5 x 5
std < 1 cm, then a 3 x 3 opening against the int16 sea-surface steps). For each
body holding valid pixels, the reference is the median amplitude (dB, median of
10 pairs x 2 bands of Igrams/*/*.amp) of the body's OWN decorrelated pixels
(>= 20 needed); valid pixels less than 6 dB above it are masked, brighter ones
are kept and flagged (piers, rocks, land). Fallback: land ring 0.2-1 km,
masked if more than 6 dB darker. A body at >= 60 m must be >= 3 dB darker than
its ring or it is kept whole (flat void-fill land).

G23 (rule v2): along each grid edge, the median land amplitude at offsets 0-31 px
(the edge less 16 px at each end, >= 20 land px, same amplitude as above) minus
the interior land median (px >= 32 from every edge, off the flat bodies). Leading
offsets with amplitude on less than half the edge are no-data; the run of offsets
after them at least 6 dB below the interior is the dark strip, taken only if its
first offset is at least 20 dB below and it is at most 16 px wide (a darker band
of terrain is not a strip). Both are masked. WM-D3 found such a strip 6-9 px wide
at the near-range edge of 10 of the 12 frames: 35-55 dB below the interior, its
phase after the Goldstein filter is the neighbours' phase (the N60 mechanism).
Flags 6 (valid, masked in a strip) and 7 (strip, already invalid).

--outdir DIR   dry run: writes the mask products and the would-be masks to DIR;
               the frame is not touched.
--apply        backs up both masks to mintpy/watermask/*.orig.h5, then writes
               the mask into mintpy/maskTempCoh.h5 and, one second later,
               mintpy/geo/geo_maskTempCoh.h5 (so Phase 6's geocode --update
               keeps it), and writes mintpy/watermask/summary.json last.
               A mask already carrying rule v2 is left alone (exit 0 when it
               still matches summary.json). A mask carrying an older rule is
               redone from the originals in mintpy/watermask/ after checking
               that they reproduce the frame's masks under the recorded flags;
               the old record moves to mintpy/watermask_superseded_<UTC>/.
               A dry run on such a frame also starts from those originals.
Run AFTER the last smallbaselineApp call (the driver's refpix), which would
rewrite the masks without it, and BEFORE Phase 6. Exit 0 on success, 1 otherwise.
"""
import argparse, glob, hashlib, json, os, shutil, subprocess, sys, time
import xml.etree.ElementTree as ET
import numpy as np, h5py
from scipy import ndimage as ndi
from mintpy.utils import readfile, writefile

ATTR = 'LINOG_WATERMASK'
RULE_V1 = ('LInOG water mask v1 (G22, 2026-09-24): SRTM-flat bodies (5x5 std<1 cm, 3x3 opening); '
        'own reference = median amplitude of the body\'s decorrelated px (>=20), valid px with D<6 dB masked, '
        'D>=6 dB kept+flagged; fallback land ring 0.2-1 km, masked if >6 dB darker; '
        'bodies at >=60 m must be >=3 dB darker than their ring, else kept+flagged')
RULE = ('LInOG masks v2 (G22 water + G23 swath edge, 2026-09-24): ' + RULE_V1.split(': ', 1)[1] + '; '
        'G23: per grid edge, no-data offsets plus the run of offsets whose median land amplitude is >=6 dB below the '
        'interior land median (px >=32 from every edge), if its first offset is >=20 dB below and it is <=16 px wide, masked')
LEGEND = {0: 'not on an SRTM-flat water body', 1: 'valid, MASKED as water', 2: 'water body, already invalid',
          3: 'valid on water, KEPT (>= 6 dB above its water)', 4: 'valid, MASKED (no amplitude reference)',
          5: 'body at >=60 m not water-like, KEPT', 6: 'valid, MASKED in a swath-edge strip (G23)',
          7: 'swath-edge strip, already invalid'}
MASKED = (1, 2, 4, 6, 7)


def die(msg):
    print('*** ABORT:', msg); sys.exit(1)


def md5file(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def has_attr(p):
    with h5py.File(p, 'r') as f:
        return ATTR in f.attrs


def attr_val(p):
    with h5py.File(p, 'r') as f:
        v = f.attrs.get(ATTR)
    return v.decode() if isinstance(v, bytes) else v


def edge_strips(h, A, water, la, lo, NMAX=32, DARK=-6., DEEP=-20., WMAX=16, CORE=32, TRIM=16, MINPX=20):
    """G23 (WM-D3's profile): per grid edge, the no-data offsets and the dark run; returns the strip mask."""
    L, Wd = h.shape; land = np.isfinite(h) & ~water; fa = np.isfinite(A)
    core = np.zeros(h.shape, bool); core[CORE:L - CORE, CORE:Wd - CORE] = True
    ref = core & land & fa
    if ref.sum() < 1000:
        return None
    Aint = float(np.median(A[ref])); rel = A - Aint
    ew = 'W' if np.nanmean(lo[:, :5]) < np.nanmean(lo[:, -5:]) else 'E'
    ns = 'S' if np.nanmean(la[:5]) < np.nanmean(la[-5:]) else 'N'
    opp = {'W': 'E', 'E': 'W', 'S': 'N', 'N': 'S'}
    E = [(f'col 0 ({ew})', lambda k: (slice(None), k), lambda k: (slice(TRIM, L - TRIM), k)),
         (f'col {Wd - 1} ({opp[ew]})', lambda k: (slice(None), Wd - 1 - k), lambda k: (slice(TRIM, L - TRIM), Wd - 1 - k)),
         (f'row 0 ({ns})', lambda k: (k, slice(None)), lambda k: (k, slice(TRIM, Wd - TRIM))),
         (f'row {L - 1} ({opp[ns]})', lambda k: (L - 1 - k, slice(None)), lambda k: (L - 1 - k, slice(TRIM, Wd - TRIM)))]
    strip = np.zeros(h.shape, bool); info = []
    for name, full, trim in E:
        med, finf = [], []
        for k in range(NMAX):
            ix = trim(k); lk = land[ix] & fa[ix]
            med.append(float(np.median(rel[ix][lk])) if lk.sum() >= MINPX else np.nan)
            finf.append(float(fa[full(k)].mean()))
        nd = 0
        while nd < NMAX and finf[nd] < 0.5: nd += 1
        dk = 0
        while nd + dk < NMAX and np.isfinite(med[nd + dk]) and med[nd + dk] <= DARK: dk += 1
        note = ''
        if dk and not (med[nd] <= DEEP and dk <= WMAX):
            note = f'{dk} px run not taken: first offset {med[nd]:+.0f} dB, needs {DEEP:+.0f} dB or less and at most {WMAX} px'
            dk = 0
        for k in range(nd + dk):
            strip[full(k)] = True
        info.append(dict(edge=name, nodata=nd, dark=dk, note=note,
                         profile_db=[None if not np.isfinite(v) else round(v, 1) for v in med[:12]]))
    return Aint, rel, strip, info, int(ref.sum())


def flat_masks(h):
    """Identical to the census classifier (Blocks 3-6) and the 23 Sept pilot."""
    fin = np.isfinite(h); h0 = np.where(fin, h, 0.0)
    w = ndi.uniform_filter(fin.astype(float), 5)
    s1 = ndi.uniform_filter(h0, 5); s2 = ndi.uniform_filter(h0 * h0, 5)
    with np.errstate(invalid='ignore', divide='ignore'):
        mu = s1 / w; sd = np.sqrt(np.clip(s2 / w - mu * mu, 0, None))
    centre = fin & (w > 0.6) & (sd < 0.01)
    box = np.ones((5, 5), bool)
    lo = ndi.binary_dilation(centre & (h0 < 60), box) & fin
    lo = fin & ~ndi.binary_opening(fin & ~lo, structure=np.ones((3, 3), bool))
    hi = ndi.binary_dilation(centre & (h0 >= 60), box) & fin & ~lo
    return lo, hi


def isce_amp(p):
    m = {pr.get('name'): pr.find('value').text for pr in ET.parse(p + '.xml').getroot().findall('property')
         if pr.find('value') is not None}
    W_, L_, nb = int(m['width']), int(m['length']), int(m['number_bands'])
    a = np.fromfile(p, dtype='<f4' if m.get('byte_order', 'l') == 'l' else '>f4')
    if m['data_type'].upper() != 'FLOAT' or a.size != W_ * L_ * nb: return None
    s = m['scheme'].upper()
    return a.reshape(L_, W_, nb).transpose(2, 0, 1) if s == 'BIP' else a.reshape(L_, nb, W_).transpose(1, 0, 2) if s == 'BIL' else a.reshape(nb, L_, W_)


def amp_median(igdir, shape, nmax=10):
    amps = sorted(glob.glob(f'{igdir}/*/*.amp')); stack = []; used = 0
    for p in amps[::max(1, len(amps) // nmax)][:nmax]:
        if not os.path.isfile(p + '.xml'): continue
        try:
            a = isce_amp(p)
        except Exception:
            continue
        if a is None or a.shape[1:] != shape: continue
        stack += [20 * np.log10(np.where(b > 0, b, np.nan)) for b in a]; used += 1
    return (np.nanmedian(np.array(stack), axis=0) if stack else None), len(amps), used


def write_mask(path, arr):
    with h5py.File(path, 'r+') as f:
        dn = 'mask' if 'mask' in f else [k for k in f.keys() if getattr(f[k], 'ndim', 0) == 2][0]
        if f[dn].shape != arr.shape:
            raise SystemExit(f'*** ABORT: {path} dataset {dn} shape {f[dn].shape} != {arr.shape}')
        f[dn][...] = arr.astype(f[dn].dtype)
        f.attrs[ATTR] = RULE


ap = argparse.ArgumentParser(description='LInOG water and swath-edge masks (G22 + G23). See the module docstring.')
ap.add_argument('frame_dir')
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument('--apply', action='store_true', help='write the water mask into the frame')
g.add_argument('--outdir', help='dry run: write the products here, touch nothing in the frame')
a = ap.parse_args()
W = os.path.realpath(a.frame_dir.rstrip('/'))
M, G = f'{W}/mintpy', f'{W}/mintpy/geo'
RADAR, GEO = f'{M}/maskTempCoh.h5', f'{G}/geo_maskTempCoh.h5'
NEED = [RADAR, GEO, f'{M}/inputs/geometryRadar.h5', f'{M}/timeseries.h5', f'{M}/smallbaselineApp.cfg']
miss = [p for p in NEED if not os.path.isfile(p)]
if miss:
    die('missing: ' + ', '.join(miss))
print(f'linog_watermask.py md5 {md5file(os.path.abspath(__file__))} | frame {W} | mode {"APPLY" if a.apply else "dry run"}')

# ---------------------------------------------------------------- 0 state
BASE_R, BASE_G, PREV, SUPER = RADAR, GEO, None, None


def originals_check(wd):
    """The masks carry an earlier write of this tool: its originals must reproduce them under its flags."""
    need = [f'{wd}/{x}' for x in ('maskTempCoh.orig.h5', 'geo_maskTempCoh.orig.h5', 'waterFlag.h5', 'geo_waterFlag.h5', 'summary.json')]
    miss = [p for p in need if not os.path.isfile(p)]
    if miss:
        die(f'the masks carry {ATTR} but ' + ', '.join(miss) + ' missing; nothing written')
    s = json.load(open(f'{wd}/summary.json'))
    for rel_, cur in (('maskTempCoh.h5', RADAR), ('geo/geo_maskTempCoh.h5', GEO)):
        if s.get('md5', {}).get(rel_) != md5file(cur):
            die(f'{rel_} was rewritten after the last mask write (md5 != {wd}/summary.json); nothing written')
    for orig, fl, cur in (('maskTempCoh.orig.h5', 'waterFlag.h5', RADAR), ('geo_maskTempCoh.orig.h5', 'geo_waterFlag.h5', GEO)):
        o = readfile.read(f'{wd}/{orig}', print_msg=False)[0].astype(bool)
        f_ = readfile.read(f'{wd}/{fl}', datasetName='waterFlag', print_msg=False)[0]
        c = readfile.read(cur, print_msg=False)[0].astype(bool)
        if o.shape != c.shape or not np.array_equal(o & ~np.isin(f_, MASKED), c):
            die(f'{wd}/{orig} under {fl} does not reproduce {cur}; nothing written')
    print(f'originals in {wd} reproduce both masks under the recorded flags')
    return s


if a.apply:
    OUT = f'{M}/watermask'
    if has_attr(RADAR):
        sj = f'{OUT}/summary.json'
        s = json.load(open(sj)) if os.path.isfile(sj) else {}
        ok = s.get('md5', {}).get('maskTempCoh.h5') == md5file(RADAR)
        if attr_val(RADAR) == RULE:
            print(f'already applied: maskTempCoh.h5 carries {ATTR} rule v2; its md5 {"matches" if ok else "DOES NOT MATCH"} {sj}')
            sys.exit(0 if ok else 1)
        if not has_attr(GEO):
            die('maskTempCoh.h5 carries an older mask rule but geo/geo_maskTempCoh.h5 carries none; nothing written')
        PREV = originals_check(OUT).get('rule', '?')
        SUPER = f'{M}/watermask_superseded_{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}'
        os.rename(OUT, SUPER)
        BASE_R, BASE_G = f'{SUPER}/maskTempCoh.orig.h5', f'{SUPER}/geo_maskTempCoh.orig.h5'
        print(f'masks carry an older rule ({PREV[:40]}...): moved {OUT} to {SUPER}; rule v2 starts again from its originals')
    elif has_attr(GEO):
        die('geo/geo_maskTempCoh.h5 carries the water mask but maskTempCoh.h5 does not (MintPy rewrote the radar mask). '
            'Restore geo/geo_maskTempCoh.h5 from mintpy/watermask/geo_maskTempCoh.orig.h5, then run again.')
    if os.path.lexists(OUT):
        dst = f'{M}/watermask_superseded_{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}'
        os.rename(OUT, dst)
        print(f'masks carry no water mask but {OUT} exists (MintPy regenerated the masks): moved it to {dst}')
else:
    OUT = os.path.realpath(a.outdir)
    if os.path.lexists(OUT):
        die(f'{OUT} exists; a dry run never overwrites')
    if has_attr(RADAR) or has_attr(GEO):
        if not (has_attr(RADAR) and has_attr(GEO)):
            die('only one of the two masks carries the mask attribute; nothing run')
        PREV = originals_check(f'{M}/watermask').get('rule', '?')
        BASE_R, BASE_G = f'{M}/watermask/maskTempCoh.orig.h5', f'{M}/watermask/geo_maskTempCoh.orig.h5'
        print(f'masks carry {"rule v2" if attr_val(RADAR) == RULE else "an older rule"} ({PREV[:40]}...); '
              f'the dry run starts from the originals in mintpy/watermask/')

# ---------------------------------------------------------------- 1 radar inputs
rd = lambda f, d=None: readfile.read(f, datasetName=d, print_msg=False)[0]
GEOM = f'{M}/inputs/geometryRadar.h5'
h = rd(GEOM, 'height').astype(float); la = rd(GEOM, 'latitude').astype(float); lo = rd(GEOM, 'longitude').astype(float)
mk = rd(BASE_R).astype(bool)
if not (h.shape == la.shape == lo.shape == mk.shape):
    die(f'shape mismatch: height {h.shape} lat {la.shape} lon {lo.shape} maskTempCoh {mk.shape}')
h[np.abs(h) > 1e5] = np.nan; la[la == 0] = np.nan; lo[lo == 0] = np.nan
fin = np.isfinite(h); valid = mk & fin
k = 111320.
az = np.nanmedian(np.hypot(np.diff(la, axis=0) * k, np.diff(lo, axis=0) * k * np.cos(np.deg2rad(la[:-1]))))
rg = np.nanmedian(np.hypot(np.diff(la, axis=1) * k, np.diff(lo, axis=1) * k * np.cos(np.deg2rad(la[:, :-1]))))
wl, wh = flat_masks(h); water = wl | wh
A, na, used = amp_median(f'{W}/Igrams', h.shape)
if A is None:
    die(f'no readable .amp of shape {h.shape} ({na} found)')
print(f'radar grid {h.shape[0]} x {h.shape[1]}, px {az:.1f} m az x {rg:.1f} m rg | amplitude: median of {used} pairs x 2 bands ({na} .amp files)')
print(f'valid (maskTempCoh) {int(mk.sum())} px | SRTM-flat water {int(water.sum())} px, valid on it {int((valid & water).sum())}')

# ---------------------------------------------------------------- 2 per-body decision
lab, n = ndi.label(water, structure=np.ones((3, 3), bool))
objs = ndi.find_objects(lab)
nval = ndi.sum(valid, lab, np.arange(1, n + 1)) if n else np.array([])
flag = np.zeros(h.shape, np.uint8); flag[water] = 2
mpx = int(np.ceil(1050. / min(az, rg))) + 2
rows = []
for i in np.nonzero(nval > 0)[0]:
    sl = objs[i]
    y0, y1 = max(sl[0].start - mpx, 0), min(sl[0].stop + mpx, h.shape[0])
    x0, x1 = max(sl[1].start - mpx, 0), min(sl[1].stop + mpx, h.shape[1])
    c = lab[y0:y1, x0:x1] == i + 1
    Ab = A[y0:y1, x0:x1]; fa = np.isfinite(Ab)
    vb = valid[y0:y1, x0:x1] & c
    dout = ndi.distance_transform_edt(~c, sampling=(az, rg)) / 1000.
    ring = fin[y0:y1, x0:x1] & ~water[y0:y1, x0:x1] & (dout > 0.2) & (dout <= 1.0) & fa
    ref = c & ~valid[y0:y1, x0:x1] & fa
    hmed = float(np.nanmedian(h[y0:y1, x0:x1][c]))
    cls = 'lo' if hmed < 60 else 'hi'
    Aring = float(np.nanmedian(Ab[ring])) if ring.sum() >= 20 else np.nan
    Abody = float(np.nanmedian(Ab[c & fa])) if (c & fa).any() else np.nan
    con = Abody - Aring
    fb = flag[y0:y1, x0:x1]
    if cls == 'hi' and not (con <= -3):
        meth = 'GUARD'; fb[c] = 5; Dv = np.array([np.nan])
    else:
        if ref.sum() >= 20:
            meth = 'own'; D = Ab - float(np.nanmedian(Ab[ref])); thr = 6.
        elif ring.sum() >= 20:
            meth = 'ring'; D = Ab - Aring; thr = -6.
        else:
            meth = 'none'; D = None
        if D is None:
            fb[vb & fa] = 4
            Dv = np.array([np.nan])
        else:
            fb[vb & fa & (D < thr)] = 1; fb[vb & fa & (D >= thr)] = 3
            Dv = D[vb & fa]
        fb[vb & ~fa] = 4
    fv = fb[vb]
    rows.append((int(vb.sum()), int(i) + 1, cls, float(np.nanmean(la[y0:y1, x0:x1][c])), float(np.nanmean(lo[y0:y1, x0:x1][c])),
                 c.sum() * az * rg / 1e6, int(ref.sum()), meth, con, float(np.nanmedian(Dv)) if np.isfinite(Dv).any() else np.nan,
                 int(np.isin(fv, (1, 4)).sum()), int(np.isin(fv, (3, 5)).sum())))
rows.sort(reverse=True)
print('bodies holding valid px (D p50 = valid px minus own water, or minus ring for method ring):')
print('  body  cls   lat      lon     area_km2  valid   ref_px  method  body-ring_dB  D_p50_dB  masked  kept')
for r in rows[:15]:
    print(f'  {r[1]:4d}  {r[2]:3s} {r[3]:7.3f} {r[4]:8.3f} {r[5]:9.2f} {r[0]:6d} {r[6]:7d}  {r[7]:6s} {r[8]:12.1f} {r[9]:9.1f} {r[10]:7d} {r[11]:5d}')
if len(rows) > 15:
    rest = rows[15:]
    print(f'  ... {len(rest)} more bodies: valid {sum(r[0] for r in rest)}, masked {sum(r[10] for r in rest)}, kept {sum(r[11] for r in rest)}')
# ---------------------------------------------------------------- 2b swath-edge strips (G23)
eg = edge_strips(h, A, water, la, lo)
if eg is None:
    die('fewer than 1000 interior land px with amplitude: no G23 reference; nothing written')
Aint, rel, strip, einfo, nref = eg
f_w = flag.copy()
flag[strip & valid & np.isin(flag, (0, 3, 5))] = 6
flag[strip & ~valid & (flag == 0)] = 7
print(f'edge strips (G23; interior land median {Aint:.1f} dB over {nref} px): '
      + ' | '.join(f"{e['edge']} no-data {e['nodata']} dark {e['dark']}" + (f" ({e['note']})" if e['note'] else '') for e in einfo))
for e in einfo:
    if e['nodata'] or e['dark']:
        print(f"  {e['edge']} land dB minus interior, offsets 0-11: " + ' '.join('..' if v is None else f'{v:+.0f}' for v in e['profile_db']))
print(f'  valid px masked in the strips (flag 6) {int((flag == 6).sum())}, of them on water kept by G22 '
      f'{int(((flag == 6) & np.isin(f_w, (3, 5))).sum())}; invalid px in the strips (flag 7) {int((flag == 7).sum())}')
keep = ~np.isin(flag, MASKED)
new = mk & keep
fa_ = np.isfinite(A)
dd = ndi.distance_transform_edt(np.pad(fa_, 1, constant_values=False))[1:-1, 1:-1] - 1
deep = fa_ & new & (rel <= -20.)
census = dict(near=int((deep & (dd < 10)).sum()), far=int((deep & (dd >= 10)).sum()))
print(f"  valid px 20 dB or more below the interior after the masks: within 10 px of an edge or no-data {census['near']}, farther {census['far']}")
cnt = {c: int(((flag == c) & (mk if c not in (2, 7) else True)).sum()) for c in LEGEND}
print('radar flag census (valid px unless noted):')
for c, t in LEGEND.items():
    print(f'  {c}  {t:48s} {cnt[c]:8d}' + ('  (all px)' if c in (2, 7) else ''))
print(f'radar maskTempCoh: {int(mk.sum())} -> {int(new.sum())} px  (removed {int((mk & ~new).sum())})')

# ---------------------------------------------------------------- 3 reference pixel
ta = readfile.read_attribute(f'{M}/timeseries.h5')
if 'REF_Y' not in ta or 'REF_X' not in ta:
    die('timeseries.h5 carries no REF_Y/REF_X')
ry, rx = int(ta['REF_Y']), int(ta['REF_X'])
print(f'reference pixel y/x {ry}/{rx}, REF_DATE {ta.get("REF_DATE")}: flag {flag[ry, rx]}, valid before {bool(mk[ry, rx])} after {bool(new[ry, rx])}')
if not new[ry, rx]:
    die('the water mask would remove the reference pixel; nothing written to the frame')

# ---------------------------------------------------------------- 4 products, geocoded flag, grid check
os.makedirs(OUT)
if a.apply:
    shutil.copy2(BASE_R, f'{OUT}/maskTempCoh.orig.h5'); shutil.copy2(BASE_G, f'{OUT}/geo_maskTempCoh.orig.h5')
am = dict(readfile.read_attribute(RADAR)); am['FILE_TYPE'] = 'mask'
for kk in ('DATA_TYPE', 'FILE_PATH', 'PROCESSOR_VERSION'):
    am.pop(kk, None)
writefile.write({'waterFlag': flag}, out_file=f'{OUT}/waterFlag.h5', metadata=am, print_msg=False)
writefile.write({'mask': keep}, out_file=f'{OUT}/waterMask.h5', metadata=am, print_msg=False)
cmd = [sys.executable, '-m', 'mintpy.cli.geocode', f'{OUT}/waterFlag.h5', f'{OUT}/waterMask.h5',
       '-l', 'inputs/geometryRadar.h5', '-t', 'smallbaselineApp.cfg', '--outdir', OUT]
r = subprocess.run(cmd, cwd=M, capture_output=True, text=True)
open(f'{OUT}/geocode.log', 'w').write(r.stdout + r.stderr)
if r.returncode:
    print(r.stdout[-2000:], r.stderr[-2000:]); die(f'geocode rc {r.returncode}; masks in the frame untouched')
ga = readfile.read_attribute(GEO)
wa = readfile.read_attribute(f'{OUT}/geo_waterFlag.h5')
bad = [kk for kk in ('LENGTH', 'WIDTH', 'Y_FIRST', 'X_FIRST', 'Y_STEP', 'X_STEP')
       if abs(float(ga[kk]) - float(wa[kk])) > 1e-9 * max(1., abs(float(ga[kk])))]
print('geo grid of the geocoded flag vs geo_maskTempCoh: ' + ('IDENTICAL' if not bad else 'DIFFERS in ' + ', '.join(bad)))
if bad:
    die('grid mismatch: ' + '; '.join(f'{kk} {ga[kk]} vs {wa[kk]}' for kk in bad) + '; masks in the frame untouched')
gflag = rd(f'{OUT}/geo_waterFlag.h5', 'waterFlag')
gold = rd(BASE_G).astype(bool)
gnew = gold & ~np.isin(gflag, MASKED)
gcnt = {c: int(((gflag == c) & gold).sum()) for c in LEGEND}
print(f'geo geo_maskTempCoh: {int(gold.sum())} -> {int(gnew.sum())} px  (removed {int((gold & ~gnew).sum())}: '
      f'flag1 {gcnt[1]}  flag2 {gcnt[2]}  flag4 {gcnt[4]}  flag6 {gcnt[6]}  flag7 {gcnt[7]}) | kept on water: flag3 {gcnt[3]}  flag5 {gcnt[5]}')
print(f'  consistency: radar-valid water px that geo marks invalid {int(((gflag == 1) & ~gold).sum())}; '
      f'radar-invalid water px that geo marks valid {gcnt[2]} (removed as water)')

# ---------------------------------------------------------------- 5 write (apply: in place, geo last) and record
if a.apply:
    tr, tg = RADAR, GEO
else:
    tr, tg = f'{OUT}/maskTempCoh.wm.h5', f'{OUT}/geo_maskTempCoh.wm.h5'
    shutil.copy2(RADAR, tr); shutil.copy2(GEO, tg)
write_mask(tr, new)
time.sleep(1.1)
write_mask(tg, gnew)
summ = dict(tool='linog_watermask.py', tool_md5=md5file(os.path.abspath(__file__)), applied=bool(a.apply), frame=W,
            utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), rule=RULE, legend=LEGEND,
            radar_before=int(mk.sum()), radar_after=int(new.sum()), radar_flags=cnt,
            geo_before=int(gold.sum()), geo_after=int(gnew.sum()), geo_flags=gcnt, ref_yx=[ry, rx],
            bodies=[dict(body=r[1], cls=r[2], lat=round(r[3], 4), lon=round(r[4], 4), valid=r[0], method=r[7],
                         masked=r[10], kept=r[11]) for r in rows],
            edge=dict(interior_db=round(Aint, 2), interior_px=nref, strips=einfo, masked_valid=int((flag == 6).sum()),
                      strip_invalid=int((flag == 7).sum()), deep_after=census),
            base=dict(radar=BASE_R, geo=BASE_G), rule_before=PREV, superseded=SUPER,
            md5={'maskTempCoh.h5': md5file(tr), 'geo/geo_maskTempCoh.h5': md5file(tg)})
json.dump(summ, open(f'{OUT}/summary.json', 'w'), indent=1)
print(f'wrote {tr} and {tg}; record {OUT}/summary.json')
