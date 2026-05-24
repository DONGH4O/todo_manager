# M6.5 React 桌面正式发布界面集成验证报告

> 日期：2026-05-24  
> 环境：Windows 11 x64，Python 3.14.0，Node/npm 已安装  
> 结论：M6.5 本地可完成项已完成。React 前端已接入真实任务数据桥，QtWebEngine 桌面壳和 `todo-gui` 默认入口已纳入构建与 smoke；`todo-react` 仅作为兼容启动器保留。macOS 原生启动和真实窗口截图待后续补证。

## 1. 本轮交付

- 新增 `gui/react_shell.py`，通过 PySide6 QtWebEngine 加载 React 静态导出，并用 QtWebChannel 注入 `window.todoBridge`。
- 更新 `gui/main.py`，支持 `todo-gui` 默认启动 React GUI；`--react` 保留为兼容 no-op，`--react-root` 用于 smoke。
- 更新 `frontend/src/lib/todo-data.ts`，React UI 正式路径优先走桌面桥和 CLI JSON contract。
- 更新 `frontend/src/components/TodoManagerApp.tsx`，任务/子任务/删除/撤销/状态/保存/刷新均接入真实数据服务。
- 更新 `scripts/build.py`，新增 `react` target，生成 `desktop-react/` 和 `todo-react` 启动器。
- 更新 `scripts/smoke_release.py` 和 `tests/test_release_packaging.py`，把 React 桌面产物纳入 release/zip 审计。
- 新增 `tests/test_react_shell_bridge.py`，用独立数据目录验证 QtWebEngine bridge 通过 CLI JSON 创建、更新和列表读取任务。
- 新增 `docs/m6_5_react_desktop_architecture.md`。

## 2. 验收映射

| M6.5 验收项 | 当前状态 |
|---|---|
| Windows 从发布包启动 React 桌面应用并完成核心任务流 | 部分完成：`todo-gui.exe` 默认入口和 `todo-react.bat` 兼容入口已生成；桥接核心任务流由 `tests/test_react_shell_bridge.py` 验证；真实窗口启动待人工执行 |
| macOS 从发布包启动 React 桌面应用并完成核心任务流 | 待补证：macOS launcher 与 audit 规则已建立，需 macOS 环境运行 |
| React UI 使用真实任务数据 | 通过：桌面路径经 `window.todoBridge` 调 CLI JSON；sample/localStorage 仅作为浏览器预览兜底 |
| 发布包不包含缓存、测试临时文件或未裁剪依赖 | 通过：`scripts/build.py zip` 触发 release smoke 和 zip audit |
| PySide6 策略在 README 和 release 文档中明确 | 已更新：旧 PySide6 widget GUI 归档；QtWebEngine 壳承接 React 正式界面 |

## 3. 已执行验证

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
.\.venv\Scripts\python.exe -m pytest tests\test_react_shell_bridge.py tests\test_release_packaging.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\build.py react
.\.venv\Scripts\python.exe scripts\build.py zip
.\.venv\Scripts\python.exe -m todo_manager.gui --help
npm.cmd audit --omit=dev
```

结果：

- 前端 lint：通过。
- 前端 typecheck：通过。
- 前端 build/static export：通过。
- React shell bridge + release packaging tests：6 passed；pytest cache 写入权限 warning 仍存在。
- 全量 pytest：245 passed；pytest cache 写入权限 warning 仍存在。
- `scripts/build.py react`：通过，生成 `desktop-react/`、`todo-react.bat`。
- `scripts/build.py zip`：通过，生成 `dist/TodoManager-windows-2026-05-24.zip`，release smoke 与 zip audit 均通过。
- `todo-gui --help`：通过，已显示 `--react` 和 `--react-root`。
- `npm audit --omit=dev`：通过，`found 0 vulnerabilities`。

## 4. Browser 验证说明

尝试用 Codex Browser 打开 `file:///.../desktop-react/ui/index.html` 时被浏览器 URL policy 拦截；改用 `http://127.0.0.1:4173/` 和 `http://localhost:4173/` 静态服务也被浏览器报告 `net::ERR_BLOCKED_BY_CLIENT`。因此本轮未取得 Browser 截图，以 Next build、CLI bridge 测试、release tree/zip audit 作为自动验证证据。

