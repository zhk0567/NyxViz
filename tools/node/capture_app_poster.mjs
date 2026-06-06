/**
 * Section-wise Playwright capture of /app.html for doc poster figures.
 * Avoids fullPage stitching bugs with fixed UI (control-dock / poster-rail).
 * Usage: npm run build && node tools/node/capture_app_poster.mjs
 */
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const OUT_DIR = path.join(ROOT, 'docs', 'figures');
const PORT = Number(process.env.CAPTURE_PORT || 5174);
const BASE = `http://127.0.0.1:${PORT}`;
const VIEW_W = Number(process.env.CAPTURE_WIDTH || 1440);
const CAPTURE_SCALE = Number(process.env.CAPTURE_SCALE || 2);
const SETTLE_MS = Number(process.env.CAPTURE_SETTLE_MS || 4000);
const SECTION_COUNT = 6;

const POSTER_FILES = ['task6_story_poster.png', 'app_infographic_poster.png'];

async function serverUp(url) {
  try {
    const res = await fetch(url);
    return res.ok;
  } catch {
    return false;
  }
}

function waitForServer(url, timeoutMs = 120000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const res = await fetch(url);
        if (res.ok) return resolve();
      } catch {
        /* retry */
      }
      if (Date.now() - start > timeoutMs) {
        reject(new Error(`Server not ready: ${url}`));
        return;
      }
      setTimeout(tick, 500);
    };
    tick();
  });
}

function startPreview() {
  const isWin = process.platform === 'win32';
  return spawn(
    isWin ? 'npx.cmd' : 'npx',
    ['vite', 'preview', '--port', String(PORT), '--strictPort', '--host', '127.0.0.1'],
    { cwd: ROOT, stdio: 'pipe', shell: isWin },
  );
}

async function buildApp() {
  const isWin = process.platform === 'win32';
  await new Promise((resolve, reject) => {
    const child = spawn(isWin ? 'npm.cmd' : 'npm', ['run', 'build'], {
      cwd: ROOT,
      stdio: 'inherit',
      shell: isWin,
    });
    child.on('exit', (code) =>
      code === 0 ? resolve() : reject(new Error(`build failed: ${code}`)),
    );
  });
}

async function stitchSections(partPaths) {
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
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  let server = null;
  let exitCode = 0;

  try {
    console.log('Building app…');
    await buildApp();
    if (await serverUp(`${BASE}/app.html`)) {
      console.log(`Restarting preview on ${BASE}…`);
    } else {
      console.log(`Starting preview on ${BASE}…`);
    }
    server = startPreview();
    await waitForServer(`${BASE}/app.html`);

    const browser = await chromium.launch({
      headless: true,
      args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
    });
    const context = await browser.newContext({
      viewport: { width: VIEW_W, height: 900 },
      deviceScaleFactor: CAPTURE_SCALE,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);

    const url = `${BASE}/app.html?posterCapture=1`;
    console.log(`Capturing ${url} (section-wise)…`);
    await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });

    await page.waitForSelector('.cosmic-poster.poster-capture-mode', { timeout: 120000 });
    await page.waitForFunction(
      () => !document.querySelector('.app-loading'),
      { timeout: 120000 },
    );
    await page.waitForFunction(
      () => document.querySelectorAll('.loading-overlay').length === 0,
      { timeout: 120000 },
    );
    await page.waitForSelector('.pl-section', { timeout: 60000 });
    await page.waitForSelector('.pl-hero-vtk canvas, .pl-hero-img', { timeout: 120000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(SETTLE_MS);

    const partPaths = [];
    const headerPath = path.join(OUT_DIR, '_app_sec_header.png');
    await page.locator('.poster-top-bar').screenshot({ path: headerPath, type: 'png' });
    partPaths.push(headerPath);
    console.log(`Section header → ${headerPath}`);

    const sections = page.locator('.pl-section');
    const count = await sections.count();
    if (count !== SECTION_COUNT) {
      throw new Error(`Expected ${SECTION_COUNT} .pl-section, got ${count}`);
    }

    for (let i = 0; i < count; i += 1) {
      const loc = sections.nth(i);
      await loc.scrollIntoViewIfNeeded();
      await page.waitForTimeout(400);
      const secPath = path.join(OUT_DIR, `_app_sec_${String(i + 1).padStart(2, '0')}.png`);
      await loc.screenshot({ path: secPath, type: 'png' });
      partPaths.push(secPath);
      const id = await loc.getAttribute('id');
      console.log(`Section ${id ?? i + 1} → ${secPath}`);
    }

    await browser.close();
    await stitchSections(partPaths);

    const resized = path.join(OUT_DIR, '_app_poster_capture_resized.png');
    const { copyFile } = await import('node:fs/promises');
    for (const name of POSTER_FILES) {
      const dest = path.join(OUT_DIR, name);
      await copyFile(resized, dest);
      console.log(`Wrote ${dest}`);
    }
  } catch (e) {
    console.error(e);
    exitCode = 1;
  } finally {
    if (server) server.kill('SIGTERM');
    process.exit(exitCode);
  }
}

main();
