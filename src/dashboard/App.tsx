import { useEffect, useState } from 'react';
import { DashboardCore } from '@/dashboard/DashboardCore';
import { loadTimelineStats } from '@/data/nyxLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';
import './dashboard.css';

export function App() {
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

  if (initError) {
    return (
      <div className="app-error">
        <h1>Nyx 可视化</h1>
        <p>{initError}</p>
        <p>
          请先运行: <code>python run.py</code>
        </p>
      </div>
    );
  }

  if (!timeline) {
    return <div className="app-loading">加载统计数据…</div>;
  }

  return (
    <DashboardCore
      timeline={timeline}
      densityData={densityData}
      loading={loading}
      error={error}
    />
  );
}
