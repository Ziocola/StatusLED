# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# Raccogli i backend di Bleak (CoreBluetooth su macOS)
hidden_bleak = collect_submodules('bleak')

block_cipher = None

a = Analysis(
    ['StatusLED.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=hidden_bleak + ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
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
    exclude_binaries=True,
    name='StatusLED',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # cambia a True se vuoi la console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None  # opzionale, se presente
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

app = BUNDLE(
    coll,
    name='StatusLED.app',
    icon='StatusLED.icns',  # opzionale, se presente
    bundle_identifier='org.acolasanto.StatusLED',
    info_plist={
        'CFBundleName': 'StatusLED',
        'CFBundleDisplayName': 'StatusLED',
        'CFBundleIdentifier': 'org.acolasanto.StatusLED',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        # Permessi Bluetooth (evita prompt ripetuti/errore Bleak)
        'NSBluetoothAlwaysUsageDescription': 'StatusLED usa il Bluetooth per leggere e impostare lo stato del LED.',
    }
)
