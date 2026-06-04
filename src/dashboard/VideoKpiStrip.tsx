import type { DensityStats, TimelineData } from '@/data/types';

interface VideoKpiStripProps {
  timeline: TimelineData;
  stats: DensityStats;
}

export function VideoKpiStrip({ timeline, stats }: VideoKpiStripProps) {
  const s0 = timeline.timesteps[0]!;
  const var0 = s0.std * s0.std;
  const varN = stats.std * stats.std;
  const varMult = var0 > 0 ? varN / var0 : 1;
  const tail0 = s0.tailMassAboveP99 * 100;
  const tailN = stats.tailMassAboveP99 * 100;
  const tailMult = tail0 > 1e-6 ? tailN / tail0 : 1;

  const items = [
    {
      label: '密度方差 σ²',
      value: varN.toFixed(2),
      badge: `↑${varMult.toFixed(1)}× vs 初值`,
      tone: 'gold' as const,
    },
    {
      label: 'Top 1% 体积占比',
      value: `${tailN.toFixed(2)}%`,
      badge: tailMult > 1 ? `↑${tailMult.toFixed(1)}×` : undefined,
      tone: 'orange' as const,
    },
    {
      label: 'Bottom 1% 体积占比',
      value: `${(stats.tailMassBelowP01 * 100).toFixed(1)}%`,
      tone: 'cyan' as const,
    },
    {
      label: '平均密度',
      value: stats.mean.toExponential(2),
      tone: 'blue' as const,
    },
  ];

  return (
    <div className="vd-kpi-strip">
      {items.map((it) => (
        <div key={it.label} className={`vd-kpi-card tone-${it.tone}`}>
          <span className="vd-kpi-label">{it.label}</span>
          <strong className="vd-kpi-value">{it.value}</strong>
          {it.badge && <span className="vd-kpi-badge">{it.badge}</span>}
        </div>
      ))}
    </div>
  );
}
