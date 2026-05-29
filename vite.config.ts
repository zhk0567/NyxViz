import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nyxDataDir = path.resolve(__dirname, 'Nyx');

function attachNyxStatic(
  middlewares: { use: (path: string, handler: (...args: unknown[]) => void) => void },
) {
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
        capture: path.resolve(__dirname, 'capture.html'),
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
