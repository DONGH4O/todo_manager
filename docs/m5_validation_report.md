# M5 GUI 重构实现验证报告

> 日期：2026-05-21  
> 环境：Windows，本地工作区，PySide6 offscreen GUI 测试  
> 结论：M5 UI 运行态已按 `docs/m4_uiux_redesign/prototype_v1.html` 与 `docs/m4_uiux_redesign/DESIGN.md` 推倒重建，并完成字体 px 语义、居中三栏、任务卡片、月历 mini bar、详情表单、子任务标签和搜索下拉的二次对齐；Windows/PySide6 offscreen 自动回归与 1366x768 截图已更新。完整验收仍需补齐 Windows 真实窗口、macOS 实机启动和多视口真实字体截图。

## 1. 交付摘要

- 重构 `gui/app.py` 为原型定义的顶部栏、左侧 rail、月历工作台、右侧详情三栏布局。
- 新增 `gui/controller.py`，集中封装 GUI 对 engine 的读写调用，减少 widget 直接承担业务逻辑。
- 重写 `gui/theme.py`，将 Layered Clarity / Glassmorphism token 映射到 PySide6 运行态。
- 重写 `gui/widgets/theme_toggle.py`，落地原型 `自动 / 明色 / 暗色` 三态主题入口。
- 重写 `gui/widgets/today_panel.py`，落地 rail 的 2x3 metrics、五段 tabs 和 agenda task cards。
- 重写 `gui/widgets/calendar_grid.py`、`calendar_cell.py`、`task_bar.py`，落地 8px gap、圆角日格、count badge 和 `.mini` 任务条。
- 重写 `gui/widgets/detail_panel.py`，从旧版详情卡片/弹窗编辑改为原型内联表单、状态 segmented、子任务状态选择和底部保存/删除。
- 调整搜索、月历、详情、主题切换和快捷键行为，补齐原型交互事项。
- 将显式 GUI 字体从 Qt point size 改为 prototype CSS pixel size，统一 Microsoft YaHei / PingFang SC / Noto Sans CJK SC fallback。
- 二次修正 topbar 与 workspace 居中容器、260px rail、fluid calendar、340px detail 的相对宽度。
- 二次修正今日节奏等高任务卡片、月历 `.mini` 任务条不撑宽列、详情输入框边界、子任务卡片/状态选择器和标签边界。
- 搜索 dropdown 改为点击/聚焦即展示当前日期父任务列表；搜索仍可命中子任务文本，但结果按原型仅展示父任务卡片。
- 新增/更新 GUI 回归测试，覆盖原型三栏尺寸、三态主题、右侧内联保存、搜索 dropdown 当前日期父任务列表与子任务命中父任务展示。
- 更新截图证据：`docs/m5_gui_smoke_1366x768.png`。

## 2. M5 任务映射

| M5 任务 | 本轮状态 |
|---|---|
| 重构主题系统，支持持久化和系统主题策略 | 已完成：`ThemeSettings` 通过 `QSettings` 持久化 `system/light/dark`，三态入口已落地 |
| 优化主布局，减少嵌套卡片和拥挤控件 | 已完成：按原型建立居中 topbar + 260px rail + fluid calendar + 340px detail |
| 调整日历任务条、详情面板、搜索下拉、弹窗 | 已完成：月历固定 6 行、8px gap 日格、mini 任务条、右侧内联编辑表单、prototype 风格搜索下拉 |
| 封装 GUI 与 engine 的交互层 | 已完成：新增 `GuiController` |
| 修复任务选中高亮和搜索定位细节 | 已完成：子任务搜索定位父任务月历条，详情展示子任务 |
| 确保快捷键不干扰输入框 | 已完成：输入控件聚焦时跳过 Delete/Edit/月份箭头等快捷键 |
| 增加 GUI smoke tests | 已完成：`tests/test_gui.py` 增至 46 个 GUI 用例 |

## 3. 验收映射

| M5 验收项 | 本轮状态 |
|---|---|
| Windows/macOS 均可启动 GUI | 部分通过：Windows 本地源码/offscreen 启动已验证；Windows 真实窗口与 macOS 实机启动待补齐 |
| 关键工作流可用 | 已覆盖日期选择、任务点击、搜索定位、主题持久化、今日节奏统计/筛选 |
| 1080P 下无明显文字遮挡或按钮溢出 | 部分通过：1366x768 offscreen 截图已生成；真实字体、多视口和实机窗口验收待补齐 |
| 暗色模式可用且持久化 | 已覆盖：`自动 / 明色 / 暗色` 三态入口与持久化回归通过；真实窗口对比度仍待人工确认 |

