# Todo Manager

Todo Manager 是一个本地待办事项管理器，包含 Python 核心引擎、命令行入口，以及以 PySide6 QtWebEngine 承载的 React 桌面 GUI。当前项目文案以中文为主，数据默认保存在本机，不包含云同步、提醒或后台常驻能力。

## 功能概览

- 主任务与二级子任务管理。
- 开始日期、截止日期、状态、背景说明。
- 软删除与撤销删除。
- 月历视图、搜索、统计和历史记录。
- CLI 与 GUI 共用同一个 `tasks.json` 数据文件。
- 开发态与冻结态数据目录已集中封装，支持 Windows 与 macOS 策略。
- React 桌面界面通过 QtWebEngine 壳和本地任务引擎读写真实任务数据。
- Windows/macOS GUI 使用基于 Figma brand mark + brand letter 的应用图标。

## 环境要求

- 推荐 Python 3.11 至 3.13。
- GUI 需要 PySide6。
- Windows PowerShell、Windows Terminal 与 macOS Terminal 均作为目标终端环境。

## 开发环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

macOS / bash：

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -U pip
./.venv/bin/python -m pip install -e '.[dev]'
```

## 运行 CLI

安装后：

```powershell
todo --help
todo add "完成周报" -s 2026-05-19 -e 2026-05-19 --status 未启动
todo list
todo stats
```

源码方式：

```powershell
python -m todo_manager.cli --help
```

指定独立数据目录：

```powershell
todo --data-dir C:\path\to\todo-data add "测试任务" -s 2026-05-19 -e 2026-05-19
```

## 运行 GUI

正式 React 桌面界面：

```powershell
todo-gui
todo-gui --data-dir C:\path\to\todo-data
```

`--react` 仍保留为兼容旧命令的 no-op：

```powershell
todo-gui --react
```

发布包中 `todo-gui.exe` / `TodoManager.app` 直接启动 React GUI；`todo-react.bat` / `todo-react` 仅作为兼容启动器保留。

旧 PySide6 widget GUI 已移入 `archive/legacy-pyside6-gui/`，不再作为后续里程碑、GitHub release 或 npm 发布路径的一部分。


源码方式：

```powershell
python -m todo_manager.gui --help
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest
```

GUI 测试默认使用 Qt offscreen 模式，不需要桌面窗口交互。

## GitHub Actions / CI

Public repo: [DONGH4O/todo_manager](https://github.com/DONGH4O/todo_manager)

M7 起仓库包含 `.github/workflows/ci.yml`，用于在 GitHub Actions 上持续验证 Windows 与 macOS：

- 安装 Python package 并运行 `compileall`、全量 `pytest`。
- 运行 `todo --help`、`todo-gui --help` 和 CLI JSON smoke。
- 在 `frontend/` 执行 `npm ci`、lint、typecheck、Next static export 和生产依赖 audit。
- 执行 React 桌面 release dry-run：`scripts/build.py react` 与 `scripts/smoke_release.py --react-only`。

完整发布前检查见 [docs/release_checklist.md](docs/release_checklist.md)。

## 数据目录

默认数据目录策略见 [docs/platform_support.md](docs/platform_support.md)。

- 开发态：项目根目录下的 `data/`。
- Windows 冻结态：`%APPDATA%\TodoManager\data`。
- macOS 冻结态：`~/Library/Application Support/TodoManager/data`。
- 显式 `--data-dir` 始终优先。

## 打包

M6 已建立按宿主平台构建的 release 入口。Windows 产物需在 Windows 构建，macOS `.app` 需在 macOS 构建。

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

打包后可复跑 release smoke：

```powershell
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
```

仅刷新 React 桌面界面资源：

```powershell
.\.venv\Scripts\python.exe scripts\build.py react
```

M6.5 后 release 包会包含 `desktop-react/` 与兼容启动器 `todo-react.bat`；`desktop-react/` 不包含 `node_modules/` 或 `.next/` 缓存。
M6.6 后 GUI 可执行文件和 macOS `.app` 会嵌入 `assets/icons/todo-manager.*` 应用图标，源码运行窗口也会使用同一图标。

macOS 当前流程会生成未签名、未公证的 `.app`；正式公开分发前需在 release note 中继续说明签名状态，或补齐 Developer ID 签名和 notarization。

## 项目文档

- [重整需求](docs/requirements_reorg_cross_platform_release.md)
- [里程碑计划](docs/milestone_plan_reorg_cross_platform_release.md)
- [测试计划](docs/test_plan_reorg_cross_platform_release.md)
- [M1 平台支持说明](docs/platform_support.md)
- [M6.5 React 桌面架构](docs/m6_5_react_desktop_architecture.md)
- [M6.5 验证报告](docs/m6_5_validation_report.md)
- [M6.6 应用图标验证报告](docs/m6_6_application_icon_validation_report.md)
- [React GUI 默认入口切换验证](docs/react_gui_cutover_validation_report.md)
- [Release checklist](docs/release_checklist.md)
- [M7 CI 验证报告](docs/m7_validation_report.md)

## 许可证

当前采用 MIT License，正式公开发布前项目 owner 可按需要替换许可证类型。
