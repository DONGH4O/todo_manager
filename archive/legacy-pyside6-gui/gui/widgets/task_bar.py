"""Compact task mini item used inside calendar day cells."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from todo_manager.gui.theme import (
    FONT_SIZE_XS,
    LightColors,
    RADIUS_SM,
    font_px,
    get_status_colors,
    status_class,
)


class TaskBar(QFrame):
    """Prototype .mini calendar task chip."""

    clicked = Signal(str, str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    add_subtask_requested = Signal(str)

    def __init__(
        self,
        task_id: str,
        title: str,
        status: str,
        date_str: str,
        is_sub: bool = False,
        theme_colors=None,
        parent=None,
    ):
        super().__init__(parent)
        self._task_id = task_id
        self._title = title
        self._status = status
        self._date_str = date_str
        self._is_sub = is_sub
        self._theme = theme_colors or LightColors
        self._highlighted = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(0)
        self.setFixedHeight(21)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 2, 7, 2)
        layout.setSpacing(4)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(font_px(FONT_SIZE_XS))
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._title_label.setMinimumWidth(0)
        self._title_label.setWordWrap(False)
        layout.addWidget(self._title_label)

    def _apply_style(self) -> None:
        _border_color, bg_color = get_status_colors(self._status, self._theme, self._is_sub)
        cls = status_class(self._status)
        text_color = {
            "pending": self._theme.TEXT_TERTIARY,
            "active": self._theme.BLUE,
            "done": self._theme.GREEN,
            "cancelled": self._theme.TEXT_SOFT_ON_LIGHT,
        }.get(cls, self._theme.TEXT_TERTIARY)
        decoration = "line-through" if cls == "cancelled" else "none"
        border = f"2px solid {self._theme.BORDER_FOCUS}" if self._highlighted else "0px solid transparent"
        self.setStyleSheet(f"""
            TaskBar {{
                background: {bg_color};
                border: {border};
                border-radius: {RADIUS_SM}px;
            }}
            TaskBar:hover {{
                border-color: {self._theme.BORDER_STRONG};
                background: {self._theme.BG_BUTTON_HOVER};
            }}
        """)
        self._title_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                text-decoration: {decoration};
                border: none;
                background: transparent;
            }}
        """)

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._task_id, self._date_str)
            event.accept()
            return
        super().mousePressEvent(event)

    def set_highlighted(self, highlighted: bool) -> None:
        self._highlighted = highlighted
        self._apply_style()

    @property
    def task_id(self) -> str:
        return self._task_id
