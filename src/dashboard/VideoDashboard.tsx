import { useEffect, useMemo, useRef, useState } from 'react';
import { VideoSceneLayout } from '@/dashboard/VideoSceneLayout';
import { VideoDashboardHeader } from '@/dashboard/VideoDashboardHeader';
import { VideoSceneChrome } from '@/dashboard/video-scenes/VideoSceneChrome';
import { VideoSceneNav } from '@/dashboard/video-scenes/VideoSceneNav';
import { useDashboardInteraction } from '@/dashboard/useDashboardInteraction';
import { useVideoScene } from '@/video/useVideoScene';
import { sceneLayoutStyle } from '@/video/sceneRegistry';
import { loadTimestep } from '@/data/nyxLoader';
import { getVtkScalarsAsync } from '@/data/vtkConvert';
import type { VideoStatsBundle } from '@/data/statsLoader';
import type { TimelineData } from '@/data/types';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import { CosmicBackdrop } from '@/components/CosmicBackdrop';
import { useAppStore } from '@/store/useAppStore';

const VIDEO_HIST_OVERLAY: ChartSizeOptions = {
  minHeight: 118,
  maxHeight: 520,
  aspect: 2.0,
  fillContainer: true,
};

const VIDEO_HISTOGRAM_SIZE: ChartSizeOptions = {
  minHeight: 132,
  maxHeight: 480,
  aspect: 1.65,
  fillContainer: true,
};

const VIDEO_RECORD_HIST_OVERLAY: ChartSizeOptions = {
  minHeight: 150,
  maxHeight: 220,
  aspect: 2.0,
  fillContainer: true,
  videoReadable: true,
};

const VIDEO_RECORD_HISTOGRAM_SIZE: ChartSizeOptions = {
  minHeight: 168,
  maxHeight: 240,
  aspect: 1.65,
  fillContainer: true,
  videoReadable: true,
};

export interface VideoDashboardProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  loading: boolean;
  error: string | null;
  videoStats: VideoStatsBundle;
}

