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


def test_frozen_gui_resolves_embedded_renderer(monkeypatch, tmp_path):
    embedded = tmp_path / "bundle" / "desktop-react" / "ui" / "index.html"
    embedded.parent.mkdir(parents=True)
    embedded.write_text("<!doctype html>", encoding="utf-8")
    monkeypatch.setattr(react_shell.sys, "frozen", True, raising=False)
    monkeypatch.setattr(react_shell.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(react_shell.sys, "executable", str(tmp_path / "Applications" / "TodoManager.app" / "Contents" / "MacOS" / "todo-gui"))
    assert react_shell._resolve_index_html() == embedded


def test_explicit_renderer_overrides_embedded_renderer(monkeypatch, tmp_path):
    monkeypatch.setattr(react_shell.sys, "frozen", True, raising=False)
    monkeypatch.setattr(react_shell.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    explicit = tmp_path / "preview" / "index.html"
    explicit.parent.mkdir()
    explicit.write_text("<!doctype html>", encoding="utf-8")
    assert react_shell._resolve_index_html(str(explicit.parent)) == explicit


def test_desktop_marker_survives_document_creation_before_html_exists():
    import json
    import shutil
    import subprocess
    from pathlib import Path
    import pytest

    node = shutil.which("node")
    local_node = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "node"
    if not node and local_node.exists():
        node = str(local_node)
    if not node:
        pytest.skip("Node is required to exercise the injected desktop script")

    scripts = []

    class Scripts:
        def insert(self, script):
            scripts.append(script.sourceCode())

    class Page:
        def scripts(self):
            return Scripts()

    class View:
        def page(self):
            return Page()

    react_shell._install_desktop_shell_script(View())
    program = """
const fs = require('node:fs');
const vm = require('node:vm');
global.window = {};
const listeners = {};
global.document = {
  documentElement: null,
  addEventListener: (name, handler) => { listeners[name] = handler; }
};
vm.runInThisContext(fs.readFileSync(0, 'utf8'));
if (window.todoDesktopShell !== true) throw Error('Desktop flag missing');
document.documentElement = { dataset: {} };
listeners.DOMContentLoaded();
if (document.documentElement.dataset.desktopShell !== 'true') throw Error('Late HTML marker missing');
console.log(JSON.stringify(document.documentElement.dataset));
"""
    result = subprocess.run([node, "-e", program], input=scripts[0], text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"desktopShell": "true"}
