import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { TransferFunctionControls } from '@/volume/TransferFunctionControls';
import { DensityColorLegend } from '@/volume/DensityColorLegend';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { TimelineMetrics } from '@/histogram/TimelineMetrics';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import { DensityProjection } from '@/spatial/DensityProjection';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { scanBrushRangeAsync } from '@/data/brushScan';
import { loadTimelineStats } from '@/data/nyxLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { usePrefetchTimestep } from '@/hooks/usePrefetchTimestep';
import { useAppStore } from '@/store/useAppStore';
import type { BrushedVoxel, TimelineData } from '@/data/types';
import { TIMESTEP_COUNT } from '@/data/types';
import { getGlobalTfDomain } from '@/volume/transferFunction';
import './dashboard.css';

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);
const BrushedPoints = lazy(() =>
  import('@/spatial/BrushedPoints').then((m) => ({ default: m.BrushedPoints })),
);

const MARK_STEPS = [0, 25, 50, 75, 99];

type TabId = 'volume' | 'stats' | 'brush';

function VtkFallback() {
  return <div className="vtk-skeleton">加载 3D 视图…</div>;
}

export function App() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>('volume');
  const [brushedPoints, setBrushedPoints] = useState<BrushedVoxel[]>([]);
  const [scanning, setScanning] = useState(false);
  const [sliderStep, setSliderStep] = useState(0);
  const [highQuality, setHighQuality] = useState(true);
  const [show3dPoints, setShow3dPoints] = useState(false);

  const timestep = useAppStore((s) => s.timestep);
  const densityData = useAppStore((s) => s.densityData);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);
  const brushRange = useAppStore((s) => s.brushRange);
  const brushedCount = useAppStore((s) => s.brushedCount);
  const setTimestep = useAppStore((s) => s.setTimestep);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const setBrushedCount = useAppStore((s) => s.setBrushedCount);
  const tfParams = useAppStore((s) => s.tfParams);
  const setTfParams = useAppStore((s) => s.setTfParams);

  useNyxTimestep();
  usePrefetchTimestep();

  useEffect(() => {
    setSliderStep(timestep);
  }, [timestep]);

  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    if (hash === 'stats' || hash === 'brush' || hash === 'volume') {
      setTab(hash);
    }
  }, []);

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  const stats = timeline?.timesteps[timestep];
  const tfDomain = timeline ? getGlobalTfDomain(timeline) : null;
  const dataMin = tfDomain?.min ?? stats?.min ?? 7.5;
  const dataMax = tfDomain?.max ?? stats?.max ?? 15;
  const volumeQuality = highQuality ? 'presentation' : 'interactive';
  const volumeActive = tab === 'volume' || tab === 'brush';

  const applyTop1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p99, max: stats.max });
  }, [stats, setBrushRange]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.min, max: stats.p01 });
  }, [stats, setBrushRange]);

  useEffect(() => {
    if (tab !== 'brush' || !densityData || !brushRange) {
      setBrushedPoints([]);
      setBrushedCount(0);
      setScanning(false);
      return;
    }

    let cancelled = false;
    setScanning(true);
    const handle = window.setTimeout(() => {
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
      window.clearTimeout(handle);
    };
  }, [tab, densityData, brushRange, setBrushedCount]);

  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);

  const commitTimestep = () => {
    if (sliderStep !== timestep) setTimestep(sliderStep);
  };

  const setTabWithHash = (id: TabId) => {
    setTab(id);
    window.location.hash = id;
  };

  if (initError) {
    return (
      <div className="app-error">
        <h1>Nyx 可视化</h1>
        <p>{initError}</p>
        <p>请先运行: <code>python run.py</code></p>
      </div>
    );
  }

  if (!timeline) {
    return <div className="app-loading">加载统计数据…</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-titles">
          <h1>Nyx 宇宙气体密度可视化</h1>
          <p className="subtitle">
            交互演示 · <a href="/">← 返回完整比赛成果页</a>
          </p>
        </div>
        <nav className="tabs">
          {(
            [
              ['volume', '体渲染'],
              ['stats', '时序统计'],
              ['brush', '刷选联动'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={tab === id ? 'active' : ''}
              onClick={() => setTabWithHash(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <div className="controls">
        <label>
          时间步 {sliderStep}
          <input
            type="range"
            min={0}
            max={TIMESTEP_COUNT - 1}
            value={sliderStep}
            list="timestep-marks"
            onChange={(e) => setSliderStep(Number(e.target.value))}
            onMouseUp={commitTimestep}
            onTouchEnd={commitTimestep}
          />
          <datalist id="timestep-marks">
            {MARK_STEPS.map((t) => (
              <option key={t} value={t} label={`t=${t}`} />
            ))}
          </datalist>
        </label>
        {stats && (
          <span className="timestep-meta">
            μ={stats.mean.toFixed(3)} σ={stats.std.toFixed(3)}
          </span>
        )}
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={highQuality}
            onChange={(e) => setHighQuality(e.target.checked)}
          />
          展板质量体渲染
        </label>
        {tab === 'brush' && (
          <>
            <button type="button" className="secondary" onClick={applyTop1}>
              Top 1%
            </button>
            <button type="button" className="secondary" onClick={applyBottom1}>
              Bottom 1%
            </button>
            <button
              type="button"
              className="muted"
              onClick={() => setBrushRange(null)}
            >
              清除刷选
            </button>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={show3dPoints}
                onChange={(e) => setShow3dPoints(e.target.checked)}
              />
              显示 3D 点云（较慢）
            </label>
          </>
        )}
        {volumeActive && (
          <TransferFunctionControls params={tfParams} onChange={setTfParams} />
        )}
        {loading && <span className="badge">加载体数据 t={timestep}…</span>}
        {scanning && <span className="badge">扫描刷选体素…</span>}
        {error && <span className="badge error">{error}</span>}
        {brushRange && tab === 'brush' && !scanning && (
          <span className="badge">
            刷选 [{brushRange.min.toFixed(3)}, {brushRange.max.toFixed(3)}] —{' '}
            {brushedCount}
            {brushedCount >= 12000 ? '+' : ''} 体素
          </span>
        )}
      </div>

      {tab === 'volume' && densityData && (
        <section className="panel full vtk-card-wrap">
          <DensityColorLegend min={dataMin} max={dataMax} />
          <LoadingOverlay visible={loading} label={`加载时间步 ${timestep}`} />
          <Suspense fallback={<VtkFallback />}>
            <VolumeScene
              data={densityData}
              dataMin={dataMin}
              dataMax={dataMax}
              tfParams={tfParams}
              quality={volumeQuality}
              renderActive={volumeActive}
              className="vtk-panel"
            />
          </Suspense>
        </section>
      )}

      {tab === 'stats' && (
        <section className="panel stats-grid">
          <div className="chart-card">
            <h3>密度对数直方图叠加 (t=0,25,50,75,99)</h3>
            <HistogramOverlay timeline={timeline} />
          </div>
          <div className="chart-card">
            <h3>时序指标</h3>
            <TimelineMetrics timeline={timeline} />
          </div>
          <div className="chart-card wide">
            <h3>当前步直方图（可刷选）</h3>
            <DensityHistogram timeline={timeline} />
          </div>
        </section>
      )}

      {tab === 'brush' && densityData && (
        <section className="panel brush-grid">
          <div className="chart-card">
            <h3>密度直方图 — 拖拽框选</h3>
            <DensityHistogram timeline={timeline} />
          </div>
          <div className="vtk-card vtk-card-wrap">
            <h3>体渲染（刷选高亮）</h3>
            <DensityColorLegend min={dataMin} max={dataMax} />
            <Suspense fallback={<VtkFallback />}>
              <VolumeScene
                data={densityData}
                dataMin={dataMin}
                dataMax={dataMax}
                tfParams={tfParams}
                quality={volumeQuality}
                renderActive={volumeActive}
                {...highlight}
                className="vtk-panel"
              />
            </Suspense>
          </div>
          <div className="chart-card wide">
            <h3>刷选区域 — 最大密度投影 (XY)</h3>
            <DensityProjection
              data={densityData}
              brushRange={brushRange}
              axis="xy"
              domainMin={dataMin}
              domainMax={dataMax}
            />
          </div>
          {show3dPoints && (
            <div className="vtk-card wide">
              <h3>刷选体素 3D 点云</h3>
              {brushedPoints.length > 0 ? (
                <Suspense fallback={<VtkFallback />}>
                  <BrushedPoints points={brushedPoints} className="vtk-panel" />
                </Suspense>
              ) : (
                <p className="placeholder-3d">
                  {scanning
                    ? '正在扫描…'
                    : '框选直方图或点击 Top 1% 后显示点云'}
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
