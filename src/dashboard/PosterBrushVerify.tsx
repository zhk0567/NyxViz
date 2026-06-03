import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

interface BrushRowProps {
  title: string;
  accentClass: 'accent-high' | 'accent-low';
  histSrc: string;
  spatialSrc: string;
  stats: { label: string; value: string }[];
  spatialNote: string;
  /** Top 1% 显示亮脊局部放大 */
  showZoom?: boolean;
}

function BrushRow({
  title,
  accentClass,
  histSrc,
  spatialSrc,
  stats,
  spatialNote,
  showZoom = false,
}: BrushRowProps) {
  return (
    <article className={`pl-brush-row ${accentClass}`}>
      <h3 className="pl-brush-row-title">{title}</h3>
      <div className={`pl-brush-grid${showZoom ? '' : ' pl-brush-grid--no-zoom'}`}>
        <figure className="pl-brush-cell">
          <figcaption>统计刷选</figcaption>
          <div className="pl-brush-media">
            <img src={histSrc} alt="" loading="lazy" />
          </div>
        </figure>

        <div className="pl-brush-arrow" aria-hidden>
          ⇄
        </div>

        <figure className="pl-brush-cell pl-brush-spatial">
          <figcaption>XY 空间投影</figcaption>
          <div className="pl-brush-media">
            <img src={spatialSrc} alt="" loading="lazy" />
          </div>
        </figure>

        <aside className="pl-brush-stats">
          <h4>结构要点</h4>
          <ul>
            {stats.map((s) => (
              <li key={s.label}>
                <span className="pl-brush-stat-label">{s.label}</span>
                <span className="pl-brush-stat-value">{s.value}</span>
              </li>
            ))}
          </ul>
        </aside>

        {showZoom ? (
          <figure className="pl-brush-cell pl-brush-zoom">
            <figcaption>局部放大（亮脊）</figcaption>
            <div className="pl-brush-media pl-brush-media--zoom">
              <img src={spatialSrc} alt="" loading="lazy" />
            </div>
          </figure>
        ) : null}
      </div>
      {spatialNote ? <p className="pl-brush-row-caption">{spatialNote}</p> : null}
    </article>
  );
}

export function PosterBrushVerify({ timeline }: { timeline: TimelineData }) {
  const s = timeline.timesteps[99]!;
  const m = computeStoryMetrics(timeline);

  return (
    <div className="pl-brush-verify">
      <BrushRow
        title="Top 1% 高密度尾 → 宇宙网节点 / 纤维"
        accentClass="accent-high"
        histSrc="/figures/task4_hist_brush_top1.png"
        spatialSrc="/figures/task4_brush_top1.png"
        spatialNote="刷选高密度尾区后，XY 投影呈现丝状亮脊与节点聚集。"
        showZoom
        stats={[
          { label: '密度阈值', value: `ρ ≥ p99 (${s.p99.toFixed(2)})` },
          { label: '体积占比', value: `${(s.tailMassAboveP99 * 100).toFixed(2)}%` },
          { label: '质量占比', value: `${m.massAbovePct.toFixed(1)}%` },
          { label: '空间特征', value: '丝状节点聚集' },
        ]}
      />
      <BrushRow
        title="Bottom 1% 低密度 → IGM 空洞"
        accentClass="accent-low"
        histSrc="/figures/task4_hist_brush_bottom1.png"
        spatialSrc="/figures/task4_brush_bottom1.png"
        spatialNote="低密度尾区在投影上几乎不可见——对应宇宙网之间的空洞背景。"
        stats={[
          { label: '密度阈值', value: `ρ ≤ p01 (${s.p01.toFixed(2)})` },
          { label: '体积占比', value: `${(s.tailMassBelowP01 * 100).toFixed(2)}%` },
          { label: '质量占比', value: `${m.massBelowPct.toFixed(1)}%` },
          { label: '空间特征', value: '弥散空洞背景' },
        ]}
      />
    </div>
  );
}
