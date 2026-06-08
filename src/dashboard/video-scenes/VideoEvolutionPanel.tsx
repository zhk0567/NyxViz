import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

interface VideoEvolutionPanelProps {
  timeline: TimelineData;
}

export function VideoEvolutionPanel({ timeline }: VideoEvolutionPanelProps) {
  const m = computeStoryMetrics(timeline);
  const p999Mult = m.s0.p999 > 0 ? m.s99.p999 / m.s0.p999 : 1;

  const rows = [
    {
      label: '线性密度 σ',
      from: m.s0.std.toFixed(4),
      to: m.s99.std.toFixed(4),
      delta: `+${m.sigmaPct.toFixed(1)}%`,
      tone: 'cyan' as const,
    },
    {
      label: 'p99−p01 分位跨度',
      from: m.span0.toFixed(3),
      to: m.span99.toFixed(3),
      delta: `+${m.spanPct.toFixed(1)}%`,
      tone: 'violet' as const,
    },
    {
      label: 'p99.9 相对 t=0',
      from: m.s0.p999.toFixed(3),
      to: m.s99.p999.toFixed(3),
      delta: `×${p999Mult.toFixed(3)}`,
      tone: 'gold' as const,
    },
  ];

  return (
    <div className="vd-scene-panel vd-evolution-panel">
      <header className="vd-scene-panel-head">
        <h3>演化量化 · 团块化与两极化</h3>
      </header>
      <div className="vd-evolution-grid">
        {rows.map((r) => (
          <div key={r.label} className={`vd-evolution-card tone-${r.tone}`}>
            <span className="vd-evolution-label">{r.label}</span>
            <div className="vd-evolution-values">
              <span>{r.from}</span>
              <span className="vd-evolution-arrow">→</span>
              <strong>{r.to}</strong>
            </div>
            <span className="vd-evolution-delta">{r.delta}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
