"""Generate four markdown report sections from stats and figures (答卷正文素材)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "public" / "stats" / "timeline.json"
REPORT = ROOT / "docs" / "report"


def load_stats() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def task1_md(timeline: dict) -> str:
    steps = {s["timestep"]: s for s in timeline["timesteps"]}
    lines = []
    for t in [0, 25, 50, 75, 99]:
        s = steps[t]
        lines.append(
            f"- t={t}: mean={s['mean']:.4f}, σ={s['std']:.4f}, "
            f"p99={s['p99']:.4f}, max={s['max']:.4f}"
        )
    stats_block = "\n".join(lines)
    return f"""# 任务一：体数据渲染与密度演化

## 方法
- **数据**：Nyx 官方 128³ 气体密度，100 时间步，小端 float32，存储顺序 z→y→x（`index = z + 128y + 128²x`）。
- **渲染**：基于 vtk.js 的 GPU 光线投射体渲染；传递函数采用宇宙学预设 `cosmic`——低密度空洞区近透明，纤维结构紫青，高密度节点金黄；双光源（主光 + 冷色补光），交互模式采样距离 2.2，可选高质量模式采样 1.0 并开启 Phong 着色。
- **展示**：选取 t=0/25/50/75/99 五帧，统一色标与相机，便于对比演化。

## 观察
- **t=0**：整体呈均匀雾状，filament 对比度弱，尚处于涨落初生的“平滑”阶段。
- **t=25–50**：丝状结构逐渐连通，低密度 void 区域扩大。
- **t=99**：宇宙网状拓扑清晰，高密度脊线与节点在体渲染中形成亮带，与统计上的右尾增厚一致。

## 数据佐证
{stats_block}

## 配图（≤5）
![五时刻体渲染条带](../figures/task1_vol_strip.png)
![t=0](../figures/task1_vol_t0000.png)
![t=50](../figures/task1_vol_t0050.png)
![t=99](../figures/task1_vol_t0099.png)
"""


def task2_md(timeline: dict) -> str:
    s0 = timeline["timesteps"][0]
    s99 = timeline["timesteps"][99]
    span0 = s0["p99"] - s0["p01"]
    span99 = s99["p99"] - s99["p01"]
    return f"""# 任务二：宇宙密度演化规律归纳

## 结构形成（团块化）
- 在 100 步引力团块化过程中，**密度分位跨度 p99−p01** 由 {span0:.3f} 增至 {span99:.3f}（+{(span99-span0)/span0*100:.1f}%），说明高低密度区域分化加剧。
- **标准差 σ** 由 {s0['std']:.4f} 升至 {s99['std']:.4f}，全域涨落幅度持续扩大，符合“均匀 IGM → 纤维/节点”结构形成图像。

## 星系际介质（IGM）
- 密度直方图主峰始终位于中低密区，**≥p99 的体素体积占比**约 {s99['tailMassAboveP99']*100:.2f}%（t=99），即绝大部分体积仍为稀疏 IGM，仅少量重子汇入致密通道构成宇宙网可见结构。

## 可视化应用价值
- **体渲染**提供全局形态直觉，识别 filaments 与 void 的空间布局；
- **100 步 log 直方图**量化分布漂移，避免“只看漂亮图”的主观判断；
- **相空间刷选**将高密度尾与空间节点一一对应，形成“假设—统计—空间”闭环，支撑宇宙学数据探索。

## 可检验结论（三条）
1. 涨落增强：σ(t) 单调上升趋势（见图 task2_evolution_story）。
2. 两极分化：偏度维持右偏且尾翼抬升，低密度空洞与高密度节点共存。
3. 宇宙网对应：Top 1% 空间投影呈丝状聚集，与体渲染亮脊位置一致（任务四验证）。

## 配图
![演化规律四联图](../figures/task2_evolution_story.png)
![直方图叠加](../figures/task3_hist_overlay.png)
![t=0 体渲染](../figures/task1_vol_t0000.png)
![t=99 体渲染](../figures/task1_vol_t0099.png)
"""


def task3_md(timeline: dict) -> str:
    s0 = timeline["timesteps"][0]
    s99 = timeline["timesteps"][99]
    gmin, gmax = timeline["globalMin"], timeline["globalMax"]
    bc = timeline["binCount"]
    return f"""# 任务三：时序密度对数直方图统计

