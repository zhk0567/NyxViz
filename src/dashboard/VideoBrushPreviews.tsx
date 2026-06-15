import { figuresUrl, isStaticFiguresOnly } from '@/config/publicPaths';
import { useSharedProjection } from '@/hooks/useSharedProjection';
import { BandPreviewCanvas } from '@/spatial/BandPreviewCanvas';
import type { BrushPresetId } from '@/data/brushPreset';
import type { BrushRange, TimelineData } from '@/data/types';

interface VideoBrushPreviewsProps {
  stats: TimelineData['timesteps'][0];
  densityData: Float32Array | null;
  volumeReady: boolean;
  loading: boolean;
  dataMin: number;
  dataMax: number;
  activePreset: BrushPresetId | null;
  onTop1: () => void;
  onFilament: () => void;
  onBottom1: () => void;
}

function bandRange(
  stats: TimelineData['timesteps'][0],
  band: BrushPresetId | 'mid',
): BrushRange {
  switch (band) {
    case 'top':
      return { min: stats.p99, max: stats.max };
    case 'filament':
      return { min: stats.p90, max: stats.p99 };
    case 'bottom':
      return { min: stats.min, max: stats.p01 };
    case 'mid':
      return { min: stats.p01, max: stats.p90 };
  }
}

const BANDS: {
  id: BrushPresetId | 'mid';
  label: string;
  preset?: BrushPresetId;
}[] = [
  { id: 'bottom', label: 'Bottom 1%', preset: 'bottom' },
  { id: 'mid', label: '10–90%' },
  { id: 'filament', label: '90–99%', preset: 'filament' },
  { id: 'top', label: 'Top 1%', preset: 'top' },
];

const STATIC_BAND_FIGURES: Record<(typeof BANDS)[number]['id'], string> = {
  bottom: 'task4_brush_bottom_proj.png',
  mid: 'task4_discovery_context_t99.png',
  filament: 'task4_spatial_filament.png',
  top: 'task4_brush_top1.png',
};

const STATIC_BAND_FALLBACKS: Partial<Record<(typeof BANDS)[number]['id'], string>> = {
  bottom: 'task4_brush_bottom_hl.png',
  filament: 'task4_panel_filament.png',
  top: 'task4_brush_top1_viz.png',
};

export function VideoBrushPreviews({
  stats,
  densityData,
  loading,
  dataMin,
  dataMax,
  activePreset,
  onTop1,
  onFilament,
  onBottom1,
}: VideoBrushPreviewsProps) {
  const projection = useSharedProjection(densityData, 'xy');

  const handlers: Record<string, () => void> = {
    top: onTop1,
    filament: onFilament,
    bottom: onBottom1,
    mid: () => {},
  };

  const canRender = densityData && projection && !loading;
  const staticOnly = isStaticFiguresOnly();

  return (
    <div className="vd-band-previews">
      {BANDS.map((b) => {
        const range = bandRange(stats, b.id);
        const onClick = b.preset ? handlers[b.preset] : undefined;
        const staticSrc = staticOnly ? STATIC_BAND_FIGURES[b.id] : undefined;
        return (
          <button
            key={b.id}
            type="button"
            className={`vd-band-cell band-${b.id}${activePreset === b.preset ? ' on' : ''}`}
            onClick={onClick}
            disabled={!onClick}
            title={b.label}
          >
            <span className="vd-band-label">{b.label}</span>
            <div className="vd-band-media">
              {canRender ? (
                <BandPreviewCanvas
                  projection={projection}
                  brushRange={range}
                  domainMin={dataMin}
                  domainMax={dataMax}
                  className="vd-band-proj"
                />
              ) : staticSrc ? (
                <img
                  className="vd-band-proj vd-band-static"
                  src={figuresUrl(staticSrc)}
                  alt={b.label}
                  loading="lazy"
                  onError={(e) => {
                    const fb = STATIC_BAND_FALLBACKS[b.id];
                    if (fb && !e.currentTarget.dataset.fallback) {
                      e.currentTarget.dataset.fallback = '1';
                      e.currentTarget.src = figuresUrl(fb);
                    }
                  }}
                />
              ) : (
                <span className="vd-band-placeholder">…</span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
