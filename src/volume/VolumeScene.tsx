import { useEffect, useRef } from 'react';
import '@kitware/vtk.js/Rendering/Profiles/Volume';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume';
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper';
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkVolumeProperty from '@kitware/vtk.js/Rendering/Core/VolumeProperty';
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction';
import vtkLight from '@kitware/vtk.js/Rendering/Core/Light';
import { getCachedVtkScalars, getVtkScalarsAsync } from '@/data/nyxLoader';
import { GRID_SIZE, DOMAIN_LENGTH, SPACING } from '@/data/types';
import {
  fillColorTransferFunction,
  fillOpacityTransferFunction,
  type TfParams,
} from './transferFunction';
import { debounce } from '@/utils/debounce';
import { fitVolumeCamera } from './fitVolumeCamera';

export type VolumeQuality = 'interactive' | 'high' | 'presentation';

interface VolumeSceneProps {
  data: Float32Array;
  timestep: number;
  dataMin: number;
  dataMax: number;
  highlightMin?: number;
  highlightMax?: number;
  tfParams?: TfParams;
  quality?: VolumeQuality;
  useLogScale?: boolean;
  /** When false, skip GPU render (e.g. hidden tab). */
  renderActive?: boolean;
  className?: string;
  onRendered?: () => void;
}

