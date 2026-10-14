// @vitest-environment jsdom
import '@/test/dom'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { deferred } from '@/test/dom'
import { api } from '@/protocol/client'
import { ReportView, type Report } from './ReportView'
import fixture from '../../../tests/fixtures/portfolio.json'
vi.mock('./EquityChart', () => ({ EquityChart: () => <div>Equity plot</div> }))
const report = fixture as unknown as Report
const page = (rows: Record<string, unknown>[] = [], total = rows.length, offset = 0) => ({ rows, total, offset, limit: 100 })
let respond: (path: string) => unknown
beforeEach(() => {
  respond = path => path.endsWith('/catalog') ? { version: 1, entries: [] } : path.endsWith('/curve') ? { points: [] } : page()
  vi.spyOn(api, 'request').mockImplementation(async <T,>(path: string) => await respond(path) as T)
})
const view = (tab = 'trades', runId = 'run-a', onFill = vi.fn()) => <ReportView runId={runId} report={report} dark={false} tab={tab} onFill={onFill} />
async function table(name: string) { const user = userEvent.setup(); await user.click(screen.getByRole('combobox', { name: 'Report table' })); await user.click(screen.getByRole('option', { name })) }

describe('report controls', () => {
  it('UI-R01: all, long and short switch the authoritative metric values and contribution label', async () => {
    const data = structuredClone(report)
    for (const [direction, value] of [['all', 101], ['long', 202], ['short', 303]] as const) data.summary[direction].totalPnl.value = value
    render(<ReportView runId="a" report={data} dark={false} tab="overview" onFill={vi.fn()} />)
    const user = userEvent.setup()
    for (const [direction, value] of [['Long', '202'], ['Short', '303'], ['All', '101']]) {
      await user.click(screen.getByRole('button', { name: direction }))
      expect(screen.getByText(value)).toBeTruthy()
      expect(screen.getByText(direction === 'All' ? 'Account results' : 'Direction contribution · not a separate account')).toBeTruthy()
    }
  })
  it.each(['Closed Fragments', 'Open Lots', 'Orders', 'Fills', 'Allocations', 'Account', 'Close'])('UI-R02: %s table chooses its own saved facts and empty state', async name => {
    render(view()); await table(name)
    await waitFor(() => expect(screen.getByText(`No ${name.toLowerCase()} in this run.`)).toBeTruthy())
    const key = name.replaceAll(' ', ''); const parameter = key[0].toLowerCase() + key.slice(1)
    expect(api.request).toHaveBeenCalledWith(`/runs/run-a/trades?table=${parameter}&offset=0`, expect.anything())
  })
  it('UI-R03: next and previous page keep correct offsets and disable at boundaries', async () => {
    respond = path => path.includes('/trades?') ? page([{ fragmentId: path.includes('offset=100') ? 'second-page' : 'first-page' }], 101, path.includes('offset=100') ? 100 : 0) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
    render(view()); await screen.findByText('first-page')
    const user = userEvent.setup()
    expect((screen.getByRole('button', { name: 'Previous' }) as HTMLButtonElement).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Next' })); await screen.findByText('second-page')
    expect((screen.getByRole('button', { name: 'Next' }) as HTMLButtonElement).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Previous' })); await screen.findByText('first-page')
  })
  it('UI-R04: Details exposes full precision and locates the fragment exit fill', async () => {
    const row = { fragmentId: 'fragment-a', pnlNet: 0.123456789, exit: { fillId: 'fill-exit', barIndex: 12 } }
    respond = path => path.includes('/trades?') ? page([row]) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
    const onFill = vi.fn(); render(view('trades', 'run-a', onFill)); await screen.findByText('fragment-a')
    await userEvent.setup().click(screen.getByRole('button', { name: 'Details' }))
    expect(onFill).toHaveBeenCalledWith('fill-exit', 12)
    expect(screen.getByText(/"pnlNet": 0.123456789/)).toBeTruthy()
    await table('Fills'); expect(screen.queryByText('Raw record · full precision')).toBeNull()
  })
  it('UI-R05: slow previous table cannot replace the currently selected table', async () => {
    const old = deferred<ReturnType<typeof page>>()
    respond = path => path.includes('table=closedFragments') ? old.promise : path.includes('table=fills') ? page([{ fill_id: 'new-fill' }]) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
    render(view()); await table('Fills'); await screen.findByText('new-fill')
    await act(async () => { old.resolve(page([{ fill_id: 'wrong-old-row', fragmentId: 'old-fragment' }])) })
    expect(screen.getByText('new-fill')).toBeTruthy(); expect(screen.queryByText('wrong-old-row')).toBeNull()
  })
  it('UI-R06: switching run while a response is pending cannot show the old run', async () => {
    const old = deferred<ReturnType<typeof page>>()
    respond = path => path.includes('/trades?') ? path.includes('/run-a/') ? old.promise : page([{ fragmentId: 'run-b-fragment' }]) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
    const mounted = render(view()); mounted.rerender(view('trades', 'run-b')); await screen.findByText('run-b-fragment')
    await act(async () => old.resolve(page([{ fragmentId: 'run-a-fragment' }])))
    expect(screen.getByText('run-b-fragment')).toBeTruthy(); expect(screen.queryByText('run-a-fragment')).toBeNull()
  })
  it('UI-R07: a table load failure does not show stale rows or enable pagination', async () => {
    respond = path => path.includes('table=fills') ? Promise.reject(Error('Saved fills unavailable')) : path.includes('/trades?') ? page([{ fragmentId: 'old-fragment' }], 200) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
    render(view()); await screen.findByText('old-fragment'); await table('Fills')
    await screen.findByText(/Saved fills unavailable/)
    expect(screen.queryByText('old-fragment')).toBeNull()
    expect((screen.getByRole('button', { name: 'Next' }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-R08: curve failure is visible in Overview and retry restores the plot', async () => {
    let failed = true
    respond = path => path.endsWith('/curve') ? failed ? Promise.reject(Error('Curve unavailable')) : { points: [] } : path.endsWith('/catalog') ? { entries: [] } : page()
    render(view('overview')); await screen.findByText(/Curve unavailable/)
    failed = false; await userEvent.setup().click(screen.getByRole('button', { name: 'Retry report data' }))
    await screen.findByText('Equity plot'); expect(screen.queryByText(/Curve unavailable/)).toBeNull()
  })
  it('UI-R09: Settings & Data displays run, execution, method and requested configuration', () => {
    render(view('settings'))
    for (const title of ['Run', 'Execution & data', 'Method & versions', 'Requested configuration']) expect(screen.getByRole('heading', { name: title })).toBeTruthy()
  })
})
it('UI-R10: allocation details locate the authoritative fill bar supplied separately from the raw row', async () => {
  const onFill = vi.fn(), allocation = { allocation_id: 'allocation-a', fill_id: 'fill-a', trade_id: 'trade-a', qty: 2 }
  respond = path => path.includes('/trades?') ? { ...page([allocation]), fillBars: { 'fill-a': 42 } } : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
  render(view('trades', 'run-a', onFill)); await table('Allocations'); await screen.findByText('allocation-a'); await userEvent.setup().click(screen.getByRole('button', { name: 'Details' }))
  expect(onFill).toHaveBeenCalledWith('fill-a', 42)
  expect(document.querySelector('pre')?.textContent).toBe(JSON.stringify(allocation, null, 2))
})
it('UI-R11: details without a known original bar never send a NaN chart location', async () => {
  const onFill = vi.fn(); respond = path => path.includes('/trades?') ? page([{ fill_id: 'missing-location' }]) : path.endsWith('/catalog') ? { entries: [] } : { points: [] }
  render(view('trades', 'run-a', onFill)); await screen.findByRole('button', { name: 'Details' }); await userEvent.setup().click(screen.getByRole('button', { name: 'Details' }))
  expect(onFill).not.toHaveBeenCalled(); expect(screen.getByText('Raw record · full precision')).toBeTruthy()
})
