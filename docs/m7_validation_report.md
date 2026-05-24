# M7 GitHub 与 CI 验证报告

> 日期：2026-05-24  
> 环境：Windows 11 x64，Python 3.14.0，本地 `.venv`，Node/npm 已安装  
> 结论：M7 已完成。Public GitHub repo 已创建并推送 `main`，GitHub Actions 已在 Windows 与 macOS 通过；GitHub Actions workflow、CLI JSON smoke helper、React 桌面 release dry-run 和 release checklist 均已落地。

GitHub repo：<https://github.com/DONGH4O/todo_manager>  
最终 CI run：<https://github.com/DONGH4O/todo_manager/actions/runs/26367268744>  
最终验证提交：`d03a13390a3a2899161042cef540549ab5d97a2d`

## 1. 本轮交付

- 新增 `.github/workflows/ci.yml`，覆盖 `windows-latest` 与 `macos-latest`。
- 新增 `.github/pull_request_template.md`，把常规验证、release dry-run 和人工补证要求放到 PR 入口。
- 新增 `scripts/ci_cli_smoke.py`，在 CI 中固定 `PYTHONUTF8=1`，使用独立临时数据目录验证 CLI JSON 创建和列表解析。
- 扩展 `scripts/smoke_release.py`，新增 `--react-only`，用于 CI 中不跑 PyInstaller 的 React 桌面 release dry-run。
- 更新 `tests/test_release_packaging.py`，覆盖 React desktop dry-run 文件清单和平台 launcher 要求。
- 新增 `docs/release_checklist.md`，汇总仓库、CI、React、release 包、人工桌面验收和发布记录 gate。
- 更新 README、测试计划、release 流程和里程碑计划。

## 2. CI Gate 映射

| M7 要求 | 当前实现 |
|---|---|
| Windows 测试 | `.github/workflows/ci.yml` matrix: `windows-latest` + Python 3.12 |
| macOS 测试 | `.github/workflows/ci.yml` matrix: `macos-latest` + Python 3.12 |
| CLI smoke | `todo --help`、`todo-gui --help`、`python scripts/ci_cli_smoke.py` |
| React lint/typecheck/build/audit | `frontend/` 下 `npm ci`、`npm run lint`、`npm run typecheck`、`npm run build`、`npm audit --omit=dev` |
| React 桌面发布链路 | `python scripts/build.py react` 与 `python scripts/smoke_release.py --react-only` |
| release checklist | `docs/release_checklist.md` |
| PR 检查说明 | `.github/pull_request_template.md` |
| GitHub repo URL | <https://github.com/DONGH4O/todo_manager> |

## 3. 已执行本地验证

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\todo.exe --help
.\.venv\Scripts\todo-gui.exe --help
.\.venv\Scripts\python.exe scripts\ci_cli_smoke.py
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd audit --omit=dev
cd ..
.\.venv\Scripts\python.exe scripts\build.py react
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --react-only
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py -q
```

结果：

- `compileall engine cli gui scripts`：通过。
- 全量 pytest：`206 passed, 1 warning`。
- `todo --help` / `todo-gui --help`：通过。
- `scripts/ci_cli_smoke.py`：通过。
- React lint/typecheck/build：通过。
- `npm audit --omit=dev`：通过，`found 0 vulnerabilities`。该命令需要访问 npm registry，本地验证时已通过授权联网执行。
- `scripts/build.py react`：通过，刷新 `dist/TodoManager/desktop-react/`、`Readme.txt`、`install.bat`、`todo-react.bat`。
- `scripts/smoke_release.py --react-only`：通过。
- release packaging 聚焦测试：`8 passed, 1 warning`。

warning 仍为既有 `.pytest_cache` 写权限 warning，不影响本轮 M7 CI 工程面判断。

## 4. 远端验证

- Public repo 已创建：<https://github.com/DONGH4O/todo_manager>。
- `main` 已推送，默认分支为 `main`。
- 首次 CI run `26367108129` 在两平台 Python 段均通过，但 `npm ci` 因 `frontend/package-lock.json` 缺少 `@emnapi/core` / `@emnapi/runtime` package 条目失败。
- 已用 npm 10.9.8 刷新 lockfile 并提交 `d03a133 fix: sync frontend lockfile for ci`。
- 最终 CI run `26367268744` 通过：Windows job 与 macOS job 均完成 Python compileall、pytest、CLI/GUI smoke、React install/lint/typecheck/build/audit 和 React desktop release dry-run。
- GitHub Actions 当前提示 Node.js 20 actions deprecation warning，属于 hosted Actions 运行器对 `actions/*@v4/v5` 的未来兼容提醒，不影响本轮 M7 通过结论。

## 5. 剩余边界

- M7 CI 执行 React desktop dry-run，不执行完整 PyInstaller 打包；完整 release 包验证仍按 `docs/release_process.md` 和 `docs/release_checklist.md` 在 M10/发布候选阶段执行。
- Windows/macOS 真实可见桌面窗口操作仍按 M6.5/M6.6 后续人工验收项补证。
