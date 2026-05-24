# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Todo Manager GUI artifact."""

import sys
from pathlib import Path


_spec_dir = Path(SPECPATH)
_project_root = _spec_dir
_package_root = _spec_dir.parent
_icon_dir = _project_root / "assets" / "icons"
_windows_icon = _icon_dir / "todo-manager.ico"
_macos_icon = _icon_dir / "todo-manager.icns"
_exe_icon = _macos_icon if sys.platform == "darwin" else _windows_icon

a = Analysis(
    [str(_project_root / "gui" / "main.py")],
    pathex=[str(_package_root)],
    binaries=[],
    datas=[(str(_icon_dir), "assets/icons")],
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
        "todo_manager.cli.main",
        "todo_manager.gui",
        "todo_manager.gui.app",
        "todo_manager.gui.icon",
        "todo_manager.gui.main",
        "todo_manager.gui.react_shell",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    name="todo-gui",
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
    icon=str(_exe_icon),
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="TodoManager.app",
        icon=str(_macos_icon),
        bundle_identifier="com.local.todo-manager",
        info_plist={
            "CFBundleDisplayName": "Todo Manager",
            "CFBundleName": "Todo Manager",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
