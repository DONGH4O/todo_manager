"""M1 source entrypoint smoke tests."""

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PARENT = PROJECT_ROOT.parent


def _run_source_module(module: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=SOURCE_PARENT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def test_cli_source_module_help_smoke():
    result = _run_source_module("todo_manager.cli", "--help")

    assert result.returncode == 0
    assert "todo" in result.stdout
    assert "命令" in result.stdout


def test_cli_source_module_data_dir_smoke(tmp_path):
    result = _run_source_module(
        "todo_manager.cli",
        "--data-dir",
        str(tmp_path),
        "add",
        "跨平台 smoke",
        "-s",
        "2026-05-19",
        "-e",
        "2026-05-19",
        "--status",
        "未启动",
    )

    assert result.returncode == 0, result.stderr
    assert "已创建任务" in result.stdout
    assert "数据目录" not in result.stdout
    assert (tmp_path / "tasks.json").is_file()


def test_gui_source_module_help_smoke():
    result = _run_source_module("todo_manager.gui", "--help")

    assert result.returncode == 0
    assert "todo-gui" in result.stdout
    assert "--data-dir" in result.stdout
