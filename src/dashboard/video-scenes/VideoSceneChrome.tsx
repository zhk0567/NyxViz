interface VideoSceneChromeProps {
  title: string;
  recordMode: boolean;
}

/** 录屏模式：header 下方单行场景标题，便于分段识别 */
export function VideoSceneChrome({ title, recordMode }: VideoSceneChromeProps) {
  if (!recordMode) return null;
  return (
    <div className="vd-scene-chrome" aria-hidden="true">
      <span className="vd-scene-chrome-label">{title}</span>
    </div>
  );
}
