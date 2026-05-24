# Todo Manager 发布流程

> 版本：v0.1  
> 日期：2026-05-24  
> 覆盖里程碑：M6 双平台打包、M6.5 React 桌面正式发布界面集成、M6.6 应用图标与桌面品牌资产、M7 CI release dry-run

## 1. 发布原则

M6 采用原生平台打包策略：Windows 产物必须在 Windows 上构建，macOS 产物必须在 macOS 上构建。当前流程不做跨平台交叉编译。

发布产物必须满足：

- CLI 与 React 桌面 GUI 同时存在；旧 PySide6 widget GUI 不进入发布路径。
- GUI 可执行文件、React 桌面壳窗口和 macOS `.app` 必须使用同一应用图标。
- zip 包经过文件清单审计。
- release 包不包含 `.venv`、`.git`、`__pycache__`、`.pytest_cache`、测试目录或源码 `.py` 文件。
- React 桌面资源不包含 `node_modules/`、`.next/`、测试截图或临时文件。
- macOS `.app` 的签名/公证状态必须记录；未签名时必须明确说明。

## 2. 环境准备

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm.cmd install
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

macOS shell：

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## 3. Windows 打包

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

预期产物：

- `dist\TodoManager\todo.exe`
- `dist\TodoManager\todo-gui.exe`
- `dist\TodoManager\todo-react.bat`
- `dist\TodoManager\Readme.txt`
- `dist\TodoManager\install.bat`
- `dist\TodoManager\desktop-react\manifest.json`
- `dist\TodoManager\desktop-react\ui\index.html`
- `dist\TodoManager-windows-YYYY-MM-DD.zip`
- `todo-gui.exe` 嵌入 `assets\icons\todo-manager.ico`。

手动复核：

```powershell
dist\TodoManager\todo.exe --help
dist\TodoManager\todo-gui.exe --help
dist\TodoManager\todo-react.bat
```

如需只复跑发布审计：

```powershell
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
```

## 4. macOS 打包

```bash
python scripts/build.py all
```

预期产物：

- `dist/TodoManager/todo`
- `dist/TodoManager/TodoManager.app`
- `dist/TodoManager/todo-react`
- `dist/TodoManager/Readme.txt`
- `dist/TodoManager/desktop-react/manifest.json`
- `dist/TodoManager/desktop-react/ui/index.html`
- `dist/TodoManager-macos-YYYY-MM-DD.zip`
- `TodoManager.app` 嵌入 `assets/icons/todo-manager.icns`。

手动复核：

```bash
./dist/TodoManager/todo --help
./dist/TodoManager/TodoManager.app/Contents/MacOS/todo-gui --help
open ./dist/TodoManager/TodoManager.app
./dist/TodoManager/todo-react
```

如需只复跑发布审计：

```bash
python scripts/smoke_release.py --platform macos --release-dir dist/TodoManager --zip dist/TodoManager-macos-YYYY-MM-DD.zip
```

当前 M6 流程生成的 macOS `.app` 未签名、未公证。正式发布前必须由项目 owner 决定是否加入 Developer ID 签名和 notarization 流程。

## 5. 发布审计口径

`scripts/smoke_release.py` 会检查：

- 平台必需产物是否存在。
- release 目录是否包含缓存、测试目录或源码文件。
- zip 文件是否包含同样的必需产物。
- CLI 与 GUI 二进制能否响应 `--help`。
- React 桌面资源和平台启动器是否存在，且 zip 中不包含 `.next` 或 `node_modules`。

该脚本不替代真实窗口验收。GUI 正式发布前仍需在 Windows 和 macOS 上打开 `todo-react`，确认 React 界面的中文字体、主题、弹窗、快捷键和核心任务流表现。

M7 起该脚本额外支持 CI dry-run：

```powershell
.\.venv\Scripts\python.exe scripts\build.py react
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --react-only
```

`--react-only` 只审计 React 桌面资源、兼容启动器、Readme 和禁止内容清单，不要求 PyInstaller CLI/GUI 二进制已生成；完整 release smoke 仍必须使用不带 `--react-only` 的命令。

