#!/usr/bin/env bash
# linog_auto.sh -- LInOG ALOS-1 automated pipeline, entry point.   v0.13 (2026-10-16), the ascending automation (ascending
# record 22.2): recon for any path (R8: a derived entry where the table lacks the path, G0.17, G0.18, G0.14 on the frame's
# own CEOS corners) and the framing check G0.16 (9.3); this driver checks its own python3's version and, before it writes
# anything, that the root is the caller's own or named by LINOG_ROOT (recon's G0.19; 12.3, items 2 and 3) and that the
# frame folder is absent or linog_auto's own (recon's G0.20, the part 1 review's B1: the course kit's delivered trees sit
# at the default frame folders, and linog_auto never writes into them). Phase 1 takes
# FBS+FBD and FBD-only frames (R6, R6-d): the new phase bandlimit (P1bs) band-limits a mixed frame's FBS dates to 14 MHz in
# place with the kit's own tool, verify reads the FBD dates' polarisation (G4) and every shelve's instrument (G1c.8), and
# Phase 1's env gates check the env's prefix (12.3, item 4); 31 phases.
# v0.12 (2026-10-09): the new phase drop1 (P5d1, after sbas)
# tests every pair R1 flags, over land or over the whole grid, against its 10 nearest unflagged peers by dropping each and
# inverting again (Doc JD's drop-one test, record 119.5; the rule, 120.5; the plan, 124.7; Ariel's word, 125.0), and
# admit (LOGIC 4) no longer culls by R2 alone; under --decide auto drop1 takes its cull and asks a restart, as d9ab's R5,
# and a run allows one restart per asking phase (drop1 and d9ab: at most 2); 30 phases.
# v0.11 (2026-10-09): deliver sets the KMZs' entry times to
# 1980-01-01 00:00:00 (G6a.10, lp_kmz.py), and the new phase rerun (P6d) checks the package against an earlier one of the frame
# (lp_compare.py, also a tool beside the pipeline), record 122.6; 29 phases, the default --to rerun.
# v0.10 (2026-10-07): admit decides D3 by the rules R1 to R3
# (the kit over land, dead and thin dates, the cull cap), d9ab takes a bridging verdict under --decide auto (R5: the frame
# restarted once from the top), and the new phase dfit tests the screened dates on the velocity fit (R4), record 108.3;
# 28 phases. v0.9 (2026-10-04): Phases 0 to 6; refine and igram plan
# ISCE2's FFTs with the pinned FFTW wisdom (linog_fftw.cfg, fftw/), and RUN_MANIFEST.json records it. v0.8 (2026-09-29): D9
# by the A/B after sbas (d9ab), and RUN_MANIFEST.json's reference cell, lead product and readings.
#
#   linog_auto.sh <PATH> <FRAME> [--to PHASE] [--only PHASE] [--force PHASE] [--recover] [--decide ask|auto] [--dry-run DIR]
#   linog_auto.sh --selftest DIR
#
# Phases:  recon (P0a, read-only on the archive)   stage (P0b, skeleton and links)
#          extract (P1a, zips -> unzipped/<zip stem>/)   unpack (P1b, -> SLC/<date>/)
#          rwin (P1br, each shelve's r0 set from its CEOS image records, the old shelve kept in _archive/rwin_<UTC>/)
#          bandlimit (P1bs, v0.13: an FBS+FBD frame's FBS dates band-limited to 14 MHz in place by the kit's tool, each
#                     unpacked file kept beside it as <date>.slc.prefilter; N/A on an FBS-only or FBD-only frame)
#          verify (P1c, -> recon/modes.json)
#          stack1 (P2a, pass 1 -> stack/pass1.vN/)   reference (P2b, D1 and G17 -> recon/reference.json)
#          stack2 (P2c, pass 2: a trial in stack/pass2.vN/, then configs/, run_files/, baselines/; the water-mask strip)
#          topo (P3a, run_01)   coarse (P3b, run_02 and run_03, then G21 and G7)   refine (P4a, run_04 with the pinned FFTW wisdom, G8)
#          invert (P4b, run_05)   datum (P4c, G16 and G9)   fine (P4d, run_06, G10)   bgrid (P4e, run_07)
#          igram (P4f, G17, run_08 with the pinned FFTW wisdom, G11)
#          report (P4g, Phase 4.5: the interferogram report, north up from the frame's geometry -> Igrams/reports/)
#          admit (P5a, the kit's G18/G20; v0.10: D3 by R1 to R3 over land; D9 no, MintPy's default, unless the operator or R5
#                names it -> recon/admission.json)
#          prep (P5b, MintPy's prep_isce.py: the .rsc files, G12, N13, N20)
#          mcfg (P5c, mintpy/smallbaselineApp.cfg from MintPy's defaults, the bootstrap load_data, SNWE, G24)
#          sbas (P5d, load_data to modify_network, the kit's G19 pick, reference_point to geocode; G15, G24, N14)
#          drop1 (P5d1, v0.12: each flagged pair of the network against its peers: MintPy's ifgram_inversion.py on a copy of
#                 the stack without the pair, the coherent land it gains or loses against sbas's; culled when it gains more
#                 than every peer, R2's guards on the cull; under --decide auto the cull is taken -> drop1/<UTC>/)
#          d9ab (P5dab, v0.8: MintPy with bridging on a copy of mintpy/'s inputs, compared with sbas's products by the rule
#                of record 62.0; its bridging is a DECISION unless the operator chose the method -> d9ab/<UTC>/)
#          wmask (P5e, the kit's linog_watermask.py --apply: the water and swath-edge masks, G22 and G23)
#          dfit (P5f, v0.10: R4, a screened date on the velocity fit: MintPy's fit A against it without the date, B; the date
#                leaves the fit, mintpy/exclude_date.txt, when B's std over maskTempCoh is lower -> dfit/<UTC>/)
#          deliver (P6a, the kit's linog_phase6.sh: the 16 files of mintpy/geo/LInOG_Upload_<TAG>/; D5 the report's
#                   pages in its reports/, D7 the H/V labels from los.rdr, F55 RUN_MANIFEST.json at the frame root, with
#                   v0.8's reference cell, D9's A/B, the lead product and the readings)
#          accept (P6b, the pipeline's copy of the kit's verifier on the frame, D6: FAIL 0 to pass)
#          package (P6c, D8: _xfer/<PREFIX>_<TAG>_<VERSION>_<date>_review/ by hard links, TRANSFER_MANIFEST_<TAG>.txt)
#          rerun (P6d, v0.11: the package against recon/rerun_reference.txt's, else the newest archived tree's; every file equal
#                 but RUN_MANIFEST.json PASS; a difference on the same network DECISION, taken by recon/rerun.txt)
# unpack, rwin, bandlimit, verify, Phases 2 to 6b and 6d (drop1 among them) run inside lp_env.sh (a clean linog_isce2, as linog_env.cfg says); the others need only python3.
# Phases 3 and 4 run the run files' lines from the frame folder, as many at once as linog_run.cfg says (and memory holds).
# --decide ask (the default) stops at the reference with DECISION NEEDED until recon/reference.txt names it; auto takes D1's pick.
# The same holds for admit (v0.10): the rules' exclusions (R3's dates, R2's cull) are taken under auto and asked under ask
# (recon/admission.txt records the operator's choice, which takes their place); R3 past its limits is always asked. D9:
# admit takes no unless recon/admission.txt names the method; d9ab's A/B reading bridging is asked under ask, and under
# auto (R5) d9ab takes it: it moves mintpy/ into _archive/, writes recon/d9ab_decision.json and status/restart.json, and
# this driver runs the frame again from the top. The ledger gets "auto_run RESTART id=... after=<phase>" between the
# passes. v0.12: drop1 takes its cull the same way (recon/drop1_decision.json, mintpy/ moved into _archive/, a restart
# from admit). A phase may ask one restart a run: LINOG_RESTART=allowed is exported to it in a run without --only until it
# has asked, and no after (a second verdict of that phase in the same run is then its DECISION); a second request from
# the same phase all the same stops the run, rc 4. So a run restarts at most twice (drop1, then d9ab); v0.13: three times
# (coarse's R7, drop1, d9ab): under auto coarse takes the dates G21 or G7 flag (R7, the ascending record 11.2 to 11.7; its
# limits L0 to L8), moves their traces into _archive/d2_<UTC>/, writes recon/d2_decision.json and status/restart.json, and
# the frame runs again from the top, recon dropping them and coarse reusing the other dates' products.
# Each phase writes <frame>/status/P<idx>_<phase>.json at START (RUNNING) and at END, and the ledger
# <frame>/logs/STATUS.txt gets "auto_<phase> START" and "auto_<phase> END rc=N", inside "auto_run START id=..."
# and "auto_run END id=... rc=N". A phase whose record is PASS with unchanged inputs is skipped. FAIL (rc 2),
# ERROR (3) or DECISION NEEDED (4) stops the run, and the reason is printed from the record. One run per frame
# at a time (flock on status/.lock).
# --dry-run DIR: recon reads the archive and writes its records under DIR; Phase 1 prints its plans and checks its
#                tools and the environment (rwin, when the frame's unpack is PASS on record, reads the frame's CEOS
#                records and shelves and prints what it would change); Phase 2, when the frame's verify is PASS on record, runs both stack
#                passes into DIR/stack/ and chooses the reference from them; Phases 3 and 4 check their tools and
#                print their plans; report renders into DIR/Igrams/reports/, admit writes DIR/recon/admission.json, mcfg
#                writes and checks the template in DIR/mintpy/ (no load), prep and sbas print their plans; d9ab, when the
#                frame's sbas is PASS, runs its A/B with B under DIR/d9ab/ (MintPy on the copy; the frame only read); wmask,
#                when the frame's sbas is PASS, runs the kit tool's own dry run into DIR/mintpy/watermask_dryrun/; dfit (v0.10),
#                when the frame's wmask is PASS, fits A and B under DIR/dfit/ and writes nothing in the frame; deliver
#                prints its plan and writes DIR/RUN_MANIFEST.json as it would be (the readings from the frame's delivery,
#                when it has one); accept runs the verifier copy on the frame as it is
#                (a baseline); package prints its plan; the frame folder is only read, and not while a run holds its
#                lock. DIR inside the frame folder, or holding it, is refused.
# Environment: LINOG_AUTO_CFG (path table), LINOG_ENV_CFG (environment pins), LINOG_STACK_CFG (Phase 2 settings and
#              pins), LINOG_RUN_CFG (Phases 3 and 4 settings and pins), LINOG_MINTPY_CFG (Phase 4.5 and 5 settings and pins),
#              LINOG_PHASE6_CFG (Phase 5e and 6 settings and pins), LINOG_FFTW_CFG (v0.9: the FFTW wisdom's pins),
#              LINOG_ROOT, LINOG_ARCHIVE, LINOG_DEM, LINOG_AUTO_HOST
#              (expected host name, default felix; tests only).
set -u
set -o pipefail

