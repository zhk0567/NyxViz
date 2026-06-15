import { useEffect, useState } from 'react';
import { figuresUrl } from '@/config/publicPaths';
import { VIDEO_POSTER_BRUSH_VERIFY } from '@/config/videoStaticFigures';
import { computeStoryMetrics } from '@/results/storyMetrics';
import { BrushHistogramPreview } from '@/histogram/BrushHistogramPreview';
import { useSharedProjection } from '@/hooks/useSharedProjection';
import { BandPreviewCanvas } from '@/spatial/BandPreviewCanvas';
import { loadTimestep } from '@/data/nyxLoader';
import type { BrushRange, TimelineData } from '@/data/types';

interface BrushSpatialPreviewProps {
  densityData: Float32Array | null;
  loading: boolean;
  dataMin: number;
  dataMax: number;
  brushRange: BrushRange;
  fallbackSrc: string;
  zoom?: boolean;
}

function BrushSpatialPreview({
  densityData,
  loading,
  dataMin,
  dataMax,
  brushRange,
  fallbackSrc,
  zoom = false,
}: BrushSpatialPreviewProps) {
  const projection = useSharedProjection(densityData, 'xy');
  const canRender = densityData && projection && !loading;

  if (canRender) {
    return (
      <BandPreviewCanvas
        projection={projection}
        brushRange={brushRange}
        domainMin={dataMin}
        domainMax={dataMax}
        className={zoom ? 'pl-brush-proj pl-brush-proj--zoom' : 'pl-brush-proj'}
      />
    );
  }

  return (
    <img
      src={fallbackSrc}
      alt=""
      loading="lazy"
      className={zoom ? 'pl-brush-proj-fallback--zoom' : undefined}
    />
  );
}

interface BrushRowProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  volumeLoading: boolean;
  dataMin: number;
  dataMax: number;
  title: string;
  accentClass: 'accent-high' | 'accent-low';
  rangeMin: number;
  rangeMax: number;
  highlightColor: string;
  legendLabel: string;
  spatialSrc: string;
  stats: { label: string; value: string }[];
  spatialNote: string;
  showZoom?: boolean;
}

function BrushRow({
  timeline,
  densityData,
  volumeLoading,
  dataMin,
  dataMax,
  title,
  accentClass,
  rangeMin,
  rangeMax,
  highlightColor,
  legendLabel,
  spatialSrc,
  stats,
  spatialNote,
  showZoom = false,
}: BrushRowProps) {
  const brushRange: BrushRange = { min: rangeMin, max: rangeMax };

  return (
    <article className={`pl-brush-row ${accentClass}`}>
      <h3 className="pl-brush-row-title">{title}</h3>
      <div className={`pl-brush-grid${showZoom ? '' : ' pl-brush-grid--no-zoom'}`}>
        <figure className="pl-brush-cell">
          <figcaption>统计刷选</figcaption>
          <div className="pl-brush-media pl-brush-media--hist">
            <BrushHistogramPreview
              timeline={timeline}
              rangeMin={rangeMin}
              rangeMax={rangeMax}
              highlightColor={highlightColor}
              legendLabel={legendLabel}
            />
          </div>
        </figure>

        <div className="pl-brush-arrow" aria-hidden>
          ⇄
        </div>

        <figure className="pl-brush-cell pl-brush-spatial">
          <figcaption>XY 空间投影</figcaption>
          <div className="pl-brush-media">
            <BrushSpatialPreview
              densityData={densityData}
              loading={volumeLoading}
              dataMin={dataMin}
              dataMax={dataMax}
              brushRange={brushRange}
              fallbackSrc={spatialSrc}
            />
          </div>
        </figure>

        <aside className="pl-brush-stats">
          <h4>结构要点</h4>
          <ul>
            {stats.map((s) => (
              <li key={s.label}>
                <span className="pl-brush-stat-label">{s.label}</span>
                <span className="pl-brush-stat-value">{s.value}</span>
              </li>
            ))}
          </ul>
        </aside>

        {showZoom ? (
          <figure className="pl-brush-cell pl-brush-zoom">
            <figcaption>局部放大（亮脊）</figcaption>
            <div className="pl-brush-media pl-brush-media--zoom">
              <BrushSpatialPreview
                densityData={densityData}
                loading={volumeLoading}
                dataMin={dataMin}
                dataMax={dataMax}
                brushRange={brushRange}
                fallbackSrc={spatialSrc}
                zoom
              />
            </div>
          </figure>
        ) : null}
      </div>
      {spatialNote ? <p className="pl-brush-row-caption">{spatialNote}</p> : null}
    </article>
  );
}

interface PosterBrushVerifyProps {
  timeline: TimelineData;
  dataMin: number;
  dataMax: number;
  loading?: boolean;
}

export function PosterBrushVerify({
  timeline,
  dataMin,
  dataMax,
  loading = false,
}: PosterBrushVerifyProps) {
  const s = timeline.timesteps[99]!;
  const m = computeStoryMetrics(timeline);
  const [t99Data, setT99Data] = useState<Float32Array | null>(null);
  const [t99Loading, setT99Loading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setT99Loading(true);
    void loadTimestep(99)
      .then((vol) => {
        if (!cancelled) {
          setT99Data(vol);
          setT99Loading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setT99Data(null);
          setT99Loading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const volumeLoading = loading || t99Loading;

  return (
    <div className="pl-brush-verify">
      <BrushRow
        timeline={timeline}
        densityData={t99Data}
        volumeLoading={volumeLoading}
        dataMin={dataMin}
        dataMax={dataMax}
        title="Top 1% 高密度尾 → 宇宙网节点 / 纤维"
        accentClass="accent-high"
        rangeMin={s.p99}
        rangeMax={s.max}
        highlightColor="#f5c842"
        legendLabel={`Top 1%: ρ≥${s.p99.toFixed(2)}`}
        spatialSrc={figuresUrl(VIDEO_POSTER_BRUSH_VERIFY.top)}
        spatialNote="刷选高密度尾区后，XY 投影呈现丝状亮脊与节点聚集。"
        showZoom
        stats={[
          { label: '密度阈值', value: `ρ ≥ p99 (${s.p99.toFixed(2)})` },
          { label: '体积占比', value: `${(s.tailMassAboveP99 * 100).toFixed(2)}%` },
          { label: '质量占比', value: `${m.massAbovePct.toFixed(1)}%` },
          { label: '空间特征', value: '丝状节点聚集' },
        ]}
      />
      <BrushRow
        timeline={timeline}
        densityData={t99Data}
        volumeLoading={volumeLoading}
        dataMin={dataMin}
        dataMax={dataMax}
        title="Bottom 1% 低密度 → IGM 空洞"
        accentClass="accent-low"
        rangeMin={s.min}
        rangeMax={s.p01}
        highlightColor="#3dd6c6"
        legendLabel={`Bottom 1%: ρ≤${s.p01.toFixed(2)}`}
        spatialSrc={figuresUrl(VIDEO_POSTER_BRUSH_VERIFY.bottom)}
        spatialNote="低密度尾区在投影上几乎不可见——对应宇宙网之间的空洞背景。"
        stats={[
          { label: '密度阈值', value: `ρ ≤ p01 (${s.p01.toFixed(2)})` },
          { label: '体积占比', value: `${(s.tailMassBelowP01 * 100).toFixed(2)}%` },
          { label: '质量占比', value: `${m.massBelowPct.toFixed(1)}%` },
          { label: '空间特征', value: '弥散空洞背景' },
        ]}
      />
    </div>
  );
}
