/** Shared cosmic colormap — used by TF, Canvas projection, and CSS legend. */

export const VIZ_BG = '#0a0e1a';

/** Normalized position 0–1 → RGB 0–1 */
export const COSMIC_COLOR_STOPS: ReadonlyArray<
  readonly [t: number, r: number, g: number, b: number]
> = [
  [0.0, 0.02, 0.03, 0.1],
  [0.15, 0.04, 0.08, 0.28],
  [0.35, 0.12, 0.2, 0.48],
  [0.55, 0.24, 0.55, 0.72],
  [0.72, 0.55, 0.42, 0.78],
  [0.85, 0.85, 0.65, 0.42],
  [1.0, 0.98, 0.92, 0.78],
];

export const BRUSH_HIGHLIGHT_RGB: readonly [number, number, number] = [
  0.96, 0.78, 0.26,
];

export function log10Safe(v: number, floor = 1e-6): number {
  return Math.log10(Math.max(v, floor));
}

/** Map density value to 0–1 using optional log scale. */
export function densityToUnit(
  v: number,
  min: number,
  max: number,
  useLog = true,
): number {
  if (max <= min) return 0;
  if (useLog) {
    const lo = log10Safe(min);
    const hi = log10Safe(max);
    const span = hi - lo || 1;
    return Math.max(0, Math.min(1, (log10Safe(v) - lo) / span));
  }
  return Math.max(0, Math.min(1, (v - min) / (max - min)));
}

export function sampleCosmicRgb(t: number): [number, number, number] {
  const x = Math.max(0, Math.min(1, t));
  const stops = COSMIC_COLOR_STOPS;
  for (let i = 0; i < stops.length - 1; i++) {
    const a = stops[i]!;
    const b = stops[i + 1]!;
    if (x >= a[0] && x <= b[0]) {
      const f = (x - a[0]) / (b[0] - a[0] || 1);
      return [
        a[1] + (b[1] - a[1]) * f,
        a[2] + (b[2] - a[2]) * f,
        a[3] + (b[3] - a[3]) * f,
      ];
    }
  }
  const last = stops[stops.length - 1]!;
  return [last[1], last[2], last[3]];
}

export function sampleCosmicCss(t: number): string {
  const [r, g, b] = sampleCosmicRgb(t);
  return `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)})`;
}

/** 256-entry LUT for Canvas ImageData. */
export function buildCosmicLut256(): Uint8ClampedArray {
  const lut = new Uint8ClampedArray(256 * 4);
  for (let i = 0; i < 256; i++) {
    const [r, g, b] = sampleCosmicRgb(i / 255);
    const o = i * 4;
    lut[o] = Math.round(r * 255);
    lut[o + 1] = Math.round(g * 255);
    lut[o + 2] = Math.round(b * 255);
    lut[o + 3] = 255;
  }
  return lut;
}

export function cosmicLegendGradient(): string {
  const stops = COSMIC_COLOR_STOPS.map(
    ([t, r, g, b]) =>
      `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)}) ${t * 100}%`,
  );
  return `linear-gradient(90deg, ${stops.join(', ')})`;
}
