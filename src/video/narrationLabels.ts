/** 旁白 TTS 统一用语标签 */
export const NARRATION_LABELS = {
  sigma: '密度标准差 σ',
  tailAbove: '≥p99 体积占比',
  tailBelow: 'Bottom 1% 体积占比',
  span: 'p99−p01 分位跨度',
  mean: '平均密度 μ',
  introHeadline:
    '左栏百步直方图与趋势 · 中栏体渲染 · 右栏刷选与投影',
  precomputeHint: '请运行 npm run precompute 生成 public/stats/',
} as const;

export type KpiDisplayMode = 'sigma' | 'variance';

export interface KpiItem {
  label: string;
  value: string;
  badge?: string;
  tone: 'gold' | 'orange' | 'cyan' | 'blue';
}
