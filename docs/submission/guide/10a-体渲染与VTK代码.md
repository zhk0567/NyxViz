# 10a · 体渲染与 VTK 代码

[← 10 答辩代码讲解](./10-答辩代码讲解.md) · [← 主索引](../NyxViz_零基础完全解读.md)

---

## 数据流总览

```mermaid
sequenceDiagram
  participant dat as Nyx_dat
  participant loader as nyxLoader
  participant worker as vtkConvert_worker
  participant vtk as VolumeScene
  participant tf as transferFunction
  dat --> loader --> worker --> vtk
  tf --> vtk
```

---

## nyxLoader.ts — 加载 .dat

**路径**：[`src/data/nyxLoader.ts`](../../../src/data/nyxLoader.ts)

**职责**：从 `public/Nyx/` fetch 单步 128³ float32，z-fast 布局缓存。

**为什么选这段**：答辩「数据从哪来」必指 `flatIndex` 与 `loadTimestep`。

```9:12:src/data/nyxLoader.ts
/** z-fastest layout: flatIndex = z + GRID_SIZE * y + GRID_SIZE^2 * x */
export function flatIndex(x: number, y: number, z: number): number {
  return z + GRID_SIZE * y + GRID_SIZE * GRID_SIZE * x;
}
```

**输入 / 输出**：输入 URL → 输出 `Float32Array`（2,097,152）

**答辩 30 秒**：赛题 `.dat` 按 z 最快顺序存储，我们用 `flatIndex` 做索引，fetch 后缓存在 Map 里避免重复下载。
## nyxLoader.ts — loadTimestep

**路径**：[`src/data/nyxLoader.ts`](../../../src/data/nyxLoader.ts)

**职责**：异步加载并校验体素数量。

**为什么选这段**：展示 fetch → ArrayBuffer → Float32Array 完整链路。

```71:88:src/data/nyxLoader.ts
export async function loadTimestep(timestep: number): Promise<Float32Array> {
  const cached = getTimestepFromCache(timestep);
  if (cached) return cached;

  const url = timestepUrl(timestep);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength !== VOXEL_COUNT * 4) {
    throw new Error(
      `Unexpected file size for ${url}: ${buffer.byteLength} bytes`,
    );
  }
  const data = new Float32Array(buffer);
  touchTimestepCache(timestep, data);
  return data;
```

**输入 / 输出**：timestep 整数 → Promise<Float32Array>

**答辩 30 秒**：换时间步就是换 URL 拉 4MB 左右的二进制，校验长度必须是 128³。
## vtkLayout.ts — 轴重排

**路径**：[`src/data/vtkLayout.ts`](../../../src/data/vtkLayout.ts)

**职责**：预计算 z-fast → vtk x-fast 索引表，Worker 与主线程共用。

**为什么选这段**：解释 Worker 只做重排、不做科学计算。

```3:20:src/data/vtkLayout.ts
/** z-fastest flat index → vtk i-fastest layout */
const Z_TO_VTK = new Uint32Array(VOXEL_COUNT);
for (let x = 0; x < GRID_SIZE; x++) {
  const xOff = x * GRID_SIZE * GRID_SIZE;
  for (let y = 0; y < GRID_SIZE; y++) {
    const yOff = xOff + y * GRID_SIZE;
    for (let z = 0; z < GRID_SIZE; z++) {
      Z_TO_VTK[yOff + z] = x + GRID_SIZE * (y + GRID_SIZE * z);
    }
  }
}

export function convertZFastToVtk(zFast: Float32Array): Float32Array {
  const out = new Float32Array(VOXEL_COUNT);
  for (let i = 0; i < VOXEL_COUNT; i++) {
    out[Z_TO_VTK[i]!] = zFast[i]!;
  }
  return out;
```

**输入 / 输出**：z-fast Float32Array → vtk 布局 Float32Array

**答辩 30 秒**：赛题是 z-fast，vtk.js 要 i-fast；启动时用三重循环生成 210 万项查找表，转换时 O(n) 拷贝。
## vtkConvert.worker.ts

