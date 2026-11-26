#!/usr/bin/env python3
"""linog_map.py: LInOG velocity maps on a satellite base, from a settings file.

    python linog_map.py SETTINGS.yaml            make the map named in the settings file
    python linog_map.py SETTINGS.yaml --check    a quick 150 dpi preview, plus a list of labels that overlap,
                                                 leave the map or sit on a traced area
    python linog_map.py --find "Gapan City, Nueva Ecija"
                                                 look a place up (OpenStreetMap Nominatim) and add it to data/my_places.json

What a map carries (the LInOG map rules, as used in the 2026 reports):
  - the LInOG velocity GeoTIFFs (LOS, m/yr) on a Sentinel-2 cloudless 2024 base (EOX), darkened a little;
  - one velocity scale for every LInOG map: RdYlBu_r, -5 to +5 cm/yr, extended at both ends
    (blue = away from the satellite, sinking; red = toward it, uplift);
  - grid coordinates in degrees and minutes, province lines (GADM 4.1), labelled places;
  - optional: frame outlines, traced sinking areas (a line drawn just outside the blue, never a dot on top of it),
    flight and look (LOS) arrows, north arrow, scale bar, title and credit lines.

Everything a user normally changes is in the settings file; this script should not need editing.
Licence: GPL-3.0-or-later (the LInOG repository). Base tiles: EOX IT Services GmbH, CC BY-NC-SA 4.0 (non-commercial use).
"""
import argparse, glob, io, json, math, os, re, sys, time, urllib.parse, urllib.request, zipfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from matplotlib.patches import Rectangle
import rasterio
import yaml
from PIL import Image
from scipy import ndimage as nd
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box as sbox
from shapely.ops import nearest_points, unary_union

VERSION = "1.1 (26 Nov 2026)"
HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1.0 / 1200.0                      # the LInOG product lattice: 3 arc seconds (about 90 m)
NAVY = "#0B2545"
CMAP_NAME = "RdYlBu_r"
EOX_URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024/default/WGS84/%d/%d/%d.jpg"
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_PHL_1.json.zip"
UA = {"User-Agent": "LInOG-map/1.1 (NIGS UP Diliman research maps)"}
HB = [pe.withStroke(linewidth=2.2, foreground="black", alpha=0.85)]
HB_S = [pe.withStroke(linewidth=1.7, foreground="black", alpha=0.85)]
LINE_HALO = [pe.withStroke(linewidth=2.6, foreground=NAVY, alpha=0.65)]

# Defaults: every key a settings file may leave out. The example files show each one.
DEFAULTS = {
    "output": {"name": "LINOG_MAP", "folder": ".", "formats": ["png", "tif"], "dpi": 400,
               "png_background": "transparent"},
    "title": None,
    "data_folder": None,
    "frames": [],
    "draw_order": ["450", "449", "447", "448"],
    "units": "m/yr",
    "box": "auto",
    "box_margin_deg": 0.05,
    "map_height_in": 4.3,
    "velocity": {"cmap": CMAP_NAME, "vmin": -5.0, "vmax": 5.0,
                 "label": "LOS velocity, cm/yr (ramp removed)",
                 "toward": "toward the\nsatellite\n(uplift)", "away": "away from\nthe satellite\n(sinking)"},
    "basemap": {"zoom": "auto", "darken": 0.80, "desaturate": 0.25},
    "grid": {"every_minutes": 30, "minor_minutes": 15},
    "provinces": True,
    "frame_outlines": False,
    "path_labels": [],
    "trace": {"enabled": False, "level_cm": -1.5, "min_area_km2": 1.0, "smooth_px": 11, "offset_px": 7},
    "places": [],
    "area_labels": [],
    "arrows": {"enabled": True, "heading_deg": -12.0, "at": "lower left"},
    "north_arrow": True,
    "scale_bar_km": "auto",
    "credits": {"velocity": "Velocity: LInOG, ALOS-1 PALSAR, LOS, ramp removed; ALOS PALSAR data © JAXA/METI.",
                "extra": []},
}


# ----------------------------------------------------------------------------------------------------- settings

def merge(d, s):
    out = dict(d)
    for k, v in (s or {}).items():
        out[k] = merge(d[k], v) if isinstance(v, dict) and isinstance(d.get(k), dict) else v
    return out


