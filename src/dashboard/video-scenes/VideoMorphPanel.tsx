import { EvolutionThumbnails } from '@/dashboard/EvolutionThumbnails';
import { NARRATION_LABELS } from '@/video/narrationLabels';
import type { TimelineData } from '@/data/types';

const MORPH_STAGES = [
  { t: 0, label: 't=0 · 均匀雾状' },
  { t: 25, label: 't=25 · 丝状初现' },
  { t: 50, label: 't=50 · 连通增强' },
  { t: 75, label: 't=75 · 结构成形' },
  { t: 99, label: 't=99 · 宇宙网' },
] as const;

interface VideoMorphPanelProps {
  timeline: TimelineData;
  timestep: number;
  stats: TimelineData['timesteps'][0];
  onSelectTimestep: (t: number) => void;
}

export function VideoMorphPanel({
  timeline,
  timestep,
  stats,
  onSelectTimestep,
}: VideoMorphPanelProps) {
  const stage =
    MORPH_STAGES.find((s) => s.t === timestep)?.label ??
    `t=${timestep}`;

  return (
    <div className="vd-scene-panel vd-morph-panel">
      <header className="vd-scene-panel-head">
        <h3>形态演化 · 五代表步</h3>
        <p className="vd-scene-panel-sub">点击缩略图标签切换 t；点击图片放大</p>
      </header>

      <EvolutionThumbnails
        timeline={timeline}
        active={timestep}
        onSelect={onSelectTimestep}
      />

      <p className="vd-morph-stage" aria-live="polite">
        {stage}
      </p>

      <dl className="vd-spec-dl vd-morph-readout-dl">
        <div>
          <dt>{NARRATION_LABELS.sigma}</dt>
          <dd>{stats.std.toFixed(4)}</dd>
        </div>
        <div>
          <dt>p99</dt>
          <dd>{stats.p99.toFixed(4)}</dd>
        </div>
        <div>
          <dt>{NARRATION_LABELS.mean}</dt>
          <dd>{stats.mean.toFixed(4)}</dd>
        </div>
      </dl>
    </div>
  );
}
