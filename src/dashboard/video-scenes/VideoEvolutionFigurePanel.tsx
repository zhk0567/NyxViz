import { ZoomableImage } from '@/components/ImageLightbox';

const EVOLUTION_PANELS = [
  {
    src: '/figures/task2_evolution_panel_0.png',
    caption: '分位跨度 p99−p01（团块化）',
    alt: '分位跨度 p99−p01 时序',
  },
  {
    src: '/figures/task2_evolution_panel_1.png',
    caption: '标准差 σ(t)',
    alt: '标准差 σ 时序',
  },
  {
    src: '/figures/task2_evolution_panel_2.png',
    caption: '高密度尾体积占比 ≥p99 (%)',
    alt: '高密度尾体积占比时序',
  },
  {
    src: '/figures/task2_evolution_panel_3.png',
    caption: '偏度 skew(t)',
    alt: '偏度 skew 时序',
  },
] as const;

export function VideoEvolutionFigurePanel() {
  return (
    <div className="vd-evolution-figures">
      <div className="vd-evolution-metrics-grid">
        {EVOLUTION_PANELS.map((panel) => (
          <figure key={panel.src} className="vd-evolution-metric">
            <div className="vd-evolution-metric-body">
              <ZoomableImage src={panel.src} alt={panel.alt} loading="eager" />
            </div>
            <figcaption className="vd-evolution-metric-caption">{panel.caption}</figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
