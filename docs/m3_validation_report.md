# M3 CLI Agent 契约验证报告

> 日期：2026-05-19  
> 环境：Windows，本地 `.venv`，Python 3.14.0，PySide6 6.11.0  
> 结论：M3 本地实现与回归验证通过；macOS CLI smoke 待后续 CI 或 macOS 环境补齐。

## 1. 变更摘要

- 新增 `cli/contract.py`，集中定义 JSON envelope、错误 schema 和稳定退出码。
- CLI 支持全局 `--json`，成功 JSON 输出到 stdout，错误 JSON 输出到 stderr。
- `--json` 与 `--data-dir` 支持命令前和命令后两种位置。
- JSON 模式为非交互模式，编辑、删除、撤销不会等待确认输入。
- CLI 文本模式保持原有人类可读输出。
- 新增 subprocess 契约测试覆盖 JSON CRUD、后置全局参数、validation/not_found/data_file/usage 错误。
- 新增 `docs/cli_contract.md` 作为后续 M8 npm wrapper 和 M9 SKILL 的调用契约。

## 2. 退出码与错误码

| 场景 | 退出码 | JSON code |
|---|---:|---|
| 成功 | 0 | success |
| 参数错误 | 2 | usage_error |
| 字段校验失败 | 3 | validation_error |
| 任务或子任务不存在 | 4 | not_found |
| 数据文件错误 | 5 | data_file_error |
| 内部错误 | 6 | internal_error |
| 用户中断 | 130 | internal_error |

## 3. 验证命令

```powershell
python -m compileall engine cli gui scripts
.venv\Scripts\python.exe -m pytest tests\test_task_manager.py tests\test_storage.py tests\test_calendar.py tests\test_cli.py tests\test_cli_contract.py tests\test_source_entrypoints.py tests\test_gui.py
.venv\Scripts\python.exe -m pytest
```

结果：

- `compileall` 通过。
- M3 相关目标回归：`222 passed`。
- 全量测试：`229 passed`。
- 观察到已知 warning：pytest 无法创建 `.pytest_cache` 的 cache path，断言不受影响。

## 4. 验收映射

| M3 验收项 | 本轮状态 |
|---|---|
| agent 可通过 JSON 创建、查询、编辑、删除、撤销任务 | 已通过 subprocess 测试覆盖 |
| 所有错误路径都能被机器解析 | 已覆盖 usage、validation、not_found、data_file；internal error schema 已在入口兜底 |
| Windows CLI smoke 通过 | 已通过本地 subprocess 测试 |
| macOS CLI smoke 通过 | 未验证，待 macOS 环境或 CI 补齐 |

## 5. 已知限制

- 本地默认 `python` 指向 `C:\Python314\python.exe`，未安装 pytest；测试使用项目 `.venv`。
- 本地环境无法验证 macOS 终端中文输出和源码 CLI smoke。
- JSON schema 当前以文档约定和回归测试锁定，尚未引入独立 JSON Schema 文件；M9 SKILL 可按 `docs/cli_contract.md` 拆出 references。
