import { evolutionPhase, MARK_STEPS } from '@/dashboard/evolutionPhase';
import type { TimelineData } from '@/data/types';

const PHASES = [
  { id: '01', range: 't=0–29', label: '线性涨落' },
  { id: '02', range: 't=30–69', label: '非线性成形' },
  { id: '03', range: 't=70–99', label: '宇宙网形成' },
] as const;

export interface VideoDashboardHeaderProps {
  timestep: number;
  sliderStep: number;
  timestepCount: number;
  stats: TimelineData['timesteps'][0] | undefined;
  recordMode: boolean;
  onSliderChange: (v: number) => void;
  onSliderDragStart: () => void;
  onSliderCommit: () => void;
  onSelectTimestep: (t: number) => void;
}

export function VideoDashboardHeader({
  timestep,
  sliderStep,
  timestepCount,
  stats,
  recordMode,
  onSliderChange,
  onSliderDragStart,
  onSliderCommit,
  onSelectTimestep,
}: VideoDashboardHeaderProps) {
  const phase = evolutionPhase(timestep);
  const activePhaseIdx =
    phase.id === 'linear' ? 0 : phase.id === 'nonlinear' ? 1 : 2;

  return (
    <header className="vd-header">
      <div className="vd-header-left">
        <span className="vd-brand">NyxViz v2.0</span>
        <div className="vd-meta-chips">
          <span>Nyx 128³</span>
          <span>ρ 气体密度</span>
          <span>
            时间步 {timestep + 1}/{timestepCount}
          </span>
        </div>
      </div>

      <div className="vd-header-center">
        <h1 className="vd-title">宇宙网诞生记</h1>
        <p className="vd-subtitle">从近乎均匀的涨落到支配宇宙的大尺度结构</p>
        <div className="vd-phase-pills" role="tablist" aria-label="演化阶段">
          {PHASES.map((p, i) => (
            <span
              key={p.id}
              className={`vd-phase-pill${i === activePhaseIdx ? ' on' : ''}`}
            >
              <strong>{p.id}</strong>
              {p.range} · {p.label}
            </span>
          ))}
        </div>
      </div>

      <div className="vd-header-right">
        <div className="vd-time-readout">
          <span className="vd-time-label">t =</span>
          <strong className="vd-time-value">{sliderStep}</strong>
        </div>
        <input
          className="vd-time-slider"
          type="range"
          min={0}
          max={timestepCount - 1}
          value={sliderStep}
          onChange={(e) => onSliderChange(Number(e.target.value))}
          onPointerDown={onSliderDragStart}
          onMouseUp={onSliderCommit}
          onTouchEnd={onSliderCommit}
        />
        <div className="vd-step-buttons">
          {MARK_STEPS.map((t) => (
            <button
              key={t}
              type="button"
              className={`vd-step-btn${timestep === t ? ' on' : ''}`}
              onClick={() => onSelectTimestep(t)}
            >
              {t}
            </button>
          ))}
        </div>
        {stats && !recordMode && (
          <span className="vd-header-stats">
            μ={stats.mean.toFixed(2)} σ={stats.std.toFixed(3)}
          </span>
        )}
      </div>
    </header>
  );
}
