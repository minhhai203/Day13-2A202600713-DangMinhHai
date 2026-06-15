#!/usr/bin/env bash
# Extract PyInstaller binary -> .runtime/ for Python 3.12 execution.
# Usage: bash scripts/extract_runtime.sh [practice|public|private] [sim|score]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PHASE="${1:-practice}"
TOOL="${2:-sim}"
PY="${PY:-$HOME/.pyenv/versions/3.12.10/bin/python3}"

if [[ "$TOOL" == "sim" ]]; then
  BIN="bin/$PHASE/observathon-sim"
  RUNTIME="$ROOT/.runtime/observathon-$PHASE"
else
  BIN="bin/$PHASE/observathon-score"
  RUNTIME="$ROOT/.runtime/observathon-score-$PHASE"
fi

if [[ ! -f "$BIN" ]]; then
  echo "[FAIL] Missing $BIN" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  xattr -dr com.apple.quarantine "$BIN" 2>/dev/null || true
  chmod +x "$BIN"
fi

if [[ ! -x "$PY" ]]; then
  echo "[FAIL] Python 3.12.10 not found at $PY (pyenv install 3.12.10)" >&2
  exit 1
fi

EXTRACTOR="/tmp/pyinstxtractor.py"
if [[ ! -f "$EXTRACTOR" ]]; then
  curl -sL https://raw.githubusercontent.com/extremecoders-re/pyinstxtractor/master/pyinstxtractor.py -o "$EXTRACTOR"
fi

rm -rf "$RUNTIME"
mkdir -p "$ROOT/.runtime"
"$PY" "$EXTRACTOR" "$BIN" >/dev/null

BASE="$(basename "$BIN")"
EXTRACTED="$(dirname "$BIN")/${BASE}_extracted"
if [[ ! -d "$EXTRACTED" ]]; then
  EXTRACTED="$ROOT/${BASE}_extracted"
fi
if [[ ! -d "$EXTRACTED" ]]; then
  EXTRACTED="$(find "$ROOT" -maxdepth 2 -type d -name '*extracted' | head -1)"
fi
if [[ ! -d "$EXTRACTED" ]]; then
  echo "[FAIL] Could not locate extracted runtime for $BIN" >&2
  exit 1
fi

mv "$EXTRACTED" "$RUNTIME"
echo "[ok] Extracted $BIN -> $RUNTIME"
