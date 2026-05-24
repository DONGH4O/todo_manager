"""Build cross-platform release artifacts for Todo Manager.

Usage:
    python scripts/build.py all
    python scripts/build.py cli
    python scripts/build.py gui
    python scripts/build.py react
    python scripts/build.py zip
    python scripts/build.py smoke

The script builds the current host platform only. Run it once on Windows and
once on macOS to produce the two supported release bundles.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_ROOT = ROOT / "dist"
APP_DIR_NAME = "TodoManager"
DIST = DIST_ROOT / APP_DIR_NAME
BUILD_ROOT = ROOT / "build"
FRONTEND_ROOT = ROOT / "frontend"
REACT_DESKTOP_DIR = DIST / "desktop-react"


@dataclass(frozen=True)
class PlatformProfile:
    key: str
    display_name: str
    cli_artifact: str
    gui_artifact: str
    data_dir_hint: str
    gui_launch_hint: str
    signing_note: str
    include_install_bat: bool


WINDOWS_PROFILE = PlatformProfile(
    key="windows",
    display_name="Windows",
    cli_artifact="todo.exe",
    gui_artifact="todo-gui.exe",
    data_dir_hint=r"%APPDATA%\TodoManager\data\tasks.json",
    gui_launch_hint="Double-click todo-gui.exe or run it from PowerShell to start the React desktop GUI.",
    signing_note="This M6 build script does not apply Authenticode signing.",
    include_install_bat=True,
)

MACOS_PROFILE = PlatformProfile(
    key="macos",
    display_name="macOS",
    cli_artifact="todo",
    gui_artifact="TodoManager.app",
    data_dir_hint="~/Library/Application Support/TodoManager/data/tasks.json",
    gui_launch_hint="Run open TodoManager.app, or open the app bundle in Finder to start the React desktop GUI.",
    signing_note="This M6 build script creates an unsigned, unnotarized .app.",
    include_install_bat=False,
)


def profile_for_platform(sys_platform: str | None = None) -> PlatformProfile:
    value = (sys_platform or sys.platform).lower()
    if value in {"windows", "win32"} or value.startswith("win"):
        return WINDOWS_PROFILE
    if value in {"macos", "darwin"}:
        return MACOS_PROFILE
    raise SystemExit(
        "Unsupported build host. M6 release builds support Windows and macOS only."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=("all", "cli", "gui", "react", "zip", "smoke"),
        help="Release target to build or validate.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Do not run scripts/smoke_release.py after an all/zip build.",
    )
    return parser.parse_args(argv)


def run(cmd: list[str], description: str = "", *, cwd: Path = ROOT) -> None:
    if description:
        print(f"  {description}...")
    sys.stdout.flush()
    result = subprocess.run(cmd, cwd=str(cwd), check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def require_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is not installed. Run: python -m pip install -e .[dev]"
        ) from exc


def clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Cleaned {DIST}")


def build_cli(profile: PlatformProfile) -> None:
    print(f"\n[BUILD] CLI - {profile.cli_artifact}")
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "build_cli.spec",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD_ROOT / f"{profile.key}-cli"),
            "--noconfirm",
        ],
        "PyInstaller CLI",
    )
    print(f"[OK] {profile.cli_artifact} built")


def build_gui(profile: PlatformProfile) -> None:
    print(f"\n[BUILD] GUI - {profile.gui_artifact}")
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "build_gui.spec",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD_ROOT / f"{profile.key}-gui"),
            "--noconfirm",
        ],
        "PyInstaller GUI",
    )
    print(f"[OK] {profile.gui_artifact} built")


def create_readme(profile: PlatformProfile) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    readme = DIST / "Readme.txt"
    today = date.today().isoformat()

    text = f"""Todo Manager Release
{"=" * 48}
Platform: {profile.display_name}
Build date: {today}

Artifacts
---------
- CLI: {profile.cli_artifact}
- GUI: {profile.gui_artifact}
- React desktop assets: desktop-react/
- Application icon: embedded from assets/icons/todo-manager.*

Quick Start
-----------
1. Extract the complete zip before running the app.
2. CLI help: {profile.cli_artifact} --help
3. GUI: {profile.gui_launch_hint}
4. Compatibility launcher: run todo-react.bat on Windows or ./todo-react on macOS.

Data Storage
------------
Default data file:
  {profile.data_dir_hint}

Use --data-dir <path> for an isolated data directory during smoke tests.

Signing / Notarization
----------------------
{profile.signing_note}

Release Validation
------------------
Run this from the source checkout after building:
  python scripts/smoke_release.py --platform {profile.key} --release-dir dist/{APP_DIR_NAME}
"""
    readme.write_text(text, encoding="utf-8")
    print("[OK] Readme.txt")


def create_install_bat() -> None:
    bat = DIST / "install.bat"
    content = r"""@echo off
chcp 65001 >nul
echo ============================================
echo   Todo Manager - Add to User PATH
echo ============================================
echo.
echo Current directory: %~dp0
echo.

set "TARGET_DIR=%~dp0"
set "TARGET_DIR=%TARGET_DIR:~0,-1%"

for /f "usebackq tokens=2,*" %%A in (`reg query HKCU\Environment /v PATH 2^>nul`) do (
    set "USER_PATH=%%B"
)

