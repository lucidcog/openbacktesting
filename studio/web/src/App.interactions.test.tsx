// @vitest-environment jsdom
import '@/test/dom'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ComponentProps, ReactNode } from 'react'
import { deferred } from '@/test/dom'
import App from './App'
import { api, ApiError } from '@/protocol/client'
import portfolio from '../../tests/fixtures/portfolio.json'
import plotting from '../../tests/fixtures/plotting.json'
import inputFixture from '../../tests/fixtures/inputs.json'
import type CodeEditor from '@/features/CodeEditor'
import type { MarketChart } from '@/chart/MarketChart'

vi.mock('@/components/ui/resizable', () => ({ ResizablePanelGroup: ({ children, onLayoutChanged, defaultLayout, orientation }: { children: ReactNode; onLayoutChanged: (layout: Record<string, number>) => void; defaultLayout: object; orientation: string }) => <div data-testid="layout" data-orientation={orientation} data-layout={JSON.stringify(defaultLayout)}>{children}<button onClick={() => onLayoutChanged({ chart: 65, bottom: 35 })}>Resize panels</button><button onClick={() => onLayoutChanged({ chart: 100 })}>Collapse layout notification</button></div>, ResizablePanel: ({ children }: { children: ReactNode }) => <div>{children}</div>, ResizableHandle: () => <div role="separator" /> }))
vi.mock('@/features/CodeEditor', () => ({ default: (props: ComponentProps<typeof CodeEditor>) => <textarea aria-label={props.original === undefined ? 'Editor content' : 'Diff content'} value={props.value} readOnly={props.readonly || props.original !== undefined} onChange={event => props.onChange(event.target.value)} onKeyDown={event => { if ((event.metaKey || event.ctrlKey) && event.key === 's') { event.preventDefault(); props.onSave() } }} /> }))
vi.mock('@/chart/MarketChart', () => ({ MarketChart: (props: ComponentProps<typeof MarketChart>) => <div aria-label="Test market chart">signals:{String(props.showSignals)} fills:{String(props.showTrades)}<button onClick={() => props.onSelect({ bar: 0, label: 'first bar', price: 123, milliseconds: 1000, fills: [], markers: [] })}>Select empty bar</button>
  <span>selected:{props.selectedFill ?? 'none'}</span>
  <button onClick={() => props.onSelect({ bar: 2, label: 'fill bar', price: 123, milliseconds: 1000, fills: [{ fill_id: 'fill-test', bar_index: 2, price: 123, qty: 1, fee: 0, side: 'buy', phase: 'open', sequence: 1 }], markers: [] })}>Select fill bar</button>
  {[0, 100].map(start => <button key={start} onClick={() => props.onSelect({ bar: start, label: 'cluster', price: 123, milliseconds: 1000, fills: [], markers: [], cluster: { bar: start, start, end: start + 100, fillCount: 150, signalCount: 0, kind: 'display' } })}>Select cluster {start}</button>)}
  <button onClick={() => props.onSelect({ bar: 0, label: 'incompatible axis', price: null, milliseconds: null, fills: [], markers: [] })}>Select invalid pick</button>
  <button onClick={() => props.onViewport?.({ from: 10, to: 100 })}>Zoom to viewport</button></div> }))
vi.mock('@/features/EquityChart', () => ({ EquityChart: () => <div>Equity plot</div> }))
const schema = { schemaVersion: '1.0.0', schemaHash: 'one', inputs: [], backtest: { settings: {} } }
const file = { path: 'strategy.py', content: 'original source', revision: 'r1' }
const caps = { workspaceId: 'workspace-a', mode: 'workspace', workspace: '/strategies', suggestedWorkspace: '/strategies', interpreter: { compatible: true, executable: '/python' }, capabilities: { edit: true, discover: true } }
type RecordRun = { id: string; status: string; error?: { message: string }; request?: object }
let runs: RecordRun[], files: string[], source: typeof file
let override: (path: string, options?: RequestInit) => unknown
const posts = () => vi.mocked(api.request).mock.calls.filter(([path, options]) => path === '/runs' && options?.method === 'POST')
const summary = (id: string) => ({ ...structuredClone(portfolio), context: { ...portfolio.context, instrument: { ...portfolio.context.instrument, symbol: id } } })
function respond(path: string, options?: RequestInit): unknown {
  const custom = override(path, options); if (custom !== undefined) return custom
  if (path === '/capabilities') return caps
  if (path === '/files') return { files }
  if (path.startsWith('/file?')) return { ...source, path: new URLSearchParams(path.split('?')[1]).get('path')! }
  if (path === '/file' && options?.method === 'PUT') { source = { ...source, ...JSON.parse(String(options.body)), revision: 'r2' }; return source }
  if (path === '/discover') return { description: schema, sourceHash: 'snapshot', sourceFiles: {} }
  if (path === '/runs') {
    if (options?.method === 'POST') { const run = { id: 'new-run', status: 'succeeded' }; runs = [run, ...runs]; return run }
    return { runs }
  }
  if (path === '/presets' || path === '/profiles') return { items: [] }
  if (path.endsWith('/summary')) return summary(path.split('/')[2])
  if (path.endsWith('/chart') || path.includes('/chart?')) return { plotting, window: { start: 0, end: 4, total: 4, granularity: 1 } }
  if (path.endsWith('/logs')) return { text: path.split('/')[2] + '-logs' }
  if (path.endsWith('/provenance')) return { origin: 'local' }
  if (path.endsWith('/curve')) return { points: [] }
  if (path.endsWith('/catalog')) return { entries: [] }
  if (path.includes('/trades?')) return { rows: [], total: 0, offset: 0, limit: 100 }
  if (path.endsWith('/workspace-match')) return { runId: path.split('/')[2], matches: true }
  if (path.startsWith('/directories')) return { path: '/strategies', parent: '/', directories: ['child'] }
  if (path.endsWith('/cancel')) { runs = runs.map(run => run.id === path.split('/')[2] ? { ...run, status: 'cancelled' } : run); return runs.find(run => run.id === path.split('/')[2]) }
  throw Error(`Unexpected API request: ${path}`)
}
beforeEach(() => {
  localStorage.setItem('studio.theme', 'light')
  runs = [{ id: 'run-a', status: 'succeeded' }, { id: 'run-b', status: 'succeeded' }]
  files = ['strategy.py', 'folder/Other.py']; source = { ...file }; override = () => undefined
  vi.spyOn(api, 'connect').mockResolvedValue()
  vi.spyOn(api, 'request').mockImplementation(async <T,>(path: string, options?: RequestInit) => await respond(path, options) as T)
})
async function mount() { render(<App />); await screen.findByRole('button', { name: 'strategy.py' }); await screen.findByLabelText('Test market chart') }
async function chooseFile(name = 'strategy.py') { await userEvent.setup().click(screen.getByTitle(name)); return screen.findByRole('textbox', { name: 'Editor content' }) }

