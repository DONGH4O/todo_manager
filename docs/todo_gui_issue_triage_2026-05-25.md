# Todo GUI 使用问题核实记录

> 日期：2026-05-25  
> 状态：原因核实完成，用户已确认修复范围；2026-05-25 已进入修复与验证  
> 范围：React 桌面 GUI、QtWebEngine 壳、engine 日历展示规则

## 1. 逾期未完成任务不再持续展示

结论：确认存在规则退化，且影响 engine 与 React 前端两层。

当前 engine 规则位于 `engine/task_manager.py::get_tasks_for_date`。重构后曾退化为仅按日期区间展示，第一轮修复又把 `未启动` / `完成中` 的逾期持续展示延伸到了未来日期。用户补充完整规则后，本轮已按以下边界二次修正：

- 条件 1：`start_date <= T <= end_date`。
- 条件 2：`T <= 今天` 且 `start_date <= T` 且任务状态属于 `未启动` / `完成中`。

本轮临时复现：

```text
任务：start_date=今天-20天, end_date=今天-10天, status=未启动/完成中
get_tasks_for_date("今天") -> ["逾期仍应展示"]
get_tasks_for_date("今天+10天") -> []
get_tasks_for_date("区间内日期") -> ["区间内仍应展示"]
```

React 前端此前还在 `frontend/src/lib/date.ts::dateInRange` / `shouldShowTaskOnDate` 中重复实现展示规则，因此即使 engine 修复，如果 GUI 仍通过 `listTasks()` 后在前端过滤，日历格、今日 rail、刷新选择逻辑仍可能与引擎规则漂移。

修复方案：

- 在 engine 增加统一谓词 `should_show_task_on_date(task, date_str)`。
- 规则改为：`start_date <= T <= end_date`，或 `T <= 今天 且 start_date <= T 且 status in ("未启动", "完成中")`。
- GUI bridge 新增 `listTasksForDates`，由 `engine.get_tasks_for_dates()` 返回各日期应展示任务。
- React 前端移除 `shouldShowTaskOnDate` 展示谓词，日历格、今日 rail、选中逻辑改为消费 bridge 返回的 `tasksByDate`。
- 补 regression test：覆盖今天仍展示、未来日期不按逾期持续展示、已完成/已取消逾期任务不展示。

## 2. QtWebEngine 渲染闪烁

结论：当前无法在本机稳定复现另一台 Windows 笔记本的闪烁，但代码中存在高风险组合。

相关风险点：

- `frontend/src/app/globals.css` 大量使用半透明 surface、radial gradient 背景、`backdrop-blur-glass`、大阴影和 hover/focus transition。
- `frontend/src/components/ui/ModalShell.tsx` 使用全屏 `backdrop-blur-sm`。
- `frontend/src/components/layout/TopNav.tsx` 与 `.tm-panel` 都使用 glass blur。
- 闪烁触发点集中在 hover、点击按钮、输入字段内容，符合 QtWebEngine/Chromium 对半透明 backdrop-filter、阴影、重绘层和 GPU compositing 组合不稳定时的表现。

优化方案：

- 先做低风险稳定化：为 QtWebEngine 桌面模式增加 `html[data-desktop-shell="true"]` 开关，只在桌面壳内关闭高成本 backdrop blur；浏览器预览可保留较丰富视觉。
- 收窄桌面壳内全局 transition，只对颜色、背景、边框、阴影和透明度过渡，避免 hover/输入时触发不必要布局或合成层变化。
- 如仍闪烁，再评估 QtWebEngine 运行参数，例如禁用 GPU 或改用软件 OpenGL，但该项需真实窗口 A/B 测试后再定。

## 3. 新建任务/子任务状态 dropdown 延展

结论：原因明确。新建父任务和子任务弹窗仍使用原生 `<select>`，而不是项目内已为子任务行实现的固定定位状态菜单。

相关位置：

- `frontend/src/components/todo/CreateTaskModal.tsx`
- `frontend/src/components/todo/CreateSubtaskModal.tsx`
- 已有稳定参考：`frontend/src/components/todo/SubtaskRow.tsx` 使用 `createPortal` + fixed positioning，将菜单限制在视口内。

修复方案：

- 抽出通用 `StatusDropdown`，使用 fixed/portal 菜单并按视口夹紧。
- 优先避免原生 `<select>`，因为 QtWebEngine 对 native dropdown 的弹层尺寸和方向控制能力有限。
- 补弹窗状态选择的手工 smoke 项，覆盖窗口右侧、底部和小窗口高度。

## 4. 删除任务后跳到最早任务开始日

