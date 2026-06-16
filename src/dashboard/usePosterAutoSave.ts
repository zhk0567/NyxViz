import { useCallback, useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    __POSTER_CAPTURE_READY__?: boolean;
  }
}

export interface PosterSaveState {
  status: 'idle' | 'saving' | 'saved' | 'error';
  message?: string;
  paths?: string[];
}

async function requestPosterSave(href: string): Promise<PosterSaveState> {
  const res = await fetch('/__api/save-app-poster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ href }),
  });
  const data = (await res.json()) as {
    ok?: boolean;
    error?: string;
    resized?: string;
    copies?: string[];
  };
  if (!res.ok || !data.ok) {
    throw new Error(data.error ?? `保存失败 (${res.status})`);
  }
  return {
    status: 'saved',
    message: '已保存到 docs/figures',
    paths: [data.resized, ...(data.copies ?? [])].filter(Boolean) as string[],
  };
}

export function usePosterAutoSave(opts: {
  enabled: boolean;
  representative: boolean;
  loading: boolean;
  volumeReady: boolean;
  autoOnLoad?: boolean;
}) {
  const [saveState, setSaveState] = useState<PosterSaveState>({ status: 'idle' });
  const autoSavedRef = useRef(false);
  const savingRef = useRef(false);

  const savePoster = useCallback(async () => {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaveState({ status: 'saving', message: '正在截屏并写入 docs/figures…' });
    try {
      const next = await requestPosterSave(window.location.href);
      setSaveState(next);
    } catch (err) {
      setSaveState({
        status: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      savingRef.current = false;
    }
  }, []);

  useEffect(() => {
    window.__POSTER_CAPTURE_READY__ = false;
    if (!opts.representative || opts.loading || !opts.volumeReady) return;

    const timer = window.setTimeout(() => {
      window.__POSTER_CAPTURE_READY__ = true;
    }, 800);

    return () => window.clearTimeout(timer);
  }, [opts.representative, opts.loading, opts.volumeReady, opts.enabled]);

  useEffect(() => {
    if (!opts.autoOnLoad || !opts.enabled || !opts.representative) return;
    if (opts.loading || !opts.volumeReady) return;

    const timer = window.setTimeout(() => {
      if (autoSavedRef.current || !window.__POSTER_CAPTURE_READY__) return;
      autoSavedRef.current = true;
      void savePoster();
    }, 1200);

    return () => window.clearTimeout(timer);
  }, [
    opts.autoOnLoad,
    opts.enabled,
    opts.representative,
    opts.loading,
    opts.volumeReady,
    savePoster,
  ]);

  return { saveState, savePoster };
}
