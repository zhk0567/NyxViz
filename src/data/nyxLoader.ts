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

const prefetchCache = new Map<number, Float32Array>();

export function getPrefetchedTimestep(timestep: number): Float32Array | undefined {
  return prefetchCache.get(timestep);
}

export function setPrefetchedTimestep(timestep: number, data: Float32Array): void {
  if (prefetchCache.size >= 3) {
    const first = prefetchCache.keys().next().value;
    if (first !== undefined) prefetchCache.delete(first);
  }
  prefetchCache.set(timestep, data);
}

export async function loadTimestep(timestep: number): Promise<Float32Array> {
  const cached = prefetchCache.get(timestep);
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
  prefetchCache.set(timestep, data);
  return data;
}

export type ProjectionAxis = 'xy' | 'xz' | 'yz';

/** Max-density projection on a 2D plane (128×128). */
export function computeMaxProjection(
  data: Float32Array,
  axis: ProjectionAxis,
): Float32Array {
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
        let vv: number;
        if (axis === 'xy') {
          u = x + y * GRID_SIZE;
        } else if (axis === 'xz') {
          u = x + z * GRID_SIZE;
        } else {
          u = y + z * GRID_SIZE;
        }
        vv = out[u]!;
        if (v > vv) out[u] = v;
      }
    }
  }

  for (let i = 0; i < size; i++) {
    if (!Number.isFinite(out[i]!)) out[i] = 0;
  }
  return out;
}

const vtkScalarCache = new WeakMap<Float32Array, Float32Array>();

/** Copy scalar field into vtk-compatible layout; cached per timestep buffer. */
export function getVtkScalars(zFastData: Float32Array): Float32Array {
  const cached = vtkScalarCache.get(zFastData);
  if (cached) return cached;

  const out = new Float32Array(VOXEL_COUNT);
  for (let x = 0; x < GRID_SIZE; x++) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y++) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z++) {
        const vtkIdx = x + GRID_SIZE * (y + GRID_SIZE * z);
        out[vtkIdx] = zFastData[yOff + z]!;
      }
    }
  }
  vtkScalarCache.set(zFastData, out);
  return out;
}

/** @deprecated Use getVtkScalars */
export const toVtkScalars = getVtkScalars;

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
