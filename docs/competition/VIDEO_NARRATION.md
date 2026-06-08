# NyxViz 答辩视频 · 完整旁白稿

> **TTS** → [`VIDEO_NARRATION_TTS.txt`](./VIDEO_NARRATION_TTS.txt)  
> **字幕** → [`VIDEO_NARRATION.srt`](./VIDEO_NARRATION.srt)  
> **录屏** → [`VIDEO_SCRIPT.md`](./VIDEO_SCRIPT.md)（**分段 URL** `?record=1&scene=…`）  
> **目标**：旁白 ~4.5 min + 停顿 → 成片 ≤5:30

---

## scene ↔ 旁白段落

| scene | URL 参数 | 旁白段落（TTS 正文） |
|-------|----------|----------------------|
| intro | `scene=intro` | 第 1 段：三栏布局概述 |
| task1-tf | `scene=task1-tf` | 第 2 段：传递函数、七 α、Phong、辅光、sampleDistance |
| task1-morph | `scene=task1-morph` | 第 2 段：t=0/25/50/75/99 形态、σ/p99 |
| task2-evolution | `scene=task2-evolution` | 第 3 段：σ、分位跨度、p99.9 量化 |
| task2-void | `scene=task2-void` | 第 3 段：void p10/p01 双阈值 |
| task2-cases | `scene=task2-cases` | 第 3 段：案例 A/B/C、Top1% 质量比 |
| task2-spatial | `scene=task2-spatial` | 第 3 段：Moran's I、ξ、bootstrap |
| task3-hist | `scene=task3-hist` | 第 4 段：128 bins、CDF L∞、五帧叠加 |
| task4-brush | `scene=task4-brush` | 第 5 段：刷选交互演示 |
| task4-validate | `scene=task4-validate` | 第 5 段：早停 KPI、离线 recall/精确 |
| findings | `scene=findings` | 第 6–7 段：四发现卡 + GitHub 结语 |

预览（非录屏）：`http://127.0.0.1:5173/video.html?scene=intro`

---

## 分镜与停顿（整轨字幕参考）

| 时段 | 段 | 对应 scene |
|------|-----|------------|
| 0:00 | 开篇 | intro |
| 0:25 | 任务一 | task1-tf → task1-morph |
| 1:10 | 任务二 | task2-evolution → void → cases → spatial |
| 1:50 | 任务三 | task3-hist |
| 2:20 | 任务四 | task4-brush → task4-validate |
| 4:20 | 发现卡 | findings |
| 4:35 | 结语 | findings |

---

## 数据口径（摘要）

σ +15.4% · p99−p01 +15.1% · void p10 10.00%→24.69% · void p01 1.00%→6.18%  
Top1% 1.00% vol / 1.19% mass · P88 像素分位 · 预设 KPI 精确 · 自定义 ~0.8% 覆盖

改 txt 后：`python tools\python\generate_video_srt.py`
