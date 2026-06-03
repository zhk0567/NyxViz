import type { EvolutionPhaseId } from '@/dashboard/evolutionPhase';

interface PhaseTrackProps {
  phaseId: EvolutionPhaseId;
}

export function PhaseTrack({ phaseId }: PhaseTrackProps) {
  return (
    <div className="phase-track" role="presentation">
      <div className="phase-track-bar">
        <span className={`phase-seg${phaseId === 'linear' ? ' active' : ''}`}>
          早期宇宙 · 线性期
        </span>
        <span className={`phase-seg${phaseId === 'nonlinear' ? ' active' : ''}`}>
          非线性增长期
        </span>
        <span className={`phase-seg${phaseId === 'web' ? ' active' : ''}`}>
          宇宙网形成期
        </span>
      </div>
      <div className="phase-track-labels">
        <span>t=0</span>
        <span>t=29</span>
        <span>t=69</span>
        <span>t=99</span>
      </div>
    </div>
  );
}
