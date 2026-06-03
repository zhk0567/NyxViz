import { GRID_SIZE } from '../data/types';

export interface ProjectionRequest {
  id: number;
  buffer: ArrayBuffer;
  axis: 'xy' | 'xz' | 'yz';
}

export interface ProjectionResponse {
  id: number;
  buffer: ArrayBuffer;
}

self.onmessage = (ev: MessageEvent<ProjectionRequest>) => {
  const { id, buffer, axis } = ev.data;
  const data = new Float32Array(buffer);
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
        if (axis === 'xy') u = x + y * GRID_SIZE;
        else if (axis === 'xz') u = x + z * GRID_SIZE;
        else u = y + z * GRID_SIZE;
        if (v > out[u]!) out[u] = v;
      }
    }
  }

  for (let i = 0; i < size; i++) {
    if (!Number.isFinite(out[i]!)) out[i] = 0;
  }

  self.postMessage({ id, buffer: out.buffer } satisfies ProjectionResponse, [
    out.buffer,
  ]);
};
