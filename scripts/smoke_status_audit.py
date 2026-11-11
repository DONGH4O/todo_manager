"""Run after the frontend build: python scripts/smoke_status_audit.py.

Starts two separate Qt desktop processes, then reads the isolated store with CLI.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import date

ROOT = Path(__file__).resolve().parents[1]


def run_window(data_dir, phase):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from todo_manager.gui.main import main

    app = QApplication.instance() or QApplication([])
    script = Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
    checking = False

    def finish(result):
        if result:
            if result != "ok":
                print(result, file=sys.stderr, flush=True)
            app.exit(0 if result == "ok" else 1)

    def check():
        nonlocal checking
        view = next((w for w in app.topLevelWidgets() if isinstance(w, QWebEngineView)), None)
        if not view:
            return
        if checking:
            view.page().runJavaScript("window.auditResult || ''", finish)
            return

        def ready(value):
            nonlocal checking
            if checking or not value:
                return
            checking = True
            view.page().runJavaScript(script + f"\ncheckDesktop({json.dumps(phase)})"
                                      ".then(() => window.auditResult = 'ok', "
                                      "e => window.auditResult = String(e.stack || e));")

        view.page().runJavaScript("Boolean(window.todoBridge && document.querySelector('aside input'))", ready)

    timer = QTimer()
    timer.timeout.connect(check)
    timer.start(50)
    QTimer.singleShot(30000, lambda: finish("Timed out waiting for the Qt desktop test"))
    return main(["--data-dir", data_dir, "--react-root", str(ROOT / "frontend/out")])


def check_restart(data_dir):
    def cli(*args):
        output = subprocess.check_output([sys.executable, "-m", "todo_manager.cli", *args,
                                          "--data-dir", data_dir, "--json"])
        return json.loads(output)["result"]

    start = date.today().isoformat()
    parent = cli("add", "父任务", "--end", "2099-12-31", "--status", "完成中")["task"]["id"]
    child = cli("sub", "add", parent, "子任务 A", "--status", "完成中")["subtask"]["id"]
    for phase in ("edit", "restart"):
        subprocess.run([sys.executable, __file__, "--window", data_dir, phase], check=True, timeout=45)
    dates = ["--from", start, "--to", date.today().isoformat(), "--level", "subtask"]
    summary, = cli("completed", *dates)["tasks"]
    event, = cli("status-history", *dates, "--to-status", "已完成")["events"]
    assert (summary["task_id"], summary["completion_count"]) == (child, 1), summary
    assert (event["task_id"], event["parent_id"], event["from_status"], event["to_status"]) == (
        child, parent, "完成中", "已完成"), event
    children = cli("sub", "list", parent)["subtasks"]
    assert [(s["title"], s["status"]) for s in children] == [
        ("子任务 A", "已完成"), ("子任务 B", "未启动")], children
    print("PASS: Qt restart; CLI found one completion for A, B retained; all four audit regressions passed.")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--window"]:
        sys.exit(run_window(*sys.argv[2:]))
    with tempfile.TemporaryDirectory(prefix="todo-status-audit-") as data:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        check_restart(data)
