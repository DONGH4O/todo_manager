# M6.5 React 桌面发布架构说明

> 日期：2026-05-24  
> 状态：M6.5 本地实现完成，React GUI 已切为默认入口，macOS 原生启动待 M7/CI 或实机补证  
> 对应里程碑：M6.5 React 桌面正式发布界面集成

## 1. 桌面壳选择

M6.5 选择 **PySide6 QtWebEngine** 作为当前正式桌面壳，React 仍作为唯一正式发布界面，PySide6 在该路径中只承担 WebView 宿主和本地桥接职责。

选择理由：

- 复用 M6 已建立的 Python/PyInstaller/PySide6 release 基线，不引入 Rust、Electron runtime 或 WebView2 的额外安装链路。
- Windows/macOS 均可通过 QtWebEngine 加载 `frontend/out/index.html` 或 release 包内 `desktop-react/ui/index.html`。
- 数据桥接可直接复用 M3 CLI JSON contract，避免 React 层直接导入 Python 业务模块。
- 包体会增加 QtWebEngine 相关运行时，但仍由现有 PyInstaller 体系统一裁剪和审计。

暂不选择：

- Tauri：需要 Rust toolchain 与额外跨平台签名/构建链路，当前里程碑成本偏高。
- Electron：跨平台能力强，但会新增独立 runtime、npm 安装体积和额外安全审计面。
- WebView2：Windows 体验好，但无法覆盖 macOS 正式发布入口。

## 2. GUI 定位

2026-05-24 切换后，React 是唯一正式 GUI。PySide6 在正式路径中只保留 QtWebEngine 宿主、QtWebChannel bridge 和应用图标设置；旧 PySide6 widget GUI 已归档到 `archive/legacy-pyside6-gui/`，不再进入后续里程碑、发布包或 npm 发布路径。

- 源码运行：`todo-gui`
- Windows release：`todo-gui.exe`
- macOS release：`TodoManager.app`
- 兼容启动器：`todo-react.bat` / `todo-react`
- 兼容参数：`--react` 保留为 no-op，旧脚本仍可运行

如后续真实场景测试确认无误，M10 发布候选只验收 React 桌面 GUI；归档的 widget GUI 仅用于历史追溯。

## 3. 数据桥接

正式桌面数据路径：

```text
React UI
  -> window.todoBridge.request(...)
  -> QtWebChannel / TodoBridge
  -> todo --json --data-dir <optional> ...
  -> engine/storage tasks.json
```

关键文件：

- `frontend/src/lib/todo-data.ts`：React 数据服务；桌面桥优先，普通浏览器仅保留本地预览兜底。
- `gui/react_shell.py`：QtWebEngine 壳、QtWebChannel 注入和 CLI JSON bridge。
- `gui/main.py`：默认启动 React shell；`--react` 兼容旧命令，`--react-root` 用于源码/打包 smoke。
- `build_gui.spec`：补齐 QtWebEngine / QtWebChannel hidden imports。

React 已接入真实数据流覆盖：

- 任务列表与日历展示
- 新建任务
- 编辑任务字段与状态
- 删除任务和撤销删除
- 新建子任务
- 子任务状态保存
- 搜索、筛选、日期选择和主题持久化

## 4. Release 布局

Windows release 关键布局：

```text
dist/TodoManager/
  todo.exe
  todo-gui.exe
  todo-react.bat
  desktop-react/
    manifest.json
    ui/
      index.html
      _next/
```

macOS release 关键布局：

```text
dist/TodoManager/
  todo
  TodoManager.app/
  todo-react
  desktop-react/
    manifest.json
    ui/
      index.html
      _next/
```

`desktop-react/` 不包含 `node_modules/`、`.next/`、测试截图或临时文件。

## 5. 构建与 Smoke

React 桌面资源构建：

```powershell
.\.venv\Scripts\python.exe scripts\build.py react
```

完整 zip 重新打包和审计：

```powershell
.\.venv\Scripts\python.exe scripts\build.py zip
```

`scripts/smoke_release.py` 已扩展为检查：

- `desktop-react/manifest.json`
- `desktop-react/ui/index.html`
- Windows `todo-gui.exe` / `todo-react.bat` 或 macOS `TodoManager.app` / `todo-react`
- release/zip 中不得包含 `.next`、`node_modules`、测试目录、缓存、源码 `.py` 或 `.pyc`

## 6. 已知边界

- 当前 Windows 环境已验证源码 bridge、React build、release 文件清单和 zip audit。
- 当前未在 macOS 原生环境运行 QtWebEngine 壳，需 M7 CI 或 macOS 实机补证。
- 当前未执行真实 GUI 窗口自动化截图；本地 Browser 插件访问 `file://` 与 `localhost` 均被浏览器策略拦截，已用构建、桥接测试和 release smoke 替代。
