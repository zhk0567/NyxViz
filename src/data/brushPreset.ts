import type { BrushRange, DensityStats } from '@/data/types';

export type BrushPresetId = 'top' | 'filament' | 'bottom';

const REL_EPS = 1e-4;
const ABS_EPS = 1e-3;

function near(a: number, b: number): boolean {
  const scale = Math.max(Math.abs(a), Math.abs(b), 1);
  return Math.abs(a - b) <= Math.max(ABS_EPS, scale * REL_EPS);
}

function rangeMatches(
  brush: BrushRange,
  min: number,
  max: number,
): boolean {
  return near(brush.min, min) && near(brush.max, max);
}

export function matchBrushPreset(
  stats: DensityStats | undefined,
  brushRange: BrushRange | null,
): BrushPresetId | null {
  if (!stats || !brushRange) return null;

  if (rangeMatches(brushRange, stats.p99, stats.max)) return 'top';
  if (rangeMatches(brushRange, stats.p90, stats.p99)) return 'filament';
  if (rangeMatches(brushRange, stats.min, stats.p01)) return 'bottom';
  return null;
}
