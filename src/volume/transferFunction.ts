import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction';
import {
  cinematicLegendGradient,
  cosmicLegendGradient,
  getColorStops,
  type ColormapStyle,
  densityToUnit,
  log10Safe,
} from '@/viz/colormap';

export type { TfDomain } from '@/viz/tfDomain';
export { getGlobalTfDomain } from '@/viz/tfDomain';
export { cosmicLegendGradient, cinematicLegendGradient };

export type VisualStyle = 'cinematic' | 'standard';

export interface TfParams {
  opacityScale?: number;
  densityGain?: number;
  highlightBoost?: number;
}

export interface TransferFunctionOptions extends TfParams {
  dataMin: number;
  dataMax: number;
  highlightMin?: number;
  highlightMax?: number;
  useLogScale?: boolean;
  visualStyle?: VisualStyle;
}

function valueAtNormT(
  t: number,
  dataMin: number,
  dataMax: number,
  useLog: boolean,
): number {
  if (useLog) {
    const lo = log10Safe(dataMin);
    const hi = log10Safe(dataMax);
    return Math.pow(10, lo + t * (hi - lo));
  }
  return dataMin + t * (dataMax - dataMin);
}

function mapDensity(
  rho: number,
  dataMin: number,
  dataMax: number,
  useLog: boolean,
): number {
  const u = densityToUnit(rho, dataMin, dataMax, useLog);
  return valueAtNormT(u, dataMin, dataMax, useLog);
}

function mapT(
  t: number,
  dataMin: number,
  dataMax: number,
  densityGain: number,
  useLog: boolean,
): number {
  const span = dataMax - dataMin || 1;
  const gainShift = span * densityGain * 0.08;
  return valueAtNormT(t, dataMin, dataMax, useLog) - gainShift;
}

function colormapStyle(visualStyle: VisualStyle = 'cinematic'): ColormapStyle {
  return visualStyle === 'cinematic' ? 'cinematic' : 'cosmic';
}

export function fillColorTransferFunction(
  ctf: vtkColorTransferFunction,
  opts: TransferFunctionOptions,
): void {
  const {
    dataMin,
    dataMax,
    densityGain = 0,
    useLogScale = true,
    visualStyle = 'cinematic',
  } = opts;

  ctf.removeAllPoints();
  for (const [t, r, g, b] of getColorStops(colormapStyle(visualStyle))) {
    const x = mapT(t, dataMin, dataMax, densityGain, useLogScale);
    ctf.addRGBPoint(x, r, g, b);
  }
}

function fillStandardOpacity(
  pwf: vtkPiecewiseFunction,
  opts: TransferFunctionOptions,
  at: (t: number) => number,
  scale: (v: number) => number,
): void {
  const { dataMin, dataMax } = opts;
  pwf.addPoint(dataMin, 0.0);
  pwf.addPoint(at(0.12), scale(0.02));
  pwf.addPoint(at(0.35), scale(0.06));
  pwf.addPoint(at(0.55), scale(0.14));
  pwf.addPoint(at(0.72), scale(0.32));
  pwf.addPoint(at(0.88), scale(0.65));
  pwf.addPoint(dataMax, scale(0.95));
}

function fillCinematicOpacity(
  pwf: vtkPiecewiseFunction,
  opts: TransferFunctionOptions,
  at: (t: number) => number,
  scale: (v: number) => number,
): void {
  const { dataMin, dataMax } = opts;
  pwf.addPoint(dataMin, 0.0);
  pwf.addPoint(at(0.08), 0.0);
  pwf.addPoint(at(0.18), scale(0.004));
  pwf.addPoint(at(0.35), scale(0.025));
  pwf.addPoint(at(0.55), scale(0.08));
  pwf.addPoint(at(0.72), scale(0.28));
  pwf.addPoint(at(0.85), scale(0.58));
  pwf.addPoint(at(0.90), scale(0.78));
  pwf.addPoint(at(0.94), scale(0.92));
  pwf.addPoint(at(0.97), scale(0.98));
  pwf.addPoint(dataMax, scale(1.0));
}

export function fillOpacityTransferFunction(
  pwf: vtkPiecewiseFunction,
  opts: TransferFunctionOptions,
): void {
  const {
    dataMin,
    dataMax,
    highlightMin,
    highlightMax,
    opacityScale = 1,
    densityGain = 0,
    highlightBoost = 1,
    useLogScale = true,
    visualStyle = 'cinematic',
  } = opts;
  const span = dataMax - dataMin || 1;
  const scale = (v: number) => Math.min(1, v * opacityScale);

  const at = (t: number) => mapT(t, dataMin, dataMax, densityGain, useLogScale);

  pwf.removeAllPoints();

  if (highlightMin !== undefined && highlightMax !== undefined) {
    const boost = highlightBoost;
    const voidOpacity = visualStyle === 'cinematic' ? 0.0 : 0.002;
    pwf.addPoint(dataMin, scale(voidOpacity));
    pwf.addPoint(
      mapDensity(highlightMin - span * 0.008, dataMin, dataMax, useLogScale),
      scale(visualStyle === 'cinematic' ? 0.008 : 0.015),
    );
    pwf.addPoint(
      mapDensity(highlightMin, dataMin, dataMax, useLogScale),
      scale(0.55 * boost),
    );
    pwf.addPoint(
      mapDensity(highlightMax, dataMin, dataMax, useLogScale),
      scale(0.98 * boost),
    );
    pwf.addPoint(
      mapDensity(highlightMax + span * 0.008, dataMin, dataMax, useLogScale),
      scale(visualStyle === 'cinematic' ? 0.08 : 0.15),
    );
    pwf.addPoint(dataMax, scale(visualStyle === 'cinematic' ? 0.04 : 0.15));
    return;
  }

  if (visualStyle === 'cinematic') {
    fillCinematicOpacity(pwf, opts, at, scale);
  } else {
    fillStandardOpacity(pwf, opts, at, scale);
  }
}

export function buildColorTransferFunction(
  opts: TransferFunctionOptions,
): vtkColorTransferFunction {
  const ctf = vtkColorTransferFunction.newInstance();
  fillColorTransferFunction(ctf, opts);
  return ctf;
}

export function buildOpacityTransferFunction(
  opts: TransferFunctionOptions,
): vtkPiecewiseFunction {
  const pwf = vtkPiecewiseFunction.newInstance();
  fillOpacityTransferFunction(pwf, opts);
  return pwf;
}
