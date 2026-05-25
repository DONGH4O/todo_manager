"""任务管理模块单元测试"""

import os
import copy
import tempfile
from datetime import date, timedelta
import pytest
from todo_manager.engine.models import Task, SubTask, VersionRecord, VALID_STATUSES
from todo_manager.engine.storage import set_data_dir
from todo_manager.engine.task_manager import (
    create_task,
    get_task,
    update_task,
    delete_task,
    undo_task,
    get_tasks_for_date,
    list_all_tasks,
    create_subtask,
    get_subtask,
    update_subtask,
    delete_subtask,
    undo_subtask,
)


@pytest.fixture(autouse=True)
def isolated_storage():
    """每个测试使用独立的数据目录，互不干扰"""
    with tempfile.TemporaryDirectory() as tmp:
        set_data_dir(tmp)
        yield tmp


# ── 创建任务 ──────────────────────────────────────────────

class TestCreateTask:
    def test_create_basic(self):
        task = create_task(
            title="完成Q2报告",
            start_date="2026-04-01",
            end_date="2026-04-30",
            status="未启动",
            background="汇总Q2产品数据",
        )
        assert task.id != ""
        assert task.title == "完成Q2报告"
        assert task.start_date == "2026-04-01"
        assert task.end_date == "2026-04-30"
        assert task.status == "未启动"
        assert task.background == "汇总Q2产品数据"
        assert task.deleted is False
        assert task.created_at != ""
        assert task.updated_at != ""

    def test_create_generates_unique_ids(self):
        t1 = create_task("A", "2026-01-01", "2026-01-05", "未启动", "bg")
        t2 = create_task("B", "2026-02-01", "2026-02-05", "未启动", "bg")
        assert t1.id != t2.id

    def test_create_generates_history_v1(self):
        task = create_task("测试", "2026-04-01", "2026-04-15", "未启动", "背景描述")
        assert len(task.history) == 1
        assert task.history[0].version == 1
        assert task.history[0].title == "测试"
        assert task.history[0].status == "未启动"

    def test_create_title_stripped(self):
        task = create_task("  含空格标题  ", "2026-04-01", "2026-04-30", "未启动", "bg")
        assert task.title == "含空格标题"

    def test_create_persists(self):
        create_task("持久化测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        tasks = list_all_tasks()
        assert len(tasks) == 1


class TestCreateTaskValidation:
    def test_empty_title(self):
        with pytest.raises(ValueError, match="任务标题不能为空"):
            create_task("", "2026-04-01", "2026-04-30", "未启动", "bg")

    def test_whitespace_only_title(self):
        with pytest.raises(ValueError, match="任务标题不能为空"):
            create_task("   ", "2026-04-01", "2026-04-30", "未启动", "bg")

    def test_title_too_long(self):
        long_title = "测" * 51
        with pytest.raises(ValueError, match="不能超过 50"):
            create_task(long_title, "2026-04-01", "2026-04-30", "未启动", "bg")

    def test_invalid_date_format(self):
        with pytest.raises(ValueError, match="任务开始日"):
            create_task("测试", "2026/04/01", "2026-04-30", "未启动", "bg")

    def test_nonexistent_date(self):
        with pytest.raises(ValueError):
            create_task("测试", "2026-02-30", "2026-03-01", "未启动", "bg")

    def test_start_after_end(self):
        with pytest.raises(ValueError, match="不可晚于"):
            create_task("测试", "2026-04-30", "2026-04-01", "未启动", "bg")

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="状态无效"):
            create_task("测试", "2026-04-01", "2026-04-30", "进行中", "bg")

    def test_background_too_long(self):
        long_bg = "测" * 501
        with pytest.raises(ValueError, match="不能超过 500"):
            create_task("测试", "2026-04-01", "2026-04-30", "未启动", long_bg)


# ── 查询任务 ──────────────────────────────────────────────