A=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PY="python3 -E -B"   # -E: PYTHONPATH and other PYTHON* variables ignored (these phases are standard library only); -B: no __pycache__ in the install
PHASES="recon stage extract unpack rwin bandlimit verify stack1 reference stack2 topo coarse refine invert datum fine bgrid igram report admit prep
        mcfg sbas drop1 d9ab wmask dfit deliver accept package rerun"
idx_of() { case "$1" in recon) echo 0a;; stage) echo 0b;; extract) echo 1a;; unpack) echo 1b;; rwin) echo 1br;; bandlimit) echo 1bs;; verify) echo 1c;;
  stack1) echo 2a;; reference) echo 2b;; stack2) echo 2c;; topo) echo 3a;; coarse) echo 3b;; refine) echo 4a;;
  invert) echo 4b;; datum) echo 4c;; fine) echo 4d;; bgrid) echo 4e;; igram) echo 4f;; report) echo 4g;; admit) echo 5a;;
  prep) echo 5b;; mcfg) echo 5c;; sbas) echo 5d;; drop1) echo 5d1;; d9ab) echo 5dab;; wmask) echo 5e;; dfit) echo 5f;; deliver) echo 6a;; accept) echo 6b;;
  package) echo 6c;; rerun) echo 6d;;
  *) echo "";; esac; }
