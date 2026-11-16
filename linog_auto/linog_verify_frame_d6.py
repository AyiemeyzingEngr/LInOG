#!/usr/bin/env python3
"""linog_verify_frame_d6.py <frame_dir> [<frame_dir> ...]

linog_auto's copy of the kit's linog_verify_frame.py (7f2b53cf), decision D6 (record 47.4, 48.0): identical except
that N22 takes each date's mode from the frame's recon/modes.json when it has one (the pipeline's per-date table,
written by Phase 1c), and from raw_fbs_unpacked/ otherwise, and prints which source it used on a line of its own
after the check (not a check: the counts stay the kit's). On an FBS-only frame without raw_fbs_unpacked/ the kit
classes every secondary FBD and FAILs N22 on all of them (F39). $S and the course kit are not changed.
v0.13 (the ascending record 18.5 and 18.6): on a frame whose datum record (status/P4c_datum.json) says method R9, N22 and
G16 check each date's dates/ value against the plan that record holds, within 1e-6, and say so ("by R9's plan"): R9
writes its own values, not G16's relation on invertMisreg's output. On any other frame with recon/modes.json N22's range
factor is the ratio of the pixel spacings, spacing(the reference's mode) / spacing(the date's): 1 on an FBS-only frame and
on an FBD-only one, 0.5 for an FBD date of a mixed frame (the kit's 0.5 for every FBD date failed an FBD-only frame); a
frame without the table (the 12 delivered frames) keeps the kit's rule and lines.
v0.13 r2 (the part 6 review, the ascending record 26.1, P6R-01 to 04, 08, 10 and 14): a datum value is off unless it is
within its line, so a NaN is off (the kit's lines read it as on); R9's plan is read right after the zero test, with or
without a pre-datum copy; the plan only from a PASS datum record that is neither planned nor a dry run's, each value a pair
of finite numbers, and a record that is there but gives no plan FAILs N22 and G16 by name; both lines name the dates in
dates/ only and in the plan only, and G16 lists its off dates; a new line R9 checks the plan against R9's arithmetic in the
record (x by the SLR and PRF it holds, x(REF) 0, each SLR recon/modes.json's); with the table, a date it lacks is named on
N22, not read as FBD; coreg_ref without a fineResamp config reads recon/reference.json, then the kit's width heuristic by
isce2's width (lp_xmlwidth, beside this copy) and only when one date alone is not 4640 wide. On frames the old copy read
right (finite values, a readable PASS record, every date in the table) the lines are the old copy's but for R9's new line.

Read-only invariant checker for a LInOG stripmapStack+MintPy frame.
Every check prints the measured number, never a bare verdict.
Exit 1 if any FAIL. WARN does not fail.

Checks are keyed to the flag that produced them; see
LINOG_P448F0300_RunLog_20260828.md sections 4-6.
"""
import os, re, sys, glob, shelve, subprocess

try:
    import isce  # noqa  (needed to unpickle Poly2D from the misreg shelves)
except Exception:
    pass

STEP = 1.0 / 1200.0
DATE = re.compile(r'^\d{8}$')
LAT_TOL = 1e-2          # index units; E30 - 1e-4 is tighter than 9-dp laloStep allows


class Report(object):
    def __init__(self):
        self.n = {"PASS": 0, "WARN": 0, "FAIL": 0}
        self.fails = []

    def __call__(self, st, tag, msg):
        self.n[st] += 1
        if st == "FAIL":
            self.fails.append("%s %s" % (tag, msg))
        print("   %-4s %-5s %s" % (st, tag, msg))


def strays(d):
    if not os.path.isdir(d):
        return None
    return sorted(x for x in os.listdir(d) if not DATE.match(x))


def shelf(base):
    s = shelve.open(base, flag='r')
    v = (s['azpoly']._coeffs[0][0], s['rgpoly']._coeffs[0][0])
    s.close()
    return v


def load_dates(root):
    out = {}
    for p in sorted(glob.glob(root + "/*/misreg.dat")):
        d = os.path.basename(os.path.dirname(p))
        if not DATE.match(d):
            continue
        try:
            out[d] = shelf(p[:-4])
        except Exception:
            pass
    return out


def newest(paths):
    t = 0.0
    for p in paths:
        try:
            t = max(t, os.path.getmtime(p))
        except OSError:
            pass
    return t


def cfgval(txt, key):
    m = re.search(r'^\s*%s\s*=\s*([^#\n]+)' % re.escape(key), txt, re.M)
    return m.group(1).strip() if m else None


