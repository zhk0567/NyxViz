import { computeStoryMetrics } from '@/results/storyMetrics';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import { PosterTrendChart } from '@/dashboard/PosterTrendChart';
import { VideoKpiStrip } from '@/dashboard/VideoKpiStrip';
import { VideoRenderSpecPanel } from '@/dashboard/video-scenes/VideoRenderSpecPanel';
import { VideoEvolutionPanel } from '@/dashboard/video-scenes/VideoEvolutionPanel';
import { VideoCaseCards } from '@/dashboard/video-scenes/VideoCaseCards';
import { VideoHistMethodStrip } from '@/dashboard/video-scenes/VideoHistMethodStrip';
import { computeTailBadge, VIDEO_MINI_TREND } from '@/dashboard/video-scenes/layout/shared';
import { NARRATION_LABELS } from '@/video/narrationLabels';
import { getSceneMeta } from '@/video/sceneRegistry';
import type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

export function VideoLeftColumn({
  sceneId,
  videoStats,
  timeline,
  stats,
  histOverlaySize,
}: Pick<
  VideoSceneLayoutProps,
  'sceneId' | 'videoStats' | 'timeline' | 'stats' | 'histOverlaySize'
>) {
  const m = computeStoryMetrics(timeline);
  const tailBadge = computeTailBadge(timeline);
  const content = getSceneMeta(sceneId).content;

  return (
    <aside className="vd-panel vd-panel-left">
      {sceneId === 'task1-tf' && (
        <VideoRenderSpecPanel renderSpec={videoStats.renderSpec} timeline={timeline} />
      )}

      {sceneId === 'task2-evolution' && (
        <>
          <header className="vd-panel-head">
            <h2>时序密度分布演化</h2>
          </header>
          <div className="vd-panel-hist vd-panel-hist--tall">
            <HistogramOverlay timeline={timeline} sizeOpts={histOverlaySize} />
          </div>
          <VideoEvolutionPanel timeline={timeline} />
          {stats && <VideoKpiStrip timeline={timeline} stats={stats} showSigma />}
          <div className="vd-mini-trends">
            <PosterTrendChart
              timeline={timeline}
              title="σ(t)"
              badge={`+${m.sigmaPct.toFixed(1)}%`}
              color="#00d4ff"
              fill="rgba(0, 212, 255, 0.12)"
              metric="std"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
            <PosterTrendChart
              timeline={timeline}
              title={NARRATION_LABELS.tailAbove}
              badge={tailBadge}
              color="#ff9500"
              fill="rgba(255, 149, 0, 0.12)"
              metric="tailPct"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
            <PosterTrendChart
              timeline={timeline}
              title={NARRATION_LABELS.span}
              badge={`+${m.spanPct.toFixed(1)}%`}
              color="#9b8cf8"
              fill="rgba(155, 140, 248, 0.12)"
              metric="span"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
          </div>
        </>
      )}

      {sceneId === 'task2-cases' && (
        <VideoCaseCards
          brushValidation={videoStats.brushValidation}
          storyMetrics={m}
        />
      )}

      {sceneId === 'task3-hist' && (
        <>
          <header className="vd-panel-head">
            <h2>时序密度分布演化</h2>
          </header>
          <div className="vd-panel-hist vd-panel-hist--tall">
            <HistogramOverlay timeline={timeline} sizeOpts={histOverlaySize} />
          </div>
          <VideoHistMethodStrip
            timeline={timeline}
            validation={videoStats.validationExtended}
          />
        </>
      )}

      {(sceneId === 'intro' ||
        (sceneId !== 'task1-tf' &&
          sceneId !== 'task2-evolution' &&
          sceneId !== 'task2-cases' &&
          sceneId !== 'task3-hist')) && (
        <>
          <header className="vd-panel-head">
            <h2>时序密度分布演化</h2>
            {content.headline && (
              <p className="vd-panel-sub">{content.headline}</p>
            )}
          </header>
          <div className="vd-panel-hist">
            <HistogramOverlay timeline={timeline} sizeOpts={histOverlaySize} />
          </div>
          {stats && (
            <VideoKpiStrip
              timeline={timeline}
              stats={stats}
              showSigma={content.kpiMode === 'sigma'}
            />
          )}
          <div className="vd-mini-trends">
            <PosterTrendChart
              timeline={timeline}
              title="σ(t)"
              badge={`+${m.sigmaPct.toFixed(1)}%`}
              color="#00d4ff"
              fill="rgba(0, 212, 255, 0.12)"
              metric="std"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
            <PosterTrendChart
              timeline={timeline}
              title={NARRATION_LABELS.tailAbove}
              badge={tailBadge}
              color="#ff9500"
              fill="rgba(255, 149, 0, 0.12)"
              metric="tailPct"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
            <PosterTrendChart
              timeline={timeline}
              title={NARRATION_LABELS.span}
              badge={`+${m.spanPct.toFixed(1)}%`}
              color="#9b8cf8"
              fill="rgba(155, 140, 248, 0.12)"
              metric="span"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
          </div>
        </>
      )}
    </aside>
  );
}
