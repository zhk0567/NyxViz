import { startTransition, useEffect, useRef } from 'react';
import {
  getPrefetchedTimestep,
  hasTimestepCached,
  loadTimestep,
  prewarmVtkScalarsQuiet,
} from '@/data/nyxLoader';
import { useAppStore } from '@/store/useAppStore';

export function useNyxTimestep() {
  const timestep = useAppStore((s) => s.timestep);
  const setDensityData = useAppStore((s) => s.setDensityData);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);
  const loadGenRef = useRef(0);

  useEffect(() => {
    const gen = ++loadGenRef.current;
    let cancelled = false;
    setError(null);

    const apply = (data: Float32Array) => {
      if (cancelled || gen !== loadGenRef.current) return;
      prewarmVtkScalarsQuiet(timestep, data);
      startTransition(() => {
        setDensityData(data);
        setLoading(false);
      });
    };

    const prefetched = getPrefetchedTimestep(timestep);
    if (prefetched) {
      apply(prefetched);
      return;
    }

    if (!hasTimestepCached(timestep) && !useAppStore.getState().densityData) {
      setLoading(true);
    }

    loadTimestep(timestep)
      .then((data) => apply(data))
      .catch((err: unknown) => {
        if (cancelled || gen !== loadGenRef.current) return;
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [timestep, setDensityData, setLoading, setError]);
}