def structure(W, say):
    d = os.path.join(W, "data")
    if os.path.islink(d):
        tgt = os.readlink(d)
        if os.path.isabs(tgt):
            say("FAIL", "E6", "data -> %s is ABSOLUTE; must be relative" % tgt)
        else:
            say("PASS", "E6", "data -> %s (relative)" % tgt)
    else:
        say("WARN", "E6", "no data symlink")

    if os.path.isdir(os.path.join(W, "SLC")):
        say("PASS", "E5", "SLC/ present")
    else:
        say("FAIL", "E5", "SLC/ ABSENT - unpack will fail at os.mkdir")

    for sub, tag in (("SLC", "N17"), ("merged/SLC", "N18"),
                     ("refineSecondaryTiming/dates", "N18")):
        s = strays(os.path.join(W, sub))
        if s is None:
            say("WARN", tag, "%s/ absent" % sub)
        elif s:
            say("WARN", tag, "%s/ has %d non-date entries: %s" % (sub, len(s), ", ".join(s)))
        else:
            say("PASS", tag, "%s/ clean, all 8-digit dates" % sub)

    n = len(glob.glob(os.path.join(W, "geom_reference", "*.rsc")))
    (say("PASS", "N13", "geom_reference .rsc = 6")
     if n == 6 else
     say("FAIL", "N13", "geom_reference .rsc = %d, need 6 (prep_isce must name "
                        "hgt lat lon los shadowMask incLocal)" % n))


def datum(W, say):
    R = os.path.join(W, "refineSecondaryTiming")
    baks = sorted(glob.glob(R + "/dates_predatum_bak_*"))
    post = load_dates(R + "/dates")
    if not post:
        say("WARN", "G16", "no misreg shelves under dates/")
        return
    ref = [d for d, v in post.items() if abs(v[0]) < 1e-9 and abs(v[1]) < 1e-9]
    if not ref:
        mx = max(post.items(), key=lambda kv: abs(kv[1][0]))
        say("FAIL", "N15", "no date reads (0,0) - frame was NEVER datum-rebased; "
                           "largest az is %s at %+.6f" % (mx[0], mx[1][0]))
        return
    r = ref[0]
    say("PASS", "G16", "reference %s reads az 0.000000 rg 0.000000" % r)

    if not baks:
        say("WARN", "N23", "no dates_predatum_bak_* - cannot verify the mode-aware "
                           "range scaling; G16's zero-reference test alone proves nothing")
        return
    pre = load_dates(baks[-1])
    if r not in pre:
        say("WARN", "N23", "reference missing from %s" % os.path.basename(baks[-1]))
        return
    fbs = set(os.path.basename(x) for x in glob.glob(os.path.join(W, "raw_fbs_unpacked", "*")))
    dat = -pre[r][1]
    daz = -pre[r][0]
    bad_rg = bad_az = nf = nb = 0
    worst = None
    for d, v in sorted(post.items()):
        if d == r or d not in pre:
            continue
        mode = "FBS" if d in fbs else "FBD"
        nf += (mode == "FBS")
        nb += (mode == "FBD")
        want = dat * (1.0 if mode == "FBS" else 0.5)
        got = v[1] - pre[d][1]
        if abs(got - want) > 1e-4:
            bad_rg += 1
            if worst is None or abs(got - want) > worst[3]:
                worst = (d, mode, got, abs(got - want), want)
        if abs((v[0] - pre[d][0]) - daz) > 1e-4:
            bad_az += 1
    say("PASS" if bad_rg == 0 else "FAIL", "N22",
        "range datum: %d FBS + %d FBD dates, %d wrong%s"
        % (nf, nb, bad_rg,
           "" if worst is None else
           "  (worst %s %s got %+.6f want %+.6f)" % (worst[0], worst[1], worst[2], worst[4])))
    say("PASS" if bad_az == 0 else "FAIL", "G16",
        "azimuth datum: %d wrong (all modes take the full shift %+.6f)" % (bad_az, daz))


