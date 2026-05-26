# Todo Manager 重整、跨平台与发布里程碑计划

> 版本：v0.1  
> 日期：2026-05-19  
> 状态：草案  
> 配套文档：`requirements_reorg_cross_platform_release.md`、`test_plan_reorg_cross_platform_release.md`
> 计划变更记录：
> - 2026-05-24：正式发布界面目标调整为桌面应用形态的 React 前端；M6 既有 PyInstaller/PySide6 release 基线保留为历史交付，后续通过 M6.5/M7/M10 将 React 纳入正式桌面发布链路，不规划 Web 端发布。
> - 2026-05-24：新增 M6.6 应用图标与桌面品牌资产，在 M6.5 React 桌面发布界面基础上补齐 Windows/macOS GUI 任务栏、桌面和 `.app` 品牌图标。
> - 2026-05-24：React GUI 切换为默认 `todo-gui` 入口；旧 PySide6 widget GUI 归档到 `archive/legacy-pyside6-gui/`，后续里程碑不再围绕旧 GUI 开发或验收。
> - 2026-05-25：M7 完成。Public GitHub repo 已创建并推送 `main`，GitHub Actions 已在 Windows/macOS 通过；repo URL 为 `https://github.com/DONGH4O/todo_manager`。
> - 2026-05-25：新增 M7.5 桌面 GUI 轻量化优化计划；同日完成 Windows 本地可完成项，`todo-gui.exe` 和 Windows zip 体积较 M6.5/M7 基线下降，验证记录见 `docs/m7_5_validation_report.md`。

## 1. 执行原则

本计划按“先稳工程，再改体验，再发布”的顺序推进。跨平台能力贯穿所有阶段，不作为最后补丁处理。

每个里程碑都必须留下可交接产物，方便后续 agent 根据文档、测试和提交历史继续工作。

## 2. 当前项目判定

项目已经有完整功能雏形：

- `engine/`：任务、子任务、历史、软删除、搜索、日历展示。
- `cli/`：argparse CLI，覆盖任务和子任务命令。
- `gui/`：React 桌面壳、QtWebEngine bridge、应用图标和 GUI 入口。
- `frontend/`：React + TypeScript + Tailwind CSS + Next.js App Router 正式桌面 GUI。
- `archive/legacy-pyside6-gui/`：旧 PySide6 widget GUI 归档，仅用于历史追溯。
- `tests/`：已有 engine、CLI、GUI 测试文件。
- `scripts/build.py` 与 PyInstaller spec：已有 Windows 打包基础。
- `prototype.html`：已有 HTML 交互原型。

但项目尚未达到可发布状态：

- 非 Git 仓库。
- 缺少 Python package 元数据。
- 缺少 npm package 元数据。
- 缺少 GitHub CI。
- 缺少跨平台数据目录和打包策略。
- 测试依赖未安装。
- 原型生成脚本不可编译。

## 3. 里程碑总览

| 里程碑 | 名称 | 目标 | 主要交付品 |
|---|---|---|---|
| M0 | 工程基线与仓库化 | 建立可安装、可测试、可提交的项目基础 | Git 初始化、`.gitignore`、`pyproject.toml`、开发依赖、README 初稿 |
| M1 | 跨平台架构重构 | 抽出平台差异，使 Windows/macOS 均可源码运行 | 平台路径模块、入口重构、数据目录策略、基础 smoke tests |
| M2 | 源码审计与可靠性修复 | 修隐藏问题，保护数据安全 | 审计报告、修复补丁、回归测试 |
| M3 | CLI agent 契约 | 让 CLI 适合人类和 agent 同时使用 | JSON 输出、稳定退出码、错误 schema、CLI 文档 |
| M4 | GUI/UX 重设计 | 形成产品级桌面体验设计 | UI/UX 设计文档、设计系统 v2、关键流程说明 |
| M5 | GUI 重构实现 | 将新设计落地，保持跨平台 | 重构后的 PySide6 GUI、隔离 React UI 重写版、主题持久化、响应式布局 |
| M6 | 双平台打包 | 建立 Python/PySide6 Windows/macOS release 基线 | PyInstaller 双平台配置、release 包、打包验证 |
| M6.5 | React 桌面正式发布界面集成 | 将 React 前端纳入桌面应用发布链路 | 桌面壳/桥接方案、真实数据接入、构建打包脚本、桌面 smoke |
| M6.6 | 应用图标与桌面品牌资产 | 为 Windows/macOS GUI 和发布包接入基于 Figma brand mark + brand letter 的应用图标 | 可复现图标资源、Qt 运行时图标、PyInstaller `.ico`/`.icns` 配置、验证报告 |
| M7 | GitHub 与 CI | 建立协作与持续验证能力 | GitHub repo、Actions、Python/React/桌面包检查、release checklist |
| M7.5 | 桌面 GUI 轻量化优化 | 降低 `todo-gui` 发布包体积，同时保持 React 桌面 GUI 稳定 | PyInstaller/QtWebEngine 裁剪策略、体积审计、真实窗口 smoke、回退说明 |
| M8 | npm CLI 发布 | 提供跨平台 npm 命令入口 | `package.json`、Node shim、`npm pack` 验证 |
| M9 | AI Agent SKILL | 让 agent 能可靠调用工具 | `SKILL.md`、references、示例调用 |
| M10 | 发布候选验收 | 汇总正式桌面发布证据并准备正式发布 | 验收报告、版本 tag、GitHub Release、React 桌面应用验收、npm publish checklist |

