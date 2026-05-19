"""数据模型定义：Task / SubTask / VersionRecord"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


# 合法的任务状态枚举值
VALID_STATUSES = ("未启动", "完成中", "已完成", "已取消")

# 字段长度限制
MAX_TITLE_LENGTH = 50
MAX_BACKGROUND_LENGTH = 500


@dataclass
class VersionRecord:
    """任务/子任务历史快照，记录某一次修改前的字段值。"""
    version: int
    title: str
    start_date: str
    end_date: str
    status: str
    background: str
    changed_at: str  # ISO 8601 时间戳


@dataclass
class SubTask:
    """二级子任务 —— 嵌套在主任务内，字段与主任务一致"""
    id: str
    title: str
    start_date: str               # YYYY-MM-DD
    end_date: str                 # YYYY-MM-DD
    status: str                   # 未启动 / 完成中 / 已完成 / 已取消
    background: str
    deleted: bool = False
    created_at: str = ""
    updated_at: str = ""
    history: List[VersionRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        """序列化为普通 dict（用于 JSON 存储）"""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SubTask":
        """从 dict 反序列化"""
        history_data = d.pop("history", [])
        history = [VersionRecord(**h) for h in history_data]
        return cls(**d, history=history)


@dataclass
class Task:
    """待办任务"""
    id: str
    title: str
    start_date: str               # YYYY-MM-DD
    end_date: str                 # YYYY-MM-DD
    status: str                   # 未启动 / 完成中 / 已完成 / 已取消
    background: str
    deleted: bool = False
    created_at: str = ""
    updated_at: str = ""
    history: List[VersionRecord] = field(default_factory=list)
    subtasks: List[SubTask] = field(default_factory=list)

    def to_dict(self) -> dict:
        """序列化为普通 dict（用于 JSON 存储）"""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        """从 dict 反序列化

        向后兼容 v1 数据：缺少 subtasks 字段时自动设为空列表。
        """
        history_data = d.pop("history", [])
        history = [VersionRecord(**h) for h in history_data]
        subtasks_data = d.pop("subtasks", [])
        subtasks = [SubTask.from_dict(s) for s in subtasks_data]
        return cls(**d, history=history, subtasks=subtasks)
