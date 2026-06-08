import type { ValidationExtendedData } from '@/data/statsLoader';
import { NARRATION_LABELS } from '@/video/narrationLabels';

interface VideoVoidPanelProps {
  validation: ValidationExtendedData | null;
}

export function VideoVoidPanel({ validation }: VideoVoidPanelProps) {
  if (!validation?.voidFractions) {
    return (
      <div className="vd-scene-panel vd-scene-panel--muted">
        <p>{NARRATION_LABELS.precomputeHint}</p>
      </div>
    );
  }

  const { t0, t99 } = validation.voidFractions;

  return (
    <div className="vd-scene-panel vd-void-panel">
      <header className="vd-scene-panel-head">
        <h3>void 占比 · 统计阈值口径</h3>
        <p className="vd-scene-panel-sub">
          子体积无全宇宙平均密度标定，改用 t=0 分位阈值 · p10：10.00%→
          {t99.belowT0P10.toFixed(2)}% · p01：1.00%→{t99.belowT0P01.toFixed(2)}%
        </p>
      </header>

      <div className="vd-void-grid">
        <article className="vd-void-card">
          <h4>阈值：t=0 的 p10</h4>
          <div className="vd-void-values">
            <div>
              <span className="vd-void-label">t=0</span>
              <strong>{t0.belowT0P10.toFixed(2)}%</strong>
            </div>
            <span className="vd-void-arrow">→</span>
            <div>
              <span className="vd-void-label">t=99</span>
              <strong>{t99.belowT0P10.toFixed(2)}%</strong>
            </div>
          </div>
          <p className="vd-void-note">初始占比 ≈ 10.00%</p>
        </article>

        <article className="vd-void-card tone-cyan">
          <h4>阈值：t=0 的 p01</h4>
          <div className="vd-void-values">
            <div>
              <span className="vd-void-label">t=0</span>
              <strong>{t0.belowT0P01.toFixed(2)}%</strong>
            </div>
            <span className="vd-void-arrow">→</span>
            <div>
              <span className="vd-void-label">t=99</span>
              <strong>{t99.belowT0P01.toFixed(2)}%</strong>
            </div>
          </div>
          <p className="vd-void-note">低密度尾扩张更明显</p>
        </article>
      </div>
    </div>
  );
}
