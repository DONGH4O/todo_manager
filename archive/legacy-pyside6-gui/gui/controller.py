"""GUI 与 engine 之间的薄控制层。

Widgets 只关心展示和信号，业务读写统一从这里进入 engine。
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from todo_manager.engine import task_manager
from todo_manager.engine.calendar_utils import is_date_in_range
from todo_manager.engine.models import VALID_STATUSES, Task, SubTask


@dataclass(frozen=True)
class TaskLookup:
    item: Task | SubTask | None
    parent: Task | None = None

    @property
    def is_subtask(self) -> bool:
        return self.item is not None and self.parent is not None


class GuiController:
    """集中封装 GUI 所需的 task_manager 调用。"""

    def create_task(self, **data) -> Task:
        return task_manager.create_task(**data)

    def update_task(self, task_id: str, **data) -> Task:
        return task_manager.update_task(task_id, **data)

    def delete_task(self, task_id: str) -> bool:
        return task_manager.delete_task(task_id)

    def undo_task(self, task_id: str) -> bool:
        return task_manager.undo_task(task_id)

    def create_subtask(self, parent_id: str, **data) -> SubTask:
        return task_manager.create_subtask(parent_id, **data)

    def update_subtask(self, parent_id: str, subtask_id: str, **data) -> SubTask:
        return task_manager.update_subtask(parent_id, subtask_id, **data)

    def delete_subtask(self, parent_id: str, subtask_id: str) -> bool:
        return task_manager.delete_subtask(parent_id, subtask_id)

    def undo_subtask(self, parent_id: str, subtask_id: str) -> bool:
        return task_manager.undo_subtask(parent_id, subtask_id)

    def get_task(self, task_id: str) -> Task | None:
        return task_manager.get_task(task_id)

    def get_subtask(self, parent_id: str, subtask_id: str) -> SubTask | None:
        return task_manager.get_subtask(parent_id, subtask_id)

    def get_tasks_for_date(self, date_str: str) -> list[Task]:
        return task_manager.get_tasks_for_date(date_str)

    def list_all_tasks(self, include_deleted: bool = False) -> list[Task]:
        return task_manager.list_all_tasks(include_deleted=include_deleted)

    def search_tasks(self, keyword: str) -> list[dict]:
        return task_manager.search_tasks(keyword)

    def find_task_any(self, task_id: str) -> TaskLookup:
        task = self.get_task(task_id)
        if task is not None:
            return TaskLookup(task, None)
        for parent in self.list_all_tasks(include_deleted=False):
            for subtask in parent.subtasks:
                if subtask.id == task_id and not subtask.deleted:
                    return TaskLookup(subtask, parent)
        return TaskLookup(None, None)

    def update_status(self, task_id: str, status: str) -> Task | SubTask:
        if status not in VALID_STATUSES:
            raise ValueError(f"任务完成状态无效，可选: {', '.join(VALID_STATUSES)}")
        found = self.find_task_any(task_id)
        if found.item is None:
            raise ValueError(f"任务不存在: {task_id}")
        if found.parent is None:
            return self.update_task(task_id, status=status)
        return self.update_subtask(found.parent.id, task_id, status=status)

    def month_task_count(self, year: int, month: int) -> int:
        start = date(year, month, 1).isoformat()
        end = date(year, month, monthrange(year, month)[1]).isoformat()
        count = 0
        for task in self.list_all_tasks(include_deleted=False):
            if is_date_in_range(task.start_date, start, end) or is_date_in_range(task.end_date, start, end):
                count += 1
                continue
            if task.start_date <= start and task.end_date >= end:
                count += 1
        return count

    def day_status_counts(self, date_str: str) -> dict[str, int]:
        counts = {status: 0 for status in VALID_STATUSES}
        for task in self.get_tasks_for_date(date_str):
            counts[task.status] = counts.get(task.status, 0) + 1
        return counts

    @staticmethod
    def subtask_progress(task: Task) -> tuple[int, int]:
        active_subtasks = [sub for sub in task.subtasks if not sub.deleted]
        done = len([sub for sub in active_subtasks if sub.status == "已完成"])
        return done, len(active_subtasks)
