"""M6.5 QtWebEngine React shell bridge tests."""

from __future__ import annotations

import json

from todo_manager.gui import react_shell
from todo_manager.gui.react_shell import TodoBridge


def test_react_shell_bridge_uses_cli_json_contract(tmp_path):
    bridge = TodoBridge(data_dir=str(tmp_path))

    created = json.loads(
        bridge.request(
            json.dumps(
                {
                    "action": "createTask",
                    "payload": {
                        "title": "M6.5 桥接任务",
                        "start_date": "2026-05-24",
                        "end_date": "2026-05-24",
                        "status": "未启动",
                        "background": "由 QtWebEngine 桌面桥调用 CLI JSON 创建",
                    },
                },
                ensure_ascii=False,
            )
        )
    )
    assert created["ok"] is True

    task_id = created["result"]["id"]
    updated = json.loads(
        bridge.request(
            json.dumps(
                {
                    "action": "updateTask",
                    "payload": {"taskId": task_id, "update": {"status": "完成中"}},
                },
                ensure_ascii=False,
            )
        )
    )
    assert updated["ok"] is True
    assert updated["result"]["status"] == "完成中"

    listed = json.loads(bridge.request(json.dumps({"action": "listTasks"})))
    assert listed["ok"] is True
    assert len(listed["result"]) == 1
    assert listed["result"][0]["id"] == task_id

    deleted = json.loads(
        bridge.request(
            json.dumps(
                {
                    "action": "deleteTask",
                    "payload": {"taskId": task_id},
                }
            )
        )
    )
    assert deleted["ok"] is True
    assert deleted["result"]["deleted"] is True

    listed_after_delete = json.loads(bridge.request(json.dumps({"action": "listTasks"})))
    assert listed_after_delete["ok"] is True
    assert listed_after_delete["result"] == []

    restored = json.loads(
        bridge.request(
            json.dumps(
                {
                    "action": "undoTask",
                    "payload": {"taskId": task_id},
                }
            )
        )
    )
    assert restored["ok"] is True
    assert restored["result"]["deleted"] is False


def test_react_shell_bridge_decodes_windows_frozen_cli_output(monkeypatch, tmp_path):
    envelope = {
        "ok": True,
        "command": "list",
        "result": {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "编码验证",
                    "start_date": "2026-05-24",
                    "end_date": "2026-05-24",
                    "status": "完成中",
                    "background": "Windows frozen CLI may emit local-codepage bytes.",
                    "subtasks": [],
                }
            ]
        },
    }
    raw = json.dumps(envelope, ensure_ascii=False).encode("gbk")

    monkeypatch.setattr(react_shell.locale, "getpreferredencoding", lambda do_setlocale=False: "gbk")
    decoded = react_shell._decode_cli_stream(raw)
    response = json.loads(decoded)

    assert response["ok"] is True
    assert response["result"]["tasks"][0]["title"] == "编码验证"
    assert response["result"]["tasks"][0]["status"] == "完成中"
