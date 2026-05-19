"""D3 GUI 主应用：窗口组装 + 交互协调 + 主题管理。"""

from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QVBoxLayout, QWidget, QSizePolicy,
)

from todo_manager.gui.theme import Theme, LightColors, DarkColors, qcolor
from todo_manager.gui.theme import FONT_FAMILY, FONT_SIZE_BASE, RADIUS_LG
from todo_manager.gui.widgets.theme_toggle import ThemeToggle
from todo_manager.gui.widgets.search_bar import SearchBar
from todo_manager.gui.widgets.month_nav import MonthNav
from todo_manager.gui.widgets.calendar_grid import CalendarGrid
from todo_manager.gui.widgets.detail_panel import DetailPanel
from todo_manager.gui.widgets.dialogs import TaskDialog
from todo_manager.engine.task_manager import (
    create_task, update_task, delete_task, undo_task,
    create_subtask, update_subtask, delete_subtask, undo_subtask,
    get_task, get_subtask, list_all_tasks,
)
from todo_manager.engine.storage import clear_data_dir, set_data_dir


class TodoApp(QMainWindow):
    """Todo Manager 主窗口。"""

    def __init__(self, data_dir: str | None = None):
        super().__init__()
        self.setWindowTitle("Todo Manager")
        self.setMinimumSize(900, 600)
        self.resize(1280, 900)
        self._center_on_screen()

        # 初始化数据目录（None = 使用 storage 默认逻辑）
        if data_dir is not None:
            set_data_dir(data_dir)
        else:
            clear_data_dir()
        self._data_dir = data_dir

        # 主题状态
        self._theme_colors = LightColors
        self._current_theme = Theme.LIGHT
        self._deleted_cache = None  # 用于撤销删除

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._install_event_filter()
        self._apply_global_theme()

        # 初始显示今天
        today = date.today().isoformat()
        self._calendar.select_date(today)
        self._detail.show_day(today)

    def _center_on_screen(self):
        """将窗口移动到屏幕中央。"""
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(20, 12, 20, 12)
        root_layout.setSpacing(10)

        # ── 顶部栏 ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self._theme_toggle = ThemeToggle()
        top_bar.addWidget(self._theme_toggle)

        self._search_bar = SearchBar(theme_colors=self._theme_colors)
        top_bar.addWidget(self._search_bar, stretch=1)

        root_layout.addLayout(top_bar)

        # ── 年月导航 ──
        today = date.today()
        self._month_nav = MonthNav(
            year=today.year,
            month=today.month,
            theme_colors=self._theme_colors,
        )
        root_layout.addWidget(self._month_nav)

        # ── 日历 + 详情 (6:4 比例) ──
        self._calendar = CalendarGrid(theme_colors=self._theme_colors)
        self._calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(self._calendar, stretch=6)

        self._detail = DetailPanel(theme_colors=self._theme_colors)
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(self._detail, stretch=4)

        # Toast 容器
        self._toast_container = QWidget(self)
        self._toast_layout = QVBoxLayout(self._toast_container)
        self._toast_layout.setContentsMargins(0, 0, 0, 0)
        self._toast_layout.setSpacing(8)
        self._toast_container.hide()

    def _connect_signals(self):
        # 主题切换
        self._theme_toggle.theme_changed.connect(self._on_theme_changed)

        # 年月导航
        self._month_nav.prev_month.connect(self._go_prev_month)
        self._month_nav.next_month.connect(self._go_next_month)
        self._month_nav.month_selected.connect(self._on_month_selected)
        self._month_nav.year_selected.connect(self._on_year_selected)

        # 搜索
        self._search_bar.result_selected.connect(self._on_search_result)

        # 日历
        self._calendar.cell_clicked.connect(self._on_cell_clicked)
        self._calendar.task_clicked.connect(self._on_task_clicked)
        self._calendar.task_edit.connect(self._on_edit_task)
        self._calendar.task_delete.connect(self._on_delete_task)
        self._calendar.task_add_subtask.connect(self._on_add_subtask)

        # 详情面板
        self._detail.create_task.connect(self._on_create_task)
        self._detail.edit_task.connect(self._on_edit_task)
        self._detail.delete_task.connect(self._on_delete_task)
        self._detail.add_subtask.connect(self._on_add_subtask)

    def _setup_shortcuts(self):
        # Ctrl+N
        sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        sc_new.activated.connect(lambda: self._on_create_task(self._detail.selected_date))

        # Ctrl+F
        sc_find = QShortcut(QKeySequence("Ctrl+F"), self)
        sc_find.activated.connect(self._search_bar.focus_input)

        # Delete
        sc_del = QShortcut(QKeySequence("Delete"), self)
        sc_del.activated.connect(self._on_delete_shortcut)

        # Ctrl+E
        sc_edit = QShortcut(QKeySequence("Ctrl+E"), self)
        sc_edit.activated.connect(self._on_edit_shortcut)

        # ← — only when search input is NOT focused
        sc_left = QShortcut(QKeySequence("Left"), self)
        sc_left.activated.connect(self._on_left_arrow)

        # → — only when search input is NOT focused
        sc_right = QShortcut(QKeySequence("Right"), self)
        sc_right.activated.connect(self._on_right_arrow)

        # Esc
        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self._search_bar.hide_dropdown)

        # F5 — 刷新数据
        sc_refresh = QShortcut(QKeySequence("F5"), self)
        sc_refresh.activated.connect(self._on_refresh)

    def _install_event_filter(self):
        self.centralWidget().installEventFilter(self)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseButtonPress:
            if self._search_bar.is_dropdown_visible():
                click_global = event.globalPosition().toPoint()
                # Search bar area (keep open)
                sr = self._search_bar.rect()
                stl = self._search_bar.mapToGlobal(sr.topLeft())
                sbr = self._search_bar.mapToGlobal(sr.bottomRight())
                in_search = (stl.x() <= click_global.x() <= sbr.x() and
                             stl.y() <= click_global.y() <= sbr.y())
                # Dropdown area (keep open — click on item handled by QListWidget)
                dr = self._search_bar.dropdown_global_rect()
                in_dropdown = dr is not None and dr.contains(click_global)
                if not in_search and not in_dropdown:
                    self._search_bar.hide_dropdown()
        return super().eventFilter(obj, event)

    # ── 主题 ─────────────────────────────────────────────

    def _on_theme_changed(self):
        if self._theme_toggle.theme == Theme.DARK:
            self._theme_colors = DarkColors
        else:
            self._theme_colors = LightColors
        self._apply_global_theme()
        self._calendar.refresh_theme(self._theme_colors)
        self._detail.refresh_theme(self._theme_colors)
        self._search_bar.refresh_theme(self._theme_colors)
        self._month_nav.refresh_theme(self._theme_colors)

    def _apply_global_theme(self):
        c = self._theme_colors
        self.centralWidget().setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {c.BG_ROOT};
                color: {c.TEXT_PRIMARY};
                font-family: "PingFang SC","Microsoft YaHei",sans-serif;
                font-size: 14px;
            }}
        """)

    # ── 导航 ─────────────────────────────────────────────

    def _go_prev_month(self):
        m = self._calendar.month - 1
        y = self._calendar.year
        if m < 1:
            m = 12
            y -= 1
        if y < 2006:
            return
        self._calendar.navigate(y, m)
        self._month_nav.update_display(y, m)

    def _go_next_month(self):
        m = self._calendar.month + 1
        y = self._calendar.year
        if m > 12:
            m = 1
            y += 1
        if y > 2046:
            return
        self._calendar.navigate(y, m)
        self._month_nav.update_display(y, m)

    def _on_left_arrow(self):
        """← only navigates when search input is NOT focused."""
        widget = QApplication.focusWidget()
        if isinstance(widget, QLineEdit):
            return
        self._go_prev_month()

    def _on_right_arrow(self):
        """→ only navigates when search input is NOT focused."""
        widget = QApplication.focusWidget()
        if isinstance(widget, QLineEdit):
            return
        self._go_next_month()

    def _on_month_selected(self, m: int):
        self._calendar.navigate(self._calendar.year, m)
        self._month_nav.update_display(self._calendar.year, m)

    def _on_year_selected(self, y: int):
        self._calendar.navigate(y, self._calendar.month)
        self._month_nav.update_display(y, self._calendar.month)

    # ── 日历交互 ─────────────────────────────────────────

    def _on_cell_clicked(self, date_str: str):
        self._calendar.select_date(date_str)
        self._detail.show_day(date_str)
        self._search_bar.hide_dropdown()

    def _on_task_clicked(self, task_id: str, date_str: str):
        self._calendar.select_task(task_id, date_str)
        self._month_nav.update_display(self._calendar.year, self._calendar.month)
        self._detail._selected_date = date_str
        self._detail.show_task(task_id)
        self._search_bar.hide_dropdown()

    # ── 搜索 ─────────────────────────────────────────────

    def _on_search_result(self, task_id: str, start_date: str):
        # Navigate calendar to the task's start_date month
        self._calendar.select_task(task_id, start_date)
        self._month_nav.update_display(self._calendar.year, self._calendar.month)
        self._detail._selected_date = start_date
        # show_task handles both parent tasks (with subtasks) and subtasks (with parent)
        self._detail.show_task(task_id)

    # ── CRUD 操作 ────────────────────────────────────────

    def _on_create_task(self, default_date: str = ""):
        dlg = TaskDialog(TaskDialog.MODE_CREATE, theme_colors=self._theme_colors, parent=self)
        if default_date:
            dlg.set_default_date(default_date)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            data = dlg.get_form_data()
            try:
                task = create_task(**data)
                self._refresh_all(data["start_date"], task.id)
                self._show_toast(f'任务 "{task.title}" 创建成功')
            except ValueError as e:
                self._show_toast(f"错误: {e}")

    def _find_task_any(self, task_id: str):
        """查找任务（主任务或子任务），返回 (found, parent_or_None)。

        - 主任务: (task, None)
        - 子任务: (subtask, parent_task)
        - 不存在: (None, None)
        """
        t = get_task(task_id)
        if t:
            return (t, None)
        for parent in list_all_tasks(include_deleted=False):
            for s in parent.subtasks:
                if s.id == task_id and not s.deleted:
                    return (s, parent)
        return (None, None)

    def _on_edit_task(self, task_id: str):
        found, parent = self._find_task_any(task_id)
        if found is None:
            self._show_toast("任务不存在")
            return

        if parent is None:
            # 主任务
            dlg = TaskDialog(TaskDialog.MODE_EDIT, theme_colors=self._theme_colors, parent=self)
            dlg.set_task_data(found)
            if dlg.exec() == TaskDialog.DialogCode.Accepted:
                data = dlg.get_form_data()
                try:
                    updated = update_task(task_id, **data)
                    self._refresh_all(data["start_date"], task_id)
                    self._show_toast(f'任务 "{updated.title}" 已更新')
                except ValueError as e:
                    self._show_toast(f"错误: {e}")
        else:
            # 子任务
            dlg = TaskDialog(TaskDialog.MODE_EDIT, theme_colors=self._theme_colors, parent=self)
            dlg.set_parent_info(parent.title)
            dlg.set_task_data(found)
            if dlg.exec() == TaskDialog.DialogCode.Accepted:
                data = dlg.get_form_data()
                try:
                    updated = update_subtask(parent.id, task_id, **data)
                    self._refresh_all(data["start_date"], task_id)
                    self._show_toast(f'子任务 "{updated.title}" 已更新')
                except ValueError as ex:
                    self._show_toast(f"错误: {ex}")

    def _on_delete_task(self, task_id: str):
        found, parent = self._find_task_any(task_id)
        if found is None:
            return

        dlg = TaskDialog(TaskDialog.MODE_DELETE, theme_colors=self._theme_colors, parent=self)
        dlg.set_task_data(found)
        if dlg.exec() != TaskDialog.DialogCode.Accepted:
            return

        if parent is None:
            # 主任务
            title = found.title
            self._deleted_cache = ("task", task_id, None)
            delete_task(task_id)
            self._refresh_all(found.start_date, None)
            self._show_undo_toast(f'"{title}" 已删除')
        else:
            # 子任务
            title = found.title
            self._deleted_cache = ("subtask", task_id, parent.id)
            delete_subtask(parent.id, task_id)
            self._refresh_all(found.start_date, None)
            self._show_undo_toast(f'"{title}" 已删除')

    def _on_add_subtask(self, parent_id: str):
        parent = get_task(parent_id)
        if not parent:
            return
        dlg = TaskDialog(TaskDialog.MODE_SUBTASK, theme_colors=self._theme_colors, parent=self)
        dlg.set_parent_info(parent.title)
        dlg.set_default_date(self._detail.selected_date)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            data = dlg.get_form_data()
            try:
                sub = create_subtask(parent_id, **data)
                self._refresh_all(data["start_date"], sub.id)
                self._show_toast(f'子任务 "{sub.title}" 创建成功')
            except ValueError as e:
                self._show_toast(f"错误: {e}")

    def _on_delete_shortcut(self):
        task_id = self._detail.selected_task_id
        if task_id:
            self._on_delete_task(task_id)

    def _on_edit_shortcut(self):
        task_id = self._detail.selected_task_id
        if task_id:
            self._on_edit_task(task_id)

    # ── 撤销删除 ─────────────────────────────────────────

    def _undo_delete(self):
        if not self._deleted_cache:
            return
        cache_type, task_id, parent_id = self._deleted_cache
        self._deleted_cache = None
        if cache_type == "task":
            undo_task(task_id)
            t = get_task(task_id)
            if t:
                self._refresh_all(t.start_date, t.id)
                self._show_toast("已撤销删除")
        elif cache_type == "subtask":
            undo_subtask(parent_id, task_id)
            s = get_subtask(parent_id, task_id)
            if s:
                self._refresh_all(s.start_date, task_id)
                self._show_toast("已撤销删除")

    # ── 刷新 ─────────────────────────────────────────────

    def _on_refresh(self):
        """F5: 从磁盘重新加载数据并刷新日历和详情。"""
        self._search_bar.hide_dropdown()
        self._calendar.refresh()
        task_id = self._detail.selected_task_id
        if task_id:
            self._detail.show_task(task_id)
        else:
            self._detail.show_day(self._detail.selected_date)
        self._show_toast("数据已刷新")

    def _refresh_all(self, date_str: str, task_id: str | None):
        self._calendar.refresh()
        if task_id:
            self._detail.show_task(task_id)
        else:
            self._detail.show_day(date_str)

    # ── Toast ────────────────────────────────────────────

    def _show_toast(self, message: str):
        """显示普通 Toast 通知 — overlay 在主窗口底部中央。"""
        c = self._theme_colors
        toast = QLabel(message, self)
        toast.setStyleSheet(f"""
            QLabel {{
                background: {c.BG_TOAST};
                color: {c.TEXT_INVERSE};
                padding: 10px 20px;
                border-radius: {RADIUS_LG}px;
                font-size: {FONT_SIZE_BASE}px;
                font-weight: 500;
            }}
        """)
        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        y = self.height() - toast.height() - 40
        toast.move(x, y)
        toast.raise_()
        toast.show()
        QTimer.singleShot(4000, toast.deleteLater)

    def _show_undo_toast(self, message: str):
        """显示带撤销按钮的 Toast — overlay 在主窗口底部中央。"""
        c = self._theme_colors
        toast = QWidget(self)
        toast.setStyleSheet(f"""
            QWidget {{
                background: {c.BG_TOAST};
                border-radius: {RADIUS_LG}px;
            }}
        """)
        layout = QHBoxLayout(toast)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        label = QLabel(message)
        label.setStyleSheet(
            f"color: {c.TEXT_INVERSE}; font-size: {FONT_SIZE_BASE}px; "
            f"border: none; background: transparent;"
        )
        layout.addWidget(label)

        undo_btn = QPushButton("撤销")
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.setStyleSheet(
            f"color: #60A5FA; font-weight: bold; font-size: {FONT_SIZE_BASE}px; "
            f"border: none; background: transparent; padding: 2px 6px;"
        )
        undo_btn.clicked.connect(self._undo_delete)
        layout.addWidget(undo_btn)

        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        y = self.height() - toast.height() - 40
        toast.move(x, y)
        toast.raise_()
        toast.show()
        self._current_toast = toast
        QTimer.singleShot(5000, toast.deleteLater)


def run_app(data_dir: str | None = None):
    """启动 GUI 应用。data_dir=None 时使用 storage 默认路径。"""
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("Todo Manager")

    window = TodoApp(data_dir=data_dir)
    window.show()

    sys.exit(app.exec())
