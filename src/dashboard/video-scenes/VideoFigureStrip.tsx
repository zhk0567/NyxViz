import { ZoomableImage } from '@/components/ImageLightbox';

interface VideoFigureStripProps {
  figures: { src: string; caption: string; alt?: string }[];
  layout?: 'row' | 'stack';
  className?: string;
}

export function VideoFigureStrip({
  figures,
  layout = 'row',
  className,
}: VideoFigureStripProps) {
  const stripClass = ['vd-figure-strip', `vd-figure-strip--${layout}`, className]
    .filter(Boolean)
    .join(' ');
  return (
    <div className={stripClass}>
      {figures.map((fig) => (
        <figure key={fig.src} className="vd-figure-strip-item">
          <ZoomableImage src={fig.src} alt={fig.alt ?? fig.caption} loading="lazy" />
          {fig.caption && <figcaption>{fig.caption}</figcaption>}
        </figure>
      ))}
    </div>
  );
}
