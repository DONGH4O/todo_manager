# Todo Manager Release Checklist

> 版本：v0.1  
> 日期：2026-05-24  
> 覆盖范围：M7 GitHub 与 CI、M7.5 桌面 GUI 轻量化、M10 发布候选验收前置清单  
> GitHub repo URL：<https://github.com/DONGH4O/todo_manager>

本清单用于每次发布候选前确认源码、CI、React 桌面界面、发布包和文档处于同一状态。勾选项应以命令输出、CI run 链接、release zip 文件清单或人工验收记录为证据。

## 1. 仓库与协作

- [ ] GitHub repo 已创建，默认分支为 `main`。
- [ ] `main` 分支已推送最新代码。
- [ ] `.github/workflows/ci.yml` 在 GitHub Actions 中可见。
- [ ] Pull Request 必须等待 Windows 与 macOS CI 通过后再合并。
- [ ] README、LICENSE、`.gitignore`、release 文档和里程碑文档随本次发布同步更新。
- [ ] `git status --short` 中没有未解释的临时文件、构建产物或缓存目录。

## 2. 本地基础验证

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m compileall engine cli gui scripts
.\.venv\Scripts\python.exe -m pytest -q
```

macOS shell：

```bash
python -m compileall engine cli gui scripts
python -m pytest -q
```

验收：

- [ ] Python 编译检查通过。
- [ ] 全量 pytest 通过；若仅有已知 warning，必须在验证报告中记录。
- [ ] `todo --help` 与 `todo-gui --help` 和 README 命令一致。
- [ ] CLI JSON smoke 可创建并列出任务；CI 使用 `python scripts/ci_cli_smoke.py` 固定 UTF-8 子进程环境。

## 3. React 前端验证

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
npm audit --omit=dev
```

验收：

- [ ] lint 通过。
- [ ] typecheck 通过。
- [ ] Next static export 通过并刷新 `frontend/out/`。
- [ ] 生产依赖 audit 通过或已记录 owner 接受的风险。
- [ ] React 桌面正式路径仍通过 `window.todoBridge` 读写真数据；浏览器预览兜底不得作为正式发布路径。

## 4. CI Gate

M7 起 GitHub Actions 最小 gate 为：

- [ ] `windows-latest` + Python 3.12：安装、compileall、pytest、CLI/GUI 入口 smoke 通过。
- [ ] `macos-latest` + Python 3.12：安装、compileall、pytest、CLI/GUI 入口 smoke 通过。
- [ ] 两个平台均执行 React lint/typecheck/build/audit。
- [ ] 两个平台均执行 `scripts/build.py react` 和 `scripts/smoke_release.py --react-only`。
- [ ] CI run URL 已记录到对应里程碑或发布候选验证报告。

## 5. Release 包验证

Windows：

```powershell
.\.venv\Scripts\python.exe scripts\build.py all
.\.venv\Scripts\python.exe scripts\smoke_release.py --platform windows --release-dir dist\TodoManager --zip dist\TodoManager-windows-YYYY-MM-DD.zip
.\.venv\Scripts\python.exe scripts\build.py audit-size
```

macOS：

```bash
python scripts/build.py all
python scripts/smoke_release.py --platform macos --release-dir dist/TodoManager --zip dist/TodoManager-macos-YYYY-MM-DD.zip
```

验收：

- [ ] Windows release zip 通过文件清单审计和 CLI/GUI `--help` smoke。
- [ ] macOS release zip 通过文件清单审计和 CLI/GUI `--help` smoke。
- [ ] release 包不包含 `.venv`、`.git`、`__pycache__`、`.pytest_cache`、`tests`、源码 `.py`、`node_modules`、`.next`。
- [ ] M7.5 体积审计通过，未发现 QtWebEngine debug/devtools、多余 locale 或未使用 Qt 模块回流。
- [ ] `todo-gui` 与 release zip 体积已记录，并与上一条发布基线对比。
- [ ] `desktop-react/manifest.json` 和 `desktop-react/ui/index.html` 存在。
- [ ] Windows `todo-gui.exe` 嵌入项目 `.ico`。
- [ ] macOS `TodoManager.app` 嵌入项目 `.icns`。

## 6. 人工桌面验收

- [ ] Windows 真实窗口可打开 React GUI。
- [ ] macOS 真实窗口可打开 React GUI。
- [ ] 新建、编辑、删除、撤销、搜索、子任务和主题切换可用。
- [ ] 中文显示、日期选择器、搜索下拉、子任务状态菜单无明显遮挡或溢出。
- [ ] Windows 任务栏、Alt-Tab 和文件资源管理器图标正确。
- [ ] macOS Dock、Command-Tab 和 Finder 图标正确。
- [ ] 未签名/未公证状态已在 release note 中说明，除非后续已补齐签名流程。

## 7. 发布记录

- [ ] `docs/m*_validation_report.md` 或发布候选验收报告记录本次命令、结果和已知缺口。
- [ ] `docs/milestone_plan_reorg_cross_platform_release.md` 状态与实际证据一致。
- [ ] 版本号、CHANGELOG 和 tag 策略已确认。
- [ ] GitHub Release 草稿包含 zip、校验说明、签名状态和已知限制。
