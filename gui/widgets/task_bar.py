"""日历单元格内的任务条目条 (Task Bar)。

显示任务标题 + 状态颜色指示，鼠标悬停时浮现操作按钮。
"""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QWidget,
)

from todo_manager.gui.theme import (
    get_status_colors, qcolor, LightColors,
    FONT_FAMILY, FONT_SIZE_XS, FONT_SIZE_SM, RADIUS_SM,
)


class TaskBar(QFrame):
    """日历单元格中的单条任务 bar。"""

    clicked = Signal(str, str)  # task_id, date_str
    edit_requested = Signal(str)  # task_id
    delete_requested = Signal(str)  # task_id
    add_subtask_requested = Signal(str)  # parent_task_id

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

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 2, 6, 2)
        layout.setSpacing(4)

        # 子任务缩进标记
        if self._is_sub:
            self._indent_label = QLabel("└─")
            self._indent_label.setFont(QFont(FONT_FAMILY, 10))
            layout.addWidget(self._indent_label)
        else:
            self._indent_label = None

        # 标题 — 原型: task-bar font-size 11px, subtask 10px
        self._title_label = QLabel(self._title)
        title_size = 10 if self._is_sub else 11
        f = QFont(FONT_FAMILY, title_size)
        if self._is_sub:
            f.setItalic(True)
        self._title_label.setFont(f)
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._title_label, stretch=1)

        # 操作按钮区（默认隐藏）
        self._actions_widget = QWidget()
        actions_layout = QHBoxLayout(self._actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)

        # Design doc §4: task-bar-btn 20x20px, icons ✏️ / ❌ / ➕
        self._edit_btn = QPushButton("✏️")
        self._edit_btn.setFixedSize(20, 20)
        self._edit_btn.setToolTip("编辑")
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(self._on_edit)
        actions_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("❌")
        self._delete_btn.setFixedSize(20, 20)
        self._delete_btn.setToolTip("删除")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.clicked.connect(self._on_delete)
        actions_layout.addWidget(self._delete_btn)

        if not self._is_sub:
            self._add_btn = QPushButton("➕")
            self._add_btn.setFixedSize(20, 20)
            self._add_btn.setToolTip("新建子任务")
            self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._add_btn.clicked.connect(self._on_add_subtask)
            actions_layout.addWidget(self._add_btn)
        else:
            self._add_btn = None

        self._actions_widget.hide()
        layout.addWidget(self._actions_widget)

    def _apply_style(self):
        border_color, bg_color = get_status_colors(self._status, self._theme, self._is_sub)

        if self._status == "已取消":
            text_decoration = "line-through"
        else:
            text_decoration = "none"

        border_style = "dashed" if self._is_sub else "solid"
        margin_left = "14px" if self._is_sub else "0"

        self.setStyleSheet(f"""
            TaskBar {{
                background: {bg_color};
                border-left: 3px {border_style} {border_color};
                border-radius: 4px;
                margin-left: {margin_left};
                min-height: 20px;
            }}
            TaskBar:hover {{
                filter: brightness(0.93);
            }}
        """)

        # 按钮基础样式 — 原型: background rgba(255,255,255,0.7)
        btn_base = f"""
            QPushButton {{
                background: rgba(255,255,255,0.7); border: none;
                color: {self._theme.TEXT_SECONDARY};
                font-size: 9px; border-radius: 4px;
            }}
        """
        self._edit_btn.setStyleSheet(btn_base + f"""
            QPushButton:hover {{ background: {self._theme.BG_ACTIVE}; }}
        """)
        self._delete_btn.setStyleSheet(btn_base + f"""
            QPushButton:hover {{ background: {self._theme.COLOR_DANGER_BG}; color: {self._theme.COLOR_DANGER}; }}
        """)
        if self._add_btn:
            self._add_btn.setStyleSheet(btn_base + f"""
                QPushButton:hover {{ background: {self._theme.BG_TODAY}; color: {self._theme.COLOR_ACTIVE}; }}
            """)

        # Title label style
        cancelled_extra = f"color: {self._theme.TEXT_TERTIARY};" if self._status == "已取消" else ""
        self._title_label.setStyleSheet(f"""
            QLabel {{
                color: {self._theme.TEXT_PRIMARY};
                text-decoration: {text_decoration};
                {cancelled_extra}
                border: none; background: transparent;
            }}
        """)

        # 子任务缩进符颜色
        if self._indent_label:
            self._indent_label.setStyleSheet(
                f"color: {self._theme.TEXT_TERTIARY}; border: none; background: transparent;"
            )

    def refresh_theme(self, theme_colors):
        """主题切换时更新颜色。"""
        self._theme = theme_colors
        self._apply_style()

    def enterEvent(self, event):
        self._actions_widget.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._actions_widget.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._task_id, self._date_str)
            event.accept()  # 阻止事件冒泡到 CalendarCell
            return
        super().mousePressEvent(event)

    def _on_edit(self):
        self.edit_requested.emit(self._task_id)

    def _on_delete(self):
        self.delete_requested.emit(self._task_id)

    def _on_add_subtask(self):
        self.add_subtask_requested.emit(self._task_id)

    def set_highlighted(self, highlighted: bool):
        """设置高亮/选中状态。"""
        self._apply_style()
        if highlighted:
            self.setStyleSheet(self.styleSheet() + f"""
                TaskBar {{ border: 2px solid {self._theme.BORDER_FOCUS}; }}
            """)

    @property
    def task_id(self) -> str:
        return self._task_id