echo %USER_PATH% | find /i "%TARGET_DIR%" >nul
if %errorlevel% equ 0 (
    echo [OK] Directory already in PATH.
) else (
    setx PATH "%USER_PATH%;%TARGET_DIR%"
    echo [OK] Added %TARGET_DIR% to user PATH.
)

echo.
echo Done. Reopen your terminal and run: todo --help
echo.
pause
"""
    bat.write_text(content, encoding="utf-8")
    print("[OK] install.bat")


def npm_command() -> str:
    return "npm.cmd" if sys.platform.startswith("win") else "npm"


def copy_react_desktop_assets(profile: PlatformProfile) -> None:
    out_dir = FRONTEND_ROOT / "out"
    if not out_dir.exists():
        raise SystemExit("React static export is missing. Run npm run build in frontend/.")

    if REACT_DESKTOP_DIR.exists():
        shutil.rmtree(REACT_DESKTOP_DIR)
    (REACT_DESKTOP_DIR / "ui").mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        out_dir,
        REACT_DESKTOP_DIR / "ui",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("node_modules", ".next", "*.tsbuildinfo"),
    )

    manifest = REACT_DESKTOP_DIR / "manifest.json"
    manifest.write_text(
        (
            "{\n"
            '  "name": "Todo Manager React Desktop",\n'
            '  "shell": "PySide6 QtWebEngine",\n'
            '  "renderer": "ui/index.html",\n'
            '  "bridge": "CLI JSON contract",\n'
            '  "launcher": "todo-gui",\n'
            f'  "platform": "{profile.key}"\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    print("[OK] desktop-react assets")


def create_react_launcher(profile: PlatformProfile) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    if profile.key == "windows":
        launcher = DIST / "todo-react.bat"
        launcher.write_text(
            r"""@echo off
chcp 65001 >nul
set "APP_DIR=%~dp0"
"%APP_DIR%todo-gui.exe" %*
""",
            encoding="utf-8",
        )
    else:
        launcher = DIST / "todo-react"
        launcher.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${APP_DIR}/TodoManager.app/Contents/MacOS/todo-gui" "$@"
""",
            encoding="utf-8",
        )
        launcher.chmod(0o755)
    print(f"[OK] {launcher.name}")


def build_react_desktop(profile: PlatformProfile) -> None:
    print("\n[BUILD] React desktop renderer")
    if not (FRONTEND_ROOT / "package.json").exists():
        raise SystemExit("frontend/package.json is missing")
    DIST.mkdir(parents=True, exist_ok=True)
    run([npm_command(), "run", "build:desktop"], "Next static export", cwd=FRONTEND_ROOT)
    copy_react_desktop_assets(profile)


def create_release_metadata(profile: PlatformProfile) -> None:
    create_readme(profile)
    if profile.include_install_bat:
        create_install_bat()
    create_react_launcher(profile)


def create_zip(profile: PlatformProfile) -> Path:
    if not DIST.exists():
        raise SystemExit(f"Release directory does not exist: {DIST}")

    print("\n[ZIP] Packaging release directory...")
    zip_name = f"{APP_DIR_NAME}-{profile.key}-{date.today().isoformat()}.zip"
    zip_path = DIST_ROOT / zip_name
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(DIST.rglob("*")):
            if file_path.is_file():
                arcname = Path(APP_DIR_NAME) / file_path.relative_to(DIST)
                zf.write(file_path, arcname.as_posix())

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] {zip_name} ({size_mb:.1f} MB)")
    return zip_path


def run_release_smoke(profile: PlatformProfile, zip_path: Path | None = None) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "smoke_release.py"),
        "--platform",
        profile.key,
        "--release-dir",
        str(DIST),
    ]
    if zip_path is not None:
        cmd.extend(["--zip", str(zip_path)])
    run(cmd, "Release smoke")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile = profile_for_platform()
    zip_path: Path | None = None

    print("=" * 52)
    print(f"  Todo Manager - {profile.display_name} Release Build")
    print("=" * 52)

    try:
        if args.target in {"all", "cli", "gui"}:
            require_pyinstaller()

        if args.target in {"all", "cli", "gui"}:
            clean_dist()

        if args.target in {"all", "cli"}:
            build_cli(profile)
        if args.target in {"all", "gui"}:
            build_gui(profile)
        if args.target in {"all", "cli", "gui", "react"}:
            create_release_metadata(profile)
        if args.target in {"all", "react"}:
            build_react_desktop(profile)
        if args.target in {"all", "zip"}:
            zip_path = create_zip(profile)
        if args.target == "smoke":
            run_release_smoke(profile)
        if args.target in {"all", "zip"} and not args.skip_smoke:
            run_release_smoke(profile, zip_path)

        if args.target == "all":
            print(f"\n[DONE] Build complete: {DIST}")
            print(f"  CLI: {profile.cli_artifact}")
            print(f"  GUI: {profile.gui_artifact}")
            print("  React desktop assets: desktop-react/")
            if zip_path:
                print(f"  Zip: {zip_path}")
    finally:
        if BUILD_ROOT.exists():
            shutil.rmtree(BUILD_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
