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

export default defineConfig({
  plugins: [react(), nyxDataPlugin()],
  build: {
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        app: path.resolve(__dirname, 'app.html'),
        capture: path.resolve(__dirname, 'capture.html'),
      },
      output: {
        manualChunks: {
          vtk: ['@kitware/vtk.js'],
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
