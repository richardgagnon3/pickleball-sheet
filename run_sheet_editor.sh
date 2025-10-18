#!/bin/bash
# Script to run the Pickleball Sheet Editor with the virtual environment activated

# Navigate to the project directory
cd "$(dirname "$0")" || exit 1

# Activate the virtual environment and run the application
./.venv/bin/python src/sheet_editor.py