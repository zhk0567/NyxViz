import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

const EVO_STEPS = [0, 25, 50, 75, 99] as const;

interface VideoFindingsStripProps {
  timeline: TimelineData;
}

export function VideoFindingsStrip({ timeline }: VideoFindingsStripProps) {
  const m = computeStoryMetrics(timeline);
  const s = timeline.timesteps[99]!;

  return (
    <section className="vd-findings" aria-label="关键科学发现">
      <h2 className="vd-findings-heading">关键科学发现</h2>
      <div className="vd-findings-grid">
        <article className="vd-finding">
          <header>
            <span className="vd-finding-num">01</span>
            <h3 className="vd-finding-title">宇宙网形成</h3>
          </header>
          <div className="vd-finding-evo">
            {EVO_STEPS.map((t) => (
              <figure key={t}>
                <div className="vd-finding-media vd-finding-media-square">
                  <img
                    src={`/figures/task1_evo_t${String(t).padStart(4, '0')}.png`}
                    alt={`t=${t}`}
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.src = `/figures/task1_vol_t${String(t).padStart(4, '0')}.png`;
                    }}
                  />
                </div>
                <figcaption>t={t}</figcaption>
              </figure>
            ))}
          </div>
        </article>

        <article className="vd-finding vd-finding--metrics">
          <header className="vd-finding-head-stack">
            <span className="vd-finding-num">02</span>
            <div className="vd-finding-head-text">
              <h3 className="vd-finding-title">密度分布两极化</h3>
              <p className="vd-finding-note vd-finding-note--inline">
                <strong className="vd-metric-em">σ +{m.sigmaPct.toFixed(1)}%</strong>
                {' · '}
                <strong className="vd-metric-em">p99−p01 +{m.spanPct.toFixed(1)}%</strong>
                {' · 右尾增厚'}
              </p>
            </div>
          </header>
          <div className="vd-finding-media vd-finding-media-wide vd-finding-media-zoom">
            <img
              className="vd-finding-img"
              src="/figures/task3_evolution_metrics.png"
              alt="σ、偏度与 p99−p01 时序演化"
              loading="lazy"
            />
          </div>
        </article>

        <article className="vd-finding vd-finding--mass">
          <header>
            <span className="vd-finding-num">03</span>
            <h3 className="vd-finding-title">
              <strong className="vd-metric-em">1%</strong> 体积 ·{' '}
              <strong className="vd-metric-em">{m.massAbovePct.toFixed(0)}%</strong> 质量
            </h3>
          </header>
          <div className="vd-finding-mass">
            <div
              className="vd-finding-donut"
              style={{
                background: `conic-gradient(#ff6b2c 0 ${m.tailAbovePct}%, #1a2848 ${m.tailAbovePct}% 100%)`,
              }}
              role="img"
              aria-label={`≥p99 体积 ${m.tailAbovePct.toFixed(2)}%`}
            />
            <div className="vd-finding-mass-metrics">
              <div className="vd-finding-mass-row">
                <span className="vd-finding-mass-label">体积</span>
                <div className="vd-finding-mass-bar" aria-hidden>
                  <span style={{ width: `${Math.max(m.tailAbovePct, 2)}%` }} />
                </div>
                <strong className="vd-metric-em">{m.tailAbovePct.toFixed(2)}%</strong>
              </div>
              <div className="vd-finding-mass-row">
                <span className="vd-finding-mass-label">质量</span>
                <div className="vd-finding-mass-bar vd-finding-mass-bar-mass" aria-hidden>
                  <span style={{ width: `${Math.min(m.massAbovePct, 100)}%` }} />
                </div>
                <strong className="vd-metric-em">{m.massAbovePct.toFixed(1)}%</strong>
              </div>
            </div>
          </div>
        </article>

        <article className="vd-finding vd-finding--verify">
          <header>
            <span className="vd-finding-num">04</span>
            <h3 className="vd-finding-title">统计—空间验证</h3>
          </header>
            <div className="vd-finding-verify">
            <figure className="vd-finding-verify-item">
              <figcaption className="vd-finding-cap">
                <strong className="vd-metric-em">Top 1%</strong> · ρ≥{s.p99.toFixed(2)}
              </figcaption>
              <div className="vd-finding-media vd-finding-media-verify">
                <img
                  src="/figures/task4_brush_top1_viz.png"
                  alt="Top 1% 空间投影"
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.src = '/figures/task4_brush_top1.png';
                  }}
                />
              </div>
            </figure>
            <figure className="vd-finding-verify-item">
              <figcaption className="vd-finding-cap">
                Bottom 1% · ρ≤{s.p01.toFixed(2)}
              </figcaption>
              <div className="vd-finding-media vd-finding-media-verify">
                <img
                  src="/figures/task4_brush_bottom_hl.png"
                  alt="Bottom 1% 刷选高亮"
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.src = '/figures/task4_brush_bottom1.png';
                    e.currentTarget.parentElement?.classList.add('vd-finding-media-crop-right');
                  }}
                />
              </div>
            </figure>
          </div>
        </article>
      </div>
    </section>
  );
}
