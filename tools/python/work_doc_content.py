"""ChinaVis-style work document content: cover + overview + tasks + appendix."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from spatial_to_stats import filament_density_band, load_volume_dat

ROOT = Path(__file__).resolve().parents[2]
STATS = ROOT / "public" / "stats" / "timeline.json"
NYX = ROOT / "Nyx"
TEAM_CONFIG = ROOT / "docs" / "competition" / "team.json"
TEAM_CONFIG_EXAMPLE = ROOT / "docs" / "competition" / "team.json.example"


@dataclass
class Heading:
    text: str
    level: int


@dataclass
class Text:
    content: str
    indent: bool = True


@dataclass
class Figure:
    file: str
    caption: str
    width_cm: float = 15.0


@dataclass
class Table:
    caption: str
    headers: list[str]
    rows: list[list[str]]


Block = Heading | Text | Figure | Table


@dataclass
class CoverInfo:
    team_name: str
    member_line_1: str
    member_lines_extra: str
    consistent_with_registration: str
    student_team: str
    tools: str
    person_days: str
    publish_ok: str


def load_team_config() -> CoverInfo:
    path = TEAM_CONFIG if TEAM_CONFIG.exists() else TEAM_CONFIG_EXAMPLE
    data = json.loads(path.read_text(encoding="utf-8"))
    extras = data.get("member_lines_extra", "")
    if isinstance(extras, list):
        extras = "\n".join(extras)
    return CoverInfo(
        team_name=data.get("team_name", "学校-姓名-赛道1-II"),
        member_line_1=data.get("member_line_1", ""),
        member_lines_extra=extras,
        consistent_with_registration=data.get("consistent_with_registration", "是"),
        student_team=data.get("student_team", "是"),
        tools=data.get("tools", ""),
        person_days=data.get("person_days", ""),
        publish_ok=data.get("publish_ok", "是"),
    )


def _steps(timeline: dict) -> dict[int, dict]:
    return {s["timestep"]: s for s in timeline["timesteps"]}


def _filament_band() -> tuple[float, float]:
    vol_path = NYX / "0099.dat"
    if vol_path.exists():
        lo, hi, _ = filament_density_band(load_volume_dat(vol_path))
        return lo, hi
    return 11.23, 12.16


def build_blocks(timeline: dict) -> list[Block]:
    steps = _steps(timeline)
    s0, s99 = steps[0], steps[99]
    span0 = s0["p99"] - s0["p01"]
    span99 = s99["p99"] - s99["p01"]
    sigma_pct = (s99["std"] - s0["std"]) / s0["std"] * 100
    span_pct = (span99 - span0) / span0 * 100
    band_lo, band_hi = _filament_band()
    gmin, gmax = timeline["globalMin"], timeline["globalMax"]
    bins = timeline["binCount"]
    tail_vol = s99["tailMassAboveP99"] * 100
    mass_above = (s99.get("massFractionAboveP99") or 0) * 100
    mass_below = (s99.get("massFractionBelowP01") or 0) * 100

    blocks: list[Block] = []

    # ── 0 系统概览 ──
    blocks.append(Heading("0  系统概览", 1))
    blocks.append(
        Figure(
            "task6_story_poster.png",
            "NyxViz「宇宙网诞生记」全景：体渲染、百步统计、刷选验证与科学发现（拼接长图）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "「NyxViz：宇宙网诞生记」面向 Nyx 宇宙学模拟输出的 128³ 重子气体密度场（100 个时间步，"
            f"全域 ρ∈[{gmin:.2f}, {gmax:.2f}]），旨在从可视化与可视分析角度揭示引力团块化过程中，"
            "由近乎均匀的微小涨落向 void—filament—node 宇宙网拓扑分化的完整叙事。"
            "系统以三栏交互仪表盘（/app.html、/video.html）与成果长卷（/）协同呈现，"
            "各视图通过统一色标、共享 timeline.json 统计源与刷选状态实现联动。"
        )
    )
    blocks.append(
        Text(
            "A. 体渲染视图：基于 vtk.js 的 GPU 光线投射，居中常驻展示当前时间步的三维密度场；"
            "cosmic 传递函数在 log 域按全域 p01–p99 映射，使低密度 void 与高密度 filament 同屏可辨。"
            "B. 时序 log 直方图：D3.js 绘制当前步密度分布，支持拖拽框选密度区间，并与体渲染高亮联动。"
            "C. 统计指标时序：σ(t)、p99−p01 分位跨度、Top 1% 尾区变化等迷你趋势图，量化演化速率。"
            "D. 相空间刷选：预设 Top 1%、90–99% 纤维带、Bottom 1%，一键刷选右尾/左尾并在体素级高亮。"
            "E. 密度投影：Canvas 2D 最大密度投影（XY），以金色标出刷选体素或 filament 亮脊。"
            "F. 发现叙事区：四张发现卡串联体渲染、统计曲线、质量占比与刷选验证，页脚给出科学结论。"
        )
    )
    blocks.append(
        Text(
            "本答卷前四章逐题解答赛题任务一至四，第五章综合归纳科学发现与启示；"
            "附录给出分析流程、各视图可视设计说明及数据预计算管线。"
            "文中配图多为 matplotlib 或 Playwright 生成的拼接图，子图含义在图注中逐一说明。"
        )
    )

    # ── 任务一 ──
    blocks.append(Heading("1、体数据渲染与密度演化", 1))
    blocks.append(Heading("1.1  视图简介", 2))
    blocks.append(
        Text(
            "本题涉及体渲染视图与五时刻演化条带。数据为 Nyx 官方 128³ 重子气体密度（仅气体，非暗物质），"
            "100 步 t=0…99，小端 float32，体素索引 z→y→x。"
            "渲染管线基于 vtk.js GPU 光线投射，传递函数采用宇宙学预设 cosmic："
            "在 log 域按全域 p01–p99 映射密度到颜色与不透明度，并启用 Phong 着色以突出 filament 脊线。"
            "为便于跨时刻对比，选取 t=0、25、50、75、99 五帧，固定相机位姿与色标，"
            "以 1920×1080 输出体渲染单帧与五联条带拼接图（task1_vol_strip.png）。"
        )
    )
    blocks.append(Heading("1.2  案例分析", 2))
    blocks.append(
        Text(
            "（1）从均匀雾状到宇宙网拓扑的三阶段演化。"
            "在体渲染视图中，t=0 时整体呈均匀雾状，filament 对比度弱，"
            f"均值约 {s0['mean']:.4f}、σ 仅 {s0['std']:.4f}，尚处于涨落初生的平滑阶段。"
            "拖动时间轴至 t=25–50，丝状结构逐渐连通，低密度 void 区域扩大，σ 由 0.43 升至 0.47 附近。"
            f"至 t=99，宇宙网拓扑最为清晰：高密度脊线与节点形成亮带，σ 达 {s99['std']:.4f}、"
            f"p99={s99['p99']:.4f}，与右尾增厚及 max={s99['max']:.4f} 一致。"
            "五帧统一色标后，void—filament—node 的空间布局由模糊走向可辨，"
            "为后续直方图统计与刷选验证提供了直观的全局参照。"
        )
    )
    blocks.append(
        Figure(
            "task1_vol_strip.png",
            "五时刻体渲染条带（左→右 t=0/25/50/75/99，统一 log 色标与相机）",
            16.0,
        )
    )
    blocks.append(
        Table(
            caption="五代表步密度统计量",
            headers=["时间步", "均值", "标准差 σ", "p99", "最大值"],
            rows=[
                [
                    str(t),
                    f"{steps[t]['mean']:.4f}",
                    f"{steps[t]['std']:.4f}",
                    f"{steps[t]['p99']:.4f}",
                    f"{steps[t]['max']:.4f}",
                ]
                for t in [0, 25, 50, 75, 99]
            ],
        )
    )
    blocks.append(
        Text(
            "（2）log 域色标对 IGM 大动态范围的压缩作用。"
            "表 1 显示均值略降而 σ 与 p99 缓升，说明物质由相对均匀分布转向分化："
            "大部分体积仍处中低密区，但极少数体素密度持续抬升，在体渲染中即对应后期更亮、更细的 filament 网络。"
            "传递函数在 log 域映射可压缩 IGM 大动态范围，使低密度 void 与高密度脊线在同一色标下同时可见；"
            "若采用线性映射，filament 细节将被中低密背景淹没。"
            "图 2 首屏海报进一步展示 t=99 代表帧、竖向色标与 Nyx 元数据条，便于读者建立尺度感。"
        )
    )
    blocks.append(
        Figure(
            "task1_hero_poster.png",
            "t=99 体渲染首屏海报：主视角 + log 密度色标 + 模拟元数据",
            15.0,
        )
    )

    # ── 任务二 ──
    blocks.append(Heading("2、宇宙密度演化规律归纳", 1))
    blocks.append(Heading("2.1  视图简介", 2))
    blocks.append(
        Text(
            "本题结合百步全域统计曲线、代表步直方图叠加与体渲染对照。"
            "数据来自 Nyx 宇宙学流体模拟：基于 AMReX 自适应网格的引力流体计算，"
            "128³ 子体积记录星系际介质（IGM）重子气体密度，而非暗物质。"
            "100 个时间步对应引力不稳定下，由近乎均匀的微涨落向 void—filament—node 拓扑分化的典型过程。"
            "precompute.py 对每步计算 mean、σ、分位数、偏度及尾区体积/质量占比，写入 timeline.json；"
            "generate_figures.py 绘制四联演化故事板（task2_evolution_story.png）。"
        )
    )
    blocks.append(Heading("2.2  案例分析", 2))
    blocks.append(
        Text(
            "（1）团块化：σ 与分位跨度同步走阔。"
            f"在「演化规律四联图」中，σ(t) 子图显示标准差由 {s0['std']:.4f} 升至 {s99['std']:.4f}（+{sigma_pct:.1f}%）；"
            f"p99−p01 分位跨度由 {span0:.3f} 增至 {span99:.3f}（+{span_pct:.1f}%），"
            "表明高低密度区域分化加剧，符合「均匀 IGM→纤维/节点」团块化图像。"
            "偏度子图维持右偏，说明分布尾翼持续增厚而非对称展宽。"
            "这一趋势与任务三 100 步直方图序列相互印证，避免仅凭单帧体渲染得出主观结论。"
        )
    )
    blocks.append(
        Figure(
            "task2_evolution_story.png",
            "100 步全域统计四联图：分位跨度、σ、≥p99 体积占比、偏度（2×2 拼接）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "（2）少数致密体素承载可见宇宙网结构。"
            f"四联图中「≥p99 体积占比」曲线稳定在约 {tail_vol:.2f}% 量级，"
            "即仅约 1% 体素处于极高密度尾，却在体渲染中对应全部可见亮脊与节点。"
            "进一步查看代表步直方图叠加（图 4）：t=0/25/50/75/99 五步曲线显示主峰略移、右尾持续抬升，"
            "低密度 void 与高密度 peak 两极并存——这正是赛题所描述的「密度分布两极化」。"
            "绝大部分体积仍为稀疏 IGM，视觉上的 filament 网络由极少数高密度体素承载，"
            "统计上的右偏与空间上的丝状结构因此并不矛盾。"
        )
    )
    blocks.append(
        Figure(
            "task3_hist_overlay.png",
            "代表步 log 直方图五步叠加（t=0/25/50/75/99，统一分箱）",
            15.0,
        )
    )
    blocks.append(
        Table(
            caption="t=0 与 t=99 演化指标对比",
            headers=["指标", "t=0", "t=99", "变化"],
            rows=[
                ["标准差 σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", f"+{sigma_pct:.1f}%"],
                ["分位跨度 p99−p01", f"{span0:.3f}", f"{span99:.3f}", f"+{span_pct:.1f}%"],
                ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", "右偏维持"],
                [
                    "≥p99 体积占比",
                    f"{s0['tailMassAboveP99'] * 100:.2f}%",
                    f"{tail_vol:.2f}%",
                    "约 1% 量级",
                ],
            ],
        )
    )

    # ── 任务三 ──
    blocks.append(Heading("3、时序密度对数直方图统计", 1))
    blocks.append(Heading("3.1  视图简介", 2))
    blocks.append(
        Text(
            f"本题以 100 步完整 log 直方图序列为核心，分箱数 {bins}，边界 [{gmin:.4f}, {gmax:.4f}]（全域 min/max）。"
            "分箱中心取相邻边界几何均值，纵轴为归一化频数 count/N；"
            "同步预计算每步 mean、σ、p01/p50/p99、偏度 skew，供交互页 D3 直方图与静态配图共用。"
            "task3_evolution_metrics.png 将 σ、偏度与 p99−p01 绘于同一故事板；"
            "task3_peak_drift.png 追踪主峰（p50 附近）随时间的漂移轨迹。"
        )
    )
    blocks.append(Heading("3.2  案例分析", 2))
    blocks.append(
        Text(
            "（1）主峰漂移与右尾增厚。"
            f"在 metrics 三联拼接图中，σ 曲线整体上升（+{sigma_pct:.1f}%），偏度维持 {s0['skewness']:.4f}→{s99['skewness']:.4f} 的右偏形态，"
            f"p99−p01 分位跨度同步由 {span0:.3f} 扩至 {span99:.3f}。"
            "peak_drift 图进一步显示 log 直方图主峰（p50 附近）随时间略向低密度侧偏移，"
            "而 p99 分位缓升——整体略向 void 偏移的同时，极端高密度体素仍在积累。"
            "这一「主峰略移 + 尾翼抬升」模式，比单帧切片更能说明分布两极化趋势。"
        )
    )
    blocks.append(
        Figure(
            "task3_evolution_metrics.png",
            "σ、偏度与 p99−p01 分位跨度时序（三联横向拼接）",
            16.0,
        )
    )
    blocks.append(
        Figure(
            "task3_peak_drift.png",
            "log 直方图主峰（p50 附近）随时间漂移轨迹",
            14.0,
        )
    )
    blocks.append(
        Text(
            "（2）与赛题描述的对照验证。"
            "赛题指出：早期密度集中于均值附近，后期出现空洞与峰值两极分化。"
            "本工作以完整 100 步直方图序列而非个别时刻证明该趋势。"
            "图 6 故事板将五步直方图叠加、σ/span 迷你趋势与 t=99 四 KPI 合于一张拼接图，"
            "便于在答辩或录屏中一图讲清「定量证据链」。"
            "结合任务一体渲染，可将统计上的右尾增厚与空间上的 filament 亮脊对应起来，"
            "形成从「数字」到「形态」的可检验闭环。"
        )
    )
    blocks.append(
        Figure(
            "task3_story_panel.png",
            "第三节专图：直方图叠加 + σ/span 趋势 + t=99 KPI 条（拼接）",
            16.0,
        )
    )
    blocks.append(
        Table(
            caption="直方图演化要点（t=0→99）",
            headers=["量", "t=0", "t=99", "含义"],
            rows=[
                ["σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", "团块化、涨落扩大"],
                ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", "右尾增厚"],
                ["p50", f"{s0['p50']:.4f}", f"{s99['p50']:.4f}", "主峰略移"],
                ["p99−p01", f"{span0:.3f}", f"{span99:.3f}", "两极分化"],
            ],
        )
    )

    # ── 任务四 ──
    blocks.append(Heading("4、相空间交互刷选可视分析", 1))
    blocks.append(Heading("4.1  视图简介", 2))
    blocks.append(
        Text(
            "本题涉及三栏交互仪表盘：左统计、中体渲染常驻、右刷选控制（/app.html、/video.html）。"
            "log 直方图支持拖拽框选；预设 Top 1%、90–99% 纤维、Bottom 1% 一键刷选。"
            f"Top 1%：ρ≥{s99['p99']:.4f}；纤维：ρ∈[{s99['p90']:.2f},{s99['p99']:.2f}]；"
            f"Bottom 1%：ρ≤{s99['p01']:.4f}。"
            "刷选后 vtk.js 传递函数对命中体素高亮，Canvas 2D 最大密度投影以金色标出刷选体素；"
            "体素扫描在 Web Worker 中执行，相邻时间步 idle 预取以保障播放流畅。"
        )
    )
    blocks.append(Heading("4.2  案例分析", 2))
    blocks.append(
        Text(
            "（1）统计→空间：Top 1% 三联验证。"
            "在直方图上刷选右尾 Top 1% 后，观察 XY 最大密度投影：高亮体素呈丝状/节点状聚集，"
            "而非随机散点；切换至 t=99 体渲染，亮脊位置与刷选高亮区域高度重合。"
            "图 8 三联拼接图从左至右依次为：直方图刷选区间、体渲染刷选高亮、投影金色标记，"
            "三者密度阈值一致，构成「统计→空间」的单屏证据。"
            "Bottom 1% 实验（图 9 双行拼接）则表明低密度尾对应投影中的大面积稀疏区，"
            "与 IGM 占主导体积的物理图像吻合。"
        )
    )
    blocks.append(
        Figure(
            "task4_brush_triptych.png",
            "Top 1% 刷选三联验证：直方图—体渲染—XY 投影（左→右拼接）",
            16.0,
        )
    )
    blocks.append(
        Figure(
            "task4_brush_rows.png",
            "Top 1% 与 Bottom 1% 刷选双行对比（上：高密度尾；下：低密度尾）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "（2）空间→统计：filament 亮脊反查密度带。"
            f"在 t=99 XY 投影上识别 filament 亮脊（投影值≥P88），汇总亮脊像素对应体素密度，"
            f"得 ρ∈[{band_lo:.2f}, {band_hi:.2f}]，位于 p75–p99 右尾，与 Top 1% 刷选区间一致。"
            "在 log 直方图上以金色标注该密度带，完成「先在空间定位结构，再反查统计位置」的路径。"
            "图 10 展示完整链路：投影亮脊→密度带标注→与 Top 1% 阈值对照。"
            "两条路径（统计→空间、空间→统计）形成双向可验证闭环，使用户从「看漂亮图」"
            "升级为「用统计约束空间、用空间检验统计」。"
        )
    )
    blocks.append(
        Figure(
            "task4_spatial_to_stats.png",
            "空间→统计：filament 亮脊识别与直方图密度带反查（拼接）",
            16.0,
        )
    )
    blocks.append(
        Table(
            caption="刷选验证摘要（t=99）",
            headers=["方向", "操作", "空间表现", "密度区间"],
            rows=[
                ["统计→空间", "Top 1% 刷选", "XY 投影丝状/节点聚集", f"ρ≥{s99['p99']:.2f}"],
                ["统计→空间", "Bottom 1% 刷选", "投影稀疏区域", f"ρ≤{s99['p01']:.2f}"],
                [
                    "空间→统计",
                    "亮脊识别（P88）",
                    "金色 filament 区域",
                    f"ρ∈[{band_lo:.2f}, {band_hi:.2f}]",
                ],
            ],
        )
    )

    # ── 任务五 综合 ──
    blocks.append(Heading("5、综合叙事与科学发现", 1))
    blocks.append(Heading("5.1  宇宙网演化的共性机制", 2))
    blocks.append(
        Text(
            "Nyx 128³ 子体积的 100 步演化呈现出可重复的「统计—空间」规律："
            f"（1）引力团块化——σ 上升 {sigma_pct:.1f}%、分位跨度扩大 {span_pct:.1f}%；"
            "（2）分布两极化——void 扩大与高密度尾增厚并存；"
            f"（3）少数致密承载结构——≥p99 体素体积仅 {tail_vol:.2f}%，"
            f"却贡献约 {mass_above:.1f}% 的质量份额；"
            "（4）统计与空间可双向验证——Top 1% 刷选呈丝状，非随机散点。"
            "体渲染提供全局形态直觉，百步直方图量化分布漂移，相空间刷选将高密度尾与空间节点一一对应，"
            "形成「假设—统计—空间—结论」的完整可视分析链路。"
        )
    )
    blocks.append(Heading("5.2  关键发现与质量占比", 2))
    blocks.append(
        Text(
            "发现区四卡（录屏页 /video.html 底部）将上述结论压缩为可展示的叙事单元："
            "01 宇宙网形成（五帧体渲染）、02 密度分布两极化（metrics 曲线）、"
            f"03 少数体积承载质量（≥p99 体积 {tail_vol:.2f}%、质量 {mass_above:.1f}%）、"
            "04 统计—空间验证（Top/Bottom 1% 投影对照）。"
            "质量占比饼图（task5_mass_pie.png）进一步强调：极少数高密度体素承载可见宇宙网结构，"
            f"而 ≤p01 低密度尾占体积 {s99['tailMassBelowP01'] * 100:.2f}%、质量约 {mass_below:.1f}%，"
            "对应 IGM 空洞主体。"
        )
    )
    blocks.append(
        Figure(
            "task5_mass_pie.png",
            "t=99 高密度尾与低密度尾的质量/体积占比（双饼图拼接）",
            14.0,
        )
    )
    blocks.append(Heading("5.3  对可视分析实践的启示", 2))
    blocks.append(
        Text(
            "从近乎均匀的微小涨落，到由引力塑造的宇宙网——这一过程的可见化，"
            "依赖 log 域映射、百步统计序列与刷选联动三者协同，而非单一体渲染截图。"
            "对一般科学可视化实践的启示在于："
            "（1）大动态范围标量场应优先在 log 或分位域建立色标与统计；"
            "（2）时序数据宜用完整序列而非抽帧概括趋势；"
            "（3）相空间刷选是连接「分布」与「几何」的最低成本验证手段。"
            "NyxViz 自研交互仪表盘与离线配图脚本共用 timeline.json，保证报告、录屏与在线探索数值一致、可复现。"
        )
    )
    blocks.append(
        Figure(
            "app_infographic_poster.png",
            "交互仪表盘信息图海报：三栏布局与模块关系（拼接）",
            16.0,
        )
    )

    # ── 附录 ──
    blocks.append(Heading("附录", 1))
    blocks.append(Heading("1  分析流程", 2))
    blocks.append(
        Text(
            "本作品聚焦 Nyx 气体密度时空演化分析，提出从粗粒度到细粒度的可视分析方案："
            "用户先通过体渲染概览全局 void—filament—node 布局，"
            "再借助百步 log 直方图与 σ/分位跨度曲线量化分布漂移，"
            "最后以 Top/Bottom 1% 刷选将统计尾区与空间结构一一对应。"
            "七步流程图（Nyx 数据→预计算→体渲染→统计→刷选→验证→结论）如下。"
        )
    )
    blocks.append(
        Figure(
            "task0_story_flow.png",
            "系统分析流程：七步闭环（横向流程图拼接）",
            16.0,
        )
    )

    blocks.append(Heading("2  可视设计", 2))
    blocks.append(Heading("2.1  体渲染视图", 3))
    blocks.append(
        Text(
            "（1）视图设计：vtk.js FullScreenRenderWindow 嵌入 React 容器，128³ 体素光线投射；"
            "cosmic 传递函数在 log₁₀ρ 域映射 RGB 与 opacity，展板质量采样距离可调。"
            "（2）交互设计：鼠标拖拽旋转、滚轮缩放；时间轴切换时间步；"
            "刷选命中体素通过传递函数二次高亮；左下角 OrientationMarkerWidget 显示 XYZ 轴向。"
        )
    )
    blocks.append(Heading("2.2  log 直方图与时序指标", 3))
    blocks.append(
        Text(
            "（1）视图设计：D3.js SVG 直方图，128 bin 与离线预计算一致；"
            "迷你趋势图展示 σ(t)、p99−p01(t)、Top 1% 尾区变化。"
            "（2）交互设计：拖拽 brush 框选密度区间；点击预设按钮（Top 1%/纤维/Bottom 1%）；"
            "框选结果同步至体渲染与投影视图。"
        )
    )
    blocks.append(Heading("2.3  刷选与密度投影", 3))
    blocks.append(
        Text(
            "（1）视图设计：Web Worker 扫描刷选体素索引；Canvas 2D 最大密度投影与体渲染同色标；"
            "金色 overlay 标记刷选或 filament 亮脊。"
            "（2）交互设计：刷选区间实时更新高亮；清除按钮恢复默认传递函数；"
            "读数栏显示 ρ 区间与选中体积占比。"
        )
    )
    blocks.append(Heading("2.4  录屏页布局", 3))
    blocks.append(
        Text(
            "（1）视图设计：1920×1080 三栏布局——左：直方图 + KPI + 迷你趋势；"
            "中：体渲染 + 色标；右：刷选控制 + 预览；底部发现区四卡 + 页脚叙事。"
            "（2）交互设计：与 app.html 共用 store；?record=1 隐藏导航链，便于 OBS 录屏。"
        )
    )

    blocks.append(Heading("3  数据预计算与配图", 2))
    blocks.append(Heading("3.1  timeline.json 字段", 3))
    blocks.append(
        Table(
            caption="timeline.json 每时间步主要字段",
            headers=["字段", "含义"],
            rows=[
                ["mean / std", "全域均值与标准差"],
                ["p01 / p50 / p99", "分位数"],
                ["skewness", "偏度"],
                ["tailMassAboveP99", "≥p99 体素体积占比"],
                ["massFractionAboveP99", "≥p99 体素质量占比"],
                ["histogram", "128-bin log 直方图归一化频数"],
            ],
        )
    )
    blocks.append(Heading("3.2  拼接图清单", 3))
    blocks.append(
        Text(
            "generate_figures.py 生成的主要拼接图：task1_vol_strip（五帧横排）、"
            "task2_evolution_story（2×2 四联）、task3_evolution_metrics（三联）、"
            "task4_brush_triptych（三联）、task4_brush_rows（双行）、"
            "task6_story_poster（长卷代表图）、task0_story_flow（七步流程）。"
            "体渲染单帧由 tools/node/capture_volumes.mjs（Playwright）截取。"
            "一键再生：npm run submission-pack。",
            indent=False,
        )
    )

    blocks.append(Heading("4  工具与环境", 2))
    blocks.append(
        Text(
            "前端：Vite、React、TypeScript、vtk.js、D3.js；"
            "预计算与静态图：Python（precompute.py、generate_figures.py、viz_style.py、projection_render.py）；"
            "体渲染截图：Playwright；自研 NyxViz 交互仪表盘（/app.html、/video.html、/）。"
            "全部统计数字可由 public/stats/timeline.json 复现，配图脚本与在线页面共用同一数据源。",
            indent=False,
        )
    )

    return blocks
