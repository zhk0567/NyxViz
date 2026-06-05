import { useEffect, useState } from 'react';
import type { TimelineData } from '@/data/types';
import { simpleMarkdownToHtml } from '@/utils/simpleMarkdown';
import {
  REPORT_SECTIONS,
  STORY_SECTIONS,
  EVOLUTION_PHASES,
  figureUrl,
  resolveFigureCandidates,
  type ReportSection,
  type StorySection,
} from './reportSections';
import {
  computeStoryMetrics,
  DISCOVERY_CARDS,
  discoveryDetail,
} from './storyMetrics';
import { CosmicBackdrop } from '@/components/CosmicBackdrop';
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
    return <polyline fill="none" stroke={color} strokeWidth={2} points={pts} />;
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

function StorySectionBlock({
  section,
  timeline,
  onPreview,
}: {
  section: StorySection;
  timeline: TimelineData;
  onPreview: (src: string, label: string) => void;
}) {
  const metrics = computeStoryMetrics(timeline);
  const hero = section.heroFigure;

  return (
    <section id={section.id} className="story-panel panel">
      <h2 className="story-heading">
        <span className="section-num">{section.num}</span>
        {section.title}
      </h2>
      <p className="story-subtitle">{section.subtitle}</p>

      {section.id === 'story-01' && hero && (
        <figure className="story-hero-fig">
          <img src={figureUrl(hero)} alt="t=99 宇宙网体渲染" loading="eager" />
          <figcaption>t=99 体渲染 · cosmic 色标 · 128³ 气体密度</figcaption>
        </figure>
      )}

      {section.id === 'story-02' && (
        <>
          <div className="phase-bands-static">
            {EVOLUTION_PHASES.map((p) => (
              <div key={p.range} className="phase-chip">
                <strong>{p.range}</strong>
                <span>{p.label}</span>
                <small>{p.detail}</small>
              </div>
            ))}
          </div>
          {hero && (
            <div className="gallery-hero">
              <FigureImage name={hero} hero onPreview={onPreview} />
            </div>
          )}
          <div className="gallery-grid gallery-grid-5">
            {section.figures
              .filter((f) => f !== hero)
              .map((fn) => (
                <FigureImage key={fn} name={fn} onPreview={onPreview} />
              ))}
          </div>
        </>
      )}

      {section.id === 'story-03' && (
        <>
          <MetricsSvg timesteps={timeline.timesteps} />
          <div className="story-kpi-row">
            <span>σ: {metrics.s0.std.toFixed(4)} → {metrics.s99.std.toFixed(4)} (+{metrics.sigmaPct.toFixed(1)}%)</span>
            <span>
              p99−p01: {metrics.span0.toFixed(3)} → {metrics.span99.toFixed(3)} (+{metrics.spanPct.toFixed(1)}%)
            </span>
          </div>
          <div className="gallery-grid">
            {section.figures.map((fn) => (
              <FigureImage key={fn} name={fn} onPreview={onPreview} />
            ))}
          </div>
        </>
      )}

      {section.id === 'story-04' && (
        <>
          <div className="verify-cols">
            <div>
              <h4>统计 → 空间</h4>
              <p>Top 1%（ρ≥{metrics.s99.p99.toFixed(2)}）刷选后投影呈丝状/节点聚集。</p>
            </div>
            <div>
              <h4>空间 → 统计</h4>
              <p>filament 亮脊反查密度带 {metrics.filamentBand}，与 Top 1% 区间一致。</p>
            </div>
          </div>
          <div className="gallery-grid gallery-grid-2">
            {section.figures.map((fn) => (
              <FigureImage key={fn} name={fn} onPreview={onPreview} />
            ))}
          </div>
        </>
      )}

      {section.id === 'story-05' && (
        <>
          <div className="discovery-grid">
            {DISCOVERY_CARDS.map((card) => (
              <article key={card.id} className="discovery-card">
                <span className="discovery-icon">{card.icon}</span>
                <h4>{card.title}</h4>
                <p>{discoveryDetail(card.id, metrics)}</p>
              </article>
            ))}
          </div>
          {section.figures[0] && (
            <FigureImage name={section.figures[0]} onPreview={onPreview} />
          )}
        </>
      )}

      {section.id === 'story-06' && hero && (
        <FigureImage name={hero} hero onPreview={onPreview} />
      )}
    </section>
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
              <FigureImage name={heroName} hero onPreview={onPreview} />
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
  const [lightbox, setLightbox] = useState<{ src: string; label: string } | null>(null);
  const [reportsOpen, setReportsOpen] = useState(false);

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
      <div className="results-page cosmic-page-frame">
        <CosmicBackdrop variant="results" fixed />
        <header className="hero">
          <h1>从涨落到宇宙网</h1>
          <p className="error">{error}</p>
        </header>
      </div>
    );
  }

  if (!timeline) {
    return (
      <div className="results-page cosmic-page-frame">
        <CosmicBackdrop variant="results" fixed />
        <header className="hero">
          <h1>从涨落到宇宙网</h1>
          <p className="sub">加载比赛成果…</p>
        </header>
      </div>
    );
  }

  const metrics = computeStoryMetrics(timeline);
  const onPreview = (src: string, label: string) => setLightbox({ src, label });

  return (
    <div className="results-page cosmic-page-frame">
      <CosmicBackdrop variant="results" fixed />
      <header className="hero" id="story-01">
        <h1>从涨落到宇宙网 · 宇宙网诞生记</h1>
        <p className="sub">
          Nyx 128³ 重子气体密度 · 100 时间步 · 体渲染 / 百步统计 / 相空间刷选
        </p>
        <div className="kpi-grid">
          <div className="kpi">
            <span>网格</span>
            <strong>128³</strong>
          </div>
          <div className="kpi">
            <span>时间步</span>
            <strong>0–99</strong>
          </div>
          <div className="kpi">
            <span>σ 变化</span>
            <strong>+{metrics.sigmaPct.toFixed(1)}%</strong>
          </div>
          <div className="kpi">
            <span>p99−p01</span>
            <strong>
              {metrics.span0.toFixed(2)} → {metrics.span99.toFixed(2)}
            </strong>
          </div>
          <div className="kpi">
            <span>≥p99 体积</span>
            <strong>{metrics.tailAbovePct.toFixed(2)}%</strong>
          </div>
          <div className="kpi">
            <span>纤维带</span>
            <strong>{metrics.filamentBand}</strong>
          </div>
        </div>
      </header>

      <nav className="toc">
        {STORY_SECTIONS.map((s) => (
          <a key={s.id} href={`#${s.id}`}>
            {s.num} {s.title.replace(/^[^:]+：/, '').slice(0, 6)}
          </a>
        ))}
        <a href="#reports" onClick={() => setReportsOpen(true)}>
          四题报告
        </a>
        <a href="#stats">统计表</a>
        <a href="/app.html" className="toc-app">
          交互仪表盘 →
        </a>
      </nav>

      <main>
        {STORY_SECTIONS.filter((s) => s.id !== 'story-01').map((sec) => (
          <StorySectionBlock
            key={sec.id}
            section={sec}
            timeline={timeline}
            onPreview={onPreview}
          />
        ))}

        <section id="reports" className="panel reports-collapsible">
          <button
            type="button"
            className="reports-toggle"
            onClick={() => setReportsOpen((o) => !o)}
            aria-expanded={reportsOpen}
          >
            {reportsOpen ? '收起' : '展开'} 四题详细报告（答卷正文）
          </button>
          {reportsOpen &&
            REPORT_SECTIONS.map((sec) => (
              <TaskSection
                key={sec.id}
                section={sec}
                bodyHtml={bodies[sec.id] ?? ''}
                onPreview={onPreview}
              />
            ))}
        </section>

        <section id="stats" className="panel">
          <h2>100 时间步密度统计（预计算）</h2>
          <p>
            由 <code>tools/python/precompute.py</code> 汇总；与交互页、答卷数字一致。
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>t</th>
                  <th>mean</th>
                  <th>σ</th>
                  <th>p90</th>
                  <th>p99</th>
                  <th>≥p99%</th>
                  <th>≤p01%</th>
                  <th>偏度</th>
                </tr>
              </thead>
              <tbody>
                {timeline.timesteps.map((s) => (
                  <tr key={s.timestep}>
                    <td>{s.timestep}</td>
                    <td>{s.mean.toFixed(4)}</td>
                    <td>{s.std.toFixed(4)}</td>
                    <td>{s.p90.toFixed(4)}</td>
                    <td>{s.p99.toFixed(4)}</td>
                    <td>{(s.tailMassAboveP99 * 100).toFixed(2)}</td>
                    <td>{(s.tailMassBelowP01 * 100).toFixed(2)}</td>
                    <td>{s.skewness.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel app-link-panel">
          <h2>三栏交互仪表盘</h2>
          <p>
            左栏百步统计与三向切片，中栏体渲染常驻，右栏直方图刷选与 XY 投影联动。需本地{' '}
            <code>Nyx/</code> 数据。
          </p>
          <a className="btn-primary" href="/app.html">
            打开 /app.html
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
          <button type="button" className="lightbox-close" onClick={() => setLightbox(null)}>
            关闭
          </button>
          <img src={lightbox.src} alt={lightbox.label} onClick={(e) => e.stopPropagation()} />
          <p>{lightbox.label}</p>
        </div>
      )}

      <footer>
        NyxViz · 宇宙网诞生记 · <code>npm run submission-pack</code> 再生交付物
      </footer>
    </div>
  );
}
