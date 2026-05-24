"""Run a small CLI JSON smoke test for GitHub Actions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cli(args: list[str], data_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "todo_manager.cli",
            "--data-dir",
            str(data_dir),
            "--json",
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def _require_success(result: subprocess.CompletedProcess[str], label: str) -> dict:
    if result.returncode != 0:
        raise SystemExit(
            f"{label} failed with exit {result.returncode}: {result.stderr.strip()}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} did not return JSON: {result.stdout!r}") from exc
    if payload.get("ok") is not True:
        raise SystemExit(f"{label} returned non-success payload: {payload!r}")
    return payload


def main() -> int:
    runner_temp = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()
    data_dir = Path(runner_temp) / "todo-ci-smoke"

    created = _require_success(
        _run_cli(
            [
                "add",
                "CI smoke task",
                "-s",
                "2026-05-24",
                "-e",
                "2026-05-24",
                "--status",
                "未启动",
            ],
            data_dir,
        ),
        "todo add --json",
    )
    task_id = created["result"]["task"]["id"]

    listed = _require_success(_run_cli(["list"], data_dir), "todo list --json")
    tasks = listed["result"]["tasks"]
    if task_id not in {task["id"] for task in tasks}:
        raise SystemExit("Created task was not present in list output")

    print(f"[OK] CLI JSON smoke passed: {task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
