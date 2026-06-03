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

/** Per-step p01–p99 — emphasizes morphological change in evolution strip captures. */
export function getTimestepTfDomain(
  timeline: TimelineData,
  timestep: number,
): TfDomain {
  const s = timeline.timesteps[timestep];
  if (!s) return getGlobalTfDomain(timeline);
  return { min: s.p01, max: s.p99, useLogScale: true };
}

/** Capture profile: early steps suppress IGM haze, late steps show full web. */
export function getEvolutionCaptureProfile(timeline: TimelineData, timestep: number) {
  const tNorm = timestep / 99;
  return {
    domain: getTimestepTfDomain(timeline, timestep),
    tfParams: {
      opacityScale: 0.72 + tNorm * 0.38,
      densityGain: tNorm < 0.45 ? -0.32 * (1 - tNorm / 0.45) : 0,
    },
  };
}
