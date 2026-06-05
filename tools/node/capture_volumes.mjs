/**
 * Capture vtk.js volume renders via Playwright.
 * Usage: node tools/node/capture_volumes.mjs
 */
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const OUT_DIR = path.join(ROOT, 'docs', 'figures');
const STEPS = [0, 25, 50, 75, 99];
const PORT = Number(process.env.CAPTURE_PORT || 5174);
const BASE = `http://127.0.0.1:${PORT}`;
const VIEW_W = Number(process.env.CAPTURE_WIDTH || 1920);
const VIEW_H = Number(process.env.CAPTURE_HEIGHT || 1080);
const CAPTURE_SCALE = Number(process.env.CAPTURE_SCALE || 2);
const SETTLE_MS = Number(process.env.CAPTURE_SETTLE_MS || 2500);

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

function startDevServer() {
  const isWin = process.platform === 'win32';
  const child = spawn(
    isWin ? 'npx.cmd' : 'npx',
    ['vite', 'preview', '--port', String(PORT), '--strictPort', '--host', '127.0.0.1'],
    { cwd: ROOT, stdio: 'pipe', shell: isWin },
  );
  child.stderr?.on('data', (d) => process.stderr.write(d));
  child.stdout?.on('data', (d) => process.stdout.write(d));
  return child;
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

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  let server = null;
  let exitCode = 0;

  try {
    if (!(await serverUp(`${BASE}/`))) {
      console.log('Building app…');
      await buildApp();
      console.log(`Starting preview on port ${PORT}…`);
      server = startDevServer();
      await waitForServer(`${BASE}/`);
    } else {
      console.log(`Using existing server at ${BASE}`);
    }
    const gpuArgs = process.env.CAPTURE_USE_GPU === '1'
      ? ['--enable-webgl']
      : ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'];
    const browser = await chromium.launch({
      headless: true,
      args: gpuArgs,
    });
    const context = await browser.newContext({
      viewport: { width: VIEW_W, height: VIEW_H },
      deviceScaleFactor: CAPTURE_SCALE,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);
    page.on('console', (msg) => console.log(`[browser] ${msg.text()}`));
    page.on('pageerror', (err) => console.error(`[pageerror] ${err.message}`));

    for (const t of STEPS) {
      const url = `${BASE}/capture.html?t=${t}`;
      console.log(`Capturing ${url}`);
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
      await page.waitForFunction(
        () =>
          window.__CAPTURE_READY__ === true ||
          typeof window.__CAPTURE_ERROR__ === 'string',
        { timeout: 120000 },
      );
      const state = await page.evaluate(() => ({
        err: window.__CAPTURE_ERROR__,
        ready: window.__CAPTURE_READY__,
        status: document.getElementById('capture-status')?.textContent,
      }));
      if (state.err) {
        throw new Error(`Capture failed at t=${t}: ${state.err}`);
      }
      if (!state.ready) {
        throw new Error(
          `Capture not ready at t=${t}: ${state.status ?? 'unknown'}`,
        );
      }
      await page.waitForFunction(
        ({ w, h, scale }) => {
          const canvas = document.querySelector('[data-vtk-volume] canvas');
          return (
            canvas instanceof HTMLCanvasElement &&
            canvas.width >= w * scale * 0.85 &&
            canvas.height >= h * scale * 0.85
          );
        },
        { w: VIEW_W, h: VIEW_H, scale: CAPTURE_SCALE },
        { timeout: 60000 },
      );
      await page.waitForTimeout(SETTLE_MS);
      const outPath = path.join(OUT_DIR, `task1_vol_t${String(t).padStart(4, '0')}.png`);
      await page.screenshot({
        path: outPath,
        clip: { x: 0, y: 0, width: VIEW_W, height: VIEW_H },
        type: 'png',
      });
      console.log(`Wrote ${outPath} (${VIEW_W * CAPTURE_SCALE}×${VIEW_H * CAPTURE_SCALE}px effective)`);
    }

    await browser.close();
  } catch (e) {
    console.error(e);
    exitCode = 1;
  } finally {
    if (server) server.kill('SIGTERM');
    process.exit(exitCode);
  }
}

main();
