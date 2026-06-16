# 06 · 录屏页 video 完全手册

[← 04 Word 解读](./04-Word正文逐章解读.md) · [← 主索引](../NyxViz_零基础完全解读.md)

> **三联对照**：旁白 [`VIDEO_NARRATION_TTS.txt`](../../competition/VIDEO_NARRATION_TTS.txt) · 操作 [`VIDEO_RECORDING_OPS.md`](../../competition/VIDEO_RECORDING_OPS.md) · 场景 [`sceneRegistry.ts`](../../../src/video/sceneRegistry.ts)

**基址**：`http://127.0.0.1:5173/video.html?record=1&scene=<id>`

---

## 录屏模式 vs 预览模式

| 项目 | `?record=1` 录屏 | 无 record 预览 |
|------|------------------|----------------|
| 字号 | 放大可读 | 正常 |
| 底部导航链 | 隐藏 | 显示 |
| 操作提示（滚轮缩放等） | 隐藏 | 部分隐藏 |
| 图片点击放大 | 禁用（findings 卡除外） | 案例卡可整卡放大 |
| html 类 | `video-record-mode` | 仅 `video-dashboard` |

实现：`VideoDashboard.tsx` 给 `<html>` 加 class；CSS 在 `video-dashboard.css`、`image-lightbox.css`。

---

## 11 段总览

| 段 | scene | 旁白行 | 需点击 | 默认 t | 刷选 |
|----|-------|--------|--------|--------|------|
| 1 | intro | 1 | 否 | 99 | 无 |
| 2 | task1-tf | 2 | 否 | 99 | 无 |
| 3 | task1-morph | 3 | **切步** | 99 | 无 |
| 4 | task2-evolution | 4 | 否 | 99 | 无 |
| 5 | task2-void | 5 | 否 | 99 | 无 |
| 6 | task2-cases | 6 | 否 | 99 | **Top 1%** |
| 7 | task2-spatial | 7 | 否 | 99 | 无 |
| 8 | task3-hist | 8 | 否 | 99 | 无 |
| 9 | task4-brush | 9 | **刷选** | 99 | 演示 |
| 10 | task4-validate | 10 | 否 | 99 | Top 1% |
| 11 | findings | 11 | **放大卡** | 99 | 无 |

---

## 1 · intro

**URL**：`?record=1&scene=intro`（或仅 `?record=1`）

**旁白全文**  
> NyxViz 是一套面向 Nyx 一百二十八立方格、一百步重子气体密度场的 Web 可视化分析系统……默认第 99 步。

**布局**：`showLeft + showCenter + showRight + showFindings`（三栏 + 底栏四发现卡）

| 区域 | 内容 | 组件/文件 |
|------|------|-----------|
| 顶栏 | 标题、t=99 步进条、σ/p99/μ | `VideoDashboardHeader.tsx` |
| 左栏 | 五步直方图叠加 + 三迷你趋势（σ、≥p99、span） | `VideoLeftColumn` → `HistogramOverlay`, `PosterTrendChart` |
| 中栏 | 体渲染 + 色标 + 场景标题条 | `VideoCenterColumn` → `VolumeScene` |
| 右栏 | 刷选直方图 + 预设 + 投影预览 | `VideoRightColumn` |
| 底栏 | 发现卡 01–04 条带 | `VideoFindingsStrip` |

**操作**：指屏扫三栏；指 t=99。**无需点击。**

**docx**：§0 系统概览 A–F。

### 代表图（与录屏解耦）

提交代表图 `task6_story_poster.png` 为 **PIL 四幕科学叙事海报**（3840×5200），由 `compose_representative_poster.py` 合成，**不依赖** intro 录屏截屏。

`posterCapture` 模式仍可用于 demo / 可选资产：

```
http://127.0.0.1:5173/video.html?record=1&scene=intro&posterCapture=1&t=99
```

| 参数 | 作用 |
|------|------|
| `record=1` | 录屏布局（大字号、隐藏导航） |
| `scene=intro` | 三栏 + 底栏四发现卡 |
| `posterCapture=1` | 隐藏场景 chrome / 预览条；就绪后设 `window.__VIDEO_POSTER_READY__` |

- **代表图合成**：`npm run capture-app-poster` → 四幕叙事 PNG → `submission_representative.jpg`  
- **可选录屏截屏**：`CAPTURE_VIDEO_INTRO=1 npm run capture-app-poster` → `_rep_video_intro.png`  
- **实现**：[`compose_representative_poster.py`](../../../tools/python/compose_representative_poster.py)、[`useVideoPosterCapture.ts`](../../../src/dashboard/useVideoPosterCapture.ts)

