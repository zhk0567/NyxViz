import type { ReactNode } from 'react';
import { DensityHistogram } from '@/histogram/DensityHistogram';
import { DensityProjection } from '@/spatial/DensityProjection';
import type { BrushRange, TimelineData } from '@/data/types';

interface InteractiveBrushLabProps {
  timeline: TimelineData;
  densityData: Float32Array | null;
  volumeReady: boolean;
  loading: boolean;
  brushRange: BrushRange | null;
  domainMin: number;
  domainMax: number;
  onTop1: () => void;
  onBottom1: () => void;
  onFilament: () => void;
  onClear: () => void;
  vtkSlot: ReactNode;
}

export function InteractiveBrushLab({
  timeline,
  densityData,
  volumeReady,
  loading,
  brushRange,
  domainMin,
  domainMax,
  onTop1,
  onBottom1,
  onFilament,
  onClear,
  vtkSlot,
}: InteractiveBrushLabProps) {
  const projection =
    densityData && volumeReady && !loading ? (
      <DensityProjection
        data={densityData}
        brushRange={brushRange}
        axis="xy"
        domainMin={domainMin}
        domainMax={domainMax}
        className="lab-projection"
      />
    ) : (
      <div className="lab-placeholder">加载体数据后显示投影…</div>
    );

  return (
    <div className="brush-lab">
      <div className="brush-lab-presets">
        <button type="button" className="lab-btn lab-top" onClick={onTop1}>
          Top 1% 节点
        </button>
        <button type="button" className="lab-btn lab-fil" onClick={onFilament}>
          90–99% 纤维
        </button>
        <button type="button" className="lab-btn lab-bot" onClick={onBottom1}>
          Bottom 1% 空洞
        </button>
        <button type="button" className="lab-btn lab-clear" onClick={onClear}>
          清除
        </button>
      </div>
      <div className="brush-lab-grid">
        <div className="brush-lab-cell">
          <span className="brush-lab-label">相空间直方图（拖拽框选）</span>
          <DensityHistogram timeline={timeline} />
        </div>
        <div className="brush-lab-cell">
          <span className="brush-lab-label">体渲染联动</span>
          <div className="brush-lab-vtk">{vtkSlot}</div>
        </div>
        <div className="brush-lab-cell">
          <span className="brush-lab-label">XY 最大密度投影</span>
          {projection}
        </div>
      </div>
    </div>
  );
}