## 4. 详细里程碑

### M0. 工程基线与仓库化

状态：已完成（2026-05-19）。验证记录见 `docs/m0_validation_report.md`。

目标：先让项目成为一个可协作、可安装、可测试的标准工程。

任务：

- 初始化 Git 仓库。
- 编写 `.gitignore`，排除 `.venv/`、`__pycache__/`、`*.pyc`、`.pytest_cache/`、`dist/`、`build/`、临时数据。
- 新增 `pyproject.toml`，声明项目名、版本、Python 版本、运行依赖、开发依赖、入口点。
- 新增 `README.md` 初稿。
- 新增 `LICENSE`，由项目 owner 确认许可类型。
- 决定 `generate_prototype.py` 和 `_write_proto.py` 是修复、归档还是删除。
- 建立统一开发命令：安装、测试、运行 CLI、运行 GUI。

交付品：

- `.gitignore`
- `pyproject.toml`
- `README.md`
- `LICENSE`
- `docs/dev_setup.md`
- 首次 Git commit

验收：

- 新 shell 中能执行 `python -m pip install -e .[dev]`。
- 能执行 `todo --help` 或明确等价入口。
- 能执行测试命令，哪怕初期有已知失败，也必须有清单。

### M1. 跨平台架构重构

状态：本地实现与回归验证已完成（2026-05-19）；完整 M1 验收待补齐 macOS CLI/GUI 实机运行和 Windows GUI 人工窗口启动。验证记录见 `docs/m1_validation_report.md`。

目标：让源码运行路径和应用数据目录同时兼容 Windows 与 macOS。

任务：

- 新增平台模块，例如 `engine/platform_paths.py` 或 `todo_manager/platform.py`。
- 将冻结态数据目录改为平台分支：
  - Windows：`%APPDATA%/TodoManager/data`
  - macOS：`~/Library/Application Support/TodoManager/data`
  - 开发态：项目 `data/` 或 `--data-dir`
- 用 `pathlib.Path` 逐步替换关键路径拼接。
- 移除正式运行路径中的 `sys.path` 手工注入。
- 明确 CLI 与 GUI 的入口点。
- 增加平台路径单元测试。
- 增加 Windows/macOS 源码运行 smoke test。

交付品：

- 平台路径模块
- 更新后的 `engine/storage.py`
- 更新后的 CLI/GUI 入口
- 跨平台路径测试
- `docs/platform_support.md`

验收：

- Windows 源码运行 CLI 成功。
- macOS 源码运行 CLI 成功。
- Windows 源码启动 GUI 成功。
- macOS 源码启动 GUI 成功。
- 显式 `--data-dir` 覆盖在两平台均生效。

### M2. 源码审计与可靠性修复

状态：本地实现与回归验证已完成（2026-05-19）；macOS 实机验证待后续 CI 或 macOS 环境补齐。审计记录见 `docs/source_audit_report.md`。

目标：清理隐藏问题，尤其是数据安全和重构风险。

任务：

- 审计 engine、storage、CLI、GUI、打包脚本。
- 修复损坏 JSON 静默返回空列表的问题，至少提供错误诊断和备份策略。
- 审计 `Task.from_dict` / `SubTask.from_dict` 对输入 dict 的原地修改风险。
- 审计 CLI 历史记录展示顺序是否符合用户预期。
- 审计 GUI 事件冒泡、任务选中高亮、子任务查找、搜索下拉窗口跨平台行为。
- 审计 `os.replace`、临时文件清理和并发写入。
- 修复原型生成链路或将不可用脚本移入归档目录并说明原因。
- 补回归测试。

