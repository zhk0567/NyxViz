import { useEffect, useState } from 'react';
import { VideoDashboard } from '@/dashboard/VideoDashboard';
import { loadTimelineStats } from '@/data/nyxLoader';
import { loadVideoStats, type VideoStatsBundle } from '@/data/statsLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useTimelineVolumePreload } from '@/hooks/useTimelineVolumePreload';
import { useAppStore } from '@/store/useAppStore';
import { isStaticFiguresOnly } from '@/config/publicPaths';
import type { TimelineData } from '@/data/types';

const EMPTY_STATS: VideoStatsBundle = {
  renderSpec: null,
  validationExtended: null,
  brushValidation: null,
};

export function VideoApp() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [videoStats, setVideoStats] = useState<VideoStatsBundle>(EMPTY_STATS);
  const [initError, setInitError] = useState<string | null>(null);

  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);

  useNyxTimestep();
  useTimelineVolumePreload(!isStaticFiguresOnly());

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
      videoStats={videoStats}
    />
  );
}
