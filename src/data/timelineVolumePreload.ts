import {
  hasTimestepCached,
  isVtkScalarsCached,
  loadTimestep,
  prewarmVtkScalarsQuiet,
} from '@/data/nyxLoader';
import { TIMESTEP_COUNT } from '@/data/types';
import { VIDEO_WARM_TIMESTEPS } from '@/video/sceneRegistry';

let warmPreloadComplete = false;
let preloadStarted = false;

export function isTimelineVolumePreloadComplete(): boolean {
  return warmPreloadComplete;
}

export function isTimestepVolumeReady(timestep: number): boolean {
  return hasTimestepCached(timestep) && isVtkScalarsCached(timestep);
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

/** 空闲时仅预载关键帧 dat，VTK 由点击/换步按需触发 */
export function startTimelineVolumePreload(): void {
  if (preloadStarted) return;
  preloadStarted = true;

  const order = VIDEO_WARM_TIMESTEPS.filter(
    (t) => t >= 0 && t < TIMESTEP_COUNT,
  );

  const run = async () => {
    for (const t of order) {
      if (document.hidden) {
        await delay(1500);
        continue;
      }
      try {
        if (!hasTimestepCached(t)) {
          const data = await loadTimestep(t);
          prewarmVtkScalarsQuiet(t, data);
        } else if (!isVtkScalarsCached(t)) {
          const data = await loadTimestep(t);
          prewarmVtkScalarsQuiet(t, data);
        }
      } catch {
        /* ignore */
      }
      await delay(600);
    }
    warmPreloadComplete = true;
  };

  const kick = () => void run();
  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback(kick, { timeout: 8000 });
  } else {
    window.setTimeout(kick, 3000);
  }
}

/** 按需：dat + 单 Worker VTK（与 VolumeScene 共享 inflight） */
export function prewarmTimestepQuiet(timestep: number): void {
  if (isTimestepVolumeReady(timestep)) return;
  void loadTimestep(timestep)
    .then((data) => prewarmVtkScalarsQuiet(timestep, data))
    .catch(() => {});
}
