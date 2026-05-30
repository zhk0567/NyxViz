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

export default defineConfig({
  root: path.resolve(__dirname, 'pages'),
  publicDir: path.resolve(__dirname, 'public'),
  plugins: [react(), nyxDataPlugin(), resolveProjectSrcPlugin()],
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'pages/index.html'),
        app: path.resolve(__dirname, 'pages/app.html'),
        capture: path.resolve(__dirname, 'pages/capture.html'),
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