**路径**：[`src/workers/vtkConvert.worker.ts`](../../../src/workers/vtkConvert.worker.ts)

**职责**：Web Worker 内执行轴重排，避免主线程卡顿。

**为什么选这段**：文件短，整段可读，适合答辩背诵。

```1:20:src/workers/vtkConvert.worker.ts
import { convertZFastToVtk } from '../data/vtkLayout';

export interface VtkConvertRequest {
  id: number;
  buffer: ArrayBuffer;
}

export interface VtkConvertResponse {
  id: number;
  buffer: ArrayBuffer;
}

self.onmessage = (ev: MessageEvent<VtkConvertRequest>) => {
  const { id, buffer } = ev.data;
  const zFast = new Float32Array(buffer);
  const out = convertZFastToVtk(zFast);
  self.postMessage({ id, buffer: out.buffer } satisfies VtkConvertResponse, [
    out.buffer,
  ]);
};
```

**输入 / 输出**：postMessage buffer → 重排后 buffer（transferable）

**答辩 30 秒**：百万体素重排放在 Worker，postMessage 用 transferable 零拷贝回主线程。
## vtkConvert.ts — Worker 调度

**路径**：[`src/data/vtkConvert.ts`](../../../src/data/vtkConvert.ts)

**职责**：主线程管理 Worker 单例、任务队列与按 timestep 缓存。

**为什么选这段**：`ensureWorker` + `enqueueConvert` 是性能关键。

```31:54:src/data/vtkConvert.ts
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
```

**输入 / 输出**：z-fast 数组 → Promise<vtk 标量数组>

**答辩 30 秒**：主线程只调度：有缓存直接返回，否则 postMessage 给 Worker，回调里写入 timestep 缓存。
## colormap.ts — 宇宙色标

**路径**：[`src/viz/colormap.ts`](../../../src/viz/colormap.ts)

**职责**：cosmic / cinematic 色标控制点，TF、Canvas、CSS 图例共用。

**为什么选这段**：保证网页、配图、图例颜色一致。

```6:38:src/viz/colormap.ts
export const COSMIC_COLOR_STOPS: ReadonlyArray<
  readonly [t: number, r: number, g: number, b: number]
> = [
  [0.0, 0.02, 0.03, 0.1],
  [0.15, 0.04, 0.08, 0.28],
  [0.35, 0.12, 0.2, 0.48],
  [0.55, 0.24, 0.55, 0.72],
  [0.72, 0.55, 0.42, 0.78],
  [0.85, 0.85, 0.65, 0.42],
  [1.0, 0.98, 0.92, 0.78],
];

/** Deep-space cinematic colormap — void + nebula + gold filaments. */
export const CINEMATIC_COLOR_STOPS: ReadonlyArray<
  readonly [t: number, r: number, g: number, b: number]
> = [
  [0.0, 0.01, 0.02, 0.06],
  [0.12, 0.02, 0.04, 0.12],
  [0.25, 0.04, 0.07, 0.2],
  [0.45, 0.15, 0.22, 0.55],
  [0.65, 0.35, 0.48, 0.78],
  [0.8, 0.95, 0.72, 0.35],
  [0.88, 1.0, 0.82, 0.42],
  [0.92, 1.0, 0.9, 0.58],
  [0.96, 1.0, 0.96, 0.86],
  [1.0, 1.0, 1.0, 0.96],
];

export type ColormapStyle = 'cosmic' | 'cinematic';

export function getColorStops(style: ColormapStyle = 'cinematic') {
  return style === 'cinematic' ? CINEMATIC_COLOR_STOPS : COSMIC_COLOR_STOPS;
}
```

**输入 / 输出**：归一化 t∈[0,1] → RGB

**答辩 30 秒**：色标不是随便调的，是共享常量；传递函数和 2D 投影都 `sampleColormap`。
## tfDomain.ts — 全局域

