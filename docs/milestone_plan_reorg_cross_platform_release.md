# Todo Manager 重整、跨平台与发布里程碑计划

> 版本：v0.1  
> 日期：2026-05-19  
> 状态：草案  
> 配套文档：`requirements_reorg_cross_platform_release.md`、`test_plan_reorg_cross_platform_release.md`

## 1. 执行原则

本计划按“先稳工程，再改体验，再发布”的顺序推进。跨平台能力贯穿所有阶段，不作为最后补丁处理。

每个里程碑都必须留下可交接产物，方便后续 agent 根据文档、测试和提交历史继续工作。

## 2. 当前项目判定

项目已经有完整功能雏形：

- `engine/`：任务、子任务、历史、软删除、搜索、日历展示。
- `cli/`：argparse CLI，覆盖任务和子任务命令。
- `gui/`：PySide6 GUI，覆盖月历、搜索、详情、弹窗、撤销、快捷键。
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
| M5 | GUI 重构实现 | 将新设计落地，保持跨平台 | 重构后的 PySide6 GUI、主题持久化、响应式布局 |
| M6 | 双平台打包 | 建立 Windows/macOS release 产物 | PyInstaller 双平台配置、release 包、打包验证 |
| M7 | GitHub 与 CI | 建立协作与持续验证能力 | GitHub repo、Actions、release checklist |
| M8 | npm CLI 发布 | 提供跨平台 npm 命令入口 | `package.json`、Node shim、`npm pack` 验证 |
| M9 | AI Agent SKILL | 让 agent 能可靠调用工具 | `SKILL.md`、references、示例调用 |
| M10 | 发布候选验收 | 汇总发布证据并准备正式发布 | 验收报告、版本 tag、GitHub Release、npm publish checklist |

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

验收：

- Windows/macOS 均可启动 GUI。
- 关键工作流可用。
- 1080P 下无明显文字遮挡或按钮溢出。
- 暗色模式可用且持久化。

### M6. 双平台打包

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

验收：

- Windows 打包成功并可运行。
- macOS 打包成功并可运行。
- 打包文件清单经过审计。

### M7. GitHub 与 CI

目标：让协作和发布可持续。

任务：

- 创建 GitHub repo。
- 推送主分支。
- 配置 GitHub Actions：
  - Windows 测试
  - macOS 测试
  - CLI smoke
  - 可选打包 dry-run
- 增加 release checklist。
- 增加 PR 检查说明。

交付品：

- `.github/workflows/ci.yml`
- `docs/release_checklist.md`
- GitHub repo URL

验收：

- Windows CI 通过。
- macOS CI 通过。
- README 上的安装与测试命令在 CI 中得到覆盖。

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
- npm pack dry-run。
- GitHub release dry-run。
- 更新版本号和 changelog。
- 确认 README、SKILL、release docs 与实际行为一致。

交付品：

- `CHANGELOG.md`
- 发布候选验收报告
- tag
- GitHub Release
- npm publish checklist

验收：

- Windows 源码运行、GUI、CLI、打包产物均通过。
- macOS 源码运行、GUI、CLI、打包产物均通过。
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
