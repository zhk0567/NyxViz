import type vtkCamera from '@kitware/vtk.js/Rendering/Core/Camera';
import type vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper';
import { VOLUME_QUALITY_PRESETS, type VolumeQuality } from './renderSpec';

export function getCameraDistance(camera: vtkCamera): number {
  const p = camera.getPosition();
  const f = camera.getFocalPoint();
  return Math.hypot(p[0] - f[0], p[1] - f[1], p[2] - f[2]);
}

const VIDEO_ADAPTIVE_CAPS = {
  maxRatio: 2.0,
  minSampleDistance: 1.0,
  maxSamplesCap: 480,
} as const;

/** 放大倍率越高，采样越密，保持屏幕空间精度 */
export function applyAdaptiveVolumeSampling(
  mapper: vtkVolumeMapper,
  quality: VolumeQuality,
  zoomRatio: number,
): void {
  const preset = VOLUME_QUALITY_PRESETS[quality];
  const isVideoLike = quality === 'video' || quality === 'cinematic';
  const maxRatio = isVideoLike ? VIDEO_ADAPTIVE_CAPS.maxRatio : 3.5;
  const minDist =
    quality === 'presentation' && zoomRatio > 1.5
      ? 0.28
      : isVideoLike
        ? VIDEO_ADAPTIVE_CAPS.minSampleDistance
        : 0.35;
  const samplesCap = isVideoLike
    ? quality === 'cinematic'
      ? 640
      : VIDEO_ADAPTIVE_CAPS.maxSamplesCap
    : 6144;
  const ratio = Math.max(1, Math.min(zoomRatio, maxRatio));
  mapper.setSampleDistance(Math.max(minDist, preset.sampleDistance / ratio));
  mapper.setMaximumSamplesPerRay(
    Math.min(samplesCap, Math.round(preset.maximumSamplesPerRay * Math.min(ratio, 2))),
  );
}

export function measureVolumeZoomRatio(
  camera: vtkCamera,
  baselineDistance: number,
): number {
  const dist = getCameraDistance(camera);
  if (dist <= 0 || baselineDistance <= 0) return 1;
  return Math.max(1, baselineDistance / dist);
}
