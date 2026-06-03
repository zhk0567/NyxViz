import type { TimelineData } from '@/data/types';
import type { StoryMetrics } from '@/results/storyMetrics';

interface SparklineTripletProps {
  timeline: TimelineData;
  metrics: StoryMetrics;
}

function Sparkline({
  label,
  values,
  color,
  badge,
}: {
  label: string;
  values: number[];
  color: string;
  badge: string;
}) {
  const w = 200;
  const h = 56;
  const pad = 4;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = pad + (i / (values.length - 1)) * (w - pad * 2);
      const y = h - pad - ((v - min) / range) * (h - pad * 2);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="spark-card">
      <div className="spark-head">
        <span className="spark-label">{label}</span>
        <span className="spark-badge">{badge}</span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="spark-svg" aria-hidden>
        <polyline points={pts} fill="none" stroke={color} strokeWidth="2" />
      </svg>
    </div>
  );
}

export function SparklineTriplet({ timeline, metrics }: SparklineTripletProps) {
  const steps = timeline.timesteps;
  const std = steps.map((s) => s.std);
  const tailAbove = steps.map((s) => s.tailMassAboveP99 * 100);
  const tailBelow = steps.map((s) => s.tailMassBelowP01 * 100);

  const tailAboveRatio =
    tailAbove[0]! > 0
      ? `+${(((tailAbove[99]! - tailAbove[0]!) / tailAbove[0]!) * 100).toFixed(0)}%`
      : '—';
  const tailBelowRatio =
    tailBelow[0]! > 0
      ? `+${(((tailBelow[99]! - tailBelow[0]!) / tailBelow[0]!) * 100).toFixed(0)}%`
      : '—';

  return (
    <div className="spark-triplet">
      <Sparkline
        label="标准差 σ"
        values={std}
        color="#3dd6c6"
        badge={`+${metrics.sigmaPct.toFixed(1)}%`}
      />
      <Sparkline
        label="≥p99 体积占比"
        values={tailAbove}
        color="#f5a623"
        badge={tailAboveRatio}
      />
      <Sparkline
        label="≤p01 体积占比"
        values={tailBelow}
        color="#58a6ff"
        badge={tailBelowRatio}
      />
    </div>
  );
}
