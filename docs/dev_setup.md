# Todo Manager 开发环境说明

> 版本：v0.1  
> 日期：2026-05-19  
> 对应里程碑：M0 工程基线与仓库化

## 1. 目标环境

- 推荐 Python 3.11 至 3.13。
- Windows 10/11 x64 与 macOS 13+ 是本轮重整目标平台。
- 所有源码、Markdown 和 JSON 文件使用 UTF-8。

## 2. 初始化环境

Windows PowerShell：

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

## 3. 常用开发命令

编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
```

运行全部测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

运行核心测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_task_manager.py tests\test_storage.py tests\test_calendar.py
```

运行 CLI 测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py tests\test_source_entrypoints.py
```

运行 GUI 测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_gui.py
```

## 4. 运行入口

安装后入口：

```powershell
todo --help
todo-gui --help
```

源码入口：

```powershell
python -m todo_manager.cli --help
python -m todo_manager.gui --help
```

显式数据目录：

```powershell
todo --data-dir C:\path\to\data stats
todo-gui --data-dir C:\path\to\data
```

当前 `--data-dir` 是全局参数，应放在子命令前。命令后全局参数兼容性将在 M3 CLI agent 契约里处理。

## 5. 打包命令

Windows 当前可用命令：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

macOS 打包策略将在 M6 里程碑补齐；当前 M0 只建立开发与测试基线。

## 6. 原型生成链路状态

`prototype.html` 作为现有 GUI 原型保留在根目录。

原 `generate_prototype.py` 和 `_write_proto.py` 在 M0 检查中被确认不可编译，已归档到 `archive/prototype-generation/` 并记录原因。后续如需要可在 M4 GUI/UX 重设计阶段重建原型生成链路。

## 7. 临时与生成文件

以下目录和文件不应提交：

- `.venv/`
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `dist/`
- `build/`
- `data/`
- `*.egg-info/`
- `.tmp/`
