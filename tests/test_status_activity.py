import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

from todo_manager.cli.main import main
from todo_manager.engine import storage, task_manager as tm
from todo_manager.gui.react_shell import TodoBridge


@pytest.fixture
def data(tmp_path):
    storage.set_data_dir(tmp_path)
    yield tmp_path
    storage.clear_data_dir()


def test_legacy_records_and_local_midnight(data, monkeypatch):
    day = "2026-11-02"
    legacy = dict(id="legacy-0001", title="此前完成", start_date=day, end_date=day,
                  status="已完成", background="")
    (data / "tasks.json").write_text(json.dumps({"version": 2, "tasks": [legacy]}))
    assert not tm.completed_tasks(day, day)
    midnight = datetime.fromisoformat(day)
    for moment, status in [(midnight, "完成中"), (midnight + timedelta(days=1, microseconds=-1), "已完成"),
                           (midnight + timedelta(days=1), "完成中")]:
        stamp = moment.astimezone(timezone.utc).isoformat()
        monkeypatch.setattr(tm, "_now_iso", lambda: stamp)
        tm.update_task("legacy-0001", status=status)
    events = tm.status_history(day, day)
    assert [e.to_status for e in events] == ["已完成", "完成中"]
    assert events[-1].from_status == "已完成"
    assert tm.completed_tasks(day, day)[0]["completion_count"] == 1


def test_bridge_cli_reports_and_atomic_failure(data, capsys, monkeypatch):
    day = datetime.now().date().isoformat()
    args = ["--from", day, "--to", day, "--data-dir", str(data), "--json"]
    bridge = TodoBridge(str(data))

    def request(action, **payload):
        return json.loads(bridge.request(json.dumps(dict(action=action, payload=payload))))

    fields = dict(title="父", start_date=day, end_date=day, status="已完成", background="")
    parent = request("createTask", **fields)["result"]["id"]
    child = request("createSubtask", taskId=parent, input={**fields, "title": "子", "status": "未启动"})["result"]["id"]
    assert not request("updateTask", taskId=parent, update={"title": "不应保存"},
                       subtaskStatuses={child: "已完成", "unknown": "完成中"})["ok"]
    assert tm.get_task(parent).title == "父"
    assert len(tm.get_subtask(parent, child).status_events) == 1
    assert request("updateTask", taskId=parent, update={"status": "完成中"},
                   subtaskStatuses={child: "已完成"})["ok"]
    assert main(["edit", parent, "--status", "已完成", "--title", "完成时", "--json", "--data-dir", str(data)]) == 0
    capsys.readouterr()
    tm.update_task(parent, status="已完成", title="后来改名")
    tm.delete_subtask(parent, child)
    tm.delete_task(parent)
    assert main(["completed", *args]) == 0
    rows = json.loads(capsys.readouterr().out)["result"]["tasks"]
    assert [(r["title"], r["completion_count"]) for r in rows] == [("完成时", 2), ("子", 1)]
    tm.undo_task(parent)
    tm.undo_subtask(parent, child)
    assert main(["status-history", *args, "--to-status", "已完成", "--level", "subtask"]) == 0
    event, = json.loads(capsys.readouterr().out)["result"]["events"]
    assert (event["parent_id"], event["task_id"], event["from_status"]) == (parent, child, "未启动")
    assert tm.status_history(day, day)[-1].event_type == "created"
    assert main(["completed", *args, "--from", "2026-02-30"]) == 3
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "validation_error"
    assert main(["completed", *args, "--to", "2000-01-01"]) == 3
    capsys.readouterr()
    before = (data / "tasks.json").read_bytes()

    def fail_replace(*args):
        raise OSError("simulated write failure")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    assert not request("updateTask", taskId=parent, update={"status": "完成中"})["ok"]
    assert (data / "tasks.json").read_bytes() == before


def test_parallel_cli_writers(data):
    commands = [
        [sys.executable, "-m", "todo_manager.cli", "add", str(i), "--status", "已完成",
         "--data-dir", str(data), "--json"] for i in range(10)
    ]
    writers = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for cmd in commands]
    for writer in writers:
        out, err = writer.communicate(timeout=30)
        assert writer.returncode == 0, err
        assert json.loads(out)["ok"]
    day = datetime.now().date().isoformat()
    assert len({event.event_id for event in tm.status_history(day, day)}) == len(writers)
