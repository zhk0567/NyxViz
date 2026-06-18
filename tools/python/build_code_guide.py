#!/usr/bin/env python3
"""Generate defense code guide chapters 10a-10e with real source excerpts."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs" / "submission" / "guide"


def read_lines(rel: str, start: int, end: int) -> str:
    path = ROOT / rel.replace("/", "\\") if "\\" not in rel else ROOT / rel
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").splitlines()
    chunk = lines[start - 1 : end]
    return "\n".join(chunk)


def block(rel: str, start: int, end: int) -> str:
    code = read_lines(rel, start, end)
    return f"```{start}:{end}:{rel}\n{code}\n```"


def section(
    title: str,
    rel: str,
    purpose: str,
    why: str,
    start: int,
    end: int,
    io: str,
    script: str,
    qa: str = "",
) -> str:
    parts = [
        f"## {title}",
        "",
        f"**路径**：[`{rel}`](../../../{rel})",
        "",
        f"**职责**：{purpose}",
        "",
        f"**为什么选这段**：{why}",
        "",
        block(rel, start, end),
        "",
        f"**输入 / 输出**：{io}",
        "",
        f"**答辩 30 秒**：{script}",
    ]
    if qa:
        parts.extend(["", f"**评委追问**：{qa}"])
    parts.append("")
    return "\n".join(parts)


def header(num: str, title: str, back: str = "./10-答辩代码讲解.md") -> str:
    return f"""# {num} · {title}

[← 10 答辩代码讲解]({back}) · [← 主索引](../NyxViz_零基础完全解读.md)

---

"""


def write_10a() -> None:
    body = header("10a", "体渲染与 VTK 代码")
    body += """## 数据流总览

```mermaid
sequenceDiagram
  participant dat as Nyx_dat
  participant loader as nyxLoader
  participant worker as vtkConvert_worker
  participant vtk as VolumeScene
  participant tf as transferFunction
  dat --> loader --> worker --> vtk
  tf --> vtk
```

---

