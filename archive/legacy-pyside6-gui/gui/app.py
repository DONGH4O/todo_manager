"""Prototype-driven PySide6 GUI shell for Todo Manager."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from todo_manager.engine.storage import clear_data_dir, set_data_dir
from todo_manager.gui.controller import GuiController
from todo_manager.gui.icon import apply_app_icon
from todo_manager.gui.theme import (
    FONT_FAMILY_FALLBACK,
    FONT_SIZE_BASE,
    FONT_SIZE_LG,
    FONT_SIZE_SM,
    APP_MAX_WIDTH,
    DETAIL_WIDTH,
    RAIL_WIDTH,
    RADIUS_MD,
    TOPBAR_BRAND_WIDTH,
    Theme,
    ThemeSettings,
    colors_for_theme,
    font_px,
    resolve_theme,
)
from todo_manager.gui.widgets.calendar_grid import CalendarGrid
from todo_manager.gui.widgets.detail_panel import DetailPanel
from todo_manager.gui.widgets.dialogs import TaskDialog
from todo_manager.gui.widgets.month_nav import MAX_YEAR, MIN_YEAR, MonthNav
from todo_manager.gui.widgets.search_bar import SearchBar
from todo_manager.gui.widgets.theme_toggle import ThemeToggle
from todo_manager.gui.widgets.today_panel import TodayPanel


class TodoApp(QMainWindow):
    """Main window rebuilt to mirror docs/m4_uiux_redesign/prototype_v1.html."""

    def __init__(self, data_dir: str | None = None):
        super().__init__()
        self.setWindowTitle("Todo Manager")
        self.setMinimumSize(1180, 720)
        self.resize(1440, 900)
        self._center_on_screen()

        if data_dir is not None:
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            set_data_dir(data_dir)
        else:
            clear_data_dir()
        self._data_dir = data_dir
        self._controller = GuiController()

        settings_path = Path(data_dir) / "gui_settings.ini" if data_dir else None
        self._theme_settings = ThemeSettings(settings_path)
        self._theme_preference = self._theme_settings.load_theme()
        self._current_theme = resolve_theme(self._theme_preference)
        self._theme_colors = colors_for_theme(self._theme_preference)
        self._deleted_cache = None
        self._current_toast = None
        app = QApplication.instance()
        if app is not None:
            app.setFont(font_px(FONT_SIZE_BASE))
            apply_app_icon(app, self)

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._install_event_filter()
        self._apply_global_theme()

        today = date.today().isoformat()
        self._calendar.select_date(today)
        self._detail.show_day(today)
        self._refresh_today_panel()
        self._update_selected_text()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("AppRoot")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(0)

        self._app_frame = QWidget()
        self._app_frame.setObjectName("AppFrame")
        self._app_frame.setMaximumWidth(APP_MAX_WIDTH)
        self._app_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        app_layout = QVBoxLayout(self._app_frame)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(14)

        self._top_bar = QFrame()
        self._top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(self._top_bar)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.setSpacing(14)

        brand = QWidget()
        brand.setFixedWidth(TOPBAR_BRAND_WIDTH)
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        self._brand_mark = QLabel("T")
        self._brand_mark.setObjectName("BrandMark")
        self._brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._brand_mark.setFixedSize(34, 34)
        self._brand_mark.setFont(font_px(FONT_SIZE_LG, QFont.Weight.ExtraBold))
        brand_layout.addWidget(self._brand_mark)
        brand_copy = QWidget()
        brand_copy_layout = QVBoxLayout(brand_copy)
        brand_copy_layout.setContentsMargins(0, 0, 0, 0)
        brand_copy_layout.setSpacing(3)
        self._brand_title = QLabel("Todo Manager")
        self._brand_title.setFont(font_px(17, QFont.Weight.Bold))
        self._brand_slogan = QLabel("让每个待办都有清晰节奏")
        self._brand_slogan.setFont(font_px(FONT_SIZE_SM))
        brand_copy_layout.addWidget(self._brand_title)
        brand_copy_layout.addWidget(self._brand_slogan)
        brand_layout.addWidget(brand_copy, stretch=1)
        top_layout.addWidget(brand)

        self._search_bar = SearchBar(theme_colors=self._theme_colors, controller=self._controller)
        self._search_bar.setMinimumWidth(320)
        top_layout.addWidget(self._search_bar, stretch=1)

        self._today_btn = self._make_top_button("◎ 今天", "回到今天")
        self._refresh_btn = self._make_top_button("↻ 刷新", "刷新数据")
        self._top_new_btn = self._make_top_button("+ 新建", "新建任务", primary=True)
        self._theme_toggle = ThemeToggle(initial_theme=self._theme_preference)
        top_layout.addWidget(self._today_btn)
        top_layout.addWidget(self._refresh_btn)
        top_layout.addWidget(self._top_new_btn)
        top_layout.addWidget(self._theme_toggle)
        app_layout.addWidget(self._top_bar)

        self._workspace = QWidget()
        self._workspace.setObjectName("Workspace")
        self._workspace.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_layout = QHBoxLayout(self._workspace)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(14)

        self._today_panel = TodayPanel(theme_colors=self._theme_colors, controller=self._controller)
        self._today_panel.setFixedWidth(RAIL_WIDTH)
        body_layout.addWidget(self._today_panel)

        self._calendar_panel = QFrame()
        self._calendar_panel.setObjectName("CalendarPanel")
        calendar_layout = QVBoxLayout(self._calendar_panel)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        calendar_layout.setSpacing(0)

        calendar_head = QWidget()
        calendar_head.setObjectName("PanelHead")
        calendar_head_layout = QHBoxLayout(calendar_head)
        calendar_head_layout.setContentsMargins(14, 12, 14, 12)
        calendar_head_layout.setSpacing(12)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self._calendar_title = QLabel("月历工作台")
        self._calendar_title.setFont(font_px(FONT_SIZE_LG, QFont.Weight.Bold))
        self._selected_text = QLabel("选择日期查看任务")
        self._selected_text.setFont(font_px(FONT_SIZE_SM))
        title_box.addWidget(self._calendar_title)
        title_box.addWidget(self._selected_text)
        calendar_head_layout.addLayout(title_box)
        calendar_head_layout.addStretch()
        today = date.today()
        self._month_nav = MonthNav(today.year, today.month, theme_colors=self._theme_colors)
        calendar_head_layout.addWidget(self._month_nav)
        calendar_layout.addWidget(calendar_head)

        self._calendar = CalendarGrid(theme_colors=self._theme_colors, controller=self._controller)
        self._calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        calendar_layout.addWidget(self._calendar, stretch=1)
        body_layout.addWidget(self._calendar_panel, stretch=1)

        self._detail = DetailPanel(theme_colors=self._theme_colors, controller=self._controller)
        self._detail.setFixedWidth(DETAIL_WIDTH)
        self._detail.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        body_layout.addWidget(self._detail)

        app_layout.addWidget(self._workspace, stretch=1)
        root_layout.addWidget(self._app_frame, stretch=1, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._sync_app_frame_width()

    def _make_top_button(self, text: str, tooltip: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("TopButtonPrimary" if primary else "TopButton")
        btn.setFixedHeight(44)
        btn.setMinimumWidth(74 if not primary else 92)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _connect_signals(self) -> None:
        self._theme_toggle.theme_changed.connect(self._on_theme_changed)
        self._today_btn.clicked.connect(self._go_today)
        self._refresh_btn.clicked.connect(self._on_refresh)
        self._top_new_btn.clicked.connect(lambda: self._on_create_task(self._detail.selected_date))

        self._month_nav.prev_month.connect(self._go_prev_month)
        self._month_nav.next_month.connect(self._go_next_month)
        self._month_nav.month_selected.connect(self._on_month_selected)
        self._month_nav.year_selected.connect(self._on_year_selected)

        self._search_bar.result_selected.connect(self._on_search_result)
        self._today_panel.task_selected.connect(self._on_today_task_selected)
        self._today_panel.create_task.connect(self._on_create_task)

        self._calendar.cell_clicked.connect(self._on_cell_clicked)
        self._calendar.task_clicked.connect(self._on_task_clicked)
        self._calendar.task_edit.connect(self._on_edit_task)
        self._calendar.task_delete.connect(self._on_delete_task)
        self._calendar.task_add_subtask.connect(self._on_add_subtask)

        self._detail.create_task.connect(self._on_create_task)
        self._detail.edit_task.connect(self._on_edit_task)
        self._detail.delete_task.connect(self._on_delete_task)
        self._detail.add_subtask.connect(self._on_add_subtask)
        self._detail.task_saved.connect(self._on_detail_saved)

    def _setup_shortcuts(self) -> None:
        sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        sc_new.activated.connect(lambda: None if self._text_input_focused() else self._on_create_task(self._detail.selected_date))

        sc_find = QShortcut(QKeySequence("Ctrl+F"), self)
        sc_find.activated.connect(self._search_bar.focus_input)

        sc_del = QShortcut(QKeySequence("Delete"), self)
        sc_del.activated.connect(self._on_delete_shortcut)

        sc_edit = QShortcut(QKeySequence("Ctrl+E"), self)
        sc_edit.activated.connect(self._on_edit_shortcut)

        sc_left = QShortcut(QKeySequence("Left"), self)
        sc_left.activated.connect(self._on_left_arrow)

        sc_right = QShortcut(QKeySequence("Right"), self)
        sc_right.activated.connect(self._on_right_arrow)

        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self._search_bar.hide_dropdown)

        sc_refresh = QShortcut(QKeySequence("F5"), self)
        sc_refresh.activated.connect(self._on_refresh)

    def _install_event_filter(self) -> None:
        self.centralWidget().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and self._search_bar.is_dropdown_visible():
            click_global = event.globalPosition().toPoint()
            sr = self._search_bar.rect()
            stl = self._search_bar.mapToGlobal(sr.topLeft())
            sbr = self._search_bar.mapToGlobal(sr.bottomRight())
            in_search = stl.x() <= click_global.x() <= sbr.x() and stl.y() <= click_global.y() <= sbr.y()
            dr = self._search_bar.dropdown_global_rect()
            in_dropdown = dr is not None and dr.contains(click_global)
            if not in_search and not in_dropdown:
                self._search_bar.hide_dropdown()
        return super().eventFilter(obj, event)

    def _on_theme_changed(self) -> None:
        self._set_theme(self._theme_toggle.theme, persist=True)

    def _set_theme(self, theme: Theme, persist: bool = False) -> None:
        self._theme_preference = theme
        self._current_theme = resolve_theme(theme)
        self._theme_colors = colors_for_theme(theme)
        self._theme_toggle.set_theme(self._theme_preference, emit=False)
        self._theme_toggle.refresh_theme(self._theme_colors)
        if persist:
            self._theme_settings.save_theme(theme)
        self._apply_global_theme()
        self._calendar.refresh_theme(self._theme_colors)
        self._detail.refresh_theme(self._theme_colors)
        self._search_bar.refresh_theme(self._theme_colors)
        self._month_nav.refresh_theme(self._theme_colors)
        self._today_panel.refresh_theme(self._theme_colors)

    def _apply_global_theme(self) -> None:
        c = self._theme_colors
        self.centralWidget().setStyleSheet(f"""
            QWidget#AppRoot {{
                background: {c.BG_ROOT_GRADIENT};
                color: {c.TEXT_PRIMARY};
                font-family: {FONT_FAMILY_FALLBACK};
                font-size: {FONT_SIZE_BASE}px;
            }}
            QWidget#AppFrame {{
                background: transparent;
                border: none;
            }}
            QFrame#TopBar, QFrame#CalendarPanel {{
                background: {c.BG_SOFT};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
            }}
            QWidget#PanelHead {{
                background: transparent;
                border-bottom: 1px solid {c.BORDER};
            }}
            QLabel#BrandMark {{
                background: {c.COLOR_PRIMARY_BTN};
                color: #FFFFFF;
                border: none;
                border-radius: {RADIUS_MD}px;
            }}
            QPushButton#TopButton {{
                background: {c.BG_BUTTON};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                padding: 0 14px;
                font-weight: 600;
            }}
            QPushButton#TopButton:hover {{
                border-color: {c.BORDER_STRONG};
                background: {c.BG_BUTTON_HOVER};
            }}
            QPushButton#TopButtonPrimary {{
                background: {c.COLOR_PRIMARY_BTN};
                color: #FFFFFF;
                border: none;
                border-radius: {RADIUS_MD}px;
                padding: 0 16px;
                font-weight: 700;
            }}
            QPushButton#TopButtonPrimary:hover {{
                background: {c.COLOR_PRIMARY_BTN_HOVER};
            }}
        """)
        self._brand_title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        self._brand_slogan.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")
        self._calendar_title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; background: transparent;")
        self._selected_text.setStyleSheet(f"color: {c.TEXT_TERTIARY}; border: none; background: transparent;")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_app_frame_width()

    def _sync_app_frame_width(self) -> None:
        if not hasattr(self, "_app_frame") or self.centralWidget() is None:
            return
        target = max(0, min(APP_MAX_WIDTH, self.centralWidget().width() - 36))
        if target > 0 and self._app_frame.width() != target:
            self._app_frame.setFixedWidth(target)

    def _go_prev_month(self) -> None:
        month = self._calendar.month - 1
        year = self._calendar.year
        if month < 1:
            month = 12
            year -= 1
        if year < MIN_YEAR:
            return
        self._calendar.navigate(year, month)
        self._month_nav.update_display(year, month)
        self._refresh_today_panel()
        self._update_selected_text()

    def _go_next_month(self) -> None:
        month = self._calendar.month + 1
        year = self._calendar.year
        if month > 12:
            month = 1
            year += 1
        if year > MAX_YEAR:
            return
        self._calendar.navigate(year, month)
        self._month_nav.update_display(year, month)
        self._refresh_today_panel()
        self._update_selected_text()

    def _go_today(self) -> None:
        today = date.today()
        today_str = today.isoformat()
        self._calendar.navigate(today.year, today.month)
        self._month_nav.update_display(today.year, today.month)
        self._calendar.select_date(today_str)
        self._detail.show_day(today_str)
        self._refresh_today_panel()
        self._update_selected_text()
        self._search_bar.hide_dropdown()

    def _on_left_arrow(self) -> None:
        if not self._text_input_focused():
            self._go_prev_month()

    def _on_right_arrow(self) -> None:
        if not self._text_input_focused():
            self._go_next_month()

    def _on_month_selected(self, month: int) -> None:
        self._calendar.navigate(self._calendar.year, month)
        self._month_nav.update_display(self._calendar.year, month)
        self._refresh_today_panel()
        self._update_selected_text()

    def _on_year_selected(self, year: int) -> None:
        self._calendar.navigate(year, self._calendar.month)
        self._month_nav.update_display(year, self._calendar.month)
        self._refresh_today_panel()
        self._update_selected_text()

    def _on_cell_clicked(self, date_str: str) -> None:
        self._calendar.select_date(date_str)
        self._detail.show_day(date_str)
        self._refresh_today_panel()
        self._update_selected_text()
        self._search_bar.hide_dropdown()

    def _on_task_clicked(self, task_id: str, date_str: str) -> None:
        self._calendar.select_task(task_id, date_str)
        self._month_nav.update_display(self._calendar.year, self._calendar.month)
        self._detail.show_task(task_id)
        self._refresh_today_panel(task_id)
        self._update_selected_text()
        self._search_bar.hide_dropdown()

    def _on_today_task_selected(self, task_id: str, date_str: str) -> None:
        self._on_task_clicked(task_id, date_str)

    def _on_search_result(
        self,
        task_id: str,
        start_date: str,
        is_sub: bool = False,
        parent_id: str | None = None,
        parent_start_date: str | None = None,
    ) -> None:
        calendar_date = parent_start_date if is_sub and parent_start_date else start_date
        calendar_task_id = parent_id if is_sub and parent_id else task_id
        self._calendar.select_task(calendar_task_id, calendar_date)
        self._month_nav.update_display(self._calendar.year, self._calendar.month)
        self._detail.show_task(task_id)
        self._refresh_today_panel(calendar_task_id)
        self._update_selected_text()

    def _on_create_task(self, default_date: str = "") -> None:
        dlg = TaskDialog(TaskDialog.MODE_CREATE, theme_colors=self._theme_colors, parent=self)
        if default_date:
            dlg.set_default_date(default_date)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            data = dlg.get_form_data()
            try:
                task = self._controller.create_task(**data)
                self._refresh_all(task.start_date, task.id)
                self._show_toast(f'任务 "{task.title}" 创建成功')
            except ValueError as exc:
                self._show_toast(f"错误: {exc}")

    def _on_edit_task(self, task_id: str) -> None:
        self._detail.show_task(task_id)

    def _on_delete_task(self, task_id: str) -> None:
        found = self._controller.find_task_any(task_id)
        if found.item is None:
            return

        dlg = TaskDialog(TaskDialog.MODE_DELETE, theme_colors=self._theme_colors, parent=self)
        dlg.set_task_data(found.item)
        if dlg.exec() != TaskDialog.DialogCode.Accepted:
            return

        if found.parent is None:
            title = found.item.title
            self._deleted_cache = ("task", task_id, None)
            self._controller.delete_task(task_id)
            self._refresh_all(found.item.start_date, None)
            self._show_undo_toast(f'"{title}" 已删除')
        else:
            title = found.item.title
            self._deleted_cache = ("subtask", task_id, found.parent.id)
            self._controller.delete_subtask(found.parent.id, task_id)
            self._refresh_all(found.parent.start_date, found.parent.id)
            self._show_undo_toast(f'"{title}" 已删除')

    def _on_add_subtask(self, parent_id: str) -> None:
        parent = self._controller.get_task(parent_id)
        if not parent:
            return
        dlg = TaskDialog(TaskDialog.MODE_SUBTASK, theme_colors=self._theme_colors, parent=self)
        dlg.set_parent_info(parent.title)
        dlg.set_default_date(self._detail.selected_date)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            data = dlg.get_form_data()
            try:
                subtask = self._controller.create_subtask(parent_id, **data)
                self._refresh_all(parent.start_date, parent.id, subtask.id)
                self._show_toast(f'子任务 "{subtask.title}" 创建成功')
            except ValueError as exc:
                self._show_toast(f"错误: {exc}")

    def _on_delete_shortcut(self) -> None:
        if self._text_input_focused():
            return
        task_id = self._detail.selected_task_id
        if task_id:
            self._on_delete_task(task_id)

    def _on_edit_shortcut(self) -> None:
        if self._text_input_focused():
            return
        task_id = self._detail.selected_task_id
        if task_id:
            self._on_edit_task(task_id)

    def _undo_delete(self) -> None:
        if not self._deleted_cache:
            return
        cache_type, task_id, parent_id = self._deleted_cache
        self._deleted_cache = None
        if self._current_toast is not None:
            self._current_toast.deleteLater()
            self._current_toast = None

        if cache_type == "task":
            self._controller.undo_task(task_id)
            task = self._controller.get_task(task_id)
            if task:
                self._refresh_all(task.start_date, task.id)
                self._show_toast("已撤销删除")
        elif cache_type == "subtask":
            self._controller.undo_subtask(parent_id, task_id)
            parent = self._controller.get_task(parent_id)
            subtask = self._controller.get_subtask(parent_id, task_id)
            if parent and subtask:
                self._refresh_all(parent.start_date, parent.id, task_id)
                self._show_toast("已撤销删除")

    def _on_refresh(self) -> None:
        self._search_bar.hide_dropdown()
        task_id = self._detail.selected_task_id
        if task_id:
            found = self._controller.find_task_any(task_id)
            if found.item and found.parent:
                self._refresh_all(found.parent.start_date, found.parent.id, task_id)
            elif found.item:
                self._refresh_all(found.item.start_date, task_id)
            else:
                self._refresh_all(self._detail.selected_date, None)
        else:
            self._refresh_all(self._detail.selected_date, None)
        self._show_toast("数据已刷新")

    def _on_detail_saved(self, date_str: str, calendar_task_id, detail_task_id) -> None:
        self._refresh_all(
            str(date_str),
            str(calendar_task_id) if calendar_task_id else None,
            str(detail_task_id) if detail_task_id else None,
        )
        self._show_toast("修改已保存")

    def _refresh_all(
        self,
        date_str: str,
        calendar_task_id: str | None,
        detail_task_id: str | None = None,
    ) -> None:
        self._calendar.refresh()
        if calendar_task_id:
            self._calendar.select_task(calendar_task_id, date_str)
            self._month_nav.update_display(self._calendar.year, self._calendar.month)
        else:
            self._calendar.select_date(date_str)

        if detail_task_id or calendar_task_id:
            self._detail.show_task(detail_task_id or calendar_task_id)
        else:
            self._detail.show_day(date_str)
        self._refresh_today_panel(calendar_task_id)
        self._update_selected_text()

    def _refresh_today_panel(self, selected_task_id: str | None = None) -> None:
        self._today_panel.refresh(
            self._calendar.selected_date,
            self._calendar.year,
            self._calendar.month,
            selected_task_id,
        )

    def _update_selected_text(self) -> None:
        self._selected_text.setText(f"{self._calendar.selected_date} · 选择日期查看任务")
        self._search_bar.set_context_date(self._calendar.selected_date)

    def _show_toast(self, message: str) -> None:
        c = self._theme_colors
        toast = QLabel(message, self)
        toast.setStyleSheet(f"""
            QLabel {{
                background: {c.BG_TOAST};
                color: {c.TEXT_INVERSE};
                padding: 10px 20px;
                border-radius: {RADIUS_MD}px;
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

    def _show_undo_toast(self, message: str) -> None:
        c = self._theme_colors
        toast = QWidget(self)
        toast.setStyleSheet(f"QWidget {{ background: {c.BG_TOAST}; border-radius: {RADIUS_MD}px; }}")
        layout = QHBoxLayout(toast)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        label = QLabel(message)
        label.setStyleSheet(
            f"color: {c.TEXT_INVERSE}; font-size: {FONT_SIZE_BASE}px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(label)

        undo_btn = QPushButton("撤销")
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.setToolTip("撤销删除")
        undo_btn.setStyleSheet(
            f"color: {c.TEXT_LINK}; font-weight: bold; font-size: {FONT_SIZE_BASE}px; "
            "border: none; background: transparent; padding: 2px 6px;"
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

    @staticmethod
    def _text_input_focused() -> bool:
        widget = QApplication.focusWidget()
        return isinstance(
            widget,
            (QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox, QSpinBox),
        )


def run_app(data_dir: str | None = None):
    """Start the GUI application."""
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("Todo Manager")
    app.setOrganizationName("WorkBuddy")
    apply_app_icon(app)

    window = TodoApp(data_dir=data_dir)
    window.show()

    sys.exit(app.exec())
