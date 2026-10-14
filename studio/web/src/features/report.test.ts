import { expect, it } from 'vitest'
import { formatMetric } from './report'
const metric = { value: .25, unit: 'ratio', methodId: 'core', status: 'ok', reason: null }
it('formats ratios according to their metric meaning, without changing undefined values', () => {
  expect(formatMetric('winRate', metric)).toBe('25%')
  expect(formatMetric('profitFactorMoney', metric)).toBe('0.25')
  expect(formatMetric('winRate', { ...metric, value: null, status: 'undefined' })).toBe('—')
  expect(formatMetric('cost', { ...metric, unit: 'percentage_points' })).toBe('0.25%')
  expect(formatMetric('money', { ...metric, unit: 'money' })).toBe('0.25')
})
it('uses identical money formatting in metrics and facts without inventing currency', async () => {
  const { formatFact } = await import('./report')
  const cash = { ...metric, value: -1234.567, unit: 'money' }
  expect(formatFact('pnlNet', cash.value, 'EUR')).toBe(formatMetric('totalPnl', cash, 'EUR'))
  expect(formatFact('pnlNet', null)).toBe('—')
  expect(formatFact('qty', .00000012)).toBe('0.00000012')
})
