# GUI 闪烁与性能排查记录（2026-05-26）

> 状态：阶段性暂停，等待下一轮继续排查。  
> 分支：`codex/gui-performance-tuning`  
> 当前回退目标：保留响应速度较稳定的前端低风险优化，撤回导致明显卡顿的 QtWebEngine 渲染后端实验。

## 1. 背景

M7.5 版本完成桌面 GUI 轻量化后，用户在另一台仅有核心显卡的 Windows 笔记本上发现 `todo-gui.exe` 鼠标移动时存在卡顿/闪烁。高性能台式机最初不易复现性能问题，但后续在高性能机器上也能观察到 QtWebEngine 窗口闪烁。

本轮目标原本是按低 UI 影响顺序验证前端性能优化。实际排查中，闪烁现象逐步表现为 QtWebEngine / Chromium 渲染层问题，因此后半段转为渲染后端实验。

## 2. M7.5 交付品审计

M7.5 基线已经上传到 GitHub：

- commit：`a4685a5 chore: complete M7.5 GUI lightweight release baseline`
- tag：`m7.5-gui-lightweight-2026-05-25`
- 分支：`main`

M7.5 交付品存在并已纳入仓库：

- `docs/m7_5_validation_report.md`
- `scripts/audit_release_size.py`
- `build_gui.spec`
- `scripts/build.py`
- `scripts/smoke_release.py`
- `tests/test_release_packaging.py`
- `docs/milestone_plan_reorg_cross_platform_release.md`
- `docs/release_checklist.md`
- `docs/release_process.md`
- `docs/test_plan_reorg_cross_platform_release.md`

M7.5 结论仍成立：Windows 本地可完成项已完成；发布包体积下降；体积审计、release smoke、PyInstaller 裁剪策略检查已落地。macOS `.app` 体积复核与实机窗口 smoke 仍待 macOS 环境补证。

## 3. 后续性能分支交付品审计

当前性能分支为 `codex/gui-performance-tuning`。相对 M7.5 基线，保留的有效前端改动包括：

- `39e1dcd` / `perf-gui-step-01-todayrail-memo`：缓存 `TodayRail` 派生数据，减少重复遍历。
- `60933d3` / `perf-gui-step-02-calendar-memo`：缓存月历派生数据和 grid style。
- `c0be9af` / `perf-gui-step-03-hot-leaf-memo`：为日历格、任务卡、状态徽标等热区叶子组件添加 `memo`，并稳定日历选择回调。
- `9efc3c1` / `perf-gui-step-05-hot-zone-transitions`：将桌面壳 transition 限制收窄到热区控件，避免全局影响 UI。
- `7b0941d` / `perf-gui-modal-input-flicker-fix`：新增父任务/子任务弹窗的文本输入改为非受控输入，减少输入时 React 弹窗重绘。
- `aa7a748` / `perf-gui-desktop-repaint-stability`：桌面壳浅色模式使用近似不透明 surface 色，并限制标准控件 transition，减少透明层混合重绘。

已撤回的 QtWebEngine 渲染后端实验：

- `c849768` / `perf-gui-qtwebengine-software-rendering`：默认全软件渲染。结论：基本消除闪烁，但窗口缩放、点击、文本输入延迟约 1-2 秒，不可接受。
- `951eeed` / `perf-gui-qtwebengine-hybrid-rendering`：关闭 GPU rasterization / zero-copy。结论：速度稍慢，闪烁与棋盘格问题无明显改善。
- `a2b95f6` / `perf-gui-qtwebengine-compositor-rendering`：关闭 GPU compositing / zero-copy。结论：不再闪烁，但速度体感接近全软件渲染，不可接受。

上述三个实验已通过非破坏性 `git revert` 回滚，保留历史用于明天继续分析。

## 4. 已执行验证

本轮改动过程中反复执行：

```powershell
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m compileall gui tests
.\.venv\Scripts\python.exe -m pytest tests\test_react_shell_bridge.py -q
```

已知 warning：`.pytest_cache` 写入权限 warning，属于既有环境问题，不影响本轮判断。

## 5. 闪烁现象记录

用户在高性能电脑上复现到以下模式，搜索框输入最容易观察：

1. 输入或删除字符时，搜索框、月历工作台、任务详情等多个组件整块消失，约 0.5-1 秒后重新浮现；“今日节奏”有时不消失。继续输入会打断消失/重现过程，使持续时间缩短。
2. 输入或删除时，窗口所有组件整块消失后立刻浮现，持续约 0.5-1 秒。该模式与第一种交替出现。
3. 多个组件出现三角形缺失区域，缺失区域显示棋盘格且呈渐变透明，约 0.5-1 秒后恢复。
4. 出现闪烁后，第一次移动鼠标也会触发闪烁；再次移动通常不再触发。
5. 闪烁概率随文本输入字数增加而升高；删除文本后再次输入仍可能触发。

## 6. 当前判断

闪烁不应再按普通 React 重渲染或 CSS transition 卡顿处理。主要依据：

- 棋盘格三角形缺失更符合 Chromium/QtWebEngine GPU tile、合成层或透明层 raster 异常。
- 全软件渲染可以消除闪烁，说明 GPU 渲染路径参与了问题。
- 只关闭 GPU rasterization / zero-copy 没有明显改善，说明 raster/zero-copy 不是唯一根因。
- 关闭 GPU compositing 可以消除闪烁，但速度不可接受，说明 GPU compositing 高度相关。
- 纯前端输入改为非受控、热区 transition 收敛、surface 不透明化均不能根治，说明组件层优化只能减轻重绘压力，无法规避底层合成问题。

当前最可能的根因：Windows + QtWebEngine + 当前显卡/驱动/Chromium GPU compositing 路径在透明层、渐变背景、阴影或快速输入触发的重绘中出现合成层瓦片丢失。

## 7. 当前分支状态

当前 `codex/gui-performance-tuning` 已回到响应速度较稳定的状态：

- 不再默认设置 QtWebEngine software / hybrid / compositor flags。
- 保留前端低风险优化、热区 transition 收敛、弹窗输入非受控和桌面 surface 不透明化。
- 渲染后端实验提交和 tag 仍保留，方便后续按 tag 或 commit 复盘。

建议明天继续前先确认：

```powershell
git status --short --branch
git log --oneline -12
```

## 8. 下一轮建议

下一轮不建议继续做 React 层性能优化，优先做更小粒度的 QtWebEngine / Windows GPU 路径实验：

1. 测试 Windows DirectComposition 相关 flags，而不是禁用整个 GPU compositing：
   - `--disable-direct-composition`
   - `--disable-direct-composition-video-overlays`
2. 测试 ANGLE / OpenGL 后端差异：
   - `QT_OPENGL=angle`
   - 视情况尝试 Chromium `--use-angle=d3d11`、`--use-angle=d3d9`、`--use-angle=gl`
3. 若仍无法稳定，再做桌面壳视觉降级实验：
   - 仅桌面壳下移除 `.app-bg` 点阵和渐变背景。
   - 减少 `shadow-panel` / `shadow-floating`。
   - 将 modal overlay 从半透明改为不透明近似色。
4. 若 QtWebEngine 仍无法接受，应重新评估桌面壳路线：
   - Windows 优先 WebView2。
   - 跨平台路线再比较 Tauri / Electron / QtWebEngine 升级。

下一轮每个实验仍应保持一个 commit 和一个 tag，避免混合多个变量。
