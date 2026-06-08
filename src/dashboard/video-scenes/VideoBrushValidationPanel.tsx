import type { BrushValidationData } from '@/data/statsLoader';
import { NARRATION_LABELS } from '@/video/narrationLabels';

interface VideoBrushValidationPanelProps {
  brushValidation: BrushValidationData | null;
}

export function VideoBrushValidationPanel({
  brushValidation,
}: VideoBrushValidationPanelProps) {
  if (!brushValidation) {
    return (
      <div className="vd-scene-panel vd-scene-panel--muted">
        <p>{NARRATION_LABELS.precomputeHint}</p>
      </div>
    );
  }

  const { fpFnDefault, benchmark } = brushValidation;
  const top1Sample = benchmark.sampleRecall.recallVsTrue * 100;
  const p25p75 = benchmark.customBrushErrors.find((e) =>
    e.label.includes('p25'),
  );

  return (
    <div className="vd-scene-panel vd-brush-validate">
      <header className="vd-scene-panel-head vd-brush-validate-head">
        <h3>离线验证 · 早停采样 KPI</h3>
      </header>

      <div className="vd-validate-grid">
        <div className="vd-validate-card">
          <span className="vd-validate-label">离线召回</span>
          <strong>{(fpFnDefault.recall * 100).toFixed(1)}%</strong>
        </div>
        <div className="vd-validate-card tone-orange">
          <span className="vd-validate-label">精确率</span>
          <strong>{(fpFnDefault.precision * 100).toFixed(1)}%</strong>
        </div>
        <div className="vd-validate-card tone-cyan">
          <span className="vd-validate-label">Top1% Worker</span>
          <strong>{benchmark.top1_earlyExit.elapsedMs.toFixed(0)} ms</strong>
          <span className="vd-validate-sub">
            全量 {benchmark.top1_fullCount.elapsedMs.toFixed(0)} ms
          </span>
        </div>
        <div className="vd-validate-card">
          <span className="vd-validate-label">Top1% 早停体素覆盖</span>
          <strong>{top1Sample.toFixed(1)}%</strong>
        </div>
        {p25p75 && (
          <div className="vd-validate-card tone-violet">
            <span className="vd-validate-label">p25–p75 早停覆盖</span>
            <strong>{p25p75.recallVsTruePct.toFixed(2)}%</strong>
          </div>
        )}
      </div>
    </div>
  );
}
