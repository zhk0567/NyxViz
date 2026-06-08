import { DensityHistogram } from '@/histogram/DensityHistogram';
import { VideoBrushPreviews } from '@/dashboard/VideoBrushPreviews';
import { VideoBrushValidationPanel } from '@/dashboard/video-scenes/VideoBrushValidationPanel';
import { VideoMorphPanel } from '@/dashboard/video-scenes/VideoMorphPanel';
import { VideoEvolutionFigurePanel } from '@/dashboard/video-scenes/VideoEvolutionFigurePanel';
import { VideoFigureStrip } from '@/dashboard/video-scenes/VideoFigureStrip';
import { ZoomableImage } from '@/components/ImageLightbox';
import { matchBrushPreset } from '@/data/brushPreset';
import { getSceneMeta } from '@/video/sceneRegistry';
import type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

function formatMassPct(stats: NonNullable<VideoSceneLayoutProps['stats']>, preset: ReturnType<typeof matchBrushPreset>) {
  if (!preset) return null;
  if (preset === 'top' && stats.massFractionAboveP99 != null) {
    return (stats.massFractionAboveP99 * 100).toFixed(2);
  }
  if (preset === 'bottom' && stats.massFractionBelowP01 != null) {
    return (stats.massFractionBelowP01 * 100).toFixed(2);
  }
  return null;
}

export function VideoRightColumn({
  sceneId,
  videoStats,
  timeline,
  densityData,
  loading,
  stats,
  timestep,
  dataMin,
  dataMax,
  volumeReady,
  brushRange,
  volumeRatio,
  onTop1,
  onBottom1,
  onFilament,
  onClear,
  activePreset,
  histogramSizeOpts,
  onSelectTimestep,
}: Pick<
  VideoSceneLayoutProps,
  | 'sceneId'
  | 'videoStats'
  | 'timeline'
  | 'densityData'
  | 'loading'
  | 'stats'
  | 'timestep'
  | 'dataMin'
  | 'dataMax'
  | 'volumeReady'
  | 'brushRange'
  | 'volumeRatio'
  | 'onTop1'
  | 'onBottom1'
  | 'onFilament'
  | 'onClear'
  | 'activePreset'
  | 'histogramSizeOpts'
  | 'onSelectTimestep'
>) {
  if (sceneId === 'task1-tf') {
    return (
      <aside className="vd-panel vd-panel-right">
        <figure className="vd-spec-figure vd-lighting-figure">
          <ZoomableImage
            src="/figures/task1_lighting_diagram.png"
            alt="Phong 主光与辅光示意"
            loading="lazy"
          />
          <figcaption>Phong 主光（东北上方）与辅光（Fill）示意</figcaption>
        </figure>
      </aside>
    );
  }

  if (sceneId === 'task1-morph' && stats) {
    return (
      <aside className="vd-panel vd-panel-right">
        <VideoMorphPanel
          timeline={timeline}
          timestep={timestep}
          stats={stats}
          onSelectTimestep={onSelectTimestep}
        />
      </aside>
    );
  }

  if (sceneId === 'task3-hist') {
    const figures = getSceneMeta(sceneId).content.figures;
    if (!figures?.length) return null;
    return (
      <aside className="vd-panel vd-panel-right vd-panel-right--figures">
        <header className="vd-panel-head">
          <h2>时序指标</h2>
        </header>
        <VideoFigureStrip
          figures={figures}
          layout="stack"
          className="vd-figure-strip--right-stack"
        />
      </aside>
    );
  }

  if (sceneId === 'task2-evolution') {
    return (
      <aside className="vd-panel vd-panel-right vd-panel-right--evolution-figures">
        <VideoEvolutionFigurePanel />
      </aside>
    );
  }

  const massPct = stats ? formatMassPct(stats, activePreset) : null;

  const isValidateScene = sceneId === 'task4-validate';

  return (
    <aside
      className={`vd-panel vd-panel-right${isValidateScene ? ' vd-panel-right--validate' : ''}`}
    >
      <header className="vd-panel-head">
        <h2>相空间刷选与空间验证</h2>
      </header>
      <div className="vd-panel-brush-hist">
        <DensityHistogram timeline={timeline} sizeOpts={histogramSizeOpts} />
      </div>
      {!isValidateScene && (
        <p className="vd-brush-hist-hint" aria-hidden>
          <span className="vd-brush-hist-arrow">↓</span>
          刷选密度区间 · 下方空间投影对应验证
        </p>
      )}
      {stats && (
        <VideoBrushPreviews
          stats={stats}
          densityData={densityData}
          volumeReady={volumeReady}
          loading={loading}
          dataMin={dataMin}
          dataMax={dataMax}
          activePreset={activePreset}
          onTop1={onTop1}
          onFilament={onFilament}
          onBottom1={onBottom1}
        />
      )}
      <div className="vd-brush-controls">
        <div className="vd-brush-presets">
          <button
            type="button"
            className={`vd-preset top${activePreset === 'top' ? ' on' : ''}`}
            onClick={onTop1}
          >
            Top 1%
          </button>
          <button
            type="button"
            className={`vd-preset fil${activePreset === 'filament' ? ' on' : ''}`}
            onClick={onFilament}
          >
            90–99%
          </button>
          <button
            type="button"
            className={`vd-preset bot${activePreset === 'bottom' ? ' on' : ''}`}
            onClick={onBottom1}
          >
            Bottom 1%
          </button>
          <button type="button" className="vd-preset clear" onClick={onClear}>
            清除
          </button>
        </div>
        {brushRange && stats && (
          <p className="vd-brush-readout">
            ρ∈[{brushRange.min.toFixed(2)}, {brushRange.max.toFixed(2)}]
            {volumeRatio != null && ` · 体积 ${volumeRatio}%`}
            {massPct != null && ` · 质量 ${massPct}%`}
          </p>
        )}
      </div>
      {sceneId === 'task4-validate' && (
        <VideoBrushValidationPanel brushValidation={videoStats.brushValidation} />
      )}
    </aside>
  );
}