**路径**：[`src/viz/tfDomain.ts`](../../../src/viz/tfDomain.ts)

**职责**：交互页固定全域 p01–p99，截图页可用逐步域。

**为什么选这段**：解释条带图与网页颜色差异的根因。

```43:56:src/viz/tfDomain.ts
/** Fixed global domain so all timesteps are comparable (p01–p99 envelope over 100 steps). */
export function getGlobalTfDomain(timeline: TimelineData): TfDomain {
  let min = Infinity;
  let max = -Infinity;
  for (const s of timeline.timesteps) {
    if (s.p01 < min) min = s.p01;
    if (s.p99 > max) max = s.p99;
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    min = timeline.globalMin;
    max = timeline.globalMax;
  }
  return { min, max, useLogScale: true };
}
```

**输入 / 输出**：timeline.json → `{ min, max, useLogScale }`

**答辩 30 秒**：交互演示用百步 p01–p99 包络做 log 域，保证换步可比；截图演化条带另用 `getGlobalMorphCaptureProfile`。
## transferFunction.ts — 刷选高亮透明度

**路径**：[`src/volume/transferFunction.ts`](../../../src/volume/transferFunction.ts)

**职责**：当 `highlightMin/Max` 存在时重写 opacity 控制点，刷选区间更亮。

**为什么选这段**：任务四联动体渲染的核心。

```128:171:src/volume/transferFunction.ts
export function fillOpacityTransferFunction(
  pwf: vtkPiecewiseFunction,
  opts: TransferFunctionOptions,
): void {
  const {
    dataMin,
    dataMax,
    highlightMin,
    highlightMax,
    opacityScale = 1,
    densityGain = 0,
    highlightBoost = 1,
    useLogScale = true,
    visualStyle = 'cinematic',
  } = opts;
  const span = dataMax - dataMin || 1;
  const scale = (v: number) => Math.min(1, v * opacityScale);

  const at = (t: number) => mapT(t, dataMin, dataMax, densityGain, useLogScale);

  pwf.removeAllPoints();

  if (highlightMin !== undefined && highlightMax !== undefined) {
    const boost = highlightBoost;
    const voidOpacity = visualStyle === 'cinematic' ? 0.0 : 0.002;
    pwf.addPoint(dataMin, scale(voidOpacity));
    pwf.addPoint(
      mapDensity(highlightMin - span * 0.008, dataMin, dataMax, useLogScale),
      scale(visualStyle === 'cinematic' ? 0.008 : 0.015),
    );
    pwf.addPoint(
      mapDensity(highlightMin, dataMin, dataMax, useLogScale),
      scale(0.55 * boost),
    );
    pwf.addPoint(
      mapDensity(highlightMax, dataMin, dataMax, useLogScale),
      scale(0.98 * boost),
    );
    pwf.addPoint(
      mapDensity(highlightMax + span * 0.008, dataMin, dataMax, useLogScale),
      scale(visualStyle === 'cinematic' ? 0.08 : 0.15),
    );
    pwf.addPoint(dataMax, scale(visualStyle === 'cinematic' ? 0.04 : 0.15));
    return;
```

**输入 / 输出**：密度域 + brush 区间 → vtk PiecewiseFunction

**答辩 30 秒**：有刷选时不用默认 cinematic 曲线，而是在 highlight 区间把 alpha 拉到 0.55–0.98，void 区几乎透明。
## transferFunction.ts — 组装 CTF/OTF

**路径**：[`src/volume/transferFunction.ts`](../../../src/volume/transferFunction.ts)

**职责**：导出 `buildColorTransferFunction` / `buildOpacityTransferFunction`。

**为什么选这段**：VolumeScene 每次 TF 更新都调这两个工厂。

