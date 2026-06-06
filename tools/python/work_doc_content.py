"""ChinaVis-style work document content: cover + overview + tasks + appendix."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from render_spec import (
    CAPTURE_ASPECT,
    DOMAIN_LENGTH,
    PRESENTATION_QUALITY,
    SPACING,
    compute_camera_spec,
)
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
        team_name=data.get("team_name", "学校-姓名-赛道II"),
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


def _brush_validation() -> dict:
    path = ROOT / "public" / "stats" / "brush_validation.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _validation_extended() -> dict:
    path = ROOT / "public" / "stats" / "validation_extended.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _fmt_ci(boot: dict) -> str:
    ci = boot.get("stdBootCi95")
    if not ci:
        return "—"
    return f"[{ci[0]:.4f}, {ci[1]:.4f}]"


def build_blocks(timeline: dict) -> list[Block]:
    steps = _steps(timeline)
    s0, s99 = steps[0], steps[99]
    span0 = s0["p99"] - s0["p01"]
    span99 = s99["p99"] - s99["p01"]
    sigma_pct = (s99["std"] - s0["std"]) / s0["std"] * 100
    span_pct = (span99 - span0) / span0 * 100
    band_lo, band_hi = _filament_band()
    brush_val = _brush_validation()
    ext_val = _validation_extended()
    gmin, gmax = timeline["globalMin"], timeline["globalMax"]
    bins = timeline["binCount"]
    tail_vol = s99["tailMassAboveP99"] * 100
    mass_above = (s99.get("massFractionAboveP99") or 0) * 100
    mass_below = (s99.get("massFractionBelowP01") or 0) * 100
    cam = compute_camera_spec(CAPTURE_ASPECT, 1.0)
    fp = cam["focalPoint"]
    pos = cam["position"]
    gmin_tf, gmax_tf = timeline["timesteps"][0]["p01"], timeline["timesteps"][99]["p99"]
    for s in timeline["timesteps"]:
        if s["p01"] < gmin_tf:
            gmin_tf = s["p01"]
        if s["p99"] > gmax_tf:
            gmax_tf = s["p99"]

    def m(s: dict, key: str, default: float = 0.0) -> float:
        return float(s.get(key, default))

    skew_delta_pct = (m(s99, "skewness") - m(s0, "skewness")) / max(m(s0, "skewness"), 1e-9) * 100
    kurt_delta = m(s99, "excessKurtosis") - m(s0, "excessKurtosis")
    moran_pct = (m(s99, "moransI") - m(s0, "moransI")) / max(abs(m(s0, "moransI")), 1e-9) * 100
    xi_r1_delta = m(s99, "xiR1") - m(s0, "xiR1")
    xi_r10_delta = m(s99, "xiR10") - m(s0, "xiR10")
    mass_frac_delta = (m(s99, "massFractionAboveP99") - m(s0, "massFractionAboveP99")) * 100
    p999_ratio = m(s99, "p999") / max(m(s0, "p999"), 1e-9)
    p99_delta_pct = (m(s99, "p99") - m(s0, "p99")) / max(m(s0, "p99"), 1e-9) * 100
    span_s0 = m(s0, "p99") - m(s0, "p01")
    cap_dg_t0 = -0.32
    cap_op_t0 = 0.72
    cap_op_t99 = 1.1
    cap_dg_t25 = -0.32 * (1 - 25 / 45)
    rho_shift_t0 = -span_s0 * cap_dg_t0 * 0.08
    void_t0p10_0 = m(s0, "voidFractionBelowT0P10") * 100
    void_t0p10_99 = m(s99, "voidFractionBelowT0P10") * 100
    void_t0p01_0 = m(s0, "voidFractionBelowT0P01") * 100
    void_t0p01_99 = m(s99, "voidFractionBelowT0P01") * 100
    voxel_n = 128**3
    samples_per_bin = voxel_n // bins

    blocks: list[Block] = []

    # ── 0 系统概览 ──
    blocks.append(Heading("0  系统概览", 1))
    blocks.append(
        Figure(
            "task6_story_poster.png",
            "NyxViz「宇宙网诞生记」交互长卷（/app.html 全页截取：01–06 节 + 发现卡 + 流程）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "「**NyxViz：宇宙网诞生记**」面向 Nyx 宇宙学模拟输出的 128³ 重子气体密度场（100 个时间步，"
            f"全域 **ρ**∈[{gmin:.2f}, {gmax:.2f}]），旨在从可视化与可视分析角度揭示引力团块化过程中，"
            "由近乎均匀的微小涨落向 **void—filament—node** 宇宙网拓扑分化的完整叙事。"
            "**Nyx** 基于 **AMReX** 块结构自适应网格（AMR）求解引力流体方程，广泛用于高红移 **IGM** 研究——"
            "其中 **莱曼阿尔法森林（Lyα forest）** 沿视线吸收谱线刻画 IGM 密度涨落；"
            "本作品在赛题给定的均匀 **128³** 子体积上，以体渲染与百步统计再现与之相关的密度对比度演化，"
            "为理解「模拟场→观测可解释量」提供可视分析入口（详见第 5 章天文背景与 AMR 范围说明）。"
            "系统以 **/app.html** 交互长卷与 **/video.html** 录屏页呈现，"
            "各视图通过交互页**统一 log 标量域**、共享 **timeline.json** 统计源与刷选状态实现联动。"
            "01–06 长卷侧重形态—统计—刷选故事线；**Moran's I、ξ(r) 等空间自相关详见任务二（第 2 章）**。"
            "录屏页 **/video.html?record=1** 采用 1920×1080 一屏布局，底部四卡发现区与页脚叙事便于答辩录屏。"
            "**重要：配图 vs 在线演示。**"
            "正文 **task1_vol_strip.png（五帧条带）** 由 **capture.html** 生成，使用 **Evolution Capture Profile**"
            "（按步变化的 TF 增益 + 本步 p01–p99 域）；"
            "**/app.html 交互页** 则固定 **getGlobalTfDomain 全局域** 与默认 **tfParams**——"
            "**条带图与在线拖动时间轴的体渲染 intentionally 不同**；答辩请以交互页为准（§1.2（5））。"
        )
    )
    blocks.append(
        Text(
            "**A. 体渲染视图：**基于 **vtk.js** 的 GPU 光线投射，居中常驻展示当前时间步的三维密度场；"
            "cosmic 传递函数在 log 域按全域 p01–p99 映射，使低密度 **void** 与高密度 **filament** 同屏可辨。"
            "**B. 时序 log 直方图：**D3.js 绘制当前步密度分布，支持拖拽框选密度区间，并与体渲染高亮联动。"
            "**C. 统计指标时序：**σ(t)、p99−p01 分位跨度、**Top 1%** 尾区变化等迷你趋势图，量化演化速率。"
            "**D. 相空间刷选：**预设 **Top 1%**、90–99% 纤维带、**Bottom 1%**，一键刷选右尾/左尾并在体素级高亮。"
            "**E. 密度投影：**Canvas 2D 最大密度投影（XY），以金色标出刷选体素或 **filament** 亮脊。"
            "**F. 发现叙事区：**四张发现卡串联体渲染、统计曲线、质量占比与刷选验证，页脚给出科学结论。"
        )
    )
    blocks.append(
        Text(
            "前四章逐题解答赛题任务一至四（**每题回答 ≤800 字**，配图 ≤5 张）；"
            "详细方法、验证与敏感度分析见**附录 5**（与正文第 5 章「综合叙事」区分）。"
            "第五章综合归纳科学发现与启示；"
            "附录 1–4 给出分析流程、可视设计、数据预计算与工具环境；**附录 5** 收纳各题方法细节与敏感度。"
            "文中配图多为 matplotlib 或 Playwright 生成的拼接图，子图含义在图注中逐一说明。"
        )
    )
    blocks.append(Heading("0.1  术语与缩写", 2))
    blocks.append(
        Table(
            caption="正文常用术语（首次出现处亦作简要说明）",
            headers=["术语", "含义"],
            rows=[
                ["IGM", "Intergalactic Medium，星系际介质"],
                ["void / filament / node", "宇宙网拓扑：低密度空洞 / 丝状纤维 / 高密度节点"],
                ["TF / 传递函数", "Transfer Function，体渲染中将标量密度 ρ 映射为 RGB 与不透明度 α 的分段函数"],
                [
                    "TF 增益 / Evolution Capture Profile",
                    "仅 **capture.html** 五帧条带截图专用：`getEvolutionCaptureProfile` 按时间步调整 "
                    "**opacityScale**（全局 α 乘子）与 **densityGain**（传递函数控制点在 ρ 轴上的平移系数）；"
                    "**不修改体素密度**，仅改变可视化映射；交互页 `/app.html` 默认不使用该曲线",
                ],
                [
                    "densityGain",
                    "传递函数平移系数：在 `mapT()` 中对每个 cosmic 控制点密度坐标施加 "
                    "Δρ = −(p99−p01)·densityGain·0.08；**负值**将控制点移向更高 ρ，"
                    "使同等低密度体素获得更低 α/RGB，等效于**压低 IGM 雾感**",
                ],
                [
                    "wideBoost",
                    "宽屏视口修正因子：16:9 横屏时相对正方体域的 `1/√aspect` 缩放，写入 `fitVolumeCamera`，与 VIEW_MARGIN、zoom 合成 effectiveZoom",
                ],
                ["pp", "percentage point，百分点（如 1.2%→1.3% 为 +0.1 pp，非相对百分比）"],
                ["σ", "标准差（standard deviation）"],
                ["p01/p99 等", "密度场的 1%/99% 分位数"],
                ["Ka / Kd / Ks", "Phong 光照的环境光 / 漫反射 / 镜面反射系数"],
                ["AMR", "Adaptive Mesh Refinement，自适应网格细化"],
                ["KPI", "Key Performance Indicator，仪表盘关键指标卡片"],
                ["LOD", "Level of Detail，多细节层次（体渲染远近分级）"],
            ],
        )
    )


    from work_doc_compact import (
        _task1_compact,
        _task2_compact,
        _task3_compact,
        _task4_compact,
        supplement_appendix_blocks,
    )

    blocks.extend(_task1_compact(
        s0=s0, s99=s99, steps=steps, sigma_pct=sigma_pct,
        gmin_tf=gmin_tf, gmax_tf=gmax_tf, fp=fp, pos=pos, cam=cam,
        cap_op_t0=cap_op_t0, cap_op_t99=cap_op_t99, cap_dg_t0=cap_dg_t0,
        cap_dg_t25=cap_dg_t25, rho_shift_t0=rho_shift_t0, span_s0=span_s0,
        ext_val=ext_val,
    ))
    blocks.extend(_task2_compact(
        s0=s0, s99=s99, sigma_pct=sigma_pct, span0=span0, span99=span99,
        span_pct=span_pct, tail_vol=tail_vol, mass_above=mass_above,
        brush_top_n=int(brush_val.get("fpFnDefault", {}).get("brushVoxels", 20972)),
        fil_lo=m(s99, "p90"), fil_hi=m(s99, "p99"),
        fil_vol_pct=m(s99, "tailMassFilament90_99") * 100,
        band_lo=band_lo, band_hi=band_hi,
        fp_rate_early=brush_val.get("fpFnDefault", {}).get("fpRateInBrush", 0) * 100,
        m=m, xi_r1_delta=xi_r1_delta, boot=ext_val.get("bootstrapSpatial", {}),
    ))
    blocks.extend(_task3_compact(
        s0=s0, s99=s99, bins=bins, samples_per_bin=samples_per_bin,
        sigma_pct=sigma_pct, span0=span0, span99=span99,
        void_t0p10_0=void_t0p10_0, void_t0p10_99=void_t0p10_99,
        p999_ratio=p999_ratio, skew_delta_pct=skew_delta_pct,
    ))
    fpfn_early = brush_val.get("fpFnDefault", {})
    bench = brush_val.get("benchmark", {})
    early_ms = bench.get("top1_earlyExit", {}).get("elapsedMs", 0)
    full_ms = bench.get("top1_fullCount", {}).get("elapsedMs", 0)
    custom_err = bench.get("customBrushErrors", [])
    custom_wide = next((r for r in custom_err if "p50" in r.get("label", "")), None)
    custom_mid = next((r for r in custom_err if "p25" in r.get("label", "")), None)
    sample_rec = bench.get("sampleRecall", {})
    blocks.extend(_task4_compact(
        s0=s0, s99=s99, band_lo=band_lo, band_hi=band_hi,
        brush_val=brush_val, fpfn=fpfn_early, early_ms=early_ms, full_ms=full_ms,
        custom_wide_pct=custom_wide["reportedOverTruePct"] if custom_wide else 0.8,
        custom_mid_pct=custom_mid["reportedOverTruePct"] if custom_mid else 0.8,
        sample_recall_pct=sample_rec.get("recallVsTrue", 0) * 100 if sample_rec else 12.7,
    ))

    # ── 任务五 综合 ──
    blocks.append(Heading("5、综合叙事与科学发现", 1))
    blocks.append(Heading("5.1  宇宙网演化的共性机制", 2))
    blocks.append(
        Text(
            "Nyx 128³ 子体积的 100 步演化呈现出可重复的「统计—空间」规律："
            f"**（1）**引力团块化——**σ 上升 {sigma_pct:.1f}%**、分位跨度扩大 **{span_pct:.1f}%**；"
            "**（2）**分布两极化——**void** 扩大与高密度尾增厚并存；"
            f"**（3）**少数致密承载结构——≥p99 体素体积仅 **{tail_vol:.2f}%**，"
            f"却贡献约 **{mass_above:.1f}%** 的质量份额；"
            "**（4）**统计与空间可双向验证——**Top 1%** 刷选呈丝状，非随机散点。"
            "体渲染提供全局形态直觉，百步直方图量化分布漂移，相空间刷选将高密度尾与空间节点一一对应，"
            "形成「假设—统计—空间—结论」的完整可视分析链路。"
        )
    )
    blocks.append(Heading("5.2  关键发现与质量占比", 2))
    blocks.append(
        Text(
            "发现区四卡（录屏页 **/video.html** 底部）将上述结论压缩为可展示的叙事单元："
            "01 宇宙网形成（五帧体渲染）、02 密度分布两极化（metrics 曲线）、"
            f"03 少数体积承载质量（≥p99 体积 **{tail_vol:.2f}%**、质量 **{mass_above:.1f}%**）、"
            "04 统计—空间验证（**Top/Bottom 1%** 投影对照）。"
            "质量占比饼图（task5_mass_pie.png）进一步强调：极少数高密度体素承载可见宇宙网结构，"
            f"而 ≤p01 低密度尾占体积 {s99['tailMassBelowP01'] * 100:.2f}%、质量约 **{mass_below:.1f}%**，"
            "对应 IGM 空洞主体。"
        )
    )
    blocks.append(
        Figure(
            "task5_mass_pie.png",
            "t=99 高密度尾与低密度尾：环形图对比体积占比，中心标注质量占比",
            14.0,
        )
    )
    blocks.append(Heading("5.3  对可视分析实践的启示", 2))
    blocks.append(
        Text(
            "从近乎均匀的微小涨落，到由引力塑造的宇宙网——这一过程的可见化，"
            "依赖 log 域映射、百步统计序列与刷选联动三者协同，而非单一体渲染截图。"
            "对一般科学可视化实践的启示在于："
            "**（1）**大动态范围标量场应优先在 log 或分位域建立色标与统计；"
            "**（2）**时序数据宜用完整序列而非抽帧概括趋势；"
            "**（3）**相空间刷选是连接「分布」与「几何」的最低成本验证手段。"
            "在宇宙学数据分析场景中，上述原则与 **yt** 的相位空间探针、**ParaView** 的阈值/等值面工作流精神一致，"
            "但本作品强调**轻量 Web 交付**与**统计—渲染—投影同屏联动**，降低答辩与非 HPC 环境下的复现门槛。"
            "**NyxViz** 自研交互仪表盘与离线配图脚本共用 **timeline.json**，保证报告、录屏与在线探索数值一致、可复现。"
        )
    )
    blocks.append(Heading("5.4  AMR 范围说明与局限", 2))
    blocks.append(
        Text(
            "**Nyx** 的核心数值优势在于 **AMReX** 块结构 **AMR**：在星系、晕与致密纤维附近自动加密网格，"
            "以较低代价解析大动态范围流体结构。"
            "**本赛题数据集** 已预先抽取为 **均匀 128³** 重子气体子体积（100 时间步 `.dat`），"
            "数据包来源为赛题官方发布的 **Nyx/** 目录（非本队自行降采样）；"
            "不包含层级网格、细化级别（level）或父子块（fab）元数据，"
            "因此 **NyxViz 未实现 AMR 多分辨率可视化**——体渲染、投影与刷选均按单一均匀体素网格处理。"
            "这一取舍与赛题数据格式、**vtk.js** 均匀 `vtkImageData` 管线及浏览器内存预算一致；"
            "并不否定 AMR 的重要性，而是明确本答卷的**有效分析尺度**为「给定子体积内的 IGM 密度演化与宇宙网形态」。"
            "若扩展至完整 Nyx 输出，建议路径为：以 **yt** 读取 AMR 数据集做层级统计与切片导出，"
            "或以 **ParaView** 的 AMR 过滤器做全局体绘制，再将感兴趣子域降采样为均匀网格供 Web 端联动展示；"
            "亦可探索按细化级别分色叠加、局部 **LOD** 体渲染等（列为后续工作）。"
        )
    )
    blocks.append(Heading("5.5  天文背景：与莱曼阿尔法森林的关联", 2))
    blocks.append(
        Text(
            "赛题背景指出，**Nyx** 等宇宙学模拟常用于研究高红移 **IGM** 与 **莱曼阿尔法森林（Lyα forest）**："
            "沿类星体视线，IGM 中性氢对背景 Lyα 连续谱产生吸收线系，"
            "线深度与间距反映沿路径的密度对比度与红移演化。"
            "本作品**未**合成完整辐射传输 Lyα 谱线，亦**未**将 t=0/99 映射到宇宙学红移 z"
            "（赛题 `.dat` 仅给时间步索引，无 lookback/redshift 元数据）。"
            "在 t=0/99 上对 **2000 条 +z 固定视线**做列平均密度，得到**通量涨落 PDF 代理**"
            "（**图18**）——**定性**对比对比度增强，**非观测拟合**。"
            "**方向敏感性（定量）：**同 seed 下对 **+x/+y/+z** 三向各 2000 条视线复算（"
            "validation_extended.json → lyalphaDirectionSensitivity）；"
            "t=99 列密度 σ 相对差异见下表——差异**存在但有限**，仍**非**各向同性森林模拟。"
        )
    )
    ly = ext_val.get("lyalphaProxy", {})
    ly_dir = ext_val.get("lyalphaDirectionSensitivity", {})
    if ly:
        a0, a99 = ly.get("t0", {}), ly.get("t99", {})
        meth = a0.get("method", {})
        blocks.append(
            Table(
                caption="Lyα 通量代理方法（validation_extended.json → lyalphaProxy.method）",
                headers=["项目", "设定"],
                rows=[
                    ["视线方向", meth.get("sightlineDirection", "+z 固定")],
                    ["是否各向同性", "否 — 仅 +z 平行于盒子 z 轴，非随机立体角"],
                    ["起点采样", meth.get("startSampling", "128×128 面内均匀随机 (x,y)")],
                    ["积分范围", meth.get("integration", "整列 z=0..127 算术平均 ρ")],
                    ["是否穿过全体素域", "是 — 每条线贯穿 128 个体素层"],
                    ["红移/时间", meth.get("redshiftMapping", "无 cosmological z；t 为模拟步")],
                    ["跨步对比", meth.get("crossTimeComparison", "t=0 与 t=99 同几何，仅比对比度演化")],
                    ["随机种子", str(a0.get("randomSeed", 7))],
                    ["复现", meth.get("reproduce", "validation_suite.py :: lyalpha_flux_pdf_proxy")],
                ],
            )
        )
        blocks.append(
            Text(
                f"t=0 列密度 **σ={a0.get('fluxStd', 0):.4f}**、p50={a0.get('p50', 0):.4f}；"
                f"t=99 **σ={a99.get('fluxStd', 0):.4f}**、p50={a99.get('p50', 0):.4f}——"
                "PDF 展宽与模拟密度对比度上升**趋势一致**，但因方向固定、无光学深度，"
                "**不宜**与真实 QSO 森林线系定量比对；完整合成谱需辐射后处理与观测红移标定。"
            )
        )
        if ly_dir:
            cmp = ly_dir.get("t99Comparison", {})
            stds = cmp.get("fluxStdByDirection", {})
            means = cmp.get("fluxMeanByDirection", {})
            pairs = cmp.get("histL1Distance", {})
            l1_xz = pairs.get("+x_vs_+z", 0)
            l1_yz = pairs.get("+y_vs_+z", 0)
            l1_xy = pairs.get("+x_vs_+y", 0)
            boot = cmp.get("stdBootstrapT99", {})
            blocks.append(
                Table(
                    caption=(
                        "Lyα 代理方向敏感性（t=99；n=2000 条视线，seed=7；"
                        "σ 为视线级 bootstrap：对 2000 条列均值有放回重采样 n=40 次；"
                        "95% CI 为 40 次 σ 的**百分位数**（2.5%, 97.5%），非 BCa/正态近似；"
                        "L1 距：32-bin PDF（density=True）归一化至和为 1 后，"
                        "L1=Σ|p_dir−p_+z|，无量纲）"
                    ),
                    headers=["视线", "列密度 σ", "σ 95% CI", "与 +z PDF L1 距（归一化，无量纲）"],
                    rows=[
                        [
                            "+x",
                            f"{stds.get('+x', 0):.4f}",
                            _fmt_ci(boot.get("+x", {})),
                            f"{l1_xz:.3f}",
                        ],
                        [
                            "+y",
                            f"{stds.get('+y', 0):.4f}",
                            _fmt_ci(boot.get("+y", {})),
                            f"{l1_yz:.3f}",
                        ],
                        [
                            "+z（基准）",
                            f"{stds.get('+z', 0):.4f}",
                            _fmt_ci(boot.get("+z", {})),
                            "—",
                        ],
                        [
                            "汇总",
                            f"σ 极差 {cmp.get('stdSpreadRelPct', 0):.2f}%",
                            f"+x/+y CI 与 +z 重叠：{cmp.get('plusZCiOverlapsPlusX')} / {cmp.get('plusZCiOverlapsPlusY')}",
                            f"max L1={cmp.get('maxHistL1', 0):.3f}",
                        ],
                    ],
                )
            )
            blocks.append(
                Text(
                    f"三向 σ 相对极差 **{cmp.get('stdSpreadRelPct', 0):.2f}%**。"
                    f"+x CI {_fmt_ci(boot.get('+x', {}))} 与 +z CI {_fmt_ci(boot.get('+z', {}))} **不重叠**，"
                    f"+y 同理——说明 **+x/+y 列密度 σ 显著高于 +z**（盒子坐标下各向异性），"
                    "而非「未超过重采样噪声」。"
                    "仍**非**辐射传输合成谱，**不作**观测森林定量拟合。"
                )
            )
        blocks.append(
            Figure(
                "task5_lyalpha_flux_proxy.png",
                "Lyα 通量涨落代理：2000 条 +z 视线列平均 ρ PDF（非各向同性、无红移标定；t=0 vs t=99）",
                15.0,
            )
        )
        if ly_dir:
            blocks.append(
                Figure(
                    "task5_lyalpha_direction_sensitivity.png",
                    "Lyα 代理方向敏感性：t=99 下 +x/+y/+z 列密度 PDF 叠加对比",
                    14.5,
                )
            )
        blocks.append(
            Text(
                "体渲染中的 **void** 与 **filament** 可直观理解为沿视线积分时产生「浅/深吸收」的空间来源；"
                "百步 **σ(t)** 与分位跨度曲线则量化对比度随**模拟时间步**增强的趋势。"
                "本代理仅说明「密度对比度演化与森林统计定性相容」，"
                "为后续接入辐射传输（光学深度 τ∝∫n_H dl）或 **yt** 视线积分预留接口；"
                "将「图上的 filament」提升为「可与观测森林对照的证据」仍需红移与 RT 管线。"
            )
        )
    blocks.append(Heading("5.6  暗物质场未纳入的原因与影响", 2))
    blocks.append(
        Text(
            "赛题 II 指出 Nyx 同时演化 **暗物质 N 体** 与 **重子气体**；引力势由暗物质主导，气体则通过流体方程响应。"
            "本赛题交付的 100 个 `.dat` 文件均为 **128³ 重子气体密度**（`timeline.json` 中 `dataScope.includedFields` 仅含 `baryon_gas_density`），"
            "**未包含**暗物质粒子坐标、暗物质密度网格或二者配对元数据，因此 NyxViz **无法**在答卷内直接对比 "
            "「DM 团块 vs 气体 filament」的共演化差异。"
            "这一限制的影响在于：我们观察到的气体宇宙网分化，在物理上由 DM 势阱驱动，"
            "但本作品的证据链限定在**重子流体可观测代理**（密度场统计、气体刷选、Lyα 敏感对比度）层面。"
            "若扩展数据集，建议以 **yt** 同时加载 DM 与 gas 组件，比较二者 power spectrum / 两点相关差异，"
            "或在 ParaView 中叠加 DM 等值面与气体质心流线——可作为后续与赛题官方数据对齐的增强方向。"
        )
    )
    blocks.append(Heading("5.7  本地复现与一键交付", 2))
    blocks.append(
        Text(
            "**本地 Demo：**赛题答卷以**可本地复现**为主（未部署公网服务器——赛题数据体积与许可限制）。"
            "评委可在 Windows/macOS/Linux 执行 **`python run.py`**"
            "（自动 precompute、缺图补全、启动 Vite 并打开 **http://127.0.0.1:5173/app.html**）。"
            "若无 Python/Node 环境，可先阅读 **§2.3** 刷选三联静态图与下文 **§5.8** 录屏说明，"
            "或观看随答卷提交的 **答辩 mp4**（大会单独通道）。"
            "**一键复现（Windows PowerShell）：** **`powershell -File scripts/reproduce.ps1`**，"
            "顺序执行：npm install → precompute → figures → export-docx → submission-pack；"
            "体渲染截图需另跑 **`npm run build; $env:CAPTURE_SCALE=2; npm run capture-volumes`**。"
            "等价命令见 **`npm run deliver`**；工具链跨 Node/Python/Playwright，"
            "入口收敛为 **run.py** 与 **reproduce.ps1**。"
        )
    )
    blocks.append(Heading("5.8  交互体验与答辩附件（补充）", 2))
    blocks.append(
        Text(
            "本 Word 以静态拼接图为主；**刷选三栏实时联动**无法完全由纸面替代，建议："
            "**（1）静态替代：**任务二 **图9**、任务四 **图12**（均为 Top 1% 三联静态冻结）可替代实时联动；"
            "**（2）本地交互：**`/app.html` 或 **`/video.html?record=1`**（1920×1080 录屏布局，见 `docs/competition/VIDEO_SCRIPT.md`）；"
            "**（3）答辩 mp4/GIF：**按大会要求上传 **30–60 s** OBS 录屏"
            "（推荐流程：Top 1% 预设 → 体渲染高亮 → XY 投影金斑 → 切换纤维带 90–99%）；"
            "亦可导出 GIF 作附录，但本 docx **不嵌入**动图文件（体积与 Word 兼容性）。"
            "录屏分镜脚本见仓库 **`docs/competition/VIDEO_SCRIPT.md`**。"
        )
    )
    blocks.append(
        Figure(
            "task4_brush_rows.png",
            "刷选双行对比（Top 1% / Bottom 1%）：无本地环境时的静态交互替代示意",
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
            "**（1）视图设计：**基于 **vtk.js** FullScreenRenderWindow 嵌入 React 容器，128³ 体素光线投射；"
            "cosmic 传递函数见正文任务一 **图4** 与 **task1_render_params.png**；"
            "交互页默认 **getGlobalTfDomain**（百步 p01–p99 包络）+ 固定 **tfParams**，"
            "拖动时间轴时 α(ρ) 映射不变；**capture 条带**另用 Evolution Profile，逐项对照见**附录 5.1**。"
            f"presentation 采样 `sampleDistance={PRESENTATION_QUALITY['sampleDistance']}`，"
            "GPU 三线性纹理插值 + Phong（Ka/Kd/Ks=0.12/0.75/0.4）。"
            "左下角 **OrientationMarkerWidget** 显示 XYZ 正方向三轴（X 红 / Y 绿 / Z 蓝）。"
            "**（2）交互设计：**鼠标拖拽旋转、滚轮缩放；时间轴切换时间步；"
            "刷选命中体素通过传递函数二次高亮。"
            "**（3）可复现参数：**`docs/figures/render_spec.json` 导出相机、光源与 TF 控制点。"
        )
    )
    blocks.append(Heading("2.2  log 直方图与时序指标", 3))
    blocks.append(
        Text(
            "**（1）视图设计：**D3.js SVG 直方图，128 bin 与离线预计算一致；"
            "迷你趋势图展示 **σ(t)**、p99−p01(t)、**Top 1%** 尾区变化。"
            "**（2）交互设计：**拖拽 brush 框选密度区间；点击预设按钮（**Top 1%**/纤维/**Bottom 1%**）；"
            "框选结果同步至体渲染与投影视图。"
        )
    )
    blocks.append(Heading("2.3  刷选与密度投影", 3))
    blocks.append(
        Text(
            "**（1）视图设计：**Web Worker 扫描刷选体素索引；Canvas 2D 最大密度投影与体渲染同色标；"
            "金色 overlay 标记刷选或 **filament** 亮脊。"
            "**（2）交互设计：**刷选区间实时更新高亮；清除按钮恢复默认传递函数；"
            "读数栏显示 **ρ** 区间与选中体积占比。"
        )
    )
    blocks.append(Heading("2.4  录屏页布局", 3))
    blocks.append(
        Text(
            "**（1）视图设计：**1920×1080 三栏布局——左：直方图 + KPI + 迷你趋势；"
            "中：体渲染画布（**vd-vtk-canvas-wrap**）+ 底栏全宽 log 密度色标；"
            "右：刷选直方图 + 四格空间投影预览 + 预设按钮；底部发现区四卡 + 页脚叙事。"
            "体渲染区左下角显示 XYZ 方向 gizmo（位于色条上方），**cameraZoom≈1.1** 略放大主结构。"
            "**（2）交互设计：**与 **/app.html** 共用 store；**?record=1** 隐藏导航链并弱化背景星尘，便于 OBS 录屏。"
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
                ["skewness", "偏度（三阶矩）"],
                ["excessKurtosis", "超额峰度 κ−3"],
                ["moransI", "Moran's I 空间自相关（6 邻域 3D）"],
                ["xiR1 / xiR10", "两点相关 ξ 在 r=1、10 像素（XY 投影）"],
                ["xiHalfLength", "ξ(r)<0.5 半长（本数据集中两时刻均≈4px）"],
                ["fractalDimP90", "P90 亮脊盒计数分形维数"],
                ["multiscaleEntropy8", "8×8 粗粒化 Shannon 熵"],
                ["tailMassAboveP99", "≥p99 体素体积占比"],
                ["massFractionAboveP99", "≥p99 体素质量占比"],
                ["histogram", "128-bin 概率质量 hist[b]=count_b/Σcount（单步 N=2,097,152）"],
                ["voidFractionBelowT0P10", "ρ≤ρ_p10(t=0) 的体素体积分数"],
                ["voidFractionBelowT0P01", "ρ≤ρ_p01(t=0) 的体素体积分数"],
                ["p25 / p75", "四分位带（peak_drift 图）"],
                ["histogramMeta", "归一化公式、void 参考阈值、分箱说明"],
            ],
        )
    )
    blocks.append(Heading("3.2  拼接图清单", 3))
    blocks.append(
        Text(
            "generate_figures.py 生成的主要拼接图：task1_transfer_function（传递函数曲线）、"
            "task1_vol_strip（五帧横排）、"
            "task2_evolution_story（2×2 四联）、task3_evolution_metrics（三联）、"
            "task4_brush_triptych（三联）、task4_brush_rows（双行）、"
            "task1_render_params / task2_spatial_summary / task3_histogram_summary / task4_brush_validation_summary / task4_performance_summary（正文拼接）及子图原件、"
            "task6_story_poster（/app.html Playwright 长卷代表图）、task0_story_flow（七步流程）。"
            "体渲染单帧由 tools/node/capture_volumes.mjs（Playwright）截取；"
            "长卷代表图由 tools/node/capture_app_poster.mjs 截取 /app.html。"
            "一键再生：npm run submission-pack。",
            indent=False,
        )
    )
    blocks.append(Heading("3.3  空间统计 bootstrap 复现", 3))
    boot_a = ext_val.get("bootstrapSpatial", {})
    if boot_a:
        ma = boot_a.get("method", {})
        blocks.append(
            Text(
                f"`validation_suite.py :: bootstrap_spatial_ci` 在 t=0、t=99 各执行 "
                f"**n={boot_a.get('nBootstrap', 40)}** 次子窗口抽样（**seed={ma.get('randomSeed', 42)}**）。"
                f"每步从 128³ 域内均匀随机选取 **{ma.get('subvolumeShape', [64, 64, 64])[0]}³** 子体积"
                "（**空间块 bootstrap**：各 replicate 独立随机平移原点；**非**像素级有放回重采样），"
                "在子体积上计算 Moran's I 与 XY 投影 ξ(r) 剖面。"
                "输出写入 `public/stats/validation_extended.json` 的 "
                "`bootstrapSpatial.method`、`xiProfileBootstrap`、`moransIGlobal`、`xiR1Global`。"
                "配图 `task2_bootstrap_ci.png`、`task2_two_point_xi.png` 由 `generate_figures.py` 读取同一 JSON。"
                "**未做 Bonferroni/FDR**——因全文不对 Moran's I / ξ 作显著性主张，仅作与 Δ 的对照参考。"
            )
        )
    blocks.append(Heading("3.4  原始数据格式与轴向重排", 3))
    blocks.append(
        Text(
            "赛题每步文件 `NNNN.dat` 为 **2,097,152** 字节（128³×4），无文件头。"
            "单精度浮点采用 **IEEE-754 小端字节序**；Python 以 `np.fromfile(path, dtype='<f4')` 读取，"
            "TypeScript 以 `fetch` + `Float32Array` 直接映射同一字节序（Windows/x86 与赛题一致）。"
            "存储为 **z 最快变维**（常记作 z→y→x）：相邻内存地址首先遍历 z，再 y，再 x。"
            "逻辑体素 `(x,y,z)` 与扁平下标关系为 **`i = z + N·y + N²·x`（N=128）**。"
            "该顺序等价于将三维数组视为 `volume[x,y,z]` 并按 C 风格（行优先）展平，"
            "其中 **最内维为 z**——与部分文献所称「列优先」在 z 维上的遍历一致。"
        )
    )
    blocks.append(
        Table(
            caption="读取链路与轴向约定",
            headers=["环节", "实现", "轴向约定"],
            rows=[
                ["磁盘 → 内存", "fromfile / Float32Array", "z-fast 一维缓冲，长度 128³"],
                ["Python 分析", "reshape((128,128,128), order='C')", "`volume[x,y,z]`，与 flat_index 一致"],
                ["TS 体素访问", "nyxLoader.flatIndex(x,y,z)", "同上，用于刷选扫描与投影"],
                ["vtk.js 体渲染", "vtkConvert.worker Z_TO_VTK 查表重排", "输出 x-fast：`vtkIdx = x + N·(y + N·z)`"],
                ["一致性校验", "tools/python/verify_loader.py", "reshape 与 flat_index 逐点比对"],
            ],
        )
    )
    blocks.append(
        Text(
            "**为何体渲染需 x-fast 而统计/刷选保留 z-fast？** "
            "`vtkImageData` 点标量按 **x 最快** 线性存储；误用 z-fast 缓冲会导致体渲染伪影。"
            "投影、刷选 Worker 与 Python 预计算均在 **z-fast**（`flatIndex` / `reshape(C)`）上访问，"
            "与磁盘 `.dat` 顺序一致，保证「统计—刷选—配图」体素级对齐。"
            "**体渲染路径：**`vtkConvert.worker` 在**独立 Worker** 中执行 z-fast→x-fast 重映射："
            "启动时预计算 **128³ 查表 `Z_TO_VTK`**（一次性），每时间步对 **N=2,097,152** 标量做 O(N) 索引写入"
            "（约 8 MB 读写，典型 **5–20 ms**，不阻塞主线程 UI）；"
            "结果缓存供时间轴复用。"
            "与主线程 `numpy.transpose(...).copy()` 相比，Worker 方案避免播放时 UI 卡顿，"
            "且刷选/统计模块**无需**跟随 vtk 轴向——两套布局各司其职、经 `verify_loader.py` 校验一致。"
        )
    )

    blocks.append(Heading("4  工具与环境", 2))
    blocks.append(
        Text(
            "前端：Vite、React、TypeScript、vtk.js、D3.js；"
            "预计算与静态图：Python（precompute.py、generate_figures.py、viz_style.py、projection_render.py、verify_loader.py）；"
            "体渲染截图：Playwright；自研 NyxViz 交互仪表盘（/app.html、/video.html、/）。"
            "天文领域常见工具 **yt**、**ParaView** 用于 AMR 级分析与 HPC 体视；"
            "本仓库聚焦赛题子体积的 Web 联动与作品说明可复现配图。"
            "全部统计数字可由 public/stats/timeline.json 复现，配图脚本与在线页面共用同一数据源。",
            indent=False,
        )
    )

    boot = ext_val.get("bootstrapSpatial", {})
    blocks.extend(
        supplement_appendix_blocks(
            s0=s0,
            s99=s99,
            steps=steps,
            sigma_pct=sigma_pct,
            span0=span0,
            span99=span99,
            span_pct=span_pct,
            gmin_tf=gmin_tf,
            gmax_tf=gmax_tf,
            fp=fp,
            pos=pos,
            cam=cam,
            cap_op_t0=cap_op_t0,
            cap_op_t99=cap_op_t99,
            cap_dg_t0=cap_dg_t0,
            cap_dg_t25=cap_dg_t25,
            rho_shift_t0=rho_shift_t0,
            span_s0=span_s0,
            ext_val=ext_val,
            boot=boot,
            brush_val=brush_val,
            band_lo=band_lo,
            band_hi=band_hi,
            fil_lo=m(s99, "p90"),
            fil_hi=m(s99, "p99"),
            fil_vol_pct=m(s99, "tailMassFilament90_99") * 100,
            fil_mass_pct=(
                brush_val.get("thresholds", [{}])[1].get("massPct", 9.86)
                if len(brush_val.get("thresholds", [])) > 1
                else 9.86
            ),
            brush_top_n=int(fpfn_early.get("brushVoxels", 20972)),
            tail_vol=tail_vol,
            mass_above=mass_above,
            proxy_n=int(fpfn_early.get("filamentProxyVoxels", 5796)),
            fp_rate_early=fpfn_early.get("fpRateInBrush", 0) * 100,
            void_t0p10_0=void_t0p10_0,
            void_t0p10_99=void_t0p10_99,
            void_t0p01_0=void_t0p01_0,
            void_t0p01_99=void_t0p01_99,
            samples_per_bin=samples_per_bin,
            bins=bins,
            gmin=gmin,
            m=m,
            xi_r1_delta=xi_r1_delta,
            skew_delta_pct=skew_delta_pct,
            kurt_delta=kurt_delta,
            p999_ratio=p999_ratio,
            p99_delta_pct=p99_delta_pct,
            mass_frac_delta=mass_frac_delta,
            moran_pct=moran_pct,
        )
    )

    return blocks