结论：原因明确。删除逻辑第一轮已固定回到今天，但刷新选择逻辑仍保留 `loadedTasks[0]` 兜底；当删除后触发重新读取或当前日期没有可选任务时，仍可能重新选中开始日期最早的任务，并把 selectedDate 和可见月份改为该任务的 `start_date`。

相关位置：`frontend/src/components/TodoManagerApp.tsx::handleConfirmDelete` 与 `refreshTasks`。

当前行为：

```text
taskToSelect = 当前任务 || 当前日期命中的任务 || loadedTasks[0] || null
if taskToSelect 不在当前日期展示:
    setSelectedDate(taskToSelect.start_date)
    setVisibleFromDate(taskToSelect.start_date)
```

因此如果 `loadedTasks[0]` 是开始日期最早的跨月任务，就会把用户带回上个月或更早月份。

修复方案：

- 删除成功后固定回到今天：`selectedDate=today`，`visibleYear/visibleMonth=today`。
- 若今天有任务，则选中今天第一条应展示任务；否则清空详情选择或保留空态。
- 移除刷新逻辑里的 `loadedTasks[0]` 兜底，避免删除后的二次刷新把视图拉回最早任务。
- 撤销删除可继续选中恢复的任务，除非用户另行要求撤销也回到今天。

## 5. 验证记录

2026-05-25 修复后验证：

- `python -m compileall engine cli gui scripts`：通过。
- `pytest tests/test_task_manager.py tests/test_release_packaging.py tests/test_react_shell_bridge.py -q`：104 passed，1 个既有 `.pytest_cache` 写入 warning。
- `pytest -q`：211 passed，1 个既有 `.pytest_cache` 写入 warning。
- `npm.cmd run lint`：通过。
- `npm.cmd run typecheck`：通过。
- `npm.cmd run build`：通过。
- `scripts/build.py all`：通过，生成 `dist/TodoManager/todo.exe`、`dist/TodoManager/todo-gui.exe`、`dist/TodoManager/desktop-react/` 和 `dist/TodoManager-windows-2026-05-25.zip`，release smoke / zip audit 通过。
- 打包后 CLI smoke：使用 `dist/TodoManager/todo.exe` 创建已过截止日的 `未启动` 任务后，按今天查询可展示该任务。

2026-05-25 二次修复后验证：

- `python -m compileall engine cli gui scripts`：通过。
- `pytest tests/test_task_manager.py tests/test_release_packaging.py -q`：104 passed，1 个既有 `.pytest_cache` 写入 warning。
- `pytest -q`：213 passed，1 个既有 `.pytest_cache` 写入 warning。
- `npm.cmd run lint`：通过。
- `npm.cmd run typecheck`：通过。
- `npm.cmd run build`：通过。
- `scripts/build.py all`：通过，生成 `dist/TodoManager/todo.exe`、`dist/TodoManager/todo-gui.exe`、`dist/TodoManager/desktop-react/` 和 `dist/TodoManager-windows-2026-05-25.zip`，release smoke / zip audit 通过。
- 打包后 CLI smoke：已过截止日且状态仍未完成的任务在今天展示，在今天之后的未来日期不展示；未来日期位于任务自身 `[start_date, end_date]` 区间内时仍展示。
- 当前打包尺寸：`todo-gui.exe` 218,866,468 bytes，`TodoManager-windows-2026-05-25.zip` 227,079,435 bytes。轻量化目前仅进入 M7.5 计划，尚未执行依赖裁剪，所以尺寸不会下降。

2026-05-25 架构收敛记录：

- CLI：`todo list --date` / `todo cal` 继续通过 `engine.get_tasks_for_date()` 获取展示结果。
- GUI：桌面 bridge 新增批量接口 `listTasksForDates`，内部调用 `engine.get_tasks_for_dates()`；React 组件不再保存独立展示规则，只根据 `tasksByDate[date]` 渲染。
- 保留浏览器预览模式的本地 demo fallback；桌面壳若 bridge 不可用会报错，不会回退到预览数据。
- 新增 bridge 回归测试：`listTasksForDates` 对同一逾期未完成任务，今天返回任务、未来日期返回空列表。
- 验证：`python -m compileall engine cli gui scripts` 通过；`pytest tests/test_react_shell_bridge.py tests/test_task_manager.py tests/test_release_packaging.py -q` 为 107 passed；`pytest -q` 为 214 passed；`npm.cmd run lint/typecheck/build` 通过；`scripts/build.py all` 通过并重新生成 release 包。
- 当前打包尺寸：`todo-gui.exe` 218,866,808 bytes，`TodoManager-windows-2026-05-25.zip` 227,082,390 bytes。