def igrams(W, say):
    PAIR = re.compile(r'^\d{8}_\d{8}$')
    allp = [p for p in glob.glob(os.path.join(W, "Igrams", "*")) if os.path.isdir(p)]
    pairs = [p for p in allp if PAIR.match(os.path.basename(p))]
    odd = [os.path.basename(p) for p in allp if not PAIR.match(os.path.basename(p))]
    if odd:
        say("WARN", "E33", "Igrams/ has %d non-pair dir(s), excluded from counts: %s"
            % (len(odd), ", ".join(odd)))
    unw = glob.glob(os.path.join(W, "Igrams", "*", "filt_*_snaphu.unw"))
    rsc = glob.glob(os.path.join(W, "Igrams", "*", "*.unw.rsc"))
    r08 = os.path.join(W, "run_files", "run_08_igram")
    nrun = sum(1 for l in open(r08) if l.strip()) if os.path.exists(r08) else -1
    say("PASS" if nrun in (-1, len(pairs)) else "FAIL", "G11",
        "Igrams dirs %d, run_08 lines %d" % (len(pairs), nrun))
    say("PASS" if len(rsc) == len(pairs) else "FAIL", "N20",
        ".rsc %d for %d pairs - every pair must have one or MintPy silently drops it"
        % (len(rsc), len(pairs)))
    st = os.path.join(W, "mintpy", "inputs", "ifgramStack.h5")
    if not os.path.exists(st):
        say("WARN", "N19", "no mintpy/inputs/ifgramStack.h5")
        return
    tu, ts = newest(unw), os.path.getmtime(st)
    d = (ts - tu) / 3600.0
    say("PASS" if ts > tu else "FAIL", "N19",
        "ifgramStack.h5 is %+.2f h relative to the newest .unw "
        "(must be POSITIVE, else MintPy read interferograms that no longer exist)" % d)


def cfg(W, say):
    p = os.path.join(W, "mintpy", "smallbaselineApp.cfg")
    if not os.path.exists(p):
        say("WARN", "cfg", "no mintpy/smallbaselineApp.cfg")
        return
    t = open(p).read()
    ls = cfgval(t, "mintpy.geocode.laloStep")
    ok = ls is not None and ls.replace(" ", "") == "-0.000833333,0.000833333"
    say("PASS" if ok else "FAIL", "E20", "geocode.laloStep = %s" % ls)
    sn = cfgval(t, "mintpy.geocode.SNWE")
    say("PASS" if sn and sn != "auto" else "FAIL", "E20", "geocode.SNWE = %s" % sn)
    yx = cfgval(t, "mintpy.reference.yx")
    say("PASS" if yx and yx != "auto" else "WARN", "G19",
        "reference.yx = %s (should be linog_refpix.py's pick, not auto)" % yx)
    um = cfgval(t, "mintpy.load.updateMode")
    say("PASS" if um == "no" else "WARN", "N19",
        "load.updateMode = %s (auto skips the reload after a rebuild)" % um)
    for k in ("mintpy.load.shadowMaskFile",):
        say("PASS", "flag7", "%s = %s" % (k, cfgval(t, k)))


def grid(W, say):
    try:
        import h5py
    except ImportError:
        say("WARN", "E20", "h5py unavailable, skipping grid check")
        return
    f = os.path.join(W, "mintpy", "geo", "geo_velocity.h5")
    if not os.path.exists(f):
        say("WARN", "E20", "no geo/geo_velocity.h5")
        return
    a = h5py.File(f, 'r').attrs
    g = lambda k: (a[k].decode() if isinstance(a[k], bytes) else a[k])
    L, Wd = int(g('LENGTH')), int(g('WIDTH'))
    ys, xs = float(g('Y_STEP')), float(g('X_STEP'))
    N, Wl = float(g('Y_FIRST')), float(g('X_FIRST'))
    S, E = N + ys * L, Wl + xs * Wd
    pin = abs(ys + STEP) < 1e-8 and abs(xs - STEP) < 1e-8
    say("PASS" if pin else "FAIL", "E20",
        "grid %d x %d step %+.9f / %+.9f" % (L, Wd, ys, xs))
    idx = [v * 1200.0 for v in (S, N, Wl, E)]
    off = max(abs(round(v) - v) for v in idx)
    say("PASS" if off < LAT_TOL else "FAIL", "E20",
        "lattice idx lat %.2f-%.2f lon %.2f-%.2f, max offset %.5f px (tol %.2f)"
        % (idx[0], idx[1], idx[2], idx[3], off, LAT_TOL))
    print("        SNWE %.7f,%.7f,%.7f,%.7f" % (S, N, Wl, E))


