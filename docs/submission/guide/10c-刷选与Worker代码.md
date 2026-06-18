# 10c · 刷选与 Worker 代码

[← 10 答辩代码讲解](./10-答辩代码讲解.md) · [← 主索引](../NyxViz_零基础完全解读.md)

---

## useAppStore.ts

**路径**：[`src/store/useAppStore.ts`](../../../src/store/useAppStore.ts)

**职责**：Zustand 全局状态：timestep、brushRange、densityData、tfParams。

**为什么选这段**：三栏联动的唯一状态源。

```5:37:src/store/useAppStore.ts
interface AppState {
  timestep: number;
  densityData: Float32Array | null;
  loading: boolean;
  error: string | null;
  brushRange: BrushRange | null;
  brushedCount: number;
  tfParams: TfParams;
  setTimestep: (t: number) => void;
  setDensityData: (data: Float32Array | null) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setBrushRange: (range: BrushRange | null) => void;
  setBrushedCount: (n: number) => void;
  setTfParams: (params: TfParams) => void;
}

export const useAppStore = create<AppState>((set) => ({
  timestep: 0,
  densityData: null,
  loading: false,
  error: null,
  brushRange: null,
  brushedCount: 0,
  tfParams: { opacityScale: 0.85, densityGain: -0.15, highlightBoost: 1.35 },
  setTimestep: (timestep) => set({ timestep }),
  setDensityData: (densityData) => set({ densityData }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setBrushRange: (brushRange) => set({ brushRange }),
  setBrushedCount: (brushedCount) => set({ brushedCount }),
  setTfParams: (tfParams) => set({ tfParams }),
}));
```

**输入 / 输出**：各组件 set/get → 同步 UI

**答辩 30 秒**：刷选区间、当前步、体数据都放在 store，体渲染和直方图只订阅不互传 props。
## brushPreset.ts

**路径**：[`src/data/brushPreset.ts`](../../../src/data/brushPreset.ts)

**职责**：Top 1% / Filament / Bottom 1% 预设区间定义与匹配。

**为什么选这段**：点按钮刷选的实现入口。

```1:60:src/data/brushPreset.ts
import type { BrushRange, DensityStats } from '@/data/types';

export type BrushPresetId = 'top' | 'filament' | 'bottom';

const REL_EPS = 1e-4;
const ABS_EPS = 1e-3;

function near(a: number, b: number): boolean {
  const scale = Math.max(Math.abs(a), Math.abs(b), 1);
  return Math.abs(a - b) <= Math.max(ABS_EPS, scale * REL_EPS);
}

function rangeMatches(
  brush: BrushRange,
  min: number,
  max: number,
): boolean {
  return near(brush.min, min) && near(brush.max, max);
}

export function matchBrushPreset(
  stats: DensityStats | undefined,
  brushRange: BrushRange | null,
): BrushPresetId | null {
  if (!stats || !brushRange) return null;

  if (rangeMatches(brushRange, stats.p99, stats.max)) return 'top';
  if (rangeMatches(brushRange, stats.p90, stats.p99)) return 'filament';
  if (rangeMatches(brushRange, stats.min, stats.p01)) return 'bottom';
  return null;
}
```

**输入 / 输出**：stats 分位数 → BrushRange

**答辩 30 秒**：预设不是手填数字，而是用当前步 p99、p01、p90 等算密度区间。
## useDashboardInteraction.ts — 预设刷选

**路径**：[`src/dashboard/useDashboardInteraction.ts`](../../../src/dashboard/useDashboardInteraction.ts)

**职责**：`applyTop1` 等回调写 brushRange 并算精确 KPI。

**为什么选这段**：答辩联动逻辑最集中文件。

```156:172:src/dashboard/useDashboardInteraction.ts
  const applyTop1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p99, max: stats.max });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.min, max: stats.p01 });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);

  const applyFilament = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p90, max: stats.p99 });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);
```

**输入 / 输出**：preset id + stats → setBrushRange + brushedCount

**答辩 30 秒**：点 Top 1% 时直接用 tailMassAboveP99 乘体素总数得精确计数，不走采样。
## useDashboardInteraction.ts — Worker 扫描

