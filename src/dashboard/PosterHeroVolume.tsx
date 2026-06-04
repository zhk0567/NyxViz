import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import type { TfParams } from '@/volume/transferFunction';
import type { VolumeQuality } from '@/volume/VolumeScene';

const VolumeScene = lazy(() =>
  import('@/volume/VolumeScene').then((m) => ({ default: m.VolumeScene })),
);

function VtkFallback() {
  return <div className="vtk-skeleton pl-hero-vtk-fallback">加载体渲染…</div>;
}

export interface PosterHeroVolumeProps {
  densityData: Float32Array | null;
  loading: boolean;
  timestep: number;
  dataMin: number;
  dataMax: number;
  tfParams?: TfParams;
  quality?: VolumeQuality;
  highlightMin?: number;
  highlightMax?: number;
  /** Pause GPU render when explore overlay is open. */
  paused?: boolean;
}

export function PosterHeroVolume({
  densityData,
  loading,
  timestep,
  dataMin,
  dataMax,
  tfParams,
  quality = 'interactive',
  highlightMin,
  highlightMax,
  paused = false,
}: PosterHeroVolumeProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(true);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    const io = new IntersectionObserver(
      ([entry]) => setInView(entry?.isIntersecting ?? false),
      { root: null, threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const renderActive = inView && !paused && !!densityData;

  return (
    <div ref={wrapRef} className="pl-hero-vtk-wrap">
      <LoadingOverlay visible={loading} label={`t=${timestep}`} />
      {densityData ? (
        <Suspense fallback={<VtkFallback />}>
          <VolumeScene
            data={densityData}
            timestep={timestep}
            dataMin={dataMin}
            dataMax={dataMax}
            tfParams={tfParams}
            quality={quality}
            highlightMin={highlightMin}
            highlightMax={highlightMax}
            renderActive={renderActive}
            className="vtk-panel pl-hero-vtk"
          />
        </Suspense>
      ) : (
        <VtkFallback />
      )}
    </div>
  );
}
