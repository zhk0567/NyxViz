import { lazy, Suspense } from 'react';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { PosterTrendChart } from '@/dashboard/PosterTrendChart';
import { VideoKpiStrip } from '@/dashboard/VideoKpiStrip';
import { VideoBrushPreviews } from '@/dashboard/VideoBrushPreviews';
import { VideoFindingsStrip } from '@/dashboard/VideoFindingsStrip';
import { DensityColorLegend } from '@/volume/DensityColorLegend';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';
import type { BrushRange } from '@/data/types';
import type { BrushPresetId } from '@/data/brushPreset';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import type { TfParams } from '@/volume/transferFunction';
import type { VolumeQuality } from '@/volume/VolumeScene';

const VIDEO_MINI_TREND: ChartSizeOptions = {
  minHeight: 96,
  maxHeight: 140,
  aspect: 2.4,
  fillContainer: true,
};

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);

function VtkFallback() {
  return <div className="vd-vtk-fallback">加载体渲染…</div>;
}

export interface VideoDashboardLayoutProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  loading: boolean;
  timestep: number;
  stats: TimelineData['timesteps'][0] | undefined;
  dataMin: number;
  dataMax: number;
  tfParams: TfParams;
  volumeQuality: VolumeQuality;
  volumeReady: boolean;
  onVolumeRendered: () => void;
  brushRange: BrushRange | null;
  highlightMin?: number;
  highlightMax?: number;
  volumeRatio: string | null;
  onTop1: () => void;
  onBottom1: () => void;
  onFilament: () => void;
  onClear: () => void;
  activePreset: BrushPresetId | null;
  histOverlaySize?: ChartSizeOptions;
  histogramSizeOpts?: ChartSizeOptions;
}

export function VideoDashboardLayout({
  timeline,
  densityData,
  loading,
  timestep,
  stats,
  dataMin,
  dataMax,
  tfParams,
  volumeQuality,
  volumeReady,
  onVolumeRendered,
  brushRange,
  highlightMin,
  highlightMax,
  volumeRatio,
  onTop1,
  onBottom1,
  onFilament,
  onClear,
  activePreset,
  histOverlaySize,
  histogramSizeOpts,
}: VideoDashboardLayoutProps) {
  const m = computeStoryMetrics(timeline);
  const tail0 = m.s0.tailMassAboveP99 * 100;
  const tail99 = m.tailAbovePct;
  const tailBadge =
    tail0 > 1e-6 ? `+${(((tail99 - tail0) / tail0) * 100).toFixed(1)}%` : '—';

  return (
    <>
      <div className="vd-body">
        <aside className="vd-panel vd-panel-left">
          <header className="vd-panel-head">
            <h2>时序密度分布演化</h2>
          </header>
          <div className="vd-panel-hist">
            <HistogramOverlay timeline={timeline} sizeOpts={histOverlaySize} />
          </div>
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
              title="Top 1%"
              badge={tailBadge}
              color="#ff9500"
              fill="rgba(255, 149, 0, 0.12)"
              metric="tailPct"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
            <PosterTrendChart
              timeline={timeline}
              title="p99−p01"
              badge={`+${m.spanPct.toFixed(1)}%`}
              color="#9b8cf8"
              fill="rgba(155, 140, 248, 0.12)"
              metric="span"
              sizeOpts={VIDEO_MINI_TREND}
              compact
            />
          </div>
          {stats && <VideoKpiStrip timeline={timeline} stats={stats} />}
        </aside>

        <main className="vd-panel vd-panel-center">
          <div className="vd-vtk-frame">
            <LoadingOverlay visible={loading} label={`t=${timestep}`} />
            {densityData ? (
              <Suspense fallback={<VtkFallback />}>
                <VolumeScene
                  data={densityData}
                  timestep={timestep}
                  dataMin={dataMin}
                  dataMax={dataMax}
                  tfParams={tfParams}
                  quality={volumeQuality}
                  renderActive
                  highlightMin={highlightMin}
                  highlightMax={highlightMax}
                  onRendered={onVolumeRendered}
                  className="vd-vtk-panel"
                />
              </Suspense>
            ) : (
              <VtkFallback />
            )}
          </div>
          <DensityColorLegend min={dataMin} max={dataMax} />
        </main>

        <aside className="vd-panel vd-panel-right">
          <header className="vd-panel-head">
            <h2>相空间刷选与空间验证</h2>
          </header>
          <div className="vd-panel-brush-hist">
            <DensityHistogram timeline={timeline} sizeOpts={histogramSizeOpts} />
          </div>
          {stats && (
            <VideoBrushPreviews
              stats={stats}
              densityData={densityData}
              volumeReady={volumeReady}
              loading={loading}
              dataMin={dataMin}
              dataMax={dataMax}
              activePreset={activePreset}
              onTop1={onTop1}
              onFilament={onFilament}
              onBottom1={onBottom1}
            />
          )}
          <div className="vd-brush-controls">
            <div className="vd-brush-presets">
              <button
                type="button"
                className={`vd-preset top${activePreset === 'top' ? ' on' : ''}`}
                onClick={onTop1}
              >
                Top 1%
              </button>
              <button
                type="button"
                className={`vd-preset fil${activePreset === 'filament' ? ' on' : ''}`}
                onClick={onFilament}
              >
                90–99%
              </button>
              <button
                type="button"
                className={`vd-preset bot${activePreset === 'bottom' ? ' on' : ''}`}
                onClick={onBottom1}
              >
                Bottom 1%
              </button>
              <button type="button" className="vd-preset clear" onClick={onClear}>
                清除
              </button>
            </div>
            {brushRange && (
              <p className="vd-brush-readout">
                ρ∈[{brushRange.min.toFixed(2)}, {brushRange.max.toFixed(2)}]
                {volumeRatio != null && ` · 选中 ${volumeRatio}% 体积`}
              </p>
            )}
          </div>
        </aside>
      </div>

      <VideoFindingsStrip timeline={timeline} />

      <footer className="vd-footer">
        <p>
          从近乎均匀的微小涨落，到由引力塑造的宇宙网 —— 这就是结构的诞生。
        </p>
      </footer>
    </>
  );
}
