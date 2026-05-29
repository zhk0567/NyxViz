import { useCallback, useEffect, useMemo, useState } from 'react';
import { VolumeScene } from '@/volume/VolumeScene';
import { TransferFunctionControls } from '@/volume/TransferFunctionControls';
import { BrushedPoints } from '@/spatial/BrushedPoints';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { TimelineMetrics } from '@/histogram/TimelineMetrics';
import { HistogramOverlay } from '@/histogram/HistogramOverlay';
import { loadTimelineStats, scanBrushRange } from '@/data/nyxLoader';
import { useNyxTimestep } from '@/hooks/useNyxTimestep';
import { useAppStore } from '@/store/useAppStore';
import type { BrushedVoxel, TimelineData } from '@/data/types';
import { TIMESTEP_COUNT } from '@/data/types';
import './dashboard.css';

type TabId = 'volume' | 'stats' | 'brush';

export function App() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>('brush');
  const [brushedPoints, setBrushedPoints] = useState<BrushedVoxel[]>([]);

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

  useEffect(() => {
    loadTimelineStats()
      .then(setTimeline)
      .catch((e: unknown) =>
        setInitError(e instanceof Error ? e.message : String(e)),
      );
  }, []);

  const stats = timeline?.timesteps[timestep];

  const dataMin = stats?.min ?? 7.5;
  const dataMax = stats?.max ?? 15;

  const applyBrush = useCallback(
    (range: { min: number; max: number }) => {
      setBrushRange(range);
    },
    [setBrushRange],
  );

  const applyTop1 = useCallback(() => {
    if (!stats) return;
    applyBrush({ min: stats.p99, max: stats.max });
  }, [stats, applyBrush]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    applyBrush({ min: stats.min, max: stats.p01 });
  }, [stats, applyBrush]);

  useEffect(() => {
    if (!densityData || !brushRange) {
      setBrushedPoints([]);
      setBrushedCount(0);
      return;
    }

    const handle = window.setTimeout(() => {
      const found = scanBrushRange(
        densityData,
        brushRange.min,
        brushRange.max,
        50000,
      );
      setBrushedPoints(found);
      setBrushedCount(found.length);
    }, 80);

    return () => window.clearTimeout(handle);
  }, [densityData, brushRange, setBrushedCount]);

  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);

  if (initError) {
    return (
      <div className="app-error">
        <h1>Nyx 可视化</h1>
        <p>{initError}</p>
        <p>请先运行: <code>npm run precompute</code></p>
      </div>
    );
  }

  if (!timeline) {
    return <div className="app-loading">加载统计数据…</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Nyx 宇宙气体密度可视化</h1>
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
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <div className="controls">
        <label>
          时间步 {timestep}
          <input
            type="range"
            min={0}
            max={TIMESTEP_COUNT - 1}
            value={timestep}
            onChange={(e) => setTimestep(Number(e.target.value))}
          />
        </label>
        <button type="button" onClick={applyTop1}>
          Top 1% 高密度
        </button>
        <button type="button" onClick={applyBottom1}>
          Bottom 1% 低密度
        </button>
        <button type="button" onClick={() => setBrushRange(null)}>
          清除刷选
        </button>
        {(tab === 'volume' || tab === 'brush') && (
          <TransferFunctionControls params={tfParams} onChange={setTfParams} />
        )}
        {loading && <span className="badge">加载体数据…</span>}
        {error && <span className="badge error">{error}</span>}
        {brushRange && (
          <span className="badge">
            刷选: [{brushRange.min.toFixed(3)}, {brushRange.max.toFixed(3)}] —{' '}
            {brushedCount} 体素
          </span>
        )}
      </div>

      {tab === 'volume' && densityData && (
        <section className="panel full">
          <VolumeScene
            data={densityData}
            dataMin={dataMin}
            dataMax={dataMax}
            tfParams={tfParams}
            className="vtk-panel"
          />
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
          <div className="vtk-card">
            <h3>体渲染（刷选高亮）</h3>
            <VolumeScene
              data={densityData}
              dataMin={dataMin}
              dataMax={dataMax}
              tfParams={tfParams}
              {...highlight}
              className="vtk-panel"
            />
          </div>
          <div className="vtk-card wide">
            <h3>刷选体素空间分布</h3>
            <BrushedPoints points={brushedPoints} className="vtk-panel" />
          </div>
        </section>
      )}
    </div>
  );
}
