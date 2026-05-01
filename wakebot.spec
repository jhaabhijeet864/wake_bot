# -*- mode: python ; coding: utf-8 -*-
"""
WakeBot PyInstaller Spec File
Builds a standalone WakeBot.exe for Windows distribution.

Usage:
    pyinstaller wakebot.spec

Notes:
    - The Vosk model directory is NOT bundled (too large, ~40MB+).
      Users must download it separately.
    - wakebot_config.json is included as a data file.
    - Requires all dependencies from requirements.txt to be installed.
"""

import os

block_cipher = None

# Project root
ROOT = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(ROOT, 'wakebot', '__main__.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Include config template
        (os.path.join(ROOT, 'wakebot_config.json'), '.'),
        (os.path.join(ROOT, '.env.example'), '.'),
    ],
    hiddenimports=[
        'wakebot',
        'wakebot.core',
        'wakebot.core.actions',
        'wakebot.core.config',
        'wakebot.core.credentials',
        'wakebot.core.dashboard',
        'wakebot.core.detector',
        'wakebot.core.hardware_monitor',
        'wakebot.core.logger',
        'wakebot.core.startup',
        'wakebot.core.tray',
        'wakebot.core.workspace_state',
        'wakebot.cli',
        'wakebot.cli.main',
        'wakebot.cli.audio_cmd',
        'wakebot.cli.vision_cmd',
        'wakebot.cli.calibrate_cmd',
        'wakebot.triggers',
        'wakebot.triggers.audio',
        'wakebot.triggers.audio.engine',
        'wakebot.triggers.audio.detector',
        'wakebot.triggers.audio.voice',
        'wakebot.triggers.vision',
        'wakebot.triggers.vision.engine',
        'wakebot.triggers.vision.detector',
        'wakebot.triggers.vision.presence',
        'wakebot.triggers.vision.screen',
        'wakebot.triggers.vision.multimodal',
        # Third-party hidden imports
        'pystray._win32',
        'keyring.backends',
        'keyring.backends.Windows',
        'PIL',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WakeBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (tray mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add a proper .ico file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WakeBot',
)
