import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { scanBrushRangeAsync } from '@/data/brushScan';
import { estimateBrushCountFromHistogram } from '@/data/brushEstimate';
import { matchBrushPreset, type BrushPresetId } from '@/data/brushPreset';
import { useAppStore } from '@/store/useAppStore';
import type { TimelineData } from '@/data/types';
import { TIMESTEP_COUNT, VOXEL_COUNT, type DensityStats } from '@/data/types';
import { getGlobalTfDomain } from '@/volume/transferFunction';
import type { VolumeQuality } from '@/volume/VolumeScene';
import { isVtkScalarsCached } from '@/data/nyxLoader';
import { isStaticFiguresOnly } from '@/config/publicPaths';
import { isTimestepVolumeReady } from '@/data/timelineVolumePreload';
import { isPresentationReady, markPresentationReady } from '@/volume/volumeQualityCache';
import { usePrefetchTimestep } from '@/hooks/usePrefetchTimestep';

function canSkipDraftQuality(timestep: number, videoMode: boolean): boolean {
  if (isPresentationReady(timestep)) return true;
  if (videoMode) return false;
  return isVtkScalarsCached(timestep) || isTimestepVolumeReady(timestep);
}

export interface UseDashboardInteractionOptions {
  /** Poster 模式：点预设刷选时打开探索浮层 */
  onPresetBrush?: () => void;
  /** 录屏页默认开启高清体渲染 */
  defaultHighQuality?: boolean;
  /** 先 high 快速出图，首帧后再切 presentation */
  progressiveQuality?: boolean;
  /** 保活模式下 scene 切换不重置 progressive 草稿阶段 */
  keepVolumeAlive?: boolean;
  /** 预载就绪后跳过草稿阶段（录屏页建议关闭） */
  instantVolume?: boolean;
  /** 录屏/预览页：画质上限 high，拖动时强制 interactive */
  videoMode?: boolean;
  /** 静止后升 presentation 的等待毫秒（录屏可设更短） */
  idleBoostDelayMs?: number;
}

function exactPresetBrushCount(stats: DensityStats, preset: BrushPresetId): number | null {
  if (preset === 'top') return Math.round(stats.tailMassAboveP99 * VOXEL_COUNT);
  if (preset === 'bottom') return Math.round(stats.tailMassBelowP01 * VOXEL_COUNT);
  if (preset === 'filament' && stats.tailMassFilament90_99 != null) {
    return Math.round(stats.tailMassFilament90_99 * VOXEL_COUNT);
  }
  return null;
}

