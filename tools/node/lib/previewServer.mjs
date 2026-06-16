/**
 * Shared vite preview helpers for Playwright capture scripts.
 */
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(__dirname, '..', '..', '..');

export async function serverUp(url) {
  try {
    const res = await fetch(url);
    return res.ok;
  } catch {
    return false;
  }
}

export function waitForServer(url, timeoutMs = 120000) {
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

export function startPreview(port = 5174) {
  const isWin = process.platform === 'win32';
  return spawn(
    isWin ? 'npx.cmd' : 'npx',
    ['vite', 'preview', '--port', String(port), '--strictPort', '--host', '127.0.0.1'],
    { cwd: ROOT, stdio: 'pipe', shell: isWin },
  );
}

export async function buildApp() {
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

export function runPython(scriptRelative, args = []) {
  const isWin = process.platform === 'win32';
  const script = path.join(ROOT, scriptRelative);
  return new Promise((resolve, reject) => {
    const child = spawn(isWin ? 'python' : 'python3', [script, ...args], {
      cwd: ROOT,
      stdio: 'inherit',
      shell: isWin,
    });
    child.on('exit', (code) =>
      code === 0 ? resolve() : reject(new Error(`${scriptRelative} failed: ${code}`)),
    );
  });
}
