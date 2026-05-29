import type { BrushedVoxel } from './types';

let worker: Worker | null = null;
let jobId = 0;

function getWorker(): Worker {
  if (!worker) {
    worker = new Worker(
      new URL('../workers/brushScan.worker.ts', import.meta.url),
      { type: 'module' },
    );
  }
  return worker;
}

export function scanBrushRangeAsync(
  data: Float32Array,
  minDensity: number,
  maxDensity: number,
  maxPoints = 12000,
): Promise<BrushedVoxel[]> {
  return new Promise((resolve, reject) => {
    const w = getWorker();
    const id = ++jobId;

    const onMessage = (ev: MessageEvent<{ points: BrushedVoxel[] }>) => {
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      resolve(ev.data.points);
    };
    const onError = (err: ErrorEvent) => {
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
      reject(err.error ?? new Error('brush scan worker failed'));
    };

    w.addEventListener('message', onMessage);
    w.addEventListener('error', onError);

    const copy = data.slice();
    void id;
    w.postMessage(
      {
        buffer: copy.buffer,
        minDensity,
        maxDensity,
        maxPoints,
      },
      [copy.buffer],
    );
  });
}
