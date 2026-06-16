import vtkCoordinate from '@kitware/vtk.js/Rendering/Core/Coordinate';
import type vtkRenderer from '@kitware/vtk.js/Rendering/Core/Renderer';
import { getVoxel } from '@/data/nyxLoader';
import { DOMAIN_LENGTH, GRID_SIZE, SPACING } from '@/data/types';

export interface WorldRay {
  origin: [number, number, number];
  direction: [number, number, number];
}

export interface PickResult {
  point: [number, number, number];
  density: number;
}

const RAY_STEPS = 96;

function normalize(v: [number, number, number]): [number, number, number] {
  const len = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / len, v[1] / len, v[2] / len];
}

/** Display pixel (relative to container) → world-space ray through volume. */
export function displayToWorldRay(
  renderer: vtkRenderer,
  displayX: number,
  displayY: number,
): WorldRay {
  const coord = vtkCoordinate.newInstance();
  coord.setCoordinateSystemToDisplay();
  coord.setValue(displayX, displayY, 0);
  const near = coord.getComputedWorldValue(renderer) as [number, number, number];
  coord.setValue(displayX, displayY, 1);
  const far = coord.getComputedWorldValue(renderer) as [number, number, number];
  coord.delete();

  const dir: [number, number, number] = [
    far[0] - near[0],
    far[1] - near[1],
    far[2] - near[2],
  ];
  return { origin: near, direction: normalize(dir) };
}

/** Ray–AABB intersection for [0, DOMAIN_LENGTH]³. Returns [tEnter, tExit] or null. */
function rayBoxIntersection(
  origin: [number, number, number],
  dir: [number, number, number],
): [number, number] | null {
  let tMin = -Infinity;
  let tMax = Infinity;

  for (let axis = 0; axis < 3; axis++) {
    const o = origin[axis]!;
    const d = dir[axis]!;
    if (Math.abs(d) < 1e-9) {
      if (o < 0 || o > DOMAIN_LENGTH) return null;
      continue;
    }
    const t1 = (0 - o) / d;
    const t2 = (DOMAIN_LENGTH - o) / d;
    const lo = Math.min(t1, t2);
    const hi = Math.max(t1, t2);
    tMin = Math.max(tMin, lo);
    tMax = Math.min(tMax, hi);
    if (tMin > tMax) return null;
  }

  if (tMax < 0) return null;
  return [Math.max(0, tMin), tMax];
}

function sampleDensityAtWorld(
  data: Float32Array,
  wx: number,
  wy: number,
  wz: number,
): number {
  const fx = wx / SPACING;
  const fy = wy / SPACING;
  const fz = wz / SPACING;
  const x = Math.min(GRID_SIZE - 1, Math.max(0, Math.floor(fx)));
  const y = Math.min(GRID_SIZE - 1, Math.max(0, Math.floor(fy)));
  const z = Math.min(GRID_SIZE - 1, Math.max(0, Math.floor(fz)));
  return getVoxel(data, x, y, z);
}

/**
 * March along ray inside volume; return highest-density point above threshold.
 * Falls back to segment midpoint if no peak exceeds threshold.
 */
export function pickDensityPeakAlongRay(
  data: Float32Array,
  origin: [number, number, number],
  direction: [number, number, number],
  densityThreshold: number,
): PickResult | null {
  const hit = rayBoxIntersection(origin, direction);
  if (!hit) return null;

  const [tEnter, tExit] = hit;
  let best: PickResult | null = null;
  let bestDensity = -Infinity;
  let anyPeak = false;

  for (let i = 0; i < RAY_STEPS; i++) {
    const t = tEnter + ((tExit - tEnter) * (i + 0.5)) / RAY_STEPS;
    const wx = origin[0]! + direction[0]! * t;
    const wy = origin[1]! + direction[1]! * t;
    const wz = origin[2]! + direction[2]! * t;
    const rho = sampleDensityAtWorld(data, wx, wy, wz);
    if (rho >= densityThreshold && rho > bestDensity) {
      bestDensity = rho;
      best = { point: [wx, wy, wz], density: rho };
      anyPeak = true;
    }
  }

  if (anyPeak && best) return best;

  const tMid = (tEnter + tExit) * 0.5;
  const wx = origin[0]! + direction[0]! * tMid;
  const wy = origin[1]! + direction[1]! * tMid;
  const wz = origin[2]! + direction[2]! * tMid;
  return {
    point: [wx, wy, wz],
    density: sampleDensityAtWorld(data, wx, wy, wz),
  };
}

/** Container client coords → display coords for vtkCoordinate. */
export function clientToDisplay(
  container: HTMLElement,
  clientX: number,
  clientY: number,
): [number, number] {
  const rect = container.getBoundingClientRect();
  const canvas = container.querySelector('canvas');
  if (!canvas) {
    return [clientX - rect.left, rect.height - (clientY - rect.top)];
  }
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (clientX - rect.left) * scaleX;
  const y = (clientY - rect.top) * scaleY;
  return [x, canvas.height - y];
}
