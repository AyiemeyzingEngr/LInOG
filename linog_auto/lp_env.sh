#!/usr/bin/env bash
# lp_env.sh CMD [ARG...] -- run CMD in a clean ISCE environment (linog_auto v0.2).
# env -i; conda.sh and `conda activate` as linog_env.cfg says; then the PYTHONPATH the operator's shell carries
# (RD2, 26 Sept 2026: <isce>/components, <env>/share/isce2, <isce>). The activation alone sets none of it.
# LINOG_* variables pass through; nothing else does. CMD's exit code is returned; 3 if the env cannot be made.
A=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
E=${LINOG_ENV_CFG:-$A/linog_env.cfg}
[ -f "$E" ] || { echo "lp_env.sh: no $E" >&2; exit 3; }
. "$E"
[ -f "${CONDA_SH:-}" ] || { echo "lp_env.sh: no conda.sh at ${CONDA_SH:-?}" >&2; exit 3; }
mapfile -t L < <(env | grep -E '^LINOG_[A-Za-z0-9_]+=')
exec env -i HOME="$HOME" USER="${USER:-$(id -un)}" LANG=C.UTF-8 PATH=/usr/bin:/bin "${L[@]}" \
  LP_CONDA_SH="$CONDA_SH" LP_CONDA_ENV="$CONDA_ENV" bash --noprofile --norc -c '
. "$LP_CONDA_SH" && conda activate "$LP_CONDA_ENV" || { echo "lp_env.sh: conda activate $LP_CONDA_ENV failed" >&2; exit 3; }
I=${ISCE_HOME:-$(python3 -c "import isce, os; print(os.path.dirname(isce.__file__))" 2>/dev/null | tail -1)}
[ -d "$I/components" ] || { echo "lp_env.sh: no ISCE components under ${I:-?} in $LP_CONDA_ENV" >&2; exit 3; }
export PYTHONPATH="$I/components:$CONDA_PREFIX/share/isce2:$I"
exec "$@"' lp_env "$@"
