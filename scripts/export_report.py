"""Generate four markdown report sections from stats and figures."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "public" / "stats" / "timeline.json"
FIGURES = ROOT / "docs" / "figures"
REPORT = ROOT / "docs" / "report"


def load_stats() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def task1_md(timeline: dict) -> str:
    s0 = timeline["timesteps"][0]
    s99 = timeline["timesteps"][99]
    return f"""# 任务一：体数据渲染与密度演化

## 方法
采用 Nyx 官方 128³ 气体密度场，按 z→y→x 列优先小端 float32 读取；使用 vtk.js 进行 GPU 光线投射体渲染，配置对数色标传递函数（低密度透明、高密度黄白）及双光源 Phong 着色，展示 t=0/25/50/75/99 五个演化时刻。

## 观察
早期（t=0）密度场在体渲染中呈均匀雾状，filament 结构微弱；随时间步推进，高密度丝状结构与节点逐渐清晰，低密度区域扩大为“空洞”。末期（t=99）可见明显宇宙网状拓扑。

## 数据佐证
- t=0: mean={s0['mean']:.4f}, std={s0['std']:.4f}, max={s0['max']:.4f}
- t=99: mean={s99['mean']:.4f}, std={s99['std']:.4f}, max={s99['max']:.4f}

## 配图
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

## 结构形成
模拟显示物质由近乎均匀分布（t=0 分位跨度 {span0:.3f}）在引力作用下逐步团块化；t=99 分位跨度增至 {span99:.3f}，表明密度涨落幅度显著增大，宇宙网 filaments 与节点结构形成。

## 星系际介质（IGM）
绝大部分体积占据低密度区间（直方图左峰），高密度尾部占比约 {s99['tailMassAboveP99']*100:.2f}%（≥p99），对应 IGM 中稀疏重子汇聚通道。

## 可视化价值
体渲染提供全局形态直觉；统计直方图量化分布漂移；交互刷选将高密度尾与空间节点对应，实现“假设—证据”闭环，降低逐体素盲目探索成本。

## 配图
复用任务一多时刻体渲染与任务三直方图叠加图。
"""


def task3_md(timeline: dict) -> str:
    std0 = timeline["timesteps"][0]["std"]
    std99 = timeline["timesteps"][99]["std"]
    sk0 = timeline["timesteps"][0]["skewness"]
    sk99 = timeline["timesteps"][99]["skewness"]
    return f"""# 任务三：时序密度对数直方图统计

## 方法
对 100 个时间步全域密度做 log 等距分箱（{timeline['binCount']} bins），预计算归一化直方图及 mean/std/分位数/偏度。

## 演化规律
- 标准差由 {std0:.4f} 增至 {std99:.4f}，波动持续扩大；
- 偏度由 {sk0:.4f} 变为 {sk99:.4f}，右尾增厚，呈现高低密度两极分化；
- 代表时刻直方图叠加显示主峰略向左移动、尾部抬升，符合“空洞 + 致密节点”团块化描述。

## 配图
![直方图叠加](../figures/task3_hist_overlay.png)
![时序指标](../figures/task3_metrics_timeline.png)
"""


def task4_md(timeline: dict) -> str:
    s99 = timeline["timesteps"][99]
    return f"""# 任务四：相空间交互刷选可视分析

## 系统功能
Web 仪表盘集成：可刷选 log 密度直方图、vtk.js 体渲染、刷选体素 3D 点云三联视图。支持 Top 1%（ρ≥p99={s99['p99']:.4f}）与 Bottom 1% 快捷筛选，刷选后 ~2 万体素点云实时联动。

## 验证
Top 1% 点云呈丝状/节点状聚集，与体渲染亮脊一致，验证直方图高密度尾对应宇宙网致密结构。

## 双向关联
统计→空间：框选密度区间定位物理单元；空间→统计：观察 filaments 后可在直方图定位对应密度带。

## 配图
![Top1% 投影](../figures/task4_brush_top1.png)
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
