import { cinematicLegendGradient, cosmicLegendGradient } from './transferFunction';

interface DensityColorLegendProps {
  min: number;
  max: number;
  cinematic?: boolean;
}

export function DensityColorLegend({ min, max, cinematic = true }: DensityColorLegendProps) {
  return (
    <div
      className={`density-legend${cinematic ? ' density-legend--cinematic' : ''}`}
      aria-label="密度色标"
    >
      <div
        className="density-legend-bar"
        style={{ background: cinematic ? cinematicLegendGradient() : cosmicLegendGradient() }}
      />
      <div className="density-legend-labels">
        <span>{min.toFixed(2)}</span>
        <span>气体密度 ρ</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  );
}
