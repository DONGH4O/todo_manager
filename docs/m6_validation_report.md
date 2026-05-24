# M6 双平台打包验证报告

> 日期：2026-05-23  
> 环境：Windows 11 x64，Python 3.14.0，PyInstaller 6.20.0  
> 结论：M6 本地可完成项已收尾。Windows release 于 2026-05-23 重新打包并通过 release smoke / zip audit；macOS 打包配置、`.app` bundle spec、zip 审计和流程文档已建立，仍需在 macOS 原生环境补齐 `.app` 构建和实机启动验证。

## 1. 本轮交付

- 重构 `scripts/build.py`，按宿主平台生成 Windows 或 macOS release 产物。
- 新增 `scripts/smoke_release.py`，统一执行 release 文件清单审计和 CLI/GUI `--help` smoke。
- 更新 `build_cli.spec` 与 `build_gui.spec`，补齐 CLI/GUI hidden imports，并为 macOS GUI 增加 `TodoManager.app` bundle 配置。
- 新增 `docs/release_process.md`，记录双平台打包、smoke、签名和公证口径。
- 新增 `tests/test_release_packaging.py`，覆盖平台 profile、release 目录审计和 zip 审计。

## 2. Windows 产物

命令：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
```

结果：通过。

产物：

| 文件 | 大小 |
|---|---:|
| `dist/TodoManager/todo.exe` | 9,396,855 bytes |
| `dist/TodoManager/todo-gui.exe` | 50,398,138 bytes |
| `dist/TodoManager/Readme.txt` | 804 bytes |
| `dist/TodoManager/install.bat` | 693 bytes |
| `dist/TodoManager-windows-2026-05-23.zip` | 59,316,466 bytes |

release smoke 输出：

```text
[OK] windows release smoke passed: C:\Users\dongh\WorkBuddy\20260429224909\todo_manager\dist\TodoManager
[OK] zip audited: C:\Users\dongh\WorkBuddy\20260429224909\todo_manager\dist\TodoManager-windows-2026-05-23.zip
```

说明：GUI smoke 当前验证 `todo-gui.exe --help`，用于确认冻结二进制可启动到 argparse 入口；真实窗口打开、中文字体和交互仍应在发布候选阶段人工复核。

## 3. macOS 状态

本轮在 Windows 环境执行，无法生成或运行 macOS `.app`。已完成的 macOS 前置项：

- `scripts/build.py` 可识别 macOS 宿主并生成 `TodoManager-macos-YYYY-MM-DD.zip`。
- `build_gui.spec` 在 `sys.platform == "darwin"` 时创建 `TodoManager.app` bundle。
- `scripts/smoke_release.py --platform macos` 会检查 `todo`、`TodoManager.app`、`TodoManager.app/Contents/MacOS/todo-gui` 和 zip 清单。
- `docs/release_process.md` 已记录未签名、未公证状态。
- `tests/test_release_packaging.py` 覆盖 Windows/macOS profile、Windows release tree audit、forbidden content audit 和 macOS `.app` zip audit。

待补齐：

- 在 macOS 上运行 `python scripts/build.py all`。
- 运行 `python scripts/smoke_release.py --platform macos --release-dir dist/TodoManager --zip dist/TodoManager-macos-YYYY-MM-DD.zip`。
- 打开 `TodoManager.app`，确认中文显示、Retina 清晰度、点击交互和快捷键。

## 4. 验收映射

| M6 验收项 | 当前状态 |
|---|---|
| Windows 打包成功并可运行 | 通过：`scripts/build.py all` 生成 CLI、GUI 和 zip；release smoke 通过 |
| macOS 打包成功并可运行 | 部分完成：配置与 smoke 脚本已建立；原生 macOS 构建待补齐 |
| 打包文件清单经过审计 | 通过：Windows release 目录与 zip 审计通过；macOS 审计逻辑已覆盖 |
| 记录 macOS 签名/公证状态 | 通过：当前 `.app` 策略为未签名、未公证，已写入 release 文档 |

## 5. 自动验证

已执行：

```powershell
python -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py
.\.venv\Scripts\python.exe -m pytest tests\test_release_packaging.py tests\test_source_entrypoints.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-2026-05-23.zip
```

结果：

- `engine cli gui scripts` compileall 通过。
- `tests/test_release_packaging.py`：4 passed，1 个 pytest cache 写入权限 warning。
- M6 聚焦测试：8 passed，1 个 pytest cache 写入 warning。
- 全量测试：243 passed，1 个 pytest cache 写入 warning。
- `scripts/build.py all`：通过，生成 `TodoManager-windows-2026-05-23.zip`，Windows release smoke 与 zip audit 均通过。
- 独立复跑 `scripts/smoke_release.py --platform windows ...`：通过。

## 6. 后续建议

- M7 CI 建立后，将 `scripts/build.py react` 与 `scripts/smoke_release.py --react-only` 纳入 React 桌面 release dry-run；完整 PyInstaller release smoke 仍保留在发布候选阶段。
- macOS runner 或实机可用后，补齐 macOS `.app` 原生构建证据。
- 正式公开发布前决定是否加入 Windows Authenticode 和 macOS Developer ID/notarization。

## 7. React 前端交付物打包边界

2026-05-22 新增的 React + Next.js 前端位于 `frontend/`，作为 Figma prototype 对齐后的独立 UI 交付物进入 M5/M6 交接范围。该前端已建立独立的 lint、typecheck、build 和 audit 验证命令；当前 M6 的 PyInstaller release 产物仍只覆盖既有 Python CLI 与 PySide6 GUI。

当前边界：

- `frontend/` 可通过 `npm.cmd run build` 生成 Next.js 生产构建。
- `npm.cmd audit --omit=dev` 用于前端运行依赖安全检查。
- React 前端尚未纳入 `scripts/build.py all`、PyInstaller release zip 或桌面安装脚本。
- 若后续选择 React 前端作为正式发布界面，需要在 M6/M7 之后新增 web/static export、桌面壳或独立分发策略，并将前端构建产物纳入 release smoke 清单。

因此，本报告的 M6 通过结论仍限定为 Windows Python release 与 macOS 打包流程准备；React 前端当前属于已验证的并行 UI 交付物，而不是已打入桌面 release 包的产物。

2026-05-24 更新：上述 React 打包边界已由 M6.5 追补里程碑承接并改变。M6 历史结论不回写，React 正式桌面入口、真实数据桥和 release 资源纳入情况以 `docs/m6_5_validation_report.md` 与 `docs/m6_5_react_desktop_architecture.md` 为准。

2026-05-23 收尾验证：

```powershell
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd audit --omit=dev
```

结果：lint、typecheck、build 均通过；`npm.cmd audit --omit=dev` 结果为 `found 0 vulnerabilities`。

## 8. M6 收尾清单

| 项目 | 状态 |
|---|---|
| Windows CLI/GUI release 产物 | 已完成：`todo.exe`、`todo-gui.exe`、`Readme.txt`、`install.bat` |
| Windows zip 产物 | 已完成：`dist/TodoManager-windows-2026-05-23.zip` |
| Windows release smoke | 已完成：CLI/GUI `--help` 与 zip audit 通过 |
| release 目录洁净度 | 已完成：`scripts/smoke_release.py` 审计通过 |
| macOS 打包配置 | 已完成：build profile、`.app` bundle spec、smoke audit profile 已建立 |
| macOS 原生产物 | 待外部补证：当前 Windows 环境无法生成或运行 `.app` |
| 签名/公证状态 | 已记录：Windows 未签名；macOS 未签名、未公证 |
| React 前端并行交付物 | 已验证：lint/typecheck/build/audit 通过；暂未纳入 Python release 包 |

M6 可进入 M7 的前置状态：本地 Windows 打包闭环完成；下一阶段应优先把 Windows/macOS 测试和 React 桌面 release dry-run 放入 GitHub Actions，并在 macOS runner 或实机上补齐 `.app` 构建证据。
