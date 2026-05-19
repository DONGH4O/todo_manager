"""CLI 命令处理函数。

每个 cmd_* 函数接收 argparse 解析后的 Namespace，
执行引擎调用，输出格式化结果到 stdout，错误到 stderr。
"""

import sys
from collections import OrderedDict
from datetime import date, datetime, timedelta

from todo_manager.engine.task_manager import (
    create_task, get_task, update_task, delete_task, undo_task,
    create_subtask, get_subtask, update_subtask, delete_subtask, undo_subtask,
    get_tasks_for_date, list_all_tasks,
    search_tasks,
)
from todo_manager.engine.models import VALID_STATUSES
from todo_manager.cli.display import (
    format_task_table, format_task_list_with_subtasks,
    format_task_detail, format_subtask_list, format_subtask_detail,
    format_history, format_calendar, format_stats, format_search_results,
)


def _confirm(prompt: str = "确认？[y/N]: ") -> bool:
    """交互式确认。读取一行输入，y/yes 为确认。"""
    try:
        ans = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("", file=sys.stderr)
        sys.exit(1)
    return ans in ("y", "yes")


def _fail(msg: str, code: int = 1):
    """打印错误到 stderr 并退出。"""
    print(f"错误: {msg}", file=sys.stderr)
    sys.exit(code)


# 字段名 → 中文标签映射（用于编辑摘要）
_FIELD_LABELS = {
    "title": "标题",
    "start_date": "开始日期",
    "end_date": "截止日期",
    "status": "状态",
    "background": "背景",
}

# args 属性名 → kwargs 字段名映射
_EDIT_FIELD_MAP = [
    ("title", "title"),
    ("start_date", "start"),
    ("end_date", "end"),
    ("status", "status"),
    ("background", "background"),
]


def _build_edit_kwargs(args):
    """从 args 提取编辑字段到 kwargs dict。"""
    kwargs = {}
    for field, attr in _EDIT_FIELD_MAP:
        val = getattr(args, attr, None)
        if val is not None:
            kwargs[field] = val
    return kwargs


# ── todo add ────────────────────────────────────────────

def cmd_add(args):
    now = date.today().isoformat()
    try:
        task = create_task(
            title=args.title,
            start_date=args.start or now,
            end_date=args.end or now,
            status=args.status or "未启动",
            background=args.background or "",
        )
    except ValueError as e:
        _fail(str(e))
    print(f"已创建任务 [{task.id[:8]}] \"{task.title}\"")


# ── todo list ───────────────────────────────────────────

def cmd_list(args):
    if args.date:
        tasks = get_tasks_for_date(args.date)
        output = format_task_list_with_subtasks(tasks)
    else:
        tasks = list_all_tasks(include_deleted=args.deleted)
        output = format_task_table(tasks, show_date=True, show_id=True)
    print(output)


# ── todo show ───────────────────────────────────────────

