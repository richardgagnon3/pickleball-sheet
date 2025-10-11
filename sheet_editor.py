#!/usr/bin/env python3
"""
Main application launcher for the Pickleball Sheet Editor

This script launches the GUI application for editing pickleball game sheets.
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sheet_editor_gui import main

if __name__ == "__main__":
    main()