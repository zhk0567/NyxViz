import { useEffect, useRef } from 'react';
import '@kitware/vtk.js/Rendering/Profiles/Volume';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume';
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper';
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkVolumeProperty from '@kitware/vtk.js/Rendering/Core/VolumeProperty';
import vtkLight from '@kitware/vtk.js/Rendering/Core/Light';
import { toVtkScalars } from '@/data/nyxLoader';
import { GRID_SIZE, DOMAIN_LENGTH, SPACING } from '@/data/types';
import {
  buildColorTransferFunction,
  buildOpacityTransferFunction,
  type TfParams,
} from './transferFunction';

interface VolumeSceneProps {
  data: Float32Array;
  dataMin: number;
  dataMax: number;
  highlightMin?: number;
  highlightMax?: number;
  tfParams?: TfParams;
  className?: string;
  onRendered?: () => void;
}

export function VolumeScene({
  data,
  dataMin,
  dataMax,
  highlightMin,
  highlightMax,
  tfParams,
  className,
  onRendered,
}: VolumeSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onRenderedRef = useRef(onRendered);
  onRenderedRef.current = onRendered;

  const contextRef = useRef<{
    fullScreenRenderer: ReturnType<typeof vtkFullScreenRenderWindow.newInstance>;
    volume: ReturnType<typeof vtkVolume.newInstance>;
    mapper: ReturnType<typeof vtkVolumeMapper.newInstance>;
    imageData: ReturnType<typeof vtkImageData.newInstance>;
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

    const light1 = vtkLight.newInstance();
    light1.setPosition(2, 3, 4);
    light1.setFocalPoint(0, 0, 0);
    light1.setColor(1, 1, 1);
    light1.setIntensity(1.0);
    renderer.addLight(light1);

    const light2 = vtkLight.newInstance();
    light2.setPosition(-3, -2, -4);
    light2.setFocalPoint(0, 0, 0);
    light2.setColor(0.6, 0.7, 1);
    light2.setIntensity(0.35);
    renderer.addLight(light2);

    const imageData = vtkImageData.newInstance();
    imageData.setDimensions(GRID_SIZE, GRID_SIZE, GRID_SIZE);
    imageData.setSpacing(SPACING, SPACING, SPACING);
    imageData.setOrigin(0, 0, 0);

    const mapper = vtkVolumeMapper.newInstance();
    mapper.setInputData(imageData);
    mapper.setSampleDistance(0.7);

    const volumeProperty = vtkVolumeProperty.newInstance();
    volumeProperty.setShade(true);
    volumeProperty.setAmbient(0.15);
    volumeProperty.setDiffuse(0.7);
    volumeProperty.setSpecular(0.35);
    volumeProperty.setSpecularPower(20);

    const volume = vtkVolume.newInstance();
    volume.setMapper(mapper);
    volume.setProperty(volumeProperty);
    renderer.addVolume(volume);

    const camera = renderer.getActiveCamera();
    camera.setPosition(
      DOMAIN_LENGTH * 1.8,
      DOMAIN_LENGTH * 1.4,
      DOMAIN_LENGTH * 1.6,
    );
    camera.setFocalPoint(
      DOMAIN_LENGTH / 2,
      DOMAIN_LENGTH / 2,
      DOMAIN_LENGTH / 2,
    );
    camera.setViewUp(0, 0, 1);
    renderer.resetCamera();
    renderer.resetCameraClippingRange();

    contextRef.current = { fullScreenRenderer, volume, mapper, imageData };

    const ro = new ResizeObserver(() => {
      fullScreenRenderer.resize();
      renderWindow.render();
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      volume.delete();
      mapper.delete();
      imageData.delete();
      fullScreenRenderer.delete();
      contextRef.current = null;
    };
  }, []);

  useEffect(() => {
    const ctx = contextRef.current;
    if (!ctx || !data) return;

    const scalars = toVtkScalars(data);
    const dataArray = vtkDataArray.newInstance({
      name: 'density',
      numberOfComponents: 1,
      values: scalars,
    });
    ctx.imageData.getPointData().setScalars(dataArray);

    const tfOpts = {
      dataMin,
      dataMax,
      highlightMin,
      highlightMax,
      ...tfParams,
    };
    const ctf = buildColorTransferFunction(tfOpts);
    const otf = buildOpacityTransferFunction(tfOpts);
    const property = ctx.volume.getProperty();
    property.setRGBTransferFunction(0, ctf);
    property.setScalarOpacity(0, otf);
    property.setScalarOpacityUnitDistance(0, SPACING * 2.5);

    ctx.mapper.modified();
    const rw = ctx.fullScreenRenderer.getRenderWindow();
    rw.render();

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        onRenderedRef.current?.();
      });
    });
  }, [
    data,
    dataMin,
    dataMax,
    highlightMin,
    highlightMax,
    tfParams?.opacityScale,
    tfParams?.densityGain,
    tfParams?.highlightBoost,
  ]);

  return <div ref={containerRef} className={className} data-vtk-volume />;
}
