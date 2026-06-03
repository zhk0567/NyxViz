import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CosmicPosterLayout } from '@/dashboard/CosmicPosterLayout';
import { InteractiveBrushLab } from '@/dashboard/InteractiveBrushLab';
import { DiscoveryCards } from '@/dashboard/DiscoveryCards';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { scanBrushRangeAsync } from '@/data/brushScan';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';
import { TIMESTEP_COUNT, VOXEL_COUNT } from '@/data/types';
import { getGlobalTfDomain } from '@/volume/transferFunction';
import { MARK_STEPS } from '@/dashboard/evolutionPhase';
import { usePrefetchTimestep } from '@/hooks/usePrefetchTimestep';

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);

const SECTION_IDS = [
  'story-01',
  'story-02',
  'story-03',
  'story-04',
  'story-05',
  'story-06',
] as const;

function VtkFallback() {
  return <div className="vtk-skeleton">加载体渲染…</div>;
}

export interface DashboardCoreProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  loading: boolean;
  error: string | null;
  embedded?: boolean;
}

export function DashboardCore({
  timeline,
  densityData,
  loading,
  error,
  embedded = false,
}: DashboardCoreProps) {
  const [sliderStep, setSliderStep] = useState(0);
  const [sliderDragging, setSliderDragging] = useState(false);
  const [highQuality, setHighQuality] = useState(false);
  const [volumeReady, setVolumeReady] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [exploreOpen, setExploreOpen] = useState(false);

  usePrefetchTimestep(sliderStep, sliderDragging);

  const timestep = useAppStore((s) => s.timestep);
  const brushRange = useAppStore((s) => s.brushRange);
  const brushedCount = useAppStore((s) => s.brushedCount);
  const tfParams = useAppStore((s) => s.tfParams);
  const setTimestep = useAppStore((s) => s.setTimestep);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const setBrushedCount = useAppStore((s) => s.setBrushedCount);

  useEffect(() => {
    setSliderStep(timestep);
    setVolumeReady(false);
  }, [timestep]);

  const stats = timeline.timesteps[sliderDragging ? sliderStep : timestep];
  const tfDomain = getGlobalTfDomain(timeline);
  const dataMin = tfDomain?.min ?? stats?.min ?? 7.5;
  const dataMax = tfDomain?.max ?? stats?.max ?? 15;
  const volumeQuality =
    loading || scanning
      ? 'interactive'
      : highQuality
        ? 'presentation'
        : 'interactive';
  const prevBrushRef = useRef<{ min: number; max: number } | null>(null);

  const applyTop1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p99, max: stats.max });
    setExploreOpen(true);
  }, [stats, setBrushRange]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.min, max: stats.p01 });
    setExploreOpen(true);
  }, [stats, setBrushRange]);

  const applyFilament = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p90, max: stats.p99 });
    setExploreOpen(true);
  }, [stats, setBrushRange]);

  useEffect(() => {
    if (!densityData || !brushRange) {
      setBrushedCount(0);
      setScanning(false);
      prevBrushRef.current = null;
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
  }, [densityData, brushRange, timestep, setBrushedCount]);

  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);

  const commitTimestep = () => {
    if (sliderStep !== timestep) setTimestep(sliderStep);
  };

  const selectTimestep = (t: number) => {
    setSliderStep(t);
    setTimestep(t);
  };

  const volumeRatio =
    brushRange && brushedCount > 0
      ? ((brushedCount / VOXEL_COUNT) * 100).toFixed(2)
      : null;

  const scrollToSection = (id: (typeof SECTION_IDS)[number]) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const heroVtk = (
    <div className="hero-vtk-inner explore-vtk">
      <LoadingOverlay visible={loading} label={`t=${timestep}`} />
      {densityData ? (
        <Suspense fallback={<VtkFallback />}>
          <VolumeScene
            data={densityData}
            timestep={timestep}
            dataMin={dataMin}
            dataMax={dataMax}
            tfParams={tfParams}
            quality={volumeQuality}
            renderActive={exploreOpen}
            onRendered={() => setVolumeReady(true)}
            {...highlight}
            className="vtk-panel"
          />
        </Suspense>
      ) : (
        <VtkFallback />
      )}
    </div>
  );

  return (
    <div className={`cosmic-poster cosmic-poster-layout${embedded ? ' cosmic-poster-embed' : ''}`}>
      <header className="poster-top-bar">
        <span className="poster-top-kicker">Nyx 128³ · 宇宙网诞生记</span>
        <button
          type="button"
          className="poster-explore-btn"
          onClick={() => setExploreOpen(true)}
        >
          交互探索
        </button>
        {!embedded && (
          <a href="/" className="poster-top-link">
            成果页
          </a>
        )}
      </header>

      <nav className="poster-rail" aria-label="章节">
        {SECTION_IDS.map((id, i) => (
          <button
            key={id}
            type="button"
            title={`0${i + 1}`}
            onClick={() => scrollToSection(id)}
          >
            {String(i + 1).padStart(2, '0')}
          </button>
        ))}
      </nav>

      <main className="poster-main">
        <CosmicPosterLayout
          timeline={timeline}
          dataMin={dataMin}
          dataMax={dataMax}
          timestep={timestep}
          onSelectTimestep={selectTimestep}
        />
      </main>

      {exploreOpen && (
        <div
          className="explore-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="交互探索"
        >
          <div className="explore-sheet">
            <header className="explore-head">
              <h2>交互探索 · t={timestep}</h2>
              <button
                type="button"
                className="explore-close"
                onClick={() => setExploreOpen(false)}
              >
                关闭
              </button>
            </header>
            <div className="explore-quick">
              <button type="button" onClick={applyTop1}>
                Top 1%
              </button>
              <button type="button" onClick={applyBottom1}>
                Bottom 1%
              </button>
              <button type="button" onClick={applyFilament}>
                纤维带
              </button>
              <button type="button" onClick={() => setBrushRange(null)}>
                清除刷选
              </button>
              {MARK_STEPS.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={timestep === t ? 'on' : ''}
                  onClick={() => selectTimestep(t)}
                >
                  t={t}
                </button>
              ))}
            </div>
            <InteractiveBrushLab
              timeline={timeline}
              densityData={densityData}
              volumeReady={volumeReady}
              loading={loading}
              brushRange={brushRange}
              domainMin={dataMin}
              domainMax={dataMax}
              onTop1={applyTop1}
              onBottom1={applyBottom1}
              onFilament={applyFilament}
              onClear={() => setBrushRange(null)}
              vtkSlot={heroVtk}
            />
            <section className="explore-discover">
              <h3>关键发现</h3>
              <DiscoveryCards timeline={timeline} />
            </section>
          </div>
        </div>
      )}

      <aside className="control-dock" aria-label="交互控制">
        <div className="dock-row">
          <span className="dock-title">时间步</span>
          <strong className="dock-t">t={sliderStep}</strong>
          <input
            type="range"
            min={0}
            max={TIMESTEP_COUNT - 1}
            value={sliderStep}
            className="dock-slider"
            onChange={(e) => setSliderStep(Number(e.target.value))}
            onPointerDown={() => setSliderDragging(true)}
            onMouseUp={() => {
              setSliderDragging(false);
              commitTimestep();
            }}
            onTouchEnd={() => {
              setSliderDragging(false);
              commitTimestep();
            }}
          />
          {stats && (
            <span className="dock-meta">
              μ={stats.mean.toFixed(2)} σ={stats.std.toFixed(3)}
            </span>
          )}
        </div>
        <div className="dock-row dock-actions">
          {MARK_STEPS.map((t) => (
            <button
              key={t}
              type="button"
              className={`dock-step${timestep === t ? ' on' : ''}`}
              onClick={() => selectTimestep(t)}
            >
              {t}
            </button>
          ))}
          <button
            type="button"
            className="dock-explore"
            onClick={() => setExploreOpen(true)}
          >
            探索
          </button>
          <label className="dock-hq">
            <input
              type="checkbox"
              checked={highQuality}
              onChange={(e) => setHighQuality(e.target.checked)}
            />
            高清
          </label>
        </div>
        {brushRange && (
          <p className="dock-brush">
            ρ∈[{brushRange.min.toFixed(2)}, {brushRange.max.toFixed(2)}]
            {volumeRatio != null && ` · ${volumeRatio}%`}
          </p>
        )}
        {loading && <span className="dock-badge">加载中…</span>}
        {error && <span className="dock-badge err">{error}</span>}
      </aside>
    </div>
  );
}
