#!/usr/bin/bash
# Generate many random games sheets and keep the fairest ones.
# Usage: ./sheet_generator.sh -p 6 -c 1 -g 9 [-n 5000] [-k 5] [-s SEED] [-o games/generated]

PROJECT_DIR="$(dirname "$0")" # this script's directory name

PYTHONPATH="$PROJECT_DIR/src" python3 "$PROJECT_DIR/src/sheet_generator.py" "$@"
