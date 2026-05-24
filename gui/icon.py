"""Application icon helpers for Qt runtime and packaged builds."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget


APP_USER_MODEL_ID = "WorkBuddy.TodoManager"


def _bundle_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[1]


def app_icon_path() -> Path:
    return _bundle_root() / "assets" / "icons" / "todo-manager.png"


def app_icon() -> QIcon:
    return QIcon(str(app_icon_path()))


def set_windows_app_user_model_id() -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        return


def apply_app_icon(app: QApplication, window: QWidget | None = None) -> QIcon:
    set_windows_app_user_model_id()
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
        if window is not None:
            window.setWindowIcon(icon)
    return icon