交付品：

- `docs/source_audit_report.md`
- 修复补丁
- 新增/更新测试

验收：

- `python -m compileall` 对项目源码通过。
- engine 和 CLI 测试通过。
- GUI 核心测试可在 offscreen 环境运行。
- 审计报告中每个 P0/P1 问题都有处理状态。

### M3. CLI agent 契约

状态：本地实现与回归验证已完成（2026-05-19）；macOS CLI smoke 待后续 CI 或 macOS 环境补齐。契约文档见 `docs/cli_contract.md`，验证记录见 `docs/m3_validation_report.md`。

目标：把 CLI 从“人能读”升级为“人和 agent 都能稳定使用”。

任务：

- 增加全局 `--json`。
- 清理 stdout 中的非结果性提示，例如默认打印数据目录。
- stderr 输出诊断信息。
- 定义 JSON schema：
  - success result
  - validation error
  - not found
  - data file error
  - internal error
- 稳定退出码。
- 确保 Windows 中文输出不乱码。
- 补真实 subprocess CLI 测试。

交付品：

- CLI JSON 模式
- `docs/cli_contract.md`
- JSON schema 示例
- subprocess 测试

验收：

- agent 可通过 JSON 创建、查询、编辑、删除、撤销任务。
- 所有错误路径都能被机器解析。
- Windows/macOS 的 CLI smoke test 均通过。

### M4. GUI/UX 重设计

状态：设计文档、设计系统和 HTML 原型已完成并经用户确认（2026-05-20）；2026-05-21 补充确认 theme toggle 三态原型、深色模式局部文字和搜索下拉点击外部关闭行为。验证记录见 `docs/m4_validation_report.md`。

目标：先设计，再重构，避免在 widget 中边改边猜。

任务：

- 复盘现有 D3 需求和 HTML 原型。
- 输出 UI 信息架构。
- 输出设计系统 v2：颜色、字体、间距、控件、状态、暗色主题。
- 设计关键工作流：
  - 今日任务查看
  - 月份切换
  - 搜索并定位任务
  - 新建任务
  - 新建子任务
  - 编辑状态
  - 删除与撤销
- 明确 1080P、2K、4K 布局规则。
- 明确 macOS 与 Windows 的视觉差异允许范围。

交付品：

- `docs/gui_ux_redesign.md`
- `docs/design_system_v2.md`
- 可选：新版 HTML 原型或截图

验收：

- 后续实现 agent 能仅凭文档理解布局和交互。
- 所有控件状态和空状态都有定义。
- 危险操作和键盘行为有明确规则。

### M5. GUI 重构实现

状态：M5 UI 运行态已按 `docs/m4_uiux_redesign/prototype_v1.html` 和 `docs/m4_uiux_redesign/DESIGN.md` 推倒重建，并于 2026-05-21 二次修正字体 px 语义、居中三栏、任务卡片、月历 mini bar、详情表单/标签和搜索 dropdown 后完成自动回归；2026-05-22 另按 Figma `Engineering Handoff / Codex Ready Spec` 新增隔离的 React + TypeScript + Tailwind CSS + Next.js App Router 前端重写版，验证记录见 `docs/m5_react_frontend_validation_report.md`。2026-05-24 决策：React 前端将作为后续正式发布界面推进，但不回填改写 M5 的历史交付；正式桌面发布集成由 M6.5 承接。完整验收尚未关闭，仍需补齐 Windows 真实窗口、macOS 实机启动和多视口真实字体截图。

目标：落地 M4 设计，同时改善代码结构。

任务：

- 重构主题系统，支持持久化和系统主题策略。
- 优化主布局，减少嵌套卡片和拥挤控件。
- 调整日历任务条、详情面板、搜索下拉、弹窗。
- 封装 GUI 与 engine 的交互层，减少 widget 直接承担业务逻辑。
- 修复任务选中高亮和搜索定位细节。
- 确保快捷键不干扰输入框。
- 增加 GUI smoke tests。

交付品：

- 更新后的 `gui/`
- GUI 测试
- 截图或人工验收记录
- `frontend/` React 前端重写版
- `docs/m5_react_frontend_validation_report.md`

验收：

