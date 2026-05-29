# NyxViz 冲高分任务清单

> 依据 [ChinaVis 2026 赛道1-II：科学可视化（Nyx）](https://chinavis.org/2026/zh/challenge_call_for_participation/)  
> 截止：**作品 2026-06-20** · 结果 **2026-07-02**

---

## 已完成（仓库内）

运行 `npm run submission-pack` 可一键再生下列产出。

### 四道赛题 · 配图与正文

| 赛题 | 配图（`docs/figures/`） | 正文（`docs/report/`） |
|------|-------------------------|----------------------|
| 任务1 体渲染 | `task1_vol_t0000`…`0099`（vtk）、`task1_vol_strip` | `task1_volume.md` |
| 任务2 演化归纳 | `task2_evolution_story`（σ/跨度/尾占比/偏度） | `task2_evolution.md`（含 3 条可检验结论） |
| 任务3 时序统计 | `task3_hist_overlay`、`task3_metrics_timeline`、`task3_evolution_metrics`、`task3_peak_drift` | `task3_histogram.md`（100 步、128 bins 方法） |
| 任务4 刷选 | `task4_brush_triptych`、`task4_hist_brush_*`、`task4_brush_top1/bottom1` | `task4_brush.md`（Top/Bottom 1% 验证） |

### 交付物

| 文件 | 说明 |
|------|------|
| `docs/report/Nyx_Submission.docx` | 四题 Word 汇总（贴官方答卷前稿） |
| `docs/report/full_report.md` | 完整 Markdown |
| `docs/submission/submission_representative.jpg` | 代表图 JPG（≤20MB） |
| `docs/VIDEO_SCRIPT.md` | 5 分钟视频分镜 |
| 首页 `/` | 静态成果展示（报告 + 配图 + 100 步表） |
| `/app.html` | 交互演示（体渲染 / 刷选 / Worker） |

### 工程命令

```powershell
npm run submission-pack   # 预计算 + 配图 + 报告 + docx + 代表图
npm run capture-volumes   # 1920×1080 展板体渲染（全局 log TF）
npm run figures:hd        # capture + 静态图 + 报告（推荐重生配图）
npm run deliver           # 含 showcase 全流程
```

---

## 一、官方提交要件（仍须人工完成）

| 材料 | 规格 | 状态 |
|------|------|------|
| 答卷 | 官方 [`1-II_answerSheet.docx`](https://chinavis.org/2026/challenge/1-II_answerSheet.docx)，四题 **≤800 字 / ≤5 图** | 待粘贴 `docs/report` + 配图 |
| 视频 | MP4，**≤5 分钟、≤50MB** | 待录制（脚本见 `docs/VIDEO_SCRIPT.md`） |
| 代表图 | JPG **1 张**，≤20MB | 已有 `docs/submission/submission_representative.jpg` |
| 摘要 | **100 字** | 待写 |
| 上传 | [赛道1 提交入口](https://s99x45wjic.jiandaoyun.com/f/6a0ae5b7d2ebb735eedc664e) 截止 **6-20** | 待办 |

---

## 二、待办清单（按优先级）

### P0 — 提交封口（高分必要）

- [ ] **A1** 将 `docs/report/task*.md` 四题内容 + 配图嵌入官方 **answerSheet**，每题裁剪至 ≤800 字、≤5 图
- [ ] **A2** 撰写 **100 字作品摘要**（100 步统计 + 体渲染 + 刷选闭环 + vtk/D3）
- [ ] **A3** 按 `docs/VIDEO_SCRIPT.md` 录制解说视频，H.264 压至 **<50MB**，含 `/app.html` 刷选录屏一段
- [ ] **A4** 终检代表图：确认 `submission_representative.jpg` 清晰、<20MB，必要时 `npm run submission-pack` 重生
- [ ] **A5** **6月18–19** 上传答卷 PDF/Word + 视频 + 代表图（避免截止日高峰）

### P1 — 内容补强（拉高评审分）

- [ ] **B1** 任务2 正文补 **2–3 句** Nyx/AMReX/IGM 背景引用（天体物理可读性）
- [ ] **B2** 任务4 补 **「空间→统计」** 反向案例：在 `/app.html` 录屏/截图——指出 filament 后在直方图标密度带
- [ ] **B3** 答卷「工具声明」段：vite、vtk.js、D3、Python（precompute/generate_figures）、Playwright（capture）
- [ ] **B4** 交叉校验：图中数字与 `public/stats/timeline.json` 一致；跑 `npm run test` / `npm run test:loader`
- [ ] **B5**（可选）100 步直方图 **GIF/短视频** 片段，插入 5 分钟视频 1:20–2:10 段

### P2 — 入选后 / 冲一等奖

- [ ] **C1** 对照 [2024 入选作品](https://chinavis.org/2024/challenge.html) / [VAST 库](http://cs.umd.edu/hcil/varepository/benchmarks.php) 润色答卷叙事（问题—方法—证据—结论）
- [ ] **C2** 百度云打包：全部 `docs/figures/`、答卷终稿、视频源、可选 `NyxViz_Showcase.html`
- [ ] **C3** 预设计 **A0 海报**（左结论 / 中代表图 / 右 QR→静态首页）
- [ ] **C4** 入选后 ≥1 人注册 **ChinaVis 2026**（7.19–22 贵阳）并完成海报张贴

### P3 — 工程可选

- [ ] **D1** 脚本：从 `Nyx_Submission.docx` 导出 **PDF** 便于上传
- [ ] **D2** 脚本：自动填入官方 answerSheet（python-docx 模板填充）
- [ ] **D3** `npm run poster`：生成 A0 海报 PDF
- [ ] **D4** 重跑 `npm run showcase` 使 `NyxViz_Showcase.html` 含最新配图

---

## 三、当前薄弱点（相对满分答卷）

| 项 | 说明 |
|----|------|
| 官方模板 | 现有 docx 为自建版式，**未**写入 answerSheet 固定栏位 |
| 任务4 反向联动 | 静态图以「统计→空间」为主，**缺**真实 UI 截图的「空间→统计」 |
| 视频 | 仓库**无** MP4，评委可能不看 live 地址 |
| 体渲染截图 | 答卷前建议 `npm run figures:hd` 重生 `task1_vol_*`（1920、展板质量） |
| 字数 | 未自动统计四题是否各 ≤800 字，粘贴前需人工删改 |
| 宇宙学文献 | 报告偏工程叙述，可补 1 段领域语境 |

---

## 四、倒排时间线

| 阶段 | 建议日期 | 目标 |
|------|----------|------|
| 本周 | 即日起 | A1–A2 答卷 + 摘要；B1–B4 补强 |
| 下周 | 6 月上旬 | A3 视频定稿；A4 代表图终检 |
| 冲刺 | **6/18–19** | A5 上传 |
| 会后 | 7/2 后 | 若入选：C3–C4 海报与注册 |

---

## 五、评分要点（写答卷/录视频时对照）

1. 四题结构：**方法 → 观察 → 数据佐证 → 配图（≤5）**
2. 反复强调 **100/100 时间步** 参与预计算，代表步仅为插图
3. 闭环：任务2 假设 → 任务3 定量 → 任务4 空间验证 → 任务1 视觉印证
4. 三张王牌：`task1_vol_strip`、`task2_evolution_story`、`task4_brush_triptych`
5. 视频需 **standalone**：无网络也能看懂分析流程

---

## 六、参考链接

- [竞赛征稿](https://chinavis.org/2026/zh/challenge_call_for_participation/)
- [Nyx 数据](https://chinavis.org/2026/challenge/1-IINyx_dataset.zip)
- [答卷模板 1-II](https://chinavis.org/2026/challenge/1-II_answerSheet.docx)
- [视频脚本](./VIDEO_SCRIPT.md)