def delivery(W, say):
    out = glob.glob(os.path.join(W, "mintpy", "geo", "LInOG_Upload_*"))
    if not out:
        say("WARN", "N6", "no LInOG_Upload_* folder")
        return
    o = out[0]
    files = [x for x in os.listdir(o) if os.path.isfile(os.path.join(o, x))]
    aux = [x for x in files if x.endswith(".aux.xml")]
    tif = [x for x in files if x.endswith(".tif")]
    say("PASS" if len(files) == 16 else "FAIL", "N6",
        "%s holds %d files (standard is 16: 6 tif + 6 png + 4 kmz)"
        % (os.path.basename(o), len(files)))
    say("PASS" if not aux else "FAIL", "N6",
        "%d .aux.xml sidecars (must be 0; a stale sidecar reports the previous "
        "product's stretch)" % len(aux))
    miss = []
    for t in tif:
        try:
            r = subprocess.run(["gdalinfo", os.path.join(o, t)],
                               capture_output=True, text=True, timeout=60)
            if "STATISTICS_MEAN" not in r.stdout:
                miss.append(t)
        except Exception:
            miss.append(t + "(gdalinfo failed)")
    say("PASS" if not miss and tif else ("FAIL" if miss else "WARN"), "N6",
        "%d/%d TIFFs carry embedded STATISTICS_MEAN%s"
        % (len(tif) - len(miss), len(tif), "" if not miss else "; missing: " + ", ".join(miss)))


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    bad = 0
    for W in args:
        W = W.rstrip("/")
        print("=" * 72)
        print("FRAME  %s" % W)
        print("=" * 72)
        rep = Report()
        for name, fn in (("structure", structure), ("datum", datum),
                         ("igrams", igrams), ("config", cfg),
                         ("grid", grid), ("delivery", delivery),
                         ("watermask", watermask), ("edgemask", edgemask)):
            print(" -- %s --" % name)
            try:
                fn(W, rep)
            except Exception as e:
                rep("FAIL", "ERR", "%s check raised %s: %s"
                    % (name, type(e).__name__, str(e)[:80]))
        print(" == %s : PASS %d  WARN %d  FAIL %d =="
              % (os.path.basename(W), rep.n["PASS"], rep.n["WARN"], rep.n["FAIL"]))
        if rep.n["FAIL"]:
            bad += 1
            for f in rep.fails:
                print("      FAILED: %s" % f)
    print()
    print("FRAMES WITH FAILURES: %d of %d" % (bad, len(args)))
    sys.exit(1 if bad else 0)




# ---------------------------------------------------------------- E32 patch
import logging
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("h5py").setLevel(logging.WARNING)


def coreg_ref(W):
    """The coregistration reference date, from what ISCE actually used.
    Never inferred from a misreg value reading zero - that is the N23 error.
    v0.13 r2 (the part 6 review's P6R-14, with 25-b): without a fineResamp config, linog_auto's own record of the reference,
    recon/reference.json (D1's pick, which stack2 writes into those configs and datum's G4c.1 holds them to), before the kit's
    width heuristic; and the heuristic reads each SLC/*/ .slc.xml as isce2 loads it (lp_xmlwidth: coordinate1's size, a file
    whose fields disagree not used) and names a date only when it is the one date not 4640 wide: on a v0.13 mixed frame every
    FBS date stays 9344 wide in SLC/, where the first of them (the earliest FBS date) is not the reference (25.6)."""
    for c in sorted(glob.glob(os.path.join(W, "configs", "config_fineResamp_*"))):
        try:
            m = re.search(r'^\s*reference\s*:\s*(\S+)', open(c).read(), re.M)
        except Exception:
            continue
        if m:
            b = os.path.basename(m.group(1).rstrip('/'))
            if DATE.match(b):
                return b, "configs/config_fineResamp_*"
    import json
    try:
        b = str(json.load(open(os.path.join(W, "recon", "reference.json"))).get("reference"))
        if DATE.match(b):
            return b, "recon/reference.json"
    except Exception:
        pass
    import lp_xmlwidth as XW   # the pipeline's helper, beside this copy (the folder accept and lp_d6check.sh run it from)
    odd = []
    for x in sorted(glob.glob(os.path.join(W, "SLC", "*", "*.slc.xml"))):
        w, _, prob = XW.check(x)
        if w is not None and not prob and w != 4640:
            odd.append((os.path.basename(os.path.dirname(x)), w))
    if len(odd) == 1:
        return odd[0][0], "SLC width %s (the one SLC/*/ .slc.xml not 4640 wide, as isce2 loads it)" % odd[0][1]
    return None, None


