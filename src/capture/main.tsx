import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VolumeScene } from '@/volume/VolumeScene';
import { loadTimestep, loadTimelineStats } from '@/data/nyxLoader';
import { getEvolutionCaptureProfile } from '@/viz/tfDomain';

declare global {
  interface Window {
    __CAPTURE_READY__?: boolean;
    __CAPTURE_ERROR__?: string;
    __CAPTURE_TIMESTEP__?: number;
  }
}

function CaptureApp() {
  const params = new URLSearchParams(window.location.search);
  const timestep = Math.max(0, Math.min(99, Number(params.get('t') ?? 0)));
  const [data, setData] = useState<Float32Array | null>(null);
  const [domain, setDomain] = useState({ min: 7.5, max: 15 });
  const [captureTf, setCaptureTf] = useState<{ opacityScale?: number; densityGain?: number }>({});

  useEffect(() => {
    window.__CAPTURE_READY__ = false;
    window.__CAPTURE_ERROR__ = undefined;
    window.__CAPTURE_TIMESTEP__ = timestep;

    Promise.all([loadTimestep(timestep), loadTimelineStats()])
      .then(([vol, timeline]) => {
        const profile = getEvolutionCaptureProfile(timeline, timestep);
        setDomain({ min: profile.domain.min, max: profile.domain.max });
        setCaptureTf(profile.tfParams);
        setData(vol);
      })
      .catch((err: unknown) => {
        window.__CAPTURE_ERROR__ =
          err instanceof Error ? err.message : String(err);
      });
  }, [timestep]);

  const handleRendered = () => {
    // Wait for layout + vtk resize so 16:9 capture is not half-height.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.__CAPTURE_READY__ = true;
      });
    });
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
      timestep={timestep}
      dataMin={domain.min}
      dataMax={domain.max}
      tfParams={captureTf}
      quality="presentation"
      useLogScale
      onRendered={handleRendered}
      className="capture-volume"
    />
  );
}

createRoot(document.getElementById('root')!).render(<CaptureApp />);
