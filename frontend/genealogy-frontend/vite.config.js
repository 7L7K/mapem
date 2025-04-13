"/Users/kingal/mapem/frontend/genealogy-frontend/vite.config.js"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      leaflet: path.resolve(__dirname, 'node_modules/leaflet'),
    },
  },
  server: {
    fs: {
      allow: ['..', path.resolve(__dirname, 'node_modules/leaflet')]
    }
  }
})
