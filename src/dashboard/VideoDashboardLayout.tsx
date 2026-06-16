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
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

const VIDEO_MINI_TREND: ChartSizeOptions = {
  minHeight: 78,
  maxHeight: 78,
  aspect: 1.35,
  fillContainer: false,
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
  const tailSeries = timeline.timesteps.map((s) => s.tailMassAboveP99 * 100);
  const tail0 = tailSeries[0]!;
  const tailPeak = Math.max(...tailSeries);
  const tailRel = tail0 > 1e-6 ? ((tailPeak - tail0) / tail0) * 100 : 0;
  const tailBadge =
    tailRel >= 0.0005 ? `+${tailRel.toFixed(tailRel < 0.1 ? 3 : 1)}%` : '≈0%';

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
          {stats && <VideoKpiStrip timeline={timeline} stats={stats} />}
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
              title="Top 1% Δ"
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
        </aside>

        <main className="vd-panel vd-panel-center">
          <div className="vd-vtk-frame">
            <div className="vd-vtk-canvas-wrap">
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
                    cameraZoom={VIDEO_CAMERA_ZOOM}
                    highlightMin={highlightMin}
                    highlightMax={highlightMax}
                    onRendered={onVolumeRendered}
                    visualStyle="cinematic"
                    className="vd-vtk-panel"
                  />
                </Suspense>
              ) : (
                <VtkFallback />
              )}
            </div>
            <DensityColorLegend min={dataMin} max={dataMax} />
          </div>
        </main>

        <aside className="vd-panel vd-panel-right">
          <header className="vd-panel-head">
            <h2>相空间刷选与空间验证</h2>
          </header>
          <div className="vd-panel-brush-hist">
            <DensityHistogram timeline={timeline} sizeOpts={histogramSizeOpts} />
          </div>
          <p className="vd-brush-hist-hint" aria-hidden>
            <span className="vd-brush-hist-arrow">↓</span>
            刷选密度区间 · 下方空间投影对应验证
          </p>
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

      <div className="vd-bottom">
        <VideoFindingsStrip timeline={timeline} />
        <div className="vd-letterbox" aria-hidden />
      </div>
    </>
  );
}
