import { useEffect, useState } from 'react';
import { VideoDashboard } from '@/dashboard/VideoDashboard';
import { loadTimelineStats, prefetchTimestepQuiet } from '@/data/nyxLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';

export function VideoApp() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);

  useNyxTimestep();

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  useEffect(() => {
    prefetchTimestepQuiet(99);
  }, []);

  if (initError) {
    return (
      <div className="app-error">
        <h1>Nyx 录屏三栏</h1>
        <p>{initError}</p>
      </div>
    );
  }

  if (!timeline) {
    return <div className="app-loading">加载统计数据…</div>;
  }

  return (
    <VideoDashboard
      timeline={timeline}
      densityData={densityData}
      loading={loading}
      error={error}
    />
  );
}
