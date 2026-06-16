import { convertZFastToVtk } from './vtkLayout';

let jobId = 0;
const vtkByTimestep = new Map<number, Float32Array>();
const vtkByZFast = new WeakMap<Float32Array, Float32Array>();
const pendingByTimestep = new Map<number, Promise<Float32Array>>();

const MAX_VTK_TIMESTEP_CACHE = 12;

let worker: Worker | null = null;
const jobCallbacks = new Map<
  number,
  {
    resolve: (v: Float32Array) => void;
    reject: (e: unknown) => void;
    timestep: number;
    zFast: Float32Array;
  }
>();

function touchVtkTimestepCache(timestep: number, scalars: Float32Array): void {
  if (vtkByTimestep.has(timestep)) vtkByTimestep.delete(timestep);
  vtkByTimestep.set(timestep, scalars);
  while (vtkByTimestep.size > MAX_VTK_TIMESTEP_CACHE) {
    const oldest = vtkByTimestep.keys().next().value;
    if (oldest === undefined) break;
    vtkByTimestep.delete(oldest);
  }
}

function ensureWorker(): Worker {
  if (worker) return worker;
  worker = new Worker(
    new URL('../workers/vtkConvert.worker.ts', import.meta.url),
    { type: 'module' },
  );
  worker.addEventListener('message', (ev: MessageEvent<{ id: number; buffer: ArrayBuffer }>) => {
    const cb = jobCallbacks.get(ev.data.id);
    if (!cb) return;
    jobCallbacks.delete(ev.data.id);
    const out = new Float32Array(ev.data.buffer);
    touchVtkTimestepCache(cb.timestep, out);
    vtkByZFast.set(cb.zFast, out);
    cb.resolve(out);
  });
  worker.addEventListener('error', (ev) => {
    worker = null;
    for (const [, cb] of jobCallbacks) {
      cb.reject(ev.error ?? new Error('vtkConvert worker failed'));
    }
    jobCallbacks.clear();
  });
  return worker;
}

function convertZFastToVtkSync(timestep: number, zFast: Float32Array): Float32Array {
  const out = convertZFastToVtk(zFast);
  touchVtkTimestepCache(timestep, out);
  vtkByZFast.set(zFast, out);
  return out;
}

function enqueueConvert(timestep: number, zFast: Float32Array): Promise<Float32Array> {
  const cached = getCachedVtkScalars(timestep, zFast);
  if (cached) return Promise.resolve(cached);

  const inflight = pendingByTimestep.get(timestep);
  if (inflight) return inflight;

  const promise = new Promise<Float32Array>((resolve, reject) => {
    const id = ++jobId;
    jobCallbacks.set(id, { resolve, reject, timestep, zFast });
    try {
      const copy = new Float32Array(zFast);
      ensureWorker().postMessage({ id, buffer: copy.buffer }, [copy.buffer]);
    } catch (err) {
      jobCallbacks.delete(id);
      reject(err);
    }
  })
    .catch(() => convertZFastToVtkSync(timestep, zFast))
    .finally(() => {
      pendingByTimestep.delete(timestep);
    });

  pendingByTimestep.set(timestep, promise);
  return promise;
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

export function isVtkScalarsCached(timestep: number): boolean {
  return vtkByTimestep.has(timestep);
}

export function getVtkScalarsAsync(
  timestep: number,
  zFast: Float32Array,
): Promise<Float32Array> {
  return enqueueConvert(timestep, zFast);
}

/** 仅当 Worker 结果已缓存时同步读取，否则返回 null */
export function getVtkScalars(zFast: Float32Array): Float32Array | null {
  return vtkByZFast.get(zFast) ?? null;
}

export const toVtkScalars = getVtkScalars;

export function prewarmVtkScalarsQuiet(
  timestep: number,
  zFast: Float32Array,
): void {
  if (getCachedVtkScalars(timestep, zFast)) return;
  void enqueueConvert(timestep, zFast).catch(() => {});
}
