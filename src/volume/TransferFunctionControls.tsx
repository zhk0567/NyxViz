import type { TfParams } from './transferFunction';

export interface TransferFunctionControlsProps {
  params: TfParams;
  onChange: (params: TfParams) => void;
}

export function TransferFunctionControls({
  params,
  onChange,
}: TransferFunctionControlsProps) {
  const opacityScale = params.opacityScale ?? 1;
  const densityGain = params.densityGain ?? 0;
  const highlightBoost = params.highlightBoost ?? 1;

  return (
    <div className="tf-controls">
      <label>
        整体透明度 {opacityScale.toFixed(2)}
        <input
          type="range"
          min={0.3}
          max={2}
          step={0.05}
          value={opacityScale}
          onChange={(e) =>
            onChange({ ...params, opacityScale: Number(e.target.value) })
          }
        />
      </label>
      <label>
        高密度阈值 {densityGain.toFixed(2)}
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={densityGain}
          onChange={(e) =>
            onChange({ ...params, densityGain: Number(e.target.value) })
          }
        />
      </label>
      <label>
        刷选高亮 {highlightBoost.toFixed(2)}
        <input
          type="range"
          min={0.5}
          max={2}
          step={0.05}
          value={highlightBoost}
          onChange={(e) =>
            onChange({ ...params, highlightBoost: Number(e.target.value) })
          }
        />
      </label>
    </div>
  );
}
