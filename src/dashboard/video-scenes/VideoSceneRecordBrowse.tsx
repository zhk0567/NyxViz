import { VIDEO_SCENES, sceneBrowseLabel, type VideoSceneId } from '@/video/sceneRegistry';

interface VideoSceneRecordBrowseProps {
  currentScene: VideoSceneId;
  onSceneChange: (id: VideoSceneId) => void;
}

export function VideoSceneRecordBrowse({
  currentScene,
  onSceneChange,
}: VideoSceneRecordBrowseProps) {
  return (
    <nav className="vd-scene-browse" aria-label="录屏 11 段场景">
      <div className="vd-scene-browse-track" role="tablist">
        {VIDEO_SCENES.map((s, index) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={currentScene === s.id}
            className={`vd-scene-browse-btn${currentScene === s.id ? ' on' : ''}`}
            title={s.title}
            onClick={() => onSceneChange(s.id)}
          >
            <span className="vd-scene-browse-num">{index + 1}</span>
            <span className="vd-scene-browse-label">{sceneBrowseLabel(s)}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
