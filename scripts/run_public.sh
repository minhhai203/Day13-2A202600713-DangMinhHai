#!/usr/bin/env bash
# Public phase: run simulator on the public test set.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Public sim =="
python3 harness/selfcheck.py
bash "$ROOT/scripts/run_phase.sh" public \
  --config solution/config.json \
  --wrapper solution/wrapper.py \
  --questions harness/public_questions.json \
  --out run_output.json \
  "$@"

echo
echo "Done -> run_output.json"
echo "Score: bash scripts/run_score.sh public"
