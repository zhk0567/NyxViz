import { GRID_SIZE, VOXEL_COUNT } from './types';

let worker: Worker | null = null;
let jobId = 0;
const vtkByTimestep = new Map<number, Float32Array>();
const vtkByZFast = new WeakMap<Float32Array, Float32Array>();
const pending = new Map<number, Promise<Float32Array>>();

function getWorker(): Worker {
  if (!worker) {
    worker = new Worker(
      new URL('../workers/vtkConvert.worker.ts', import.meta.url),
      { type: 'module' },
    );
  }
  return worker;
}

function convertOnMainThread(zFast: Float32Array): Float32Array {
  const hit = vtkByZFast.get(zFast);
  if (hit) return hit;
  const out = new Float32Array(VOXEL_COUNT);
  for (let x = 0; x < GRID_SIZE; x++) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y++) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z++) {
        const zIdx = yOff + z;
        const vtkIdx = x + GRID_SIZE * (y + GRID_SIZE * z);
        out[vtkIdx] = zFast[zIdx]!;
      }
    }
  }
  vtkByZFast.set(zFast, out);
  return out;
}

export function getCachedVtkScalars(
  timestep: number,
  zFast?: Float32Array,
): Float32Array | undefined {
  const byStep = vtkByTimestep.get(timestep);
  if (byStep) return byStep;
  if (zFast) return vtkByZFast.get(zFast);
  return undefined;
}

export function getVtkScalarsAsync(
  timestep: number,
  zFast: Float32Array,
): Promise<Float32Array> {
  const cached = getCachedVtkScalars(timestep, zFast);
  if (cached) return Promise.resolve(cached);

  const inflight = pending.get(timestep);
  if (inflight) return inflight;

  const promise = new Promise<Float32Array>((resolve, reject) => {
    const id = ++jobId;
    const w = getWorker();
    const copy = new Float32Array(zFast);

    const onMessage = (ev: MessageEvent<{ id: number; buffer: ArrayBuffer }>) => {
      if (ev.data.id !== id) return;
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      const out = new Float32Array(ev.data.buffer);
      vtkByTimestep.set(timestep, out);
      vtkByZFast.set(zFast, out);
      pending.delete(timestep);
      resolve(out);
    };
    const onError = () => {
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      pending.delete(timestep);
      try {
        const out = convertOnMainThread(zFast);
        vtkByTimestep.set(timestep, out);
        resolve(out);
      } catch (e) {
        reject(e);
      }
    };

    w.addEventListener('message', onMessage);
    w.addEventListener('error', onError);
    w.postMessage({ id, buffer: copy.buffer }, [copy.buffer]);
  });

  pending.set(timestep, promise);
  return promise;
}

/** Synchronous path — only if worker result already cached. */
export function getVtkScalars(zFast: Float32Array): Float32Array {
  const hit = vtkByZFast.get(zFast);
  if (hit) return hit;
  return convertOnMainThread(zFast);
}

export const toVtkScalars = getVtkScalars;

export function prewarmVtkScalarsQuiet(
  timestep: number,
  zFast: Float32Array,
): void {
  if (getCachedVtkScalars(timestep, zFast)) return;
  void getVtkScalarsAsync(timestep, zFast).catch(() => {});
}
