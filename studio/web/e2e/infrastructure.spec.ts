import { test, expect } from '@playwright/test'
import { mkdtemp, rm, readFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { launch, stop, redact, restrictNetwork, test as studioTest, strategy, edit, configure, run } from './fixtures'

test('failed readiness and cancellation preserve an independent host', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ob-harness-lifecycle-'))
  const logs: string[] = []
  const survivor = await launch(directory, [directory], logs)
  try {
    await expect(launch(directory, ['--invalid-option'], logs, 1000)).rejects.toThrow()
    await expect(launch(directory, [directory], logs, 1)).rejects.toThrow('deadline')
    const cancelled = await launch(directory, [directory], logs)
    await stop(cancelled.child)
    expect(cancelled.child.exitCode !== null || cancelled.child.signalCode !== null).toBe(true)
    expect((await fetch(new URL('/', survivor.url))).status).toBe(200)
    expect(logs.join('')).not.toContain(new URL(survivor.url).hash.slice(7))
    expect(redact('token=synthetic-secret\nCookie: test-cookie')).not.toMatch(/synthetic-secret|test-cookie/)
    expect(redact('{"authorization": "Bearer synthetic-bearer", "cookie": "synthetic-cookie"}')).not.toMatch(/synthetic-bearer|synthetic-cookie/)
  } finally { await stop(survivor.child); await rm(directory, { recursive: true, force: true }) }
})

test('browser loopback policy rejects external traffic before transport', async ({ context, page }) => {
  const rejected: string[] = []
  await restrictNetwork(context, rejected)
  await expect(page.goto('https://example.invalid/')).rejects.toThrow()
  expect(rejected).toEqual(['https://example.invalid'])
})


studioTest('cancelling a real host reclaims its running strategy worker', async ({ page, studio }) => {
  const marker = join(studio.directory, 'worker.pid')
  const source = strategy.replace('if self.bar_index == 0: self.buy(qty=self.quantity)',
    `if self.bar_index == 0:\n            import os, time\n            from pathlib import Path\n            Path(${JSON.stringify(marker)}).write_text(str(os.getpid()))\n            time.sleep(60)`)
  await edit(page, source)
  await configure(page)
  await run(page, 'running')
  let pid = 0
  await expect.poll(async () => { pid = Number(await readFile(marker, 'utf8').catch(() => '0')); return pid }).toBeGreaterThan(0)
  await studio.stop()
  await expect.poll(() => { try { process.kill(pid, 0); return true } catch { return false } }).toBe(false)
})
