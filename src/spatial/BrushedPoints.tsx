import { useEffect, useRef } from 'react';
import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkPoints from '@kitware/vtk.js/Common/Core/Points';
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData';
import type { BrushedVoxel } from '@/data/types';
import { DOMAIN_LENGTH, SPACING } from '@/data/types';

interface BrushedPointsProps {
  points: BrushedVoxel[];
  className?: string;
}

export function BrushedPoints({ points, className }: BrushedPointsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contextRef = useRef<{
    fullScreenRenderer: ReturnType<typeof vtkFullScreenRenderWindow.newInstance>;
    polyData: ReturnType<typeof vtkPolyData.newInstance>;
  } | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
      rootContainer: container,
      containerStyle: { width: '100%', height: '100%' },
    });
    const renderer = fullScreenRenderer.getRenderer();
    const renderWindow = fullScreenRenderer.getRenderWindow();
    renderer.setBackground(0.04, 0.05, 0.1);

    const polyData = vtkPolyData.newInstance();
    const pointsData = vtkPoints.newInstance();
    polyData.setPoints(pointsData);

    const mapper = vtkMapper.newInstance();
    mapper.setInputData(polyData);

    const actor = vtkActor.newInstance();
    actor.setMapper(mapper);
    actor.getProperty().setColor(1, 0.85, 0.35);
    actor.getProperty().setPointSize(3);
    renderer.addActor(actor);

    const camera = renderer.getActiveCamera();
    camera.setPosition(
      DOMAIN_LENGTH * 1.6,
      DOMAIN_LENGTH * 1.3,
      DOMAIN_LENGTH * 1.5,
    );
    camera.setFocalPoint(
      DOMAIN_LENGTH / 2,
      DOMAIN_LENGTH / 2,
      DOMAIN_LENGTH / 2,
    );
    camera.setViewUp(0, 0, 1);
    renderer.resetCamera();

    contextRef.current = { fullScreenRenderer, polyData };

    const ro = new ResizeObserver(() => {
      fullScreenRenderer.resize();
      renderWindow.render();
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      actor.delete();
      mapper.delete();
      polyData.delete();
      fullScreenRenderer.delete();
      contextRef.current = null;
    };
  }, []);

  useEffect(() => {
    const ctx = contextRef.current;
    if (!ctx || points.length === 0) return;

    const coords = new Float32Array(points.length * 3);
    for (let i = 0; i < points.length; i++) {
      const p = points[i]!;
      coords[i * 3] = (p.x + 0.5) * SPACING;
      coords[i * 3 + 1] = (p.y + 0.5) * SPACING;
      coords[i * 3 + 2] = (p.z + 0.5) * SPACING;
    }

    const n = points.length;
    const verts = new Uint32Array(n * 2);
    for (let i = 0; i < n; i++) {
      verts[i * 2] = 1;
      verts[i * 2 + 1] = i;
    }

    const vtkPts = ctx.polyData.getPoints();
    vtkPts.setData(coords, 3);
    ctx.polyData.getVerts().setData(verts, 1);
    ctx.polyData.modified();

    const renderer = ctx.fullScreenRenderer.getRenderer();
    renderer.resetCamera();
    ctx.fullScreenRenderer.getRenderWindow().render();
  }, [points]);

  return <div ref={containerRef} className={className} />;
}
