import { useEffect, useRef, useState } from 'react';

const MIN_H = 260;
const DEFAULT_MAX_H = 320;

export function useChartSize(
  ref: React.RefObject<HTMLElement | null>,
  minHeight = MIN_H,
  aspect = 2.2,
  maxHeight = DEFAULT_MAX_H,
) {
  const [size, setSize] = useState({ width: 520, height: minHeight });
  const lastW = useRef(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const w = Math.max(280, el.clientWidth);
      if (w === lastW.current) return;
      lastW.current = w;
      const h = Math.min(maxHeight, Math.max(minHeight, Math.round(w / aspect)));
      setSize((prev) => (prev.width === w && prev.height === h ? prev : { width: w, height: h }));
    };

    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, minHeight, aspect, maxHeight]);

  return size;
}
