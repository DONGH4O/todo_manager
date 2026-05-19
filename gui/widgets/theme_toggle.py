"""主题切换按钮。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton

from todo_manager.gui.theme import Theme, LightColors, DarkColors, FONT_FAMILY


class ThemeToggle(QPushButton):
    """明/暗主题切换按钮。"""

    theme_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = Theme.LIGHT
        self._theme_colors = LightColors

        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont(FONT_FAMILY, 16))
        self.setText("🌙")

        self.clicked.connect(self._toggle)
        self._apply_style()

    def _toggle(self):
        if self._current_theme == Theme.LIGHT:
            self._current_theme = Theme.DARK
            self._theme_colors = DarkColors
            self.setText("☀️")
        else:
            self._current_theme = Theme.LIGHT
            self._theme_colors = LightColors
            self.setText("🌙")
        self._apply_style()
        self.theme_changed.emit()

    def _apply_style(self):
        c = self._theme_colors
        self.setStyleSheet(f"""
            QPushButton {{
                background: {c.BG_SURFACE};
                border: 1px solid {c.BORDER};
                border-radius: 10px;
                color: {c.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background: {c.BG_HOVER};
            }}
        """)

    @property
    def theme(self) -> Theme:
        return self._current_theme

    @property
    def theme_colors(self):
        return self._theme_colors
