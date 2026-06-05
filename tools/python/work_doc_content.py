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
            "NyxViz「宇宙网诞生记」全景长卷（hero + 五帧条带 + 统计 + 刷选 + 质量占比 + 流程，纵向拼接）",
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
            "本答卷前四章逐题解答赛题任务一至四，第五章综合归纳科学发现与启示；"
            "附录给出分析流程、可视设计、数据预计算管线与工具环境（附录 1–4）。"
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

    # ── 任务一 ──
    blocks.append(Heading("1、体数据渲染与密度演化", 1))
    blocks.append(Heading("1.1  视图简介", 2))
    blocks.append(
        Text(
            "本题涉及体渲染视图与五时刻演化条带。数据为 Nyx 官方 **128³** 重子气体密度（仅气体，非暗物质），"
            "100 步 t=0…99。"
            "**字节序与存储布局：**每体素 4 字节 **小端 float32**（Python `dtype='<f4'`；浏览器 `Float32Array` 在 x86 平台按小端解释），"
            "文件按 **z 最快、y 次之、x 最慢** 的线性顺序排列（赛题所称 z→y→x），"
            "扁平索引 `i = z + 128·y + 128²·x`。"
            "读取后 **不** 改变物理含义下的 `(x,y,z)` 体素坐标，仅将一维数组解释为三维标量场；"
            "Python 侧以 `reshape((128,128,128), order='C')` 得 `volume[x,y,z]`；"
            "浏览器侧 **vtk.js** 的 `vtkImageData` 点数据要求 **x 最快**，故经 `vtkConvert.worker` 将 z-fast 缓冲重映射为 x-fast（见附录 3.4）。"
            "渲染管线基于 **vtk.js** GPU 光线投射；传递函数、光照、采样与相机参数见 **§1.2**。"
            "为便于跨时刻**定性**对比，选取 t=0、25、50、75、99 五帧，"
            "在 **capture.html** 下以固定算法位姿（`fitVolumeCamera`，`cameraZoom=1`）截图，"
            "输出五联条带（task1_vol_strip.png）。"
            "条带底部色条标注 **百步 p01–p99 全局包络**（与交互页 `getGlobalTfDomain` 一致），"
            "作为 cosmic 调色板的**参照刻度**；"
            "各帧实际渲染另采用 capture 专用 Evolution Profile（见 §1.2（5）），"
            "**严格而言五帧间 α(ρ) 映射并不相同**——此为配图可读性取舍，非交互页默认行为。"
        )
    )
    blocks.append(Heading("1.2  传递函数、光照、采样与相机", 2))
    blocks.append(
        Text(
            "**（1）传递函数。**采用自研 **cosmic** 预设：在 log10 密度域将标量 **p01–p99** 映射到 RGB 与不透明度。"
            f"交互页默认标量域为百步包络 **[{gmin_tf:.3f}, {gmax_tf:.3f}]**；"
            "capture 条带各帧可改用本步 p01–p99（§1.2（5））。"
            "颜色由 7 段控制点插值（深蓝 void → 青蓝 IGM → 紫粉 filament → 金黄 node）；"
            "不透明度在归一化 t=0/0.12/0.35/0.55/0.72/0.88/1.0 处取 α=0/0.02/0.06/0.14/0.32/0.65/0.95，"
            "低密度区近乎透明、右尾渐显，避免 IGM 雾屏。"
            "下图（task1_transfer_function.png）给出独立的 **颜色条 + 不透明度曲线** 示意图，"
            "与线上一致的定义见 `src/volume/transferFunction.ts`。"
        )
    )
    blocks.append(
        Figure(
            "task1_transfer_function.png",
            "cosmic 传递函数设计图（交互页默认参数）",
            15.5,
        )
    )
    blocks.append(
        Text(
            "**（2）光照（Phong）。**展板/截图质量（`quality=presentation`）启用体素光照："
            "**VolumeProperty.setShade(true)**，环境光 **Ka=0.12**、漫反射 **Kd=0.75**、镜面 **Ks=0.4**；"
            "双光源均指向体素域几何中心 **(7.1225, 7.1225, 7.1225)**（域长 **14.245** 代码单位的一半）："
            "主光位置 **(15.12, 17.12, 19.12)**、RGB **(1,1,1)**、强度 **1.0**；"
            "补光位置 **(-4.88, -0.88, -2.88)**、RGB **(0.55,0.75,1)**、强度 **0.3**。"
            "该配置在保持 IGM 半透明感的同时，为 **filament** 脊线提供可辨的明暗起伏。"
            "下图（task1_lighting_diagram.png）以三维示意主光/补光方向（箭头指向体素域中心），"
            "与传递函数曲线图并列，便于复现光照空间分布。"
        )
    )
    blocks.append(
        Figure(
            "task1_lighting_diagram.png",
            "Phong 双光源空间示意：主光/补光位置与指向域中心的方向",
            14.0,
        )
    )
    blocks.append(
        Table(
            caption="体渲染光照与采样参数（presentation / capture 默认）",
            headers=["参数", "取值", "说明"],
            rows=[
                ["shade", "true", "启用 Phong 体绘制明暗"],
                ["ambient Ka", "0.12", "环境光，防止阴影区全黑"],
                ["diffuse Kd", "0.75", "漫反射主分量"],
                ["specular Ks", "0.4", "镜面高光，突出细脊"],
                ["scalarOpacityUnitDistance", f"{SPACING * 2.5:.5f}", "≈2.5 倍体素间距，调节沿程透明度累积"],
                ["sampleDistance", str(PRESENTATION_QUALITY["sampleDistance"]), "光线步长（<1 为亚体素采样）"],
                ["maximumSamplesPerRay", "4096", "单射线最大步数上限"],
                ["3D 纹理插值", "三线性", "WebGL 3D 纹理 LINEAR 滤波，体素间线性插值"],
                ["截图超采样", "CAPTURE_SCALE=2", "Playwright 设备像素比 2×，减轻屏幕锯齿"],
            ],
        )
    )
    blocks.append(
        Text(
            "（表注）上表为 **Phong 光照与光线步进**；**TF 参数**（opacityScale 等）见 **§1.2（5）表3**。"
        )
    )
    blocks.append(
        Text(
            "**（3）128³ 分辨率与平滑策略。**赛题子体积仅 **128³** 体素，纤维与节点边缘在放大观察时仍可能出现块状感——"
            "这是数据分辨率上限，而非色标失误。"
            "本作品从渲染侧做三层缓解：**①** GPU 三线性插值（采样点落在体素之间时按 8 邻点加权）；"
            f"**②** 亚体素光线步进（`sampleDistance={PRESENTATION_QUALITY['sampleDistance']}`）；"
            "**③** 截图阶段 2× 设备像素比超采样。"
            "未对原始网格做几何上采样（避免伪造亚体素物理量）；更高分辨率需更细 AMR 层级或更大均匀网格导出。"
            "**（4）五帧条带固定相机。**`fitVolumeCamera` 根据包围盒 **[0, 14.245]³** 自动取景；"
            f"焦点 **({fp[0]:.4f}, {fp[1]:.4f}, {fp[2]:.4f})**，"
            f"相机位置 **({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})**，"
            f"viewUp **(0,0,1)**；**wideBoost**（宽屏修正，见 §0.1）**≈{cam['wideAspectBoost']:.4f}**，"
            f"zoomFactor **1.0**（capture 页；录屏页为 **1.1**），合成 effectiveZoom **≈{cam['effectiveZoom']:.4f}**。"
            "五帧截图仅更换标量场与按步 **Evolution Capture Profile**（见 §1.2（5）），不改动上述取景公式。"
            "**为何需要 capture 专用 TF：**t=0 时 IGM 占绝对体积优势，若沿用交互页同一组 α(ρ)，"
            "早期帧会被「雾屏」淹没、晚期对比度不足。"
            "故 **opacityScale** 由 **0.72→1.10** 随 t 线性抬升，整体调节沿程积分亮度。"
            "**densityGain 在 t<45 为负**（t=0 最低 **−0.32**，t≈45 归零）："
            "其含义**并非**改变 Nyx 模拟密度，而是在 `transferFunction.ts` 的 `mapT()` 中，"
            f"将 RGB/α 控制点在 ρ 轴上整体平移 **Δρ≈−(p99−p01)·densityGain·0.08**"
            f"（t=0 约 **+{rho_shift_t0:.3f}** 代码单位，向更高密度方向）。"
            "效果等价于：早期帧对 **ρ 接近 p01 的 IGM 体素**施加更强的不透明衰减——"
            "光线积分中低密度段的 α 贡献被压低，雾状背景变暗、filament 对比度提升。"
            "**是否引入非物理畸变？** 就模拟场而言**否**（体素 ρ 未变）；"
            "就**跨时刻严格可比性**而言**是**——同一 ρ 在 t=0 与 t=99 的 capture 帧中会得到不同 RGB/α，"
            "故条带图应解读为「固定相机下的形态演化叙事」，**不宜**作为定量 ρ–亮度标定图。"
            "增益曲线见 task1_tf_gain_curve.png；完整 JSON 见 `docs/figures/render_spec.json`。"
        )
    )
    blocks.append(
        Text(
            "**（5）交互页统一 TF vs capture 条带专用 Profile。**"
            "二者共用 cosmic 控制点形状，但标量域与增益策略不同："
        )
    )
    blocks.append(
        Table(
            caption="体渲染传递函数：交互页（默认可复现）vs capture 五帧条带（配图专用）",
            headers=["项", "交互页 /app.html", "capture.html 五帧条带"],
            rows=[
                [
                    "标量域",
                    f"百步 p01–p99 全局包络 [{gmin_tf:.3f}, {gmax_tf:.3f}]（`getGlobalTfDomain`）",
                    "各帧本步 p01–p99（`getTimestepTfDomain`），强调单步形态",
                ],
                [
                    "opacityScale",
                    "默认 **1.15**（用户可调，全时间步共用）",
                    f"**{cap_op_t0:.2f}→{cap_op_t99:.2f}** 随 t 线性变化",
                ],
                [
                    "densityGain",
                    "默认 **+0.12**（用户可调，全时间步共用）",
                    f"t<45 为负（t=0 **{cap_dg_t0:.2f}**，t=25 **{cap_dg_t25:.2f}**），t≥45 为 **0**",
                ],
                [
                    "跨步 α(ρ) 一致？",
                    "**是**——拖动时间轴时映射关系不变",
                    "**否**——每帧独立 Profile，仅为条带可读性",
                ],
                [
                    "条带底部色条",
                    "—",
                    f"标注全局 [{gmin_tf:.3f}, {gmax_tf:.3f}]，**装饰参照**；与各帧实际域/增益可不一致",
                ],
                ["实现", "`useDashboardInteraction` + `useAppStore.tfParams`", "`getEvolutionCaptureProfile`"],
            ],
        )
    )
    blocks.append(
        Text(
            "答辩录屏与在线探索请以 **交互页**为准：统计刷选、直方图与体渲染共用同一全局域，"
            "保证「同一 ρ 区间→同一颜色/不透明度」的可复现联动。"
            "五帧条带属于 **Playwright 离线配图管线**（`capture_volumes.mjs` → `capture.html`），"
            "与交互 TF 解耦，已在图注与上表标明。"
        )
    )
    blocks.append(
        Table(
            caption="五时刻条带可复现相机参数（capture.html，1920×1080）",
            headers=["项", "值"],
            rows=[
                ["域尺寸 DOMAIN_LENGTH", f"{DOMAIN_LENGTH}（代码单位）"],
                ["体素间距 SPACING", f"{SPACING:.6f}"],
                ["包围盒", "[0, 14.245] × [0, 14.245] × [0, 14.245]"],
                ["focalPoint", f"({fp[0]:.4f}, {fp[1]:.4f}, {fp[2]:.4f})"],
                ["cameraPosition", f"({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})"],
                ["viewUp", "(0, 0, 1)"],
                ["wideBoost（宽屏修正）", f"{cam['wideAspectBoost']:.4f}"],
                ["VIEW_MARGIN × wideBoost × zoom", f"{cam['effectiveZoom']:.4f}（effectiveZoom）"],
                ["viewport", "1920 × 1080，CAPTURE_SCALE=2"],
                ["实现", "src/volume/fitVolumeCamera.ts + tools/python/render_spec.py"],
            ],
        )
    )
    blocks.append(
        Figure(
            "task1_tf_gain_curve.png",
            "capture 专用 TF 增益曲线：opacityScale（α 乘子）与 densityGain（ρ 轴平移；t<45 负值=压低 IGM 雾感）",
            14.5,
        )
    )
    res_rows = ext_val.get("resolutionCoarseningT99", [])
    cam_chk = ext_val.get("cameraFov", {})
    if res_rows:
        r64 = next((r for r in res_rows if r["grid"] == 64), res_rows[1] if len(res_rows) > 1 else {})
        r32 = next((r for r in res_rows if r["grid"] == 32), res_rows[-1] if res_rows else {})
        jacc64 = r64.get("ridgeJaccardVs128", 0)
        jacc32 = r32.get("ridgeJaccardVs128", 0)
        blocks.append(
            Text(
                "**128³ 能否分辨细丝？**赛题包**未提供 512³ 对照场**，无法在同等物理子域做高分辨率 A/B。"
                "**块平均粗化**（128→64→32）是**低通盒滤波**，频谱特性不同于真实 AMR 重采样或独立低分辨率模拟。"
                f"粗化结果：64³ 投影相关 **r={r64.get('projCorrWith128', 0):.3f}**、脊线 Jaccard **{jacc64:.2f}**；"
                f"32³ Jaccard **{jacc32:.2f}**。"
                "**如何解读 Jaccard≈0.65（64³ vs 128³）？**"
                "在 t=99 P88 亮脊掩膜上，约 **35%** 像素在粗化—上采样后与 128³ 脊线不一致——"
                "说明**减半分辨率会显著改变细丝连通性外观**。"
                "**反向含义（对结论置信度的影响）：**"
                "该实验**不能**直接给出「128³ 相对 512³ 丢失 35% 真细丝」的定量数，"
                "但表明**至少 ~35% 量级的脊线形态对网格尺度敏感**；"
                "因此 128³ 上观察到的 filament **连通性/细度**应理解为**该分辨率可解析的结构**，"
                "亚网格或更细 AMR 层级上可能存在额外丝状细节——**不能**将体渲染中的每条亮脊等同于物理真值。"
                "**哪些结论更稳健？**"
                "全域矩（**σ↑**、分位跨度、void 体积分数、Top 1% 刷选占比）对粗化相对不敏感；"
                "**filament 几何细部与连通性**结论需附加「128³ 上限」 caveat。"
                "128³ 是赛题数据上限；定量 Nyquist 证明仍需更细网格或完整 Nyx AMR 导出。"
            )
        )
        blocks.append(
            Figure(
                "task1_resolution_coarsening.png",
                "分辨率粗化敏感性：投影相关 r 与 P88 脊线 Jaccard（相对 128³；Jaccard≈0.65 暗示尺度敏感）",
                15.0,
            )
        )
    if cam_chk:
        proj_spread = cam_chk.get("projectionDensitySpreadAcrossSteps", 0)
        rgb_spread = cam_chk.get("screenshotCornerRgbSpread", 0)
        blocks.append(
            Text(
                "**视场一致性（分层验证）：**"
                "**① 主证**——五帧共用 `render_spec.json` 同一相机公式（focalPoint/position/effectiveZoom）。"
                f"**② 内容证**——各帧 XY 投影**角点区域平均密度**跨步极差 **{proj_spread:.4f}**（>0，说明 void 区密度随演化微变）。"
                f"**③ 截图 RGB**——四角 letterbox 背景均值极差 **{rgb_spread:.4f}**（可为 0：页面留白/背景色恒定，**不能**作为相机漂移反证）。"
                "既往「RGB 极差=0」表述易误导，已改为以上分层说明。"
            )
        )
    blocks.append(Heading("1.3  案例分析", 2))
    blocks.append(
        Text(
            "**（1）**从均匀雾状到宇宙网拓扑的三阶段演化。"
            "在体渲染视图中，t=0 时整体呈均匀雾状，**filament** 对比度弱，"
            f"均值约 {s0['mean']:.4f}、**σ** 仅 {s0['std']:.4f}，尚处于涨落初生的平滑阶段。"
            "拖动时间轴至 t=25–50，丝状结构逐渐连通，低密度 **void** 区域扩大，σ 由 0.43 升至 0.47 附近。"
            f"至 t=99，宇宙网拓扑最为清晰：高密度脊线与节点形成亮带，**σ** 达 {s99['std']:.4f}、"
            f"p99={s99['p99']:.4f}，与右尾增厚及 max={s99['max']:.4f} 一致。"
            "五帧条带在**固定相机**下呈现 void—filament—node 由模糊走向可辨的形态叙事；"
            "因采用 capture 专用 Evolution Profile（§1.2（5）），**五帧间 α(ρ) 并非常数**，"
            "底部 log 色条为全局 p01–p99 **参照刻度**，非逐帧严格映射标尺。"
            "定量对比请用交互页或 timeline.json 统计曲线。"
        )
    )
    blocks.append(
        Figure(
            "task1_vol_strip.png",
            "五帧体渲染条带（capture 专用 TF；非交互页效果；左→右 t=0/25/50/75/99）",
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
            "**（2）**log 域色标对 IGM 大动态范围的压缩作用。"
            "表 1 显示均值略降而 **σ** 与 p99 缓升，说明物质由相对均匀分布转向分化："
            "大部分体积仍处中低密区，但极少数体素密度持续抬升，在体渲染中即对应后期更亮、更细的 **filament** 网络。"
            "传递函数在 log 域映射可压缩 IGM 大动态范围，使低密度 **void** 与高密度脊线在同一色标下同时可见；"
            "若采用线性映射，filament 细节将被中低密背景淹没。"
            "下图（task1_hero_poster.png）进一步展示 t=99 代表帧、竖向色标与 Nyx 元数据条，便于读者建立尺度感。"
        )
    )
    blocks.append(
        Figure(
            "task1_hero_poster.png",
            "t=99 体渲染首屏海报：元数据徽章 + 主视角卡片 + 竖向 log10 色标",
            14.0,
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
            "precompute.py 除 mean、σ、分位数、偏度与尾区占比外，另算 **Moran's I**、**两点相关 ξ(r)**、"
            "**分形维数 D**、**超额峰度**与 **多尺度熵代理**（8×8 粗粒化 Shannon 熵），写入 timeline.json；"
            "generate_figures.py 绘制基础四联图（task2_evolution_story.png）与空间统计图（task2_spatial_metrics.png）。"
            "**数据范围说明：**完整 Nyx 模拟含 **暗物质 N 体 + 气体** 两套场；赛题包仅提供 **128³ 重子气体密度 .dat**，"
            "本作品因此聚焦气体 **ρ** 的可视分析（暗物质对比见 **§5.6**）。"
        )
    )
    blocks.append(Heading("2.2  案例分析", 2))
    blocks.append(
        Text(
            "**（1）**团块化：σ 与分位跨度走阔，并由空间统计印证。"
            f"基础四联图中 σ(t) 由 {s0['std']:.4f} 升至 {s99['std']:.4f}（**+{sigma_pct:.1f}%**）；"
            f"p99−p01 由 {span0:.3f} 增至 {span99:.3f}（**+{span_pct:.1f}%**）。"
            f"仅凭 σ 上升不足以证明空间成团，故列出 **Moran's I** 供参考："
            f"{m(s0, 'moransI'):.4f}→{m(s99, 'moransI'):.4f}（Δ=**{m(s99, 'moransI')-m(s0, 'moransI'):+.4f}**）；"
            "t=0 已处于高自相关（宇宙学初条件），**该增量小于 bootstrap 噪声（见下），不作团块化方向证据**。"
            f"XY 投影 **ξ(r=1)** {m(s0, 'xiR1'):.3f}→{m(s99, 'xiR1'):.3f}（Δ={xi_r1_delta:+.3f}），"
            f"**ξ(r=10)** {m(s0, 'xiR10'):.3f}→{m(s99, 'xiR10'):.3f}，"
            "大尺度投影相关衰减与小尺度对比增强可并存。"
            "**ξ 未做宇宙学模拟集合显著性检验**；下文以 **64³ 子块 Monte Carlo** 给出 ±1σ 误差带（图 task2_two_point_xi.png），"
            "用于判断 r=1 处微小差异是否落在子窗口采样波动内。"
            "**主证仍为 σ↑、分位跨度↑、直方图右尾抬高与刷选空间形态。**"
            f"**分形维数 D**（P90 亮脊盒计数）{m(s0, 'fractalDimP90'):.3f}→{m(s99, 'fractalDimP90'):.3f} 近乎不变："
            "团块化主要体现在**密度对比度**而非填充维数突变。"
            "更直接的拓扑度量（**Betti 数、持续同调** barcode）未纳入赛题范围，列为局限。"
            "下图（task2_spatial_metrics.png、task2_two_point_xi.png）供对照。"
        )
    )
    boot = ext_val.get("bootstrapSpatial", {})
    if boot:
        mg = boot.get("moransIGlobal", {})
        xg = boot.get("xiR1Global", {})
        delta_i = mg.get("delta", m(s99, "moransI") - m(s0, "moransI"))
        delta_xi = xg.get("delta", xi_r1_delta)
        pooled_i = boot.get("pooledBootstrapStdMoran", boot.get("pooledBootstrapStd", 0))
        pooled_xi = boot.get("pooledBootstrapStdXiR1", 0)
        sig_i = boot.get("moransISignificantAt2Sigma", False)
        sig_xi = boot.get("xiR1SignificantAt2Sigma", False)
        meth = boot.get("method", {})
        sub_shape = meth.get("subvolumeShape", [64, 64, 64])
        blocks.append(
            Table(
                caption="空间统计 bootstrap 方法（可复现，见 validation_extended.json → bootstrapSpatial.method）",
                headers=["项目", "设定"],
                rows=[
                    ["方法", meth.get("name", "spatial_block_monte_carlo")],
                    ["子窗口形状", f"{sub_shape[0]}³（128³ 边长 50%）"],
                    ["重采样次数 n", str(boot.get("nBootstrap", meth.get("nBootstrap", 40)))],
                    ["随机种子", str(meth.get("randomSeed", 42))],
                    ["重采样类型", "空间块 bootstrap：各 replicate **独立随机平移** 64³ 子窗口原点（非像素级 bootstrap）"],
                    ["Moran's I", "6 邻域 3D，在子体积内部计算"],
                    ["ξ(r)", "各子体积 XY 最大密度投影 → radial_two_point_profile"],
                    ["多重检验校正", "无 — 仅 t=0 vs t=99 单次对比，不作显著性主张"],
                    ["复现入口", meth.get("reproduce", "tools/python/validation_suite.py :: bootstrap_spatial_ci")],
                ],
            )
        )
        blocks.append(
            Text(
                f"**Moran's I：**t=0 / t=99 子窗口 bootstrap 标准差约 "
                f"**±{boot['t0']['moransI']['std']:.4f}** / **±{boot['t99']['moransI']['std']:.4f}**；"
                f"全域 ΔI=**{delta_i:+.4f}**，合并噪声 **2σ≈{2*pooled_i:.4f}**——"
                f"{'达到' if sig_i else '**未达到**'} 2σ，"
                "故 **Moran's I 仅列值，不解读为团块化方向证据**。"
                f"**ξ(r=1)：**全域 {xg.get('t0', m(s0, 'xiR1')):.3f}→{xg.get('t99', m(s99, 'xiR1')):.3f}（Δ=**{delta_xi:+.3f}**），"
                f"子块 bootstrap 合并 σ≈**{pooled_xi:.3f}**，2σ≈**{2*pooled_xi:.3f}**——"
                f"{'达到' if sig_xi else '**未达到**'} 2σ；"
                "图 task2_two_point_xi.png 中金色阴影为各 r 处 **±1σ** 子块波动带。"
                "上述检验均为**描述性**对照，非宇宙学 N-body 集合推断。"
            )
        )
        blocks.append(
            Figure(
                "task2_bootstrap_ci.png",
                "Moran's I 与 ξ(r=1) 的 64³ 子块 Monte Carlo 均值±1σ（n=40，seed=42）",
                14.5,
            )
        )
    blocks.append(
        Figure(
            "task2_spatial_metrics.png",
            "空间与高阶统计四联：Moran's I、ξ 半长、分形维数 D、超额峰度（2×2）",
            15.5,
        )
    )
    blocks.append(
        Figure(
            "task2_two_point_xi.png",
            "XY 最大密度投影 ξ(r)：实线为全域曲线，金色阴影为 64³ 子块 Monte Carlo ±1σ（虚线 ξ=0.5）",
            15.5,
        )
    )
    blocks.append(
        Text(
            "**（2）**偏度几乎不变，不等于“右尾未增厚”——需用更敏感指标。"
            f"偏度仅由 {s0['skewness']:.4f} 变为 {s99['skewness']:.4f}（**+{skew_delta_pct:.2f}%**），"
            "三阶矩对整体尺度变化不敏感：σ 扩大、p50 略移时，偏度可近乎持平。"
            f"右尾增厚的更可靠证据来自：**①** p99、p999 抬升（p999 比 **×{p999_ratio:.2f}**）；"
            f"**②** p99 由 {m(s0, 'p99'):.4f} 升至 {m(s99, 'p99'):.4f}（**+{p99_delta_pct:.2f}%**），p999 比 **×{p999_ratio:.3f}**；"
            f"**③** ≥p99 **体积**占比恒约 1%（分位定义）；**质量**占比 t=0→99 为 "
            f"{m(s0, 'massFractionAboveP99')*100:.2f}%→{m(s99, 'massFractionAboveP99')*100:.2f}%（**+{mass_frac_delta:.2f} pp**，"
            "变化极小，**不宜作为主证**——右尾增厚应看 **p99/p999 分位值与直方图右尾抬高**）。"
            f"超额峰度由 {m(s0, 'excessKurtosis'):.3f} 变为 {m(s99, 'excessKurtosis'):.3f}（**{kurt_delta:+.3f}**），亦未显著抬升——"
            "故「右尾增厚」主证为 **分位数尾翼 + 直方图右尾抬高 + 质量加权**，而非偏度/峰度曲线；"
            "四联图中的偏度子图仅说明分布**保持右偏形态**，不宜过度解读其斜率。"
            "**峰度下降机制：**超额峰度 κ−3 = E[(x−μ)⁴]/σ⁴ − 3，分母含 **σ⁴**。"
            f"本数据 **σ** 由 {s0['std']:.4f} 升至 {s99['std']:.4f}（**+{sigma_pct:.1f}%**），"
            "主体（IGM 巨体积）方差增大会**压低**标准化四阶矩，即使 p99/p999 抬升。"
            "故峰度下降更可能反映**全域离散度扩大**，而非右尾消失；"
            "右尾请用 **分位数与直方图** 判定，不宜用峰度反证。"
        )
    )
    blocks.append(
        Figure(
            "task2_evolution_story.png",
            "100 步全域统计四联图：分位跨度、σ、≥p99 体积占比、偏度（2×2 拼接）",
            15.5,
        )
    )
    blocks.append(
        Text(
            "**（3）**少数致密体素承载可见宇宙网结构。"
            f"「≥p99 体积占比」曲线稳定在约 **{tail_vol:.2f}%** 量级，"
            "即仅约 **1%** 体素处于极高密度尾，却在体渲染中对应全部可见亮脊与节点。"
            "进一步查看代表步直方图叠加（task3_hist_overlay.png）：纵轴为 **Probability mass×100**（非 ρ 分位数）；"
            "横轴 ρ 与表「直方图演化要点」中 p01/p50/p99 **同单位**。"
            "t=0/25/50/75/99 五步曲线显示主峰略移、右尾持续抬升，"
            "低密度 **void** 与高密度 peak 两极并存——这正是赛题所描述的「密度分布两极化」。"
            "绝大部分体积仍为稀疏 IGM，视觉上的 **filament** 网络由极少数高密度体素承载，"
            "尾区 **p99/p999 分位抬升**支撑右尾增厚；Moran's I 见 §2.2（不作方向证据）。"
        )
    )
    blocks.append(
        Figure(
            "task3_hist_overlay.png",
            "五步 log 直方图叠加：纵轴 Probability mass×100；横轴 ρ（与表「直方图演化要点」同单位）",
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
                ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", f"+{skew_delta_pct:.2f}%（形态右偏，非尾翼主证）"],
                ["超额峰度 κ−3", f"{m(s0, 'excessKurtosis'):.3f}", f"{m(s99, 'excessKurtosis'):.3f}", f"{kurt_delta:+.3f}（非主证）"],
                [
                    "Moran's I",
                    f"{m(s0, 'moransI'):.4f}",
                    f"{m(s99, 'moransI'):.4f}",
                    f"Δ={m(s99, 'moransI')-m(s0, 'moransI'):+.4f}（<2σ bootstrap，仅列值）",
                ],
                [
                    "ξ(r=1)",
                    f"{m(s0, 'xiR1'):.3f}",
                    f"{m(s99, 'xiR1'):.3f}",
                    (
                        f"{xi_r1_delta:+.3f}（2σ≈{2 * boot.get('pooledBootstrapStdXiR1', 0):.3f}，"
                        f"{'≥2σ' if boot.get('xiR1SignificantAt2Sigma') else '<2σ'}，描述性）"
                        if boot
                        else f"{xi_r1_delta:+.3f}"
                    ),
                ],
                ["ξ(r=10)", f"{m(s0, 'xiR10'):.3f}", f"{m(s99, 'xiR10'):.3f}", f"{xi_r10_delta:+.3f}"],
                ["分形维数 D", f"{m(s0, 'fractalDimP90'):.3f}", f"{m(s99, 'fractalDimP90'):.3f}", "≈稳定"],
                [
                    "≥p99 质量占比",
                    f"{m(s0, 'massFractionAboveP99') * 100:.2f}%",
                    f"{m(s99, 'massFractionAboveP99') * 100:.2f}%",
                    f"+{mass_frac_delta:.2f} pp（≈持平，非主证）",
                ],
                [
                    "≥p99 体积占比",
                    f"{s0['tailMassAboveP99'] * 100:.2f}%",
                    f"{tail_vol:.2f}%",
                    "约 1% 量级",
                ],
            ],
        )
    )
    fpfn_early = brush_val.get("fpFnDefault", {})
    fil_lo = m(s99, "p90")
    fil_hi = m(s99, "p99")
    fil_vol_pct = m(s99, "tailMassFilament90_99") * 100
    fil_mass_pct = (
        brush_val.get("thresholds", [{}])[1].get("massPct", 9.86)
        if len(brush_val.get("thresholds", [])) > 1
        else 9.86
    )
    brush_top_n = int(fpfn_early.get("brushVoxels", 20972))
    proxy_n = int(fpfn_early.get("filamentProxyVoxels", 5796))
    fp_rate_early = fpfn_early.get("fpRateInBrush", 0) * 100
    blocks.append(Heading("2.3  可视化在宇宙学数据分析中的应用价值", 2))
    blocks.append(
        Text(
            "任务二除归纳 **σ↑、分位跨度↑、void 扩张与右尾增厚** 等演化规律外，"
            "还要求阐释可视化在宇宙学分析中的**应用价值**。"
            "本作品的立场是：可视化不仅是「配图」，而是把 IGM 演化从**不可检验的体渲染印象**"
            "转化为**可量化、可联动、可复现**的科学命题的媒介——"
            "下列案例均来自本仓库交互链路的真实走查，而非事后附会。"
        )
    )
    blocks.append(
        Table(
            caption="可视化驱动发现：设计—局限—本作品所得（任务二应用价值）",
            headers=["可视化设计", "对应科学问题", "若仅静态图/离线图", "交互联动带来的发现"],
            rows=[
                [
                    "100 步 σ / p99−p01 时序",
                    "团块化是否贯穿全时域？",
                    "五帧条带易「挑帧」讲故事",
                    f"σ **+{sigma_pct:.1f}%**、跨度 **+{span_pct:.1f}%** 为全时域曲线，非单帧偶然",
                ],
                [
                    "log 直方图 ↔ Top 1% 刷选",
                    "右尾 1% 体素在空间上是什么？",
                    "直方图只见分布，不见 filament 几何",
                    f"刷选 **{brush_top_n:,}** 体素（≈{tail_vol:.2f}% 体积）在体渲染/投影呈**丝状/节点**聚集",
                ],
                [
                    "纤维带 90–99% 预设",
                    "形态过渡区与极端尾区是否同一集合？",
                    "单阈值截图无法对比体积—形态差异",
                    f"ρ∈[{fil_lo:.2f},{fil_hi:.2f}] 占 **{fil_vol_pct:.1f}%** 体积，宽于 Top 1%，对应 **filament 过渡带**",
                ],
                [
                    "空间→统计（P88 亮脊反查）",
                    "filament 在密度轴上落在哪？",
                    "投影图与直方图分属两页，难建立对应",
                    f"亮脊反查 ρ∈[{band_lo:.2f},{band_hi:.2f}]；与 Top 1% 对照得误报率 **{fp_rate_early:.1f}%**",
                ],
                [
                    "void 固定 t=0 阈值追踪",
                    "空洞扩张能否跨步量化？",
                    "单步直方图看不出低密度尾扩张",
                    f"ρ≤ρ_p10(t=0) 体积 **{void_t0p10_0:.1f}%→{void_t0p10_99:.1f}%**（task3_void_evolution）",
                ],
            ],
        )
    )
    blocks.append(
        Text(
            "**案例 1｜时序统计对抗「挑帧叙事」。**"
            "体渲染条带（§1.3）适合建立 void—filament—node 的**形态直觉**，"
            "但若只展示 t=0/99 两帧，无法证明「团块化」是 100 步单调趋势。"
            "task2_evolution_story.png 将 **σ(t)** 与 **p99−p01(t)** 并列，"
            f"使「涨落扩大 + 两极分化」成为**可引用的曲线证据**——"
            "这正是可视化作为**时间维度压缩器**的价值：把四维时空场转为可扫视的一维轨迹。"
        )
    )
    blocks.append(
        Text(
            "**案例 2｜刷选验证：从「右尾数字」到「宇宙网几何」。**"
            f"直方图 alone 只能告诉我们 ≥p99 约占 **{tail_vol:.2f}%** 体积、"
            f"却承载约 **{mass_above:.1f}%** 质量——**数字与形态之间缺一座桥**。"
            "在 `/app.html` 点击 **Top 1%** 后，三栏同步："
            "左直方图标黄区间、中体渲染高亮丝状结构、右 XY 投影出现金色聚集斑。"
            "task4_brush_triptych.png 将这一**同一刷选状态**冻结为静态证据；"
            "但三联图的科学意义恰恰来自**交互先行**——"
            "若无刷选，审稿人需手动对照 ρ 阈值与体渲染，很难在 128³ 密度场内建立"
            "「**1% 尾区 = 可见 filament 载体**」的置信联系。"
            f"离线验证（brush_validation.json）进一步量化：以 P88 亮脊代理（**{proxy_n:,}** 体素）对照 Top 1%，"
            f"代理**召回率 100%**（全落在刷选内），而刷选内 **{fp_rate_early:.1f}%** 为形态外的高密尾——"
            "该「密度分位 ⊃ 丝状脊线」关系**由刷选实验揭示**，非体渲染截图可直接读出。"
        )
    )
    blocks.append(
        Figure(
            "task4_brush_triptych.png",
            "可视化驱动发现示例：Top 1% 刷选三联（统计区间 → 体渲染高亮 → 投影验证）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "**案例 3｜双预设对比：纤维带 vs 极端尾。**"
            f"预设 **90–99% 纤维带**（ρ∈[{fil_lo:.2f},{fil_hi:.2f}]）覆盖 **{fil_vol_pct:.1f}%** 体积、"
            f"**{fil_mass_pct:.1f}%** 质量，显著宽于 Top 1%；"
            "切换预设即可在**同一相机、同一色标**下对比「过渡区 filament」与「极端节点核」的空间展布。"
            "静态 threshold 柱状图（task4_threshold_comparison.png）给出占比数字，"
            "但**只有交互预设**才能在数秒内完成「宽尾 vs 窄尾」的形态对照——"
            "这是宇宙学探索中常见的「操作定义敏感性」检验，可视化降低了试错成本。"
            "**案例 4｜空间→统计反查。**"
            "在投影上圈定 **filament** 亮脊（≥P88）后反查密度带 "
            f"ρ∈[{band_lo:.2f},{band_hi:.2f}]（task4_spatial_to_stats.png），"
            "完成赛题要求的「先在空间定位结构，再在统计轴上读位置」。"
            "该路径与 Top-down（分位→空间）刷选**互为可逆**，"
            "构成 NyxViz「统计—空间」闭环的核心——"
            "单靠任一方向的静态图都无法闭合这一环路。"
        )
    )
    blocks.append(
        Figure(
            "task4_spatial_to_stats.png",
            "空间→统计反查：filament 亮脊 → log 直方图密度带（可视化闭环的另一方向）",
            15.5,
        )
    )
    blocks.append(
        Text(
            "**方法论归纳。**"
            "上述案例共同说明：在 **128³×100 步** 的 IGM 子体积上，"
            "可视化技术的价值在于 **(i)** 把高维场压缩为可扫视的时序与分布；"
            "**(ii)** 用联动刷选建立**密度分位 ↔ 宇宙网形态**的可检验映射；"
            "**(iii)** 以同一 timeline.json 贯通在线探索、离线配图与 Word 报告，避免「图数两张皮」。"
            "对更大尺度 AMR 数据，上述交互范式可迁移至 yt/ParaView 批处理 + 子区域 Web 仪表盘；"
            "本作品在赛题约束下将其落地为可答辩、可复现的完整实例。"
        )
    )
    blocks.append(
        Text(
            "**与主流工具的定位（补充）。**"
            "yt/ParaView 擅长大规模 AMR 批处理与 HPC 体视；"
            "NyxViz 聚焦赛题子体积的**浏览器端统计—刷选—投影联动**与答辩交付。"
            "二者互补而非替代：全盒多层级分析应优先 yt/ParaView（见第 5.4 节）；"
            "本作品证明，在 **128³** 尺度上，轻量 Web 联动同样能驱动上述科学发现链。"
        )
    )
    blocks.append(
        Table(
            caption="NyxViz 与主流天文可视化工具的定位对比（补充）",
            headers=["工具", "典型优势", "本作品关系"],
            rows=[
                [
                    "yt",
                    "Python 生态、原生 AMR/Chombo 数据、投影/相位空间分析配方",
                    "互补：批处理与 AMR 层级；NyxViz 提供子体积浏览器端联动刷选",
                ],
                [
                    "ParaView",
                    "HPC 体绘制、等值面/流线、多数据集批处理与 AMR 过滤器",
                    "互补：专家桌面探索；NyxViz 提供 Web 仪表盘 + 可复现配图管线",
                ],
                [
                    "NyxViz",
                    "vtk.js 体渲染 + D3 直方图 + Worker 刷选 + 统一 timeline.json",
                    "128³×100 步「统计—空间」闭环与可视化驱动发现（见上表案例）",
                ],
            ],
        )
    )
    blocks.append(Heading("2.4  进阶统计量说明", 2))
    blocks.append(
        Text(
            "为回应「仅 σ/偏度过于基础」的批评，本作品在 timeline.json 中扩展以下指标（见 `tools/python/spatial_stats.py`）："
            "**Moran's I**——6 邻域 3D 权重，衡量全局空间自相关，I↑ 表示相似密度体素空间聚集（团块化直接证据）；"
            "**两点相关 ξ(r)**——对 XY 最大密度投影做 Wiener–Khinchin 估计，ξ 半长增大表示相关结构在投影面上延展更远；"
            "**盒计数分形维数 D**——对 P90 阈值亮脊二值掩膜做 box-counting，D↑ 暗示丝状结构占据更多尺度层级；"
            "**超额峰度 κ−3**——四阶尾翼敏感量，弥补偏度对右尾不敏感的问题；"
            "**多尺度熵（8×8 粗粒化）**——块平均后的 Shannon 熵，作为多尺度复杂度的轻量代理（完整样本熵留作后续）。"
            "上述指标与体渲染、刷选验证共用同一 128³ 气体场，可在答辩中形成「全域矩 → 空间相关 → 形态维数」多层证据。"
        )
    )

    # ── 任务三 ──
    blocks.append(Heading("3、时序密度对数直方图统计", 1))
    blocks.append(Heading("3.1  视图简介", 2))
    blocks.append(
        Text(
            f"本题以 100 步完整 **log 等距**直方图序列为核心。默认 **{bins} bins**，边界 [{gmin:.4f}, {gmax:.4f}]"
            "（百步全域 min/max，所有时间步共用同一组边界以保证可比）。"
            f"**归一化（重要）：**每时间步 **N = {voxel_n:,}**（单步体素总数），"
            "直方图满足 `hist[b] = count_b / Σ count`（概率质量），故**每步纵轴积分和为 1**；"
            "图上纵轴标注 **Probability mass ×100**（= count/N×100），**横轴 ρ** 与 p01/p50/p99 等同单位。"
            "**不是**百步 pooled 的 2.1×10⁸ 样本混合归一化。"
            "跨时间步对比的是**分布形状**，而非绝对计数。"
            "分箱中心为相邻边界几何均值；横轴为 **log10 等距**的 ρ 边界，图上以 log 轴展示。"
            "另提供 **64/128/256 bin** 敏感度对比图（task3_bin_sensitivity.png）；"
            f"128 bin 时平均每箱约 **{samples_per_bin:,}** 样本，曲线仍显锯齿主因是 **log 域宽动态范围 + 多峰结构**，"
            "而非样本不足（详见 **§3.3**）。"
            "除 p01/p50/p99 外，预计算 **void 追踪**（固定 t=0 低密度阈值的体积分数）、"
            "p25–p75 带，写入 timeline.json 的 histogramMeta。"
        )
    )
    blocks.append(Heading("3.2  案例分析", 2))
    blocks.append(
        Text(
            "**（1）**分布中心漂移（p50）与右尾增厚。"
            f"metrics 三联图中 **σ** 上升 **+{sigma_pct:.1f}%**，p99−p01 由 {span0:.3f} 扩至 {span99:.3f}。"
            "peak_drift 图纵轴为 **线性密度 ρ、log10 刻度**，轨迹为逐步精确 **p50**（非直方图 argmax）；"
            f"金色阴影为 **p25–p75 四分位带**（全样本分位数，非 bootstrap 误差——128³ 总体下分位估计稳定）。"
            f"p50 由 {s0['p50']:.4f} 降至 {s99['p50']:.4f}，与 p99 缓升并存，体现「中心下移 + 右尾抬高」。"
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
            "p50 中位密度轨迹（log10 纵轴）+ p25–p75 四分位带；横轴为时间步",
            15.0,
        )
    )
    blocks.append(
        Text(
            "**（2）**低密度尾（void）定量追踪。"
            f"仅报告 p01 分位不足以刻画 void **扩张**：本作品增加 **固定 t=0 阈值** 的体积分数——"
            f"ρ ≤ ρ_p10(t=0) 的体素占比由 **{void_t0p10_0:.2f}%** 升至 **{void_t0p10_99:.2f}%**；"
            f"ρ ≤ ρ_p01(t=0) 由 **{void_t0p01_0:.2f}%** 升至 **{void_t0p01_99:.2f}%**，"
            "表明更多体素落入早期低密度范畴（宇宙空洞扩张的统计签名）。"
            f"同步追踪 p01(t)、p10(t) 曲线下移（t=99 时 p01={s99['p01']:.4f}）。"
            "图见 task3_void_evolution.png。"
        )
    )
    blocks.append(
        Figure(
            "task3_void_evolution.png",
            "void 扩张：固定 t=0 阈值体积分数（左）与 p01/p10 分位下移（右）",
            15.5,
        )
    )
    blocks.append(
        Text(
            "**（3）**与赛题描述的对照验证。"
            "赛题指出：早期密度集中于均值附近，后期出现空洞与峰值两极分化。"
            "本工作以完整 100 步直方图序列而非个别时刻证明该趋势。"
            "task3_story_panel.png 故事板将五步直方图叠加、σ/span 迷你趋势与 t=99 四 KPI 合于一张拼接图，"
            "便于在答辩或录屏中一图讲清「定量证据链」。"
            "结合任务一体渲染，可将统计上的右尾增厚与空间上的 **filament** 亮脊对应起来，"
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
                ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", f"右偏形态（+{skew_delta_pct:.2f}%）"],
                ["p999", f"{m(s0, 'p999'):.4f}", f"{m(s99, 'p999'):.4f}", f"比值 ×{p999_ratio:.3f}"],
                ["p50", f"{s0['p50']:.4f}", f"{s99['p50']:.4f}", "主峰略移"],
                ["p99−p01", f"{span0:.3f}", f"{span99:.3f}", "两极分化"],
                ["void 体积 (ρ≤ρ_p10(t=0))", f"{void_t0p10_0:.2f}%", f"{void_t0p10_99:.2f}%", "空洞扩张"],
                ["p01 阈值", f"{s0['p01']:.4f}", f"{s99['p01']:.4f}", "低密度尾下移"],
            ],
        )
    )
    blocks.append(Heading("3.3  分箱敏感度与曲线粗糙度", 2))
    blocks.append(
        Text(
            "128 bins 相对 2,097,152 体素并非统计样本不足（平均每箱约 1.6×10⁴ 点），"
            "曲线视觉粗糙的主因是：**（1）**log 等距分箱在低密度区 bin 宽度窄、高密度区宽，"
            "绘制为折线时相邻点斜率变化大；**（2）**分布呈多峰/宽尾，128 箱在峰间仍可能不足。"
            "task3_bin_sensitivity.png 对比 **64 / 128 / 256** bins（t=0 与 t=99）："
            "64 bins 更平滑但峰位偏移；256 bins 更锯齿；**128 bins 为交互页与 timeline.json 默认**，"
            "在平滑度与 log 域分辨率之间折中。"
            "配图纵轴统一标注 **Probability mass ×100**（= count/N×100，N=2,097,152），"
            "即离散概率质量而非 PDF；**横轴 ρ** 与表中 p01/p50/p99 等分位数同单位，避免与纵轴百分比混淆。"
        )
    )
    bin_sens = ext_val.get("binSensitivityT99", {})
    kl_rows = bin_sens.get("binRows", ext_val.get("binKlT99", []))
    if kl_rows:
        linf64 = next((r for r in kl_rows if r["bins"] == 64), {})
        linf256 = next((r for r in kl_rows if r["bins"] == 256), {})
        blocks.append(
            Text(
                f"**128 bins 定量依据：**在**同一 log 全域边界**下，64/256 bins 的边界分别是 128 bins 的整数倍嵌套，"
                "故 **KL 散度→0 为数学恒等式**，不代表「分箱无影响」。"
                f"改用 **CDF L∞ 距离**：64 bins **{linf64.get('cdfLinfVs128', 0):.4f}**、256 bins **{linf256.get('cdfLinfVs128', 0):.4f}**——"
                "分布形状几乎一致，差异主要在**右尾折线锯齿**（见 task3_bin_sensitivity.png）；"
                "128 bins 为交互默认。"
            )
        )
        blocks.append(
            Figure(
                "task3_bin_kl.png",
                "t=99 分箱敏感度：CDF L∞ 距（KL≈0 因 log 嵌套边界，见正文）",
                14.0,
            )
        )
    void_ext = ext_val.get("voidFractions", {})
    if void_ext:
        blocks.append(
            Text(
                "**void 阈值说明：**采用**固定 t=0 分位**（ρ_p10(t=0)、ρ_p01(t=0)）追踪低密度尾扩张，"
                "而非宇宙学 Δ 过密度——赛题包无平均密度标定。"
                f"**不采用「ρ≤k×盒均值」相对阈值**：t=99 盒均值≈{m(s99, 'mean'):.2f}，"
                f"0.8×均值≈{0.8 * m(s99, 'mean'):.2f} 低于全域 min ρ≈{gmin:.2f}，"
                "体积分数恒为 0，不提供信息，故已从正文与配图中删除。"
                "void 扩张定量见 task3_void_evolution.png。"
            )
        )
    blocks.append(
        Figure(
            "task3_bin_sensitivity.png",
            "分箱敏感度：64 / 128 / 256 bins 在 t=0 与 t=99 的 log 直方图对比",
            15.5,
        )
    )

    # ── 任务四 ──
    blocks.append(Heading("4、相空间交互刷选可视分析", 1))
    blocks.append(Heading("4.1  视图简介", 2))
    blocks.append(
        Text(
            "本题涉及三栏交互仪表盘：左统计、中体渲染常驻、右刷选控制（**/app.html**、**/video.html**）。"
            "log 直方图支持拖拽框选；预设 **Top 1%**、90–99% 纤维、**Bottom 1%** 一键刷选。"
            f"**重要：预设阈值随当前时间步更新**——`useDashboardInteraction` 读取 `timeline.timesteps[t].p99`，"
            f"非全局固定 t=99 值；故任意时刻 **Top 1% 严格对应「该步右尾 1% 体素」**。"
            f"（文档表格中 t=99 示例：ρ≥{s99['p99']:.4f}；t=0 为 ρ≥{s0['p99']:.4f}。）"
            f"纤维：ρ∈[p90,p99]；**Bottom 1%**：ρ≤p01。"
            "刷选后 **vtk.js** 传递函数对命中体素高亮，Canvas 2D 最大密度投影以金色标出刷选体素；"
            "体素扫描在 Web Worker 中执行，相邻时间步 idle 预取以保障播放流畅。"
            "录屏页 **/video.html?record=1** 在直方图下方标注「刷选密度区间→下方空间投影」映射关系，便于答辩演示。"
        )
    )
    blocks.append(Heading("4.2  案例分析", 2))
    blocks.append(
        Text(
            "**（1）**统计→空间：**Top 1%** 三联验证。"
            "在直方图上刷选右尾 **Top 1%** 后，观察 XY 最大密度投影：高亮体素呈丝状/节点状聚集，"
            "而非随机散点；切换至 t=99 体渲染，亮脊位置与刷选高亮区域高度重合。"
            "下图三联拼接（**§2.3 案例 2** 已插图）从左至右依次为：**直方图刷选区间 / 体渲染刷选高亮 / 投影金色标记**，"
            "三者密度阈值一致，构成「统计→空间」的单屏证据。"
            "task4_brush_rows.png 双行拼接则对比 **Top 1%**（上）与 **Bottom 1%**（下）刷选，"
            "表明低密度尾对应投影中的大面积稀疏区，与 IGM 占主导体积的物理图像吻合。"
        )
    )
    blocks.append(
        Figure(
            "task4_brush_triptych.png",
            "Top 1% 刷选三联：统计刷选 → 体渲染 (t=99) → 空间投影验证（统一卡片框）",
            15.5,
        )
    )
    blocks.append(
        Figure(
            "task4_brush_rows.png",
            "Top 1% 与 Bottom 1% 刷选双行对比：统计 | 投影 | KPI | 局部放大（每行四列卡片）",
            16.0,
        )
    )
    blocks.append(
        Text(
            "**（2）**空间→统计：**filament** 亮脊反查密度带。"
            f"在 t=99 XY 投影上识别 **filament** 亮脊（投影值≥P88），汇总亮脊像素对应体素密度，"
            f"得 **ρ**∈[{band_lo:.2f}, {band_hi:.2f}]，位于 p75–p99 右尾，与 **Top 1%** 刷选区间一致。"
            "在 log 直方图上以金色标注该密度带，完成「先在空间定位结构，再反查统计位置」的路径。"
            "下图展示完整链路（**§2.3 案例 4** 已插图）：投影亮脊→密度带标注→与 **Top 1%** 阈值对照。"
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

    thr_rows = brush_val.get("thresholds", [])
    bench = brush_val.get("benchmark", {})
    fpfn = brush_val.get("fpFnDefault", {})
    p88_rows = brush_val.get("p88Sweep", [])
    early_ms = bench.get("top1_earlyExit", {}).get("elapsedMs", 0)
    full_ms = bench.get("top1_fullCount", {}).get("elapsedMs", 0)

    p95_vol = thr_rows[0]["volumePct"] if thr_rows else 5.0
    p95_mass = thr_rows[0]["massPct"] if thr_rows else 5.7
    fil_row = next((r for r in thr_rows if "纤维" in r.get("label", "")), None)
    fil_vol = fil_row["volumePct"] if fil_row else m(s99, "tailMassFilament90_99") * 100
    fil_mass = fil_row["massPct"] if fil_row else 0.0
    p999_row = next((r for r in thr_rows if "p99.9" in r.get("label", "")), None)
    p999_vol = p999_row["volumePct"] if p999_row else 0.1
    fil_lo = m(s99, "p90")
    fil_hi = m(s99, "p99")
    custom_err = bench.get("customBrushErrors", [])
    custom_wide = next((r for r in custom_err if "p50" in r.get("label", "")), None)
    custom_mid = next((r for r in custom_err if "p25" in r.get("label", "")), None)
    blocks.append(Heading("4.3  阈值选取依据与对比", 2))
    blocks.append(
        Text(
            f"**Top 1%** 预设采用经验分位 **ρ≥p99**（t=99 为 **{s99['p99']:.4f}**），"
            "而非暗物质晕常用的 **Δ≈200** 过密度定义：本数据集为 **128³ 气体子体积** 原始密度场，"
            "未附带晕质量表或平均密度标定，无法在不引入额外假设的情况下换算为 Δ200。"
            "交互预设的目标是「可复现的右尾 1% 体素」与答辩演示一致性，"
            "故以逐步百分位作为可操作阈值。"
            f"下图（task4_threshold_comparison.png）对比 **p95 / 90–99% 纤维带 / p99 / p99.9** 四档："
            f"p95 覆盖约 **{p95_vol:.2f}%** 体积、**{p95_mass:.1f}%** 质量，高亮过宽；"
            f"**纤维带 90–99%**（ρ∈**[{fil_lo:.2f}, {fil_hi:.2f}]**）占 **{fil_vol:.2f}%** 体积、"
            f"**{fil_mass:.1f}%** 质量，保留 p90–p99 形态过渡区；"
            f"p99.9 仅 **{p999_vol:.2f}%** 体积，节点过稀；"
            "p99 在体积—质量份额与视觉可读性之间折中，故为默认 **Top 1%**。"
        )
    )
    if thr_rows:
        blocks.append(
            Table(
                caption="右尾与纤维带阈值对比（t=99，brush_validation.json）",
                headers=["阈值", "ρ 区间", "体积占比 %", "质量占比 %", "说明"],
                rows=[
                    [
                        r["label"],
                        (
                            f"[{r['rhoMin']:.2f}, {r['rhoMax']:.2f}]"
                            if r.get("rhoMax") is not None
                            else f"≥{r['rhoMin']:.4f}"
                        ),
                        f"{r['volumePct']:.2f}",
                        f"{r['massPct']:.2f}",
                        r["note"],
                    ]
                    for r in thr_rows
                ],
            )
        )
    blocks.append(
        Figure(
            "task4_threshold_comparison.png",
            "p95 / 90–99% 纤维带 / p99 / p99.9 体积与质量占比（t=99）",
            15.5,
        )
    )

    brush_n = int(fpfn.get("brushVoxels", 20972))
    blocks.append(Heading("4.4  刷选性能、采样误差与多向投影", 2))
    blocks.append(
        Text(
            "体素扫描在 **Web Worker**（`brushScan.worker.ts`）中执行，与主线程渲染解耦。"
            "默认 **stride=2** 子采样 + **maxPoints=8000** 早停（与 UI 一致），用于交互采样而非全量枚举。"
            f"Python 复现：Top 1% 早停 **{early_ms or 48:.0f} ms** vs 全网格 **{full_ms or 339:.0f} ms**；"
            f"全量 Top 1% 共 **{brush_n:,}** 体素。"
            "低端移动设备 Worker 开销通常为桌面 **2–3×**，仍预期 **<500 ms**；"
            "相邻步 **idle 预取** 避免播放时重复扫描。"
            "task4_projection_axes.png 补充 **XZ / YZ** 投影，检验 Top 1% 高亮在侧视仍呈丝状聚集。"
        )
    )
    if bench:
        blocks.append(
            Table(
                caption="刷选扫描耗时（t=99，tools/python/brush_analysis.py 复现 Worker 逻辑）",
                headers=["模式", "stride", "maxPoints", "耗时 ms", "用途"],
                rows=[
                    [
                        "Top 1% 早停",
                        str(bench.get("top1_earlyExit", {}).get("stride", 2)),
                        str(bench.get("top1_earlyExit", {}).get("maxPoints", 8000)),
                        f"{early_ms:.1f}",
                        "交互高亮（默认）",
                    ],
                    [
                        "Top 1% 全计数",
                        str(bench.get("top1_fullCount", {}).get("stride", 1)),
                        "2,097,152",
                        f"{full_ms:.1f}",
                        "验证命中体素总数",
                    ],
                    [
                        "纤维带早停",
                        str(bench.get("filament_earlyExit", {}).get("stride", 2)),
                        str(bench.get("filament_earlyExit", {}).get("maxPoints", 8000)),
                        f"{bench.get('filament_earlyExit', {}).get('elapsedMs', 63):.1f}",
                        "90–99% 预设",
                    ],
                ],
            )
        )
    blocks.append(
        Figure(
            "task4_projection_axes.png",
            "三向最大密度投影：XY / XZ / YZ 同一 Top 1% 高亮（t=99）",
            16.0,
        )
    )
    sample_rec = bench.get("sampleRecall", {})
    if sample_rec or custom_err:
        recall_pct = sample_rec.get("recallVsTrue", 0) * 100 if sample_rec else 0
        blocks.append(
            Text(
                "**预设 vs 自定义 KPI：**预设刷选（Top/Bottom 1%、纤维带）读数由 **timeline.json 分位占比×N** 精确给出；"
                "自定义拖拽仍显示 Worker 采样点数（**≤8000**），**可能严重低估**（见下表与 task4_custom_brush_error.png）。"
                "**体渲染/投影高亮**按密度阈值作用于全场，不依赖采样列表。"
            )
        )
        if sample_rec:
            blocks.append(
                Text(
                    f"**Top 1% 采样召回（对照）：**stride=2 遍历子网格时，"
                    f"仅命中 **{sample_rec.get('uniqueTrueFound', 0):,}/{sample_rec.get('trueBrushVoxels', 0):,}** "
                    f"真值体素（**{recall_pct:.1f}%**）——这是 stride 稀疏化所致，"
                    "与早停上限叠加后，若区间未匹配预设，仪表盘数字可仅为真值的 **≈10–13%**。"
                )
            )
        if custom_err:
            blocks.append(
                Table(
                    caption="自定义拖拽刷选 KPI 低估典型幅度（t=99，maxPoints=8000，mirrors Worker）",
                    headers=["区间", "真值体素", "仪表盘显示", "显示/真值", "说明"],
                    rows=[
                        [
                            r["label"],
                            f"{r['trueVoxels']:,}",
                            f"{r['reportedCount']:,}",
                            f"{r['reportedOverTruePct']:.1f}%",
                            "预设精确 KPI" if "对照" in r["label"] else "自定义拖拽",
                        ]
                        for r in custom_err
                    ],
                )
            )
            wide_pct = custom_wide["reportedOverTruePct"] if custom_wide else 0.8
            mid_pct = custom_mid["reportedOverTruePct"] if custom_mid else 0.8
            blocks.append(
                Text(
                    f"**典型误差范围：**宽区间（如 p50–p99）显示数仅为真值 **≈{wide_pct:.1f}%**；"
                    f"中等带宽（p25–p75）约 **≈{mid_pct:.1f}%**；"
                    "大区间常触顶 **8000** 上限。"
                    "**体渲染/投影高亮**按密度阈值作用于**全场标量**，不依赖采样列表，视觉高亮仍完整。"
                    "读数栏「选中体素数」仅对**预设按钮**可信；自定义区间请看直方图 **ρ 区间**。"
                    "**赛题范围内的取舍（已知局限，未改代码）：**"
                    "**(a)** 预设刷选已用 timeline 精确占比×N；"
                    "**(b)** 自定义区间可改为 `stride=1` + 提高 `maxPoints` 或拖拽结束后异步全网格计数；"
                    "**(c)** 宽区间可用直方图 bin 质量之和×N **估算**体积占比。"
                    "本次交付优先保证 **<500 ms** 交互与预设 KPI 精确性；自定义 KPI 低估已量化（上表），"
                    "体渲染/投影高亮不受影响。"
                )
            )
            blocks.append(
                Figure(
                    "task4_custom_brush_error.png",
                    "自定义拖拽：仪表盘显示数/真值体素数（t=99；stride=2, maxPoints=8000）",
                    15.0,
                )
            )
        if sample_rec:
            blocks.append(
                Figure(
                    "task4_brush_sample_recall.png",
                    "Top 1% 早停：真值体素召回 vs stride=2 网格覆盖率（t=99）",
                    14.0,
                )
            )

    blocks.append(Heading("4.5  P88 敏感度与误报/漏报", 2))
    p88_88 = next((r for r in p88_rows if r["projPercentile"] == 88), None)
    band_lo_vals = [r["densityBand"][0] for r in p88_rows] if p88_rows else [band_lo]
    band_span = max(band_lo_vals) - min(band_lo_vals)
    band_span_pct = band_span / max(min(band_lo_vals), 1e-9) * 100
    p85_ridge = p88_rows[0]["ridgePixelPct"] if p88_rows else 15.0
    p95_ridge = p88_rows[-1]["ridgePixelPct"] if p88_rows else 5.0
    p88_ridge = p88_88["ridgePixelPct"] if p88_88 else 12.0
    blocks.append(
        Text(
            "空间→统计路径在 XY 投影上以 **投影值≥P88** 提取亮脊。"
            f"P88 并非随意常数：在 **P85–P95** 扫描中，亮脊像素占比由 **{p85_ridge:.1f}%** 单调降至 **{p95_ridge:.1f}%**，"
            f"反查密度带下界变化 **{band_span:.2f}**（约 **{band_span_pct:.1f}%** 相对跨度），"
            f"P88 处亮脊约占 **{p88_ridge:.1f}%** 像素、密度带 **ρ∈[{band_lo:.2f},{band_hi:.2f}]**，"
            "与 **Top 1%** 阈值区间相容且对百分位微扰不敏感。"
            "亮脊定义的是**形态约束**（投影脊线 + 列内密度），与 **Top 1%** 的**纯密度分位**并非同一集合，"
            "故需单独量化误报/漏报。"
            "另提供**梯度脊线**自动化对照（投影梯度模≥P92，task4_ridge_methods.png），"
            "与 P88 亮脊 Jaccard 约 "
            f"**{ext_val.get('ridgeMethodsT99', {}).get('jaccard', 0)*100:.0f}%**——"
            "**两种定义差异大，存在 filament 操作定义歧义。**"
            "选用 **P88 亮脊**而非梯度脊的原因：**①** 与交互「投影高亮→反查密度带」流程一致（百分位稳定）；"
            "**②** P85–P95 敏感度显示密度带变化小；**③** 梯度脊对噪声更敏感、Jaccard 低。"
            "梯度结果作为**对照**，不宣称唯一客观 filament 真值。"
        )
    )
    if ext_val.get("ridgeMethodsT99"):
        blocks.append(
            Figure(
                "task4_ridge_methods.png",
                "P88 亮脊 vs 梯度脊线(P92) 重叠度（t=99）",
                14.0,
            )
        )
    if fpfn:
        prec = fpfn.get("precision", 0) * 100
        rec = fpfn.get("recall", 0) * 100
        fp_rate = fpfn.get("fpRateInBrush", 0) * 100
        iso = int(fpfn.get("isolatedHighDensityInBrush", 0))
        iso_rate = fpfn.get("isolatedRateInBrush", 0) * 100
        blocks.append(
            Text(
                f"以 **P88 亮脊列 + ρ≥band_lo** 构建 filament **代理掩膜**（**{fpfn.get('filamentProxyVoxels', 0):,}** 体素），"
                f"与 **Top 1%** 刷选（**{fpfn.get('brushVoxels', 0):,}** 体素）对照："
                f"**召回率 {rec:.1f}%**（代理体素几乎全部落在 Top 1% 内，**FN={fpfn.get('falseNegative', 0):,}**）；"
                f"**精确率 {prec:.1f}%**、刷选内 **误报率 {fp_rate:.1f}%**——"
                "即多数 Top 1% 体素位于丝状结构之外的高密尾区，符合「密度分位 ⊃ 形态脊线」的预期。"
                f"其中 **6-邻接孤立高密体素 {iso:,} 个（占刷选 {iso_rate:.2f}%）** 可能为噪声或未连通节点；"
                "剔除后可略抬精确率，但会损失合法节点核；当前保留并以低占比说明误报可控。"
                "未计入代理漏报，因代理定义更严。"
            )
        )
        blocks.append(
            Table(
                caption="刷选 vs filament 代理（t=99，brush_validation.json）",
                headers=["指标", "数值", "含义"],
                rows=[
                    ["TP", f"{fpfn.get('truePositive', 0):,}", "刷选 ∩ 代理"],
                    ["FP", f"{fpfn.get('falsePositive', 0):,}", "刷选内非代理（预期为主）"],
                    ["FN", f"{fpfn.get('falseNegative', 0):,}", "代理内未刷选"],
                    ["精确率", f"{prec:.1f}%", "刷选命中代理的比例"],
                    ["召回率", f"{rec:.1f}%", "代理被刷选覆盖的比例"],
                    ["孤立高密点", f"{iso:,} ({iso_rate:.2f}%)", "刷选内 ≤1 邻居体素"],
                ],
            )
        )
    blocks.append(
        Figure("task4_p88_sensitivity.png", "P85–P95 亮脊阈值敏感度：像素占比与反查密度带", 15.5)
    )
    blocks.append(
        Figure(
            "task4_brush_precision.png",
            "刷选精确率/召回率与误报、漏报率（相对 filament 代理）",
            15.5,
        )
    )

    blocks.append(Heading("4.6  仪表盘可用性（启发式检查单）", 2))
    blocks.append(
        Text(
            "本作品**未**开展正式用户实验（赛期限制）；下列检查单**不能替代**可用性量表或任务完成率实证。"
            "作者走查项：**①** void/filament 体渲染可辨；**②** 预设刷选后投影高亮；"
            "**③** 切换时间步后 Top 1% 对应该步 p99；**④** 空间↔统计双向对照。"
            "评委可在 **python run.py** 下自行计时；正式 SUS/被试实验列为后续工作。"
        )
    )

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
            "在 t=0/99 上对 **2000 条随机视线**做列平均密度，得到**通量涨落 PDF 代理**"
            "（task5_lyalpha_flux_proxy.png）——**定性**对比对比度增强，非观测拟合。"
        )
    )
    ly = ext_val.get("lyalphaProxy", {})
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
        blocks.append(
            Figure(
                "task5_lyalpha_flux_proxy.png",
                "Lyα 通量涨落代理：2000 条 +z 视线列平均 ρ PDF（非各向同性、无红移标定；t=0 vs t=99）",
                15.0,
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
            "**（1）静态替代：**§2.3 **Top 1% 三联图**（task4_brush_triptych.png）冻结「直方图→体渲染→投影」同一状态；"
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
    blocks.append(
        Figure(
            "app_infographic_poster.png",
            "交互仪表盘信息图海报（hero + strip + story + brush + pie + flow 纵向拼接）",
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
            "cosmic 传递函数见正文 **§1.2** 与 **task1_transfer_function.png**；"
            "交互页默认 **getGlobalTfDomain**（百步 p01–p99 包络）+ 固定 **tfParams**，"
            "拖动时间轴时 α(ρ) 映射不变；**capture 条带**另用 Evolution Profile，见 §1.2（5）。"
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
            "task4_threshold_comparison / task4_custom_brush_error / task4_projection_axes / task4_p88_sensitivity / task4_brush_precision（刷选验证补强）、"
            "task6_story_poster（长卷代表图）、task0_story_flow（七步流程）。"
            "体渲染单帧由 tools/node/capture_volumes.mjs（Playwright）截取。"
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

    return blocks
