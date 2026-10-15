import { defineConfig, mergeConfig } from 'vitest/config'
import vite from './vite.config.ts'
export default mergeConfig(vite, defineConfig({ test: { include: ['src/**/*.test.{ts,tsx}'] } }))
