import { useEffect, useMemo } from 'react';
import { StarfieldBackground } from '@/components/StarfieldBackground';
import { VideoDashboardLayout } from '@/dashboard/VideoDashboardLayout';
import { VideoDashboardHeader } from '@/dashboard/VideoDashboardHeader';
import { useDashboardInteraction } from '@/dashboard/useDashboardInteraction';
import { useAppStore } from '@/store/useAppStore';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import type { TimelineData } from '@/data/types';

const VIDEO_HIST_OVERLAY: ChartSizeOptions = {
  minHeight: 128,
  maxHeight: 158,
  aspect: 2.2,
  fillContainer: true,
};

const VIDEO_HISTOGRAM_SIZE: ChartSizeOptions = {
  minHeight: 100,
  maxHeight: 165,
  aspect: 1.65,
  fillContainer: true,
};

function isRecordMode(): boolean {
  const q = new URLSearchParams(window.location.search);
  return q.get('record') === '1' || q.get('rec') === '1';
}

export interface VideoDashboardProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  loading: boolean;
  error: string | null;
}

export function VideoDashboard({
  timeline,
  densityData,
  loading,
  error,
}: VideoDashboardProps) {
  const setTimestep = useAppStore((s) => s.setTimestep);
  const recordMode = useMemo(() => isRecordMode(), []);

  useEffect(() => {
    setTimestep(99);
  }, [setTimestep]);

  const ix = useDashboardInteraction(timeline, densityData, loading, {
    defaultHighQuality: true,
  });

  const {
    timestep,
    sliderStep,
    sliderDragging,
    setSliderStep,
    setSliderDragging,
    volumeReady,
    setVolumeReady,
    brushRange,
    tfParams,
    stats,
    dataMin,
    dataMax,
    volumeQuality,
    highlight,
    applyTop1,
    applyBottom1,
    applyFilament,
    clearBrush,
    commitTimestep,
    selectTimestep,
    volumeRatio,
    activePreset,
    timestepCount,
  } = ix;

  return (
    <div className={`video-dashboard${recordMode ? ' video-record-mode' : ''}`}>
      <StarfieldBackground count={160} seed={42} />
      <VideoDashboardHeader
        timestep={timestep}
        sliderStep={sliderStep}
        timestepCount={timestepCount}
        stats={stats}
        recordMode={recordMode}
        onSliderChange={setSliderStep}
        onSliderDragStart={() => setSliderDragging(true)}
        onSliderCommit={() => {
          setSliderDragging(false);
          commitTimestep();
        }}
        onSelectTimestep={selectTimestep}
      />

      {!recordMode && (
        <div className="vd-nav-links">
          <a href="/app.html">← 长卷版</a>
          <a href="/">成果页</a>
          <a href="/video.html?record=1">录屏模式</a>
          {loading && <span className="vd-badge">加载中…</span>}
          {error && <span className="vd-badge error">{error}</span>}
        </div>
      )}

      <VideoDashboardLayout
        timeline={timeline}
        densityData={densityData}
        loading={loading}
        timestep={timestep}
        stats={stats}
        dataMin={dataMin}
        dataMax={dataMax}
        tfParams={tfParams}
        volumeQuality={volumeQuality}
        volumeReady={volumeReady}
        onVolumeRendered={() => setVolumeReady(true)}
        brushRange={brushRange}
        highlightMin={highlight.highlightMin}
        highlightMax={highlight.highlightMax}
        volumeRatio={volumeRatio}
        onTop1={applyTop1}
        onBottom1={applyBottom1}
        onFilament={applyFilament}
        onClear={clearBrush}
        activePreset={activePreset}
        histOverlaySize={VIDEO_HIST_OVERLAY}
        histogramSizeOpts={VIDEO_HISTOGRAM_SIZE}
      />
    </div>
  );
}
