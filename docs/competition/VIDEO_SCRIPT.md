# NyxViz 答辩视频 · 录屏操作手册

> **完整旁白（照读稿）** → **[`VIDEO_NARRATION.md`](./VIDEO_NARRATION.md)** ← 字幕与配音请用该文件，本文**不含**旁白全文。  
> **旁白同步操作** → **[`VIDEO_RECORDING_OPS.md`](./VIDEO_RECORDING_OPS.md)** ← 说到哪句时点什么、指哪里。  
> **目标**：≤5:00 旁白/字幕整轨，≤5:30 成片（含操作停顿），**≤50MB**  
> **方案**：**分段 URL 录屏** — 同一 `video.html` 下 11 个子场景（`scene=`），每段单独 OBS 录制后剪辑拼接

---

## 1. 录屏地址

基础参数：

```text
http://127.0.0.1:5173/video.html?record=1&scene=<id>
```

- `record=1`：隐藏导航、弱化背景、默认 t=99、底部黑边，适合 OBS
- `scene` 缺省等同 `intro`（兼容旧链接 `?record=1`）
- **预览全部子场景**（非录屏）：`video.html?scene=task1-tf` — 预览栏横向场景条 **无刷新切换** scene，地址栏 `?scene=` 同步更新
- **录屏分段**：仍用下方表格中的 `?record=1&scene=` URL，每段独立打开浏览器录制；录屏模式下预览条仅显示「复制分段 URL」，避免误切场景
- **布局差异**：`intro` 与 `findings` 的底部四卡高度由 scene 配置驱动（intro 较紧凑、findings 更大），属预期行为

---

## 2. 分段录屏表（11 段）

按顺序录制，每段改浏览器地址后 OBS 开始/停止，后期按旁白时间轴拼接。

| 顺序 | scene id | 录屏 URL | TTS 行 | 建议时长 | OBS 操作 |
|------|----------|----------|--------|----------|----------|
| 1 | intro | `?record=1&scene=intro` | 第 1 行 | ~25s | 指三栏布局 |
| 2 | task1-tf | `?record=1&scene=task1-tf` | 第 2 行 | ~22s | 指七处 alpha、冯氏光照、右栏光照示意 |
| 3 | task1-morph | `?record=1&scene=task1-morph` | 第 3 行 | ~27s | 第 0→25→50→75→99 步，各停 2s |
| 4 | task2-evolution | `?record=1&scene=task2-evolution` | 第 4 行 | ~28s | 指左栏 KPI + 右栏四图 |
| 5 | task2-void | `?record=1&scene=task2-void` | 第 5 行 | ~15s | 指 p10/p01 双阈值卡片 |
| 6 | task2-cases | `?record=1&scene=task2-cases` | 第 6 行 | ~20s | 指案例 A/B/C + 中栏 Top 1% 投影 |
| 7 | task2-spatial | `?record=1&scene=task2-spatial` | 第 7 行 | ~18s | 指 Moran/xi/D/峰度四图 + bootstrap |
| 8 | task3-hist | `?record=1&scene=task3-hist` | 第 8 行 | ~25s | 指五帧叠加 + 128 分箱条 |
| 9 | task4-brush | `?record=1&scene=task4-brush` | 第 9 行 | ~69s | Top 1%→纤维带→最暗 1%→拖拽框选→清除选区 |
| 10 | task4-validate | `?record=1&scene=task4-validate` | 第 10 行 | ~26s | 指阈值对比/自定义误差/早停召回 |
| 11 | findings | `?record=1&scene=findings` | 第 11 行 | ~30s | 指四卡放大；开源结语 |

完整示例：

```text
http://127.0.0.1:5173/video.html?record=1&scene=task4-brush
```

---

## 3. 录前准备

```powershell
cd F:\commercial\NyxViz
npm install
pip install -r tools/python/requirements.txt
npm run precompute
python run.py
```

### OBS 建议

