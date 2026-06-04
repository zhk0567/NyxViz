import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

const EVO_STEPS = [0, 25, 50, 75, 99] as const;

interface VideoFindingsStripProps {
  timeline: TimelineData;
}

export function VideoFindingsStrip({ timeline }: VideoFindingsStripProps) {
  const m = computeStoryMetrics(timeline);

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

        <article className="vd-finding">
          <header>
            <span className="vd-finding-num">02</span>
            <h3 className="vd-finding-title">密度分布两极化</h3>
          </header>
          <div className="vd-finding-media vd-finding-media-wide">
            <img
              className="vd-finding-img"
              src="/figures/task3_hist_overlay.png"
              alt="t=0 与 t=99 直方图对比"
              loading="lazy"
            />
          </div>
          <p className="vd-finding-note">
            σ +{m.sigmaPct.toFixed(1)}% · 右尾增厚 void 与节点并存
          </p>
        </article>

        <article className="vd-finding">
          <header>
            <span className="vd-finding-num">03</span>
            <h3 className="vd-finding-title">1% 体积 · 24% 质量</h3>
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
                <strong>{m.tailAbovePct.toFixed(2)}%</strong>
              </div>
              <div className="vd-finding-mass-row">
                <span className="vd-finding-mass-label">质量</span>
                <div className="vd-finding-mass-bar vd-finding-mass-bar-mass" aria-hidden>
                  <span style={{ width: `${Math.min(m.massAbovePct, 100)}%` }} />
                </div>
                <strong>{m.massAbovePct.toFixed(1)}%</strong>
              </div>
            </div>
          </div>
        </article>

        <article className="vd-finding">
          <header>
            <span className="vd-finding-num">04</span>
            <h3 className="vd-finding-title">统计—空间验证</h3>
          </header>
          <div className="vd-finding-verify">
            <div className="vd-finding-media vd-finding-media-square">
              <img src="/figures/task4_brush_top1.png" alt="Top 1% 空间" loading="lazy" />
            </div>
            <div className="vd-finding-media vd-finding-media-square">
              <img src="/figures/task4_brush_bottom1.png" alt="Bottom 1%" loading="lazy" />
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
