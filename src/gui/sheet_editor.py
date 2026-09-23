#!/usr/bin/env python3
"""
Main application launcher for the Pickleball Sheet Editor

This script launches the GUI application for editing pickleball game sheets.
"""

import os
import sys

# Make the top-level src/ modules (sheet_reader, games_table, player, etc.)
# importable when this script is run directly from src/gui/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sheet_editor_gui import main

if __name__ == "__main__":
    main()
