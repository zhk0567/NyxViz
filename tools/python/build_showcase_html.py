"""Build a single self-contained HTML showcase with embedded figures and stats."""
from __future__ import annotations

import argparse
import base64
import gzip
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "figures"
STATS = ROOT / "public" / "stats" / "timeline.json"
REPORT_DIR = ROOT / "docs" / "report"
OUT = ROOT / "docs" / "showcase" / "NyxViz_Showcase.html"

TASK_SECTIONS = [
    ("task1", "任务一：体数据渲染与密度演化", "task1_volume.md"),
    ("task2", "任务二：宇宙密度演化规律归纳", "task2_evolution.md"),
    ("task3", "任务三：时序密度对数直方图统计", "task3_histogram.md"),
    ("task4", "任务四：相空间交互刷选可视分析", "task4_brush.md"),
]

def task1_figure_names() -> list[str]:
    steps = [0, 25, 50, 75, 99]
    names = []
    for t in steps:
        vol = f"task1_vol_t{t:04d}.png"
        slc = f"task1_slice_t{t:04d}.png"
        legacy = f"task1_t{t:04d}.png"
        if (FIGURES / vol).exists():
            names.append(vol)
        elif (FIGURES / legacy).exists():
            names.append(legacy)
        elif (FIGURES / slc).exists():
            names.append(slc)
    return names


FIGURE_GROUPS = [
    (
        "task1",
        "体渲染关键帧（vtk.js 光线投射，t = 0 / 25 / 50 / 75 / 99）",
        ["task1_vol_strip.png"],
    ),
    (
        "task2",
        "演化规律配图（四联指标 + 体渲染对比）",
        [
            "task2_evolution_story.png",
            "task1_vol_t0000.png",
            "task1_vol_t0099.png",
            "task3_hist_overlay.png",
        ],
    ),
    (
        "task3",
        "时序统计图（100 步）",
        [
            "task3_hist_overlay.png",
            "task3_metrics_timeline.png",
            "task3_evolution_metrics.png",
        ],
    ),
    (
        "task4",
        "刷选联动验证",
        [
            "task4_brush_triptych.png",
            "task4_hist_brush_top1.png",
            "task4_brush_top1.png",
        ],
    ),
]


def resolve_figure(name: str) -> str | None:
    candidates = [
        name,
        name.replace("task1_vol_", "task1_"),
        name.replace("task1_vol_", "task1_slice_"),
    ]
    for c in candidates:
        if (FIGURES / c).exists():
            return c
    return None


def build_showcase_bundle() -> tuple[str, str]:
    """Build IIFE bundle via Vite; return (js, css)."""
    subprocess.run(
        ["npm", "run", "build:showcase"],
        cwd=ROOT,
        check=True,
        shell=sys.platform == "win32",
    )
    js_path = ROOT / "dist-showcase" / "showcase.iife.js"
    if not js_path.exists():
        raise FileNotFoundError(f"Missing {js_path}")
    css_path = ROOT / "dist-showcase" / "showcase.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    return js_path.read_text(encoding="utf-8"), css


def embed_timesteps_gzip(steps: list[int]) -> str:
    nyx = ROOT / "Nyx"
    payload: dict[str, str] = {}
    for t in steps:
        raw = (nyx / f"{t:04d}.dat").read_bytes()
        payload[str(t)] = base64.standard_b64encode(gzip.compress(raw)).decode("ascii")
    return json.dumps(payload)


