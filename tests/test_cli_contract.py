"""M3 CLI agent contract subprocess tests."""

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PARENT = PROJECT_ROOT.parent


def _run_cli(*args: str, data_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    cmd = [sys.executable, "-m", "todo_manager.cli"]
    if data_dir is not None:
        cmd.extend(["--data-dir", str(data_dir)])
    cmd.extend(args)
    return subprocess.run(
        cmd,
        cwd=SOURCE_PARENT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def _json_stdout(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.stderr == ""
    return json.loads(result.stdout)


def _json_stderr(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.stdout == ""
    return json.loads(result.stderr)


def test_json_crud_undo_workflow(tmp_path):
    add = _run_cli(
        "--json",
        "add",
        "契约任务",
        "-s",
        "2026-05-19",
        "-e",
        "2026-05-20",
        "--status",
        "未启动",
        data_dir=tmp_path,
    )
    assert add.returncode == 0, add.stderr
    payload = _json_stdout(add)
    assert payload["ok"] is True
    task = payload["result"]["task"]
    task_id = task["id"]
    assert task["title"] == "契约任务"

    sub_add = _run_cli(
        "sub",
        "add",
        task_id,
        "契约子任务",
        "-s",
        "2026-05-19",
        "-e",
        "2026-05-19",
        "--json",
        data_dir=tmp_path,
    )
    assert sub_add.returncode == 0, sub_add.stderr
    subtask_id = _json_stdout(sub_add)["result"]["subtask"]["id"]

    edited = _run_cli(
        "edit",
        task_id,
        "--status",
        "完成中",
        "--json",
        data_dir=tmp_path,
    )
    assert edited.returncode == 0, edited.stderr
    assert _json_stdout(edited)["result"]["task"]["status"] == "完成中"

    listed = _run_cli("list", "--json", data_dir=tmp_path)
    assert listed.returncode == 0, listed.stderr
    list_payload = _json_stdout(listed)
    assert [item["id"] for item in list_payload["result"]["tasks"]] == [task_id]

    shown = _run_cli("--json", "show", task_id, data_dir=tmp_path)
    assert shown.returncode == 0, shown.stderr
    assert _json_stdout(shown)["result"]["task"]["subtasks"][0]["id"] == subtask_id

    sub_deleted = _run_cli("sub", "delete", task_id, subtask_id, "--json", data_dir=tmp_path)
    assert sub_deleted.returncode == 0, sub_deleted.stderr
    sub_deleted_payload = _json_stdout(sub_deleted)
    assert sub_deleted_payload["result"]["deleted"] is True
    assert sub_deleted_payload["result"]["subtask"]["deleted"] is True

    sub_restored = _run_cli("sub", "undo", task_id, subtask_id, "--json", data_dir=tmp_path)
    assert sub_restored.returncode == 0, sub_restored.stderr
    assert _json_stdout(sub_restored)["result"]["subtask"]["deleted"] is False

    deleted = _run_cli("delete", task_id, "--json", data_dir=tmp_path)
    assert deleted.returncode == 0, deleted.stderr
    deleted_payload = _json_stdout(deleted)
    assert deleted_payload["result"]["deleted"] is True
    assert deleted_payload["result"]["task"]["deleted"] is True

    restored = _run_cli("undo", task_id, "--json", data_dir=tmp_path)
    assert restored.returncode == 0, restored.stderr
    restored_payload = _json_stdout(restored)
    assert restored_payload["result"]["restored"] is True
    assert restored_payload["result"]["task"]["deleted"] is False


def test_json_global_options_work_after_command(tmp_path):
    result = _run_cli(
        "add",
        "后置全局参数",
        "-s",
        "2026-05-19",
        "-e",
        "2026-05-19",
        "--json",
        "--data-dir",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    payload = _json_stdout(result)
    assert payload["ok"] is True
    assert payload["result"]["task"]["title"] == "后置全局参数"
    assert (tmp_path / "tasks.json").is_file()


def test_json_validation_error_schema(tmp_path):
    result = _run_cli(
        "--json",
        "add",
        "",
        "-s",
        "2026-05-19",
        "-e",
        "2026-05-19",
        data_dir=tmp_path,
    )

    assert result.returncode == 3
    payload = _json_stderr(result)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "validation_error"
    assert "不能为空" in payload["error"]["message"]


def test_json_not_found_error_schema(tmp_path):
    result = _run_cli("--json", "show", "missing-task", data_dir=tmp_path)

    assert result.returncode == 4
    payload = _json_stderr(result)
    assert payload["error"]["code"] == "not_found"
    assert "未找到任务" in payload["error"]["message"]


def test_json_data_file_error_schema(tmp_path):
    (tmp_path / "tasks.json").write_text("broken {{{", encoding="utf-8")

    result = _run_cli("--json", "list", data_dir=tmp_path)

    assert result.returncode == 5
    payload = _json_stderr(result)
    assert payload["error"]["code"] == "data_file_error"
    assert "不是合法 JSON" in payload["error"]["message"]
    assert list(tmp_path.glob("tasks.json.corrupt-*.bak"))


def test_json_usage_error_schema():
    result = _run_cli("--json", "unknown-command")

    assert result.returncode == 2
    payload = _json_stderr(result)
    assert payload["error"]["code"] == "usage_error"
