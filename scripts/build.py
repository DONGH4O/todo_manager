"""Build script - package CLI + GUI as standalone exe.

Usage:
    python scripts/build.py           # Build all
    python scripts/build.py cli       # CLI only
    python scripts/build.py gui       # GUI only
    python scripts/build.py zip       # ZIP packaging only

Output:
    dist/TodoManager/
    ├── todo.exe
    ├── todo-gui.exe
    └── Readme.txt
"""

import os
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parent.parent
DIST = ROOT / 'dist' / 'TodoManager'
RELEASE_DIR = ROOT / 'dist'


def run(cmd: list, description: str = ""):
    """Run command, exit on failure."""
    if description:
        print(f"  {description}...")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=False)
    if result.returncode != 0:
        print(f"\n[FAIL] exit code {result.returncode}")
        sys.exit(result.returncode)


def clean_dist():
    """Clean output directory."""
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)
    print("[OK] Cleaned output directory")


def build_cli():
    """PyInstaller build CLI."""
    print("\n[BUILD] CLI - todo.exe")
    run([
        sys.executable, '-m', 'PyInstaller',
        'build_cli.spec',
        '--distpath', str(DIST),
        '--workpath', str(ROOT / 'build' / 'cli'),
        '--noconfirm',
    ], "PyInstaller CLI")
    print("[OK] todo.exe built")


def build_gui():
    """PyInstaller build GUI."""
    print("\n[BUILD] GUI - todo-gui.exe")
    run([
        sys.executable, '-m', 'PyInstaller',
        'build_gui.spec',
        '--distpath', str(DIST),
        '--workpath', str(ROOT / 'build' / 'gui'),
        '--noconfirm',
    ], "PyInstaller GUI")
    print("[OK] todo-gui.exe built")


def create_readme():
    """Generate usage guide."""
    readme = DIST / 'Readme.txt'
    today = date.today().isoformat()
    appdata = r'%APPDATA%\TodoManager\data\tasks.json'

    text = f"""Todo Manager - Readme
{"=" * 48}
Version: {today}

[Quick Start]
  1. Extract this zip to any folder (e.g. D:\\TodoManager)
  2. Double-click todo-gui.exe to launch the GUI
  3. Or run todo.exe in a terminal

[CLI Commands]
  todo add "Task Title" -s 2026-05-01 -e 2026-05-15
         --status <status> -b "background"
  todo list                     [-d YYYY-MM-DD] [--deleted]
  todo show <task-id>           [--history N]
  todo edit <task-id>           [-t title] [-s start] [-e end]
                                [--status s] [-b bg] [-f]
  todo delete <task-id>         [-f]
  todo undo <task-id>           [-f]
  todo sub add <task-id> "title"  [-s start] [-e end] [--status s] [-b bg]
  todo sub list <task-id>
  todo sub show <task-id> <sub-id>  [--history N]
  todo sub edit <task-id> <sub-id>  [-t title] [-s start] [-e end]
                                    [--status s] [-b bg] [-f]
  todo sub delete <task-id> <sub-id>  [-f]
  todo sub undo <task-id> <sub-id>    [-f]
  todo cal                      [YYYY-MM]
  todo search <keyword>
  todo stats

  Status values: 未启动 / 完成中 / 已完成 / 已取消
  -f: skip confirmation    Full help: todo --help

[Add to PATH] (optional)
  Right-click install.bat and run as Administrator to add
  the current directory to your system PATH.
  Then you can run 'todo' from any terminal.

[Data Storage]
  All task data is stored at:
    {appdata}
  To uninstall, simply delete the extracted folder.
  To keep your data, back up the tasks.json file above.

[FAQ]
  Q: todo.exe flashes and disappears when double-clicked?
  A: todo.exe is a CLI tool. Run it in cmd or PowerShell.
  Q: GUI shows no data?
  A: CLI and GUI share the same data file.
  Q: "Missing DLL" error?
  A: Ensure you extracted the complete zip. todo-gui.exe
     requires the _internal folder in the same directory.
"""
    readme.write_text(text, encoding='utf-8')
    print("[OK] Readme.txt")


def create_install_bat():
    """Generate PATH installer script."""
    bat = DIST / 'install.bat'
    content = r"""@echo off
chcp 65001 >nul
echo ============================================
echo   Todo Manager - Add to System PATH
echo ============================================
echo.
echo Current directory: %~dp0
echo.

:: Request admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Administrator privileges required to modify PATH.
    echo Requesting elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Add current directory to user PATH
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
echo Done! Reopen your terminal and type: todo --help
echo.
pause
"""
    bat.write_text(content, encoding='gbk')
    print("[OK] install.bat")


def create_zip():
    """Package as zip."""
    print("\n[ZIP] Packaging...")
    zip_name = f"TodoManager_{date.today().isoformat()}.zip"
    zip_path = RELEASE_DIR / zip_name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in DIST.rglob('*'):
            if file_path.is_file():
                arcname = str(file_path.relative_to(DIST))
                zf.write(file_path, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] {zip_name} ({size_mb:.1f} MB)")
    return zip_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target not in ("all", "cli", "gui", "zip"):
        print(f"Usage: python {__file__} [all|cli|gui|zip]")
        sys.exit(1)

    print("=" * 50)
    print("  Todo Manager - Build Tool")
    print("=" * 50)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[FAIL] PyInstaller not installed. Run: pip install pyinstaller")
        sys.exit(1)

    # Clean once at the start (except for zip-only builds)
    if target != "zip":
        clean_dist()

    if target in ("all", "cli"):
        build_cli()
    if target in ("all", "gui"):
        build_gui()
    if target in ("all", "gui", "cli"):
        create_readme()
        create_install_bat()
    if target in ("all", "zip"):
        zip_path = create_zip()
        print(f"\n[DONE] Release package: {zip_path}")

    if target == "all":
        print(f"\n[DONE] Build complete! Output: {DIST}")
        print(f"  todo.exe      - CLI")
        print(f"  todo-gui.exe  - GUI")

    # Clean up build temp
    build_dir = ROOT / 'build'
    if build_dir.exists():
        shutil.rmtree(build_dir)


if __name__ == '__main__':
    main()