**路径**：[`src/dashboard/useDashboardInteraction.ts`](../../../src/dashboard/useDashboardInteraction.ts)

**职责**：自定义 brush 时调 scanBrushRangeAsync。

**为什么选这段**：解释 KPI 采样与全场高亮的区别。

```203:237:src/dashboard/useDashboardInteraction.ts
    const preset = matchBrushPreset(stats, brushRange);
    const exactCount = preset ? exactPresetBrushCount(stats, preset) : null;
    if (exactCount != null) {
      setBrushedCount(exactCount);
      setScanning(false);
      prevBrushRef.current = { min: brushRange.min, max: brushRange.max };
      return;
    }

    const sameBrush =
      prevBrushRef.current?.min === brushRange.min &&
      prevBrushRef.current?.max === brushRange.max;
    prevBrushRef.current = brushRange;

    let cancelled = false;
    setScanning(true);
    const delay = sameBrush ? 450 : 180;

    const handle = window.setTimeout(() => {
      scanBrushRangeAsync(densityData, brushRange.min, brushRange.max, 8000)
        .then((found) => {
          if (!cancelled) {
            setBrushedCount(found.length);
            setScanning(false);
          }
        })
        .catch(() => {
          if (!cancelled) setScanning(false);
        });
    }, delay);

    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
```

**输入 / 输出**：densityData + range → brushedCount（采样）

**答辩 30 秒**：宽区间拖拽时 Worker stride 扫描，maxPoints 8000 早停；预设仍用 JSON 精确值。
## useDashboardInteraction.ts — highlight 导出

**路径**：[`src/dashboard/useDashboardInteraction.ts`](../../../src/dashboard/useDashboardInteraction.ts)

**职责**：brushRange 转 highlightMin/Max 给 VolumeScene。

**为什么选这段**：连接 store 与体渲染。

```240:243:src/dashboard/useDashboardInteraction.ts
  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);
```

**输入 / 输出**：brushRange → { highlightMin, highlightMax }

**答辩 30 秒**：useMemo 把 store 区间转成传递函数参数，体渲染和投影读同一份。
## brushScan.ts

**路径**：[`src/data/brushScan.ts`](../../../src/data/brushScan.ts)

**职责**：封装 brushScan.worker 的 Promise API。

**为什么选这段**：主线程不阻塞。

```1:45:src/data/brushScan.ts
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

    void id;
    const copy = new Float32Array(data);
    w.postMessage(
      {
        buffer: copy.buffer,
        minDensity,
```

**输入 / 输出**：buffer + min/max → Promise<points[]>

**答辩 30 秒**：把 Float32Array 传给 Worker，返回刷选到的体素坐标列表用于 KPI。
## brushEstimate.ts

**路径**：[`src/data/brushEstimate.ts`](../../../src/data/brushEstimate.ts)

**职责**：无体数据时用直方图积分估计刷选计数。

**为什么选这段**：静态图模式 fallback。

```1:40:src/data/brushEstimate.ts
import * as d3 from 'd3';
import type { BrushRange, TimelineData } from '@/data/types';
import { VOXEL_COUNT } from '@/data/types';

/** Static-mode fallback: estimate brushed voxel count from precomputed histogram bins. */
export function estimateBrushCountFromHistogram(
  timeline: TimelineData,
  timestep: number,
  brushRange: BrushRange,
): number {
  const hist = timeline.histograms[timestep];
  if (!hist?.length) return 0;

  const edges = timeline.logBinEdges;
  let mass = 0;
  for (let i = 0; i < hist.length; i++) {
    const lo = edges[i]!;
    const hi = edges[i + 1]!;
    if (hi < brushRange.min || lo > brushRange.max) continue;
    const center = Math.sqrt(lo * hi);
    if (center >= brushRange.min && center <= brushRange.max) {
      mass += hist[i]!;
    }
  }
  const total = d3.sum(hist) || 1;
  return Math.round((mass / total) * VOXEL_COUNT);
}
```

**输入 / 输出**：histogram + range → 估计体素数

