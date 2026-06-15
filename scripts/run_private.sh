#!/usr/bin/env bash
# Private phase: use the official private simulator and its embedded test set.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f bin/private/observathon-sim ]]; then
  echo "[FAIL] Missing bin/private/observathon-sim" >&2
  exit 1
fi

echo "== Private sim =="
python3 harness/selfcheck.py
bash "$ROOT/scripts/run_phase.sh" private \
  --config solution/config.json \
  --wrapper solution/wrapper.py \
  --out run_output.json \
  "$@"

echo
echo "Done -> run_output.json"
echo "Score: bash scripts/run_score.sh private"