def embed_image(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.standard_b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def md_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_list = False
    for line in lines:
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{html.escape(line[3:])}</h3>")
        elif line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{html.escape(line[4:])}</h4>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("![") and "](" in line:
            continue
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if line.strip():
                out.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def build_metrics_svg(timesteps: list[dict]) -> str:
    w, h, pad = 720, 220, 48
    ts = [s["timestep"] for s in timesteps]
    mean = [s["mean"] for s in timesteps]
    std = [s["std"] for s in timesteps]
    p99 = [s["p99"] for s in timesteps]
    y_min = min(mean) - 0.2
    y_max = max(p99) + 0.2

    def sx(t: int) -> float:
        return pad + (w - 2 * pad) * t / 99

    def sy(v: float) -> float:
        return h - pad - (h - 2 * pad) * (v - y_min) / (y_max - y_min)

    def poly(vals: list[float], color: str) -> str:
        pts = " ".join(f"{sx(t):.1f},{sy(v):.1f}" for t, v in zip(ts, vals))
        return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}"/>'

    legend = """
    <text x="560" y="28" fill="#58a6ff" font-size="12">● 均值</text>
    <text x="560" y="48" fill="#f0c040" font-size="12">● p99</text>
    <text x="560" y="68" fill="#6ad49b" font-size="12">● 标准差</text>
    """
    return f"""<svg viewBox="0 0 {w} {h}" class="metrics-svg" role="img" aria-label="时序指标曲线">
      <rect width="{w}" height="{h}" fill="#0d1117"/>
      {poly(mean, "#58a6ff")}
      {poly(p99, "#f0c040")}
      {poly(std, "#6ad49b")}
      {legend}
      <text x="{pad}" y="{h-8}" fill="#8b949e" font-size="11">0</text>
      <text x="{w-pad-20}" y="{h-8}" fill="#8b949e" font-size="11">99</text>
    </svg>"""


