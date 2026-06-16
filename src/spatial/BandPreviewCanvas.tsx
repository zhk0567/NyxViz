import { useEffect, useRef } from 'react';
import type { BrushRange } from '@/data/types';
import { GRID_SIZE } from '@/data/types';
import {
  BRUSH_HIGHLIGHT_RGB,
  buildCosmicLut256,
  densityToUnit,
} from '@/viz/colormap';

const COSMIC_LUT = buildCosmicLut256();

export function drawProjectionToCanvas(
  canvas: HTMLCanvasElement,
  proj: Float32Array,
  domainMin: number,
  domainMax: number,
  brushRange: BrushRange | null,
  compact = false,
) {
  const w = canvas.clientWidth || 120;
  const h = canvas.clientHeight || 120;
  const dpr = Math.min(window.devicePixelRatio || 1, 1.25);
  canvas.width = w * dpr;
  canvas.height = h * dpr;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

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
  ctx.imageSmoothingQuality = 'medium';
  if (compact) {
    const size = Math.min(w, h);
    const dx = (w - size) / 2;
    const dy = (h - size) / 2;
    ctx.fillStyle = '#060c18';
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(off, dx, dy, size, size);
  } else {
    ctx.drawImage(off, 0, 0, w, h);
  }
}

interface BandPreviewCanvasProps {
  projection: Float32Array;
  brushRange: BrushRange;
  domainMin: number;
  domainMax: number;
  className?: string;
}

export function BandPreviewCanvas({
  projection,
  brushRange,
  domainMin,
  domainMax,
  className,
}: BandPreviewCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawProjectionToCanvas(canvas, projection, domainMin, domainMax, brushRange, true);
  }, [projection, brushRange, domainMin, domainMax]);

  return <canvas ref={canvasRef} className={className ?? 'density-projection-canvas'} />;
}
