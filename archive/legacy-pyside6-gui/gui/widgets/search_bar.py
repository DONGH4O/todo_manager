"""Prototype search bar and floating result panel."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from todo_manager.gui.controller import GuiController
from todo_manager.gui.theme import (
    FONT_SIZE_BASE,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    LightColors,
    RADIUS_MD,
    font_px,
    get_status_colors,
    qcolor,
    status_class,
)


class SearchBar(QWidget):
    result_selected = Signal(str, str, bool, object, object)
    overlay_toggled = Signal(bool)

    def __init__(self, theme_colors=None, controller: GuiController | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._controller = controller or GuiController()
        self._context_date = date.today().isoformat()
        self._debounce_timer = QTimer(singleShot=True, interval=180, timeout=self._do_search)
        self.setFixedHeight(44)
        self.setMinimumWidth(260)
        self._build_ui()
        self._create_dropdown()

    def _build_ui(self) -> None:
        self._input = QLineEdit(self)
        self._input.setPlaceholderText("搜索标题、备注、子任务、状态")
        self._input.setFont(font_px(FONT_SIZE_BASE))
        self._input.setFixedHeight(44)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._do_search)
        self._input.installEventFilter(self)

        self._search_btn = QPushButton("搜索", self)
        self._search_btn.setFixedSize(60, 36)
        self._search_btn.setToolTip("搜索")
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_btn.clicked.connect(self._do_search)
        self._apply_input_style()

    def _create_dropdown(self) -> None:
        self._dropdown = QListWidget()
        self._dropdown.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self._dropdown.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._dropdown.setSpacing(6)
        self._dropdown.setFont(font_px(FONT_SIZE_SM))
        self._dropdown.itemClicked.connect(self._on_item_clicked)

        shadow = QGraphicsDropShadowEffect(self._dropdown)
        shadow.setBlurRadius(42)
        shadow.setOffset(0, 18)
        shadow.setColor(qcolor("rgba(48,88,114,0.18)"))
        self._dropdown.setGraphicsEffect(shadow)
        self._apply_dropdown_style()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._input.setGeometry(0, 0, self.width(), 44)
        self._search_btn.move(max(0, self.width() - 64), 4)
        if self._dropdown.isVisible():
            self._show_dropdown(move_only=True)

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() in (QEvent.Type.FocusIn, QEvent.Type.MouseButtonPress):
            QTimer.singleShot(0, self._do_search)
        return super().eventFilter(obj, event)

    def _apply_input_style(self) -> None:
        c = self._theme
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {c.BG_INPUT};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                padding: 0 72px 0 14px;
                color: {c.TEXT_PRIMARY};
                font-size: {FONT_SIZE_BASE}px;
            }}
            QLineEdit:focus {{
                border-color: {c.BORDER_FOCUS};
            }}
        """)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c.BG_BUTTON};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                color: {c.TEXT_PRIMARY};
                font-size: {FONT_SIZE_BASE}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {c.BG_BUTTON_HOVER};
                border-color: {c.BORDER_STRONG};
            }}
        """)

    def _apply_dropdown_style(self) -> None:
        c = self._theme
        self._dropdown.setStyleSheet(f"""
            QListWidget {{
                background: {c.BG_DROPDOWN};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                color: {c.TEXT_PRIMARY};
                padding: 10px;
                outline: none;
            }}
            QListWidget::item {{
                border: none;
                padding: 0;
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
            QListWidget::item:hover {{
                background: {c.BLUE_SOFT};
                border-radius: {RADIUS_MD}px;
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

    def set_context_date(self, date_str: str) -> None:
        self._context_date = date_str or date.today().isoformat()

    def _on_text_changed(self) -> None:
        self._debounce_timer.start()

    def _do_search(self) -> None:
        keyword = self._input.text().strip()
        if keyword:
            rows = self._search_parent_tasks(keyword)
            self._populate_results(rows, f"找到 {len(rows)} 个结果", "标题 / 备注 / 子任务 / 状态 / 日期")
        else:
            rows = self._tasks_for_context_date()
            label = "今日任务列表" if self._context_date == date.today().isoformat() else f"{self._context_date} 任务列表"
            self._populate_results(rows, label, "标题 / 备注 / 状态 / 日期")

    def _tasks_for_context_date(self) -> list[dict]:
        return [self._task_to_row(task) for task in self._controller.get_tasks_for_date(self._context_date)]

    def _search_parent_tasks(self, keyword: str) -> list[dict]:
        kw = keyword.lower()
        rows: list[dict] = []
        for task in self._controller.list_all_tasks(include_deleted=False):
            fields = [
                task.title,
                task.background or "",
                task.status,
                task.start_date,
                task.end_date,
            ]
            fields.extend(
                f"{sub.title} {sub.background or ''} {sub.status} {sub.start_date} {sub.end_date}"
                for sub in task.subtasks
                if not sub.deleted
            )
            if any(kw in str(field).lower() for field in fields):
                rows.append(self._task_to_row(task))
        rows.sort(key=lambda item: item["created_at"])
        return rows[:50]

    @staticmethod
    def _task_to_row(task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "start_date": task.start_date,
            "end_date": task.end_date,
            "status": task.status,
            "background": task.background or "",
            "created_at": task.created_at,
        }

    def _populate_results(self, rows: list[dict], summary: str, fields: str) -> None:
        self._dropdown.clear()
        self._add_summary(summary, fields)
        if not rows:
            empty = QListWidgetItem()
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            empty.setSizeHint(QSize(100, 58))
            box = QLabel("没有找到匹配任务。")
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setStyleSheet(f"""
                QLabel {{
                    color: {self._theme.TEXT_MUTED_ON_LIGHT};
                    border: 1px dashed {self._theme.BORDER_STRONG};
                    border-radius: {RADIUS_MD}px;
                    background: rgba(255,255,255,0.48);
                    padding: 14px;
                    font-size: {FONT_SIZE_BASE}px;
                }}
            """)
            self._dropdown.addItem(empty)
            self._dropdown.setItemWidget(empty, box)
            self._show_dropdown()
            return

        for row in rows:
            self._add_result(row)
        self._show_dropdown()

    def _add_summary(self, summary: str, fields: str) -> None:
        item = QListWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setSizeHint(QSize(100, 28))
        box = QWidget()
        box.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(box)
        layout.setContentsMargins(10, 4, 10, 0)
        layout.setSpacing(12)
        left = QLabel(summary)
        right = QLabel(fields)
        for label in (left, right):
            label.setFont(font_px(FONT_SIZE_SM))
            label.setStyleSheet(f"color: {self._theme.TEXT_TERTIARY}; border: none; background: transparent;")
        right.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(left)
        layout.addStretch()
        layout.addWidget(right)
        self._dropdown.addItem(item)
        self._dropdown.setItemWidget(item, box)

    def _add_result(self, row: dict) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, (row["id"], row["start_date"], False, None, None))
        item.setSizeHint(QSize(100, 72))

        box = QWidget()
        box.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        title = QLabel(row["title"])
        title.setFont(font_px(13, QFont.Weight.Bold))
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        title.setStyleSheet(f"color: {self._theme.TEXT_PRIMARY}; border: none; background: transparent;")
        title.setToolTip(row["title"])
        date_range = QLabel(f'{row["start_date"]} - {row["end_date"]}')
        note = QLabel(self._trim(row["background"], 58))
        for label in (date_range, note):
            label.setFont(font_px(FONT_SIZE_SM))
            label.setStyleSheet(
                f"color: {self._theme.TEXT_TERTIARY}; border: none; background: transparent; line-height: 1.45;"
            )
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        text_box.addWidget(title)
        text_box.addWidget(date_range)
        text_box.addWidget(note)
        layout.addLayout(text_box, stretch=1)
        layout.addWidget(self._status_badge(row["status"]))

        box.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-radius: {RADIUS_MD}px;
            }}
            QWidget:hover {{
                background: {self._theme.BLUE_SOFT};
            }}
        """)
        self._dropdown.addItem(item)
        self._dropdown.setItemWidget(item, box)

    def _status_badge(self, status: str) -> QLabel:
        border, bg = get_status_colors(status, self._theme)
        cls = status_class(status)
        text_color = {
            "pending": self._theme.TEXT_TERTIARY,
            "active": self._theme.BLUE,
            "done": self._theme.GREEN,
            "cancelled": self._theme.TEXT_SOFT_ON_LIGHT,
        }.get(cls, self._theme.TEXT_TERTIARY)
        badge = QLabel(status)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedHeight(24)
        badge.setMinimumWidth(58)
        badge.setFont(font_px(FONT_SIZE_SM, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background: {bg};
                border: 1px solid {border};
                border-radius: 999px;
                padding: 2px 9px;
                text-decoration: {"line-through" if cls == "cancelled" else "none"};
            }}
        """)
        return badge

    @staticmethod
    def _trim(text: str, limit: int) -> str:
        clean = (text or "").strip()
        if not clean:
            return "暂无备注"
        return clean if len(clean) <= limit else clean[:limit] + "…"

    def _show_dropdown(self, move_only: bool = False) -> None:
        self._dropdown.setFixedWidth(max(260, self.width()))
        target_pos = self._dropdown_position()
        height = self._dropdown_height(target_pos)
        self._dropdown.setFixedHeight(height)
        self._dropdown.move(target_pos)
        if move_only:
            return
        if not self._dropdown.isVisible():
            self._dropdown.show()
        self._input.setFocus()
        self.overlay_toggled.emit(True)

    def _dropdown_position(self) -> QPoint:
        return self.mapToGlobal(QPoint(0, 52))

    def _dropdown_height(self, target_pos: QPoint) -> int:
        screen = QApplication.screenAt(target_pos) or QApplication.primaryScreen()
        if screen is None:
            return 560
        available = screen.availableGeometry()
        return max(120, min(560, available.bottom() - target_pos.y() - 8))

    def _hide_dropdown(self) -> None:
        self._dropdown.hide()
        self.overlay_toggled.emit(False)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and len(data) >= 2:
            self._input.blockSignals(True)
            self._input.clear()
            self._input.blockSignals(False)
            self._hide_dropdown()
            self.result_selected.emit(data[0], data[1], False, None, None)

    def focus_input(self) -> None:
        self._input.setFocus()
        self._input.selectAll()
        self._do_search()

    def hide_dropdown(self) -> None:
        self._hide_dropdown()

    def is_dropdown_visible(self) -> bool:
        return self._dropdown.isVisible()

    def dropdown_global_rect(self) -> QRect:
        r = self._dropdown.rect()
        return QRect(self._dropdown.mapToGlobal(r.topLeft()), self._dropdown.mapToGlobal(r.bottomRight()))

    def refresh_theme(self, theme_colors) -> None:
        self._theme = theme_colors or LightColors
        self._apply_input_style()
        self._apply_dropdown_style()
