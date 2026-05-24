# M2 源码审计与可靠性修复报告

> 日期：2026-05-19  
> 范围：`engine/`、`cli/`、`gui/`、`scripts/`、原型生成归档  
> 结论：M2 本地实现与回归验证通过；macOS 实机验证仍待后续 CI 或 macOS 环境补齐。

## 1. 审计摘要

本轮按 `milestone_plan_reorg_cross_platform_release.md` 的 M2 目标，重点检查数据安全、模型反序列化副作用、CLI 历史输出、GUI 子任务与搜索交互、原子写入和原型生成链路。

已完成修复：

- `engine/storage.py` 不再把损坏 `tasks.json` 静默当作空列表；坏 JSON 或结构错误会抛出可诊断的 `DataFileError`，并在同目录生成 `tasks.json.corrupt-*.bak` 备份。
- `save_tasks()` 改为每次使用唯一临时文件，通过 `os.replace()` 原子替换；替换失败时保留旧 `tasks.json`，并尽力清理本次临时文件。
- `Task.from_dict()` 与 `SubTask.from_dict()` 改为复制输入 dict 后再反序列化，避免污染调用者持有的原始数据。
- CLI 入口捕获存储错误，错误写入 stderr，返回码为 `2`，避免用户或 agent 把坏数据误判为“无任务”。
- CLI 历史记录改为最新版本在前，便于快速审计最近变更。
- GUI 修复子任务删除弹窗访问 `SubTask.subtasks` 的异常。
- GUI 搜索子任务时携带父任务起始日期，日历定位到能展示该子任务的父任务日期。
- GUI 任务点击和搜索定位后会同步高亮对应任务条。
- 搜索下拉窗口位置增加屏幕边界约束，减少跨平台跑出屏幕的风险。

## 2. P0/P1 问题处理

| 优先级 | 问题 | 处理状态 | 回归覆盖 |
|---|---|---|---|
| P0 | 损坏 JSON 被 `load_tasks()` 吞掉并返回空列表，后续写入可能覆盖用户数据 | 已修复：抛 `DataFileError`，保留原文件并生成坏文件备份 | `tests/test_storage.py::TestLoadTasks::test_corrupted_json`、`tests/test_source_entrypoints.py::test_cli_source_module_reports_corrupt_data` |
| P0 | `os.replace()` 失败路径缺少显式诊断和旧文件保护测试 | 已修复：唯一临时文件、失败后保留旧文件、抛 `DataWriteError` | `tests/test_storage.py::TestSaveTasks::test_atomic_write_failure_preserves_existing_file` |
| P1 | `Task.from_dict()` / `SubTask.from_dict()` 会 `pop` 输入 dict，可能污染缓存或审计用原始数据 | 已修复：先复制输入 dict | `tests/test_task_manager.py::TestModelSerialization::test_task_from_dict_does_not_mutate_input`、`test_subtask_from_dict_does_not_mutate_input` |
| P1 | CLI 历史记录按旧到新展示，用户查看最近修改不直观 | 已修复：最新在前展示 | `tests/test_cli.py::TestHistoryContent::test_history_renders_newest_first` |
| P1 | GUI 删除子任务时删除弹窗按主任务结构读取 `subtasks`，会异常 | 已修复：区分主任务和子任务删除提示。2026-05-24 React GUI 切换后，该旧 widget GUI 回归用例已随旧实现归档 | `archive/legacy-pyside6-gui/tests/legacy_gui_pytest.py::TestDialogs::test_delete_dialog_accepts_subtask_without_subtask_attribute` |
| P1 | GUI 搜索命中子任务时日历可能跳到子任务日期，而该日期未必展示父任务和子任务 | 已修复：搜索结果携带 `parent_start_date` 并用于日历定位。2026-05-24 React GUI 切换后，该旧 widget GUI 回归用例已随旧实现归档 | `archive/legacy-pyside6-gui/tests/legacy_gui_pytest.py::TestSearch::test_search_result_for_subtask_uses_parent_calendar_date` |
| P1 | 任务点击/搜索定位后 `selected_task_id` 有值但任务条没有视觉高亮 | 已修复：日历刷新和增量选择都会更新 `TaskBar` 高亮。2026-05-24 React GUI 切换后，该旧 widget GUI 回归用例已随旧实现归档 | `archive/legacy-pyside6-gui/tests/legacy_gui_pytest.py::TestSearch::test_task_click_highlights_selected_task_bar` |

## 3. 其他审计结论

- `engine/task_manager.py` 的软删除、撤销删除、子任务父子关系和日期展示规则未做行为性改动。
- `cli/main.py` 当前仍是人类可读输出为主，完整 JSON schema、稳定错误 schema 和全局 `--json` 留到 M3。
- `gui/` 仍保留当前 M1/M2 结构；更大范围的视觉和交互重构留到 M4/M5。
- `scripts/build.py` 仍明显偏 Windows release 产物，属于 M6 双平台打包范围；本轮未提前重构。
- 原型生成脚本已在 M0 移入 `archive/prototype-generation/` 并说明原因；M2 复核后保持归档，后续若需要可在 M4 重新设计可复现原型链路。

## 4. 验证记录

已执行：

```powershell
python -m compileall engine cli gui scripts
.venv\Scripts\python.exe -m pytest tests\test_storage.py tests\test_task_manager.py tests\test_source_entrypoints.py tests\test_cli.py tests\test_gui.py
.venv\Scripts\python.exe -m pytest
```

结果：

- `compileall` 通过。
- 目标回归测试：`192 passed`。
- 全量测试：`223 passed`。
- 观察到已知 warning：pytest 无法创建 `.pytest_cache` 的 cache path，断言不受影响。

## 5. 已知限制

- 本地默认 `python` 指向 `C:\Python314\python.exe`，未安装 pytest；本轮测试使用项目 `.venv`。
- 本地环境为 Windows，无法证明 macOS 源码 CLI/GUI 实机运行；该项仍需 M7 CI 或 macOS 手工验证。
- CLI JSON 契约、agent 友好错误 schema 和命令后全局参数兼容属于 M3，不在 M2 内展开。
