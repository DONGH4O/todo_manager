# React GUI 默认入口切换验证报告

> 日期：2026-05-24  
> 环境：Windows 11 x64，Python 3.14.0，Node/npm 已安装  
> 结论：React GUI 已封装进正式发布链路并切换为默认 `todo-gui` 入口。旧 PySide6 widget GUI 已集中归档到 `archive/legacy-pyside6-gui/`，主包、构建 spec、测试计划和 release 文档不再把它作为后续交付对象。

## 1. 本轮调整

- `gui/main.py` 默认启动 `gui/react_shell.py`；`--react` 保留为兼容 no-op。
- `gui/app.py` 改为 React GUI 兼容 wrapper，避免外部旧导入直接断裂。
- `build_gui.spec` 移除旧 widget GUI hidden imports，仅保留 React shell、图标、CLI/engine 和 QtWebEngine 相关依赖。
- `scripts/build.py` 生成的 `todo-react.bat` / `todo-react` 改为透传调用默认 `todo-gui`。
- `pyproject.toml` 不再声明 `todo_manager.gui.widgets` 包。
- 旧 GUI 源码和旧 GUI pytest 文件移入 `archive/legacy-pyside6-gui/`，其中测试文件改名为 `legacy_gui_pytest.py`，避免常规 pytest 自动收集。
- README、里程碑计划、测试计划、M6.5 架构、M6.5/M6.6 验证报告和 release 流程已同步默认入口与归档策略。

## 2. 当前发布入口

- 源码：`todo-gui`
- 源码静态资源 smoke：`todo-gui --react-root frontend/out`
- Windows release：`dist/TodoManager/todo-gui.exe`
- macOS release：`TodoManager.app`
- 兼容入口：`todo-react.bat` / `todo-react`

## 3. 已执行验证

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_gui.py tests\test_react_shell_bridge.py tests\test_release_packaging.py tests\test_source_entrypoints.py -q
C:\Users\dongh\WorkBuddy\20260429224909\todo_manager\.venv\Scripts\python.exe -m todo_manager.gui --help
npm.cmd run lint
npm.cmd run typecheck
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run build
.\.venv\Scripts\python.exe scripts\build.py all
dist\TodoManager\todo-react.bat --help
```

结果：

- compileall 通过。
- 聚焦测试：`15 passed, 1 warning`。
- `python -m todo_manager.gui --help` 在包父目录下通过，显示 React 桌面界面为默认 GUI，`--react` 为兼容旧命令。
- 前端 lint/typecheck/build 通过。
- 全量 pytest：`204 passed, 1 warning`。
- Windows release 已重建：`dist/TodoManager/`。
- Windows zip 已重建并通过 release smoke / zip audit：`dist/TodoManager-windows-2026-05-24.zip`。
- `dist/TodoManager/todo-react.bat` 已改为调用 `todo-gui.exe %*`。

warning 为既有 `.pytest_cache` 写权限 warning，不影响本轮 React GUI 切换判断。

## 4. 后续人工补证

- Windows 真实窗口：双击或运行 `dist\TodoManager\todo-gui.exe --data-dir C:\tmp\todo-react-window-smoke`，验证新建、编辑、删除、撤销、搜索、主题切换和应用图标。
- 兼容入口抽查：运行 `dist\TodoManager\todo-react.bat --data-dir C:\tmp\todo-react-window-smoke`。
- macOS 实机：运行 `python scripts/build.py all` 后打开 `TodoManager.app`，验证 Dock/Finder 图标和核心任务流。

## 5. 真实环境截图反馈修复

2026-05-24 Windows 真实环境截图复测发现两个 UI 问题：

- 1920x1080 最大化窗口中，页面根容器高度超过视口，导致最右侧出现 body 级滚动条。
- 子任务状态 dropdown 永远向上展开，且会被详情面板上方组件遮挡。

已修复：

- `frontend/src/app/globals.css` 将 `html` / `body` 固定为 `height: 100%` 并隐藏 body 级 overflow。
- `frontend/src/components/TodoManagerApp.tsx` 将根布局改为 `h-dvh overflow-hidden`，顶层容器和三栏 grid 使用 `h-full` / `min-h-0` / `flex-1`，三栏面板各自内部滚动。
- `TodayRail`、`CalendarWorkbench`、`TaskDetailPanel` 改为填满可用窗口高度，不再用 `calc(100vh - 118px)` 的独立高度估算。
- `SubtaskRow` 的状态菜单改为 `createPortal(..., document.body)` + fixed 坐标，打开时测量按钮到视口底部的剩余空间：下方足够则向下弹出，不足则向上弹出；菜单层级提升到 `z-[300]`，避免被面板内容遮挡。

复跑验证：

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
.\.venv\Scripts\python.exe -m pytest tests\test_gui.py tests\test_react_shell_bridge.py tests\test_release_packaging.py tests\test_source_entrypoints.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\build.py all
```

结果：前端 lint/typecheck/build 通过；聚焦测试 `15 passed, 1 warning`；全量 pytest `204 passed, 1 warning`；Windows release 目录和 `dist/TodoManager-windows-2026-05-24.zip` 已重新生成，release smoke / zip audit 通过。Codex in-app Browser 仍被本地 URL policy 拦截，QtWebEngine offscreen 探针在当前无头环境无法创建渲染上下文，因此最终视觉确认仍以 Windows 真实窗口复测为准。
