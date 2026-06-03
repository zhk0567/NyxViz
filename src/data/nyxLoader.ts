import {
  GRID_SIZE,
  TIMESTEP_COUNT,
  VOXEL_COUNT,
} from './types';

/** z-fastest layout: flatIndex = z + GRID_SIZE * y + GRID_SIZE^2 * x */
export function flatIndex(x: number, y: number, z: number): number {
  return z + GRID_SIZE * y + GRID_SIZE * GRID_SIZE * x;
}

export function getVoxel(
  data: Float32Array,
  x: number,
  y: number,
  z: number,
): number {
  return data[flatIndex(x, y, z)]!;
}

export function timestepUrl(timestep: number): string {
  const step = Math.max(0, Math.min(TIMESTEP_COUNT - 1, timestep));
  return `/Nyx/${String(step).padStart(4, '0')}.dat`;
}

const MAX_TIMESTEP_CACHE = 8;
const prefetchCache = new Map<number, Float32Array>();

function touchTimestepCache(timestep: number, data: Float32Array): void {
  if (prefetchCache.has(timestep)) prefetchCache.delete(timestep);
  prefetchCache.set(timestep, data);
  while (prefetchCache.size > MAX_TIMESTEP_CACHE) {
    const oldest = prefetchCache.keys().next().value;
    if (oldest === undefined) break;
    prefetchCache.delete(oldest);
  }
}

function getTimestepFromCache(timestep: number): Float32Array | undefined {
  const data = prefetchCache.get(timestep);
  if (!data) return undefined;
  prefetchCache.delete(timestep);
  prefetchCache.set(timestep, data);
  return data;
}

export function getPrefetchedTimestep(timestep: number): Float32Array | undefined {
  return getTimestepFromCache(timestep);
}

export function setPrefetchedTimestep(timestep: number, data: Float32Array): void {
  touchTimestepCache(timestep, data);
}

export function prefetchTimestepQuiet(timestep: number): void {
  if (prefetchCache.has(timestep)) return;
  void loadTimestep(timestep).catch(() => {});
}

export function hasTimestepCached(timestep: number): boolean {
  return prefetchCache.has(timestep);
}

export async function loadTimestep(timestep: number): Promise<Float32Array> {
  const cached = getTimestepFromCache(timestep);
  if (cached) return cached;

  const url = timestepUrl(timestep);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength !== VOXEL_COUNT * 4) {
    throw new Error(
      `Unexpected file size for ${url}: ${buffer.byteLength} bytes`,
    );
  }
  const data = new Float32Array(buffer);
  touchTimestepCache(timestep, data);
  return data;
}

export type ProjectionAxis = 'xy' | 'xz' | 'yz';

const projectionCache = new WeakMap<
  Float32Array,
  Map<ProjectionAxis, Float32Array>
>();

/** Max-density projection on a 2D plane (128×128). */
export function computeMaxProjection(
  data: Float32Array,
  axis: ProjectionAxis,
): Float32Array {
  let perAxis = projectionCache.get(data);
  if (!perAxis) {
    perAxis = new Map();
    projectionCache.set(data, perAxis);
  }
  const hit = perAxis.get(axis);
  if (hit) return hit;

  const size = GRID_SIZE * GRID_SIZE;
  const out = new Float32Array(size);
  out.fill(-Infinity);

  for (let x = 0; x < GRID_SIZE; x++) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y++) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z++) {
        const v = data[yOff + z]!;
        let u: number;
        if (axis === 'xy') {
          u = x + y * GRID_SIZE;
        } else if (axis === 'xz') {
          u = x + z * GRID_SIZE;
        } else {
          u = y + z * GRID_SIZE;
        }
        if (v > out[u]!) out[u] = v;
      }
    }
  }

  for (let i = 0; i < size; i++) {
    if (!Number.isFinite(out[i]!)) out[i] = 0;
  }
  perAxis.set(axis, out);
  return out;
}

export { getVtkScalars, getVtkScalarsAsync, getCachedVtkScalars, prewarmVtkScalarsQuiet } from './vtkConvert';

export function scanBrushRange(
  data: Float32Array,
  minDensity: number,
  maxDensity: number,
  maxPoints = 12000,
): { x: number; y: number; z: number; density: number }[] {
  const points: { x: number; y: number; z: number; density: number }[] = [];
  const stride =
    maxPoints < 20000 ? 2 : 1;

  outer: for (let x = 0; x < GRID_SIZE; x += stride) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y += stride) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z += stride) {
        const density = data[yOff + z]!;
        if (density >= minDensity && density <= maxDensity) {
          points.push({ x, y, z, density });
          if (points.length >= maxPoints) {
            break outer;
          }
        }
      }
    }
  }
  return points;
}

export async function loadTimelineStats(): Promise<import('./types').TimelineData> {
  const embedded = (
    window as unknown as { __NYX_TIMELINE__?: import('./types').TimelineData }
  ).__NYX_TIMELINE__;
  if (embedded) return embedded;

  const response = await fetch('/stats/timeline.json');
  if (!response.ok) {
    throw new Error('Missing /stats/timeline.json — run: npm run precompute');
  }
  return response.json();
}
