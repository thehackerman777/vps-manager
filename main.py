#!/usr/bin/env python3
"""Legacy entry-point — delegates to the refactored src package."""
import sys
import os

# Ensure the project root is on sys.path for the `python main.py` use case
_proj_root = os.path.dirname(os.path.abspath(__file__))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from src.main import main

if __name__ == "__main__":
    main()
