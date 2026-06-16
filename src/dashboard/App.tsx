import { useEffect, useState } from 'react';
import { DashboardCore } from '@/dashboard/DashboardCore';
import { loadTimelineStats } from '@/data/nyxLoader';
import { loadVideoStats, type VideoStatsBundle } from '@/data/statsLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useTimelineVolumePreload } from '@/hooks/useTimelineVolumePreload';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';
import './dashboard.css';

const EMPTY_VIDEO_STATS: VideoStatsBundle = {
  renderSpec: null,
  validationExtended: null,
  brushValidation: null,
};

export function App() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [videoStats, setVideoStats] = useState<VideoStatsBundle>(EMPTY_VIDEO_STATS);
  const [initError, setInitError] = useState<string | null>(null);

  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);

  useNyxTimestep();
  useTimelineVolumePreload(true);

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
    loadVideoStats().then(setVideoStats);
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
      videoStats={videoStats}
    />
  );
}
