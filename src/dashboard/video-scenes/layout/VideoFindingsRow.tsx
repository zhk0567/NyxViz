import { VideoFindingsStrip } from '@/dashboard/VideoFindingsStrip';
import type { VideoSceneLayoutProps } from '@/dashboard/video-scenes/layout/types';

export function VideoFindingsRow({
  sceneId,
  showFindings,
  timeline,
}: Pick<VideoSceneLayoutProps, 'sceneId' | 'timeline'> & {
  showFindings: boolean;
}) {
  return (
    <div
      className={`vd-bottom${showFindings ? ' vd-bottom--findings-focus' : ''}${sceneId === 'findings' ? ' vd-bottom--findings-only' : ''}`}
    >
      {showFindings && (
        <VideoFindingsStrip timeline={timeline} focusMode={sceneId === 'findings'} />
      )}
      <div className="vd-letterbox" aria-hidden />
    </div>
  );
}
