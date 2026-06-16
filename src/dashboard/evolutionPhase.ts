import { figuresUrl } from '@/config/publicPaths';

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

/** XY max-projection frames — adaptive threshold shows sparse t=0 → web t=99. */
export function evolutionThumbnailSrc(t: number): string {
  return figuresUrl(`task1_evo_t${String(t).padStart(4, '0')}.png`);
}

export function handleEvolutionThumbnailError(
  img: HTMLImageElement,
  t: number,
): void {
  const pad = String(t).padStart(4, '0');
  const stage = img.dataset.evoFallback ?? '0';
  if (stage === '0' && img.src.includes(`task1_evo_t${pad}`)) {
    img.dataset.evoFallback = '1';
    img.src = figuresUrl(`task1_slice_t${pad}.png`);
  } else if (stage === '1' && img.src.includes(`task1_slice_t${pad}`)) {
    img.dataset.evoFallback = '2';
    img.src = figuresUrl(`task1_vol_t${pad}.png`);
  }
}

/** Swap img src once to fallback; avoids onError loops when fallback also 404s. */
export function setFigureFallbackOnce(
  img: HTMLImageElement,
  fallbackName: string,
): void {
  if (img.dataset.figureFallback === fallbackName) return;
  img.dataset.figureFallback = fallbackName;
  img.src = figuresUrl(fallbackName);
}
