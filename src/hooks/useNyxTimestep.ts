import { useEffect } from 'react';
import { getPrefetchedTimestep, loadTimestep } from '@/data/nyxLoader';
import { useAppStore } from '@/store/useAppStore';

export function useNyxTimestep() {
  const timestep = useAppStore((s) => s.timestep);
  const setDensityData = useAppStore((s) => s.setDensityData);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    const prefetched = getPrefetchedTimestep(timestep);
    if (prefetched) {
      setDensityData(prefetched);
      setLoading(false);
      return;
    }

    setLoading(true);
    loadTimestep(timestep)
      .then((data) => {
        if (!cancelled) {
          setDensityData(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [timestep, setDensityData, setLoading, setError]);
}
