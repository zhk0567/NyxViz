import { useEffect, useRef } from 'react';
import {
  getPrefetchedTimestep,
  hasTimestepCached,
  loadTimestep,
  prewarmVtkScalarsQuiet,
} from '@/data/nyxLoader';
import { isStaticFiguresOnly } from '@/config/publicPaths';
import { useAppStore } from '@/store/useAppStore';

export function useNyxTimestep() {
  const timestep = useAppStore((s) => s.timestep);
  const setDensityData = useAppStore((s) => s.setDensityData);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);
  const loadGenRef = useRef(0);

  useEffect(() => {
    if (isStaticFiguresOnly()) {
      setDensityData(null);
      setLoading(false);
      setError(null);
      return;
    }

    const gen = ++loadGenRef.current;
    let cancelled = false;
    setError(null);

    const commit = (data: Float32Array, t: number) => {
      if (cancelled || gen !== loadGenRef.current) return;
      setDensityData(data);
      setLoading(false);
      prewarmVtkScalarsQuiet(t, data);
    };

    const prefetched = getPrefetchedTimestep(timestep);
    if (prefetched) {
      commit(prefetched, timestep);
      return () => {
        cancelled = true;
      };
    }

    if (!hasTimestepCached(timestep) && !useAppStore.getState().densityData) {
      setLoading(true);
    }

    void loadTimestep(timestep)
      .then((data) => commit(data, timestep))
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
