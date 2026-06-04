import { useEffect, useRef } from 'react';
import { computeMaxProjectionAsync } from '@/data/projectionAsync';
import type { ProjectionAxis } from '@/data/nyxLoader';
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
  compact?: boolean;
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
  hideCaption = false,
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

  if (hideCaption) {
    const size = Math.min(displayW, displayH);
    const dx = (displayW - size) / 2;
    const dy = (displayH - size) / 2;
    ctx.fillStyle = '#060c18';
    ctx.fillRect(0, 0, displayW, displayH);
    ctx.drawImage(off, dx, dy, size, size);
  } else {
    ctx.drawImage(off, 0, 0, displayW, displayH);
  }

  if (!hideCaption) {
    ctx.fillStyle = 'rgba(154, 163, 184, 0.9)';
    ctx.font = '11px sans-serif';
    ctx.fillText('最大密度投影 (log, 全局色标)', 8, 16);
  }
}

export function DensityProjection({
  data,
  brushRange,
  axis = 'xy',
  domainMin,
  domainMax,
  className,
  compact = false,
}: DensityProjectionProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let cancelled = false;
    let idleId: number | undefined;

    const timer = window.setTimeout(() => {
      const run = () => {
        if (cancelled) return;
        void computeMaxProjectionAsync(data, axis).then((proj) => {
          if (cancelled) return;
          const w = canvas.clientWidth || 400;
          const h = canvas.clientHeight || 280;
          const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
          canvas.width = w * dpr;
          canvas.height = h * dpr;

          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          ctx.clearRect(0, 0, w, h);
          drawProjection(ctx, proj, domainMin, domainMax, brushRange, w, h, compact);
        });
      };

      if (typeof requestIdleCallback !== 'undefined') {
        idleId = requestIdleCallback(run, { timeout: 800 });
      } else {
        idleId = requestAnimationFrame(run);
      }
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      if (idleId !== undefined) {
        if (typeof cancelIdleCallback !== 'undefined') {
          cancelIdleCallback(idleId);
        } else {
          cancelAnimationFrame(idleId);
        }
      }
    };
  }, [data, brushRange, axis, domainMin, domainMax, compact]);

  return (
    <canvas
      ref={canvasRef}
      className={className ?? 'density-projection-canvas'}
    />
  );
}
