import type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

export type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

export const VIDEO_MINI_TREND = {
  minHeight: 86,
  maxHeight: 92,
  aspect: 1.55,
  fillContainer: true,
  videoReadable: true,
} as const;

export function computeTailBadge(timeline: VideoSceneLayoutProps['timeline']): string {
  const tailSeries = timeline.timesteps.map((s) => s.tailMassAboveP99 * 100);
  const tail0 = tailSeries[0]!;
  const tailPeak = Math.max(...tailSeries);
  const tailRel = tail0 > 1e-6 ? ((tailPeak - tail0) / tail0) * 100 : 0;
  return tailRel >= 0.0005 ? `+${tailRel.toFixed(tailRel < 0.1 ? 3 : 1)}%` : '≈0%';
}
