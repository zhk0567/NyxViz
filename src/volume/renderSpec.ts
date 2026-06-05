import { DOMAIN_LENGTH } from '@/data/types';

/** Shared volume-rendering constants — keep in sync with tools/python/render_spec.py */
export const VIEW_MARGIN = 0.88;
export const CAMERA_DISTANCE_FACTOR = 1.75;
export const CAMERA_OFFSET = { x: 0.92, y: 0.78, z: 0.68 } as const;
export const CAPTURE_CAMERA_ZOOM = 1.0;
export const VIDEO_CAMERA_ZOOM = 1.1;

export const VOLUME_LIGHTING = {
  key: {
    offset: [8, 10, 12] as const,
    color: [1, 1, 1] as const,
    intensity: 1.0,
  },
  fill: {
    offset: [-12, -8, -10] as const,
    color: [0.55, 0.75, 1] as const,
    intensity: 0.3,
  },
} as const;

export const VOLUME_QUALITY_PRESETS = {
  interactive: {
    sampleDistance: 4.0,
    maximumSamplesPerRay: 512,
    shade: false,
    ambient: 0.2,
    diffuse: 0.55,
    specular: 0.1,
  },
  high: {
    sampleDistance: 1.2,
    maximumSamplesPerRay: 2048,
    shade: true,
    ambient: 0.12,
    diffuse: 0.75,
    specular: 0.4,
  },
  presentation: {
    sampleDistance: 0.65,
    maximumSamplesPerRay: 4096,
    shade: true,
    ambient: 0.12,
    diffuse: 0.75,
    specular: 0.4,
  },
} as const;

export const OPACITY_SCALAR_UNIT_DISTANCE = 2.5; // × voxel spacing

/** Default cosmic opacity control points (normalized t∈[0,1] on log domain, opacityScale=1). */
export const COSMIC_OPACITY_STOPS: ReadonlyArray<readonly [t: number, opacity: number]> = [
  [0.0, 0.0],
  [0.12, 0.02],
  [0.35, 0.06],
  [0.55, 0.14],
  [0.72, 0.32],
  [0.88, 0.65],
  [1.0, 0.95],
];

export interface VolumeCameraSpec {
  domainLength: number;
  focalPoint: [number, number, number];
  position: [number, number, number];
  viewUp: [number, number, number];
  viewMargin: number;
  wideAspectBoost: number;
  zoomFactor: number;
  effectiveZoom: number;
  viewAspect: number;
}

export function computeVolumeCameraSpec(
  viewAspect = 16 / 9,
  zoomFactor = CAPTURE_CAMERA_ZOOM,
): VolumeCameraSpec {
  const cx = DOMAIN_LENGTH / 2;
  const cy = DOMAIN_LENGTH / 2;
  const cz = DOMAIN_LENGTH / 2;
  const extent = DOMAIN_LENGTH;
  const d = extent * CAMERA_DISTANCE_FACTOR;
  const wideBoost = viewAspect > 1.2 ? 1 / Math.sqrt(viewAspect) : 1;
  const effectiveZoom = VIEW_MARGIN * wideBoost * zoomFactor;

  return {
    domainLength: DOMAIN_LENGTH,
    focalPoint: [cx, cy, cz],
    position: [
      cx + d * CAMERA_OFFSET.x,
      cy + d * CAMERA_OFFSET.y,
      cz + d * CAMERA_OFFSET.z,
    ],
    viewUp: [0, 0, 1],
    viewMargin: VIEW_MARGIN,
    wideAspectBoost: wideBoost,
    zoomFactor,
    effectiveZoom,
    viewAspect,
  };
}
