#!/usr/bin/env python3
"""
linog_reg_common.py -- shared machinery for G7 (coarse) and G10 (fine).
LInOG, 29 August 2026.

Written as ONE module because N41's root cause was the two gates drifting
apart: G7 gained MIN_FILL in v3 (N35) and G10 never did, so the same defect
was half-fixed for a month. A change here lands in both gates or in neither.

EVERY THRESHOLD BELOW WAS READ OFF A MEASUREMENT, not chosen.
Source: LINOG_N41_CALIBRATION_20260829.md, three frames and two paths
(p447 f0300 water, p447 f0310, p448 f0320), probe md5 c72ea8b35928a44b.

  peak significance (C.max()-C.mean())/C.std()   REJECTED as a threshold.
      lowest on a fully-correct window 5.14, highest on a fully-wrong one
      5.20. It overlaps. Inside one window it is near-constant across every
      date including the failures, because it measures how correlatable the
      WINDOW is, not whether a date registered. Computed and printed for the
      record; never used to decide.

  peak / second peak, suppression +/-16          ADOPTED, cut at 1.25.
      good >= 1.28, bad <= 1.20, consistent on all three frames. At +/-3 the
      "second peak" is the shoulder of the first and everything reads
      1.00-1.20 -- which is how this statistic was nearly discarded.

  window selection    DEM std alone picks frame-edge windows where most
      secondaries are partial. Needs, together: DEM texture, reference
      amplitude against the frame's own median, and a COUNT of secondaries at
      full fill (>= n-1, so one off-frame granule does not veto a window).

  residual            tested against the window MEDIAN, not zero. p447 f0300
      carries a frame-wide -1 to -2 sample azimuth bias; median-centring turns
      its 23-of-25 window into 25 of 25. Same construction G21 uses.

  20101213 and its class are NOT caught here and must not be claimed. G7 and
      G10 read RESAMPLED products, so run_03 has already applied the granule's
      geometric offset. An off-frame acquisition belongs to G21 and to per-date
      coherence.
"""
import glob, json, os, re, sys
import numpy as np

N          = 512     # window edge, the geometry the calibration used
MIN_FILL   = 0.90    # per-date patch fill (N35, G7 v3, unchanged)
SEL_FILL   = 0.99    # a window is viable only where coverage is essentially total
ALLOW_MISS = 1       # secondaries permitted below SEL_FILL when selecting a window
SUPPRESS   = 16      # peak suppression radius for the second-peak search
RATIO_MIN  = 1.25    # measured gap: good >= 1.28, bad <= 1.20
AMP_FRAC   = 0.50    # ref window amplitude vs the FRAME's P75, not vs the candidates
DEM_MIN    = 1.0     # metres of relief in a window; void-fill reads exactly 0.00
AMP_GRID   = 6       # spread sample, AMP_GRID x AMP_GRID positions, for the frame scale
TOL        = 2       # residual tolerance in reference samples, AFTER median-centring
QUORUM     = 3       # windows that must vote
# Search DEPTH only: NCAND changes WHICH windows are considered, never whether
# one passes -- DEM_MIN, SEL_FILL, AMP_FRAC and the nfull >= n-ALLOW_MISS bar
# are applied per window regardless. Default 20 = the N41 calibration.
NCAND      = int(os.environ.get("LINOG_REG_NCAND", "20"))
NWIN       = 5       # viable windows kept
FILLROWS   = 64      # rows sampled for the cheap fill test


def parse_inject(argv):
    """--inject <dy>,<dx>,<DATE>  -- the gate's own negative control.

    Eleven runs over six frames all passed, so the fix had never been observed
    FAILING a real fault. This shifts one date's patch by a known amount in
    memory, after reading and before correlating. Nothing on disk is touched.
    If the gate does not flag an injected shift on a frame it has just passed,
    the gate is broken and says so."""
    for i, a in enumerate(argv):
        if a == "--inject" and i + 1 < len(argv):
            try:
                dy, dx, d = argv[i + 1].split(",")
                return argv[:i] + argv[i + 2:], (int(dy), int(dx), d)
            except Exception:
                sys.exit("*** --inject wants <dy>,<dx>,<DATE>, e.g. --inject 4,0,20091227")
    return argv, None


def die(msg):
    print("*** %s" % msg)
    sys.exit(2)


def xml_int(path, name):
    if not os.path.exists(path):
        return None
    m = re.search(r'name="%s".*?<value>(\d+)' % name, open(path).read(), re.S)
    return int(m.group(1)) if m else None


