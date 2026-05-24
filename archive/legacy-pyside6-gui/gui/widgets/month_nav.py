"""Prototype aligned month navigation header."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from todo_manager.gui.theme import (
    FONT_FAMILY,
    FONT_SIZE_BASE,
    LightColors,
    RADIUS_MD,
)


MIN_YEAR = 1900
MAX_YEAR = 2100


class MonthNav(QWidget):
    """Month controls matching prototype .month-tools/.month-picker."""

    prev_month = Signal()
    next_month = Signal()
    month_selected = Signal(int)
    year_selected = Signal(int)

    def __init__(self, year: int, month: int, theme_colors=None, parent=None):
        super().__init__(parent)
        self._year = year
        self._month = month
        self._theme = theme_colors or LightColors
        self._updating = False
        self._build_ui()
        self.update_display(year, month)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._prev_btn = QPushButton("‹")
        self._prev_btn.setFixedSize(44, 38)
        self._prev_btn.setToolTip("上个月")
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self.prev_month)
        layout.addWidget(self._prev_btn)

        self._year_select = QComboBox()
        self._year_select.setFixedSize(92, 38)
        self._year_select.setToolTip("选择年份")
        self._year_select.addItems([str(year) for year in range(MIN_YEAR, MAX_YEAR + 1)])
        self._year_select.currentTextChanged.connect(self._on_year_changed)
        layout.addWidget(self._year_select)

        self._month_select = QComboBox()
        self._month_select.setFixedSize(78, 38)
        self._month_select.setToolTip("选择月份")
        self._month_select.addItems([f"{month}月" for month in range(1, 13)])
        self._month_select.currentIndexChanged.connect(self._on_month_changed)
        layout.addWidget(self._month_select)

        self._next_btn = QPushButton("›")
        self._next_btn.setFixedSize(44, 38)
        self._next_btn.setToolTip("下个月")
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self.next_month)
        layout.addWidget(self._next_btn)

        self._apply_style()

    def _apply_style(self) -> None:
        c = self._theme
        self.setStyleSheet(f"""
            QPushButton {{
                background: {c.BG_BUTTON};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                font-family: "{FONT_FAMILY}";
                font-size: 22px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {c.BG_BUTTON_HOVER};
                border-color: {c.BORDER_STRONG};
            }}
            QPushButton:disabled {{
                color: {c.TEXT_TERTIARY};
                background: {c.BG_BUTTON};
            }}
            QComboBox {{
                height: 38px;
                background: {c.BG_INPUT};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                padding: 0 10px;
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_BASE}px;
            }}
            QComboBox:focus {{
                border-color: {c.BORDER_FOCUS};
            }}
            QComboBox QAbstractItemView {{
                background: {c.BG_DROPDOWN};
                color: {c.TEXT_PRIMARY};
                selection-background-color: {c.BLUE_SOFT};
                border: 1px solid {c.BORDER};
            }}
        """)

    def _on_year_changed(self, value: str) -> None:
        if self._updating or not value:
            return
        self.year_selected.emit(int(value))

    def _on_month_changed(self, index: int) -> None:
        if self._updating or index < 0:
            return
        self.month_selected.emit(index + 1)

    def update_display(self, year: int, month: int) -> None:
        self._year = year
        self._month = month
        self._updating = True
        self._year_select.setCurrentText(str(year))
        self._month_select.setCurrentIndex(month - 1)
        self._updating = False
        self._prev_btn.setEnabled(not (year == MIN_YEAR and month == 1))
        self._next_btn.setEnabled(not (year == MAX_YEAR and month == 12))

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors
        self._apply_style()
