# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Todo Manager GUI artifact."""

import sys
import re
from pathlib import Path


_spec_dir = Path(SPECPATH)
_project_root = _spec_dir
_package_root = _spec_dir.parent
_icon_dir = _project_root / "assets" / "icons"
_windows_icon = _icon_dir / "todo-manager.ico"
_macos_icon = _icon_dir / "todo-manager.icns"
_exe_icon = _macos_icon if sys.platform == "darwin" else _windows_icon

QTWEBENGINE_ALLOWED_LOCALES = {"en-us", "zh-cn"}
_QTWEBENGINE_LOCALE_RE = re.compile(
    r"(?:^|[\\/])(?:qtwebengine_)?locales[\\/](?P<tag>[a-z]{2}(?:[-_][a-z]{2})?)\.pak$",
    re.IGNORECASE,
)
_PRUNED_QT_MARKERS = (
    "devtools",
    "qtwebengine_devtools",
    "qt3d",
    "qt6charts",
    "qtcharts",
    "qt6datavisualization",
    "qtdatavisualization",
    "qt6multimedia",
    "qtmultimedia",
    "qt6pdf",
    "qtpdf",
    "qt6quick3d",
    "qtquick3d",
)


def _toc_text(entry):
    return "/".join(
        str(part).replace("\\", "/").lower()
        for part in entry[:2]
        if isinstance(part, str)
    )


def _qtwebengine_locale_tag(text):
    match = _QTWEBENGINE_LOCALE_RE.search(text)
    if match is None:
        return None
    return match.group("tag").replace("_", "-").lower()


def _should_prune_toc_entry(entry):
    text = _toc_text(entry)
    locale = _qtwebengine_locale_tag(text)
    if locale is not None and locale not in QTWEBENGINE_ALLOWED_LOCALES:
        return True
    return any(marker in text for marker in _PRUNED_QT_MARKERS)

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
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQuick3D",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# M7.5 lightweight GUI policy. Keep QtWebEngine, QtWebChannel and Widgets, but
# prune debug/devtools resources, unused Qt add-on modules, and nonessential
# Chromium locale packs from the one-file GUI archive.
a.binaries = [entry for entry in a.binaries if not _should_prune_toc_entry(entry)]
a.datas = [entry for entry in a.datas if not _should_prune_toc_entry(entry)]
a.zipfiles = [entry for entry in a.zipfiles if not _should_prune_toc_entry(entry)]

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
