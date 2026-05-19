"""主题管理：明/暗双主题的颜色、字体、样式常量。

所有颜色值基于原型 HTML 的 CSS 变量设计。
"""

from enum import Enum
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"


# ── 基础颜色（与 prototype.html CSS 变量一致） ─────────────

class LightColors:
    """明色主题色板"""
    BG_ROOT = "#F1F5F9"
    BG_SURFACE = "#FFFFFF"
    BG_SURFACE_ALT = "#F8FAFC"
    BG_HOVER = "#F1F5F9"
    BG_ACTIVE = "#E2E8F0"
    BG_TODAY = "#EFF6FF"
    BG_TODAY_HOVER = "#DBEAFE"
    BG_MODAL = "#FFFFFF"
    BG_OVERLAY = "rgba(15,23,42,0.45)"
    BG_TOAST = "#1E293B"
    BG_SUBTASK = "#F8FAFC"
    BG_INPUT = "#FFFFFF"
    BG_DROPDOWN = "#FFFFFF"

    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_TERTIARY = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"
    TEXT_LINK = "#2563EB"

    BORDER = "#E2E8F0"
    BORDER_LIGHT = "#F1F5F9"
    BORDER_FOCUS = "#3B82F6"

    # 状态颜色（主任务）
    COLOR_PENDING = "#9CA3AF"
    COLOR_PENDING_BG = "#F3F4F6"
    COLOR_ACTIVE = "#3B82F6"
    COLOR_ACTIVE_BG = "#EFF6FF"
    COLOR_DONE = "#10B981"
    COLOR_DONE_BG = "#ECFDF5"
    COLOR_CANCELLED = "#9CA3AF"
    COLOR_CANCELLED_BG = "#F3F4F6"

    # 状态颜色（子任务）
    COLOR_PENDING_SUB = "#D1D5DB"
    COLOR_PENDING_SUB_BG = "#F9FAFB"
    COLOR_ACTIVE_SUB = "#93C5FD"
    COLOR_ACTIVE_SUB_BG = "#F0F7FF"
    COLOR_DONE_SUB = "#6EE7B7"
    COLOR_DONE_SUB_BG = "#F0FDF6"
    COLOR_CANCELLED_SUB = "#D1D5DB"
    COLOR_CANCELLED_SUB_BG = "#F9FAFB"

    COLOR_DANGER = "#EF4444"
    COLOR_DANGER_HOVER = "#DC2626"
    COLOR_DANGER_BG = "#FEF2F2"

    COLOR_PRIMARY_BTN = "#3B82F6"
    COLOR_PRIMARY_BTN_HOVER = "#2563EB"

    SCROLLBAR_THUMB = "#CBD5E1"
    SCROLLBAR_TRACK = "transparent"


class DarkColors:
    """暗色主题色板"""
    BG_ROOT = "#0B1120"
    BG_SURFACE = "#1E293B"
    BG_SURFACE_ALT = "#172033"
    BG_HOVER = "#273548"
    BG_ACTIVE = "#334155"
    BG_TODAY = "#1E3A5F"
    BG_TODAY_HOVER = "#254574"
    BG_MODAL = "#1E293B"
    BG_OVERLAY = "rgba(0,0,0,0.65)"
    BG_TOAST = "#F1F5F9"
    BG_SUBTASK = "#1A2744"
    BG_INPUT = "#0F172A"
    BG_DROPDOWN = "#1E293B"

    TEXT_PRIMARY = "#F1F5F9"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_TERTIARY = "#64748B"
    TEXT_INVERSE = "#0F172A"
    TEXT_LINK = "#60A5FA"

    BORDER = "#334155"
    BORDER_LIGHT = "#1E293B"
    BORDER_FOCUS = "#60A5FA"

    COLOR_PENDING = "#6B7280"
    COLOR_PENDING_BG = "#1F2937"
    COLOR_ACTIVE = "#3B82F6"
    COLOR_ACTIVE_BG = "#1E3A5F"
    COLOR_DONE = "#34D399"
    COLOR_DONE_BG = "#064E3B"
    COLOR_CANCELLED = "#6B7280"
    COLOR_CANCELLED_BG = "#1F2937"

    COLOR_PENDING_SUB = "#4B5563"
    COLOR_PENDING_SUB_BG = "#1A2332"
    COLOR_ACTIVE_SUB = "#1D4ED8"
    COLOR_ACTIVE_SUB_BG = "#1A3050"
    COLOR_DONE_SUB = "#059669"
    COLOR_DONE_SUB_BG = "#053B2E"
    COLOR_CANCELLED_SUB = "#4B5563"
    COLOR_CANCELLED_SUB_BG = "#1A2332"

    COLOR_DANGER = "#F87171"
    COLOR_DANGER_HOVER = "#EF4444"
    COLOR_DANGER_BG = "#450A0A"

    COLOR_PRIMARY_BTN = "#60A5FA"
    COLOR_PRIMARY_BTN_HOVER = "#3B82F6"

    SCROLLBAR_THUMB = "#475569"
    SCROLLBAR_TRACK = "transparent"


# ── 字体 ─────────────────────────────────────────────────

# Qt 单个字体族名（QFont 不支持 CSS 列表语法）
FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"

FONT_SIZE_BASE = 14
FONT_SIZE_SM = 12
FONT_SIZE_XS = 10
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20

# ── 圆角 ─────────────────────────────────────────────────

RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
RADIUS_XL = 18


# ── 状态映射 ─────────────────────────────────────────────

STATUS_EN_MAP = {
    "未启动": "pending",
    "完成中": "active",
    "已完成": "done",
    "已取消": "cancelled",
}


def get_status_colors(status: str, theme_colors, is_sub: bool = False):
    """获取指定状态的颜色（左边框色 + 底色）。

    Args:
        status: 中文状态名
        theme_colors: LightColors 或 DarkColors
        is_sub: 是否为子任务

    Returns:
        (border_color, bg_color) 十六进制颜色字符串
    """
    status_en = STATUS_EN_MAP.get(status, "pending")
    if is_sub:
        border_attr = f"COLOR_{status_en.upper()}_SUB"
        bg_attr = f"COLOR_{status_en.upper()}_SUB_BG"
    else:
        border_attr = f"COLOR_{status_en.upper()}"
        bg_attr = f"COLOR_{status_en.upper()}_BG"
    return getattr(theme_colors, border_attr, "#9CA3AF"), getattr(theme_colors, bg_attr, "#F3F4F6")


def qcolor(hex_str: str) -> QColor:
    """将十六进制颜色字符串转为 QColor。"""
    if hex_str.startswith("rgba"):
        # 简单处理：忽略 alpha
        parts = hex_str.replace("rgba(", "").replace(")", "").split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        return QColor(r, g, b)
    return QColor(hex_str)
