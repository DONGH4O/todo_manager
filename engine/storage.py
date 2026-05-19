"""JSON 文件存储：读写 tasks.json"""

import json
from pathlib import Path
from typing import List

from .models import Task
from .platform_paths import resolve_data_dir

# 数据文件目录 — 启动时由 set_data_dir() 配置
_data_dir: Path | None = None


def set_data_dir(dir_path: str | Path) -> None:
    """设置数据文件所在目录。

    应在程序启动时调用一次。
    传入相对路径时相对于当前工作目录解析。
    """
    global _data_dir
    _data_dir = resolve_data_dir(dir_path)


def clear_data_dir() -> None:
    """清除显式数据目录配置，恢复平台默认策略。"""
    global _data_dir
    _data_dir = None


def get_data_dir() -> str:
    """获取当前数据目录路径。

    - 已调用 set_data_dir() → 使用配置的路径
    - 冻结态未配置 → 使用平台应用数据目录
    - 开发模式且未配置 → 使用项目 ./data
    """
    return str(_data_dir or resolve_data_dir())


def _get_data_path() -> Path:
    """获取 tasks.json 的完整路径"""
    return Path(get_data_dir()) / "tasks.json"


def load_tasks() -> List[Task]:
    """从 data/tasks.json 加载全部任务。

    文件不存在或损坏时返回空列表。
    """
    path = _get_data_path()
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    tasks_data = data.get("tasks", [])
    return [Task.from_dict(t) for t in tasks_data]


def save_tasks(tasks: List[Task]) -> None:
    """将任务列表原子写入 data/tasks.json。

    先写临时文件，再 os.replace() 原子重命名，
    防止多进程并发写入导致数据损坏。
    """
    path = _get_data_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": 2,
        "tasks": [t.to_dict() for t in tasks],
    }

    tmp_path = path.with_name(path.name + ".tmp")
    # 清理上次崩溃可能残留的 .tmp 文件
    if tmp_path.exists():
        tmp_path.unlink()
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        import os
        os.fsync(f.fileno())
    tmp_path.replace(path)
