# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts/gui_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=['qkdn_sim', 'qkdn_sim.qkdn_sim'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PQC-QKD Suite GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PQC-QKD Suite GUI',
)
app = BUNDLE(
    coll,
    name='PQC-QKD Suite GUI.app',
    icon=None,
    bundle_identifier=None,
)
