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
import { markPresentationReady } from '@/volume/volumeQualityCache';
import { GRID_SIZE, DOMAIN_LENGTH, SPACING, VOXEL_COUNT } from '@/data/types';
import {
  fillColorTransferFunction,
  fillOpacityTransferFunction,
  type TfParams,
  type VisualStyle,
} from './transferFunction';
import { debounce } from '@/utils/debounce';
import { fitVolumeCamera } from './fitVolumeCamera';
import {
  applyAdaptiveVolumeSampling,
  getCameraDistance,
  measureVolumeZoomRatio,
} from './adaptiveVolumeSampling';
import {
  cancelFlyAnimation,
  captureCameraState,
  flyCameraToPoint,
  flyCameraToState,
  restoreCameraState,
  type CameraState,
} from './volumeCameraFly';
import {
  displayToWorldRay,
  pickDensityPeakAlongRay,
} from './volumeFocusPick';
import {
  CINEMATIC_LIGHTING,
  OPACITY_SCALAR_UNIT_DISTANCE,
  VOLUME_LIGHTING,
  VOLUME_QUALITY_PRESETS,
  VOLUME_RENDERER_BG,
  VIDEO_DRAG_SAMPLING,
  type PerformanceMode,
  type VolumeQuality,
} from './renderSpec';

export type { VolumeQuality };

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
  /** >1 zooms in (video dashboard uses ~1.24). */
  cameraZoom?: number;
  /** 录屏页关闭方向轴控件以加快初始化 */
  showOrientation?: boolean;
  /** 允许滚轮缩放 / 拖拽旋转 */
  interactiveCamera?: boolean;
  /** 局部放大时自动提高体渲染采样精度 */
  adaptivePrecisionZoom?: boolean;
  /** 单击拾取高密结构并飞入特写 */
  focusOnClick?: boolean;
  /** 射线拾取密度阈值（默认 p75） */
  focusDensityThreshold?: number;
  onFocusChange?: (focused: boolean) => void;
  /** 录屏页降低交互帧率与拖拽采样 */
  performanceMode?: PerformanceMode;
  /** cinematic = 深空亮丝；standard = 原 cosmic 曲线 */
  visualStyle?: VisualStyle;
  className?: string;
  onRendered?: () => void;
  /** 相机拖拽 / 飞行动画开始，用于重置 idle 升采样计时 */
  onCameraActivity?: () => void;
}

