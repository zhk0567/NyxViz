import { DensityProjection } from '@/spatial/DensityProjection';
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

export function VideoBrushPreviews({
  stats,
  densityData,
  volumeReady,
  loading,
  dataMin,
  dataMax,
  activePreset,
  onTop1,
  onFilament,
  onBottom1,
}: VideoBrushPreviewsProps) {
  const handlers: Record<string, () => void> = {
    top: onTop1,
    filament: onFilament,
    bottom: onBottom1,
    mid: () => {},
  };

  const canRender = densityData && volumeReady && !loading;

  return (
    <div className="vd-band-previews">
      {BANDS.map((b) => {
        const range = bandRange(stats, b.id);
        const onClick = b.preset ? handlers[b.preset] : undefined;
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
                <DensityProjection
                  data={densityData}
                  brushRange={range}
                  domainMin={dataMin}
                  domainMax={dataMax}
                  className="vd-band-proj"
                  compact
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