**答辩 30 秒**：只有 JSON 没有 .dat 时，对 bin 概率质量积分估计占比。
## brushScan.worker.ts

**路径**：[`src/workers/brushScan.worker.ts`](../../../src/workers/brushScan.worker.ts)

**职责**：三重循环 stride 扫描 + maxPoints 早停。

**为什么选这段**：文件短且逻辑完整，适合现场读代码。

```1:42:src/workers/brushScan.worker.ts
import { GRID_SIZE } from '../data/types';

export interface BrushScanRequest {
  buffer: ArrayBuffer;
  minDensity: number;
  maxDensity: number;
  maxPoints: number;
}

export interface BrushScanPoint {
  x: number;
  y: number;
  z: number;
  density: number;
}

export interface BrushScanResponse {
  points: BrushScanPoint[];
}

self.onmessage = (ev: MessageEvent<BrushScanRequest>) => {
  const { buffer, minDensity, maxDensity, maxPoints } = ev.data;
  const data = new Float32Array(buffer);
  const points: BrushScanPoint[] = [];
  const stride = maxPoints < 20000 ? 2 : 1;

  outer: for (let x = 0; x < GRID_SIZE; x += stride) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y += stride) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z += stride) {
        const density = data[yOff + z]!;
        if (density >= minDensity && density <= maxDensity) {
          points.push({ x, y, z, density });
          if (points.length >= maxPoints) break outer;
        }
      }
    }
  }

  self.postMessage({ points } satisfies BrushScanResponse);
};
```

**输入 / 输出**：ArrayBuffer + 阈值 → points[]

**答辩 30 秒**：三层 for 遍历 128³，密度落在区间内就 push，达到 maxPoints 立即 break。
## projectionAsync.ts

**路径**：[`src/data/projectionAsync.ts`](../../../src/data/projectionAsync.ts)

**职责**：调度 projection.worker 做 XY 最大密度投影。

**为什么选这段**：BandPreviewCanvas 的数据源。

```1:42:src/data/projectionAsync.ts
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
```

**输入 / 输出**：体数据 + axis → Promise<投影数组>

**答辩 30 秒**：投影在 Worker 里做 max-intensity，主线程只贴 Canvas。
## projection.worker.ts

**路径**：[`src/workers/projection.worker.ts`](../../../src/workers/projection.worker.ts)

**职责**：沿 z 轴取最大密度得到 128×128 投影。

**为什么选这段**：金斑高亮的 2D 来源。

```1:55:src/workers/projection.worker.ts
import { GRID_SIZE } from '../data/types';

export interface ProjectionRequest {
  id: number;
  buffer: ArrayBuffer;
  axis: 'xy' | 'xz' | 'yz';
}

export interface ProjectionResponse {
  id: number;
  buffer: ArrayBuffer;
}

self.onmessage = (ev: MessageEvent<ProjectionRequest>) => {
  const { id, buffer, axis } = ev.data;
  const data = new Float32Array(buffer);
  const size = GRID_SIZE * GRID_SIZE;
  const out = new Float32Array(size);
  out.fill(-Infinity);

  for (let x = 0; x < GRID_SIZE; x++) {
    const xOff = x * GRID_SIZE * GRID_SIZE;
    for (let y = 0; y < GRID_SIZE; y++) {
      const yOff = xOff + y * GRID_SIZE;
      for (let z = 0; z < GRID_SIZE; z++) {
        const v = data[yOff + z]!;
        let u: number;
        if (axis === 'xy') u = x + y * GRID_SIZE;
        else if (axis === 'xz') u = x + z * GRID_SIZE;
        else u = y + z * GRID_SIZE;
        if (v > out[u]!) out[u] = v;
      }
    }
  }

  for (let i = 0; i < size; i++) {
    if (!Number.isFinite(out[i]!)) out[i] = 0;
  }

  self.postMessage({ id, buffer: out.buffer } satisfies ProjectionResponse, [
    out.buffer,
  ]);
};
```

**输入 / 输出**：体数据 buffer → 投影 buffer

**答辩 30 秒**：每个 (x,y) 在 z 方向取 max，得到与体渲染一致的 XY 视图。
