# M7.5 桌面 GUI 轻量化优化验证报告

> 日期：2026-05-25  
> 环境：Windows 11 x64，Python 3.14.0，本地 `.venv`，PyInstaller 6.20.0，Node 24.11.1  
> 结论：M7.5 Windows 本地可完成项已完成。`todo-gui.exe` 和 Windows zip 体积较 M6.5/M7 基线明确下降；发布包 smoke、PyInstaller TOC 体积审计、M7.5 裁剪策略检查和真实窗口 CDP bridge smoke 均通过。macOS `.app` 体积复核与实机窗口 smoke 仍需在 macOS 环境补证。

## 1. 本轮交付

- 新增 `scripts/audit_release_size.py`，支持按 release 目录、zip 和 PyInstaller `PKG-00.toc` 统计体积分类，并检查 M7.5 裁剪策略。
- 更新 `build_gui.spec`，为 GUI one-file archive 增加可读裁剪策略：
  - 仅保留 QtWebEngine locale allowlist：`en-US`、`zh-CN`。
  - 移除 QtWebEngine debug/devtools 资源。
  - 排除正式 React 桌面壳未使用的 Qt3D、Charts、DataVisualization、Multimedia、Pdf、Quick3D 等模块。
  - 保留 QtWebEngine、QtWebChannel、Widgets、Qt runtime、应用图标和 React release 资源。
- 更新 `scripts/smoke_release.py`，在 release tree / zip 审计中拒绝 debug/devtools、多余 QtWebEngine locale 和无关 Qt 模块回流。
- 更新 `scripts/build.py`，新增 `audit-size` target，可复跑当前 release 体积审计。
- 更新 `tests/test_release_packaging.py`，覆盖 M7.5 spec 策略、release smoke 回流检查和体积审计分类。

## 2. 体积结果

| 产物 | M6.5/M7 基线 | M7.5 当前 | 变化 |
|---|---:|---:|---:|
| `dist/TodoManager/todo-gui.exe` | 218,866,808 bytes / 208.73 MiB | 170,487,859 bytes / 162.59 MiB | -48,378,949 bytes / -46.14 MiB / -22.1% |
| `dist/TodoManager-windows-2026-05-25.zip` | 227,082,390 bytes / 216.56 MiB | 178,811,133 bytes / 170.53 MiB | -48,271,257 bytes / -46.04 MiB / -21.3% |
| `dist/TodoManager/desktop-react/` | 约 0.82 MiB | 863,866 bytes / 0.82 MiB | 基本不变 |

`scripts/audit_release_size.py` 当前 release 目录分类：

| 分类 | 体积 | 占比 |
|---|---:|---:|
| `gui_binary` | 162.59 MiB | 94.32% |
| `cli_binary` | 8.96 MiB | 5.20% |
| `react_desktop` | 0.82 MiB | 0.48% |

PyInstaller `PKG-00.toc` 内部审计使用未压缩源文件体积估算，不等同于最终 EXE 大小，但可用于判断主要来源：

| 分类 | 体积 | 占比 |
|---|---:|---:|
| `qt_webengine` | 215.81 MiB | 53.04% |
| `qt_runtime` | 132.98 MiB | 32.68% |
| `native_other` | 18.67 MiB | 4.59% |
| `qt_qml_quick` | 18.07 MiB | 4.44% |
| `qt_locales` | 11.22 MiB | 2.76% |
| `python_runtime` | 7.84 MiB | 1.93% |
| `qt_webchannel` | 0.12 MiB | 0.03% |

结论：体积大头仍在 QtWebEngine / Chromium runtime，但本轮已移除最高收益且低风险的 devtools、多语言 locale 和无关 Qt 模块；React 静态资源不是主要体积来源。

## 3. 验证记录

已执行命令：

```powershell
.\.venv\Scripts\python.exe -m compileall scripts gui engine cli
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py -q
.\.venv\Scripts\python.exe scripts\audit_release_size.py --release-dir dist\TodoManager --zip dist\TodoManager-windows-2026-05-25.zip
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe -m PyInstaller build_gui.spec --distpath dist\TodoManager --workpath .tmp\m75-gui-audit --noconfirm
.\.venv\Scripts\python.exe scripts\audit_release_size.py --release-dir dist\TodoManager --zip dist\TodoManager-windows-2026-05-25.zip --pyinstaller-workpath .tmp\m75-gui-audit
.\.venv\Scripts\python.exe scripts\build.py zip
```

结果：

- `compileall scripts gui engine cli`：通过。
- `tests/test_release_packaging.py`：`14 passed, 1 warning`；warning 仍为既有 `.pytest_cache` 写权限 warning。
- `scripts/build.py all`：通过，生成 `dist/TodoManager/todo.exe`、`dist/TodoManager/todo-gui.exe`、`dist/TodoManager/desktop-react/` 和 `dist/TodoManager-windows-2026-05-25.zip`。
- 完整 release smoke / zip audit：通过。
- 体积审计：通过，未发现 M7.5 裁剪策略回流。

真实窗口 CDP smoke：

- 使用发布包 `dist/TodoManager/todo-gui.exe` 启动真实 QtWebEngine 窗口，并通过 `QTWEBENGINE_REMOTE_DEBUGGING=9234` 连接页面。
- 页面标题为 `Todo Manager`，加载 URL 为 `desktop-react/ui/index.html?desktop=1`。
- 页面未出现 `This page couldn't load`。
- `window.todoBridge` 可用。
- bridge 核心流通过：`listTasks`、`createTask`、`updateTask`、`deleteTask`、`undoTask`、再次 `listTasks`。
- 中文状态路径通过：任务从 `未启动` 更新到 `完成中`；删除后 `deleted=true`，撤销后 `deleted=false`。

## 4. 剩余边界

- Windows 本轮完成了真实窗口启动与 CDP bridge 核心流验证；日期选择器、状态菜单、悬浮、点击和主题切换的完整人工视觉复核仍建议在发布候选阶段继续执行。
- macOS `.app` 的体积复核、启动和真实窗口 smoke 仍需在 macOS 环境补证，避免 Windows-only 裁剪策略破坏 macOS bundle。
- 若后续发现裁剪导致 QtWebEngine 渲染、中文字体、日期弹层或 bridge 不稳定，应优先恢复稳定性，再缩小裁剪范围。
