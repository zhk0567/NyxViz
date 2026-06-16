import {
  MARK_STEPS,
  evolutionThumbnailSrc,
  handleEvolutionThumbnailError,
} from '@/dashboard/evolutionPhase';
import type { TimelineData } from '@/data/types';
import { ZoomableImage } from '@/components/ImageLightbox';

interface EvolutionThumbnailsProps {
  timeline: TimelineData;
  active: number;
  onSelect: (t: number) => void;
}

export function EvolutionThumbnails({ timeline, active, onSelect }: EvolutionThumbnailsProps) {
  return (
    <div className="evo-thumbs" role="list" aria-label="代表时间步">
      {MARK_STEPS.map((t) => {
        const stats = timeline.timesteps[t];
        const sigma = stats?.std.toFixed(3) ?? '—';
        return (
          <button
            key={t}
            type="button"
            role="listitem"
            className={`evo-thumb${active === t ? ' active' : ''}`}
            onClick={(e) => {
              // ZoomableImage 嵌在 button 内时，浏览器仍会激活 button；点击图片只放大，不切步
              if ((e.target as Element).closest('.vd-zoomable')) return;
              onSelect(t);
            }}
          >
            <div className="evo-thumb-media">
              <ZoomableImage
                src={evolutionThumbnailSrc(t)}
                alt={`t=${t} XY 最大密度投影演化`}
                loading="lazy"
                onError={(e) => handleEvolutionThumbnailError(e.currentTarget, t)}
              />
            </div>
            <span className="evo-thumb-label">
              t={t}
              <span className="evo-thumb-sigma">σ={sigma}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
