import type { ReactNode } from 'react';
import type { VideoStatsBundle } from '@/data/statsLoader';
import type { BrushPresetId } from '@/data/brushPreset';
import type { BrushRange, TimelineData } from '@/data/types';
import type { ChartSizeOptions } from '@/hooks/useChartSize';
import type { TfParams, VisualStyle } from '@/volume/transferFunction';
import type { VolumeQuality } from '@/volume/VolumeScene';
import type { VideoSceneId, VideoSceneMeta } from '@/video/sceneRegistry';

export interface VideoSceneLayoutProps {
  sceneId: VideoSceneId;
  sceneMeta: VideoSceneMeta;
  videoStats: VideoStatsBundle;
  timeline: TimelineData;
  densityData: Float32Array | null;
  loading: boolean;
  timestep: number;
  stats: TimelineData['timesteps'][0] | undefined;
  dataMin: number;
  dataMax: number;
  volumeDataMin?: number;
  volumeDataMax?: number;
  tfParams: TfParams;
  volumeQuality: VolumeQuality;
  qualityPhase: 'draft' | 'final';
  volumeReady: boolean;
  onVolumeRendered: () => void;
  onVolumeCameraActivity?: () => void;
  brushRange: BrushRange | null;
  highlightMin?: number;
  highlightMax?: number;
  volumeRatio: string | null;
  onTop1: () => void;
  onBottom1: () => void;
  onFilament: () => void;
  onClear: () => void;
  activePreset: BrushPresetId | null;
  histOverlaySize?: ChartSizeOptions;
  histogramSizeOpts?: ChartSizeOptions;
  keepVolumeAlive: boolean;
  volumeEverMounted: boolean;
  onVolumeMounted: () => void;
  onSelectTimestep: (t: number) => void;
  volumeInteractive?: boolean;
  volumeFocusOnClick?: boolean;
  volumeCameraZoom?: number;
  /** 录屏浏览：场景条嵌入 main-stack 顶栏，避免额外 grid 行挤压布局 */
  recordBrowse?: ReactNode;
}

export interface VolumePaneProps {
  densityData: Float32Array | null;
  loading: boolean;
  timestep: number;
  dataMin: number;
  dataMax: number;
  tfParams: TfParams;
  volumeQuality: VolumeQuality;
  qualityPhase: 'draft' | 'final';
  highlightMin?: number;
  highlightMax?: number;
  onVolumeRendered: () => void;
  onVolumeCameraActivity?: () => void;
  renderActive: boolean;
  progressiveQuality: boolean;
  interactiveCamera?: boolean;
  focusOnClick?: boolean;
  focusDensityThreshold?: number;
  onFocusChange?: (focused: boolean) => void;
  performanceMode?: 'video' | 'interactive';
  cameraZoom?: number;
  visualStyle?: VisualStyle;
}
