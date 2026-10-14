// @vitest-environment jsdom
import '@/test/dom'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { api } from '@/protocol/client'
import { deferred } from '@/test/dom'
import { OptimizerPanel } from './OptimizerPanel'
import type { Description } from './inputs'
import type { Experiment } from './optimizer'
const schema: Description = { schemaVersion: '1.0.0', schemaHash: 'hash', backtest: { settings: {} }, inputs: [{ title: 'Length', attribute: 'length', kind: 'int', default: 1, active: true, display: 'all', confirm: false, group: '', inline: '', tooltip: '' }] }
const metric = 'summary.all.totalPnl.value'
const plan = { total: 3, inputs: { schemaHash: 'hash', values: { Length: 1 } }, dimensions: [{ title: 'Length', values: [1, 2, 3] }], execution: { backtest: { settings: { cash: 10000 } } } }
let item: Experiment, override: (path: string, options?: RequestInit) => unknown
const trial = (id: string) => ({ trial_id: id, ordinal: id === 'first' ? 0 : 1, inputs: { Length: 2 }, values: { [metric]: { value: 12.5, status: 'ok', unit: 'money', methodId: 'core' } } })
beforeEach(() => {
  item = { id: 'experiment-a', status: 'completed', source: 'strategy.py', plan, info: { total: 3, checked: 3, committed: 2, skipped: 1, failed: 0, remaining: 0 } }; override = () => undefined
  vi.spyOn(api, 'request').mockImplementation(async <T,>(path: string, options?: RequestInit) => {
    const custom = override(path, options); if (custom !== undefined) return await custom as T
    let result: unknown
    if (path === '/optimizations') result = { items: [item] }
    else if (path === '/optimizations/experiment-a') result = item
    else if (path.endsWith('/fields')) result = { fields: [{ path: metric, kind: 'number', unit: 'money', status: 'ok', method: 'core', suggestedDirection: 'desc' }] }
    else if (path.endsWith('/query')) result = { rows: [trial(JSON.parse(String(options?.body)).cursor ? 'second' : 'first')], cursor: JSON.parse(String(options?.body)).cursor ? null : 'next-cursor', watermark: 2 }
    else if (path.endsWith('/start')) result = item = { ...item, status: 'running' }
    else if (path.endsWith('/cancel')) result = item = { ...item, status: 'cancelled' }
    else if (path.endsWith('/open')) result = { id: 'saved-trial' }
    else if (path.includes('/trials?')) result = { rows: [{ trial_id: 'first', ordinal: 0, state: 'succeeded', attempt: 1, request: '{"values":{"Length":2}}', error: null }, { trial_id: 'bad', ordinal: 1, state: 'failed', attempt: 1, request: '{"values":{"Length":3}}', error: 'execution: ValueError: invalid order' }] }
    else throw Error('Unexpected ' + path)
    return result as T
  })
})
function mount() {
  const props = { schema, values: { Length: 1 }, canPrepare: true, onConfigure: vi.fn(), onPrepare: vi.fn(async () => ({ ...item, status: 'planned', info: undefined })), onActive: vi.fn(), onOpenReport: vi.fn(async () => {}), onApply: vi.fn() }
  const rendered = render(<OptimizerPanel {...props} />); return { props, ...rendered }
}
it('UI-O01: range preview sends only selected dimensions and never starts execution automatically', async () => {
  const { props } = mount(), user = userEvent.setup()
  await user.click(screen.getByRole('checkbox', { name: 'Length' }))
  await user.click(screen.getByRole('combobox', { name: 'Domain type for Length' })); await user.click(screen.getByRole('option', { name: 'range' }))
  fireEvent.change(screen.getByLabelText('Length stop'), { target: { value: '3' } })
  await user.type(screen.getByLabelText('Constraint function'), 'acceptable')
  await user.click(screen.getByRole('button', { name: 'Preview search' }))
  expect(props.onPrepare).toHaveBeenCalledExactlyOnceWith({ Length: { kind: 'range', start: 1, stop: 3, step: 1 } }, 'acceptable')
  expect(vi.mocked(api.request).mock.calls.some(([path]) => path.endsWith('/start'))).toBe(false)
  expect(await screen.findByRole('button', { name: 'Start experiment' })).toBeTruthy()
})
it('UI-O02: invalid candidates show an actionable error without a preview request', async () => {
  const { props } = mount(), user = userEvent.setup()
  await user.click(screen.getByRole('checkbox', { name: 'Length' })); fireEvent.change(screen.getByLabelText('Length candidate 1'), { target: { value: 'bad' } })
  await user.click(screen.getByRole('button', { name: 'Preview search' }))
  expect(screen.getByRole('alert').textContent).toContain('finite number'); expect(props.onPrepare).not.toHaveBeenCalled()
  await user.click(screen.getByRole('button', { name: 'Dismiss optimizer error' })); expect(screen.queryByRole('alert')).toBeNull()
})
it('UI-O03: start, cancel and resume use explicit actions and prevent duplicate starts', async () => {
  item = { ...item, status: 'planned', info: undefined }; mount(); const user = userEvent.setup()
  await user.dblClick(await screen.findByRole('button', { name: 'Start experiment' }))
  expect(vi.mocked(api.request).mock.calls.filter(([path]) => path.endsWith('/start'))).toHaveLength(1)
  await user.click(await screen.findByRole('button', { name: 'Cancel experiment' }))
  expect(await screen.findByRole('button', { name: 'Resume experiment' })).toBeTruthy()
})
it('UI-O04: sorting, typed filters, columns and snapshot pagination reach the core query unchanged', async () => {
  mount(); const user = userEvent.setup(); await screen.findByText('3 combinations')
  await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByText('Length=2')
  await user.click(screen.getByRole('button', { name: 'Add sort' })); await user.click(screen.getByRole('button', { name: 'Add filter' }))
  fireEvent.change(screen.getByLabelText('Filter value 1'), { target: { value: '10.5' } }); await user.click(screen.getByRole('button', { name: 'Refresh results' }))
  await waitFor(() => expect(api.request).toHaveBeenCalledWith('/optimizations/experiment-a/query', expect.objectContaining({ body: JSON.stringify({ fields: [metric], order_by: [[metric, 'desc']], filters: [[metric, 'ge', 10.5]], cursor: null, limit: 50 }) })))
  await screen.findByText('Length=2'); await user.click(screen.getByRole('button', { name: 'Next results' }))
  await waitFor(() => expect(vi.mocked(api.request).mock.calls.filter(([path]) => path.endsWith('/query')).at(-1)?.[1]?.body).toContain('next-cursor'))
  await screen.findByText('Page 2', { exact: false }); await user.click(screen.getByRole('button', { name: 'Previous results' })); await screen.findByText('Page 1', { exact: false })
})
it('UI-O05: successful trials open stored reports or apply inputs without starting a backtest', async () => {
  const { props } = mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByText('Length=2')
  await user.click(screen.getByRole('button', { name: 'Apply inputs' })); expect(props.onApply).toHaveBeenCalledExactlyOnceWith({ Length: 2 }, 'hash', { cash: 10000 })
  await user.click(screen.getByRole('button', { name: 'Open report' })); expect(props.onOpenReport).toHaveBeenCalledExactlyOnceWith('saved-trial')
  expect(vi.mocked(api.request).mock.calls.some(([path]) => path === '/runs')).toBe(false)
})
it('UI-O06: all-trial view includes failed diagnostics but only successful rows can open a report', async () => {
  mount(); await userEvent.setup().click(screen.getByRole('tab', { name: 'All trials' }))
  await screen.findByText('execution: ValueError: invalid order')
  expect(screen.getAllByRole('button', { name: 'Open report' })).toHaveLength(1)
})
it('UI-O07: imported experiments stay queryable but cannot start or resume source execution', async () => {
  item = { ...item, imported: true, status: 'cancelled' }; mount(); await screen.findByText('3 combinations')
  expect(screen.queryByRole('button', { name: 'Resume experiment' })).toBeNull()
  expect((screen.getByRole('button', { name: 'Export database' }) as HTMLButtonElement).disabled).toBe(false)
})
it('UI-O08: query errors are visible and Refresh retries instead of leaving perpetual loading', async () => {
  let failed = true; override = path => path.endsWith('/query') && failed ? Promise.reject(Error('Invalid field')) : undefined
  mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByText('Invalid field')
  failed = false; await user.click(screen.getByRole('button', { name: 'Refresh results' })); await screen.findByText('Length=2'); expect(screen.queryByRole('alert')).toBeNull()
})
it('UI-O09: late results cannot overwrite a new query snapshot', async () => {
  const pending = deferred<{ rows: ReturnType<typeof trial>[]; cursor: null; watermark: number }>(); let delay = true
  override = path => path.endsWith('/query') && delay ? pending.promise : undefined
  mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByText('Loading saved trial results…')
  delay = false; await user.click(screen.getByRole('button', { name: 'Refresh results' })); await screen.findByText('Length=2')
  await act(async () => pending.resolve({ rows: [{ ...trial('old'), inputs: { Length: 999 } }], cursor: null, watermark: 0 }))
  expect(screen.queryByText('Length=999')).toBeNull()
})
it('UI-O10: switching experiments restores default columns and ignores the previous response', async () => {
  const second = { ...item, id: 'experiment-b', source: 'second.py' }
  override = path => path === '/optimizations' ? { items: [item, second] } : path === '/optimizations/experiment-b' ? second : undefined
  mount(); const user = userEvent.setup(); await screen.findByText('3 combinations')
  await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByRole('columnheader', { name: 'Total Pnl' })
  await user.click(screen.getByRole('combobox', { name: 'Saved experiment' })); await user.click(screen.getByRole('option', { name: /second.py/ }))
  await waitFor(() => expect(api.request).toHaveBeenCalledWith('/optimizations/experiment-b'))
  await screen.findByRole('columnheader', { name: 'Total Pnl' })
  await user.click(screen.getByRole('combobox', { name: 'Saved experiment' })); await user.click(screen.getByRole('option', { name: /strategy.py/ }))
  await screen.findByRole('columnheader', { name: 'Total Pnl' })
})
it('UI-O11: importing a database keeps its plan and exporting downloads the saved SQLite snapshot', async () => {
  const imported = { ...item, id: 'imported', imported: true, status: 'cancelled' }
  override = path => path === '/optimizations/import' || path === '/optimizations/imported' ? imported : undefined
  const download = vi.spyOn(api, 'download').mockResolvedValue(new Blob(['SQLite format 3']))
  const create = vi.fn(() => 'blob:export'), revoke = vi.fn()
  vi.stubGlobal('URL', class extends URL { static createObjectURL = create; static revokeObjectURL = revoke })
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  mount(); const user = userEvent.setup(); await screen.findByText('3 combinations')
  const file = new File(['SQLite format 3'], 'saved.sqlite', { type: 'application/octet-stream' })
  await user.upload(screen.getByLabelText('Import experiment database'), file)
  await waitFor(() => expect(api.request).toHaveBeenCalledWith('/optimizations/import', expect.objectContaining({ method: 'POST', body: file })))
  await screen.findByText('cancelled'); expect(screen.queryByRole('button', { name: 'Resume experiment' })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Export database' }))
  expect(download).toHaveBeenCalledWith('/optimizations/imported/export'); expect(create).toHaveBeenCalled(); expect(click).toHaveBeenCalledOnce()
})
it('UI-O12: trial pagination sends explicit offsets and preserves failed diagnostic text', async () => {
  item.info = { ...item.info!, total: 52, checked: 52 }
  override = path => path.includes('/trials?offset=0') ? { rows: Array.from({ length: 50 }, (_, ordinal) => ({ trial_id: String(ordinal), ordinal, state: 'skipped_constraint', attempt: 1, request: '{"values":{"Length":2}}', error: null })) } : undefined
  mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'All trials' }))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Next trials' }).hasAttribute('disabled')).toBe(false))
  await user.click(screen.getByRole('button', { name: 'Next trials' })); await screen.findByText('execution: ValueError: invalid order')
  expect(api.request).toHaveBeenCalledWith('/optimizations/experiment-a/trials?offset=50&limit=50')
  await user.click(screen.getByRole('button', { name: 'Previous trials' })); await screen.findAllByText('skipped_constraint')
})
it('UI-O13: searchable field picker selects from the complete catalogue for filters and columns', async () => {
  const other = 'summary.all.totalReturn.value'
  override = path => path.endsWith('/fields') ? { fields: [metric, ...Array.from({ length: 120 }, (_, i) => `extra.${i}`), other].map(path => ({ path, kind: 'number', unit: null, status: null, method: null, suggestedDirection: 'desc' })) } : undefined
  mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Ranked results' })); await screen.findByText('Length=2')
  await user.click(screen.getByRole('button', { name: 'Add filter' })); await user.click(screen.getByRole('combobox', { name: 'Filter field 1' }))
  await user.click(screen.getByRole('button', { name: 'Next fields' })); expect(screen.getByRole('option', { name: other })).toBeTruthy()
  await user.type(screen.getByRole('textbox', { name: 'Search result fields' }), 'totalPnl'); await user.click(screen.getByRole('option', { name: metric }))
  expect(screen.queryByRole('dialog')).toBeNull(); expect(screen.getByRole('combobox', { name: 'Filter field 1' }).textContent).toBe('Total Pnl')
  await user.click(screen.getByRole('combobox', { name: 'Add result column' })); await user.type(screen.getByRole('textbox', { name: 'Search result fields' }), 'extra.119'); await user.click(screen.getByRole('option', { name: 'extra.119' }))
  await user.click(screen.getByRole('button', { name: 'Refresh results' }))
  await waitFor(() => expect(String(vi.mocked(api.request).mock.calls.filter(([path]) => path.endsWith('/query')).at(-1)?.[1]?.body)).toContain('extra.119'))
})