def build_stats_table(timesteps: list[dict]) -> str:
    rows = []
    for s in timesteps:
        rows.append(
            "<tr>"
            f"<td>{s['timestep']}</td>"
            f"<td>{s['min']:.4f}</td>"
            f"<td>{s['max']:.4f}</td>"
            f"<td>{s['mean']:.4f}</td>"
            f"<td>{s['std']:.4f}</td>"
            f"<td>{s['p01']:.4f}</td>"
            f"<td>{s['p99']:.4f}</td>"
            f"<td>{s['skewness']:.4f}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--embed-steps",
        type=str,
        default="",
        help="Comma-separated timesteps to gzip-embed for offline (e.g. 0,99)",
    )
    parser.add_argument("--skip-bundle", action="store_true")
    args = parser.parse_args()

    if not STATS.exists():
        print("Run: npm run precompute", file=sys.stderr)
        return 1

    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    timesteps = timeline["timesteps"]

    figure_html: dict[str, str] = {}
    for path in FIGURES.glob("*.png"):
        figure_html[path.name] = embed_image(path)

    sections_html = []
    for sec_id, title, md_name in TASK_SECTIONS:
        md_path = REPORT_DIR / md_name
        body = md_to_html(md_path.read_text(encoding="utf-8")) if md_path.exists() else ""
        gallery = ""
        for gid, gtitle, files in FIGURE_GROUPS:
            if gid != sec_id:
                continue
            file_list = task1_figure_names() if files is None else files
            imgs = []
            for fn in file_list:
                resolved = resolve_figure(fn)
                if not resolved:
                    continue
                src = figure_html.get(resolved)
                if not src:
                    continue
                label = resolved.replace(".png", "").replace("_", " ")
                imgs.append(
                    f'<figure class="shot"><img src="{src}" alt="{html.escape(label)}"/>'
                    f'<figcaption>{html.escape(label)}</figcaption></figure>'
                )
            if imgs:
                gallery = f'<div class="gallery"><h4>{html.escape(gtitle)}</h4>{"".join(imgs)}</div>'
        sections_html.append(
            f'<section id="{sec_id}" class="task-section">'
            f'<h2>{html.escape(title)}</h2>{body}{gallery}</section>'
        )

    embed_steps = [int(s.strip()) for s in args.embed_steps.split(",") if s.strip()]
    embedded_data_js = ""
    if embed_steps:
        embedded_data_js = f"""
    const __NYX_GZIP_B64__ = {embed_timesteps_gzip(embed_steps)};
    window.__NYX_EMBEDDED_TIMESTEPS__ = {{}};
    for (const [k, b64] of Object.entries(__NYX_GZIP_B64__)) {{
      const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const raw = pako.inflate(bin);
      window.__NYX_EMBEDDED_TIMESTEPS__[Number(k)] = new Float32Array(raw.buffer);
    }}
"""

    bundle_js = ""
    bundle_css = ""
    if not args.skip_bundle:
        try:
            bundle_js, bundle_css = build_showcase_bundle()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Warning: showcase bundle failed: {e}", file=sys.stderr)

    s0, s99 = timesteps[0], timesteps[99]
    overview = f"""
    <p>本页汇总 Nyx 赛题 II 全部可视化成果：128³ 气体密度、100 演化时间步、体渲染/统计/刷选联动。
    数据路径 <code>Nyx/0000.dat–0099.dat</code>，小端 float32，z→y→x 列优先。</p>
    <div class="kpi-grid">
      <div class="kpi"><span>网格</span><strong>128³</strong></div>
      <div class="kpi"><span>时间步</span><strong>100</strong></div>
      <div class="kpi"><span>t=0 σ</span><strong>{s0['std']:.4f}</strong></div>
      <div class="kpi"><span>t=99 σ</span><strong>{s99['std']:.4f}</strong></div>
      <div class="kpi"><span>全局密度范围</span><strong>{timeline['globalMin']:.2f} – {timeline['globalMax']:.2f}</strong></div>
      <div class="kpi"><span>p99 跨度变化</span><strong>{s0['p99']-s0['p01']:.3f} → {s99['p99']-s99['p01']:.3f}</strong></div>
    </div>
    """

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Nyx 宇宙密度可视化 — 完整展示</title>
  <style>
    :root {{
      --bg: #0d1117;
      --panel: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
    }}
    header.hero {{
      padding: 2.5rem 2rem 2rem;
      background: linear-gradient(135deg, #0d1117 0%, #1a1f3a 50%, #0d1117 100%);
      border-bottom: 1px solid var(--border);
    }}
    header.hero h1 {{
      margin: 0 0 0.5rem;
      font-size: 1.85rem;
      font-weight: 700;
      background: linear-gradient(90deg, #58a6ff, #a371f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    header.hero .sub {{ color: var(--muted); margin: 0; }}
    nav.toc {{
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      padding: 0.75rem 1.5rem;
      background: rgba(13,17,23,0.92);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border);
    }}
    nav.toc a {{
      color: var(--accent);
      text-decoration: none;
      font-size: 0.85rem;
      padding: 0.35rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    nav.toc a:hover {{ background: #21262d; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; }}
    section {{ margin-bottom: 3rem; }}
    section h2 {{
      font-size: 1.35rem;
      border-left: 4px solid var(--accent);
      padding-left: 0.75rem;
      margin: 0 0 1rem;
    }}
    section h3 {{ color: #c9d1d9; margin-top: 1.25rem; }}
    section h4 {{ color: var(--muted); font-size: 0.95rem; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem 1.5rem;
      margin: 1rem 0;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 0.75rem;
      margin-top: 1rem;
    }}
    .kpi {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 1rem;
    }}
    .kpi span {{ display: block; font-size: 0.75rem; color: var(--muted); }}
    .kpi strong {{ font-size: 1.1rem; color: var(--accent); }}
    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }}
    figure.shot {{
      margin: 0;
      background: #0d1117;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    figure.shot img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    figcaption {{
      padding: 0.5rem 0.75rem;
      font-size: 0.8rem;
      color: var(--muted);
      text-align: center;
    }}
    .metrics-svg {{
      width: 100%;
      max-width: 720px;
      height: auto;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .table-wrap {{
      overflow-x: auto;
      max-height: 420px;
      overflow-y: auto;
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }}
    th, td {{
      padding: 0.4rem 0.6rem;
      border-bottom: 1px solid var(--border);
      text-align: right;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #21262d;
      color: var(--muted);
    }}
    tr:nth-child(even) td {{ background: rgba(255,255,255,0.02); }}
    code {{
      background: #21262d;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-size: 0.9em;
    }}
    .app-note {{
      border-left: 4px solid var(--green);
      padding: 1rem 1.25rem;
      background: rgba(63,185,80,0.08);
      border-radius: 0 8px 8px 0;
      margin: 1rem 0;
    }}
    footer {{
      text-align: center;
      padding: 2rem;
      color: var(--muted);
      font-size: 0.85rem;
      border-top: 1px solid var(--border);
    }}
    ul {{ padding-left: 1.25rem; }}
    li {{ margin: 0.25rem 0; }}
    #showcase-root {{ min-height: 720px; }}
    .showcase-embedded .brush-grid {{ height: auto; min-height: 680px; }}
    .showcase-wrap {{ border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
    {bundle_css}
  </style>
  {"<script src=\"https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako.min.js\"></script>" if embed_steps else ""}
  <script type="application/json" id="timeline-data">{json.dumps(timeline, ensure_ascii=False).replace("<", "\\u003c")}</script>
</head>
<body>
  <header class="hero">
    <h1>Nyx 宇宙学密度可视化 — 完整成果展示</h1>
    <p class="sub">赛题 II · 科学可视化挑战赛 · 体渲染 / 时序统计 / 相空间刷选联动</p>
  </header>
  <nav class="toc">
    <a href="#overview">概览</a>
    <a href="#task1">任务一</a>
    <a href="#task2">任务二</a>
    <a href="#task3">任务三</a>
    <a href="#task4">任务四</a>
    <a href="#stats">全步统计表</a>
    <a href="#interactive">交互演示</a>
  </nav>
  <script>
    window.__NYX_TIMELINE__ = JSON.parse(document.getElementById('timeline-data').textContent);
    {embedded_data_js}
  </script>
  <main>
    <section id="overview" class="panel">
      <h2>项目概览</h2>
      {overview}
    </section>
    {"".join(sections_html)}
    <section id="stats" class="panel">
      <h2>100 时间步密度统计（预计算）</h2>
      <p>下表为 <code>tools/python/precompute.py</code> 对每步全域密度的汇总；上图为由相同数据绘制的 SVG 时序曲线。</p>
      {build_metrics_svg(timesteps)}
      <div class="table-wrap" style="margin-top:1rem">
        <table>
          <thead>
            <tr>
              <th>步</th><th>min</th><th>max</th><th>mean</th><th>std</th><th>p01</th><th>p99</th><th>偏度</th>
            </tr>
          </thead>
          <tbody>
            {build_stats_table(timesteps)}
          </tbody>
        </table>
      </div>
    </section>
    <section id="interactive" class="panel">
      <h2>交互演示（体渲染 + 直方图刷选 + 点云联动）</h2>
      <div class="app-note">
        <p>下方为内嵌 vtk.js 仪表盘。全部 100 步数据需通过 HTTP 访问 <code>/Nyx/####.dat</code>
        （运行 <code>npm run preview</code> 后打开本页同源访问）。
        {"已内嵌时间步: " + ", ".join(str(s) for s in embed_steps) + "（可 file:// 离线试用）。" if embed_steps else "生成时加 <code>--embed-steps 0,99</code> 可内嵌代表步。"}</p>
      </div>
      <div class="showcase-wrap">
        <div id="showcase-root"></div>
      </div>
    </section>
  </main>
  <footer>
    NyxViz · 数据来源：赛题指定 Nyx 宇宙学模拟密度场 · tools/python/build_showcase_html.py
  </footer>
  {f"<script>{bundle_js}</script>" if bundle_js else "<p><!-- showcase bundle missing: npm run build:showcase --></p>"}
</body>
</html>
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"Wrote {OUT} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
