#!/usr/bin/env python3
"""Jaimini Tropical Astrology Engine — Web Launcher (PyInstaller entry point)."""

import sys
import os
import socket
import webbrowser
import threading

# PyInstaller sets sys._MEIPASS to the temp extraction directory
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    exe_dir = os.path.dirname(sys.executable)
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

    # Windowed EXE has no console: redirect stdio to devnull
    # otherwise uvicorn logging crashes with AttributeError on stderr.isatty()
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')


def find_free_port(start=8000, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def main():
    import uvicorn

    port = find_free_port(8000, 8100)
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    def open_browser():
        import time
        time.sleep(2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    # Use a log config that doesn't call isatty()
    uvicorn.run(
        "jaimini.web.app:app",
        host=host,
        port=port,
        log_level="warning",
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(levelprefix)s %(message)s",
                    "use_colors": False,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "WARNING"},
                "uvicorn.error": {"level": "WARNING"},
                "uvicorn.access": {"handlers": ["default"], "level": "WARNING"},
            },
        },
    )


if __name__ == "__main__":
    main()
