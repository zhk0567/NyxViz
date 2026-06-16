# NyxViz 答辩视频 · 完整旁白稿

> **TTS** → [`VIDEO_NARRATION_TTS.txt`](./VIDEO_NARRATION_TTS.txt)（**11 行**，一行对应一个 `scene=` 录屏页）  
> **字幕** → [`VIDEO_NARRATION.srt`](./VIDEO_NARRATION.srt)  
> **录屏** → [`VIDEO_SCRIPT.md`](./VIDEO_SCRIPT.md)（**分段 URL** `?record=1&scene=…`）  
> **操作表** → [`VIDEO_RECORDING_OPS.md`](./VIDEO_RECORDING_OPS.md)（旁白说到哪句时做什么）  
> **目标**：旁白 + 字幕整轨 **≤5:00**（298 s），成片含操作停顿 **≤5:30**

---

## scene ↔ TTS 行（一行一页）

| 行 | scene | URL 参数 |
|----|-------|----------|
| 1 | intro | `scene=intro` |
| 2 | task1-tf | `scene=task1-tf` |
| 3 | task1-morph | `scene=task1-morph` |
| 4 | task2-evolution | `scene=task2-evolution` |
| 5 | task2-void | `scene=task2-void` |
| 6 | task2-cases | `scene=task2-cases` |
| 7 | task2-spatial | `scene=task2-spatial` |
| 8 | task3-hist | `scene=task3-hist` |
| 9 | task4-brush | `scene=task4-brush` |
| 10 | task4-validate | `scene=task4-validate` |
| 11 | findings | `scene=findings` |

---

## 分镜与停顿（整轨字幕参考）

| 时段 | 行 | scene |
|------|-----|-------|
| 0:00 | 1 | intro |
| 0:24 | 2 | task1-tf |
| 0:46 | 3 | task1-morph |
| 1:13 | 4 | task2-evolution |
| 1:49 | 5 | task2-void |
| 2:02 | 6 | task2-cases |
| 2:19 | 7 | task2-spatial |
| 2:37 | 8 | task3-hist |
| 3:01 | 9 | task4-brush |
| 4:02 | 10 | task4-validate |
| 4:28 | 11 | findings |

> 整轨字幕 4:58 结束；第 9 行轴长 61s，TTS 连续读较短，刷选录屏后于剪辑插静音对齐。

---

## 数据口径（摘要）

标准差 +15.4% · p99 减 p01 +15.1% · void p10 10→24.69% · p01 1→6.18%  
Top 1% 1% 体积 / 1.19% 质量 · 离线召回 100% / 精确率 27.6% · 早停 37ms vs 全网格 282ms

改 txt 后：`python tools\python\generate_video_srt.py`
