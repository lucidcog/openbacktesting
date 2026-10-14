import { expect, it } from 'vitest'
import { initialDomain, searchDomains, filterValue } from './optimizer'
import type { InputSpec } from './inputs'
const base: InputSpec = { title: 'Value', attribute: 'value', kind: 'int', default: 1, group: '', inline: '', tooltip: '', active: true, display: 'all', confirm: false }
it.each([
  ['int', '3', 3], ['float', '1.5', 1.5], ['price', '9.25', 9.25], ['bool', true, true],
  ['string', 'a,b\ntext', 'a,b\ntext'], ['time', '1704067200000', 1704067200000],
  ['session', '24x7', '0000-0000:1234567'], ['color', '#ffaa00', '#ffaa00'], ['enum', 'FAST', 'FAST'],
] as const)('optimizer preserves and validates %s candidates', (kind, value, expected) => {
  const input = { ...base, kind, members: [{ name: 'FAST', title: 'Fast' }] }
  const draft = { ...initialDomain(input), enabled: true, values: [value] }
  expect(searchDomains([input], { Value: draft })).toEqual({ Value: { kind: 'values', values: [expected] } })
})
it.each(['int', 'float', 'price'] as const)('optimizer sends %s ranges without rounding decimal strings', kind => {
  const input = { ...base, kind }, draft = { ...initialDomain(input), enabled: true, kind: 'range' as const, start: '1', stop: '3', step: '1' }
  expect(searchDomains([input], { Value: draft })).toEqual({ Value: { kind: 'range', start: kind === 'int' ? 1 : '1', stop: kind === 'int' ? 3 : '3', step: kind === 'int' ? 1 : '1' } })
})
it.each([
  { values: [] }, { values: [1, '1'] }, { values: ['NaN'] },
  { kind: 'range' as const, start: '3', stop: '1', step: '1' },
  { kind: 'range' as const, start: '1', stop: '3', step: '0' },
  { kind: 'range' as const, start: '1.5', stop: '3', step: '1' },
])('invalid search domain is rejected before submitting: %j', patch => {
  expect(() => searchDomains([base], { Value: { ...initialDomain(base), enabled: true, ...patch } })).toThrow()
})
it('disabled dimensions are omitted so their current base inputs remain fixed', () => {
  expect(() => searchDomains([base], { Value: initialDomain(base) })).toThrow('Select at least one')
})
it.each(['bool', 'string', 'enum', 'time', 'session', 'color'] as const)('%s cannot silently become a numeric range', kind => {
  const input = { ...base, kind }
  expect(() => searchDomains([input], { Value: { ...initialDomain(input), enabled: true, kind: 'range', start: '1', stop: '3', step: '1' } })).toThrow('numeric')
})
it('filters preserve numeric, boolean, null and literal text values', () => {
  expect(['2.5', 'false', 'null', 'ok', '"001"'].map(filterValue)).toEqual([2.5, false, null, 'ok', '001'])
})
it('result presentation formats ratios and money while leaving nanosecond strings exact', async () => {
  const { resultLabel, resultValue } = await import('./optimizer')
  const metric = { value: 0.0730439539999, unit: 'ratio', status: 'ok', methodId: 'core' }
  expect(resultLabel('summary.all.totalReturn.value')).toBe('Total Return')
  expect(resultValue('summary.all.totalReturn.value', metric)).toBe('7.3%')
  expect(resultValue('summary.all.totalPnl.value', { ...metric, value: 730.43953999, unit: 'money' })).toBe('730.44')
  expect(resultValue('time.ns', { ...metric, value: '1700000000000000001', unit: 'ns' })).toBe('1700000000000000001 ns')
  expect(resultValue('summary.all.totalPnl.value', { ...metric, status: 'undefined' })).toBe('—')
})
