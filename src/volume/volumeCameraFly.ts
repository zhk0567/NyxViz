import type vtkCamera from '@kitware/vtk.js/Rendering/Core/Camera';

export interface CameraState {
  position: [number, number, number];
  focalPoint: [number, number, number];
  viewUp: [number, number, number];
  parallelScale: number;
}

let flyRafId = 0;

export function cancelFlyAnimation(): void {
  if (flyRafId) {
    cancelAnimationFrame(flyRafId);
    flyRafId = 0;
  }
}

export function captureCameraState(camera: vtkCamera): CameraState {
  return {
    position: camera.getPosition() as [number, number, number],
    focalPoint: camera.getFocalPoint() as [number, number, number],
    viewUp: camera.getViewUp() as [number, number, number],
    parallelScale: camera.getParallelScale(),
  };
}

export function restoreCameraState(camera: vtkCamera, state: CameraState): void {
  camera.setPosition(...state.position);
  camera.setFocalPoint(...state.focalPoint);
  camera.setViewUp(...state.viewUp);
  camera.setParallelScale(state.parallelScale);
}

function lerp3(
  a: [number, number, number],
  b: [number, number, number],
  t: number,
): [number, number, number] {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export interface FlyOptions {
  homeDistance: number;
  focusDistanceFactor?: number;
  durationMs?: number;
  /** Cap animation render rate (default 60). */
  maxFps?: number;
  onFrame?: () => void;
  onComplete?: () => void;
}

export interface FlyStateOptions {
  durationMs?: number;
  maxFps?: number;
  onFrame?: () => void;
  onComplete?: () => void;
}

function scheduleFlyTick(
  t0: number,
  durationMs: number,
  maxFps: number,
  onStep: (eased: number) => void,
  onFrame?: () => void,
  onComplete?: () => void,
): void {
  let lastFrame = 0;
  const minInterval = maxFps > 0 ? 1000 / maxFps : 0;

  const tick = (now: number) => {
    if (minInterval > 0 && now - lastFrame < minInterval) {
      flyRafId = requestAnimationFrame(tick);
      return;
    }
    lastFrame = now;

    const raw = Math.min(1, (now - t0) / durationMs);
    const t = easeOutCubic(raw);
    onStep(t);
    onFrame?.();

    if (raw < 1) {
      flyRafId = requestAnimationFrame(tick);
    } else {
      flyRafId = 0;
      onComplete?.();
    }
  };

  flyRafId = requestAnimationFrame(tick);
}

/** Smoothly fly camera to focus on target while preserving view direction. */
export function flyCameraToPoint(
  camera: vtkCamera,
  target: [number, number, number],
  opts: FlyOptions,
): void {
  cancelFlyAnimation();

  const factor = opts.focusDistanceFactor ?? 0.32;
  const durationMs = opts.durationMs ?? 450;
  const maxFps = opts.maxFps ?? 60;
  const start = captureCameraState(camera);

  const viewDir: [number, number, number] = [
    start.position[0] - start.focalPoint[0],
    start.position[1] - start.focalPoint[1],
    start.position[2] - start.focalPoint[2],
  ];
  const viewLen = Math.hypot(viewDir[0], viewDir[1], viewDir[2]) || 1;
  const dir: [number, number, number] = [
    viewDir[0] / viewLen,
    viewDir[1] / viewLen,
    viewDir[2] / viewLen,
  ];

  const newDistance = opts.homeDistance * factor;
  const endFocal = target;
  const endPos: [number, number, number] = [
    target[0] + dir[0] * newDistance,
    target[1] + dir[1] * newDistance,
    target[2] + dir[2] * newDistance,
  ];

  const t0 = performance.now();

  scheduleFlyTick(
    t0,
    durationMs,
    maxFps,
    (t) => {
      camera.setFocalPoint(...lerp3(start.focalPoint, endFocal, t));
      camera.setPosition(...lerp3(start.position, endPos, t));
      camera.setViewUp(...start.viewUp);
    },
    opts.onFrame,
    opts.onComplete,
  );
}

/** Animate from current camera back to saved home state. */
export function flyCameraToState(
  camera: vtkCamera,
  home: CameraState,
  opts: FlyStateOptions,
): void {
  cancelFlyAnimation();

  const durationMs = opts.durationMs ?? 400;
  const maxFps = opts.maxFps ?? 60;
  const start = captureCameraState(camera);
  const t0 = performance.now();

  scheduleFlyTick(
    t0,
    durationMs,
    maxFps,
    (t) => {
      camera.setFocalPoint(...lerp3(start.focalPoint, home.focalPoint, t));
      camera.setPosition(...lerp3(start.position, home.position, t));
      camera.setViewUp(...lerp3(start.viewUp, home.viewUp, t));
      camera.setParallelScale(
        start.parallelScale + (home.parallelScale - start.parallelScale) * t,
      );
    },
    opts.onFrame,
    opts.onComplete,
  );
}