```181:195:src/volume/transferFunction.ts
export function buildColorTransferFunction(
  opts: TransferFunctionOptions,
): vtkColorTransferFunction {
  const ctf = vtkColorTransferFunction.newInstance();
  fillColorTransferFunction(ctf, opts);
  return ctf;
}

export function buildOpacityTransferFunction(
  opts: TransferFunctionOptions,
): vtkPiecewiseFunction {
  const pwf = vtkPiecewiseFunction.newInstance();
  fillOpacityTransferFunction(pwf, opts);
  return pwf;
}
```

**输入 / 输出**：TransferFunctionOptions → vtk 对象

**答辩 30 秒**：颜色用 cosmic/cinematic 控制点映射到 log 域密度；透明度分标准/电影/刷选三种模式。
## renderSpec.ts — 质量档位

**路径**：[`src/volume/renderSpec.ts`](../../../src/volume/renderSpec.ts)

**职责**：sampleDistance、maximumSamplesPerRay 等 GPU 采样参数。

**为什么选这段**：解释录屏 60fps 与高清静帧的取舍。

```59:90:src/volume/renderSpec.ts
export const VOLUME_QUALITY_PRESETS: Record<
  VolumeQuality,
  {
    sampleDistance: number;
    maximumSamplesPerRay: number;
    shade: boolean;
    ambient: number;
    diffuse: number;
    specular: number;
  }
> = {
  video: {
    // 域长约 14.2；8.0 会导致每射线仅 ~2 次采样，体渲染完全不可见
    sampleDistance: 2.8,
    maximumSamplesPerRay: 320,
    shade: false,
    ambient: 0.2,
    diffuse: 0.55,
    specular: 0.1,
  },
  interactive: {
    sampleDistance: 4.0,
    maximumSamplesPerRay: 512,
    shade: false,
    ambient: 0.2,
    diffuse: 0.55,
    specular: 0.1,
  },
  high: {
    sampleDistance: 1.2,
    maximumSamplesPerRay: 2048,
    shade: true,
```

**输入 / 输出**：quality 字符串 → 采样预设对象

**答辩 30 秒**：video 档降低每射线采样数，interactive 更密，presentation/cinematic 用于静帧和答辩特写。
## VolumeScene.tsx — VTK 管线初始化

**路径**：[`src/volume/VolumeScene.tsx`](../../../src/volume/VolumeScene.tsx)

**职责**：创建 vtkImageData、VolumeMapper、CTF/OTF、三光源。

**为什么选这段**：答辩「怎么画 3D」指这段 useEffect。

```427:461:src/volume/VolumeScene.tsx
    const imageData = vtkImageData.newInstance();
    imageData.setDimensions(GRID_SIZE, GRID_SIZE, GRID_SIZE);
    imageData.setSpacing(SPACING, SPACING, SPACING);
    imageData.setOrigin(0, 0, 0);

    const dataArray = vtkDataArray.newInstance({
      name: 'density',
      numberOfComponents: 1,
      values: new Float32Array(VOXEL_COUNT),
    });
    imageData.getPointData().setScalars(dataArray);

    const mapper = vtkVolumeMapper.newInstance();
    mapper.setInputData(imageData);
    mapper.setAutoAdjustSampleDistances(false);

    const ctf = vtkColorTransferFunction.newInstance();
    const otf = vtkPiecewiseFunction.newInstance();

    const volumeProperty = vtkVolumeProperty.newInstance();
    volumeProperty.setShade(false);
    volumeProperty.setAmbient(0.2);
    volumeProperty.setDiffuse(0.55);
    volumeProperty.setSpecular(0.1);
    volumeProperty.setRGBTransferFunction(0, ctf);
    volumeProperty.setScalarOpacity(0, otf);
    volumeProperty.setScalarOpacityUnitDistance(
      0,
      SPACING * OPACITY_SCALAR_UNIT_DISTANCE,
    );

    const volume = vtkVolume.newInstance();
    volume.setMapper(mapper);
    volume.setProperty(volumeProperty);
    renderer.addVolume(volume);
```

**输入 / 输出**：空体数据 → 完整 vtk 渲染上下文

