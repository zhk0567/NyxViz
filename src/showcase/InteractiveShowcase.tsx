import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { DensityProjection } from '@/spatial/DensityProjection';
import { TransferFunctionControls } from '@/volume/TransferFunctionControls';
import { scanBrushRangeAsync } from '@/data/brushScan';
import {
  loadTimestep,
  loadTimelineStats,
} from '@/data/nyxLoader';
import { useAppStore } from '@/store/useAppStore';
import type { BrushedVoxel, TimelineData } from '@/data/types';
import { TIMESTEP_COUNT } from '@/data/types';
import '@/dashboard/dashboard.css';

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);
const BrushedPoints = lazy(() =>
  import('@/spatial/BrushedPoints').then((m) => ({ default: m.BrushedPoints })),
);

export function InteractiveShowcase() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [brushedPoints, setBrushedPoints] = useState<BrushedVoxel[]>([]);
  const [initError, setInitError] = useState<string | null>(null);
  const [sliderStep, setSliderStep] = useState(0);
  const [highQuality, setHighQuality] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [show3dPoints, setShow3dPoints] = useState(false);

  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const brushRange = useAppStore((s) => s.brushRange);
  const brushedCount = useAppStore((s) => s.brushedCount);
  const tfParams = useAppStore((s) => s.tfParams);
  const setTimestep = useAppStore((s) => s.setTimestep);
  const setDensityData = useAppStore((s) => s.setDensityData);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const setBrushedCount = useAppStore((s) => s.setBrushedCount);
  const setTfParams = useAppStore((s) => s.setTfParams);

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const embedded = (
      window as unknown as { __NYX_EMBEDDED_TIMESTEPS__?: Record<number, Float32Array> }
    ).__NYX_EMBEDDED_TIMESTEPS__;

    const load = embedded?.[timestep]
      ? Promise.resolve(embedded[timestep]!)
      : loadTimestep(timestep);

    load
      .then((data) => {
        if (!cancelled) {
          setDensityData(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [timestep, setDensityData, setLoading, setError]);

  useEffect(() => {
    setSliderStep(timestep);
  }, [timestep]);

  const stats = timeline?.timesteps[timestep];
  const volumeQuality = highQuality ? 'high' : 'interactive';
  const dataMin = stats?.min ?? 7.5;
  const dataMax = stats?.max ?? 15;

  const applyTop1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p99, max: stats.max });
  }, [stats, setBrushRange]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.min, max: stats.p01 });
  }, [stats, setBrushRange]);

  useEffect(() => {
    if (!densityData || !brushRange) {
      setBrushedPoints([]);
      setBrushedCount(0);
      setScanning(false);
      return;
    }

    let cancelled = false;
    setScanning(true);
    const h = window.setTimeout(() => {
      scanBrushRangeAsync(
        densityData,
        brushRange.min,
        brushRange.max,
        12000,
      )
        .then((found) => {
          if (!cancelled) {
            setBrushedPoints(found);
            setBrushedCount(found.length);
            setScanning(false);
          }
        })
        .catch(() => {
          if (!cancelled) setScanning(false);
        });
    }, 150);
    return () => {
      cancelled = true;
      window.clearTimeout(h);
    };
  }, [densityData, brushRange, setBrushedCount]);

  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);

  if (initError) {
    return <p className="badge error">{initError}</p>;
  }
  if (!timeline) {
    return <p>加载统计数据…</p>;
  }

  return (
    <div className="dashboard showcase-embedded">
      <div className="controls">
        <label>
          时间步 {sliderStep}
          <input
            type="range"
            min={0}
            max={TIMESTEP_COUNT - 1}
            value={sliderStep}
            onChange={(e) => setSliderStep(Number(e.target.value))}
            onMouseUp={() => setTimestep(sliderStep)}
            onTouchEnd={() => setTimestep(sliderStep)}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={highQuality}
            onChange={(e) => setHighQuality(e.target.checked)}
          />
          高质量体渲染
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={show3dPoints}
            onChange={(e) => setShow3dPoints(e.target.checked)}
          />
          显示 3D 点云
        </label>
        <button type="button" onClick={applyTop1}>
          Top 1%
        </button>
        <button type="button" onClick={applyBottom1}>
          Bottom 1%
        </button>
        <button type="button" onClick={() => setBrushRange(null)}>
          清除刷选
        </button>
        {loading && <span className="badge">加载中…</span>}
        {scanning && <span className="badge">扫描刷选体素…</span>}
        {brushRange && !scanning && (
          <span className="badge">
            刷选 {brushedCount} 体素 [{brushRange.min.toFixed(2)},{' '}
            {brushRange.max.toFixed(2)}]
          </span>
        )}
        <TransferFunctionControls params={tfParams} onChange={setTfParams} />
      </div>
      {densityData ? (
        <section className="panel brush-grid">
          <div className="chart-card">
            <h3>密度直方图（拖拽框选）</h3>
            <DensityHistogram timeline={timeline} />
          </div>
          <div className="vtk-card">
            <h3>体渲染</h3>
            <Suspense fallback={<div className="vtk-skeleton">加载 3D…</div>}>
              <VolumeScene
                data={densityData}
                dataMin={dataMin}
                dataMax={dataMax}
                tfParams={tfParams}
                quality={volumeQuality}
                renderActive
                {...highlight}
                className="vtk-panel"
              />
            </Suspense>
          </div>
          <div className="chart-card wide">
            <h3>最大密度投影 (XY)</h3>
            <DensityProjection
              data={densityData}
              brushRange={brushRange}
              axis="xy"
            />
          </div>
          {show3dPoints && (
            <div className="vtk-card wide">
              <h3>刷选体素点云</h3>
              {brushedPoints.length > 0 ? (
                <Suspense fallback={<div className="vtk-skeleton">加载点云…</div>}>
                  <BrushedPoints points={brushedPoints} className="vtk-panel" />
                </Suspense>
              ) : (
                <p className="placeholder-3d">
                  {scanning ? '正在扫描…' : '框选直方图或 Top 1% 后显示点云'}
                </p>
              )}
            </div>
          )}
        </section>
      ) : (
        <p>等待体数据…（需通过 HTTP 提供 /Nyx/ 或使用内嵌时间步）</p>
      )}
    </div>
  );
}
