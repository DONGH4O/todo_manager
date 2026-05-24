# M6.6 应用图标与桌面品牌资产验证报告

> 日期：2026-05-24  
> 环境：Windows 11 x64，Python 3.14.0  
> 结论：M6.6 本地实现与自动回归已完成。源码运行时的 React QtWebEngine 壳已接入应用图标；PyInstaller GUI spec 已配置 Windows `.ico`、macOS `.icns` 和运行时 PNG 资源。旧 PySide6 widget GUI 已归档，不再作为后续图标验收对象。Windows 真实任务栏/桌面图标与 macOS Dock/Finder 图标仍需发布包实机补证。

## 1. 本轮交付

- 新增 `scripts/generate_app_icons.py`，按 Figma handoff 已落地的 brand mark + brand letter 样式生成图标资源。
- 新增 `assets/icons/todo-manager.png`、`todo-manager.ico`、`todo-manager.icns`、`todo-manager.svg`。
- 新增 `gui/icon.py`，集中处理运行时图标路径、Windows AppUserModelID 和 Qt `QIcon` 应用。
- 更新 `gui/app.py` / `gui/main.py`，默认 GUI 入口转向 React 桌面壳。
- 更新 `gui/react_shell.py`，React 桌面壳窗口设置同一图标。
- 更新 `build_gui.spec`，Windows EXE 嵌入 `.ico`，macOS `.app` 嵌入 `.icns`，并将 `assets/icons/` 纳入 PyInstaller datas。
- 更新 `pyproject.toml`，将 `assets/icons/*` 作为 package data。
- 更新 README、release 流程、测试计划和里程碑计划。

## 2. Figma 取证边界

本轮尝试通过 Figma MCP 读取 `Todo Manager M4 UI Prototype v1` 根节点时返回账号计划调用限制，无法实时导出 `brand mark` / `brand letter` 节点。因此当前图标资源依据仓库中已从 Figma handoff 落地的 `BrandLockup` / M4 原型样式生成：蓝绿渐变圆角 brand mark 与白色 brand letter `T`。

后续若 Figma MCP 额度恢复，可补一次节点级导出比对；若视觉有差异，以 Figma 原型节点为准刷新 `scripts/generate_app_icons.py` 和 `assets/icons/`。

## 3. 已执行验证

```powershell
.\.venv\Scripts\python.exe scripts\generate_app_icons.py
.\.venv\Scripts\python.exe -m compileall gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_gui.py tests\test_release_packaging.py -q
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest -q
```

结果：

- 图标生成脚本通过，资源集中输出到 `assets/icons/`。
- `compileall gui scripts` 和 `compileall engine cli gui scripts` 均通过。
- 聚焦测试 `53 passed, 1 warning`，覆盖 Qt 窗口图标非空和 PyInstaller spec 图标配置。
- 全量 pytest `248 passed, 1 warning`。
- warning 为既有 `.pytest_cache` 写权限 warning，不影响本轮图标功能判断。

## 4. 后续补证

- Windows release：重新运行 `.\.venv\Scripts\python.exe scripts\build.py all`，检查 `todo-gui.exe` 文件图标、任务栏缩略图、Alt-Tab 和 `todo-react.bat` 启动窗口图标。
- macOS release：在 macOS 上运行 `python scripts/build.py all`，检查 `TodoManager.app` 在 Finder、Dock 和 Command-Tab 中的图标。
- 若创建桌面快捷方式，确认快捷方式继承 `todo-gui.exe` 图标或显式指向 `assets/icons/todo-manager.ico`。
