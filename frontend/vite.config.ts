import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5173,
    // Allow access through a Cloudflare quick tunnel (hostname changes on every start,
    // so the whole trycloudflare.com domain is allowed rather than one fixed name).
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      // Proxy API calls to the local FastAPI backend so there is no CORS setup needed in dev.
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
