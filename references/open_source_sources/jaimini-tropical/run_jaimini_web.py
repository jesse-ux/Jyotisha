#!/usr/bin/env python3
"""Jaimini Tropical Astrology Engine — Web Server.

Usage:
    python run_jaimini_web.py
    # Opens browser at http://127.0.0.1:8000
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jaimini.web.app import run

if __name__ == "__main__":
    run()
