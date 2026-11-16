#!/usr/bin/env bash
# linog_path.sh -- linog_auto v0.10: the path runner (record 108.5, item 4). The frames of one path, one after another,
# (v0.13, R8: a path the table lacks runs only by its named frames; a path outside 1 to 671 is refused as such)
# each through linog_auto.sh from this pipeline folder; each frame's outcome recorded; a stop on one frame does not stop
# the next (the stopped frame keeps its tree for its resume); the free disk printed before each start (recon's G0.15
# holds each frame to its own budget). Used only after F3300 passes alone (record 102.9).
#
#   linog_path.sh <PATH> [FRAME ...] [--decide ask|auto] [--to PHASE] [--dry-run DIR]
#
# No FRAME: the frames the path table lists for the path (its expect_<frame> keys), in order, those with a tree already
# among them (P084's F3310 and F3320 are delivered: each is run again in place, as linog_auto.sh does): name the frames to
# run. v0.13 (the part 1 review's B1): a listed frame whose folder linog_auto did not make (recon's G0.20: the course kit's
# delivered ascending trees sit at the default frame folders) is skipped and named; a named frame is refused by the driver
# itself (rc 2, nothing written). No --decide: linog_auto.sh's default, ask. --dry-run DIR: each frame's dry run under DIR/p<PATH>_f<FRAME>/
# (linog_auto.sh's --dry-run: nothing written in the tree), and the runner's own records in DIR, which may be neither
# inside the path's folder <root>/p<PATH>/ nor around it. A real run keeps the runner's records in <root>/p<PATH>/_path_runs/<UTC>_<pid>/: runner.tsv (one line
# a frame: frame, start, rc, seconds, the driver's last "==" line) and frame_<FRAME>.log (the frame's console).
# Exit 0 every frame ended rc 0; 5 a frame ended otherwise (the others ran); 130, 143 or 129 stopped by a signal (no
# frame started after it; Ctrl-C or a TERM to the process group also stops the frame's run, whose driver ends its record;
# a TERM to the runner alone lets the frame's run end first); 3 a usage error or the wrong host, or every listed frame
# skipped (no frame started); 2 (v0.13) recon's G0.19 refused the root before the runner wrote its records (nothing written).
set -u
set -o pipefail

A=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PY="python3 -E -B"
die() { printf '*** linog_path: %s\n' "$1" >&2; exit "${2:-3}"; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

[ $# -ge 1 ] || die "usage: linog_path.sh <PATH> [FRAME ...] [--decide ask|auto] [--to PHASE] [--dry-run DIR]"
PN=$1; shift
FRAMES=(); DECIDE=; TO=; DRY=
while [ $# -gt 0 ]; do
  case "$1" in
    --decide)  DECIDE=${2:-}; shift 2 || die "--decide needs ask or auto";;
    --to)      TO=${2:-}; shift 2 || die "--to needs a phase";;
    --dry-run) DRY=${2:-}; shift 2 || die "--dry-run needs a folder";;
    -*) die "unknown option $1";;
    *) FRAMES+=("$1"); shift;;
  esac
