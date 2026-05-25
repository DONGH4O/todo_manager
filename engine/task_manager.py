"""任务管理：CRUD + 历史管理 + 日期筛选 + 子任务"""

import copy
from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from .calendar_utils import is_date_in_range, _parse_date
from .models import Task, SubTask, VersionRecord, VALID_STATUSES, MAX_TITLE_LENGTH, MAX_BACKGROUND_LENGTH
from .storage import load_tasks, save_tasks


ONGOING_DISPLAY_STATUSES = ("未启动", "完成中")


def _now_iso() -> str:
    """获取当前 UTC+8 时间的 ISO 8601 字符串（微秒精度）"""
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def _make_history_record(task: Task) -> VersionRecord:
    """根据任务当前字段生成一个历史快照"""
    return VersionRecord(
        version=len(task.history) + 1,
        title=task.title,
        start_date=task.start_date,
        end_date=task.end_date,
        status=task.status,
        background=task.background,
        changed_at=_now_iso(),
    )


def _make_subtask_history_record(subtask: SubTask) -> VersionRecord:
    """根据子任务当前字段生成一个历史快照"""
    return VersionRecord(
        version=len(subtask.history) + 1,
        title=subtask.title,
        start_date=subtask.start_date,
        end_date=subtask.end_date,
        status=subtask.status,
        background=subtask.background,
        changed_at=_now_iso(),
    )


# ── 字段校验 ──────────────────────────────────────────────

def _validate_title(title: str) -> None:
    if not title or not title.strip():
        raise ValueError("任务标题不能为空")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"任务标题不能超过 {MAX_TITLE_LENGTH} 个字符，当前 {len(title)} 字")


def _validate_date(date_str: str, field_name: str) -> None:
    """校验日期格式及有效性"""
    if not isinstance(date_str, str) or len(date_str) != 10:
        raise ValueError(f"{field_name} 格式无效，应为 YYYY-MM-DD")
    try:
        _parse_date(date_str)  # 格式 + 有效性
    except ValueError:
        raise ValueError(f"{field_name} 格式无效或不存在: {date_str}")


def _validate_date_order(start: str, end: str) -> None:
    """校验 start <= end"""
    s = _parse_date(start)
    e = _parse_date(end)
    if s > e:
        raise ValueError(f"任务开始日({start})不可晚于截止日({end})")


def _validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"任务完成状态无效，可选: {', '.join(VALID_STATUSES)}")


def _validate_background(background: str) -> None:
    if len(background) > MAX_BACKGROUND_LENGTH:
        raise ValueError(
            f"任务背景及目标不能超过 {MAX_BACKGROUND_LENGTH} 个字符，当前 {len(background)} 字"
        )


def _validate_all(title: str, start_date: str, end_date: str, status: str, background: str) -> None:
    """对全部字段执行校验"""
    _validate_title(title)
    _validate_date(start_date, "任务开始日")
    _validate_date(end_date, "任务截止日")
    _validate_date_order(start_date, end_date)
    _validate_status(status)
    _validate_background(background)


# ── 内部辅助 ──────────────────────────────────────────────

def _resolve_task_id(task_id: str, tasks: list = None) -> Optional[Task]:
    """按 ID 查找任务，支持完整 UUID（36位）或 ≥8 位前缀匹配。

    若前缀匹配到多个任务则报歧义错误。
    """
    if tasks is None:
        tasks = load_tasks()
    if len(task_id) >= 36:
        # 完整 UUID：精确匹配
        for t in tasks:
            if t.id == task_id:
                return t
        return None
    # 短 ID：前缀匹配（<8 位几乎不可能匹配，直接返回 None）
    if len(task_id) < 8:
        return None
    matches = [t for t in tasks if t.id.startswith(task_id)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"ID 前缀 '{task_id}' 匹配到 {len(matches)} 个任务，请提供更多字符"
        )
    return None


def _find_parent_task(task_id: str) -> tuple:
    """查找父任务，返回 (tasks, parent)。找不到抛 ValueError。

    支持完整 UUID 或 ≥8 位前缀匹配。
    """
    tasks = load_tasks()
    parent = _resolve_task_id(task_id, tasks)
    if parent is None:
        raise ValueError(f"任务不存在: {task_id}")
    return tasks, parent