def resolve_reference(ref, candidates):
    """Return (path, width, how). Width comes from the .slc.xml where one exists;
    otherwise it is inferred from the byte count and printed as inferred, never
    hardcoded (G10 v1 hardcoded 9344 x 18432 and would read garbage on any other
    frame without saying so)."""
    for pat in candidates:
        p = pat % (ref, ref)
        if not os.path.exists(p):
            continue
        w = xml_int(p + ".xml", "width")
        if w:
            return p, w, "from %s.xml" % os.path.basename(p)
        nb = os.path.getsize(p)
        if nb % (18432 * 8) == 0:
            return p, nb // (18432 * 8), "INFERRED from %d bytes at 18432 lines" % nb
        return p, None, "UNKNOWN"
    return None, None, None


def load_dem():
    p, x = "geom_reference/hgt.rdr", "geom_reference/hgt.rdr.xml"
    if not os.path.exists(p):
        return None, "geom_reference/hgt.rdr absent"
    dw, dl = xml_int(x, "width"), xml_int(x, "length")
    if not (dw and dl):
        return None, "geom_reference/hgt.rdr.xml has no width/length"
    if dw * dl * 8 != os.path.getsize(p):
        return None, "hgt.rdr is %d bytes, xml says %dx%d" % (os.path.getsize(p), dl, dw)
    return np.fromfile(p, dtype=np.float64).reshape(dl, dw), "%d x %d float64" % (dl, dw)


def patch(path, r0, c0, width, n=N, rows=None):
    idx = list(range(n)) if rows is None else \
        sorted(set(np.linspace(0, n - 1, rows).round().astype(int).tolist()))
    o = np.empty((len(idx), n), dtype=np.complex64)
    with open(path, "rb") as fh:
        for j, i in enumerate(idx):
            fh.seek(((r0 + i) * width + c0) * 8)
            b = fh.read(n * 8)
            if len(b) < n * 8:
                raise IOError("short read at line %d of %s (width %d assumed)"
                              % (r0 + i, path, width))
            o[j] = np.frombuffer(b, dtype=np.complex64)
    m = np.abs(o)
    return o, float((m != 0).mean()), float(m.mean())


def prep_ref(a):
    A = np.abs(a).astype(np.float64)
    A -= A.mean()
    return np.conj(np.fft.rfft2(A)), A.shape


