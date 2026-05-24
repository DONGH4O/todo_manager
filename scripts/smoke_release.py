"""Smoke-test and audit Todo Manager release artifacts."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_NAMES = {
    ".next",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "playwright-report",
    "test-results",
    "tests",
}
FORBIDDEN_SUFFIXES = {".py", ".pyc", ".pyo", ".tsbuildinfo"}


@dataclass(frozen=True)
class ReleaseProfile:
    key: str
    required_artifacts: tuple[Path, ...]
    react_release_artifacts: tuple[Path, ...]
    react_desktop_artifacts: tuple[Path, ...]
    cli_help_path: Path
    gui_help_path: Path


REACT_DESKTOP_ARTIFACTS = (
    Path("desktop-react") / "manifest.json",
    Path("desktop-react") / "ui" / "index.html",
)


WINDOWS_PROFILE = ReleaseProfile(
    key="windows",
    required_artifacts=(
        Path("todo.exe"),
        Path("todo-gui.exe"),
        Path("Readme.txt"),
        Path("install.bat"),
        Path("todo-react.bat"),
    ),
    react_release_artifacts=(
        Path("Readme.txt"),
        Path("install.bat"),
        Path("todo-react.bat"),
    ),
    react_desktop_artifacts=REACT_DESKTOP_ARTIFACTS,
    cli_help_path=Path("todo.exe"),
    gui_help_path=Path("todo-gui.exe"),
)

MACOS_PROFILE = ReleaseProfile(
    key="macos",
    required_artifacts=(
        Path("todo"),
        Path("TodoManager.app"),
        Path("TodoManager.app") / "Contents" / "MacOS" / "todo-gui",
        Path("Readme.txt"),
        Path("todo-react"),
    ),
    react_release_artifacts=(
        Path("Readme.txt"),
        Path("todo-react"),
    ),
    react_desktop_artifacts=REACT_DESKTOP_ARTIFACTS,
    cli_help_path=Path("todo"),
    gui_help_path=Path("TodoManager.app") / "Contents" / "MacOS" / "todo-gui",
)


def profile_for_platform(value: str | None = None) -> ReleaseProfile:
    platform = (value or sys.platform).lower()
    if platform in {"windows", "win32"} or platform.startswith("win"):
        return WINDOWS_PROFILE
    if platform in {"macos", "darwin"}:
        return MACOS_PROFILE
    raise ValueError("Unsupported platform. Expected windows or macos.")


def _is_forbidden_path(parts: tuple[str, ...], suffix: str) -> bool:
    lowered = {part.lower() for part in parts}
    if lowered & FORBIDDEN_NAMES:
        return True
    return suffix.lower() in FORBIDDEN_SUFFIXES


def audit_release_tree(release_dir: Path, profile: ReleaseProfile) -> list[str]:
    errors: list[str] = []
    if not release_dir.exists():
        return [f"release directory is missing: {release_dir}"]
    if not release_dir.is_dir():
        return [f"release path is not a directory: {release_dir}"]

    for artifact in profile.required_artifacts:
        if not (release_dir / artifact).exists():
            errors.append(f"missing artifact: {artifact.as_posix()}")
    for artifact in profile.react_desktop_artifacts:
        if not (release_dir / artifact).exists():
            errors.append(f"missing React desktop artifact: {artifact.as_posix()}")

    for path in release_dir.rglob("*"):
        if _is_forbidden_path(path.relative_to(release_dir).parts, path.suffix):
            errors.append(f"forbidden release content: {path.relative_to(release_dir).as_posix()}")

    return errors


def audit_react_desktop_tree(release_dir: Path, profile: ReleaseProfile) -> list[str]:
    """Audit the React desktop release subset used by CI dry-runs."""
    errors: list[str] = []
    if not release_dir.exists():
        return [f"release directory is missing: {release_dir}"]
    if not release_dir.is_dir():
        return [f"release path is not a directory: {release_dir}"]

    for artifact in profile.react_release_artifacts:
        if not (release_dir / artifact).exists():
            errors.append(f"missing React release artifact: {artifact.as_posix()}")
    for artifact in profile.react_desktop_artifacts:
        if not (release_dir / artifact).exists():
            errors.append(f"missing React desktop artifact: {artifact.as_posix()}")

    for path in release_dir.rglob("*"):
        if _is_forbidden_path(path.relative_to(release_dir).parts, path.suffix):
            errors.append(f"forbidden release content: {path.relative_to(release_dir).as_posix()}")

    return errors


def _zip_has_path(names: set[str], rel_path: Path) -> bool:
    rel = rel_path.as_posix()
    dir_rel = f"{rel}/"
    return any(
        name == rel
        or name.endswith(f"/{rel}")
        or name.startswith(dir_rel)
        or f"/{dir_rel}" in f"/{name}"
        or name.endswith(f"/{dir_rel}")
        for name in names
    )


def audit_zip(
    zip_path: Path,
    profile: ReleaseProfile,
    required_artifacts: tuple[Path, ...] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not zip_path.exists():
        return [f"zip is missing: {zip_path}"]

    required = required_artifacts or profile.required_artifacts
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        for artifact in required:
            if not _zip_has_path(names, artifact):
                errors.append(f"zip missing artifact: {artifact.as_posix()}")
        for artifact in profile.react_desktop_artifacts:
            if not _zip_has_path(names, artifact):
                errors.append(f"zip missing React desktop artifact: {artifact.as_posix()}")
        for name in names:
            parts = tuple(part for part in Path(name).parts if part not in {"", "."})
            if _is_forbidden_path(parts, Path(name).suffix):
                errors.append(f"zip forbidden content: {name}")

    return errors


def find_latest_zip(release_dir: Path, profile: ReleaseProfile) -> Path | None:
    candidates = sorted(
        release_dir.parent.glob(f"TodoManager-{profile.key}-*.zip"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def validate_help_text(
    help_text: str,
    label: str,
    required_snippets: tuple[str, ...],
) -> str | None:
    lowered = help_text.lower()
    for snippet in required_snippets:
        if snippet.lower() not in lowered:
            return f"{label} --help output missing expected text: {snippet}"
    return None


def run_help_command(
    executable: Path,
    label: str,
    *,
    required_snippets: tuple[str, ...] = ("todo",),
) -> str | None:
    if not executable.exists():
        return f"{label} executable is missing: {executable}"

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    result = subprocess.run(
        [str(executable), "--help"],
        cwd=str(executable.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return f"{label} --help failed with exit {result.returncode}: {result.stderr.strip()}"
    return validate_help_text(result.stdout, label, required_snippets)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        default=None,
        choices=("windows", "macos"),
        help="Release platform. Defaults to the current host.",
    )
    parser.add_argument(
        "--release-dir",
        default=str(Path("dist") / "TodoManager"),
        type=Path,
        help="Directory containing extracted release artifacts.",
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        default=None,
        type=Path,
        help="Release zip to audit. Defaults to the latest platform zip in dist/.",
    )
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="Only audit files; do not run CLI/GUI --help.",
    )
    parser.add_argument(
        "--react-only",
        action="store_true",
        help="Audit only React desktop assets and compatibility launcher for CI dry-runs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile = profile_for_platform(args.platform)
    release_dir = args.release_dir

    if args.react_only:
        errors = audit_react_desktop_tree(release_dir, profile)
        zip_path = args.zip_path
    else:
        errors = audit_release_tree(release_dir, profile)
        zip_path = args.zip_path or find_latest_zip(release_dir, profile)

    if zip_path is not None:
        required_artifacts = profile.react_release_artifacts if args.react_only else None
        errors.extend(audit_zip(zip_path, profile, required_artifacts))

    if not args.react_only and not args.no_exec:
        cli_error = run_help_command(release_dir / profile.cli_help_path, "CLI")
        gui_error = run_help_command(
            release_dir / profile.gui_help_path,
            "GUI",
            required_snippets=("todo", "--react"),
        )
        errors.extend(error for error in (cli_error, gui_error) if error)

    if errors:
        print("[FAIL] release smoke failed")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.react_only:
        print(f"[OK] {profile.key} React desktop release dry-run passed: {release_dir}")
    else:
        print(f"[OK] {profile.key} release smoke passed: {release_dir}")
    if zip_path is not None:
        print(f"[OK] zip audited: {zip_path}")
    elif args.react_only:
        print("[OK] no release zip requested for React desktop dry-run")
    else:
        print("[WARN] no release zip found to audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
