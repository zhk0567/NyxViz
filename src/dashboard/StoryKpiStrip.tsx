import type { TimelineData } from '@/data/types';

interface StoryKpiStripProps {
  stats: TimelineData['timesteps'][0];
}

export function StoryKpiStrip({ stats }: StoryKpiStripProps) {
  const items = [
    { label: '标准差 σ', value: stats.std.toFixed(4), tone: 'cyan' },
    { label: '≥p99 体积', value: `${(stats.tailMassAboveP99 * 100).toFixed(2)}%`, tone: 'gold' },
    { label: '≤p01 体积', value: `${(stats.tailMassBelowP01 * 100).toFixed(2)}%`, tone: 'blue' },
    { label: '均值 μ', value: stats.mean.toFixed(3), tone: 'purple' },
  ];

  return (
    <div className="story-kpi-strip" aria-label={`t=${stats.timestep} 关键指标`}>
      {items.map((it) => (
        <div key={it.label} className={`story-kpi story-kpi-${it.tone}`}>
          <span className="story-kpi-label">{it.label}</span>
          <span className="story-kpi-value">{it.value}</span>
        </div>
      ))}
    </div>
  );
}