def correlate(Rconj, shape, b, supp=SUPPRESS):
    """dy, dx, sigma, ratio. sigma is None when the surface is flat (all-zero
    patch), which G10 v1 decoded as a perfect dy=0 dx=0 pass."""
    B = np.abs(b).astype(np.float64)
    B -= B.mean()
    C = np.fft.irfft2(np.fft.rfft2(B) * Rconj, s=shape)
    ny, nx = C.shape
    iy, ix = np.unravel_index(np.argmax(C), C.shape)
    sd = C.std()
    sigma = None if sd == 0 else float((C.max() - C.mean()) / sd)
    D = C.copy()
    ys = [(iy + k) % ny for k in range(-supp, supp + 1)]
    xs = [(ix + k) % nx for k in range(-supp, supp + 1)]
    D[np.ix_(ys, xs)] = C.min()
    second = float(D.max())
    ratio = None if second <= 0 else float(C.max() / second)
    return (iy if iy < ny // 2 else iy - ny), (ix if ix < nx // 2 else ix - nx), sigma, ratio


def dates_under(src, ref):
    return sorted(d for d in (os.path.basename(p.rstrip("/")) for p in glob.glob(src + "/*/"))
                  if re.match(r"^\d{8}$", d) and d != ref)


def frame_amp_scale(refpath, width, lines=18432, verbose=True):
    """Amplitude scale for the FRAME, from a spread grid that ignores DEM texture.

    DEFECT FOUND IN TESTING, 29 Aug: the first version of this file took the
    median amplitude of the top-N DEM-texture candidates and compared each
    candidate against it. On a frame whose highest-texture windows are all dim,
    that compares dim against dim and passes everything -- a threshold derived
    from the very sample it is meant to filter, which is the error this project
    has a rule against. The scale now comes from a spread sample of the frame,
    at the 75th percentile so that a half-water frame still yields a LAND scale
    rather than a blend."""
    amps = []
    for r0 in np.linspace(0, lines - N - 1, AMP_GRID).astype(int):
        for c0 in np.linspace(0, width - N - 1, AMP_GRID).astype(int):
            try:
                _, f, m = patch(refpath, int(r0), int(c0), width, rows=FILLROWS)
            except IOError:
                continue
            if f >= SEL_FILL:
                amps.append(m)
    if not amps:
        return None
    scale = float(np.percentile(amps, 75))
    if len(amps) < (AMP_GRID * AMP_GRID) // 2:
        print("  *** WARNING: only %d of %d grid positions had usable fill, so the frame"
              % (len(amps), AMP_GRID * AMP_GRID))
        print("  *** amplitude scale rests on a thin sample. Treat the amp/P75 column with care.")
    if verbose:
        print("  frame amplitude scale: %d sampled windows, P75 %.0f "
              "(min %.0f median %.0f max %.0f); a window must reach %.2f x P75 = %.0f"
              % (len(amps), scale, min(amps), float(np.median(amps)), max(amps),
                 AMP_FRAC, AMP_FRAC * scale))
    return scale


def select_windows(refpath, width, dem, src, dates, lines=18432, verbose=True):
    """DEM texture, then reference amplitude against the frame's own median,
    then a COUNT of secondaries at full fill. All three, in that order."""
    dl, dw = dem.shape
    rlk, alk = width / dw, lines / dl
    cands = []
    for r0 in range(0, lines - N, 1024):
        for c0 in range(0, width - N, 512):
            b = dem[int(r0 / alk):int((r0 + N) / alk) + 1, int(c0 / rlk):int((c0 + N) / rlk) + 1]
            if b.size >= 16:
                cands.append((float(np.nanstd(b)), r0, c0))
    cands.sort(reverse=True)
    top = cands[:NCAND]
    rows = []
    for sd, r0, c0 in top:
        try:
            _, rf, rm = patch(refpath, r0, c0, width, rows=FILLROWS)
        except IOError:
            continue
        rows.append([sd, r0, c0, rf, rm, None])
    if not rows:
        return [], "no candidate window is readable in the reference"
    med_amp = frame_amp_scale(refpath, width, lines, verbose)
    if not med_amp:
        return [], "cannot establish a frame amplitude scale from the reference"
    if verbose:
        print("  candidate windows: %d evaluated, top %d surveyed"
              % (len(cands), len(rows)))
        print("  %-5s %-7s %-7s %9s %11s %8s %7s %s"
              % ("rank", "row", "col", "DEMstd", "ref amp", "amp/P75", "nfull", "verdict"))
    viable = []
    for i, r in enumerate(rows):
        sd, r0, c0, rf, rm, _ = r
        why = []
        if sd < DEM_MIN:
            why.append("DEMstd %.2f, flat (void-fill reads 0.00)" % sd)
        if rf < SEL_FILL:
            why.append("ref fill %.3f" % rf)
        if rm < AMP_FRAC * med_amp:
            why.append("amp %.2fx frame P75" % (rm / med_amp if med_amp else 0))
        nfull = 0
        if not why:
            for d in dates:
                p = "%s/%s/%s.slc" % (src, d, d)
                if not os.path.exists(p):
                    continue
                try:
                    _, f, _ = patch(p, r0, c0, width, rows=FILLROWS)
                except IOError:
                    f = 0.0
                nfull += (f >= SEL_FILL)
            if nfull < len(dates) - ALLOW_MISS:
                why.append("only %d of %d secondaries full" % (nfull, len(dates)))
        ok = not why
        if verbose:
            print("  %-5d %-7d %-7d %9.2f %11.0f %8.2f %7s %s"
                  % (i, r0, c0, sd, rm, rm / med_amp if med_amp else 0,
                     nfull if nfull else "-", "VIABLE" if ok else "reject: " + "; ".join(why)))
        if ok:
            viable.append((sd, r0, c0))
        if len(viable) >= NWIN:
            break
    return viable, None


def run(gate, src, refcands, ref, tol=TOL, want=None, reselect=False, inject=None):
    print("=" * 74)
    print("== %s   ref %s   src %s" % (gate, ref, src))
    print("=" * 74)
    if not os.path.isdir(src):
        die("%s does not exist -- has the run that produces it been done?" % src)
    refpath, width, how = resolve_reference(ref, refcands)
    if refpath is None:
        die("no reference SLC for %s in %s" % (ref, ", ".join(refcands)))
    if not width:
        die("cannot determine the reference width for %s" % refpath)
    print("  reference %s   width %d   (%s)" % (refpath, width, how))
    dem, note = load_dem()
    if dem is None:
        die("window selection needs the multilooked DEM: %s" % note)
    print("  DEM %s" % note)

    dates = dates_under(src, ref)
    # N51: measure and median-centre over ALL secondaries; restrict only the
    # REPORTING. Filtering here made the tested subset its own median -- a run
    # restricted to three bad dates read median dx -32.0 and "passed" them on
    # bit-identical files (29 Aug, p449 f0320).
    report = [d for d in dates if d in want] if want else list(dates)
    if not dates:
        die("no 8-digit date directories under %s/" % src)
    if want and not report:
        die("none of the requested dates are secondaries under %s/" % src)
    print("  %d secondary date(s) measured, %d reported; tolerance +/-%d after "
          "median-centring; ratio cut %.2f; quorum %d"
          % (len(dates), len(report), tol, RATIO_MIN, QUORUM))
    if inject:
        print("\n" + "!" * 74)
        print("!! SELF-TEST: injecting dy=%+d dx=%+d into %s, in memory only."
              % (inject[0], inject[1], inject[2]))
        print("!! NOTHING ON DISK IS MODIFIED. This run's verdict is NOT a frame result.")
        print("!! The gate is working if and only if %s comes out FAIL." % inject[2])
        print("!" * 74)
        if inject[2] not in dates:
            die("%s is not a secondary date here; pick one from %s/" % (inject[2], src))

    cache = "logs/reg_windows_%s.json" % re.sub(r"\W+", "_", src)
    viable = None
    if os.path.exists(cache) and not reselect:
        try:
            j = json.load(open(cache))
            if j.get("ref") == ref and j.get("ndates") == len(dates):
                viable = [tuple(x) for x in j["windows"]]
                print("  windows reused from %s (--reselect to redo)" % cache)
        except Exception:
            viable = None
    if viable is None:
        viable, err = select_windows(refpath, width, dem, src, dates, verbose=True)
        if err:
            die(err)
        try:
            os.makedirs("logs", exist_ok=True)
            json.dump({"ref": ref, "ndates": len(dates), "windows": viable}, open(cache, "w"))
        except Exception as e:
            print("  (could not cache windows: %r)" % (e,))

    if len(viable) < QUORUM:
        print("\n*** FAIL: only %d viable window(s), quorum is %d." % (len(viable), QUORUM))
        print("*** The gate cannot measure this frame rather than passing it by default.")
        print("*** A frame that is mostly water or void-fill will land here; that is the")
        print("*** correct outcome, and G21 plus per-date coherence remain the nets.")
        sys.exit(1)

    per = {}
    for wi, (sd, r0, c0) in enumerate(viable):
        R, shape, refok = None, None, True
        try:
            a, rf, rm = patch(refpath, r0, c0, width)
            R, shape = prep_ref(a)
        except IOError as e:
            print("\n  window %d r%d c%d: reference unreadable, %s" % (wi, r0, c0, e))
            refok = False
        if not refok:
            continue
        res = {}
        for d in dates:
            p = "%s/%s/%s.slc" % (src, d, d)
            if not os.path.exists(p):
                res[d] = ("MISSING", None, None, None, None); continue
            try:
                b, f, mn = patch(p, r0, c0, width)
            except IOError as e:
                res[d] = ("READERR", None, None, None, None); continue
            if f < MIN_FILL:
                res[d] = ("EMPTY", None, None, f, None); continue
            if inject and d == inject[2]:
                b = np.roll(np.roll(b, inject[0], axis=0), inject[1], axis=1)
            dy, dx, sg, rt = correlate(R, shape, b)
            res[d] = ("m", dy, dx, f, (sg, rt))
        good = [v for v in res.values() if v[0] == "m"]
        rats = [v[4][1] for v in good if v[4][1] is not None]
        medr = float(np.median(rats)) if rats else 0.0
        mdy = float(np.median([v[1] for v in good])) if good else 0.0
        mdx = float(np.median([v[2] for v in good])) if good else 0.0
        per[wi] = dict(r0=r0, c0=c0, demstd=sd, res=res, medr=medr, mdy=mdy, mdx=mdx,
                       votes=(medr >= RATIO_MIN))
        print("\n  window %d  row %-6d col %-6d  DEMstd %.1f  median ratio %.2f  "
              "median dy %+.1f dx %+.1f  %s"
              % (wi, r0, c0, sd, medr, mdy, mdx,
                 "VOTES" if medr >= RATIO_MIN else "EXCLUDED, ratio below %.2f" % RATIO_MIN))

    voting = [w for w in per if per[w]["votes"]]
    if len(voting) < QUORUM:
        print("\n*** FAIL: %d window(s) qualified to vote, quorum is %d." % (len(voting), QUORUM))
        sys.exit(1)

    print("\n" + "=" * 74)
    print("== per-date residual against each voting window's median. tolerance +/-%d" % tol)
    print("=" * 74)
    hdr = ("  %-10s" % "DATE" + "".join("  w%-11d" % w for w in voting)
           + "  %4s %4s %8s %s" % ("sprY", "sprX", "ratio", "verdict"))
    print(hdr)
    bad = 0
    spreads = []
    for d in report:
        cells, outs, tot, rmin = [], 0, 0, None
        rawy, rawx = [], []
        for w in voting:
            st = per[w]["res"][d]
            if st[0] != "m":
                cells.append("%-13s" % st[0]); outs += 1; tot += 1; continue
            ry = st[1] - per[w]["mdy"]; rx = st[2] - per[w]["mdx"]
            rawy.append(st[1]); rawx.append(st[2])
            o = abs(ry) > tol or abs(rx) > tol
            outs += o; tot += 1
            # one decimal: with an even date count a window median can be a
            # half-integer, and "%+.0f" printed -0.5 as "-0", indistinguishable
            # from zero. The test always used the float; only the display lied.
            cells.append("%+5.1f%+6.1f%s " % (ry, rx, "!" if o else " "))
            r = st[4][1]
            rmin = r if (r is not None and (rmin is None or r < rmin)) else rmin
        sy = (max(rawy) - min(rawy)) if rawy else 0
        sx = (max(rawx) - min(rawx)) if rawx else 0
        if rawy:
            spreads.append((max(sy, sx), d))
        v = "FAIL" if outs * 2 > tot else "ok"
        if v == "FAIL":
            bad += 1
        print("  %-10s" % d + "".join("  " + c for c in cells)
              + "  %4d %4d %8s %s" % (sy, sx, "-" if rmin is None else "%.2f" % rmin, v))
    if spreads:
        spreads.sort(reverse=True)
        over = [d for sp, d in spreads if sp > 1]
        print("\n  across-window spread of the RAW offsets, max(dy,dx) per date:")
        print("    worst %d (%s); %d date(s) exceed 1 sample%s"
              % (spreads[0][0], spreads[0][1], len(over),
                 (": " + ", ".join(over[:8])) if over else ""))
        print("    a large spread is not a failure -- it is measured here so the question")
        print("    of geometric distortion can be settled rather than eyeballed.")
    print("\n  a date FAILS when a MAJORITY of the %d voting windows call it out" % len(voting))
    print("\n  NOT TESTED HERE: an off-frame acquisition. These are resampled products,")
    print("  so run_03 has already applied the granule offset. G21 owns that class.")
    print("%s  %d of %d date(s) failed" % ("FAIL" if bad else "PASS", bad, len(report)))
    if inject:
        # Use the SAME majority rule the frame verdict uses -- a date flagged by
        # one window of five does not fail the frame, so it must not count as a
        # catch either.
        outs = tot = 0
        for w in voting:
            st = per[w]["res"][inject[2]]
            if st[0] != "m":
                outs += 1; tot += 1; continue
            tot += 1
            outs += (abs(st[1] - per[w]["mdy"]) > tol or abs(st[2] - per[w]["mdx"]) > tol)
        caught = outs * 2 > tot
        # An injection inside the tolerance SHOULD be ignored. Testing only the
        # large case would leave the gate's other failure mode -- crying wolf on
        # a sub-tolerance shift -- unmeasured.
        expect = max(abs(inject[0]), abs(inject[1])) > tol
        ok = (caught == expect)
        print("\n" + "!" * 74)
        print("!! injected %+d,%+d on %s; tolerance is +/-%d, so the correct outcome"
              % (inject[0], inject[1], inject[2], tol))
        print("!! is %s, and the gate %s it (%d of %d windows called it out)."
              % ("FLAGGED" if expect else "IGNORED",
                 "flagged" if caught else "ignored", outs, tot))
        if ok and expect:
            print("!! SELF-TEST PASSED -- the gate can fail. This run's frame verdict")
            print("!! above is MEANINGLESS: one date was doctored.")
        elif ok:
            print("!! SELF-TEST PASSED -- a sub-tolerance shift was correctly ignored.")
        elif expect:
            print("!! SELF-TEST FAILED: a shift beyond tolerance was NOT flagged.")
            print("!! THE GATE IS BROKEN. Do not trust any verdict it has produced.")
        else:
            print("!! SELF-TEST FAILED: a shift INSIDE tolerance was flagged.")
            print("!! The gate is over-sensitive; its passes may be luck, not measurement.")
        print("!" * 74)
        sys.exit(0 if ok else 1)
    sys.exit(1 if bad else 0)