def _resolve_subtask_in_parent(task_id: str, subtask_id: str):
    """在父任务下按 ID 查找子任务，返回 (tasks, parent, subtask)。

    支持完整 UUID（36位）或 ≥8 位前缀匹配子任务 ID。
    找不到抛 ValueError。
    """
    tasks, parent = _find_parent_task(task_id)
    if len(subtask_id) >= 36:
        for s in parent.subtasks:
            if s.id == subtask_id:
                return tasks, parent, s
        raise ValueError(f"子任务不存在: {subtask_id}")
    if len(subtask_id) < 8:
        raise ValueError(f"子任务不存在: {subtask_id}")
    matches = [s for s in parent.subtasks if s.id.startswith(subtask_id)]
    if len(matches) == 1:
        return tasks, parent, matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"子任务 ID 前缀 '{subtask_id}' 匹配到 {len(matches)} 个，请提供更多字符"
        )
    raise ValueError(f"子任务不存在: {subtask_id}")


# ── 任务 CRUD（不变）──────────────────────────────────────

def create_task(
    title: str,
    start_date: str,
    end_date: str,
    status: str,
    background: str,
) -> Task:
    """新建任务。

    自动生成 id、created_at、updated_at，
    并写入 history[0] 作为初始版本快照。

    Raises:
        ValueError: 任一字段校验失败
    """
    _validate_all(title, start_date, end_date, status, background)

    now = _now_iso()
    task = Task(
        id=str(uuid4()),
        title=title.strip(),
        start_date=start_date,
        end_date=end_date,
        status=status,
        background=background,
        deleted=False,
        created_at=now,
        updated_at=now,
    )

    # 写入初始版本快照
    task.history.append(_make_history_record(task))

    # 持久化
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

    return task


def get_task(task_id: str) -> Optional[Task]:
    """按 ID 查询任务（含完整历史记录和子任务）。

    支持完整 UUID 或 ≥8 位前缀匹配。

    Returns:
        Task 对象，不存在返回 None
    """
    return _resolve_task_id(task_id)


def update_task(task_id: str, **kwargs) -> Task:
    """更新任务字段。

    支持部分字段更新，只更新传入的字段。
    更新前将当前字段快照推入 history。
    自动刷新 updated_at。

    Raises:
        ValueError: 任务不存在或字段校验失败
    """
    tasks = load_tasks()
    target = _resolve_task_id(task_id, tasks)

    if target is None:
        raise ValueError(f"任务不存在: {task_id}")

    if target.deleted:
        raise ValueError("无法修改已删除的任务")

    # 合并新值与旧值
    merged_title = kwargs.get("title", target.title)
    merged_start = kwargs.get("start_date", target.start_date)
    merged_end = kwargs.get("end_date", target.end_date)
    merged_status = kwargs.get("status", target.status)
    merged_background = kwargs.get("background", target.background)

    # 仅对变更的字段做校验
    if "title" in kwargs:
        _validate_title(merged_title)
    if "start_date" in kwargs or "end_date" in kwargs:
        _validate_date(merged_start, "任务开始日")
        _validate_date(merged_end, "任务截止日")
        _validate_date_order(merged_start, merged_end)
    if "status" in kwargs:
        _validate_status(merged_status)
    if "background" in kwargs:
        _validate_background(merged_background)

    # push 当前快照
    target.history.append(_make_history_record(target))

    # 更新字段
    target.title = merged_title.strip()
    target.start_date = merged_start
    target.end_date = merged_end
    target.status = merged_status
    target.background = merged_background
    target.updated_at = _now_iso()

    save_tasks(tasks)
    return target


def delete_task(task_id: str) -> bool:
    """软删除任务（deleted = True），不删除数据和历史。

    Returns:
        True 删除成功，False 任务不存在
    """
    tasks = load_tasks()
    target = _resolve_task_id(task_id, tasks)
    if target is None:
        return False
    target.deleted = True
    target.updated_at = _now_iso()
    save_tasks(tasks)
    return True


def should_show_task_on_date(task: Task, date_str: str) -> bool:
    """Return whether a non-deleted task should appear on a calendar date."""
    in_range = is_date_in_range(date_str, task.start_date, task.end_date)
    ongoing_until_today = (
        date_str <= date.today().isoformat()
        and date_str >= task.start_date
        and task.status in ONGOING_DISPLAY_STATUSES
    )
    return in_range or ongoing_until_today


def get_tasks_for_date(date_str: str) -> List[Task]:
    """返回指定日期应展示的任务列表（含未删除的子任务）。

    展示规则（主任务）：
      条件1: T.deleted == False
      条件2: date_str 在 [T.start_date, T.end_date] 区间内，或
      条件3: date_str <= 今天
             AND date_str >= T.start_date
             AND T.status IN ("未启动", "完成中")
      展示当且仅当: 条件1 AND (条件2 OR 条件3)

    展示规则（子任务）：
      当主任务被展示时，其下所有 deleted=False 的子任务一并随 Task 返回。
      子任务自身的时间和状态不影响其是否展示。
    """
    all_tasks = load_tasks()
    result: List[Task] = []

    for t in all_tasks:
        if t.deleted:
            continue
        if should_show_task_on_date(t, date_str):
            t_copy = copy.copy(t)
            t_copy.subtasks = [s for s in t.subtasks if not s.deleted]
            result.append(t_copy)

    return result


