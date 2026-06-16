import type { DensityStats, TimelineData } from '@/data/types';
import {
  NARRATION_LABELS,
  type KpiDisplayMode,
  type KpiItem,
} from '@/video/narrationLabels';

export function buildKpiItems(
  timeline: TimelineData,
  stats: DensityStats,
  mode: KpiDisplayMode = 'variance',
): KpiItem[] {
  const s0 = timeline.timesteps[0]!;
  const var0 = s0.std * s0.std;
  const varN = stats.std * stats.std;
  const varMult = var0 > 0 ? varN / var0 : 1;
  const tail0 = s0.tailMassAboveP99 * 100;
  const tailN = stats.tailMassAboveP99 * 100;
  const tailMult = tail0 > 1e-6 ? tailN / tail0 : 1;

  return [
    mode === 'sigma'
      ? {
          label: NARRATION_LABELS.sigma,
          value: stats.std.toFixed(4),
          badge: `+${(((stats.std - s0.std) / s0.std) * 100).toFixed(1)}% vs t=0`,
          tone: 'gold' as const,
        }
      : {
          label: '密度方差 σ²',
          value: varN.toFixed(2),
          badge: `↑${varMult.toFixed(1)}× vs 初值`,
          tone: 'gold' as const,
        },
    {
      label: NARRATION_LABELS.tailAbove,
      value: `${tailN.toFixed(2)}%`,
      badge: tailMult > 1 ? `↑${tailMult.toFixed(1)}×` : undefined,
      tone: 'orange' as const,
    },
    {
      label: NARRATION_LABELS.tailBelow,
      value: `${(stats.tailMassBelowP01 * 100).toFixed(1)}%`,
      tone: 'cyan' as const,
    },
    {
      label: NARRATION_LABELS.mean,
      value: stats.mean >= 100 || stats.mean < 0.01
        ? stats.mean.toExponential(2)
        : stats.mean.toFixed(2),
      tone: 'blue' as const,
    },
  ];
}

interface VideoKpiStripProps {
  timeline: TimelineData;
  stats: DensityStats;
  /** 旁白口径为 σ 时显示标准差（非 σ²） */
  showSigma?: boolean;
}

export function VideoKpiStrip({ timeline, stats, showSigma }: VideoKpiStripProps) {
  const items = buildKpiItems(timeline, stats, showSigma ? 'sigma' : 'variance');

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
