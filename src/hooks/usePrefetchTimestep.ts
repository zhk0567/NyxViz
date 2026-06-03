import { useEffect } from 'react';
import { loadTimestep, prefetchTimestepQuiet } from '@/data/nyxLoader';
import { TIMESTEP_COUNT } from '@/data/types';
import { useAppStore } from '@/store/useAppStore';

const NEIGHBOR_DELTAS = [-1, 1] as const;
const SLIDER_PREFETCH_MS = 420;

export function usePrefetchTimestep(
  previewStep?: number,
  sliderDragging = false,
) {
  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);

  useEffect(() => {
    if (previewStep === undefined || previewStep === timestep) return;

    if (sliderDragging) {
      const t = window.setTimeout(
        () => prefetchTimestepQuiet(previewStep),
        SLIDER_PREFETCH_MS,
      );
      return () => window.clearTimeout(t);
    }

    prefetchTimestepQuiet(previewStep);
  }, [previewStep, timestep, sliderDragging]);

  useEffect(() => {
    if (!densityData || sliderDragging) return;

    const schedule =
      typeof requestIdleCallback !== 'undefined'
        ? (cb: () => void) =>
            requestIdleCallback(cb, { timeout: 1200 })
        : (cb: () => void) => window.setTimeout(cb, 400);

    const cancel =
      typeof cancelIdleCallback !== 'undefined'
        ? cancelIdleCallback
        : (id: number) => window.clearTimeout(id);

    const id = schedule(() => {
      for (const delta of NEIGHBOR_DELTAS) {
        const t = timestep + delta;
        if (t < 0 || t >= TIMESTEP_COUNT) continue;
        void loadTimestep(t).catch(() => {});
      }
    });

    return () => cancel(id as number);
  }, [timestep, densityData, sliderDragging]);
}
