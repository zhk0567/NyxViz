import { HorizontalColorLegend } from '@/dashboard/HorizontalColorLegend';
import { EvolutionThumbnails } from '@/dashboard/EvolutionThumbnails';
import {
  computeStoryMetrics,
  DISCOVERY_CARDS,
  discoveryChip,
} from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';
import type { ReactNode } from 'react';

export interface CosmicPosterRepresentativeProps {
  timeline: TimelineData;
  dataMin: number;
  dataMax: number;
  timestep: number;
  onSelectTimestep: (t: number) => void;
  heroSlot?: ReactNode;
  showToolbar?: boolean;
  onExplore?: () => void;
  onSavePoster?: () => void;
  saveState?: { status: string; message?: string };
}

/** 代表图 / 提交封面：横向单屏（约 16∶9，非长卷） */
export function CosmicPosterRepresentative({
  timeline,
  dataMin,
  dataMax,
  timestep,
  onSelectTimestep,
  heroSlot,
  showToolbar = false,
  onExplore,
  onSavePoster,
  saveState,
}: CosmicPosterRepresentativeProps) {
  const metrics = computeStoryMetrics(timeline);

  return (
    <div className="poster-layout poster-representative-capture">
      <header className="pr-cover-head">
        <div className="pr-cover-brand">
          <span className="pr-cover-num">01</span>
          <div>
            <h1 className="pr-cover-title">宇宙网诞生记</h1>
            <p className="pr-cover-sub">Nyx 128³ · vtk.js 体渲染 · 百步统计 · 相空间刷选</p>
          </div>
        </div>
        <ul className="pr-cover-kpis" aria-label="核心指标">
          <li>
            <span>σ 增幅</span>
            <strong>+{metrics.sigmaPct.toFixed(1)}%</strong>
          </li>
          <li>
            <span>p99−p01</span>
            <strong>+{metrics.spanPct.toFixed(1)}%</strong>
          </li>
          <li>
            <span>≥p99 体积</span>
            <strong>{metrics.tailAbovePct.toFixed(2)}%</strong>
          </li>
          <li>
            <span>t={timestep}</span>
            <strong>σ={metrics.s99.std.toFixed(4)}</strong>
          </li>
        </ul>
        {showToolbar ? (
          <div className="pr-top-actions">
            {onSavePoster ? (
              <button
                type="button"
                className="poster-explore-btn pr-save-btn"
                onClick={onSavePoster}
                disabled={saveState?.status === 'saving'}
              >
                {saveState?.status === 'saving' ? '保存中…' : '保存代表图'}
              </button>
            ) : null}
            <button type="button" className="poster-explore-btn" onClick={onExplore}>
              交互探索
            </button>
            <a href="/video.html" className="poster-top-link">
              录屏版
            </a>
          </div>
        ) : null}
      </header>

      {saveState?.status === 'saved' || saveState?.status === 'error' ? (
        <p
          className={`pr-save-toast pr-save-toast--${saveState.status === 'saved' ? 'ok' : 'err'}`}
          role="status"
        >
          {saveState.message}
        </p>
      ) : null}

      <div className="pr-cover-hero-wrap">
        <div className="pr-cover-hero pl-hero-frame">{heroSlot}</div>
        <HorizontalColorLegend min={dataMin} max={dataMax} />
      </div>

      <section className="pr-cover-evo" aria-label="百步演化">
        <EvolutionThumbnails
          timeline={timeline}
          active={timestep}
          onSelect={onSelectTimestep}
        />
      </section>

      <section className="pr-cover-chips" aria-label="关键发现">
        {DISCOVERY_CARDS.map((card) => (
          <article key={card.id} className="pr-cover-chip">
            <span className="pr-cover-chip-num">{card.icon}</span>
            <div>
              <h4>{card.title}</h4>
              <p>{discoveryChip(card.id, metrics)}</p>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
