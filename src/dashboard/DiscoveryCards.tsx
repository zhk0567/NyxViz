import {
  computeStoryMetrics,
  DISCOVERY_CARDS,
  discoveryDetail,
  type StoryMetrics,
} from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

interface DiscoveryCardsProps {
  timeline: TimelineData;
  /** 长卷页：更大字号、2×2 布局 + 底部质量对比条 */
  variant?: 'default' | 'poster' | 'representative';
}

function MassHighlightPanel({ m }: { m: StoryMetrics }) {
  const vol = m.tailAbovePct;
  const mass = m.massAbovePct;
  return (
    <div className="discovery-mass-panel" aria-label="体积与质量占比">
      <h5 className="discovery-mass-title">少数致密区承载可见结构 · t=99</h5>
      <div className="discovery-mass-inner">
        <div
          className="discovery-donut"
          style={{
            background: `conic-gradient(
              #ff6b2c 0 ${vol}%,
              #1e2b48 ${vol}% 100%
            )`,
          }}
          role="img"
          aria-label={`体积占比 ${vol.toFixed(2)}%`}
        />
        <div className="discovery-mass-kpis">
          <div className="discovery-mass-kpi">
            <span className="discovery-mass-label">≥p99 体积占比</span>
            <strong className="discovery-mass-value">{vol.toFixed(2)}%</strong>
          </div>
          <div className="discovery-mass-kpi">
            <span className="discovery-mass-label">质量占比（Σρ）</span>
            <strong className="discovery-mass-value">{mass.toFixed(1)}%</strong>
          </div>
          <p className="discovery-mass-note">
            少数高密度体素占据体积小，却承载显著质量份额——与宇宙网节点/纤维一致。
          </p>
        </div>
      </div>
    </div>
  );
}

export function DiscoveryCards({ timeline, variant = 'default' }: DiscoveryCardsProps) {
  const m = computeStoryMetrics(timeline);
  const poster = variant === 'poster';
  const representative = variant === 'representative';

  return (
    <div
      className={`discovery-grid${
        poster ? ' discovery-grid--poster' : ''
      }${representative ? ' discovery-grid--representative' : ''}`}
    >
      {DISCOVERY_CARDS.map((card, i) => (
        <article key={card.id} className={`discovery-tile discovery-tile-${i + 1}`}>
          <span className="discovery-num">{card.icon}</span>
          <h4>{card.title}</h4>
          <p>{discoveryDetail(card.id, m)}</p>
        </article>
      ))}
      {poster ? (
        <MassHighlightPanel m={m} />
      ) : representative ? null : (
        <figure className="discovery-mass">
          <img src="/figures/task5_mass_pie.png" alt="体积与质量占比" loading="lazy" />
          <figcaption>
            少数致密区：体积 {m.tailAbovePct.toFixed(2)}% · 质量 {m.massAbovePct.toFixed(1)}%
          </figcaption>
        </figure>
      )}
    </div>
  );
}