cmd_of() {   # PHASE: its command line in the array CMD; the env phases through lp_env.sh with the env's python3.
  # A simple command in the pipeline (not a function) keeps the phase a direct child of this shell, so a stopped
  # run waits for the phase to end its record before it writes its own END line.
  case "$1" in
    unpack|rwin|bandlimit|verify|stack1|reference|stack2|topo|coarse|refine|invert|datum|fine|bgrid|igram|report|admit|prep|mcfg|sbas|\
    drop1|d9ab|wmask|dfit|deliver|accept|rerun)
      CMD=(bash "$A/lp_env.sh" python3 -B "$A/lp_$1.py");;
    *) CMD=($PY "$A/lp_$1.py");;
  esac; }
die() { printf '*** linog_auto: %s\n' "$1" >&2; exit "${2:-3}"; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
recmd5() { [ -f "$1" ] && md5sum < "$1" | cut -c1-32; }
why() {   # $1 record, $2 its md5 before the phase ran
  if [ ! -f "$1" ] || [ "$(recmd5 "$1")" = "$2" ]; then echo "the phase wrote no record (it did not start; see the lines above)"
  else $PY "$A/lp_common.py" reason "$1" 2>/dev/null; fi; }

[ $# -ge 1 ] || die "usage: linog_auto.sh <PATH> <FRAME> [--to P] [--only P] [--force P] [--recover] [--decide ask|auto] [--dry-run DIR] | --selftest DIR"
# v0.13 (12.3, item 3): the driver's own python3 runs recon, stage, extract, package and every --state; the first python3 on
# the caller's PATH, so its version is checked (lp_common.py: Python 3.6 or later) and printed below
PYV=$($PY -c 'import sys; print("%d.%d.%d" % sys.version_info[:3]); sys.exit(0 if sys.version_info >= (3, 6) else 1)' 2>&1) || \
  die "the driver's python3 ($(command -v python3 || echo none), ${PYV:-no version}) is not Python 3.6 or later: put a python3 3.6 or later (felix: /usr/bin/python3) first on the PATH"
if [ "$1" = "--selftest" ]; then
  [ $# -ge 2 ] || die "--selftest needs a folder for its mock data"
  # v0.13 (the part 1 review's m1): every suite, whatever the caller's LINOG_SELFTEST_SUITES (a development switch)
  exec env -u LINOG_SELFTEST_SUITES $PY "$A/lp_selftest.py" "$2"
fi
[ $# -ge 2 ] || die "usage: linog_auto.sh <PATH> <FRAME> [options]"
PN=$1; FR=$2; shift 2
TO=rerun; ONLY=; FORCE=; RECOVER=0; DRY=; DECIDE=ask
while [ $# -gt 0 ]; do
  case "$1" in
    --to)      TO=${2:-}; shift 2 || die "--to needs a phase";;
    --only)    ONLY=${2:-}; shift 2 || die "--only needs a phase";;
    --force)   FORCE=${2:-}; shift 2 || die "--force needs a phase";;
    --recover) RECOVER=1; shift;;
    --decide)  DECIDE=${2:-}; shift 2 || die "--decide needs ask or auto";;
    --dry-run) DRY=${2:-}; shift 2 || die "--dry-run needs a folder";;
    *) die "unknown option $1";;
  esac
