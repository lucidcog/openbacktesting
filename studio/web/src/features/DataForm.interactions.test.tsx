// @vitest-environment jsdom
import '@/test/dom'
import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { DataForm, defaultProfile, type DataProfile } from './DataForm'
function Form({ initial = defaultProfile, change = vi.fn(), validity = vi.fn() }: { initial?: DataProfile; change?: (value: DataProfile) => void; validity?: (valid: boolean) => void }) {
  const [value, setValue] = useState(initial)
  return <DataForm value={value} onChange={next => { change(next); setValue(next) }} onValidity={validity} />
}
const loader: DataProfile = { ...defaultProfile, kind: 'loader', path: 'loader.py', function: 'load_data', parameters: { period: 10 } }
const csv: DataProfile = { ...defaultProfile, kind: 'csv', path: 'prices.csv', timeColumn: 'Date' }
async function select(label: string, option: string) { const user = userEvent.setup(); await user.click(screen.getByRole('combobox', { name: label })); await user.click(screen.getByRole('option', { name: option })) }
function type(label: string, value: string) { fireEvent.change(screen.getByLabelText(label), { target: { value } }) }
it.each([['Workspace CSV', 'csv'], ['Local Python loader', 'loader'], ['Bundled sample', 'sample']])('UI-D01: source %s selects the matching source contract', async (label, kind) => {
  const change = vi.fn(); render(<Form initial={kind === 'sample' ? csv : defaultProfile} change={change} />)
  await select('Data source', label)
  expect(change.mock.lastCall?.[0]).toMatchObject({ kind, sample: kind === 'sample' ? 'GOOG' : null, function: kind === 'loader' ? 'load_data' : null, timeColumn: kind === 'csv' ? 'Date' : null })
})
it.each([['BTCUSD', 'month', 1], ['EURUSD', 'minute', 60], ['GOOG', 'day', 1]] as const)('UI-D02: sample %s updates symbol and declared timeframe', async (sample, unit, multiplier) => {
  const change = vi.fn(); render(<Form initial={{ ...defaultProfile, sample: sample === 'GOOG' ? 'BTCUSD' : 'GOOG' }} change={change} />)
  await select('Sample dataset', sample); expect(change.mock.lastCall?.[0]).toMatchObject({ sample, instrument: { symbol: sample }, timeframe: { unit, multiplier } })
})
it.each([
  ['Workspace path', 'data/other.csv', 'path'], ['Time column', 'timestamp', 'timeColumn'], ['Source timezone', 'America/New_York', 'sourceTimezone'],
  ['Chart timezone', 'Asia/Shanghai', 'timezone'], ['Start (inclusive, with offset)', '2024-01-01T00:00:00Z', 'start'], ['End (inclusive, with offset)', '2025-01-01T00:00:00Z', 'end'],
])('UI-D03: %s updates its data profile field', (label, text, key) => {
  const change = vi.fn(); render(<Form initial={csv} change={change} />); type(label, text); expect(change.mock.lastCall?.[0][key]).toBe(text)
})
it.each(['s', 'ms', 'us', 'ns', 'text'])('UI-D04: time encoding %s preserves the timestamp unit', async unit => {
  const change = vi.fn(); render(<Form initial={{ ...csv, timeUnit: unit === 'text' ? 'ms' : null }} change={change} />)
  await select('Time encoding', unit === 'text' ? 'Date/time text' : `Unix ${unit}`); expect(change.mock.lastCall?.[0].timeUnit).toBe(unit === 'text' ? null : unit)
})
it.each(['Open', 'High', 'Low', 'Close', 'Volume'])('UI-D05: %s mapping replaces the old source without losing other mappings', target => {
  const change = vi.fn(); render(<Form initial={{ ...csv, columns: { old: target, unrelated: 'Keep' } }} change={change} />)
  type(`${target} column`, 'new'); expect(change.mock.lastCall?.[0].columns).toEqual({ new: target, unrelated: 'Keep' })
  type(`${target} column`, target); expect(change.mock.lastCall?.[0].columns).toEqual({ unrelated: 'Keep' })
})
it.each(['second', 'minute', 'day', 'week', 'month'])('UI-D06: timeframe %s is saved without changing the data source', async unit => {
  const change = vi.fn(); render(<Form initial={{ ...csv, timeframe: { unit: unit === 'day' ? 'month' : 'day', multiplier: 3 } }} change={change} />)
  await select('Timeframe unit', unit); expect(change.mock.lastCall?.[0]).toMatchObject({ path: 'prices.csv', timeframe: { unit, multiplier: 3 } })
})
it.each([['Quantity step', 'quantity_step'], ['Price tick', 'price_tick'], ['Minimum quantity', 'min_quantity'], ['Minimum notional', 'min_notional']])('UI-D07: %s keeps a decimal draft and emits a numeric value', (label, key) => {
  const change = vi.fn(); render(<Form change={change} />); type(label, '0.'); expect((screen.getByLabelText(label) as HTMLInputElement).value).toBe('0.')
  type(label, '0.25'); expect(change.mock.lastCall?.[0].instrument[key]).toBe(0.25)
})
it.each(['Multiplier', 'Quantity step', 'Minimum notional'])('UI-D08: empty required %s remains invalid rather than silently becoming zero', label => {
  const change = vi.fn(); render(<Form change={change} />); type(label, '')
  expect((screen.getByLabelText(label) as HTMLInputElement).value).toBe('')
  const profile = change.mock.lastCall?.[0]; expect(Number.isNaN(label === 'Multiplier' ? profile.timeframe.multiplier : profile.instrument[label === 'Quantity step' ? 'quantity_step' : 'min_notional'])).toBe(true)
})
it.each(['Price tick', 'Minimum quantity'])('UI-D09: nullable %s can be cleared', label => {
  const change = vi.fn(); render(<Form change={change} />); type(label, '1.5'); type(label, '')
  expect(change.mock.lastCall?.[0].instrument[label === 'Price tick' ? 'price_tick' : 'min_quantity']).toBeNull()
})
it('UI-D10: symbol, currency, loader function and resources preserve their intended types', () => {
  const change = vi.fn(); render(<Form initial={loader} change={change} />)
  type('Symbol', 'ES'); type('Currency label', 'USD'); type('Loader function', 'prices'); type('Declared resources (comma separated)', ' a.csv, b.json, , ')
  expect(change.mock.lastCall?.[0]).toMatchObject({ function: 'prices', resources: ['a.csv', 'b.json'], instrument: { symbol: 'ES', currency: 'USD' } })
  type('Currency label', ''); expect(change.mock.lastCall?.[0].instrument.currency).toBeNull()
})
it.each(['{', '[]', 'null', '1'])('UI-D11: invalid loader JSON %s blocks applying while preserving the draft', text => {
  const validity = vi.fn(), change = vi.fn(); render(<Form initial={loader} validity={validity} change={change} />); type('Loader parameters (JSON object)', text)
  expect((screen.getByLabelText('Loader parameters (JSON object)') as HTMLTextAreaElement).value).toBe(text)
  expect(validity).toHaveBeenLastCalledWith(false); expect(change).not.toHaveBeenCalled(); expect(screen.getByRole('alert')).toBeTruthy()
  type('Loader parameters (JSON object)', '{"period": 20}'); expect(validity).toHaveBeenLastCalledWith(true); expect(change.mock.lastCall?.[0].parameters).toEqual({ period: 20 })
})
it('UI-D12: loading another profile with the same name refreshes JSON and its validation state', () => {
  const validity = vi.fn(); const view = render(<DataForm value={loader} onChange={vi.fn()} onValidity={validity} />)
  type('Loader parameters (JSON object)', '{'); expect(validity).toHaveBeenLastCalledWith(false)
  view.rerender(<DataForm value={{ ...loader, parameters: { period: 30 } }} onChange={vi.fn()} onValidity={validity} />)
  expect(JSON.parse((screen.getByLabelText('Loader parameters (JSON object)') as HTMLTextAreaElement).value)).toEqual({ period: 30 })
  expect(screen.queryByRole('alert')).toBeNull(); expect(validity).toHaveBeenLastCalledWith(true)
})
it('UI-D13: unrelated field edits preserve invalid JSON, changing source updates validity', async () => {
  const validity = vi.fn(); render(<Form initial={loader} validity={validity} />); type('Loader parameters (JSON object)', '{'); type('Symbol', 'NEW')
  expect((screen.getByLabelText('Loader parameters (JSON object)') as HTMLTextAreaElement).value).toBe('{'); expect(validity).toHaveBeenLastCalledWith(false)
  await select('Data source', 'Bundled sample'); expect(validity).toHaveBeenLastCalledWith(true)
  await select('Data source', 'Local Python loader'); expect(validity).toHaveBeenLastCalledWith(false)
})
