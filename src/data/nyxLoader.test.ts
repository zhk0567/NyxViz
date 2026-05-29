import { describe, expect, it } from 'vitest';
import { flatIndex, getVoxel } from './nyxLoader';
import { GRID_SIZE } from './types';

describe('nyxLoader axis order (z fastest)', () => {
  it('flatIndex matches z-fast layout', () => {
    const data = new Float32Array(GRID_SIZE ** 3);
    for (let i = 0; i < data.length; i++) data[i] = i;

    expect(getVoxel(data, 0, 0, 0)).toBe(0);
    expect(getVoxel(data, 0, 0, 1)).toBe(1);
    expect(getVoxel(data, 0, 1, 0)).toBe(128);
    expect(getVoxel(data, 1, 0, 0)).toBe(128 * 128);
    expect(flatIndex(64, 64, 64)).toBe(64 + 128 * 64 + 128 * 128 * 64);
  });
});
