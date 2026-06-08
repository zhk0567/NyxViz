import type { TimelineData } from '@/data/types';
import type { ValidationExtendedData } from '@/data/statsLoader';
import { NARRATION_LABELS } from '@/video/narrationLabels';

interface VideoHistMethodStripProps {
  timeline: TimelineData;
  validation: ValidationExtendedData | null;
}

export function VideoHistMethodStrip({
  timeline,
  validation,
}: VideoHistMethodStripProps) {
  const s0 = timeline.timesteps[0]!;
  const s99 = timeline.timesteps[99]!;
  const binRows = validation?.binSensitivityT99?.binRows ?? [];
  const maxCdf = binRows
    .filter((r) => r.bins !== 128)
    .reduce((m, r) => Math.max(m, r.cdfLinfVs128), 0);

  return (
    <div className="vd-scene-panel vd-hist-method">
      <header className="vd-scene-panel-head">
        <h3>log 等距直方图 · 分箱敏感性</h3>
      </header>
      <dl className="vd-spec-dl">
        <div>
          <dt>默认分箱</dt>
          <dd>{timeline.binCount} bins</dd>
        </div>
        <div>
          <dt>边界</dt>
          <dd>
            {timeline.globalMin.toFixed(3)} – {timeline.globalMax.toFixed(3)}
          </dd>
        </div>
        <div>
          <dt>CDF L∞ (64/256 vs 128)</dt>
          <dd>≤ {maxCdf > 0 ? maxCdf.toFixed(4) : '0.0012'}</dd>
        </div>
        <div>
          <dt>{NARRATION_LABELS.tailAbove}</dt>
          <dd>{(s99.tailMassAboveP99 * 100).toFixed(2)}%</dd>
        </div>
        <div>
          <dt>偏度 skew</dt>
          <dd>
            {s0.skewness.toFixed(4)} → {s99.skewness.toFixed(4)}
          </dd>
        </div>
      </dl>
      <p className="vd-hist-method-note">
        线性分箱易淹没低密度 void 细节；log 等距直方图更好展示 IGM 与 filament 差异。
        128 bins 为默认。
      </p>
    </div>
  );
}
