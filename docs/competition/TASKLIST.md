# NyxViz 任务清单

> [ChinaVis 2026 赛道1-II（Nyx）](https://chinavis.org/2026/zh/challenge_call_for_participation/)  
> 作品截止：**2026-06-20** · 结果公布：**2026-07-02**

仓库侧工程与内容已就绪：交互页 v2 三栏仪表盘、`/` 成果页「宇宙网诞生记」01–06 叙事、四题报告/配图/答卷脚本、`timeline.json` 统计与 `submission-pack` 流水线。

- **M 段**：赛题截止前**必须**由你本人完成的上传/录屏/答卷（原先清单只保留这部分，故未写视觉差距）。
- **V 段**：相对「宇宙网诞生记」参考长图的**版式与专图**差距（**不阻塞** 6/20 提交；做则视频/代表图更像设计稿，数字仍须来自 `timeline.json`，勿抄示意图 8.7×、76% 等）。

---

## 常用命令

```powershell
npm run submission-pack      # 预计算 + 配图 + 报告 + docx + 代表图 + 答卷
npm run fill-answer-sheet    # 官方答卷（需先填 docs/competition/team.json）
npm run figures:hd           # capture + 静态图 + 报告
npm run export-pdf           # docx → PDF（本机 Word）
npm run test:words           # 四题 ≤800 字/题
npm run test:report          # 报告数字与 timeline 一致
npm run deliver              # 含 showcase 全流程
python run.py                # 本地预览 / 与 app.html
```

---

## 待办：手动交付（截止前）

| 编号 | 任务 | 说明 |
|------|------|------|
| **M1** | 官方答卷终检 | ✅ 占位 `team.json` + `fill-answer-sheet` + `test:words`/`test:report`；**提交前**改真实队名/成员 |
| **M2** | 100 字摘要 | ✅ 见 [`ABSTRACT_100.txt`](./ABSTRACT_100.txt)，提交表单粘贴 |
| **M3** | 录制视频 | ⏳ 待你录屏；分镜见 [`VIDEO_SCRIPT.md`](./VIDEO_SCRIPT.md)；刷选段用 **`/video.html`** 三栏（1920×1080） |
| **M4** | 代表图终检 | ✅ `submission_representative.jpg`（由 `task6_story_poster` 导出，&lt;20MB）；可选 `figures:hd` 提质 |
| **M5** | 上传提交 | ⏳ [提交入口](https://s99x45wjic.jiandaoyun.com/f/6a0ae5b7d2ebb735eedc664e)，建议 **6/18–19** |

### 建议时间

| 时间 | 动作 |
|------|------|
| 6 月中旬 | M1–M4 |
| **6/18–19** | M5 上传 |

---

## 待办：相对参考长图（可选 · V）

> 与交互 v2 / 成果页 01–06 **叙事已对齐**，差的是海报级排版与若干静态信息图。未列入 M 段是因为赛题不要求与参考图版式一致。  
> **制作基准**：[`LAYOUT_SPEC.md`](./LAYOUT_SPEC.md)（3840×6480）→ 先 [`WIREFRAME_CHECKLIST.md`](./WIREFRAME_CHECKLIST.md) 灰度线框 → 再按坐标出图。

| 编号 | 任务 | 说明 | 粗估 |
|------|------|------|------|
| **V0** | 布局规格书 | ✅ `LAYOUT_SPEC.md` + `layout_spec.py` + 参考图 `reference/` |
| **V0b** | 灰度线框 | ✅ `npm run wireframe` → `wireframe_3840x6480.png` |
| **V0c** | 3840×6480 成品 | ✅ `npm run poster:3840`（提交/代表图）；**`/app.html` 默认 HTML 分段长卷**（非单张拼版 PNG） |
| **V1** | Hero 海报级首屏 | ✅ `task1_hero_poster.png` + 成果页 01 hero |
| **V2** | 03 专图版式 | ✅ `task3_story_panel.png`（真实 σ/span/体积增幅 + t=99 四 KPI） |
| **V3** | 04 双行四列静图 | ✅ `task4_brush_rows.png` |
| **V4** | 05 质量占比 | ✅ `massFractionAbove/BelowP99` + `task5_mass_pie.png` |
| **V5** | 06 流程图美化 | ✅ 七步 `task0_story_flow.png` |
| **V6** | 单页长图导出 | ✅ `task6_story_poster.png` → 代表图 |
| **V7** | 交互页 vs 04 版式 | ✅ `/app.html` 右栏 `brush-verify-hint` 文案 |

**建议顺序（时间紧可只做 V3+V6）**：V3 → V2 → V1 → V6；V4 需新统计再动；V7 最低优先级。

---

## 待办：入选后（7 月）

| 编号 | 任务 |
|------|------|
| **F1** | 对照 [2024 入选作品](https://chinavis.org/2024/challenge.html) 润色现场叙事 |
| **F2** | 百度云打包：figures、答卷、视频、Showcase |
| **F3** | A0 海报（结论 / 代表图 / QR） |
| **F4** | ChinaVis 2026 注册与现场张贴（7.19–22 贵阳） |

---

## 提交前自检

1. 四题答卷：方法 → 观察 → 数据佐证；数字与 `public/stats/timeline.json` 一致（勿用示意图夸大倍数）。
2. 叙事闭环：任务2 假设 → 任务3 定量 → 任务4 刷选验证 → 任务1 体渲染印证。
3. 三张主图：`task1_vol_strip`、`task2_evolution_story`、`task4_brush_triptych`。
4. 视频含 **`/video.html`** 三栏 Top 1% → 体渲染高亮 → XY 投影一段（或 `app.html` 探索浮层）。
5. **（可选）** 若做 V 段：代表图/长图数字仍跑 `npm run test:report`；未完成 V 段不视为缺交。

---

## 参考

- [竞赛征稿](https://chinavis.org/2026/zh/challenge_call_for_participation/)
- [Nyx 数据](https://chinavis.org/2026/challenge/1-IINyx_dataset.zip)
- [答卷模板 1-II](https://chinavis.org/2026/challenge/1-II_answerSheet.docx)
- [视频脚本](./VIDEO_SCRIPT.md)
- [长卷布局规格](./LAYOUT_SPEC.md)
- [线框检查清单](./WIREFRAME_CHECKLIST.md)
- [文档目录](../README.md)
