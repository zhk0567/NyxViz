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

## 快速开始（唯一入口）

将赛题数据放入 `Nyx/` 后，在项目根目录执行：

```powershell
cd F:\commercial\NyxViz
pip install -r tools/python/requirements.txt
python run.py
```

`run.py` 会自动：释放 5173/5174/4173 等占用端口 → 首次运行 `npm install` / `precompute` / 生成报告与配图 → 启动 Vite → 打开浏览器。

**默认首页**为「宇宙网诞生记」叙事（01–06 节 + 四题报告 + 统计表）。三栏交互仪表盘见 [http://localhost:5173/app.html](http://localhost:5173/app.html)。

可选环境变量：`NYXVIZ_PORT=5173` 指定端口。

### 手动启动（开发）

```powershell
npm install
npm run precompute
npm run dev
```

浏览器访问 http://localhost:5173 查看完整成果；交互仪表盘见 `/app.html`（默认勾选「展板质量体渲染」，全局 log 色标与截图一致）。

## 赛题交付（四任务成果）

```powershell
npm run submission-pack
```

生成：`docs/submission/` 内答卷、报告 docx/pdf、代表图；配图在 `docs/figures/`。填写 `team.json` 后 `npm run fill-answer-sheet`。

## 一键交付

```powershell
npm run deliver
```

依次执行：预计算 → vtk 体渲染截图 → 静态图 → 报告 → docx → submission-pack → 单文件 Showcase HTML。

## 命令一览

| 命令 | 说明 |
|------|------|
| `npm run capture-volumes` | Playwright **1920×1080** 展板体渲染 → `task1_vol_*.png`（可选 `CAPTURE_USE_GPU=1`） |
| `npm run figures` | 任务 2–4 静态图（dark cosmic 主题、dpi 200） |
| `npm run figures:hd` | `capture-volumes` + `figures` + `export-report`（展板配图一条龙） |
| `npm run export-report` | `docs/report/*.md` |
| `npm run fill-answer-sheet` | `docs/submission/Nyx_answerSheet_filled.docx`（官方模板） |
| `npm run hist-animation` | `docs/figures/task3_hist_evolution.gif`（视频 B-roll） |
| `npm run export-docx` | `docs/submission/NyxViz_作品说明文档.docx` |
| `npm run export-pdf` | `docs/submission/NyxViz_作品说明文档.pdf` |
| `npm run showcase` | `NyxViz_Showcase.html`（静态 + 内嵌交互 bundle） |
| `npm run showcase:offline` | 同上，并 gzip 内嵌 t=0,99 体数据 |
| `npm run build:showcase` | 仅构建 `dist-showcase/showcase.iife.js` |
| `npm run test` | Vitest 轴序测试 |

## 单文件展示页

生成 [`docs/showcase/NyxViz_Showcase.html`](docs/showcase/NyxViz_Showcase.html) 后：

- **静态部分**：四任务报告、配图、100 步统计表（可 `file://` 打开）
- **交互部分**：内嵌 vtk.js 刷选仪表盘
  - 完整 100 步：先 `npm run preview`，再访问 `http://localhost:4173/NyxViz_Showcase.html`（需将 HTML 放在可被同源访问的位置，或直接用 `npm run dev` 主应用）
  - 离线代表步：`npm run showcase:offline` 内嵌 t=0/99

## 功能

1. **体渲染**：宇宙学 `cosmic` 色标、传递函数滑块、密度图例、双光源；默认交互采样，可勾选「高质量体渲染」
2. **时序统计**：五步直方图叠加（主题色板）、mean/p99/std 曲线与淡填充
3. **刷选联动**：直方图框选 / Top1% / Bottom1% → 体渲染高亮 + Canvas 2D 最大密度投影；**默认不加载第二个 VTK**，勾选「显示 3D 点云」后再挂载点云
4. **性能**：刷选扫描在 Web Worker；VTK 按需 `lazy` 分包；相邻时间步 `requestIdleCallback` 预取（最多 3 步缓存）；非当前页签跳过 GPU 渲染

页签可通过 URL hash 直达，例如 `http://localhost:5173/#volume`、`#stats`、`#brush`。

## 目录结构

```
pages/              Vite HTML 入口（index / app / capture）
src/                React + vtk.js 源码
tools/python/       预计算、配图、报告、docx、submission-pack
tools/node/         Playwright 体渲染截图
public/stats/       timeline.json（precompute 生成）
docs/figures/       任务配图 PNG
docs/report/        Markdown 报告与 docx 源
docs/submission/    赛题交付副本
docs/competition/   赛题清单与视频脚本
docs/showcase/      单文件 Showcase HTML
Nyx/                赛题体数据（本地，不入库）
run.py              一键启动
```

详见 [`docs/README.md`](docs/README.md)。

## 赛题对应

| 任务 | 实现 |
|------|------|
| 体数据渲染 | `VolumeScene.tsx` + `capture-volumes` |
| 演化归纳 | `docs/report/task2_evolution.md` |
| 对数直方图 | `precompute.py` + `histogram/*` |
| 刷选联动 | `App.tsx` / `InteractiveShowcase.tsx` |
