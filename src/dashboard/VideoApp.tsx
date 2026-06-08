import { useEffect, useState } from 'react';
import { VideoDashboard } from '@/dashboard/VideoDashboard';
import { VIDEO_WARM_TIMESTEPS } from '@/video/sceneRegistry';
import { loadTimelineStats, loadTimestep, prefetchTimestepQuiet } from '@/data/nyxLoader';
import { getVtkScalarsAsync } from '@/data/vtkConvert';
import { loadVideoStats, type VideoStatsBundle } from '@/data/statsLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useAppStore } from '@/store/useAppStore';
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

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
    loadVideoStats().then(setVideoStats);
  }, []);

  useEffect(() => {
    for (const t of VIDEO_WARM_TIMESTEPS) prefetchTimestepQuiet(t);
    void loadTimestep(99).then((data) => {
      void getVtkScalarsAsync(99, data);
    });
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