def list_all_tasks(include_deleted: bool = False) -> List[Task]:
    """列出所有任务。

    Args:
        include_deleted: 是否包含已删除的任务（默认不包含）
    """
    tasks = load_tasks()
    if include_deleted:
        return list(tasks)
    return [t for t in tasks if not t.deleted]


# ── 子任务 CRUD ────────────────────────────────────────────

def create_subtask(
    task_id: str,
    title: str,
    start_date: str,
    end_date: str,
    status: str,
    background: str,
) -> SubTask:
    """在指定主任务下新建子任务。

    自动生成 id、created_at、updated_at，
    并写入 history[0] 作为初始版本快照。
    校验规则与 create_task 完全一致。

    Raises:
        ValueError: 父任务不存在、父任务已删除、字段校验失败
    """
    _validate_all(title, start_date, end_date, status, background)

    tasks, parent = _find_parent_task(task_id)

    if parent.deleted:
        raise ValueError("无法为已删除的任务创建子任务")

    now = _now_iso()
    subtask = SubTask(
        id=str(uuid4()),
        title=title.strip(),
        start_date=start_date,
        end_date=end_date,
        status=status,
        background=background,
        deleted=False,
        created_at=now,
        updated_at=now,
    )

    # 写入初始版本快照
    subtask.history.append(_make_subtask_history_record(subtask))

    # 挂到父任务下并持久化
    parent.subtasks.append(subtask)
    save_tasks(tasks)

    return subtask


def get_subtask(task_id: str, subtask_id: str) -> Optional[SubTask]:
    """按父任务 ID + 子任务 ID 查询子任务（含完整历史记录）。

    支持完整 UUID 或 ≥8 位前缀匹配。

    Returns:
        SubTask 对象，不存在或父任务不存在返回 None
    """
    try:
        _tasks, _parent, subtask = _resolve_subtask_in_parent(task_id, subtask_id)
        return subtask
    except ValueError:
        return None


def update_subtask(task_id: str, subtask_id: str, **kwargs) -> SubTask:
    """更新子任务字段。

    支持部分字段更新，只更新传入的字段。
    更新前将当前字段快照推入 history。
    自动刷新 updated_at。

    Raises:
        ValueError: 父任务不存在、父任务已删除、子任务不存在、子任务已删除、字段校验失败
    """
    tasks, parent, subtask = _resolve_subtask_in_parent(task_id, subtask_id)

    if parent.deleted:
        raise ValueError("无法修改已删除任务的子任务")

    if subtask.deleted:
        raise ValueError("无法修改已删除的子任务")

    # 合并新值与旧值
    merged_title = kwargs.get("title", subtask.title)
    merged_start = kwargs.get("start_date", subtask.start_date)
    merged_end = kwargs.get("end_date", subtask.end_date)
    merged_status = kwargs.get("status", subtask.status)
    merged_background = kwargs.get("background", subtask.background)

    # 仅对变更的字段做校验
    if "title" in kwargs:
        _validate_title(merged_title)
    if "start_date" in kwargs or "end_date" in kwargs:
        _validate_date(merged_start, "子任务开始日")
        _validate_date(merged_end, "子任务截止日")
        _validate_date_order(merged_start, merged_end)
    if "status" in kwargs:
        _validate_status(merged_status)
    if "background" in kwargs:
        _validate_background(merged_background)

    # push 当前快照
    subtask.history.append(_make_subtask_history_record(subtask))

    # 更新字段
    subtask.title = merged_title.strip()
    subtask.start_date = merged_start
    subtask.end_date = merged_end
    subtask.status = merged_status
    subtask.background = merged_background
    subtask.updated_at = _now_iso()

    save_tasks(tasks)
    return subtask


def delete_subtask(task_id: str, subtask_id: str) -> bool:
    """软删除子任务（deleted = True），不删除数据和历史。

    支持完整 UUID 或 ≥8 位前缀匹配。

    Returns:
        True 删除成功，False 父任务或子任务不存在
    """
    try:
        tasks, parent, subtask = _resolve_subtask_in_parent(task_id, subtask_id)
    except ValueError:
        return False

    if subtask.deleted:
        return False  # 已删除，无需重复操作
    subtask.deleted = True
    subtask.updated_at = _now_iso()
    save_tasks(tasks)
    return True


