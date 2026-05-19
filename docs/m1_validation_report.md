# M1 跨平台架构重构验证报告

> 日期：2026-05-19  
> 环境：Windows，本地 `.venv`，Python 3.14.0，PySide6 6.11.0  
> 结论：M1 本地开发与回归验证通过；macOS 实机验证待后续 CI 或 macOS 环境补齐。

## 1. 变更摘要

- 新增 `engine/platform_paths.py`，集中处理开发态、Windows 冻结态、macOS 冻结态和显式 `--data-dir` 的数据目录策略。
- 更新 `engine/storage.py`，使用 `pathlib.Path` 和统一路径模块解析 `tasks.json`。
- 更新 CLI/GUI 正式入口，移除 GUI 中的 `sys.path` 手工注入，并让 GUI 支持 `--data-dir`。
- 新增 `pyproject.toml` 和包根 `__init__.py`，声明 `todo`、`todo-gui` 安装入口。
- 新增 M1 测试：`tests/test_platform_paths.py`、`tests/test_source_entrypoints.py`。
- 新增 `docs/platform_support.md`，记录平台策略和使用方式。

## 2. 执行命令与结果

| 命令 | 结果 |
|---|---|
| `.venv\Scripts\python.exe -m pip install -e .[dev]` | 通过，开发测试依赖已安装 |
| `.venv\Scripts\python.exe -m compileall engine cli gui scripts` | 通过 |
| `python -m todo_manager.cli --help` | 通过 |
| `python -m todo_manager.gui --help` | 通过 |
| `.venv\Scripts\todo.exe --help` | 通过 |
| `.venv\Scripts\todo-gui.exe --help` | 通过 |
| `.venv\Scripts\todo.exe --data-dir <temp> add ...` + `stats` | 通过，`tasks.json` 正常创建 |
| `.venv\Scripts\python.exe -m pytest tests\test_platform_paths.py tests\test_source_entrypoints.py` | 10 passed |
| `.venv\Scripts\python.exe -m pytest tests\test_task_manager.py tests\test_storage.py tests\test_calendar.py` | 121 passed |
| `.venv\Scripts\python.exe -m pytest tests\test_cli.py` | 49 passed |
| `.venv\Scripts\python.exe -m pytest tests\test_gui.py` | 33 passed |
| `.venv\Scripts\python.exe -m pytest` | 213 passed |

## 3. 观察到的非阻塞问题

- pytest 提示 `.pytest_cache` 缓存路径创建 warning：`could not create cache path ... [WinError 183]`。断言全部通过，缓存目录问题不影响本轮功能验证。
- 当前本地 Python 为 3.14.0，高于需求文档推荐的 3.11 至 3.13。代码和测试已通过，但发布/CI 仍应按推荐矩阵验证 3.11、3.12、3.13。
- macOS 实机 CLI/GUI 尚未在本轮本地环境执行；目前通过路径模拟和平台无关入口 smoke 覆盖，后续 M7 CI 或 macOS 手工验证需要补齐。

## 4. M1 验收映射

| 验收项 | 本轮状态 |
|---|---|
| Windows 源码运行 CLI 成功 | 已验证 |
| macOS 源码运行 CLI 成功 | 待 macOS 环境复验 |
| Windows 源码启动 GUI 成功 | 已验证 GUI help 入口与 offscreen GUI 测试；人工窗口启动待需要时执行 |
| macOS 源码启动 GUI 成功 | 待 macOS 环境复验 |
| 显式 `--data-dir` 覆盖在两平台均生效 | Windows smoke 已验证；Windows/macOS 路径解析单测已覆盖 |
