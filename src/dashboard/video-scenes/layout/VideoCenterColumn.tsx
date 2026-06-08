import { LoadingOverlay } from '@/components/LoadingOverlay';
import { VolumeScene } from '@/volume/VolumeScene';
import { DensityColorLegend } from '@/volume/DensityColorLegend';
import type { VolumePaneProps } from '@/dashboard/video-scenes/layout/types';

export function VolumePane({
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
  renderActive,
  progressiveQuality,
}: VolumePaneProps) {
  const showFullOverlay = loading && !densityData;
  const showQualityBadge =
    progressiveQuality &&
    !showFullOverlay &&
    densityData != null &&
    qualityPhase === 'draft' &&
    volumeQuality !== 'presentation';

  return (
    <div className="vd-vtk-frame">
      <div className="vd-vtk-canvas-wrap">
        <LoadingOverlay visible={showFullOverlay} label={`加载 t=${timestep}…`} />
        <LoadingOverlay
          visible={showQualityBadge}
          label="高清渲染中…"
          variant="badge"
        />
        {densityData ? (
          <VolumeScene
            data={densityData}
            timestep={timestep}
            dataMin={dataMin}
            dataMax={dataMax}
            tfParams={tfParams}
            quality={volumeQuality}
            renderActive={renderActive}
            cameraZoom={1.1}
            showOrientation={false}
            highlightMin={highlightMin}
            highlightMax={highlightMax}
            onRendered={onVolumeRendered}
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
