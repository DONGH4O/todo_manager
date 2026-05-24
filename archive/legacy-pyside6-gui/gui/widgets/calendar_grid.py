"""Six-row month calendar grid aligned to the HTML prototype."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from todo_manager.gui.controller import GuiController
from todo_manager.gui.theme import FONT_SIZE_SM, LightColors, font_px
from todo_manager.gui.widgets.calendar_cell import CalendarCell
from todo_manager.gui.widgets.task_bar import TaskBar


WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


class CalendarGrid(QWidget):
    """Prototype .calendar-body with weekday row and 6x7 day grid."""

    cell_clicked = Signal(str)
    task_clicked = Signal(str, str)
    task_edit = Signal(str)
    task_delete = Signal(str)
    task_add_subtask = Signal(str)

    def __init__(self, theme_colors=None, controller: GuiController | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._controller = controller or GuiController()
        today = date.today()
        self._year = today.year
        self._month = today.month
        self._today_str = today.isoformat()
        self._selected_date = self._today_str
        self._selected_task_id: str | None = None
        self._cells: dict[str, CalendarCell] = {}
        self._header_labels: list[QLabel] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        header = QWidget()
        header_layout = QGridLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(8)
        for index, day_name in enumerate(WEEKDAYS):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
            header_layout.addWidget(label, 0, index)
            header_layout.setColumnStretch(index, 1)
            self._header_labels.append(label)
        main_layout.addWidget(header)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(8)
        self._grid_layout.setVerticalSpacing(8)
        main_layout.addWidget(self._grid_widget, stretch=1)
        self._update_header_style()

    def refresh(self) -> None:
        self._build_grid()

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors
        self._update_header_style()
        for cell in self._cells.values():
            cell._theme = self._theme
            cell._apply_style()
            for bar in cell.findChildren(TaskBar):
                bar.refresh_theme(self._theme)

    def _build_grid(self) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._cells.clear()

        for row_idx, week in enumerate(self._display_grid()):
            for col_idx, cell_info in enumerate(week):
                date_str = cell_info["date"]
                day_num = int(date_str[-2:])
                parts = date_str.split("-")
                is_other = int(parts[1]) != self._month
                cell = CalendarCell(theme_colors=self._theme)
                cell.configure(
                    date_str=date_str,
                    day_num=day_num,
                    is_today=date_str == self._today_str,
                    is_selected=date_str == self._selected_date,
                    is_other_month=is_other,
                )
                tasks = self._controller.get_tasks_for_date(date_str)
                cell.set_tasks(self._format_task_infos(tasks, date_str))
                cell.cell_clicked.connect(self.cell_clicked)
                cell.task_clicked.connect(self.task_clicked)
                cell.task_edit.connect(self.task_edit)
                cell.task_delete.connect(self.task_delete)
                cell.task_add_subtask.connect(self.task_add_subtask)
                self._cells[date_str] = cell
                self._grid_layout.addWidget(cell, row_idx, col_idx)

        for row in range(6):
            self._grid_layout.setRowStretch(row, 1)
        for col in range(7):
            self._grid_layout.setColumnStretch(col, 1)

    def _display_grid(self) -> list[list[dict[str, str]]]:
        first_day = date(self._year, self._month, 1)
        cursor = first_day - timedelta(days=first_day.weekday())
        rows: list[list[dict[str, str]]] = []
        for _ in range(6):
            week: list[dict[str, str]] = []
            for _ in range(7):
                week.append({"date": cursor.isoformat()})
                cursor += timedelta(days=1)
            rows.append(week)
        return rows

    def _format_task_infos(self, tasks: list, date_str: str) -> list[dict]:
        result = []
        for task in tasks:
            result.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "date_str": date_str,
                    "is_sub": False,
                    "created_at": task.created_at,
                    "is_selected": task.id == self._selected_task_id,
                    "subtask_count": len([sub for sub in task.subtasks if not sub.deleted]),
                }
            )
        result.sort(key=lambda item: item["created_at"])
        return result

    def navigate(self, year: int, month: int) -> None:
        self._year = year
        self._month = month
        self.refresh()

    def select_date(self, date_str: str) -> None:
        old_selected = self._selected_date
        self._selected_date = date_str
        self._selected_task_id = None
        self._update_cell_selection(old_selected, date_str)
        self._update_task_highlight(None)

    def select_task(self, task_id: str, date_str: str) -> None:
        self._selected_task_id = task_id
        parts = date_str.split("-")
        new_year = int(parts[0])
        new_month = int(parts[1])
        old_selected = self._selected_date
        self._selected_date = date_str
        if new_year != self._year or new_month != self._month:
            self._year = new_year
            self._month = new_month
            self.refresh()
        else:
            self._update_cell_selection(old_selected, date_str)
            self._update_task_highlight(task_id)

    def _update_cell_selection(self, old_date: str, new_date: str) -> None:
        if old_date in self._cells:
            self._cells[old_date]._is_selected = False
            self._cells[old_date]._apply_style()
        if new_date in self._cells:
            self._cells[new_date]._is_selected = True
            self._cells[new_date]._apply_style()

    def _update_task_highlight(self, task_id: str | None) -> None:
        for cell in self._cells.values():
            for bar in cell.findChildren(TaskBar):
                bar.set_highlighted(bool(task_id and bar.task_id == task_id))

    def _update_header_style(self) -> None:
        for index, label in enumerate(self._header_labels):
            color = self._theme.DANGER if index >= 5 else self._theme.TEXT_TERTIARY
            label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        self.setStyleSheet("background: transparent; border: none;")

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