- Windows/macOS 均可启动 GUI。
- 关键工作流可用。
- 1080P 下无明显文字遮挡或按钮溢出。
- 暗色模式可用且持久化。

### M6. 双平台打包

状态：M6 本地可完成项已收尾（2026-05-23）。Windows release 已重新打包为 `dist/TodoManager-windows-2026-05-23.zip`，CLI/GUI `--help` smoke、release tree audit 和 zip audit 均通过；macOS 打包配置、`.app` bundle spec、zip 审计和流程文档已建立，macOS 原生构建与实机启动待 macOS 环境补齐。React 前端并行交付物已刷新 lint/typecheck/build/audit 验证边界；当前 Python release 包尚未包含 React 前端。2026-05-24 决策：该结论保留为 Python/PySide6 release 基线，React 正式桌面发布不改写 M6，改由 M6.5 追加承接。验证记录见 `docs/m6_validation_report.md`。

目标：建立 Windows 与 macOS 发布产物。

任务：

- 重构 `scripts/build.py`，支持平台分支。
- Windows 产物：CLI exe、GUI exe、zip。
- macOS 产物：CLI 可执行文件、GUI `.app`，可选 dmg/zip。
- 编写 `scripts/smoke_release.py` 或等价验证脚本。
- 检查产物不包含源码外泄、缓存、测试数据。
- 记录 macOS 签名/公证状态。

交付品：

- 双平台 PyInstaller 配置
- `docs/release_process.md`
- release smoke test
- React 前端 build/audit 记录与打包边界说明

验收：

- Windows 打包成功并可运行。
- macOS 打包成功并可运行。
- 打包文件清单经过审计。

### M6.5. React 桌面正式发布界面集成

状态：本地可完成项已完成（2026-05-24）。QtWebEngine 桌面壳、React 真实数据桥、`desktop-react/` release 资源、兼容 `todo-react` 启动器、release smoke 和验证报告已落地；React GUI 已切为默认 `todo-gui` 入口，旧 PySide6 widget GUI 已归档；macOS 原生启动与 Windows 真实窗口人工截图仍待后续补证。验证记录见 `docs/m6_5_validation_report.md` 与 `docs/react_gui_cutover_validation_report.md`。

目标：将 `frontend/` 从隔离 UI 交付物提升为正式桌面应用界面，并接入真实任务数据、发布打包和 smoke 验证链路。

任务：

- 明确桌面壳方案：Tauri、Electron、WebView2 或等价方案择一，并记录选择理由、运行时依赖和包体影响。
- 明确旧 PySide6 widget GUI 的后续定位：归档留存，不再进入正式发布和后续里程碑验收。
- 设计 React 与现有业务层的数据桥接方式：
  - 本地 Python API 服务；
  - 桌面壳 IPC 调用 Python backend；
  - 或通过已有 CLI JSON contract 作为稳定边界。
- 将任务、子任务、搜索、筛选、日历选择、详情编辑、新建任务、删除确认、撤销 toast、主题持久化接入真实数据流。
- 更新构建脚本，将前端构建产物和桌面壳产物纳入 release 目录，但排除 `node_modules/`、Next cache、测试截图和临时文件。
- 扩展 release smoke，覆盖 React 桌面应用启动、关键交互和发布包文件清单。
- 补充桌面窗口尺寸验证：desktop、tablet、mobile 三档布局仍用于响应式验收，但正式入口是桌面应用窗口，不发布 Web 站点。

交付品：

- React 桌面发布架构说明
- 桌面壳配置和构建脚本
- 真实数据桥接层
- 更新后的 release smoke
- React 桌面应用截图/Playwright 或等价验证记录
- 更新后的 `docs/release_process.md`

验收：

- Windows 能从发布包启动 React 桌面应用并完成核心任务流。
- macOS 能从发布包启动 React 桌面应用并完成核心任务流。
- React UI 使用真实任务数据，不再依赖 sample/in-memory 数据作为正式路径。
- 发布包不包含源码缓存、测试临时文件或未裁剪依赖。
- 旧 PySide6 widget GUI 的归档/退役策略在 README 和 release 文档中明确。

### M6.6. 应用图标与桌面品牌资产

状态：本地实现与自动回归已完成（2026-05-24）；Windows 真实任务栏/桌面图标和 macOS Dock/Finder 图标仍需发布包实机补证。Figma MCP 当前因账号计划调用限制无法实时导出原型节点，本轮按 M4/M5 已落地的 Figma handoff brand mark + brand letter 样式生成可复现资源。验证记录见 `docs/m6_6_application_icon_validation_report.md`。

