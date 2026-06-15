#!/usr/bin/env bash
# One-time / refresh environment setup for Observathon (Day 13 lab).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Observathon environment setup =="
echo "Project: $ROOT"
echo

# Directories
mkdir -p bin/practice bin/public bin/private logs traces

# Local env file (gitignored)
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[created] .env from .env.example"
else
  echo "[ok] .env exists"
fi

# Load env for this shell session
set -a
# shellcheck disable=SC1091
source .env
set +a

# Python (stdlib only for harness + telemetry)
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "[FAIL] python3 not found"; exit 1
fi
echo "[ok] $($PY --version)"

echo
echo "-- Self-check (no LLM key required) --"
"$PY" harness/selfcheck.py

echo
echo "-- LLM backend --"
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  echo "[ok] OPENAI_API_KEY is set (cloud mode ready)"
  echo "     config.json default: provider=openai, model=gpt-5.4-nano"
elif [[ -n "${LOCAL_BASE_URL:-}" ]]; then
  echo "[ok] LOCAL_BASE_URL=$LOCAL_BASE_URL"
  if curl -sf "${LOCAL_BASE_URL%/}/models" >/dev/null 2>&1; then
    echo "[ok] Local OpenAI-compatible endpoint responds"
    echo "     For local runs, set in solution/config.json:"
    echo '       "provider": "local", "model": "'"${LOCAL_MODEL:-phi3:latest}"'"'
    echo "     and export LOCAL_BASE_URL (already in .env)"
  else
    echo "[WARN] Local endpoint not reachable. Start Ollama: ollama serve"
    echo "       Or pull a model: ollama pull phi3"
  fi
else
  echo "[WARN] No OPENAI_API_KEY and no LOCAL_BASE_URL."
  echo "       Edit .env before running the simulator."
fi

echo
echo "-- Simulator binaries --"
missing=0
for phase in practice public private; do
  if compgen -G "bin/$phase/observathon-sim*" >/dev/null; then
    echo "[ok] bin/$phase/ has observathon-sim"
    if [[ "$(uname -s)" == "Darwin" ]]; then
      xattr -dr com.apple.quarantine "bin/$phase/"* 2>/dev/null || true
      chmod +x bin/$phase/observathon-sim* 2>/dev/null || true
    fi
  else
    echo "[TODO] bin/$phase/ — copy observathon-sim from instructor (see bin/README.md)"
    missing=1
  fi
done

echo
if [[ "$missing" -eq 0 ]]; then
  echo "Ready. Commands:"
  echo "  bash scripts/run_public.sh          # public test set -> run_output.json"
  echo "  bash scripts/run_score.sh public    # score (needs bin/public/observathon-score)"
  echo "  bash scripts/run_sim.sh ... --practice"
else
  echo "Almost ready — add binaries to bin/<phase>/ then: bash scripts/setup_env.sh"
  echo "Public can run now with practice sim: bash scripts/run_public.sh"
fi
