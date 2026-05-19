# M0 工程基线与仓库化验证报告

> 日期：2026-05-19  
> 环境：Windows，本地 `.venv`，Python 3.14.0，PySide6 6.11.0  
> 结论：M0 本地工程基线通过；Git 仓库已初始化，首次提交已完成。

## 1. 变更摘要

- 初始化 Git 仓库。
- 新增 `.gitignore`，排除虚拟环境、缓存、构建产物、本地数据和临时文件。
- 新增 `README.md`，覆盖安装、运行、测试、数据目录和打包入口。
- 新增 `LICENSE`，当前采用 MIT License，正式公开发布前可由 owner 调整。
- 新增 `docs/dev_setup.md`，记录开发环境、常用命令、入口和原型链路处置。
- 更新 `pyproject.toml`，将项目 readme 指向 `README.md`。
- 将不可编译的 `generate_prototype.py`、`_write_proto.py` 归档为 `.broken` 文件，并在 `archive/prototype-generation/README.md` 中记录原因。

## 2. 执行命令与结果

| 命令 | 结果 |
|---|---|
| `python -m py_compile generate_prototype.py _write_proto.py` | 失败，确认原型生成链路不可编译 |
| `git init` | 通过 |
| `.venv\Scripts\python.exe -m pip install -e .[dev]` | 通过 |
| `.venv\Scripts\python.exe -m compileall engine cli gui scripts` | 通过 |
| `.venv\Scripts\todo.exe --help` | 通过 |
| `.venv\Scripts\todo-gui.exe --help` | 通过 |
| `.venv\Scripts\python.exe -m pytest` | 213 passed |

## 3. 观察到的非阻塞问题

- 本地 Python 为 3.14.0，高于需求文档推荐的 3.11 至 3.13。后续 CI 应按推荐矩阵验证 3.11、3.12、3.13。
- `.pytest_cache` 在本地出现访问拒绝，且 pytest 在写缓存时报告 `PytestCacheWarning`。测试断言全部通过；该目录已由 `.gitignore` 排除，不进入仓库。
- `dist/` 和 `.venv/` 作为已有本地产物/环境保留在工作区，但通过 `.gitignore` 排除。

## 4. M0 验收映射

| 验收项 | 本轮状态 |
|---|---|
| 新 shell 中能执行 `python -m pip install -e .[dev]` | 已验证 |
| 能执行 `todo --help` 或明确等价入口 | 已验证 `.venv\Scripts\todo.exe --help` |
| 能执行测试命令 | 已验证，全量 `213 passed` |
| `.gitignore`、`pyproject.toml`、`README.md`、`LICENSE`、`docs/dev_setup.md` | 已完成 |
| 原型生成脚本处置决策 | 已归档并记录 |
| 首次 Git commit | 已完成，最终提交号以 `git log -1` 为准 |
