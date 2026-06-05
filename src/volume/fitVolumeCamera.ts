import type vtkRenderer from '@kitware/vtk.js/Rendering/Core/Renderer';
import type vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';
import {
  CAMERA_DISTANCE_FACTOR,
  CAMERA_OFFSET,
  VIEW_MARGIN,
} from './renderSpec';

/**
 * Frame the volume cube centered and fully visible (works for 16:9 capture).
 */
export function fitVolumeCamera(
  renderer: vtkRenderer,
  imageData: vtkImageData,
  viewAspect?: number,
  zoomFactor = 1,
): void {
  const bounds = imageData.getBounds();
  const camera = renderer.getActiveCamera();

  const cx = 0.5 * (bounds[0] + bounds[1]);
  const cy = 0.5 * (bounds[2] + bounds[3]);
  const cz = 0.5 * (bounds[4] + bounds[5]);

  camera.setViewUp(0, 0, 1);
  camera.setFocalPoint(cx, cy, cz);

  const extent = Math.max(
    bounds[1] - bounds[0],
    bounds[3] - bounds[2],
    bounds[5] - bounds[4],
  );
  const d = extent * CAMERA_DISTANCE_FACTOR;
  camera.setPosition(
    cx + d * CAMERA_OFFSET.x,
    cy + d * CAMERA_OFFSET.y,
    cz + d * CAMERA_OFFSET.z,
  );

  renderer.resetCamera(bounds);

  const aspect = viewAspect ?? 1;
  const wideBoost = aspect > 1.2 ? 1 / Math.sqrt(aspect) : 1;
  camera.zoom(VIEW_MARGIN * wideBoost * zoomFactor);

  renderer.resetCameraClippingRange();
}