## 5. 审计跟进修复

2026-05-24 审计跟进已修复两项 M6.5 发布界面风险：

- React 桌面正式模式新增 `desktop=1` URL 标记和 `window.todoDesktopShell` 壳标记；桥接不可用时会报告 `bridge_unavailable`，不再静默回退到 sample/localStorage 预览数据。
- CLI JSON 删除成功后会重新读取已删除对象，`delete` / `sub delete` payload 中的 `task.deleted` / `subtask.deleted` 与持久化状态保持一致；QtWebEngine bridge 的 `deleteTask` 返回值同步修正。

复跑验证：

```powershell
python -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_cli_contract.py tests\test_react_shell_bridge.py -q
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe scripts\build.py react
.\.venv\Scripts\python.exe scripts\build.py zip
```

结果：compileall 通过；CLI contract + React shell bridge 聚焦测试 `7 passed`；全量 pytest `245 passed`，仍有 `.pytest_cache` 写权限 warning；前端 lint/typecheck/build 通过；React 资源和 Windows zip 重新生成，release smoke / zip audit 通过。

## 6. 真实窗口问题跟进修复

2026-05-24 针对 Windows 真实窗口 smoke 中暴露的问题继续修复：

- 桌面桥接注入改为在 QtWebEngine `DocumentReady` 阶段加载，并在 `qrc:///qtwebchannel/qwebchannel.js` 成功加载后再安装 `window.todoBridge`；若 Qt transport 或脚本加载失败，会显式派发 `todoBridgeUnavailable`。这修复了过早注入脚本时 DOM 挂载点尚不可用，导致新建任务报“桌面数据桥不可用”的问题。
- 新建/编辑任务与新建子任务的日期字段改用成熟组件 `react-day-picker`，通过项目内 `DatePickerField` 统一封装；不再使用 QtWebEngine 中表现不稳定的原生 `input type="date"` 弹层，避免日期选择器打开后窗口右边界持续外扩。
- 搜索结果下拉移除空结果提前返回，空结果和有结果状态都会渲染底部绿色提示框，提示文案固定为“提示：点击结果可定位到对应日期与任务；Esc关闭”。
- `frontend/package-lock.json` 清理了一个缺失 version/resolved/integrity 的异常可选依赖条目，随后安装 `react-day-picker@10.0.1` 与 `date-fns@4.1.0` 并通过 npm audit。

复跑验证：

```powershell
python -m compileall gui scripts
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd audit --omit=dev
cd ..
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py tests\test_react_shell_bridge.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-2026-05-24.zip
```

结果：compileall 通过；前端 lint/typecheck/build 通过；`npm audit --omit=dev` 通过，`found 0 vulnerabilities`；release packaging + React shell bridge 聚焦测试 `6 passed`；全量 pytest `245 passed`，仍有 `.pytest_cache` 写权限 warning；`scripts/build.py all` 重新生成 Windows release 目录和 zip，release smoke / zip audit 通过。受当前自动化环境限制，真实可见窗口交互仍需人工按 release 流程补证。

## 7. 后续补证

- Windows 人工双击 `dist/TodoManager/todo-gui.exe`，验证真实窗口可打开并执行新建、编辑、删除、撤销；兼容抽查 `dist/TodoManager/todo-react.bat`。
- macOS 上运行 `python scripts/build.py all` 或至少 `python scripts/build.py react && python scripts/build.py zip`，再执行 `./todo-react`。
- M7 CI 中加入 React build、bridge test、`scripts/build.py react` 与 `scripts/smoke_release.py --react-only`。

## 8. 发布包黑屏问题跟进修复

2026-05-24 Windows release 真实窗口复测发现：发布包启动后卡顿明显，新建任务后页面进入 Next 错误页，显示 “This page couldn't load”，之后 reload 仍复现。通过 QtWebEngine 远程调试确认根因有两层：

