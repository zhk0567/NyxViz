import { GRID_SIZE } from '../data/types';

export interface BrushScanRequest {
  buffer: ArrayBuffer;
  minDensity: number;
  maxDensity: number;
  maxPoints: number;
}

export interface BrushScanPoint {
  x: number;
  y: number;
  z: number;
  density: number;
}

export interface BrushScanResponse {
  points: BrushScanPoint[];
}

self.onmessage = (ev: MessageEvent<BrushScanRequest>) => {
  const { buffer, minDensity, maxDensity, maxPoints } = ev.data;
  const data = new Float32Array(buffer);
  const points: BrushScanPoint[] = [];
  const stride = maxPoints < 20000 ? 2 : 1;

  outer: for (let x = 0; x < GRID_SIZE; x += stride) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y += stride) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z += stride) {
        const density = data[yOff + z]!;
        if (density >= minDensity && density <= maxDensity) {
          points.push({ x, y, z, density });
          if (points.length >= maxPoints) break outer;
        }
      }
    }
  }

  self.postMessage({ points } satisfies BrushScanResponse);
};
