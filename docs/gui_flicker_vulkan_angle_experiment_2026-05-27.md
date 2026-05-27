# GUI 闪烁排查记录：Vulkan + ANGLE 实验（2026-05-27）

> 分支：`codex/gui-performance-tuning`  
> 基线：`perf-gui-qtwebengine-angle-d3d9`  
> 实验目标：绕开默认 ANGLE/D3D 路径，让 Chromium compositor 使用 Vulkan 渲染，同时保留 ANGLE 给 WebGL 兼容路径。

## 1. 前置结论

`angle-d3d9` 已被人工复测判定为不可用：

- 窗口空白；
- 控制台持续输出 GPU context lost；
- `eglCreateContext` 报 requested version not supported；
- `CreateSharedImage failed`。

因此后续不再以 D3D9 作为候选修复方向。

## 2. 本轮改动

将 `TODO_MANAGER_QTWEBENGINE_RENDERING` 的默认模式调整为：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=vulkan-angle
```

等效追加 Chromium flags：

```text
--use-gl=angle
--enable-features=Vulkan
--use-vulkan=native
```

同时保留一个备用模式：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=vulkan-stub
```

该模式等效：

```text
--use-gl=stub
--enable-features=Vulkan
--use-vulkan=native
```

`vulkan-stub` 会完全绕开 ANGLE，风险更高，只有在 `vulkan-angle` 速度可接受但仍闪烁时才建议测试。

## 3. 判定标准

本轮复测优先判断：

1. 是否能正常显示窗口，不能正常显示则立即关闭。
2. 搜索框、父任务/子任务文本输入是否仍闪烁。
3. 三角形棋盘格缺失是否消失或明显减少。
4. 窗口缩放、输入、按钮点击是否保持可接受速度。

若 `vulkan-angle` 无法显示或持续输出 GPU context lost，应切回 `hardware`，并将 Vulkan 路径标记为当前环境不可用。

## 4. 参考依据

Qt 官方文档说明 QtWebEngine 可通过 `QTWEBENGINE_CHROMIUM_FLAGS` 传入 `--use-gl=` 和 `--use-angle=` 等 Chromium flags；当 ANGLE 在特定配置下崩溃时，可尝试 Vulkan 后端配置，包括 `--use-gl=angle --enable-features=Vulkan --use-vulkan=native` 或更激进的 `--use-gl=stub --enable-features=Vulkan --use-vulkan=native`。
