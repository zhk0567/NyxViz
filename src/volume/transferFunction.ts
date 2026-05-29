import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction';

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
}

export function buildColorTransferFunction(
  opts: TransferFunctionOptions,
): vtkColorTransferFunction {
  const { dataMin, dataMax, densityGain = 0 } = opts;
  const span = dataMax - dataMin || 1;
  const shift = span * densityGain * 0.15;
  const ctf = vtkColorTransferFunction.newInstance();
  ctf.addRGBPoint(dataMin, 0.02, 0.02, 0.08);
  ctf.addRGBPoint(dataMin + span * 0.35 - shift, 0.1, 0.15, 0.45);
  ctf.addRGBPoint(dataMin + span * 0.65 - shift, 0.35, 0.2, 0.65);
  ctf.addRGBPoint(dataMin + span * 0.85 - shift, 0.85, 0.55, 0.2);
  ctf.addRGBPoint(dataMax, 1.0, 0.95, 0.85);
  return ctf;
}

export function buildOpacityTransferFunction(
  opts: TransferFunctionOptions,
): vtkPiecewiseFunction {
  const {
    dataMin,
    dataMax,
    highlightMin,
    highlightMax,
    opacityScale = 1,
    densityGain = 0,
    highlightBoost = 1,
  } = opts;
  const span = dataMax - dataMin || 1;
  const gainShift = span * densityGain * 0.12;
  const scale = (v: number) => Math.min(1, v * opacityScale);

  const pwf = vtkPiecewiseFunction.newInstance();

  if (highlightMin !== undefined && highlightMax !== undefined) {
    const boost = highlightBoost;
    pwf.addPoint(dataMin, scale(0.01));
    pwf.addPoint(highlightMin - span * 0.01, scale(0.02));
    pwf.addPoint(highlightMin, scale(0.35 * boost));
    pwf.addPoint(highlightMax, scale(0.9 * boost));
    pwf.addPoint(highlightMax + span * 0.01, scale(0.15));
    pwf.addPoint(dataMax, scale(0.2));
    return pwf;
  }

  pwf.addPoint(dataMin, 0.0);
  pwf.addPoint(dataMin + span * 0.25 - gainShift, scale(0.02));
  pwf.addPoint(dataMin + span * 0.55 - gainShift, scale(0.08));
  pwf.addPoint(dataMin + span * 0.78 - gainShift, scale(0.25));
  pwf.addPoint(dataMax, scale(0.95));
  return pwf;
}
