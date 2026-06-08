interface VideoSceneChromeProps {
  title: string;
  recordMode: boolean;
}

/** 不占 grid 行；录屏/预览均不渲染，避免破坏 dashboard 行布局 */
export function VideoSceneChrome(_props: VideoSceneChromeProps) {
  return null;
}