export function VolumeScene({
  data,
  timestep,
  dataMin,
  dataMax,
  highlightMin,
  highlightMax,
  tfParams,
  quality = 'presentation',
  useLogScale = true,
  renderActive = true,
  className,
  onRendered,
}: VolumeSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onRenderedRef = useRef(onRendered);
  onRenderedRef.current = onRendered;
  const renderActiveRef = useRef(renderActive);
  renderActiveRef.current = renderActive;

  const contextRef = useRef<{
    fullScreenRenderer: ReturnType<typeof vtkFullScreenRenderWindow.newInstance>;
    renderer: ReturnType<
      ReturnType<typeof vtkFullScreenRenderWindow.newInstance>['getRenderer']
    >;
    volume: ReturnType<typeof vtkVolume.newInstance>;
    mapper: ReturnType<typeof vtkVolumeMapper.newInstance>;
    imageData: ReturnType<typeof vtkImageData.newInstance>;
    dataArray: ReturnType<typeof vtkDataArray.newInstance>;
    ctf: ReturnType<typeof vtkColorTransferFunction.newInstance>;
    otf: ReturnType<typeof vtkPiecewiseFunction.newInstance>;
  } | null>(null);

  const frameCamera = () => {
    const ctx = contextRef.current;
    const container = containerRef.current;
    if (!ctx || !container) return;
    const aspect =
      container.clientHeight > 0
        ? container.clientWidth / container.clientHeight
        : 1;
    ctx.fullScreenRenderer.resize();
    fitVolumeCamera(ctx.renderer, ctx.imageData, aspect);
    ctx.fullScreenRenderer.getRenderWindow().render();
  };

  const requestRender = () => {
    const ctx = contextRef.current;
    if (!ctx || !renderActiveRef.current) return;
    ctx.fullScreenRenderer.getRenderWindow().render();
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
      rootContainer: container,
      containerStyle: { width: '100%', height: '100%' },
    });
    const renderer = fullScreenRenderer.getRenderer();
    const renderWindow = fullScreenRenderer.getRenderWindow();
    renderer.setBackground(0.039, 0.055, 0.153);

    const fc = DOMAIN_LENGTH / 2;
    const light1 = vtkLight.newInstance();
    light1.setPosition(fc + 8, fc + 10, fc + 12);
    light1.setFocalPoint(fc, fc, fc);
    light1.setColor(1, 1, 1);
    light1.setIntensity(1.0);
    renderer.addLight(light1);

    const light2 = vtkLight.newInstance();
    light2.setPosition(fc - 12, fc - 8, fc - 10);
    light2.setFocalPoint(fc, fc, fc);
    light2.setColor(0.55, 0.75, 1);
    light2.setIntensity(0.3);
    renderer.addLight(light2);

    const imageData = vtkImageData.newInstance();
    imageData.setDimensions(GRID_SIZE, GRID_SIZE, GRID_SIZE);
    imageData.setSpacing(SPACING, SPACING, SPACING);
    imageData.setOrigin(0, 0, 0);

    const dataArray = vtkDataArray.newInstance({
      name: 'density',
      numberOfComponents: 1,
      values: new Float32Array(0),
    });
    imageData.getPointData().setScalars(dataArray);

    const mapper = vtkVolumeMapper.newInstance();
    mapper.setInputData(imageData);

    const ctf = vtkColorTransferFunction.newInstance();
    const otf = vtkPiecewiseFunction.newInstance();

    const volumeProperty = vtkVolumeProperty.newInstance();
    volumeProperty.setShade(false);
    volumeProperty.setAmbient(0.2);
    volumeProperty.setDiffuse(0.55);
    volumeProperty.setSpecular(0.1);
    volumeProperty.setRGBTransferFunction(0, ctf);
    volumeProperty.setScalarOpacity(0, otf);
    volumeProperty.setScalarOpacityUnitDistance(0, SPACING * 2.5);

    const volume = vtkVolume.newInstance();
    volume.setMapper(mapper);
    volume.setProperty(volumeProperty);
    renderer.addVolume(volume);

    fitVolumeCamera(renderer, imageData, container.clientWidth / container.clientHeight || 1);

    contextRef.current = {
      fullScreenRenderer,
      renderer,
      volume,
      mapper,
      imageData,
      dataArray,
      ctf,
      otf,
    };

    const resize = debounce(() => {
      frameCamera();
    }, 120);
    const ro = new ResizeObserver(() => resize());
    ro.observe(container);

    return () => {
      resize.cancel();
      ro.disconnect();
      volume.delete();
      mapper.delete();
      otf.delete();
      ctf.delete();
      dataArray.delete();
      imageData.delete();
      fullScreenRenderer.delete();
      contextRef.current = null;
    };
  }, []);

  useEffect(() => {
    const ctx = contextRef.current;
    if (!ctx || !data) return;

    let cancelled = false;

    const upload = (scalars: Float32Array) => {
      if (cancelled) return;
      ctx.dataArray.setData(scalars, 1);
      ctx.imageData.modified();
      ctx.mapper.modified();
      requestAnimationFrame(() => {
        if (cancelled) return;
        requestRender();
        onRenderedRef.current?.();
      });
    };

    const cached = getCachedVtkScalars(timestep, data);
    if (cached) {
      upload(cached);
      return () => {
        cancelled = true;
      };
    }

    void getVtkScalarsAsync(timestep, data).then((scalars) => upload(scalars));

    return () => {
      cancelled = true;
    };
  }, [data, timestep]);

  useEffect(() => {
    const ctx = contextRef.current;
    if (!ctx) return;

    const pres = quality === 'presentation' || quality === 'high';
    const sampleDist =
      quality === 'presentation' ? 0.85 : quality === 'high' ? 1.2 : 4.0;
    ctx.mapper.setSampleDistance(sampleDist);
    ctx.mapper.setMaximumSamplesPerRay(
      quality === 'presentation' ? 4096 : quality === 'high' ? 2048 : 512,
    );
    const property = ctx.volume.getProperty();
    property.setShade(pres);
    property.setAmbient(pres ? 0.12 : 0.2);
    property.setDiffuse(pres ? 0.75 : 0.55);
    property.setSpecular(pres ? 0.4 : 0.1);

    const opts = {
      dataMin,
      dataMax,
      highlightMin,
      highlightMax,
      useLogScale,
      ...tfParams,
    };
    fillColorTransferFunction(ctx.ctf, opts);
    fillOpacityTransferFunction(ctx.otf, opts);

    ctx.mapper.modified();
    requestRender();
  }, [
    dataMin,
    dataMax,
    highlightMin,
    highlightMax,
    quality,
    useLogScale,
    tfParams?.opacityScale,
    tfParams?.densityGain,
    tfParams?.highlightBoost,
  ]);

  useEffect(() => {
    if (renderActive) requestRender();
  }, [renderActive]);

  useEffect(() => {
    const onVisibility = () => {
      if (!document.hidden && renderActiveRef.current) requestRender();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  return <div ref={containerRef} className={className} data-vtk-volume />;
}
