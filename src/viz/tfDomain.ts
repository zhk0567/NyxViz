import type { TimelineData } from '@/data/types';

export interface TfDomain {
  min: number;
  max: number;
  useLogScale: boolean;
}

/** Fixed global domain so all timesteps are comparable (p01–p99 envelope over 100 steps). */
export function getGlobalTfDomain(timeline: TimelineData): TfDomain {
  let min = Infinity;
  let max = -Infinity;
  for (const s of timeline.timesteps) {
    if (s.p01 < min) min = s.p01;
    if (s.p99 > max) max = s.p99;
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    min = timeline.globalMin;
    max = timeline.globalMax;
  }
  return { min, max, useLogScale: true };
}
