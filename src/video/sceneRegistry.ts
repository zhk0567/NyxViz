import type { BrushPresetId } from '@/data/brushPreset';
import { NARRATION_LABELS } from '@/video/narrationLabels';

export const VIDEO_SCENE_IDS = [
  'intro',
  'task1-tf',
  'task1-morph',
  'task2-evolution',
  'task2-void',
  'task2-cases',
  'task2-spatial',
  'task3-hist',
  'task4-brush',
  'task4-validate',
  'findings',
] as const;

export type VideoSceneId = (typeof VIDEO_SCENE_IDS)[number];

export type SceneLayoutKind =
  | 'full'
  | 'focus-left'
  | 'focus-center'
  | 'focus-right'
  | 'focus-bottom'
  | 'dedicated';

export type SceneBodyColumns =
  | 'default'
  | 'tf'
  | 'morph'
  | 'void'
  | 'cases'
  | 'brush'
  | 'spatial';

export interface SceneContentFigure {
  src: string;
  caption: string;
  alt?: string;
}

export interface SceneContent {
  headline?: string;
  figures?: SceneContentFigure[];
  kpiMode?: 'sigma' | 'variance';
}

export interface SceneLayoutTokens {
  /** 底部发现卡高度（px）；0 表示不显示 */
  findingsHeight: number;
  /** 录屏模式下发现卡高度（可选，默认同 findingsHeight） */
  recordFindingsHeight?: number;
  bodyColumns: SceneBodyColumns;
  /** 中栏体渲染最小高度（px） */
  centerMinHeight: number;
  /** 录屏模式（非 intro）中栏最小高度 */
  recordCenterMinHeight?: number;
}

export interface VideoSceneMeta {
  id: VideoSceneId;
  title: string;
  narrationIndex: number;
  defaultTimestep: number;
  brushPreset: BrushPresetId | null;
  layout: SceneLayoutKind;
  showLeft: boolean;
  showCenter: boolean;
  showRight: boolean;
  showFindings: boolean;
  layoutTokens: SceneLayoutTokens;
  content: SceneContent;
}

/** 录屏页预热的常用时间步 */
export const VIDEO_WARM_TIMESTEPS = [0, 25, 50, 75, 99] as const;

