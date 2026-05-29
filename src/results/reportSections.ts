export interface ReportSection {
  id: string;
  title: string;
  mdFile: string;
  galleryTitle?: string;
  figures: string[];
}

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
    galleryTitle: '刷选联动：Top 1% / Bottom 1% 验证',
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

/** Slice fallback names when vtk capture PNGs are absent. */
export function resolveFigureCandidates(name: string): string[] {
  if (name.startsWith('task1_vol_')) {
    const t = name.replace('task1_vol_', '').replace('.png', '');
    return [name, `task1_slice_${t}.png`, `task1_${t}.png`];
  }
  return [name];
}
