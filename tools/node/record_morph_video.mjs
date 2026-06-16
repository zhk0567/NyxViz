/**
 * Record morph animation t=0..99 via capture.html?seq=1 (single page, no reload).
 * Usage: npm run record-morph-video
 *
 * Env:
 *   VIDEO_FPS, VIDEO_SETTLE_MS, CAPTURE_PORT, CAPTURE_WIDTH, CAPTURE_HEIGHT
 *   VIDEO_KEYFRAMES=0,25,50,75,99  — comma list; empty/unset → all T0..T1
 *   VIDEO_DWELL_S=2  — repeat each keyframe N seconds at FPS
 *   VIDEO_ENCODE_ONLY=1  — skip capture, encode existing frames only
 */
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

let ffmpegStatic;
try {
  ffmpegStatic = (await import('ffmpeg-static')).default;
} catch {
  ffmpegStatic = null;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const OUT_DIR = path.join(ROOT, 'docs', 'figures');
const FRAMES_DIR = path.join(OUT_DIR, '_morph_frames');
const OUT_VIDEO = path.join(OUT_DIR, 'morph_t0_99.mp4');
const OUT_GIF = path.join(OUT_DIR, 'morph_t0_99.gif');
const ENCODE_ONLY = process.env.VIDEO_ENCODE_ONLY === '1';

const PORT = Number(process.env.CAPTURE_PORT || 5174);
const BASE = `http://127.0.0.1:${PORT}`;
const VIEW_W = Number(process.env.CAPTURE_WIDTH || 1920);
const VIEW_H = Number(process.env.CAPTURE_HEIGHT || 1080);
const CAPTURE_SCALE = Number(process.env.CAPTURE_SCALE || 1);
const SETTLE_MS = Number(process.env.VIDEO_SETTLE_MS || 350);
const FPS = Number(process.env.VIDEO_FPS || 12);
const T0 = Number(process.env.VIDEO_T0 ?? 0);
const T1 = Number(process.env.VIDEO_T1 ?? 99);
const DWELL_S = Number(process.env.VIDEO_DWELL_S || 2);

function parseKeyframes() {
  const raw = process.env.VIDEO_KEYFRAMES;
  if (raw === '') {
    const steps = [];
    for (let t = T0; t <= T1; t++) steps.push(t);
    return steps;
  }
  const list =
    raw === undefined ? [0, 25, 50, 75, 99] : raw.split(',').map((s) => Number(s.trim()));
  return list.filter((n) => Number.isFinite(n) && n >= T0 && n <= T1);
}

const KEYFRAMES = parseKeyframes();
const FRAMES_PER_KEYFRAME = Math.max(1, Math.round(DWELL_S * FPS));

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

function resolveFfmpeg() {
  if (ffmpegStatic && typeof ffmpegStatic === 'string') return ffmpegStatic;
  const bundled = path.join(
    ROOT,
    'tools',
    'ffmpeg',
    'bin',
    process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg',
  );
  if (existsSync(bundled)) return bundled;
  return 'ffmpeg';
}

function runCmd(bin, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, args, { stdio: 'inherit', shell: false });
    child.on('error', (err) => reject(err));
    child.on('exit', (code) =>
      code === 0 ? resolve() : reject(new Error(`${bin} failed: ${code}`)),
    );
  });
}

async function runFfmpeg(framesPattern, outPath, fps) {
  const bin = resolveFfmpeg();
  await runCmd(bin, [
    '-y',
    '-framerate',
    String(fps),
    '-i',
    framesPattern,
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-movflags',
    '+faststart',
    outPath,
  ]);
}

async function runGifEncode(fps) {
  const isWin = process.platform === 'win32';
  await runCmd(isWin ? 'python' : 'python3', [
    path.join(ROOT, 'tools', 'python', 'encode_morph_gif.py'),
    String(fps),
  ]);
}

async function encodeOutput(fps) {
  try {
    console.log(`Encoding ${OUT_VIDEO} @ ${fps} fps (ffmpeg)…`);
    await runFfmpeg(path.join(FRAMES_DIR, 'frame_%04d.png'), OUT_VIDEO, fps);
    console.log(`Done: ${OUT_VIDEO}`);
    return;
  } catch {
    console.warn('ffmpeg unavailable — falling back to GIF (Pillow)…');
  }
  await runGifEncode(fps);
  console.log(`Done: ${OUT_GIF}`);
}

async function waitCaptureReady(page, t, timeoutMs = 120000) {
  await page.waitForFunction(
    (step) => {
      const rec = window.__CAPTURE_REC__;
      return rec?.ready === true && rec.timestep === step;
    },
    t,
    { timeout: timeoutMs },
  );
}

async function captureFrames() {
  let server = null;
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

    const gpuArgs =
      process.env.CAPTURE_USE_GPU === '1'
        ? ['--enable-webgl']
        : ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'];

    const browser = await chromium.launch({ headless: true, args: gpuArgs });
    const context = await browser.newContext({
      viewport: { width: VIEW_W, height: VIEW_H },
      deviceScaleFactor: CAPTURE_SCALE,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(180000);
    page.on('pageerror', (err) => console.error(`[pageerror] ${err.message}`));

    const url = `${BASE}/capture.html?seq=1&domain=morph&t=${KEYFRAMES[0] ?? T0}`;
    console.log(`Open ${url}`);
    console.log(
      `Keyframes: [${KEYFRAMES.join(', ')}] · dwell ${DWELL_S}s (${FRAMES_PER_KEYFRAME} frames each)`,
    );
    await page.goto(url, { waitUntil: 'networkidle', timeout: 180000 });

    let frameIdx = 0;
    const totalFrames = KEYFRAMES.length * FRAMES_PER_KEYFRAME;

    for (let k = 0; k < KEYFRAMES.length; k++) {
      const t = KEYFRAMES[k];
      if (k > 0) {
        await page.evaluate((step) => window.__CAPTURE_GO_TIMESTEP__?.(step), t);
      }
      await waitCaptureReady(page, t);
      if (SETTLE_MS > 0) await page.waitForTimeout(SETTLE_MS);

      for (let d = 0; d < FRAMES_PER_KEYFRAME; d++) {
        const framePath = path.join(FRAMES_DIR, `frame_${String(frameIdx).padStart(4, '0')}.png`);
        await page.screenshot({ path: framePath, type: 'png' });
        console.log(
          `Frame ${frameIdx + 1}/${totalFrames}  t=${t}  dwell ${d + 1}/${FRAMES_PER_KEYFRAME}  → ${framePath}`,
        );
        frameIdx++;
      }
    }

    await browser.close();
    return server;
  } catch (e) {
    if (server) server.kill('SIGTERM');
    throw e;
  }
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  let server = null;
  let exitCode = 0;

  try {
    if (!ENCODE_ONLY) {
      await rm(FRAMES_DIR, { recursive: true, force: true });
      await mkdir(FRAMES_DIR, { recursive: true });
      server = await captureFrames();
    } else {
      console.log(`Encode-only mode — using ${FRAMES_DIR}`);
    }
    await encodeOutput(FPS);
  } catch (e) {
    console.error(e);
    exitCode = 1;
  } finally {
    if (server) server.kill('SIGTERM');
    process.exit(exitCode);
  }
}

main();