done
case "$DECIDE" in ''|ask|auto) ;; *) die "--decide takes ask or auto, not '$DECIDE'";; esac
case "$PN" in *[!0-9]*|'') die "the path must be a number, not '$PN'";; esac
[ $((10#$PN)) -ge 1 ] && [ $((10#$PN)) -le 671 ] || die "path $PN is not a path number (1 to 671)"
if [ -n "$TO" ]; then   # the driver's own phase list
  PL=$(sed -n 's/^PHASES="\([^"]*\)"$/\1/p; /^PHASES="[^"]*$/,/"$/{s/^PHASES="//; s/"$//; p}' "$A/linog_auto.sh" | tr -s ' \n' ' ' | sed 's/^ //; s/ $//')
  case " $PL " in *" $TO "*) ;; *) die "--to: unknown phase '$TO' (linog_auto.sh has: $PL)";; esac
fi
HOSTWANT=${LINOG_AUTO_HOST:-felix}
[ "$(hostname)" = "$HOSTWANT" ] || die "wrong host $(hostname), expected $HOSTWANT"
PNN=$(printf '%03d' $((10#$PN)))
SKIP=()   # v0.13: the listed frames skipped (G0.20)
if [ ${#FRAMES[@]} -eq 0 ]; then
  # the table's frames for the path (its expect_<frame> keys), in order; read into a variable first, so a path the table
  # cannot give stops here (a process substitution would hide the exit status)
  FL=$($PY -c 'import sys
sys.path.insert(0, sys.argv[1])
import lp_common as C
try:
    c = C.load_cfg(C.norm_path(sys.argv[2]))
except (ValueError, KeyError, FileNotFoundError) as e:
    sys.stderr.write("*** linog_path: %s\n" % e)
    sys.exit(1)
print(c["entry"])
print("\n".join(sorted(k[7:] for k in c if k.startswith("expect_"))))' "$A" "$PN") || die "cannot read the path table for path $PN (the line above)"
  mapfile -t FL2 <<< "$FL"
  [ "${FL2[0]}" = derived ] && die "path $PN is not in the path table (R8 derives its entry): name its frames"
  FRAMES=("${FL2[@]:1}")
  [ ${#FRAMES[@]} -gt 0 ] && [ -n "${FRAMES[0]}" ] || die "the path table lists no frame for path $PN (no expect_<frame> key): name the frames"
  # v0.13 (the part 1 review's B1): only frames whose folder is absent or linog_auto's own (recon's G0.20); the others named
  KEEP=(); SKIP=()
  for F in "${FRAMES[@]}"; do
    FC=$($PY "$A/lp_recon.py" --path "$PN" --frame "$F" --framecheck 2>&1); fcr=$?
    if [ "$fcr" -eq 0 ]; then KEEP+=("$F")
    elif [ "$fcr" -eq 2 ]; then SKIP+=("$F"); echo "   skipped frame $F: $(echo "$FC" | sed -n 's/^ *G0\.20 *FAIL *the frame folder *//p' | head -1)"
    else die "recon's frame check for frame $F failed (rc $fcr): $FC"; fi
  done
  [ ${#KEEP[@]} -gt 0 ] || die "every frame the path table lists for path $PN (${SKIP[*]}) has a folder linog_auto did not make (G0.20, above): none run; set LINOG_ROOT to a root of your own"
  FRAMES=("${KEEP[@]}")
fi
for F in "${FRAMES[@]}"; do
  case "$F" in *[!0-9]*|'') die "a frame must be a number, not '$F'";; esac
  [ $((10#$F)) -le 7199 ] || die "a frame is 0 to 7199, not '$F'"
done
W0=$($PY "$A/lp_common.py" framedir "$PN" "${FRAMES[0]}") || die "cannot resolve path $PN in the path table"
PDIR=$(dirname "$W0")
RUNID=$(date -u +%Y%m%dT%H%M%SZ)_$$
if [ -n "$DRY" ]; then
  PR=$(realpath -m -- "$PDIR"); DR=$(realpath -m -- "$DRY"); PR=${PR%/}/; DR=${DR%/}/
  case "$DR" in "$PR"*) die "the dry-run folder $DRY is inside the path's folder $PDIR; give a folder outside it";; esac
  case "$PR" in "$DR"*) die "the dry-run folder $DRY holds the path's folder $PDIR; give a folder outside it";; esac
  mkdir -p "$DRY" || die "cannot create $DRY"
  LD=$(cd "$DRY" && pwd)
else
  # v0.13 (the part 1 review's M1): recon's G0.19 before the runner writes its records into the root
  RC0=$($PY "$A/lp_recon.py" --path "$PN" --frame "${FRAMES[0]}" --rootcheck 2>&1); rc0=$?
  echo "$RC0"
  [ "$rc0" -eq 0 ] || { [ "$rc0" -eq 2 ] && die "recon's G0.19 refused the root (the line above): nothing written" 2; die "recon's root check failed (rc $rc0, the line above): nothing written" 3; }
  LD="$PDIR/_path_runs/$RUNID"
  mkdir -p "$LD" || die "cannot create $LD"
fi
FS=$PDIR; while [ ! -e "$FS" ]; do FS=$(dirname "$FS"); done
echo "== linog_path v0.13  path $PNN, ${#FRAMES[@]} frame(s): ${FRAMES[*]}${SKIP:+ (skipped, G0.20: ${SKIP[*]})}  $(utc)  host $(hostname)  user $(id -un)"
echo "   pipeline $A"
[ -n "$DRY" ] && echo "   records  $LD   (DRY RUN: the frames' dry runs under it)" || echo "   records  $LD"
[ -e "$LD/runner.tsv" ] || printf 'frame\tstart\trc\tseconds\tlast\n' > "$LD/runner.tsv"
SIG=; trap 'SIG=130' INT; trap 'SIG=143' TERM; trap 'SIG=129' HUP
worst=0; i=0
for F in "${FRAMES[@]}"; do
  [ -z "$SIG" ] || { echo; echo "== linog_path STOPPED by a signal before frame $F: no further frame started"; break; }
  i=$((i+1))
  FN=$(printf '%04d' $((10#$F)))
  echo; echo "== frame $FN ($i of ${#FRAMES[@]})  $(utc)  free $(df -BG --output=avail "$FS" | tail -1 | tr -d ' ') at $FS"
  args=("$PN" "$FN")
  [ -n "$DECIDE" ] && args+=(--decide "$DECIDE")
  [ -n "$TO" ] && args+=(--to "$TO")
  [ -n "$DRY" ] && args+=(--dry-run "$LD/p${PNN}_f${FN}")
  s0=$(utc); t0=$(date +%s)
  # the console copy ignores SIGINT (-i), SIGTERM and SIGHUP: a signal to the process group then stops the frame's run
  # (the driver ends its record and its ledger line, rc 130, 143 or 129), and the copy keeps the driver's last lines and
  # its exit status (a copy killed with the group would leave the driver writing into a closed pipe: rc 141, SIGPIPE)
  bash "$A/linog_auto.sh" "${args[@]}" 2>&1 | ( trap '' TERM HUP; exec tee -i "$LD/frame_${FN}.log" )
  rc=${PIPESTATUS[0]}
  last=$(grep -E '^== (STOPPED|DRY RUN STOPPED|DRY RUN complete|linog_auto done)' "$LD/frame_${FN}.log" | tail -1)
  [ -n "$last" ] || last=$(grep -E '^\*\*\* linog_auto: ' "$LD/frame_${FN}.log" | tail -1)
  if [ -z "$last" ]; then
    case "$rc" in 129|130|143) last="stopped by a signal (rc $rc): the frame's logs/STATUS.txt has its END line";; *) last="no closing line";; esac
  fi
  printf '%s\t%s\t%d\t%d\t%s\n' "$FN" "$s0" "$rc" "$(( $(date +%s) - t0 ))" "$last" >> "$LD/runner.tsv"
  echo "== frame $FN: rc $rc"
  [ "$rc" -eq 0 ] || worst=5
  if [ -n "$SIG" ] || [ "$rc" -eq 130 ] || [ "$rc" -eq 143 ] || [ "$rc" -eq 129 ]; then
    [ -n "$SIG" ] || SIG=$rc
    echo; echo "== linog_path STOPPED by a signal after frame $FN: no further frame started"
    break
  fi
done
echo; echo "== linog_path done $(utc): the frames (frame, start, rc, seconds, the driver's last line), from $LD/runner.tsv"
tail -n +2 "$LD/runner.tsv" | while IFS=$'\t' read -r f s r t l; do printf '   %s  %s  rc %s  %6s s  %s\n' "$f" "$s" "$r" "$t" "$l"; done
[ -z "$SIG" ] || exit "$SIG"
exit "$worst"
