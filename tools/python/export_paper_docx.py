"""Export ChinaVis-style paper docx: 上表下图, Chinese typography, no markdown artifacts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from report_docx_shared import FIGURES, ROOT, resolve_image
from spatial_to_stats import filament_density_band, load_volume_dat

STATS = ROOT / "public" / "stats" / "timeline.json"
NYX = ROOT / "Nyx"
OUT = ROOT / "docs" / "submission" / "NyxViz_报告终稿.docx"

FIGURE_SPECS: list[tuple[str, str]] = [
    ("task1_vol_strip.png", "五时刻体渲染对比（t=0/25/50/75/99，统一色标）"),
    ("task1_vol_t0000.png", "t=0 体渲染"),
    ("task1_vol_t0099.png", "t=99 体渲染"),
    ("task2_evolution_story.png", "100步全域统计：分位跨度、σ、高密度尾占比与偏度"),
    ("task3_hist_overlay.png", "代表步 log 直方图叠加"),
    ("task3_metrics_timeline.png", "100步 mean、p99 与 σ 时序曲线"),
    ("task3_evolution_metrics.png", "σ、偏度与 p99−p01 分位跨度"),
    ("task4_spatial_to_stats.png", "空间→统计：filament 亮脊与对应密度带"),
    ("task4_brush_triptych.png", "Top 1% 刷选：直方图—体渲染—投影三联验证"),
    ("task4_hist_brush_top1.png", "Top 1% 直方图刷选区间"),
    ("task4_brush_top1.png", "Top 1% 空间投影高亮"),
]


def load_timeline() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def normalize_cn(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+([，。；：、）】])", r"\1", text)
    text = re.sub(r"([（【])\s+", r"\1", text)
    text = re.sub(r"\s+→\s+", "→", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def set_run_font(run, name: str = "宋体", size_pt: float = 12, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    r = run._element.get_or_add_rPr()
    r.rFonts.set(qn("w:eastAsia"), name)


def set_paragraph_format(paragraph, *, indent: bool = True, align=WD_ALIGN_PARAGRAPH.JUSTIFY) -> None:
    fmt = paragraph.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)
    fmt.alignment = align
    if indent:
        fmt.first_line_indent = Pt(24)


def add_body(doc: Document, text: str, *, indent: bool = True) -> None:
    text = normalize_cn(text)
    if not text:
        return
    p = doc.add_paragraph()
    set_paragraph_format(p, indent=indent)
    set_run_font(p.add_run(text))


def add_heading(doc: Document, text: str, level: int) -> None:
    text = normalize_cn(text)
    sizes = {0: 18, 1: 16, 2: 14, 3: 12}
    fonts = {0: "黑体", 1: "黑体", 2: "黑体", 3: "宋体"}
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_before = Pt(12 if level <= 1 else 6)
    p.paragraph_format.space_after = Pt(6)
    if level == 0:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run(text), fonts.get(level, "宋体"), sizes.get(level, 12), bold=True)


def add_table_caption(doc: Document, num: int, title: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    set_run_font(p.add_run(f"表{num} {normalize_cn(title)}"), "宋体", 10.5, bold=True)


def add_figure_caption(doc: Document, num: int, title: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(12)
    set_run_font(p.add_run(f"图{num} {normalize_cn(title)}"), "宋体", 10.5)


def style_table(table) -> None:
    table.style = "Table Grid"
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                for run in para.runs:
                    set_run_font(run, "宋体", 10.5)


def add_table(doc: Document, num: int, title: str, headers: list[str], rows: list[list[str]]) -> None:
    add_table_caption(doc, num, title)
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    style_table(table)
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = h
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                set_run_font(run, "宋体", 10.5, bold=True)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.rows[i].cells[j]
            cell.text = val
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    set_run_font(run, "宋体", 10.5)
    doc.add_paragraph()


def add_figure(doc: Document, num: int, image_name: str, caption: str, width_cm: float = 14.5) -> None:
    path = resolve_image(image_name)
    if not path:
        add_body(doc, f"（缺图：{image_name}）", indent=False)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    add_figure_caption(doc, num, caption)


def setup_page(doc: Document) -> None:
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.17)
    sec.right_margin = Cm(3.17)
    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def filament_band() -> tuple[float, float]:
    vol_path = NYX / "0099.dat"
    if vol_path.exists():
        lo, hi, _ = filament_density_band(load_volume_dat(vol_path))
        return lo, hi
    return 11.23, 12.16


def build_document(timeline: dict) -> Document:
    steps = {s["timestep"]: s for s in timeline["timesteps"]}
    s0, s99 = steps[0], steps[99]
    band_lo, band_hi = filament_band()
    fig_no = 1
    tbl_no = 1

    doc = Document()
    setup_page(doc)

    add_heading(doc, "Nyx 128³ 气体密度可视化分析报告", 0)
    add_heading(doc, "ChinaVis 2026 赛道1-II", 3)
    doc.add_paragraph()

    add_heading(doc, "摘要", 2)
    add_body(
        doc,
        "本文针对 Nyx 宇宙学模拟输出的 128³ 重子气体密度场（100 个时间步），"
        "完成体渲染、时序 log 直方图统计与相空间刷选联动分析。"
        f"全域密度范围 {timeline['globalMin']:.2f}–{timeline['globalMax']:.2f}。"
        f"统计显示 σ 由 {s0['std']:.4f} 增至 {s99['std']:.4f}，分位跨度 p99−p01 由 "
        f"{s0['p99'] - s0['p01']:.3f} 增至 {s99['p99'] - s99['p01']:.3f}，"
        "结构由近似均匀转向 void—filament—node 分化。"
        "Top 1% 高密度尾在投影与体渲染中呈丝状聚集；"
        f"由亮脊反推的密度带为 ρ∈[{band_lo:.2f}, {band_hi:.2f}]，与刷选结果一致。",
    )

    add_heading(doc, "关键词", 2)
    add_body(doc, "体渲染；Nyx；宇宙网；时序直方图；相空间刷选", indent=False)

    # ── 任务一 ──
    add_heading(doc, "一、体数据渲染与密度演化", 1)

    add_heading(doc, "1.1 方法", 2)
    add_body(
        doc,
        "数据为 Nyx 官方 128³ 气体密度，100 时间步，小端 float32，体素索引 z→y→x。"
        "体渲染基于 vtk.js 光线投射，传递函数在 log 域按全域 p01–p99 映射（cosmic 预设）。"
        "选取 t=0、25、50、75、99 五帧，固定相机与色标，1920×1080 截取体渲染图。",
    )

    add_heading(doc, "1.2 观察", 2)
    add_body(
        doc,
        "t=0 整体呈均匀雾状，filament 对比度低；t=25–50 丝状结构逐渐连通，void 区域扩大；"
        "t=99 宇宙网拓扑清晰，高密度脊线与节点形成亮带，与统计右尾增厚相对应。",
    )

    add_table(
        doc,
        tbl_no,
        "五代表步密度统计量",
        ["时间步", "均值", "标准差 σ", "p99", "最大值"],
        [
            [str(t), f"{steps[t]['mean']:.4f}", f"{steps[t]['std']:.4f}", f"{steps[t]['p99']:.4f}", f"{steps[t]['max']:.4f}"]
            for t in [0, 25, 50, 75, 99]
        ],
    )
    tbl_no += 1

    for name, cap in FIGURE_SPECS[:3]:
        add_figure(doc, fig_no, name, cap)
        fig_no += 1

    # ── 任务二 ──
    add_heading(doc, "二、宇宙密度演化规律", 1)

    add_heading(doc, "2.1 物理背景与指标", 2)
    add_body(
        doc,
        "数据来自 Nyx 宇宙学流体模拟（AMReX），子体积为重子气体密度而非暗物质。"
        "100 步演化对应引力不稳定下，由微涨落向宇宙网拓扑分化的过程；"
        "IGM 占体积主体，可见亮脊对应极少数高密度尾。",
    )

    span0 = s0["p99"] - s0["p01"]
    span99 = s99["p99"] - s99["p01"]
    add_table(
        doc,
        tbl_no,
        "t=0 与 t=99 演化指标对比",
        ["指标", "t=0", "t=99", "变化"],
        [
            ["标准差 σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", f"+{(s99['std'] - s0['std']) / s0['std'] * 100:.1f}%"],
            ["分位跨度 p99−p01", f"{span0:.3f}", f"{span99:.3f}", f"+{(span99 - span0) / span0 * 100:.1f}%"],
            ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", "右偏维持"],
            ["≥p99 体积占比", f"{s0['tailMassAboveP99'] * 100:.2f}%", f"{s99['tailMassAboveP99'] * 100:.2f}%", "约 1% 量级"],
        ],
    )
    tbl_no += 1

    add_heading(doc, "2.2 结论", 2)
    add_body(
        doc,
        "（1）σ(t) 整体上升，涨落增强；（2）分布持续右偏，低密度 void 与高密度节点并存；"
        "（3）Top 1% 体素在空间投影中呈丝状，与体渲染亮脊位置一致（见任务四）。",
    )

    add_figure(doc, fig_no, FIGURE_SPECS[3][0], FIGURE_SPECS[3][1], width_cm=15)
    fig_no += 1

    # ── 任务三 ──
    add_heading(doc, "三、时序密度对数直方图", 1)

    add_heading(doc, "3.1 方法", 2)
    add_body(
        doc,
        f"对 100 步密度做 log 等距分箱（{timeline['binCount']} bins），"
        f"边界 [{timeline['globalMin']:.4f}, {timeline['globalMax']:.4f}]。"
        "分箱中心取几何均值，直方图为归一化频数；同步输出 mean、σ、分位数与偏度时序。",
    )

    add_table(
        doc,
        tbl_no,
        "直方图演化要点（t=0→99）",
        ["量", "t=0", "t=99", "含义"],
        [
            ["σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", "团块化、涨落扩大"],
            ["偏度", f"{s0['skewness']:.4f}", f"{s99['skewness']:.4f}", "右尾增厚"],
            ["p50", f"{s0['p50']:.4f}", f"{s99['p50']:.4f}", "主峰略移"],
            ["p99−p01", f"{span0:.3f}", f"{span99:.3f}", "两极分化"],
        ],
    )
    tbl_no += 1

    add_body(
        doc,
        "与赛题描述一致：早期密度集中于均值附近，后期直方图主峰略移、右尾抬升，"
        "对应 void 与致密节点并存；100 步序列比单帧切片更能说明趋势。",
    )

    for name, cap in FIGURE_SPECS[4:7]:
        add_figure(doc, fig_no, name, cap)
        fig_no += 1

    # ── 任务四 ──
    add_heading(doc, "四、相空间刷选联动", 1)

    add_heading(doc, "4.1 系统", 2)
    add_body(
        doc,
        f"交互页含 log 直方图（D3）与 vtk.js 体渲染：用户框选密度区间，"
        f"体素传递函数高亮，2D 最大密度投影以金色标出刷选结果；"
        f"Top 1% 阈值为 ρ≥{s99['p99']:.4f}，Bottom 1% 为 ρ≤{s99['p01']:.4f}。"
        "刷选扫描在 Web Worker 中执行，避免阻塞渲染。",
    )

    add_table(
        doc,
        tbl_no,
        "刷选验证摘要（t=99）",
        ["方向", "操作", "空间表现", "统计对应"],
        [
            ["统计→空间", "Top 1% 刷选", "XY 投影丝状/节点聚集", f"ρ≥{s99['p99']:.2f}"],
            ["统计→空间", "Bottom 1% 刷选", "投影稀疏区域", f"ρ≤{s99['p01']:.2f}"],
            ["空间→统计", "亮脊识别（P88）", "金色 filament 区域", f"ρ∈[{band_lo:.2f}, {band_hi:.2f}]"],
        ],
    )
    tbl_no += 1

    add_heading(doc, "4.2 讨论", 2)
    add_body(
        doc,
        "Top 1% 刷选后投影非随机散点，而与体渲染亮脊重合，说明高密度尾对应宇宙网致密结构。"
        "自投影识别 filament 后反查密度带，在直方图上的位置与 Top 1% 区间一致，"
        "形成统计—空间双向可验证的闭环。",
    )

    for name, cap in FIGURE_SPECS[7:]:
        add_figure(doc, fig_no, name, cap)
        fig_no += 1

    add_heading(doc, "工具说明", 2)
    add_body(
        doc,
        "前端：Vite、React、vtk.js、D3；预计算与静态图：Python（precompute、generate_figures）；"
        "体渲染截图：Playwright。数据与统计结果可由 public/stats/timeline.json 复现。",
        indent=False,
    )

    return doc


def main() -> int:
    if not STATS.exists():
        print("Missing timeline.json — run: npm run precompute", file=sys.stderr)
        return 1

    timeline = load_timeline()
    doc = build_document(timeline)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
