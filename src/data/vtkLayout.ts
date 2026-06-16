import { GRID_SIZE, VOXEL_COUNT } from './types';

/** z-fastest flat index → vtk i-fastest layout */
const Z_TO_VTK = new Uint32Array(VOXEL_COUNT);
for (let x = 0; x < GRID_SIZE; x++) {
  const xOff = x * GRID_SIZE * GRID_SIZE;
  for (let y = 0; y < GRID_SIZE; y++) {
    const yOff = xOff + y * GRID_SIZE;
    for (let z = 0; z < GRID_SIZE; z++) {
      Z_TO_VTK[yOff + z] = x + GRID_SIZE * (y + GRID_SIZE * z);
    }
  }
}

export function convertZFastToVtk(zFast: Float32Array): Float32Array {
  const out = new Float32Array(VOXEL_COUNT);
  for (let i = 0; i < VOXEL_COUNT; i++) {
    out[Z_TO_VTK[i]!] = zFast[i]!;
  }
  return out;
}