def cmd_show(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    detail = format_task_detail(task)
    history = format_history(task.history, max_n=args.history or 5)
    print(detail)
    print()
    print(history)


# ── todo edit ───────────────────────────────────────────

def cmd_edit(args):
    kwargs = _build_edit_kwargs(args)

    if not kwargs:
        _fail("至少需要提供一个要修改的字段。使用 -h 查看选项。")

    # 确认机制（默认不跳过）
    if not args.force:
        task = get_task(args.task_id)
        if task is None:
            _fail(f"未找到任务: {args.task_id}")
        change_items = []
        for field, val in kwargs.items():
            label = _FIELD_LABELS.get(field, field)
            change_items.append(f"{label}={val}")
        msg = f"将更新任务 \"{task.title}\" ({', '.join(change_items)})，确认？[y/N]: "
        if not _confirm(msg):
            print("已取消")
            return

    try:
        updated = update_task(args.task_id, **kwargs)
    except ValueError as e:
        _fail(str(e))

    # 打印变更摘要（使用中文标签）
    change_items = [_FIELD_LABELS.get(k, k) + " 已更新" for k in kwargs]
    changes = ", ".join(change_items)
    print(f"任务 \"{updated.title}\" {changes}")


# ── todo delete ─────────────────────────────────────────

def cmd_delete(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    if task.deleted:
        print(f"任务已处于删除状态: {task.title}")
        return

    sub_count = len([s for s in task.subtasks if not s.deleted])
    msg = f"将删除任务 \"{task.title}\""
    if sub_count:
        msg += f" (含 {sub_count} 条子任务)"
    msg += "，确认？[y/N]: "

    if not args.force and not _confirm(msg):
        print("已取消")
        return

    result = delete_task(args.task_id)
    if result:
        print(f"已删除: {task.title}")
    else:
        _fail(f"删除失败: {args.task_id}")


# ── todo undo ───────────────────────────────────────────

def cmd_undo(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")
    if not task.deleted:
        print(f"该任务未被删除，无需恢复: {task.title}")
        return

    msg = f"将恢复任务 \"{task.title}\"，确认？[y/N]: "

    if not args.force and not _confirm(msg):
        print("已取消")
        return

    result = undo_task(args.task_id)
    if result:
        print(f"已恢复: {task.title}")
    else:
        _fail(f"恢复失败: {args.task_id}")


# ── todo sub add ────────────────────────────────────────

def cmd_sub_add(args):
    now = date.today().isoformat()
    try:
        sub = create_subtask(
            task_id=args.task_id,
            title=args.title,
            start_date=args.start or now,
            end_date=args.end or now,
            status=args.status or "未启动",
            background=args.background or "",
        )
    except ValueError as e:
        _fail(str(e))
    print(f"已创建子任务 [{sub.id[:8]}] \"{sub.title}\"")


# ── todo sub list ───────────────────────────────────────

def cmd_sub_list(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    print(format_subtask_list(task))


# ── todo sub show ───────────────────────────────────────

def cmd_sub_show(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    sub = get_subtask(args.task_id, args.sub_id)
    if sub is None:
        _fail(f"未找到子任务: {args.sub_id}")

    detail = format_subtask_detail(sub, task.title)
    history = format_history(sub.history, max_n=args.history or 5)
    print(detail)
    print()
    print(history)


# ── todo sub edit ───────────────────────────────────────

def cmd_sub_edit(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    sub = get_subtask(args.task_id, args.sub_id)
    if sub is None:
        _fail(f"未找到子任务: {args.sub_id}")

    kwargs = _build_edit_kwargs(args)

    if not kwargs:
        _fail("至少需要提供一个要修改的字段。使用 -h 查看选项。")

    # 确认机制（默认不跳过）
    if not args.force:
        change_items = []
        for field, val in kwargs.items():
            label = _FIELD_LABELS.get(field, field)
            change_items.append(f"{label}={val}")
        msg = f"将更新子任务 \"{sub.title}\" ({', '.join(change_items)})，确认？[y/N]: "
        if not _confirm(msg):
            print("已取消")
            return

    try:
        updated = update_subtask(args.task_id, args.sub_id, **kwargs)
    except ValueError as e:
        _fail(str(e))

    print(f"子任务 \"{updated.title}\" 已更新")


# ── todo sub delete ─────────────────────────────────────

def cmd_sub_delete(args):
    task = get_task(args.task_id)
    if task is None:
        _fail(f"未找到任务: {args.task_id}")

    sub = get_subtask(args.task_id, args.sub_id)
    if sub is None:
        _fail(f"未找到子任务: {args.sub_id}")

    if sub.deleted:
        print(f"子任务已处于删除状态: {sub.title}")
        return

    if not args.force:
        msg = f"将删除子任务 \"{sub.title}\"，确认？[y/N]: "
        if not _confirm(msg):
            print("已取消")
            return

    result = delete_subtask(args.task_id, args.sub_id)
    if result:
        print(f"已删除子任务: {sub.title}")
    else:
        _fail(f"删除失败")


# ── todo sub undo ───────────────────────────────────────

def cmd_sub_undo(args):
    sub = get_subtask(args.task_id, args.sub_id)
    if sub is None:
        _fail(f"未找到子任务: {args.sub_id}")
    if not sub.deleted:
        print(f"该子任务未被删除，无需恢复: {sub.title}")
        return

    msg = f"将恢复子任务 \"{sub.title}\"，确认？[y/N]: "
    if not args.force and not _confirm(msg):
        print("已取消")
        return

    result = undo_subtask(args.task_id, args.sub_id)
    if result:
        print(f"已恢复子任务: {sub.title}")
    else:
        _fail(f"恢复失败")


# ── todo cal ────────────────────────────────────────────

def cmd_cal(args):
    today = date.today()
    if args.month:
        try:
            parts = args.month.split("-")
            year, month = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            _fail(f"日期格式无效: {args.month}，应为 YYYY-MM")
    else:
        year, month = today.year, today.month

    if not (1 <= month <= 12):
        _fail(f"月份无效: {month}，应为 1-12")

    # 遍历当月每一天，收集任务
    tasks_by_date = OrderedDict()
    day = 1
    while True:
        try:
            d = date(year, month, day)
        except ValueError:
            break
        date_str = d.isoformat()
        key = date_str[5:]  # MM-DD
        day_tasks = get_tasks_for_date(date_str)
        # 按 start_date 升序排列
        day_tasks.sort(key=lambda t: t.start_date)
        tasks_by_date[key] = day_tasks
        day += 1

    print(format_calendar(year, month, tasks_by_date))


# ── todo search ─────────────────────────────────────────

def cmd_search(args):
    results = search_tasks(args.keyword)
    if not results:
        print(f'搜索 "{args.keyword}" (标题+背景+子任务):\n(无匹配结果)')
        return
    headers = ["#", "ID", "标题", "开始日期", "截止日期", "状态", "类型"]
    aligns = ["left", "left", "left", "center", "center", "center", "center"]
    rows = []
    for idx, t in enumerate(results, 1):
        task_type = "子任务" if t.get("is_sub") else "主任务"
        rows.append([
            str(idx), t["id"][:8], t["title"],
            t["start_date"], t["end_date"], t["status"], task_type,
        ])
    from todo_manager.cli.display import _build_table
    print(f'搜索 "{args.keyword}" (标题+背景+子任务):')
    print(_build_table(headers, rows, aligns))


# ── todo stats ──────────────────────────────────────────

def cmd_stats(args):
    all_tasks = list_all_tasks(include_deleted=False)
    total = len(all_tasks)

    by_status = {}
    for t in all_tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1

    # 总子任务数（不含已删除）
    subtask_total = 0
    for t in all_tasks:
        subtask_total += len([s for s in t.subtasks if not s.deleted])

    # 即将到期：截止日在未来 3 天内，且未完成
    today = date.today()
    deadline = today + timedelta(days=3)
    upcoming = []
    for t in all_tasks:
        if t.status in ("已完成", "已取消"):
            continue
        try:
            end_date = datetime.strptime(t.end_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if today <= end_date <= deadline:
            upcoming.append(t)
    upcoming.sort(key=lambda t: t.end_date)

    print(format_stats(total, by_status, subtask_total, upcoming))