## 6. 应用图标资源

M6.6 起应用图标由 `scripts/generate_app_icons.py` 从 Figma handoff 已落地的 brand mark + brand letter 样式生成，输出集中放在 `assets/icons/`：

```powershell
.\.venv\Scripts\python.exe scripts\generate_app_icons.py
```

关键产物：

- `assets/icons/todo-manager.png`：Qt 运行时窗口图标。
- `assets/icons/todo-manager.ico`：Windows PyInstaller EXE 图标。
- `assets/icons/todo-manager.icns`：macOS `.app` bundle 图标。
- `assets/icons/todo-manager.svg`：可读源图形。

发布前真实窗口验收需确认：

- Windows 任务栏、Alt-Tab/缩略图和桌面/文件资源管理器中的 `todo-gui.exe` 图标可见。
- `todo-gui.exe` 及兼容启动器 `todo-react.bat` 启动后的 React 桌面壳窗口使用同一图标。
- macOS Dock、Command-Tab、Finder 中的 `TodoManager.app` 使用同一图标。

## 7. 当前签名状态

- Windows：未做 Authenticode 签名。
- macOS：未做 Developer ID 签名，未做 notarization。

正式公开分发前，release note 或 README 必须继续保留上述状态说明，除非后续里程碑补齐签名流程。

## 8. M6 收尾检查清单

M6 本地收尾时至少执行：

```powershell
python -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py tests\test_source_entrypoints.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
```

React 桌面界面已在 M6.5 纳入 release zip，并在 2026-05-24 切换为默认 GUI。若只需要刷新 React 桌面资源：

```powershell
.\.venv\Scripts\python.exe scripts\build.py react
.\.venv\Scripts\python.exe scripts\build.py zip
```

2026-05-24 M6.5 收尾记录：Windows release 产物 `TodoManager-windows-2026-05-24.zip` 已生成并通过 smoke；React 前端 lint/typecheck/build 通过；QtWebEngine bridge 测试通过；macOS 原生 `.app` 和 `todo-react` 启动仍需在 macOS 环境补证。

## 9. Windows React 真实窗口验收

M6.5 的自动 smoke 不替代真实窗口验收。Windows 人工验收建议使用独立数据目录，避免污染日常任务数据：

```powershell
mkdir C:\tmp\todo-react-window-smoke
dist\TodoManager\todo-gui.exe --data-dir C:\tmp\todo-react-window-smoke
```

窗口打开后检查：

- 首屏能显示 React 桌面界面，没有显示“桌面数据桥不可用”错误。
- 新建任务：标题、开始/截止日期、状态、背景保存后出现在今日 rail 和月历中；若使用全新数据目录，可先新建今天、昨天和下月各一条任务，覆盖 rail、历史月历和跨月定位。
- 日期选择器：在新建任务、编辑任务和新建子任务中打开日期选择器，弹层宽度稳定，窗口右边界不随时间外扩。
- 编辑任务：从月历或搜索结果定位到任务后修改标题、背景和状态并保存，刷新后仍保留。
- 子任务：新增子任务，打开子任务状态菜单时弹层稳定，最后一条子任务不会向下撑开边框；修改子任务状态并保存，刷新后仍保留。
- 删除与撤销：删除任务后任务从列表和月历消失；点击撤销后任务恢复。
- 搜索与定位：搜索刚创建的任务或子任务，结果可选中并定位到详情；搜索下拉底部应显示绿色提示“提示：点击结果可定位到对应日期与任务；Esc关闭”，空结果状态也应显示。
- 主题：light/dark/system 切换可见，重启窗口后选择保持。

验收后可用 CLI 复核真实数据写入：

```powershell
dist\TodoManager\todo.exe --json --data-dir C:\tmp\todo-m65-window-smoke list
```

记录建议：保存一张真实窗口截图，并把上述核心流程结果补入 `docs/m6_5_validation_report.md` 后续补证区。
