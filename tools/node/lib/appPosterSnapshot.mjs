/**
 * Shared Playwright logic for /app.html representative poster capture.
 */
import { copyFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(__dirname, '..', '..', '..');
export const OUT_DIR = path.join(ROOT, 'docs', 'figures');

export const POSTER_FILES = ['task6_story_poster.png', 'app_infographic_poster.png'];
export const FINAL_NAME = '_app_poster_capture_resized.png';

export const DEFAULT_VIEW_W = Number(process.env.CAPTURE_WIDTH || 1280);
export const DEFAULT_SCALE = Number(process.env.CAPTURE_SCALE || 2);
export const DEFAULT_SETTLE_MS = Number(process.env.CAPTURE_SETTLE_MS || 4000);
export const SECTION_COUNT = 6;

export function capturePageUrl(base, { fullScroll = false } = {}) {
  const params = new URLSearchParams({ posterCapture: '1' });
  if (!fullScroll) params.set('representative', '1');
  return `${base.replace(/\/$/, '')}/app.html?${params}`;
}

export async function waitForPosterReady(page, settleMs = DEFAULT_SETTLE_MS) {
  await page.waitForSelector('.cosmic-poster.poster-capture-mode', { timeout: 120000 });
  await page.waitForFunction(() => !document.querySelector('.app-loading'), {
    timeout: 120000,
  });
  await page.waitForFunction(
    () => document.querySelectorAll('.loading-overlay').length === 0,
    { timeout: 120000 },
  );
  const isRepresentative = await page.evaluate(
    () => new URLSearchParams(window.location.search).has('representative'),
  );
  if (isRepresentative) {
    await page.waitForFunction(
      () => window.__POSTER_CAPTURE_READY__ === true,
      { timeout: 120000 },
    );
  }
  await page.waitForSelector('.pl-hero-vtk canvas, .pl-hero-img', { timeout: 120000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(settleMs);
}

export async function captureRepresentativeElement(page, outDir = OUT_DIR) {
  await page.waitForSelector('.poster-representative-capture', { timeout: 60000 });
  await mkdir(outDir, { recursive: true });
  const rawPath = path.join(outDir, '_app_poster_capture_raw.png');
  await page.locator('.poster-representative-capture').screenshot({ path: rawPath, type: 'png' });
  return rawPath;
}

export async function captureFullScrollSections(page, outDir = OUT_DIR) {
  await page.waitForSelector('.pl-section', { timeout: 60000 });
  await mkdir(outDir, { recursive: true });

  const partPaths = [];
  const headerPath = path.join(outDir, '_app_sec_header.png');
  await page.locator('.poster-top-bar').screenshot({ path: headerPath, type: 'png' });
  partPaths.push(headerPath);

  const sections = page.locator('.pl-section');
  const count = await sections.count();
  if (count !== SECTION_COUNT) {
    throw new Error(`Expected ${SECTION_COUNT} .pl-section, got ${count}`);
  }

  for (let i = 0; i < count; i += 1) {
    const loc = sections.nth(i);
    await loc.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    const secPath = path.join(outDir, `_app_sec_${String(i + 1).padStart(2, '0')}.png`);
    await loc.screenshot({ path: secPath, type: 'png' });
    partPaths.push(secPath);
  }

  return partPaths;
}

export async function stitchAndPublish(partPaths, outDir = OUT_DIR) {
  const { spawn } = await import('node:child_process');
  const isWin = process.platform === 'win32';
  const py = path.join(ROOT, 'tools', 'python', 'stitch_app_poster.py');
  await new Promise((resolve, reject) => {
    const child = spawn(isWin ? 'python' : 'python3', [py, ...partPaths], {
      cwd: ROOT,
      stdio: 'inherit',
      shell: isWin,
    });
    child.on('exit', (code) =>
      code === 0 ? resolve() : reject(new Error(`stitch failed: ${code}`)),
    );
  });

  const resized = path.join(outDir, FINAL_NAME);
  const copies = [];
  for (const name of POSTER_FILES) {
    const dest = path.join(outDir, name);
    await copyFile(resized, dest);
    copies.push(dest);
  }
  return { resized, copies };
}

export async function snapshotAppPoster({
  pageUrl,
  outDir = OUT_DIR,
  fullScroll = false,
  viewW = DEFAULT_VIEW_W,
  scale = DEFAULT_SCALE,
  settleMs = DEFAULT_SETTLE_MS,
}) {
  const browser = await chromium.launch({
    headless: true,
    args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: viewW, height: 900 },
      deviceScaleFactor: scale,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);

    await page.goto(pageUrl, { waitUntil: 'networkidle', timeout: 120000 });
    await waitForPosterReady(page, settleMs);

    const partPaths = fullScroll
      ? await captureFullScrollSections(page, outDir)
      : [await captureRepresentativeElement(page, outDir)];

    const { resized, copies } = await stitchAndPublish(partPaths, outDir);
    return { resized, copies, partPaths };
  } finally {
    await browser.close();
  }
}
