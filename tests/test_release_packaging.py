"""M6 release packaging script tests."""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    script_path = PROJECT_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_react_desktop_artifacts(base: Path) -> None:
    (base / "desktop-react" / "ui").mkdir(parents=True, exist_ok=True)
    (base / "desktop-react" / "manifest.json").write_text("{}", encoding="utf-8")
    (base / "desktop-react" / "ui" / "index.html").write_text("<!doctype html>", encoding="utf-8")


def test_build_profiles_match_windows_and_macos_artifacts():
    build = _load_script("build.py")

    assert build.profile_for_platform("win32").cli_artifact == "todo.exe"
    assert build.profile_for_platform("win32").gui_artifact == "todo-gui.exe"
    assert build.profile_for_platform("darwin").cli_artifact == "todo"
    assert build.profile_for_platform("darwin").gui_artifact == "TodoManager.app"


def test_gui_spec_embeds_application_icons():
    spec_text = (PROJECT_ROOT / "build_gui.spec").read_text(encoding="utf-8")

    assert "todo-manager.ico" in spec_text
    assert "todo-manager.icns" in spec_text
    assert "assets/icons" in spec_text
    assert (PROJECT_ROOT / "assets" / "icons" / "todo-manager.ico").exists()
    assert (PROJECT_ROOT / "assets" / "icons" / "todo-manager.icns").exists()
    assert (PROJECT_ROOT / "assets" / "icons" / "todo-manager.png").exists()


def test_react_status_controls_avoid_native_select_popups():
    create_task = (PROJECT_ROOT / "frontend" / "src" / "components" / "todo" / "CreateTaskModal.tsx").read_text(encoding="utf-8")
    create_subtask = (PROJECT_ROOT / "frontend" / "src" / "components" / "todo" / "CreateSubtaskModal.tsx").read_text(encoding="utf-8")
    subtask_row = (PROJECT_ROOT / "frontend" / "src" / "components" / "todo" / "SubtaskRow.tsx").read_text(encoding="utf-8")

    assert "StatusDropdown" in create_task
    assert "StatusDropdown" in create_subtask
    assert "StatusDropdown" in subtask_row
    assert "<select" not in create_task
    assert "<select" not in create_subtask


def test_qtwebengine_desktop_shell_has_stability_mode():
    shell = (PROJECT_ROOT / "gui" / "react_shell.py").read_text(encoding="utf-8")
    css = (PROJECT_ROOT / "frontend" / "src" / "app" / "globals.css").read_text(encoding="utf-8")

    assert 'dataset.desktopShell = "true"' in shell
    assert ':root[data-desktop-shell="true"]' in css
    assert "backdrop-filter: none" in css


def test_react_calendar_rule_caps_ongoing_tasks_at_today():
    date_ts = (PROJECT_ROOT / "frontend" / "src" / "lib" / "date.ts").read_text(encoding="utf-8")
    app_tsx = (PROJECT_ROOT / "frontend" / "src" / "components" / "TodoManagerApp.tsx").read_text(encoding="utf-8")
    today_rail = (PROJECT_ROOT / "frontend" / "src" / "components" / "todo" / "TodayRail.tsx").read_text(encoding="utf-8")
    calendar = (PROJECT_ROOT / "frontend" / "src" / "components" / "calendar" / "CalendarWorkbench.tsx").read_text(encoding="utf-8")

    assert "date <= today" in date_ts
    assert "shouldShowTaskOnDate(key, task, today)" in date_ts
    assert "shouldShowTaskOnDate(selectedDate, task, today)" in today_rail
    assert "shouldShowTaskOnDate(selectedDate, task, today)" in calendar
    assert "loadedTasks[0]" not in app_tsx


def test_release_tree_audit_accepts_expected_windows_layout(tmp_path):
    smoke = _load_script("smoke_release.py")
    profile = smoke.profile_for_platform("windows")

    for name in ("todo.exe", "todo-gui.exe", "Readme.txt", "install.bat", "todo-react.bat"):
        (tmp_path / name).write_text("placeholder", encoding="utf-8")
    _write_react_desktop_artifacts(tmp_path)

    assert smoke.audit_release_tree(tmp_path, profile) == []


def test_react_desktop_tree_audit_accepts_ci_dry_run_layout(tmp_path):
    smoke = _load_script("smoke_release.py")
    profile = smoke.profile_for_platform("windows")

    for name in ("Readme.txt", "install.bat", "todo-react.bat"):
        (tmp_path / name).write_text("placeholder", encoding="utf-8")
    _write_react_desktop_artifacts(tmp_path)

    assert smoke.audit_react_desktop_tree(tmp_path, profile) == []


def test_react_desktop_tree_audit_requires_platform_launcher(tmp_path):
    smoke = _load_script("smoke_release.py")
    profile = smoke.profile_for_platform("macos")

    (tmp_path / "Readme.txt").write_text("placeholder", encoding="utf-8")
    _write_react_desktop_artifacts(tmp_path)

    errors = smoke.audit_react_desktop_tree(tmp_path, profile)

    assert "missing React release artifact: todo-react" in errors


def test_release_tree_audit_rejects_cache_and_source_files(tmp_path):
    smoke = _load_script("smoke_release.py")
    profile = smoke.profile_for_platform("windows")

    for name in ("todo.exe", "todo-gui.exe", "Readme.txt", "install.bat", "todo-react.bat"):
        (tmp_path / name).write_text("placeholder", encoding="utf-8")
    _write_react_desktop_artifacts(tmp_path)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"cache")
    (tmp_path / "leaked_source.py").write_text("print('nope')", encoding="utf-8")
    (tmp_path / "desktop-react" / ".next").mkdir()
    (tmp_path / "desktop-react" / ".next" / "cache.txt").write_text("cache", encoding="utf-8")

    errors = smoke.audit_release_tree(tmp_path, profile)

    assert any("__pycache__" in error for error in errors)
    assert any("leaked_source.py" in error for error in errors)
    assert any(".next" in error for error in errors)


def test_zip_audit_accepts_macos_app_bundle_without_directory_entries(tmp_path):
    smoke = _load_script("smoke_release.py")
    profile = smoke.profile_for_platform("macos")
    zip_path = tmp_path / "TodoManager-macos-test.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("TodoManager/todo", "")
        zf.writestr("TodoManager/TodoManager.app/Contents/MacOS/todo-gui", "")
        zf.writestr("TodoManager/Readme.txt", "")
        zf.writestr("TodoManager/todo-react", "")
        zf.writestr("TodoManager/desktop-react/manifest.json", "{}")
        zf.writestr("TodoManager/desktop-react/ui/index.html", "<!doctype html>")

    assert smoke.audit_zip(zip_path, profile) == []


def test_help_smoke_requires_expected_text():
    smoke = _load_script("smoke_release.py")

    missing_react = smoke.validate_help_text(
        "usage: todo-gui [-h] [--data-dir DATA_DIR]",
        "GUI",
        ("todo", "--react"),
    )
    assert missing_react == "GUI --help output missing expected text: --react"

    assert (
        smoke.validate_help_text(
            "usage: todo-gui [-h] [--data-dir DATA_DIR] [--react]",
            "GUI",
            ("todo", "--react"),
        )
        is None
    )
