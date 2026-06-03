import type { DensityStats } from '@/data/types';

interface TimestepKpiCardsProps {
  stats: DensityStats;
}

export function TimestepKpiCards({ stats }: TimestepKpiCardsProps) {
  const span = stats.p99 - stats.p01;
  const items = [
    { label: '均值 μ', value: stats.mean.toFixed(4) },
    { label: '标准差 σ', value: stats.std.toFixed(4) },
    { label: 'p99−p01', value: span.toFixed(3) },
    { label: '≥p99 体积', value: `${(stats.tailMassAboveP99 * 100).toFixed(2)}%` },
    { label: '≤p01 体积', value: `${(stats.tailMassBelowP01 * 100).toFixed(2)}%` },
    { label: 'max', value: stats.max.toFixed(3) },
  ];

  return (
    <div className="kpi-grid">
      {items.map(({ label, value }) => (
        <div key={label} className="kpi-card">
          <span className="kpi-label">{label}</span>
          <span className="kpi-value">{value}</span>
        </div>
      ))}
    </div>
  );
}