**答辩 30 秒**：组件挂载时建 vtk 管线：128³ imageData、光线投射 mapper、RGB+opacity 传递函数、Phong 风格多光源。
## VolumeScene.tsx — 交互降采样

**路径**：[`src/volume/VolumeScene.tsx`](../../../src/volume/VolumeScene.tsx)

**职责**：拖动相机时切 interactive/video 采样，静止后恢复。

**为什么选这段**：展示性能优化不是黑魔法。

```289:313:src/volume/VolumeScene.tsx
  const applyTargetSampling = () => {
    const ctx = contextRef.current;
    if (!ctx) return;

    if (flyActiveRef.current) {
      applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);
      return;
    }

    if (interactionActiveRef.current) {
      if (performanceModeRef.current === 'video' || qualityRef.current === 'video') {
        applyStaticSampling(VIDEO_DRAG_SAMPLING);
      } else {
        applyStaticSampling(VOLUME_QUALITY_PRESETS.interactive);
      }
      return;
    }

    if (isFocusedRef.current && adaptivePrecisionRef.current) {
      applyFocusedAdaptiveSampling();
      return;
    }

    applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);
  };
```

**输入 / 输出**：performanceMode + quality → mapper 采样参数

**答辩 30 秒**：拖相机时强制低密度采样，松手后按 quality 档恢复；录屏模式用 VIDEO_DRAG_SAMPLING 常量。
## adaptiveVolumeSampling.ts

**路径**：[`src/volume/adaptiveVolumeSampling.ts`](../../../src/volume/adaptiveVolumeSampling.ts)

**职责**：根据相机 zoom 动态调整 sampleDistance。

**为什么选这段**：聚焦 filament 时提高细节。

```1:42:src/volume/adaptiveVolumeSampling.ts
import type vtkCamera from '@kitware/vtk.js/Rendering/Core/Camera';
import type vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper';
import { VOLUME_QUALITY_PRESETS, type VolumeQuality } from './renderSpec';

export function getCameraDistance(camera: vtkCamera): number {
  const p = camera.getPosition();
  const f = camera.getFocalPoint();
  return Math.hypot(p[0] - f[0], p[1] - f[1], p[2] - f[2]);
}

const VIDEO_ADAPTIVE_CAPS = {
  maxRatio: 2.0,
  minSampleDistance: 1.0,
  maxSamplesCap: 480,
} as const;

/** 放大倍率越高，采样越密，保持屏幕空间精度 */
export function applyAdaptiveVolumeSampling(
  mapper: vtkVolumeMapper,
  quality: VolumeQuality,
  zoomRatio: number,
): void {
  const preset = VOLUME_QUALITY_PRESETS[quality];
  const isVideoLike = quality === 'video' || quality === 'cinematic';
  const maxRatio = isVideoLike ? VIDEO_ADAPTIVE_CAPS.maxRatio : 3.5;
  const minDist =
    quality === 'presentation' && zoomRatio > 1.5
      ? 0.28
      : isVideoLike
        ? VIDEO_ADAPTIVE_CAPS.minSampleDistance
        : 0.35;
  const samplesCap = isVideoLike
    ? quality === 'cinematic'
      ? 640
      : VIDEO_ADAPTIVE_CAPS.maxSamplesCap
    : 6144;
  const ratio = Math.max(1, Math.min(zoomRatio, maxRatio));
  mapper.setSampleDistance(Math.max(minDist, preset.sampleDistance / ratio));
  mapper.setMaximumSamplesPerRay(
    Math.min(samplesCap, Math.round(preset.maximumSamplesPerRay * Math.min(ratio, 2))),
  );
}
```

**输入 / 输出**：mapper + quality + zoomRatio → 修改采样

**答辩 30 秒**：放大时缩短 sample distance，让细丝更清晰；缩小用粗采样保帧率。
## volumeQualityCache.ts

**路径**：[`src/volume/volumeQualityCache.ts`](../../../src/volume/volumeQualityCache.ts)

**职责**：记录某 timestep 是否已达 presentation 画质。

