import { useEffect } from 'react';
import { VideoSpatialPanel } from '@/dashboard/video-scenes/VideoSpatialPanel';
import { VideoVoidScene } from '@/dashboard/video-scenes/VideoVoidScene';
import { VideoValidateFigureColumn } from '@/dashboard/video-scenes/VideoValidateFigureColumn';
import { VideoLeftColumn } from '@/dashboard/video-scenes/layout/VideoLeftColumn';
import { VideoRightColumn } from '@/dashboard/video-scenes/layout/VideoRightColumn';
import { VideoFindingsRow } from '@/dashboard/video-scenes/layout/VideoFindingsRow';
import { PersistentVolumePane } from '@/dashboard/video-scenes/layout/VideoCenterColumn';
import type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

export function VideoSceneLayout(props: VideoSceneLayoutProps) {
  const {
    sceneId,
    sceneMeta,
    videoStats,
    keepVolumeAlive,
    volumeEverMounted,
    onVolumeMounted,
  } = props;

  const showLeft = sceneMeta.showLeft;
  const showCenter = sceneMeta.showCenter;
  const showRight = sceneMeta.showRight;
  const showFindings = sceneMeta.showFindings;
  const hasBody =
    sceneId === 'task2-spatial' ||
    sceneId === 'task2-void' ||
    showLeft ||
    showCenter ||
    showRight;

  useEffect(() => {
    if (showCenter && !volumeEverMounted) {
      onVolumeMounted();
    }
  }, [showCenter, volumeEverMounted, onVolumeMounted]);

  const volumeMounted = keepVolumeAlive
    ? volumeEverMounted || showCenter
    : showCenter;

  const volumeProps = {
    densityData: props.densityData,
    loading: props.loading,
    timestep: props.timestep,
    dataMin: props.dataMin,
    dataMax: props.dataMax,
    tfParams: props.tfParams,
    volumeQuality: props.volumeQuality,
    qualityPhase: props.qualityPhase,
    highlightMin: props.highlightMin,
    highlightMax: props.highlightMax,
    onVolumeRendered: props.onVolumeRendered,
    renderActive: true,
    progressiveQuality: true,
  };

  const volumeInCenter =
    showCenter && volumeMounted ? (
      <PersistentVolumePane visible mounted {...volumeProps} />
    ) : null;

  const body = !hasBody ? null : sceneId === 'task2-spatial' ? (
    <div className="vd-body vd-body--spatial">
      <VideoSpatialPanel validation={videoStats.validationExtended} />
    </div>
  ) : sceneId === 'task2-void' ? (
    <VideoVoidScene validation={videoStats.validationExtended} />
  ) : sceneId === 'task4-validate' ? (
    <div className="vd-body vd-body--validate">
      <VideoValidateFigureColumn />
      {showRight && (
        <VideoRightColumn
          sceneId={sceneId}
          videoStats={videoStats}
          timeline={props.timeline}
          densityData={props.densityData}
          loading={props.loading}
          stats={props.stats}
          timestep={props.timestep}
          dataMin={props.dataMin}
          dataMax={props.dataMax}
          volumeReady={props.volumeReady}
          brushRange={props.brushRange}
          volumeRatio={props.volumeRatio}
          onTop1={props.onTop1}
          onBottom1={props.onBottom1}
          onFilament={props.onFilament}
          onClear={props.onClear}
          activePreset={props.activePreset}
          histogramSizeOpts={props.histogramSizeOpts}
          onSelectTimestep={props.onSelectTimestep}
        />
      )}
    </div>
  ) : (
    <div
      className={`vd-body${showLeft && !showCenter && !showRight ? ' vd-body--left-full' : ''}`}
    >
      {showLeft && (
        <VideoLeftColumn
          sceneId={sceneId}
          videoStats={videoStats}
          timeline={props.timeline}
          stats={props.stats}
          histOverlaySize={props.histOverlaySize}
        />
      )}

      {showCenter && (
        <main className="vd-panel vd-panel-center">{volumeInCenter}</main>
      )}

      {showRight && (
        <VideoRightColumn
          sceneId={sceneId}
          videoStats={videoStats}
          timeline={props.timeline}
          densityData={props.densityData}
          loading={props.loading}
          stats={props.stats}
          timestep={props.timestep}
          dataMin={props.dataMin}
          dataMax={props.dataMax}
          volumeReady={props.volumeReady}
          brushRange={props.brushRange}
          volumeRatio={props.volumeRatio}
          onTop1={props.onTop1}
          onBottom1={props.onBottom1}
          onFilament={props.onFilament}
          onClear={props.onClear}
          activePreset={props.activePreset}
          histogramSizeOpts={props.histogramSizeOpts}
          onSelectTimestep={props.onSelectTimestep}
        />
      )}
    </div>
  );

  return (
    <>
      <div className="vd-main-stack">
        {body}
        <VideoFindingsRow
          sceneId={sceneId}
          showFindings={showFindings}
          timeline={props.timeline}
        />
      </div>
      {keepVolumeAlive && volumeMounted && !showCenter && (
        <div className="vd-volume-offscreen" aria-hidden>
          <PersistentVolumePane visible={false} mounted {...volumeProps} />
        </div>
      )}
    </>
  );
}
