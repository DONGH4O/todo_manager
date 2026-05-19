"""Cross-platform application path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping


APP_NAME = "TodoManager"


def is_frozen() -> bool:
    """Return whether the app is running from a frozen bundle."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Return the source checkout root used by development mode."""
    return Path(__file__).resolve().parents[1]


def _home_dir(home: Path | None = None) -> Path:
    return home if home is not None else Path.home()


def default_data_dir(
    *,
    platform: str | None = None,
    frozen: bool | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the default data directory for the current execution mode.

    Development mode intentionally stays inside the source checkout. Frozen
    builds use the host platform's standard per-user application data area.
    Optional keyword arguments are test seams for platform simulation.
    """
    platform_name = platform if platform is not None else sys.platform
    running_frozen = is_frozen() if frozen is None else frozen
    environ = os.environ if env is None else env

    if not running_frozen:
        return project_root() / "data"

    if platform_name.startswith("win"):
        appdata = environ.get("APPDATA")
        base = Path(appdata) if appdata else _home_dir(home) / "AppData" / "Roaming"
        return base / APP_NAME / "data"

    if platform_name == "darwin":
        return _home_dir(home) / "Library" / "Application Support" / APP_NAME / "data"

    return _home_dir(home) / ".local" / "share" / APP_NAME / "data"


def resolve_data_dir(explicit_data_dir: str | os.PathLike[str] | None = None) -> Path:
    """Resolve an explicit data directory or the platform default."""
    if explicit_data_dir is None:
        return default_data_dir()

    path = Path(explicit_data_dir).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()