**为什么选这段**：scene 切换时跳过草稿阶段。

```1:14:src/volume/volumeQualityCache.ts
/** 会话级：某时间步已完成 presentation 质量体渲染 */
const presentationReady = new Set<number>();

export function markPresentationReady(timestep: number): void {
  presentationReady.add(timestep);
}

export function isPresentationReady(timestep: number): boolean {
  return presentationReady.has(timestep);
}

export function clearPresentationCache(): void {
  presentationReady.clear();
}
```

**输入 / 输出**：timestep → boolean 缓存

**答辩 30 秒**：首帧 draft 快速出图，静止 1.8s 升 presentation；缓存避免重复草稿。
## fitVolumeCamera.ts

**路径**：[`src/volume/fitVolumeCamera.ts`](../../../src/volume/fitVolumeCamera.ts)

**职责**：按包围盒与 aspect 设置相机位置。

**为什么选这段**：保证 128³ 立方体完整入画。

```1:40:src/volume/fitVolumeCamera.ts
import type vtkRenderer from '@kitware/vtk.js/Rendering/Core/Renderer';

import type vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';

import {

  CAMERA_DISTANCE_FACTOR,

  CAMERA_OFFSET,

  VIEW_MARGIN,

} from './renderSpec';



/**

 * Frame the volume cube centered and fully visible (works for 16:9 capture).

 */

export function fitVolumeCamera(

  renderer: vtkRenderer,

  imageData: vtkImageData,

  viewAspect?: number,

  zoomFactor = 1,

): void {

  const bounds = imageData.getBounds();

  const camera = renderer.getActiveCamera();



```

**输入 / 输出**：renderer + imageData + aspect + zoom → 相机参数

**答辩 30 秒**：用 vtk 的 resetCamera 思路，按域长 14.245 Mpc/h 与 zoom 系数摆放相机。
## volumeFocusPick.ts — 射线拾取

**路径**：[`src/volume/volumeFocusPick.ts`](../../../src/volume/volumeFocusPick.ts)

**职责**：屏幕点击 → 世界射线 → 沿射线找密度峰值。

**为什么选这段**：探索页点击聚焦 filament 用。

```92:130:src/volume/volumeFocusPick.ts
export function pickDensityPeakAlongRay(
  data: Float32Array,
  origin: [number, number, number],
  direction: [number, number, number],
  densityThreshold: number,
): PickResult | null {
  const hit = rayBoxIntersection(origin, direction);
  if (!hit) return null;

  const [tEnter, tExit] = hit;
  let best: PickResult | null = null;
  let bestDensity = -Infinity;
  let anyPeak = false;

  for (let i = 0; i < RAY_STEPS; i++) {
    const t = tEnter + ((tExit - tEnter) * (i + 0.5)) / RAY_STEPS;
    const wx = origin[0]! + direction[0]! * t;
    const wy = origin[1]! + direction[1]! * t;
    const wz = origin[2]! + direction[2]! * t;
    const rho = sampleDensityAtWorld(data, wx, wy, wz);
    if (rho >= densityThreshold && rho > bestDensity) {
      bestDensity = rho;
      best = { point: [wx, wy, wz], density: rho };
      anyPeak = true;
    }
  }

  if (anyPeak && best) return best;

  const tMid = (tEnter + tExit) * 0.5;
  const wx = origin[0]! + direction[0]! * tMid;
  const wy = origin[1]! + direction[1]! * tMid;
  const wz = origin[2]! + direction[2]! * tMid;
  return {
    point: [wx, wy, wz],
    density: sampleDensityAtWorld(data, wx, wy, wz),
  };
}

```

**输入 / 输出**：体数据 + 射线 → 峰值世界坐标

**答辩 30 秒**：把屏幕坐标反投影成射线，在 128³ 网格上步进采样，找超过阈值的密度峰作为飞行目标。
## DensityColorLegend.tsx

