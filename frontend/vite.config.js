// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { VitePWA } from 'vite-plugin-pwa';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'robots.txt'],
      manifest: {
        name: 'MapEm',
        short_name: 'MapEm',
        theme_color: '#0f0f0f',
        background_color: '#0f0f0f',
        display: 'standalone',
        icons: [
          { src: '/vite.svg', sizes: '192x192', type: 'image/svg+xml' },
        ],
      },
    }),
    mode === 'analyze' && visualizer({ open: true, gzipSize: true, brotliSize: true })
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@features': path.resolve(__dirname, './src/features'),
      '@shared': path.resolve(__dirname, './src/shared'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@app': path.resolve(__dirname, './src/app'),
      '@components': path.resolve(__dirname, './src/shared/components'),
      '@hooks': path.resolve(__dirname, './src/shared/hooks'),
      '@context': path.resolve(__dirname, './src/shared/context'),
      '@utils': path.resolve(__dirname, './src/shared/utils'),
      '@styles': path.resolve(__dirname, './src/shared/styles'),
      '@api': path.resolve(__dirname, './src/lib/api'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5050',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    rollupOptions: {
      external: ['whatwg-fetch'], // 👈 Fix for Netlify build
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [],
  }
}));
