import { GRID_SIZE, VOXEL_COUNT } from '../data/types';

const Z_TO_VTK = new Uint32Array(VOXEL_COUNT);
for (let x = 0; x < GRID_SIZE; x++) {
  const xOff = x * GRID_SIZE * GRID_SIZE;
  for (let y = 0; y < GRID_SIZE; y++) {
    const yOff = xOff + y * GRID_SIZE;
    for (let z = 0; z < GRID_SIZE; z++) {
      const zIdx = yOff + z;
      Z_TO_VTK[zIdx] = x + GRID_SIZE * (y + GRID_SIZE * z);
    }
  }
}

export interface VtkConvertRequest {
  id: number;
  buffer: ArrayBuffer;
}

export interface VtkConvertResponse {
  id: number;
  buffer: ArrayBuffer;
}

self.onmessage = (ev: MessageEvent<VtkConvertRequest>) => {
  const { id, buffer } = ev.data;
  const zFast = new Float32Array(buffer);
  const out = new Float32Array(VOXEL_COUNT);
  for (let i = 0; i < VOXEL_COUNT; i++) {
    out[Z_TO_VTK[i]!] = zFast[i]!;
  }
  self.postMessage({ id, buffer: out.buffer } satisfies VtkConvertResponse, [
    out.buffer,
  ]);
};
