# GUI 闪烁排查记录：DirectComposition 实验（2026-05-27）

> 分支：`codex/gui-performance-tuning`  
> 基线：`perf-gui-rollback-flicker-handoff-2026-05-26`  
> 实验目标：验证只绕开 Windows DirectComposition 路径，是否能降低 QtWebEngine 棋盘格/整块消失闪烁，同时避免 software/compositor 方案的严重卡顿。

## 1. 背景判断

上一轮结果显示：

- React 层的输入改造、热区 `transition` 收敛、surface 不透明化均无法根治闪烁。
- `software` 渲染与禁用 GPU compositing 可以消除闪烁，但窗口缩放、文本输入、点击响应慢到不可接受。
- 仅禁用 GPU rasterization / zero-copy 没有明显改善。
- 用户观察到的三角形棋盘格缺失，更符合 Chromium/QtWebEngine 合成层或 DirectComposition 路径中的瓦片显示异常。

因此，本轮不继续扩大 React 层优化，而是优先测试更窄的 Windows GPU 后端变量。

## 2. 本轮改动

在 `gui/react_shell.py` 中新增 `TODO_MANAGER_QTWEBENGINE_RENDERING` 模式开关，并在导入 QtWebEngine 前合并 Chromium flags。

默认模式：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=direct-composition
```

等效追加：

```text
--disable-direct-composition
--disable-direct-composition-video-overlays
```

对照模式：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=hardware
```

该模式不追加 Chromium flags，用于对比原始 QtWebEngine 硬件路径。

## 3. 验证重点

人工验证时只需要判断以下四点：

1. 搜索框连续输入/删除较长文本时，是否仍出现整块组件消失。
2. 新建父任务、新建子任务的标题和备注输入时，是否仍出现闪烁。
3. 是否仍出现三角形棋盘格缺失。
4. 窗口缩放、文本输入、按钮点击响应是否比回滚基线明显变慢。

判定标准：

- 若闪烁消失且交互速度接近回滚基线，本实验可作为候选修复。
- 若闪烁消失但速度接近 software/compositor 方案，则不可接受。
- 若速度可接受但闪烁仍存在，则继续测试 ANGLE/OpenGL 后端差异。

## 4. 当前状态

本文件记录的是待人工复测的实验版本。复测完成后，应追加实际结果，并决定是否继续推进 ANGLE / OpenGL 或桌面壳视觉降级实验。