done
for p in "$TO" "$ONLY" "$FORCE"; do
  [ -z "$p" ] || [ -n "$(idx_of "$p")" ] || die "unknown phase '$p' (v0.13 has: $(echo $PHASES))"
done
case "$DECIDE" in ask|auto) export LINOG_DECIDE=$DECIDE;; *) die "--decide takes ask or auto, not '$DECIDE'";; esac
HOSTWANT=${LINOG_AUTO_HOST:-felix}
[ "$(hostname)" = "$HOSTWANT" ] || die "wrong host $(hostname), expected $HOSTWANT"
W=$($PY "$A/lp_common.py" framedir "$PN" "$FR") || die "cannot resolve the frame folder for path $PN frame $FR"
echo "== linog_auto v0.13  path $PN frame $FR  $(utc)  host $(hostname)  user $(id -un)"
echo "   pipeline $A"
echo "   frame    $W"
# both Pythons (59.8): the driver's runs --state and the standard-library phases; the env's runs the phases in lp_env.sh
echo "   python   $($PY -c 'import sys; print(sys.executable, sys.version.split()[0])') (the driver's: --state, recon, stage, extract, package)"
echo "   python   $(bash "$A/lp_env.sh" python3 -E -B -c 'import sys; print(sys.executable, sys.version.split()[0])' 2>&1 | tail -1) (the env's, through lp_env.sh: the other phases)"

