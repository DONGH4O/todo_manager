"""Right-side inline detail editor from the M4 prototype."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
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
    LightColors,
    RADIUS_MD,
    font_px,
    get_status_colors,
    status_class,
)


class DetailPanel(QFrame):
    """Prototype detail panel with inline editing and footer actions."""

    create_task = Signal(str)
    edit_task = Signal(str)
    delete_task = Signal(str)
    add_subtask = Signal(str)
    task_saved = Signal(str, object, object)

    def __init__(self, theme_colors=None, controller: GuiController | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._controller = controller or GuiController()
        self._selected_date = ""
        self._selected_task_id: str | None = None
        self._current_lookup = None
        self._status_buttons: dict[str, QPushButton] = {}
        self._subtask_status: dict[str, QComboBox] = {}
        self.setObjectName("DetailPanel")
        self.setFixedWidth(340)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("PanelHead")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self._title_label = QLabel("任务详情")
        self._title_label.setFont(font_px(FONT_SIZE_LG, QFont.Weight.Bold))
        self._subtitle_label = QLabel("选中任务后编辑")
        self._subtitle_label.setFont(font_px(FONT_SIZE_SM))
        title_box.addWidget(self._title_label)
        title_box.addWidget(self._subtitle_label)
        header_layout.addLayout(title_box)
        layout.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(14, 14, 14, 14)
        self._content_layout.setSpacing(14)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll, stretch=1)

        self._footer = QWidget()
        self._footer.setObjectName("DetailActions")
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(14, 12, 14, 12)
        footer_layout.setSpacing(10)
        self._delete_btn = QPushButton("删除")
        self._delete_btn.setToolTip("删除任务")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.clicked.connect(self._on_delete)
        footer_layout.addWidget(self._delete_btn)
        footer_layout.addStretch()
        self._save_btn = QPushButton("保存")
        self._save_btn.setToolTip("保存修改")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(self._save_btn)
        layout.addWidget(self._footer)
        self._apply_style()
        self._render_empty()

    def show_day(self, date_str: str) -> None:
        self._selected_date = date_str
        self._selected_task_id = None
        self._current_lookup = None
        tasks = self._controller.get_tasks_for_date(date_str)
        self._subtitle_label.setText(f"{date_str} · {len(tasks)} 条任务")
        self._render_empty()

    def show_task(self, task_id: str) -> None:
        self._selected_task_id = task_id
        lookup = self._controller.find_task_any(task_id)
        self._current_lookup = lookup
        if lookup.item is None:
            self._render_empty()
            return
        item = lookup.item
        self._selected_date = item.start_date if lookup.parent is None else lookup.parent.start_date
        self._subtitle_label.setText(f"{item.start_date} - {item.end_date} · {item.status}")
        self._render_form()

    def _render_empty(self) -> None:
        self._clear_content()
        empty = QLabel("请选择日历中的任务，或新建一个任务。")
        empty.setWordWrap(True)
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setFont(font_px(FONT_SIZE_BASE))
        empty.setObjectName("EmptyState")
        self._content_layout.addWidget(empty)
        self._content_layout.addStretch()
        self._set_footer_enabled(False)
        self._apply_style()

    def _render_form(self) -> None:
        lookup = self._current_lookup
        if lookup is None or lookup.item is None:
            self._render_empty()
            return
        item = lookup.item
        self._clear_content()
        self._set_footer_enabled(True)

        self._title_input = self._field_input("标题", item.title)
        self._content_layout.addWidget(self._title_input["container"])

        dates = QWidget()
        date_layout = QGridLayout(dates)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setHorizontalSpacing(10)
        date_layout.setVerticalSpacing(0)
        self._start_edit = self._date_edit(item.start_date)
        self._end_edit = self._date_edit(item.end_date)
        date_layout.addWidget(self._field_label("开始日期"), 0, 0)
        date_layout.addWidget(self._field_label("截止日期"), 0, 1)
        date_layout.addWidget(self._start_edit, 1, 0)
        date_layout.addWidget(self._end_edit, 1, 1)
        self._content_layout.addWidget(dates)

        note_box = QWidget()
        note_layout = QVBoxLayout(note_box)
        note_layout.setContentsMargins(0, 0, 0, 0)
        note_layout.setSpacing(7)
        note_layout.addWidget(self._field_label("备注"))
        self._note_edit = QPlainTextEdit()
        self._note_edit.setPlainText(item.background or "")
        self._note_edit.setFixedHeight(88)
        note_layout.addWidget(self._note_edit)
        self._content_layout.addWidget(note_box)

        self._content_layout.addWidget(self._status_segment(item.status))

        if lookup.parent is None:
            self._content_layout.addWidget(self._subtask_section(item))
        else:
            parent_box = QLabel(f"所属任务：{lookup.parent.title}")
            parent_box.setObjectName("ParentHint")
            parent_box.setWordWrap(True)
            self._content_layout.addWidget(parent_box)

        self._content_layout.addStretch()
        self._apply_style()
        self._scroll.verticalScrollBar().setValue(0)

    def _field_input(self, label: str, value: str) -> dict:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addWidget(self._field_label(label))
        edit = QLineEdit(value)
        layout.addWidget(edit)
        return {"container": box, "edit": edit}

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
        return label

    def _date_edit(self, value: str) -> QDateEdit:
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        parsed = QDate.fromString(value, "yyyy-MM-dd")
        edit.setDate(parsed if parsed.isValid() else QDate.currentDate())
        edit.setDisplayFormat("yyyy-MM-dd")
        return edit

    def _status_segment(self, current: str) -> QWidget:
        box = QWidget()
        box.setObjectName("SegmentedBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addWidget(self._field_label("状态"))
        segment = QWidget()
        segment.setObjectName("Segmented")
        segment_layout = QHBoxLayout(segment)
        segment_layout.setContentsMargins(4, 4, 4, 4)
        segment_layout.setSpacing(6)
        self._status_group = QButtonGroup(self)
        self._status_group.setExclusive(True)
        self._status_buttons = {}
        for status in VALID_STATUSES:
            btn = QPushButton(status)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setChecked(status == current)
            btn.setProperty("statusClass", status_class(status))
            self._status_group.addButton(btn)
            self._status_buttons[status] = btn
            segment_layout.addWidget(btn, stretch=1)
        layout.addWidget(segment)
        return box

    def _subtask_section(self, task) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        label = self._field_label("子任务")
        row.addWidget(label)
        row.addStretch()
        add_btn = QPushButton("+ 子任务")
        add_btn.setObjectName("AddSubtaskButton")
        add_btn.setToolTip("新增子任务")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_subtask.emit(task.id))
        row.addWidget(add_btn)
        layout.addLayout(row)

        self._subtask_status = {}
        list_box = QWidget()
        list_box.setObjectName("SubtaskList")
        list_layout = QVBoxLayout(list_box)
        list_layout.setContentsMargins(0, 0, 2, 0)
        list_layout.setSpacing(8)
        active_subtasks = [sub for sub in task.subtasks if not sub.deleted]
        if not active_subtasks:
            empty = QLabel("暂无子任务")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            list_layout.addWidget(empty)
        for subtask in active_subtasks:
            list_layout.addWidget(self._subtask_row(subtask))
        layout.addWidget(list_box)
        return box

    def _subtask_row(self, subtask) -> QWidget:
        row = QFrame()
        row.setObjectName("SubtaskRow")
        row.setProperty("statusClass", status_class(subtask.status))
        layout = QHBoxLayout(row)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(8)
        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        title = QLabel(subtask.title)
        title.setObjectName("SubtaskTitle")
        title.setFont(font_px(13, QFont.Weight.Bold))
        title.setWordWrap(False)
        title.setToolTip(subtask.title)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        text_box.addWidget(title)
        meta = QLabel(f"{subtask.start_date} - {subtask.end_date}")
        meta.setObjectName("SubtaskMeta")
        meta.setFont(font_px(FONT_SIZE_SM))
        text_box.addWidget(meta)
        layout.addLayout(text_box, stretch=1)

        combo = QComboBox()
        combo.setFixedSize(96, 28)
        combo.addItems(list(VALID_STATUSES))
        combo.setCurrentText(subtask.status)
        combo.currentTextChanged.connect(
            lambda value, widget=row, control=combo: self._refresh_subtask_row_status(widget, control, value)
        )
        self._subtask_status[subtask.id] = combo
        layout.addWidget(combo)
        self._style_subtask_row(row, subtask.status)
        self._style_subtask_combo(combo, subtask.status)
        return row

    def _refresh_subtask_row_status(self, row: QFrame, combo: QComboBox, status: str) -> None:
        row.setProperty("statusClass", status_class(status))
        self._style_subtask_row(row, status)
        self._style_subtask_combo(combo, status)

    def _style_subtask_row(self, row: QFrame, status: str) -> None:
        c = self._theme
        _, bg = get_status_colors(status, c, is_sub=True)
        row.setStyleSheet(f"""
            QFrame#SubtaskRow {{
                background: {c.BG_SUBTASK};
                color: {c.TEXT_ON_LIGHT};
                border: 1px solid {c.BORDER_STRONG};
                border-radius: {RADIUS_MD}px;
            }}
            QFrame#SubtaskRow QLabel#SubtaskTitle {{
                color: {c.TEXT_SOFT_ON_LIGHT if status_class(status) == "cancelled" else c.TEXT_ON_LIGHT};
                text-decoration: {"line-through" if status_class(status) == "cancelled" else "none"};
                background: transparent;
                border: none;
            }}
            QFrame#SubtaskRow QLabel#SubtaskMeta {{
                color: {c.TEXT_MUTED_ON_LIGHT};
                background: transparent;
                border: none;
            }}
        """)

    def _style_subtask_combo(self, combo: QComboBox, status: str) -> None:
        c = self._theme
        border, bg = get_status_colors(status, c, is_sub=True)
        cls = status_class(status)
        text_color = {
            "pending": c.TEXT_TERTIARY,
            "active": c.BLUE,
            "done": c.GREEN,
            "cancelled": c.TEXT_SOFT_ON_LIGHT,
        }.get(cls, c.TEXT_PRIMARY)
        combo.setStyleSheet(f"""
            QComboBox {{
                background: {bg};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 999px;
                padding: 0 8px;
                font-size: {FONT_SIZE_SM}px;
                font-weight: 700;
            }}
            QComboBox QAbstractItemView {{
                background: {c.BG_DROPDOWN};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER_STRONG};
                selection-background-color: {c.BLUE_SOFT};
            }}
        """)

    def _on_save(self) -> None:
        lookup = self._current_lookup
        if lookup is None or lookup.item is None:
            return
        item = lookup.item
        selected_status = next((status for status, btn in self._status_buttons.items() if btn.isChecked()), item.status)
        data = {
            "title": self._title_input["edit"].text().strip(),
            "start_date": self._start_edit.date().toString("yyyy-MM-dd"),
            "end_date": self._end_edit.date().toString("yyyy-MM-dd"),
            "status": selected_status,
            "background": self._note_edit.toPlainText(),
        }
        if lookup.parent is None:
            updated = self._controller.update_task(item.id, **data)
            for subtask_id, combo in self._subtask_status.items():
                current = next((sub for sub in item.subtasks if sub.id == subtask_id), None)
                if current is not None and current.status != combo.currentText():
                    self._controller.update_subtask(item.id, subtask_id, status=combo.currentText())
            self.task_saved.emit(updated.start_date, updated.id, updated.id)
            self.show_task(updated.id)
        else:
            updated = self._controller.update_subtask(lookup.parent.id, item.id, **data)
            parent = self._controller.get_task(lookup.parent.id)
            parent_date = parent.start_date if parent else updated.start_date
            self.task_saved.emit(parent_date, lookup.parent.id, updated.id)
            self.show_task(updated.id)

    def _on_delete(self) -> None:
        if self._selected_task_id:
            self.delete_task.emit(self._selected_task_id)

    def _set_footer_enabled(self, enabled: bool) -> None:
        self._save_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _apply_style(self) -> None:
        c = self._theme
        self.setStyleSheet(f"""
            DetailPanel#DetailPanel {{
                background: {c.BG_SURFACE};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
            }}
            QWidget#PanelHead {{
                border-bottom: 1px solid {c.BORDER};
                background: transparent;
            }}
            QWidget#DetailActions {{
                border-top: 1px solid {c.BORDER};
                background: transparent;
            }}
            QLabel {{
                color: {c.TEXT_PRIMARY};
                border: none;
                background: transparent;
            }}
            QLabel#EmptyState {{
                color: {c.TEXT_MUTED_ON_LIGHT};
                border: 1px dashed {c.BORDER_STRONG};
                border-radius: {RADIUS_MD}px;
                background: rgba(255,255,255,0.48);
                padding: 18px;
            }}
            QLabel#ParentHint {{
                color: {c.TEXT_LINK};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                background: {c.BG_SUBTASK};
                padding: 9px;
            }}
            QLineEdit, QDateEdit, QPlainTextEdit, QComboBox {{
                background: {c.BG_INPUT};
                color: {c.TEXT_ON_LIGHT};
                border: 1px solid {c.BORDER_STRONG};
                border-radius: {RADIUS_MD}px;
                padding: 0 10px;
                selection-background-color: {c.BLUE_SOFT};
                font-size: {FONT_SIZE_BASE}px;
            }}
            QLineEdit, QDateEdit {{
                min-height: 38px;
            }}
            QPlainTextEdit {{
                padding: 10px;
            }}
            QLineEdit:focus, QDateEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
                border-color: {c.BORDER_FOCUS};
            }}
            QWidget#Segmented {{
                background: rgba(255,255,255,0.45);
                border: 1px solid {c.BORDER_STRONG};
                border-radius: {RADIUS_MD}px;
            }}
            QWidget#Segmented QPushButton {{
                background: transparent;
                color: {c.TEXT_MUTED_ON_LIGHT};
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: {FONT_SIZE_SM}px;
                font-weight: 700;
            }}
            QWidget#Segmented QPushButton:checked {{
                color: {c.TEXT_ON_LIGHT};
                background: {c.BG_SURFACE_STRONG};
                border-color: {c.BORDER};
            }}
            QWidget#Segmented QPushButton[statusClass="pending"]:checked {{
                color: {c.TEXT_TERTIARY};
                background: {c.COLOR_PENDING_BG};
                border-color: {c.COLOR_PENDING};
            }}
            QWidget#Segmented QPushButton[statusClass="active"]:checked {{
                color: {c.BLUE};
                background: {c.BLUE_SOFT};
                border-color: {c.BLUE};
            }}
            QWidget#Segmented QPushButton[statusClass="done"]:checked {{
                color: {c.GREEN};
                background: {c.GREEN_SOFT};
                border-color: {c.GREEN};
            }}
            QWidget#Segmented QPushButton[statusClass="cancelled"]:checked {{
                color: {c.TEXT_SOFT_ON_LIGHT};
                background: {c.COLOR_CANCELLED_BG};
                border-color: {c.COLOR_CANCELLED};
                text-decoration: line-through;
            }}
            QPushButton {{
                min-height: 38px;
                padding: 0 14px;
                border-radius: {RADIUS_MD}px;
                border: 1px solid {c.BORDER_STRONG};
                background: {c.BG_BUTTON};
                color: {c.TEXT_PRIMARY};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {c.BG_BUTTON_HOVER};
                border-color: {c.BORDER_STRONG};
            }}
            QPushButton:disabled {{
                color: {c.TEXT_TERTIARY};
            }}
            QPushButton#AddSubtaskButton {{
                min-height: 32px;
                padding: 0 10px;
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
        self._title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        self._subtitle_label.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
        self._content.setStyleSheet("background: transparent; border: none;")
        self._delete_btn.setStyleSheet(f"""
            QPushButton {{
                color: {c.DANGER};
                background: {c.DANGER_SOFT};
                border: 1px solid rgba(224,88,88,0.24);
            }}
        """)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                color: #FFFFFF;
                background: {c.COLOR_PRIMARY_BTN};
                border: none;
            }}
            QPushButton:hover {{
                background: {c.COLOR_PRIMARY_BTN_HOVER};
            }}
        """)

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors
        self._apply_style()
        if self._selected_task_id:
            self.show_task(self._selected_task_id)
        elif self._selected_date:
            self.show_day(self._selected_date)

    @property
    def selected_date(self) -> str:
        return self._selected_date

    @property
    def selected_task_id(self) -> str | None:
        return self._selected_task_id
