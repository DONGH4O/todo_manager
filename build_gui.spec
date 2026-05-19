# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — GUI 入口 todo-gui.exe

用法: pyinstaller build_gui.spec
"""

import sys
from pathlib import Path

# SPECPATH 由 PyInstaller 自动设置为 spec 文件所在目录
_spec_dir = Path(SPECPATH)
_project_root = _spec_dir
_package_root = _spec_dir.parent

a = Analysis(
    [str(_project_root / 'gui' / 'main.py')],
    pathex=[str(_package_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'todo_manager.engine',
        'todo_manager.engine.models',
        'todo_manager.engine.task_manager',
        'todo_manager.engine.storage',
        'todo_manager.engine.platform_paths',
        'todo_manager.engine.calendar_utils',
        'todo_manager.gui',
        'todo_manager.gui.app',
        'todo_manager.gui.theme',
        'todo_manager.gui.widgets',
        'todo_manager.gui.widgets.task_bar',
        'todo_manager.gui.widgets.calendar_cell',
        'todo_manager.gui.widgets.calendar_grid',
        'todo_manager.gui.widgets.detail_panel',
        'todo_manager.gui.widgets.dialogs',
        'todo_manager.gui.widgets.search_bar',
        'todo_manager.gui.widgets.month_nav',
        'todo_manager.gui.widgets.theme_toggle',
        # Qt 插件隐式导入
        'PySide6.QtPrintSupport',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'unittest',
        'tkinter',
        'matplotlib',
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
    name='todo-gui',
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
