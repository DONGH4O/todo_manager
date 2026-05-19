"""日历单元格 — 单个日期格。

包含日期数字、今天标识、以及任务条列表。
"""

from datetime import date
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget, QSpacerItem,
)

from todo_manager.gui.theme import (
    get_status_colors, qcolor, LightColors,
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XS,
    RADIUS_SM,
)
from todo_manager.gui.widgets.task_bar import TaskBar


class CalendarCell(QFrame):
    """单个日期格。"""

    cell_clicked = Signal(str)       # date_str
    task_clicked = Signal(str, str)  # task_id, date_str
    task_edit = Signal(str)          # task_id
    task_delete = Signal(str)        # task_id
    task_add_subtask = Signal(str)   # parent_task_id

    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._date_str = ""
        self._is_today = False
        self._is_selected = False
        self._is_other_month = False

        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._build_ui()

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

        # 日期行
        date_row = QHBoxLayout()
        date_row.setSpacing(4)

        self._date_label = QLabel()
        self._date_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM, QFont.Weight.Bold))
        date_row.addWidget(self._date_label)

        self._today_dot = QLabel("●")
        self._today_dot.setFont(QFont(FONT_FAMILY, 7))
        self._today_dot.hide()
        date_row.addWidget(self._today_dot)

        self._today_text = QLabel("今天")
        self._today_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
        self._today_text.hide()
        date_row.addWidget(self._today_text)

        date_row.addStretch()
        self._layout.addLayout(date_row)

        # 任务列表区（可滚动）
        self._task_container = QWidget()
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setContentsMargins(0, 0, 0, 0)
        self._task_layout.setSpacing(1)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setWidget(self._task_container)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._layout.addWidget(self._scroll_area, stretch=1)

        self._apply_style()

    def _apply_style(self):
        if self._is_today and self._is_selected:
            bg = self._theme.BG_TODAY_HOVER
        elif self._is_today:
            bg = self._theme.BG_TODAY
        elif self._is_selected:
            bg = self._theme.BG_TODAY
        elif self._is_other_month:
            bg = self._theme.BG_SURFACE_ALT
        else:
            bg = self._theme.BG_SURFACE

        border_color = self._theme.BORDER_FOCUS if self._is_selected else self._theme.BORDER_LIGHT

        self.setStyleSheet(f"""
            CalendarCell {{
                background: {bg};
                border-right: 1px solid {border_color};
                border-bottom: 1px solid {border_color};
            }}
            CalendarCell:hover {{
                background: {self._theme.BG_HOVER};
            }}
            QScrollArea {{
                background: transparent; border: none;
            }}
        """)

        if self._is_other_month:
            self._date_label.setStyleSheet(f"color: {self._theme.TEXT_TERTIARY}; opacity: 0.4; border: none; background: transparent;")
        else:
            self._date_label.setStyleSheet(f"color: {self._theme.TEXT_PRIMARY}; border: none; background: transparent;")

        self._today_dot.setStyleSheet(f"color: {self._theme.COLOR_ACTIVE}; border: none; background: transparent;")
        self._today_text.setStyleSheet(f"color: {self._theme.COLOR_ACTIVE}; border: none; background: transparent; font-weight: bold;")
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ width: 4px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {self._theme.SCROLLBAR_THUMB}; border-radius: 2px; }}
        """)

    def configure(
        self,
        date_str: str,
        day_num: int,
        is_today: bool = False,
        is_selected: bool = False,
        is_other_month: bool = False,
    ):
        """配置单元格基本信息。"""
        self._date_str = date_str
        self._is_today = is_today
        self._is_selected = is_selected
        self._is_other_month = is_other_month

        self._date_label.setText(str(day_num))
        self._today_dot.setVisible(is_today)
        self._today_text.setVisible(is_today)
        self._apply_style()

    def set_tasks(self, tasks: list):
        """填充任务条列表。

        Args:
            tasks: dict 列表，每项含 id, title, status, is_sub, has_subtasks, date_str
        """
        # 清除旧条目（含 spacer）
        while self._task_layout.count():
            item = self._task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                pass  # takeAt 已从 layout 移除，spacer 无需额外处理

        for t in tasks:
            bar = TaskBar(
                task_id=t["id"],
                title=t["title"],
                status=t["status"],
                date_str=t.get("date_str", self._date_str),
                is_sub=t.get("is_sub", False),
                theme_colors=self._theme,
            )
            bar.clicked.connect(self.task_clicked)
            bar.edit_requested.connect(self.task_edit)
            bar.delete_requested.connect(self.task_delete)
            bar.add_subtask_requested.connect(self.task_add_subtask)
            self._task_layout.addWidget(bar)

        self._task_layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.cell_clicked.emit(self._date_str)
        super().mousePressEvent(event)

    @property
    def date_str(self) -> str:
        return self._date_str
