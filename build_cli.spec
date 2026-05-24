# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Todo Manager CLI artifact."""

from pathlib import Path


_spec_dir = Path(SPECPATH)
_project_root = _spec_dir
_package_root = _spec_dir.parent

a = Analysis(
    [str(_project_root / "cli" / "__main__.py")],
    pathex=[str(_package_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "todo_manager.engine",
        "todo_manager.engine.models",
        "todo_manager.engine.task_manager",
        "todo_manager.engine.storage",
        "todo_manager.engine.platform_paths",
        "todo_manager.engine.calendar_utils",
        "todo_manager.cli",
        "todo_manager.cli.commands",
        "todo_manager.cli.contract",
        "todo_manager.cli.display",
        "todo_manager.cli.main",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6",
        "PySide6.QtWidgets",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "shiboken6",
        "pytest",
        "unittest",
        "tkinter",
        "matplotlib",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="todo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