def datum(W, say):
    R = os.path.join(W, "refineSecondaryTiming")
    baks = sorted(glob.glob(R + "/dates_predatum_bak_*"))
    post = load_dates(R + "/dates")
    if not post:
        say("WARN", "G16", "no misreg shelves under dates/")
        return
    r, src = coreg_ref(W)
    zeros = [d for d, v in post.items() if abs(v[0]) < 1e-9 and abs(v[1]) < 1e-9]
    if r is None:
        say("WARN", "G16", "cannot identify the coregistration reference; "
                           "%d date(s) read zero: %s" % (len(zeros), ", ".join(zeros)))
        return
    if r not in post:
        say("FAIL", "G16", "coreg reference %s (from %s) has no misreg shelf" % (r, src))
        return
    if not (abs(post[r][0]) <= 1e-9 and abs(post[r][1]) <= 1e-9):   # v0.13 r2 (P6R-01): off unless within the line
        say("FAIL", "N15", "coreg reference %s (from %s) reads az %+.6f rg %+.6f - "
                           "frame was NEVER rebased onto it. Datum sits on %s instead. "
                           "E32: a zero somewhere is not a rebase."
            % (r, src, post[r][0], post[r][1],
               zeros[0] if zeros else "no date at all"))
        return
    say("PASS", "G16", "coreg reference %s (from %s) reads az 0.000000 rg 0.000000; "
                       "%d date(s) at zero" % (r, src, len(zeros)))
    if len(zeros) != 1:
        say("WARN", "G16", "%d dates read zero, expected exactly 1: %s"
            % (len(zeros), ", ".join(zeros)))
    # v0.13 r2 (the part 6 review's P6R-02): R9's plan is read right after the zero test; it needs no pre-datum copy
    plan, r9, why = r9_plan(W)
    if plan is not None or why:
        fbs, msrc, tab = modes_fbs(W)
        if why:   # P6R-03: a datum record that is there but gives no plan to check against FAILs both lines by name
            say("FAIL", "N22", "range datum: %s" % why)
            print("        N22 modes from %s" % msrc)
            say("FAIL", "G16", "azimuth datum: %s" % why)
        else:   # v0.13 (18.6): R9's values, checked against the datum record's plan
            datum_r9(W, say, post, plan, r9, r, fbs, msrc, tab)
        return
    if not baks:
        say("WARN", "N23", "no dates_predatum_bak_* - cannot verify the mode-aware "
                           "range scaling; the zero-reference test alone proves nothing")
        return
    pre = load_dates(baks[-1])
    if r not in pre:
        say("WARN", "N23", "reference missing from %s" % os.path.basename(baks[-1]))
        return
    fbs, msrc, tab = modes_fbs(W)   # D6: recon/modes.json when the frame has one, raw_fbs_unpacked/ otherwise
    dat = -pre[r][1]
    daz = -pre[r][0]
    bad_rg = bad_az = nf = nb = 0
    worst = None
    sp = {"FBS": 1.0, "FBD": 2.0}   # v0.13 (18.5): the pixel spacings' ratio, by the reference's mode and the date's, read
    mref = "FBS" if r in fbs else "FBD"   # from recon/modes.json; without that table the kit's rule and lines stand (D6)
    table = msrc.startswith("recon/modes.json")
    for d, v in sorted(post.items()):
        if d == r or d not in pre:
            continue
        mode = "FBS" if d in fbs else "FBD"
        nf += (mode == "FBS")
        nb += (mode == "FBD")
        want = dat * (sp[mref] / sp[mode] if table else (1.0 if mode == "FBS" else 0.5))
        got = v[1] - pre[d][1]
        dev = abs(got - want)
        if not dev <= 1e-4:   # v0.13 r2 (P6R-01): off unless within the line (a NaN is off, and the worst)
            bad_rg += 1
            key = dev if dev == dev else float("inf")
            if worst is None or key > worst[3]:
                worst = (d, mode, got, key, want)
        if not abs((v[0] - pre[d][0]) - daz) <= 1e-4:
            bad_az += 1
    # v0.13 r2 (P6R-10): with the table, a date it lacks (the reference among them) is named, not read as FBD
    notab = [] if not table else sorted(d for d in set(post) | set([r]) if d not in tab)
    say("PASS" if bad_rg == 0 and not notab else "FAIL", "N22",
        "range datum: %d FBS + %d FBD secondaries, %d wrong%s%s"
        % (nf, nb, bad_rg,
           "" if worst is None else
           "  (worst %s %s got %+.6f want %+.6f)"
           % (worst[0], worst[1], worst[2], worst[4]),
           "" if not notab else "; not in recon/modes.json: %s" % ", ".join(notab)))
    print("        N22 modes from %s" % msrc)
    say("PASS" if bad_az == 0 else "FAIL", "G16",
        "azimuth datum: %d wrong (all modes take the full shift %+.6f)" % (bad_az, daz))

