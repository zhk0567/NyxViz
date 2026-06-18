/**
 * Playwright capture of video.html intro record layout for representative poster top half.
 */
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';
import { OUT_DIR } from './appPosterSnapshot.mjs';

export const VIDEO_VIEW_W = Number(process.env.CAPTURE_WIDTH || 1920);
export const VIDEO_VIEW_H = Number(process.env.CAPTURE_HEIGHT || 1400);
export const VIDEO_SCALE = Number(process.env.CAPTURE_SCALE || 2);
export const VIDEO_SETTLE_MS = Number(process.env.CAPTURE_SETTLE_MS || 5000);
export const VIDEO_INTRO_OUT = '_rep_video_intro.png';

export function videoPosterUrl(base, scene = 'intro') {
  const params = new URLSearchParams({
    record: '1',
    scene,
    posterCapture: '1',
    staticOnly: '1',
    t: '99',
  });
  return `${base.replace(/\/$/, '')}/video.html?${params}`;
}

export async function waitForVideoPosterReady(page, settleMs = VIDEO_SETTLE_MS) {
  await page.waitForSelector('.video-dashboard.video-record-mode.video-poster-capture-mode', {
    timeout: 120000,
  });
  await page.waitForFunction(() => !document.querySelector('.app-loading'), {
    timeout: 120000,
  });
  await page.waitForFunction(
    () => document.querySelectorAll('.loading-overlay').length === 0,
    { timeout: 120000 },
  );
  await page.waitForFunction(
    () => window.__VIDEO_POSTER_READY__ === true,
    { timeout: 120000 },
  );
  await page.waitForSelector('.vd-vtk-canvas-wrap canvas, .vd-vtk-static-figure', {
    timeout: 120000,
  });
  await page.waitForFunction(
    () => {
      const img = document.querySelector('.vd-vtk-static-figure');
      if (img instanceof HTMLImageElement) {
        return img.complete && img.naturalWidth > 0;
      }
      const canvas = document.querySelector('.vd-vtk-canvas-wrap canvas');
      return canvas instanceof HTMLCanvasElement && canvas.width > 0;
    },
    { timeout: 120000 },
  );
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(settleMs);
}

export async function getPosterContentClip(page) {
  return page.evaluate(() => {
    const nodes = [
      ...document.querySelectorAll('.vd-header'),
      ...document.querySelectorAll('.vd-body .vd-panel'),
      ...document.querySelectorAll('.vd-findings'),
    ];
    let x0 = Infinity;
    let y0 = Infinity;
    let x1 = -Infinity;
    let y1 = -Infinity;
    for (const el of nodes) {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      x0 = Math.min(x0, r.left);
      y0 = Math.min(y0, r.top);
      x1 = Math.max(x1, r.right);
      y1 = Math.max(y1, r.bottom);
    }
    if (!Number.isFinite(x0)) return null;
    return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  });
}

export async function captureVideoIntroPoster({
  pageUrl,
  outDir = OUT_DIR,
  outName = VIDEO_INTRO_OUT,
  viewW = VIDEO_VIEW_W,
  viewH = VIDEO_VIEW_H,
  scale = VIDEO_SCALE,
  settleMs = VIDEO_SETTLE_MS,
}) {
  const browser = await chromium.launch({
    headless: true,
    args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
  });

  try {
    await mkdir(outDir, { recursive: true });
    const context = await browser.newContext({
      viewport: { width: viewW, height: viewH },
      deviceScaleFactor: scale,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);

    await page.goto(pageUrl, { waitUntil: 'networkidle', timeout: 120000 });
    await waitForVideoPosterReady(page, settleMs);

    const outPath = path.join(outDir, outName);
    const clip = await getPosterContentClip(page);
    const dashboard = page.locator('#root .video-dashboard.video-record-mode');

    if (clip && clip.width > 0 && clip.height > 0) {
      await page.screenshot({
        path: outPath,
        type: 'png',
        clip,
      });
    } else {
      await dashboard.screenshot({ path: outPath, type: 'png' });
    }
    return outPath;
  } finally {
    await browser.close();
  }
}
