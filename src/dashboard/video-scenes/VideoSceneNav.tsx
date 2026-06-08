import { VIDEO_SCENES, sceneUrl, type VideoSceneId } from '@/video/sceneRegistry';

interface VideoSceneNavProps {
  currentScene: VideoSceneId;
  recordMode: boolean;
  onSceneChange: (id: VideoSceneId) => void;
}

export function VideoSceneNav({
  currentScene,
  recordMode,
  onSceneChange,
}: VideoSceneNavProps) {
  if (recordMode) {
    const url =
      typeof window !== 'undefined'
        ? `${window.location.origin}${sceneUrl(currentScene, true)}`
        : sceneUrl(currentScene, true);
    const title = VIDEO_SCENES.find((s) => s.id === currentScene)?.title ?? currentScene;

    return (
      <div className="vd-scene-record-copy">
        <span className="vd-scene-record-label">录屏场景 · {title}</span>
        <button
          type="button"
          className="vd-scene-copy-btn"
          onClick={() => {
            void navigator.clipboard.writeText(url);
          }}
        >
          复制分段 URL
        </button>
      </div>
    );
  }

  return (
    <div className="vd-scene-strip" role="tablist" aria-label="预览场景">
      {VIDEO_SCENES.map((s) => (
        <button
          key={s.id}
          type="button"
          role="tab"
          aria-selected={currentScene === s.id}
          className={`vd-scene-tab${currentScene === s.id ? ' on' : ''}`}
          onClick={() => onSceneChange(s.id)}
        >
          {s.title}
        </button>
      ))}
    </div>
  );
}
