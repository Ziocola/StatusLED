# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hidden_bleak = collect_submodules('bleak')
# WinRT per BLE su Windows
hidden_winrt = collect_submodules('winrt')

block_cipher = None

a = Analysis(
    ['StatusLED.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=hidden_bleak + hidden_winrt + ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,
    name='StatusLED',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # True se vuoi finestra console
    disable_windowed_traceback=False,
    target_arch=None,
    icon='StatusLED.ico'  # opzionale, se presente
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StatusLED'
)