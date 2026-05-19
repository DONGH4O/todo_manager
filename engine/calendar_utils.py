"""公历日历计算（纯 Python 实现，不依赖系统/外部 API）"""

import calendar
from datetime import date, datetime
from typing import List, Optional, Dict, Union


WEEKDAY_CN = {
    0: "星期一",
    1: "星期二",
    2: "星期三",
    3: "星期四",
    4: "星期五",
    5: "星期六",
    6: "星期日",
}


def get_weekday_cn(date_str: str) -> str:
    """返回中文星期名。

    Args:
        date_str: "YYYY-MM-DD" 格式的日期字符串

    Returns:
        星期一 ~ 星期日

    Raises:
        ValueError: 日期格式无效或不存在
    """
    d = _parse_date(date_str)
    return WEEKDAY_CN[d.weekday()]


def get_month_grid(year: int, month: int) -> List[List[Optional[Dict[str, str]]]]:
    """生成月视图网格，以星期一为每周首列。

    返回一个 2D 列表，每行（周）7 列。
    每个格子为 {"date": "YYYY-MM-DD", "weekday": "星期一"}，
    非当月日期填 None。

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        list[list[dict | None]] — 行数取决于当月周数（通常 4-6 周）
    """
    # calendar.monthcalendar 返回以星期一开头的周列表
    # 每项为 7 个整数的列表，非当月日期为 0
    weeks = calendar.monthcalendar(year, month)
    grid: List[List[Optional[Dict[str, str]]]] = []

    for week in weeks:
        row: List[Optional[Dict[str, str]]] = []
        for day in week:
            if day == 0:
                row.append(None)
            else:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                row.append({
                    "date": date_str,
                    "weekday": get_weekday_cn(date_str),
                })
        grid.append(row)

    return grid


def is_date_in_range(date_str: str, start_str: str, end_str: str) -> bool:
    """判断 date_str 是否在 [start_str, end_str] 区间内（含两端）。

    Args:
        date_str: 待判断的日期 "YYYY-MM-DD"
        start_str: 区间开始
        end_str: 区间结束

    Returns:
        True 如果在区间内
    """
    d = _parse_date(date_str)
    s = _parse_date(start_str)
    e = _parse_date(end_str)
    return s <= d <= e


def _parse_date(date_str: str) -> date:
    """将 YYYY-MM-DD 解析为 datetime.date，校验有效性。"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"日期格式无效或不存在: {date_str}")
