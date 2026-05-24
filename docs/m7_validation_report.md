# M7 GitHub 与 CI 验证报告

> 日期：2026-05-24  
> 环境：Windows 11 x64，Python 3.14.0，本地 `.venv`，Node/npm 已安装  
> 结论：M7 本地可完成项已完成。GitHub Actions workflow、CLI JSON smoke helper、React 桌面 release dry-run 和 release checklist 已落地；GitHub repo 创建、主分支推送、真实 Windows/macOS Actions run 仍需使用项目 owner 的 GitHub 凭证补证。

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
| GitHub repo URL | 待创建远端仓库并回填 |

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

## 4. 已知缺口

- 尚未创建 GitHub repo，因此无法提供 GitHub repo URL。
- 尚未推送 `main`，无法取得真实 GitHub Actions run URL。
- 本地仅验证 Windows host；macOS gate 已写入 workflow，需远端 Actions 或 macOS 实机补证。
- M7 CI 当前执行 React desktop dry-run，不执行完整 PyInstaller 打包；完整 release 包验证仍按 `docs/release_process.md` 和 `docs/release_checklist.md` 在 M10/发布候选阶段执行。

## 5. 下一步补证

1. 创建 GitHub repo 并添加 remote。
2. 推送 `main` 分支。
3. 等待 GitHub Actions 在 Windows 与 macOS 跑完。
4. 将 repo URL 与 CI run URL 回填到本报告或后续发布候选验收报告。
