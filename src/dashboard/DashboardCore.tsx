import { lazy, Suspense, useEffect, useState } from 'react';
import { CosmicBackdrop } from '@/components/CosmicBackdrop';
import { CosmicPosterLayout } from '@/dashboard/CosmicPosterLayout';
import { CosmicPosterRepresentative } from '@/dashboard/CosmicPosterRepresentative';
import { PosterHeroVolume } from '@/dashboard/PosterHeroVolume';
import { InteractiveBrushLab } from '@/dashboard/InteractiveBrushLab';
import { DiscoveryCards } from '@/dashboard/DiscoveryCards';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { useDashboardInteraction } from '@/dashboard/useDashboardInteraction';
import { useVolumeVisualProfile } from '@/hooks/useVolumeVisualProfile';
import { MARK_STEPS } from '@/dashboard/evolutionPhase';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';
import type { TimelineData } from '@/data/types';
import { TIMESTEP_COUNT } from '@/data/types';
import type { VideoStatsBundle } from '@/data/statsLoader';
import { usePosterAutoSave } from '@/dashboard/usePosterAutoSave';

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
  videoStats?: VideoStatsBundle;
}

export function DashboardCore({
  timeline,
  densityData,
  loading,
  error,
  embedded = false,
  videoStats,
}: DashboardCoreProps) {
  const posterCapture =
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).has('posterCapture');
  const representative =
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).has('representative');
  const savePoster =
    typeof window !== 'undefined' &&
    (new URLSearchParams(window.location.search).has('savePoster') ||
      (import.meta.env.DEV &&
        new URLSearchParams(window.location.search).has('representative')));
  const [exploreOpen, setExploreOpen] = useState(false);
  const [posterVolumeReady, setPosterVolumeReady] = useState(false);

  const ix = useDashboardInteraction(timeline, densityData, loading, {
    onPresetBrush: () => setExploreOpen(true),
    instantVolume: true,
    defaultHighQuality: false,
    idleBoostDelayMs: 1200,
  });

  const {
    timestep,
    sliderStep,
    sliderDragging,
    setSliderStep,
    setSliderDragging,
    highQuality,
    setHighQuality,
    volumeReady,
    setVolumeReady,
    brushRange,
    tfParams,
    stats,
    dataMin,
    dataMax,
    volumeQuality,
    highlight,
    applyTop1,
    onVolumeCameraActivity,
    applyBottom1,
    applyFilament,
    clearBrush,
    commitTimestep,
    selectTimestep,
    volumeRatio,
  } = ix;

  const visualProfile = useVolumeVisualProfile(timeline, timestep);
  const volumeHighlightMin = highlight.highlightMin ?? visualProfile.highlightMin;
  const volumeHighlightMax = highlight.highlightMax ?? visualProfile.highlightMax;

  const { saveState, savePoster: triggerSavePoster } = usePosterAutoSave({
    enabled: import.meta.env.DEV,
    representative: representative || posterCapture,
    loading,
    volumeReady: posterVolumeReady,
    autoOnLoad: savePoster,
  });

  useEffect(() => {
    setPosterVolumeReady(false);
  }, [timestep]);

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
            dataMin={visualProfile.dataMin}
            dataMax={visualProfile.dataMax}
            tfParams={visualProfile.tfParams}
            quality={volumeQuality}
            cameraZoom={VIDEO_CAMERA_ZOOM}
            renderActive={exploreOpen}
            interactiveCamera={exploreOpen}
            adaptivePrecisionZoom
            visualStyle="cinematic"
            onRendered={() => setVolumeReady(true)}
            onCameraActivity={onVolumeCameraActivity}
            highlightMin={volumeHighlightMin}
            highlightMax={volumeHighlightMax}
            className="vtk-panel"
          />
        </Suspense>
      ) : (
        <VtkFallback />
      )}
    </div>
  );

  const posterHero = (
    <PosterHeroVolume
      densityData={densityData}
      loading={loading}
      timestep={timestep}
      dataMin={visualProfile.dataMin}
      dataMax={visualProfile.dataMax}
      tfParams={visualProfile.tfParams}
      quality={volumeQuality}
      highlightMin={volumeHighlightMin}
      highlightMax={volumeHighlightMax}
      paused={exploreOpen}
      onCameraActivity={onVolumeCameraActivity}
      onRendered={() => setPosterVolumeReady(true)}
    />
  );

  return (
    <div
      className={`cosmic-poster cosmic-poster-layout cosmic-page-frame${
        embedded ? ' cosmic-poster-embed' : ''
      }${posterCapture ? ' poster-capture-mode' : ''}${
        representative ? ' poster-representative-mode' : ''
      }`}
    >
      <CosmicBackdrop variant="poster" intensity="full" fixed={!posterCapture} />
      {!representative && (
      <header className="poster-top-bar">
        <span className="poster-top-kicker pl-text-gradient-cyan">Nyx 128³ · 宇宙网诞生记</span>
        {!posterCapture && !representative && (
          <>
            <button
              type="button"
              className="poster-explore-btn"
              onClick={() => setExploreOpen(true)}
            >
              交互探索
            </button>
            {!embedded && (
              <a href="/video.html" className="poster-top-link">
                录屏版
              </a>
            )}
          </>
        )}
      </header>
      )}

      {!posterCapture && !representative && (
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
      )}

      <main className="poster-main">
        {representative ? (
          <CosmicPosterRepresentative
            timeline={timeline}
            dataMin={dataMin}
            dataMax={dataMax}
            timestep={timestep}
            onSelectTimestep={selectTimestep}
            heroSlot={posterHero}
            showToolbar={!posterCapture}
            onExplore={() => setExploreOpen(true)}
            onSavePoster={import.meta.env.DEV ? triggerSavePoster : undefined}
            saveState={saveState}
          />
        ) : (
          <CosmicPosterLayout
            timeline={timeline}
            dataMin={dataMin}
            dataMax={dataMax}
            timestep={timestep}
            onSelectTimestep={selectTimestep}
            heroSlot={posterHero}
            loading={loading}
            validationExtended={videoStats?.validationExtended ?? null}
          />
        )}
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
              <button type="button" onClick={clearBrush}>
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
              onClear={clearBrush}
              vtkSlot={heroVtk}
            />
            <section className="explore-discover">
              <h3>关键发现</h3>
              <DiscoveryCards timeline={timeline} />
            </section>
          </div>
        </div>
      )}

      {!posterCapture && !representative && (
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
      )}
    </div>
  );
}