"""
    sections = [
        ("nyxLoader.ts — 加载 .dat", "src/data/nyxLoader.ts",
         "从 `public/Nyx/` fetch 单步 128³ float32，z-fast 布局缓存。",
         "答辩「数据从哪来」必指 `flatIndex` 与 `loadTimestep`。",
         9, 12, "输入 URL → 输出 `Float32Array`（2,097,152）",
         "赛题 `.dat` 按 z 最快顺序存储，我们用 `flatIndex` 做索引，fetch 后缓存在 Map 里避免重复下载。"),
        ("nyxLoader.ts — loadTimestep", "src/data/nyxLoader.ts",
         "异步加载并校验体素数量。",
         "展示 fetch → ArrayBuffer → Float32Array 完整链路。",
         71, 88, "timestep 整数 → Promise<Float32Array>",
         "换时间步就是换 URL 拉 4MB 左右的二进制，校验长度必须是 128³。"),
        ("vtkLayout.ts — 轴重排", "src/data/vtkLayout.ts",
         "预计算 z-fast → vtk x-fast 索引表，Worker 与主线程共用。",
         "解释 Worker 只做重排、不做科学计算。",
         3, 20, "z-fast Float32Array → vtk 布局 Float32Array",
         "赛题是 z-fast，vtk.js 要 i-fast；启动时用三重循环生成 210 万项查找表，转换时 O(n) 拷贝。"),
        ("vtkConvert.worker.ts", "src/workers/vtkConvert.worker.ts",
         "Web Worker 内执行轴重排，避免主线程卡顿。",
         "文件短，整段可读，适合答辩背诵。",
         1, 20, "postMessage buffer → 重排后 buffer（transferable）",
         "百万体素重排放在 Worker，postMessage 用 transferable 零拷贝回主线程。"),
        ("vtkConvert.ts — Worker 调度", "src/data/vtkConvert.ts",
         "主线程管理 Worker 单例、任务队列与按 timestep 缓存。",
         "`ensureWorker` + `enqueueConvert` 是性能关键。",
         31, 54, "z-fast 数组 → Promise<vtk 标量数组>",
         "主线程只调度：有缓存直接返回，否则 postMessage 给 Worker，回调里写入 timestep 缓存。"),
        ("colormap.ts — 宇宙色标", "src/viz/colormap.ts",
         "cosmic / cinematic 色标控制点，TF、Canvas、CSS 图例共用。",
         "保证网页、配图、图例颜色一致。",
         6, 38, "归一化 t∈[0,1] → RGB",
         "色标不是随便调的，是共享常量；传递函数和 2D 投影都 `sampleColormap`。"),
        ("tfDomain.ts — 全局域", "src/viz/tfDomain.ts",
         "交互页固定全域 p01–p99，截图页可用逐步域。",
         "解释条带图与网页颜色差异的根因。",
         43, 56, "timeline.json → `{ min, max, useLogScale }`",
         "交互演示用百步 p01–p99 包络做 log 域，保证换步可比；截图演化条带另用 `getGlobalMorphCaptureProfile`。"),
        ("transferFunction.ts — 刷选高亮透明度", "src/volume/transferFunction.ts",
         "当 `highlightMin/Max` 存在时重写 opacity 控制点，刷选区间更亮。",
         "任务四联动体渲染的核心。",
         128, 171, "密度域 + brush 区间 → vtk PiecewiseFunction",
         "有刷选时不用默认 cinematic 曲线，而是在 highlight 区间把 alpha 拉到 0.55–0.98，void 区几乎透明。"),
        ("transferFunction.ts — 组装 CTF/OTF", "src/volume/transferFunction.ts",
         "导出 `buildColorTransferFunction` / `buildOpacityTransferFunction`。",
         "VolumeScene 每次 TF 更新都调这两个工厂。",
         181, 195, "TransferFunctionOptions → vtk 对象",
         "颜色用 cosmic/cinematic 控制点映射到 log 域密度；透明度分标准/电影/刷选三种模式。"),
        ("renderSpec.ts — 质量档位", "src/volume/renderSpec.ts",
         "sampleDistance、maximumSamplesPerRay 等 GPU 采样参数。",
         "解释录屏 60fps 与高清静帧的取舍。",
         59, 90, "quality 字符串 → 采样预设对象",
         "video 档降低每射线采样数，interactive 更密，presentation/cinematic 用于静帧和答辩特写。"),
        ("VolumeScene.tsx — VTK 管线初始化", "src/volume/VolumeScene.tsx",
         "创建 vtkImageData、VolumeMapper、CTF/OTF、三光源。",
         "答辩「怎么画 3D」指这段 useEffect。",
         427, 461, "空体数据 → 完整 vtk 渲染上下文",
         "组件挂载时建 vtk 管线：128³ imageData、光线投射 mapper、RGB+opacity 传递函数、Phong 风格多光源。"),
        ("VolumeScene.tsx — 交互降采样", "src/volume/VolumeScene.tsx",
         "拖动相机时切 interactive/video 采样，静止后恢复。",
         "展示性能优化不是黑魔法。",
         289, 313, "performanceMode + quality → mapper 采样参数",
         "拖相机时强制低密度采样，松手后按 quality 档恢复；录屏模式用 VIDEO_DRAG_SAMPLING 常量。"),
        ("adaptiveVolumeSampling.ts", "src/volume/adaptiveVolumeSampling.ts",
         "根据相机 zoom 动态调整 sampleDistance。",
         "聚焦 filament 时提高细节。",
         1, 42, "mapper + quality + zoomRatio → 修改采样",
         "放大时缩短 sample distance，让细丝更清晰；缩小用粗采样保帧率。"),
        ("volumeQualityCache.ts", "src/volume/volumeQualityCache.ts",
         "记录某 timestep 是否已达 presentation 画质。",
         "scene 切换时跳过草稿阶段。",
         1, 14, "timestep → boolean 缓存",
         "首帧 draft 快速出图，静止 1.8s 升 presentation；缓存避免重复草稿。"),
        ("fitVolumeCamera.ts", "src/volume/fitVolumeCamera.ts",
         "按包围盒与 aspect 设置相机位置。",
         "保证 128³ 立方体完整入画。",
         1, 40, "renderer + imageData + aspect + zoom → 相机参数",
         "用 vtk 的 resetCamera 思路，按域长 14.245 Mpc/h 与 zoom 系数摆放相机。"),
        ("volumeFocusPick.ts — 射线拾取", "src/volume/volumeFocusPick.ts",
         "屏幕点击 → 世界射线 → 沿射线找密度峰值。",
         "探索页点击聚焦 filament 用。",
         92, 130, "体数据 + 射线 → 峰值世界坐标",
         "把屏幕坐标反投影成射线，在 128³ 网格上步进采样，找超过阈值的密度峰作为飞行目标。"),
        ("DensityColorLegend.tsx", "src/volume/DensityColorLegend.tsx",
         "CSS 渐变图例，与 colormap 一致。",
         "右栏色标与 3D 颜色对齐。",
         1, 45, "min/max + style → DOM 渐变",
         "图例不是截图，是 `cinematicLegendGradient` 生成的 CSS linear-gradient。"),
        ("TransferFunctionControls.tsx", "src/volume/TransferFunctionControls.tsx",
         "探索面板滑条写 `tfParams` 到 store。",
         "长卷 app 微调透明度/增益。",
         1, 50, "用户拖动 → setTfParams",
         "三个滑条改 opacityScale、densityGain、highlightBoost，VolumeScene 监听后重填传递函数。"),
        ("PosterHeroVolume.tsx", "src/dashboard/PosterHeroVolume.tsx",
         "长卷海报区嵌入 VolumeScene。",
         "代表图网页截图的体渲染入口。",
         1, 55, "timeline + timestep → 海报主视觉",
         "Cosmic 长卷顶部用同一 VolumeScene，参数来自 `getCinematicDefaultProfile`。"),
        ("capture/main.tsx", "src/capture/main.tsx",
         "Playwright 无头截图专用入口，TF 随步变化。",
         "五帧条带与网页 TF 差异的解释落点。",
         1, 60, "URL 参数 timestep/scene → PNG",
         "capture 路由读 sceneId，调用 `resolveVolumeVisualProfile` 用演化截图配置，不是交互全局域。"),
    ]
    for s in sections:
        body += section(*s)
    (GUIDE / "10a-体渲染与VTK代码.md").write_text(body, encoding="utf-8")
    print(f"10a: {len(body.splitlines())} lines")


def write_10b() -> None:
    body = header("10b", "直方图与 D3 代码")
    sections = [
        ("statsLoader.ts", "src/data/statsLoader.ts",
         "加载 render_spec、validation、brush_validation 等 JSON。",
         "录屏 validate 场景 KPI 来源。",
         64, 81, "fetch stats/*.json → VideoStatsBundle",
         "前端 KPI 和直方图共用 timeline；录屏验证页另外读 brush_validation.json。"),
        ("chartTheme.ts", "src/histogram/chartTheme.ts",
         "D3 轴、网格、刷选柄的颜色与字号 token。",
         "保证录屏页与 app 直方图视觉一致。",
         1, 50, "无外部输入 → CSS 变量/常量",
         "主题集中定义，改一处全站直方图跟色。"),
        ("useChartSize.ts", "src/hooks/useChartSize.ts",
         "ResizeObserver 测量容器，返回 width/height。",
         "D3 需要像素尺寸才能 scale。",
         1, 40, "ref 指向 DOM → { width, height }",
         "容器大小变时自动重绘直方图，避免拉伸模糊。"),
        ("DensityHistogram.tsx — D3 bin 绘制", "src/histogram/DensityHistogram.tsx",
         "用预计算 histogram 数组画 log 轴柱状图。",
         "任务三核心组件。",
         41, 90, "stats.histogram + logBinEdges → SVG bars",
         "不在浏览器里重算 bin，只把 JSON 里的 128 个概率质量画成矩形。"),
        ("DensityHistogram.tsx — brush 写 store", "src/histogram/DensityHistogram.tsx",
         "D3 brush 事件把选中密度区间写入 `setBrushRange`。",
         "统计→空间联动的入口。",
         152, 166, "拖拽像素区间 → brushRange {min,max}",
         "用户框选直方图横轴，brush end 事件把 log 域反算成物理密度，写入全局 store。"),
        ("HistogramOverlay.tsx", "src/histogram/HistogramOverlay.tsx",
         "多时间步直方图叠加、void 标注层。",
         "录屏 task3 与静态五步叠加对应。",
         1, 70, "多步 histogram[] → 半透明折线叠加",
         "每一步一条半透明轮廓，展示分布随时间漂移，不是重新分箱。"),
        ("BrushHistogramPreview.tsx", "src/histogram/BrushHistogramPreview.tsx",
         "刷选区间在迷你直方图上的高亮带。",
         "右栏预览刷选位置。",
         1, 50, "brushRange + histogram → 高亮 SVG",
         "小图只画刷选带，帮助评委看到当前区间在分布的哪一段。"),
        ("TimelineMetrics.tsx", "src/histogram/TimelineMetrics.tsx",
         "逐步 KPI 迷你条（mean/σ 等）。",
         "演化面板辅助读数。",
         1, 55, "timeline.timesteps → 小 multiples",
         "把百步 mean 或 span 画成 sparkline，辅助讲任务二。"),
        ("PosterTrendChart.tsx", "src/dashboard/PosterTrendChart.tsx",
         "长卷 σ%、p99−p01 趋势 SVG。",
         "任务二叙事主图网页版。",
         1, 70, "storyMetrics → 折线路径",
         "从 timeline 算 σ 增长 15.4% 等，画在 Cosmic 长卷里，数字与 Word 一致。"),
    ]
    for s in sections:
        body += section(*s)
    (GUIDE / "10b-直方图与D3代码.md").write_text(body, encoding="utf-8")
    print(f"10b: {len(body.splitlines())} lines")


def write_10c() -> None:
    body = header("10c", "刷选与 Worker 代码")
    sections = [
        ("useAppStore.ts", "src/store/useAppStore.ts",
         "Zustand 全局状态：timestep、brushRange、densityData、tfParams。",
         "三栏联动的唯一状态源。",
         5, 37, "各组件 set/get → 同步 UI",
         "刷选区间、当前步、体数据都放在 store，体渲染和直方图只订阅不互传 props。"),
        ("brushPreset.ts", "src/data/brushPreset.ts",
         "Top 1% / Filament / Bottom 1% 预设区间定义与匹配。",
         "点按钮刷选的实现入口。",
         1, 60, "stats 分位数 → BrushRange",
         "预设不是手填数字，而是用当前步 p99、p01、p90 等算密度区间。"),
        ("useDashboardInteraction.ts — 预设刷选", "src/dashboard/useDashboardInteraction.ts",
         "`applyTop1` 等回调写 brushRange 并算精确 KPI。",
         "答辩联动逻辑最集中文件。",
         156, 172, "preset id + stats → setBrushRange + brushedCount",
         "点 Top 1% 时直接用 tailMassAboveP99 乘体素总数得精确计数，不走采样。"),
        ("useDashboardInteraction.ts — Worker 扫描", "src/dashboard/useDashboardInteraction.ts",
         "自定义 brush 时调 scanBrushRangeAsync。",
         "解释 KPI 采样与全场高亮的区别。",
         203, 237, "densityData + range → brushedCount（采样）",
         "宽区间拖拽时 Worker stride 扫描，maxPoints 8000 早停；预设仍用 JSON 精确值。"),
        ("useDashboardInteraction.ts — highlight 导出", "src/dashboard/useDashboardInteraction.ts",
         "brushRange 转 highlightMin/Max 给 VolumeScene。",
         "连接 store 与体渲染。",
         240, 243, "brushRange → { highlightMin, highlightMax }",
         "useMemo 把 store 区间转成传递函数参数，体渲染和投影读同一份。"),
        ("brushScan.ts", "src/data/brushScan.ts",
         "封装 brushScan.worker 的 Promise API。",
         "主线程不阻塞。",
         1, 45, "buffer + min/max → Promise<points[]>",
         "把 Float32Array 传给 Worker，返回刷选到的体素坐标列表用于 KPI。"),
        ("brushEstimate.ts", "src/data/brushEstimate.ts",
         "无体数据时用直方图积分估计刷选计数。",
         "静态图模式 fallback。",
         1, 40, "histogram + range → 估计体素数",
         "只有 JSON 没有 .dat 时，对 bin 概率质量积分估计占比。"),
        ("brushScan.worker.ts", "src/workers/brushScan.worker.ts",
         "三重循环 stride 扫描 + maxPoints 早停。",
         "文件短且逻辑完整，适合现场读代码。",
         1, 42, "ArrayBuffer + 阈值 → points[]",
         "三层 for 遍历 128³，密度落在区间内就 push，达到 maxPoints 立即 break。"),
        ("projectionAsync.ts", "src/data/projectionAsync.ts",
         "调度 projection.worker 做 XY 最大密度投影。",
         "BandPreviewCanvas 的数据源。",
         1, 42, "体数据 + axis → Promise<投影数组>",
         "投影在 Worker 里做 max-intensity，主线程只贴 Canvas。"),
        ("projection.worker.ts", "src/workers/projection.worker.ts",
         "沿 z 轴取最大密度得到 128×128 投影。",
         "金斑高亮的 2D 来源。",
         1, 55, "体数据 buffer → 投影 buffer",
         "每个 (x,y) 在 z 方向取 max，得到与体渲染一致的 XY 视图。"),
    ]
    for s in sections:
        body += section(*s)
    (GUIDE / "10c-刷选与Worker代码.md").write_text(body, encoding="utf-8")
    print(f"10c: {len(body.splitlines())} lines")


def find_export_line(rel: str) -> tuple[int, int]:
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if re.match(r"export (function|const|class|interface)", line):
            start = i + 1
            end = min(start + 35, len(lines))
            return start, end
    return 1, min(40, len(lines))


def auto_section(rel: str, purpose: str, script: str) -> str:
    start, end = find_export_line(rel)
    name = Path(rel).name
    return section(
        name,
        rel,
        purpose,
        "展示该组件/export 入口与 props。",
        start,
        end,
        "见源码 props / 父组件传参",
        script,
    )


def write_10d() -> None:
    body = header("10d", "投影空间与录屏组件代码")
    body += "## 空间与投影\n\n"
    spatial = [
        ("src/spatial/BandPreviewCanvas.tsx", "2D 密度带 Canvas + brush 高亮金斑。", "任务四右栏空间视图。"),
        ("src/spatial/BrushedPoints.tsx", "刷选体素 scatter 点云。", "验证刷选空间分布。"),
        ("src/spatial/TriaxialSlices.tsx", "三正交切片。", "探索页空间剖面。"),
        ("src/spatial/DensityProjection.tsx", "密度投影 React 封装。", "复用 projection worker。"),
        ("src/hooks/useSharedProjection.ts", "多组件共享投影缓存。", "避免重复 Worker 计算。"),
    ]
    for rel, purpose, script in spatial:
        body += auto_section(rel, purpose, script)

    body += "## 录屏壳层\n\n"
    shell = [
        ("src/dashboard/VideoDashboard.tsx", "录屏页根组件，调 useDashboardInteraction。", "video.html 入口。"),
        ("src/dashboard/VideoSceneLayout.tsx", "三栏布局分发 ix 状态。", "11 段 scene 共用壳。"),
        ("src/dashboard/VideoDashboardLayout.tsx", "顶栏 + 场景区框架。", "录屏布局 CSS grid。"),
        ("src/dashboard/VideoApp.tsx", "Video 路由挂载。", "与 app 分离的入口。"),
        ("src/video/sceneRegistry.ts", "11 段 scene 元数据：默认步、brush、布局。", "改录屏默认值看这里。"),
        ("src/video/useVideoScene.ts", "解析 URL scene 参数。", "OBS 录屏切 scene。"),
        ("src/video/narrationLabels.ts", "旁白 UI 标签文案。", "与 TTS 稿对齐。"),
    ]
    for rel, purpose, script in shell:
        body += auto_section(rel, purpose, script)

    body += "## 录屏 layout\n\n"
    for rel in [
        "src/dashboard/video-scenes/layout/types.ts",
        "src/dashboard/video-scenes/layout/shared.ts",
        "src/dashboard/video-scenes/layout/VideoLeftColumn.tsx",
        "src/dashboard/video-scenes/layout/VideoCenterColumn.tsx",
        "src/dashboard/video-scenes/layout/VideoRightColumn.tsx",
        "src/dashboard/video-scenes/layout/VideoFindingsRow.tsx",
    ]:
        body += auto_section(rel, f"录屏三栏布局：{Path(rel).stem}", "左中右/findings 列组装。")

    body += "## 录屏 scene 组件\n\n"
    scenes = [
        "VideoSceneChrome", "VideoSceneNav", "VideoKpiStrip", "VideoFindingsStrip",
        "VideoSpatialPanel", "VideoVoidPanel", "VideoVoidScene", "VideoMorphPanel",
        "VideoEvolutionPanel", "VideoBrushGuidePanel", "VideoBrushValidationPanel",
        "VideoHistMethodStrip", "VideoRenderSpecPanel", "VideoFigureStrip", "VideoCaseCards",
        "VideoSceneRecordBrowse", "VideoEvolutionFigurePanel", "VideoValidateFigureColumn",
        "VideoDashboardHeader",
    ]
    for name in scenes:
        rel = f"src/dashboard/video-scenes/{name}.tsx"
        if name == "VideoKpiStrip":
            rel = "src/dashboard/VideoKpiStrip.tsx"
        elif name == "VideoFindingsStrip":
            rel = "src/dashboard/VideoFindingsStrip.tsx"
        elif name == "VideoDashboardHeader":
            rel = "src/dashboard/VideoDashboardHeader.tsx"
        path = ROOT / rel
        if path.exists():
            body += auto_section(rel, f"录屏场景组件 {name}。", f"scene 段对应 UI：{name}。")

    body += "## 辅助 viz 组件\n\n"
    aux = [
        ("src/components/StarfieldBackground.tsx", "星空 CSS 粒子背景。", "录屏 intro 氛围。"),
        ("src/components/ImageLightbox.tsx", "配图点击放大。", "发现卡插图。"),
        ("src/dashboard/HorizontalColorLegend.tsx", "水平色标。", "KPI 条旁密度图例。"),
        ("src/dashboard/VerticalColorLegend.tsx", "垂直色标。", "体渲染旁图例。"),
        ("src/dashboard/VideoBrushPreviews.tsx", "刷选预设缩略预览。", "task4-brush 左栏。"),
    ]
    for rel, purpose, script in aux:
        body += auto_section(rel, purpose, script)

    body += "## Cosmic 长卷 viz 组件\n\n"
    cosmic = [
        ("src/dashboard/StoryKpiStrip.tsx", "故事 KPI 条。", "长卷任务二摘要。"),
        ("src/dashboard/TimestepKpiCards.tsx", "单步 KPI 卡。", "当前步 mean/σ。"),
        ("src/dashboard/HeroMetaBar.tsx", "主视觉 meta 条。", "海报区标注。"),
        ("src/dashboard/EvolutionThumbnails.tsx", "百步缩略图条。", "task1-morph 切步。"),
        ("src/dashboard/DiscoveryCards.tsx", "四发现卡。", "叙事结论。"),
        ("src/dashboard/SparklineTriplet.tsx", "三联 sparkline。", "辅助趋势。"),
        ("src/dashboard/PhaseTrack.tsx", "演化阶段轨道。", "时间叙事。"),
        ("src/dashboard/PosterFlowchart.tsx", "方法流程图 SVG。", "附录流程可视化。"),
        ("src/dashboard/CosmicPosterLayout.tsx", "长卷整体布局。", "app.html 结构。"),
        ("src/dashboard/InteractiveBrushLab.tsx", "刷选实验浮层。", "探索交互。"),
        ("src/dashboard/BrushVerifySection.tsx", "刷选验证区块。", "离线指标展示。"),
    ]
    for rel, purpose, script in cosmic:
        if (ROOT / rel).exists():
            body += auto_section(rel, purpose, script)

    (GUIDE / "10d-投影空间与录屏组件代码.md").write_text(body, encoding="utf-8")
    print(f"10d: {len(body.splitlines())} lines")


def write_10e() -> None:
    body = header("10e", "Python 配图代码")
    sections = [
        ("precompute.py — load_volume", "tools/python/precompute.py",
         "读取单步 .dat 为 numpy 128³。", "统计真源生成入口。",
         1, 45, ".dat → ndarray", "和前端一样 fromfile float32，reshape 128³ 后算 mean/std/分位数。"),
        ("precompute.py — 直方图分箱", "tools/python/precompute.py",
         "log 域 128 bins 概率质量。", "任务三 JSON 字段来源。",
         80, 130, "体数据 → histogram + logBinEdges", "每步把体素分到 log 等距 bin，存概率质量供 D3 直接画。"),
        ("spatial_to_stats.py", "tools/python/spatial_to_stats.py",
         "空间统计与 P88 反查。", "task2-spatial 静态图。",
         1, 50, "体数据 → 空间指标 JSON/图", "从亮脊投影反查密度带，生成空间验证配图。"),
        ("brush_analysis.py", "tools/python/brush_analysis.py",
         "离线刷选召回/精确率。", "task4-validate KPI。",
         1, 55, "体数据 + 阈值 → brush_validation.json", "Top 1% 密度集与 filament 几何代理对比，得到召回 100%、精确率 27.6%。"),
        ("render_spec.py", "tools/python/render_spec.py",
         "导出 render_spec.json 相机/光照。", "与前端 renderSpec.ts 对齐。",
         1, 50, "常量 → public/stats/render_spec.json", "Python 与 TypeScript 各一份常量，保证截图与网页相机一致。"),
        ("projection_render.py", "tools/python/projection_render.py",
         "matplotlib XY 最大密度投影。", "Word 空间配图。",
         1, 55, ".dat → PNG 投影", "离线用 numpy 做 max-Z 投影，色标调 viz_style。"),
        ("viz_style.py", "tools/python/viz_style.py",
         "matplotlib rcParams 与赛题色板。", "全部配图统一风格。",
         1, 60, "无 → 全局样式", "字体、背景、cosmic 色表在这里设，generate_figures 复用。"),
        ("generate_figures.py — compose_narrative_poster", "tools/python/generate_figures.py",
         "四幕叙事代表图 PIL 合成。", "submission_representative 来源。",
         4238, 4285, "截图 PNG → task6_story_poster.png", "把 app 截图、发现卡、配图按叙事幕次竖拼，动态算画布宽。"),
        ("generate_figures.py — findings 卡", "tools/python/generate_figures.py",
         "第 4 幕发现卡铺满。", "代表图第 4 节。",
         4130, 4185, "指标 dict → PIL 卡片", "从 timeline 读 σ%、void 等，画四张发现卡。"),
        ("compose_representative_poster.py", "tools/python/compose_representative_poster.py",
         "npm run capture-app-poster 流水线。", "一键生成代表图。",
         1, 45, "Playwright 截图 → generate_figures", "先截 app 海报，再调 compose_narrative_poster。"),
    ]
    for s in sections:
        try:
            body += section(*s)
        except Exception as e:
            body += f"## {s[0]}\n\n> 摘录待补：{e}\n\n"
    (GUIDE / "10e-Python配图代码.md").write_text(body, encoding="utf-8")
    print(f"10e: {len(body.splitlines())} lines")


def main() -> None:
    write_10a()
    write_10b()
    write_10c()
    write_10d()
    write_10e()
    print("Done.")


if __name__ == "__main__":
    main()
