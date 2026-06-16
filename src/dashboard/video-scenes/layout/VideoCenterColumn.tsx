import { memo, useState } from 'react';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { VolumeScene } from '@/volume/VolumeScene';
import { DensityColorLegend } from '@/volume/DensityColorLegend';
import { isStaticFiguresOnly, volumeFigureUrl } from '@/config/publicPaths';
import type { VolumePaneProps } from '@/dashboard/video-scenes/layout/types';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

function StaticVolumeFigure({
  timestep,
  onReady,
}: {
  timestep: number;
  onReady?: () => void;
}) {
  return (
    <img
      className="vd-vtk-static-figure"
      src={volumeFigureUrl(timestep)}
      alt={`密度体渲染 t=${timestep}`}
      onLoad={() => onReady?.()}
    />
  );
}

function VolumePaneInner({
  densityData,
  loading,
  timestep,
  dataMin,
  dataMax,
  tfParams,
  volumeQuality,
  qualityPhase,
  highlightMin,
  highlightMax,
  onVolumeRendered,
  onVolumeCameraActivity,
  renderActive,
  progressiveQuality,
  interactiveCamera = false,
  focusOnClick = false,
  focusDensityThreshold,
  performanceMode = 'video',
  cameraZoom = VIDEO_CAMERA_ZOOM,
  visualStyle = 'cinematic',
}: VolumePaneProps) {
  const [focused, setFocused] = useState(false);
  const showFullOverlay = loading && !densityData;
  const showQualityBadge =
    progressiveQuality &&
    !showFullOverlay &&
    densityData != null &&
    qualityPhase === 'draft' &&
    volumeQuality !== 'presentation' &&
    volumeQuality !== 'cinematic';
  const showInteractHint = interactiveCamera || focusOnClick;

  if (isStaticFiguresOnly()) {
    return (
      <div className="vd-vtk-frame">
        <div className="vd-vtk-canvas-wrap">
          <StaticVolumeFigure timestep={timestep} onReady={onVolumeRendered} />
        </div>
        <DensityColorLegend min={dataMin} max={dataMax} />
      </div>
    );
  }

  return (
    <div className="vd-vtk-frame">
      {showInteractHint && (
        <p className="vd-vtk-interact-hint">
          单击聚焦结构 · 双击复位 · 滚轮缩放 · 拖拽旋转
        </p>
      )}
      <div className="vd-vtk-canvas-wrap">
        <LoadingOverlay visible={showFullOverlay} label={`加载 t=${timestep}…`} />
        <LoadingOverlay
          visible={showQualityBadge}
          label="高清渲染中…"
          variant="badge"
        />
        {focused && focusOnClick && (
          <div className="vd-vtk-focus-badge" aria-hidden>
            局部视图 · 双击复位
          </div>
        )}
        {densityData ? (
          <VolumeScene
            data={densityData}
            timestep={timestep}
            dataMin={dataMin}
            dataMax={dataMax}
            tfParams={tfParams}
            quality={volumeQuality}
            renderActive={renderActive}
            cameraZoom={cameraZoom}
            showOrientation={false}
            highlightMin={highlightMin}
            highlightMax={highlightMax}
            onRendered={onVolumeRendered}
            onCameraActivity={onVolumeCameraActivity}
            interactiveCamera={interactiveCamera}
            adaptivePrecisionZoom={interactiveCamera || focusOnClick}
            focusOnClick={focusOnClick}
            focusDensityThreshold={focusDensityThreshold}
            performanceMode={performanceMode}
            visualStyle={visualStyle}
            onFocusChange={setFocused}
            className="vd-vtk-panel"
          />
        ) : (
          <div className="vd-vtk-fallback">加载密度场…</div>
        )}
      </div>
      <DensityColorLegend min={dataMin} max={dataMax} />
    </div>
  );
}

export const VolumePane = memo(VolumePaneInner);

interface PersistentVolumePaneProps extends VolumePaneProps {
  visible: boolean;
  mounted: boolean;
}

export function PersistentVolumePane({
  visible,
  mounted,
  ...volumeProps
}: PersistentVolumePaneProps) {
  if (!mounted) return null;

  return (
    <div className="vd-volume-keepalive" aria-hidden={!visible}>
      <VolumePane {...volumeProps} renderActive={visible && volumeProps.renderActive} />
    </div>
  );
}
