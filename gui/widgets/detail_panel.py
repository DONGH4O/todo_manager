"""详情面板 — 展示选中日期/任务的详细信息。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget, QSpacerItem,
)

from todo_manager.gui.theme import (
    get_status_colors, LightColors,
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XS, FONT_SIZE_LG, FONT_SIZE_BASE,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    qcolor,
)
from todo_manager.engine.task_manager import get_tasks_for_date, get_task, get_subtask, list_all_tasks


class DetailPanel(QWidget):
    """详情面板：日历下方 40% 区域。"""

    create_task = Signal(str)        # default_date
    edit_task = Signal(str)          # task_id
    delete_task = Signal(str)        # task_id
    add_subtask = Signal(str)        # parent_task_id

    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._selected_date = ""
        self._selected_task_id = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        self._title_label = QLabel("任务详情")
        self._title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LG, QFont.Weight.Bold))
        title_layout.addWidget(self._title_label)
        self._subtitle_label = QLabel()
        self._subtitle_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
        title_layout.addWidget(self._subtitle_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        self._new_btn = QPushButton("＋ 新建")
        # 设计文档: small(12px) + 600 weight
        self._new_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM, QFont.Weight.Bold))
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.clicked.connect(self._on_new)
        header_layout.addWidget(self._new_btn)

        layout.addWidget(header)

        # 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # 滚动内容区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(18, 14, 18, 14)
        self._content_layout.setSpacing(10)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll, stretch=1)

        self._apply_style()

    def _apply_style(self):
        c = self._theme
        self.setStyleSheet(f"""
            DetailPanel {{
                background: {c.BG_SURFACE};
                border-radius: {RADIUS_XL}px;
                border: 1px solid {c.BORDER};
            }}
        """)
        self._title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        self._subtitle_label.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
        self._new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c.COLOR_DANGER}; color: #FFF;
                border: none; border-radius: {RADIUS_MD}px;
                padding: 8px 22px;
            }}
            QPushButton:hover {{ background: {c.COLOR_DANGER_HOVER}; }}
        """)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ width: 4px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {c.SCROLLBAR_THUMB}; border-radius: 2px; }}
        """)
        self._content.setStyleSheet(f"background: transparent;")

    def show_day(self, date_str: str):
        """展示某日所有任务。"""
        self._selected_date = date_str
        self._selected_task_id = None
        tasks = get_tasks_for_date(date_str)

        self._title_label.setText("任务详情")
        self._subtitle_label.setText(f"{date_str} · {len(tasks)}条任务")

        self._clear_content()

        if not tasks:
            empty_label = QLabel(f"{date_str} 暂无任务\n\n点击右上角\"新建\"按钮创建任务")
            empty_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: {self._theme.TEXT_TERTIARY}; border: none;")
            self._content_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            for t in tasks:
                self._add_task_card(t, is_sub=False)
                for s in t.subtasks:
                    self._add_subtask_card(s, t.title)

        self._content_layout.addStretch()
        self._scroll.verticalScrollBar().setValue(0)

    def show_task(self, task_id: str):
        """展示任务详情 — 主任务时含子任务，子任务时含父任务。"""
        self._selected_task_id = task_id

        # 尝试作为主任务查找
        t = get_task(task_id)
        if t:
            self._title_label.setText("任务详情")
            self._subtitle_label.setText(self._selected_date)
            self._clear_content()
            # 展示主任务卡片
            self._add_task_card(t, is_sub=False)
            # 展示其下所有子任务
            for s in (t.subtasks or []):
                if not s.deleted:
                    self._add_subtask_card(s, t.title)
            self._content_layout.addStretch()
            self._scroll.verticalScrollBar().setValue(0)
            return

        # 尝试作为子任务查找 — 展示父任务 + 该子任务
        for parent in self._get_all_tasks():
            for s in (parent.subtasks or []):
                if s.id == task_id and not s.deleted:
                    self._title_label.setText("子任务详情")
                    self._subtitle_label.setText(self._selected_date)
                    self._clear_content()
                    # 先展示所属父任务卡片
                    self._add_task_card(parent, is_sub=False)
                    # 再展示该子任务
                    self._add_subtask_card(s, parent.title)
                    self._content_layout.addStretch()
                    self._scroll.verticalScrollBar().setValue(0)
                    return

    def _get_all_tasks(self):
        return list_all_tasks(include_deleted=False)

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self._content_layout.removeItem(item.spacerItem())

    def _add_task_card(self, task, is_sub: bool = False):
        """添加一个任务卡片。"""
        c = self._theme
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(7)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel(task.title)
        # 设计文档: sub-heading(16px) bold
        title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LG, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        title_row.addWidget(title_label)
        title_row.addStretch()

        # 操作按钮 — Design doc §4 icons
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_task.emit(task.id))
        title_row.addWidget(edit_btn)

        del_btn = QPushButton("❌")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_task.emit(task.id))
        title_row.addWidget(del_btn)

        if not is_sub:
            add_btn = QPushButton("➕")
            add_btn.setFixedSize(28, 28)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(lambda: self.add_subtask.emit(task.id))
            title_row.addWidget(add_btn)

        card_layout.addLayout(title_row)

        # 详细字段
        fields = [
            ("开始日期", task.start_date),
            ("截止日期", task.end_date),
            ("状态", task.status),
            ("背景", task.background or "—"),
        ]
        for label_text, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS, QFont.Weight.Bold))
            lbl.setFixedWidth(84)  # 容纳中文字段名
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            lbl.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
            row.addWidget(lbl)

            val = QLabel(value)
            val.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
            val.setWordWrap(True)
            val.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
            row.addWidget(val)
            card_layout.addLayout(row)

        # 状态 badge — 状态色左边框
        border_c, bg_c = get_status_colors(task.status, c, is_sub=False)
        card.setStyleSheet(f"""
            QFrame {{
                background: {c.BG_SURFACE_ALT};
                border: 1px solid {c.BORDER};
                border-left: 3px solid {border_c};
                border-radius: {RADIUS_LG}px;
            }}
            QFrame:hover {{ border-color: {c.BORDER_FOCUS}; }}
        """)

        # 按钮样式
        btn_base = f"""
            QPushButton {{
                background: {c.BG_SURFACE}; border: 1px solid {c.BORDER};
                border-radius: {RADIUS_SM}px; color: {c.TEXT_SECONDARY};
                font-size: 12px;
            }}
        """
        edit_btn.setStyleSheet(btn_base + f"QPushButton:hover {{ background: {c.BG_TODAY}; color: {c.COLOR_ACTIVE}; border-color: {c.COLOR_ACTIVE}; }}")
        del_btn.setStyleSheet(btn_base + f"QPushButton:hover {{ background: {c.COLOR_DANGER_BG}; color: {c.COLOR_DANGER}; border-color: {c.COLOR_DANGER}; }}")
        if not is_sub:
            add_btn.setStyleSheet(btn_base + f"QPushButton:hover {{ background: {c.BG_TODAY}; color: {c.COLOR_ACTIVE}; border-color: {c.COLOR_ACTIVE}; }}")

        self._content_layout.addWidget(card)

    def _add_subtask_card(self, subtask, parent_title: str):
        """添加子任务卡片。"""
        c = self._theme
        card = QFrame()

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(7)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel(subtask.title)
        # 设计文档: sub-heading(16px) bold + italic for subtasks
        f = QFont(FONT_FAMILY, FONT_SIZE_LG, QFont.Weight.Bold)
        f.setItalic(True)
        title_label.setFont(f)
        title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        title_row.addWidget(title_label)
        title_row.addStretch()

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_task.emit(subtask.id))
        title_row.addWidget(edit_btn)

        del_btn = QPushButton("❌")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_task.emit(subtask.id))
        title_row.addWidget(del_btn)

        card_layout.addLayout(title_row)

        # 字段
        fields = [
            ("开始日期", subtask.start_date),
            ("截止日期", subtask.end_date),
            ("状态", subtask.status),
            ("背景", subtask.background or "—"),
            ("所属任务", parent_title),
        ]
        for label_text, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS, QFont.Weight.Bold))
            lbl.setFixedWidth(84)  # 容纳中文字段名
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            lbl.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
            row.addWidget(lbl)

            val = QLabel(value)
            val.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
            val.setWordWrap(True)
            if label_text == "所属任务":
                val.setStyleSheet(f"color: {c.TEXT_LINK}; border: none; background: transparent;")
            else:
                val.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
            row.addWidget(val)
            card_layout.addLayout(row)

        border_c, bg_c = get_status_colors(subtask.status, c, is_sub=True)
        card.setStyleSheet(f"""
            QFrame {{
                background: {c.BG_SUBTASK};
                border: 1px solid {c.BORDER};
                border-left: 3px dashed {border_c};
                border-radius: {RADIUS_LG}px;
                margin-left: 24px;
            }}
            QFrame:hover {{ border-color: {c.BORDER_FOCUS}; }}
        """)

        btn_base = f"""
            QPushButton {{
                background: {c.BG_SURFACE}; border: 1px solid {c.BORDER};
                border-radius: {RADIUS_SM}px; color: {c.TEXT_SECONDARY};
                font-size: 12px;
            }}
        """
        edit_btn.setStyleSheet(btn_base + f"QPushButton:hover {{ background: {c.BG_TODAY}; color: {c.COLOR_ACTIVE}; border-color: {c.COLOR_ACTIVE}; }}")
        del_btn.setStyleSheet(btn_base + f"QPushButton:hover {{ background: {c.COLOR_DANGER_BG}; color: {c.COLOR_DANGER}; border-color: {c.COLOR_DANGER}; }}")

        self._content_layout.addWidget(card)

    def _on_new(self):
        self.create_task.emit(self._selected_date)

    def refresh_theme(self, theme_colors):
        self._theme = theme_colors
        self._apply_style()
        # 重新渲染内容
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