- 冻结版 `todo.exe` 在 Windows 上输出本地代码页字节，旧桥接层固定按 UTF-8 + replacement 解码，导致 `"完成中"` / `"未启动"` 被解析为乱码；React 渲染任务卡片时用 `statusTone[task.status].dot` 直接取值，未知状态触发 `TypeError: Cannot read properties of undefined (reading 'dot')`，Next 因此切换到错误页。
- 旧桥接层每次 `list/create/update` 都在 GUI 线程同步启动一次 `todo.exe`，release 环境下一次 bridge `listTasks` 实测约 5.8 秒，造成首屏和新建任务明显卡顿。

已修复：

- `gui/react_shell.py` 改为同进程调用 `engine.task_manager`，保留 React bridge 的请求/响应语义，避免每次操作拉起冻结版 EXE。
- 保留 CLI 字节流自适应解码 helper，并新增回归测试覆盖 Windows 本地代码页输出，防止类似乱码路径回归。
- `frontend/src/lib/tokens.ts` 新增状态归一化与 `getStatusTone()`，`TaskCard`、`StatusBadge`、`MiniTaskPill`、`SubtaskRow` 改走兜底样式；`todo-data` 在 bridge 数据归一化时将未知状态兜底为 `"未启动"`，防止脏数据打崩整页。

复跑验证：

```powershell
python -m compileall gui
.\.venv\Scripts\python.exe -m pytest tests\test_react_shell_bridge.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py tests\test_react_shell_bridge.py -q
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe scripts\build.py all
```

结果：React shell bridge 聚焦测试 `2 passed`；release packaging + bridge 聚焦测试 `7 passed`；全量 pytest `246 passed`，仍有 `.pytest_cache` 写权限 warning；前端 lint/typecheck/build 通过；Windows release 目录和 zip 已重新生成，release smoke / zip audit 通过。重建后使用 QtWebEngine CDP 验证：页面无 “This page couldn't load”，`window.todoBridge.request({ action: "listTasks" })` 返回中文状态正常，bridge `listTasks` 约 `1ms`；通过 release 页面新建 `release final create probe` 后约 `807ms` 内任务可见，无运行时异常。

## 9. 子任务状态选择器跟进修复

2026-05-24 Windows 真实窗口复测确认其他模块正常，仅任务详情中最后一个子任务的状态选择器仍会在打开下拉时持续向下扩展边框。该问题与此前原生日期输入类似，属于 QtWebEngine 对原生表单弹层的表现不稳定。

已修复：`frontend/src/components/todo/SubtaskRow.tsx` 移除原生 `<select>`，改为按钮 + 固定尺寸上弹菜单；菜单使用绝对定位，不参与行高和滚动容器布局计算，因此不会继续向下撑开最后一个子任务行。复跑 `npm.cmd run lint`、`npm.cmd run typecheck`、`npm.cmd run build` 通过，并刷新 release React 资源与 Windows zip。

## 10. React GUI 默认入口切换与旧 GUI 归档

2026-05-24 根据后续发布方向，React GUI 已切换为默认桌面入口，旧 PySide6 widget GUI 已移入 `archive/legacy-pyside6-gui/`，不再作为后续里程碑、GitHub release 或 npm 发布路径的一部分。

交付调整：

- `todo-gui` / `todo-gui.exe` 默认启动 React QtWebEngine 桌面壳。
- `--react` 保留为兼容 no-op，旧命令和旧启动器仍可运行。
- `todo-react.bat` / `todo-react` 改为透传调用默认 `todo-gui`，仅作为兼容启动器。
- `gui/` 主路径只保留 `main.py`、`react_shell.py`、`icon.py`、`app.py` 兼容 wrapper 和包入口。
- 旧 widget GUI 源码与旧 GUI pytest 文件集中归档到 `archive/legacy-pyside6-gui/`。

复跑验证：

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_gui.py tests\test_react_shell_bridge.py tests\test_release_packaging.py tests\test_source_entrypoints.py -q
npm.cmd run lint
npm.cmd run typecheck
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run build
.\.venv\Scripts\python.exe scripts\build.py all
```

结果：compileall 通过；聚焦测试 `15 passed, 1 warning`；前端 lint/typecheck/build 通过；全量 pytest `204 passed, 1 warning`；`scripts/build.py all` 重新生成 `dist/TodoManager/` 和 `dist/TodoManager-windows-2026-05-24.zip`，release smoke 与 zip audit 通过。warning 仍为既有 `.pytest_cache` 写权限 warning。
