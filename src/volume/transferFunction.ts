import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction';
import {
  COSMIC_COLOR_STOPS,
  cosmicLegendGradient,
  densityToUnit,
  log10Safe,
} from '@/viz/colormap';

export type { TfDomain } from '@/viz/tfDomain';
export { getGlobalTfDomain } from '@/viz/tfDomain';
export { cosmicLegendGradient };

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

export function fillColorTransferFunction(
  ctf: vtkColorTransferFunction,
  opts: TransferFunctionOptions,
): void {
  const { dataMin, dataMax, densityGain = 0, useLogScale = true } = opts;

  ctf.removeAllPoints();
  for (const [t, r, g, b] of COSMIC_COLOR_STOPS) {
    const x = mapT(t, dataMin, dataMax, densityGain, useLogScale);
    ctf.addRGBPoint(x, r, g, b);
  }
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
  } = opts;
  const span = dataMax - dataMin || 1;
  const scale = (v: number) => Math.min(1, v * opacityScale);

  const at = (t: number) => mapT(t, dataMin, dataMax, densityGain, useLogScale);

  pwf.removeAllPoints();

  if (highlightMin !== undefined && highlightMax !== undefined) {
    const boost = highlightBoost;
    pwf.addPoint(dataMin, scale(0.002));
    pwf.addPoint(
      mapDensity(highlightMin - span * 0.008, dataMin, dataMax, useLogScale),
      scale(0.015),
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
      scale(0.15),
    );
    pwf.addPoint(dataMax, scale(0.22));
    return;
  }

  pwf.addPoint(dataMin, 0.0);
  pwf.addPoint(at(0.12), scale(0.02));
  pwf.addPoint(at(0.35), scale(0.06));
  pwf.addPoint(at(0.55), scale(0.14));
  pwf.addPoint(at(0.72), scale(0.32));
  pwf.addPoint(at(0.88), scale(0.65));
  pwf.addPoint(dataMax, scale(0.95));
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