export function VolumeScene({
  data,
  timestep,
  dataMin,
  dataMax,
  highlightMin,
  highlightMax,
  tfParams,
  quality = 'cinematic',
  useLogScale = true,
  renderActive = true,
  cameraZoom = 1,
  showOrientation = true,
  interactiveCamera = false,
  adaptivePrecisionZoom = true,
  focusOnClick = false,
  focusDensityThreshold,
  onFocusChange,
  performanceMode = 'interactive',
  visualStyle = 'cinematic',
  className,
  onRendered,
  onCameraActivity,
}: VolumeSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onRenderedRef = useRef(onRendered);
  onRenderedRef.current = onRendered;
  const onCameraActivityRef = useRef(onCameraActivity);
  onCameraActivityRef.current = onCameraActivity;
  const renderActiveRef = useRef(renderActive);
  renderActiveRef.current = renderActive;
  const cameraZoomRef = useRef(cameraZoom);
  cameraZoomRef.current = cameraZoom;
  const qualityRef = useRef(quality);
  qualityRef.current = quality;
  const baselineDistanceRef = useRef(1);
  const interactiveCameraRef = useRef(interactiveCamera);
  interactiveCameraRef.current = interactiveCamera;
  const adaptivePrecisionRef = useRef(adaptivePrecisionZoom);
  adaptivePrecisionRef.current = adaptivePrecisionZoom;
  const focusOnClickRef = useRef(focusOnClick);
  focusOnClickRef.current = focusOnClick;
  const focusThresholdRef = useRef(focusDensityThreshold ?? 9.5);
  focusThresholdRef.current = focusDensityThreshold ?? 9.5;
  const onFocusChangeRef = useRef(onFocusChange);
  onFocusChangeRef.current = onFocusChange;
  const dataRef = useRef(data);
  dataRef.current = data;
  const homeCameraRef = useRef<CameraState | null>(null);
  const isFocusedRef = useRef(false);
  const interactionActiveRef = useRef(false);
  const flyActiveRef = useRef(false);
  const performanceModeRef = useRef(performanceMode);
  performanceModeRef.current = performanceMode;
  const visualStyleRef = useRef(visualStyle);
  visualStyleRef.current = visualStyle;
  const interactionEndTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const loadedScalarsRef = useRef<{ timestep: number; scalars: Float32Array } | null>(
    null,
  );
  const renderRafRef = useRef(0);
  const uploadGenRef = useRef(0);
  const scheduleUploadRef = useRef<(() => void) | null>(null);
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

  const applyStaticSampling = (preset: {
    sampleDistance: number;
    maximumSamplesPerRay: number;
  }) => {
    const ctx = contextRef.current;
    if (!ctx) return;
    ctx.mapper.setSampleDistance(preset.sampleDistance);
    ctx.mapper.setMaximumSamplesPerRay(preset.maximumSamplesPerRay);
    ctx.mapper.modified();
  };

  const applyFocusedAdaptiveSampling = () => {
    const ctx = contextRef.current;
    if (!ctx || !adaptivePrecisionRef.current) return;
    const zoomRatio = measureVolumeZoomRatio(
      ctx.renderer.getActiveCamera(),
      baselineDistanceRef.current,
    );
    applyAdaptiveVolumeSampling(ctx.mapper, qualityRef.current, zoomRatio);
    ctx.mapper.modified();
  };

  const cancelFly = () => {
    cancelFlyAnimation();
    flyActiveRef.current = false;
  };

  const notifyCameraActivity = () => {
    onCameraActivityRef.current?.();
  };

  const saveHomeCamera = () => {
    const ctx = contextRef.current;
    if (!ctx) return;
    const camera = ctx.renderer.getActiveCamera();
    homeCameraRef.current = captureCameraState(camera);
    baselineDistanceRef.current = getCameraDistance(camera);
    isFocusedRef.current = false;
    onFocusChangeRef.current?.(false);
  };

  const resetHomeCamera = (animate = true) => {
    const ctx = contextRef.current;
    const home = homeCameraRef.current;
    if (!ctx || !home) return;
    cancelFly();
    const camera = ctx.renderer.getActiveCamera();
    const rw = ctx.fullScreenRenderer.getRenderWindow();
    const flyMaxFps = performanceModeRef.current === 'video' ? 24 : 60;

    const finish = () => {
      flyActiveRef.current = false;
      isFocusedRef.current = false;
      onFocusChangeRef.current?.(false);
      applyTargetSampling();
      rw.render();
    };

    if (animate) {
      flyActiveRef.current = true;
      notifyCameraActivity();
      applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);
      flyCameraToState(camera, home, {
        maxFps: flyMaxFps,
        onFrame: () => {
          ctx.renderer.resetCameraClippingRange();
          requestRender();
        },
        onComplete: finish,
      });
    } else {
      restoreCameraState(camera, home);
      ctx.renderer.resetCameraClippingRange();
      finish();
    }
  };

  const handleFocusPick = (displayX: number, displayY: number) => {
    const ctx = contextRef.current;
    if (!ctx || !focusOnClickRef.current || flyActiveRef.current) return;

    const ray = displayToWorldRay(ctx.renderer, displayX, displayY);
    const pick = pickDensityPeakAlongRay(
      dataRef.current,
      ray.origin,
      ray.direction,
      focusThresholdRef.current,
    );
    if (!pick) return;

    if (!pick) return;

    cancelFly();
    const camera = ctx.renderer.getActiveCamera();
    const rw = ctx.fullScreenRenderer.getRenderWindow();
    const flyMaxFps = performanceModeRef.current === 'video' ? 24 : 60;

    flyActiveRef.current = true;
    notifyCameraActivity();
    applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);

    flyCameraToPoint(camera, pick.point, {
      homeDistance: baselineDistanceRef.current,
      maxFps: flyMaxFps,
      onFrame: () => {
        ctx.renderer.resetCameraClippingRange();
        requestRender();
      },
      onComplete: () => {
        flyActiveRef.current = false;
        isFocusedRef.current = true;
        onFocusChangeRef.current?.(true);
        applyTargetSampling();
        rw.render();
      },
    });
  };

  const applyTargetSampling = () => {
    const ctx = contextRef.current;
    if (!ctx) return;

    if (flyActiveRef.current) {
      applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);
      return;
    }

    if (interactionActiveRef.current) {
      if (performanceModeRef.current === 'video' || qualityRef.current === 'video') {
        applyStaticSampling(VIDEO_DRAG_SAMPLING);
      } else {
        applyStaticSampling(VOLUME_QUALITY_PRESETS.interactive);
      }
      return;
    }

    if (isFocusedRef.current && adaptivePrecisionRef.current) {
      applyFocusedAdaptiveSampling();
      return;
    }

    applyStaticSampling(VOLUME_QUALITY_PRESETS[qualityRef.current]);
  };

  const applyInteractionSampling = () => {
    if (performanceModeRef.current === 'video' || qualityRef.current === 'video') {
      applyStaticSampling(VIDEO_DRAG_SAMPLING);
    } else {
      applyStaticSampling(VOLUME_QUALITY_PRESETS.interactive);
    }
  };

  const resetCameraForTimestep = () => {
    const ctx = contextRef.current;
    const container = containerRef.current;
    if (!ctx || !container) return;

    cancelFly();
    isFocusedRef.current = false;
    onFocusChangeRef.current?.(false);

    const aspect =
      container.clientHeight > 0
        ? container.clientWidth / container.clientHeight
        : 1;
    fitVolumeCamera(ctx.renderer, ctx.imageData, aspect, cameraZoomRef.current);
    saveHomeCamera();
    applyTargetSampling();
    ctx.orientationWidget?.updateMarkerOrientation();
    requestRender();
  };

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
    saveHomeCamera();
    applyTargetSampling();
    ctx.orientationWidget?.updateViewport();
    ctx.orientationWidget?.updateMarkerOrientation();
    ctx.fullScreenRenderer.getRenderWindow().render();
  };

  const requestRender = () => {
    const ctx = contextRef.current;
    if (!ctx || !renderActiveRef.current) return;
    if (renderRafRef.current) return;
    renderRafRef.current = requestAnimationFrame(() => {
      renderRafRef.current = 0;
      if (!contextRef.current || !renderActiveRef.current) return;
      contextRef.current.orientationWidget?.updateMarkerOrientation();
      contextRef.current.fullScreenRenderer.getRenderWindow().render();
    });
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.replaceChildren();

    const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
      rootContainer: container,
      containerStyle: { width: '100%', height: '100%' },
      listenWindowResize: false,
    });
    const renderer = fullScreenRenderer.getRenderer();
    const renderWindow = fullScreenRenderer.getRenderWindow();
    renderer.setBackground(...VOLUME_RENDERER_BG);

    const fc = DOMAIN_LENGTH / 2;
    const lighting =
      visualStyleRef.current === 'cinematic' ? CINEMATIC_LIGHTING : VOLUME_LIGHTING;

    const light1 = vtkLight.newInstance();
    light1.setPosition(
      fc + lighting.key.offset[0],
      fc + lighting.key.offset[1],
      fc + lighting.key.offset[2],
    );
    light1.setFocalPoint(fc, fc, fc);
    light1.setColor(...lighting.key.color);
    light1.setIntensity(lighting.key.intensity);
    renderer.addLight(light1);

    const light2 = vtkLight.newInstance();
    light2.setPosition(
      fc + lighting.fill.offset[0],
      fc + lighting.fill.offset[1],
      fc + lighting.fill.offset[2],
    );
    light2.setFocalPoint(fc, fc, fc);
    light2.setColor(...lighting.fill.color);
    light2.setIntensity(lighting.fill.intensity);
    renderer.addLight(light2);

    if (visualStyleRef.current === 'cinematic' && 'rim' in lighting) {
      const rim = lighting.rim;
      const light3 = vtkLight.newInstance();
      light3.setPosition(
        fc + rim.offset[0],
        fc + rim.offset[1],
        fc + rim.offset[2],
      );
      light3.setFocalPoint(fc, fc, fc);
      light3.setColor(...rim.color);
      light3.setIntensity(rim.intensity);
      renderer.addLight(light3);
    }

    const imageData = vtkImageData.newInstance();
    imageData.setDimensions(GRID_SIZE, GRID_SIZE, GRID_SIZE);
    imageData.setSpacing(SPACING, SPACING, SPACING);
    imageData.setOrigin(0, 0, 0);

    const dataArray = vtkDataArray.newInstance({
      name: 'density',
      numberOfComponents: 1,
      values: new Float32Array(VOXEL_COUNT),
    });
    imageData.getPointData().setScalars(dataArray);

    const mapper = vtkVolumeMapper.newInstance();
    mapper.setInputData(imageData);
    mapper.setAutoAdjustSampleDistances(false);

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
    baselineDistanceRef.current = getCameraDistance(renderer.getActiveCamera());
    homeCameraRef.current = captureCameraState(renderer.getActiveCamera());

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
    scheduleUploadRef.current?.();
    renderWindow.render();

    const resize = debounce(() => {
      frameCamera();
    }, 120);
    const ro = new ResizeObserver(() => resize());
    ro.observe(container);

    return () => {
      resize.cancel();
      ro.disconnect();
      if (renderRafRef.current) {
        cancelAnimationFrame(renderRafRef.current);
        renderRafRef.current = 0;
      }
      uploadGenRef.current += 1;
      cancelFly();
      if (orientationWidget) {
        orientationWidget.setEnabled(false);
        orientationWidget.delete();
      }
      if (axesActor) axesActor.delete();
      renderWindow.getInteractor().unbindEvents();
      volume.delete();
      mapper.delete();
      otf.delete();
      ctf.delete();
      dataArray.delete();
      imageData.delete();
      fullScreenRenderer.delete();
      container.replaceChildren();
      contextRef.current = null;
      loadedScalarsRef.current = null;
    };
  }, [showOrientation]);

  useEffect(() => {
    if (!data) {
      scheduleUploadRef.current = null;
      return;
    }

    let cancelled = false;
    const gen = ++uploadGenRef.current;

    const commitRender = (sync = false) => {
      if (cancelled || gen !== uploadGenRef.current || !contextRef.current) return;
      if (renderActiveRef.current) requestRender();
      if (sync) markPresentationReady(timestep);
      onRenderedRef.current?.();
    };

    const upload = (scalars: Float32Array, sync = false) => {
      if (cancelled || gen !== uploadGenRef.current) return;
      if (!contextRef.current) return;
      if (scalars.length !== VOXEL_COUNT) return;
      const prev = loadedScalarsRef.current;
      if (prev?.timestep === timestep && prev.scalars === scalars) {
        commitRender(sync);
        return;
      }
      loadedScalarsRef.current = { timestep, scalars };
      contextRef.current.dataArray.setData(scalars, 1);
      contextRef.current.imageData.modified();
      contextRef.current.mapper.modified();
      if (sync) {
        commitRender(true);
      } else {
        requestAnimationFrame(() => commitRender(false));
      }
    };

    const runUpload = () => {
      if (cancelled || gen !== uploadGenRef.current || !contextRef.current) return;

      const cached = getCachedVtkScalars(timestep, data);
      if (cached) {
        upload(cached, true);
        return;
      }

      void getVtkScalarsAsync(timestep, data).then((scalars) => {
        if (cancelled || gen !== uploadGenRef.current) return;
        upload(scalars, true);
      });
    };

    scheduleUploadRef.current = runUpload;
    runUpload();

    return () => {
      cancelled = true;
      if (scheduleUploadRef.current === runUpload) {
        scheduleUploadRef.current = null;
      }
    };
  }, [data, timestep]);

  useEffect(() => {
    const ctx = contextRef.current;
    if (!ctx) return;

    const preset = VOLUME_QUALITY_PRESETS[quality];
    applyTargetSampling();
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
      visualStyle,
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
    visualStyle,
    tfParams?.opacityScale,
    tfParams?.densityGain,
    tfParams?.highlightBoost,
  ]);

  useEffect(() => {
    if (!renderActive || !contextRef.current || !loadedScalarsRef.current) return;
    requestRender();
  }, [renderActive]);

  useEffect(() => {
    resetCameraForTimestep();
  }, [cameraZoom, timestep]);

  useEffect(() => {
    const ctx = contextRef.current;
    const container = containerRef.current;
    if (!ctx || !container) return;

    const interactor = ctx.fullScreenRenderer.getRenderWindow().getInteractor();
    const needsInteraction = interactiveCamera || focusOnClick;

    if (needsInteraction) {
      interactor.bindEvents(container);
      interactor.enable();
      if (performanceMode === 'video') {
        interactor.setDesiredUpdateRate(20);
        interactor.setStillUpdateRate(8);
      } else {
        interactor.setDesiredUpdateRate(30);
        interactor.setStillUpdateRate(12);
      }
    } else {
      interactor.unbindEvents();
    }

    if (!needsInteraction) return;

    let pressX = 0;
    let pressY = 0;
    let pressTime = 0;

    const onStart = () => {
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      interactionActiveRef.current = true;
      notifyCameraActivity();
      applyInteractionSampling();
    };

    const onEnd = () => {
      interactionActiveRef.current = false;
      notifyCameraActivity();
      const debounceMs = performanceMode === 'video' ? 150 : 0;
      const apply = () => {
        interactionEndTimerRef.current = null;
        applyTargetSampling();
        requestRender();
      };
      if (debounceMs > 0) {
        interactionEndTimerRef.current = setTimeout(apply, debounceMs);
      } else {
        apply();
      }
    };

    const subStart = interactiveCamera ? interactor.onStartInteraction(onStart) : null;
    const subEnd = interactiveCamera ? interactor.onEndInteraction(onEnd) : null;

    const subPress = focusOnClick
      ? interactor.onLeftButtonPress((callData: { position: { x: number; y: number } }) => {
          pressX = callData.position.x;
          pressY = callData.position.y;
          pressTime = performance.now();
        })
      : null;

    const subRelease = focusOnClick
      ? interactor.onLeftButtonRelease((callData: { position: { x: number; y: number } }) => {
          if (flyActiveRef.current) return;
          const dx = callData.position.x - pressX;
          const dy = callData.position.y - pressY;
          const dt = performance.now() - pressTime;
          if (dx * dx + dy * dy < 36 && dt < 300) {
            handleFocusPick(callData.position.x, callData.position.y);
          }
        })
      : null;

    const onDblClick = (e: MouseEvent) => {
      e.preventDefault();
      resetHomeCamera(true);
    };
    container.addEventListener('dblclick', onDblClick);

    return () => {
      subStart?.unsubscribe();
      subEnd?.unsubscribe();
      subPress?.unsubscribe();
      subRelease?.unsubscribe();
      container.removeEventListener('dblclick', onDblClick);
      if (interactionEndTimerRef.current) {
        clearTimeout(interactionEndTimerRef.current);
        interactionEndTimerRef.current = null;
      }
      interactionActiveRef.current = false;
      interactor.unbindEvents();
    };
  }, [interactiveCamera, focusOnClick, performanceMode, showOrientation]);

  useEffect(() => {
    const onVisibility = () => {
      if (!document.hidden && renderActiveRef.current) requestRender();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  return (
    <div
      ref={containerRef}
      className={[
        className,
        interactiveCamera || focusOnClick ? 'vd-vtk-interactive' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      data-vtk-volume
    />
  );
}
