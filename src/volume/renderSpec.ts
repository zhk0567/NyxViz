import { DOMAIN_LENGTH } from '@/data/types';

/** Shared volume-rendering constants — keep in sync with tools/python/render_spec.py */
export const VIEW_MARGIN = 0.88;
export const CAMERA_DISTANCE_FACTOR = 1.75;
export const CAMERA_OFFSET = { x: 0.92, y: 0.78, z: 0.68 } as const;
export const CAPTURE_CAMERA_ZOOM = 1.0;
export const VIDEO_CAMERA_ZOOM = 1.24;

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

/** Cinematic three-point lighting — key + fill + rim. */
export const CINEMATIC_LIGHTING = {
  key: {
    offset: [8, 10, 12] as const,
    color: [1, 0.98, 0.95] as const,
    intensity: 1.05,
  },
  fill: {
    offset: [-10, -6, -8] as const,
    color: [0.45, 0.62, 0.95] as const,
    intensity: 0.22,
  },
  rim: {
    offset: [-4, 14, 6] as const,
    color: [0.55, 0.75, 1] as const,
    intensity: 0.42,
  },
} as const;

/** Renderer background RGB — matches VIZ_BG #0a0e1a */
export const VOLUME_RENDERER_BG: [number, number, number] = [0.039, 0.055, 0.102];

export type VolumeQuality = 'video' | 'interactive' | 'high' | 'cinematic' | 'presentation';

/** 录屏/预览页拖拽旋转时的粗采样（比 video 更省 GPU） */
export const VIDEO_DRAG_SAMPLING = {
  sampleDistance: 5.0,
  maximumSamplesPerRay: 256,
  shade: false,
  ambient: 0.2,
  diffuse: 0.55,
  specular: 0.1,
} as const;

export type PerformanceMode = 'video' | 'interactive';

export const VOLUME_QUALITY_PRESETS: Record<
  VolumeQuality,
  {
    sampleDistance: number;
    maximumSamplesPerRay: number;
    shade: boolean;
    ambient: number;
    diffuse: number;
    specular: number;
  }
> = {
  video: {
    // 域长约 14.2；8.0 会导致每射线仅 ~2 次采样，体渲染完全不可见
    sampleDistance: 2.8,
    maximumSamplesPerRay: 320,
    shade: false,
    ambient: 0.2,
    diffuse: 0.55,
    specular: 0.1,
  },
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
  cinematic: {
    sampleDistance: 1.6,
    maximumSamplesPerRay: 1024,
    shade: true,
    ambient: 0.08,
    diffuse: 0.82,
    specular: 0.66,
  },
  presentation: {
    sampleDistance: 0.65,
    maximumSamplesPerRay: 4096,
    shade: true,
    ambient: 0.1,
    diffuse: 0.75,
    specular: 0.52,
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
