# 04 · Word 正文逐章解读

[← 03 叙事逻辑](./03-叙事逻辑与科学结论.md) · [← 主索引](../NyxViz_零基础完全解读.md)

> 对照 [`NyxViz.docx`](../NyxViz.docx) 与 [`_docx_live_extract.txt`](../_docx_live_extract.txt)。  
> 图号文件在 [`docs/figures/`](../../figures/)。

---

## 0 · 系统概览

### 0 段在说什么

Word 开篇说明 **NyxViz** 面向 **128³、100 步**重子气体密度（ρ 全域约 7.75–14.52），讲述 **void—filament—node 宇宙网**如何随引力团块化而显现。系统两个入口：

- **`/app.html`**：交互长卷 + 三栏探索  
- **`/video.html?record=1`**：1920×1080 录屏布局 + 底部四发现卡  

### 六个视图 A–F（docx §0 列表）

| 代号 | 名称 | 人话 | 录屏/页面 |
|------|------|------|-----------|
| A | 体渲染 | 3D 密度「云」 | 中栏 VolumeScene |
| B | 时序 log 直方图 | 当前步密度分布 + 拖拽刷选 | 左栏/右栏 HistogramOverlay |
| C | 统计指标时序 | σ、span、尾区迷你曲线 | 左栏 PosterTrendChart |
| D | 相空间刷选 | Top1%/90–99%/Bottom1% 预设 | 右栏预设按钮 |
| E | 密度投影 | XY 最大密度 + 金色高亮 | 右栏 BandPreviewCanvas |
| F | 发现叙事区 | 四卡 + 页脚结论 | intro/findings 底栏 |

### 配图 vs 在线演示（必背对比）

| 项目 | 交互页 / 录屏 | capture 五帧条带（图2） |
|------|---------------|-------------------------|
| 入口 | app.html / video.html | capture.html + Playwright |
| TF 标量域 | **全局** p01–p99 包络 | **每帧**该步 p01–p99 |
| opacityScale | 固定（如 1.15） | 0.72→1.10 随步变化 |
| densityGain | 固定小正值 | t=0 可为负，压雾 |
| 能否跨步比亮度 | 可以（同一映射） | **不宜**定量比 ρ–亮度 |
| 答辩以谁为准 | **交互页** | 条带只讲**形态** |

### 图1 · 科学叙事代表图

- **文件**：`task6_story_poster.png`（`npm run capture-app-poster`）  
- **看到什么**：四幕海报——体渲染演化 → σ/p99−p01 统计 → 刷选空间验证 → 四发现  
- **一句话**：独立讲完科学故事，非 NyxViz 控制台截屏  

### 表1 · 术语表

→ 已扩展为 [02 名词词典](./02-专业名词词典.md)。

---

## 1 · 体数据渲染与密度演化（任务一）

### 本章要回答

用体渲染展示 **t=0/25/50/75/99** 五帧，说明宇宙网从均匀雾到清晰丝网；交代 **TF、光照、capture 参数**。

### 图2 · 五帧体渲染条带

- **文件**：`task1_vol_strip.png`（子帧 `task1_vol_t0000.png` 等）  
- **左→右**：t=0, 25, 50, 75, 99；**固定相机**  
- **看到什么**：t=0 雾状；t=99 亮脊/节点  
- **注意**：capture 专用 TF（见上表）  
- **录屏**：task1-morph 动态切换同五步；task1-tf 讲参数不讲条带  

### 图3 · t=99 代表帧 + log 色标

- **文件**：`task1_hero_poster.png` 或 `task1_vol_t0099.png`  
- **看到什么**：主视角体渲染 + 底部 ρ 色标  
- **一句话**：最终形态与色标范围  

### 图4 · 渲染参数汇总 (a)(b)(c)

- **文件**：`task1_render_params.png`  
- **(a) 传递函数**：log 域 RGB/α 控制点  
- **(b) Phong 光照**：主光/补光方向示意  
- **(c) capture TF 增益**：仅条带用的时间步曲线  
- **录屏**：task1-tf 左栏对应 (a)(b) 文字；右栏 `task1_lighting_diagram.png`  

### 表2 · 五代表步统计

| t | σ | 答辩点 |
|---|-----|--------|
| 0 | 0.4318 | 起点均匀 |
| 99 | 0.4983 | +15.4% |

完整表见 docx；数字与 `timeline.json` 一致。

### 图5 · 分辨率粗化 Jaccard

