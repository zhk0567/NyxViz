import { useEffect } from 'react';

declare global {
  interface Window {
    __VIDEO_POSTER_READY__?: boolean;
  }
}

export function isVideoPosterCapture(): boolean {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location.search).get('posterCapture') === '1';
}

/** Playwright 代表图截屏：intro 录屏页体渲染 + 图表就绪 */
export function useVideoPosterCapture(opts: {
  enabled: boolean;
  recordMode: boolean;
  sceneId: string;
  loading: boolean;
  volumeReady: boolean;
}) {
  useEffect(() => {
    window.__VIDEO_POSTER_READY__ = false;
    if (!opts.enabled || !opts.recordMode || opts.sceneId !== 'intro') return;
    if (opts.loading || !opts.volumeReady) return;

    const timer = window.setTimeout(() => {
      window.__VIDEO_POSTER_READY__ = true;
    }, 1200);

    return () => window.clearTimeout(timer);
  }, [opts.enabled, opts.recordMode, opts.sceneId, opts.loading, opts.volumeReady]);
}