目标：让 Todo Manager GUI 在 Windows 和 macOS 的任务栏缩略图、Alt-Tab/Command-Tab、桌面/文件管理器和 `.app` bundle 中呈现统一应用图标。

任务：

- 以 Figma 原型 `Todo Manager M4 UI Prototype v1` 中的 `brand mark` 与 `brand letter` 组合为源样式，生成可复现应用图标资源。
- 图标资源集中放入 `assets/icons/`，包含运行时 PNG、Windows `.ico`、macOS `.icns` 和可读源 SVG。
- React QtWebEngine 壳在源码运行时设置项目 `QIcon`。
- Windows 运行时设置 AppUserModelID，减少任务栏缩略图继续显示默认 Python/Qt 图标的风险。
- PyInstaller GUI spec 在 Windows EXE 中嵌入 `.ico`，在 macOS `.app` bundle 中嵌入 `.icns`，并打包运行时图标资源。
- 补自动测试和发布流程说明，记录 Windows/macOS 实机补证项。

交付品：

- `assets/icons/todo-manager.png`
- `assets/icons/todo-manager.ico`
- `assets/icons/todo-manager.icns`
- `assets/icons/todo-manager.svg`
- `scripts/generate_app_icons.py`
- 更新后的 `gui/` 图标接入
- 更新后的 `build_gui.spec`
- `docs/m6_6_application_icon_validation_report.md`

验收：

- 源码运行 React 桌面壳窗口加载非空应用图标。
- Windows 打包后的 `todo-gui.exe` 使用项目图标，任务栏缩略图和桌面快捷入口不再显示默认图标。
- macOS 打包后的 `TodoManager.app` 使用项目图标，Dock、Command-Tab 和 Finder 显示一致。
- 图标生成脚本可复跑且不会产生临时散落文件。
- 自动回归覆盖图标资源存在性、Qt 窗口图标和 PyInstaller spec 图标配置。

### M7. GitHub 与 CI

状态：已完成（2026-05-25）。Public GitHub repo 已创建：`https://github.com/DONGH4O/todo_manager`；`main` 已推送；GitHub Actions run `26367268744` 已在 Windows/macOS 通过。验证记录见 `docs/m7_validation_report.md`。

目标：让协作和发布可持续。

任务：

- 创建 GitHub repo。
- 推送主分支。
- 配置 GitHub Actions：
  - Windows 测试
  - macOS 测试
  - CLI smoke
  - React lint/typecheck/build/audit
  - React 桌面应用 smoke 或打包 dry-run
  - 可选打包 dry-run
- 增加 release checklist。
- 增加 PR 检查说明。

交付品：

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/release_checklist.md`
- `docs/m7_validation_report.md`
- GitHub repo URL：`https://github.com/DONGH4O/todo_manager`

验收：

- Windows CI 通过。
- macOS CI 通过。
- React 前端和桌面发布链路在 CI 中得到覆盖。
- README 上的安装与测试命令在 CI 中得到覆盖。

### M7.5. 桌面 GUI 轻量化优化

状态：Windows 本地可完成项已完成（2026-05-25）。已新增可复现体积审计脚本、`build_gui.spec` 低风险 PyInstaller/QtWebEngine 裁剪策略、release smoke 回流检查和验证报告；`todo-gui.exe` 从 218,866,808 bytes 降至 170,487,859 bytes，Windows zip 从 227,082,390 bytes 降至 178,811,133 bytes。macOS `.app` 体积复核与实机窗口 smoke 仍待 macOS 环境补证。验证记录见 `docs/m7_5_validation_report.md`。

目标：在不牺牲 React 桌面 GUI 稳定性、中文显示、日期选择器和核心任务流的前提下，降低 Windows/macOS 发布包体积，并为后续发布候选建立可复现的体积审计口径。

任务：

- 建立 `todo-gui` 体积审计脚本或文档化命令，按 PyInstaller archive 分类统计 QtWebEngine、Qt resources、locales、Qt Quick/QML、Python runtime 等体积。
- 在正式修改前保留基线数据，例如当前 Windows `todo-gui.exe` 约 208 MB，`desktop-react/` 约 0.82 MB，证明大头不在 React 静态资源。
- 评估低风险 PyInstaller 裁剪：
  - 移除 QtWebEngine debug/devtools 资源；
  - 仅保留必要 locale，例如 `zh-CN` 与 `en-US`；
  - 排除 Qt3D、Charts、DataVisualization、Multimedia、Pdf、Quick3D 等正式 GUI 未使用模块；
  - 保留 `Qt6WebEngineCore.dll`、QtWebEngine process、核心 resources、QtWebChannel 和 Widgets 栈。
