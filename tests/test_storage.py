"""存储模块单元测试"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from todo_manager.engine.models import Task
from todo_manager.engine.storage import (
    DataFileError,
    DataWriteError,
    load_tasks,
    save_tasks,
    set_data_dir,
)


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录并在测试后清理"""
    with tempfile.TemporaryDirectory() as tmp:
        set_data_dir(tmp)
        yield tmp


class TestLoadTasks:
    def test_empty_dir(self, temp_data_dir):
        tasks = load_tasks()
        assert tasks == []

    def test_valid_file(self, temp_data_dir):
        task = Task(
            id="test-id",
            title="测试任务",
            start_date="2026-04-01",
            end_date="2026-04-30",
            status="未启动",
            background="测试背景",
        )
        save_tasks([task])

        loaded = load_tasks()
        assert len(loaded) == 1
        assert loaded[0].id == "test-id"
        assert loaded[0].title == "测试任务"

    def test_corrupted_json(self, temp_data_dir):
        path = os.path.join(temp_data_dir, "tasks.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("这不是合法的 JSON {{{")

        with pytest.raises(DataFileError) as exc_info:
            load_tasks()

        assert "不是合法 JSON" in str(exc_info.value)
        backups = list(Path(temp_data_dir).glob("tasks.json.corrupt-*.bak"))
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "这不是合法的 JSON {{{"
        assert Path(path).read_text(encoding="utf-8") == "这不是合法的 JSON {{{"

    def test_invalid_tasks_schema_is_diagnosed(self, temp_data_dir):
        path = Path(temp_data_dir) / "tasks.json"
        path.write_text(
            json.dumps({"version": 2, "tasks": {"bad": "shape"}}, ensure_ascii=False),
            encoding="utf-8",
        )

        with pytest.raises(DataFileError) as exc_info:
            load_tasks()

        assert "tasks 字段无效" in str(exc_info.value)
        assert list(Path(temp_data_dir).glob("tasks.json.corrupt-*.bak"))


class TestSaveTasks:
    def test_creates_directory(self, temp_data_dir):
        """测试 save 自动创建 data 目录"""
        subdir = os.path.join(temp_data_dir, "nested")
        set_data_dir(subdir)
        save_tasks([])
        assert os.path.isdir(subdir)
        assert os.path.isfile(os.path.join(subdir, "tasks.json"))

    def test_roundtrip_multiple_tasks(self, temp_data_dir):
        tasks = [
            Task(id=f"id-{i}", title=f"任务{i}",
                 start_date="2026-04-01", end_date="2026-04-30",
                 status="未启动", background="bg")
            for i in range(5)
        ]
        save_tasks(tasks)
        loaded = load_tasks()
        assert len(loaded) == 5
        assert [t.id for t in loaded] == ["id-0", "id-1", "id-2", "id-3", "id-4"]

    def test_preserves_version_field(self, temp_data_dir):
        save_tasks([])
        path = os.path.join(temp_data_dir, "tasks.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["version"] == 2

    def test_roundtrip_preserves_history(self, temp_data_dir):
        from todo_manager.engine.models import VersionRecord
        task = Task(
            id="h-id",
            title="历史任务",
            start_date="2026-04-01",
            end_date="2026-04-15",
            status="未启动",
            background="bg",
            history=[
                VersionRecord(version=1, title="历史任务", start_date="2026-04-01",
                              end_date="2026-04-15", status="未启动", background="bg",
                              changed_at="2026-04-01T00:00:00")
            ]
        )
        save_tasks([task])
        loaded = load_tasks()
        assert len(loaded) == 1
        assert len(loaded[0].history) == 1
        assert loaded[0].history[0].version == 1

    def test_atomic_write_no_temp_leftover(self, temp_data_dir):
        """原子写入后不应残留 .tmp 临时文件。"""
        task = Task(id="atomic-test", title="原子测试",
                    start_date="2026-05-01", end_date="2026-05-15",
                    status="未启动", background="bg")
        save_tasks([task])
        tmp_path = os.path.join(temp_data_dir, "tasks.json.tmp")
        assert not os.path.exists(tmp_path)
        assert not list(Path(temp_data_dir).glob("tasks.json.*.tmp"))
        assert os.path.isfile(os.path.join(temp_data_dir, "tasks.json"))

    def test_atomic_write_preserves_data(self, temp_data_dir):
        """原子写入后数据完整可读。"""
        tasks = [
            Task(id=f"a-{i}", title=f"原子任务{i}",
                 start_date="2026-05-01", end_date="2026-05-10",
                 status="未启动", background="test")
            for i in range(10)
        ]
        save_tasks(tasks)
        loaded = load_tasks()
        assert len(loaded) == 10
        for i, t in enumerate(loaded):
            assert t.id == f"a-{i}"
            assert t.title == f"原子任务{i}"

    def test_concurrent_write_no_corruption(self, temp_data_dir):
        """模拟并发写入：两个 write 交错后数据不应损坏。"""
        task_a = Task(id="conc-a", title="并发A",
                       start_date="2026-05-01", end_date="2026-05-15",
                       status="未启动", background="")
        task_b = Task(id="conc-b", title="并发B",
                       start_date="2026-05-16", end_date="2026-05-30",
                       status="完成中", background="")
        # A 写入
        save_tasks([task_a])
        # B 写入（模拟 CLI 在 GUI 写入后立即写入）
        save_tasks([task_a, task_b])
        loaded = load_tasks()
        assert len(loaded) == 2
        ids = {t.id for t in loaded}
        assert ids == {"conc-a", "conc-b"}

    def test_stale_temp_files_cleaned_after_success(self, temp_data_dir):
        """成功写入后清理历史遗留临时文件，但不让清理影响本次写入。"""
        Path(temp_data_dir, "tasks.json.tmp").write_text("old", encoding="utf-8")
        Path(temp_data_dir, "tasks.json.123.tmp").write_text("old", encoding="utf-8")

        save_tasks([])

        assert not list(Path(temp_data_dir).glob("tasks.json*.tmp"))

    def test_atomic_write_failure_preserves_existing_file(self, temp_data_dir, monkeypatch):
        """替换失败时旧 tasks.json 应保持可读，临时文件应尽力清理。"""
        old_task = Task(id="old", title="旧数据",
                        start_date="2026-05-01", end_date="2026-05-10",
                        status="未启动", background="")
        new_task = Task(id="new", title="新数据",
                        start_date="2026-06-01", end_date="2026-06-10",
                        status="完成中", background="")
        save_tasks([old_task])

        def fail_replace(_src, _dst):
            raise OSError("simulated replace failure")

        monkeypatch.setattr("todo_manager.engine.storage.os.replace", fail_replace)

        with pytest.raises(DataWriteError):
            save_tasks([new_task])

        path = Path(temp_data_dir) / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert [item["id"] for item in data["tasks"]] == ["old"]
        assert not list(Path(temp_data_dir).glob("tasks.json.*.tmp"))
