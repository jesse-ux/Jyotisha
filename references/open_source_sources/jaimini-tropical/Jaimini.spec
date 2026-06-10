# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH)

a = Analysis(
    [str(PROJECT_ROOT / 'jaimini_web_launcher.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'jaimini' / 'data' / 'de421.bsp'), 'jaimini/data'),
        (str(PROJECT_ROOT / 'jaimini' / 'web' / 'templates'), 'jaimini/web/templates'),
        (str(PROJECT_ROOT / 'jaimini' / 'web' / 'static'), 'jaimini/web/static'),
    ],
    hiddenimports=[
        # Skyfield + numpy
        'skyfield',
        'skyfield.timelib',
        'skyfield.data',
        'numpy',
        # Jaimini engine
        'jaimini',
        'jaimini.engine',
        'jaimini.engine.ephemeris',
        'jaimini.engine.time_utils',
        'jaimini.engine.houses',
        # Jaimini core
        'jaimini.core',
        'jaimini.core.karakas',
        'jaimini.core.dashas',
        'jaimini.core.padas',
        'jaimini.core.lagnas',
        'jaimini.core.divisions',
        'jaimini.core.argala',
        # Jaimini panchanga (NEW)
        'jaimini.panchanga',
        'jaimini.panchanga.panchanga',
        # Jaimini chart
        'jaimini.chart',
        'jaimini.chart.chart',
        # Jaimini CLI
        'jaimini.cli',
        'jaimini.cli.main',
        # Jaimini web (NEW)
        'jaimini.web',
        'jaimini.web.app',
        # Web server dependencies
        'uvicorn',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.h11_impl',
        'fastapi',
        'starlette',
        'jinja2',
        'jinja2.ext',
        # AnyIO (uvicorn dependency)
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Jaimini',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
