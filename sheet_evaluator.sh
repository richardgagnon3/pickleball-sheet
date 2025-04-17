#!/usr/bin/bash

PROJECT_DIR="$(dirname "$0")" # this script's directory name

PYTHONPATH="$PROJECT_DIR/src"

python3 "$PROJECT_DIR/src/sheet_evaluator.py" "$@"
