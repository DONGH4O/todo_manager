"""弹窗组件：新建/编辑任务、新建/编辑子任务、删除确认。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QWidget, QDateEdit, QButtonGroup,
    QRadioButton, QSizePolicy, QFrame,
)
from PySide6.QtCore import QDate

from todo_manager.gui.theme import (
    LightColors,
    FONT_SIZE_BASE, FONT_SIZE_SM, FONT_SIZE_XS, FONT_SIZE_LG,
    RADIUS_MD, RADIUS_SM, RADIUS_XL, qcolor, font_px,
)
from todo_manager.engine.models import VALID_STATUSES


class TaskDialog(QDialog):
    """新建/编辑任务弹窗。"""

    MODE_CREATE = "create"
    MODE_EDIT = "edit"
    MODE_SUBTASK = "subtask"
    MODE_DELETE = "delete"

    def __init__(self, mode: str, theme_colors=None, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._theme = theme_colors or LightColors
        self._task_id = None
        self._parent_id = None
        self._parent_title = ""

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(440)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        c = self._theme
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 12)

        title_text = {
            self.MODE_CREATE: "新建任务",
            self.MODE_EDIT: "编辑任务",
            self.MODE_SUBTASK: "新建子任务",
            self.MODE_DELETE: "确认删除",
        }.get(self._mode, "新建任务")

        self._title_label = QLabel(title_text)
        # 设计文档: sub-heading(16px) bold
        self._title_label.setFont(font_px(FONT_SIZE_LG, QFont.Weight.Bold))
        header_layout.addWidget(self._title_label)

        self._parent_info_label = QLabel()
        self._parent_info_label.setFont(font_px(FONT_SIZE_XS))
        self._parent_info_label.hide()

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.reject)
        self._close_btn.setFlat(True)
        header_layout.addStretch()
        header_layout.addWidget(self._close_btn)

        self._main_layout.addWidget(header)

        # 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        self._main_layout.addWidget(sep)

        # 表单区
        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(20, 16, 20, 16)
        self._body_layout.setSpacing(14)

        if self._mode == self.MODE_DELETE:
            self._build_delete_body()
        else:
            self._build_form_body()

        self._main_layout.addWidget(self._body)

        # 错误提示
        self._error_label = QLabel()
        self._error_label.setFont(font_px(FONT_SIZE_XS))
        self._error_label.setStyleSheet(f"color: {c.COLOR_DANGER}; padding: 0 20px;")
        self._error_label.hide()
        self._main_layout.addWidget(self._error_label)

        # 按钮区
        self._footer = QWidget()
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(20, 12, 20, 16)
        footer_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        if self._mode == self.MODE_DELETE:
            self._confirm_btn = QPushButton("确认删除")
            self._confirm_btn.clicked.connect(self.accept)
        else:
            self._confirm_btn = QPushButton("保存")
            self._confirm_btn.clicked.connect(self._validate_and_accept)

        footer_layout.addWidget(self._confirm_btn)
        self._main_layout.addWidget(self._footer)

    def _build_form_body(self):
        c = self._theme

        # 标题
        self._body_layout.addWidget(QLabel("标题 *"))
        self._title_input = QLineEdit()
        self._title_input.setMaxLength(50)
        self._title_input.setPlaceholderText("输入任务标题")
        self._body_layout.addWidget(self._title_input)

        # 开始日期
        self._body_layout.addWidget(QLabel("开始日期"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._body_layout.addWidget(self._start_date)

        # 截止日期
        self._body_layout.addWidget(QLabel("截止日期"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._body_layout.addWidget(self._end_date)

        # 状态
        self._body_layout.addWidget(QLabel("状态"))
        self._status_group = QButtonGroup(self)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        self._status_buttons = {}
        for s in VALID_STATUSES:
            rb = QRadioButton(s)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            self._status_group.addButton(rb)
            status_layout.addWidget(rb)
            self._status_buttons[s] = rb
        # 默认选中"未启动"
        self._status_buttons["未启动"].setChecked(True)
        self._body_layout.addLayout(status_layout)

        # 背景
        self._body_layout.addWidget(QLabel("背景"))
        self._bg_input = QTextEdit()
        self._bg_input.setMaximumHeight(100)
        self._bg_input.setPlaceholderText("输入任务背景描述（不超过500字）")
        self._body_layout.addWidget(self._bg_input)

    def _build_delete_body(self):
        self._delete_text = QLabel()
        self._delete_text.setFont(font_px(FONT_SIZE_SM))
        self._delete_text.setWordWrap(True)
        self._body_layout.addWidget(self._delete_text)

        self._delete_sub_hint = QLabel()
        self._delete_sub_hint.setFont(font_px(FONT_SIZE_XS))
        self._delete_sub_hint.hide()
        self._body_layout.addWidget(self._delete_sub_hint)

    def _validate_and_accept(self):
        title = self._title_input.text().strip()
        if not title:
            self._error_label.setText("标题不能为空")
            self._error_label.show()
            return
        if self._start_date.date() > self._end_date.date():
            self._error_label.setText("截止日期不能早于开始日期")
            self._error_label.show()
            return
        self._error_label.hide()
        self.accept()

    def set_task_data(self, task):
        """预填编辑数据。"""
        if self._mode == self.MODE_DELETE:
            subtasks = getattr(task, "subtasks", None)
            if subtasks is None:
                self._delete_text.setText(f'确认删除子任务 "{task.title}"？')
                self._delete_sub_hint.hide()
                return

            sub_count = len([s for s in subtasks if not s.deleted])
            self._delete_text.setText(f'确认删除任务 "{task.title}"？')
            if sub_count > 0:
                self._delete_sub_hint.setText(f"⚠ 包含 {sub_count} 条子任务，将一并删除")
                self._delete_sub_hint.show()
            else:
                self._delete_sub_hint.hide()
            return

        self._title_input.setText(task.title)
        self._start_date.setDate(QDate.fromString(task.start_date, "yyyy-MM-dd"))
        self._end_date.setDate(QDate.fromString(task.end_date, "yyyy-MM-dd"))
        if task.status in self._status_buttons:
            self._status_buttons[task.status].setChecked(True)
        self._bg_input.setPlainText(task.background or "")

    def set_default_date(self, date_str: str):
        """设置默认日期。"""
        qd = QDate.fromString(date_str, "yyyy-MM-dd")
        if qd.isValid():
            if hasattr(self, '_start_date'):
                self._start_date.setDate(qd)
            if hasattr(self, '_end_date'):
                self._end_date.setDate(qd)

    def set_parent_info(self, parent_title: str):
        """设置所属任务信息（子任务模式）。"""
        self._parent_title = parent_title
        self._parent_info_label.setText(f"所属任务：{parent_title}")
        self._parent_info_label.show()

    def get_form_data(self) -> dict:
        """获取表单数据。"""
        if self._mode == self.MODE_DELETE:
            return {}
        status = "未启动"
        for s, rb in self._status_buttons.items():
            if rb.isChecked():
                status = s
                break
        return {
            "title": self._title_input.text().strip(),
            "start_date": self._start_date.date().toString("yyyy-MM-dd"),
            "end_date": self._end_date.date().toString("yyyy-MM-dd"),
            "status": status,
            "background": self._bg_input.toPlainText().strip(),
        }

    @property
    def mode(self) -> str:
        return self._mode

    def _apply_style(self):
        c = self._theme
        self.setStyleSheet(f"""
            TaskDialog {{
                background: {c.BG_MODAL};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_XL}px;
            }}
            QLabel {{
                color: {c.TEXT_PRIMARY}; background: transparent; border: none;
                font-size: {FONT_SIZE_XS}px; font-weight: 600;
            }}
            QLineEdit, QDateEdit, QTextEdit {{
                background: {c.BG_INPUT};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 9px 12px;
                color: {c.TEXT_PRIMARY};
                font-size: {FONT_SIZE_BASE}px;
            }}
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {{
                border-color: {c.BORDER_FOCUS};
            }}
            QRadioButton {{
                color: {c.TEXT_SECONDARY};
                font-size: {FONT_SIZE_XS}px; font-weight: 600;
                padding: 6px 14px;
                border: 1.5px solid {c.BORDER};
                border-radius: 20px;
            }}
            QRadioButton:checked {{
                color: {c.BORDER_FOCUS};
                border-color: {c.BORDER_FOCUS};
                background: {c.BG_TODAY};
            }}
            QFrame[frameShape="4"] {{ color: {c.BORDER}; }}
        """)

        # 按钮样式
        btn_cancel_style = f"""
            QPushButton {{
                background: {c.BG_SURFACE}; color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER}; border-radius: {RADIUS_MD}px;
                padding: 8px 20px; font-size: {FONT_SIZE_SM}px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {c.BG_HOVER}; }}
        """

        if self._mode == self.MODE_DELETE:
            confirm_style = f"""
                QPushButton {{
                    background: {c.COLOR_DANGER}; color: #FFF;
                    border: none; border-radius: {RADIUS_MD}px;
                    padding: 8px 20px; font-size: {FONT_SIZE_SM}px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {c.COLOR_DANGER_HOVER}; }}
            """
        else:
            confirm_style = f"""
                QPushButton {{
                    background: {c.COLOR_PRIMARY_BTN}; color: #FFF;
                    border: none; border-radius: {RADIUS_MD}px;
                    padding: 8px 20px; font-size: {FONT_SIZE_SM}px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {c.COLOR_PRIMARY_BTN_HOVER}; }}
            """

        # Apply button styles
        for child in self._footer.findChildren(QPushButton):
            if child is self._confirm_btn:
                child.setStyleSheet(confirm_style)
            else:
                child.setStyleSheet(btn_cancel_style)

        if self._mode == self.MODE_DELETE and hasattr(self, '_delete_sub_hint'):
            self._delete_sub_hint.setStyleSheet(f"color: {c.COLOR_DANGER}; border: none; background: transparent;")

        # Close button
        self._close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {c.TEXT_TERTIARY}; font-size: 16px; }}
            QPushButton:hover {{ background: {c.BG_HOVER}; border-radius: 8px; }}
        """)
