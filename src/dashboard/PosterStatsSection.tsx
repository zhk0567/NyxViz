import { PosterTrendChart } from '@/dashboard/PosterTrendChart';
import { VideoKpiStrip } from '@/dashboard/VideoKpiStrip';
import { VideoHistMethodStrip } from '@/dashboard/video-scenes/VideoHistMethodStrip';
import { computeTailBadge } from '@/dashboard/video-scenes/layout/shared';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';
import type { ValidationExtendedData } from '@/data/statsLoader';

const POSTER_HIST_OVERLAY: ChartSizeOptions = {
  minHeight: 360,
  maxHeight: 420,
  aspect: 2.15,
};

interface PosterStatsSectionProps {
  timeline: TimelineData;
  validationExtended?: ValidationExtendedData | null;
}

export function PosterStatsSection({
  timeline,
  validationExtended = null,
}: PosterStatsSectionProps) {
  const m = computeStoryMetrics(timeline);
  const s99 = timeline.timesteps[99]!;
  const sigmaBadge = `+${m.sigmaPct.toFixed(1)}%`;
  const spanBadge = `+${m.spanPct.toFixed(1)}%`;
  const tailBadge = computeTailBadge(timeline);

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

      <VideoKpiStrip timeline={timeline} stats={s99} showSigma />

      <VideoHistMethodStrip timeline={timeline} validation={validationExtended} />
    </div>
  );
}
