# Todo Manager 重整与跨平台发布需求文档

> 版本：v0.1  
> 日期：2026-05-19  
> 状态：草案  
> 适用项目：`todo_manager`

## 1. 背景

Todo Manager 已完成核心数据引擎、CLI、PySide6 GUI、HTML 原型与 PyInstaller 打包脚本的主要开发。下一阶段目标不是继续堆功能，而是把项目整理成可维护、可测试、可跨平台运行、可发布、可被 AI agent 稳定调用的产品化项目。

当前已知事实：

- 项目目录当前不是 Git 仓库。
- 项目缺少 `pyproject.toml`、`.gitignore`、`README.md`、`LICENSE` 等发布基础文件。
- `.venv` 中只有 PySide6，缺少 pytest 与 PyInstaller；现有测试暂时不能直接运行。
- 当前源码以 Windows 为默认运行环境，打包说明和安装脚本也偏 Windows。
- `engine/storage.py` 的冻结态默认数据目录依赖 `%APPDATA%`，macOS 缺少对应应用数据目录策略。
- `scripts/build.py`、`build_cli.spec`、`build_gui.spec` 当前产物以 `.exe` 和 `install.bat` 为中心。
- `generate_prototype.py` 与 `_write_proto.py` 当前存在语法错误，原型生成链路不可复现。
- CLI 在未设置 UTF-8 输出环境时，Windows 终端可能出现中文乱码。
- 从项目根目录直接导入 `todo_manager` 会失败，说明包结构和运行入口需要规范化。

## 2. 总体目标

本轮重整应达成以下目标：

1. 重新设计 GUI 的 UI/UX，使其更美观、更清晰、更适合长时间任务管理。
2. 审计并修复源码中的隐藏问题，尤其是数据安全、路径、编码、并发写入、打包、跨平台行为。
3. 重构项目代码，使其能在 Windows 和 macOS 上运行。
4. 建立 GitHub repo 工程面，包括 CI、README、版本、发布说明和 release checklist。
5. 发布 npm CLI 工具，使用户和 AI agent 能通过稳定命令调用 Todo Manager。
6. 编写 SKILL，使 AI agent 能理解工具边界、调用 CLI、解析输出、处理错误。

## 3. 平台支持范围

### 3.1 必须支持

- Windows 10/11 x64。
- macOS 13+，Apple Silicon 与 Intel 至少各保留明确策略；若短期无法同时产出二进制包，源码安装和 CLI 调用必须可用。
- Python 3.11 至 3.13 作为推荐支持范围。

### 3.2 暂不承诺

- Linux 桌面打包。
- iOS、Android。
- 多用户同步、云存储、网络 API。
- 任务提醒、系统托盘、后台常驻。

## 4. 功能需求

### R1. 核心引擎保持行为兼容

- 任务和子任务数据模型继续兼容现有 D1 v2 文档。
- `tasks.json` 的 `version: 2` 格式继续可读写。
- v1 数据缺失 `subtasks` 时应自动升级为空列表。
- 软删除、撤销删除、历史快照、日期展示规则不得因跨平台重构发生行为退化。

### R2. 跨平台数据目录

应用必须使用平台合适的数据目录：

- Windows 冻结态默认：`%APPDATA%\TodoManager\data`。
- macOS 冻结态默认：`~/Library/Application Support/TodoManager/data`。
- 开发态默认：项目本地 `data` 目录，或由 `--data-dir` 显式覆盖。

数据目录逻辑必须集中在单一模块，禁止 GUI、CLI、打包脚本各自拼路径。

### R3. 路径与文件系统行为

- 全部路径处理优先使用 `pathlib.Path`。
- 不得硬编码 Windows 路径分隔符。
- 原子写入需要兼容 Windows 和 macOS。
- 临时文件清理失败不得造成数据丢失；应有可诊断错误路径。
- 损坏 JSON 不应静默吞掉而导致用户误以为数据为空；至少 CLI/GUI 要能给出可恢复提示。

### R4. 包结构与入口

- 项目必须可以通过标准包方式安装。
- CLI 应提供稳定入口命令，例如 `todo`。
- GUI 应提供稳定入口命令，例如 `todo-gui` 或 `todo gui`。
- 不应依赖手动修改 `sys.path` 来运行正式入口。
- 所有入口在 Windows PowerShell、Windows Terminal、macOS Terminal 中都应可用。

### R5. CLI agent 友好性

CLI 必须提供面向 AI agent 的稳定模式：

- 支持 `--json` 或等价机器可读输出。
- stdout 默认只输出结果；诊断信息、数据目录提示、警告应进入 stderr 或调试模式。
- 退出码必须稳定：成功为 0，参数错误、校验错误、数据错误、内部错误应可区分。
- 错误输出应包含可解析的错误 code 与人类可读 message。
- 所有命令必须支持 `--data-dir`，并清楚规定全局参数放置位置；推荐支持命令前和命令后两种形式。

### R6. GUI UI/UX 重设计

