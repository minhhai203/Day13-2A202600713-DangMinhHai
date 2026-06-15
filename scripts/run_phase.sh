#!/usr/bin/env bash
# Run observathon-sim for a phase via Python 3.12 extracted runtime.
# Usage: bash scripts/run_phase.sh <practice|public|private> [extra sim args...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PHASE="${1:?phase required: practice|public|private}"
shift

PY="${PY:-$HOME/.pyenv/versions/3.12.10/bin/python3}"
RUNTIME="$ROOT/.runtime/observathon-$PHASE"
if [[ "$PHASE" == "practice" && ! -d "$RUNTIME" && -d "$ROOT/.runtime/observathon-sim" ]]; then
  RUNTIME="$ROOT/.runtime/observathon-sim"
fi
SIM_MAIN="$RUNTIME/sim_main.pyc"
PYZ="$RUNTIME/PYZ.pyz_extracted"
BIN="bin/$PHASE/observathon-sim"
EXTRA=()

if [[ ! -f "$SIM_MAIN" ]]; then
  if [[ -f "$BIN" ]]; then
    echo "[info] Extracting runtime from $BIN ..."
    bash "$ROOT/scripts/extract_runtime.sh" "$PHASE" sim
    RUNTIME="$ROOT/.runtime/observathon-$PHASE"
    SIM_MAIN="$RUNTIME/sim_main.pyc"
    PYZ="$RUNTIME/PYZ.pyz_extracted"
  elif [[ "$PHASE" != "practice" ]]; then
    echo "[WARN] No bin/$PHASE/observathon-sim — using practice runtime + --testset $PHASE"
    RUNTIME="$ROOT/.runtime/observathon-sim"
    if [[ ! -d "$RUNTIME" ]]; then
      bash "$ROOT/scripts/extract_runtime.sh" practice sim
      RUNTIME="$ROOT/.runtime/observathon-practice"
      [[ -d "$RUNTIME" ]] || RUNTIME="$ROOT/.runtime/observathon-sim"
    fi
    SIM_MAIN="$RUNTIME/sim_main.pyc"
    PYZ="$RUNTIME/PYZ.pyz_extracted"
    EXTRA=(--testset "$PHASE")
  else
    echo "[FAIL] Missing $BIN and runtime under .runtime/" >&2
    exit 1
  fi
fi

if [[ ! -x "$PY" ]] && ! command -v "$PY" >/dev/null 2>&1; then
  echo "[FAIL] Python 3.12.10 not found at $PY" >&2
  exit 1
fi

if [[ -f .env ]]; then set -a; source .env; set +a; fi

export PYTHONPATH="$PYZ${PYTHONPATH:+:$PYTHONPATH}"
if [[ ${#EXTRA[@]} -gt 0 ]]; then
  exec "$PY" "$SIM_MAIN" "${EXTRA[@]}" "$@"
else
  exec "$PY" "$SIM_MAIN" "$@"
fi
