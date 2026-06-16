import { useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VolumeScene } from '@/volume/VolumeScene';
import { loadTimestep, loadTimelineStats } from '@/data/nyxLoader';
import {
  getCinematicDefaultProfile,
  getEvolutionCaptureProfile,
  getGlobalMorphCaptureProfile,
  type CaptureProfile,
} from '@/viz/tfDomain';
import { VIDEO_CAMERA_ZOOM } from '@/volume/renderSpec';

declare global {
  interface Window {
    __CAPTURE_READY__?: boolean;
    __CAPTURE_ERROR__?: string;
    __CAPTURE_TIMESTEP__?: number;
    __CAPTURE_REC__?: { timestep: number; ready: boolean };
    __CAPTURE_GO_TIMESTEP__?: (t: number) => void;
  }
}

function resolveCaptureProfile(
  timeline: Awaited<ReturnType<typeof loadTimelineStats>>,
  timestep: number,
  domainMode: string,
): CaptureProfile {
  if (domainMode === 'cinematic') {
    return getCinematicDefaultProfile(timeline);
  }
  if (domainMode === 'evolution') {
    return getEvolutionCaptureProfile(timeline, timestep);
  }
  if (domainMode === 'global' || domainMode === 'morph') {
    return getGlobalMorphCaptureProfile(timeline, timestep);
  }
  return getGlobalMorphCaptureProfile(timeline, timestep);
}

function CaptureApp() {
  const params = new URLSearchParams(window.location.search);
  const seqMode = params.get('seq') === '1';
  const domainMode = params.get('domain') ?? (seqMode ? 'morph' : 'evolution');
  const initialT = Math.max(0, Math.min(99, Number(params.get('t') ?? 0)));
  const [timestep, setTimestep] = useState(initialT);
  const [data, setData] = useState<Float32Array | null>(null);
  const [domain, setDomain] = useState({ min: 7.5, max: 15 });
  const [captureTf, setCaptureTf] = useState<CaptureProfile['tfParams']>({});
  const [highlightMin, setHighlightMin] = useState<number | undefined>();
  const [highlightMax, setHighlightMax] = useState<number | undefined>();
  const cameraZoom =
    domainMode === 'cinematic'
      ? VIDEO_CAMERA_ZOOM
      : VIDEO_CAMERA_ZOOM + (timestep / 99) * 0.08;
  const timelineRef = useRef<Awaited<ReturnType<typeof loadTimelineStats>> | null>(null);
  const loadGenRef = useRef(0);

  const markNotReady = useCallback((t: number) => {
    window.__CAPTURE_READY__ = false;
    window.__CAPTURE_REC__ = { timestep: t, ready: false };
  }, []);

  const markReady = useCallback((t: number) => {
    window.__CAPTURE_TIMESTEP__ = t;
    window.__CAPTURE_READY__ = true;
    window.__CAPTURE_REC__ = { timestep: t, ready: true };
  }, []);

  useEffect(() => {
    if (!seqMode) return;
    window.__CAPTURE_GO_TIMESTEP__ = (t: number) => {
      const clamped = Math.max(0, Math.min(99, Math.round(t)));
      markNotReady(clamped);
      setTimestep(clamped);
    };
    return () => {
      delete window.__CAPTURE_GO_TIMESTEP__;
    };
  }, [seqMode, markNotReady]);

  useEffect(() => {
    let cancelled = false;
    markNotReady(timestep);
    window.__CAPTURE_ERROR__ = undefined;

    const gen = ++loadGenRef.current;

    void (async () => {
      try {
        if (!timelineRef.current) {
          timelineRef.current = await loadTimelineStats();
        }
        if (cancelled || gen !== loadGenRef.current) return;
        const timeline = timelineRef.current;
        const vol = await loadTimestep(timestep);
        if (cancelled || gen !== loadGenRef.current) return;
        const profile = resolveCaptureProfile(timeline, timestep, domainMode);
        setDomain({ min: profile.domain.min, max: profile.domain.max });
        setCaptureTf(profile.tfParams);
        setHighlightMin(profile.highlightMin);
        setHighlightMax(profile.highlightMax);
        setData(vol);
      } catch (err: unknown) {
        if (cancelled) return;
        window.__CAPTURE_ERROR__ =
          err instanceof Error ? err.message : String(err);
        setData(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [timestep, domainMode, markNotReady]);

  const handleRendered = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => markReady(timestep));
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
    <>
      <VolumeScene
        data={data}
        timestep={timestep}
        dataMin={domain.min}
        dataMax={domain.max}
        tfParams={captureTf}
        highlightMin={highlightMin}
        highlightMax={highlightMax}
        cameraZoom={cameraZoom}
        quality="presentation"
        visualStyle="cinematic"
        useLogScale
        onRendered={handleRendered}
        className="capture-volume"
      />
      {seqMode && (
        <div
          className="capture-step-badge"
          aria-hidden
        >
          t = {timestep}
        </div>
      )}
    </>
  );
}

createRoot(document.getElementById('root')!).render(<CaptureApp />);
