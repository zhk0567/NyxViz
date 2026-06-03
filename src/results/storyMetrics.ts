import type { TimelineData } from '@/data/types';

export interface StoryMetrics {
  s0: TimelineData['timesteps'][0];
  s99: TimelineData['timesteps'][99];
  sigmaPct: number;
  span0: number;
  span99: number;
  spanPct: number;
  tailAbovePct: number;
  tailBelowPct: number;
  massAbovePct: number;
  massBelowPct: number;
  filamentBand: string;
}

export function computeStoryMetrics(timeline: TimelineData): StoryMetrics {
  const s0 = timeline.timesteps[0]!;
  const s99 = timeline.timesteps[99]!;
  const span0 = s0.p99 - s0.p01;
  const span99 = s99.p99 - s99.p01;
  const sigmaPct = ((s99.std - s0.std) / s0.std) * 100;
  const spanPct = ((span99 - span0) / span0) * 100;

  return {
    s0,
    s99,
    sigmaPct,
    span0,
    span99,
    spanPct,
    tailAbovePct: s99.tailMassAboveP99 * 100,
    tailBelowPct: s99.tailMassBelowP01 * 100,
    massAbovePct: (s99.massFractionAboveP99 ?? 0) * 100,
    massBelowPct: (s99.massFractionBelowP01 ?? 0) * 100,
    filamentBand: `ρ∈[${s99.p90.toFixed(2)}, ${s99.p99.toFixed(2)}]`,
  };
}

export const DISCOVERY_CARDS = [
  {
    id: 'clump',
    title: '引力驱动团块化',
    icon: '01',
  },
  {
    id: 'polarize',
    title: '密度分布两极化',
    icon: '02',
  },
  {
    id: 'tail',
    title: '少数致密承载可见结构',
    icon: '03',
  },
  {
    id: 'link',
    title: '统计—空间可双向验证',
    icon: '04',
  },
] as const;

export function discoveryDetail(
  id: (typeof DISCOVERY_CARDS)[number]['id'],
  m: StoryMetrics,
): string {
  switch (id) {
    case 'clump':
      return `σ 由 ${m.s0.std.toFixed(4)} 升至 ${m.s99.std.toFixed(4)}（+${m.sigmaPct.toFixed(1)}%），分位跨度 p99−p01 由 ${m.span0.toFixed(3)} 增至 ${m.span99.toFixed(3)}（+${m.spanPct.toFixed(1)}%）。`;
    case 'polarize':
      return `偏度维持右偏（${m.s0.skewness.toFixed(4)}→${m.s99.skewness.toFixed(4)}），早期主峰集中、后期右尾增厚，void 与致密节点并存。`;
    case 'tail':
      return `≥p99 体素约占体积 ${m.tailAbovePct.toFixed(2)}%、质量 ${m.massAbovePct.toFixed(1)}%；≤p01 体积 ${m.tailBelowPct.toFixed(2)}%、质量 ${m.massBelowPct.toFixed(1)}%——少数致密区承载可见结构。`;
    case 'link':
      return `Top 1% 刷选呈丝状聚集；纤维带 ${m.filamentBand} 与亮脊反查一致，非随机散点。`;
    default:
      return '';
  }
}
