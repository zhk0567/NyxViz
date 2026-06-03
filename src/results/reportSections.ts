export interface ReportSection {
  id: string;
  title: string;
  mdFile: string;
  galleryTitle?: string;
  figures: string[];
}

export interface StorySection {
  id: string;
  num: string;
  title: string;
  subtitle: string;
  figures: string[];
  heroFigure?: string;
}

export const STORY_SECTIONS: StorySection[] = [
  {
    id: 'story-01',
    num: '01',
    title: '引言：宇宙网诞生',
    subtitle:
      'Nyx 128³ 重子气体密度模拟——在引力作用下，微涨落逐步分化为 void、filament 与 node 的大尺度结构。',
    figures: [],
    heroFigure: 'task1_hero_poster.png',
  },
  {
    id: 'story-02',
    num: '02',
    title: '演化全景：100 步结构生长',
    subtitle: 't=0/25/50/75/99 五帧体渲染，统一 log 色标，展示由均匀雾状到宇宙网拓扑的可见转变。',
    figures: [
      'task1_vol_strip.png',
      'task1_vol_t0000.png',
      'task1_vol_t0025.png',
      'task1_vol_t0050.png',
      'task1_vol_t0075.png',
      'task1_vol_t0099.png',
    ],
    heroFigure: 'task1_vol_strip.png',
  },
  {
    id: 'story-03',
    num: '03',
    title: '定量分析：密度两极化',
    subtitle: '100 步 log 直方图与 mean/p99/σ 时序曲线，量化团块化与右尾增厚。',
    figures: [
      'task3_story_panel.png',
      'task3_hist_overlay.png',
      'task3_evolution_metrics.png',
      'task3_metrics_timeline.png',
    ],
    heroFigure: 'task3_story_panel.png',
  },
  {
    id: 'story-04',
    num: '04',
    title: '统计↔空间：刷选验证',
    subtitle: 'Top 1%、90–99% 纤维带与 Bottom 1% 预设，在直方图、体渲染与 XY 投影间双向联动。',
    figures: [
      'task4_brush_rows.png',
      'task4_brush_triptych.png',
      'task4_spatial_to_stats.png',
      'task4_hist_brush_top1.png',
      'task4_brush_top1.png',
    ],
    heroFigure: 'task4_brush_rows.png',
  },
  {
    id: 'story-05',
    num: '05',
    title: '科学发现摘要',
    subtitle: '四条可检验结论，均来自 timeline.json 与刷选/投影实验。',
    figures: ['task5_mass_pie.png', 'task2_evolution_story.png'],
  },
  {
    id: 'story-06',
    num: '06',
    title: '分析流程',
    subtitle: '从 Nyx 体数据到体渲染、百步统计、相空间刷选与科学结论的完整管线。',
    figures: ['task0_story_flow.png'],
    heroFigure: 'task0_story_flow.png',
  },
];

export const REPORT_SECTIONS: ReportSection[] = [
  {
    id: 'task1',
    title: '任务一：体数据渲染与密度演化',
    mdFile: 'task1_volume.md',
    galleryTitle: '体渲染关键帧（t = 0 / 25 / 50 / 75 / 99）',
    figures: [
      'task1_vol_strip.png',
      'task1_vol_t0000.png',
      'task1_vol_t0025.png',
      'task1_vol_t0050.png',
      'task1_vol_t0099.png',
    ],
  },
  {
    id: 'task2',
    title: '任务二：宇宙密度演化规律归纳',
    mdFile: 'task2_evolution.md',
    galleryTitle: '演化规律配图',
    figures: [
      'task2_evolution_story.png',
      'task3_hist_overlay.png',
      'task1_vol_t0000.png',
      'task1_vol_t0099.png',
    ],
  },
  {
    id: 'task3',
    title: '任务三：时序密度对数直方图统计',
    mdFile: 'task3_histogram.md',
    galleryTitle: '时序统计图',
    figures: [
      'task3_hist_overlay.png',
      'task3_metrics_timeline.png',
      'task3_evolution_metrics.png',
      'task3_peak_drift.png',
    ],
  },
  {
    id: 'task4',
    title: '任务四：相空间交互刷选可视分析',
    mdFile: 'task4_brush.md',
    galleryTitle: '刷选联动验证',
    figures: [
      'task4_spatial_to_stats.png',
      'task4_brush_triptych.png',
      'task4_hist_brush_top1.png',
      'task4_brush_top1.png',
      'task4_brush_bottom1.png',
    ],
  },
];

export function figureUrl(name: string): string {
  return `/figures/${name}`;
}

export function resolveFigureCandidates(name: string): string[] {
  if (name === 'task1_hero_poster.png') {
    return [name, 'task1_vol_t0099.png', 'task1_vol_strip.png'];
  }
  if (name.startsWith('task1_vol_')) {
    const t = name.replace('task1_vol_', '').replace('.png', '');
    return [name, `task1_slice_${t}.png`, `task1_${t}.png`];
  }
  return [name];
}

export const EVOLUTION_PHASES = [
  { range: 't=0–29', label: '线性期', detail: '涨落初生，整体均匀' },
  { range: 't=30–69', label: '非线性增长', detail: '丝状结构连通' },
  { range: 't=70–99', label: '宇宙网形成', detail: 'void–filament–node 清晰' },
] as const;
