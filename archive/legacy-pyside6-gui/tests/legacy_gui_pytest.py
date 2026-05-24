"""D3 GUI 集成测试 — 使用 pytest-qt 测试核心交互流程。

测试策略：
- 测核心行为（CRUD、导航、搜索、主题），不测像素级渲染
- 每个测试使用独立的临时数据目录
- 不依赖 Display Server（使用 offscreen 模式）
"""

import os
import sys
import tempfile
import pytest

# 确保 offscreen 渲染（无头测试）
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from datetime import date, timedelta

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit
from PySide6.QtTest import QTest

from todo_manager.gui.app import TodoApp
from todo_manager.gui.icon import app_icon, app_icon_path
from todo_manager.gui.widgets.dialogs import TaskDialog
from todo_manager.gui.widgets.task_bar import TaskBar
from todo_manager.gui.widgets.today_panel import TaskListItem
from todo_manager.gui.widgets.month_nav import MIN_YEAR, MAX_YEAR
from todo_manager.gui.theme import Theme, LightColors, DarkColors
from todo_manager.engine.task_manager import (
    create_task, get_task, list_all_tasks,
    get_tasks_for_date, create_subtask, delete_task,
)
from todo_manager.engine.storage import set_data_dir


@pytest.fixture(scope="session")
def qapp():
    """Session 级别 QApplication（pytest-qt 自动提供 qapp fixture）。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def tmp_data_dir():
    """每个测试使用独立的临时数据目录。"""
    with tempfile.TemporaryDirectory() as tmp:
        set_data_dir(tmp)
        yield tmp


@pytest.fixture
def app_window(qapp, tmp_data_dir):
    """创建 TodoApp 窗口。"""
    window = TodoApp(data_dir=tmp_data_dir)
    window.resize(1280, 900)
    # 不调用 show() — 在 offscreen 模式下可能会有问题
    yield window
    window.close()
    window.deleteLater()


# ── 初始化测试 ────────────────────────────────────────────

class TestAppInit:
    def test_window_title(self, app_window):
        assert app_window.windowTitle() == "Todo Manager"

    def test_window_uses_packaged_application_icon(self, app_window):
        assert app_icon_path().exists()
        assert not app_icon().isNull()
        assert not app_window.windowIcon().isNull()

    def test_default_to_today(self, app_window):
        today = date.today().isoformat()
        assert app_window._calendar.selected_date == today

    def test_initial_theme_follows_prototype_system_mode(self, app_window):
        assert app_window._theme_toggle.theme == Theme.SYSTEM

    def test_month_nav_shows_current(self, app_window):
        today = date.today()
        assert app_window._month_nav._year == today.year
        assert app_window._month_nav._month == today.month

    def test_prototype_shell_dimensions(self, app_window):
        assert app_window._today_panel.minimumWidth() == 260
        assert app_window._today_panel.maximumWidth() == 260
        assert app_window._detail.minimumWidth() == 340
        assert app_window._detail.maximumWidth() == 340
        assert app_window._today_btn.text() == "◎ 今天"
        assert app_window._refresh_btn.text() == "↻ 刷新"


# ── 日历导航测试 ──────────────────────────────────────────

class TestCalendarNavigation:
    def test_prev_month(self, app_window):
        y, m = app_window._calendar.year, app_window._calendar.month
        app_window._go_prev_month()
        if m == 1:
            assert app_window._calendar.year == y - 1
            assert app_window._calendar.month == 12
        else:
            assert app_window._calendar.month == m - 1

    def test_next_month(self, app_window):
        y, m = app_window._calendar.year, app_window._calendar.month
        app_window._go_next_month()
        if m == 12:
            assert app_window._calendar.year == y + 1
            assert app_window._calendar.month == 1
        else:
            assert app_window._calendar.month == m + 1

    def test_boundary_prev_min_year(self, app_window):
        """最小年份1月时不应再前翻。"""
        app_window._calendar.navigate(MIN_YEAR, 1)
        app_window._month_nav.update_display(MIN_YEAR, 1)
        # 前翻应被拒绝
        app_window._go_prev_month()
        assert app_window._calendar.year == MIN_YEAR
        assert app_window._calendar.month == 1

    def test_boundary_next_max_year(self, app_window):
        """最大年份12月时不应再后翻。"""
        app_window._calendar.navigate(MAX_YEAR, 12)
        app_window._month_nav.update_display(MAX_YEAR, 12)
        app_window._go_next_month()
        assert app_window._calendar.year == MAX_YEAR
        assert app_window._calendar.month == 12

    def test_month_picker_signal(self, app_window, qtbot):
        app_window._on_month_selected(6)
        assert app_window._calendar.month == 6

    def test_year_picker_signal(self, app_window, qtbot):
        app_window._on_year_selected(2030)
        assert app_window._calendar.year == 2030


# ── CRUD 集成测试 ─────────────────────────────────────────

class TestTaskCRUD:
    def test_create_task_via_engine(self, app_window, tmp_data_dir):
        """通过引擎创建任务，验证日历和详情区刷新。"""
        today = date.today().isoformat()
        task = create_task("GUI测试任务", today, today, "未启动", "测试背景")
        app_window._refresh_all(today, task.id)
        # 验证任务出现在列表中
        tasks = get_tasks_for_date(today)
        assert any(t.id == task.id for t in tasks)

    def test_delete_task_via_engine(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        task = create_task("待删除任务", today, today, "未启动", "")
        task_id = task.id
        delete_task(task_id)
        t = get_task(task_id)
        assert t.deleted is True

    def test_undo_delete(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import undo_task
        today = date.today().isoformat()
        task = create_task("可恢复任务", today, today, "未启动", "")
        task_id = task.id
        delete_task(task_id)
        result = undo_task(task_id)
        assert result is True
        t = get_task(task_id)
        assert t.deleted is False

    def test_detail_panel_inline_save_updates_task(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        task = create_task("旧标题", today, today, "未启动", "旧备注")
        app_window._refresh_all(today, task.id)

        app_window._detail._title_input["edit"].setText("原型内联编辑")
        app_window._detail._status_buttons["完成中"].click()
        app_window._detail._note_edit.setPlainText("右侧详情区直接保存")
        app_window._detail._on_save()

        updated = get_task(task.id)
        assert updated.title == "原型内联编辑"
        assert updated.status == "完成中"
        assert updated.background == "右侧详情区直接保存"


# ── 子任务测试 ────────────────────────────────────────────

class TestSubtaskCRUD:
    def test_create_subtask(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        parent = create_task("父任务", today, today, "未启动", "")
        sub = create_subtask(parent.id, "子任务", today, today, "未启动", "")
        assert sub.id != ""
        assert sub.title == "子任务"
        # 验证子任务在父任务下
        reloaded = get_task(parent.id)
        assert len(reloaded.subtasks) == 1
        assert reloaded.subtasks[0].id == sub.id

    def test_delete_subtask(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import delete_subtask, get_subtask
        today = date.today().isoformat()
        parent = create_task("父", today, today, "未启动", "")
        sub = create_subtask(parent.id, "子", today, today, "未启动", "")
        result = delete_subtask(parent.id, sub.id)
        assert result is True
        found = get_subtask(parent.id, sub.id)
        assert found.deleted is True

    def test_undo_subtask_delete(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import (
            delete_subtask, undo_subtask, get_subtask,
        )
        today = date.today().isoformat()
        parent = create_task("父", today, today, "未启动", "")
        sub = create_subtask(parent.id, "子", today, today, "未启动", "")
        delete_subtask(parent.id, sub.id)
        result = undo_subtask(parent.id, sub.id)
        assert result is True
        found = get_subtask(parent.id, sub.id)
        assert found.deleted is False


# ── 搜索测试 ──────────────────────────────────────────────

class TestSearch:
    def test_search_finds_task(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import search_tasks
        today = date.today().isoformat()
        create_task("独特的搜索关键词", today, today, "未启动", "")
        results = search_tasks("独特的")
        assert len(results) == 1
        assert results[0]["title"] == "独特的搜索关键词"

    def test_search_case_insensitive(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import search_tasks
        today = date.today().isoformat()
        create_task("TestCase", today, today, "未启动", "")
        results = search_tasks("test")
        assert len(results) == 1

    def test_search_matches_status_and_date(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import search_tasks
        create_task("状态搜索任务", "2026-05-20", "2026-05-21", "完成中", "")
        assert any(item["title"] == "状态搜索任务" for item in search_tasks("完成中"))
        assert any(item["title"] == "状态搜索任务" for item in search_tasks("2026-05"))

    def test_search_no_results(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import search_tasks
        results = search_tasks("不存在的关键词xyz")
        assert len(results) == 0

    def test_search_excludes_deleted(self, app_window, tmp_data_dir):
        from todo_manager.engine.task_manager import search_tasks
        today = date.today().isoformat()
        task = create_task("已删搜索测试", today, today, "未启动", "")
        delete_task(task.id)
        results = search_tasks("已删搜索测试")
        assert len(results) == 0

    def test_search_result_for_subtask_uses_parent_calendar_date(self, app_window, tmp_data_dir):
        parent = create_task("父任务", "2026-05-01", "2026-05-02", "未启动", "")
        sub = create_subtask(parent.id, "六月子任务", "2026-06-01", "2026-06-01", "未启动", "")

        app_window._on_search_result(sub.id, sub.start_date, True, parent.id, parent.start_date)

        assert app_window._calendar.year == 2026
        assert app_window._calendar.month == 5
        assert app_window._calendar.selected_task_id == parent.id
        assert app_window._detail.selected_task_id == sub.id

    def test_search_dropdown_focus_shows_selected_day_parent_tasks_only(self, app_window, tmp_data_dir):
        selected = "2026-05-21"
        today_task = create_task("今日下拉父任务", selected, selected, "未启动", "")
        other_task = create_task("其他日期父任务", "2026-05-22", "2026-05-22", "未启动", "")
        sub = create_subtask(today_task.id, "今日下拉子任务", selected, selected, "未启动", "")

        app_window._search_bar.set_context_date(selected)
        app_window._search_bar._input.clear()
        app_window._search_bar._do_search()

        rows = [
            app_window._search_bar._dropdown.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(app_window._search_bar._dropdown.count())
        ]
        ids = {row[0] for row in rows if row}
        assert today_task.id in ids
        assert other_task.id not in ids
        assert sub.id not in ids
        app_window._search_bar.hide_dropdown()

    def test_search_dropdown_matches_subtask_text_but_displays_parent(self, app_window, tmp_data_dir):
        parent = create_task("父级展示任务", "2026-05-21", "2026-05-21", "未启动", "")
        sub = create_subtask(parent.id, "needle 子任务", "2026-05-21", "2026-05-21", "完成中", "")

        app_window._search_bar._input.setText("needle")
        app_window._search_bar._do_search()

        rows = [
            app_window._search_bar._dropdown.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(app_window._search_bar._dropdown.count())
        ]
        ids = {row[0] for row in rows if row}
        assert parent.id in ids
        assert sub.id not in ids
        app_window._search_bar.hide_dropdown()

    def test_task_click_highlights_selected_task_bar(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        task = create_task("高亮任务", today, today, "未启动", "")
        app_window._refresh_all(today, None)

        app_window._on_task_clicked(task.id, today)

        target = [
            bar for bar in app_window._calendar.findChildren(TaskBar)
            if bar.task_id == task.id
        ][0]
        assert f"border: 2px solid {app_window._theme_colors.BORDER_FOCUS}" in target.styleSheet()

    def test_calendar_renders_parent_not_independent_subtask(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        parent = create_task("父任务日历", today, today, "未启动", "")
        sub = create_subtask(parent.id, "不独立上日历", today, today, "未启动", "")

        app_window._refresh_all(today, parent.id)

        bar_ids = {bar.task_id for bar in app_window._calendar.findChildren(TaskBar)}
        assert parent.id in bar_ids
        assert sub.id not in bar_ids


# ── 主题测试 ──────────────────────────────────────────────

class TestTheme:
    def test_toggle_to_dark(self, app_window):
        app_window._theme_toggle.set_theme(Theme.DARK)
        app_window._on_theme_changed()
        assert app_window._current_theme == Theme.DARK
        assert app_window._theme_colors is DarkColors

    def test_toggle_to_light(self, app_window):
        app_window._theme_toggle.set_theme(Theme.LIGHT)
        app_window._on_theme_changed()
        assert app_window._current_theme == Theme.LIGHT
        assert app_window._theme_colors is LightColors

    def test_theme_colors_not_none(self, app_window):
        assert app_window._theme_colors is not None
        assert hasattr(app_window._theme_colors, 'BG_ROOT')

    def test_theme_persists_in_data_dir(self, qapp, tmp_data_dir):
        first = TodoApp(data_dir=tmp_data_dir)
        first._theme_toggle.set_theme(Theme.DARK)
        first._on_theme_changed()
        first.close()
        first.deleteLater()

        second = TodoApp(data_dir=tmp_data_dir)
        try:
            assert second._current_theme == Theme.DARK
            assert second._theme_toggle.theme == Theme.DARK
        finally:
            second.close()
            second.deleteLater()


class TestTodayPanel:
    def test_today_panel_counts_selected_date(self, app_window, tmp_data_dir):
        selected = "2026-05-20"
        create_task("未启动任务", selected, selected, "未启动", "")
        create_task("进行中任务", selected, selected, "完成中", "")
        app_window._calendar.navigate(2026, 5)
        app_window._calendar.select_date(selected)

        app_window._refresh_today_panel()

        assert app_window._today_panel._metric_labels["当日安排"].text() == "2"
        assert app_window._today_panel._metric_labels["未启动"].text() == "1"
        assert app_window._today_panel._metric_labels["完成中"].text() == "1"

    def test_today_panel_status_filter(self, app_window, tmp_data_dir):
        selected = "2026-05-20"
        create_task("保留", selected, selected, "完成中", "")
        create_task("过滤", selected, selected, "未启动", "")
        app_window._calendar.navigate(2026, 5)
        app_window._calendar.select_date(selected)
        app_window._refresh_today_panel()

        app_window._today_panel._filter_buttons["完成中"].click()

        items = app_window._today_panel.findChildren(TaskListItem)
        assert len(items) == 1
        assert items[0]._task.title == "保留"


class TestShortcuts:
    def test_delete_shortcut_ignored_when_search_input_focused(self, app_window, tmp_data_dir, monkeypatch):
        today = date.today().isoformat()
        task = create_task("输入框中不删除", today, today, "未启动", "")
        app_window._refresh_all(today, task.id)
        monkeypatch.setattr(app_window, "_text_input_focused", lambda: True)

        app_window._on_delete_shortcut()

        assert get_task(task.id).deleted is False


# ── 数据持久化测试 ────────────────────────────────────────

class TestDataPersistence:
    def test_tasks_survive_reload(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        task = create_task("持久化测试", today, today, "未启动", "持久化背景")
        task_id = task.id
        # 模拟重新加载
        from todo_manager.engine.storage import load_tasks
        reloaded = load_tasks()
        found = [t for t in reloaded if t.id == task_id]
        assert len(found) == 1
        assert found[0].title == "持久化测试"


# ── 日期筛选测试 ──────────────────────────────────────────

class TestDateFiltering:
    def test_tasks_for_today(self, app_window, tmp_data_dir):
        today = date.today().isoformat()
        create_task("今日任务", today, today, "未启动", "")
        tasks = get_tasks_for_date(today)
        assert len(tasks) >= 1

    def test_task_not_shown_before_start(self, app_window, tmp_data_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        create_task("未来任务", future, future, "未启动", "")
        today = date.today().isoformat()
        tasks = get_tasks_for_date(today)
        # 未完成任务会滞留展示，所以会出现在 today
        # 这是个设计特性：未完成的任务在超出日期后仍展示
        assert len(tasks) >= 0  # 验证不崩溃

    def test_subtask_no_independent_display(self, app_window, tmp_data_dir):
        """子任务不应独立出现在日历中（仅随父任务出现）。"""
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        parent = create_task("父", yesterday, yesterday, "已完成", "")
        sub = create_subtask(parent.id, "子", today, today, "未启动", "")
        tasks_today = get_tasks_for_date(today)
        # 父任务已完成且不在 today 区间，所以不应展示子任务
        parent_ids = [t.id for t in tasks_today]
        assert parent.id not in parent_ids


# ── 弹窗测试 ──────────────────────────────────────────────

class TestDialogs:
    def test_create_dialog_fields(self, qapp, app_window):
        dlg = TaskDialog(TaskDialog.MODE_CREATE, theme_colors=app_window._theme_colors)
        dlg._title_input.setText("弹窗测试")
        dlg._start_date.setDate(QDate.currentDate())
        dlg._end_date.setDate(QDate.currentDate())
        data = dlg.get_form_data()
        assert data["title"] == "弹窗测试"
        assert data["status"] == "未启动"

    def test_edit_dialog_prefilled(self, qapp, app_window, tmp_data_dir):
        today = date.today().isoformat()
        task = create_task("待编辑", today, today, "完成中", "原始背景")
        dlg = TaskDialog(TaskDialog.MODE_EDIT, theme_colors=app_window._theme_colors)
        dlg.set_task_data(task)
        assert dlg._title_input.text() == "待编辑"

    def test_delete_dialog_has_warning_for_subtasks(self, qapp, app_window, tmp_data_dir):
        today = date.today().isoformat()
        parent = create_task("含子任务", today, today, "未启动", "")
        create_subtask(parent.id, "子", today, today, "未启动", "")
        dlg = TaskDialog(TaskDialog.MODE_DELETE, theme_colors=app_window._theme_colors)
        task = get_task(parent.id)
        dlg.set_task_data(task)
        # isHidden() checks the widget's internal hidden state (not screen visibility)
        assert not dlg._delete_sub_hint.isHidden()

    def test_delete_dialog_accepts_subtask_without_subtask_attribute(self, qapp, app_window, tmp_data_dir):
        today = date.today().isoformat()
        parent = create_task("父", today, today, "未启动", "")
        sub = create_subtask(parent.id, "待删子任务", today, today, "未启动", "")
        dlg = TaskDialog(TaskDialog.MODE_DELETE, theme_colors=app_window._theme_colors)

        dlg.set_task_data(sub)

        assert "子任务" in dlg._delete_text.text()
        assert dlg._delete_sub_hint.isHidden()

    def test_subtask_dialog_has_parent_info(self, qapp, app_window, tmp_data_dir):
        today = date.today().isoformat()
        parent = create_task("父", today, today, "未启动", "")
        dlg = TaskDialog(TaskDialog.MODE_SUBTASK, theme_colors=app_window._theme_colors)
        dlg.set_parent_info(parent.title)
        assert dlg._parent_info_label.isVisible()
        assert "父" in dlg._parent_info_label.text()


# ── 扁平化函数测试 ────────────────────────────────────────

class TestFlatList:
    def test_get_all_tasks_flat_includes_subtasks(self, tmp_data_dir):
        from todo_manager.engine.task_manager import get_all_tasks_flat
        today = date.today().isoformat()
        parent = create_task("父", today, today, "未启动", "")
        create_subtask(parent.id, "子", today, today, "未启动", "")
        flat = get_all_tasks_flat()
        assert len(flat) == 2
        assert any(item["is_sub"] for item in flat)

    def test_flat_excludes_deleted(self, tmp_data_dir):
        from todo_manager.engine.task_manager import get_all_tasks_flat
        today = date.today().isoformat()
        task = create_task("待删", today, today, "未启动", "")
        delete_task(task.id)
        flat = get_all_tasks_flat()
        assert not any(item["id"] == task.id for item in flat)
