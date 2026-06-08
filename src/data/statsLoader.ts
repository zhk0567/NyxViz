export interface RenderSpecData {
  presentation: {
    sampleDistance: number;
    ambient: number;
    diffuse: number;
    specular: number;
  };
  lights: {
    key: { color_rgb: number[]; intensity: number; position_offset: number[] };
    fill: { color_rgb: number[]; intensity: number; position_offset: number[] };
  };
  opacityStopsNormalized: [number, number][];
  colorStopsNormalized: { t: number; rgb: number[] }[];
}

export interface ValidationExtendedData {
  voidFractions: {
    t0: { belowT0P10: number; belowT0P01: number };
    t99: { belowT0P10: number; belowT0P01: number };
  };
  bootstrapSpatial: {
    moransIGlobal: { t0: number; t99: number; delta: number };
    xiR1Global: { t0: number; t99: number; delta: number };
    pooledBootstrapStdMoran: number;
    pooledBootstrapStdXiR1: number;
    moransISignificantAt2Sigma: boolean;
    xiR1SignificantAt2Sigma: boolean;
  };
  binSensitivityT99: {
    binRows: { bins: number; cdfLinfVs128: number }[];
    p99: number;
  };
}

export interface BrushValidationData {
  fpFnDefault: {
    precision: number;
    recall: number;
    filamentBand: [number, number];
  };
  p88Sweep: {
    projPercentile: number;
    densityBand: [number, number];
  }[];
  benchmark: {
    top1_earlyExit: { elapsedMs: number };
    top1_fullCount: { elapsedMs: number };
    sampleRecall: { recallVsTrue: number };
    customBrushErrors: {
      label: string;
      recallVsTruePct: number;
    }[];
  };
}

export interface VideoStatsBundle {
  renderSpec: RenderSpecData | null;
  validationExtended: ValidationExtendedData | null;
  brushValidation: BrushValidationData | null;
}

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

export async function loadVideoStats(): Promise<VideoStatsBundle> {
  const [renderSpec, validationExtended, brushValidation] = await Promise.all([
    fetchJson<RenderSpecData>('/stats/render_spec.json'),
    fetchJson<ValidationExtendedData>('/stats/validation_extended.json'),
    fetchJson<BrushValidationData>('/stats/brush_validation.json'),
  ]);
  return { renderSpec, validationExtended, brushValidation };
}
