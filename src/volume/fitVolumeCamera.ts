import type vtkRenderer from '@kitware/vtk.js/Rendering/Core/Renderer';
import type vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';

/** Padding factor after resetCamera (<1 zooms out). */
const VIEW_MARGIN = 0.88;

/**
 * Frame the volume cube centered and fully visible (works for 16:9 capture).
 */
export function fitVolumeCamera(
  renderer: vtkRenderer,
  imageData: vtkImageData,
  viewAspect?: number,
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
  const d = extent * 1.75;
  camera.setPosition(cx + d * 0.92, cy + d * 0.78, cz + d * 0.68);

  renderer.resetCamera(bounds);

  // Wide viewports: pull back a bit more so the cube is not clipped top/bottom.
  const aspect = viewAspect ?? 1;
  const wideBoost = aspect > 1.2 ? 1 / Math.sqrt(aspect) : 1;
  camera.zoom(VIEW_MARGIN * wideBoost);

  renderer.resetCameraClippingRange();
}
