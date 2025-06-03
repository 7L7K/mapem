// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@features': path.resolve(__dirname, 'frontend/src/features'),
      '@shared' : path.resolve(__dirname, 'frontend/src/shared'),
      '@app'    : path.resolve(__dirname, 'frontend/src/app'),
      '@lib'    : path.resolve(__dirname, 'frontend/src/lib'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5050',
        changeOrigin: true,
      },
    },
  },
})