# ── 撤销删除 ──────────────────────────────────────────────

def undo_task(task_id: str) -> bool:
    """撤销任务删除，将 deleted 恢复为 False。

    Returns:
        True 恢复成功
        False 任务不存在 或 任务未被删除
    """
    tasks = load_tasks()
    target = _resolve_task_id(task_id, tasks)
    if target is None:
        return False
    if not target.deleted:
        return False  # 未被删除，无需恢复
    target.history.append(_make_history_record(target))
    target.deleted = False
    target.updated_at = _now_iso()
    save_tasks(tasks)
    return True


def undo_subtask(task_id: str, subtask_id: str) -> bool:
    """撤销子任务删除，将 deleted 恢复为 False。

    支持完整 UUID 或 ≥8 位前缀匹配。

    Returns:
        True 恢复成功
        False 父任务或子任务不存在，或子任务未被删除
    """
    try:
        tasks, parent, subtask = _resolve_subtask_in_parent(task_id, subtask_id)
    except ValueError:
        return False

    if not subtask.deleted:
        return False  # 未被删除，无需恢复
    subtask.history.append(_make_subtask_history_record(subtask))
    subtask.deleted = False
    subtask.updated_at = _now_iso()
    save_tasks(tasks)
    return True


# ── 搜索与扁平化（GUI 辅助）─────────────────────────────────

def search_tasks(keyword: str) -> List[dict]:
    """在标题、背景、状态和日期中模糊搜索任务及子任务（不含已删除）。

    匹配规则：
      - ≥2 个字符时部分匹配即命中
      - 大小写不敏感

    Returns:
        扁平化 dict 列表，字段同 get_all_tasks_flat()：
        id, title, start_date, end_date, status, background,
        created_at, deleted, is_sub, parent_id, parent_title
    """
    if not keyword or len(keyword.strip()) < 2:
        return get_all_tasks_flat()

    kw = keyword.strip().lower()
    all_tasks = list_all_tasks(include_deleted=False)
    results: List[dict] = []

    for t in all_tasks:
        parent_fields = (
            t.title,
            t.background or "",
            t.status,
            t.start_date,
            t.end_date,
        )
        parent_match = any(kw in str(field).lower() for field in parent_fields)

        if parent_match:
            results.append({
                "id": t.id, "title": t.title,
                "start_date": t.start_date, "end_date": t.end_date,
                "status": t.status, "background": t.background,
                "created_at": t.created_at, "deleted": t.deleted,
                "is_sub": False, "parent_id": None, "parent_title": None,
                "parent_start_date": None,
            })

        # Also search subtasks
        for s in t.subtasks:
            if s.deleted:
                continue
            sub_fields = (
                s.title,
                s.background or "",
                s.status,
                s.start_date,
                s.end_date,
            )
            if any(kw in str(field).lower() for field in sub_fields):
                results.append({
                    "id": s.id, "title": s.title,
                    "start_date": s.start_date, "end_date": s.end_date,
                    "status": s.status, "background": s.background,
                    "created_at": s.created_at, "deleted": s.deleted,
                    "is_sub": True, "parent_id": t.id, "parent_title": t.title,
                    "parent_start_date": t.start_date,
                })

    results.sort(key=lambda x: x["created_at"])
    return results


def get_all_tasks_flat() -> List[dict]:
    """获取所有任务（含子任务）的扁平化列表，按创建时间升序排列。

    用于 GUI 搜索下拉和日历视图中统一排序展示。

    Returns:
        扁平化 dict 列表，每项包含：
          - id, title, start_date, end_date, status, background
          - created_at, deleted
          - is_sub (bool), parent_id (str|None), parent_title (str|None)
    """
    all_tasks = list_all_tasks(include_deleted=False)
    flat: List[dict] = []

    for t in all_tasks:
        flat.append({
            "id": t.id,
            "title": t.title,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "status": t.status,
            "background": t.background,
            "created_at": t.created_at,
            "deleted": t.deleted,
            "is_sub": False,
            "parent_id": None,
            "parent_title": None,
            "parent_start_date": None,
        })
        for s in t.subtasks:
            if s.deleted:
                continue
            flat.append({
                "id": s.id,
                "title": s.title,
                "start_date": s.start_date,
                "end_date": s.end_date,
                "status": s.status,
                "background": s.background,
                "created_at": s.created_at,
                "deleted": s.deleted,
                "is_sub": True,
                "parent_id": t.id,
                "parent_title": t.title,
                "parent_start_date": t.start_date,
            })

    flat.sort(key=lambda x: x["created_at"])
    return flat