export function VideoDashboard({
  timeline,
  densityData,
  loading,
  error,
  videoStats,
}: VideoDashboardProps) {
  const { sceneId, sceneMeta, setScene, recordMode } = useVideoScene();
  const setTimestep = useAppStore((s) => s.setTimestep);
  const sceneBrushApplied = useRef(false);
  const [volumeEverMounted, setVolumeEverMounted] = useState(false);
  const warmedTimesteps = useRef(new Set<number>());

  const keepVolumeAlive = !recordMode;

  const recordReadable = recordMode && sceneId !== 'intro';

  const layoutStyle = useMemo(
    () => sceneLayoutStyle(sceneMeta, recordMode),
    [sceneMeta, recordMode],
  );

  const histOverlaySize = useMemo(
    () => (recordReadable ? VIDEO_RECORD_HIST_OVERLAY : VIDEO_HIST_OVERLAY),
    [recordReadable],
  );

  const histogramSizeOpts = useMemo(
    () => (recordReadable ? VIDEO_RECORD_HISTOGRAM_SIZE : VIDEO_HISTOGRAM_SIZE),
    [recordReadable],
  );

  const ix = useDashboardInteraction(timeline, densityData, loading, {
    defaultHighQuality: true,
    progressiveQuality: true,
    keepVolumeAlive,
  });

  const {
    timestep,
    sliderStep,
    sliderDragging,
    setSliderStep,
    setSliderDragging,
    volumeReady,
    onVolumeRendered,
    brushRange,
    tfParams,
    stats,
    dataMin,
    dataMax,
    volumeQuality,
    qualityPhase,
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

  useEffect(() => {
    setTimestep(sceneMeta.defaultTimestep);
    setSliderStep(sceneMeta.defaultTimestep);
    sceneBrushApplied.current = false;
  }, [sceneMeta.defaultTimestep, sceneMeta.id, setTimestep, setSliderStep]);

  useEffect(() => {
    const t = sceneMeta.defaultTimestep;
    if (warmedTimesteps.current.has(t)) return;
    warmedTimesteps.current.add(t);
    void loadTimestep(t).then((data) => {
      void getVtkScalarsAsync(t, data);
    });
  }, [sceneMeta.defaultTimestep]);

  useEffect(() => {
    if (!stats || sceneBrushApplied.current) return;
    sceneBrushApplied.current = true;
    if (sceneMeta.brushPreset === 'top') applyTop1();
    else if (sceneMeta.brushPreset === 'bottom') applyBottom1();
    else if (sceneMeta.brushPreset === 'filament') applyFilament();
    else clearBrush();
  }, [
    stats,
    sceneMeta.brushPreset,
    applyTop1,
    applyBottom1,
    applyFilament,
    clearBrush,
  ]);

  return (
    <div
      className={`video-dashboard cosmic-page-frame video-scene-${sceneId}${recordMode ? ' video-record-mode' : ''}`}
      data-scene={sceneId}
      style={layoutStyle}
    >
      <CosmicBackdrop
        variant="video"
        intensity={recordMode ? 'subtle' : 'full'}
      />
      <VideoSceneChrome title={sceneMeta.title} recordMode={recordMode} />

      {sceneMeta.showFindings === false || sceneId !== 'findings' ? (
        <VideoDashboardHeader
          timestep={timestep}
          sliderStep={sliderStep}
          timestepCount={timestepCount}
          stats={stats}
          recordMode={recordMode}
          sceneId={sceneId}
          onSliderChange={setSliderStep}
          onSliderDragStart={() => setSliderDragging(true)}
          onSliderCommit={() => {
            setSliderDragging(false);
            commitTimestep();
          }}
          onSelectTimestep={selectTimestep}
        />
      ) : (
        <header className="vd-header vd-header--findings">
          <div className="vd-header-center">
            <h1 className="vd-title">综合发现</h1>
            <p className="vd-subtitle">统计—空间闭环 · NyxViz</p>
          </div>
        </header>
      )}

      {!recordMode && (
        <div className="vd-preview-bar">
          <div className="vd-preview-util">
            <a href="/app.html">← 交互页</a>
            <a href={`/video.html?record=1&scene=${sceneId}`}>当前场景 · 录屏</a>
            {loading && densityData == null && (
              <span className="vd-badge">加载密度场…</span>
            )}
            {loading && densityData != null && (
              <span className="vd-badge">切换时间步…</span>
            )}
            {error && <span className="vd-badge error">{error}</span>}
          </div>
          <VideoSceneNav
            currentScene={sceneId}
            recordMode={recordMode}
            onSceneChange={setScene}
          />
        </div>
      )}

      {recordMode && sceneId === 'intro' && (
        <div className="vd-preview-bar vd-preview-bar--record">
          <VideoSceneNav
            currentScene={sceneId}
            recordMode={recordMode}
            onSceneChange={setScene}
          />
        </div>
      )}

      <VideoSceneLayout
        sceneId={sceneId}
        sceneMeta={sceneMeta}
        videoStats={videoStats}
        timeline={timeline}
        densityData={densityData}
        loading={loading}
        timestep={timestep}
        stats={stats}
        dataMin={dataMin}
        dataMax={dataMax}
        tfParams={tfParams}
        volumeQuality={volumeQuality}
        qualityPhase={qualityPhase}
        volumeReady={volumeReady}
        onVolumeRendered={onVolumeRendered}
        brushRange={brushRange}
        highlightMin={highlight.highlightMin}
        highlightMax={highlight.highlightMax}
        volumeRatio={volumeRatio}
        onTop1={applyTop1}
        onBottom1={applyBottom1}
        onFilament={applyFilament}
        onClear={clearBrush}
        activePreset={activePreset}
        histOverlaySize={histOverlaySize}
        histogramSizeOpts={histogramSizeOpts}
        keepVolumeAlive={keepVolumeAlive}
        volumeEverMounted={volumeEverMounted}
        onVolumeMounted={() => setVolumeEverMounted(true)}
        onSelectTimestep={selectTimestep}
      />
    </div>
  );
}
