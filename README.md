# Todo Manager

Todo Manager 是一个本地待办事项管理器，包含 Python 核心引擎、命令行入口和 PySide6 桌面 GUI。当前项目文案以中文为主，数据默认保存在本机，不包含云同步、提醒或后台常驻能力。

## 功能概览

- 主任务与二级子任务管理。
- 开始日期、截止日期、状态、背景说明。
- 软删除与撤销删除。
- 月历视图、搜索、统计和历史记录。
- CLI 与 GUI 共用同一个 `tasks.json` 数据文件。
- 开发态与冻结态数据目录已集中封装，支持 Windows 与 macOS 策略。

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

```powershell
todo-gui
todo-gui --data-dir C:\path\to\todo-data
```

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

## 数据目录

默认数据目录策略见 [docs/platform_support.md](docs/platform_support.md)。

- 开发态：项目根目录下的 `data/`。
- Windows 冻结态：`%APPDATA%\TodoManager\data`。
- macOS 冻结态：`~/Library/Application Support/TodoManager/data`。
- 显式 `--data-dir` 始终优先。

## 打包

Windows 现有打包入口：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

双平台打包策略将在后续 M6 里程碑继续完善。

## 项目文档

- [重整需求](docs/requirements_reorg_cross_platform_release.md)
- [里程碑计划](docs/milestone_plan_reorg_cross_platform_release.md)
- [测试计划](docs/test_plan_reorg_cross_platform_release.md)
- [M1 平台支持说明](docs/platform_support.md)

## 许可证

当前采用 MIT License，正式公开发布前项目 owner 可按需要替换许可证类型。
