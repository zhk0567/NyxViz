import { create } from 'zustand';
import type { BrushRange } from '@/data/types';
import type { TfParams } from '@/volume/transferFunction';

interface AppState {
  timestep: number;
  densityData: Float32Array | null;
  loading: boolean;
  error: string | null;
  brushRange: BrushRange | null;
  brushedCount: number;
  tfParams: TfParams;
  setTimestep: (t: number) => void;
  setDensityData: (data: Float32Array | null) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setBrushRange: (range: BrushRange | null) => void;
  setBrushedCount: (n: number) => void;
  setTfParams: (params: TfParams) => void;
}

export const useAppStore = create<AppState>((set) => ({
  timestep: 0,
  densityData: null,
  loading: false,
  error: null,
  brushRange: null,
  brushedCount: 0,
  tfParams: { opacityScale: 1, densityGain: 0, highlightBoost: 1 },
  setTimestep: (timestep) => set({ timestep }),
  setDensityData: (densityData) => set({ densityData }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setBrushRange: (brushRange) => set({ brushRange }),
  setBrushedCount: (brushedCount) => set({ brushedCount }),
  setTfParams: (tfParams) => set({ tfParams }),
}));
