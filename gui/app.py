"""Compatibility wrapper for the React desktop GUI entrypoint."""

from __future__ import annotations

from todo_manager.gui.react_shell import run_react_app


def run_app(data_dir: str | None = None, react_root: str | None = None) -> int:
    """Run the current GUI, which is the React desktop shell."""

    return run_react_app(data_dir=data_dir, react_root=react_root)
