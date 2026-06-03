import { useEffect, useState } from 'react';
import { DashboardCore } from '@/dashboard/DashboardCore';
import { loadTimestep, loadTimelineStats } from '@/data/nyxLoader';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';
import '@/dashboard/dashboard.css';

export function InteractiveShowcase() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);
  const setDensityData = useAppStore((s) => s.setDensityData);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const embedded = (
      window as unknown as { __NYX_EMBEDDED_TIMESTEPS__?: Record<number, Float32Array> }
    ).__NYX_EMBEDDED_TIMESTEPS__;

    const load = embedded?.[timestep]
      ? Promise.resolve(embedded[timestep]!)
      : loadTimestep(timestep);

    load
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

  if (initError) {
    return <p className="badge error">{initError}</p>;
  }
  if (!timeline) {
    return <p className="app-loading">加载统计数据…</p>;
  }

  return (
    <DashboardCore
      timeline={timeline}
      densityData={densityData}
      loading={loading}
      error={error}
      embedded
    />
  );
}
