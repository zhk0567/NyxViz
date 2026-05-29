# NyxViz 任务清单

> 依据 [ChinaVis 2026 赛道1-II：科学可视化（Nyx）](https://chinavis.org/2026/zh/challenge_call_for_participation/)  
> 作品截止：**2026-06-20** · 结果公布：**2026-07-02**

**原则**：仓库内能自动/协作完成的先做；**需你手动交付**（填答卷、录视频、上传）统一放到清单末尾，截止前再收口即可。

---

## 已完成（仓库内）

运行 `npm run submission-pack` 可一键再生下列产出。

| 类别 | 内容 |
|------|------|
| 四任务配图 | `docs/figures/`（体渲染、演化、直方图、刷选三联等） |
| 四任务正文 | `docs/report/task*.md`、`full_report.md` |
| 交付副本 | `docs/submission/`（**Nyx_answerSheet_filled.docx** + pdf + 代表图 JPG） |
| 成果页 | `/` 静态报告 + 配图 + 100 步表 |
| 交互演示 | `/app.html` 体渲染 / 刷选 / Worker |
| 工程结构 | `pages/`、`tools/python`、`tools/node`、`docs/competition/` |
| 视觉管线 | cosmic 色标、1920 截图、展板质量体渲染、目录整理 |

```powershell
npm run figures:hd        # 推荐：capture + 静态图 + 报告
npm run submission-pack     # 预计算 + 配图 + 报告 + docx + 代表图
npm run fill-answer-sheet # 官方答卷模板自动填四题正文+图
npm run hist-animation   # 100 步直方图演化 GIF（视频 B-roll）
npm run export-pdf          # docx → PDF（需本机 Word 或 LibreOffice）
npm run test:words        # 四题答卷字数自检（≤800 字/题）
npm run deliver             # 含 showcase 全流程
```

---

## 一、当前待办（仓库 / 可协作）

按建议顺序执行；做完一项勾一项。

### P0 — 内容与质量（优先）

- [x] **E1** 任务2 正文补 **2–3 句** Nyx / AMReX / IGM 宇宙学背景（改 `docs/report/task2_evolution.md` → `export-report`）
- [x] **E2** 任务4 补 **「空间→统计」** 证据：`task4_spatial_to_stats.png` + `task4_brush.md` / `spatial_to_stats.py` / `generate_figures.py`
- [x] **E3** 四题报告补 **工具声明** 段（vite、vtk.js、D3、`tools/python`、`tools/node` Playwright）→ 同步 `export_report.py` 模板
- [x] **E4** **交叉校验**：图中数字与 `public/stats/timeline.json` 一致；跑 `npm run test`、`npm run test:loader`、`npm run test:report`
- [x] **E5** 重跑 `npm run showcase`，更新 `docs/showcase/NyxViz_Showcase.html`（含最新配图）

### P1 — 工程增强（可选，提效）

- [x] **E6** 脚本：`tools/python/count_report_chars.py` + `npm run test:words`（四题 ≤800 字/题，粘贴用计数）
- [x] **E7** 脚本：`export_docx_pdf.py` + `npm run export-pdf`（Word COM → `docs/submission/Nyx_Submission.pdf`）
- [x] **E8** 脚本：`fill_answer_sheet.py` + `npm run fill-answer-sheet`（官方 `1-II_answerSheet.docx` → `Nyx_answerSheet_filled.docx`；可选 `team.json`）
- [x] **E9** 100 步直方图 **GIF**：`generate_hist_animation.py` + `npm run hist-animation` → `task3_hist_evolution.gif`（可选 MP4 需 ffmpeg）

### P2 — 入选后（7 月以后）

- [ ] **F1** 对照 [2024 入选作品](https://chinavis.org/2024/challenge.html) 润色叙事（问题—方法—证据—结论）
- [ ] **F2** 百度云打包：`docs/figures/`、答卷终稿、视频源、Showcase
- [ ] **F3** A0 海报（左结论 / 中代表图 / 右 QR）
- [ ] **F4** ChinaVis 2026 注册 + 现场张贴（7.19–22 贵阳）

---

## 二、薄弱点（待 E 段任务消化）

| 项 | 说明 | 对应任务 |
|----|------|----------|
| 宇宙学语境 | 报告偏工程叙述 | ~~E1~~ 已完成 |
| 任务4 反向联动 | ~~缺「空间→统计」证据~~ → `task4_spatial_to_stats.png` | ~~E2~~ 已完成 |
| Showcase 过期 | ~~单文件 HTML 可能未含最新图~~ → 5.37 MB 已重建 | ~~E5~~ 已完成 |
| 字数未自检 | ~~四题是否各 ≤800 字未知~~ → `npm run test:words` | ~~E6~~ 已完成 |

---

## 三、建议节奏（不含手动交付）

| 阶段 | 目标 |
|------|------|
| **现在** | **P0 + P1 工程项已全部完成** → **M 段手动交付**（答卷 / 视频 / 上传） |
| **随后** | M1–M5 手动交付 |
| **7 月后** | F1–F4（若入选） |

---

## 四、评分要点（写报告 / 日后录视频时对照）

1. 四题结构：**方法 → 观察 → 数据佐证 → 配图（≤5）**
2. 强调 **100/100 时间步** 参与预计算，代表步仅为插图
3. 闭环：任务2 假设 → 任务3 定量 → 任务4 空间验证 → 任务1 视觉印证
4. 三张王牌：`task1_vol_strip`、`task2_evolution_story`、`task4_brush_triptych`

---

## 五、手动交付（不着急 · 截止前收口）

> 以下全部依赖你本人操作，**建议 6 月中旬再集中处理**，不必现在开工。

| 编号 | 任务 | 规格 / 说明 |
|------|------|-------------|
| **M1** | 官方答卷 | `npm run fill-answer-sheet` → `docs/submission/Nyx_answerSheet_filled.docx`；复制 `team.json.example` → `team.json` 填队名/成员；**≤800 字 / ≤5 图 / 题** |
| **M2** | 100 字摘要 | 100 步统计 + 体渲染 + 刷选闭环 + 技术栈 |
| **M3** | 录制视频 | MP4 **≤5 分钟、≤50MB**；分镜见 [`VIDEO_SCRIPT.md`](./VIDEO_SCRIPT.md)，含 `/app.html` 刷选一段 |
| **M4** | 终检代表图 | `docs/submission/submission_representative.jpg`，清晰且 **<20MB**；必要时 `npm run submission-pack` |
| **M5** | 上传提交 | [提交入口](https://s99x45wjic.jiandaoyun.com/f/6a0ae5b7d2ebb735eedc664e)，建议 **6/18–19** 上传 |

### 手动交付倒排（参考）

| 时间 | 动作 |
|------|------|
| 6 月上旬 | 确认 E 段仓库任务完成；`npm run submission-pack` 终版 |
| 6 月中旬 | M1–M4（答卷、摘要、视频、代表图） |
| **6/18–19** | M5 上传 |

---

## 六、参考链接

- [竞赛征稿](https://chinavis.org/2026/zh/challenge_call_for_participation/)
- [Nyx 数据](https://chinavis.org/2026/challenge/1-IINyx_dataset.zip)
- [答卷模板 1-II](https://chinavis.org/2026/challenge/1-II_answerSheet.docx)
- [视频脚本](./VIDEO_SCRIPT.md)
- [文档目录说明](../README.md)