export const VIDEO_SCENES: VideoSceneMeta[] = [
  {
    id: 'intro',
    title: '开篇 · 三栏总览',
    narrationIndex: 0,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'full',
    showLeft: true,
    showCenter: true,
    showRight: true,
    showFindings: true,
    layoutTokens: {
      findingsHeight: 252,
      recordFindingsHeight: 268,
      bodyColumns: 'default',
      centerMinHeight: 420,
    },
    content: {
      headline: NARRATION_LABELS.introHeadline,
      kpiMode: 'sigma',
    },
  },
  {
    id: 'task1-tf',
    title: '任务一 · 传递函数与光照',
    narrationIndex: 1,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'focus-left',
    showLeft: true,
    showCenter: false,
    showRight: true,
    showFindings: false,
    layoutTokens: {
      findingsHeight: 0,
      bodyColumns: 'tf',
      centerMinHeight: 440,
      recordCenterMinHeight: 460,
    },
    content: {},
  },
  {
    id: 'task1-morph',
    title: '任务一 · 形态演化',
    narrationIndex: 1,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'focus-center',
    showLeft: false,
    showCenter: true,
    showRight: true,
    showFindings: false,
    layoutTokens: {
      findingsHeight: 0,
      bodyColumns: 'morph',
      centerMinHeight: 440,
      recordCenterMinHeight: 460,
    },
    content: {},
  },
  {
    id: 'task2-evolution',
    title: '任务二 · 演化量化',
    narrationIndex: 2,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'focus-left',
    showLeft: true,
    showCenter: false,
    showRight: true,
    showFindings: false,
    layoutTokens: { findingsHeight: 0, bodyColumns: 'default', centerMinHeight: 0 },
    content: {
      kpiMode: 'sigma',
      figures: [
        {
          src: '/figures/task2_evolution_panel_0.png',
          caption: '分位跨度 p99−p01（团块化）',
        },
        {
          src: '/figures/task2_evolution_panel_1.png',
          caption: '标准差 σ(t)',
        },
        {
          src: '/figures/task2_evolution_panel_2.png',
          caption: '高密度尾体积占比 ≥p99 (%)',
        },
        {
          src: '/figures/task2_evolution_panel_3.png',
          caption: '偏度 skew(t)',
        },
      ],
    },
  },
  {
    id: 'task2-void',
    title: '任务二 · void 双阈值',
    narrationIndex: 2,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'dedicated',
    showLeft: false,
    showCenter: false,
    showRight: false,
    showFindings: false,
    layoutTokens: { findingsHeight: 0, bodyColumns: 'void', centerMinHeight: 0 },
    content: {},
  },
  {
    id: 'task2-cases',
    title: '任务二 · 案例 A/B/C',
    narrationIndex: 2,
    defaultTimestep: 99,
    brushPreset: 'top',
    layout: 'focus-left',
    showLeft: true,
    showCenter: true,
    showRight: false,
    showFindings: false,
    layoutTokens: {
      findingsHeight: 0,
      bodyColumns: 'cases',
      centerMinHeight: 420,
      recordCenterMinHeight: 480,
    },
    content: {},
  },
  {
    id: 'task2-spatial',
    title: '任务二 · 空间统计',
    narrationIndex: 2,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'dedicated',
    showLeft: false,
    showCenter: false,
    showRight: false,
    showFindings: false,
    layoutTokens: { findingsHeight: 0, bodyColumns: 'spatial', centerMinHeight: 0 },
    content: {},
  },
  {
    id: 'task3-hist',
    title: '任务三 · 密度时序统计',
    narrationIndex: 3,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'full',
    showLeft: true,
    showCenter: true,
    showRight: true,
    showFindings: false,
    layoutTokens: {
      findingsHeight: 0,
      bodyColumns: 'default',
      centerMinHeight: 420,
      recordCenterMinHeight: 440,
    },
    content: {
      figures: [
        { src: '/figures/task3_peak_drift.png', caption: '主峰漂移' },
        { src: '/figures/task3_evolution_metrics.png', caption: 'σ · 偏度 · 分位跨度' },
      ],
    },
  },
  {
    id: 'task4-brush',
    title: '任务四 · 相空间刷选',
    narrationIndex: 4,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'focus-right',
    showLeft: false,
    showCenter: true,
    showRight: true,
    showFindings: false,
    layoutTokens: { findingsHeight: 0, bodyColumns: 'brush', centerMinHeight: 420 },
    content: {},
  },
  {
    id: 'task4-validate',
    title: '任务四 · 验证与早停',
    narrationIndex: 4,
    defaultTimestep: 99,
    brushPreset: 'top',
    layout: 'focus-right',
    showLeft: false,
    showCenter: false,
    showRight: true,
    showFindings: false,
    layoutTokens: { findingsHeight: 0, bodyColumns: 'brush', centerMinHeight: 0 },
    content: {},
  },
  {
    id: 'findings',
    title: '发现卡 · 结语',
    narrationIndex: 5,
    defaultTimestep: 99,
    brushPreset: null,
    layout: 'focus-bottom',
    showLeft: false,
    showCenter: false,
    showRight: false,
    showFindings: true,
    layoutTokens: {
      /* 专场景由 flex 撑满视口；此处仅作 intro 条带等场景的 min 回退 */
      findingsHeight: 420,
      recordFindingsHeight: 440,
      bodyColumns: 'default',
      centerMinHeight: 0,
    },
    content: {},
  },
];

export function resolveFindingsHeight(
  meta: VideoSceneMeta,
  recordMode: boolean,
): number {
  if (!meta.showFindings) return 0;
  const tokens = meta.layoutTokens;
  if (recordMode && tokens.recordFindingsHeight != null) {
    return tokens.recordFindingsHeight;
  }
  return tokens.findingsHeight;
}

export function resolveCenterMinHeight(
  meta: VideoSceneMeta,
  recordMode: boolean,
): number {
  const tokens = meta.layoutTokens;
  if (recordMode && meta.id !== 'intro' && tokens.recordCenterMinHeight != null) {
    return tokens.recordCenterMinHeight;
  }
  return tokens.centerMinHeight;
}

export function sceneLayoutStyle(
  meta: VideoSceneMeta,
  recordMode: boolean,
): Record<string, string> {
  const findingsH = resolveFindingsHeight(meta, recordMode);
  const centerMin = resolveCenterMinHeight(meta, recordMode);
  return {
    '--vd-findings-h': `${findingsH}px`,
    '--scene-findings-h': `${findingsH}px`,
    '--scene-center-min-h': centerMin > 0 ? `${centerMin}px` : '0px',
  };
}

const SCENE_MAP = new Map(VIDEO_SCENES.map((s) => [s.id, s]));

export function parseSceneId(raw: string | null): VideoSceneId {
  if (raw && SCENE_MAP.has(raw as VideoSceneId)) {
    return raw as VideoSceneId;
  }
  return 'intro';
}

export function getSceneMeta(id: VideoSceneId): VideoSceneMeta {
  return SCENE_MAP.get(id)!;
}

export function sceneUrl(id: VideoSceneId, record = false): string {
  const params = new URLSearchParams();
  if (record) params.set('record', '1');
  if (id !== 'intro') params.set('scene', id);
  const q = params.toString();
  return q ? `/video.html?${q}` : '/video.html';
}
