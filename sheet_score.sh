#!/usr/bin/bash
# Rank one or more games sheets by fairness score (lower is better).
# Usage: ./sheet_score.sh [-v] games/*.csv

PROJECT_DIR="$(dirname "$0")" # this script's directory name

PYTHONPATH="$PROJECT_DIR/src" python3 "$PROJECT_DIR/src/sheet_score.py" "$@"
