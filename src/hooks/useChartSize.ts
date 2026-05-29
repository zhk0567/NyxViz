import { useEffect, useState } from 'react';

const MIN_H = 260;

export function useChartSize(
  ref: React.RefObject<HTMLElement | null>,
  minHeight = MIN_H,
  aspect = 2.2,
) {
  const [size, setSize] = useState({ width: 520, height: minHeight });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const w = Math.max(280, el.clientWidth);
      const h = Math.max(minHeight, Math.round(w / aspect));
      setSize({ width: w, height: h });
    };

    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, minHeight, aspect]);

  return size;
}
