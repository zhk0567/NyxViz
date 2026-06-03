# 任务三：时序密度对数直方图统计

## 定量分析：密度两极化（03）
- 对应「宇宙网诞生记」第三节：用 **100 步完整 log 直方图** 证明分布由集中于均值附近，转向 void 与峰值两极分化（非单帧主观判断）。

## 方法
- 对 **全部 100 个时间步** 的气体密度做 **log 等距分箱**（128 bins），边界 `[7.7533, 14.5231]`（全域 min/max）。
- 分箱中心 ρᵢ = √(edgeᵢ · edgeᵢ₊₁)，直方图为归一化频数 Σcount/N。
- 同步预计算每步 mean、σ、p01/p50/p99、偏度 skew，用于时序曲线（`tools/python/precompute.py` → `timeline.json`）。

## 演化规律
- **团块化**：σ 由 0.4318 → 0.4983（+15.4%），物质由相对均匀转向聚敛。
- **两极分化**：偏度 0.7162 → 0.7183；p99−p01 由 2.098 → 2.414（+15.1%）。
- **高密度尾**：≥p99 体积占比约 1.00%，空间上对应 filament/节点。

## 与赛题描述的对照
赛题指出早期密度集中于均值附近、后期出现空洞与峰值两极分化——本工作用 **100 步完整直方图序列** 而非单帧切片证明该趋势，并给出可复现的数值曲线。

## 工具与环境
- **本任务**：`precompute.py` 生成 128-bin log 直方图与 `timeline.json`；静态曲线/叠加图由 `generate_figures.py` 输出；交互页 **D3.js** 直方图与时序图与成果页一致。
- **通用栈**：Vite + React + TypeScript；**vtk.js** 体渲染；**D3.js** 统计图表；Python（`tools/python/precompute.py`、`generate_figures.py`、`viz_style.py`）预计算与 matplotlib 配图；**Playwright**（`tools/node/capture_volumes.mjs`）1920×1080 体渲染截图；`export_report.py` / `export_docx.py` 报告导出；`npm run submission-pack` 一键交付。


## 配图
![五步直方图叠加](../figures/task3_hist_overlay.png)
![100步 mean/p99/σ](../figures/task3_metrics_timeline.png)
![σ/skew/分位跨度](../figures/task3_evolution_metrics.png)
![主峰漂移](../figures/task3_peak_drift.png)
