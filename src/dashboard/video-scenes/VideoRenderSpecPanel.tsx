import type { RenderSpecData } from '@/data/statsLoader';
import type { TimelineData } from '@/data/types';
import { NARRATION_LABELS } from '@/video/narrationLabels';
import { ZoomableImage } from '@/components/ImageLightbox';

interface VideoRenderSpecPanelProps {
  renderSpec: RenderSpecData | null;
  timeline: TimelineData;
  /** 左栏仅保留参数表；光照示意图由右栏展示 */
  showLightingFigure?: boolean;
}

function ColorTfBar({
  stops,
}: {
  stops: RenderSpecData['colorStopsNormalized'];
}) {
  const gradient = stops
    .map((s) => {
      const [r, g, b] = s.rgb.map((c) => Math.round(c * 255));
      return `rgb(${r},${g},${b}) ${(s.t * 100).toFixed(0)}%`;
    })
    .join(', ');

  return (
    <div
      className="vd-color-tf-bar"
      style={{ background: `linear-gradient(90deg, ${gradient})` }}
      role="img"
      aria-label="cosmic 传递函数颜色映射"
    />
  );
}

export function VideoRenderSpecPanel({
  renderSpec,
  timeline,
  showLightingFigure = false,
}: VideoRenderSpecPanelProps) {
  const s99 = timeline.timesteps[99]!;
  const p01 = s99.p01;
  const p99 = s99.p99;

  if (!renderSpec) {
    return (
      <div className="vd-scene-panel vd-scene-panel--muted">
        <p>{NARRATION_LABELS.precomputeHint}</p>
      </div>
    );
  }

  const pres = renderSpec.presentation;
  const fill = renderSpec.lights.fill;
  const stops = renderSpec.opacityStopsNormalized;

  return (
    <div className="vd-scene-panel vd-render-spec">
      <header className="vd-scene-panel-head">
        <h3>cosmic 传递函数 · Phong 光照</h3>
        <p className="vd-scene-panel-sub">
          log₁₀ 域 ρ：p01 {p01.toFixed(3)} → p99 {p99.toFixed(3)}
        </p>
      </header>

      <section className="vd-spec-block">
        <h4>颜色映射</h4>
        <ColorTfBar stops={renderSpec.colorStopsNormalized} />
      </section>

      <section className="vd-spec-block">
        <h4>不透明度 α（7 控制点）</h4>
        <div className="vd-alpha-ladder">
          {stops.map(([t, alpha], i) => (
            <div key={i} className="vd-alpha-step">
              <span className="vd-alpha-t">{(t * 100).toFixed(0)}%</span>
              <div
                className="vd-alpha-bar"
                style={{ opacity: Math.max(0.15, alpha) }}
              />
              <span className="vd-alpha-val">α={alpha.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="vd-spec-block">
        <h4>Phong 光照</h4>
        <dl className="vd-spec-dl">
          <div>
            <dt>Ka</dt>
            <dd>{pres.ambient.toFixed(2)}</dd>
          </div>
          <div>
            <dt>Kd</dt>
            <dd>{pres.diffuse.toFixed(2)}</dd>
          </div>
          <div>
            <dt>Ks</dt>
            <dd>{pres.specular.toFixed(2)}</dd>
          </div>
          <div>
            <dt>sampleDistance</dt>
            <dd>{pres.sampleDistance.toFixed(2)}</dd>
          </div>
        </dl>
      </section>

      <section className="vd-spec-block">
        <h4>光源</h4>
        <dl className="vd-spec-dl">
          <div>
            <dt>主光</dt>
            <dd>
              东北上方 (+{renderSpec.lights.key.position_offset.join(', ')})
            </dd>
          </div>
          <div>
            <dt>辅光 RGB</dt>
            <dd>
              {fill.color_rgb.map((c) => c.toFixed(2)).join(' · ')} · 强度{' '}
              {fill.intensity.toFixed(1)}
            </dd>
          </div>
        </dl>
      </section>

      {showLightingFigure && (
        <figure className="vd-spec-figure vd-spec-figure--lighting">
          <ZoomableImage
            src="/figures/task1_lighting_diagram.png"
            alt="Phong 主光与辅光示意"
            loading="lazy"
          />
        </figure>
      )}
    </div>
  );
}
