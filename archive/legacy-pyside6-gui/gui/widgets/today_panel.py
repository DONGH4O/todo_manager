"""Left rail agenda panel from the M4 prototype."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from todo_manager.engine.models import VALID_STATUSES
from todo_manager.gui.controller import GuiController
from todo_manager.gui.theme import (
    FONT_SIZE_BASE,
    FONT_SIZE_LG,
    FONT_SIZE_SM,
    FONT_SIZE_XL,
    LightColors,
    RADIUS_MD,
    font_px,
    get_status_colors,
    status_class,
)


FILTERS = ("全部",) + VALID_STATUSES
FILTER_LABELS = {
    "全部": "全部",
    "未启动": "未启",
    "完成中": "进行",
    "已完成": "完成",
    "已取消": "取消",
}


class TaskListItem(QFrame):
    """Prototype .task card used in the left rail agenda."""

    clicked = Signal(str, str)

    def __init__(self, task, theme_colors=None, selected: bool = False, controller=None, parent=None):
        super().__init__(parent)
        self._task = task
        self._theme = theme_colors or LightColors
        self._selected = selected
        self._controller = controller or GuiController()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(124)
        self.setMinimumWidth(0)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        top.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        top.addSpacing(0)
        top.addWidget(self._dot)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(3)
        self._title = QLabel(self._task.title)
        self._title.setWordWrap(False)
        self._title.setToolTip(self._task.title)
        self._title.setFont(font_px(FONT_SIZE_BASE, QFont.Weight.Bold))
        self._title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        title_box.addWidget(self._title)
        self._range = QLabel(f"{self._task.start_date} - {self._task.end_date}")
        self._range.setFont(font_px(FONT_SIZE_SM))
        self._range.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        title_box.addWidget(self._range)
        top.addLayout(title_box, stretch=1)

        self._status = QLabel(self._task.status)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFixedHeight(24)
        self._status.setMinimumWidth(54)
        self._status.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
        top.addWidget(self._status)
        layout.addLayout(top)

        summary = (self._task.background or "").strip()
        if len(summary) > 64:
            summary = summary[:64] + "…"
        self._summary = QLabel(summary or "暂无备注")
        self._summary.setWordWrap(False)
        self._summary.setToolTip(summary or "暂无备注")
        self._summary.setFixedHeight(18)
        self._summary.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self._summary.setFont(font_px(FONT_SIZE_SM))
        layout.addWidget(self._summary)

        done, total = self._controller.subtask_progress(self._task)
        tags = QHBoxLayout()
        tags.setSpacing(6)
        self._subtasks = QLabel(f"子任务 {done}/{total}")
        self._subtasks.setFont(font_px(FONT_SIZE_SM))
        tags.addWidget(self._subtasks)
        tags.addStretch()
        layout.addLayout(tags)

    def _apply_style(self) -> None:
        cls = status_class(self._task.status)
        dot_color, bg = get_status_colors(self._task.status, self._theme)
        border = self._theme.BORDER_FOCUS if self._selected else self._theme.BORDER
        shadow = f"border: 1px solid {border};"
        decoration = "line-through" if cls == "cancelled" else "none"
        title_color = self._theme.TEXT_SOFT_ON_LIGHT if cls == "cancelled" else self._theme.TEXT_ON_LIGHT
        self.setStyleSheet(f"""
            TaskListItem {{
                background: rgba(255,255,255,0.68);
                {shadow}
                border-radius: {RADIUS_MD}px;
            }}
            TaskListItem:hover {{
                background: {self._theme.BG_SURFACE_STRONG};
                border-color: {self._theme.BORDER_STRONG};
            }}
        """)
        self._dot.setStyleSheet(f"background: {dot_color}; border-radius: 4px; margin-top: 5px;")
        self._title.setStyleSheet(
            f"color: {title_color}; text-decoration: {decoration}; border: none; background: transparent;"
        )
        self._range.setStyleSheet(f"color: {self._theme.TEXT_MUTED_ON_LIGHT}; border: none; background: transparent;")
        self._summary.setStyleSheet(f"color: {self._theme.TEXT_MUTED_ON_LIGHT}; border: none; background: transparent;")
        self._subtasks.setStyleSheet(f"""
            QLabel {{
                color: #33546A;
                background: {self._theme.SILVER};
                border: 1px solid {self._theme.BORDER};
                border-radius: 999px;
                padding: 2px 8px;
            }}
        """)
        self._status.setStyleSheet(f"""
            QLabel {{
                color: {dot_color};
                background: {bg};
                border: 1px solid {dot_color};
                border-radius: 999px;
                padding: 2px 9px;
                min-height: 24px;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._task.id, self._task.start_date)
            event.accept()
            return
        super().mousePressEvent(event)


class TodayPanel(QFrame):
    """Prototype rail panel: metrics, status tabs, and selected-date agenda."""

    task_selected = Signal(str, str)
    create_task = Signal(str)

    def __init__(self, theme_colors=None, controller: GuiController | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._controller = controller or GuiController()
        self._selected_date = date.today().isoformat()
        self._selected_task_id: str | None = None
        self._current_filter = "全部"
        self.setObjectName("RailPanel")
        self.setFixedWidth(260)
        self._build_ui()
        self.refresh(self._selected_date, date.today().year, date.today().month)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        head = QWidget()
        head.setObjectName("PanelHead")
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(14, 12, 14, 12)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self._title = QLabel("今日节奏")
        self._title.setFont(font_px(FONT_SIZE_LG, QFont.Weight.Bold))
        self._subtitle = QLabel()
        self._subtitle.setFont(font_px(FONT_SIZE_SM))
        title_box.addWidget(self._title)
        title_box.addWidget(self._subtitle)
        head_layout.addLayout(title_box)
        layout.addWidget(head)

        self._metric_grid = QGridLayout()
        self._metric_grid.setContentsMargins(12, 12, 12, 12)
        self._metric_grid.setSpacing(8)
        self._metric_labels: dict[str, QLabel] = {}
        metric_names = ("当月任务", "当日安排", "未启动", "完成中", "已完成", "已取消")
        for idx, name in enumerate(metric_names):
            box = QFrame()
            box.setObjectName("Metric")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(12, 10, 12, 10)
            box_layout.setSpacing(4)
            number = QLabel("0")
            number.setFont(font_px(FONT_SIZE_XL, QFont.Weight.ExtraBold))
            label = QLabel(name)
            label.setFont(font_px(FONT_SIZE_SM))
            box_layout.addWidget(number)
            box_layout.addWidget(label)
            self._metric_grid.addWidget(box, idx // 2, idx % 2)
            self._metric_labels[name] = number
        layout.addLayout(self._metric_grid)

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        self._filter_buttons: dict[str, QPushButton] = {}
        tabs = QHBoxLayout()
        tabs.setContentsMargins(12, 0, 12, 12)
        tabs.setSpacing(6)
        for name in FILTERS:
            btn = QPushButton(FILTER_LABELS[name])
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, value=name: self._on_filter(value))
            self._filter_group.addButton(btn)
            self._filter_buttons[name] = btn
            tabs.addWidget(btn, stretch=1)
        self._filter_buttons["全部"].setChecked(True)
        layout.addLayout(tabs)

        self._agenda = QWidget()
        agenda_layout = QVBoxLayout(self._agenda)
        agenda_layout.setContentsMargins(12, 0, 12, 12)
        agenda_layout.setSpacing(10)
        self._agenda_title = QLabel()
        self._agenda_title.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
        agenda_layout.addWidget(self._agenda_title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list = QWidget()
        self._list_layout = QVBoxLayout(self._list)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._scroll.setWidget(self._list)
        agenda_layout.addWidget(self._scroll, stretch=1)
        layout.addWidget(self._agenda, stretch=1)
        self._apply_style()

    def refresh(
        self,
        date_str: str,
        year: int,
        month: int,
        selected_task_id: str | None = None,
    ) -> None:
        self._selected_date = date_str
        self._selected_task_id = selected_task_id
        tasks = self._controller.get_tasks_for_date(date_str)
        counts = self._controller.day_status_counts(date_str)
        self._subtitle.setText(date_str)
        self._agenda_title.setText(self._format_day_title(date_str))
        self._metric_labels["当月任务"].setText(str(self._controller.month_task_count(year, month)))
        self._metric_labels["当日安排"].setText(str(len(tasks)))
        for status in VALID_STATUSES:
            self._metric_labels[status].setText(str(counts.get(status, 0)))
        self._render_tasks(tasks)

    def _render_tasks(self, tasks: list) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if self._current_filter != "全部":
            tasks = [task for task in tasks if task.status == self._current_filter]

        if not tasks:
            empty = QLabel("这一天还没有任务。")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            empty.setFont(font_px(FONT_SIZE_BASE))
            empty.setStyleSheet(f"""
                QLabel {{
                    color: {self._theme.TEXT_MUTED_ON_LIGHT};
                    border: 1px dashed {self._theme.BORDER_STRONG};
                    border-radius: {RADIUS_MD}px;
                    background: rgba(255,255,255,0.48);
                    padding: 18px;
                }}
            """)
            self._list_layout.addWidget(empty)
            self._list_layout.addStretch()
            return

        for task in tasks:
            item = TaskListItem(
                task,
                theme_colors=self._theme,
                selected=task.id == self._selected_task_id,
                controller=self._controller,
            )
            item.clicked.connect(self.task_selected)
            self._list_layout.addWidget(item)
        self._list_layout.addStretch()
        self._scroll.verticalScrollBar().setValue(0)

    def _on_filter(self, value: str) -> None:
        self._current_filter = value
        selected = date.fromisoformat(self._selected_date)
        self.refresh(self._selected_date, selected.year, selected.month, self._selected_task_id)

    def _apply_style(self) -> None:
        c = self._theme
        self.setStyleSheet(f"""
            TodayPanel#RailPanel {{
                background: {c.BG_SURFACE};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
            }}
            QWidget#PanelHead {{
                border-bottom: 1px solid {c.BORDER};
                background: transparent;
            }}
            QFrame#Metric {{
                min-height: 74px;
                background: rgba(255,255,255,0.56);
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                color: {c.TEXT_ON_LIGHT};
            }}
            QFrame#Metric QLabel {{
                color: {c.TEXT_ON_LIGHT};
                border: none;
                background: transparent;
            }}
            QPushButton {{
                background: transparent;
                color: {c.TEXT_TERTIARY};
                border: 1px solid {c.BORDER_LIGHT};
                border-radius: {RADIUS_MD}px;
                font-size: {FONT_SIZE_SM}px;
                white-space: nowrap;
            }}
            QPushButton:hover {{
                color: {c.TEXT_PRIMARY};
                background: {c.BG_BUTTON_HOVER};
            }}
            QPushButton:checked {{
                color: {c.TEXT_ON_LIGHT};
                background: {c.BG_SURFACE_STRONG};
                border: 1px solid {c.BORDER};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {c.SCROLLBAR_THUMB};
                border-radius: 2px;
            }}
        """)
        self._title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        self._subtitle.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
        self._agenda_title.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
        self._agenda.setStyleSheet("background: transparent; border: none;")
        self._list.setStyleSheet("background: transparent; border: none;")

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors
        self._apply_style()
        selected = date.fromisoformat(self._selected_date)
        self.refresh(self._selected_date, selected.year, selected.month, self._selected_task_id)

    @staticmethod
    def _format_day_title(date_str: str) -> str:
        day = date.fromisoformat(date_str)
        return f"{day.month}月{day.day}日"