describe('workspace and history controls', () => {
  it('UI-A01: repeated click on a loaded history row keeps report and chart visible without refetching', async () => {
    await mount(); const count = vi.mocked(api.request).mock.calls.filter(([path]) => path === '/runs/run-a/summary').length
    await userEvent.setup().click(screen.getByRole('button', { name: /run-a.*succeeded/ }))
    expect(screen.getByLabelText('Test market chart')).toBeTruthy(); expect(screen.queryByText('Loading result')).toBeNull()
    expect(vi.mocked(api.request).mock.calls.filter(([path]) => path === '/runs/run-a/summary')).toHaveLength(count)
  })
  it('UI-A02: clicking the selected run during initial loading does not cancel its only request', async () => {
    const saved = deferred<ReturnType<typeof summary>>()
    override = path => path === '/runs/run-a/summary' ? saved.promise : undefined
    await mount(); await userEvent.setup().click(screen.getByRole('button', { name: /run-a.*succeeded/ }))
    await act(async () => saved.resolve(summary('run-a')))
    await screen.findByText('Total Pnl'); expect(screen.queryByText('Loading saved report…')).toBeNull()
  })
  it('UI-A03: rapid history changes ignore late old results and returning to a cached run needs no reload', async () => {
    const delayed = deferred<ReturnType<typeof summary>>()
    override = path => path === '/runs/run-b/summary' ? delayed.promise : undefined
    await mount(); await screen.findByText('Total Pnl'); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /run-b.*succeeded/ })); await user.click(screen.getByRole('button', { name: /run-a.*succeeded/ }))
    await act(async () => delayed.resolve(summary('wrong-old-result')))
    expect(screen.queryByText('wrong-old-result')).toBeNull(); expect(screen.getByText('Total Pnl')).toBeTruthy()
    expect(vi.mocked(api.request).mock.calls.filter(([path]) => path === '/runs/run-a/summary')).toHaveLength(1)
  })
  it('UI-A04: report or chart read failures are visible and do not hide the other artifact', async () => {
    override = path => path === '/runs/run-a/chart' ? Promise.reject(Error('Chart snapshot missing')) : undefined
    render(<App />); await screen.findByText('Chart snapshot missing'); await screen.findByText('Total Pnl')
    expect(screen.queryByText('Loading result')).toBeNull()
  })
  it('UI-A05: file search matches name/path case-insensitively, clears by button and Escape, and shows empty results', async () => {
    await mount(); const user = userEvent.setup(), input = screen.getByRole('textbox', { name: 'Search workspace files by name or path' })
    await user.type(input, 'FOLDER/OTHER'); expect(screen.getByRole('button', { name: 'folder/Other.py' })).toBeTruthy(); expect(screen.queryByRole('button', { name: 'strategy.py' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Clear file search' })); expect(document.activeElement).toBe(input)
    await user.type(input, 'no-match'); expect(screen.getByText('No matching files.')).toBeTruthy()
    await user.keyboard('{Escape}'); expect(screen.getByRole('button', { name: 'strategy.py' })).toBeTruthy()
  })
  it('UI-A06: sidebar, theme and results-panel toggles preserve their visible states and preferences', async () => {
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Toggle file sidebar' })); expect(screen.queryByRole('complementary')).toBeNull(); expect(localStorage.getItem('studio.sidebar')).toBe('false')
    await user.click(screen.getByRole('button', { name: 'Toggle file sidebar' })); expect(screen.getByRole('complementary')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: 'Toggle color theme' })); expect(document.documentElement.classList.contains('dark')).toBe(true); expect(localStorage.getItem('studio.theme')).toBe('dark')
    await user.click(screen.getByRole('button', { name: 'Collapse results panel' })); expect(screen.queryByRole('tab', { name: 'Overview' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Show results & code' })); expect(screen.getByRole('tab', { name: 'Overview' })).toBeTruthy()
  })
  it.each(['Overview', 'Performance', 'List of trades', 'Settings & Data', 'Code', 'Logs'])('UI-A07: %s tab selects the corresponding panel', async name => {
    await mount(); await userEvent.setup().click(screen.getByRole('tab', { name }))
    expect(screen.getByRole('tab', { name }).getAttribute('aria-selected')).toBe('true')
    if (name === 'Code') expect(screen.getByText('Select a file from the workspace.')).toBeTruthy()
    if (name === 'Logs') expect(await screen.findByText(/run-a-logs/)).toBeTruthy()
  })
  it('UI-A08: failed history logs can be left by selecting the successful current run again', async () => {
    runs.push({ id: 'failure', status: 'failed', error: { message: 'failed-run-only' } })
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /failure.*failed/ })); expect(screen.getByText(/failed-run-only/)).toBeTruthy()
    await user.click(screen.getByRole('button', { name: /run-a.*succeeded/ }))
    expect(screen.queryByText(/failed-run-only/)).toBeNull()
    await user.click(screen.getByRole('tab', { name: 'Logs' })); expect(await screen.findByText(/run-a-logs/)).toBeTruthy(); expect(screen.queryByText(/failed-run-only/)).toBeNull()
  })
  it.each(['queued', 'running'])('UI-A09: cancel %s history updates the durable displayed status', async status => {
    runs.push({ id: 'queued-run', status }); await mount()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel run queued-run' }))
    await screen.findByRole('button', { name: /queued-run.*cancelled/ })
    expect(screen.queryByRole('button', { name: 'Cancel run queued-run' })).toBeNull()
  })
  it('UI-A10: signal and fill checkboxes update independent chart layers', async () => {
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByRole('checkbox', { name: 'Signals' })); expect(screen.getByLabelText('Test market chart').textContent).toContain('signals:false fills:true')
    await user.click(screen.getByRole('checkbox', { name: 'Fills' })); expect(screen.getByLabelText('Test market chart').textContent).toContain('signals:false fills:false')
  })
  it('UI-A11: selecting an empty chart bar opens details and Close returns to the report', async () => {
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Select empty bar' }))
    expect(screen.getByRole('dialog', { name: 'Bar 0' })).toBeTruthy(); expect(screen.getByText('No fills or strategy markers at this bar.')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: 'Close' })); expect(screen.queryByRole('dialog')).toBeNull()
  })
})

describe('editor and execution controls', () => {
  it('UI-A12: switching files retains unsaved buffers; Save writes the selected file with its revision', async () => {
    await mount(); const editor = await chooseFile(); fireEvent.change(editor, { target: { value: 'edited draft' } })
    await chooseFile('folder/Other.py'); await chooseFile()
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('edited draft')
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save strategy' }))
    await waitFor(() => expect((screen.getByRole('button', { name: 'Save strategy' }) as HTMLButtonElement).disabled).toBe(true))
    expect(api.request).toHaveBeenCalledWith('/file', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ path: 'strategy.py', baseRevision: 'r1', content: 'edited draft' }) }))
  })
  it('UI-A13: save failure preserves the draft and Dismiss error clears only the message', async () => {
    override = (path, options) => path === '/file' && options?.method === 'PUT' ? Promise.reject(Error('Disk full')) : undefined
    await mount(); fireEvent.change(await chooseFile(), { target: { value: 'keep draft' } }); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Save strategy' })); await screen.findByText('Disk full')
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('keep draft')
    await user.click(screen.getByRole('button', { name: 'Dismiss error' })); expect(screen.queryByText('Disk full')).toBeNull(); expect(screen.getByText('Unsaved')).toBeTruthy()
  })
  it('UI-A14: first Run requires one settings review and Apply & Run submits exactly once', async () => {
    await mount(); await chooseFile(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Run' })); await screen.findByRole('dialog', { name: 'Strategy settings' }); expect(posts()).toHaveLength(0)
    await user.click(screen.getByRole('button', { name: 'Apply & Run' })); await screen.findByRole('button', { name: /new-run.*succeeded/ }); expect(posts()).toHaveLength(1)
  })
  it('UI-A15: closing initial review does not submit; standalone Apply does not start a run', async () => {
    await mount(); await chooseFile(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Run' })); await screen.findByRole('dialog', { name: 'Strategy settings' }); await user.click(screen.getByRole('button', { name: 'Close' }))
    expect(posts()).toHaveLength(0)
    await user.click(screen.getByRole('button', { name: 'Strategy settings' })); await screen.findByRole('dialog', { name: 'Strategy settings' }); await user.click(screen.getByRole('button', { name: 'Apply to next run' })); expect(posts()).toHaveLength(0)
  })
  it('UI-A16: Save & Run does not discover or execute after a save conflict', async () => {
    override = (path, options) => path === '/file' && options?.method === 'PUT' ? Promise.reject(new ApiError('FileConflict', 'Changed on disk')) : undefined
    await mount(); fireEvent.change(await chooseFile(), { target: { value: 'conflicting draft' } })
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save & Run' })); await screen.findByRole('dialog', { name: 'External file change' })
    expect(posts()).toHaveLength(0); expect(vi.mocked(api.request).mock.calls.some(([path]) => path === '/discover')).toBe(false)
    expect((screen.getByRole('textbox', { name: 'Diff content' }) as HTMLTextAreaElement).value).toBe('conflicting draft')
    await userEvent.setup().click(screen.getByRole('button', { name: 'Keep draft for manual merge' })); expect(screen.queryByRole('dialog')).toBeNull()
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('conflicting draft')
  })
  it('UI-A17: export defaults exclude private resources and selected checkboxes affect download query', async () => {
    vi.spyOn(api, 'download').mockResolvedValue(new Blob(['archive']))
    URL.createObjectURL = vi.fn(() => 'blob:test'); URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    await mount(); await screen.findByText('Total Pnl'); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Export result' }))
    const dialog = screen.getByRole('dialog', { name: 'Export this run' })
    for (const checkbox of within(dialog).getAllByRole('checkbox')) expect(checkbox.getAttribute('aria-checked')).toBe('false')
    await user.click(within(dialog).getByRole('checkbox', { name: 'Include Python source snapshot' }))
    await user.click(screen.getByRole('button', { name: 'Download .obstudio' })); await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(api.download).toHaveBeenCalledWith('/runs/run-a/export?source=true&data=false&logs=false')
  })
})

