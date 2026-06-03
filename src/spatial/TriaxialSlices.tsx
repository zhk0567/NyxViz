import { useEffect, useRef } from 'react';
import { getVoxel } from '@/data/nyxLoader';
import { GRID_SIZE } from '@/data/types';
import { buildCosmicLut256, densityToUnit } from '@/viz/colormap';

const LUT = buildCosmicLut256();
const MID = Math.floor(GRID_SIZE / 2);

type PlaneId = 'xy' | 'xz' | 'yz';

function fillPlane(
  data: Float32Array,
  plane: PlaneId,
  domainMin: number,
  domainMax: number,
): Uint8ClampedArray {
  const rgba = new Uint8ClampedArray(GRID_SIZE * GRID_SIZE * 4);
  for (let a = 0; a < GRID_SIZE; a++) {
    for (let b = 0; b < GRID_SIZE; b++) {
      let x: number;
      let y: number;
      let z: number;
      if (plane === 'xy') {
        x = a;
        y = b;
        z = MID;
      } else if (plane === 'xz') {
        x = a;
        y = MID;
        z = b;
      } else {
        x = MID;
        y = a;
        z = b;
      }
      const v = getVoxel(data, x, y, z);
      const u = densityToUnit(v, domainMin, domainMax, true);
      const li = Math.min(255, Math.floor(u * 255)) * 4;
      const o = (a + b * GRID_SIZE) * 4;
      rgba[o] = LUT[li]!;
      rgba[o + 1] = LUT[li + 1]!;
      rgba[o + 2] = LUT[li + 2]!;
      rgba[o + 3] = 255;
    }
  }
  return rgba;
}

function SliceThumb({
  label,
  plane,
  data,
  domainMin,
  domainMax,
}: {
  label: string;
  plane: PlaneId;
  data: Float32Array;
  domainMin: number;
  domainMax: number;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    let cancelled = false;
    const frame = requestAnimationFrame(() => {
      if (cancelled) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const rgba = fillPlane(data, plane, domainMin, domainMax);
      const img = new ImageData(rgba, GRID_SIZE, GRID_SIZE);
      canvas.width = GRID_SIZE;
      canvas.height = GRID_SIZE;
      ctx.putImageData(img, 0, 0);
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
    };
  }, [data, plane, domainMin, domainMax]);

  return (
    <figure className="slice-thumb">
      <canvas ref={ref} className="slice-canvas" />
      <figcaption>{label}</figcaption>
    </figure>
  );
}

interface TriaxialSlicesProps {
  data: Float32Array | null;
  domainMin: number;
  domainMax: number;
}

export function TriaxialSlices({ data, domainMin, domainMax }: TriaxialSlicesProps) {
  if (!data) {
    return <p className="panel-placeholder">加载体数据后显示切片…</p>;
  }

  return (
    <div className="triaxial-slices">
      <SliceThumb
        label={`XY z=${MID}`}
        plane="xy"
        data={data}
        domainMin={domainMin}
        domainMax={domainMax}
      />
      <SliceThumb
        label={`XZ y=${MID}`}
        plane="xz"
        data={data}
        domainMin={domainMin}
        domainMax={domainMax}
      />
      <SliceThumb
        label={`YZ x=${MID}`}
        plane="yz"
        data={data}
        domainMin={domainMin}
        domainMax={domainMax}
      />
    </div>
  );
}
