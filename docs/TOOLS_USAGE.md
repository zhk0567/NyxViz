# 技术方法清单

本作品实际采用的可视化方法与工具——仅列项目中**已使用**的技术，不含安装命令与交付流程。

---

## 交互与体渲染（浏览器）

| 名称 | 用途 | 位置 / 场景 |
|------|------|-------------|
| **React + TypeScript + Vite** | 交互长卷、三栏仪表盘、录屏页 UI 框架 | `src/dashboard/`、`pages/` |
| **Zustand** | 时间步、刷选区间、视图模式等全局状态 | `src/store/useAppStore.ts` |
| **vtk.js** | GPU 光线投射体渲染（128³ 均匀体素） | `src/volume/VolumeScene.tsx` |
| **传递函数 / cosmic 色标** | log 域密度→颜色/不透明度，filament 高亮 | `src/volume/transferFunction.ts`、`src/viz/colormap.ts` |
| **自适应体采样** | 按视距调节采样步长，平衡质量与帧率 | `src/volume/adaptiveVolumeSampling.ts` |
| **D3.js** | 对数直方图、时序指标曲线、brush 框选 | `src/histogram/` |
| **Canvas 2D** | 三向正交切片、XY 最大密度投影预览 | `src/spatial/TriaxialSlices.tsx`、`BandPreviewCanvas.tsx` |
| **Web Workers** | 最大密度投影、z-fast→vtk 轴重排、刷选体素扫描 | `src/workers/` |
| **vtk.js 点云** | 刷选体素三维散点展示 | `src/spatial/BrushedPoints.tsx` |

---

## 离线预计算与静态配图（Python）

| 名称 | 用途 | 位置 / 场景 |
|------|------|-------------|
| **NumPy** | 读取 128³ 体数据、100 步 log 直方图与统计量预计算 | `tools/python/precompute.py` |
| **matplotlib** | 任务 2–4 曲线/切片回退、长图条带、线框版式 | `tools/python/generate_figures.py`、`viz_style.py` |
| **PIL (Pillow)** | 多面板 PNG 拼接、色标/徽章合成、GIF 编码 | `tools/python/viz_style.py`、`encode_morph_gif.py` |
| **Python 最大密度投影** | 静态刷选三联图、空间→统计 filament 验证 | `tools/python/projection_render.py`、`spatial_to_stats.py` |
| **matplotlib 动画** | 100 步对数直方图演化 GIF/MP4（视频 B-roll） | `tools/python/generate_hist_animation.py` |

---

## 截图、对比与演示

| 名称 | 用途 | 位置 / 场景 |
|------|------|-------------|
| **Playwright** | vtk 体渲染五帧截图、长卷分段拼接、morph 变形序列 | `tools/node/capture_*.mjs`、`record_morph_video.mjs` |
| **Showcase 单文件 HTML** | 内嵌 Vite IIFE bundle，离线浏览报告与交互 | `tools/python/build_showcase_html.py` |

---

## 数据约定（贯穿上述方法）

- **体数据**：Nyx 128³ 气体密度，小端 float32，存储顺序 **z→y→x**（`flatIndex = z + 128y + 128²x`）。
- **直方图**：128 bin 对数等距分箱，边界由全域 min/max 确定，产出 `public/stats/timeline.json`。
- **体渲染缓冲**：vtk.js 要求 **x 最快** 布局，经 Worker 查表重排后送入 `vtkImageData`；投影与刷选仍在 z-fast 上运算。

---

*依据 `src/`、`tools/python/`、`tools/node/`、`pages/` 及 `docs/report/` 实际代码整理。*
