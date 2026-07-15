import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const root = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig({
  root,
  base: '/static/dist/',
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
})
