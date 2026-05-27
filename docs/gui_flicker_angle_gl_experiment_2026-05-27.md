# GUI 闪烁排查记录：ANGLE OpenGL 实验（2026-05-27）

> 分支：`codex/gui-performance-tuning`  
> 基线：`perf-gui-qtwebengine-vulkan-angle`  
> 实验目标：保留 Chromium ANGLE 路径，但将显示后端切到 OpenGL，观察是否能绕开默认 D3D 路径中的合成层闪烁。

## 1. 前置结论

目前已排除或降级的 QtWebEngine 后端实验：

- `direct-composition`：速度快，但闪烁基本没有缓解。
- `angle-d3d9`：空白窗口，持续 GPU context lost，不可用。
- `vulkan-angle`：空白窗口，持续 `Context lost`，不可用。
- `software` / 禁用 GPU compositing：可消除闪烁，但交互速度不可接受。

因此，本轮只剩 `angle-gl` 作为最后一个较小粒度的图形后端对照项。

## 2. 本轮改动

将 `TODO_MANAGER_QTWEBENGINE_RENDERING` 的默认模式调整为：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=angle-gl
```

等效追加 Chromium flags：

```text
--use-gl=angle
--use-angle=gl
```

该实验不改 React UI 结构、不改 CSS 视觉层，只改变 Chromium / ANGLE 图形后端选择。

## 3. 判定标准

1. 若出现空白窗口或持续 `Context lost`，立即关闭，判定 `angle-gl` 不可用。
2. 若能正常显示但闪烁无改善，停止继续 QtWebEngine flags 排查。
3. 若闪烁明显减少且速度可接受，再考虑将其作为候选修复进入打包版测试。

若本轮失败，后续方向应切换到：

- 桌面壳视觉降级实验：去除桌面壳点阵/渐变背景、降低阴影、使 overlay 更不透明。
- 或重新评估桌面壳路线：Windows WebView2、Tauri/Electron、QtWebEngine 版本升级。
