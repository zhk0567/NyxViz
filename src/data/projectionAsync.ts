import type { ProjectionAxis } from './nyxLoader';
import { computeMaxProjection } from './nyxLoader';

let worker: Worker | null = null;
let jobId = 0;
const projCache = new WeakMap<
  Float32Array,
  Map<ProjectionAxis, Float32Array>
>();
const inflight = new WeakMap<
  Float32Array,
  Map<ProjectionAxis, Promise<Float32Array>>
>();

function getWorker(): Worker {
  if (!worker) {
    worker = new Worker(
      new URL('../workers/projection.worker.ts', import.meta.url),
      { type: 'module' },
    );
  }
  return worker;
}

export function computeMaxProjectionAsync(
  data: Float32Array,
  axis: ProjectionAxis,
): Promise<Float32Array> {
  let perAxis = projCache.get(data);
  if (!perAxis) {
    perAxis = new Map();
    projCache.set(data, perAxis);
  }
  const hit = perAxis.get(axis);
  if (hit) return Promise.resolve(hit);

  let perInflight = inflight.get(data);
  if (!perInflight) {
    perInflight = new Map();
    inflight.set(data, perInflight);
  }
  const pending = perInflight.get(axis);
  if (pending) return pending;

  const promise = new Promise<Float32Array>((resolve, reject) => {
    const id = ++jobId;
    const w = getWorker();
    const copy = new Float32Array(data);

    const onMessage = (ev: MessageEvent<{ id: number; buffer: ArrayBuffer }>) => {
      if (ev.data.id !== id) return;
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      const out = new Float32Array(ev.data.buffer);
      perAxis!.set(axis, out);
      perInflight!.delete(axis);
      resolve(out);
    };
    const onError = () => {
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      perInflight!.delete(axis);
      try {
        const out = computeMaxProjection(data, axis);
        perAxis!.set(axis, out);
        resolve(out);
      } catch (e) {
        reject(e);
      }
    };

    w.addEventListener('message', onMessage);
    w.addEventListener('error', onError);
    w.postMessage({ id, buffer: copy.buffer, axis }, [copy.buffer]);
  });

  perInflight.set(axis, promise);
  return promise;
}
