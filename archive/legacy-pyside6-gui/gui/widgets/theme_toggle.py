"""Three-state theme mode switch from the M4 prototype."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from todo_manager.gui.theme import (
    FONT_SIZE_SM,
    LightColors,
    DarkColors,
    RADIUS_SM,
    Theme,
    colors_for_theme,
    font_px,
)


class ThemeToggle(QWidget):
    """Segmented automatic/light/dark theme control."""

    theme_changed = Signal()

    OPTIONS = (
        (Theme.SYSTEM, "◐", "自动", "跟随系统主题"),
        (Theme.LIGHT, "☼", "明色", "使用明色主题"),
        (Theme.DARK, "☾", "暗色", "使用暗色主题"),
    )

    def __init__(self, initial_theme: Theme = Theme.SYSTEM, parent=None):
        super().__init__(parent)
        self._theme = initial_theme
        self._theme_colors = colors_for_theme(initial_theme)
        self._buttons: dict[Theme, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self.setFixedHeight(44)
        self.setMinimumWidth(182)
        self._build_ui()
        self.set_theme(initial_theme, emit=False)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        for theme, icon, label, tooltip in self.OPTIONS:
            button = QPushButton(f"{icon} {label}")
            button.setCheckable(True)
            button.setFixedHeight(34)
            button.setToolTip(tooltip)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
            button.clicked.connect(lambda checked=False, value=theme: self.set_theme(value, emit=True))
            self._group.addButton(button)
            self._buttons[theme] = button
            layout.addWidget(button, stretch=1)

    def set_theme(self, theme: Theme, emit: bool = False) -> None:
        self._theme = theme
        self._theme_colors = colors_for_theme(theme)
        for value, button in self._buttons.items():
            button.setChecked(value == theme)
        self._apply_style()
        if emit:
            self.theme_changed.emit()

    def _apply_style(self) -> None:
        c = self._theme_colors
        self.setStyleSheet(f"""
            ThemeToggle {{
                background: {c.BG_BUTTON};
                border: 1px solid {c.BORDER};
                border-radius: 8px;
            }}
            QPushButton {{
                background: transparent;
                color: {c.TEXT_TERTIARY};
                border: none;
                border-radius: {RADIUS_SM}px;
                padding: 0 8px;
            }}
            QPushButton:hover {{
                background: {c.BG_BUTTON_HOVER};
                color: {c.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background: {c.BG_SURFACE_STRONG};
                color: {c.BLUE};
                border: 1px solid {c.BORDER_STRONG};
            }}
        """)

    def refresh_theme(self, theme_colors) -> None:
        self._theme_colors = theme_colors or LightColors
        self._apply_style()

    @property
    def theme(self) -> Theme:
        return self._theme

    @property
    def theme_colors(self):
        return self._theme_colors or DarkColors
