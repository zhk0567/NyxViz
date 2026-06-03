import { cosmicLegendGradient } from '@/volume/transferFunction';

interface VerticalColorLegendProps {
  min: number;
  max: number;
}

export function VerticalColorLegend({ min, max }: VerticalColorLegendProps) {
  const logMin = Math.log10(Math.max(min, 1e-6));
  const logMax = Math.log10(Math.max(max, 1e-6));
  const ticks = [logMax, (logMax + logMin) / 2, logMin];

  return (
    <div className="vertical-legend" aria-label="密度色标">
      <span className="vertical-legend-caption">密度</span>
      <span className="vertical-legend-unit">log₁₀ ρ</span>
      <div className="vertical-legend-wrap">
        <div
          className="vertical-legend-bar"
          style={{
            background: cosmicLegendGradient().replace('90deg', '0deg'),
          }}
        />
        <div className="vertical-legend-ticks">
          {ticks.map((t) => (
            <span key={t}>{t.toFixed(0)}</span>
          ))}
        </div>
      </div>
      <span className="vertical-legend-note">Nyx 全局 p01–p99</span>
    </div>
  );
}
