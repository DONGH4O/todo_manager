# Todo Manager 重整与跨平台发布测试计划

> 版本：v0.1  
> 日期：2026-05-19  
> 状态：草案  
> 配套文档：`requirements_reorg_cross_platform_release.md`、`milestone_plan_reorg_cross_platform_release.md`

## 1. 测试目标

本测试计划用于验证 Todo Manager 在重整、跨平台、发布和 agent 调用场景下的质量。

核心目标：

1. 防止 engine 行为在重构中退化。
2. 验证 Windows 与 macOS 的源码运行、数据目录、CLI、GUI 行为。
3. 验证 CLI 机器可读契约，确保 AI agent 可稳定调用。
4. 验证发布包、npm 包和 SKILL 的可用性。
5. 验证 GUI 重设计后关键工作流可用且无明显布局问题。

## 2. 测试环境矩阵

| 环境 | Python | 目标 |
|---|---|---|
| Windows 11 x64 | 3.11、3.12、3.13 任选至少 1 个主版本 | 开发、CLI、GUI、打包、npm |
| macOS 13+ Apple Silicon | 3.11、3.12、3.13 任选至少 1 个主版本 | 开发、CLI、GUI、打包、npm |
| macOS 13+ Intel | 可选，至少记录策略 | 打包兼容性评估 |

推荐 CI 最小矩阵：

- `windows-latest` + Python 3.12
- `macos-latest` + Python 3.12

本地发布前扩展矩阵：

- Windows + Python 3.11/3.12/3.13
- macOS + Python 3.11/3.12/3.13

## 3. 测试类型

### 3.1 静态与编译检查

目的：发现语法错误、导入错误和基础工程问题。

命令：

```powershell
python -m compileall engine cli gui scripts
```

后续可加入：

```powershell
python -m ruff check .
python -m mypy engine cli gui
```

验收：

- 项目正式源码无语法错误。
- 不可维护或废弃脚本必须修复、删除或移入归档，并在文档说明。

### 3.2 Engine 单元测试

覆盖范围：

- `Task`、`SubTask`、`VersionRecord` 序列化。
- 创建、查询、更新、删除、撤销。
- 子任务父子关系。
- 日期展示规则。
- 搜索与扁平化。
- v1 数据兼容。

重点新增：

- `Task.from_dict` 与 `SubTask.from_dict` 不应意外污染输入 dict。
- 损坏 JSON 不应静默当作空数据成功处理。
- 原子写入失败时旧文件保留。
- Windows/macOS 路径下保存和读取均正常。

验收：

```powershell
python -m pytest tests/test_task_manager.py tests/test_storage.py tests/test_calendar.py
```

### 3.3 CLI 测试

现有 CLI 测试主要直接调用 command 函数。重整后必须增加真实入口测试。

覆盖范围：

- `todo --help`
- `todo add`
- `todo list`
- `todo show`
- `todo edit`
- `todo delete`
- `todo undo`
- `todo sub add/list/show/edit/delete/undo`
- `todo cal`
- `todo search`
- `todo stats`
- `--data-dir`
- `--json`

真实入口示例：

```powershell
todo --data-dir C:\tmp\todo-smoke add "测试任务" -s 2026-05-19 -e 2026-05-19 --status 未启动
todo --data-dir C:\tmp\todo-smoke list --json
```

macOS 示例：

```bash
todo --data-dir /tmp/todo-smoke add "测试任务" -s 2026-05-19 -e 2026-05-19 --status 未启动
todo --data-dir /tmp/todo-smoke list --json
```

验收：

- stdout 中无非结果性噪声。
- stderr 用于错误和诊断。
- JSON 输出可被标准 JSON parser 解析。
- 退出码符合 CLI contract。
- Windows 中文输出不乱码。

### 3.4 平台路径测试

覆盖范围：

- Windows 冻结态默认目录。
- macOS 冻结态默认目录。
- 开发态默认目录。
- 显式 `--data-dir` 覆盖。
- 路径中包含空格、中文字符。

建议通过 monkeypatch 模拟：

- `sys.platform`
- `APPDATA`
- `HOME`
- `sys.frozen`