describe('manual workspace selection and persistence', () => {
  const unselected = { ...caps, workspace: null, capabilities: { edit: false, discover: false } }
  it('UI-W07: first launch asks for a directory without reading workspace files or runs', async () => {
    override = path => path === '/capabilities' ? unselected : undefined
    render(<App />)
    await screen.findByRole('dialog', { name: 'Choose workspace directory' })
    expect(vi.mocked(api.request).mock.calls.some(([path]) => ['/files', '/runs', '/profiles', '/presets'].includes(path))).toBe(false)
    await userEvent.setup().click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.getByRole('button', { name: 'Choose directory' })).toBeTruthy()
    expect(screen.queryByTitle('strategy.py')).toBeNull()
  })
  it('UI-W08: remembered selection is restored before any workspace files are read', async () => {
    localStorage.setItem('studio.workspace', '/remembered')
    override = path => path === '/capabilities' ? unselected : path === '/workspace' ? { ...caps, workspace: '/remembered' } : undefined
    await mount()
    expect(api.request).toHaveBeenCalledWith('/workspace', { method: 'PUT', body: JSON.stringify({ path: '/remembered' }) })
    const calls = vi.mocked(api.request).mock.calls.map(([path]) => path)
    expect(calls.indexOf('/workspace')).toBeLessThan(calls.indexOf('/files'))
    expect(screen.queryByRole('dialog')).toBeNull()
  })
  it('UI-W09: an unavailable remembered directory returns to the picker without loading the launch directory', async () => {
    localStorage.setItem('studio.workspace', '/deleted')
    override = path => path === '/capabilities' ? unselected : path === '/workspace' ? Promise.reject(Error('Directory missing')) : undefined
    render(<App />)
    await screen.findByRole('dialog', { name: 'Choose workspace directory' })
    expect(screen.getByText(/The remembered workspace is unavailable/)).toBeTruthy()
    expect(vi.mocked(api.request).mock.calls.some(([path]) => path === '/files')).toBe(false)
  })
  it('UI-W10: successful manual selection persists the canonical directory, not the typed alias', async () => {
    override = path => path === '/capabilities' ? unselected : path === '/workspace' ? { ...caps, workspace: '/canonical/strategies' } : undefined
    // jsdom reports full-page navigation as unsupported; persistence is asserted before it.
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<App />); await screen.findByRole('dialog', { name: 'Choose workspace directory' })
    await screen.findByRole('button', { name: 'child' })
    const user = userEvent.setup(), input = screen.getByRole('textbox', { name: 'Workspace directory path' })
    await user.clear(input); await user.type(input, '/alias'); await user.click(screen.getByRole('button', { name: 'Open directory' }))
    await waitFor(() => expect(localStorage.getItem('studio.workspace')).toBe('/canonical/strategies'))
    expect(api.request).toHaveBeenCalledWith('/workspace', { method: 'PUT', body: JSON.stringify({ path: '/alias' }) })
  })
  it('UI-W11: failed selection keeps the old preference and current workspace intact', async () => {
    localStorage.setItem('studio.workspace', '/strategies')
    override = path => path === '/workspace' ? Promise.reject(Error('Permission denied')) : undefined
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Choose workspace directory' }))
    await screen.findByRole('button', { name: 'child' }); await user.click(screen.getByRole('button', { name: 'Open directory' }))
    await screen.findByRole('alert'); expect(localStorage.getItem('studio.workspace')).toBe('/strategies')
    await user.click(screen.getByRole('button', { name: 'Close' })); expect(screen.getByTitle('strategy.py')).toBeTruthy()
  })
  it('UI-W12: unsaved edits prevent switching workspaces until saved', async () => {
    await mount(); fireEvent.change(await chooseFile(), { target: { value: 'unsaved' } })
    expect((screen.getByRole('button', { name: 'Choose workspace directory' }) as HTMLButtonElement).disabled).toBe(true)
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save strategy' }))
    await waitFor(() => expect((screen.getByRole('button', { name: 'Choose workspace directory' }) as HTMLButtonElement).disabled).toBe(false))
  })
  it('UI-W13: active runs prevent workspace switching', async () => {
    runs.push({ id: 'active', status: 'running' }); await mount()
    expect((screen.getByRole('button', { name: 'Choose workspace directory' }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-W14: a selected server workspace is not overwritten by another browser preference', async () => {
    localStorage.setItem('studio.workspace', '/stale-choice'); await mount()
    expect(vi.mocked(api.request).mock.calls.some(([path]) => path === '/workspace')).toBe(false)
  })
})

describe('concurrent file operations', () => {
  it('UI-E01: a slower first file read cannot replace the last file selected', async () => {
    const delayed = deferred<typeof file>()
    override = path => path === '/file?path=strategy.py' ? delayed.promise : undefined
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByTitle('strategy.py')); await chooseFile('folder/Other.py')
    await act(async () => delayed.resolve({ ...file, content: 'late first file' }))
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('original source')
    expect(screen.getByRole('banner').textContent).toContain('folder/Other.py')
  })
  it('UI-E02: overlapping reads of the same file cannot overwrite a draft typed after the first read', async () => {
    const first = deferred<typeof file>(), second = deferred<typeof file>(); let count = 0
    override = path => path === '/file?path=strategy.py' ? (++count === 1 ? first.promise : second.promise) : undefined
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByTitle('strategy.py')); await user.click(screen.getByTitle('strategy.py'))
    await act(async () => first.resolve(file));
    // If duplicate reads are coalesced, the first response is also the latest selection.
    if (count > 1) await act(async () => second.resolve(file))
    fireEvent.change(await screen.findByRole('textbox', { name: 'Editor content' }), { target: { value: 'new draft' } })
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('new draft')
    expect(count).toBe(1)
  })
  it('UI-E03: typing during a save keeps newer changes dirty after the submitted revision is saved', async () => {
    const delayed = deferred<typeof file>()
    override = (path, options) => path === '/file' && options?.method === 'PUT' ? delayed.promise : undefined
    await mount(); const editor = await chooseFile(); fireEvent.change(editor, { target: { value: 'submitted' } })
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save strategy' })); fireEvent.change(editor, { target: { value: 'newer draft' } })
    await act(async () => delayed.resolve({ ...file, content: 'submitted', revision: 'r2' }))
    expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('newer draft')
    expect((screen.getByRole('button', { name: 'Save strategy' }) as HTMLButtonElement).disabled).toBe(false)
  })
})
it('UI-E04: finishing an earlier file read does not mark a later pending read as ready', async () => {
  const first = deferred<typeof file>(), last = deferred<typeof file>()
  override = path => path === '/file?path=strategy.py' ? first.promise : path === '/file?path=folder%2FOther.py' ? last.promise : undefined
  await mount(); const user = userEvent.setup()
  await user.click(screen.getByTitle('strategy.py')); await user.click(screen.getByTitle('folder/Other.py'))
  await act(async () => first.resolve(file))
  expect((screen.getByRole('button', { name: 'Choose workspace directory' }) as HTMLButtonElement).disabled).toBe(true)
  await act(async () => last.resolve({ ...file, path: 'folder/Other.py' }))
  expect((screen.getByRole('button', { name: 'Choose workspace directory' }) as HTMLButtonElement).disabled).toBe(false)
})
it('UI-E05: an abandoned file read failure cannot show an error over the selected file', async () => {
  const first = deferred<typeof file>()
  override = path => path === '/file?path=strategy.py' ? first.promise : undefined
  await mount(); await userEvent.setup().click(screen.getByTitle('strategy.py')); await chooseFile('folder/Other.py')
  await act(async () => first.reject(Error('Old file missing')))
  expect(screen.queryByText('Old file missing')).toBeNull()
  expect((screen.getByRole('textbox', { name: 'Editor content' }) as HTMLTextAreaElement).value).toBe('original source')
})

