import { useEffect } from 'react';
import { startTimelineVolumePreload } from '@/data/timelineVolumePreload';

/** 空闲时预载关键帧 dat，不占用启动主线程 */
export function useTimelineVolumePreload(enabled = true) {
  useEffect(() => {
    if (!enabled) return;
    startTimelineVolumePreload();
  }, [enabled]);
}
