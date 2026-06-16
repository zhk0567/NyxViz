import { VideoVoidPanel } from '@/dashboard/video-scenes/VideoVoidPanel';
import type { ValidationExtendedData } from '@/data/statsLoader';
import { figuresUrl } from '@/config/publicPaths';
import { ZoomableImage } from '@/components/ImageLightbox';

interface VideoVoidSceneProps {
  validation: ValidationExtendedData | null;
}

export function VideoVoidScene({ validation }: VideoVoidSceneProps) {
  return (
    <div className="vd-body vd-body--void">
      <div className="vd-void-col vd-void-col--stats">
        <VideoVoidPanel validation={validation} />
      </div>
      <figure className="vd-void-figure vd-void-col--chart">
        <ZoomableImage
          src={figuresUrl('task3_void_evolution.png')}
          alt="void 占比随时间演化"
          loading="eager"
        />
        <figcaption>低密度 void 占比演化（p10 / p01 阈值）</figcaption>
      </figure>
    </div>
  );
}
