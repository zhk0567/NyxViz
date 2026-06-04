import { PosterTrendChart } from '@/dashboard/PosterTrendChart';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

const POSTER_HIST_OVERLAY: ChartSizeOptions = {
  minHeight: 360,
  maxHeight: 420,
  aspect: 2.15,
};

function KpiStrip({ timeline }: { timeline: TimelineData }) {
  const s = timeline.timesteps[99]!;
  const items = [
    { label: '均值 μ', value: s.mean.toFixed(3) },
    { label: '标准差 σ', value: s.std.toFixed(4) },
    { label: 'p99', value: s.p99.toFixed(3) },
    { label: '≥p99 体积', value: `${(s.tailMassAboveP99 * 100).toFixed(2)}%` },
  ];
  return (
    <div className="pl-kpi-strip" aria-label="t=99 指标">
      {items.map((it) => (
        <div key={it.label} className="pl-kpi-card">
          <span className="pl-kpi-label">{it.label}</span>
          <span className="pl-kpi-value">{it.value}</span>
        </div>
      ))}
    </div>
  );
}

export function PosterStatsSection({ timeline }: { timeline: TimelineData }) {
  const m = computeStoryMetrics(timeline);
  const sigmaBadge = `+${m.sigmaPct.toFixed(1)}%`;
  const spanBadge = `+${m.spanPct.toFixed(1)}%`;
  const tail0 = m.s0.tailMassAboveP99 * 100;
  const tail99 = m.tailAbovePct;
  const tailBadge =
    tail0 > 1e-6 ? `+${(((tail99 - tail0) / tail0) * 100).toFixed(1)}%` : '—';

  return (
    <div className="pl-s03-body">
      <figure className="pl-s03-hist-figure">
        <figcaption>多时刻 log 直方图叠加（t=0, 25, 50, 75, 99）</figcaption>
        <HistogramOverlay timeline={timeline} sizeOpts={POSTER_HIST_OVERLAY} />
      </figure>

      <div className="pl-s03-trends">
        <PosterTrendChart
          timeline={timeline}
          title="σ(t)"
          badge={`t=0→99  ${sigmaBadge}`}
          color="#4ec4ff"
          fill="rgba(78, 196, 255, 0.15)"
          metric="std"
        />
        <PosterTrendChart
          timeline={timeline}
          title="p99 − p01"
          badge={`t=0→99  ${spanBadge}`}
          color="#9eefff"
          fill="rgba(158, 239, 255, 0.12)"
          metric="span"
        />
        <PosterTrendChart
          timeline={timeline}
          title="≥p99 体积占比"
          badge={`t=0→99  ${tailBadge}`}
          color="#ffcc66"
          fill="rgba(255, 204, 102, 0.12)"
          metric="tailPct"
        />
      </div>

      <KpiStrip timeline={timeline} />
    </div>
  );
}
