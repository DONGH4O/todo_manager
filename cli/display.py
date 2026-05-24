"""CLI 输出渲染：表格、详情、日历、统计等格式化函数。

所有函数均为纯函数：接收数据，返回格式化字符串。
不包含任何 CLI 逻辑或副作用。
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from todo_manager.engine.models import Task, SubTask, VersionRecord

# 月历表头缩写
_WEEKDAY_ABBRS = ["一", "二", "三", "四", "五", "六", "日"]

# 子任务缩进
_SUBTASK_INDENT = "     "


# ── CJK 字符宽度辅助 ─────────────────────────────────────

def _char_width(ch: str) -> int:
    """估算单字符在终端中的显示宽度。

    中文字符 2 列，ASCII 1 列。尽力而为。
    """
    code = ord(ch)
    if (0x1100 <= code <= 0x115F or       # hangul
        0x2E80 <= code <= 0xA4CF or       # CJK
        0xAC00 <= code <= 0xD7A3 or       # hangul syllables
        0xF900 <= code <= 0xFAFF or       # CJK compat
        0xFE30 <= code <= 0xFE4F or       # CJK compat forms
        0xFF01 <= code <= 0xFF60 or       # fullwidth forms
        0xFFE0 <= code <= 0xFFE6):        # fullwidth signs
        return 2
    if code > 0x1F000:
        return 2  # emoji etc.
    return 1


def _str_width(s: str) -> int:
    return sum(_char_width(ch) for ch in s)


def _pad(s: str, width: int, align: str = "left") -> str:
    """按显示宽度填充字符串。

    align: "left" | "right" | "center"
    """
    current = _str_width(s)
    if current >= width:
        return s
    padding = width - current
    if align == "left":
        return s + " " * padding
    elif align == "right":
        return " " * padding + s
    else:  # center
        left = padding // 2
        right = padding - left
        return " " * left + s + " " * right


# ── 表格渲染 ──────────────────────────────────────────────

def _build_table(headers: List[str], rows: List[List[str]],
                 aligns: Optional[List[str]] = None) -> str:
    """通用 Unicode 表格渲染。

    自动计算列宽（取表头和数据中最大宽度 + 2 padding）。
    """
    if not rows:
        return ""

    if aligns is None:
        aligns = ["left"] * len(headers)

    # 计算列宽
    col_widths = []
    for i, h in enumerate(headers):
        max_w = _str_width(h)
        for row in rows:
            if i < len(row):
                w = _str_width(str(row[i]))
                if w > max_w:
                    max_w = w
        col_widths.append(max_w + 2)  # padding

    def _row_str(cells: List[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            if i < len(col_widths):
                parts.append(_pad(str(cell), col_widths[i], aligns[i]))
        return "│ " + " │ ".join(parts) + " │"

    sep_top = "┌─" + "─┬─".join("─" * w for w in col_widths) + "─┐"
    sep_mid = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    sep_bot = "└─" + "─┴─".join("─" * w for w in col_widths) + "─┘"

    lines = [sep_top, _row_str(headers), sep_mid]
    for row in rows:
        lines.append(_row_str(row))
    lines.append(sep_bot)

    return "\n".join(lines)


# ── todo list 表格 ───────────────────────────────────────

def format_task_table(tasks: List[Task], show_date: bool = True,
                      show_id: bool = True) -> str:
    """任务列表表格。

    Args:
        tasks: 任务列表
        show_date: 是否显示开始/截止日期列
        show_id: 是否显示 ID 列
    """
    if not tasks:
        return "(无任务)"

    headers = ["#"]
    aligns = ["left"]
    if show_id:
        headers.append("ID")
        aligns.append("left")
    headers.append("标题")
    aligns.append("left")
    if show_date:
        headers.extend(["开始日期", "截止日期"])
        aligns.extend(["center", "center"])
    headers.extend(["状态", "子任务"])
    aligns.extend(["center", "center"])

    rows = []
    for idx, t in enumerate(tasks, 1):
        row = [str(idx)]
        if show_id:
            row.append(t.id[:8])
        row.append(t.title)
        if show_date:
            row.extend([t.start_date, t.end_date])
        subtask_count = len([s for s in t.subtasks if not s.deleted])
        row.extend([t.status, str(subtask_count)])
        rows.append(row)

    return _build_table(headers, rows, aligns)


# ── todo list -d 子任务树形 ──────────────────────────────

def format_task_list_with_subtasks(tasks: List[Task]) -> str:
    """带子任务缩进的列表视图（用于 -d 模式）。

    每个主任务下方缩进列出子任务。
    """
    if not tasks:
        return "(无任务)"

    lines = []
    for idx, t in enumerate(tasks, 1):
        lines.append(f"{idx}. [{t.status}] {t.title}")
        for s in t.subtasks:
            if s.deleted:
                continue
            lines.append(f"{_SUBTASK_INDENT}├─ [{s.status}] {s.title}  {s.start_date} ~ {s.end_date}")
    return "\n".join(lines)


# ── todo show 详情 ──────────────────────────────────────

def format_task_detail(task: Task) -> str:
    """任务完整详情。"""
    lines = [
        f"任务详情: {task.id}",
        "─" * 50,
        f"标题:      {task.title}",
        f"开始日期:  {task.start_date}",
        f"截止日期:  {task.end_date}",
        f"状态:      {task.status}",
        f"背景:      {task.background or '(无)'}",
        f"创建时间:  {task.created_at}",
        f"更新时间:  {task.updated_at}",
        f"已删除:    {'是' if task.deleted else '否'}",
    ]

    # 子任务
    non_deleted_subs = [s for s in task.subtasks if not s.deleted]
    lines.append("")
    if non_deleted_subs:
        lines.append(f"子任务 ({len(non_deleted_subs)}条):")
        for idx, s in enumerate(non_deleted_subs, 1):
            lines.append(f"  {idx}. [{s.status}] {s.title}")
            lines.append(f"     日期: {s.start_date} ~ {s.end_date}")
            lines.append(f"     背景: {s.background or '(无)'}")
    else:
        lines.append("子任务: (无)")

    return "\n".join(lines)


# ── todo sub list 表格 ──────────────────────────────────

def format_subtask_list(task: Task) -> str:
    """某任务下所有子任务列表（含已删除）。"""
    if not task.subtasks:
        return f"子任务列表 (任务: {task.title})\n(无子任务)"

    headers = ["#", "ID", "标题", "开始日期", "截止日期", "状态", "已删除"]
    aligns = ["left", "left", "left", "center", "center", "center", "center"]

    rows = []
    for idx, s in enumerate(task.subtasks, 1):
        rows.append([
            str(idx),
            s.id[:8],
            s.title,
            s.start_date,
            s.end_date,
            s.status,
            "是" if s.deleted else "否",
        ])

    return f"子任务列表 (任务: {task.title})\n" + _build_table(headers, rows, aligns)


# ── todo sub show 详情 ──────────────────────────────────

def format_subtask_detail(subtask: SubTask, parent_title: str) -> str:
    """单个子任务完整详情。"""
    lines = [
        f"子任务详情: {subtask.id}",
        f"  所属任务: {parent_title}",
        "─" * 50,
        f"标题:      {subtask.title}",
        f"开始日期:  {subtask.start_date}",
        f"截止日期:  {subtask.end_date}",
        f"状态:      {subtask.status}",
        f"背景:      {subtask.background or '(无)'}",
        f"创建时间:  {subtask.created_at}",
        f"更新时间:  {subtask.updated_at}",
        f"已删除:    {'是' if subtask.deleted else '否'}",
    ]
    return "\n".join(lines)


# ── 历史记录渲染 ────────────────────────────────────────

def format_history(records: List[VersionRecord], max_n: int = 5) -> str:
    """格式化历史快照列表。

    每条显示全部 5 个字段，与上一版本对比：
    - 初始版本（v1）直接列出初始值
    - 后续版本：值不变标注"(不变)"，变更用 → 展示
    """
    if not records:
        return "历史记录: (无)"

    # 取最近 max_n 条并按“最新在前”展示，更符合 CLI 快速审计习惯。
    selected = list(enumerate(records))[-max_n:]
    recent = list(reversed(selected))

    lines = [f"历史记录 (最近{len(recent)}条，最新在前):"]
    for original_idx, rec in recent:
        lines.append(f"  v{rec.version}  {rec.changed_at}")

        if original_idx == 0:
            # 初始版本：直接列出所有初始值
            lines.append(f"      [初始创建]")
            lines.append(f"      标题: {rec.title}")
            lines.append(f"      状态: {rec.status}")
            lines.append(f"      日期: {rec.start_date} ~ {rec.end_date}")
            lines.append(f"      背景: {rec.background or '(无)'}")
        else:
            # 后续版本：对比上一版本
            prev = records[original_idx - 1]

            t_changed = rec.title != prev.title
            s_changed = rec.status != prev.status
            d_changed = rec.start_date != prev.start_date or rec.end_date != prev.end_date
            b_changed = rec.background != prev.background

            if t_changed:
                lines.append(f"      标题: {prev.title} → {rec.title}")
            else:
                lines.append(f"      标题: {rec.title} (不变)")

            if s_changed:
                lines.append(f"      状态: {prev.status} → {rec.status}")
            else:
                lines.append(f"      状态: {rec.status} (不变)")

            if d_changed:
                lines.append(f"      日期: {prev.start_date} ~ {prev.end_date} → {rec.start_date} ~ {rec.end_date}")
            else:
                lines.append(f"      日期: {rec.start_date} ~ {rec.end_date} (不变)")

            if b_changed:
                prev_bg = prev.background or "(无)"
                cur_bg = rec.background or "(无)"
                lines.append(f"      背景: {prev_bg} → {cur_bg}")
            else:
                lines.append(f"      背景: {rec.background or '(无)'} (不变)")

        lines.append("")

    return "\n".join(lines).rstrip()


# ── todo cal 月历 ───────────────────────────────────────

def format_calendar(year: int, month: int,
                    tasks_by_date: "dict[str, List[Task]]") -> str:
    """渲染月历视图。

    Args:
        year, month: 年月
        tasks_by_date: dict，key="MM-DD"，value=该日任务列表
    """
    from todo_manager.engine.calendar_utils import get_month_grid, get_weekday_cn

    grid = get_month_grid(year, month)

    # 表头（周一 ~ 周日）
    header = "   ".join(_WEEKDAY_ABBRS)
    lines = [f"{year}年 {month}月".center(28), "", header]

    for week in grid:
        row_parts = []
        for cell in week:
            if cell is None:
                row_parts.append("  ")
            else:
                day = int(cell["date"][-2:])
                key = cell["date"][5:]
                count = len(tasks_by_date.get(key, []))
                if count > 0:
                    # 日期 + 任务数标记
                    cell_str = f"{day:2d}+{count}"
                else:
                    cell_str = f"{day:2d} "
                row_parts.append(_pad(cell_str, 4, "left"))
        lines.append(" ".join(row_parts).rstrip())

    # 任务摘要
    if any(tasks_by_date.values()):
        lines.append("")
        lines.append("本月任务:")
        for date_key, task_list in tasks_by_date.items():
            if not task_list:
                continue
            lines.append(f"  {date_key} ({len(task_list)}条):")
            for t in task_list:
                sub_count = len([s for s in t.subtasks if not s.deleted])
                sub_note = f" ← {sub_count}条子任务" if sub_count > 0 else ""
                lines.append(f"                [{t.status}] {t.title}{sub_note}")

    return "\n".join(lines)


# ── todo stats 统计 ─────────────────────────────────────

def format_stats(total: int, by_status: dict, subtask_count: int,
                 upcoming: List[Task]) -> str:
    """统计概览。"""
    lines = [
        "任务统计",
        "─" * 24,
        f"总任务数:     {total}",
    ]
    for status in ["未启动", "完成中", "已完成", "已取消"]:
        lines.append(f"  {status}:      {by_status.get(status, 0)}")

    lines.append(f"总子任务数:    {subtask_count}")

    if upcoming:
        lines.append(f"即将到期 (3天内): {len(upcoming)}")
        for t in upcoming:
            lines.append(f"  [{t.status}] {t.title} (截止: {t.end_date})")
    else:
        lines.append("即将到期 (3天内): 0")

    return "\n".join(lines)


# ── todo search 结果 ────────────────────────────────────

def format_search_results(tasks: List[Task], keyword: str) -> str:
    """搜索结果表格。"""
    if not tasks:
        return f'搜索 "{keyword}" (标题+背景):\n(无匹配结果)'

    result = format_task_table(tasks, show_date=True, show_id=True)
    return f'搜索 "{keyword}" (标题+背景):\n' + result