def load_settings(path):
    with open(path, encoding="utf-8") as f:
        s = yaml.safe_load(f) or {}
    unknown = sorted(set(s) - set(DEFAULTS))
    if unknown:
        sys.exit("settings: unknown key(s) %s (check the spelling; the keys are listed in the guide)" % ", ".join(unknown))
    c = merge(DEFAULTS, s)
    c["_dir"] = os.path.dirname(os.path.abspath(path))
    return c


def rel(c, p):
    p = os.path.expanduser(str(p))
    return p if os.path.isabs(p) else os.path.join(c["_dir"], p)


def cache_dir():
    d = os.path.join(os.path.expanduser("~"), ".linog_map_cache")
    os.makedirs(d, exist_ok=True)
    return d


def say(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------------------------------- frames

FRAME_RE = re.compile(r"P(\d{3})F(\d{4})", re.I)


def frame_files(c):
    """The GeoTIFFs named in 'frames' (paths or wildcard patterns), each with its path number, in drawing order."""
    files = []
    base = rel(c, c["data_folder"]) if c.get("data_folder") else None
    if base and not os.path.isdir(base):
        sys.exit("data_folder: not found: %s (check the path; on Windows write it with / and in quotes)" % base)
    for item in c["frames"]:
        p_ = os.path.expanduser(str(item))
        pat = p_ if os.path.isabs(p_) else (os.path.join(base, p_) if base else rel(c, p_))
        hits = sorted(glob.glob(pat, recursive=True))
        if not hits:
            sys.exit("frames: nothing found for %s" % pat)
        files += [h for h in hits if h.lower().endswith((".tif", ".tiff")) and h not in files]
    if not files:
        sys.exit("frames: the settings list no GeoTIFF")
    out = []
    for f in files:
        m = FRAME_RE.search(os.path.basename(f))
        out.append(dict(path=f, track=m.group(1) if m else "?", name=("P%sF%s" % m.groups()) if m else os.path.basename(f)))
    desc = [r["name"] for r in out if (r["track"] != "?" and int(r["track"]) < 200) or "descending" in r["path"].lower()]
    if desc and len(desc) < len(out):
        sys.exit("frames: ascending and descending frames in one map (%s): they look in opposite directions, so their LOS "
                 "velocities do not join. Make one map for each direction." % ", ".join(desc))
    order = [str(x) for x in c["draw_order"]]
    out.sort(key=lambda r: order.index(r["track"]) if r["track"] in order else -1)   # unknown paths first, listed last on top
    return out


def read_frame(r, scale):
    with rasterio.open(r["path"]) as ds:
        if ds.crs is None or ds.crs.to_epsg() != 4326:
            sys.exit("%s: not in latitude/longitude (EPSG:4326); the LInOG GeoTIFFs are" % r["path"])
        a = ds.read(1).astype("float64")
        if ds.nodata is not None and not np.isnan(ds.nodata):
            a[a == ds.nodata] = np.nan
        a[a == 0] = np.nan
        t, b = ds.transform, ds.bounds
    return a * scale, t, (b.left, b.right, b.bottom, b.top)


def mosaic(frames, W, E, S, N):
    """Frames on the shared 1/1200 degree lattice, drawn over one another in order (the last on top); off-lattice files are resampled."""
    c0, c1, r0, r1 = int(math.floor(W / RES)), int(math.ceil(E / RES)), int(math.ceil(N / RES)), int(math.floor(S / RES))
    out = np.full((r0 - r1, c1 - c0), np.nan)
    for r in frames:
        a, t = r["a"], r["t"]
        if abs(t.a - RES) < 1e-9 and abs(t.e + RES) < 1e-9 and abs(t.c / RES - round(t.c / RES)) < 1e-3:
            fc, fr = int(round(t.c / RES)), int(round(t.f / RES))
            ys, xs = r0 - fr, fc - c0
            Y0, X0, y0, x0 = max(0, -ys), max(0, -xs), max(0, ys), max(0, xs)
            hh, ww = min(a.shape[0] - Y0, out.shape[0] - y0), min(a.shape[1] - X0, out.shape[1] - x0)
            if hh > 0 and ww > 0:
                blk = a[Y0:Y0 + hh, X0:X0 + ww]; ok = np.isfinite(blk)
                out[y0:y0 + hh, x0:x0 + ww][ok] = blk[ok]
        else:                                                   # nearest-neighbour onto the lattice
            lon = (np.arange(c0, c1) + 0.5) * RES; lat = (r0 - np.arange(out.shape[0]) - 0.5) * RES
            cc = np.floor((lon - t.c) / t.a).astype(int); rr = np.floor((lat - t.f) / t.e).astype(int)
            okc = (cc >= 0) & (cc < a.shape[1]); okr = (rr >= 0) & (rr < a.shape[0])
            sub = np.full(out.shape, np.nan)
            sub[np.ix_(okr, okc)] = a[np.ix_(rr[okr], cc[okc])]
            ok = np.isfinite(sub); out[ok] = sub[ok]
    return out, (c0 * RES, c1 * RES, r1 * RES, r0 * RES)


def hull(r, step=4):
    a, t = r["a"], r["t"]
    rr, cc = np.nonzero(np.isfinite(a[::step, ::step]))
    if rr.size < 3:
        return None
    return MultiPoint(np.c_[t.c + (cc * step + 0.5) * t.a, t.f + (rr * step + 0.5) * t.e]).convex_hull


# ---------------------------------------------------------------------------------------------------- base data

def fetch(url, dest, tries=4):
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return dest
    for k in range(tries):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            tmp = dest + ".part"; open(tmp, "wb").write(b); os.replace(tmp, dest)
            return dest
        except Exception as ex:
            say("  download %s: %s; trying again" % (url, ex)); time.sleep(3 * (k + 1))
    sys.exit("could not download %s (is the computer online?)" % url)


def basemap(W, E, S, N, zoom, map_w_px):
    """EOX Sentinel-2 cloudless 2024 (WGS84 tile matrix: level z tiles span 180/2^z degrees, 256 px), cached on disk."""
    if zoom in (None, "auto"):
        need = (E - W) / max(map_w_px, 1)                                  # degrees per output pixel
        zoom = max(6, min(13, int(math.ceil(math.log2(180.0 / 256.0 / need)))))
    z = int(zoom); span = 180.0 / 2 ** z
    c0, c1 = int((W + 180) // span), int((E + 180) // span)
    r0, r1 = int((90 - N) // span), int((90 - S) // span)
    n = (c1 - c0 + 1) * (r1 - r0 + 1)
    if n > 900:
        sys.exit("basemap: %d tiles at level %d; set basemap: zoom: to a smaller number" % (n, z))
    tdir = os.path.join(cache_dir(), "eox_s2c2024"); os.makedirs(tdir, exist_ok=True)
    img = np.zeros(((r1 - r0 + 1) * 256, (c1 - c0 + 1) * 256, 3), np.uint8)
    got = 0
    for r in range(r0, r1 + 1):
        for cc in range(c0, c1 + 1):
            p = os.path.join(tdir, "%d_%d_%d.jpg" % (z, r, cc))
            if not os.path.isfile(p):
                fetch(EOX_URL % (z, r, cc), p); got += 1; time.sleep(0.05)
            img[(r - r0) * 256:(r - r0 + 1) * 256, (cc - c0) * 256:(cc - c0 + 1) * 256] = np.array(Image.open(p).convert("RGB"))
    ext = (-180 + c0 * span, -180 + (c1 + 1) * span, 90 - (r1 + 1) * span, 90 - r0 * span)
    say("  basemap: EOX level %d, %d tiles (%d downloaded now, the rest from %s)" % (z, n, got, tdir))
    return img, ext


def provinces_geojson():
    z = fetch(GADM_URL, os.path.join(cache_dir(), "gadm41_PHL_1.json.zip"))
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".json")][0]
        return json.loads(zf.read(name))


def load_places():
    P = {}
    for f in (os.path.join(HERE, "data", "places.json"), os.path.join(HERE, "data", "my_places.json")):
        if os.path.isfile(f):
            P.update(json.load(open(f, encoding="utf-8")))
    return P


def find_place(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(dict(q=query, format="json", limit=3, countrycodes="ph"))
    res = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
    if not res:
        sys.exit("nothing found for %r; try adding the province, e.g. \"Gapan City, Nueva Ecija\"" % query)
    for k, r in enumerate(res):
        say("%d. %s\n   lat %.5f  lon %.5f" % (k + 1, r["display_name"], float(r["lat"]), float(r["lon"])))
    key = query.split(",")[0].strip()
    f = os.path.join(HERE, "data", "my_places.json")
    mine = json.load(open(f, encoding="utf-8")) if os.path.isfile(f) else {}
    mine[key] = dict(lat=round(float(res[0]["lat"]), 5), lon=round(float(res[0]["lon"]), 5))
    json.dump(mine, open(f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    say("saved the first one as %r in %s (edit the file if another one is right)" % (key, f))


# ---------------------------------------------------------------------------------------------------- the trace

def smooth(a, k):
    v = np.isfinite(a); z = np.where(v, a, 0.0)
    num = nd.uniform_filter(z, k, mode="constant"); den = nd.uniform_filter(v.astype(float), k, mode="constant")
    return np.where(den >= 0.5, num / np.maximum(den, 1e-9), np.nan)


def trace(a, ext, tr):
    """Sinking areas: velocity smoothed over smooth_px x smooth_px pixels at level_cm or less, in patches of min_area_km2 or more;
    the outline is drawn offset_px pixels outside the edge, so it does not cover the blue."""
    from skimage import measure
    k, off = int(tr["smooth_px"]), int(tr["offset_px"])
    s = smooth(a, k)
    m = np.nan_to_num(s, nan=0.0) <= float(tr["level_cm"])
    lab, n = nd.label(m, structure=np.ones((3, 3)))
    lat = ext[3] - (np.arange(a.shape[0]) + 0.5) * RES; lon = ext[0] + (np.arange(a.shape[1]) + 0.5) * RES
    pxkm2 = ((RES * 111.32 * np.cos(np.radians(lat))) * (RES * 110.6))[:, None] * np.ones((1, a.shape[1]))
    areas = nd.sum(pxkm2, lab, index=np.arange(1, n + 1)) if n else []
    ids = [i + 1 for i in range(n) if areas[i] >= float(tr["min_area_km2"])]
    patches = []
    for i in ids:
        mk = lab == i; j = np.argmin(np.where(mk, s, np.inf)); r, cc = np.unravel_index(j, s.shape)
        patches.append(dict(area_km2=round(float(areas[i - 1]), 2), deepest_cm_yr=round(float(s[r, cc]), 2),
                            deepest_lat=round(float(lat[r]), 4), deepest_lon=round(float(lon[cc]), 4)))
    if not ids:
        return Polygon(), patches
    keep = nd.binary_fill_holes(np.isin(lab, ids))
    yy, xx = np.mgrid[-off:off + 1, -off:off + 1]
    dil = nd.binary_fill_holes(nd.binary_dilation(keep, structure=(xx ** 2 + yy ** 2) <= off ** 2))
    g = np.pad(nd.gaussian_filter(dil.astype(float), 1.2), 1)
    polys = []
    for cnt in measure.find_contours(g, 0.5):
        if len(cnt) >= 8:
            pg = Polygon(np.c_[ext[0] + (cnt[:, 1] - 0.5) * RES, ext[3] - (cnt[:, 0] - 0.5) * RES]).buffer(0)
            if pg.area > 0:
                polys.append(pg)
    return unary_union(polys), patches


def geoms(g):
    return [] if g.is_empty else (list(g.geoms) if hasattr(g, "geoms") else [g])


def lines_outside(ax, line, hole, **kw):
    for part in geoms(line.difference(hole) if not hole.is_empty else line):
        if part.geom_type in ("LineString", "LinearRing"):
            x, y = np.asarray(part.coords).T
            ax.plot(x, y, **kw)


# ------------------------------------------------------------------------------------------------------ drawing

def dms(v, lat):
    h = ("N" if v >= 0 else "S") if lat else ("E" if v >= 0 else "W")
    v = abs(v); d = int(math.floor(v + 1e-9)); m = int(round((v - d) * 60))
    if m == 60:
        d, m = d + 1, 0
    return "%d°%02d′%s" % (d, m, h)


def km_per_deg_lon(lat):
    return 111.32 * math.cos(math.radians(lat))


def draw(c, check=False):
    frames = frame_files(c)
    scale = {"m/yr": 100.0, "cm/yr": 1.0, "mm/yr": 0.1}.get(c["units"])
    if scale is None:
        sys.exit("units: one of m/yr, cm/yr, mm/yr (the LInOG GeoTIFFs are m/yr)")
    say("linog_map %s: %d frame(s)" % (VERSION, len(frames)))
    for r in frames:
        r["a"], r["t"], r["ext"] = read_frame(r, scale)
        say("  %s  (path %s)  %s" % (r["name"], r["track"], r["path"]))
    if c["box"] in (None, "auto"):
        mg = float(c["box_margin_deg"])
        W = min(r["ext"][0] for r in frames) - mg; E = max(r["ext"][1] for r in frames) + mg
        S = min(r["ext"][2] for r in frames) - mg; N = max(r["ext"][3] for r in frames) + mg
    else:
        W, E, S, N = (float(x) for x in c["box"])
        if not (W < E and S < N):
            sys.exit("box: write it as [west, east, south, north] in degrees, e.g. [120.80, 121.20, 15.30, 15.65]")
    latm = (S + N) / 2; asp = 1.0 / math.cos(math.radians(latm))
    MH = float(c["map_height_in"]); MW = MH * (E - W) / (N - S) / asp
    L_, R_, T_, B_ = 0.62, 1.00, (0.55 if c["title"] else 0.26), 0.62
    FW, FH = L_ + MW + R_, B_ + MH + T_
    dpi = 150 if check else int(c["output"]["dpi"])
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in ("Arial", "Liberation Sans", "Helvetica", "DejaVu Sans") if f in have), "DejaVu Sans")
    plt.rcParams.update({"font.family": font, "font.size": 7, "text.color": NAVY,
                         "axes.edgecolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY})
    fig = plt.figure(figsize=(FW, FH))
    ax = fig.add_axes([L_ / FW, B_ / FH, MW / FW, MH / FH])
    ax.set_xlim(W, E); ax.set_ylim(S, N); ax.set_aspect(asp)

    # base
    bm = c["basemap"]
    rgb, bext = basemap(W, E, S, N, bm["zoom"], MW * dpi)
    f = rgb.astype(np.float32) / 255.0; gray = f.mean(axis=2, keepdims=True)
    f = float(bm["darken"]) * ((1 - float(bm["desaturate"])) * f + float(bm["desaturate"]) * gray)
    ax.imshow(np.clip(f, 0, 1), extent=bext, origin="upper", interpolation="bilinear", zorder=0, aspect=asp)

    # velocity
    v = c["velocity"]
    cmap = matplotlib.colormaps[v["cmap"]]
    a, ext = mosaic(frames, W - 0.05, E + 0.05, S - 0.05, N + 0.05)
    ax.imshow(np.ma.masked_invalid(a), extent=ext, origin="upper", cmap=cmap, vmin=float(v["vmin"]), vmax=float(v["vmax"]),
              interpolation="nearest", zorder=3, aspect=asp)
    ax.set_xlim(W, E); ax.set_ylim(S, N)

    # traced sinking areas
    tr = c["trace"]
    outline, patches = (trace(a, ext, tr) if tr.get("enabled") else (Polygon(), []))
    hole = outline.buffer(0.004) if not outline.is_empty else Polygon()
    for g in geoms(outline):
        x, y = np.asarray(g.exterior.coords).T
        ax.plot(x, y, color="black", lw=0.8, zorder=9, path_effects=[pe.withStroke(linewidth=1.9, foreground="white", alpha=0.95)])
    if tr.get("enabled"):
        say("  trace: %d patch(es) at %.1f cm/yr or less, %.1f km2 or more" % (len(patches), float(tr["level_cm"]), float(tr["min_area_km2"])))

    # province lines
    if c["provinces"]:
        G = provinces_geojson()
        for feat in G["features"]:
            gm = feat["geometry"]; polys = gm["coordinates"] if gm["type"] == "MultiPolygon" else [gm["coordinates"]]
            for poly in polys:
                ring = np.array(poly[0])
                if ring[:, 0].max() < W - 0.2 or ring[:, 0].min() > E + 0.2 or ring[:, 1].max() < S - 0.2 or ring[:, 1].min() > N + 0.2:
                    continue
                lines_outside(ax, LineString(ring), hole, color="white", lw=0.4, alpha=0.45, zorder=4)

    # frame outlines
    if c["frame_outlines"]:
        sty = {"448": dict(color="white", ls="-", lw=1.0), "449": dict(color="#CFE0EC", ls=(0, (5, 2.2)), lw=1.0),
               "447": dict(color="#CFE0EC", ls=(0, (1.4, 1.6)), lw=1.2), "450": dict(color="white", ls=(0, (6, 2, 1.4, 2)), lw=1.0)}
        for r in frames:
            h = hull(r)
            if h is not None:
                x, y = np.asarray(h.exterior.coords).T
                ax.plot(x, y, zorder=8, path_effects=LINE_HALO, **sty.get(r["track"], dict(color="white", ls="-", lw=1.0)))
    for pl in c["path_labels"]:
        ax.text(float(pl["lon"]), float(pl["lat"]), pl["text"], color="white", fontsize=7.2, fontweight="bold", ha="center",
                va="center", zorder=13, path_effects=HB)

    # grid coordinates
    gstep = float(c["grid"]["every_minutes"]) / 60.0; mstep = float(c["grid"].get("minor_minutes") or 0) / 60.0
    xt = np.arange(math.ceil(W / gstep - 1e-9) * gstep, E + 1e-9, gstep); yt = np.arange(math.ceil(S / gstep - 1e-9) * gstep, N + 1e-9, gstep)
    ax.set_xticks(xt); ax.set_yticks(yt)
    ax.set_xticklabels([dms(x, False) for x in xt], fontsize=6.6); ax.set_yticklabels([dms(y, True) for y in yt], fontsize=6.6)
    if mstep > 0:
        ax.set_xticks(np.arange(math.ceil(W / mstep) * mstep, E + 1e-9, mstep), minor=True)
        ax.set_yticks(np.arange(math.ceil(S / mstep) * mstep, N + 1e-9, mstep), minor=True)
    ax.tick_params(which="both", top=True, right=True, labeltop=True, labelright=False, direction="out", width=0.6, color=NAVY, pad=1.5)
    ax.tick_params(which="major", length=2.5); ax.tick_params(which="minor", length=1.5)
    gkw = dict(color="white", lw=0.4, alpha=0.5, ls=(0, (2, 2)), zorder=6)
    for x in xt:
        lines_outside(ax, LineString([(x, S), (x, N)]), hole, **gkw)
    for y in yt:
        lines_outside(ax, LineString([(W, y), (E, y)]), hole, **gkw)
    for sp in ax.spines.values():
        sp.set_color(NAVY); sp.set_linewidth(0.8)

    # places
    P = load_places()
    for p in c["places"]:
        name = p["name"]
        if "lat" in p and "lon" in p:
            lat, lon = float(p["lat"]), float(p["lon"])
        elif name in P:
            lat, lon = P[name]["lat"], P[name]["lon"]
        else:
            sys.exit("places: %r is not in data/places.json; give lat and lon, or run: python linog_map.py --find \"%s, <province>\"" % (name, name))
        label = p.get("label", name); style = p.get("style", "town")
        dx, dy, ha = float(p.get("dx", 0.03)), float(p.get("dy", 0.0)), p.get("ha", "left")
        if style == "site" and p.get("point_to_trace") and not outline.is_empty:
            q = nearest_points(unary_union([g.exterior for g in geoms(outline)]), Point(lon + dx, lat + dy))[0]   # the edge nearest the label
            ax.annotate(label, xy=(q.x, q.y), xytext=(lon + dx, lat + dy), ha=ha, va="center", fontsize=8.4, fontweight="bold",
                        color=NAVY, zorder=16, bbox=dict(boxstyle="round,pad=0.24", fc="white", ec=NAVY, lw=0.7, alpha=0.95),
                        arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.8, shrinkA=0, shrinkB=0,
                                        path_effects=[pe.withStroke(linewidth=1.9, foreground="white", alpha=0.95)]))
            continue
        if style == "site":
            ax.plot(lon, lat, marker="o", ms=6.2, mfc="white", mec=NAVY, mew=1.8, zorder=15)
            ax.text(lon + dx, lat + dy, label, ha=ha, va="center", fontsize=8.4, fontweight="bold", color=NAVY, zorder=16,
                    bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=NAVY, lw=0.7, alpha=0.95))
        else:
            mk = {"town": ("o", "white", 3.0, 6.8), "small": ("o", "white", 2.4, 5.6),
                  "volcano": ("^", "#FF6B6B", 3.6, 5.6), "peak": ("^", "white", 3.4, 5.6)}.get(style)
            if mk is None:
                sys.exit("places: style %r for %r; use site, town, small, volcano or peak" % (style, name))
            ax.plot(lon, lat, marker=mk[0], color=mk[1], markersize=mk[2], markeredgecolor="black", markeredgewidth=0.6, zorder=12)
            ax.text(lon + dx, lat + dy, label, color="white", fontsize=float(p.get("size", mk[3])), ha=ha, va="center", zorder=13,
                    fontweight="bold" if p.get("bold") else "normal", path_effects=HB_S)
    for t in c["area_labels"]:
        kind = t.get("kind", "province")
        sty = {"province": dict(color="#FFF3B0", fontsize=5.6, fontweight="bold", fontvariant="small-caps"),
               "water": dict(color="#BFE9FF", fontsize=5.8, style="italic"),
               "range": dict(color="#E6EEF5", fontsize=5.6, style="italic"),
               "basin": dict(color="white", fontsize=7.6, style="italic", fontweight="bold"),
               "plain": dict(color="white", fontsize=6.8)}.get(kind)
        if sty is None:
            sys.exit("area_labels: kind %r; use province, water, range, basin or plain" % kind)
        if "size" in t:
            sty["fontsize"] = float(t["size"])
        ax.text(float(t["lon"]), float(t["lat"]), t["text"], ha=t.get("ha", "center"), va="center", rotation=float(t.get("rotation", 0)),
                zorder=11, path_effects=HB_S, **sty)

    # arrows, north, scale
    def arrow(x, y, az, d):
        dx = d * math.sin(math.radians(az)) * asp; dy = d * math.cos(math.radians(az))
        ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y), zorder=14,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.22", color="white", lw=1.6,
                                    path_effects=[pe.withStroke(linewidth=3.2, foreground="black", alpha=0.8)]))
        return x + dx, y + dy
    span = min(E - W, N - S)
    if c["arrows"]["enabled"]:
        hd = float(c["arrows"]["heading_deg"])
        at = c["arrows"].get("at", "lower left")
        # the two arrows' tips from their common tail; the tail is placed so both stay in the chosen corner
        # (an ascending heading points up and right, a descending one down and left: v1.1)
        vec = lambda az, d: (d * math.sin(math.radians(az)) * asp, d * math.cos(math.radians(az)))
        (fdx, fdy), (ldx, ldy) = vec(hd, 0.10 * span), vec(hd + 90.0, 0.08 * span)
        xs, ys = (0.0, fdx, ldx), (0.0, fdy, ldy)
        pad_x, pad_y = 0.05 * (E - W), 0.06 * (N - S)
        ox = W + pad_x - min(xs) if "left" in at else E - 0.24 * (E - W) - max(xs)
        oy = S + pad_y - min(ys) if "lower" in at else N - pad_y - max(ys)
        fx, fy = arrow(ox, oy, hd, 0.10 * span); lx, ly = arrow(ox, oy, hd + 90.0, 0.08 * span)
        up = fdy >= 0
        ax.text(fx, fy + (0.008 if up else -0.008) * span, "Flight", color="white", fontsize=6.0, ha="center",
                va="bottom" if up else "top", zorder=14, path_effects=HB_S)
        right = ldx >= 0
        ax.text(lx + (0.006 if right else -0.006) * span, ly, "LOS", color="white", fontsize=6.8, fontweight="bold",
                ha="left" if right else "right", va="center", zorder=14, path_effects=HB_S)
    if c["north_arrow"]:
        nx_, ny_ = W + (E - W) * 0.94, S + (N - S) * 0.88
        ax.annotate("", xy=(nx_, ny_ + 0.06 * span), xytext=(nx_, ny_ - 0.01 * span), zorder=14,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.25", color="white", lw=1.5,
                                    path_effects=[pe.withStroke(linewidth=3.0, foreground="black", alpha=0.8)]))
        ax.text(nx_, ny_ + 0.065 * span, "N", color="white", fontsize=8.0, fontweight="bold", ha="center", va="bottom", zorder=14, path_effects=HB)
    km = c["scale_bar_km"]
    if km not in (None, False, 0):
        wkm = (E - W) * km_per_deg_lon(S)
        if km == "auto":
            km = next(k for k in (100, 50, 25, 20, 10, 5, 2, 1) if k <= 0.28 * wkm)
        km = float(km); slat = S + 0.03 * (N - S); dl = km / km_per_deg_lon(slat); sx = E - 0.06 * (E - W) - dl; sh = 0.008 * (N - S)
        for i in range(4):
            ax.add_patch(Rectangle((sx + i * dl / 4, slat), dl / 4, sh, facecolor="white" if i % 2 == 0 else "black",
                                   edgecolor="black", lw=0.5, zorder=14))
        for xv, tt in ((sx, "0"), (sx + dl / 2, "%g" % (km / 2)), (sx + dl, "%g km" % km)):
            ax.text(xv, slat + sh + 0.006 * (N - S), tt, color="white", fontsize=6.4, ha="center", va="bottom", zorder=14, path_effects=HB_S)

    # colour bar
    cax = fig.add_axes([(L_ + MW + 0.22) / FW, (B_ + 0.55) / FH, 0.11 / FW, (MH - 1.10) / FH])
    sm = matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(float(v["vmin"]), float(v["vmax"])), cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, extend="both")
    cb.ax.tick_params(labelsize=6.8, colors=NAVY, width=0.6, length=2.5); cb.outline.set_edgecolor(NAVY); cb.outline.set_linewidth(0.6)
    cb.set_label(v["label"], fontsize=7.2, color=NAVY, labelpad=3)
    if tr.get("enabled"):
        cb.ax.axhline(float(tr["level_cm"]), color="black", lw=1.0)
    fig.text((L_ + MW + 0.275) / FW, (B_ + MH - 0.48) / FH, v["toward"], ha="center", va="bottom", fontsize=6.2, fontweight="bold", linespacing=1.05)
    fig.text((L_ + MW + 0.275) / FW, (B_ + 0.48) / FH, v["away"], ha="center", va="top", fontsize=6.2, fontweight="bold", linespacing=1.05)

    # title and credits
    if c["title"]:
        fig.text(L_ / FW, (FH - 0.12) / FH, c["title"], ha="left", va="top", fontsize=10, fontweight="bold")
    lines = [c["credits"]["velocity"],
             "Base: Sentinel-2 cloudless 2024 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2024; CC BY-NC-SA 4.0).",
             "Places: OpenStreetMap (Nominatim)." + (" Provinces: GADM 4.1." if c["provinces"] else "")
             + (" Flight direction approximate (heading %g° from north)." % float(c["arrows"]["heading_deg"]) if c["arrows"]["enabled"] else "")]
    lines += list(c["credits"].get("extra") or [])
    fig.text(0.10 / FW, 0.24 / FH, "\n".join(lines), ha="left", va="center", fontsize=4.7, color="#3C4654", linespacing=1.3)
    return fig, ax, outline, patches, (W, E, S, N)


