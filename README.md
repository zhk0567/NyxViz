# Nyx 宇宙学密度可视化（赛题 II）

基于 Nyx 官方 100 步、128³ 气体密度数据集的可视分析工程：vtk.js 体渲染、时序对数直方图统计、相空间刷选联动仪表盘，并自动生成报告与单文件 HTML 展示页。

## 数据

将赛题数据置于仓库根目录：

```
Nyx/
  0000.dat … 0099.dat
```

- 格式：小端 `float32`
- 存储：z 最快 → y → x（`flatIndex = z + 128*y + 128²*x`）

## 环境

- Node.js 18+
- Python 3.10+（预计算、出图、docx）
- Playwright Chromium（体渲染截图，`npx playwright install chromium`）

## 快速开始

```powershell
cd F:\commercial\NyxViz
npm install
npx playwright install chromium
pip install -r scripts/requirements.txt
npm run precompute
npm run dev
```

浏览器打开 http://localhost:5173（体渲染 / 时序统计 / 刷选联动）。

## 一键交付

```powershell
npm run deliver
```

依次执行：预计算 → vtk 体渲染截图 → 静态图 → Markdown 报告 → docx → 单文件 Showcase HTML。

## 命令一览

| 命令 | 说明 |
|------|------|
| `npm run capture-volumes` | Playwright 导出 `docs/figures/task1_vol_*.png` |
| `npm run figures` | 任务 2–4 静态图（任务一优先用 vol 图） |
| `npm run export-report` | `docs/report/*.md` |
| `npm run export-docx` | `docs/report/Nyx_Submission.docx` |
| `npm run showcase` | `NyxViz_Showcase.html`（静态 + 内嵌交互 bundle） |
| `npm run showcase:offline` | 同上，并 gzip 内嵌 t=0,99 体数据 |
| `npm run build:showcase` | 仅构建 `dist-showcase/showcase.iife.js` |
| `npm run test` | Vitest 轴序测试 |

## 单文件展示页

生成 [`NyxViz_Showcase.html`](NyxViz_Showcase.html) 后：

- **静态部分**：四任务报告、配图、100 步统计表（可 `file://` 打开）
- **交互部分**：内嵌 vtk.js 刷选仪表盘
  - 完整 100 步：先 `npm run preview`，再访问 `http://localhost:4173/NyxViz_Showcase.html`（需将 HTML 放在可被同源访问的位置，或直接用 `npm run dev` 主应用）
  - 离线代表步：`npm run showcase:offline` 内嵌 t=0/99

## 功能

1. **体渲染**：传递函数滑块 + 双光源，时间步滑块
2. **时序统计**：五步直方图叠加、mean/p99/std 曲线
3. **刷选联动**：直方图框选 / Top1% / Bottom1% → 体渲染高亮 + 3D 点云

## 目录结构

```
src/volume/       体渲染与传递函数
src/histogram/    直方图与时序图
src/showcase/     嵌入 Showcase 的交互组件
capture.html      vtk 截图专用页
scripts/          Python / Playwright 工具链
docs/figures/     配图
docs/report/      报告与 docx
NyxViz_Showcase.html
```

## 赛题对应

| 任务 | 实现 |
|------|------|
| 体数据渲染 | `VolumeScene.tsx` + `capture-volumes` |
| 演化归纳 | `docs/report/task2_evolution.md` |
| 对数直方图 | `precompute.py` + `histogram/*` |
| 刷选联动 | `App.tsx` / `InteractiveShowcase.tsx` |
