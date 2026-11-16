#!/usr/bin/env bash
# lp_d6check.sh OUTDIR FRAME... -- D6's check (linog_auto v0.7): the kit's verifier and the pipeline's copy of it, run
# read-only on the same frames inside lp_env.sh, from OUTDIR (the verifier imports isce, whose logging opens isce.log in
# the working folder). The copy must print the kit's lines: the same lines once its own "N22 modes from ..." lines are
# left out, and the same exit code; how many source lines it printed (one per frame that reaches N22) is printed apart.
# The frames are named by absolute path (a relative one is taken from the folder this is run from) and listed (paths,
# types, sizes, mtimes) before and after. Writes only OUTDIR: kit.txt, copy.txt, copy_less_n22src.txt, d6.txt (these
# lines). Exit 0 when the copy prints the kit's lines and the frames are unchanged, 1 otherwise, 3 on a usage error.
set -u
A=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[ $# -ge 2 ] || { echo "usage: lp_d6check.sh OUTDIR FRAME..." >&2; exit 3; }
O=$1; shift
FR=(); for f in "$@"; do [ -d "$f" ] || { echo "lp_d6check.sh: no folder $f" >&2; exit 3; }; FR+=("$(realpath -- "$f")"); done
set -- "${FR[@]}"
mkdir -p "$O" && cd "$O" || exit 3
E=${LINOG_ENV_CFG:-$A/linog_env.cfg}
KIT=$(sed -n 's/^KIT=//p' "$E" | tail -1)
COPY=$A/$(sed -n 's/^VERIFY_COPY=//p' "${LINOG_PHASE6_CFG:-$A/linog_phase6.cfg}" | tail -1)
lst() { find "$@" -printf '%p %y %s %T@\n' 2>&1 | LC_ALL=C sort | md5sum | cut -c1-32; }
{
Q0=$(lst "$@")
bash "$A/lp_env.sh" python3 -B "$KIT/linog_verify_frame.py" "$@" > kit.txt 2>&1; rk=$?
bash "$A/lp_env.sh" python3 -B "$COPY" "$@" > copy.txt 2>&1; rc=$?
Q1=$(lst "$@")
grep -v '^        N22 modes from ' copy.txt > copy_less_n22src.txt
nd=$(diff kit.txt copy_less_n22src.txt | grep -c '^[<>]')
ns=$(grep -c '^        N22 modes from ' copy.txt)
echo "   kit $KIT/linog_verify_frame.py $(md5sum < "$KIT/linog_verify_frame.py" | cut -c1-32): rc $rk, $(wc -l < kit.txt) lines, md5 $(md5sum < kit.txt | cut -c1-32)"
echo "   copy $COPY $(md5sum < "$COPY" | cut -c1-32): rc $rc, $(wc -l < copy.txt) lines, md5 $(md5sum < copy.txt | cut -c1-32)"
echo "   the copy's N22 source lines: $ns of $#: $(grep '^        N22 modes from ' copy.txt | sed 's/^        N22 modes from //; s/ (.*//' | LC_ALL=C sort | uniq -c | tr -s ' ' | tr '\n' ';')"
echo "   lines that differ once the copy's source lines are left out: $nd"
diff kit.txt copy_less_n22src.txt | head -12 | sed 's/^/   | /'
paste -d '|' <(grep '^ == ' kit.txt) <(grep '^ == ' copy.txt) | sed 's/^ == /   kit: /; s/| == /  | copy: /'
echo "   the frames' listing $Q0 before, $Q1 after: $([ "$Q0" = "$Q1" ] && echo unchanged || echo CHANGED)"
if [ "$nd" -eq 0 ] && [ "$rk" = "$rc" ] && [ "$Q0" = "$Q1" ]; then
  echo "   D6: the copy prints the kit's lines on the $# frames"; ok=0
else
  echo "   D6: NOT the kit's lines (read the lines above)"; ok=1
fi
exit $ok
} | tee d6.txt
exit "${PIPESTATUS[0]}"
