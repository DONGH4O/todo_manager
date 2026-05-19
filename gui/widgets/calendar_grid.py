"""日历网格 — 7 列月视图，包含表头和日期格网格。"""

from datetime import date
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QVBoxLayout, QWidget, QSizePolicy,
)

from todo_manager.gui.theme import (
    LightColors,
    FONT_FAMILY, FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_LG, FONT_SIZE_XL,
    qcolor, RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
)
from todo_manager.gui.widgets.calendar_cell import CalendarCell
from todo_manager.gui.widgets.task_bar import TaskBar
from todo_manager.engine.calendar_utils import get_month_grid
from todo_manager.engine.task_manager import get_tasks_for_date


WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


class CalendarGrid(QWidget):
    """月视图日历网格。"""

    cell_clicked = Signal(str)       # date_str
    task_clicked = Signal(str, str)  # task_id, date_str
    task_edit = Signal(str)          # task_id
    task_delete = Signal(str)        # task_id
    task_add_subtask = Signal(str)   # parent_task_id

    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._year = date.today().year
        self._month = date.today().month
        self._today_str = date.today().isoformat()
        self._selected_date = self._today_str
        self._selected_task_id = None

        self._cells: dict = {}  # key: date_str -> CalendarCell
        self._header_labels: list = []  # 表头 QLabel 引用

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 表头行
        header_container = QWidget()
        header_layout = QGridLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        for i, day_name in enumerate(WEEKDAYS):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设计文档: 表头 weekday 使用 small(12px) 字号
            label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM, QFont.Weight.Bold))
            is_weekend = i >= 5
            weekend_color = "#EF4444"  # 周末 red，与 prototype 一致
            label.setStyleSheet(f"""
                QLabel {{
                    color: {weekend_color if is_weekend else self._theme.TEXT_TERTIARY};
                    padding: 10px 0; border: none;
                    background: {self._theme.BG_SURFACE};
                    border-bottom: 1px solid {self._theme.BORDER};
                    border-right: 1px solid {self._theme.BORDER_LIGHT if i < 6 else 'none'};
                }}
            """)
            header_layout.addWidget(label, 0, i)
            self._header_labels.append(label)

        main_layout.addWidget(header_container)

        # 日历网格
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)

        main_layout.addWidget(self._grid_widget, stretch=1)

    def refresh(self):
        """重新渲染整个日历（月份切换等结构性变化时调用）。"""
        self._build_grid()

    def refresh_theme(self, theme_colors):
        """主题切换时仅更新样式，不重建网格结构。"""
        self._theme = theme_colors
        self._update_header_style()
        # 增量更新所有单元格
        for cell in self._cells.values():
            cell._theme = self._theme
            cell._apply_style()
            for bar in cell.findChildren(TaskBar):
                if hasattr(bar, 'refresh_theme'):
                    bar.refresh_theme(self._theme)

    def _build_grid(self):
        # 清空旧单元格
        for cell in self._cells.values():
            cell.setParent(None)
            cell.deleteLater()
        self._cells.clear()

        grid = get_month_grid(self._year, self._month)

        for row_idx, week in enumerate(grid):
            for col_idx, cell_info in enumerate(week):
                if cell_info is None:
                    continue

                date_str = cell_info["date"]
                day_num = int(date_str[-2:])

                # 判断是否属于当前月
                parts = date_str.split("-")
                is_other = int(parts[1]) != self._month
                is_today = date_str == self._today_str
                is_selected = date_str == self._selected_date

                cell = CalendarCell(theme_colors=self._theme)
                cell.configure(
                    date_str=date_str,
                    day_num=day_num,
                    is_today=is_today,
                    is_selected=is_selected,
                    is_other_month=is_other,
                )

                # 获取该日任务
                tasks_for_day = get_tasks_for_date(date_str)
                task_infos = self._format_task_infos(tasks_for_day, date_str)
                cell.set_tasks(task_infos)

                # 信号连接
                cell.cell_clicked.connect(self.cell_clicked)
                cell.task_clicked.connect(self.task_clicked)
                cell.task_edit.connect(self.task_edit)
                cell.task_delete.connect(self.task_delete)
                cell.task_add_subtask.connect(self.task_add_subtask)

                self._cells[date_str] = cell
                self._grid_layout.addWidget(cell, row_idx, col_idx)

        # 设置行拉伸
        for r in range(self._grid_layout.rowCount()):
            self._grid_layout.setRowStretch(r, 1)
        for c in range(7):
            self._grid_layout.setColumnStretch(c, 1)

    def _format_task_infos(self, tasks: list, date_str: str) -> list:
        """将 Task 对象列表转为 dict 列表（扁平化含子任务）。"""
        result = []
        for t in tasks:
            result.append({
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "date_str": date_str,
                "is_sub": False,
                "created_at": t.created_at,
            })
            for s in t.subtasks:
                result.append({
                    "id": s.id,
                    "title": s.title,
                    "status": s.status,
                    "date_str": date_str,
                    "is_sub": True,
                    "created_at": s.created_at,
                })
        result.sort(key=lambda x: x["created_at"])
        return result

    def navigate(self, year: int, month: int):
        """跳转到指定年月。"""
        self._year = year
        self._month = month
        self.refresh()

    def select_date(self, date_str: str):
        """选中指定日期（增量更新，避免全量重建）。"""
        old_selected = self._selected_date
        self._selected_date = date_str
        self._selected_task_id = None
        self._update_cell_selection(old_selected, date_str)

    def select_task(self, task_id: str, date_str: str):
        """选中指定任务并跳转到其 start_date 所在月。"""
        self._selected_task_id = task_id
        parts = date_str.split("-")
        new_year = int(parts[0])
        new_month = int(parts[1])
        old_selected = self._selected_date
        self._selected_date = date_str
        # 月份变化时重建网格，否则增量更新
        if new_year != self._year or new_month != self._month:
            self._year = new_year
            self._month = new_month
            self.refresh()
        else:
            self._update_cell_selection(old_selected, date_str)

    def _update_cell_selection(self, old_date: str, new_date: str):
        """增量更新单元格选中状态。"""
        if old_date and old_date in self._cells:
            cell = self._cells[old_date]
            cell._is_selected = False
            cell._apply_style()
        if new_date and new_date in self._cells:
            cell = self._cells[new_date]
            cell._is_selected = True
            cell._apply_style()

    def _update_header_style(self):
        """更新表头样式（主题切换时调用）。"""
        for i, label in enumerate(self._header_labels):
            is_weekend = i >= 5
            weekend_color = "#EF4444"
            label.setStyleSheet(f"""
                QLabel {{
                    color: {weekend_color if is_weekend else self._theme.TEXT_TERTIARY};
                    padding: 10px 0; border: none;
                    background: {self._theme.BG_SURFACE};
                    border-bottom: 1px solid {self._theme.BORDER};
                    border-right: 1px solid {self._theme.BORDER_LIGHT if i < 6 else 'none'};
                }}
            """)

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def selected_date(self) -> str:
        return self._selected_date

    @property
    def selected_task_id(self) -> str | None:
        return self._selected_task_id
