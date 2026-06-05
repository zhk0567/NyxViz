export const GRID_SIZE = 128;
export const VOXEL_COUNT = GRID_SIZE ** 3;
export const DOMAIN_LENGTH = 14.245;
export const SPACING = DOMAIN_LENGTH / GRID_SIZE;
export const TIMESTEP_COUNT = 100;

export interface DensityStats {
  timestep: number;
  min: number;
  max: number;
  mean: number;
  std: number;
  skewness: number;
  p01: number;
  p10?: number;
  p25?: number;
  p50: number;
  p75?: number;
  p90: number;
  p99: number;
  p999: number;
  tailMassAboveP99: number;
  tailMassBelowP01: number;
  tailMassFilament90_99?: number;
  tailMassBelowP10?: number;
  tailMassBelowP25?: number;
  voidFractionBelowT0P10?: number;
  voidFractionBelowT0P01?: number;
  massFractionAboveP99: number;
  massFractionBelowP01: number;
}

export interface TimelineData {
  globalMin: number;
  globalMax: number;
  binCount: number;
  logBinEdges: number[];
  timesteps: DensityStats[];
  histograms: number[][];
}

export interface BrushRange {
  min: number;
  max: number;
}

export interface BrushedVoxel {
  x: number;
  y: number;
  z: number;
  density: number;
}
