/// <reference types="vitest" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost',
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: true,
    setupFiles: ['./src/test/setup.ts'],
    pool: 'forks',
    // Bound file-level concurrency to prevent jsdom worker memory pressure from
    // starving async tests while preserving parallel execution and normal timeouts.
    maxWorkers: 4,
    // Browser acceptance specs live in e2e/ and run under Playwright, not
    // Vitest; keep Vitest scoped to src so *.spec.ts files are not double-run.
    include: ['src/**/*.{test,spec}.?(c|m)[jt]s?(x)'],
  },
})
