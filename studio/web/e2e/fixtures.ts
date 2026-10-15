import { redact } from './redact'
export { redact } from './redact'
import { test as base, expect, type Page, type BrowserContext } from '@playwright/test'
import { spawn, type ChildProcess } from 'node:child_process'
import { mkdtemp, mkdir, readFile, writeFile, rm, readdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..')
export const strategy = `from openbacktesting import Strategy, backtest, inputs

@backtest()
class Fixture(Strategy):
    quantity = inputs.int(1, title="Quantity")
    def init(self): pass
    def next(self):
        if self.bar_index == 0: self.buy(qty=self.quantity)
        if self.bar_index == 3: self.position.close()
`
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
export async function stop(child: ChildProcess) {
  if (child.exitCode !== null || child.signalCode !== null) return
  child.kill('SIGTERM')
  for (let i = 0; i < 100 && child.exitCode === null && child.signalCode === null; i++) await delay(50)
  if (child.exitCode === null && child.signalCode === null && child.pid) {
    try { process.kill(-child.pid, 'SIGKILL') } catch { /* Already exited. */ }
  }
  await Promise.race([new Promise(resolve => child.once('exit', resolve)), delay(100)])
}
export async function launch(directory: string, args: string[], logs: string[], timeout = 30_000) {
  const home = join(directory, 'home')
  await mkdir(home, { recursive: true })
  const child = spawn(join(root, 'studio/.venv/bin/python'), ['-m', 'openbacktesting_studio.cli', ...args, '--port', '0', '--no-open'], {
    cwd: directory, detached: true, env: { ...process.env, HOME: home, PYTHONUNBUFFERED: '1',
      PYTHONPATH: join(root, 'studio/web/e2e/guard'), HARNESS_NETWORK_LOG: join(directory, 'network.log') },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  let output = '', failure = ''
  child.on('error', error => { failure = error.message })
  for (const stream of [child.stdout, child.stderr]) stream?.on('data', value => {
    output = (output + String(value)).slice(0, 262144)
    if (logs.join('').length < 262144) logs.push(redact(String(value)))
  })
  const deadline = Date.now() + timeout
  try {
    while (Date.now() < deadline) {
      if (failure || child.exitCode !== null) throw Error(failure || `Studio exited ${child.exitCode}: ${redact(output)}`)
      const url = output.match(/http:\/\/127\.0\.0\.1:\d+\/#token=[^\s]+/)?.[0]
      if (url) {
        try { if ((await fetch(new URL('/', url), { signal: AbortSignal.timeout(1000) })).ok) return { child, url } } catch { /* Readiness remains bounded. */ }
      }
      await delay(50)
    }
    throw Error(`Studio readiness deadline exceeded: ${redact(output)}`)
  } catch (error) { await stop(child); throw error }
}
export async function enter(page: Page, url: string) {
  try { await page.goto(url); await expect(page.getByText('Connecting to the local workspace…')).toHaveCount(0) }
  catch (error) {
    // Startup URLs carry credentials; never attach the original error as a cause.
    // eslint-disable-next-line preserve-caught-error
    throw Error(redact(String(error)))
  }
}
export async function edit(page: Page, source: string) {
  await page.getByRole('tab', { name: 'Code', exact: true }).click()
  await page.locator('.monaco-editor .view-lines').first().click({ position: { x: 30, y: 10 } })
  await page.keyboard.press('ControlOrMeta+A')
  await page.evaluate(text => {
    const clipboard = new DataTransfer()
    clipboard.setData('text/plain', text)
    document.activeElement?.dispatchEvent(new ClipboardEvent('paste', { clipboardData: clipboard, bubbles: true, cancelable: true }))
  }, source)
  const saved = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/file' && response.request().method() === 'PUT')
  await page.getByRole('button', { name: 'Save strategy', exact: true }).click()
  expect((await saved).ok()).toBeTruthy()
  await expect(page.getByRole('button', { name: 'Save strategy', exact: true })).toBeDisabled()
}
export async function configure(page: Page) {
  await page.getByRole('button', { name: 'Strategy settings', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Strategy settings', exact: true })
  await dialog.getByRole('tab', { name: 'Inputs', exact: true }).click()
  await expect(dialog.getByText('Quantity', { exact: true })).toBeVisible()
  await dialog.getByRole('tab', { name: 'Data', exact: true }).click()
  await dialog.getByRole('combobox', { name: 'Data source', exact: true }).click()
  await page.getByRole('option', { name: 'Workspace CSV', exact: true }).click()
  await dialog.getByLabel('Workspace path', { exact: true }).fill('prices.csv')
  await dialog.getByLabel('Symbol', { exact: true }).fill('FIXTURE')
  await dialog.getByRole('button', { name: 'Apply to next run', exact: true }).click()
}
export async function run(page: Page, status = 'succeeded') {
  const submitted = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/runs' && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Run', exact: true }).click()
  const response = await submitted
  expect(response.ok()).toBeTruthy()
  const record = await response.json() as { id: string }
  const item = page.getByRole('button').filter({ hasText: record.id.slice(0, 10) })
  await expect(item).toContainText(status, { timeout: 45_000 })
  await item.click()
  return record.id
}
export async function fills(page: Page) {
  await page.getByRole('tab', { name: 'List of trades', exact: true }).click()
  await page.getByRole('combobox', { name: 'Report table', exact: true }).click()
  const response = page.waitForResponse(response => response.url().includes('/trades?table=fills'))
  await page.getByRole('option', { name: 'Fills', exact: true }).click()
  const body = await (await response).json()
  await expect(page.getByText('2 records', { exact: true })).toBeVisible()
  // Independent arithmetic: market orders on bars 0/3 fill at next opens 101/104.
  expect(body.rows.map((row: { price: number; qty: number; bar_index: number }) => [row.price, row.qty, row.bar_index])).toEqual([[101, 1, 1], [104, 1, 4]])
  return body
}
export async function restrictNetwork(context: BrowserContext, outbound: string[]) {
    await context.route('**/*', async route => {
      const url = new URL(route.request().url())
      if (['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol) && !['127.0.0.1', '[::1]', 'localhost'].includes(url.hostname)) {
        outbound.push(`${url.protocol}//${url.hostname}`); await route.abort('blockedbyclient')
      } else await route.continue()
    })
    await context.routeWebSocket(/.*/, socket => {
      const url = new URL(socket.url())
      if (['127.0.0.1', '[::1]', 'localhost'].includes(url.hostname)) socket.connectToServer()
      else { outbound.push(`${url.protocol}//${url.hostname}`); socket.close() }
    })
}
export const test = base.extend<{ studio: { workspace: string; directory: string; viewer: (path: string) => Promise<string>; stop: () => Promise<void> } }>({
  studio: async ({ page, context }, provide, info) => {
    const directory = await mkdtemp(join(tmpdir(), 'ob-harness-'))
    const workspace = join(directory, 'workspace')
    await mkdir(workspace)
    await writeFile(join(workspace, 'strategy.py'), strategy)
    await writeFile(join(workspace, 'prices.csv'), 'Date,Open,High,Low,Close,Volume\n' + Array.from({ length: 8 }, (_, i) => `2024-01-${String(i + 1).padStart(2, '0')},${100+i},${102+i},${99+i},${101+i},1000\n`).join(''))
    const hosts: ChildProcess[] = [], logs: string[] = [], events: string[] = [], outbound: string[] = []
    await restrictNetwork(context, outbound)
    page.on('console', msg => { if (events.length < 300) events.push(redact(`console ${msg.type()}: ${msg.text().slice(0, 4096)}`)) })
    page.on('pageerror', error => { if (events.length < 300) events.push(redact(`pageerror: ${error.message.slice(0, 4096)}`)) })
    page.on('response', response => { if (events.length < 300) events.push(`${response.status()} ${new URL(response.url()).pathname}`) })
    const start = async (args: string[]) => { const host = await launch(directory, args, logs); hosts.push(host.child); return host.url }
    let fixtureFailed = false
    try {
      await enter(page, await start([workspace]))
      const opened = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/workspace' && response.request().method() === 'PUT', { timeout: 30_000 })
      await page.getByRole('button', { name: 'Open directory', exact: true }).click()
      expect((await opened).ok()).toBeTruthy()
      await page.getByRole('button', { name: 'strategy.py', exact: true }).click()
      await provide({ workspace, directory, viewer: path => start(['view', path]), stop: async () => { for (const child of [...hosts].reverse()) await stop(child) } })
    } catch (error) {
      fixtureFailed = true
      throw error
    } finally {
      try {
        // Capture bounded evidence before removing the isolated workspace, including setup failures.
        await mkdir(info.outputPath(''), { recursive: true })
        if (fixtureFailed || info.status !== info.expectedStatus) {
          await page.screenshot({ path: info.outputPath('failure.png') }).catch(() => {})
          await writeFile(info.outputPath('dom.txt'), redact((await page.locator('body').innerText().catch(() => '')).slice(0, 262144)))
        }
        const runRoot = join(workspace, '.openbacktesting/studio/runs')
        const runs: Record<string, unknown>[] = []
        for (const id of await readdir(runRoot).catch(() => [])) {
          const files: Record<string, string> = {}
          for (const name of await readdir(join(runRoot, id))) {
            if (/\.(json|log|txt)$/.test(name)) files[name] = redact((await readFile(join(runRoot, id, name), 'utf8').catch(() => '')).slice(0, 65536))
          }
          runs.push({ id, files })
        }
        for (const child of [...hosts].reverse()) await stop(child)
        const network = await readFile(join(directory, 'network.log'), 'utf8').catch(() => '')
        await writeFile(info.outputPath('evidence.json'), JSON.stringify({ test: info.title, status: fixtureFailed ? 'failed' : info.status, hostLogs: logs, events, runs, outbound, network, runEvidence: runs.length ? 'Collected' : 'No run was created before completion or failure', hostPids: hosts.map(child => child.pid), stopped: hosts.every(child => child.exitCode !== null || child.signalCode !== null) }, null, 2))
        expect(network, 'Unexpected Python external requests').toBe('')
      } finally {
        for (const child of [...hosts].reverse()) await stop(child)
        await rm(directory, { recursive: true, force: true })
      }
      expect(outbound, 'Unexpected browser external requests').toEqual([])

    }
  },
})
export { expect }