def audit(fig, ax, outline, box):
    W, E, S, N = box
    fig.canvas.draw()
    inv = ax.transData.inverted(); frame = sbox(W, S, E, N); items = []
    for t in ax.texts:
        if not t.get_text().strip():
            continue
        bp = t.get_bbox_patch(); bb = bp.get_window_extent() if bp is not None else t.get_window_extent()
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        items.append((t.get_text().replace("\n", " "), sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))))
    bad = 0
    for name, b in items:
        if not outline.is_empty and b.intersects(outline):
            say("  ON A TRACED AREA: %s" % name); bad += 1
        if not frame.contains(b):
            say("  OUTSIDE THE MAP:  %s" % name); bad += 1
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][1].intersects(items[j][1]):
                say("  OVERLAP: %s  |  %s" % (items[i][0], items[j][0])); bad += 1
    say("  check: %d label(s), %d to look at" % (len(items), bad))


def main():
    ap = argparse.ArgumentParser(description="LInOG velocity maps from a settings file (see the guide).")
    ap.add_argument("settings", nargs="?", help="the settings file, e.g. examples/coverage_12_frames.yaml")
    ap.add_argument("--check", action="store_true", help="quick preview and label check")
    ap.add_argument("--find", metavar="PLACE", help='look a place up, e.g. --find "Gapan City, Nueva Ecija"')
    o = ap.parse_args()
    if o.find:
        return find_place(o.find)
    if not o.settings:
        ap.error("give a settings file, or --find")
    c = load_settings(o.settings)
    fig, ax, outline, patches, box = draw(c, check=o.check)
    out = c["output"]; folder = rel(c, out["folder"]); os.makedirs(folder, exist_ok=True)
    base = os.path.join(folder, out["name"])
    if o.check:
        audit(fig, ax, outline, box)
        fig.savefig(base + "_CHECK.png", dpi=150, facecolor="white")
        say("wrote %s_CHECK.png" % base)
        return
    dpi = int(out["dpi"]); wrote = []
    for fmt in out["formats"]:
        if fmt == "png":
            tr = out.get("png_background", "transparent") == "transparent"
            fig.savefig(base + ".png", dpi=dpi, transparent=tr, facecolor=None if tr else "white"); wrote.append(base + ".png")
        elif fmt == "pdf":
            fig.savefig(base + ".pdf", dpi=dpi, facecolor="white"); wrote.append(base + ".pdf")
        elif fmt in ("tif", "tiff"):
            buf = io.BytesIO(); fig.savefig(buf, dpi=dpi, facecolor="white", format="png"); buf.seek(0)
            Image.open(buf).convert("RGB").save(base + ".tif", compression="tiff_lzw", dpi=(dpi, dpi)); wrote.append(base + ".tif")
        else:
            sys.exit("output formats: png, tif or pdf")
    if patches:
        json.dump(patches, open(base + "_traced.json", "w"), indent=1); wrote.append(base + "_traced.json")
    for w in wrote:
        say("wrote %s" % w)


if __name__ == "__main__":
    main()