def r9_plan(W):
    """v0.13 (18.6): (plan, r9, why): R9's plan {date: (az, rg)} and the record's r9 block when status/P4c_datum.json says
    method R9, (None, None, None) when there is no such file or the record says another method (G16's relation then).
    v0.13 r2 (the part 6 review's P6R-03, P6R-01): the plan only from a PASS record that is neither planned nor a dry run's,
    each value a pair of finite numbers; why names the record and what it lacks when it is there but gives no plan (not
    JSON, not a datum record, R9 with another verdict, a dry run's, no plan, a value not a pair of finite numbers)."""
    import json
    import math
    f = os.path.join(W, "status", "P4c_datum.json")
    if not os.path.isfile(f):
        return None, None, None
    name = "status/P4c_datum.json"
    try:
        rec = json.load(open(f))
    except (OSError, ValueError) as e:
        return None, None, "%s unreadable (%s): no plan and no method to check by" % (name, type(e).__name__)
    o = rec.get("outputs") if isinstance(rec, dict) else None
    if not isinstance(o, dict):
        return None, None, "%s is not a datum record (its %s is a %s): no plan and no method to check by" % (
            name, "outputs" if isinstance(rec, dict) else "top level",
            type(rec.get("outputs") if isinstance(rec, dict) else rec).__name__)
    if o.get("method") != "R9":
        return None, None, None
    if rec.get("verdict") != "PASS":
        return None, None, "%s says method R9 but reads verdict %s: its plan is not the datum on record" % (
            name, rec.get("verdict"))
    if o.get("planned") or o.get("dryrun"):
        return None, None, "%s says method R9 in a dry run's record (planned %s, dryrun %s): its plan was not written" % (
            name, o.get("planned"), o.get("dryrun"))
    p = o.get("plan")
    if not isinstance(p, dict) or not p:
        return None, None, "%s says method R9 with no plan (%s)" % (name, type(p).__name__)
    plan, bad = {}, []
    for d, v in sorted(p.items()):
        try:
            az, rg = (float(x) for x in v)
        except (TypeError, ValueError):
            bad.append("%s %r" % (d, v))
            continue
        if not (math.isfinite(az) and math.isfinite(rg)):
            bad.append("%s %r" % (d, v))
            continue
        plan[d] = (az, rg)
    if bad:
        return None, None, "%s says method R9; its plan's values not a pair of finite numbers: %s" % (name, ", ".join(bad))
    return plan, o.get("r9") if isinstance(o.get("r9"), dict) else {}, None


def datum_r9(W, say, post, plan, r9, r, fbs, msrc, tab):
    """v0.13 (18.6): N22 (range) and G16 (azimuth) by R9's plan: every date of dates/ as the plan, within 1e-6.
    v0.13 r2 (the part 6 review): a value is off unless it is within 1e-6, so a NaN is off (P6R-01); both lines name the
    dates in dates/ only and in the plan only, and G16 lists its off dates as N22 does (P6R-04); a date recon/modes.json
    lacks is named on N22 (P6R-10); then the plan against R9's own arithmetic in the record (P6R-08, r9_arith)."""
    only_post = sorted(set(post) - set(plan))
    only_plan = sorted(set(plan) - set(post))
    miss = "".join("; %s: %s" % (k, ", ".join(v)) for k, v in (("in dates/ only", only_post), ("in the plan only", only_plan)) if v)
    off = [(d, post[d][0] - plan[d][0], post[d][1] - plan[d][1]) for d in sorted(set(post) & set(plan))]
    bad_rg = [x for x in off if not abs(x[2]) <= 1e-6]
    bad_az = [x for x in off if not abs(x[1]) <= 1e-6]
    nf = sum(1 for d in post if d != r and d in fbs)
    nb = sum(1 for d in post if d != r and d not in fbs)
    notab = [] if tab is None else sorted(d for d in set(post) | set([r]) if d not in tab)

    def worst(bad, i):
        if not bad:
            return ""
        w = max(bad, key=lambda x: abs(x[i]) if x[i] == x[i] else float("inf"))
        return "  (worst %s off %+.6f: %s)" % (w[0], w[i], ", ".join(x[0] for x in bad))
    say("PASS" if not bad_rg and not miss and not notab else "FAIL", "N22",
        "range datum by R9's plan (status/P4c_datum.json): %d FBS + %d FBD secondaries, %d off by more than 1e-6%s%s%s"
        % (nf, nb, len(bad_rg), worst(bad_rg, 2), miss, "" if not notab else "; not in recon/modes.json: %s" % ", ".join(notab)))
    print("        N22 modes from %s" % msrc)
    say("PASS" if not bad_az and not miss else "FAIL", "G16",
        "azimuth datum by R9's plan: %d off by more than 1e-6%s%s" % (len(bad_az), worst(bad_az, 1), miss))
    r9_arith(W, say, plan, r9, r, fbs, tab)


