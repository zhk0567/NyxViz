import { useEffect, useRef, useState } from 'react';

const MIN_H = 260;
const DEFAULT_MAX_H = 320;

export interface ChartSizeOptions {
  minHeight?: number;
  aspect?: number;
  maxHeight?: number;
  fillContainer?: boolean;
}

export function useChartSize(
  ref: React.RefObject<HTMLElement | null>,
  minHeight = MIN_H,
  aspect = 2.2,
  maxHeight = DEFAULT_MAX_H,
  fillContainer = false,
) {
  const [size, setSize] = useState({ width: 520, height: minHeight });
  const lastDims = useRef({ w: 0, h: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const w = Math.max(120, el.clientWidth);
      const containerH = el.clientHeight;
      let h: number;
      if (fillContainer && containerH > 40) {
        // 不得超过容器实际高度，避免 SVG 撑开父级 → ResizeObserver 振荡
        h = Math.min(maxHeight, containerH);
      } else {
        h = Math.min(maxHeight, Math.max(minHeight, Math.round(w / aspect)));
      }

      if (w === lastDims.current.w && h === lastDims.current.h) return;
      lastDims.current = { w, h };
      setSize((prev) => (prev.width === w && prev.height === h ? prev : { width: w, height: h }));
    };

    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, minHeight, aspect, maxHeight, fillContainer]);

  return size;
}

export function useChartSizeFromOpts(
  ref: React.RefObject<HTMLElement | null>,
  opts?: ChartSizeOptions,
) {
  return useChartSize(
    ref,
    opts?.minHeight ?? MIN_H,
    opts?.aspect ?? 2.2,
    opts?.maxHeight ?? DEFAULT_MAX_H,
    opts?.fillContainer ?? false,
  );
}
