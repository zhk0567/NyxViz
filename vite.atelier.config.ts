/**
 * Atelier static deploy build — video.html only, base=/static/nyxviz/
 *
 * Usage:
 *   $env:VITE_NYX_DATA_BASE = "https://data.zhkun.xyz/nyx/"
 *   npm run build:atelier
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function resolveProjectSrcPlugin() {
  const srcDir = path.resolve(__dirname, 'src');
  return {
    name: 'resolve-project-src',
    resolveId(source: string) {
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
  base: '/static/nyxviz/',
  plugins: [react(), resolveProjectSrcPlugin()],
  build: {
    outDir: path.resolve(__dirname, 'dist-atelier'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        video: path.resolve(__dirname, 'pages/video.html'),
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
  optimizeDeps: {
    include: ['globalthis', '@kitware/vtk.js'],
  },
});
