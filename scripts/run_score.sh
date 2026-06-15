#!/usr/bin/env bash
# Score a run (public or private phase).
# Usage: bash scripts/run_score.sh [public|private]
# Optional: ANSWERKEY=path/to/key.json for harness/local runs (official sim embeds its own key).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PHASE="${1:-public}"
TEAM="${TEAM:-2A202600713-DangMinhHai}"
BIN="bin/$PHASE/observathon-score"
EXTRA=()

if [[ ! -f run_output.json ]]; then
  echo "[FAIL] run_output.json not found — run public sim first." >&2
  exit 1
fi

if [[ -f .env ]]; then set -a; source .env; set +a; fi

if [[ ! -f "$BIN" ]]; then
  echo "[FAIL] Missing $BIN — download observathon-score for phase $PHASE from instructor." >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  xattr -dr com.apple.quarantine "$BIN" 2>/dev/null || true
  chmod +x "$BIN"
fi

if [[ -n "${ANSWERKEY:-}" ]]; then
  EXTRA+=(--answerkey "$ANSWERKEY")
elif [[ -f harness/public_answerkey.json ]] && grep -q '"qid": "pub-[0-9][0-9]"' run_output.json 2>/dev/null; then
  echo "[warn] Harness qids detected (pub-01). Using harness/public_answerkey.json."
  echo "       For official leaderboard score, run bin/$PHASE/observathon-sim first."
  EXTRA+=(--answerkey harness/public_answerkey.json)
fi

exec "$BIN" \
  --run run_output.json \
  --findings solution/findings.json \
  --team "$TEAM" \
  --out score.json \
  "${EXTRA[@]}"
