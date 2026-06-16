import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nyxDataDir = path.resolve(__dirname, 'Nyx');

function attachStaticDir(
  middlewares: { use: (path: string, handler: (...args: unknown[]) => void) => void },
  urlPrefix: string,
  dir: string,
  contentType?: string,
) {
  const base = path.resolve(dir);
  middlewares.use(urlPrefix, (req, res, next) => {
    const rel = ((req as { url?: string }).url ?? '/').replace(/^\//, '');
    const filePath = path.join(base, rel);
    if (!filePath.startsWith(base) || !fs.existsSync(filePath)) {
      (next as () => void)();
      return;
    }
    if (contentType) {
      (res as { setHeader: (k: string, v: string) => void }).setHeader(
        'Content-Type',
        contentType,
      );
    }
    fs.createReadStream(filePath).pipe(res as NodeJS.WritableStream);
  });
}

function attachNyxStatic(
  middlewares: { use: (path: string, handler: (...args: unknown[]) => void) => void },
) {
  attachStaticDir(middlewares, '/figures', path.join(__dirname, 'docs', 'figures'));
  attachStaticDir(
    middlewares,
    '/report',
    path.join(__dirname, 'docs', 'report'),
    'text/markdown; charset=utf-8',
  );
  middlewares.use('/Nyx', (req, res, next) => {
    const rel = ((req as { url?: string }).url ?? '/').replace(/^\//, '');
    const filePath = path.join(nyxDataDir, rel);
    if (!filePath.startsWith(nyxDataDir) || !fs.existsSync(filePath)) {
      (next as () => void)();
      return;
    }
    (res as { setHeader: (k: string, v: string) => void }).setHeader(
      'Content-Type',
      'application/octet-stream',
    );
    fs.createReadStream(filePath).pipe(res as NodeJS.WritableStream);
  });
}

function nyxDataPlugin(): Plugin {
  return {
    name: 'nyx-data-static',
    configureServer(server) {
      attachNyxStatic(server.middlewares);
    },
    configurePreviewServer(server) {
      attachNyxStatic(server.middlewares);
    },
  };
}

function resolveProjectSrcPlugin(): Plugin {
  const srcDir = path.resolve(__dirname, 'src');
  return {
    name: 'resolve-project-src',
    resolveId(source) {
      if (source.startsWith('/src/')) {
        return path.join(srcDir, source.slice('/src/'.length));
      }
      if (source.startsWith('../src/')) {
        return path.join(srcDir, source.slice('../src/'.length));
      }
      return null;
    },
  };
}

function readJsonBody(req: import('http').IncomingMessage): Promise<{ href?: string }> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'));
      } catch {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

function posterSaveApiPlugin(): Plugin {
  let saving = false;

  return {
    name: 'poster-save-api',
    configureServer(server) {
      server.middlewares.use('/__api/save-app-poster', (req, res, next) => {
        if (req.method !== 'POST') {
          (next as () => void)();
          return;
        }

        void (async () => {
          if (saving) {
            res.statusCode = 429;
            res.setHeader('Content-Type', 'application/json; charset=utf-8');
            res.end(JSON.stringify({ ok: false, error: '已有保存任务进行中' }));
            return;
          }

          saving = true;
          try {
            const body = await readJsonBody(req);
            const href = body.href ?? '';
            const origin = href ? new URL(href).origin : `http://127.0.0.1:${server.config.server.port ?? 5173}`;
            const script = path.resolve(__dirname, 'tools/node/snapshot_app_poster_once.mjs');
            const isWin = process.platform === 'win32';
            const { spawn } = await import('node:child_process');
            const stdout = await new Promise<string>((resolve, reject) => {
              const child = spawn(
                process.execPath,
                [script, origin],
                { cwd: __dirname, shell: isWin, stdio: ['ignore', 'pipe', 'pipe'] },
              );
              let out = '';
              let err = '';
              child.stdout?.on('data', (d) => {
                out += String(d);
              });
              child.stderr?.on('data', (d) => {
                err += String(d);
              });
              child.on('exit', (code) => {
                if (code === 0) resolve(out);
                else reject(new Error(err || `snapshot exit ${code}`));
              });
            });

            const payload = JSON.parse(stdout);
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json; charset=utf-8');
            res.end(JSON.stringify(payload));
          } catch (err) {
            res.statusCode = 500;
            res.setHeader('Content-Type', 'application/json; charset=utf-8');
            res.end(
              JSON.stringify({
                ok: false,
                error: err instanceof Error ? err.message : String(err),
              }),
            );
          } finally {
            saving = false;
          }
        })();
      });
    },
  };
}

export default defineConfig({
  root: path.resolve(__dirname, 'pages'),
  publicDir: path.resolve(__dirname, 'public'),
  plugins: [react(), nyxDataPlugin(), resolveProjectSrcPlugin(), posterSaveApiPlugin()],
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'pages/index.html'),
        app: path.resolve(__dirname, 'pages/app.html'),
        video: path.resolve(__dirname, 'pages/video.html'),
        capture: path.resolve(__dirname, 'pages/capture.html'),
      },
      output: {
        manualChunks(id) {
          if (id.includes('@kitware/vtk.js')) return 'vtk';
          if (
            id.includes('/src/dashboard/Video') ||
            id.includes('/src/volume/VolumeScene') ||
            id.includes('/src/video-main')
          ) {
            return 'video';
          }
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    fs: {
      allow: [__dirname],
    },
  },
  optimizeDeps: {
    include: ['globalthis', '@kitware/vtk.js'],
  },
});