---

**URL**：`?record=1&scene=task1-tf`

**旁白全文**  
> 传递函数与光照。宇宙学色标……冯氏光照系数 0.10、0.75、0.52……右栏为 Phong 主辅光示意图。

**布局**：`focus-left`；**无中栏体渲染**；左 TF 面板 + 右光照图

| 区域 | 内容 | 文件 |
|------|------|------|
| 左栏 | cosmic TF、p01–p99 域、7 级 α、Ka/Kd/Ks、光源说明 | `VideoRenderSpecPanel.tsx` |
| 右栏 | Phong 主辅光示意图 | `VideoRightColumn` → `task1_lighting_diagram.png` |

**操作**：指色标、α 阶梯、光照系数、右栏示意图。**无需点击。**

**docx**：§1 图4(a)(b)；附录 2.1。

---

## 3 · task1-morph

**URL**：`?record=1&scene=task1-morph`

**旁白全文**  
> 形态演化。此处依次切换至第 0、25、50、75、99 步……第 99 步 sigma 0.4983，p99 10.7601。

**布局**：`focus-center`；中栏体渲染 + 右栏形态面板

| 区域 | 内容 | 文件 |
|------|------|------|
| 中栏 | 体渲染 | `VolumeScene.tsx` |
| 右栏 | 五缩略图 + σ 读数；点击缩略图**仅切步**（录屏禁用放大） | `VideoMorphPanel`, `EvolutionThumbnails.tsx` |

**操作（本段唯一切步）**  
顶栏或右栏缩略图：**0 → 25 → 50 → 75 → 99**，每步停 **2 秒**。

**数字**：t=99 σ=0.4983，p99=10.7601。

**docx**：§1 图2 五帧（动态版）。

---

## 4 · task2-evolution

**URL**：`?record=1&scene=task2-evolution`

**旁白全文**  
> 演化量化。左栏叠加直方图与三卡 KPI……右栏四图……偏度由 0.716 缓升至 0.718。

**布局**：`focus-left`；左 histogram + KPI + 右四联曲线

| 区域 | 内容 | 文件 |
|------|------|------|
| 左栏 | 叠加直方图、演化 KPI 三卡（σ、span、p99.9）、迷你趋势 | `VideoLeftColumn`, `VideoEvolutionPanel` |
| 右栏 | 四张百步曲线图 | `VideoFigureStrip` / `sceneRegistry` content.figures |

**操作**：指 KPI 与右栏四图。**无需点击。**

**数字**：σ +15.4%；span +15.1%；p99.9 ×1.009；≥p99 体积 ~1%；skew 0.716→0.718。

**docx**：§2 图6–7；表3。

---

## 5 · task2-void

**URL**：`?record=1&scene=task2-void`

**旁白全文**  
> void 双阈值。p10 体积占比由 10% 增至 24.69%，p01 由 1% 增至 6.18%……

**布局**：`dedicated` 专页（无三栏）

| 区域 | 内容 | 文件 |
|------|------|------|
| 全页 | p10/p01 双卡 + void 占比演化图 | `VideoVoidScene.tsx` |

**操作**：指 p10 卡与 p01 卡。**无需点击。**

**docx**：§3 void 扩张；表4 void 行。

---

## 6 · task2-cases

**URL**：`?record=1&scene=task2-cases`

**旁白全文**  
> 案例 A、B、C……B 为 Top 1%……C 沿 P88 亮脊反查，密度 11.23 到 12.16。

**布局**：`focus-left`；左三案例卡 + **中栏体渲染**（预置 Top 1%）

| 区域 | 内容 | 文件 |
|------|------|------|
| 左栏 | 案例 A/B/C（预览模式点击**整卡** lightbox；录屏指屏） | `VideoCaseCards.tsx` |
| 中栏 | Top 1% 高亮体渲染 | `VolumeScene` + `brushPreset: top` |

**操作**：指 A→B→中栏高亮→C。**无需点击**（Top 1% 自动加载）。

**数字**：体积 1%、质量 1.19%；P88 带 11.23–12.16。

**docx**：§2.2 图9；表13 案例。

---

## 7 · task2-spatial

**URL**：`?record=1&scene=task2-spatial`

