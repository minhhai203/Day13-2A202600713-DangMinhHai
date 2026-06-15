#!/usr/bin/env bash
# Install observathon binary zip from instructor.
# Usage: bash scripts/install_binary.sh observathon-public-macos-arm64.zip public
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ZIP="${1:?path to zip file}"
PHASE="${2:?phase: practice|public|private}"

if [[ ! -f "$ZIP" ]]; then
  echo "[FAIL] Zip not found: $ZIP" >&2
  exit 1
fi

mkdir -p "bin/$PHASE"
unzip -o "$ZIP" -d "bin/$PHASE/"
chmod +x bin/$PHASE/observathon-* 2>/dev/null || true
if [[ "$(uname -s)" == "Darwin" ]]; then
  xattr -dr com.apple.quarantine "bin/$PHASE/"* 2>/dev/null || true
fi

echo "[ok] Installed to bin/$PHASE/:"
ls -la "bin/$PHASE/"

echo "[info] Extracting Python 3.12 runtime..."
if compgen -G "bin/$PHASE/observathon-sim*" >/dev/null; then
  bash "$ROOT/scripts/extract_runtime.sh" "$PHASE" sim
fi
if compgen -G "bin/$PHASE/observathon-score*" >/dev/null; then
  bash "$ROOT/scripts/extract_runtime.sh" "$PHASE" score
fi

echo
echo "Run: bash scripts/run_public.sh"
echo "Score: bash scripts/run_score.sh public"
