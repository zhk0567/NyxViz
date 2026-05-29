import { cosmicLegendGradient } from './transferFunction';

interface DensityColorLegendProps {
  min: number;
  max: number;
}

export function DensityColorLegend({ min, max }: DensityColorLegendProps) {
  return (
    <div className="density-legend" aria-label="密度色标">
      <div
        className="density-legend-bar"
        style={{ background: cosmicLegendGradient() }}
      />
      <div className="density-legend-labels">
        <span>{min.toFixed(2)}</span>
        <span>气体密度 ρ</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  );
}
