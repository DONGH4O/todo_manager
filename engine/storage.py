"""JSON 文件存储：读写 tasks.json"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from .models import Task
from .platform_paths import resolve_data_dir

# 数据文件目录 — 启动时由 set_data_dir() 配置
_data_dir: Path | None = None


class StorageError(RuntimeError):
    """Base class for user-actionable storage failures."""


class DataFileError(StorageError):
    """Raised when tasks.json cannot be safely read."""

    def __init__(
        self,
        message: str,
        *,
        path: Path,
        backup_path: Path | None = None,
        cause: BaseException | None = None,
    ):
        self.path = path
        self.backup_path = backup_path
        self.__cause__ = cause
        details = f"{message}: {path}"
        if backup_path is not None:
            details += f"；已备份为: {backup_path}"
        super().__init__(details)


class DataWriteError(StorageError):
    """Raised when tasks.json cannot be safely written."""


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def _backup_data_file(path: Path) -> Path:
    backup_path = path.with_name(f"{path.name}.corrupt-{_timestamp()}.bak")
    shutil.copy2(path, backup_path)
    return backup_path


def _cleanup_stale_temp_files(path: Path) -> None:
    """Best-effort cleanup for temp files left by interrupted writes."""
    patterns = (f"{path.name}.*.tmp", f"{path.name}.tmp")
    for pattern in patterns:
        for candidate in path.parent.glob(pattern):
            try:
                candidate.unlink()
            except OSError:
                pass


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

    文件不存在时返回空列表；文件损坏或无法读取时抛出 StorageError，
    防止调用方误把坏数据当作空任务列表继续写入。
    """
    path = _get_data_path()
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        try:
            backup_path = _backup_data_file(path)
        except OSError as backup_exc:
            raise DataFileError(
                "数据文件不是合法 JSON，且自动备份失败",
                path=path,
                cause=backup_exc,
            ) from backup_exc
        raise DataFileError(
            "数据文件不是合法 JSON",
            path=path,
            backup_path=backup_path,
            cause=exc,
        ) from exc
    except OSError as exc:
        raise DataFileError("无法读取数据文件", path=path, cause=exc) from exc

    if not isinstance(data, dict):
        backup_path = _backup_data_file(path)
        raise DataFileError("数据文件结构无效", path=path, backup_path=backup_path)

    tasks_data = data.get("tasks", [])
    if not isinstance(tasks_data, list):
        backup_path = _backup_data_file(path)
        raise DataFileError("数据文件 tasks 字段无效", path=path, backup_path=backup_path)

    try:
        return [Task.from_dict(t) for t in tasks_data]
    except (TypeError, ValueError) as exc:
        backup_path = _backup_data_file(path)
        raise DataFileError(
            "数据文件任务结构无效",
            path=path,
            backup_path=backup_path,
            cause=exc,
        ) from exc


def save_tasks(tasks: List[Task]) -> None:
    """将任务列表原子写入 data/tasks.json。

    先写临时文件，再 os.replace() 原子重命名，
    防止多进程并发写入导致数据损坏。
    """
    path = _get_data_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DataWriteError(f"无法创建数据目录: {path.parent}") from exc

    data = {
        "version": 2,
        "tasks": [t.to_dict() for t in tasks],
    }

    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{_timestamp()}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise DataWriteError(f"无法写入数据文件: {path}") from exc
    _cleanup_stale_temp_files(path)
