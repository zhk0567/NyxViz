export type EvolutionPhaseId = 'linear' | 'nonlinear' | 'web';

export interface EvolutionPhase {
  id: EvolutionPhaseId;
  label: string;
  detail: string;
}

export function evolutionPhase(timestep: number): EvolutionPhase {
  if (timestep < 30) {
    return {
      id: 'linear',
      label: '线性期',
      detail: 't=0–29 · 涨落初生',
    };
  }
  if (timestep < 70) {
    return {
      id: 'nonlinear',
      label: '非线性增长',
      detail: 't=30–69 · 丝状结构连通',
    };
  }
  return {
    id: 'web',
    label: '宇宙网形成',
    detail: 't=70–99 · void–filament–node',
  };
}

export const MARK_STEPS = [0, 25, 50, 75, 99] as const;
