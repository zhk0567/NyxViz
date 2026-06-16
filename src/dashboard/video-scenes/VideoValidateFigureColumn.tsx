import { figuresUrl } from '@/config/publicPaths';
import { ZoomableImage } from '@/components/ImageLightbox';

const VALIDATE_PANELS = [
  {
    src: figuresUrl('task4_threshold_comparison.png'),
    caption: '阈值对比',
    alt: '刷选阈值对比',
  },
  {
    src: figuresUrl('task4_custom_brush_error.png'),
    caption: '自定义 KPI 误差',
    alt: '自定义刷选 KPI 误差',
  },
  {
    src: figuresUrl('task4_brush_sample_recall.png'),
    caption: 'Top 1% 早停召回',
    alt: 'Top 1% 早停采样召回',
  },
] as const;

export function VideoValidateFigureColumn() {
  return (
    <main className="vd-panel vd-panel-center vd-panel-center--validate-figures">
      <header className="vd-panel-head">
        <h2>刷选验证摘要</h2>
      </header>
      <div className="vd-validate-figure-column">
        {VALIDATE_PANELS.map((panel) => (
          <figure key={panel.src} className="vd-validate-figure-cell">
            <div className="vd-validate-figure-body">
              <ZoomableImage src={panel.src} alt={panel.alt} loading="eager" />
            </div>
            <figcaption className="vd-validate-figure-caption">{panel.caption}</figcaption>
          </figure>
        ))}
      </div>
    </main>
  );
}