## 方法
- 对 **全部 100 个时间步** 的气体密度做 **log 等距分箱**（{bc} bins），边界 `[{gmin:.4f}, {gmax:.4f}]`（全域 min/max）。
- 分箱中心 ρᵢ = √(edgeᵢ · edgeᵢ₊₁)，直方图为归一化频数 Σcount/N。
- 同步预计算每步 mean、σ、p01/p50/p99、偏度 skew，用于时序曲线（`scripts/precompute.py` → `timeline.json`）。

## 演化规律
- **团块化**：σ 由 {s0['std']:.4f} → {s99['std']:.4f}，物质分布由相对均匀转向强烈聚敛。
- **两极分化**：偏度 {s0['skewness']:.4f} → {s99['skewness']:.4f}，右尾持续增厚；代表步直方图叠加显示主峰略移、尾部抬升，对应“void + 致密节点”。
- **分位跨度**：p99−p01 扩大，高密度尾体积占比稳定在 ~1% 量级，但空间上对应可见宇宙网。

## 与赛题描述的对照
赛题指出早期密度集中于均值附近、后期出现空洞与峰值两极分化——本工作用 **100 步完整直方图序列** 而非单帧切片证明该趋势，并给出可复现的数值曲线。

## 配图
![五步直方图叠加](../figures/task3_hist_overlay.png)
![100步 mean/p99/σ](../figures/task3_metrics_timeline.png)
![σ/skew/分位跨度](../figures/task3_evolution_metrics.png)
![主峰漂移](../figures/task3_peak_drift.png)
"""


def task4_md(timeline: dict) -> str:
    s99 = timeline["timesteps"][99]
    return f"""# 任务四：相空间交互刷选可视分析

## 系统功能
- **统计视图**：log 密度直方图，支持拖拽框选密度区间；快捷 **Top 1%**（ρ≥p99={s99['p99']:.4f}）与 **Bottom 1%**（ρ≤p01={s99['p01']:.4f}）。
- **空间视图**：vtk.js 体渲染对刷选区间体素做传递函数高亮；Canvas 2D **最大密度投影** 以金色标出刷选体素；可选 3D 点云（≤12000 点，Web Worker 后台扫描）。
- **性能**：刷选扫描在 Worker 线程；VTK 按需加载；相邻时间步 idle 预取。

## 验证：统计 → 空间
- **Top 1%**：直方图右尾刷选后，XY 投影显示丝状/节点状聚集（非随机散点），与 t=99 体渲染中的亮脊一致 → **高密度尾对应宇宙网致密结构**。
- **Bottom 1%**：刷选低密度左尾，投影显示广袤稀疏区域，对应 IGM 主体。

## 双向关联
- **统计→空间**：框选 [ρ_min, ρ_max] 定位满足条件的体素集合；
- **空间→统计**：在体渲染/投影中识别 filament 后，可在直方图上标出对应密度带（见代表步直方图标注）。

## 配图
![Top1% 三联图](../figures/task4_brush_triptych.png)
![Top1% 直方图刷选](../figures/task4_hist_brush_top1.png)
![Top1% 空间投影](../figures/task4_brush_top1.png)
![Bottom1% 投影](../figures/task4_brush_bottom1.png)
"""


def main() -> int:
    if not STATS.exists():
        print("Missing timeline.json — run: npm run precompute", file=sys.stderr)
        return 1

    REPORT.mkdir(parents=True, exist_ok=True)
    timeline = load_stats()
    files = {
        "task1_volume.md": task1_md(timeline),
        "task2_evolution.md": task2_md(timeline),
        "task3_histogram.md": task3_md(timeline),
        "task4_brush.md": task4_md(timeline),
    }
    for name, content in files.items():
        path = REPORT / name
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path}")

    full = "\n\n---\n\n".join(files.values())
    (REPORT / "full_report.md").write_text(full, encoding="utf-8")
    print(f"Wrote {REPORT / 'full_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