async function openSettings() {
  await mount(); await chooseFile(); await userEvent.setup().click(screen.getByRole('button', { name: 'Strategy settings' }))
  return screen.findByRole('dialog', { name: 'Strategy settings' })
}
describe('presets, profiles and source settings', () => {
  it('UI-C01: saving a preset stores current values and settings without changing Python files', async () => {
    override = (path, options) => path === '/presets/research' && options?.method === 'PUT' ? {} : undefined
    await openSettings(); const user = userEvent.setup()
    const name = screen.getByRole('textbox', { name: 'Preset or data profile identifier' }); await user.clear(name); await user.type(name, 'research')
    await user.click(screen.getByRole('button', { name: 'Save preset' }))
    expect(api.request).toHaveBeenCalledWith('/presets/research', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ schemaVersion: 1, name: 'research', inputs: { schemaVersion: schema.schemaVersion, schemaHash: schema.schemaHash, values: {} }, settings: {} }) }))
    expect(vi.mocked(api.request).mock.calls.some(([path, options]) => path === '/file' && options?.method === 'PUT')).toBe(false)
  })
  it('UI-C02: loading a matching preset applies its execution properties and Defaults restores them', async () => {
    override = path => path === '/discover' ? { description: { ...schema, backtest: { settings: { cash: 10000 } } }, sourceHash: 'snapshot', sourceFiles: {} } : path === '/presets' ? { items: [{ id: 'saved', value: { schemaVersion: 1, name: 'Saved preset', inputs: { schemaVersion: schema.schemaVersion, schemaHash: schema.schemaHash, values: {} }, settings: { cash: 4321 } } }] } : undefined
    await openSettings(); const user = userEvent.setup()
    await user.click(screen.getByRole('combobox', { name: 'Load preset' })); await user.click(screen.getByRole('option', { name: 'Saved preset' }))
    await user.click(screen.getByRole('tab', { name: 'Properties' })); expect((screen.getByLabelText('Cash') as HTMLInputElement).value).toBe('4321')
    await user.click(screen.getByRole('button', { name: 'Defaults' })); expect((screen.getByLabelText('Cash') as HTMLInputElement).value).toBe('10000')
  })
  it('UI-C03: invalid loader JSON cannot be saved as a profile using stale last-valid parameters', async () => {
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Data' }))
    await user.click(screen.getByRole('combobox', { name: 'Data source' })); await user.click(screen.getByRole('option', { name: 'Local Python loader' }))
    fireEvent.change(screen.getByLabelText('Loader parameters (JSON object)'), { target: { value: '{' } })
    expect((screen.getByRole('button', { name: 'Save profile' }) as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Apply to next run' }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-C04: invalid required data numbers prevent both saving a profile and applying configuration', async () => {
    await openSettings(); await userEvent.setup().click(screen.getByRole('tab', { name: 'Data' }))
    fireEvent.change(screen.getByLabelText('Minimum notional'), { target: { value: '' } })
    expect((screen.getByRole('button', { name: 'Save profile' }) as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Apply to next run' }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-C05: saving a data profile uses its identifier and updated metadata', async () => {
    override = (path, options) => path === '/profiles/default' && options?.method === 'PUT' ? {} : undefined
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Data' }))
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'NEW' } }); await user.click(screen.getByRole('button', { name: 'Save profile' }))
    const call = vi.mocked(api.request).mock.calls.find(([path, options]) => path === '/profiles/default' && options?.method === 'PUT')!
    expect(JSON.parse(String(call[1]?.body))).toMatchObject({ name: 'default', instrument: { symbol: 'NEW' } })
  })
  it('UI-C06: preset save errors stay visible and preserve the configuration dialog', async () => {
    override = (path, options) => path.startsWith('/presets/') && options?.method === 'PUT' ? Promise.reject(Error('Preset cannot be written')) : undefined
    await openSettings(); await userEvent.setup().click(screen.getByRole('button', { name: 'Save preset' }))
    await screen.findByText('Preset cannot be written'); expect(screen.getByRole('dialog', { name: 'Strategy settings' })).toBeTruthy()
  })
  it('UI-C07: source roots and resources flow into the next run as trimmed arrays', async () => {
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Source' }))
    fireEvent.change(screen.getByLabelText('Source roots (comma separated)'), { target: { value: '., lib, ' } })
    fireEvent.change(screen.getByLabelText('Additional workspace resources'), { target: { value: ' data.csv, settings.json, ' } })
    await user.click(screen.getByRole('button', { name: 'Apply to next run' })); await user.click(screen.getByRole('button', { name: 'Run' }))
    await waitFor(() => expect(posts()).toHaveLength(1))
    expect(JSON.parse(String(posts()[0][1]?.body)).source).toMatchObject({ roots: ['.', 'lib'], resources: ['data.csv', 'settings.json'] })
  })
})
it('UI-C08: changing settings tabs preserves invalid loader JSON and keeps Apply blocked', async () => {
  await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Data' }))
  await user.click(screen.getByRole('combobox', { name: 'Data source' })); await user.click(screen.getByRole('option', { name: 'Local Python loader' }))
  fireEvent.change(screen.getByLabelText('Loader parameters (JSON object)'), { target: { value: '{unfinished' } })
  await user.click(screen.getByRole('tab', { name: 'Source' })); await user.click(screen.getByRole('tab', { name: 'Data' }))
  expect((screen.getByLabelText('Loader parameters (JSON object)') as HTMLTextAreaElement).value).toBe('{unfinished')
  expect((screen.getByRole('button', { name: 'Apply to next run' }) as HTMLButtonElement).disabled).toBe(true)
})

const exportLabels = ['Include Python source snapshot', 'Include normalized data snapshot', 'Include complete available logs']
describe('import, export and saved reruns', () => {
  it.each(Array.from({ length: 8 }, (_, mask) => mask))('UI-X01: export resource combination %i downloads exactly the selected options', async mask => {
    vi.spyOn(api, 'download').mockResolvedValue(new Blob(['archive']))
    URL.createObjectURL = vi.fn(() => 'blob:test'); URL.revokeObjectURL = vi.fn()
    const clicked = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { expect(this.download).toBe('run-a.obstudio') })
    await mount(); await screen.findByText('Total Pnl'); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Export result' }))
    for (let index = 0; index < exportLabels.length; index++) if (mask & (1 << index)) await user.click(screen.getByRole('checkbox', { name: exportLabels[index] }))
    await user.click(screen.getByRole('button', { name: 'Download .obstudio' }))
    expect(api.download).toHaveBeenCalledWith(`/runs/run-a/export?source=${!!(mask & 1)}&data=${!!(mask & 2)}&logs=${!!(mask & 4)}`)
    expect(clicked).toHaveBeenCalledOnce(); expect(screen.queryByRole('dialog')).toBeNull()
  })
  it('UI-X02: closing export does not download; failed download preserves options for retry', async () => {
    const download = vi.spyOn(api, 'download').mockRejectedValue(Error('Export unavailable'))
    await mount(); await screen.findByText('Total Pnl'); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Export result' })); await user.click(screen.getByRole('button', { name: 'Close' })); expect(download).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Export result' })); await user.click(screen.getByRole('checkbox', { name: exportLabels[2] })); await user.click(screen.getByRole('button', { name: 'Download .obstudio' }))
    await screen.findByText('Export unavailable'); expect(screen.getByRole('dialog', { name: 'Export this run' })).toBeTruthy()
    expect(screen.getByRole('checkbox', { name: exportLabels[2] }).getAttribute('aria-checked')).toBe('true')
    expect((screen.getByRole('button', { name: 'Download .obstudio' }) as HTMLButtonElement).disabled).toBe(false)
  })
  it.each([['report.json', 'application/json'], ['report.obstudio', 'application/octet-stream']])('UI-X03: importing %s sends the file and opens the saved result', async (name, contentType) => {
    override = (path, options) => path === '/imports' && options?.method === 'POST' ? (() => { const run = { id: 'imported', status: 'succeeded' }; runs.push(run); return run })() : undefined
    await mount(); const input = screen.getByLabelText('Import report file'), file = new File(['{}'], name)
    fireEvent.change(input, { target: { files: [file] } })
    await screen.findByRole('button', { name: /imported.*succeeded/ }); await waitFor(() => expect(screen.getByRole('main').textContent).toContain('Run imported'))
    expect(api.request).toHaveBeenCalledWith('/imports', { method: 'POST', body: file, headers: { 'Content-Type': contentType } })
    expect((input as HTMLInputElement).value).toBe('')
  })
  it('UI-X04: invalid imports show an error and the same file can be selected again without losing current results', async () => {
    override = path => path === '/imports' ? Promise.reject(Error('Archive checksum mismatch')) : undefined
    await mount(); await screen.findByText('Total Pnl'); const input = screen.getByLabelText('Import report file'), file = new File(['bad'], 'bad.obstudio')
    for (let count = 0; count < 2; count++) {
      fireEvent.change(input, { target: { files: [file] } }); await screen.findByText('Archive checksum mismatch')
      expect(screen.getByText('Total Pnl')).toBeTruthy(); expect((input as HTMLInputElement).value).toBe('')
    }
    expect(vi.mocked(api.request).mock.calls.filter(([path]) => path === '/imports')).toHaveLength(2)
  })
  it('UI-X05: snapshot rerun uses only the selected saved run and leaves dirty source untouched', async () => {
    runs[0].request = { source: { path: 'strategy.py', revision: 'r1' }, inputs: { values: {} }, settings: {}, data: {} }
    override = path => path === '/runs/run-a/rerun' ? (() => { const run = { id: 'rerun', status: 'succeeded' }; runs.push(run); return run })() : undefined
    await mount(); fireEvent.change(await chooseFile(), { target: { value: 'unsaved local change' } })
    await userEvent.setup().click(screen.getByRole('button', { name: 'Rerun saved snapshot' }))
    await screen.findByRole('button', { name: /rerun.*succeeded/ })
    expect(api.request).toHaveBeenCalledWith('/runs/run-a/rerun', { method: 'POST' })
    expect(vi.mocked(api.request).mock.calls.some(([path, options]) => path === '/file' && options?.method === 'PUT' || path === '/discover')).toBe(false)
    await userEvent.setup().click(screen.getByRole('tab', { name: 'Code' })); expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('unsaved local change')
  })
  it('UI-X06: readonly reports expose export and report controls without execution or source editing', async () => {
    override = path => path === '/capabilities' ? { ...caps, mode: 'view', workspace: null, capabilities: { edit: false, discover: false } } : undefined
    render(<App />); await screen.findByText('Total Pnl')
    for (const name of ['Import result', 'Run', 'Save strategy', 'Strategy settings', 'Choose workspace directory', 'Rerun saved snapshot']) expect(screen.queryByRole('button', { name })).toBeNull()
    expect(screen.queryByRole('tab', { name: 'Code' })).toBeNull(); expect(screen.getByRole('button', { name: 'Export result' })).toBeTruthy()
    expect(screen.getByRole('contentinfo').textContent).toContain('Read-only report · no source execution')
  })
})

