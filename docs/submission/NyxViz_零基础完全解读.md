# NyxViz 零基础完全解读手册

> **读者**：完全不懂可视化、宇宙学或代码，但需要答辩、录屏或阅读 [`NyxViz.docx`](./NyxViz.docx) 的任何人。  
> **母本**：作品说明 Word [`NyxViz.docx`](./NyxViz.docx)（与 [`NyxViz_作品说明文档.docx`](./NyxViz_作品说明文档.docx) 同源）。  
> **本手册**：独立 Markdown 解读层，不替换 Word，只帮你「看懂每一句在说什么」。

---

## 推荐阅读顺序（约 2 小时入门）

| 顺序 | 章节 | 你会得到什么 |
|------|------|--------------|
| 1 | [00 阅读指南](./guide/00-阅读指南.md) | 本仓库里 Word、网页、录屏、代码各自是什么 |
| 2 | [01 竞赛题目](./guide/01-竞赛题目与我们要回答什么.md) | 赛题四任务在问什么、我们答了什么 |
| 3 | [03 叙事逻辑](./guide/03-叙事逻辑与科学结论.md) | 答辩主线与必背 5 个数字 |
| 4 | [06 录屏 11 页](./guide/06-录屏页video完全手册.md) | 每段视频指哪里、说什么 |
| 5 | [02 名词词典](./guide/02-专业名词词典.md) | 遇到不懂的词随时查 |
| 6 | [04 Word 逐章解读](./guide/04-Word正文逐章解读.md) | docx 每一图、每一表的白话说明 |

答辩前可加读：[09 复现与答辩清单](./guide/09-本地复现与答辩清单.md)、[10 答辩代码讲解](./guide/10-答辩代码讲解.md)（总索引）及子章 [10a](./guide/10a-体渲染与VTK代码.md)–[10e](./guide/10e-Python配图代码.md)（**含全部可视化源码摘录**）。

---

## 分章目录

### [00 · 阅读指南](./guide/00-阅读指南.md)

怎么读这份手册；`NyxViz.docx` 与答卷、配图、网页、录屏的关系；三种入口（`app.html` / `video.html` / 静态 PNG）的区别。

### [01 · 竞赛题目与我们要回答什么](./guide/01-竞赛题目与我们要回答什么.md)

ChinaVis 2026 赛道 1-II（Nyx）；128³×100 步数据是什么；任务一至四各要完成什么；本作品刻意**不做什么**（无 AMR、无暗物质、无真实 Lyα 谱）。

### [02 · 专业名词词典](./guide/02-专业名词词典.md)

天文、统计、可视化、工程四类术语；每条含「人话 + 在本作品哪里出现 + 相关文件」。

### [03 · 叙事逻辑与科学结论](./guide/03-叙事逻辑与科学结论.md)

「宇宙网诞生记」故事线；四题闭环；案例 A/B/C；答辩必说的核心数字与一句话结论。

### [04 · Word 正文逐章解读](./guide/04-Word正文逐章解读.md)

对照 docx §0–§5 与附录：系统概览、四题正文、综合叙事、附录 1–5；**逐图逐表**说明图上看到什么、数字含义、对应录屏哪一段。

### [05 · 交互页 app 说明](./guide/05-交互页app说明.md)

`/app.html` 长卷 01–06 节、三栏仪表盘、探索浮层；与 docx 图号、代表图 `task6_story_poster` 的对应。

### [06 · 录屏页 video 完全手册](./guide/06-录屏页video完全手册.md)

11 个 `?record=1&scene=` 页面：URL、布局、旁白、操作、KPI、组件源码、与 docx 图号对照（**答辩录屏必读**）。

### [07 · 仓库文档地图](./guide/07-仓库文档地图.md)

`docs/` 下每个文件夹与关键文件：何时改、与 Word/录屏的关系。

### [08 · 数据与代码管线](./guide/08-数据与代码管线.md)

从 `Nyx/*.dat` 到 `timeline.json`、网页与配图；想改某功能该打开哪个文件。

### [09 · 本地复现与答辩清单](./guide/09-本地复现与答辩清单.md)

`python run.py`、录屏前检查、提交自检、常见评委问答（FAQ）。

### [10 · 答辩代码讲解](./guide/10-答辩代码讲解.md)

按赛题四任务 + 全局 store 联动，讲清**关键文件、函数与口述稿**；评委追问「代码怎么做的」时对照本章。

| 子章 | 内容 |
|------|------|
| [10a 体渲染与 VTK](./guide/10a-体渲染与VTK代码.md) | nyxLoader → Worker → VolumeScene → 传递函数 |
| [10b 直方图与 D3](./guide/10b-直方图与D3代码.md) | DensityHistogram、brush、趋势图 |
| [10c 刷选与 Worker](./guide/10c-刷选与Worker代码.md) | store、联动钩子、三个 Worker |
| [10d 投影与录屏 UI](./guide/10d-投影空间与录屏组件代码.md) | Canvas 投影、video-scenes、长卷组件 |
| [10e Python 配图](./guide/10e-Python配图代码.md) | precompute、generate_figures、viz_style |

---

## 三个入口，别搞混

| 入口 | 地址 | 用途 |
|------|------|------|
| 交互长卷 | `http://localhost:5173/app.html` | 日常探索、代表图截取、答辩现场演示 |
| 录屏专页 | `http://localhost:5173/video.html?record=1&scene=…` | OBS 1920×1080 分段录屏 |
| Word + PNG | `docs/submission/NyxViz.docx` + `docs/figures/` | 上交材料、离线阅读 |

**重要**：任务一「五帧体渲染条带」是 `capture.html` 专用参数拍的静态图，与 `app.html` 拖动时间轴时的体渲染** intentionally 不同**——答辩以交互页为准，条带只讲形态叙事。详见 [04 §0](./guide/04-Word正文逐章解读.md#0-系统概览)。

---

## 与本仓库其他文档的关系

| 文档 | 关系 |
|------|------|
| [`docs/competition/TASKLIST.md`](../competition/TASKLIST.md) | 截止日与提交待办 |
| [`docs/competition/VIDEO_NARRATION_TTS.txt`](../competition/VIDEO_NARRATION_TTS.txt) | 录屏旁白 11 行原文 |
| [`docs/competition/VIDEO_RECORDING_OPS.md`](../competition/VIDEO_RECORDING_OPS.md) | 旁白说到哪句指哪里 |
| [`docs/TOOLS_USAGE.md`](../TOOLS_USAGE.md) | 技术栈清单（本手册 08 章展开） |
| [`docs/report/*.md`](../report/) | 四题 Markdown 文字源（生成答卷用） |

---

*本手册随 NyxViz 仓库维护；数字以 `public/stats/timeline.json` 与 docx 正文为准。*
