import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VolumeScene } from '@/volume/VolumeScene';
import { loadTimestep } from '@/data/nyxLoader';

declare global {
  interface Window {
    __CAPTURE_READY__?: boolean;
    __CAPTURE_ERROR__?: string;
    __CAPTURE_TIMESTEP__?: number;
  }
}

function minMax(data: Float32Array) {
  let min = Infinity;
  let max = -Infinity;
  for (let i = 0; i < data.length; i++) {
    const v = data[i]!;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  return { min, max };
}

function CaptureApp() {
  const params = new URLSearchParams(window.location.search);
  const timestep = Math.max(0, Math.min(99, Number(params.get('t') ?? 0)));
  const [data, setData] = useState<Float32Array | null>(null);
  const [range, setRange] = useState({ min: 7.5, max: 15 });

  useEffect(() => {
    window.__CAPTURE_READY__ = false;
    window.__CAPTURE_ERROR__ = undefined;
    window.__CAPTURE_TIMESTEP__ = timestep;

    loadTimestep(timestep)
      .then((vol) => {
        setData(vol);
        setRange(minMax(vol));
      })
      .catch((err: unknown) => {
        window.__CAPTURE_ERROR__ =
          err instanceof Error ? err.message : String(err);
      });
  }, [timestep]);

  const handleRendered = () => {
    window.__CAPTURE_READY__ = true;
  };

  if (window.__CAPTURE_ERROR__) {
    return (
      <div id="capture-status" style={{ color: '#f85149', padding: 20 }}>
        {window.__CAPTURE_ERROR__}
      </div>
    );
  }

  if (!data) {
    return (
      <div id="capture-status" style={{ color: '#8b949e', padding: 20 }}>
        Loading timestep {timestep}…
      </div>
    );
  }

  return (
    <VolumeScene
      data={data}
      dataMin={range.min}
      dataMax={range.max}
      onRendered={handleRendered}
      className="capture-volume"
    />
  );
}

createRoot(document.getElementById('root')!).render(<CaptureApp />);
