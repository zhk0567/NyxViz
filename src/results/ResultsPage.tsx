import { useEffect, useState } from 'react';
import type { TimelineData } from '@/data/types';
import { simpleMarkdownToHtml } from '@/utils/simpleMarkdown';
import {
  REPORT_SECTIONS,
  figureUrl,
  resolveFigureCandidates,
  type ReportSection,
} from './reportSections';
import './results.css';

function FigureImage({
  name,
  onPreview,
  hero,
}: {
  name: string;
  onPreview?: (src: string, label: string) => void;
  hero?: boolean;
}) {
  const candidates = resolveFigureCandidates(name);
  const [src, setSrc] = useState(figureUrl(candidates[0]!));
  const [failed, setFailed] = useState(false);
  const [idx, setIdx] = useState(0);

  const onError = () => {
    const next = idx + 1;
    if (next < candidates.length) {
      setIdx(next);
      setSrc(figureUrl(candidates[next]!));
    } else {
      setFailed(true);
    }
  };

  const label = name.replace('.png', '').replace(/_/g, ' ');

  if (failed) {
    return (
      <figure className={`shot shot-missing${hero ? ' shot-hero' : ''}`}>
        <div className="shot-placeholder">配图未生成：{label}</div>
        <figcaption>{label}</figcaption>
      </figure>
    );
  }

  return (
    <figure className={`shot${hero ? ' shot-hero' : ''}`}>
      <button
        type="button"
        className="shot-btn"
        onClick={() => onPreview?.(src, label)}
        aria-label={`放大查看 ${label}`}
      >
        <img src={src} alt={label} onError={onError} loading="lazy" />
      </button>
      <figcaption>{label}</figcaption>
    </figure>
  );
}

function MetricsSvg({ timesteps }: { timesteps: TimelineData['timesteps'] }) {
  const w = 720;
  const h = 220;
  const pad = 48;
  const ts = timesteps.map((s) => s.timestep);
  const mean = timesteps.map((s) => s.mean);
  const std = timesteps.map((s) => s.std);
  const p99 = timesteps.map((s) => s.p99);
  const yMin = Math.min(...mean) - 0.2;
  const yMax = Math.max(...p99) + 0.2;

  const sx = (t: number) => pad + ((w - 2 * pad) * t) / 99;
  const sy = (v: number) => h - pad - ((h - 2 * pad) * (v - yMin)) / (yMax - yMin);

  const poly = (vals: number[], color: string) => {
    const pts = ts.map((t, i) => `${sx(t).toFixed(1)},${sy(vals[i]!).toFixed(1)}`).join(' ');
    return (
      <polyline fill="none" stroke={color} strokeWidth={2} points={pts} />
    );
  };

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="metrics-svg" role="img" aria-label="时序指标曲线">
      <rect width={w} height={h} fill="#0a0e1a" />
      {poly(mean, '#7c6cf0')}
      {poly(p99, '#f5c842')}
      {poly(std, '#3dd6c6')}
      <text x={560} y={28} fill="#7c6cf0" fontSize={12}>
        ● 均值
      </text>
      <text x={560} y={48} fill="#f5c842" fontSize={12}>
        ● p99
      </text>
      <text x={560} y={68} fill="#3dd6c6" fontSize={12}>
        ● 标准差
      </text>
      <text x={pad} y={h - 8} fill="#9aa3b8" fontSize={11}>
        0
      </text>
      <text x={w - pad - 20} y={h - 8} fill="#9aa3b8" fontSize={11}>
        99
      </text>
    </svg>
  );
}

function TaskSection({
  section,
  bodyHtml,
  onPreview,
}: {
  section: ReportSection;
  bodyHtml: string;
  onPreview: (src: string, label: string) => void;
}) {
  const heroName = section.id === 'task1' ? 'task1_vol_strip.png' : undefined;

  return (
    <section id={section.id} className="task-section panel">
      <h2>{section.title}</h2>
      <div className="report-body" dangerouslySetInnerHTML={{ __html: bodyHtml }} />
      {section.galleryTitle && section.figures.length > 0 && (
        <div className="gallery">
          <h4>{section.galleryTitle}</h4>
          {heroName && section.figures.includes(heroName) && (
            <div className="gallery-hero">
              <FigureImage
                key={`hero-${heroName}`}
                name={heroName}
                hero
                onPreview={onPreview}
              />
            </div>
          )}
          <div className="gallery-grid">
            {section.figures
              .filter((fn) => fn !== heroName)
              .map((fn) => (
                <FigureImage key={fn} name={fn} onPreview={onPreview} />
              ))}
          </div>
        </div>
      )}
    </section>
  );
}

