import { useEffect, useRef } from 'react';
import '@kitware/vtk.js/Rendering/Profiles/Volume';
import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume';
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper';
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkVolumeProperty from '@kitware/vtk.js/Rendering/Core/VolumeProperty';
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction';
import vtkLight from '@kitware/vtk.js/Rendering/Core/Light';
import vtkAxesActor from '@kitware/vtk.js/Rendering/Core/AxesActor';
import vtkOrientationMarkerWidget from '@kitware/vtk.js/Interaction/Widgets/OrientationMarkerWidget';
import { getCachedVtkScalars, getVtkScalarsAsync } from '@/data/nyxLoader';
import { GRID_SIZE, DOMAIN_LENGTH, SPACING } from '@/data/types';
import {
  fillColorTransferFunction,
  fillOpacityTransferFunction,
  type TfParams,
} from './transferFunction';
import { debounce } from '@/utils/debounce';
import { fitVolumeCamera } from './fitVolumeCamera';
import {
  OPACITY_SCALAR_UNIT_DISTANCE,
  VOLUME_LIGHTING,
  VOLUME_QUALITY_PRESETS,
} from './renderSpec';

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
  /** >1 zooms in (video dashboard uses ~1.1). */
  cameraZoom?: number;
  /** 录屏页关闭方向轴控件以加快初始化 */
  showOrientation?: boolean;
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
  cameraZoom = 1,
  showOrientation = true,
  className,
  onRendered,
}: VolumeSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onRenderedRef = useRef(onRendered);
  onRenderedRef.current = onRendered;
  const renderActiveRef = useRef(renderActive);
  renderActiveRef.current = renderActive;
  const cameraZoomRef = useRef(cameraZoom);
  cameraZoomRef.current = cameraZoom;

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
    orientationWidget: ReturnType<
      typeof vtkOrientationMarkerWidget.newInstance
    > | null;
    axesActor: ReturnType<typeof vtkAxesActor.newInstance> | null;
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
    fitVolumeCamera(ctx.renderer, ctx.imageData, aspect, cameraZoomRef.current);
    ctx.orientationWidget?.updateViewport();
    ctx.orientationWidget?.updateMarkerOrientation();
    ctx.fullScreenRenderer.getRenderWindow().render();
  };

  const requestRender = () => {
    const ctx = contextRef.current;
    if (!ctx || !renderActiveRef.current) return;
    ctx.orientationWidget?.updateMarkerOrientation();
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
    light1.setPosition(
      fc + VOLUME_LIGHTING.key.offset[0],
      fc + VOLUME_LIGHTING.key.offset[1],
      fc + VOLUME_LIGHTING.key.offset[2],
    );
    light1.setFocalPoint(fc, fc, fc);
    light1.setColor(...VOLUME_LIGHTING.key.color);
    light1.setIntensity(VOLUME_LIGHTING.key.intensity);
    renderer.addLight(light1);

    const light2 = vtkLight.newInstance();
    light2.setPosition(
      fc + VOLUME_LIGHTING.fill.offset[0],
      fc + VOLUME_LIGHTING.fill.offset[1],
      fc + VOLUME_LIGHTING.fill.offset[2],
    );
    light2.setFocalPoint(fc, fc, fc);
    light2.setColor(...VOLUME_LIGHTING.fill.color);
    light2.setIntensity(VOLUME_LIGHTING.fill.intensity);
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
    volumeProperty.setScalarOpacityUnitDistance(
      0,
      SPACING * OPACITY_SCALAR_UNIT_DISTANCE,
    );

    const volume = vtkVolume.newInstance();
    volume.setMapper(mapper);
    volume.setProperty(volumeProperty);
    renderer.addVolume(volume);

    fitVolumeCamera(
      renderer,
      imageData,
      container.clientWidth / container.clientHeight || 1,
      cameraZoomRef.current,
    );

    let orientationWidget: ReturnType<
      typeof vtkOrientationMarkerWidget.newInstance
    > | null = null;
    let axesActor: ReturnType<typeof vtkAxesActor.newInstance> | null = null;

    if (showOrientation) {
      axesActor = vtkAxesActor.newInstance({
        config: {
          recenter: false,
          tipRadius: 0.14,
          shaftRadius: 0.05,
          tipLength: 0.26,
        },
      });
      axesActor.setXAxisColor([235, 72, 72]);
      axesActor.setYAxisColor([72, 210, 92]);
      axesActor.setZAxisColor([72, 140, 255]);
      axesActor.update();

      orientationWidget = vtkOrientationMarkerWidget.newInstance({
        actor: axesActor,
        interactor: renderWindow.getInteractor(),
        parentRenderer: renderer,
      });
      orientationWidget.setViewportCorner(
        vtkOrientationMarkerWidget.Corners.BOTTOM_LEFT,
      );
      orientationWidget.setViewportSize(0.2);
      orientationWidget.setMinPixelSize(80);
      orientationWidget.setMaxPixelSize(128);
      orientationWidget.setEnabled(true);

      requestAnimationFrame(() => {
        orientationWidget?.updateViewport();
        orientationWidget?.updateMarkerOrientation();
        renderWindow.render();
      });
    }

    contextRef.current = {
      fullScreenRenderer,
      renderer,
      volume,
      mapper,
      imageData,
      dataArray,
      ctf,
      otf,
      orientationWidget,
      axesActor,
    };

    const resize = debounce(() => {
      frameCamera();
    }, 120);
    const ro = new ResizeObserver(() => resize());
    ro.observe(container);

    return () => {
      resize.cancel();
      ro.disconnect();
      if (orientationWidget) {
        orientationWidget.setEnabled(false);
        orientationWidget.delete();
      }
      if (axesActor) axesActor.delete();
      volume.delete();
      mapper.delete();
      otf.delete();
      ctf.delete();
      dataArray.delete();
      imageData.delete();
      fullScreenRenderer.delete();
      contextRef.current = null;
    };
  }, [showOrientation]);

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

    const preset = VOLUME_QUALITY_PRESETS[quality];
    ctx.mapper.setSampleDistance(preset.sampleDistance);
    ctx.mapper.setMaximumSamplesPerRay(preset.maximumSamplesPerRay);
    const property = ctx.volume.getProperty();
    property.setShade(preset.shade);
    property.setAmbient(preset.ambient);
    property.setDiffuse(preset.diffuse);
    property.setSpecular(preset.specular);

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
    frameCamera();
  }, [cameraZoom]);

  useEffect(() => {
    const onVisibility = () => {
      if (!document.hidden && renderActiveRef.current) requestRender();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  return <div ref={containerRef} className={className} data-vtk-volume />;
}