**路径**：[`src/volume/DensityColorLegend.tsx`](../../../src/volume/DensityColorLegend.tsx)

**职责**：CSS 渐变图例，与 colormap 一致。

**为什么选这段**：右栏色标与 3D 颜色对齐。

```1:45:src/volume/DensityColorLegend.tsx
import { cinematicLegendGradient, cosmicLegendGradient } from './transferFunction';

interface DensityColorLegendProps {
  min: number;
  max: number;
  cinematic?: boolean;
}

export function DensityColorLegend({ min, max, cinematic = true }: DensityColorLegendProps) {
  return (
    <div
      className={`density-legend${cinematic ? ' density-legend--cinematic' : ''}`}
      aria-label="密度色标"
    >
      <div
        className="density-legend-bar"
        style={{ background: cinematic ? cinematicLegendGradient() : cosmicLegendGradient() }}
      />
      <div className="density-legend-labels">
        <span>{min.toFixed(2)}</span>
        <span>气体密度 ρ</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  );
}
```

**输入 / 输出**：min/max + style → DOM 渐变

**答辩 30 秒**：图例不是截图，是 `cinematicLegendGradient` 生成的 CSS linear-gradient。
## TransferFunctionControls.tsx

**路径**：[`src/volume/TransferFunctionControls.tsx`](../../../src/volume/TransferFunctionControls.tsx)

**职责**：探索面板滑条写 `tfParams` 到 store。

**为什么选这段**：长卷 app 微调透明度/增益。

```1:50:src/volume/TransferFunctionControls.tsx
import { useEffect, useRef, useState } from 'react';
import type { TfParams } from './transferFunction';
import { debounce } from '@/utils/debounce';

export interface TransferFunctionControlsProps {
  params: TfParams;
  onChange: (params: TfParams) => void;
}

export function TransferFunctionControls({
  params,
  onChange,
}: TransferFunctionControlsProps) {
  const [local, setLocal] = useState<TfParams>(params);
  const commitRef = useRef(debounce((p: TfParams) => onChange(p), 120));

  useEffect(() => {
    setLocal(params);
  }, [params]);

  useEffect(() => {
    commitRef.current = debounce((p: TfParams) => onChange(p), 120);
    return () => commitRef.current.cancel();
  }, [onChange]);

  const update = (patch: Partial<TfParams>) => {
    const next = { ...local, ...patch };
    setLocal(next);
    commitRef.current(next);
  };

  const opacityScale = local.opacityScale ?? 1;
  const densityGain = local.densityGain ?? 0;
  const highlightBoost = local.highlightBoost ?? 1;

  return (
    <div className="tf-controls">
      <label>
        整体透明度 {opacityScale.toFixed(2)}
        <input
          type="range"
          min={0.3}
          max={2}
          step={0.05}
          value={opacityScale}
          onChange={(e) => update({ opacityScale: Number(e.target.value) })}
        />
      </label>
      <label>
        高密度阈值 {densityGain.toFixed(2)}
```

**输入 / 输出**：用户拖动 → setTfParams

**答辩 30 秒**：三个滑条改 opacityScale、densityGain、highlightBoost，VolumeScene 监听后重填传递函数。
## PosterHeroVolume.tsx

**路径**：[`src/dashboard/PosterHeroVolume.tsx`](../../../src/dashboard/PosterHeroVolume.tsx)

**职责**：长卷海报区嵌入 VolumeScene。

**为什么选这段**：代表图网页截图的体渲染入口。

