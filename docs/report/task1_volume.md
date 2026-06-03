# 任务一：体数据渲染与密度演化

## 宇宙网诞生（01–02）
- 本任务展示 Nyx **128³ 重子气体密度**在 100 步引力演化中，由微涨落向 **void—filament—node** 宇宙网分化的可见过程（仅气体密度，非暗物质）。
- 叙事对应「宇宙网诞生记」：**01 引言**给出全局形态直觉，**02 演化全景**用五帧体渲染对比结构生长。

## 方法
- **数据**：Nyx 官方 128³ 气体密度，100 时间步（t=0…99），小端 float32，存储顺序 z→y→x（`index = z + 128y + 128²x`）。
- **渲染**：基于 vtk.js 的 GPU 光线投射体渲染；传递函数采用宇宙学预设 `cosmic`（log 域、全局 p01–p99）；展板质量采样 + Phong 着色；五帧由 Playwright 截取。
- **展示**：选取 t=0/25/50/75/99 五帧，统一色标与相机，便于对比演化。

## 观察（三阶段）
- **t=0–29 线性期**：整体呈均匀雾状，filament 对比度弱。
- **t=30–69 非线性期**：丝状结构逐渐连通，void 区域扩大。
- **t=70–99 宇宙网期**：高密度脊线与节点形成亮带，与统计右尾增厚一致。

## 数据佐证
- t=0: mean=9.4854, σ=0.4318, p99=10.7255, max=13.8433
- t=25: mean=9.4369, σ=0.4525, p99=10.7402, max=14.0505
- t=50: mean=9.3954, σ=0.4693, p99=10.7507, max=14.3269
- t=75: mean=9.3556, σ=0.4847, p99=10.7547, max=14.3541
- t=99: mean=9.3187, σ=0.4983, p99=10.7601, max=14.4494

## 工具与环境
- **本任务**：vtk.js 体渲染 + cosmic 传递函数；静态条带与单帧图由 `generate_figures.py` 排版，体渲染帧由 Playwright 生成。
- **通用栈**：Vite + React + TypeScript；**vtk.js** 体渲染；**D3.js** 统计图表；Python（`tools/python/precompute.py`、`generate_figures.py`、`viz_style.py`）预计算与 matplotlib 配图；**Playwright**（`tools/node/capture_volumes.mjs`）1920×1080 体渲染截图；`export_report.py` / `export_docx.py` 报告导出；`npm run submission-pack` 一键交付。


## 配图（≤5）
![五时刻体渲染条带](../figures/task1_vol_strip.png)
![t=0](../figures/task1_vol_t0000.png)
![t=50](../figures/task1_vol_t0050.png)
![t=99](../figures/task1_vol_t0099.png)
