import { useEffect, useRef } from 'react';
import {
  computeMaxProjection,
  type ProjectionAxis,
} from '@/data/nyxLoader';
import type { BrushRange } from '@/data/types';
import { GRID_SIZE } from '@/data/types';
import {
  BRUSH_HIGHLIGHT_RGB,
  buildCosmicLut256,
  densityToUnit,
} from '@/viz/colormap';

interface DensityProjectionProps {
  data: Float32Array;
  brushRange: BrushRange | null;
  axis?: ProjectionAxis;
  /** Global log-scale domain (p01–p99 envelope). */
  domainMin: number;
  domainMax: number;
  className?: string;
}

const COSMIC_LUT = buildCosmicLut256();

function drawProjection(
  ctx: CanvasRenderingContext2D,
  proj: Float32Array,
  domainMin: number,
  domainMax: number,
  brushRange: BrushRange | null,
  displayW: number,
  displayH: number,
) {
  const off = document.createElement('canvas');
  off.width = GRID_SIZE;
  off.height = GRID_SIZE;
  const offCtx = off.getContext('2d');
  if (!offCtx) return;

  const img = offCtx.createImageData(GRID_SIZE, GRID_SIZE);
  const px = img.data;
  const [hr, hg, hb] = BRUSH_HIGHLIGHT_RGB;

  for (let j = 0; j < GRID_SIZE; j++) {
    for (let i = 0; i < GRID_SIZE; i++) {
      const v = proj[i + j * GRID_SIZE]!;
      const inBrush =
        brushRange !== null && v >= brushRange.min && v <= brushRange.max;
      const t = densityToUnit(v, domainMin, domainMax, true);
      const li = Math.min(255, Math.round(t * 255)) * 4;
      const o = ((GRID_SIZE - 1 - j) * GRID_SIZE + i) * 4;
      if (inBrush) {
        px[o] = Math.round(hr * 255);
        px[o + 1] = Math.round(hg * 255);
        px[o + 2] = Math.round(hb * 255);
        px[o + 3] = 255;
      } else {
        px[o] = COSMIC_LUT[li]!;
        px[o + 1] = COSMIC_LUT[li + 1]!;
        px[o + 2] = COSMIC_LUT[li + 2]!;
        px[o + 3] = 255;
      }
    }
  }
  offCtx.putImageData(img, 0, 0);

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(off, 0, 0, displayW, displayH);

  ctx.fillStyle = 'rgba(154, 163, 184, 0.9)';
  ctx.font = '11px sans-serif';
  ctx.fillText('最大密度投影 (log, 全局色标)', 8, 16);
}

export function DensityProjection({
  data,
  brushRange,
  axis = 'xy',
  domainMin,
  domainMax,
  className,
}: DensityProjectionProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const proj = computeMaxProjection(data, axis);
    const w = canvas.clientWidth || 400;
    const h = canvas.clientHeight || 280;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    drawProjection(ctx, proj, domainMin, domainMax, brushRange, w, h);
  }, [data, brushRange, axis, domainMin, domainMax]);

  return (
    <canvas
      ref={canvasRef}
      className={className ?? 'density-projection-canvas'}
    />
  );
}
