// @vitest-environment jsdom
import '@/test/dom'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { deferred } from '@/test/dom'
import { api } from '@/protocol/client'
import { LogPanel } from './LogPanel'
vi.mock('./CodeEditor', () => ({ default: ({ value, readonly, line }: { value: string; readonly: boolean; line: number }) => <textarea aria-label={`Source at line ${line}`} readOnly={readonly} value={value} /> }))
const frames = [{ workspacePath: 'first.py', line: 2 }, { workspacePath: 'second.py', line: 7 }]
const source = (path: string) => ({ path, content: `saved ${path}`, revision: 'snapshot', currentMatches: false })
let respond: (url: string) => unknown
beforeEach(() => { respond = url => source(new URLSearchParams(url.split('?')[1]).get('path')!); vi.spyOn(api, 'request').mockImplementation(async <T,>(url: string) => await respond(url) as T) })
it('UI-L01: snapshot link reads the logged run, displays its saved line read-only and closes', async () => {
  render(<LogPanel value={{ runId: 'failure-run', frames }} runId="selected-success" dark={false} />)
  const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Snapshot: second.py:7' }))
  const editor = await screen.findByRole('textbox', { name: 'Source at line 7' }) as HTMLTextAreaElement
  expect(editor.value).toBe('saved second.py'); expect(editor.readOnly).toBe(true)
  expect(api.request).toHaveBeenCalledWith('/runs/failure-run/source?path=second.py', expect.anything())
  expect(screen.getByText(/Historical version/)).toBeTruthy(); await user.click(screen.getByRole('button', { name: 'Close' })); expect(screen.queryByRole('dialog')).toBeNull()
})
it('UI-L02: a late source response from a previous run cannot open under the new run title', async () => {
  const pending = deferred<ReturnType<typeof source>>(); respond = () => pending.promise
  const mounted = render(<LogPanel value={{ frames }} runId="run-a" dark={false} />)
  await userEvent.setup().click(screen.getByRole('button', { name: 'Snapshot: first.py:2' }))
  mounted.rerender(<LogPanel value={{ frames }} runId="run-b" dark={false} />)
  await act(async () => pending.resolve(source('first.py')))
  expect(screen.queryByRole('dialog')).toBeNull(); expect(screen.queryByDisplayValue('saved first.py')).toBeNull()
})
it('UI-L03: source fetch failures are actionable and retry restores the saved source', async () => {
  let failed = true; respond = () => failed ? Promise.reject(Error('Source unavailable')) : source('first.py')
  render(<LogPanel value={{ frames }} runId="run-a" dark={false} />)
  const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Snapshot: first.py:2' })); await screen.findByText('Source unavailable')
  failed = false; await user.click(screen.getByRole('button', { name: 'Retry source' })); await screen.findByDisplayValue('saved first.py'); expect(screen.queryByText('Source unavailable')).toBeNull()
})
it('UI-L04: closing while source is loading prevents a delayed response from reopening the dialog', async () => {
  const pending = deferred<ReturnType<typeof source>>(); respond = () => pending.promise
  render(<LogPanel value={{ frames }} runId="run-a" dark={false} />)
  const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Snapshot: first.py:2' })); await user.click(screen.getByRole('button', { name: 'Close' }))
  await act(async () => pending.resolve(source('first.py'))); expect(screen.queryByRole('dialog')).toBeNull()
})