- **文件**：`task1_coarsen_jaccard.png`（名可能略异）  
- **左**：投影相关 r  
- **右**：64³ 粗化后脊线 Jaccard——菱形 **0.65** 原点对齐；圆点 **0.544±0.076** 八种偏移  
- **人话**：分辨率降低后结构仍部分保留，但不应等同 AMR  

### 附录 5.1 要点

- 交互页 vs capture 对照表（表10）  
- `render_spec.json` 完整参数  

---

## 2 · 宇宙密度演化规律归纳（任务二）

### 本章要回答

百步统计归纳 **团块化、右尾、少数体素承载结构**；阐释可视化 **三项案例**价值。

### 图6 · 100 步统计四联

- **文件**：`task2_evolution_story.png` 或 panel 分图  
- **四联**：分位跨度、σ、≥p99 体积%、偏度  
- **录屏**：task2-evolution **右栏四图**一一对应  

### 图7 · 五步 log 直方图叠加

- **文件**：`task3_hist_overlay.png`  
- **看到什么**：t=0,25,50,75,99 五步分布叠在一起，右尾抬高  
- **录屏**：task2-evolution / task3-hist 左栏叠加直方图  

### 图8 · 空间统计汇总

- **文件**：`task2_spatial_summary.png` 等  
- **(a–d)**：Moran's I、ξ(r=1)、分形维 D、峰度时序  
- **(e)**：ξ(r) 剖面 + 子块 MC ±1σ  
- **(f)**：bootstrap 置信带  
- **答辩**：增量 **未达 2σ**，辅证不主证  
- **录屏**：**task2-spatial** 专页  

### 图9 · 可视化驱动发现

- **文件**：`task4_spatial_to_stats.png` 或四联合成  
- **(a–c)** Top 1% 三联：直方图 / 体渲染 / 投影  
- **(d)** P88 空间→统计反查  
- **录屏**：**task2-cases** 左栏 A/B/C 案例卡（点击可整卡放大）  

### 表3 · t=0 vs t=99 核心指标

σ、span、Moran's I、ξ(r=1)、≥p99 体积——与 [03 章](./03-叙事逻辑与科学结论.md) 五组数字一致。

### §2.2 案例 A/B/C

