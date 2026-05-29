# 任务四：相空间交互刷选可视分析

## 系统功能
- **统计视图**：log 密度直方图，支持拖拽框选密度区间；快捷 **Top 1%**（ρ≥p99=10.7601）与 **Bottom 1%**（ρ≤p01=8.3458）。
- **空间视图**：vtk.js 体渲染对刷选区间体素做传递函数高亮；Canvas 2D **最大密度投影** 以金色标出刷选体素；可选 3D 点云（≤12000 点，Web Worker 后台扫描）。
- **性能**：刷选扫描在 Worker 线程；VTK 按需加载；相邻时间步 idle 预取。

## 验证：统计 → 空间
- **Top 1%**：直方图右尾刷选后，XY 投影显示丝状/节点状聚集（非随机散点），与 t=99 体渲染中的亮脊一致 → **高密度尾对应宇宙网致密结构**。
- **Bottom 1%**：刷选低密度左尾，投影显示广袤稀疏区域，对应 IGM 主体。

## 验证：空间 → 统计
- 在 t=99 **XY 最大密度投影**上识别 **filament 亮脊**（投影值 ≥ P88 的像素，金色叠加）。
- 汇总这些亮脊像素的密度，得到对应区间 **ρ∈[11.23, 12.16]**（位于 p75–p99 右尾，与 Top 1% 刷选区间一致）。
- 在 log 直方图上以金色标注该密度带 → **空间结构可反查统计位置**，与 `/app.html` 中「先在投影/体渲染定位 filament，再在直方图标密度带」的交互路径一致。

## 双向关联
- **统计→空间**：框选 [ρ_min, ρ_max] 定位满足条件的体素集合（见 Top/Bottom 1% 三联图）。
- **空间→统计**：在投影中识别 filament 亮脊后，反推密度带 ρ∈[11.23, 12.16] 并在直方图高亮（见 `task4_spatial_to_stats.png`，由 `spatial_to_stats.py` 与 `generate_figures.py` 可复现）。

## 工具与环境
- **本任务**：**D3.js** 直方图框选 + **vtk.js** 刷选高亮 + Canvas 2D 最大密度投影（与体渲染同色标）；刷选体素扫描在 **Web Worker**；静态三联图与空间→统计配图由 `generate_figures.py` / `projection_render.py` / `spatial_to_stats.py` 生成。
- **通用栈**：Vite + React + TypeScript；**vtk.js** 体渲染；**D3.js** 统计图表；Python（`tools/python/precompute.py`、`generate_figures.py`、`viz_style.py`）预计算与 matplotlib 配图；**Playwright**（`tools/node/capture_volumes.mjs`）1920×1080 体渲染截图；`export_report.py` / `export_docx.py` 报告导出；`npm run submission-pack` 一键交付。


## 配图
![空间→统计 filament 密度带](../figures/task4_spatial_to_stats.png)
![Top1% 三联图](../figures/task4_brush_triptych.png)
![Top1% 直方图刷选](../figures/task4_hist_brush_top1.png)
![Top1% 空间投影](../figures/task4_brush_top1.png)
![Bottom1% 投影](../figures/task4_brush_bottom1.png)