if [ -n "$DRY" ]; then
  # the dry-run folder must be neither the frame folder, nor inside it, nor around it: a dry run writes its records,
  # the report and the template there, and moves an earlier dry run's report and mintpy/ into its _archive/
  WR=$(realpath -m -- "$W"); DR=$(realpath -m -- "$DRY"); WR=${WR%/}/; DR=${DR%/}/   # "/" stays "/"
  case "$DR" in "$WR"*) die "the dry-run folder $DRY is the frame folder or inside it; give a folder outside $W";; esac
  case "$WR" in "$DR"*) die "the dry-run folder $DRY holds the frame folder $W; give a folder outside it";; esac
  # the dry run reads the frame (Phase 2 runs stackStripMap over its SLC/): not while a run holds the frame's lock,
  # and none can start meanwhile; the lock file is opened read-only and only when it exists, so nothing is created
  if [ -f "$W/status/.lock" ]; then
    exec 9<"$W/status/.lock"
    flock -n 9 || die "another linog_auto run holds $W/status/.lock; the dry run reads the frame, so it waits for that run" 4
  fi
  mkdir -p "$DRY" || die "cannot create $DRY"
  DRY=$(cd "$DRY" && pwd)
  echo "   DRY RUN: records under $DRY; the frame folder is not touched"
  for ph in $PHASES; do
    [ -n "$ONLY" ] && [ "$ph" != "$ONLY" ] && continue
    f="$DRY/status/P$(idx_of "$ph")_$ph.json"; m0=$(recmd5 "$f")
    echo; echo "-- P$(idx_of "$ph") $ph (dry run)"
    cmd_of "$ph"; "${CMD[@]}" --path "$PN" --frame "$FR" --dryrun "$DRY" 2>&1 | tee -i -a "$DRY/dryrun.log"
    rc=${PIPESTATUS[0]}
    [ "$rc" -eq 0 ] || { echo "== DRY RUN STOPPED at $ph, rc $rc: $(why "$f" "$m0")"; exit "$rc"; }
    [ "$ph" = "$TO" ] && break
  done
  echo; echo "== DRY RUN complete: $(utc)"
  exit 0
fi

# v0.13 (12.3, item 2): recon's G0.19 before anything is written: the root is the caller's own, or LINOG_ROOT names it;
# and G0.20 (the part 1 review's B1): the frame folder is absent, empty or linog_auto's own (status/P0a_recon.json)
RC0=$($PY "$A/lp_recon.py" --path "$PN" --frame "$FR" --rootcheck --framecheck 2>&1); rc0=$?
echo "$RC0"
if [ "$rc0" -ne 0 ]; then
  case "$RC0" in *"G0.19   FAIL"*) die "recon's G0.19 refused the root (the line above): nothing written" 2;; esac
  case "$RC0" in *"G0.20   FAIL"*) die "recon's G0.20 refused the frame folder $W, which linog_auto did not make (the line above): nothing written" 2;; esac
  die "recon's root check failed (rc $rc0, the line above): nothing written" 3
fi
mkdir -p "$W/status" "$W/logs" || die "cannot create $W/status and $W/logs"
exec 9>"$W/status/.lock"
flock -n 9 || die "another linog_auto run holds $W/status/.lock" 4
RUN=$(date -u +%Y%m%dT%H%M%SZ)_$$
printf '%s  auto_run START id=%s to=%s host=%s pipeline=%s\n' "$(utc)" "$RUN" "$TO" "$(hostname)" "$A" >> "$W/logs/STATUS.txt"
CUR=
trap 'exit 129' HUP; trap 'exit 130' INT; trap 'exit 143' TERM   # a stop is logged with its own rc, not 0
trap 'rc=$?; printf "%s  auto_run END id=%s rc=%d%s\n" "$(utc)" "$RUN" "$rc" "${CUR:+ stopped in $CUR}" >> "$W/logs/STATUS.txt"' EXIT
# v0.10, R5: a restart asked by a run that ended before this driver read it (the run starts from the top anyway) is kept
# aside, so it cannot restart this run
RF="$W/status/restart.json"
if [ -e "$RF" ]; then
  mv -n -- "$RF" "$W/status/restart_stale_${RUN}.json" && [ ! -e "$RF" ] || die "cannot move $RF aside" 3
  echo "   an earlier run's restart request kept as status/restart_stale_${RUN}.json (this run starts from the top)"
