# GUI 闪烁排查记录：ANGLE D3D9 实验（2026-05-27）

> 分支：`codex/gui-performance-tuning`  
> 基线：`perf-gui-qtwebengine-disable-dcomp`  
> 实验目标：在保留硬件加速的前提下，将 QtWebEngine / Chromium 的 ANGLE 后端切换到 D3D9，观察是否能绕开 D3D11/默认 ANGLE 路径中的闪烁。

## 1. DirectComposition 复测结论

用户复测 `perf-gui-qtwebengine-disable-dcomp` 后反馈：

- 运行速度较快；
- 闪烁仍会出现；
- 闪烁看起来基本没有缓解。

结论：单独关闭 DirectComposition 不是有效修复方向，至少不能作为当前闪烁问题的候选方案。

## 2. 本轮改动

将 `TODO_MANAGER_QTWEBENGINE_RENDERING` 的默认模式调整为：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=angle-d3d9
```

等效追加 Chromium flags：

```text
--use-gl=angle
--use-angle=d3d9
```

仍保留以下对照模式：

```powershell
TODO_MANAGER_QTWEBENGINE_RENDERING=hardware
TODO_MANAGER_QTWEBENGINE_RENDERING=direct-composition
TODO_MANAGER_QTWEBENGINE_RENDERING=angle-d3d11
TODO_MANAGER_QTWEBENGINE_RENDERING=angle-gl
```

## 3. 预期判断

本实验只判断两个结果：

1. 闪烁是否明显降低或消失。
2. 输入、点击、窗口缩放是否仍保持可接受速度。

若 `angle-d3d9` 速度可接受但闪烁仍存在，下一步应测试 `angle-gl`。若 `angle-d3d9` 出现空白窗口、启动失败或严重卡顿，应立即切回 `hardware`，并将 D3D9 记录为不可用。

## 4. 参考依据

Qt 官方文档说明 QtWebEngine 的最终图像由 Chromium compositor 生成，并可通过 `QTWEBENGINE_CHROMIUM_FLAGS` 传入 `--use-gl=` / `--use-angle=` 来覆盖 Chromium 图形后端。该实验据此只改变 Chromium ANGLE 后端，不触碰 React UI 结构。
