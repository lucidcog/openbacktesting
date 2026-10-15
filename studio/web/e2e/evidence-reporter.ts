import { redact } from './redact'
import type { Reporter, FullConfig } from '@playwright/test/reporter'
import { readdir, readFile, writeFile, rm } from 'node:fs/promises'
import { join } from 'node:path'

// Raw Playwright page snapshots are not a reviewed evidence format.
export default class EvidenceReporter implements Reporter {
  directories: string[] = []
  onBegin(config: FullConfig) { this.directories = config.projects.map(project => project.outputDir) }
  async onEnd() {
    async function clean(directory: string) {
      for (const entry of await readdir(directory, { withFileTypes: true }).catch(() => [])) {
        const path = join(directory, entry.name)
        if (entry.isDirectory()) await clean(path)
        else if (entry.name === 'error-context.md') await rm(path)
        else if (/\.(json|txt|log)$/.test(entry.name)) {
          const text = await readFile(path, 'utf8')
          const walk = (value: unknown): unknown => typeof value === 'string' ? redact(value) : Array.isArray(value) ? value.map(walk) : value && typeof value === 'object' ? Object.fromEntries(Object.entries(value).map(([key, item]) => [key, /^(?:token|csrf|cookie|authorization|password|secret)$/i.test(key) ? '[REDACTED]' : walk(item)])) : value
          const safe = entry.name.endsWith('.json') ? JSON.stringify(walk(JSON.parse(text)), null, 2) : redact(text)
          if (safe !== text) await writeFile(path, safe)
        }
      }
    }
    for (const directory of this.directories) await clean(directory)
  }
}
