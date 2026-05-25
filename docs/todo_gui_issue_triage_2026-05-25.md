# Todo GUI 使用问题核实记录

> 日期：2026-05-25  
> 状态：原因核实完成，用户已确认修复范围；2026-05-25 已进入修复与验证  
> 范围：React 桌面 GUI、QtWebEngine 壳、engine 日历展示规则

## 1. 逾期未完成任务不再持续展示

结论：确认存在规则退化，且影响 engine 与 React 前端两层。

当前 engine 规则位于 `engine/task_manager.py::get_tasks_for_date`。现有实现只在 `date_str < 今天` 且 `date_str > end_date` 时补充展示逾期的 `未启动` / `完成中` 任务。这会导致两类应展示任务丢失：

- 日期 T 等于今天，且任务已过截止日但仍为 `未启动` / `完成中`。
- 日期 T 在未来，且任务 start_date <= T、状态仍为 `未启动` / `完成中`。

本轮临时复现：

```text
任务：start_date=2026-05-01, end_date=2026-05-10, status=未启动
get_tasks_for_date("2026-05-25") -> []
get_tasks_for_date("2026-06-01") -> []
get_tasks_for_date("2026-05-05") -> ["逾期仍应展示"]
```

React 前端还在 `frontend/src/lib/date.ts::dateInRange` 中重复实现了仅按 `[start_date, end_date]` 判断的规则，因此即使 engine 修复，如果 GUI 仍通过 `listTasks()` 后在前端过滤，日历格、今日 rail、刷新选择逻辑仍会漏掉逾期未完成任务。

修复方案：

- 在 engine 增加统一谓词 `should_show_task_on_date(task, date_str)`。
- 规则改为：`start_date <= T <= end_date`，或 `start_date <= T 且 status in ("未启动", "完成中")`。
- 前端新增同语义 `shouldShowTaskOnDate(date, task)`，日历格、今日 rail、选中逻辑统一调用。
- 补 engine regression test：覆盖今天、未来日期、已完成/已取消逾期任务不展示。

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

结论：原因明确。删除逻辑会在剩余任务中选择当前日期命中的任务，否则选择 `remainingTasks[0]`，随后把 selectedDate 和可见月份改为 fallback 的 `start_date`。

相关位置：`frontend/src/components/TodoManagerApp.tsx::handleConfirmDelete`。

当前行为：

```text
fallback = 当前日期命中的剩余任务 || remainingTasks[0] || null
setSelectedDate(fallback.start_date)
setVisibleFromDate(fallback.start_date)
```

因此如果 `remainingTasks[0]` 是开始日期最早的跨月任务，就会把用户带回上个月或更早月份。

修复方案：

- 删除成功后固定回到今天：`selectedDate=today`，`visibleYear/visibleMonth=today`。
- 若今天有任务，则选中今天第一条应展示任务；否则清空详情选择或保留空态。
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
