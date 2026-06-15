#!/usr/bin/env bash
# Backward-compatible alias for practice runs.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run_phase.sh" practice "$@"
