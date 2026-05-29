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

export async function loadTimestep(timestep: number): Promise<Float32Array> {
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
  return new Float32Array(buffer);
}

/** Copy scalar field into vtk-compatible C-order (x fastest in point index). */
export function toVtkScalars(zFastData: Float32Array): Float32Array {
  const out = new Float32Array(VOXEL_COUNT);
  for (let x = 0; x < GRID_SIZE; x++) {
    for (let y = 0; y < GRID_SIZE; y++) {
      for (let z = 0; z < GRID_SIZE; z++) {
        const vtkIdx = x + GRID_SIZE * (y + GRID_SIZE * z);
        out[vtkIdx] = zFastData[flatIndex(x, y, z)]!;
      }
    }
  }
  return out;
}

export function scanBrushRange(
  data: Float32Array,
  minDensity: number,
  maxDensity: number,
  maxPoints = 50000,
): { x: number; y: number; z: number; density: number }[] {
  const points: { x: number; y: number; z: number; density: number }[] = [];
  for (let x = 0; x < GRID_SIZE; x++) {
    for (let y = 0; y < GRID_SIZE; y++) {
      for (let z = 0; z < GRID_SIZE; z++) {
        const density = getVoxel(data, x, y, z);
        if (density >= minDensity && density <= maxDensity) {
          points.push({ x, y, z, density });
          if (points.length >= maxPoints) {
            return points;
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
