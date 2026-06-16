import { useEffect } from 'react';
import {
  hasTimestepCached,
  isVtkScalarsCached,
  prefetchTimestepQuiet,
} from '@/data/nyxLoader';
import { prewarmTimestepQuiet } from '@/data/timelineVolumePreload';
import { TIMESTEP_COUNT } from '@/data/types';
import { useAppStore } from '@/store/useAppStore';

const NEIGHBOR_DELTAS = [-1, 1] as const;
const NEIGHBOR_IDLE_MS = 3000;

export function usePrefetchTimestep(
  previewStep?: number,
  sliderDragging = false,
) {
  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);

  useEffect(() => {
    if (!sliderDragging || previewStep === undefined) return;
    prefetchTimestepQuiet(previewStep);
  }, [previewStep, sliderDragging]);

  useEffect(() => {
    if (!densityData || sliderDragging || document.hidden) return;

    const id = window.setTimeout(() => {
      for (const delta of NEIGHBOR_DELTAS) {
        const t = timestep + delta;
        if (t < 0 || t >= TIMESTEP_COUNT) continue;
        if (hasTimestepCached(t) && isVtkScalarsCached(t)) continue;
        prewarmTimestepQuiet(t);
      }
    }, NEIGHBOR_IDLE_MS);

    return () => window.clearTimeout(id);
  }, [timestep, densityData, sliderDragging]);
}