- 为 `build_gui.spec` 增加可读的裁剪规则，并补测试防止 debug/devtools、多余 locale 或无关 Qt 模块回流。
- 重新执行 Windows 真实窗口 smoke，覆盖启动、悬浮、点击、输入、日期选择器、状态选择、新建/删除/撤销、搜索、主题切换和图标显示。
- 在 macOS 环境执行对应 `.app` 启动与体积复核，避免 Windows-only 裁剪破坏 macOS bundle。
- 明确回退策略：若裁剪导致 QtWebEngine 渲染、中文字体、日期弹层或桥接不稳定，优先恢复稳定性，再缩小裁剪范围。
- 仅在 PyInstaller/QtWebEngine 裁剪无法满足目标时，另行评估 WebView2/Tauri/WKWebView 等桌面壳替代路线；该替代路线不在本里程碑默认实施范围内。

交付品：

- 更新后的 `build_gui.spec` 或独立裁剪配置说明
- 体积审计记录
- 更新后的 release smoke / packaging tests
- Windows 与 macOS 真实窗口验证记录
- 回退说明

验收：

- `todo-gui` 发布体积较 M6.5/M7 基线有明确下降，且体积变化可复现。
- Windows/macOS React 桌面 GUI 核心任务流全部通过。
- 发布包不包含 debug/devtools 资源、多余 locale、无关 Qt 模块或前端缓存。
- 若体积目标与稳定性冲突，以稳定性为验收优先级。

### M8. npm CLI 发布

目标：提供跨平台 npm 安装入口。

任务：

- 设计 npm wrapper 策略。
- 新增 `package.json`。
- 新增 `bin/` 下的 Node launcher。
- 定义 npm 包内容白名单。
- 增加 `npm pack --dry-run` 检查。
- 增加 npm 安装后的 CLI smoke test。

交付品：

- `package.json`
- `bin/todo-manager` 或等价入口
- `docs/npm_publish.md`

验收：

- Windows 上 `npm install -g` 后可执行 CLI。
- macOS 上 `npm install -g` 后可执行 CLI。
- `npm pack --dry-run` 文件清单干净。

### M9. AI Agent SKILL

目标：让其他 agent 能正确使用 Todo Manager。

任务：

- 编写 `skills/todo-manager/SKILL.md`。
- 编写 `skills/todo-manager/references/cli.md`。
- 编写 `skills/todo-manager/references/json-schema.md`。
- 提供常见任务流示例。
- 写明不支持能力和安全边界。

交付品：

- `skills/todo-manager/SKILL.md`
- references 文档

验收：

- agent 能按 skill 查日历、列任务、建任务、改状态、撤销删除。
- skill 不依赖 GUI。
- skill 中没有过时路径或平台假设。

### M10. 发布候选验收

目标：形成可发布版本。

任务：

- 全量跑测试。
- 双平台运行 smoke。
- React 桌面应用启动与关键流程 smoke。
- npm pack dry-run。
- GitHub release dry-run。
- 更新版本号和 changelog。
- 确认 README、SKILL、release docs 与实际行为一致。

交付品：

- `CHANGELOG.md`
- 发布候选验收报告
- tag
- GitHub Release
- React 桌面应用发布验收记录
- npm publish checklist

验收：

- Windows 源码运行、CLI、React 桌面 GUI、打包产物均通过。
- macOS 源码运行、CLI、React 桌面 GUI、打包产物均通过。
- npm 包安装后 CLI 可用。
- SKILL 经 agent 调用验证。

## 5. 推荐推进顺序

推荐先完成 M0、M1、M2，再进入 GUI 重设计。原因：

- GUI 重构会触碰大量文件，如果包结构和测试环境不稳，后续回归成本会快速上升。
- 跨平台路径与入口会影响 CLI、GUI、打包、npm、SKILL，必须尽早定型。
- agent 调用要求会反过来影响 CLI 输出契约，最好在 npm 和 SKILL 之前完成。

## 6. 每轮 agent 交接要求

后续 agent 每完成一个里程碑，应更新：

- 对应文档的状态。
- 测试命令和结果。
- 已知问题清单。
- 若涉及发布，附 dry-run 文件清单摘要。
