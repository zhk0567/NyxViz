import { InfographicHeader } from '@/dashboard/InfographicHeader';
import { MetaStrip } from '@/dashboard/MetaStrip';
import { VerticalColorLegend } from '@/dashboard/VerticalColorLegend';
import { EvolutionThumbnails } from '@/dashboard/EvolutionThumbnails';
import { PhaseTrack } from '@/dashboard/PhaseTrack';
import { DiscoveryCards } from '@/dashboard/DiscoveryCards';
import { evolutionPhase } from '@/dashboard/evolutionPhase';
import { PosterFlowchart } from '@/dashboard/PosterFlowchart';
import { PosterBrushVerify } from '@/dashboard/PosterBrushVerify';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';
import type { ValidationExtendedData } from '@/data/statsLoader';

import { PosterStatsSection } from '@/dashboard/PosterStatsSection';
import type { ReactNode } from 'react';

export interface CosmicPosterLayoutProps {
  timeline: TimelineData;
  dataMin: number;
  dataMax: number;
  timestep: number;
  onSelectTimestep: (t: number) => void;
  heroSlot?: ReactNode;
  loading?: boolean;
  validationExtended?: ValidationExtendedData | null;
}

export function CosmicPosterLayout({
  timeline,
  dataMin,
  dataMax,
  timestep,
  onSelectTimestep,
  heroSlot,
  loading = false,
  validationExtended = null,
}: CosmicPosterLayoutProps) {
  const metrics = computeStoryMetrics(timeline);
  const phase = evolutionPhase(timestep);
  const stepStats = timeline.timesteps[timestep] ?? metrics.s99;

  return (
    <div className="poster-layout">
      <section id="story-01" className="pl-section pl-s01">
        <InfographicHeader
          num="01"
          title="宇宙网诞生记"
          subtitle="基于 Nyx 模拟的 128³ 气体密度数据，揭示宇宙大尺度结构（宇宙网）的形成过程"
        />
        <div className="pl-s01-split">
          <aside className="pl-s01-left">
            <MetaStrip />
            <VerticalColorLegend min={dataMin} max={dataMax} />
            <dl className="pl-s01-stats">
              <div className="pl-s01-stat">
                <dt>当前步 σ</dt>
                <dd>
                  t={timestep} · {stepStats.std.toFixed(4)}
                </dd>
              </div>
              <div className="pl-s01-stat">
                <dt>p99 − p01</dt>
                <dd>+{metrics.spanPct.toFixed(1)}%</dd>
              </div>
            </dl>
          </aside>
          <div className="pl-hero-frame">
            {heroSlot ?? (
              <img
                src="/figures/task1_vol_t0099.png"
                alt="t=99 宇宙网体渲染"
                className="pl-hero-img"
                onError={(e) => {
                  e.currentTarget.src = '/figures/task1_slice_t0099.png';
                }}
              />
            )}
          </div>
        </div>
      </section>

      <section id="story-02" className="pl-section pl-s02">
        <InfographicHeader
          num="02"
          title="宇宙如何长大：100 步演化全景"
          subtitle="从均匀气体到纤维、节点分明的宇宙网拓扑"
        />
        <EvolutionThumbnails
          timeline={timeline}
          active={timestep}
          onSelect={onSelectTimestep}
        />
        <PhaseTrack phaseId={phase.id} />
      </section>

      <section id="story-03" className="pl-section pl-s03">
        <InfographicHeader
          num="03"
          title="用数字证明变化：密度分布的两极化演化"
          subtitle={`σ +${metrics.sigmaPct.toFixed(1)}% · p99−p01 +${metrics.spanPct.toFixed(1)}% · 数据来自 timeline.json`}
        />
        <PosterStatsSection
          timeline={timeline}
          validationExtended={validationExtended}
        />
      </section>

      <section id="story-04" className="pl-section pl-s04">
        <InfographicHeader
          num="04"
          title="统计与空间验证：相空间刷选与结构定位"
          subtitle="Top 1% / Bottom 1% 在直方图、体渲染与投影间双向联动"
        />
        <PosterBrushVerify
          timeline={timeline}
          dataMin={dataMin}
          dataMax={dataMax}
          loading={loading}
        />
        <p className="pl-conclusion">
          高密度区 → 节点/纤维聚集；低密度区 → IGM 空洞。统计刷选与空间结构一致。
        </p>
      </section>

      <section id="story-05" className="pl-section pl-s05">
        <InfographicHeader num="05" title="关键科学发现（t=99）" />
        <DiscoveryCards timeline={timeline} variant="poster" />
      </section>

      <section id="story-06" className="pl-section pl-s06">
        <InfographicHeader
          num="06"
          title="整体分析流程图"
          subtitle="从涨落到宇宙网 · Nyx 数据 → 可视化 → 统计 → 刷选 → 验证 → 结论"
        />
        <PosterFlowchart />
      </section>
    </div>
  );
}
