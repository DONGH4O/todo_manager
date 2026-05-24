# Todo Manager 平台支持说明

> 版本：v0.1  
> 日期：2026-05-19  
> 对应里程碑：M1 跨平台架构重构

## 1. 数据目录策略

数据目录策略集中在 `engine/platform_paths.py`，业务代码不应再自行拼接平台相关路径。

| 场景 | 默认数据目录 |
|---|---|
| 显式传入 `--data-dir` | 完全使用传入路径，相对路径按当前工作目录解析 |
| 开发态 / 源码运行 | `<项目根目录>/data` |
| Windows 冻结态 | `%APPDATA%/TodoManager/data` |
| Windows 冻结态且缺少 `%APPDATA%` | `~/AppData/Roaming/TodoManager/data` |
| macOS 冻结态 | `~/Library/Application Support/TodoManager/data` |

说明：

- 路径处理统一使用 `pathlib.Path`。
- `engine/storage.py` 只通过平台路径模块解析默认目录。
- Linux 暂不作为承诺平台；当前实现保留 `~/.local/share/TodoManager/data` 兜底，方便未来扩展。

## 2. 入口命令

安装后入口：

```powershell
todo --help
todo-gui --help
```

源码运行入口：

```powershell
python -m todo_manager.cli --help
python -m todo_manager.gui --help
```

源码运行时应从 `todo_manager` 目录的上一级执行上述 `python -m` 命令，或先在项目根目录执行 editable 安装：

```powershell
python -m pip install -e .[dev]
```

CLI 和 GUI 都支持显式数据目录：

```powershell
todo --data-dir C:\path\to\data stats
todo-gui --data-dir C:\path\to\data
```

当前 `--data-dir` 是全局参数，应放在子命令之前；“命令前和命令后都可用”的契约留到 M3 CLI agent 契约里统一处理。

## 3. 相关实现文件

- `engine/platform_paths.py`：平台默认目录、源码根目录、显式目录解析。
- `engine/storage.py`：通过统一路径模块读写 `tasks.json`。
- `cli/main.py`：CLI 正式入口，初始化显式数据目录或恢复平台默认策略。
- `gui/main.py`：GUI 正式入口，支持 `--data-dir`。
- `pyproject.toml`：声明 Python 包元数据与 `todo`、`todo-gui` 入口。

## 4. 本地验证范围

本轮已在 Windows 本地完成：

- 源码 CLI help smoke。
- 源码 GUI help smoke。
- 安装入口 `todo` / `todo-gui` help smoke。
- 显式 `--data-dir` 写入 smoke。
- 平台路径单元测试，包括 Windows/macOS 冻结态模拟。
- engine、CLI、GUI 全量 pytest 回归。

尚需后续在 macOS 环境或 CI 中复验：

- macOS 源码 CLI 实际运行。
- macOS GUI 实际启动、中文显示与点击交互。
- macOS 冻结态打包产物路径行为。

M6 更新：

- Windows 冻结态 CLI/GUI 已通过 `scripts/build.py all` 与 `scripts/smoke_release.py` 验证。
- macOS `.app` 打包配置已建立，仍需 macOS 原生构建和实机启动验证。