export function ResultsPage() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [bodies, setBodies] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<{ src: string; label: string } | null>(
    null,
  );

  useEffect(() => {
    fetch('/stats/timeline.json')
      .then((r) => {
        if (!r.ok) throw new Error('缺少 timeline.json，请先运行 precompute');
        return r.json();
      })
      .then(setTimeline)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  useEffect(() => {
    Promise.all(
      REPORT_SECTIONS.map(async (sec) => {
        const res = await fetch(`/report/${sec.mdFile}`);
        const text = res.ok ? await res.text() : '';
        return [sec.id, simpleMarkdownToHtml(text)] as const;
      }),
    ).then((pairs) => {
      const map: Record<string, string> = {};
      for (const [id, html] of pairs) map[id] = html;
      setBodies(map);
    });
  }, []);

  if (error) {
    return (
      <div className="results-page">
        <header className="hero">
          <h1>Nyx 宇宙学密度可视化</h1>
          <p className="error">{error}</p>
        </header>
      </div>
    );
  }

  if (!timeline) {
    return (
      <div className="results-page">
        <header className="hero">
          <h1>Nyx 宇宙学密度可视化</h1>
          <p className="sub">加载比赛成果…</p>
        </header>
      </div>
    );
  }

  const s0 = timeline.timesteps[0]!;
  const s99 = timeline.timesteps[99]!;

  return (
    <div className="results-page">
      <header className="hero">
        <h1>Nyx 宇宙学密度可视化 — 完整成果展示</h1>
        <p className="sub">赛题 II · 体渲染 / 时序统计 / 相空间刷选 · 科学可视化挑战赛</p>
      </header>

      <nav className="toc">
        <a href="#overview">概览</a>
        {REPORT_SECTIONS.map((s) => (
          <a key={s.id} href={`#${s.id}`}>
            {s.title.replace(/^任务[一二三四]：/, '')}
          </a>
        ))}
        <a href="#stats">统计表</a>
        <a href="/app.html" className="toc-app">
          交互演示 →
        </a>
      </nav>

      <main>
        <section id="overview" className="panel">
          <h2>项目概览</h2>
          <p>
            本页为赛题 II 全部可视化成果：128³ 气体密度、100 演化时间步、体渲染 / 统计 /
            刷选联动分析。数据为 <code>Nyx/0000.dat–0099.dat</code>，小端 float32，z→y→x
            列优先。
          </p>
          <div className="kpi-grid">
            <div className="kpi">
              <span>网格</span>
              <strong>128³</strong>
            </div>
            <div className="kpi">
              <span>时间步</span>
              <strong>100</strong>
            </div>
            <div className="kpi">
              <span>t=0 σ</span>
              <strong>{s0.std.toFixed(4)}</strong>
            </div>
            <div className="kpi">
              <span>t=99 σ</span>
              <strong>{s99.std.toFixed(4)}</strong>
            </div>
            <div className="kpi">
              <span>全局密度</span>
              <strong>
                {timeline.globalMin.toFixed(2)} – {timeline.globalMax.toFixed(2)}
              </strong>
            </div>
            <div className="kpi">
              <span>p99 跨度</span>
              <strong>
                {(s0.p99 - s0.p01).toFixed(3)} → {(s99.p99 - s99.p01).toFixed(3)}
              </strong>
            </div>
          </div>
          <figure className="overview-hero">
            <img
              src={figureUrl('task1_vol_strip.png')}
              alt="体渲染五时刻条带"
              loading="eager"
            />
            <figcaption>体渲染演化条带（全局 log 色标 · 展板质量截图）</figcaption>
          </figure>
        </section>

        {REPORT_SECTIONS.map((sec) => (
          <TaskSection
            key={sec.id}
            section={sec}
            bodyHtml={bodies[sec.id] ?? ''}
            onPreview={(src, label) => setLightbox({ src, label })}
          />
        ))}

        <section id="stats" className="panel">
          <h2>100 时间步密度统计（预计算）</h2>
          <p>
            下表由 <code>tools/python/precompute.py</code> 对每步全域密度汇总；上图为相同数据的时序曲线。
          </p>
          <MetricsSvg timesteps={timeline.timesteps} />
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>步</th>
                  <th>min</th>
                  <th>max</th>
                  <th>mean</th>
                  <th>std</th>
                  <th>p01</th>
                  <th>p99</th>
                  <th>偏度</th>
                </tr>
              </thead>
              <tbody>
                {timeline.timesteps.map((s) => (
                  <tr key={s.timestep}>
                    <td>{s.timestep}</td>
                    <td>{s.min.toFixed(4)}</td>
                    <td>{s.max.toFixed(4)}</td>
                    <td>{s.mean.toFixed(4)}</td>
                    <td>{s.std.toFixed(4)}</td>
                    <td>{s.p01.toFixed(4)}</td>
                    <td>{s.p99.toFixed(4)}</td>
                    <td>{s.skewness.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel app-link-panel">
          <h2>需要实时交互？</h2>
          <p>
            本页为静态比赛成果（报告 + 配图 + 统计表）。体渲染、直方图刷选、点云联动请打开
            交互仪表盘（需本地 <code>Nyx/</code> 数据）。
          </p>
          <a className="btn-primary" href="/app.html">
            打开交互演示
          </a>
        </section>
      </main>

      {lightbox && (
        <div
          className="lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={lightbox.label}
          onClick={() => setLightbox(null)}
          onKeyDown={(e) => e.key === 'Escape' && setLightbox(null)}
        >
          <button
            type="button"
            className="lightbox-close"
            onClick={() => setLightbox(null)}
          >
            关闭
          </button>
          <img src={lightbox.src} alt={lightbox.label} onClick={(e) => e.stopPropagation()} />
          <p>{lightbox.label}</p>
        </div>
      )}

      <footer>
        NyxViz · 赛题 Nyx 宇宙学模拟密度场 · 展板配图请运行{' '}
        <code>npm run figures:hd</code>（含 <code>capture-volumes</code>，默认展板质量）
      </footer>
    </div>
  );
}
