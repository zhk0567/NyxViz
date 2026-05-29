import { useEffect, useRef, useState } from 'react';
import type { TfParams } from './transferFunction';
import { debounce } from '@/utils/debounce';

export interface TransferFunctionControlsProps {
  params: TfParams;
  onChange: (params: TfParams) => void;
}

export function TransferFunctionControls({
  params,
  onChange,
}: TransferFunctionControlsProps) {
  const [local, setLocal] = useState<TfParams>(params);
  const commitRef = useRef(debounce((p: TfParams) => onChange(p), 120));

  useEffect(() => {
    setLocal(params);
  }, [params]);

  useEffect(() => {
    commitRef.current = debounce((p: TfParams) => onChange(p), 120);
    return () => commitRef.current.cancel();
  }, [onChange]);

  const update = (patch: Partial<TfParams>) => {
    const next = { ...local, ...patch };
    setLocal(next);
    commitRef.current(next);
  };

  const opacityScale = local.opacityScale ?? 1;
  const densityGain = local.densityGain ?? 0;
  const highlightBoost = local.highlightBoost ?? 1;

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
          onChange={(e) => update({ opacityScale: Number(e.target.value) })}
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
          onChange={(e) => update({ densityGain: Number(e.target.value) })}
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
          onChange={(e) => update({ highlightBoost: Number(e.target.value) })}
        />
      </label>
    </div>
  );
}
