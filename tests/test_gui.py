"""React desktop GUI entrypoint tests."""

from __future__ import annotations

from todo_manager.gui import app as gui_app
from todo_manager.gui import main as gui_main
from todo_manager.gui import react_shell


def test_gui_main_defaults_to_react_shell(monkeypatch, tmp_path):
    calls = []

    def fake_run_react_app(*, data_dir=None, react_root=None):
        calls.append({"data_dir": data_dir, "react_root": react_root})
        return 0

    monkeypatch.setattr(react_shell, "run_react_app", fake_run_react_app)

    assert gui_main.main(["--data-dir", str(tmp_path), "--react-root", "frontend/out"]) == 0
    assert calls == [{"data_dir": str(tmp_path), "react_root": "frontend/out"}]


def test_gui_main_accepts_legacy_react_flag_as_noop(monkeypatch):
    calls = []

    def fake_run_react_app(*, data_dir=None, react_root=None):
        calls.append({"data_dir": data_dir, "react_root": react_root})
        return 0

    monkeypatch.setattr(react_shell, "run_react_app", fake_run_react_app)

    assert gui_main.main(["--react"]) == 0
    assert calls == [{"data_dir": None, "react_root": None}]


def test_gui_app_wrapper_delegates_to_react_shell(monkeypatch, tmp_path):
    calls = []

    def fake_run_react_app(*, data_dir=None, react_root=None):
        calls.append({"data_dir": data_dir, "react_root": react_root})
        return 0

    monkeypatch.setattr(gui_app, "run_react_app", fake_run_react_app)

    assert gui_app.run_app(data_dir=str(tmp_path), react_root="frontend/out") == 0
    assert calls == [{"data_dir": str(tmp_path), "react_root": "frontend/out"}]
