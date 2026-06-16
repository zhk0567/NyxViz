import { useEffect, useState } from 'react';
import { computeMaxProjectionAsync } from '@/data/projectionAsync';
import type { ProjectionAxis } from '@/data/nyxLoader';

export function useSharedProjection(
  data: Float32Array | null | undefined,
  axis: ProjectionAxis = 'xy',
): Float32Array | null {
  const [projection, setProjection] = useState<Float32Array | null>(null);

  useEffect(() => {
    if (!data) {
      setProjection(null);
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(() => {
      void computeMaxProjectionAsync(data, axis).then((proj) => {
        if (!cancelled) setProjection(proj);
      });
    }, 320);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [data, axis]);

  return projection;
}
