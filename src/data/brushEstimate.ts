import * as d3 from 'd3';
import type { BrushRange, TimelineData } from '@/data/types';
import { VOXEL_COUNT } from '@/data/types';

/** Static-mode fallback: estimate brushed voxel count from precomputed histogram bins. */
export function estimateBrushCountFromHistogram(
  timeline: TimelineData,
  timestep: number,
  brushRange: BrushRange,
): number {
  const hist = timeline.histograms[timestep];
  if (!hist?.length) return 0;

  const edges = timeline.logBinEdges;
  let mass = 0;
  for (let i = 0; i < hist.length; i++) {
    const lo = edges[i]!;
    const hi = edges[i + 1]!;
    if (hi < brushRange.min || lo > brushRange.max) continue;
    const center = Math.sqrt(lo * hi);
    if (center >= brushRange.min && center <= brushRange.max) {
      mass += hist[i]!;
    }
  }
  const total = d3.sum(hist) || 1;
  return Math.round((mass / total) * VOXEL_COUNT);
}
