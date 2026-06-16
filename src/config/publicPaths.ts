/** Public asset URL helpers (Vite BASE_URL + optional external Nyx data CDN). */

function trimSlashes(s: string): string {
  return s.replace(/\/+$/, '');
}

function ensureTrailingSlash(s: string): string {
  return s.endsWith('/') ? s : `${s}/`;
}

export const APP_BASE = import.meta.env.BASE_URL;

declare global {
  interface Window {
    __NYX_DATA_BASE__?: string;
    /** When true, skip .dat volume fetch and show pre-rendered PNG in the center pane. */
    __NYX_STATIC_ONLY__?: boolean;
  }
}

function resolveNyxDataBase(): string {
  if (typeof window !== 'undefined') {
    const runtime = window.__NYX_DATA_BASE__?.trim();
    if (runtime) {
      return ensureTrailingSlash(runtime);
    }
  }
  const nyxDataBaseRaw = import.meta.env.VITE_NYX_DATA_BASE as string | undefined;
  return ensureTrailingSlash(nyxDataBaseRaw?.trim() || `${APP_BASE}Nyx/`);
}

export let NYX_DATA_BASE = resolveNyxDataBase();

export function isStaticFiguresOnly(): boolean {
  if (typeof window !== 'undefined' && window.__NYX_STATIC_ONLY__) {
    return true;
  }
  return false;
}

export function figuresUrl(name: string): string {
  const path = name.replace(/^\/+/, '').replace(/^figures\//, '');
  return `${APP_BASE}figures/${path}`;
}

export function statsUrl(name: string): string {
  const path = name.replace(/^\/+/, '').replace(/^stats\//, '');
  return `${APP_BASE}stats/${path}`;
}

export function nyxTimestepUrl(timestep: number, maxStep = 99): string {
  const step = Math.max(0, Math.min(maxStep, timestep));
  const file = `${String(step).padStart(4, '0')}.dat`;
  return `${ensureTrailingSlash(trimSlashes(NYX_DATA_BASE))}${file}`;
}

/** Pre-rendered volume PNG for static-only deploy (no .dat). */
export function volumeFigureUrl(timestep: number, maxStep = 99): string {
  const step = Math.max(0, Math.min(maxStep, timestep));
  const pad = String(step).padStart(4, '0');
  return figuresUrl(`task1_vol_t${pad}.png`);
}