def r9_arith(W, say, plan, r9, r, fbs, tab):
    """v0.13 r2 (the part 6 review's P6R-08): R9's plan against the arithmetic its own record holds, so accept does not rest
    on the plan alone: each date's plan = x converted by the shelves' SLR and PRF the record holds (rg = x_rg x SLR(REF) /
    SLR(d), az = x_az x PRF(d) / PRF(REF), 17.3's step 5) within 1e-9; x(REF) 0 and 0; each date's SLR recon/modes.json's
    slr_m within 1e-9 (relative), and SLR(d) / SLR(REF) the modes' spacing ratio (1 or 2 or 0.5) within 1e-6."""
    import json
    xa, xr, sp = (r9 or {}).get("x_az"), (r9 or {}).get("x_rg"), (r9 or {}).get("slr_prf")
    if not (isinstance(xa, dict) and isinstance(xr, dict) and isinstance(sp, dict)):
        say("FAIL", "R9", "R9's arithmetic: status/P4c_datum.json holds no r9.x_az, r9.x_rg and r9.slr_prf to check the "
                          "plan by (%s)" % ", ".join(k for k, v in (("x_az", xa), ("x_rg", xr), ("slr_prf", sp)) if not isinstance(v, dict)))
        return
    slr_m = {}
    try:
        for x in json.load(open(os.path.join(W, "recon", "modes.json"))).get("dates") or []:
            slr_m[x.get("date")] = x.get("slr_m")
    except Exception:
        pass
    nan = float("nan")

    def fl(v):   # a number of the record, NaN when it is not one
        try:
            return float(v)
        except (TypeError, ValueError):
            return nan

    def pair(d):   # (SLR, PRF) the record holds for d
        v = sp.get(d)
        return (fl(v[0]), fl(v[1])) if isinstance(v, (list, tuple)) and len(v) == 2 else (nan, nan)

    def div(a, b):
        return a / b if b == b and b != 0 else nan
    bad = []
    sref, pref = pair(r)
    if not (fl(xa.get(r)) == 0.0 and fl(xr.get(r)) == 0.0):
        bad.append("x(REF %s) az %r rg %r, not 0 and 0" % (r, xa.get(r), xr.get(r)))
    spc = {"FBS": 1.0, "FBD": 2.0}
    mref = "FBS" if r in fbs else "FBD"
    for d in sorted(plan):
        s, p = pair(d)
        rg, az = div(fl(xr.get(d)) * sref, s), div(fl(xa.get(d)) * p, pref)   # lp_datum.r9_solve's order of operations
        if not (abs(rg - plan[d][1]) <= 1e-9 and abs(az - plan[d][0]) <= 1e-9):
            bad.append("%s plan az %+.9f rg %+.9f, x by SLR and PRF %+.9f %+.9f" % (d, plan[d][0], plan[d][1], az, rg))
        if not abs(div(s, fl(slr_m.get(d))) - 1.0) <= 1e-9:
            bad.append("%s SLR %r, recon/modes.json's slr_m %r" % (d, s, slr_m.get(d)))
        want = spc["FBS" if d in fbs else "FBD"] / spc[mref]
        if tab is not None and d in tab and not abs(div(s, sref) - want) <= 1e-6 * want:
            bad.append("%s SLR / SLR(REF) %.9f, its mode %s wants %g" % (d, div(s, sref), "FBS" if d in fbs else "FBD", want))
    say("PASS" if not bad else "FAIL", "R9",
        "R9's arithmetic in status/P4c_datum.json: each date's plan = x by its SLR and PRF (17.3) within 1e-9, x(REF) 0 and 0, "
        "SLR = recon/modes.json's slr_m and the modes' ratio, on %d dates: %d off%s" % (
            len(plan), len(bad), "" if not bad else " (%s%s)" % ("; ".join(bad[:4]), " and %d more" % (len(bad) - 4) if len(bad) > 4 else "")))


def modes_fbs(W):
    """D6: (the FBS dates, their source, the table's dates or None). recon/modes.json when the frame has one (its 'dates'
    rows, mode FBS), else the kit's rule: the folders of raw_fbs_unpacked/ (no table: None)."""
    import json
    mj = os.path.join(W, "recon", "modes.json")
    if os.path.isfile(mj):
        rows = json.load(open(mj)).get("dates") or []
        fbs = set(x.get("date") for x in rows if x.get("mode") == "FBS")
        return fbs, "recon/modes.json (%d FBS of %d dates)" % (len(fbs), len(rows)), set(x.get("date") for x in rows)
    fbs = set(os.path.basename(x)
              for x in glob.glob(os.path.join(W, "raw_fbs_unpacked", "*")))
    return fbs, "raw_fbs_unpacked/ (%d folders; the frame has no recon/modes.json)" % len(fbs), None