async function withFilePolling() {
  const timers = vi.spyOn(globalThis, 'setInterval'); await mount(); await chooseFile()
  return timers.mock.calls.find(([, delay]) => delay === 2000)![0] as () => Promise<void>
}
describe('external file changes', () => {
  it('UI-E06: a clean buffer reloads external disk changes automatically', async () => {
    const poll = await withFilePolling(); source = { ...file, content: 'new disk content', revision: 'r2' }
    await act(poll); expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('new disk content')
    expect(screen.queryByRole('button', { name: 'Review conflict' })).toBeNull()
  })
  it('UI-E07: conflict review can discard the draft and reload the changed disk version', async () => {
    const poll = await withFilePolling(); fireEvent.change(screen.getByLabelText('Editor content'), { target: { value: 'my draft' } }); source = { ...file, content: 'changed disk', revision: 'r2' }
    await act(poll); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Review conflict' })); expect((screen.getByLabelText('Diff content') as HTMLTextAreaElement).value).toBe('my draft')
    await user.click(screen.getByRole('button', { name: 'Reload disk and discard draft' }))
    expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('changed disk')
    expect((screen.getByRole('button', { name: 'Save strategy' }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-E08: keeping the draft uses the new disk revision for the next save', async () => {
    const poll = await withFilePolling(); fireEvent.change(screen.getByLabelText('Editor content'), { target: { value: 'my draft' } }); source = { ...file, content: 'changed disk', revision: 'r2' }
    await act(poll); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Review conflict' })); await user.click(screen.getByRole('button', { name: 'Keep draft for manual merge' })); await user.click(screen.getByRole('button', { name: 'Save strategy' }))
    expect(api.request).toHaveBeenCalledWith('/file', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ path: 'strategy.py', baseRevision: 'r2', content: 'my draft' }) }))
  })
  it('UI-E09: deleted files preserve drafts while disabling save and run', async () => {
    const poll = await withFilePolling(); fireEvent.change(screen.getByLabelText('Editor content'), { target: { value: 'my draft' } }); files = []
    await act(poll)
    expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('my draft')
    for (const name of ['Save strategy', 'Save & Run', 'Review conflict']) expect((screen.getByRole('button', { name }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('UI-E10: a polling read started before save cannot revert the newly saved revision', async () => {
    const poll = await withFilePolling(), stale = deferred<typeof file>(); fireEvent.change(screen.getByLabelText('Editor content'), { target: { value: 'saved edit' } })
    override = path => path === '/file?path=strategy.py' ? stale.promise : undefined
    let polling: Promise<void>; await act(async () => { polling = poll(); await Promise.resolve() })
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save strategy' }))
    await act(async () => { stale.resolve(file); await polling! })
    expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('saved edit')
    expect(screen.queryByRole('button', { name: 'Review conflict' })).toBeNull()
  })
})
it('UI-E11: restoring a deleted file clears the conflict and enables saving its preserved draft', async () => {
  const poll = await withFilePolling(); fireEvent.change(screen.getByLabelText('Editor content'), { target: { value: 'my draft' } }); files = []
  await act(poll); files = ['strategy.py']; await act(poll)
  expect(screen.queryByRole('button', { name: 'Review conflict' })).toBeNull()
  expect((screen.getByRole('button', { name: 'Save strategy' }) as HTMLButtonElement).disabled).toBe(false)
  expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('my draft')
})
it('UI-E12: editor save shortcuts cannot submit duplicate writes while a save is in flight', async () => {
  const saving = deferred<typeof file>(); override = (path, options) => path === '/file' && options?.method === 'PUT' ? saving.promise : undefined
  await mount(); const editor = await chooseFile(); fireEvent.change(editor, { target: { value: 'draft' } })
  fireEvent.keyDown(editor, { key: 's', metaKey: true }); fireEvent.keyDown(editor, { key: 's', ctrlKey: true })
  expect(vi.mocked(api.request).mock.calls.filter(([path, options]) => path === '/file' && options?.method === 'PUT')).toHaveLength(1)
  await act(async () => saving.resolve({ ...file, content: 'draft', revision: 'r2' }))
})

const chartPage = (start = 0, end = 5000, total = 12000) => ({ plotting, window: { start, end, total, granularity: 1 } })
describe('chart windows and event selection', () => {
  it('UI-G01: Earlier, Later and All bars load the requested saved intervals', async () => {
    override = path => path.endsWith('/chart') ? chartPage(5000, 10000) : path.includes('/chart?') ? (() => { const query = new URLSearchParams(path.split('?')[1]), start = Number(query.get('start')); return chartPage(start, query.has('end') ? Number(query.get('end')) : Math.min(12000, start + 5000)) })() : undefined
    await mount(); const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Earlier' })); await screen.findByText('1–5000 / 12000')
    expect((screen.getByRole('button', { name: 'Earlier' }) as HTMLButtonElement).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Later' })); await screen.findByText('5001–10000 / 12000')
    await user.click(screen.getByRole('button', { name: 'All bars' })); await screen.findByText('1–12000 / 12000')
    expect((screen.getByRole('button', { name: 'Later' }) as HTMLButtonElement).disabled).toBe(true)
    expect(api.request).toHaveBeenCalledWith('/runs/run-a/chart?start=0&end=12000', expect.anything())
  })
  it('UI-G02: a failed chart window read keeps the old chart and offers an exact-window retry', async () => {
    let failed = true
    override = path => path.endsWith('/chart') ? chartPage() : path.includes('/chart?') ? failed ? Promise.reject(Error('Window unavailable')) : chartPage(5000, 10000) : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Later' }))
    await screen.findByText('Window unavailable'); expect(screen.getByLabelText('Test market chart')).toBeTruthy()
    failed = false; await user.click(screen.getByRole('button', { name: 'Retry chart window' })); await screen.findByText('5001–10000 / 12000')
    expect(screen.queryByText('Window unavailable')).toBeNull()
  })
  it('UI-G03: a window request cannot overwrite a different run selected while it was pending', async () => {
    const delayed = deferred<ReturnType<typeof chartPage>>()
    override = path => path === '/runs/run-a/chart' ? chartPage() : path.includes('/runs/run-a/chart?') ? delayed.promise : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Later' })); await user.click(screen.getByRole('button', { name: /run-b.*succeeded/ }))
    await act(async () => delayed.resolve(chartPage(5000, 10000))); await screen.findByText('1–4 / 4')
    expect(screen.queryByText('5001–10000 / 12000')).toBeNull()
  })
  it('UI-G04: failed initial chart reads retry without rerunning the strategy or losing the report', async () => {
    let failed = true; override = path => path === '/runs/run-a/chart' && failed ? Promise.reject(Error('Chart unavailable temporarily')) : undefined
    render(<App />); await screen.findByText('Chart unavailable temporarily'); await screen.findByText('Total Pnl'); failed = false
    await userEvent.setup().click(screen.getByRole('button', { name: 'Retry chart' })); await screen.findByLabelText('Test market chart'); expect(posts()).toHaveLength(0)
  })
  it('UI-G05: a failed summary can be retried while its chart stays available', async () => {
    let failed = true; override = path => path === '/runs/run-a/summary' && failed ? Promise.reject(Error('Summary unavailable')) : undefined
    await mount(); await screen.findByText('Report unavailable: Summary unavailable'); failed = false
    await userEvent.setup().click(screen.getByRole('button', { name: 'Retry saved report' })); await screen.findByText('Total Pnl'); expect(posts()).toHaveLength(0)
  })
  it('UI-G06: selecting a fill opens trades and Clear fill selection removes chart highlighting', async () => {
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Select fill bar' }))
    await user.click(screen.getByRole('button', { name: /fill-test.*buy/ })); expect(screen.getByRole('tab', { name: 'List of trades' }).getAttribute('aria-selected')).toBe('true')
    expect(screen.getByLabelText('Test market chart').textContent).toContain('selected:fill-test')
    await user.click(screen.getByRole('button', { name: 'Clear fill selection' })); expect(screen.getByLabelText('Test market chart').textContent).toContain('selected:none')
  })
  it('UI-G07: event cluster members paginate and locate the original fill', async () => {
    override = path => path.includes('/events?') ? { rows: [{ kind: 'fill', value: { fill_id: path.includes('offset=100') ? 'last-fill' : 'first-fill', bar_index: 5100 } }], total: 150, offset: path.includes('offset=100') ? 100 : 0 } : path.includes('/chart?') ? chartPage(2600, 7600) : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Select cluster 0' })); await screen.findByText(/first-fill/)
    await user.click(screen.getByRole('button', { name: 'Next members' })); await screen.findByText(/last-fill/)
    expect((screen.getByRole('button', { name: 'Next members' }) as HTMLButtonElement).disabled).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Previous members' })); await screen.findByText(/first-fill/)
    await user.click(screen.getByRole('button', { name: 'Locate original fill' })); await screen.findByText('2601–7600 / 12000'); expect(screen.queryByRole('dialog')).toBeNull()
  })
  it('UI-G08: changing clusters hides old members until the new request completes', async () => {
    const delayed = deferred<{ rows: { kind: string; value: object }[]; total: number; offset: number }>()
    override = path => path.includes('/events?start=0&') ? { rows: [{ kind: 'signal', value: { id: 'old-member' } }], total: 1, offset: 0 } : path.includes('/events?start=100&') ? delayed.promise : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Select cluster 0' })); await screen.findByText(/old-member/); await user.click(screen.getByRole('button', { name: 'Close' }))
    await user.click(screen.getByRole('button', { name: 'Select cluster 100' })); expect(screen.queryByText(/old-member/)).toBeNull()
    await act(async () => delayed.resolve({ rows: [{ kind: 'signal', value: { id: 'new-member' } }], total: 1, offset: 0 })); await screen.findByText(/new-member/)
  })
  it('UI-G09: failed cluster reads show a retry within the dialog', async () => {
    let failed = true; override = path => path.includes('/events?') ? failed ? Promise.reject(Error('Members unavailable')) : { rows: [], total: 0, offset: 0 } : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Select cluster 0' })); await screen.findByText('Members unavailable'); failed = false
    await user.click(screen.getByRole('button', { name: 'Retry cluster members' })); await screen.findByText('No events in this cluster.')
  })
})

describe('chart picking and parameter schema review', () => {
  const discovery = { description: inputFixture, sourceHash: 'inputs-snapshot', sourceFiles: {} }
  it.each([['Reference price', '123'], ['Highlight start', '1970-01-01T00:00:01.000']])('UI-G10: selecting the chart updates %s without executing a strategy', async (title, expected) => {
    override = path => path === '/discover' ? discovery : undefined
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: `Pick ${title} on chart` }))
    expect(screen.queryByRole('dialog', { name: 'Strategy settings' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Select empty bar' })); const control = screen.getByLabelText(title) as HTMLInputElement
    if (title === 'Highlight start') expect(new Date(control.value + 'Z').getTime()).toBe(1000)
    else expect(control.value).toBe(expected)
    expect(posts()).toHaveLength(0)
  })
  it.each(['button', 'Escape'])('UI-G11: cancelling chart picking by %s preserves the previous parameter', async method => {
    override = path => path === '/discover' ? discovery : undefined
    await openSettings(); const user = userEvent.setup(); fireEvent.change(screen.getByLabelText('Reference price'), { target: { value: '321' } })
    await user.click(screen.getByRole('button', { name: 'Pick Reference price on chart' }))
    if (method === 'button') await user.click(screen.getByRole('button', { name: 'Cancel pick' })); else await user.keyboard('{Escape}')
    expect((screen.getByLabelText('Reference price') as HTMLInputElement).value).toBe('321'); expect(posts()).toHaveLength(0)
  })
  it('UI-G12: incompatible points keep pick mode available; a later valid pick clears the error', async () => {
    override = path => path === '/discover' ? discovery : undefined
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Pick Reference price on chart' })); await user.click(screen.getByRole('button', { name: 'Select invalid pick' }))
    await screen.findByText('The chart position has no compatible price or UTC time'); expect(screen.getByRole('button', { name: 'Cancel pick' })).toBeTruthy()
    await user.click(screen.getByRole('button', { name: 'Select empty bar' })); expect((screen.getByLabelText('Reference price') as HTMLInputElement).value).toBe('123')
    expect(screen.queryByText('The chart position has no compatible price or UTC time')).toBeNull()
  })
  it('UI-C09: cancelling an incompatible preset does not apply its properties', async () => {
    override = path => path === '/discover' ? discovery : path === '/presets' ? { items: [{ id: 'old', value: { name: 'Old schema', inputs: { schemaHash: 'old', values: {} }, settings: { cash: 4321 } } }] } : undefined
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('combobox', { name: 'Load preset' })); await user.click(screen.getByRole('option', { name: 'Old schema' }))
    await screen.findByRole('dialog', { name: 'Review parameter schema' }); await user.click(screen.getByRole('button', { name: 'Cancel' })); await user.click(screen.getByRole('tab', { name: 'Properties' }))
    expect((screen.getByLabelText('Cash') as HTMLInputElement).value).toBe(String(inputFixture.backtest.settings.cash))
  })
  it('UI-C10: reviewing an incompatible preset retains valid inputs and resets invalid ones before Apply', async () => {
    override = path => path === '/discover' ? discovery : path === '/presets' ? { items: [{ id: 'old', value: { name: 'Old schema', inputs: { schemaHash: 'old', values: { 'Reference price': 222, 'Moving-average period': 999 } }, settings: { cash: 4321 } } }] } : undefined
    await openSettings(); const user = userEvent.setup(); await user.click(screen.getByRole('combobox', { name: 'Load preset' })); await user.click(screen.getByRole('option', { name: 'Old schema' }))
    await screen.findByText('Moving-average period: Maximum 100'); await user.click(screen.getByRole('button', { name: 'Review inputs' }))
    expect((screen.getByLabelText('Reference price') as HTMLInputElement).value).toBe('222'); expect((screen.getByLabelText('Moving-average period') as HTMLInputElement).value).toBe('20')
    await user.click(screen.getByRole('tab', { name: 'Properties' })); expect((screen.getByLabelText('Cash') as HTMLInputElement).value).toBe('4321'); expect(posts()).toHaveLength(0)
  })
})
it('UI-S06: invalid properties disable Apply and Save preset across tabs and block Run', async () => {
  override = path => path === '/discover' ? { description: inputFixture, sourceHash: 'snapshot', sourceFiles: {} } : undefined
  await openSettings(); const user = userEvent.setup()
  await user.click(screen.getByRole('tab', { name: 'Properties' })); const field = screen.getByLabelText('Commission value') as HTMLInputElement
  await user.clear(field); await user.type(field, '0.'); await user.click(screen.getByRole('tab', { name: 'Inputs' })); await user.click(screen.getByRole('tab', { name: 'Properties' })); expect(field.value).toBe('0.')
  await user.clear(field); expect((screen.getByRole('button', { name: 'Apply to next run' }) as HTMLButtonElement).disabled).toBe(true)
  expect((screen.getByRole('button', { name: 'Save preset' }) as HTMLButtonElement).disabled).toBe(true)
  await user.click(screen.getByRole('button', { name: 'Close' })); await user.click(screen.getByRole('button', { name: /^Run$/ })); await screen.findByText('Correct the execution properties before running'); expect(posts()).toHaveLength(0)
})

it('UI-G20: missing chart data disables layer toggles while retaining report and retry controls', async () => {
  override = path => path.endsWith('/chart') ? Promise.reject(Error('No chart data')) : undefined
  render(<App />); await screen.findByText('No chart data'); await screen.findByText('Total Pnl')
  for (const name of ['Signals', 'Fills']) expect((screen.getByRole('checkbox', { name }) as HTMLButtonElement).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Retry chart' })).toBeTruthy()
})

it.each(['failed', 'cancelled', 'running', 'queued'])('UI-A18: selecting %s history uses its own run identity and never displays another result', async status => {
  runs.push({ id: 'other-run', status, error: { message: 'own-run-diagnostic' } }); await mount()
  await userEvent.setup().click(screen.getByRole('button', { name: new RegExp(`other-run.*${status}`) }))
  expect(screen.getByText('Run other-ru')).toBeTruthy()
  expect(screen.getByText(`Run ${status}; no completed chart`)).toBeTruthy()
  expect(screen.queryByLabelText('Test market chart')).toBeNull(); expect(screen.queryByText('Total Pnl')).toBeNull()
  expect(screen.getByText(/own-run-diagnostic/)).toBeTruthy()
  expect(vi.mocked(api.request).mock.calls.some(([url]) => url === '/runs/other-run/summary')).toBe(false)
})
it('UI-A19: a failed cancel preserves the operation for retry', async () => {
  let fail = true; runs.push({ id: 'slow-run', status: 'running' })
  override = path => path.endsWith('/cancel') && fail ? Promise.reject(Error('Cancellation unavailable')) : undefined
  await mount(); const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: 'Cancel run slow-run' })); await screen.findByText('Cancellation unavailable')
  fail = false; await user.click(screen.getByRole('button', { name: 'Cancel run slow-run' })); await screen.findByRole('button', { name: /slow-run.*cancelled/ })
})

it('UI-A20: resizing persists the two-panel layout and collapse cannot overwrite that preference', async () => {
  localStorage.setItem('studio.layout', JSON.stringify({ chart: 70, bottom: 30 })); await mount()
  expect(screen.getByTestId('layout').getAttribute('data-layout')).toBe(JSON.stringify({ chart: 70, bottom: 30 }))
  const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Resize panels' }))
  expect(JSON.parse(localStorage.getItem('studio.layout')!)).toEqual({ chart: 65, bottom: 35 })
  await user.click(screen.getByRole('button', { name: 'Collapse layout notification' }))
  expect(JSON.parse(localStorage.getItem('studio.layout')!)).toEqual({ chart: 65, bottom: 35 })
})
it('UI-A21: selected running history changes to its saved result when polling reports success', async () => {
  const intervals = vi.spyOn(globalThis, 'setInterval'); runs.push({ id: 'live-run', status: 'running' }); await mount()
  await userEvent.setup().click(screen.getByRole('button', { name: /live-run.*running/ })); expect(screen.getByText('Run running; no completed chart')).toBeTruthy()
  runs = runs.map(run => run.id === 'live-run' ? { ...run, status: 'succeeded' } : run)
  const poll = intervals.mock.calls.find(([, delay]) => delay === 2000)![0] as () => Promise<void>
  await act(async () => poll()); await screen.findByLabelText('Test market chart')
  await userEvent.setup().click(screen.getByRole('tab', { name: 'Overview' })); await screen.findByText('Total Pnl')
  expect(screen.queryByText('Run running; no completed chart')).toBeNull()
})
it.each(['All bars', 'another run'])('UI-G21: %s supersedes pending viewport refinement', async action => {
  override = path => path.endsWith('/chart') || path.includes('/chart?') ? { plotting, window: { start: 0, end: 12000, total: 12000, granularity: 3 } } : undefined
  await mount(); vi.useFakeTimers()
  try {
    fireEvent.click(screen.getByRole('button', { name: 'Zoom to viewport' }))
    fireEvent.click(screen.getByRole('button', { name: action === 'All bars' ? 'All bars' : /run-b.*succeeded/ }))
    await act(async () => { await vi.advanceTimersByTimeAsync(200) })
    expect(vi.mocked(api.request).mock.calls.some(([path]) => path.includes('start=10&end=101'))).toBe(false)
  } finally { vi.useRealTimers() }
})
it('UI-G22: a user viewport gesture loads the precise original bar interval after debounce', async () => {
  override = path => path.endsWith('/chart') || path.includes('/chart?') ? { plotting, window: { start: 0, end: 12000, total: 12000, granularity: 3 } } : undefined
  await mount(); vi.useFakeTimers()
  try {
    fireEvent.click(screen.getByRole('button', { name: 'Zoom to viewport' }))
    await act(async () => { await vi.advanceTimersByTimeAsync(150) })
    expect(api.request).toHaveBeenCalledWith('/runs/run-a/chart?start=10&end=101', expect.anything())
  } finally { vi.useRealTimers() }
})
it('UI-A22: chart attribution is an explicit external link with no opener access', async () => {
  await mount(); const link = screen.getByRole('link', { name: 'Charts by TradingView' })
  expect(link.getAttribute('href')).toBe('https://www.tradingview.com/'); expect(link.getAttribute('rel')).toBe('noreferrer')
})

describe('results panel placement', () => {
  it('UI-DOCK01: toggles bottom/right without remounting the chart or editor and persists placement', async () => {
    await mount(); const user = userEvent.setup(), editor = await chooseFile()
    fireEvent.change(editor, { target: { value: 'unsaved draft' } })
    const chart = screen.getByLabelText('Test market chart'), initialPosts = posts().length
    expect(screen.getByTestId('layout').dataset.orientation).toBe('vertical')
    await user.click(screen.getByRole('button', { name: 'Move results to right' }))
    expect(screen.getByTestId('layout').dataset.orientation).toBe('horizontal')
    expect(screen.getByLabelText('Test market chart')).toBe(chart)
    expect(screen.getByRole('textbox', { name: 'Editor content' })).toBe(editor)
    expect((editor as HTMLTextAreaElement).value).toBe('unsaved draft')
    expect(localStorage.getItem('studio.resultsDock')).toBe('right')
    await user.click(screen.getByRole('button', { name: 'Resize panels' }))
    expect(JSON.parse(localStorage.getItem('studio.layout')!)).toEqual({ chart: 65, bottom: 35 })
    await user.click(screen.getByRole('button', { name: 'Move results to bottom' }))
    expect(screen.getByTestId('layout').dataset.orientation).toBe('vertical')
    expect(screen.getByLabelText('Test market chart')).toBe(chart)
    expect(screen.getByRole('textbox', { name: 'Editor content' })).toBe(editor)
    expect(localStorage.getItem('studio.resultsDock')).toBe('bottom')
    expect(posts()).toHaveLength(initialPosts)
  })
  it.each(['bottom', 'right'])('UI-DOCK02: restores %s placement and size, with collapse/reopen and resize available', async dock => {
    localStorage.setItem('studio.resultsDock', dock)
    localStorage.setItem('studio.layout', JSON.stringify({ chart: 70, bottom: 30 }))
    await mount(); const user = userEvent.setup()
    const orientation = dock === 'right' ? 'horizontal' : 'vertical'
    expect(screen.getByTestId('layout').dataset.orientation).toBe(orientation)
    expect(JSON.parse(screen.getByTestId('layout').dataset.layout!)).toEqual({ chart: 70, bottom: 30 })
    expect(screen.getByRole('separator')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: 'Collapse results panel' }))
    expect(screen.queryByRole('separator')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Collapse layout notification' }))
    expect(JSON.parse(localStorage.getItem('studio.layout')!)).toEqual({ chart: 70, bottom: 30 })
    await user.click(screen.getByRole('button', { name: 'Show results & code' }))
    expect(screen.getByRole('separator')).toBeTruthy()
    expect(screen.getByTestId('layout').dataset.orientation).toBe(orientation)
    await user.click(screen.getByRole('button', { name: 'Resize panels' }))
    expect(JSON.parse(localStorage.getItem('studio.layout')!)).toEqual({ chart: 65, bottom: 35 })
  })
  it('UI-DOCK03: malformed placement falls back to bottom and read-only reports can also switch', async () => {
    localStorage.setItem('studio.resultsDock', 'invalid')
    override = path => path === '/capabilities' ? { ...caps, mode: 'view', capabilities: { edit: false, discover: false } } : undefined
    render(<App />); await screen.findByLabelText('Test market chart')
    expect(screen.getByTestId('layout').dataset.orientation).toBe('vertical')
    await userEvent.setup().click(screen.getByRole('button', { name: 'Move results to right' }))
    expect(screen.getByTestId('layout').dataset.orientation).toBe('horizontal')
    expect(screen.getByText('Total Pnl')).toBeTruthy()
  })
})

describe('optimizer application integration', () => {
  const optimizerSchema = { ...schema, inputs: [{ title: 'Length', attribute: 'length', kind: 'int', default: 1, active: true, display: 'all', confirm: false, group: '', inline: '', tooltip: '' }] }
  const planned = { id: 'experiment', status: 'planned', source: 'strategy.py', plan: { total: 1, dimensions: [{ title: 'Length', values: [1] }], inputs: { schemaHash: 'one', values: { Length: 1 } }, execution: { backtest: { settings: {} } } } }
  it('UI-OA01: Optimizer follows Code, previews saved current code, persists drafts across tabs and does not submit a run', async () => {
    override = (path, options) => path === '/discover' ? { description: optimizerSchema, sourceHash: 'snapshot', sourceFiles: {} } : path === '/optimizations' ? options?.method === 'POST' ? planned : { items: [] } : path === '/optimizations/experiment' ? planned : undefined
    await mount(); const user = userEvent.setup(), tabs = screen.getAllByRole('tab').map(tab => tab.textContent)
    expect(tabs[tabs.indexOf('Code') + 1]).toBe('Optimizer')
    const editor = await chooseFile(); await user.click(screen.getByRole('button', { name: 'Strategy settings' })); await screen.findByRole('dialog'); await user.click(screen.getByRole('button', { name: 'Apply to next run' }))
    fireEvent.change(editor, { target: { value: 'edited optimizer source' } })
    await user.click(screen.getByRole('tab', { name: 'Optimizer' })); await user.click(screen.getByRole('checkbox', { name: 'Length' }))
    await user.click(screen.getByRole('tab', { name: 'Code' })); await user.click(screen.getByRole('tab', { name: 'Optimizer' }))
    expect(screen.getByRole('checkbox', { name: 'Length' }).getAttribute('aria-checked')).toBe('true')
    await user.click(screen.getByRole('button', { name: 'Preview search' })); await screen.findByRole('button', { name: 'Start experiment' })
    const call = vi.mocked(api.request).mock.calls.find(([path, options]) => path === '/optimizations' && options?.method === 'POST')!
    const request = JSON.parse(String(call[1]!.body))
    expect(source.content).toBe('edited optimizer source'); expect(request.run.source.revision).toBe('r2'); expect(request.search).toEqual({ Length: { kind: 'values', values: [1] } }); expect(posts()).toHaveLength(0)
  })
  it('UI-OA02: preparation blocks file switching until the captured request is submitted', async () => {
    const pending = deferred<typeof planned>()
    override = (path, options) => path === '/discover' ? { description: optimizerSchema, sourceHash: 'snapshot', sourceFiles: {} } : path === '/optimizations' ? options?.method === 'POST' ? pending.promise : { items: [] } : undefined
    await mount(); const user = userEvent.setup(); await chooseFile(); await user.click(screen.getByRole('button', { name: 'Strategy settings' })); await screen.findByRole('dialog'); await user.click(screen.getByRole('button', { name: 'Apply to next run' }))
    await user.click(screen.getByRole('tab', { name: 'Optimizer' })); await user.click(screen.getByRole('checkbox', { name: 'Length' })); await user.click(screen.getByRole('button', { name: 'Preview search' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Choose workspace directory' }).hasAttribute('disabled')).toBe(true))
    expect(screen.getByRole('button', { name: /^Run$/ }).hasAttribute('disabled')).toBe(true)
    await act(async () => pending.resolve(planned)); await screen.findByRole('button', { name: 'Start experiment' })
  })
  it('UI-LA01: a log bar action reads a bounded saved chart window without executing a strategy', async () => {
    override = path => path === '/runs/run-a/logs' ? { logs: { records: [{ message: 'signal here', level: 'info', bar_index: 2 }] } } : undefined
    await mount(); const user = userEvent.setup(); await user.click(screen.getByRole('tab', { name: 'Logs' })); await user.click(await screen.findByRole('button', { name: 'Scroll to bar 2' }))
    await waitFor(() => expect(vi.mocked(api.request).mock.calls.some(([path]) => path.includes('/runs/run-a/chart?start=0&end=4'))).toBe(true))
    expect(posts()).toHaveLength(0)
  })
})
