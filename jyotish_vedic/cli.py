#!/usr/bin/env python3
"""
Jyotish CLI entry point.
Usage: jyotish <command> [args]
"""
import sys
import os

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def main():
    """Delegate to jyotish_engine.py CLI."""
    engine = os.path.join(SCRIPT_DIR, "jyotish_engine.py")
    if not os.path.exists(engine):
        print(f"Error: Engine not found at {engine}", file=sys.stderr)
        sys.exit(1)
    
    # Pass all args after 'jyotish' to the engine
    cmd = [sys.executable, engine] + sys.argv[1:]
    os.execv(sys.executable, cmd)


if __name__ == "__main__":
    main()
