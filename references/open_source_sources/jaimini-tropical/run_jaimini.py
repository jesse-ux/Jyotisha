#!/usr/bin/env python3
"""Jaimini Tropical Astrology Engine — convenient entry point.

Usage:
    python run_jaimini.py "1949-10-01" "15:00:00" "+8" "39.907" "116.397"
    python run_jaimini.py "1949-10-01" "15:00:00" "+8" "39°54′25″" "116°23′50″" --name "My Chart"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jaimini.cli.main import main

if __name__ == '__main__':
    main()