class TestGetTask:
    def test_get_existing(self):
        task = create_task("查询测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        found = get_task(task.id)
        assert found is not None
        assert found.id == task.id
        assert found.history is not None

    def test_get_nonexistent(self):
        assert get_task("不存在的id") is None


# ── 更新任务 ──────────────────────────────────────────────

class TestUpdateTask:
    def test_update_status(self):
        task = create_task("更新测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        updated = update_task(task.id, status="完成中")
        assert updated.status == "完成中"
        assert updated.updated_at != task.updated_at

    def test_update_title(self):
        task = create_task("旧标题", "2026-04-01", "2026-04-30", "未启动", "bg")
        updated = update_task(task.id, title="新标题")
        assert updated.title == "新标题"

    def test_update_partial_fields(self):
        """只传部分字段，其余保持不变"""
        task = create_task("部分更新", "2026-04-01", "2026-04-30", "未启动", "原始背景")
        updated = update_task(task.id, status="完成中")
        assert updated.status == "完成中"
        assert updated.title == "部分更新"
        assert updated.start_date == "2026-04-01"
        assert updated.background == "原始背景"

    def test_update_pushes_history(self):
        task = create_task("历史测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        assert len(task.history) == 1  # 初始版本

        updated = update_task(task.id, status="完成中")
        assert len(updated.history) == 2
        # 确认 v2 是更新前的快照（status=未启动）
        assert updated.history[1].version == 2
        assert updated.history[1].status == "未启动"

    def test_update_nonexistent(self):
        with pytest.raises(ValueError, match="任务不存在"):
            update_task("fake-id", status="完成中")

    def test_update_deleted_task(self):
        task = create_task("删后改", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(task.id)
        with pytest.raises(ValueError, match="已删除"):
            update_task(task.id, status="完成中")


# ── 删除任务 ──────────────────────────────────────────────

class TestDeleteTask:
    def test_delete_existing(self):
        task = create_task("删除测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        result = delete_task(task.id)
        assert result is True
        # 从存储重新加载
        reloaded = get_task(task.id)
        assert reloaded.deleted is True

    def test_delete_nonexistent(self):
        assert delete_task("fake-id") is False

    def test_delete_preserves_history(self):
        task = create_task("历史保留", "2026-04-01", "2026-04-30", "未启动", "bg")
        update_task(task.id, status="完成中")
        delete_task(task.id)
        reloaded = get_task(task.id)
        assert len(reloaded.history) == 2
        assert reloaded.deleted is True


# ── 日期展示筛选 ──────────────────────────────────────────

class TestGetTasksForDate:
    def test_in_range_shows(self):
        create_task("区间内", "2026-04-01", "2026-04-15", "已完成", "bg")
        tasks = get_tasks_for_date("2026-04-10")
        assert len(tasks) == 1

    def test_out_of_range_completed_hidden(self):
        create_task("已完成过期", "2026-03-01", "2026-03-15", "已完成", "bg")
        tasks = get_tasks_for_date("2026-04-01")
        assert len(tasks) == 0

    def test_out_of_range_cancelled_hidden(self):
        create_task("已取消过期", "2026-03-01", "2026-03-15", "已取消", "bg")
        tasks = get_tasks_for_date("2026-04-01")
        assert len(tasks) == 0

    def test_out_of_range_not_finished_shows(self):
        """未完成的任务即使超出日期范围也要滞留展示"""
        create_task("未完成滞留", "2026-03-01", "2026-03-15", "未启动", "bg")
        tasks = get_tasks_for_date("2026-04-20")
        assert len(tasks) == 1
        assert tasks[0].title == "未完成滞留"

    def test_out_of_range_in_progress_shows(self):
        create_task("完成中滞留", "2026-03-01", "2026-03-15", "完成中", "bg")
        tasks = get_tasks_for_date("2026-05-01")
        assert len(tasks) == 1

    def test_deleted_not_shown(self):
        task = create_task("删除不展示", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(task.id)
        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 0

    def test_completed_in_range_still_shows(self):
        """已完成但仍在日期区间内的任务，仍然展示"""
        create_task("已完成区间内", "2026-04-01", "2026-04-30", "已完成", "bg")
        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 1

    def test_multiple_tasks_same_day(self):
        create_task("A", "2026-04-01", "2026-04-30", "未启动", "bg")
        create_task("B", "2026-04-01", "2026-04-30", "完成中", "bg")
        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 2


# ── 列出所有任务 ──────────────────────────────────────────

class TestListAllTasks:
    def test_empty(self):
        assert list_all_tasks() == []

    def test_excludes_deleted_by_default(self):
        t1 = create_task("存活", "2026-04-01", "2026-04-30", "未启动", "bg")
        t2 = create_task("删除", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(t2.id)
        tasks = list_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == t1.id

    def test_includes_deleted_when_requested(self):
        create_task("存活", "2026-04-01", "2026-04-30", "未启动", "bg")
        t2 = create_task("删除", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(t2.id)
        tasks = list_all_tasks(include_deleted=True)
        assert len(tasks) == 2


# ── 创建子任务 ──────────────────────────────────────────────

class TestCreateSubtask:
    def test_create_basic(self):
        task = create_task("主任务", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子任务1", "2026-04-01", "2026-04-15", "未启动", "子背景")
        assert sub.id != ""
        assert sub.title == "子任务1"
        assert sub.start_date == "2026-04-01"
        assert sub.end_date == "2026-04-15"
        assert sub.status == "未启动"
        assert sub.background == "子背景"
        assert sub.deleted is False
        assert sub.created_at != ""
        assert sub.updated_at != ""

    def test_create_multiple_subtasks(self):
        task = create_task("多子任务", "2026-04-01", "2026-04-30", "未启动", "bg")
        s1 = create_subtask(task.id, "子A", "2026-04-01", "2026-04-05", "未启动", "")
        s2 = create_subtask(task.id, "子B", "2026-04-06", "2026-04-10", "完成中", "")
        assert s1.id != s2.id
        reloaded = get_task(task.id)
        assert len(reloaded.subtasks) == 2

    def test_create_generates_history_v1(self):
        task = create_task("历史", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子历史", "2026-04-01", "2026-04-15", "未启动", "")
        assert len(sub.history) == 1
        assert sub.history[0].version == 1
        assert sub.history[0].title == "子历史"
        assert sub.history[0].status == "未启动"

    def test_create_title_stripped(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "  有空格  ", "2026-04-01", "2026-04-15", "未启动", "")
        assert sub.title == "有空格"

    def test_create_background_empty_allowed(self):
        """background 可以为空字符串"""
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "")
        sub = create_subtask(task.id, "子空背景", "2026-04-01", "2026-04-15", "未启动", "")
        assert sub.background == ""


class TestCreateSubtaskValidation:
    def test_parent_not_found(self):
        with pytest.raises(ValueError, match="任务不存在"):
            create_subtask("fake-id", "子", "2026-04-01", "2026-04-15", "未启动", "")

    def test_parent_deleted(self):
        task = create_task("已删", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(task.id)
        with pytest.raises(ValueError, match="已删除"):
            create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")

    def test_empty_title(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="任务标题不能为空"):
            create_subtask(task.id, "", "2026-04-01", "2026-04-15", "未启动", "")

    def test_title_too_long(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="不能超过 50"):
            create_subtask(task.id, "测" * 51, "2026-04-01", "2026-04-15", "未启动", "")

    def test_invalid_date_format(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="任务开始日"):
            create_subtask(task.id, "子", "2026/04/01", "2026-04-15", "未启动", "")

    def test_nonexistent_date(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError):
            create_subtask(task.id, "子", "2026-02-30", "2026-03-01", "未启动", "")

    def test_start_after_end(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="不可晚于"):
            create_subtask(task.id, "子", "2026-04-15", "2026-04-01", "未启动", "")

    def test_invalid_status(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="状态无效"):
            create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "进行中", "")

    def test_background_too_long(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="不能超过 500"):
            create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "测" * 501)


# ── 查询子任务 ──────────────────────────────────────────────

class TestGetSubtask:
    def test_get_existing(self):
        task = create_task("查询", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子查询", "2026-04-01", "2026-04-15", "未启动", "")
        found = get_subtask(task.id, sub.id)
        assert found is not None
        assert found.id == sub.id
        assert found.title == "子查询"
        assert len(found.history) == 1

    def test_get_subtask_nonexistent(self):
        task = create_task("查询", "2026-04-01", "2026-04-30", "未启动", "bg")
        assert get_subtask(task.id, "fake-sub-id") is None

    def test_get_parent_not_found(self):
        assert get_subtask("fake-task-id", "fake-sub-id") is None

    def test_get_subtask_includes_deleted(self):
        """get_subtask 也返回已删除的子任务（用于审计/恢复）"""
        task = create_task("查询", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_subtask(task.id, sub.id)
        found = get_subtask(task.id, sub.id)
        assert found is not None
        assert found.deleted is True


# ── 更新子任务 ──────────────────────────────────────────────

class TestUpdateSubtask:
    def test_update_status(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        updated = update_subtask(task.id, sub.id, status="完成中")
        assert updated.status == "完成中"
        assert updated.updated_at != sub.updated_at

    def test_update_title(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "旧标题", "2026-04-01", "2026-04-15", "未启动", "")
        updated = update_subtask(task.id, sub.id, title="新标题")
        assert updated.title == "新标题"

    def test_update_partial_fields(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "部分", "2026-04-01", "2026-04-15", "未启动", "原始")
        updated = update_subtask(task.id, sub.id, status="完成中")
        assert updated.status == "完成中"
        assert updated.title == "部分"
        assert updated.start_date == "2026-04-01"
        assert updated.background == "原始"

    def test_update_pushes_history(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "历史", "2026-04-01", "2026-04-15", "未启动", "")
        assert len(sub.history) == 1

        updated = update_subtask(task.id, sub.id, status="完成中")
        assert len(updated.history) == 2
        assert updated.history[1].version == 2
        assert updated.history[1].status == "未启动"  # 更新前的快照

    def test_update_all_fields(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "旧", "2026-04-01", "2026-04-15", "未启动", "旧背景")
        updated = update_subtask(
            task.id, sub.id,
            title="新", start_date="2026-04-05", end_date="2026-04-20",
            status="已完成", background="新背景"
        )
        assert updated.title == "新"
        assert updated.start_date == "2026-04-05"
        assert updated.end_date == "2026-04-20"
        assert updated.status == "已完成"
        assert updated.background == "新背景"

    def test_parent_not_found(self):
        with pytest.raises(ValueError, match="任务不存在"):
            update_subtask("fake-id", "fake-sub", status="完成中")

    def test_parent_deleted(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_task(task.id)
        with pytest.raises(ValueError, match="已删除"):
            update_subtask(task.id, sub.id, status="完成中")

    def test_subtask_not_found(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        with pytest.raises(ValueError, match="子任务不存在"):
            update_subtask(task.id, "fake-sub", status="完成中")

    def test_subtask_deleted(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_subtask(task.id, sub.id)
        with pytest.raises(ValueError, match="无法修改已删除的子任务"):
            update_subtask(task.id, sub.id, status="完成中")


# ── 删除子任务 ──────────────────────────────────────────────

class TestDeleteSubtask:
    def test_delete_existing(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "待删", "2026-04-01", "2026-04-15", "未启动", "")
        result = delete_subtask(task.id, sub.id)
        assert result is True
        found = get_subtask(task.id, sub.id)
        assert found.deleted is True

    def test_delete_nonexistent_subtask(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        assert delete_subtask(task.id, "fake-sub") is False

    def test_delete_nonexistent_parent(self):
        assert delete_subtask("fake-task", "fake-sub") is False

    def test_delete_preserves_history(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "历史", "2026-04-01", "2026-04-15", "未启动", "")
        update_subtask(task.id, sub.id, status="完成中")
        delete_subtask(task.id, sub.id)
        found = get_subtask(task.id, sub.id)
        assert len(found.history) == 2
        assert found.deleted is True

    def test_delete_parent_does_not_cascade(self):
        """父任务软删除不影响子任务的 deleted 字段"""
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_task(task.id)
        found = get_subtask(task.id, sub.id)
        assert found.deleted is False  # 子任务自身未删


# ── 日历展示（含子任务）────────────────────────────────────

class TestCalendarWithSubtasks:
    def test_ongoing_task_stays_visible_on_today_after_deadline(self):
        """未启动/完成中任务过截止日后，今天仍应持续展示。"""
        today = date.today()
        task = create_task(
            "逾期未启动",
            (today - timedelta(days=20)).isoformat(),
            (today - timedelta(days=10)).isoformat(),
            "未启动",
            "bg",
        )

        tasks = get_tasks_for_date(today.isoformat())

        assert [item.id for item in tasks] == [task.id]

    def test_ongoing_task_stays_visible_on_future_dates_after_deadline(self):
        """未启动/完成中任务在未来日期也应持续展示。"""
        today = date.today()
        task = create_task(
            "未来仍展示",
            (today - timedelta(days=20)).isoformat(),
            (today - timedelta(days=10)).isoformat(),
            "完成中",
            "bg",
        )

        tasks = get_tasks_for_date((today + timedelta(days=10)).isoformat())

        assert [item.id for item in tasks] == [task.id]

    def test_completed_or_cancelled_tasks_do_not_continue_after_deadline(self):
        """已完成/已取消任务超过截止日后不再按持续任务展示。"""
        today = date.today()
        start = (today - timedelta(days=20)).isoformat()
        end = (today - timedelta(days=10)).isoformat()
        create_task("已完成过期", start, end, "已完成", "bg")
        create_task("已取消过期", start, end, "已取消", "bg")

        tasks = get_tasks_for_date(today.isoformat())

        assert tasks == []

    def test_parent_shown_subtasks_included(self):
        """父任务展示时，未删除的子任务也出现"""
        task = create_task("主", "2026-04-01", "2026-04-30", "未启动", "bg")
        create_subtask(task.id, "子A", "2026-03-01", "2026-03-15", "已完成", "")
        create_subtask(task.id, "子B", "2026-05-01", "2026-05-15", "未启动", "")

        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 1
        assert len(tasks[0].subtasks) == 2
        subtask_titles = [s.title for s in tasks[0].subtasks]
        assert "子A" in subtask_titles
        assert "子B" in subtask_titles

    def test_deleted_subtask_not_included(self):
        """已删除的子任务不出现在日历展示中"""
        task = create_task("主", "2026-04-01", "2026-04-30", "未启动", "bg")
        create_subtask(task.id, "可见", "2026-04-01", "2026-04-15", "未启动", "")
        dead = create_subtask(task.id, "不可见", "2026-04-01", "2026-04-15", "未启动", "")
        delete_subtask(task.id, dead.id)

        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 1
        assert len(tasks[0].subtasks) == 1
        assert tasks[0].subtasks[0].title == "可见"

    def test_parent_not_shown_subtasks_not_shown(self):
        """父任务不展示时，子任务也不出现"""
        task = create_task("已完成过期", "2026-03-01", "2026-03-15", "已完成", "bg")
        create_subtask(task.id, "子", "2026-04-01", "2026-04-30", "未启动", "")

        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 0

    def test_parent_deleted_subtasks_not_shown(self):
        """父任务被删除后，子任务也不展示"""
        task = create_task("主", "2026-04-01", "2026-04-30", "未启动", "bg")
        create_subtask(task.id, "子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_task(task.id)

        tasks = get_tasks_for_date("2026-04-15")
        assert len(tasks) == 0

    def test_subtask_own_status_does_not_affect_display(self):
        """子任务自身状态不影响展示：已完成/已取消的子任务仍然随父任务出现"""
        task = create_task("主", "2026-04-01", "2026-04-15", "未启动", "bg")
        create_subtask(task.id, "已完成子", "2026-04-01", "2026-04-15", "已完成", "")
        create_subtask(task.id, "已取消子", "2026-04-01", "2026-04-15", "已取消", "")

        tasks = get_tasks_for_date("2026-04-20")
        assert len(tasks) == 1
        assert len(tasks[0].subtasks) == 2


# ── 存储：v1 数据向后兼容 ─────────────────────────────────

class TestBackwardCompat:
    def test_load_v1_data_subtasks_empty(self):
        """加载 v1 格式的 tasks.json（无 subtasks 字段），subtasks 应为空列表"""
        import json
        v1_data = {
            "version": 1,
            "tasks": [
                {
                    "id": "old-task-id",
                    "title": "旧版本任务",
                    "start_date": "2026-04-01",
                    "end_date": "2026-04-30",
                    "status": "未启动",
                    "background": "old",
                    "deleted": False,
                    "created_at": "2026-04-01T00:00:00+08:00",
                    "updated_at": "2026-04-01T00:00:00+08:00",
                    "history": []
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            set_data_dir(tmp)
            path = os.path.join(tmp, "tasks.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(v1_data, f, ensure_ascii=False)

            from todo_manager.engine.storage import load_tasks
            tasks = load_tasks()
            assert len(tasks) == 1
            assert tasks[0].id == "old-task-id"
            assert tasks[0].subtasks == []


# ── 模型序列化（含子任务）──────────────────────────────────

class TestModelSerialization:
    def test_subtask_to_dict_and_back(self):
        sub = SubTask(
            id="sub-id",
            title="子任务",
            start_date="2026-04-01",
            end_date="2026-04-15",
            status="未启动",
            background="bg",
            history=[
                VersionRecord(version=1, title="子任务", start_date="2026-04-01",
                              end_date="2026-04-15", status="未启动", background="bg",
                              changed_at="2026-04-01T00:00:00")
            ]
        )
        d = sub.to_dict()
        restored = SubTask.from_dict(d)
        assert restored.id == "sub-id"
        assert restored.title == "子任务"
        assert len(restored.history) == 1
        assert restored.history[0].version == 1

    def test_subtask_from_dict_does_not_mutate_input(self):
        sub = SubTask(
            id="sub-id",
            title="子任务",
            start_date="2026-04-01",
            end_date="2026-04-15",
            status="未启动",
            background="bg",
            history=[
                VersionRecord(version=1, title="子任务", start_date="2026-04-01",
                              end_date="2026-04-15", status="未启动", background="bg",
                              changed_at="2026-04-01T00:00:00")
            ]
        )
        data = sub.to_dict()
        before = copy.deepcopy(data)

        SubTask.from_dict(data)

        assert data == before

    def test_task_with_subtasks_roundtrip(self):
        sub = SubTask(
            id="sub-1",
            title="子",
            start_date="2026-04-01",
            end_date="2026-04-15",
            status="未启动",
            background="",
        )
        task = Task(
            id="task-1",
            title="主",
            start_date="2026-04-01",
            end_date="2026-04-30",
            status="未启动",
            background="bg",
            subtasks=[sub],
        )
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == "task-1"
        assert len(restored.subtasks) == 1
        assert restored.subtasks[0].id == "sub-1"
        assert restored.subtasks[0].title == "子"

    def test_task_from_dict_does_not_mutate_input(self):
        sub = SubTask(
            id="sub-1",
            title="子",
            start_date="2026-04-01",
            end_date="2026-04-15",
            status="未启动",
            background="",
            history=[
                VersionRecord(version=1, title="子", start_date="2026-04-01",
                              end_date="2026-04-15", status="未启动", background="",
                              changed_at="2026-04-01T00:00:00")
            ]
        )
        task = Task(
            id="task-1",
            title="主",
            start_date="2026-04-01",
            end_date="2026-04-30",
            status="未启动",
            background="bg",
            history=[
                VersionRecord(version=1, title="主", start_date="2026-04-01",
                              end_date="2026-04-30", status="未启动", background="bg",
                              changed_at="2026-04-01T00:00:00")
            ],
            subtasks=[sub],
        )
        data = task.to_dict()
        before = copy.deepcopy(data)

        Task.from_dict(data)

        assert data == before

    def test_subtask_history_independent(self):
        """验证子任务历史与主任务历史各自独立"""
        task = Task(id="t", title="T", start_date="2026-04-01", end_date="2026-04-30",
                    status="未启动", background="",
                    history=[VersionRecord(version=1, title="T", start_date="2026-04-01",
                                           end_date="2026-04-30", status="未启动", background="",
                                           changed_at="2026-04-01T00:00:00")])
        sub = SubTask(id="s", title="S", start_date="2026-04-01", end_date="2026-04-15",
                      status="未启动", background="",
                      history=[VersionRecord(version=1, title="S", start_date="2026-04-01",
                                             end_date="2026-04-15", status="未启动", background="",
                                             changed_at="2026-04-01T00:00:00")])
        task.subtasks.append(sub)

        d = task.to_dict()
        restored = Task.from_dict(d)
        assert len(restored.history) == 1
        assert len(restored.subtasks[0].history) == 1
        assert restored.history[0].title == "T"
        assert restored.subtasks[0].history[0].title == "S"


# ── 撤销删除（任务）────────────────────────────────────────

class TestUndoTask:
    def test_undo_deleted_task(self):
        task = create_task("撤销测试", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(task.id)
        result = undo_task(task.id)
        assert result is True
        reloaded = get_task(task.id)
        assert reloaded.deleted is False
        assert reloaded.title == "撤销测试"

    def test_undo_not_deleted_task(self):
        """未被删除的任务 undo 返回 False"""
        task = create_task("存活任务", "2026-04-01", "2026-04-30", "未启动", "bg")
        result = undo_task(task.id)
        assert result is False

    def test_undo_nonexistent_task(self):
        assert undo_task("不存在的id") is False

    def test_undo_restores_visibility(self):
        """撤销删除后，任务应在 list_all_tasks 中出现"""
        task = create_task("恢复可见", "2026-04-01", "2026-04-30", "未启动", "bg")
        delete_task(task.id)
        assert len(list_all_tasks()) == 0
        undo_task(task.id)
        tasks = list_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task.id

    def test_undo_preserves_history(self):
        task = create_task("历史保留", "2026-04-01", "2026-04-30", "未启动", "bg")
        update_task(task.id, status="完成中")
        delete_task(task.id)
        undo_task(task.id)
        reloaded = get_task(task.id)
        assert len(reloaded.history) == 3


# ── 撤销删除（子任务）──────────────────────────────────────

class TestUndoSubtask:
    def test_undo_deleted_subtask(self):
        task = create_task("撤销子", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "待恢复", "2026-04-01", "2026-04-15", "未启动", "")
        delete_subtask(task.id, sub.id)
        result = undo_subtask(task.id, sub.id)
        assert result is True
        found = get_subtask(task.id, sub.id)
        assert found.deleted is False

    def test_undo_not_deleted_subtask(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "存活子", "2026-04-01", "2026-04-15", "未启动", "")
        assert undo_subtask(task.id, sub.id) is False

    def test_undo_nonexistent_parent(self):
        assert undo_subtask("fake-task", "fake-sub") is False

    def test_undo_nonexistent_subtask(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        assert undo_subtask(task.id, "fake-sub") is False

    def test_undo_restores_calendar_visibility(self):
        """撤销删除后子任务应重新出现在日历中"""
        task = create_task("日历恢复", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "可见子", "2026-04-01", "2026-04-15", "未启动", "")
        delete_subtask(task.id, sub.id)
        tasks = get_tasks_for_date("2026-04-10")
        assert len(tasks[0].subtasks) == 0
        undo_subtask(task.id, sub.id)
        tasks = get_tasks_for_date("2026-04-10")
        assert len(tasks[0].subtasks) == 1

    def test_undo_preserves_history(self):
        task = create_task("T", "2026-04-01", "2026-04-30", "未启动", "bg")
        sub = create_subtask(task.id, "历史子", "2026-04-01", "2026-04-15", "未启动", "")
        update_subtask(task.id, sub.id, status="完成中")
        delete_subtask(task.id, sub.id)
        undo_subtask(task.id, sub.id)
        found = get_subtask(task.id, sub.id)
        assert len(found.history) == 3
