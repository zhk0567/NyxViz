/**
 * Playwright capture of /app.html for doc poster figures.
 * Default: compact representative layout — single screenshot → docs/figures.
 * Full 6-section scroll: CAPTURE_FULL=1 node tools/node/capture_app_poster.mjs
 * Dev live save (page already open): npm run save-poster
 */
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import {
  capturePageUrl,
  OUT_DIR,
  ROOT,
  snapshotAppPoster,
} from './lib/appPosterSnapshot.mjs';

const PORT = Number(process.env.CAPTURE_PORT || 5174);
const BASE = `http://127.0.0.1:${PORT}`;
const FULL_SCROLL = process.env.CAPTURE_FULL === '1';

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

    const pageUrl = capturePageUrl(BASE, { fullScroll: FULL_SCROLL });
    console.log(
      `Capturing ${pageUrl} (${FULL_SCROLL ? 'full 6-section scroll' : 'compact representative'})…`,
    );

    const result = await snapshotAppPoster({ pageUrl, fullScroll: FULL_SCROLL });
    console.log(`Wrote ${result.resized}`);
    for (const dest of result.copies) {
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
