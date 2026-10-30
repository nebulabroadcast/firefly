# -*- mode: python ; coding: utf-8 -*-
# Cross-platform PyInstaller spec (Windows and Linux): `make build`
#
# skin.css, images/ and fonts/ are read from the working directory at runtime,
# so they are copied next to the executable (see Makefile) rather than bundled.

import os

block_cipher = None


a = Analysis(
    [os.path.join("firefly", "__main__.py")],
    pathex=[SPECPATH],
    binaries=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    datas=[],
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
    name='firefly',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join("images", "firefly.ico")],
)
