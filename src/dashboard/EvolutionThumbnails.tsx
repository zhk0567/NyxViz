import { MARK_STEPS } from '@/dashboard/evolutionPhase';
import type { TimelineData } from '@/data/types';
import { ZoomableImage } from '@/components/ImageLightbox';

const EVO_FIGURES = MARK_STEPS.map(
  (t) => `/figures/task1_evo_t${String(t).padStart(4, '0')}.png`,
);

interface EvolutionThumbnailsProps {
  timeline: TimelineData;
  active: number;
  onSelect: (t: number) => void;
}

export function EvolutionThumbnails({ timeline, active, onSelect }: EvolutionThumbnailsProps) {
  return (
    <div className="evo-thumbs" role="list" aria-label="代表时间步">
      {MARK_STEPS.map((t, i) => {
        const stats = timeline.timesteps[t];
        const sigma = stats?.std.toFixed(3) ?? '—';
        return (
          <button
            key={t}
            type="button"
            role="listitem"
            className={`evo-thumb${active === t ? ' active' : ''}`}
            onClick={() => onSelect(t)}
          >
            <div className="evo-thumb-media">
              <ZoomableImage
                src={EVO_FIGURES[i]}
                alt={`t=${t} 密度投影演化`}
                loading="lazy"
                onError={(e) => {
                  const img = e.currentTarget;
                  if (!img.dataset.fallback) {
                    img.dataset.fallback = 'vol';
                    img.src = `/figures/task1_vol_t${String(t).padStart(4, '0')}.png`;
                    return;
                  }
                  img.src = `/figures/task1_slice_t${String(t).padStart(4, '0')}.png`;
                }}
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