```1:55:src/dashboard/PosterHeroVolume.tsx
import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import type { TfParams } from '@/volume/transferFunction';
import type { VolumeQuality } from '@/volume/VolumeScene';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);

function VtkFallback() {
  return <div className="vtk-skeleton pl-hero-vtk-fallback">加载体渲染…</div>;
}

export interface PosterHeroVolumeProps {
  densityData: Float32Array | null;
  loading: boolean;
  timestep: number;
  dataMin: number;
  dataMax: number;
  tfParams?: TfParams;
  quality?: VolumeQuality;
  highlightMin?: number;
  highlightMax?: number;
  /** Pause GPU render when explore overlay is open. */
  paused?: boolean;
  onCameraActivity?: () => void;
  onRendered?: () => void;
}

export function PosterHeroVolume({
  densityData,
  loading,
  timestep,
  dataMin,
  dataMax,
  tfParams,
  quality = 'cinematic',
  highlightMin,
  highlightMax,
  paused = false,
  onCameraActivity,
  onRendered,
}: PosterHeroVolumeProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(true);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    const forceRender = new URLSearchParams(window.location.search).has('posterCapture');
    if (forceRender) {
      setInView(true);
      return;
```

**输入 / 输出**：timeline + timestep → 海报主视觉

**答辩 30 秒**：Cosmic 长卷顶部用同一 VolumeScene，参数来自 `getCinematicDefaultProfile`。
## capture/main.tsx

**路径**：[`src/capture/main.tsx`](../../../src/capture/main.tsx)

**职责**：Playwright 无头截图专用入口，TF 随步变化。

**为什么选这段**：五帧条带与网页 TF 差异的解释落点。

```1:60:src/capture/main.tsx
import { useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VolumeScene } from '@/volume/VolumeScene';
import { loadTimestep, loadTimelineStats } from '@/data/nyxLoader';
import {
  getCinematicDefaultProfile,
  getEvolutionCaptureProfile,
  getGlobalMorphCaptureProfile,
  type CaptureProfile,
} from '@/viz/tfDomain';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

declare global {
  interface Window {
    __CAPTURE_READY__?: boolean;
    __CAPTURE_ERROR__?: string;
    __CAPTURE_TIMESTEP__?: number;
    __CAPTURE_REC__?: { timestep: number; ready: boolean };
    __CAPTURE_GO_TIMESTEP__?: (t: number) => void;
  }
}

function resolveCaptureProfile(
  timeline: Awaited<ReturnType<typeof loadTimelineStats>>,
  timestep: number,
  domainMode: string,
): CaptureProfile {
  if (domainMode === 'cinematic') {
    return getCinematicDefaultProfile(timeline);
  }
  if (domainMode === 'evolution') {
    return getEvolutionCaptureProfile(timeline, timestep);
  }
  if (domainMode === 'global' || domainMode === 'morph') {
    return getGlobalMorphCaptureProfile(timeline, timestep);
  }
  return getGlobalMorphCaptureProfile(timeline, timestep);
}

function CaptureApp() {
  const params = new URLSearchParams(window.location.search);
  const seqMode = params.get('seq') === '1';
  const domainMode = params.get('domain') ?? (seqMode ? 'morph' : 'evolution');
  const initialT = Math.max(0, Math.min(99, Number(params.get('t') ?? 0)));
  const [timestep, setTimestep] = useState(initialT);
  const [data, setData] = useState<Float32Array | null>(null);
  const [domain, setDomain] = useState({ min: 7.5, max: 15 });
  const [captureTf, setCaptureTf] = useState<CaptureProfile['tfParams']>({});
  const [highlightMin, setHighlightMin] = useState<number | undefined>();
  const [highlightMax, setHighlightMax] = useState<number | undefined>();
  const cameraZoom =
    domainMode === 'cinematic'
      ? VIDEO_CAMERA_ZOOM
      : VIDEO_CAMERA_ZOOM + (timestep / 99) * 0.08;
  const timelineRef = useRef<Awaited<ReturnType<typeof loadTimelineStats>> | null>(null);
  const loadGenRef = useRef(0);

  const markNotReady = useCallback((t: number) => {
    window.__CAPTURE_READY__ = false;
    window.__CAPTURE_REC__ = { timestep: t, ready: false };
```

**输入 / 输出**：URL 参数 timestep/scene → PNG

**答辩 30 秒**：capture 路由读 sceneId，调用 `resolveVolumeVisualProfile` 用演化截图配置，不是交互全局域。
