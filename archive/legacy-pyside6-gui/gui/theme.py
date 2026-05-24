"""Theme tokens for the M4 prototype driven PySide6 GUI."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LightColors:
    BG_ROOT = "#F7F9FF"
    BG_ROOT_GRADIENT = (
        "qlineargradient(x1:0,y1:0,x2:1,y2:1, "
        "stop:0 #DFF4FF, stop:0.46 #DFF8EC, stop:1 #EEF2F5)"
    )
    BG_SOFT = "rgba(255,255,255,0.68)"
    BG_SURFACE = "rgba(255,255,255,0.84)"
    BG_SURFACE_STRONG = "#FFFFFF"
    BG_SURFACE_ALT = "rgba(255,255,255,0.56)"
    BG_BUTTON = "rgba(255,255,255,0.62)"
    BG_BUTTON_HOVER = "#FFFFFF"
    BG_INPUT = "rgba(255,255,255,0.74)"
    BG_DAY = "rgba(255,255,255,0.48)"
    BG_DAY_HOVER = "rgba(255,255,255,0.76)"
    BG_HOVER = "#E8F4FF"
    BG_ACTIVE = "#FFFFFF"
    BG_TODAY = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(232,244,255,0.88), stop:1 rgba(232,248,240,0.88))"
    BG_MODAL = "rgba(255,255,255,0.94)"
    BG_OVERLAY = "rgba(21,43,58,0.24)"
    BG_TOAST = "#17344A"
    BG_SUBTASK = "rgba(255,255,255,0.54)"
    BG_DROPDOWN = "#FFFFFF"

    TEXT_PRIMARY = "#123047"
    TEXT_SECONDARY = "#4F6578"
    TEXT_TERTIARY = "#6A7D8E"
    TEXT_ON_LIGHT = "#123047"
    TEXT_MUTED_ON_LIGHT = "#4F6578"
    TEXT_SOFT_ON_LIGHT = "#6A7D8E"
    TEXT_INVERSE = "#FFFFFF"
    TEXT_LINK = "#2E8DF5"

    BORDER = "rgba(98,132,154,0.18)"
    BORDER_LIGHT = "rgba(98,132,154,0.12)"
    BORDER_STRONG = "rgba(73,121,151,0.34)"
    BORDER_FOCUS = "#2E8DF5"

    BLUE = "#2E8DF5"
    BLUE_SOFT = "#E8F4FF"
    GREEN = "#23B883"
    GREEN_SOFT = "#E8F8F0"
    SILVER = "#EEF3F6"
    AMBER = "#D69B18"
    AMBER_SOFT = "#FFF5D9"
    DANGER = "#E05858"
    DANGER_SOFT = "#FFF0F0"

    COLOR_PENDING = "#98A8B6"
    COLOR_PENDING_BG = SILVER
    COLOR_ACTIVE = BLUE
    COLOR_ACTIVE_BG = BLUE_SOFT
    COLOR_DONE = GREEN
    COLOR_DONE_BG = GREEN_SOFT
    COLOR_CANCELLED = "#AEB8C2"
    COLOR_CANCELLED_BG = "#EDF1F4"

    COLOR_PENDING_SUB = "#98A8B6"
    COLOR_PENDING_SUB_BG = "rgba(255,255,255,0.54)"
    COLOR_ACTIVE_SUB = BLUE
    COLOR_ACTIVE_SUB_BG = BLUE_SOFT
    COLOR_DONE_SUB = GREEN
    COLOR_DONE_SUB_BG = GREEN_SOFT
    COLOR_CANCELLED_SUB = "#AEB8C2"
    COLOR_CANCELLED_SUB_BG = "#EDF1F4"

    COLOR_DANGER = DANGER
    COLOR_DANGER_HOVER = "#C94646"
    COLOR_DANGER_BG = DANGER_SOFT
    COLOR_PRIMARY_BTN = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2E8DF5, stop:1 #23B883)"
    COLOR_PRIMARY_BTN_HOVER = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1F7FEA, stop:1 #16A978)"

    SCROLLBAR_THUMB = "#CBD5E1"
    SCROLLBAR_TRACK = "transparent"


class DarkColors:
    BG_ROOT = "#07131D"
    BG_ROOT_GRADIENT = (
        "qlineargradient(x1:0,y1:0,x2:1,y2:1, "
        "stop:0 #07131D, stop:0.46 #0E2230, stop:1 #142A38)"
    )
    BG_SOFT = "rgba(18,35,48,0.86)"
    BG_SURFACE = "rgba(18,35,48,0.92)"
    BG_SURFACE_STRONG = "#122330"
    BG_SURFACE_ALT = "rgba(26,47,62,0.82)"
    BG_BUTTON = "rgba(26,47,62,0.82)"
    BG_BUTTON_HOVER = "rgba(34,62,82,0.96)"
    BG_INPUT = "rgba(10,26,38,0.92)"
    BG_DAY = "rgba(26,47,62,0.62)"
    BG_DAY_HOVER = "rgba(34,62,82,0.92)"
    BG_HOVER = "#16344F"
    BG_ACTIVE = "#122330"
    BG_TODAY = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #16344F, stop:1 #123D32)"
    BG_MODAL = "#122330"
    BG_OVERLAY = "rgba(0,0,0,0.65)"
    BG_TOAST = "#F1F5F9"
    BG_SUBTASK = "rgba(26,47,62,0.70)"
    BG_DROPDOWN = "#122330"

    TEXT_PRIMARY = "#E8F3F8"
    TEXT_SECONDARY = "#B2C3CE"
    TEXT_TERTIARY = "#94A8B7"
    TEXT_ON_LIGHT = "#E8F3F8"
    TEXT_MUTED_ON_LIGHT = "#94A8B7"
    TEXT_SOFT_ON_LIGHT = "#94A8B7"
    TEXT_INVERSE = "#0F172A"
    TEXT_LINK = "#65B5FF"

    BORDER = "rgba(146,180,198,0.20)"
    BORDER_LIGHT = "rgba(146,180,198,0.12)"
    BORDER_STRONG = "rgba(146,180,198,0.38)"
    BORDER_FOCUS = "#65B5FF"

    BLUE = "#65B5FF"
    BLUE_SOFT = "#16344F"
    GREEN = "#4DD7A1"
    GREEN_SOFT = "#123D32"
    SILVER = "#23303B"
    AMBER = "#FFD166"
    AMBER_SOFT = "#42351A"
    DANGER = "#FF7A7A"
    DANGER_SOFT = "#431A1D"

    COLOR_PENDING = "#8EA0AD"
    COLOR_PENDING_BG = SILVER
    COLOR_ACTIVE = BLUE
    COLOR_ACTIVE_BG = BLUE_SOFT
    COLOR_DONE = GREEN
    COLOR_DONE_BG = GREEN_SOFT
    COLOR_CANCELLED = "#7E909C"
    COLOR_CANCELLED_BG = "#22303A"

    COLOR_PENDING_SUB = "#8EA0AD"
    COLOR_PENDING_SUB_BG = "rgba(26,47,62,0.70)"
    COLOR_ACTIVE_SUB = BLUE
    COLOR_ACTIVE_SUB_BG = BLUE_SOFT
    COLOR_DONE_SUB = GREEN
    COLOR_DONE_SUB_BG = GREEN_SOFT
    COLOR_CANCELLED_SUB = "#7E909C"
    COLOR_CANCELLED_SUB_BG = "#22303A"

    COLOR_DANGER = DANGER
    COLOR_DANGER_HOVER = "#F15F5F"
    COLOR_DANGER_BG = DANGER_SOFT
    COLOR_PRIMARY_BTN = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #65B5FF, stop:1 #4DD7A1)"
    COLOR_PRIMARY_BTN_HOVER = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4EA4F4, stop:1 #36C58D)"

    SCROLLBAR_THUMB = "#475569"
    SCROLLBAR_TRACK = "transparent"


FONT_FAMILY = "Microsoft YaHei"
FONT_FAMILY_FALLBACK = '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",system-ui,-apple-system,sans-serif'
FONT_MONO = "Consolas"

FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_BASE = 14
FONT_SIZE_LG = 16
FONT_SIZE_XL = 21

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 8
RADIUS_XL = 8

APP_MARGIN = 18
APP_GAP = 14
PANEL_HEAD_HEIGHT = 62
APP_MAX_WIDTH = 1440
TOPBAR_BRAND_WIDTH = 240
RAIL_WIDTH = 260
DETAIL_WIDTH = 340

STATUS_EN_MAP = {
    "未启动": "pending",
    "完成中": "active",
    "已完成": "done",
    "已取消": "cancelled",
}


def get_status_colors(status: str, theme_colors, is_sub: bool = False) -> tuple[str, str]:
    status_en = STATUS_EN_MAP.get(status, "pending")
    if is_sub:
        border_attr = f"COLOR_{status_en.upper()}_SUB"
        bg_attr = f"COLOR_{status_en.upper()}_SUB_BG"
    else:
        border_attr = f"COLOR_{status_en.upper()}"
        bg_attr = f"COLOR_{status_en.upper()}_BG"
    return getattr(theme_colors, border_attr, "#98A8B6"), getattr(theme_colors, bg_attr, "#EEF3F6")


def status_class(status: str) -> str:
    return STATUS_EN_MAP.get(status, "pending")


def qcolor(color: str) -> QColor:
    if color.startswith("rgba"):
        parts = color.replace("rgba(", "").replace(")", "").split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        alpha = float(parts[3]) if len(parts) > 3 else 1
        return QColor(r, g, b, int(alpha * 255))
    return QColor(color)


def font_px(size_px: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont(FONT_FAMILY)
    font.setPixelSize(size_px)
    font.setWeight(weight)
    return font


def detect_system_theme() -> Theme:
    app = QApplication.instance()
    if app is None:
        return Theme.LIGHT
    window_color = app.palette().color(QPalette.ColorRole.Window)
    return Theme.DARK if window_color.lightness() < 128 else Theme.LIGHT


def resolve_theme(theme: Theme) -> Theme:
    return detect_system_theme() if theme == Theme.SYSTEM else theme


def colors_for_theme(theme: Theme):
    return DarkColors if resolve_theme(theme) == Theme.DARK else LightColors


class ThemeSettings:
    KEY = "appearance/theme"

    def __init__(self, settings_path: str | Path | None = None):
        if settings_path is None:
            self._settings = QSettings("WorkBuddy", "TodoManager")
        else:
            self._settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

    def load_theme(self) -> Theme:
        raw = self._settings.value(self.KEY, Theme.SYSTEM.value)
        try:
            return Theme(str(raw))
        except ValueError:
            return Theme.SYSTEM

    def save_theme(self, theme: Theme) -> None:
        self._settings.setValue(self.KEY, theme.value)
        self._settings.sync()