fi
ASKED=" "   # v0.12: the phases that asked a restart in this run (each may ask once)
RESTARTS=0
while :; do
  AGAIN=
  for ph in $PHASES; do
    idx=$(idx_of "$ph")
    if [ -n "$ONLY" ] && [ "$ph" != "$ONLY" ]; then continue; fi
    st=$($PY "$A/lp_$ph.py" --path "$PN" --frame "$FR" --state) || die "state check failed for $ph"
    echo; echo "-- P$idx $ph: record $st"
    case "$st" in
      CURRENT)
        if [ "$FORCE" != "$ph" ]; then
          echo "   skip: PASS on record, inputs unchanged"
          [ "$ph" = "$TO" ] && break
          continue
        fi;;
      RUNNING)
        [ "$RECOVER" = 1 ] || die "P$idx $ph has a RUNNING record without an END: an earlier run died (this run holds the lock, so none is active). Read $W/status/P${idx}_$ph.json, then re-run with --recover" 4
        echo "   --recover: re-running $ph";;
    esac
    f="$W/status/P${idx}_$ph.json"; m0=$(recmd5 "$f")
    lg="$W/logs/auto_P${idx}_$ph.log"; n=1
    while [ -e "$lg.v$n" ]; do n=$((n+1)); done
    lg="$lg.v$n"
    printf '%s  auto_%s START\n' "$(utc)" "$ph" >> "$W/logs/STATUS.txt"
    # v0.12: a phase may ask one restart a run; LINOG_RESTART tells it whether it still may (never under --only)
    case "$ASKED" in *" $ph "*) export LINOG_RESTART=no;; *) if [ -z "$ONLY" ]; then export LINOG_RESTART=allowed; else export LINOG_RESTART=no; fi;; esac
    CUR=$ph; cmd_of "$ph"; "${CMD[@]}" --path "$PN" --frame "$FR" 2>&1 | tee -i "$lg"
    rc=${PIPESTATUS[0]}
    printf '%s  auto_%s END rc=%d\n' "$(utc)" "$ph" "$rc" >> "$W/logs/STATUS.txt"; CUR=""
    if [ "$rc" -ne 0 ]; then
      echo; echo "== STOPPED at P$idx $ph, rc $rc: $(why "$f" "$m0")"
      echo "   log $lg"
      exit "$rc"
    fi
    if [ -e "$RF" ]; then   # v0.10, R5: the phase asked a restart (d9ab took bridging, v0.12 drop1 its cull; mintpy/ moved aside)
      RK="$W/status/restart_${RUN}_$((RESTARTS+1)).json"
      mv -n -- "$RF" "$RK" && [ ! -e "$RF" ] || die "cannot move $RF to $RK" 3
      why5=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1])).get("reason", "no reason recorded"))' "$RK" 2>/dev/null || echo unreadable)
      case "$ASKED" in *" $ph "*)
        printf '%s  auto_run RESTART REFUSED id=%s after=%s record=%s\n' "$(utc)" "$RUN" "$ph" "$(basename "$RK")" >> "$W/logs/STATUS.txt"
        echo; echo "== STOPPED after P$idx $ph, rc 4: a second restart asked by $ph in one run ($why5); read status/$(basename "$RK")"
        exit 4;;
      esac
      RESTARTS=$((RESTARTS+1)); AGAIN=$ph
      ASKED="$ASKED$ph "   # one restart a phase: a second verdict of this phase in this run is its DECISION, not a second move
      printf '%s  auto_run RESTART id=%s after=%s record=%s\n' "$(utc)" "$RUN" "$ph" "$(basename "$RK")" >> "$W/logs/STATUS.txt"
      echo; echo "== RESTART after P$idx $ph: $why5; the frame runs again from the top (the record: status/$(basename "$RK"))"
      break
    fi
    [ "$ph" = "$TO" ] && break
  done
  [ -n "$AGAIN" ] || break
done
echo; echo "== records in $W/status"
# v0.12: in the pipeline's order (lp_common.py's summary sorts by file name, which puts P5d1_drop1 before P5d_sbas; it stays
# byte-identical, since Phases 0 and 1 hold its md5 in their fingerprints)
SUM=(); for ph in $PHASES; do SUM+=("$W/status/P$(idx_of "$ph")_$ph.json"); done
$PY -c 'import json, os, sys
for f in sys.argv[1:]:
    if os.path.isfile(f):
        r = json.load(open(f))
        print("   P%-3s %-8s %-8s %-20s %s" % (r.get("index"), r.get("phase"), r.get("verdict"), r.get("end") or r.get("start"), r.get("reason")))' "${SUM[@]}"
echo "== linog_auto done up to $TO: $(utc)"