→ 详见 [03 章](./03-叙事逻辑与科学结论.md#三个可视化价值案例任务二-22)。

---

## 3 · 时序密度对数直方图统计（任务三）

### 本章要回答

128 bin log 直方图量化 **两极分化、void 扩张**；与任务一体渲染对照。

### 图10 · 直方图故事板

- **文件**：`task3_histogram_summary.png` 或 story panel  
- **看到什么**：五步叠加 + σ/span 趋势 + t=99 KPI  
- **录屏**：task3-hist 左栏直方图 + 中栏体渲染  

### 图11 · 时序指标汇总

- **文件**：`task3_evolution_metrics.png`, `task3_peak_drift.png`  
- **看到什么**：σ/span 三联、p50 轨迹、void 扩张曲线  
- **录屏**：task3-hist 右栏两图 + 左栏分箱读数  

### 表4 · 直方图演化要点

| 量 | t=0→99 | 含义 |
|----|--------|------|
| p50 | 9.4504→9.2745 | 主峰下移 |
| void (ρ≤ρ_p10(t=0)) | 10→24.69% | 空洞扩大 |
| p999 比 | ×1.009 | 右尾微抬 |

### 附录 5.3 · 分箱敏感度

- 图21：64/128/256 bins 对比  
- 图22：CDF L∞ 距；默认 **128 bins**  
- void 阈值：**固定 t=0 分位**，非物理 δ-b 过密度  

---

## 4 · 相空间交互刷选（任务四）

### 本章要回答

三栏 **直方图—体渲染—投影**联动；Top 1%、纤维带、Bottom 1%、P88 反查；性能与 KPI 局限。

### 图12 · Top 1% 三联

- **(a)** log 直方图刷选区  
- **(b)** 体渲染高亮  
- **(c)** XY 投影金斑  
- **录屏**：**task4-brush** 演示 Top 1%（需点击）  

### 图13 · Top/Bottom 双行对比

- 无本地环境时的静态替代  
- 见 docx §5.8  

### 图14 · 空间→统计 P88

- 亮脊反查 ρ 带  
- **录屏**：task2-cases 案例 C  

### 图15–16 · 验证与扩展

- 阈值对比、自定义 KPI 误差、早停召回、P88 敏感度、精确率/召回  
- **录屏**：**task4-validate** 左三图 + 右 KPI 格  

### 表5 · 刷选验证摘要

| 操作 | 空间表现 | 密度区间 (t=99) |
|------|----------|-----------------|
| Top 1% | 丝/节点 | ρ≥10.76 |
| Bottom 1% | 稀疏 void | ρ≤8.35 |
| P88 亮脊 | filament | ρ∈[11.23,12.16] |

### 附录 5.4 要点

- 表14：早停 **45.4 ms** vs 全网格 **351.8 ms**（录屏口语 **37/282 ms** 为 UI 侧近似，以 JSON 为准）  
- 表16：召回 **100%**、精确率 **27.6%**  
- 表17：宽区间刷选 KPI **采样低估**（高亮仍全场）  

---

## 5 · 综合叙事与科学发现

### 5.1 共性机制

四条：团块化、两极化、少数致密承载、统计—空间双向验证。→ [03 章](./03-叙事逻辑与科学结论.md)。

### 5.2 关键发现与质量占比

- **图17**：`task5_mass_pie.png` 高低密度尾体积/质量环形对比  
- **四发现卡**：录屏 **findings** 专页  

### 5.3 可视分析启示

log 域、百步序列、刷选联动三原则；Web 轻量交付。

### 5.4 AMR 范围说明

赛题为均匀 128³；未做 AMR 可视化——**数据格式边界**，非能力缺失。

### 5.5 Lyα 森林关联

- **图18**：+z 视线 PDF 代理 t=0 vs t=99  
- **图19**：+x/+y/+z 方向敏感性  
- **表6–7**：方法设定与 σ 极差 **12.43%**  
- **不能说**：真实观测拟合、各向同性森林  

### 5.6 暗物质未纳入

数据无 DM；证据链限定重子气体。

### 5.7 本地复现

`python run.py`、`reproduce.ps1`、`npm run deliver` → [09 章](./09-本地复现与答辩清单.md)。

### 5.8 交互体验与答辩附件

- 静态替代：图9、图12  
- 录屏：`video.html?record=1` → [06 章](./06-录屏页video完全手册.md)  

---

## 附录 1 · 分析流程

### 图20 · 七步流程

- **文件**：`task0_story_flow.png`  
- **步骤**：Nyx 数据 → 预计算 → 体渲染 → 统计 → 刷选 → 验证 → 结论  

---

## 附录 2 · 可视设计

### 2.1 体渲染

- vtk.js 光线投射；`render_spec.json` 可复现  
- Orientation gizmo：XYZ 轴  

### 2.2 log 直方图

- D3 SVG；128 bin；brush 同步 store  

### 2.3 刷选与投影

- Worker 扫描；Canvas 2D MDP；金色 overlay  

### 2.4 录屏页布局

- 1920×1080 三栏 + 发现区；`?record=1` 弱化导航  

---

## 附录 3 · 数据预计算

### 表8 · timeline.json 字段

→ [08 章字段表](./08-数据与代码管线.md#timelinejson-主要字段)

### 3.2 拼接图清单

`generate_figures.py` 产出 task1_vol_strip、task2_evolution_story、task4_brush_triptych、task6_story_poster 等。

### 3.3 bootstrap 复现

`validation_suite.py`；n=40 子窗口；seed=42。

### 3.4 轴向 z-fast / x-fast

→ [02 词典](./02-专业名词词典.md#z-fast--x-fast存储顺序)；`verify_loader.py` 校验。

---

## 附录 4 · 工具与环境

React + vtk.js + D3 + Python + Playwright；详见 [TOOLS_USAGE.md](../../TOOLS_USAGE.md) 与 [08 章](./08-数据与代码管线.md)。

---

## 附录 5 · 补充材料

- **5.1** 任务一 TF 表10、粗化表11  
- **5.2** 空间统计表12–13、案例表  
- **5.3** 图21–22 分箱  
- **5.4** 表14–17 刷选性能与 KPI  

---

## 图号 ↔ 文件名 ↔ 录屏 速查

| 图号 | 主要文件 | 录屏 scene |
|------|----------|------------|
| 1 | task6_story_poster | —（PIL 四幕合成，非录屏） |
| 2 | task1_vol_strip | task1-morph |
| 4 | task1_render_params | task1-tf |
| 6–7 | task2_evolution*, task3_hist_overlay | task2-evolution |
| 8 | task2_spatial* | task2-spatial |
| 9 | task4_spatial_to_stats | task2-cases |
| 10–11 | task3_histogram*, task3_peak_drift | task3-hist |
| 12–16 | task4_brush* | task4-brush / validate |
| 17 | task5_mass_pie | findings（质量卡） |
| 20 | task0_story_flow | app 长卷 06 节 |

---

[← 03 叙事逻辑](./03-叙事逻辑与科学结论.md) · [下一章：05 交互页 app →](./05-交互页app说明.md)
