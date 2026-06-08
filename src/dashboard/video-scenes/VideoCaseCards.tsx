import { computeStoryMetrics } from '@/results/storyMetrics';
import type { BrushValidationData } from '@/data/statsLoader';
import { ZoomableImage } from '@/components/ImageLightbox';

interface VideoCaseCardsProps {
  brushValidation: BrushValidationData | null;
  storyMetrics: ReturnType<typeof computeStoryMetrics>;
}

const CASE_FIGURES = {
  a: '/figures/task3_metrics_timeline.png',
  b: '/figures/task4_brush_top1.png',
  c: '/figures/task4_p88_sensitivity.png',
} as const;

export function VideoCaseCards({
  brushValidation,
  storyMetrics: m,
}: VideoCaseCardsProps) {
  const p88 = brushValidation?.p88Sweep.find((s) => s.projPercentile === 88);
  const band = p88?.densityBand ?? brushValidation?.fpFnDefault.filamentBand;

  return (
    <div className="vd-scene-panel vd-case-cards">
      <header className="vd-scene-panel-head">
        <h3>可视化价值 · 三案例</h3>
      </header>

      <article className="vd-case-card vd-case-card--row">
        <div className="vd-case-media">
          <ZoomableImage src={CASE_FIGURES.a} alt="百步 σ/p99 曲线" loading="lazy" />
        </div>
        <div className="vd-case-body">
          <span className="vd-case-id">A</span>
          <div className="vd-case-copy">
            <h4>百步曲线 vs 挑帧叙事</h4>
            <p>若无百步 σ / 分位趋势，易只看 t=0 与 t=99 挑帧叙事，遗漏中间非线性成形。</p>
          </div>
        </div>
      </article>

      <article className="vd-case-card vd-case-card--row tone-orange">
        <div className="vd-case-media">
          <ZoomableImage src={CASE_FIGURES.b} alt="Top 1% 空间投影" loading="lazy" />
        </div>
        <div className="vd-case-body">
          <span className="vd-case-id">B</span>
          <div className="vd-case-copy">
            <h4>Top 1% 质量集中</h4>
            <p>
              体积 {m.tailAbovePct.toFixed(2)}% 承载质量 {m.massAbovePct.toFixed(2)}
              %；刷选呈 filament 丝状聚集。
            </p>
          </div>
        </div>
      </article>

      <article className="vd-case-card vd-case-card--row tone-gold">
        <div className="vd-case-media">
          <ZoomableImage src={CASE_FIGURES.c} alt="P88 亮脊敏感性" loading="lazy" />
        </div>
        <div className="vd-case-body">
          <span className="vd-case-id">C</span>
          <div className="vd-case-copy">
            <h4>P88 亮脊反查</h4>
            <p>
              投影像素第 88 百分位提取亮脊，反查密度{' '}
              {band
                ? `${band[0].toFixed(2)} – ${band[1].toFixed(2)}`
                : '11.23 – 12.16'}
              ，与 Top 1% 一致。
            </p>
          </div>
        </div>
      </article>
    </div>
  );
}