const messages = { logs: { truncated: true, records: [
  { sequence: 1, level: 'info', message: 'A multiline\nmessage <script>unsafe()</script>', bar_index: 7, bar_time: '2024-01-01T00:00:00+00:00', time_kind: 'aware', source: { workspacePath: 'first.py', line: 2 } },
  { sequence: 2, level: 'warning', message: 'Risk warning', bar_index: 8, bar_time: '2024-01-02T00:00:00', time_kind: 'naive' },
  { sequence: 3, level: 'error', message: 'Order rejected', bar_index: null, recorded_at: '2024-01-03T01:00:00Z' },
] }, stdout: { text: 'printed output\n', truncated: false }, stderr: { text: 'library diagnostic\n', truncated: false } }
it('UI-L05: renders readable messages, timezone timestamps, severities and truncation without a JSON dump', () => {
  render(<LogPanel value={messages} runId="run-a" dark={false} timezone="Asia/Shanghai" />)
  expect(screen.getByText('2024-01-01T08:00:00')).toBeTruthy()
  expect(screen.getByText('2024-01-02T00:00:00')).toBeTruthy()
  expect(screen.getByText(/A multiline/).textContent).toBe('A multiline\nmessage <script>unsafe()</script>')
  expect(document.querySelector('script')).toBeNull()
  expect(screen.getByText('printed output')).toBeTruthy(); expect(screen.getByText('library diagnostic')).toBeTruthy()
  expect(screen.getByRole('status').textContent).toContain('truncated')
  expect(screen.queryByText(/"records":/)).toBeNull()
})
it('UI-L06: level, search, source and start-date filters combine and Reset restores messages', async () => {
  render(<LogPanel value={messages} runId="run-a" dark={false} />); const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: 'Show info logs' }))
  expect(screen.queryByText('printed output')).toBeNull(); expect(screen.getByText('Risk warning')).toBeTruthy()
  await user.type(screen.getByRole('textbox', { name: 'Search logs' }), 'REJECTED')
  expect(screen.queryByText('Risk warning')).toBeNull(); expect(screen.getByText('Order rejected')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Reset log filters' }))
  await user.click(screen.getByRole('combobox', { name: 'Log source' })); await user.click(screen.getByRole('option', { name: 'stdout' }))
  expect(screen.getAllByRole('listitem')).toHaveLength(1)
  await user.click(screen.getByRole('button', { name: 'Reset log filters' }))
  const input = screen.getByLabelText('Logs from date and time')
  const { fireEvent } = await import('@testing-library/react')
  fireEvent.change(input, { target: { value: '2024-01-03T00:00' } })
  expect(screen.getAllByRole('listitem')).toHaveLength(1); expect(screen.getByText('Order rejected')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Reset log filters' })); expect(screen.getAllByRole('listitem')).toHaveLength(5)
})
it('UI-L07: per-message actions open frozen source and locate the original bar without running code', async () => {
  const onBar = vi.fn(); render(<LogPanel value={messages} runId="run-a" dark={false} onBar={onBar} />)
  const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: 'Scroll to bar 7' }))
  expect(onBar).toHaveBeenCalledExactlyOnceWith(7)
  await user.click(screen.getByRole('button', { name: 'Source code: first.py:2' }))
  await screen.findByDisplayValue('saved first.py')
  expect(vi.mocked(api.request).mock.calls.every(([url]) => url.includes('/source?'))).toBe(true)
})
it('UI-L08: absent charts disable bar navigation; empty and zero-match states are explicit', async () => {
  const { rerender } = render(<LogPanel value={null} runId="run-a" dark={false} />)
  expect(screen.getByText('No logs were included with this report.')).toBeTruthy()
  rerender(<LogPanel value={messages} runId="run-a" dark={false} />)
  expect((screen.getByRole('button', { name: 'Scroll to bar 7' }) as HTMLButtonElement).disabled).toBe(true)
  await userEvent.setup().type(screen.getByRole('textbox', { name: 'Search logs' }), 'missing text')
  expect(screen.getByText('No messages match these filters.')).toBeTruthy()
})
it('UI-L09: long saved logs are paged without hiding the total or losing messages', async () => {
  render(<LogPanel value={{ logs: { records: Array.from({ length: 205 }, (_, index) => ({ level: 'info', message: `message ${index}` })) } }} runId="run-a" dark={false} />)
  const user = userEvent.setup(); expect(screen.getAllByRole('listitem')).toHaveLength(100)
  await user.click(screen.getByRole('button', { name: 'Next logs' })); expect(screen.getByText('message 100')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Next logs' })); expect(screen.getAllByRole('listitem')).toHaveLength(5)
  expect((screen.getByRole('button', { name: 'Next logs' }) as HTMLButtonElement).disabled).toBe(true)
  await user.click(screen.getByRole('button', { name: 'Previous logs' })); expect(screen.getByText('message 100')).toBeTruthy()
})
it('UI-L10: failed-run structured messages and exception text remain readable together', () => {
  render(<LogPanel value={{ error: { message: 'Strategy crashed', logs: messages.logs }, logsIncomplete: true }} runId="run-a" dark={false} />)
  expect(screen.getByText('Strategy crashed')).toBeTruthy(); expect(screen.getByText('Order rejected')).toBeTruthy()
  expect(screen.getAllByRole('listitem')).toHaveLength(4)
})
it('UI-L11: case, whole-word and regular-expression search follow the toolbar options with recoverable syntax errors', async () => {
  render(<LogPanel value={{ logs: { records: [{ message: 'Order ordered ORDER reorder', level: 'info' }, { message: 'order', level: 'warning' }] } }} runId="run-a" dark={false} />)
  const user = userEvent.setup(), search = screen.getByRole('textbox', { name: 'Search logs' })
  await user.type(search, 'order'); expect(screen.getAllByRole('listitem')).toHaveLength(2)
  await user.click(screen.getByRole('button', { name: /^Match case$/ })); await user.click(screen.getByRole('button', { name: 'Match whole word' }))
  expect(screen.getAllByRole('listitem')).toHaveLength(1)
  await user.clear(search); await user.type(search, '^Order'); await user.click(screen.getByRole('button', { name: 'Use regular expression' }))
  expect(screen.getAllByRole('listitem')).toHaveLength(1); expect(screen.getByText('Order ordered ORDER reorder')).toBeTruthy()
  await user.clear(search); await user.type(search, '[['); expect(screen.getByRole('alert').textContent).toContain('Invalid regular expression')
  await user.click(screen.getByRole('button', { name: 'Reset log filters' })); expect(screen.getAllByRole('listitem')).toHaveLength(2); expect(screen.queryByRole('alert')).toBeNull()
})
