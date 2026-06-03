import type { ReactNode } from 'react';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { DensityProjection } from '@/spatial/DensityProjection';
import type { BrushRange, TimelineData } from '@/data/types';

interface BrushVerifySectionProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  volumeReady: boolean;
  loading: boolean;
  brushRange: BrushRange | null;
  domainMin: number;
  domainMax: number;
  stats: TimelineData['timesteps'][0] | undefined;
  onTop1: () => void;
  onBottom1: () => void;
  onFilament: () => void;
  onClear: () => void;
}

function VerifyRow({
  tone,
  title,
  bullets,
  histFigure,
  projection,
  histInteractive,
}: {
  tone: 'top' | 'bottom';
  title: string;
  bullets: string[];
  histFigure: string;
  projection: ReactNode;
  histInteractive?: ReactNode;
}) {
  return (
    <div className={`verify-row verify-row-${tone}`}>
      <div className="verify-cell verify-hist">
        <span className="verify-cell-title">统计刷选</span>
        {histInteractive ?? (
          <img src={histFigure} alt="" className="verify-static-img" loading="lazy" />
        )}
      </div>
      <div className="verify-cell verify-spatial">
        <span className="verify-cell-title">空间投影</span>
        {projection}
      </div>
      <div className="verify-cell verify-notes">
        <span className="verify-cell-title">{title}</span>
        <ul>
          {bullets.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      </div>
      <div className="verify-cell verify-inset">
        <span className="verify-cell-title">结构示意</span>
        <img
          src={tone === 'top' ? '/figures/task4_brush_top1.png' : '/figures/task4_brush_bottom1.png'}
          alt=""
          className="verify-static-img verify-inset-img"
          loading="lazy"
        />
      </div>
    </div>
  );
}

export function BrushVerifySection({
  timeline,
  densityData,
  volumeReady,
  loading,
  brushRange,
  domainMin,
  domainMax,
  stats,
  onTop1,
  onBottom1,
  onFilament,
  onClear,
}: BrushVerifySectionProps) {
  const projection =
    densityData && volumeReady && !loading ? (
      <DensityProjection
        data={densityData}
        brushRange={brushRange}
        axis="xy"
        domainMin={domainMin}
        domainMax={domainMax}
        className="projection-verify"
      />
    ) : (
      <p className="panel-placeholder">加载体数据…</p>
    );

  const topBullets = stats
    ? [
        `ρ ≥ p99 = ${stats.p99.toFixed(2)}`,
        `体积占比 ${(stats.tailMassAboveP99 * 100).toFixed(2)}%`,
        `质量占比 ${((stats.massFractionAboveP99 ?? 0) * 100).toFixed(1)}%`,
        '空间：节点 / 纤维聚集',
      ]
    : [];

  const bottomBullets = stats
    ? [
        `ρ ≤ p01 = ${stats.p01.toFixed(2)}`,
        `体积占比 ${(stats.tailMassBelowP01 * 100).toFixed(2)}%`,
        `质量占比 ${((stats.massFractionBelowP01 ?? 0) * 100).toFixed(1)}%`,
        '空间：弥散 IGM 空洞',
      ]
    : [];

  return (
    <div className="brush-verify">
      <div className="brush-presets story-presets">
        <button type="button" className="preset preset-top" onClick={onTop1}>
          Top 1% 节点
        </button>
        <button type="button" className="preset preset-filament" onClick={onFilament}>
          90–99% 纤维
        </button>
        <button type="button" className="preset preset-bottom" onClick={onBottom1}>
          Bottom 1% 空洞
        </button>
        <button type="button" className="preset preset-clear" onClick={onClear}>
          清除刷选
        </button>
      </div>

      <VerifyRow
        tone="top"
        title="Top 1% 高密度尾"
        bullets={topBullets}
        histFigure="/figures/task4_hist_brush_top1.png"
        projection={projection}
      />

      <div className="verify-hist-live">
        <h4>交互直方图（拖拽框选密度区间）</h4>
        <DensityHistogram timeline={timeline} />
      </div>

      <VerifyRow
        tone="bottom"
        title="Bottom 1% 低密度区"
        bullets={bottomBullets}
        histFigure="/figures/task4_hist_brush_bottom1.png"
        projection={
          densityData && volumeReady && !loading ? (
            <DensityProjection
              data={densityData}
              brushRange={
                stats
                  ? { min: stats.min, max: stats.p01 }
                  : brushRange
              }
              axis="xy"
              domainMin={domainMin}
              domainMax={domainMax}
              className="projection-verify"
            />
          ) : (
            <p className="panel-placeholder">加载体数据…</p>
          )
        }
      />

      <p className="verify-conclusion">
        高密度区对应宇宙网 <strong>节点/纤维</strong>，低密度区对应{' '}
        <strong>IGM 空洞</strong>——统计刷选与空间投影一致，非随机散点。
      </p>
    </div>
  );
}