测试样例：

| 用例 | 输入 | 期望 |
---|---|---|
| Windows frozen | `APPDATA=C:\Users\me\AppData\Roaming` | `...\TodoManager\data` |
| macOS frozen | `HOME=/Users/me` | `~/Library/Application Support/TodoManager/data` |
| explicit data dir | `--data-dir <path>` | 完全使用显式路径 |
| Chinese path | `C:\tmp\待办数据` | 正常读写 |

### 3.5 GUI 测试

GUI 测试不追求像素级精确，重点验证核心交互。

覆盖范围：

- GUI 启动。
- 默认展示今天。
- 月份前后切换。
- 搜索任务并定位。
- 新建任务弹窗字段。
- 编辑任务。
- 删除任务和撤销。
- 新建子任务。
- 暗色主题切换与持久化。
- 快捷键不干扰输入框。

命令：

```powershell
python -m pytest tests/test_gui.py
```

macOS 本地人工检查：

- 中文显示正常。
- Retina 下清晰。
- 快捷键可用。
- 弹窗不跑到屏幕外。
- 搜索下拉层级正常。

### 3.6 GUI 视觉验收

M5 完成后需要人工或截图验收。

视口：

- 1366x768 或等价小屏。
- 1920x1080。
- 2560x1440。
- 3840x2160。

检查项：

- 顶部栏不拥挤。
- 月历格高度稳定。
- 任务条文字不明显溢出。
- 详情面板字段可读。
- 图标按钮有 tooltip。
- 暗色模式对比度足够。
- 弹窗按钮和输入框不重叠。

### 3.7 打包测试

Windows：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
dist\TodoManager\todo.exe --help
dist\TodoManager\todo-gui.exe --help
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
```

macOS：

```bash
python scripts/build.py all
./dist/TodoManager/todo --help
./dist/TodoManager/TodoManager.app/Contents/MacOS/todo-gui --help
open ./dist/TodoManager/TodoManager.app
python scripts/smoke_release.py --platform macos --release-dir dist/TodoManager --zip dist/TodoManager-macos-YYYY-MM-DD.zip
```

验收：

- 打包成功。
- CLI 产物可运行。
- GUI 产物可启动。
- 数据目录符合平台要求。
- release 包中不包含 `.venv`、`__pycache__`、`.pytest_cache`、测试临时数据。

### 3.8 npm 包测试

必须测试：

```bash
npm pack --dry-run
npm install -g .
todo-manager --help
todo-manager --json stats
```

Windows PowerShell 也需等价测试。

验收：

- `npm pack --dry-run` 文件清单干净。
- 安装后命令在 Windows 和 macOS 可执行。
- npm wrapper 能正确传递参数、stdin、stdout、stderr 和退出码。
- 卸载后不残留不可解释文件。

### 3.8.5 React 桌面壳测试

M6.5 起正式发布界面为 React 桌面界面，需覆盖：

- `npm run lint`、`npm run typecheck`、`npm run build`。
- `todo-gui --react-root frontend/out` 可加载 React 静态导出，且不需要 `--react` 即可启动 React GUI。
- `tests/test_react_shell_bridge.py` 验证 QtWebEngine bridge 通过 CLI JSON contract 创建、更新、读取任务。
- `scripts/build.py react` 生成 `desktop-react/` 与平台启动器。
- `scripts/smoke_release.py` 审计 release/zip 中包含 React 桌面资源且不包含 `.next`、`node_modules`、测试截图或临时文件。
- Windows 手工打开 `todo-gui.exe`，macOS 手工打开 `TodoManager.app`，验证新建、编辑、删除、撤销、搜索和主题切换；`todo-react.bat` / `todo-react` 仅作为兼容启动器抽查。

### 3.8.6 应用图标测试

M6.6 起需覆盖 GUI 应用图标：

- `scripts/generate_app_icons.py` 可复现生成 `png`、`ico`、`icns`、`svg`。
- React QtWebEngine 壳窗口设置项目 `QIcon`；旧 PySide6 widget GUI 仅归档留存，不再作为验收对象。
- `build_gui.spec` 在 Windows EXE 中使用 `.ico`，在 macOS `.app` bundle 中使用 `.icns`，并将运行时 PNG 资源纳入 PyInstaller datas。
- Windows 手工检查任务栏、Alt-Tab/缩略图和桌面/文件资源管理器图标。
- macOS 手工检查 Dock、Command-Tab 和 Finder `.app` 图标。

### 3.8.7 GitHub Actions CI

M7 起最小 CI gate 由 `.github/workflows/ci.yml` 承载，覆盖 `windows-latest` 与 `macos-latest`：

- Python 3.12 环境安装：`python -m pip install -e ".[dev]"`。
- Python 编译检查：`python -m compileall engine cli gui scripts`。
- 全量回归：`python -m pytest -q`。
- README 入口 smoke：`todo --help`、`todo-gui --help`。
- CLI JSON smoke：运行 `python scripts/ci_cli_smoke.py`，使用独立临时数据目录创建任务并解析 `list --json` 输出。
- React 前端验证：`npm ci`、`npm run lint`、`npm run typecheck`、`npm run build`、`npm audit --omit=dev`。
- React 桌面 release dry-run：`python scripts/build.py react` 与 `python scripts/smoke_release.py --react-only`。

CI 不替代完整 PyInstaller release build；完整发布包仍按 3.7 在 Windows/macOS 原生环境执行 `scripts/build.py all` 与完整 `scripts/smoke_release.py`。

### 3.8.8 桌面 GUI 轻量化测试

M7.5 起需覆盖 `todo-gui` 发布体积审计和 PyInstaller/QtWebEngine 裁剪策略：

- `scripts/audit_release_size.py` 可对 release 目录、zip 和 PyInstaller `PKG-00.toc` 输出分类体积。
- `build_gui.spec` 保留 QtWebEngine、QtWebChannel、Widgets 和核心 runtime，排除 debug/devtools、多余 QtWebEngine locale 和未使用 Qt add-on 模块。
- `scripts/smoke_release.py` 在 release tree / zip 审计中拒绝裁剪资源回流。
- Windows/macOS 完整发布包均需记录 `todo-gui`、release zip 和 `desktop-react/` 体积。
- 发布候选阶段仍需真实窗口 smoke，覆盖启动、桥接、新建、编辑、删除、撤销、日期选择器、状态菜单、搜索、主题切换和图标显示。

Windows 示例：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe scripts\build.py audit-size
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
```