# ---------------------------------------------------------------- G22 patch
def watermask(W, say):
    """G22 / N60 (24 Sept 2026): linog_watermask.py --apply ran after the last
    MintPy mask write, and Phase 6 delivered from the water-masked geo mask."""
    import json, hashlib
    try:
        import h5py
    except ImportError:
        say("WARN", "G22", "h5py unavailable, water-mask check skipped")
        return
    M = os.path.join(W, "mintpy")
    sj = os.path.join(M, "watermask", "summary.json")
    if not os.path.exists(sj):
        say("FAIL", "G22", "no mintpy/watermask/summary.json - linog_watermask.py --apply never ran")
        return
    s = json.load(open(sj))
    for rel in ("maskTempCoh.h5", "geo/geo_maskTempCoh.h5"):
        p = os.path.join(M, rel)
        if not os.path.exists(p):
            say("FAIL", "G22", "%s missing" % rel)
            continue
        with h5py.File(p, 'r') as f:
            has = 'LINOG_WATERMASK' in f.attrs
        same = hashlib.md5(open(p, 'rb').read()).hexdigest() == s.get("md5", {}).get(rel)
        if has and same:
            say("PASS", "G22", "%s carries the water mask, md5 = summary.json" % rel)
        elif has:
            say("WARN", "G22", "%s carries the water mask but was rewritten since (md5 != summary.json)" % rel)
        else:
            say("FAIL", "G22", "%s has NO water mask - MintPy rewrote it; run the watermask phase, then deliver" % rel)
    out = glob.glob(os.path.join(M, "geo", "LInOG_Upload_*"))
    tif = glob.glob(os.path.join(out[0], "*_Velocity_demErr.tif")) if len(out) == 1 else []
    if len(tif) != 1:
        say("WARN", "G22", "delivery not checked: %d LInOG_Upload_* dirs, %d demErr tif" % (len(out), len(tif)))
        return
    try:
        import numpy as np
        from osgeo import gdal
        gdal.UseExceptions()
        gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
        ds = gdal.Open(tif[0])
        n = int(np.isfinite(ds.GetRasterBand(1).ReadAsArray()).sum())
        ds = None
        with h5py.File(os.path.join(M, "geo", "geo_maskTempCoh.h5"), 'r') as f:
            gm = int(f['mask'][:].astype(bool).sum())
    except Exception as e:
        say("WARN", "G22", "delivery not checked: %s" % type(e).__name__)
        return
    say("PASS" if n == gm else "FAIL", "G22",
        "%s valid %d, water-masked geo mask %d%s (mask removed %s geo px, %s kept on water)"
        % (os.path.basename(tif[0]), n, gm, "" if n == gm else " - delivery predates the water mask; re-run deliver",
           s.get("geo_before", 0) - s.get("geo_after", 0), s.get("geo_flags", {}).get("3", "?")))

# ---------------------------------------------------------------- G23 patch
def edgemask(W, say):
    """G23 / WM-D3 (24 Sept 2026): linog_watermask.py rule v2 masked the dark
    swath-edge strips; no valid px 20 dB or more below the interior is left."""
    import json
    try:
        import h5py
        import numpy as np
    except ImportError:
        say("WARN", "G23", "h5py unavailable, edge check skipped")
        return
    M = os.path.join(W, "mintpy")
    sj = os.path.join(M, "watermask", "summary.json")
    if not os.path.exists(sj):
        say("FAIL", "G23", "no mintpy/watermask/summary.json - linog_watermask.py --apply never ran")
        return
    s = json.load(open(sj))
    e = s.get("edge")
    if not e or not str(s.get("rule", "")).startswith("LInOG masks v2"):
        say("FAIL", "G23", "the masks predate rule v2 (no swath-edge strips) - run the watermask phase with linog_watermask.py v2, then deliver")
        return
    st = ", ".join("%s %d+%d" % (x["edge"], x["nodata"], x["dark"]) for x in e["strips"])
    try:
        with h5py.File(os.path.join(M, "watermask", "waterFlag.h5"), "r") as f:
            flag = f["waterFlag"][:]
        with h5py.File(os.path.join(M, "maskTempCoh.h5"), "r") as f:
            mk = f["mask"][:].astype(bool)
        left = int((np.isin(flag, (6, 7)) & mk).sum())
    except Exception as ex:
        say("WARN", "G23", "strips not checked: %s" % type(ex).__name__)
        return
    say("PASS" if left == 0 else "FAIL", "G23",
        "swath-edge strips (no-data+dark px: %s): %s valid px masked, %d valid px left in them"
        % (st, e.get("masked_valid", "?"), left))
    d = e.get("deep_after", {})
    n, fa = d.get("near", -1), d.get("far", -1)
    say("PASS" if n == 0 and fa == 0 else "WARN", "G23",
        "valid px 20 dB or more below the interior after the masks: %d within 10 px of an edge or no-data, %d farther" % (n, fa))

if __name__ == "__main__":
    main()
