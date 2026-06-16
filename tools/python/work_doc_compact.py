"""Compact task answers (≤800 字/题) and supplement appendix blocks for work doc."""
from __future__ import annotations

from render_spec import PRESENTATION_QUALITY

from work_doc_content import Figure, Heading, Table, Text, Block


def _task1_compact(
    *,
    s0: dict,
    s99: dict,
    steps: dict,
    sigma_pct: float,
    gmin_tf: float,
    gmax_tf: float,
    fp: tuple,
    pos: tuple,
    cam: dict,
    cap_op_t0: float,
    cap_op_t99: float,
    cap_dg_t0: float,
    cap_dg_t25: float,
    rho_shift_t0: float,
    span_s0: float,
    ext_val: dict,
) -> list[Block]:
    blocks: list[Block] = []
    jboot = ext_val.get("resolutionJaccardBootstrapT99", {})
    res_rows = ext_val.get("resolutionCoarseningT99", [])
    r64 = next((r for r in res_rows if r["grid"] == 64), {}) if res_rows else {}
    res_body = ""
    if res_rows and jboot:
        res_body = (
            f"**图5** 块粗化：原点对齐 64³ 脊 Jaccard≈{r64.get('ridgeJaccardVs128', 0):.2f}；"
            f"**8 组 lattice 偏移**均值 **{jboot.get('jaccardMean', 0):.3f}±{jboot.get('jaccardStd', 0):.3f}**"
            f"（**样本标准差** ddof=1；图5 圆点误差棒为 **均值±1×样本SD**；详见 **附录 5.1**）。"
        )
    blocks.append(Heading("1、体数据渲染与密度演化", 1))
    blocks.append(
        Text(
            f"**回答：**基于 **vtk.js** 对 Nyx **128³** 气体密度场做 GPU 体渲染，"
            f"在固定相机下截取 t=0/25/50/75/99 五帧（**图2**），呈现 void—filament—node 宇宙网由模糊到清晰的形态演化。"
            f"t=0 整体呈均匀雾状（σ={s0['std']:.4f}），t=99 脊线与节点亮带可辨（σ={s99['std']:.4f}，**+{sigma_pct:.1f}%**）。"
            "采用 **log 域 cosmic 传递函数** 压缩 IGM 大动态范围，使低密度 void 与高密度 filament 同屏可见（**图4** 汇总 TF/光照/capture 增益）。"
            "**核心结论：**① 引力团块化表现为丝状连通与 void 扩大；"
            "② 五帧条带仅用于**固定相机下的形态叙事**。"
            "**⚠ 不宜定量对比：**capture 专用 Evolution Profile 使**同一 ρ 在不同时间步的 RGB/α 映射不同**——"
            "条带图**不能**作为 ρ–亮度标定或跨步定量对比依据；定量请用 **timeline.json** 或交互页（全局 TF 一致）。"
            "图4 已汇总 TF/光照/capture 增益示意；**附录 5.1** 补充分辨率粗化与表格式 capture 对照。"
            f"{res_body}"
        )
    )
    blocks.append(
        Figure(
            "task1_vol_strip.png",
            "五帧体渲染条带（capture 专用 TF；左→右 t=0/25/50/75/99）",
            16.0,
        )
    )
    blocks.append(
        Figure(
            "task1_hero_poster.png",
            "t=99 代表帧：体渲染主视角 + log10 色标",
            14.0,
        )
    )
    blocks.append(
        Figure(
            "task1_render_params.png",
            "渲染参数汇总：(a) 传递函数 · (b) Phong 光照 · (c) capture TF 增益",
            15.5,
        )
    )
    blocks.append(
        Table(
            caption="五代表步密度统计量",
            headers=["时间步", "均值", "σ", "p99", "max"],
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
    res_rows = ext_val.get("resolutionCoarseningT99", [])
    if res_rows:
        r64 = next((r for r in res_rows if r["grid"] == 64), res_rows[1] if len(res_rows) > 1 else {})
        jboot = ext_val.get("resolutionJaccardBootstrapT99", {})
        cap = "分辨率粗化敏感性（128³ 细丝连通性上限；详见附录 5.1）"
        if jboot:
            cap = (
                f"分辨率粗化（t=99）：(左) 投影相关 r；(右) 64³ Jaccard——"
                f"菱形=原点对齐 {r64.get('ridgeJaccardVs128', 0):.2f}；"
                f"圆点+误差棒=8 组 lattice 偏移 {jboot.get('jaccardMean', 0):.3f}±{jboot.get('jaccardStd', 0):.3f}（均值±1×样本SD, ddof=1）"
            )
        blocks.append(
            Figure(
                "task1_resolution_coarsening.png",
                cap,
                14.5,
            )
        )
    return blocks


def _task2_compact(
    *,
    s0: dict,
    s99: dict,
    sigma_pct: float,
    span0: float,
    span99: float,
    span_pct: float,
    tail_vol: float,
    mass_above: float,
    brush_top_n: int,
    fil_lo: float,
    fil_hi: float,
    fil_vol_pct: float,
    band_lo: float,
    band_hi: float,
    fp_rate_early: float,
    m,
    xi_r1_delta: float,
    boot: dict,
) -> list[Block]:
    blocks: list[Block] = []
    blocks.append(Heading("2、宇宙密度演化规律归纳", 1))
    blocks.append(
        Text(
            f"**回答：**结合百步 **timeline.json** 统计与代表步直方图，归纳 IGM 密度演化规律。"
            f"**（1）团块化：**σ 由 {s0['std']:.4f} 升至 {s99['std']:.4f}（**+{sigma_pct:.1f}%**），"
            f"p99−p01 由 {span0:.3f} 扩至 {span99:.3f}（**+{span_pct:.1f}%**）——全时域曲线支撑，非单帧挑选（**图6**）。"
            f"**（2）右尾增厚：**p99/p999 分位抬升、直方图右尾抬高；偏度/峰度曲线仅说明形态右偏，**不作尾翼主证**。"
            f"**（3）少数体素承载结构：**≥p99 体积约 **{tail_vol:.2f}%**，却贡献约 **{mass_above:.1f}%** 质量（**图6–7**）。"
            "Moran's I、ξ(r) 等空间统计**列值供对照**，bootstrap 显示增量未达 2σ，**不作团块化方向主证**（**图8**，方法见附录 5.2）。"
        )
    )
    blocks.append(Heading("2.2  可视化在宇宙学分析中的应用价值", 2))
    blocks.append(
        Text(
            "赛题要求阐释可视化在宇宙学分析中的价值——本作品以**可检验联动**回应，而非静态配图："
            f"**案例 A｜时序压缩防挑帧：**σ **+{sigma_pct:.1f}%**、p99−p01 **+{span_pct:.1f}%** 来自百步曲线（**图6**），"
            "避免仅展示 t=0/99 两帧造成「偶然团块化」叙事。"
            f"**案例 B｜统计→空间桥接：**Top 1% 仅 **{tail_vol:.2f}%** 体积却约 **{mass_above:.1f}%** 质量；"
            f"刷选 **{brush_top_n:,}** 体素后，体渲染/投影呈**丝状 filament** 而非散点（**图9**，(a–c) 三联）。"
            f"**案例 C｜双向闭环：**P88 亮脊反查 ρ∈[{band_lo:.2f},{band_hi:.2f}]，与 Top 1% 一致；"
            f"刷选内形态外高密尾约 **{fp_rate_early:.1f}%**，说明「分位集合 ⊃ 脊线几何」。"
            f"纤维带 90–99%（ρ∈[{fil_lo:.2f},{fil_hi:.2f}]，**{fil_vol_pct:.1f}%** 体积）可在同相机下对比宽尾/窄尾形态。"
            "工具对比与进阶统计见**附录 5.2**。"
        )
    )
    blocks.append(
        Figure(
            "task2_evolution_story.png",
            "100 步统计四联：分位跨度、σ、≥p99 体积占比、偏度",
            15.5,
        )
    )
    blocks.append(
        Figure(
            "task3_hist_overlay.png",
            "五步 log 直方图叠加（Probability mass×100）",
            15.0,
        )
    )
    blocks.append(
        Figure(
            "task2_spatial_summary.png",
            "空间统计汇总：(a)–(d) Moran's I / ξ / D / 峰度时序 · (e) ξ 剖面 · (f) bootstrap（各子图左上角标注）",
            15.5,
        )
    )
    blocks.append(
        Figure(
            "task4_discovery_summary.png",
            "可视化驱动发现：(a–c) Top 1% 三联（直方图/体渲染/投影）· (d) 空间→统计反查",
            16.0,
        )
    )
    blocks.append(
        Table(
            caption="t=0 与 t=99 核心演化指标",
            headers=["指标", "t=0", "t=99", "变化"],
            rows=[
                ["σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", f"+{sigma_pct:.1f}%"],
                ["p99−p01", f"{span0:.3f}", f"{span99:.3f}", f"+{span_pct:.1f}%"],
                [
                    "Moran's I",
                    f"{m(s0, 'moransI'):.4f}",
                    f"{m(s99, 'moransI'):.4f}",
                    "Δ<2σ bootstrap（附录）",
                ],
                [
                    "ξ(r=1)",
                    f"{m(s0, 'xiR1'):.3f}",
                    f"{m(s99, 'xiR1'):.3f}",
                    f"Δ={xi_r1_delta:+.3f}（描述性）",
                ],
                ["≥p99 体积", f"{s0['tailMassAboveP99']*100:.2f}%", f"{tail_vol:.2f}%", "≈1%"],
            ],
        )
    )
    return blocks


def _task3_compact(
    *,
    s0: dict,
    s99: dict,
    bins: int,
    samples_per_bin: int,
    sigma_pct: float,
    span0: float,
    span99: float,
    void_t0p10_0: float,
    void_t0p10_99: float,
    p999_ratio: float,
    skew_delta_pct: float,
) -> list[Block]:
    blocks: list[Block] = []
    blocks.append(Heading("3、时序密度对数直方图统计", 1))
    blocks.append(
        Text(
            f"**回答：**以 **100 步 log 等距直方图**（默认 **{bins} bins**，每步 N=2,097,152，"
            f"纵轴 **Probability mass×100**）量化密度分布漂移。"
            f"**（1）两极分化：**σ **+{sigma_pct:.1f}%**，p99−p01 {span0:.3f}→{span99:.3f}；"
            f"p50 由 {s0['p50']:.4f} 降至 {s99['p50']:.4f}，与 p99 缓升并存——「中心下移 + 右尾抬高」（**任务二图6–7**）。"
            f"**（2）void 扩张：**固定 t=0 阈值 ρ_p10(t=0) 的体积分数 "
            f"{void_t0p10_0:.2f}%→{void_t0p10_99:.2f}%，与赛题「空洞扩大」一致（**图10**）。"
            f"**（3）与任务一对照：**右尾增厚对应体渲染 filament 亮脊；"
            f"p999 **×{p999_ratio:.3f}**（t=99/t=0）、偏度 +{skew_delta_pct:.2f}% 为辅证。"
            f"128 bin 曲线锯齿来自 log 域宽动态范围与多峰结构（平均每箱约 **{samples_per_bin:,}** 点），"
            "**分箱敏感度 64/128/256 对比见附录 5.3**（**附录图18–19**）。"
        )
    )
    blocks.append(
        Figure(
            "task3_void_evolution.png",
            "void 扩张：固定 t=0 低密度分位阈值下的体素占比与 p01/p10 轨迹",
            15.0,
        )
    )
    blocks.append(
        Table(
            caption="直方图演化要点（t=0→99）",
            headers=["量", "t=0", "t=99", "含义 / 备注"],
            rows=[
                ["σ", f"{s0['std']:.4f}", f"{s99['std']:.4f}", "涨落扩大"],
                ["p50", f"{s0['p50']:.4f}", f"{s99['p50']:.4f}", "主峰略移"],
                ["p99−p01", f"{span0:.3f}", f"{span99:.3f}", "两极分化"],
                [
                    "p999",
                    f"{float(s0.get('p999', 0)):.4f}",
                    f"{float(s99.get('p999', 0)):.4f}",
                    f"×{p999_ratio:.3f} (t=99/t=0)",
                ],
                [
                    "void (ρ≤ρ_p10(t=0))",
                    f"{void_t0p10_0:.2f}%",
                    f"{void_t0p10_99:.2f}%",
                    "固定 t=0 分位阈值下扩张（非 δ-b 过密度 void）",
                ],
            ],
        )
    )
    return blocks


def _task4_compact(
    *,
    s0: dict,
    s99: dict,
    band_lo: float,
    band_hi: float,
    brush_val: dict,
    fpfn: dict,
    early_ms: float,
    full_ms: float,
    custom_wide_pct: float,
    custom_mid_pct: float,
    sample_recall_pct: float,
) -> list[Block]:
    fp_rate = fpfn.get("fpRateInBrush", 0) * 100
    rec = fpfn.get("recall", 0) * 100
    blocks: list[Block] = []
    blocks.append(Heading("4、相空间交互刷选可视分析", 1))
    blocks.append(
        Text(
            f"**回答：**三栏仪表盘（**/app.html**）实现 log 直方图、体渲染与 XY 投影联动刷选。"
            f"**Top 1%**（ρ≥该步 p99；t=99 为 **{s99['p99']:.4f}**）刷选后，"
            "投影呈丝状/节点聚集而非随机散点，体渲染高亮与统计区间一致（**任务二图9**，(a–c)）——完成「统计→空间」。"
            f"反向以 P88 亮脊反查密度带 **ρ∈[{band_lo:.2f},{band_hi:.2f}]**，与 Top 1% 相容（**图9 (d)**）。"
            f"离线验证：filament 代理对 Top 1% **召回率 {rec:.1f}%**，刷选内误报率 **{fp_rate:.1f}%**（密度分位 ⊃ 形态脊线，符合预期）。"
            f"Worker 早停 **{early_ms:.0f} ms** vs 全网格 **{full_ms:.0f} ms**（复现见 **附录 5.4** 耗时表）。"
            f"**局限（量化）：**自定义拖拽 KPI 为 stride=2、maxPoints=8000 的采样估计——"
            f"宽区间 p50–p99 显示数可仅为真值 **≈{custom_wide_pct:.2f}%**（t=99），"
            f"p25–p75 约 **≈{custom_mid_pct:.2f}%**；Top 1% 早停召回约 **{sample_recall_pct:.1f}%**。"
            "**体渲染/投影高亮**仍按密度阈值作用于全场，不受采样列表限制。"
            "阈值对比、P88 敏感度等见**附录 5.4** 与 **图11–13**。"
        )
    )
    blocks.append(
        Figure(
            "task4_brush_rows.png",
            "Top 1% / Bottom 1% 双行对比",
            16.0,
        )
    )
    blocks.append(
        Figure(
            "task4_brush_validation_summary.png",
            "刷选验证汇总：(a) 阈值对比 · (b) 早停采样 KPI",
            16.0,
        )
    )
    blocks.append(
        Figure(
            "task4_performance_summary.png",
            "刷选扩展验证：(a) 三向投影 · (b) P88 敏感度 · (c) 精确率/召回 · (d) 脊线方法对照",
            16.0,
        )
    )
    blocks.append(
        Table(
            caption="刷选验证摘要（t=99）",
            headers=["方向", "操作", "空间表现", "密度区间"],
            rows=[
                ["统计→空间", "Top 1%", "丝状/节点聚集", f"ρ≥{s99['p99']:.2f}"],
                ["统计→空间", "Bottom 1%", "稀疏 void 区", f"ρ≤{s99['p01']:.2f}"],
                ["空间→统计", "P88 亮脊", "filament 区域", f"ρ∈[{band_lo:.2f}, {band_hi:.2f}]"],
            ],
        )
    )
    return blocks


def supplement_appendix_blocks(
    *,
    s0: dict,
    s99: dict,
    steps: dict,
    sigma_pct: float,
    span0: float,
    span99: float,
    span_pct: float,
    gmin_tf: float,
    gmax_tf: float,
    fp: tuple,
    pos: tuple,
    cam: dict,
    cap_op_t0: float,
    cap_op_t99: float,
    cap_dg_t0: float,
    cap_dg_t25: float,
    rho_shift_t0: float,
    span_s0: float,
    ext_val: dict,
    boot: dict,
    brush_val: dict,
    band_lo: float,
    band_hi: float,
    fil_lo: float,
    fil_hi: float,
    fil_vol_pct: float,
    fil_mass_pct: float,
    brush_top_n: int,
    tail_vol: float,
    mass_above: float,
    proxy_n: int,
    fp_rate_early: float,
    void_t0p10_0: float,
    void_t0p10_99: float,
    void_t0p01_0: float,
    void_t0p01_99: float,
    samples_per_bin: int,
    bins: int,
    gmin: float,
    m,
    xi_r1_delta: float,
    skew_delta_pct: float,
    kurt_delta: float,
    p999_ratio: float,
    p99_delta_pct: float,
    mass_frac_delta: float,
    moran_pct: float,
) -> list[Block]:
    """Appendix 5: detailed methods, validation, sensitivity moved from task bodies."""
    blocks: list[Block] = []
    blocks.append(Heading("附录 5  补充材料（方法、验证与敏感度）", 2))
    blocks.append(
        Text(
            "本附录收纳任务一至四正文中「详见附录 5.x」的方法细节、验证与敏感度分析；"
            "与正文第 5 章「综合叙事」区分——第 5 章归纳科学发现，"
            "附录 5 提供可复现参数与补充图表（图18–19 等）。"
        )
    )

    # 附录 5.1 Task 1 details
    blocks.append(Heading("5.1  任务一：渲染参数与验证", 3))
    blocks.append(
        Text(
            f"**传递函数：**cosmic 预设，log10 域映射 p01–p99；交互页全局域 **[{gmin_tf:.3f}, {gmax_tf:.3f}]**，"
            "opacityScale=1.15、densityGain=0.12；capture 条带另用 Evolution Profile（opacityScale "
            f"{cap_op_t0:.2f}→{cap_op_t99:.2f}，t<45 时 densityGain 为负以压低 IGM 雾感）。"
            f"**光照：**Phong Ka/Kd/Ks=0.12/0.75/0.4；sampleDistance={PRESENTATION_QUALITY['sampleDistance']}。"
            f"**相机：**focalPoint ({fp[0]:.4f},{fp[1]:.4f},{fp[2]:.4f})，effectiveZoom≈{cam['effectiveZoom']:.4f}。"
            "完整 JSON：`docs/figures/render_spec.json`。"
            "正文 **图4** 已图示 TF/光照/capture 增益；下表仅作交互页与 capture 条带**逐项对照**。"
        )
    )
    blocks.append(
        Table(
            caption="体渲染传递函数：交互页 vs capture 条带",
            headers=["项", "交互页", "capture 条带"],
            rows=[
                ["标量域", f"全局 [{gmin_tf:.3f}, {gmax_tf:.3f}]", "各帧本步 p01–p99"],
                ["opacityScale", "1.15（固定）", f"{cap_op_t0:.2f}→{cap_op_t99:.2f}"],
                ["densityGain", "+0.12", f"t=0 {cap_dg_t0:.2f}，t=25 {cap_dg_t25:.2f}"],
                ["跨步 α(ρ)", "一致", "每帧独立"],
            ],
        )
    )
    res_rows = ext_val.get("resolutionCoarseningT99", [])
    jboot = ext_val.get("resolutionJaccardBootstrapT99", {})
    if res_rows:
        r64 = next((r for r in res_rows if r["grid"] == 64), {})
        j_mean = jboot.get("jaccardMean", r64.get("ridgeJaccardVs128", 0))
        j_std = jboot.get("jaccardStd", 0)
        j_method = jboot.get("method", {})
        blocks.append(
            Text(
                f"**128³ 分辨率说明：**64³ **块平均粗化**（确定性对齐）脊线 Jaccard≈"
                f"{r64.get('ridgeJaccardVs128', 0):.2f}。"
                f"另对 **factor=2 全部 {jboot.get('offsetsUnique', 8)} 组** lattice 偏移逐一粗化："
                f"Jaccard **{j_mean:.3f}±{j_std:.3f}**（**样本 SD**，ddof=1；"
                f"图5 菱形=原点、圆点=8 偏移均值±样本SD）——仍为低通盒滤波，**非 AMR 重采样**。"
            )
        )
        if j_method:
            offset_list = jboot.get("offsetsSampled", [])
            blocks.append(
                Table(
                    caption="64³ Jaccard 偏移粗化方法",
                    headers=["项", "设定"],
                    rows=[
                        ["块尺寸", j_method.get("blockSize", "2³")],
                        ["粗网格", "×".join(str(v) for v in j_method.get("coarseGridShape", [64, 64, 64]))],
                        ["偏移范围", j_method.get("offsetRangePerAxis", "0…1")],
                        ["采样", j_method.get("sampling", "exhaustive 8 shifts")],
                        ["误差棒", jboot.get("jaccardStdNote", "样本 SD，非标准误")],
                        ["边界", j_method.get("windowInBounds", "窗口在 128³ 内")],
                        [
                            "8 组偏移",
                            ", ".join(f"({o[0]},{o[1]},{o[2]})" for o in offset_list),
                        ],
                    ],
                )
            )

    # 5.2 Task 2 details
    blocks.append(Heading("5.2  任务二：空间统计与可视化应用", 3))
    if boot:
        meth = boot.get("method", {})
        ov = boot.get("overlapComparison", {})
        ratio = ov.get("pooledStdRatioRandomOverGrid")
        ratio_txt = f"{ratio:.3f}" if ratio is not None else "—"
        rb = ov.get("ratioBootstrap", {})
        rb_mean = rb.get("ratioMean")
        rb_ci = rb.get("ratioCi95")
        rb_result_row: list[str] | None = None
        if rb_mean is not None and rb_ci:
            rb_result_row = [
                "比值 bootstrap 结果",
                f"400 次 replicate 的比值分布：均值 **{rb_mean:.3f}**，"
                f"标准差 **{rb.get('ratioStd', 0):.3f}**；"
                f"95% CI **[{rb_ci[0]:.3f}, {rb_ci[1]:.3f}]** "
                f"（**百分位数法**，CI 不对称，**≠ mean±SD**）",
            ]
        rows_512: list[list[str]] = [
            ["子窗口", "64³，n=40，seed=42"],
            ["采样", "各 replicate **独立随机平移** 64³ 原点（允许重叠）"],
            [
                "重叠 vs 不重叠",
                f"随机原点 σ_Moran≈{ov.get('randomOriginPooledStdMoran', 0):.4f} "
                f"（t=0/t=99 各 40 replicate 的样本 SD，合并 √(σ₀²+σ₉₉²)）；"
                f"8 块**不重叠** tile 重采样 σ≈{ov.get('gridTilePooledStdMoran', 0):.4f} "
                f"（Moran's I 样本 SD，无量纲）；"
                f"点估计 random/grid≈**{ratio_txt}**",
            ],
            [
                "比值 bootstrap 方法",
                "128³ → 2×2×2 共 **8 块 tile**，每块 1 个 Moran's I。"
                "400 次：从 8 tile 中有放回抽 40 个 → σ_grid"
                "（n=40 与随机原点 replicate 数对齐，便于同一合并公式；**非**同一批子窗口）。"
                "比值=σ_random/σ_grid；CI 为 400 比值的百分位数。",
            ],
            ["Moran's I", "6 邻域 3D，在子体积内计算"],
            ["ξ(r)", "XY 投影 Wiener–Khinchin"],
            ["解读", "描述性对照，不作显著性主张"],
        ]
        if rb_result_row:
            rows_512.insert(3, rb_result_row)
        blocks.append(
            Table(
                caption="空间统计 bootstrap 方法",
                headers=["项目", "设定"],
                rows=rows_512,
            )
        )
        if ratio is not None:
            ci_note = ""
            if rb_ci:
                ci_note = (
                    f" tile 重采样 bootstrap 95% CI **[{rb_ci[0]:.3f}, {rb_ci[1]:.3f}]** 跨度大"
                    f"（上限 {rb_ci[1]:.3f} 接近 1）——说明仅 8 块 tile 时 conservative 程度**不稳定**，"
                    f"点估计 {ratio:.3f} 应结合 CI 解读，而非仅记「≈74%」。"
                )
            blocks.append(
                Text(
                    "**重叠保守性机理：**随机平移的 64³ 子窗口可**共享体素** → replicate 间 Moran's I "
                    "呈正相关 ρ>0 → bootstrap replicate 分布的样本标准差**低于**从 8 块互不重叠 tile "
                    "有放回重采样（后者覆盖独立空间异质性）。"
                    f"本数据点估计 random/grid≈**{ratio:.3f}**（重叠方案 σ 约为不重叠的 **{ratio*100:.0f}%**），"
                    f"用于 2σ 判据时**更保守**（更难宣称显著），**非**正式假设检验。{ci_note}"
                )
            )
    blocks.append(
        Table(
            caption="可视化驱动发现案例",
            headers=["设计", "发现"],
            rows=[
                ["σ/p99−p01 时序", f"全时域 +{sigma_pct:.1f}% / +{span_pct:.1f}%"],
                ["Top 1% 刷选", f"{brush_top_n:,} 体素呈 filament 聚集"],
                ["纤维带 90–99%", f"ρ∈[{fil_lo:.2f},{fil_hi:.2f}]，{fil_vol_pct:.1f}% 体积"],
                ["P88 反查", f"误报率 {fp_rate_early:.1f}%"],
            ],
        )
    )
    blocks.append(
        Text(
            "进阶指标：Moran's I、ξ(r)、盒计数分形维 D、超额峰度、多尺度熵——见 timeline.json 与 spatial_stats.py。"
        )
    )

    # 5.3 Task 3 details
    blocks.append(Heading("5.3  任务三：分箱敏感度", 3))
    blocks.append(
        Text(
            f"128 bins 平均每箱 **{samples_per_bin:,}** 样本；锯齿主因 log 域宽动态范围与多峰。"
            "64/128/256 bins 对比：64 更平滑、256 更锯齿；128 为默认。"
            "配图：**图18**（分箱叠加）、**图19**（CDF L∞ 距）；void 采用固定 t=0 分位阈值。"
        )
    )
    blocks.append(Figure("task3_bin_sensitivity.png", "分箱敏感度：64/128/256 bins（t=0 与 t=99）", 15.0))
    bin_sens = ext_val.get("binSensitivityT99", {})
    if bin_sens:
        blocks.append(Figure("task3_bin_kl.png", "CDF L∞ 距（嵌套 log 边界下 KL≈0）", 14.0))

    # 5.4 Task 4 details
    blocks.append(Heading("5.4  任务四：刷选验证与性能", 3))
    bench = brush_val.get("benchmark", {})
    if bench:
        early = bench.get("top1_earlyExit", {})
        full = bench.get("top1_fullCount", {})
        blocks.append(
            Table(
                caption="Worker 刷选扫描耗时（t=99；brush_analysis.py → brush_validation.json）",
                headers=["模式", "耗时 (ms)", "stride", "maxPoints", "体素数"],
                rows=[
                    [
                        "Top 1% 早停",
                        f"{early.get('elapsedMs', 0):.1f}",
                        str(early.get("stride", 2)),
                        f"{early.get('maxPoints', 8000):,}",
                        f"{early.get('hitsSampled', 0):,}",
                    ],
                    [
                        "Top 1% 全网格",
                        f"{full.get('elapsedMs', 0):.1f}",
                        str(full.get("stride", 1)),
                        f"{full.get('maxPoints', 0):,}",
                        f"{full.get('hitsSampled', 0):,}",
                    ],
                ],
            )
        )
    thr_rows = brush_val.get("thresholds", [])
    if thr_rows:
        blocks.append(
            Table(
                caption="阈值对比（t=99）",
                headers=["阈值", "体积%", "质量%"],
                rows=[[r["label"], f"{r['volumePct']:.2f}", f"{r['massPct']:.2f}"] for r in thr_rows],
            )
        )
    fpfn = brush_val.get("fpFnDefault", {})
    if fpfn:
        blocks.append(
            Table(
                caption="刷选 vs filament 代理",
                headers=["指标", "数值"],
                rows=[
                    ["召回率", f"{fpfn.get('recall', 0)*100:.1f}%"],
                    ["精确率", f"{fpfn.get('precision', 0)*100:.1f}%"],
                    ["误报率", f"{fpfn.get('fpRateInBrush', 0)*100:.1f}%"],
                ],
            )
        )
    custom_rows = brush_val.get("benchmark", {}).get("customBrushErrors", [])
    if custom_rows:
        blocks.append(
            Table(
                caption="自定义拖拽 KPI 低估幅度（t=99；stride=2，maxPoints=8000）",
                headers=["刷选区间", "真值体素", "显示体素", "显示/真值×100%"],
                rows=[
                    [
                        r["label"].replace("自定义：", ""),
                        f"{r['trueVoxels']:,}",
                        f"{r.get('reportedCount', r.get('uniqueTrueFound', 0)):,}",
                        f"{r['reportedOverTruePct']:.2f}%",
                    ]
                    for r in custom_rows
                ],
            )
        )
    blocks.append(
        Text(
            "子图原件：task4_threshold_comparison、task4_brush_kpi_sampling、task4_custom_brush_error、"
            "task4_brush_sample_recall、"
            "task4_projection_axes、task4_p88_sensitivity、task4_brush_precision、task4_ridge_methods。"
            "上表与正文任务四 KPI 数值一致；**体渲染/投影高亮**仍按密度阈值作用于全场，不受采样列表限制。"
        )
    )
    blocks.append(
        Text(
            "**可用性：**未开展正式用户实验；作者走查 void/filament 可辨、预设刷选联动、"
            "时间步切换后 Top 1% 对应该步 p99。正式 SUS 实验列为后续工作。"
        )
    )
    return blocks