**旁白全文**  
> 空间统计。Moran I、xi……bootstrap……增量均未达两倍抽样标准差。

**布局**：`dedicated` 空间统计专页

| 区域 | 内容 | 文件 |
|------|------|------|
| 左 | 四宫格 Moran I / ξ / D / 峰度 + 宽图 ξ 剖面 | `VideoSpatialPanel.tsx` |
| 右 | 数值表 + bootstrap 小图 | 同面板 |

**操作**：依次指四宫格、宽图、右侧 2σ 行。**无需点击。**

**docx**：§2 图8；附录 5.2 表12。

---

## 8 · task3-hist

**URL**：`?record=1&scene=task3-hist`

**旁白全文**  
> 密度时序。对数直方图……128 分箱……p99 及以上体积 1%……

**布局**：`full` 三栏（无底栏发现）

| 区域 | 内容 | 文件 |
|------|------|------|
| 左栏 | 叠加直方图 + 分箱敏感性读数 | `VideoLeftColumn`, `VideoHistMethodStrip` |
| 中栏 | 体渲染（指最亮纤维） | `VolumeScene` |
| 右栏 | 主峰漂移 + σ/偏度/span 趋势 | `VideoFigureStrip` |

**操作**：指左栏 bin 读数、右栏两图、中栏亮丝。**无需点击。**

**docx**：§3 图10–11；附录 5.3。

---

## 9 · task4-brush

**URL**：`?record=1&scene=task4-brush`

**旁白全文**  
> 相空间刷选。Top 1%……90 至 99%……Bottom 1%……拖拽框选……清除选区。

**布局**：`focus-right`；中栏体渲染 + 右栏刷选区

**操作（录屏重点）**  
1. 点击 **Top 1%** → 等 2–3 秒  
2. 点击 **90–99%**  
3. 点击 **Bottom 1%**  
4. 右栏直方图 **拖拽**框选  
5. 点击 **清除**

| 区域 | 文件 |
|------|------|
| 中栏体渲染 | `VolumeScene` |
| 右栏直方图+预设+投影 | `VideoRightColumn`, `DensityHistogram` |

**docx**：§4 图12；表5。

---

## 10 · task4-validate

**URL**：`?record=1&scene=task4-validate`

**旁白全文**  
> 验证与早停。离线召回 100%、精确率 27.6%……早停 37 毫秒，全网格 282 毫秒。

**布局**：`focus-right`；左验证图 + 右 KPI（无中栏）

| 区域 | 内容 | 文件 |
|------|------|------|
| 左栏 | 阈值对比、KPI 误差、早停召回三图 | `VideoValidateFigureColumn.tsx` |
| 右栏 | 离线召回/精确率/耗时 KPI 格 | `VideoBrushValidationPanel` 等 |

**操作**：指左三图、右 KPI。**无需点击**（进入已 Top 1%）。

**docx**：§4 图15–16；附录 5.4 表14–17。

---

## 11 · findings

**URL**：`?record=1&scene=findings`

**旁白全文**  
> 综合发现。四张发现卡……各卡均支持放大细读……GitHub 仓库 NyxViz。

**布局**：`focus-bottom`；全屏四发现卡

| 卡 | 标题 | 文件 |
|----|------|------|
| 01 | 宇宙网形成 | `VideoFindingsStrip` → FindingEvoCard |
| 02 | 密度分布两极化 | FindingMetricsCard |
| 03 | 1% 体积 · 质量集中 | FindingMassCard |
| 04 | 统计—空间验证 | FindingVerifyCard |

**操作**：指四卡；**点击 1–4 张放大**（OverlayLightbox），每张约 2 秒。

**docx**：§5.2 图17 相关。

---

## 核心代码索引

| 职责 | 路径 |
|------|------|
| 场景定义 | `src/video/sceneRegistry.ts` |
| 录屏壳层 | `src/dashboard/VideoDashboard.tsx` |
| 代表图截屏 | `src/dashboard/useVideoPosterCapture.ts`、`tools/node/lib/captureVideoPoster.mjs` |
| 三栏布局 | `src/dashboard/VideoSceneLayout.tsx` |
| 左/中/右列 | `src/dashboard/video-scenes/layout/Video*Column.tsx` |
| 旁白标签 | `src/video/narrationLabels.ts` |
| record 检测 | `src/video/useVideoScene.ts` |

---

[← 04 Word 解读](./04-Word正文逐章解读.md) · [下一章：05 交互页 app →](./05-交互页app说明.md)
