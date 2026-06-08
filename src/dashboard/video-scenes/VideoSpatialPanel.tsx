import type { ValidationExtendedData } from '@/data/statsLoader';
import { ZoomableImage } from '@/components/ImageLightbox';

interface VideoSpatialPanelProps {
  validation: ValidationExtendedData | null;
}

const METRIC_PANELS = [
  {
    src: '/figures/task2_spatial_panel_0.png',
    caption: "Moran's I 时序",
    alt: "Moran's I 时序",
  },
  {
    src: '/figures/task2_spatial_panel_1.png',
    caption: 'ξ(r=1) 时序',
    alt: 'ξ(r=1) 时序',
  },
  {
    src: '/figures/task2_spatial_panel_2.png',
    caption: '分形维 D',
    alt: '分形维 D 时序',
  },
  {
    src: '/figures/task2_spatial_panel_3.png',
    caption: '超额峰度 κ−3',
    alt: '超额峰度 κ−3 时序',
  },
] as const;

export function VideoSpatialPanel({ validation }: VideoSpatialPanelProps) {
  const bs = validation?.bootstrapSpatial;

  return (
    <div className="vd-spatial-scene">
      <div className="vd-spatial-figures">
        <div className="vd-spatial-metrics-grid">
          {METRIC_PANELS.map((panel) => (
            <figure key={panel.src} className="vd-spatial-metric">
              <div className="vd-spatial-metric-body">
                <ZoomableImage src={panel.src} alt={panel.alt} loading="eager" />
              </div>
              <figcaption className="vd-spatial-metric-caption">{panel.caption}</figcaption>
            </figure>
          ))}
        </div>
        <figure className="vd-spatial-wide-figure">
          <ZoomableImage
            src="/figures/task2_two_point_xi.png"
            alt="ξ(r) 剖面 + 子块 MC ±1σ"
            loading="eager"
          />
          <figcaption>ξ(r) 剖面 + 子块 MC ±1σ</figcaption>
        </figure>
      </div>

      <aside className="vd-scene-panel vd-spatial-stats">
        <header className="vd-scene-panel-head">
          <h3>空间统计辅证</h3>
          <p className="vd-scene-panel-sub">
            Moran I {bs ? `${bs.moransIGlobal.t0.toFixed(4)}→${bs.moransIGlobal.t99.toFixed(4)}` : '—'}
            ；ξ(r=1){' '}
            {bs ? `${bs.xiR1Global.t0.toFixed(3)}→${bs.xiR1Global.t99.toFixed(3)}` : '—'}
            ；增量未达 2σ 显著
          </p>
        </header>

        {bs ? (
          <dl className="vd-spatial-dl">
            <div>
              <dt>Moran&apos;s I</dt>
              <dd>
                {bs.moransIGlobal.t0.toFixed(4)} → {bs.moransIGlobal.t99.toFixed(4)}
                <span className="vd-spatial-delta">
                  Δ{bs.moransIGlobal.delta.toFixed(4)}
                </span>
              </dd>
            </div>
            <div>
              <dt>ξ(r=1)</dt>
              <dd>
                {bs.xiR1Global.t0.toFixed(3)} → {bs.xiR1Global.t99.toFixed(3)}
                <span className="vd-spatial-delta">
                  Δ{bs.xiR1Global.delta.toFixed(3)}
                </span>
              </dd>
            </div>
            <div>
              <dt>bootstrap σ (Moran)</dt>
              <dd>≈ {bs.pooledBootstrapStdMoran.toFixed(3)}</dd>
            </div>
            <div>
              <dt>bootstrap σ (ξ)</dt>
              <dd>≈ {bs.pooledBootstrapStdXiR1.toFixed(3)}</dd>
            </div>
            <div className="vd-spatial-flag">
              <dt>2σ 显著？</dt>
              <dd>
                Moran {bs.moransISignificantAt2Sigma ? '是' : '否'} · ξ{' '}
                {bs.xiR1SignificantAt2Sigma ? '是' : '否'}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="vd-scene-panel--muted">空间统计数据未加载</p>
        )}

        <figure className="vd-spatial-boot-figure">
          <ZoomableImage
            src="/figures/task2_bootstrap_ci.png"
            alt="Moran I 与 ξ bootstrap CI"
            loading="eager"
          />
          <figcaption>bootstrap 置信区间</figcaption>
        </figure>
      </aside>
    </div>
  );
}
