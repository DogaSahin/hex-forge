import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const root = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig(({ command }) => ({
  root,
  // The dev server is its own origin (localhost:5173) and serves from root, which
  // is what vite_assets._dev_tags() points at. The production build is served by
  // uvicorn under /static/dist/, so the built assets carry that base.
  base: command === 'serve' ? '/' : '/static/dist/',
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    cors: true,
    origin: 'http://localhost:5173',
  },
  build: {
    manifest: true,
    outDir: 'app/core/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: { main: resolve(root, 'app/core/frontend/main.ts') },
    },
  },
}))