export function useDashboardInteraction(
  timeline: TimelineData,
  densityData: Float32Array | null,
  loading: boolean,
  options: UseDashboardInteractionOptions = {},
) {
  const { onPresetBrush, defaultHighQuality = false, progressiveQuality = false, keepVolumeAlive = false, instantVolume = false, videoMode = false, idleBoostDelayMs = 1800 } =
    options;

  const useProgressive = progressiveQuality && !videoMode;

  const [sliderStep, setSliderStep] = useState(0);
  const [sliderDragging, setSliderDragging] = useState(false);
  const [highQuality, setHighQuality] = useState(defaultHighQuality);
  const [volumeReady, setVolumeReady] = useState(false);
  const [qualityPhase, setQualityPhase] = useState<'draft' | 'final'>(
    useProgressive ? 'draft' : 'final',
  );
  const [scanning, setScanning] = useState(false);
  const [idleBoost, setIdleBoost] = useState(false);
  const [activityTick, setActivityTick] = useState(0);

  const resetIdleBoost = useCallback(() => {
    setIdleBoost(false);
    setActivityTick((t) => t + 1);
  }, []);

  usePrefetchTimestep(sliderStep, sliderDragging);

  const timestep = useAppStore((s) => s.timestep);
  const brushRange = useAppStore((s) => s.brushRange);
  const brushedCount = useAppStore((s) => s.brushedCount);
  const tfParams = useAppStore((s) => s.tfParams);
  const setTimestep = useAppStore((s) => s.setTimestep);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const setBrushedCount = useAppStore((s) => s.setBrushedCount);
  const setTfParams = useAppStore((s) => s.setTfParams);

  useEffect(() => {
    if (isStaticFiguresOnly() && videoMode) {
      setVolumeReady(true);
      setQualityPhase('final');
    }
  }, [timestep, videoMode]);

  useEffect(() => {
    setSliderStep(timestep);
    const volumeReadyNow = instantVolume && isTimestepVolumeReady(timestep);
    if (!keepVolumeAlive && !volumeReadyNow && !videoMode) {
      setVolumeReady(false);
    }
    if (videoMode || !useProgressive) {
      setQualityPhase('final');
    } else if (instantVolume && isTimestepVolumeReady(timestep)) {
      setQualityPhase('final');
    } else {
      setQualityPhase(canSkipDraftQuality(timestep, videoMode) ? 'final' : 'draft');
    }
    resetIdleBoost();
  }, [timestep, useProgressive, instantVolume, keepVolumeAlive, videoMode, resetIdleBoost]);

  useEffect(() => {
    resetIdleBoost();
  }, [loading, scanning, sliderDragging, resetIdleBoost]);

  useEffect(() => {
    if (!volumeReady || loading || scanning || sliderDragging) {
      setIdleBoost(false);
      return;
    }
    const handle = window.setTimeout(() => setIdleBoost(true), idleBoostDelayMs);
    return () => window.clearTimeout(handle);
  }, [volumeReady, loading, scanning, sliderDragging, activityTick, idleBoostDelayMs]);

  const stats = timeline.timesteps[sliderDragging ? sliderStep : timestep];
  const tfDomain = getGlobalTfDomain(timeline);
  const dataMin = tfDomain?.min ?? stats?.min ?? 7.5;
  const dataMax = tfDomain?.max ?? stats?.max ?? 15;
  const baseQuality: VolumeQuality = highQuality ? 'presentation' : 'cinematic';
  const settledQuality: VolumeQuality = idleBoost ? 'presentation' : baseQuality;

  const volumeQuality: VolumeQuality =
    (loading && !densityData) || scanning || sliderDragging
      ? 'video'
      : instantVolume && isTimestepVolumeReady(timestep)
        ? settledQuality
        : useProgressive && qualityPhase === 'draft'
          ? 'interactive'
          : settledQuality;

  const onVolumeCameraActivity = resetIdleBoost;

  const onVolumeRendered = useCallback(() => {
    setVolumeReady(true);
    if (useProgressive && qualityPhase === 'draft') {
      const bump = () => setQualityPhase('final');
      if (typeof requestIdleCallback !== 'undefined') {
        requestIdleCallback(bump, { timeout: videoMode ? 800 : 120 });
      } else {
        window.setTimeout(bump, videoMode ? 200 : 32);
      }
    } else {
      markPresentationReady(timestep);
    }
  }, [useProgressive, qualityPhase, timestep, videoMode]);

  const prevBrushRef = useRef<{ min: number; max: number } | null>(null);

  const applyTop1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p99, max: stats.max });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);

  const applyBottom1 = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.min, max: stats.p01 });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);

  const applyFilament = useCallback(() => {
    if (!stats) return;
    setBrushRange({ min: stats.p90, max: stats.p99 });
    onPresetBrush?.();
  }, [stats, setBrushRange, onPresetBrush]);

  const clearBrush = useCallback(() => {
    setBrushRange(null);
  }, [setBrushRange]);

  useEffect(() => {
    if (!brushRange) {
      setBrushedCount(0);
      setScanning(false);
      prevBrushRef.current = null;
      return;
    }

    if (!densityData) {
      if (isStaticFiguresOnly()) {
        const preset = matchBrushPreset(stats, brushRange);
        const exactCount = preset ? exactPresetBrushCount(stats, preset) : null;
        setBrushedCount(
          exactCount ?? estimateBrushCountFromHistogram(timeline, timestep, brushRange),
        );
        setScanning(false);
        prevBrushRef.current = { min: brushRange.min, max: brushRange.max };
        return;
      }
      setBrushedCount(0);
      setScanning(false);
      prevBrushRef.current = null;
      return;
    }

    const preset = matchBrushPreset(stats, brushRange);
    const exactCount = preset ? exactPresetBrushCount(stats, preset) : null;
    if (exactCount != null) {
      setBrushedCount(exactCount);
      setScanning(false);
      prevBrushRef.current = { min: brushRange.min, max: brushRange.max };
      return;
    }

    const sameBrush =
      prevBrushRef.current?.min === brushRange.min &&
      prevBrushRef.current?.max === brushRange.max;
    prevBrushRef.current = brushRange;

    let cancelled = false;
    setScanning(true);
    const delay = sameBrush ? 450 : 180;

    const handle = window.setTimeout(() => {
      scanBrushRangeAsync(densityData, brushRange.min, brushRange.max, 8000)
        .then((found) => {
          if (!cancelled) {
            setBrushedCount(found.length);
            setScanning(false);
          }
        })
        .catch(() => {
          if (!cancelled) setScanning(false);
        });
    }, delay);

    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [densityData, brushRange, timestep, stats, setBrushedCount, timeline]);

  const highlight = useMemo(() => {
    if (!brushRange) return {};
    return { highlightMin: brushRange.min, highlightMax: brushRange.max };
  }, [brushRange]);

  const commitTimestep = () => {
    if (sliderStep !== timestep) setTimestep(sliderStep);
  };

  const selectTimestep = (t: number) => {
    setSliderStep(t);
    setTimestep(t);
  };

  const volumeRatio =
    brushRange && brushedCount > 0
      ? ((brushedCount / VOXEL_COUNT) * 100).toFixed(2)
      : null;

  const activePreset = useMemo(
    () => matchBrushPreset(stats, brushRange),
    [stats, brushRange],
  );

  return {
    timestep,
    sliderStep,
    sliderDragging,
    setSliderStep,
    setSliderDragging,
    highQuality,
    setHighQuality,
    volumeReady,
    setVolumeReady,
    onVolumeRendered,
    onVolumeCameraActivity,
    scanning,
    brushRange,
    brushedCount,
    tfParams,
    setTfParams,
    stats,
    dataMin,
    dataMax,
    volumeQuality,
    qualityPhase,
    highlight,
    applyTop1,
    applyBottom1,
    applyFilament,
    clearBrush,
    commitTimestep,
    selectTimestep,
    volumeRatio,
    activePreset,
    timestepCount: TIMESTEP_COUNT,
  };
}
