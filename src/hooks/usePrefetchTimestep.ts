import { useEffect } from 'react';
import { loadTimestep, setPrefetchedTimestep } from '@/data/nyxLoader';
import { TIMESTEP_COUNT } from '@/data/types';
import { useAppStore } from '@/store/useAppStore';

export function usePrefetchTimestep() {
  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);

  useEffect(() => {
    if (!densityData) return;

    const schedule =
      typeof requestIdleCallback !== 'undefined'
        ? requestIdleCallback
        : (cb: () => void) => window.setTimeout(cb, 200);

    const cancel =
      typeof cancelIdleCallback !== 'undefined'
        ? cancelIdleCallback
        : (id: number) => window.clearTimeout(id);

    const id = schedule(() => {
      for (const delta of [-1, 1]) {
        const t = timestep + delta;
        if (t < 0 || t >= TIMESTEP_COUNT) continue;
        loadTimestep(t)
          .then((d) => setPrefetchedTimestep(t, d))
          .catch(() => {});
      }
    });

    return () => cancel(id as number);
  }, [timestep, densityData]);
}
