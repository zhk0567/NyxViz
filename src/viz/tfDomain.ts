import type { DensityStats, TimelineData } from '@/data/types';
import type { TfParams } from '@/volume/transferFunction';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

export interface TfDomain {
  min: number;
  max: number;
  useLogScale: boolean;
}

export interface CaptureProfile {
  domain: TfDomain;
  tfParams: TfParams;
  highlightMin?: number;
  highlightMax?: number;
}

/** Linear interpolation between known percentile knots on per-step stats. */
function percentileAt(stats: DensityStats, pct: number): number {
  const knots: [number, number][] = [
    [1, stats.p01],
    [10, stats.p10 ?? stats.p01],
    [25, stats.p25 ?? stats.p50],
    [50, stats.p50],
    [75, stats.p75 ?? stats.p50],
    [90, stats.p90],
    [99, stats.p99],
    [99.9, stats.p999],
  ];
  if (pct <= knots[0][0]) return knots[0][1];
  if (pct >= knots[knots.length - 1][0]) return knots[knots.length - 1][1];
  for (let i = 0; i < knots.length - 1; i++) {
    const [p0, v0] = knots[i];
    const [p1, v1] = knots[i + 1];
    if (pct <= p1) {
      const w = (pct - p0) / (p1 - p0);
      return v0 + w * (v1 - v0);
    }
  }
  return stats.p99;
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

/** Default cinematic profile for general volume views. */
export function getCinematicDefaultProfile(timeline: TimelineData): CaptureProfile {
  return {
    domain: getGlobalTfDomain(timeline),
    tfParams: {
      opacityScale: 0.92,
      densityGain: -0.15,
      highlightBoost: 1.48,
    },
  };
}

/** Scene-aware volume visual profile. */
export function resolveVolumeVisualProfile(
  timeline: TimelineData,
  timestep: number,
  sceneId?: string,
): CaptureProfile & { cameraZoom?: number } {
  if (sceneId === 'task1-morph') {
    const profile = getGlobalMorphCaptureProfile(timeline, timestep);
    return {
      ...profile,
      cameraZoom: VIDEO_CAMERA_ZOOM + (timestep / 99) * 0.08,
    };
  }
  if (
    sceneId === 'task2-evolution' ||
    sceneId === 'task3-hist' ||
    sceneId === 'task2-cases'
  ) {
    return getEvolutionCaptureProfile(timeline, timestep);
  }
  return getCinematicDefaultProfile(timeline);
}

/**
 * Evolution-strip capture: fixed global domain + progressive density reveal.
 * Per-step p01–p99 normalization was stretching each frame to full saturation,
 * making t=0…99 thumbnails look identical; global domain keeps early steps faint.
 */
export function getEvolutionCaptureProfile(
  timeline: TimelineData,
  timestep: number,
): CaptureProfile {
  return getGlobalMorphCaptureProfile(timeline, timestep);
}

/**
 * Global-domain morph/evolution capture: strong TF evolution + progressive highlight reveal.
 * Keeps getGlobalTfDomain for cross-step comparability while amplifying visible change.
 */
export function getGlobalMorphCaptureProfile(
  timeline: TimelineData,
  timestep: number,
): CaptureProfile {
  const tNorm = timestep / 99;
  const stats = timeline.timesteps[timestep];
  const domain = getGlobalTfDomain(timeline);

  const tfParams: TfParams = {
    opacityScale: 0.55 + tNorm * 1.0,
    densityGain: tNorm < 0.45 ? -0.48 * (1 - tNorm / 0.45) : 0,
    highlightBoost: 1.0 + tNorm * 0.48,
  };

  if (timestep >= 99 || !stats) {
    return { domain, tfParams };
  }

  const p92 = percentileAt(stats, 92);
  const p55 = percentileAt(stats, 55);
  const highlightMin = p92 + tNorm * (p55 - p92);

  return {
    domain,
    tfParams,
    highlightMin,
    highlightMax: stats.p99,
  };
}