GUI 应继续以月历为主体，但需要从“功能可用”提升到“产品级可用”：

- 视觉风格更现代，减少卡片套卡片和大面积单色块。
- 明暗主题应一致且可持久化，优先使用 Qt 原生设置机制。
- 顶部搜索、月份导航、日历、详情区的层级要更清晰。
- 日历格、任务条、详情字段、弹窗按钮在 1080P、2K、4K 下不得拥挤或溢出。
- 所有图标按钮必须有 tooltip；重要危险操作必须有确认。
- 支持键盘快捷键，且不干扰文本输入。
- GUI 不维护独立业务缓存，数据变更应通过 engine 完成。

### R7. macOS GUI 体验

- PySide6 GUI 在 macOS 下必须能启动、显示中文、响应点击和快捷键。
- 高 DPI / Retina 显示下文字和控件不可模糊。
- macOS 应使用合适的 app name、窗口标题和应用数据目录。
- 若发布 `.app` 或 `.dmg`，需要记录签名/公证状态；未签名时必须在 README 中说明。

### R8. Windows GUI 体验

- Windows 打包产物继续提供 GUI 与 CLI。
- 中文输出应优先以 UTF-8 处理。
- `install.bat` 不应是唯一安装策略；npm 和 Python 包安装路径应同样可用。

### R9. npm CLI 发布

npm 包的目标是给用户和 agent 一个跨平台命令入口，而不是只分发 Windows `.exe`。

要求：

- `package.json` 必须声明 `bin`。
- npm 包中不得包含 `.venv`、`dist`、缓存、测试临时文件。
- npm wrapper 应能在 Windows 和 macOS 下启动 Todo Manager CLI。
- 推荐策略：npm 包提供 Node shim，调用已安装的 Python 包或随包 wheel/bootstrap；具体实现须在设计阶段明确。
- `npm pack --dry-run` 必须纳入发布验证。

### R10. GitHub repo 与 CI

GitHub repo 必须包含：

- README：安装、运行、开发、测试、打包、agent 用法。
- LICENSE。
- `.gitignore`。
- CI workflow：Windows 与 macOS 至少运行静态检查、单元测试、CLI smoke test。
- Release checklist。
- Issue/PR 模板可选，但推荐加入。

### R11. SKILL

SKILL 应面向 AI agent，清楚描述：

- 何时使用 Todo Manager。
- 如何调用 CLI。
- 如何指定数据目录。
- 如何使用 JSON 输出。
- 如何处理错误。
- 哪些能力不支持，例如云同步、提醒、跨设备同步。

SKILL 必须短小清晰；详细命令和 schema 可放在 references 文件中。

## 5. 非功能需求

### N1. 可维护性

- UI、engine、CLI、打包、发布逻辑分层清楚。
- 平台差异集中封装。
- 业务逻辑不应散落在 GUI widget 内。

### N2. 可测试性

- 单元测试覆盖 engine。
- CLI 使用 subprocess 或等价端到端测试覆盖真实入口。
- GUI 测试覆盖核心交互，不追求像素级快照。
- 跨平台测试通过 CI 执行。

### N3. 数据安全

- 写入失败时不得损坏已有 `tasks.json`。
- 损坏文件应保留，不能直接覆盖。
- 删除仍然为软删除。

### N4. 编码与国际化

- 所有源码、文档、JSON 文件使用 UTF-8。
- Windows 终端中文输出必须有明确测试和文档说明。
- 项目文案当前继续中文优先。

### N5. 发布洁净度

- 源码包、wheel、npm 包、GitHub release 包都不得包含虚拟环境、缓存、pyc、pytest cache、旧 dist。
- 每次发布必须有 dry-run 输出和文件清单审计。

## 6. 当前风险清单

| 风险 | 影响 | 要求 |
|---|---|---|
| 缺少 Git 和发布元数据 | 无法安全协作和发布 | M0 必须补齐 |
| 测试依赖缺失 | 无法验证重构 | M0 必须建立开发依赖 |
| Windows 路径和 `.exe` 假设 | macOS 不可用 | M1/M2 必须抽象平台层 |
| 原型生成脚本语法错误 | UI 原型不可复现 | M1 决定修复或归档 |
| CLI stdout 有数据目录提示 | agent 难解析 | M3 必须清理输出契约 |
| 中文终端乱码 | Windows 用户体验差 | M3/M6 必须验证 |
| PyInstaller 只面向 Windows | macOS 二进制发布缺口 | M5 必须建立双平台策略 |

## 7. 验收总口径

本轮工作完成时，必须能证明：

1. Windows 与 macOS 均可从源码运行 CLI 和 GUI。
2. Windows 与 macOS CI 均能通过测试。
3. GitHub repo 具备可读、可维护、可发布的工程面。
4. npm 包 dry-run 文件清单干净，安装后 CLI 可调用。
5. SKILL 能指导 AI agent 完成常见任务管理操作。
6. GUI 新设计完成并落地，关键工作流可用。