验收：

- `todo-gui` 发布体积较 M6.5/M7 基线有明确下降，且变化可复现。
- 体积审计未发现 debug/devtools、多余 locale、无关 Qt 模块或前端缓存回流。
- 若体积目标与稳定性冲突，以稳定性为优先级。

### 3.9 SKILL 测试

使用一个独立数据目录验证 agent 工作流：

1. 查看今日任务。
2. 新建一个主任务。
3. 新建一个子任务。
4. 修改主任务状态。
5. 搜索任务。
6. 删除子任务。
7. 撤销删除。
8. 输出最终任务摘要。

验收：

- agent 只依赖 CLI JSON 模式即可完成。
- SKILL 中的命令与实际 CLI 一致。
- 错误处理说明能覆盖 not found、validation error、data file error。

## 4. 发布前完整验收清单

发布候选必须完成：

- `python -m compileall engine cli gui scripts`
- engine 测试通过。
- CLI 真实入口测试通过。
- GUI 测试通过。
- Windows CI 通过。
- macOS CI 通过。
- Windows 本地 GUI smoke 通过。
- macOS 本地 GUI smoke 通过。
- Windows 打包产物 smoke 通过。
- macOS 打包产物 smoke 通过。
- `npm pack --dry-run` 文件清单审计通过。
- SKILL agent 工作流通过。
- README 与实际命令一致。
- release checklist 完成。

## 5. 当前阻塞与前置动作

当前无法执行完整测试，原因：

- 本地 `.venv` 缺少 pytest。
- 本地 `.venv` 缺少 PyInstaller。
- 项目缺少 `pyproject.toml`，无法按标准 editable package 安装。

M0 必须先解决这些前置动作，然后再以本测试计划作为回归基线。
