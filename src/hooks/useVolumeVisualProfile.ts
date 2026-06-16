import { useMemo } from 'react';
import type { TimelineData } from '@/data/types';
import type { TfParams } from '@/volume/transferFunction';
import { resolveVolumeVisualProfile } from '@/viz/tfDomain';

export interface VolumeVisualProfile {
  dataMin: number;
  dataMax: number;
  tfParams: TfParams;
  highlightMin?: number;
  highlightMax?: number;
  cameraZoom?: number;
}

export function useVolumeVisualProfile(
  timeline: TimelineData | null | undefined,
  timestep: number,
  sceneId?: string,
): VolumeVisualProfile {
  return useMemo(() => {
    if (!timeline) {
      return {
        dataMin: 7.5,
        dataMax: 15,
        tfParams: {
          opacityScale: 0.92,
          densityGain: -0.15,
          highlightBoost: 1.48,
        },
      };
    }

    const profile = resolveVolumeVisualProfile(timeline, timestep, sceneId);
    return {
      dataMin: profile.domain.min,
      dataMax: profile.domain.max,
      tfParams: profile.tfParams,
      highlightMin: profile.highlightMin,
      highlightMax: profile.highlightMax,
      cameraZoom: profile.cameraZoom,
    };
  }, [timeline, timestep, sceneId]);
}