## 4. 验证命令

```powershell
python -m compileall engine cli gui scripts
```

结果：通过。

```powershell
.venv\Scripts\python.exe -m pytest tests/test_gui.py -q
```

结果：`46 passed`。

```powershell
.venv\Scripts\python.exe -m pytest -q
```

结果：`243 passed, 1 warning`。warning 为 Windows 环境下 `.pytest_cache` 已存在导致的 `PytestCacheWarning`，不影响功能验证。

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

结果：Windows release 重新打包通过，`todo.exe`、`todo-gui.exe` 与 zip 均生成，release smoke 与 zip audit 通过；最新产物尺寸见 `docs/m6_validation_report.md`。

## 5. 截图记录

- `docs/m5_gui_smoke_1366x768.png`

说明：该截图由 PySide6 offscreen 渲染生成，用于确认 1366x768 几何布局、三栏结构和控件不重叠。当前 headless 渲染环境对中文字体 fallback 不完整，截图中的中文可能显示为方块；真实 Windows 桌面字体渲染仍需人工窗口验收。

## 6. 视觉与实机验收矩阵

| 验收项 | 当前证据 | 状态 |
|---|---|---|
| Windows 真实窗口启动 | 尚未执行人工窗口启动 | 待补齐 |
| macOS 源码 GUI 启动 | 尚无 macOS 环境证据 | 待补齐 |
| 1366x768 / 等价小屏 | offscreen 截图已生成，中文字体 fallback 不完整 | 部分通过 |
| 1920x1080 | 尚无截图或人工记录 | 待补齐 |
| 2560x1440 | 尚无截图或人工记录 | 待补齐 |
| 3840x2160 | 尚无截图或人工记录 | 待补齐 |
| 暗色模式真实窗口对比度 | 自动测试覆盖持久化，真实窗口对比度未人工确认 | 待补齐 |
| 弹窗位置、搜索下拉层级 | offscreen 回归覆盖基础交互，真实窗口层级未人工确认 | 待补齐 |
| Theme toggle 三态入口 | PySide6 已实现 `自动 / 明色 / 暗色` 交互并覆盖回归 | 已完成 |

## 7. 后续补齐项

- 在真实 Windows 桌面窗口中人工确认中文字体、弹窗位置、搜索下拉层级和暗色对比度。
- 在 macOS 环境执行源码 GUI 启动 smoke。
- 按 `docs/test_plan_reorg_cross_platform_release.md` 的 1366x768、1920x1080、2560x1440、3840x2160 视口补齐截图或人工记录。
- M6 打包时继续复核 Windows/macOS 发布产物 GUI 启动。

## 8. React/Figma 前端重写补充

2026-05-22 根据 Figma `Engineering Handoff / Codex Ready Spec` 新增独立 React + TypeScript + Tailwind CSS + Next.js App Router 前端实现，代码位于 `frontend/`，验证记录见 `docs/m5_react_frontend_validation_report.md`。该实现完全隔离于既有 PySide6 GUI，用于承接 Figma prototype 的前端 UI 重写，不复用旧 GUI 代码。

已补齐的 M5 前端交付面：

- Design Tokens 与 Tailwind theme 映射。
- 按 Component Mapping 拆分的 React 组件。
- 搜索、筛选、日历选择、任务详情编辑、新建任务、子任务、新建子任务、删除确认和撤销 toast 交互。
- desktop、tablet、mobile 三档响应式布局。
- light / dark / system theme。
- 2026-05-22 二次修正搜索 dropdown 层级、月历可见周数、等高日格和子任务状态 pill 箭头。
- 2026-05-23 二次修正月历网格填满工作台高度，并验证月历、今日节奏内容区和任务详情编辑区在短窗口/内容溢出时均可滚动。

边界说明：当前 React 前端仍是独立前端交付物，尚未替代 PySide6 桌面运行态；M5 完整验收仍以真实窗口、多视口字体与 macOS 实机证据补齐为关闭条件。
