"""Calendar day cell matching the M4 HTML prototype."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from todo_manager.gui.theme import (
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    LightColors,
    RADIUS_MD,
    font_px,
)
from todo_manager.gui.widgets.task_bar import TaskBar


class CalendarCell(QFrame):
    """Rounded day card with day number, count badge, and mini task list."""

    cell_clicked = Signal(str)
    task_clicked = Signal(str, str)
    task_edit = Signal(str)
    task_delete = Signal(str)
    task_add_subtask = Signal(str)

    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._date_str = ""
        self._is_today = False
        self._is_selected = False
        self._is_other_month = False
        self._task_count = 0
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(9, 9, 9, 9)
        self._layout.setSpacing(8)

        day_row = QHBoxLayout()
        day_row.setContentsMargins(0, 0, 0, 0)
        day_row.setSpacing(6)
        self._date_label = QLabel()
        self._date_label.setFont(font_px(FONT_SIZE_SM, QFont.Weight.ExtraBold))
        day_row.addWidget(self._date_label)
        day_row.addStretch()
        self._count_label = QLabel("0")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_label.setFixedSize(20, 20)
        self._count_label.setFont(font_px(FONT_SIZE_XS, QFont.Weight.Bold))
        day_row.addWidget(self._count_label)
        self._layout.addLayout(day_row)

        self._task_container = QWidget()
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setContentsMargins(0, 0, 0, 0)
        self._task_layout.setSpacing(5)
        self._layout.addWidget(self._task_container, stretch=1)
        self._apply_style()

    def configure(
        self,
        date_str: str,
        day_num: int,
        is_today: bool = False,
        is_selected: bool = False,
        is_other_month: bool = False,
    ) -> None:
        self._date_str = date_str
        self._is_today = is_today
        self._is_selected = is_selected
        self._is_other_month = is_other_month
        self._date_label.setText(str(day_num))
        self._apply_style()

    def set_tasks(self, tasks: list[dict]) -> None:
        while self._task_layout.count():
            item = self._task_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        self._task_count = len(tasks)
        self._count_label.setVisible(self._task_count > 0)
        self._count_label.setText(str(self._task_count))

        visible_tasks = tasks[:3]
        for task in visible_tasks:
            bar = TaskBar(
                task_id=task["id"],
                title=task["title"],
                status=task["status"],
                date_str=task.get("date_str", self._date_str),
                is_sub=task.get("is_sub", False),
                theme_colors=self._theme,
            )
            bar.clicked.connect(self.task_clicked)
            bar.edit_requested.connect(self.task_edit)
            bar.delete_requested.connect(self.task_delete)
            bar.add_subtask_requested.connect(self.task_add_subtask)
            self._task_layout.addWidget(bar)
            bar.set_highlighted(task.get("is_selected", False))

        overflow = len(tasks) - len(visible_tasks)
        if overflow > 0:
            more = QLabel(f"+{overflow} 更多")
            more.setFont(font_px(FONT_SIZE_XS))
            more.setStyleSheet(f"color: {self._theme.TEXT_TERTIARY}; border: none; background: transparent;")
            self._task_layout.addWidget(more)
        self._task_layout.addStretch()
        self._apply_style()

    def _apply_style(self) -> None:
        if self._is_today:
            bg = self._theme.BG_TODAY
        elif self._is_selected:
            bg = self._theme.BG_DAY_HOVER
        else:
            bg = self._theme.BG_DAY
        border_color = self._theme.BORDER_FOCUS if self._is_selected else self._theme.BORDER
        opacity = "0.46" if self._is_other_month else "1"
        self.setStyleSheet(f"""
            CalendarCell {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: {RADIUS_MD}px;
            }}
            CalendarCell:hover {{
                background: {self._theme.BG_DAY_HOVER};
                border-color: {self._theme.BORDER_STRONG};
            }}
        """)
        self._date_label.setStyleSheet(f"""
            color: {self._theme.TEXT_PRIMARY};
            border: none;
            background: transparent;
            opacity: {opacity};
        """)
        self._count_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                background: {self._theme.BLUE};
                border: none;
                border-radius: 10px;
                font-size: 11px;
            }}
        """)
        self._task_container.setStyleSheet("background: transparent; border: none;")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.cell_clicked.emit(self._date_str)
        super().mousePressEvent(event)

    @property
    def date_str(self) -> str:
        return self._date_str
