"""M1 platform path tests."""

from pathlib import Path

import pytest

from todo_manager.engine.platform_paths import default_data_dir, project_root, resolve_data_dir
from todo_manager.engine.storage import clear_data_dir, get_data_dir, set_data_dir


@pytest.fixture(autouse=True)
def reset_data_dir():
    clear_data_dir()
    yield
    clear_data_dir()


def test_windows_frozen_uses_appdata():
    appdata = Path(r"C:\Users\me\AppData\Roaming")

    data_dir = default_data_dir(
        platform="win32",
        frozen=True,
        env={"APPDATA": str(appdata)},
        home=Path(r"C:\Users\me"),
    )

    assert data_dir == appdata / "TodoManager" / "data"


def test_windows_frozen_falls_back_to_roaming_home():
    home = Path(r"C:\Users\me")

    data_dir = default_data_dir(
        platform="win32",
        frozen=True,
        env={},
        home=home,
    )

    assert data_dir == home / "AppData" / "Roaming" / "TodoManager" / "data"


def test_macos_frozen_uses_application_support():
    home = Path("/Users/me")

    data_dir = default_data_dir(
        platform="darwin",
        frozen=True,
        env={},
        home=home,
    )

    assert data_dir == home / "Library" / "Application Support" / "TodoManager" / "data"


def test_development_default_uses_project_data_dir():
    assert default_data_dir(platform="darwin", frozen=False) == project_root() / "data"


def test_explicit_relative_data_dir_resolves_from_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    data_dir = resolve_data_dir(Path("待办 数据") / "nested")

    assert data_dir == (tmp_path / "待办 数据" / "nested").resolve()


def test_storage_uses_explicit_data_dir_override(tmp_path):
    expected = (tmp_path / "custom data").resolve()

    set_data_dir(expected)

    assert Path(get_data_dir()) == expected


def test_storage_default_uses_platform_resolver():
    assert Path(get_data_dir()) == project_root() / "data"