| 项 | 设置 |
|----|------|
| 画布 | 1920 × 1080 |
| 来源 | 窗口捕获 → Chrome/Edge，勾选「捕获光标」 |
| 浏览器 | F11 全屏；缩放 **100%**（Ctrl+0） |
| 帧率 | 30 fps |
| 工作流 | 每 scene 一段素材；或 OBS 多场景各绑一个浏览器书签 |

### 录前检查

- [ ] 浏览器 **1920×1080**、缩放 **100%**、**F11 全屏**；URL 带 **`?record=1`**
- [ ] 录屏模式 **不显示** 预览条与「复制分段 URL」（OBS 画面无开发 UI）
- [ ] **`intro` 与后续 scene 视觉一致**：同一套录屏字号/对比度；header 下可见 **场景标题条**
- [ ] 各 scene URL 3–5 秒内体渲染出图（含 task1-tf、task2-spatial）
- [ ] `intro`：左栏五帧叠加 + sigma/p99 及以上/p99 减 p01 趋势；三栏副标题可见
- [ ] `task1-tf`：七处 alpha 阶梯、颜色传递函数条、冯氏光照/辅光、光照示意图
- [ ] `task1-morph`：右栏五帧缩略图可点切步；阶段说明与 sigma/p99 读数
- [ ] `task2-evolution`：演化三卡 + task2_evolution_story 图
- [ ] `task2-void`：p10/p01 双卡 + void 演化图（无中栏体渲染）
- [ ] `task2-cases`：案例 A/B/C 配图 + Top 1% 投影
- [ ] `task2-spatial`：莫兰指数/xi 数值 + bootstrap 图
- [ ] `task3-hist`：五帧叠加 + 128 分箱/skew + peak_drift 图
- [ ] `task4-brush`：操作步骤条 + Top 1% 后体积/质量读数
- [ ] `task4-validate`：recall/精确/早停 KPI + 验证摘要图
- [ ] `findings` 四卡底边框完整、支持放大细读
- [ ] `public/stats/*.json` 已生成（`npm run precompute`）

---

## 4. 刷选段细步骤（scene=task4-brush）

1. 确认顶栏 **t=99**
2. **Top 1%** → 等渲染 **3s**
3. **90–99%** → **Bottom 1%**
4. 在直方图上 **拖拽** 框选（如 p50–p99）
5. **清除**

验证段（`task4-validate`）已预置 Top 1%，指右栏阈值对比、自定义误差与早停召回三图。

---

## 5. 剪辑与导出

| 步骤 | 说明 |
|------|------|
| 拼接 | 按 §2 顺序对齐 11 段素材 |
| 剪掉 | 各段加载等待、误点 |
| 字幕 | 导入 **`VIDEO_NARRATION.srt`**（整轨一条，按 SECTION 手动微调） |
| 导出 | H.264 1080p，目标 &lt;50MB |
| 自检 | task4-brush 段须出现 **Top 1% → 高亮 → 金色投影** |

---

## 6. 常见问题

| 问题 | 处理 |
|------|------|
| 体渲染黑屏 | 刷新；确认 `Nyx/` 存在 |
| scene 无数据面板 | 运行 `npm run precompute` 生成 `public/stats/` |
| Top 1% 无金斑 | 等 Worker 1–2s |
| 旁白数字不符 | `npm run test:report` 后改 TTS，再跑 `generate_video_srt.py` |

---

## 7. 文档索引

| 文件 | 内容 |
|------|------|
| **[`VIDEO_NARRATION.srt`](./VIDEO_NARRATION.srt)** | Premiere 字幕 |
| **[`VIDEO_NARRATION_TTS.txt`](./VIDEO_NARRATION_TTS.txt)** | TTS 旁白纯文本 |
| **[`VIDEO_NARRATION.md`](./VIDEO_NARRATION.md)** | 旁白稿 + scene 对照 |
| **`VIDEO_SCRIPT.md`**（本文件） | 分段 URL、OBS、剪辑 |
| [`TASKLIST.md`](./TASKLIST.md) | 提交待办 |

---

*旁白数字以 `timeline.json` / `public/stats/` 为准；scene 实现见 `src/video/sceneRegistry.ts`。*
