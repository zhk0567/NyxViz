import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getSceneMeta,
  parseSceneId,
  sceneUrl,
  type VideoSceneId,
} from '@/video/sceneRegistry';

function readSceneFromUrl(): VideoSceneId {
  const q = new URLSearchParams(window.location.search);
  return parseSceneId(q.get('scene'));
}

export function isVideoRecordMode(): boolean {
  const q = new URLSearchParams(window.location.search);
  return q.get('record') === '1' || q.get('rec') === '1';
}

export function useVideoScene() {
  const recordMode = useMemo(() => isVideoRecordMode(), []);
  const [sceneId, setSceneIdState] = useState<VideoSceneId>(() => readSceneFromUrl());
  const sceneMeta = useMemo(() => getSceneMeta(sceneId), [sceneId]);

  useEffect(() => {
    if (recordMode) return;
    const onPopState = () => setSceneIdState(readSceneFromUrl());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [recordMode]);

  const setScene = useCallback(
    (id: VideoSceneId) => {
      if (recordMode) {
        window.location.href = sceneUrl(id, true);
        return;
      }
      const params = new URLSearchParams(window.location.search);
      if (id === 'intro') {
        params.delete('scene');
      } else {
        params.set('scene', id);
      }
      const q = params.toString();
      const url = q ? `/video.html?${q}` : '/video.html';
      window.history.replaceState(null, '', url);
      setSceneIdState(id);
    },
    [recordMode],
  );

  return { sceneId, sceneMeta, setScene, recordMode };
}
