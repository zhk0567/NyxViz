import { cosmicLegendGradient } from '@/volume/transferFunction';

interface HorizontalColorLegendProps {
  min: number;
  max: number;
}

export function HorizontalColorLegend({ min, max }: HorizontalColorLegendProps) {
  const logMin = Math.log10(Math.max(min, 1e-6));
  const logMax = Math.log10(Math.max(max, 1e-6));
  const mid = (logMax + logMin) / 2;

  return (
    <div className="horizontal-legend" aria-label="密度色标">
      <div className="horizontal-legend-head">
        <span className="horizontal-legend-title">密度 log₁₀ ρ</span>
        <span className="horizontal-legend-note">Nyx 全局 p01–p99</span>
      </div>
      <div
        className="horizontal-legend-bar"
        style={{ background: cosmicLegendGradient() }}
      />
      <div className="horizontal-legend-labels">
        <span>低密度 {logMin.toFixed(0)}</span>
        <span>中密度 {mid.toFixed(0)}</span>
        <span>高密度 {logMax.toFixed(0)}</span>
      </div>
    </div>
  );
}
