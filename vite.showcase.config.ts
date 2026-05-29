import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nyxDataDir = path.resolve(__dirname, 'Nyx');

function attachNyxStatic(
  middlewares: { use: (p: string, h: (...args: unknown[]) => void) => void },
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
  };
}

export default defineConfig({
  plugins: [react(), nyxDataPlugin()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  build: {
    outDir: 'dist-showcase',
    emptyOutDir: true,
    lib: {
      entry: path.resolve(__dirname, 'src/showcase/main.tsx'),
      name: 'NyxShowcase',
      formats: ['iife'],
      fileName: () => 'showcase.iife.js',
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        assetFileNames: 'showcase.[ext]',
      },
    },
    cssCodeSplit: false,
  },
  define: {
    'process.env.NODE_ENV': '"production"',
  },
});
