# 05 · 交互页 app 说明

[← 06 录屏手册](./06-录屏页video完全手册.md) · [← 主索引](../NyxViz_零基础完全解读.md)

---

## 入口

- **URL**：`http://127.0.0.1:5173/app.html`（`python run.py` 默认打开）  
- **HTML**：[`pages/app.html`](../../../pages/app.html)  
- **React 根**：[`src/dashboard/DashboardCore.tsx`](../../../src/dashboard/DashboardCore.tsx)

录屏页 [`video.html`](../../../pages/video.html) 是**精简专版**；app 是**完整交互长卷**。

---

## 页面结构：「宇宙网诞生记」01–06

长卷纵向滚动，对应 Word 代表图 **图1 / task6_story_poster**：

| 节 | 主题 | 内容概要 | docx |
|----|------|----------|------|
| 01 | 引言 / Hero | 标题、全局 KPI、体渲染首屏 | §0、§1 |
| 02 | 演化全景 | 五帧/演化条带、σ 叙述 | §1–2 |
| 03 | 直方图故事 | 分布漂移、void | §3 |
| 04 | 刷选验证 | Top 1% 三联、预设说明 | §4 |
| 05 | 质量占比 | 高低密度尾体积/质量 | §5.2 图17 |
| 06 | 流程 / 发现 | 七步流程图、发现卡 | 附录1 图20 |

具体 DOM 节 ID 见 `DashboardCore.tsx` 内 `scrollToSection` 与 `story-dashboard.css`。

---

## 三栏交互仪表盘

长卷中嵌入 **与 video 同源** 的三栏核心（共享 `useAppStore`）：

| 栏 | 功能 | 主要组件 |
|----|------|----------|
| 左 | log 直方图叠加、KPI、迷你趋势 | `HistogramOverlay`, `VideoKpiStrip`, `PosterTrendChart` |
| 中 | vtk.js 体渲染 | `VolumeScene` |
| 右 | 刷选直方图、预设、XY 投影 | `DensityHistogram`, `BandPreviewCanvas` |

与录屏 **intro** scene 类似，但 app 保留：

- 顶栏 **「交互探索」** 浮层按钮  
- 分段 **01–06 导航** 圆点  
- 更多文案与 poster 级排版  

---

## 交互探索浮层

- **触发**：`交互探索` 按钮 → `exploreOpen`  
- **内容**：Top 1% / Bottom 1% / 纤维 / 清除快捷钮 + 时间步 0/25/50/75/99  
- **用途**：答辩现场快速演示刷选，不必滚长卷  

代码：`DashboardCore.tsx` 内 explore 面板。

---

## app vs video 对照

| 项目 | app.html | video.html?record=1 |
|------|----------|---------------------|
| 布局 | 长卷 + 嵌入式三栏 | 每 scene 一屏 1920×1080 |
| 导航 | 01–06 + scene 无 | 11 scene URL 切换 |
| 发现卡 | 长卷内嵌 | intro/findings 专页 |
| 字号 | 正常 | 录屏放大 |
| 用途 | 日常演示、代表图 | OBS 分段录屏 |

**统计与刷选逻辑完全相同**（同一 store、同一 `timeline.json`）。

---

## 其他 HTML 入口（了解即可）

| 文件 | 用途 |
|------|------|
| `index.html` | 跳转 app |
| `capture.html` | Playwright 体渲染截图（任务一条带） |
| `capture.html` | 非答辩主路径 |

---

## 代表图怎么来的

代表图与 **[03 叙事逻辑](./03-叙事逻辑与科学结论.md)**、**录屏 11 段**对齐（3840×**5200**）：

| 幕 | 录屏 scene | 配图（文档已有拼接图） |
|----|------------|------------------------|
| 1 | task1-morph | `task1_vol_strip.png` |
| 2 | task3-hist | `task3_story_panel.png` |
| 3 | task4-validate | `task4_discovery_summary.png` |
| 4 | findings | 四发现文字卡（无重复配图） |

每幕 **一张** task 配图原样缩放，不再手工拼贴重复体渲染/刷选图。

- **命令**：`npm run capture-app-poster`  
- **脚本**：[`compose_representative_poster.py`](../../../tools/python/compose_representative_poster.py)  
- **输出**：`task6_story_poster.png` → `submission_representative.jpg`

---

[← 06 录屏手册](./06-录屏页video完全手册.md) · [下一章：07 仓库文档地图 →](./07-仓库文档地图.md)
