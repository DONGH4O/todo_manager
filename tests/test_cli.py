"""D2 CLI 集成测试。

通过调用命令处理函数（而非 subprocess）来测试 CLI 层。
复用 D1 的 isolated_storage fixture 隔离数据目录。
"""

import argparse
import io
import sys
import tempfile

import pytest

from todo_manager.engine.storage import set_data_dir
from todo_manager.engine.task_manager import (
    create_task, delete_task, create_subtask,
)


# ── 辅助函数 ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_storage():
    """每个测试使用独立的数据目录"""
    with tempfile.TemporaryDirectory() as tmp:
        set_data_dir(tmp)
        yield tmp


def _capture_stdout(func, *args, **kwargs):
    """捕获 stdout 输出。"""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        func(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


def _capture_stderr(func, *args, **kwargs):
    """捕获 stderr 输出 + 拦截 sys.exit。"""
    buf = io.StringIO()
    old = sys.stderr
    sys.stderr = buf
    try:
        func(*args, **kwargs)
    except SystemExit as e:
        pass
    finally:
        sys.stderr = old
    return buf.getvalue()


def _ns(**kwargs):
    """快捷创建 argparse.Namespace。"""
    return argparse.Namespace(**kwargs)


# ── todo add ────────────────────────────────────────────

class TestCmdAdd:
    def test_add_basic(self):
        from todo_manager.cli.commands import cmd_add
        args = _ns(
            title="Q2报告", start=None, end=None,
            status=None, background=None,
        )
        out = _capture_stdout(cmd_add, args)
        assert "已创建任务" in out
        assert "Q2报告" in out

    def test_add_with_all_fields(self):
        from todo_manager.cli.commands import cmd_add
        args = _ns(
            title="完整任务", start="2026-06-01", end="2026-06-15",
            status="完成中", background="测试背景",
        )
        out = _capture_stdout(cmd_add, args)
        assert "已创建任务" in out
        assert "完整任务" in out

    def test_add_validation_error(self):
        from todo_manager.cli.commands import cmd_add
        args = _ns(
            title="", start=None, end=None, status=None, background=None,
        )
        err = _capture_stderr(cmd_add, args)
        assert "错误" in err


# ── todo list ───────────────────────────────────────────

class TestCmdList:
    def test_list_empty(self):
        from todo_manager.cli.commands import cmd_list
        args = _ns(date=None, deleted=False)
        out = _capture_stdout(cmd_list, args)
        assert "无任务" in out

    def test_list_with_tasks(self):
        from todo_manager.cli.commands import cmd_list
        create_task("A任务", "2026-05-01", "2026-05-15", "未启动", "")
        create_task("B任务", "2026-05-10", "2026-05-20", "完成中", "")
        args = _ns(date=None, deleted=False)
        out = _capture_stdout(cmd_list, args)
        assert "A任务" in out
        assert "B任务" in out

    def test_list_by_date(self):
        from todo_manager.cli.commands import cmd_list
        create_task("区间内", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(date="2026-05-10", deleted=False)
        out = _capture_stdout(cmd_list, args)
        assert "区间内" in out

    def test_list_by_date_with_subtasks(self):
        from todo_manager.cli.commands import cmd_list
        task = create_task("主任务", "2026-05-01", "2026-05-15", "未启动", "")
        create_subtask(task.id, "子任务", "2026-05-01", "2026-05-05", "未启动", "")
        args = _ns(date="2026-05-10", deleted=False)
        out = _capture_stdout(cmd_list, args)
        assert "主任务" in out
        assert "子任务" in out

    def test_list_with_deleted(self):
        from todo_manager.cli.commands import cmd_list
        t = create_task("删除的", "2026-05-01", "2026-05-05", "未启动", "")
        delete_task(t.id)
        args = _ns(date=None, deleted=True)
        out = _capture_stdout(cmd_list, args)
        assert "删除的" in out


# ── todo show ───────────────────────────────────────────

class TestCmdShow:
    def test_show_existing(self):
        from todo_manager.cli.commands import cmd_show
        task = create_task("详情测试", "2026-05-01", "2026-05-15", "完成中", "测试背景")
        args = _ns(task_id=task.id, history=5)
        out = _capture_stdout(cmd_show, args)
        assert "详情测试" in out
        assert "测试背景" in out
        assert "完成中" in out
        assert "历史记录" in out

    def test_show_not_found(self):
        from todo_manager.cli.commands import cmd_show
        args = _ns(task_id="不存在的id", history=5)
        err = _capture_stderr(cmd_show, args)
        assert "未找到" in err

    def test_show_with_subtasks(self):
        from todo_manager.cli.commands import cmd_show
        task = create_task("有子任务", "2026-05-01", "2026-05-15", "未启动", "")
        create_subtask(task.id, "子", "2026-05-01", "2026-05-05", "未启动", "子背景")
        args = _ns(task_id=task.id, history=5)
        out = _capture_stdout(cmd_show, args)
        assert "子任务" in out
        assert "子" in out
        assert "子背景" in out

    def test_show_with_background_in_history(self):
        """验证历史记录包含 background 字段"""
        from todo_manager.cli.commands import cmd_show
        task = create_task("历史背景", "2026-05-01", "2026-05-15", "未启动", "原始背景")
        from todo_manager.engine.task_manager import update_task
        update_task(task.id, background="新背景")
        args = _ns(task_id=task.id, history=5)
        out = _capture_stdout(cmd_show, args)
        assert "原始背景" in out
        assert "新背景" in out


# ── todo edit ───────────────────────────────────────────

class TestCmdEdit:
    def test_edit_status(self):
        from todo_manager.cli.commands import cmd_edit
        task = create_task("编辑测试", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(
            task_id=task.id, title=None, start=None, end=None,
            status="完成中", background=None, force=True,
        )
        out = _capture_stdout(cmd_edit, args)
        assert "已更新" in out

    def test_edit_no_fields(self):
        from todo_manager.cli.commands import cmd_edit
        task = create_task("无字段", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(
            task_id=task.id, title=None, start=None, end=None,
            status=None, background=None,
        )
        err = _capture_stderr(cmd_edit, args)
        assert "至少需要" in err

    def test_edit_not_found(self):
        from todo_manager.cli.commands import cmd_edit
        args = _ns(
            task_id="fake", title="新", start=None, end=None,
            status=None, background=None, force=True,
        )
        err = _capture_stderr(cmd_edit, args)
        assert "不存在" in err


# ── todo delete ─────────────────────────────────────────

class TestCmdDelete:
    def test_delete_with_force(self):
        from todo_manager.cli.commands import cmd_delete
        task = create_task("强制删除", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(task_id=task.id, force=True)
        out = _capture_stdout(cmd_delete, args)
        assert "已删除" in out

    def test_delete_not_found(self):
        from todo_manager.cli.commands import cmd_delete
        args = _ns(task_id="fake", force=True)
        err = _capture_stderr(cmd_delete, args)
        assert "未找到" in err

    def test_delete_without_force_cancelled(self, monkeypatch):
        from todo_manager.cli.commands import cmd_delete
        task = create_task("取消删除", "2026-05-01", "2026-05-15", "未启动", "")
        monkeypatch.setattr("builtins.input", lambda _: "n")
        args = _ns(task_id=task.id, force=False)
        out = _capture_stdout(cmd_delete, args)
        assert "已取消" in out


# ── todo undo ───────────────────────────────────────────

class TestCmdUndo:
    def test_undo_deleted(self):
        from todo_manager.cli.commands import cmd_undo
        task = create_task("待恢复", "2026-05-01", "2026-05-15", "未启动", "")
        delete_task(task.id)
        args = _ns(task_id=task.id, force=True)
        out = _capture_stdout(cmd_undo, args)
        assert "已恢复" in out

    def test_undo_not_deleted(self):
        from todo_manager.cli.commands import cmd_undo
        task = create_task("未删", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(task_id=task.id, force=True)
        out = _capture_stdout(cmd_undo, args)
        assert "无需恢复" in out

    def test_undo_not_found(self):
        from todo_manager.cli.commands import cmd_undo
        args = _ns(task_id="fake", force=True)
        err = _capture_stderr(cmd_undo, args)
        assert "未找到" in err


# ── todo sub add ────────────────────────────────────────

class TestCmdSubAdd:
    def test_sub_add_basic(self):
        from todo_manager.cli.commands import cmd_sub_add
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(
            task_id=task.id, title="子任务A",
            start=None, end=None, status=None, background=None,
        )
        out = _capture_stdout(cmd_sub_add, args)
        assert "已创建子任务" in out

    def test_sub_add_parent_not_found(self):
        from todo_manager.cli.commands import cmd_sub_add
        args = _ns(
            task_id="fake", title="子",
            start=None, end=None, status=None, background=None,
        )
        err = _capture_stderr(cmd_sub_add, args)
        assert "错误" in err


# ── todo sub list ───────────────────────────────────────

class TestCmdSubList:
    def test_sub_list_empty(self):
        from todo_manager.cli.commands import cmd_sub_list
        task = create_task("空子任务", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(task_id=task.id)
        out = _capture_stdout(cmd_sub_list, args)
        assert "无子任务" in out

    def test_sub_list_with_items(self):
        from todo_manager.cli.commands import cmd_sub_list
        task = create_task("有子", "2026-05-01", "2026-05-15", "未启动", "")
        create_subtask(task.id, "子A", "2026-05-01", "2026-05-05", "未启动", "")
        create_subtask(task.id, "子B", "2026-05-06", "2026-05-10", "完成中", "")
        args = _ns(task_id=task.id)
        out = _capture_stdout(cmd_sub_list, args)
        assert "子A" in out
        assert "子B" in out

    def test_sub_list_includes_deleted(self):
        from todo_manager.cli.commands import cmd_sub_list
        from todo_manager.engine.task_manager import delete_subtask
        task = create_task("T", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "已删子", "2026-05-01", "2026-05-05", "未启动", "")
        delete_subtask(task.id, sub.id)
        args = _ns(task_id=task.id)
        out = _capture_stdout(cmd_sub_list, args)
        assert "已删子" in out
        assert "是" in out  # 已删除列


# ── todo sub show ───────────────────────────────────────

class TestCmdSubShow:
    def test_sub_show_with_history(self):
        from todo_manager.cli.commands import cmd_sub_show
        from todo_manager.engine.task_manager import update_subtask
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "子详情", "2026-05-01", "2026-05-05", "未启动", "背景")
        update_subtask(task.id, sub.id, status="完成中")
        args = _ns(task_id=task.id, sub_id=sub.id, history=5)
        out = _capture_stdout(cmd_sub_show, args)
        assert "子详情" in out
        assert "背景" in out
        assert "历史记录" in out

    def test_sub_show_not_found(self):
        from todo_manager.cli.commands import cmd_sub_show
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(task_id=task.id, sub_id="fake-sub", history=5)
        err = _capture_stderr(cmd_sub_show, args)
        assert "未找到" in err


# ── todo sub edit ───────────────────────────────────────

class TestCmdSubEdit:
    def test_sub_edit_with_force(self):
        from todo_manager.cli.commands import cmd_sub_edit
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "可编辑", "2026-05-01", "2026-05-05", "未启动", "")
        args = _ns(
            task_id=task.id, sub_id=sub.id,
            title=None, start=None, end=None,
            status="已完成", background=None,
            force=True,
        )
        out = _capture_stdout(cmd_sub_edit, args)
        assert "已更新" in out

    def test_sub_edit_no_fields(self):
        from todo_manager.cli.commands import cmd_sub_edit
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "子", "2026-05-01", "2026-05-05", "未启动", "")
        args = _ns(
            task_id=task.id, sub_id=sub.id,
            title=None, start=None, end=None,
            status=None, background=None,
            force=True,
        )
        err = _capture_stderr(cmd_sub_edit, args)
        assert "至少需要" in err

    def test_sub_edit_without_force_cancelled(self, monkeypatch):
        from todo_manager.cli.commands import cmd_sub_edit
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "子", "2026-05-01", "2026-05-05", "未启动", "")
        monkeypatch.setattr("builtins.input", lambda _: "n")
        args = _ns(
            task_id=task.id, sub_id=sub.id,
            title=None, start=None, end=None,
            status="已完成", background=None,
            force=False,
        )
        out = _capture_stdout(cmd_sub_edit, args)
        assert "已取消" in out


# ── todo sub delete & undo ──────────────────────────────

class TestCmdSubDeleteUndo:
    def test_sub_delete_force(self):
        from todo_manager.cli.commands import cmd_sub_delete
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "待删子", "2026-05-01", "2026-05-05", "未启动", "")
        args = _ns(task_id=task.id, sub_id=sub.id, force=True)
        out = _capture_stdout(cmd_sub_delete, args)
        assert "已删除子任务" in out

    def test_sub_undo(self):
        from todo_manager.cli.commands import cmd_sub_undo
        from todo_manager.engine.task_manager import delete_subtask
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        sub = create_subtask(task.id, "待恢复", "2026-05-01", "2026-05-05", "未启动", "")
        delete_subtask(task.id, sub.id)
        args = _ns(task_id=task.id, sub_id=sub.id, force=True)
        out = _capture_stdout(cmd_sub_undo, args)
        assert "已恢复子任务" in out


# ── todo cal ────────────────────────────────────────────

class TestCmdCal:
    def test_cal_current_month(self):
        from todo_manager.cli.commands import cmd_cal
        args = _ns(month=None)
        out = _capture_stdout(cmd_cal, args)
        assert "年" in out
        assert "月" in out

    def test_cal_specific_month_empty(self):
        from todo_manager.cli.commands import cmd_cal
        args = _ns(month="2026-07")
        out = _capture_stdout(cmd_cal, args)
        assert "2026年 7月" in out

    def test_cal_with_tasks(self):
        from todo_manager.cli.commands import cmd_cal
        create_task("月内任务", "2026-05-01", "2026-05-05", "未启动", "")
        args = _ns(month="2026-05")
        out = _capture_stdout(cmd_cal, args)
        assert "月内任务" in out

    def test_cal_invalid_month(self):
        from todo_manager.cli.commands import cmd_cal
        args = _ns(month="2026-13")
        err = _capture_stderr(cmd_cal, args)
        assert "月份无效" in err


# ── todo search ─────────────────────────────────────────

class TestCmdSearch:
    def test_search_by_title(self):
        from todo_manager.cli.commands import cmd_search
        create_task("搜索测试标题", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(keyword="搜索")
        out = _capture_stdout(cmd_search, args)
        assert "搜索测试标题" in out

    def test_search_by_background(self):
        from todo_manager.cli.commands import cmd_search
        create_task("任务", "2026-05-01", "2026-05-15", "未启动", "独特关键字背景")
        args = _ns(keyword="独特")
        out = _capture_stdout(cmd_search, args)
        assert "任务" in out

    def test_search_no_match(self):
        from todo_manager.cli.commands import cmd_search
        create_task("任务X", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(keyword="不存在的关键字")
        out = _capture_stdout(cmd_search, args)
        assert "无匹配" in out

    def test_search_single_char(self):
        """单字符搜索也应能匹配"""
        from todo_manager.cli.commands import cmd_search
        create_task("测", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(keyword="测")
        out = _capture_stdout(cmd_search, args)
        assert "测" in out

    def test_search_case_insensitive(self):
        from todo_manager.cli.commands import cmd_search
        create_task("ABC任务", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(keyword="abc")
        out = _capture_stdout(cmd_search, args)
        assert "ABC任务" in out

    def test_search_single_char_case_insensitive(self):
        """单字符搜索也应大小写不敏感"""
        from todo_manager.cli.commands import cmd_search
        create_task("X任务", "2026-05-01", "2026-05-15", "未启动", "")
        args = _ns(keyword="x")
        out = _capture_stdout(cmd_search, args)
        assert "X任务" in out


# ── todo stats ──────────────────────────────────────────

class TestCmdStats:
    def test_stats_empty(self):
        from todo_manager.cli.commands import cmd_stats
        args = _ns()
        out = _capture_stdout(cmd_stats, args)
        assert "总任务数:     0" in out
        assert "即将到期" in out

    def test_stats_with_mixed_statuses(self):
        from todo_manager.cli.commands import cmd_stats
        create_task("A", "2026-05-01", "2026-05-15", "未启动", "")
        create_task("B", "2026-05-01", "2026-05-15", "完成中", "")
        create_task("C", "2026-05-01", "2026-05-15", "已完成", "")
        create_task("D", "2026-05-01", "2026-05-15", "已取消", "")
        args = _ns()
        out = _capture_stdout(cmd_stats, args)
        assert "总任务数:     4" in out
        assert "未启动:      1" in out
        assert "完成中:      1" in out
        assert "已完成:      1" in out
        assert "已取消:      1" in out

    def test_stats_with_subtasks(self):
        from todo_manager.cli.commands import cmd_stats
        task = create_task("父", "2026-05-01", "2026-05-15", "未启动", "")
        create_subtask(task.id, "子A", "2026-05-01", "2026-05-05", "未启动", "")
        create_subtask(task.id, "子B", "2026-05-06", "2026-05-10", "未启动", "")
        args = _ns()
        out = _capture_stdout(cmd_stats, args)
        assert "总子任务数:    2" in out

    def test_stats_upcoming_deadline(self, monkeypatch):
        from todo_manager.cli.commands import cmd_stats
        # 创建一个明后天到期的任务
        from datetime import date, timedelta
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_task("快到期", tomorrow, tomorrow, "未启动", "")
        args = _ns()
        out = _capture_stdout(cmd_stats, args)
        assert "快到期" in out


# ── 历史记录具体内容验证 ────────────────────────────────

class TestHistoryContent:
    def test_history_shows_background_change(self):
        """验证历史记录正确展示 background 变更"""
        from todo_manager.cli.commands import cmd_show
        from todo_manager.engine.task_manager import update_task
        task = create_task("背景变更", "2026-05-01", "2026-05-15", "未启动", "旧背景")
        update_task(task.id, background="新背景", title="背景变更")
        args = _ns(task_id=task.id, history=5)
        out = _capture_stdout(cmd_show, args)
        assert "旧背景" in out
        assert "新背景" in out

    def test_history_shows_unchanged_fields(self):
        """验证未变更字段标注 '(不变)'"""
        from todo_manager.cli.commands import cmd_show
        from todo_manager.engine.task_manager import update_task
        task = create_task("单字段变", "2026-05-01", "2026-05-15", "未启动", "背景")
        update_task(task.id, status="完成中")
        args = _ns(task_id=task.id, history=5)
        out = _capture_stdout(cmd_show, args)
        assert "不变" in out
